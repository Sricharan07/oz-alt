from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from oz_crawler.crawl import CrawlOptions, crawl_single_page


def run_local_worker(
    *,
    queue_path: Path,
    registry_root: Path,
    max_pages: int,
    fetcher: str = "auto",
    concurrent_requests: int = 6,
    download_delay: float = 0.0,
    robots_txt: bool = True,
) -> int:
    if not queue_path.exists():
        return 0

    jobs = [json.loads(line) for line in queue_path.read_text(encoding="utf-8").splitlines() if line.strip()]
    processed = 0
    results: list[dict[str, Any]] = []
    for job in jobs:
        if job.get("status") not in {"queued", None}:
            results.append(job)
            continue
        vendor = job.get("vendor") or job.get("vendor_hint")
        library = job.get("library_name")
        source_url = job.get("source_url") or job.get("source_url_hint")
        version = str(job.get("version") or "latest")
        if not vendor or not library or not source_url:
            job["status"] = "failed"
            job["error"] = "vendor, library_name, and source_url are required"
            results.append(job)
            continue
        try:
            target = crawl_single_page(
                url=source_url,
                registry_root=registry_root,
                vendor=vendor,
                library=library,
                version=version,
                max_pages=max_pages,
                options=CrawlOptions(
                    max_pages=int(job.get("max_pages") or max_pages),
                    fetcher=str(job.get("fetcher") or fetcher),
                    concurrent_requests=int(job.get("concurrent_requests") or concurrent_requests),
                    download_delay=float(job.get("download_delay") or download_delay),
                    robots_txt=bool(job.get("robots_txt", robots_txt)),
                ),
            )
        except Exception as exc:  # pragma: no cover - operational boundary
            job["status"] = "failed"
            job["error"] = str(exc)
        else:
            job["status"] = "completed"
            job["fixture_path"] = str(target)
            processed += 1
        results.append(job)

    queue_path.write_text(
        "".join(json.dumps(job, sort_keys=True) + "\n" for job in results),
        encoding="utf-8",
    )
    return processed
