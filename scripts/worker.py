#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import logging
import os
import signal
import sys
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "packages" / "oz-api" / "src"))

from oz_api.admin_ops import mark_crawler_job_failed  # noqa: E402
from oz_api.crawler_jobs import process_job, process_pending_embedding_promotions  # noqa: E402
from oz_api.observability import configure_logging, trace_context  # noqa: E402
from oz_api.queue import requeue_queued_crawler_jobs  # noqa: E402
from oz_api.redis_store import redis_client, redis_key  # noqa: E402
from oz_api.storage import RegistryStorage  # noqa: E402

RUNNING = True
LOGGER = logging.getLogger("oz.worker")


def main() -> int:
    configure_logging()
    parser = argparse.ArgumentParser(description="Run the portable Oz crawl worker.")
    parser.add_argument("--repo-root", type=Path, default=Path(os.environ.get("OZ_REPO_ROOT", ROOT)))
    parser.add_argument("--once", action="store_true")
    args = parser.parse_args()

    client = redis_client()
    if client is None:
        LOGGER.error("OZ_REDIS_URL or REDIS_URL is required for oz-worker")
        return 2

    signal.signal(signal.SIGTERM, stop)
    signal.signal(signal.SIGINT, stop)

    storage = RegistryStorage.from_env(args.repo_root.resolve())
    queue_name = redis_key("OZ_CRAWLER_REDIS_QUEUE", "oz:crawler:jobs")
    while RUNNING:
        item = client.blpop(queue_name, timeout=5)
        if item is not None:
            process_queue_item(storage, item)
            if args.once:
                break
            continue
        if queue_has_items(client, queue_name):
            continue
        if recover_db_queued_jobs():
            continue
        try:
            process_pending_embedding_promotions(storage)
        except Exception as exc:
            LOGGER.warning("embedding promotion poll failed: %s", exc)
        if args.once:
            break
    return 0


def process_queue_item(storage: RegistryStorage, item: Any) -> None:
    _queue, body = item
    job = parse_job(body)
    trace_id = str(job.get("request_id") or f"crawl-job-{job.get('db_job_id') or job.get('id') or 'unknown'}")
    with trace_context(trace_id, sampled=True):
        try:
            process_job(storage, job)
        except Exception as exc:
            mark_crawler_job_failed(job, str(exc))
            LOGGER.exception("crawler job failed")


def queue_has_items(client: Any, queue_name: str) -> bool:
    try:
        return int(client.llen(queue_name) or 0) > 0
    except Exception as exc:
        LOGGER.warning("crawler queue depth check failed: %s", exc)
        return False


def recover_db_queued_jobs() -> bool:
    try:
        count = requeue_queued_crawler_jobs(limit=int(os.environ.get("OZ_CRAWLER_REQUEUE_LIMIT", "20")))
    except Exception as exc:
        LOGGER.warning("queued crawler job recovery failed: %s", exc)
        return False
    if count:
        LOGGER.info("requeued DB-backed crawler jobs", extra={"count": count})
    return count > 0


def parse_job(body: Any) -> dict[str, Any]:
    if isinstance(body, bytes):
        body = body.decode("utf-8")
    payload = json.loads(str(body))
    if not isinstance(payload, dict):
        raise RuntimeError("crawler job payload must be a JSON object")
    return payload


def stop(_signum: int, _frame: Any) -> None:
    global RUNNING
    RUNNING = False


if __name__ == "__main__":
    raise SystemExit(main())
