from __future__ import annotations

import json
import os
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from oz_api.admin_ops import (
    get_library_profile,
    mark_crawler_job_completed,
    mark_crawler_job_failed,
    mark_crawler_job_started,
    record_eval_run,
    record_quality_run,
    record_catalog_promotion,
)
from oz_api.auth_store import AuthStore
from oz_api.indexer import PostgresWriter, write_catalog_and_chunks
from oz_api.queue import enqueue_crawler_job
from oz_api.retrieval import RetrievalContext, postgres_connection
from oz_api.storage import RegistryStorage, normalize_query
from oz_crawler.crawl import CrawlOptions, crawl_single_page
from oz_crawler.pack import build_pack_bytes


ROOT = Path(os.environ.get("OZ_REPO_ROOT", Path.cwd())).resolve()


def process_job(storage: RegistryStorage, job: dict[str, Any]) -> None:
    vendor = job.get("vendor") or job.get("vendor_hint")
    library = job.get("library_name") or job.get("library")
    source_url = job.get("source_url") or job.get("source_url_hint")
    version = str(job.get("version") or "latest")
    if not vendor or not library or not source_url:
        raise RuntimeError("vendor, library_name, and source_url are required")

    registry_root = Path("/tmp/oz-fixtures")
    write_job_profile(registry_root, vendor, library, job)
    mark_crawler_job_started(job)
    target = crawl_single_page(
        url=source_url,
        registry_root=registry_root,
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
            require_profile=os.environ.get("OZ_CRAWLER_REQUIRE_PROFILE", "1").lower() not in {"0", "false", "no"},
            fail_on_validation=os.environ.get("OZ_CRAWLER_FAIL_ON_VALIDATION", "1").lower() not in {"0", "false", "no"},
        ),
    )
    quality = load_quality_report(target)
    if not quality_gate_passed(quality):
        failed_entry = catalog_entry_for_job(
            vendor=vendor,
            library=library,
            version=version,
            source_url=source_url,
            fixture_path=target,
            pack_key="",
            ref_sha="",
        )
        record_quality_run(failed_entry, job, quality)
        raise RuntimeError("quality gate failed; pack was not promoted")
    pack_body, manifest = build_pack_bytes(target, vendor, library, version)
    pack_eval = pack_eval_report(manifest)
    if not pack_eval["passed"]:
        record_eval_run(catalog_entry_for_job(
            vendor=vendor,
            library=library,
            version=version,
            source_url=source_url,
            fixture_path=target,
            pack_key="",
            ref_sha=str(manifest["tree_sha256"]),
        ), eval_type="pack_materialization", passed=False, metrics=pack_eval)
        raise RuntimeError("pack materialization eval failed; pack was not promoted")
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
    index_catalog_entry(storage, catalog_entry)
    upsert_catalog_entry(storage, catalog_entry)
    record_eval_run(catalog_entry, eval_type="pack_materialization", passed=True, metrics=pack_eval)
    record_catalog_promotion(catalog_entry, job, quality)
    mark_crawler_job_completed(job, pack_key=pack_key, ref_sha=str(manifest["tree_sha256"]))


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
    connection = postgres_connection(ctx.database_url)
    if connection is None:
        raise RuntimeError("Postgres connection is required to index crawled docs")
    with connection:
        write_catalog_and_chunks(PostgresWriter(connection), storage, [entry])


def write_job_profile(registry_root: Path, vendor: str, library: str, job: dict[str, Any]) -> None:
    profile = job.get("profile")
    if not isinstance(profile, dict):
        return
    registry_root.mkdir(parents=True, exist_ok=True)
    document = {
        "libraries": [
            {
                "library": f"{vendor}/{library}",
                "allowed_hosts": profile.get("allowed_hosts") or [],
                "allowed_paths": profile.get("allowed_paths") or [],
                "denied_paths": profile.get("denied_paths") or [],
                "preferred_urls": profile.get("preferred_urls") or profile.get("source_priority") or [],
                "required_topics": profile.get("required_topics") or [],
                "expected_symbols": profile.get("expected_symbols") or [],
                "min_quality_score": profile.get("min_quality_score", 0.35),
                "min_documents": profile.get("min_documents", 2),
                "max_junk_ratio": profile.get("max_junk_ratio", 0.25),
            }
        ]
    }
    (registry_root / "library_profiles.json").write_text(
        json.dumps(document, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )


def load_quality_report(target: Path) -> dict[str, Any]:
    path = target / "_quality.json"
    if not path.exists():
        return {}
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return {}
    return data if isinstance(data, dict) else {}


def quality_gate_passed(quality: dict[str, Any]) -> bool:
    return bool(quality.get("passed"))


def pack_eval_report(manifest: dict[str, Any]) -> dict[str, Any]:
    blobs = manifest.get("blobs") if isinstance(manifest.get("blobs"), list) else []
    paths = {str(row.get("path") or "") for row in blobs if isinstance(row, dict)}
    require_signature = os.environ.get("OZ_PACK_REQUIRE_SIGNATURE", "").lower() in {"1", "true", "yes", "on"}
    has_signature = bool(manifest.get("signature"))
    metrics = {
        "blob_count": len(paths),
        "has_index": "INDEX.md" in paths,
        "has_meta": "_meta.json" in paths,
        "has_signature": has_signature,
        "requires_signature": require_signature,
        "has_path_traversal": any(path.startswith("/") or ".." in Path(path).parts for path in paths),
    }
    passed = (
        metrics["blob_count"] > 0
        and bool(metrics["has_index"])
        and bool(metrics["has_meta"])
        and not bool(metrics["has_path_traversal"])
        and (not require_signature or has_signature)
    )
    return {"passed": passed, "metrics": metrics}


def enqueue_due_freshness_policies(storage: RegistryStorage) -> int:
    store = AuthStore.from_env()
    if store is None:
        return 0
    try:
        rows = store.execute(
            """
            select fp.vendor, fp.library as library_name, fp.source_url,
                   coalesce(lv.version, 'latest') as version,
                   fp.recrawl_interval_hours
            from freshness_policies fp
            left join vendors v on v.name = fp.vendor
            left join libraries l on l.vendor_id = v.id and l.name = fp.library
            left join lateral (
              select version, last_crawled_at
              from library_versions
              where library_id = l.id
              order by indexed_at desc nulls last, created_at desc
              limit 1
            ) lv on true
            where fp.enabled = true
              and not exists (
                select 1
                from crawler_jobs j
                where j.library_id = l.id
                  and j.status in ('queued', 'running')
              )
              and (
                lv.last_crawled_at is null
                or lv.last_crawled_at < now() - make_interval(hours => fp.recrawl_interval_hours)
              )
            order by fp.updated_at asc
            limit 100
            """
        )
    except Exception:
        return 0
    queued = 0
    for row in rows:
        try:
            enqueue_crawler_job(
                storage,
                with_profile(
                    {
                        "vendor": row["vendor"],
                        "library_name": row["library_name"],
                        "version": row.get("version") or "latest",
                        "source_url": row["source_url"],
                        "max_pages": int(os.environ.get("OZ_CRAWLER_MAX_PAGES", "128")),
                        "fetcher": os.environ.get("OZ_CRAWLER_FETCHER", "auto"),
                        "concurrent_requests": int(os.environ.get("OZ_CRAWLER_CONCURRENCY", "6")),
                        "download_delay": float(os.environ.get("OZ_CRAWLER_DELAY", "0")),
                        "robots_txt": os.environ.get("OZ_CRAWLER_ROBOTS", "1").lower() not in {"0", "false", "no"},
                    }
                ),
            )
            queued += 1
        except Exception:
            continue
    return queued


def enqueue_seed_libraries(storage: RegistryStorage) -> None:
    seed_path = ROOT / "registry" / "seed_libraries.json"
    if not seed_path.exists():
        return
    for item in json.loads(seed_path.read_text(encoding="utf-8")):
        enqueue_crawler_job(
            storage,
            with_profile(
                {
                    "vendor": item["vendor"],
                    "library_name": item["library"],
                    "version": item["version"],
                    "source_url": item["source_url"],
                    "max_pages": int(os.environ.get("OZ_CRAWLER_MAX_PAGES", "16")),
                    "fetcher": os.environ.get("OZ_CRAWLER_FETCHER", "auto"),
                    "concurrent_requests": int(os.environ.get("OZ_CRAWLER_CONCURRENCY", "6")),
                    "download_delay": float(os.environ.get("OZ_CRAWLER_DELAY", "0")),
                    "robots_txt": os.environ.get("OZ_CRAWLER_ROBOTS", "1").lower() not in {"0", "false", "no"},
                }
            ),
        )


def with_profile(job: dict[str, Any]) -> dict[str, Any]:
    vendor = str(job.get("vendor") or "")
    library = str(job.get("library_name") or job.get("library") or "")
    profile = get_library_profile(vendor, library) or static_profile(vendor, library)
    if profile:
        return {**job, "profile": profile}
    return job


def static_profile(vendor: str, library: str) -> dict[str, Any] | None:
    path = ROOT / "registry" / "library_profiles.json"
    if not path.exists():
        return None
    try:
        rows = json.loads(path.read_text(encoding="utf-8")).get("libraries", [])
    except Exception:
        return None
    key = f"{vendor}/{library}"
    for row in rows:
        if isinstance(row, dict) and row.get("library") == key:
            return {
                "vendor": vendor,
                "library": library,
                "allowed_hosts": row.get("allowed_hosts") or [],
                "allowed_paths": row.get("allowed_paths") or [],
                "denied_paths": row.get("denied_paths") or [],
                "source_priority": row.get("preferred_urls") or row.get("source_priority") or [],
                "required_topics": row.get("required_topics") or [],
                "expected_symbols": row.get("expected_symbols") or [],
                "min_quality_score": row.get("min_quality_score", 0.35),
                "min_documents": row.get("min_documents", 2),
                "max_junk_ratio": row.get("max_junk_ratio", 0.25),
            }
    return None


def parse_body(body: Any) -> dict[str, Any]:
    if body is None:
        return {}
    if isinstance(body, dict):
        return body
    return json.loads(str(body))
