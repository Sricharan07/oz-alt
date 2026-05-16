from __future__ import annotations

import json
import os
import sys
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT / "packages" / "oz-crawler" / "src"))
sys.path.insert(0, str(ROOT / "packages" / "oz-api" / "src"))

from oz_api.storage import RegistryStorage  # noqa: E402
from oz_crawler.crawl import crawl_single_page  # noqa: E402


def handler(event: dict[str, Any], context: Any) -> dict[str, Any]:
    storage = RegistryStorage.from_env(Path(os.environ.get("OZ_REPO_ROOT", ".")).resolve())
    processed = 0
    failed = 0
    for record in event.get("Records", []):
        body = parse_body(record.get("body"))
        if body.get("type") == "scheduled_recrawl":
            enqueue_seed_libraries()
            processed += 1
            continue
        try:
            process_job(storage, body)
            processed += 1
        except Exception as exc:  # pragma: no cover - operational boundary
            failed += 1
            storage.append_admin_event(
                "crawler_jobs",
                {
                    "status": "failed",
                    "error": str(exc),
                    "job": body,
                },
            )
            raise
    return {"processed": processed, "failed": failed}


def process_job(storage: RegistryStorage, job: dict[str, Any]) -> None:
    vendor = job.get("vendor") or job.get("vendor_hint")
    library = job.get("library_name") or job.get("library")
    source_url = job.get("source_url") or job.get("source_url_hint")
    version = str(job.get("version") or "latest")
    if not vendor or not library or not source_url:
        raise RuntimeError("vendor, library_name, and source_url are required")

    target = crawl_single_page(
        url=source_url,
        registry_root=Path("/tmp/oz-fixtures"),
        vendor=vendor,
        library=library,
        version=version,
        max_pages=int(job.get("max_pages") or os.environ.get("OZ_CRAWLER_MAX_PAGES", "16")),
    )
    storage.append_admin_event(
        "crawler_jobs",
        {
            "status": "completed",
            "vendor": vendor,
            "library_name": library,
            "version": version,
            "source_url": source_url,
            "fixture_path": str(target),
        },
    )


def enqueue_seed_libraries() -> None:
    queue_url = os.environ.get("OZ_CRAWLER_QUEUE_URL")
    if not queue_url:
        return
    try:
        import boto3  # type: ignore
    except ImportError:
        return
    seed_path = ROOT / "registry" / "seed_libraries.json"
    if not seed_path.exists():
        return
    client = boto3.client("sqs")
    for item in json.loads(seed_path.read_text(encoding="utf-8")):
        client.send_message(
            QueueUrl=queue_url,
            MessageBody=json.dumps(
                {
                    "status": "queued",
                    "vendor": item["vendor"],
                    "library_name": item["library"],
                    "version": item["version"],
                    "source_url": item["source_url"],
                    "max_pages": int(os.environ.get("OZ_CRAWLER_MAX_PAGES", "16")),
                },
                sort_keys=True,
            ),
        )


def parse_body(body: Any) -> dict[str, Any]:
    if body is None:
        return {}
    if isinstance(body, dict):
        return body
    return json.loads(str(body))
