from __future__ import annotations

import json
import os
import sys
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT / "packages" / "oz-crawler" / "src"))
sys.path.insert(0, str(ROOT / "packages" / "oz-api" / "src"))

from lambda_crawler_entry import process_job  # noqa: E402
from oz_api.storage import RegistryStorage  # noqa: E402


def main() -> None:
    payload = os.environ.get("OZ_CRAWLER_JOB")
    if not payload:
        raise RuntimeError("OZ_CRAWLER_JOB must contain the crawler job JSON")
    storage = RegistryStorage.from_env(Path(os.environ.get("OZ_REPO_ROOT", ".")).resolve())
    process_job(storage, parse_payload(payload))


def parse_payload(payload: str) -> dict[str, Any]:
    parsed = json.loads(payload)
    if not isinstance(parsed, dict):
        raise RuntimeError("OZ_CRAWLER_JOB must decode to a JSON object")
    return parsed


if __name__ == "__main__":
    main()
