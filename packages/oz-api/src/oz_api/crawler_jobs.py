from __future__ import annotations

import json
import os
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from oz_api.admin_ops import (
    get_library_profile,
    mark_crawler_job_completed,
    mark_crawler_job_embedding_waiting,
    mark_crawler_job_failed,
    mark_crawler_job_started,
    update_crawler_job_progress,
    record_crawler_job_log,
    record_eval_run,
    record_quality_run,
    record_catalog_promotion,
)
from oz_api.embedding_jobs import poll_pending_embedding_jobs
from oz_api.auth_store import AuthStore
from oz_api.indexer import PostgresWriter, write_catalog_and_chunks
from oz_api.jury import judge_search_check, jury_required, jury_requested
from oz_api.queue import enqueue_crawler_job
from oz_api.retrieval import RetrievalContext, postgres_connection
from oz_api.retrieval_local import search_from_fixtures
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
    record_crawler_job_log(
        job,
        "info",
        "profile written",
        {"vendor": vendor, "library": library, "version": version, "source_url": source_url},
    )
    mark_crawler_job_started(job)
    record_crawler_job_log(job, "info", "crawl started", {"max_pages": int(job.get("max_pages") or 0)})
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
            crawldir=crawler_checkpoint_dir(job, vendor, library, version),
            headless=os.environ.get("OZ_CRAWLER_HEADLESS", "1").lower() not in {"0", "false", "no"},
            network_idle=os.environ.get("OZ_CRAWLER_NETWORK_IDLE", "1").lower() not in {"0", "false", "no"},
            require_profile=os.environ.get("OZ_CRAWLER_REQUIRE_PROFILE", "1").lower() not in {"0", "false", "no"},
            fail_on_validation=os.environ.get("OZ_CRAWLER_FAIL_ON_VALIDATION", "1").lower() not in {"0", "false", "no"},
            progress_callback=lambda progress: update_crawler_job_progress(job, progress),
        ),
    )
    record_crawler_job_log(job, "info", "crawl finished", {"fixture_path": str(target)})
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
        record_crawler_job_log(job, "error", "quality gate failed", quality_summary(quality))
        raise RuntimeError("quality gate failed; pack was not promoted")
    record_crawler_job_log(job, "info", "quality gate passed", quality_summary(quality))
    quality_entry = catalog_entry_for_job(
        vendor=vendor,
        library=library,
        version=version,
        source_url=source_url,
        fixture_path=target,
        pack_key="",
        ref_sha="",
    )
    record_quality_run(quality_entry, job, quality)
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
        record_crawler_job_log(job, "error", "pack materialization eval failed", pack_eval)
        raise RuntimeError("pack materialization eval failed; pack was not promoted")
    record_crawler_job_log(job, "info", "pack built", pack_eval.get("metrics") or {})
    eval_entry = catalog_entry_for_job(
        vendor=vendor,
        library=library,
        version=version,
        source_url=source_url,
        fixture_path=target,
        pack_key="",
        ref_sha=str(manifest["tree_sha256"]),
    )
    record_eval_run(eval_entry, eval_type="pack_materialization", passed=True, metrics=pack_eval)
    search_eval = search_eval_report(storage, f"{vendor}/{library}", version)
    if search_eval is not None:
        record_eval_run(eval_entry, eval_type="semantic_search", passed=bool(search_eval["passed"]), metrics=search_eval)
        if not search_eval["passed"]:
            record_crawler_job_log(job, "error", "semantic search eval failed", search_eval)
            raise RuntimeError("semantic search eval failed; pack was not promoted")
        record_crawler_job_log(job, "info", "semantic search eval passed", search_eval)
    pack_key = storage.put_pack_bytes(vendor, library, version, pack_body)
    record_crawler_job_log(job, "info", "pack uploaded", {"pack_key": pack_key, "bytes": len(pack_body)})
    catalog_entry = catalog_entry_for_job(
        vendor=vendor,
        library=library,
        version=version,
        source_url=source_url,
        fixture_path=target,
        pack_key=pack_key,
        ref_sha=str(manifest["tree_sha256"]),
        crawler_job_id=job.get("db_job_id"),
    )
    embedding_results = index_catalog_entry(storage, catalog_entry)
    record_crawler_job_log(
        job,
        "info",
        "catalog indexed",
        {
            "ref_sha": catalog_entry["ref_sha"],
            "embedding_results": [result.__dict__ for result in embedding_results],
        },
    )
    incomplete = [result for result in embedding_results if not result.complete]
    if incomplete:
        waiting = incomplete[0]
        record_crawler_job_log(
            job,
            "info",
            "promotion waiting for embeddings",
            {"embedding_status": waiting.status, "embedding_job_id": waiting.job_id, "pending_chunks": waiting.pending_chunks},
        )
        mark_crawler_job_embedding_waiting(
            job,
            pack_key=pack_key,
            ref_sha=str(manifest["tree_sha256"]),
            status=waiting.status,
            embedding_job_id=waiting.job_id,
        )
        return
    upsert_catalog_entry(storage, catalog_entry)
    record_catalog_promotion(catalog_entry, job, quality)
    record_crawler_job_log(job, "info", "catalog promoted", {"pack_key": pack_key})
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
    crawler_job_id: Any | None = None,
) -> dict[str, Any]:
    description = f"Documentation crawled from {source_url}."
    fixture_value = str(fixture_path) if str(fixture_path) not in {"", "."} else f"registry/fixtures/{vendor}/{library}/{version}"
    return {
        "vendor": vendor,
        "library": library,
        "version": version,
        "description": description,
        "source_urls": [source_url],
        "keywords": sorted(set(normalize_query(description))),
        "fixture_path": fixture_value,
        "pack_path": pack_key,
        "ref_sha": ref_sha,
        "indexed_at": datetime.now(timezone.utc).isoformat(),
        "crawler_job_id": crawler_job_id,
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


def index_catalog_entry(storage: RegistryStorage, entry: dict[str, Any]) -> list[Any]:
    ctx = RetrievalContext.from_env(storage)
    connection = postgres_connection(ctx.database_url)
    if connection is None:
        raise RuntimeError("Postgres connection is required to index crawled docs")
    with connection:
        return write_catalog_and_chunks(PostgresWriter(connection), storage, [entry])


def process_pending_embedding_promotions(storage: RegistryStorage) -> int:
    ctx = RetrievalContext.from_env(storage)
    if not ctx.database_url:
        return 0
    ready = embedding_ready_rows(ctx.database_url)
    if not ready:
        completed = poll_and_apply_embedding_jobs(ctx.database_url)
        for result in completed:
            finalize_embedding_index(ctx.database_url, result.version_id, result.job_id)
        ready = embedding_ready_rows(ctx.database_url)
    count = 0
    for row in ready:
        if promote_embedding_ready_job(storage, row):
            count += 1
    return count


def embedding_ready_rows(database_url: str | None) -> list[dict[str, Any]]:
    connection = postgres_connection(database_url)
    if connection is None:
        return []
    with connection:
        ready = reused_embedding_ready_rows(connection)
        ready.extend(ready_embedding_promotion_rows(connection))
        return dedupe_ready_rows(ready)


def poll_and_apply_embedding_jobs(database_url: str | None) -> list[Any]:
    connection = postgres_connection(database_url)
    if connection is None:
        return []
    with connection:
        return [
            result
            for result in poll_pending_embedding_jobs(connection)
            if result.complete and result.version_id is not None and result.job_id is not None
        ]


def finalize_embedding_index(database_url: str | None, version_id: int | None, embedding_job_id: int | None) -> None:
    if version_id is None or embedding_job_id is None:
        return
    connection = postgres_connection(database_url)
    if connection is None:
        return
    with connection:
        writer = PostgresWriter(connection)
        writer.resolve_parent_chunks(version_id)
        writer.rebuild_dedupe_clusters(version_id)
        with connection.cursor() as cursor:
            cursor.execute(
                "update embedding_jobs set status = 'dedupe_done', updated_at = now() where id = %s and status = 'embeddings_applied'",
                (embedding_job_id,),
            )


def dedupe_ready_rows(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    seen: set[int] = set()
    output: list[dict[str, Any]] = []
    for row in rows:
        job_id = int(row["db_job_id"])
        if job_id in seen:
            continue
        seen.add(job_id)
        output.append(row)
    return output


def ready_embedding_promotion_rows(connection: Any) -> list[dict[str, Any]]:
    with connection.cursor() as cursor:
        cursor.execute(
            """
            select ej.id as embedding_job_id,
                   j.id as db_job_id,
                   v.name as vendor,
                   l.name as library,
                   coalesce(nullif(j.version, ''), lv.version) as version,
                   j.source_url,
                   j.pack_key,
                   j.ref_sha
            from embedding_jobs ej
            join library_versions lv on lv.id = ej.version_id
            join libraries l on l.id = lv.library_id
            join vendors v on v.id = l.vendor_id
            left join crawler_jobs j on j.id = ej.crawler_job_id
            where ej.status in ('embeddings_applied', 'dedupe_done')
              and j.status = 'batch_running'
              and j.pack_key is not null
              and j.ref_sha is not null
            order by ej.updated_at asc
            limit 20
            """,
        )
        columns = [getattr(column, "name", column[0]) for column in cursor.description]
        return [dict(zip(columns, row, strict=False)) for row in cursor.fetchall()]


def reused_embedding_ready_rows(connection: Any) -> list[dict[str, Any]]:
    with connection.cursor() as cursor:
        cursor.execute(
            """
            select distinct on (j.id)
                   ej.id as embedding_job_id,
                   j.id as db_job_id,
                   v.name as vendor,
                   l.name as library,
                   coalesce(nullif(j.version, ''), lv.version) as version,
                   j.source_url,
                   j.pack_key,
                   j.ref_sha
            from crawler_jobs j
            join libraries l on l.id = j.library_id
            join vendors v on v.id = l.vendor_id
            join library_versions lv on lv.library_id = l.id
                 and lv.version = coalesce(nullif(j.version, ''), lv.version)
            join embedding_jobs ej on ej.version_id = lv.id
            where j.status = 'batch_running'
              and j.pack_key is not null
              and j.ref_sha is not null
              and ej.status in ('embeddings_applied', 'dedupe_done', 'promoted')
              and (ej.crawler_job_id is null or ej.crawler_job_id <> j.id)
              and not exists (
                select 1 from chunks c
                where c.version_id = lv.id and c.embedding is null
              )
            order by j.id, ej.updated_at desc
            limit 20
            """,
        )
        columns = [getattr(column, "name", column[0]) for column in cursor.description]
        return [dict(zip(columns, row, strict=False)) for row in cursor.fetchall()]


def promote_embedding_ready_job(storage: RegistryStorage, row: dict[str, Any]) -> bool:
    entry = catalog_entry_for_job(
        vendor=str(row["vendor"]),
        library=str(row["library"]),
        version=str(row["version"]),
        source_url=str(row.get("source_url") or ""),
        fixture_path=Path(""),
        pack_key=str(row.get("pack_key") or ""),
        ref_sha=str(row.get("ref_sha") or ""),
        crawler_job_id=row.get("db_job_id"),
    )
    job = {"db_job_id": str(row["db_job_id"])}
    quality = latest_quality_for_job(row.get("db_job_id"))
    upsert_catalog_entry(storage, entry)
    record_catalog_promotion(entry, job, quality)
    record_crawler_job_log(job, "info", "catalog promoted after embedding batch", {"embedding_job_id": row["embedding_job_id"]})
    mark_crawler_job_completed(job, pack_key=str(row.get("pack_key") or ""), ref_sha=str(row.get("ref_sha") or ""))
    store = AuthStore.from_env()
    if store is not None:
        store.execute("update embedding_jobs set status = 'promoted', updated_at = now() where id = :id", {"id": row["embedding_job_id"]})
    return True


def latest_quality_for_job(job_id: Any) -> dict[str, Any]:
    store = AuthStore.from_env()
    if store is None or not job_id:
        return {}
    row = store.one(
        """
        select passed, metrics, errors, warnings
        from quality_runs
        where job_id = cast(:job_id as bigint)
        order by created_at desc
        limit 1
        """,
        {"job_id": str(job_id)},
    )
    if not row:
        return {}
    return {
        "passed": bool(row.get("passed")),
        "metrics": row.get("metrics") or {},
        "errors": row.get("errors") or [],
        "warnings": row.get("warnings") or [],
    }


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
                "source_file_patterns": profile.get("source_file_patterns") or [],
                "min_quality_score": profile.get("min_quality_score", 0.35),
                "min_documents": profile.get("min_documents", 2),
                "max_junk_ratio": profile.get("max_junk_ratio", 0.25),
                "needs_js": bool(profile.get("needs_js")),
                "include_source_files": bool(profile.get("include_source_files")),
                "target_language": profile.get("target_language") or "en",
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


def quality_summary(quality: dict[str, Any]) -> dict[str, Any]:
    return {
        "passed": bool(quality.get("passed")),
        "metrics": quality.get("metrics") or {},
        "errors": quality.get("errors") or [],
        "warnings": quality.get("warnings") or [],
    }


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


def search_eval_report(storage: RegistryStorage, library: str, version: str) -> dict[str, Any] | None:
    spec = eval_spec_for_library(storage, library, version)
    if spec is None:
        return None
    checks = []
    hits = 0
    top1 = 0
    reciprocal = 0.0
    junk_failures = 0
    duplicate_failures = 0
    content_failures = 0
    jury_scores: list[float] = []
    use_jury = jury_requested() or jury_required()
    for check in spec.get("checks", []):
        query = str(check.get("query") or "")
        expected = [str(item) for item in check.get("expected_files", [])]
        banned = [str(item).lower() for item in check.get("must_not_include", [])]
        required = [str(item).lower() for item in check.get("must_include", [])]
        rows = search_from_fixtures(storage, query, library_scope=library, max_results=5)
        paths = [str(row.get("path") or "") for row in rows]
        ranks = [idx + 1 for idx, path in enumerate(paths) if any(path.endswith(item) for item in expected)]
        contents = fixture_result_contents(storage, paths)
        jury_result: dict[str, Any] = {}
        if use_jury:
            try:
                jury_result = judge_search_check(check, paths, contents)
                jury_scores.append(float(jury_result.get("score") or 0))
            except Exception as exc:
                if jury_required():
                    raise RuntimeError(f"jury search eval failed: {exc}") from exc
                jury_result = {"error": str(exc)[:500]}
        joined = "\n".join(contents).lower()
        junk_hit = any(term in content.lower() for term in banned for content in contents)
        content_hit = all(term in joined for term in required)
        duplicate_hit = len(paths) != len(set(paths))
        if ranks:
            hits += 1
            reciprocal += 1.0 / ranks[0]
            top1 += int(ranks[0] == 1)
        junk_failures += int(junk_hit)
        duplicate_failures += int(duplicate_hit)
        content_failures += int(required and not content_hit)
        checks.append(
            {
                "name": check.get("name", query),
                "query": query,
                "paths": paths,
                "expected_files": expected,
                "expected_file_hit": bool(ranks),
                "junk_top5": junk_hit,
                "duplicate_top5": duplicate_hit,
                "required_content_hit": content_hit,
                "jury": jury_result,
            }
        )
    total = len(checks)
    recall = hits / total if total else 0.0
    materialized = materialization_rate(storage, checks)
    junk_rate = junk_failures / total if total else 0.0
    duplicate_rate = duplicate_failures / total if total else 0.0
    content_rate = 1 - (content_failures / total if total else 0.0)
    jury_score = sum(jury_scores) / len(jury_scores) if jury_scores else 0.0
    passed = (
        recall >= 0.85
        and materialized == 1.0
        and junk_rate == 0
        and duplicate_rate == 0
        and content_rate == 1.0
        and (not jury_required() or jury_score >= float(os.environ.get("OZ_EVAL_MIN_JURY_SCORE", "0.75")))
    )
    return {
        "passed": passed,
        "precision_at_1": round(top1 / total if total else 0.0, 3),
        "expected_file_recall_at_5": round(recall, 3),
        "precision_at_5": round(recall, 3),
        "mrr": round(reciprocal / total if total else 0.0, 3),
        "materialization_rate": round(materialized, 3),
        "junk_top5_rate": round(junk_rate, 3),
        "duplicate_top5_rate": round(duplicate_rate, 3),
        "content_requirement_rate": round(content_rate, 3),
        "jury_score": round(jury_score, 3) if use_jury else None,
        "checks": checks,
    }


def eval_spec_for_library(storage: RegistryStorage, library: str, version: str) -> dict[str, Any] | None:
    eval_root = storage.registry_root / "evals"
    for path in sorted(eval_root.glob("*.yaml")):
        try:
            spec = json.loads(path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            continue
        if spec.get("library") == library and str(spec.get("version") or version) == version:
            return spec
    return None


def fixture_result_contents(storage: RegistryStorage, paths: list[str]) -> list[str]:
    output: list[str] = []
    for result_path in paths:
        relative = result_path.removeprefix(".codo/vendors/")
        if "/" not in relative:
            continue
        vendor, rest = relative.split("/", 1)
        if "@" not in rest or "/" not in rest:
            continue
        library_version, doc_path = rest.split("/", 1)
        if "@" not in library_version:
            continue
        library, version = library_version.rsplit("@", 1)
        path = storage.fixtures_root / vendor / library / version / doc_path
        if path.exists():
            output.append(path.read_text(encoding="utf-8", errors="replace"))
    return output


def materialization_rate(storage: RegistryStorage, checks: list[dict[str, Any]]) -> float:
    total = 0
    existing = 0
    for check in checks:
        for result_path in check.get("paths", []):
            total += 1
            existing += int(bool(fixture_result_contents(storage, [str(result_path)])))
    return existing / total if total else 1.0


def enqueue_due_freshness_policies(storage: RegistryStorage) -> int:
    store = AuthStore.from_env()
    if store is None:
        return 0
    try:
        rows = store.execute(
            """
            with ranked_versions as (
              select fp.vendor,
                     fp.library as library_name,
                     fp.source_url,
                     coalesce(nullif(fp.version, 'latest'), lv.version, 'latest') as version,
                     coalesce(lv.last_crawled_at, timestamp with time zone 'epoch') as last_crawled_at,
                     lv.last_requested_at,
                     dense_rank() over (order by coalesce(lv.pull_count, 0) desc, lv.last_requested_at desc nulls last) as usage_rank,
                     fp.recrawl_interval_hours,
                     l.id as library_id
              from freshness_policies fp
              left join vendors v on v.name = fp.vendor
              left join libraries l on l.vendor_id = v.id and l.name = fp.library
              left join refs r on r.library_id = l.id and r.channel = 'latest'
              left join library_versions lv on lv.library_id = l.id
                   and lv.id = case
                     when fp.version = 'latest' then coalesce(l.default_version_id, r.version_id)
                     else lv.id
                   end
                   and (fp.version = 'latest' or lv.version = fp.version)
                   and lv.archived_at is null
              where fp.enabled = true
            ),
            due as (
              select *,
                     case
                       when usage_rank <= 100 then 24
                       when usage_rank <= 1000 then 360
                       when usage_rank <= 5000 then 720
                       else 1080
                     end as tier_interval_hours
              from ranked_versions
            )
            select vendor, library_name, source_url, version,
                   least(recrawl_interval_hours, tier_interval_hours)::integer as recrawl_interval_hours
            from due
            where library_id is not null
              and (last_requested_at is not null or version = 'latest')
              and not exists (
                select 1
                from crawler_jobs j
                where j.library_id = due.library_id
                  and j.version = due.version
                  and j.status in ('queued', 'running', 'batch_running')
              )
              and last_crawled_at < now() - make_interval(hours => least(recrawl_interval_hours, tier_interval_hours)::integer)
            order by usage_rank asc, last_crawled_at asc
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
                "source_file_patterns": row.get("source_file_patterns") or [],
                "min_quality_score": row.get("min_quality_score", 0.35),
                "min_documents": row.get("min_documents", 2),
                "max_junk_ratio": row.get("max_junk_ratio", 0.25),
                "needs_js": bool(row.get("needs_js")),
                "include_source_files": bool(row.get("include_source_files")),
                "target_language": row.get("target_language") or "en",
            }
    return None


def parse_body(body: Any) -> dict[str, Any]:
    if body is None:
        return {}
    if isinstance(body, dict):
        return body
    return json.loads(str(body))


def crawler_checkpoint_dir(job: dict[str, Any], vendor: Any, library: Any, version: str) -> Path | None:
    root = os.environ.get("OZ_CRAWLER_CRAWLDIR") or os.environ.get("OZ_CRAWLER_CHECKPOINT_DIR")
    if not root:
        root = "/tmp/oz-crawler-checkpoints"
    job_id = str(job.get("db_job_id") or "").strip()
    name = job_id or normalize_query(f"{vendor}-{library}-{version}")[:80]
    return Path(root) / name
