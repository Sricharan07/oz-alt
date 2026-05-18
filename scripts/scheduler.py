#!/usr/bin/env python3
from __future__ import annotations

import argparse
import os
import signal
import sys
import time
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "packages" / "oz-api" / "src"))

from oz_api.crawler_jobs import enqueue_due_freshness_policies, enqueue_seed_libraries  # noqa: E402
from oz_api.observability import configure_logging, trace_context  # noqa: E402
from oz_api.storage import RegistryStorage  # noqa: E402

RUNNING = True


def main() -> int:
    configure_logging()
    parser = argparse.ArgumentParser(description="Run the portable Oz scheduler.")
    parser.add_argument("--repo-root", type=Path, default=Path(os.environ.get("OZ_REPO_ROOT", ROOT)))
    parser.add_argument("--once", action="store_true")
    parser.add_argument(
        "--interval-seconds",
        type=int,
        default=int(os.environ.get("OZ_SCHEDULER_INTERVAL_SECONDS", "3600")),
    )
    args = parser.parse_args()

    signal.signal(signal.SIGTERM, stop)
    signal.signal(signal.SIGINT, stop)

    storage = RegistryStorage.from_env(args.repo_root.resolve())
    while RUNNING:
        with trace_context("scheduler-tick", sampled=False):
            queued = enqueue_due_freshness_policies(storage)
            if queued == 0 and os.environ.get("OZ_SCHEDULER_SEED_FALLBACK", "0").lower() in {"1", "true", "yes"}:
                enqueue_seed_libraries(storage)
        if args.once:
            break
        time.sleep(max(30, args.interval_seconds))
    return 0


def stop(_signum: int, _frame: Any) -> None:
    global RUNNING
    RUNNING = False


if __name__ == "__main__":
    raise SystemExit(main())
