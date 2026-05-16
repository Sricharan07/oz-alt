from __future__ import annotations

import json
import os
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT / "packages" / "oz-crawler" / "src"))
sys.path.insert(0, str(ROOT / "packages" / "oz-api" / "src"))

from oz_api.indexer import DataApiWriter, write_catalog_and_chunks  # noqa: E402
from oz_api.retrieval import RetrievalContext  # noqa: E402
from oz_api.storage import RegistryStorage, normalize_query  # noqa: E402
from oz_crawler.crawl import CrawlOptions, crawl_single_page  # noqa: E402
from oz_crawler.pack import build_pack_bytes  # noqa: E402


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
        options=CrawlOptions(
            max_pages=int(job.get("max_pages") or os.environ.get("OZ_CRAWLER_MAX_PAGES", "16")),
            fetcher=str(job.get("fetcher") or os.environ.get("OZ_CRAWLER_FETCHER", "auto")),
            concurrent_requests=int(job.get("concurrent_requests") or os.environ.get("OZ_CRAWLER_CONCURRENCY", "6")),
            download_delay=float(job.get("download_delay") or os.environ.get("OZ_CRAWLER_DELAY", "0")),
            robots_txt=str(job.get("robots_txt", os.environ.get("OZ_CRAWLER_ROBOTS", "1"))).lower()
            not in {"0", "false", "no"},
            crawldir=Path(os.environ["OZ_CRAWLER_CRAWLDIR"]) if os.environ.get("OZ_CRAWLER_CRAWLDIR") else None,
            headless=os.environ.get("OZ_CRAWLER_HEADLESS", "1").lower() not in {"0", "false", "no"},
            network_idle=os.environ.get("OZ_CRAWLER_NETWORK_IDLE", "1").lower() not in {"0", "false", "no"},
        ),
    )
    pack_body, manifest = build_pack_bytes(target, vendor, library, version)
    pack_key = storage.put_pack_bytes(vendor, library, version, pack_body)
    catalog_entry = catalog_entry_for_job(
        vendor=vendor,
        library=library,
        version=version,
        source_url=source_url,
        fixture_path=target,
        pack_key=pack_key,
        ref_sha=str(manifest["tree_sha256"]),
    )
    upsert_catalog_entry(storage, catalog_entry)
    index_catalog_entry(storage, catalog_entry)
    storage.append_admin_event(
        "crawler_jobs",
        {
            "status": "completed",
            "vendor": vendor,
            "library_name": library,
            "version": version,
            "source_url": source_url,
            "fixture_path": str(target),
            "pack_key": pack_key,
            "ref_sha": manifest["tree_sha256"],
        },
    )


def catalog_entry_for_job(
    *,
    vendor: str,
    library: str,
    version: str,
    source_url: str,
    fixture_path: Path,
    pack_key: str,
    ref_sha: str,
) -> dict[str, Any]:
    description = f"Documentation crawled from {source_url}."
    return {
        "vendor": vendor,
        "library": library,
        "version": version,
        "description": description,
        "source_urls": [source_url],
        "keywords": sorted(set(normalize_query(description))),
        "fixture_path": str(fixture_path),
        "pack_path": pack_key,
        "ref_sha": ref_sha,
        "indexed_at": datetime.now(timezone.utc).isoformat(),
    }


def upsert_catalog_entry(storage: RegistryStorage, entry: dict[str, Any]) -> None:
    document = storage.load_catalog_document()
    libraries = [
        row
        for row in document.get("libraries", [])
        if not (
            row.get("vendor") == entry["vendor"]
            and row.get("library") == entry["library"]
            and row.get("version") == entry["version"]
        )
    ]
    libraries.append(entry)
    libraries.sort(key=lambda row: (str(row.get("vendor")), str(row.get("library")), str(row.get("version"))))
    document["schema_version"] = document.get("schema_version") or 1
    document["generated_at"] = datetime.now(timezone.utc).isoformat()
    document["libraries"] = libraries
    storage.put_catalog_document(document)


def index_catalog_entry(storage: RegistryStorage, entry: dict[str, Any]) -> None:
    ctx = RetrievalContext.from_env(storage)
    writer = DataApiWriter(ctx)
    if not writer.available:
        return
    write_catalog_and_chunks(writer, storage, [entry])


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
                    "fetcher": os.environ.get("OZ_CRAWLER_FETCHER", "auto"),
                    "concurrent_requests": int(os.environ.get("OZ_CRAWLER_CONCURRENCY", "6")),
                    "download_delay": float(os.environ.get("OZ_CRAWLER_DELAY", "0")),
                    "robots_txt": os.environ.get("OZ_CRAWLER_ROBOTS", "1").lower() not in {"0", "false", "no"},
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
