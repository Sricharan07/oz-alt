from __future__ import annotations

import json
import os
from typing import Any

from oz_api.admin_templates import render_admin_template
from oz_api.auth_store import AuthStore
from oz_api.storage import RegistryStorage


def render_admin(storage: RegistryStorage, csrf: str = "") -> str:
    snapshot = load_admin_snapshot(storage)
    catalog = storage.load_catalog()
    enrich_admin_snapshot(snapshot)
    return render_admin_template(
        {
            "csrf": csrf,
            "snapshot": snapshot,
            "catalog": catalog,
            "index_requests": snapshot["index_requests"],
            "telemetry": snapshot["telemetry"],
            "crawler_jobs": snapshot["crawler_jobs"],
            "aggregated_requests": aggregate_index_requests(snapshot["index_requests"]),
            "catalog_health": catalog_health_rows(catalog, snapshot["crawler_jobs"], snapshot["telemetry"]),
            "zero_result_queries": top_zero_result_queries(snapshot["telemetry"]),
            "crawl_max_pages": default_crawl_max_pages(),
            "crawl_recrawl_interval_hours": default_recrawl_interval_hours(),
            "crawl_concurrent_requests": default_crawl_concurrent_requests(),
        }
    )


def default_crawl_max_pages() -> int:
    return positive_int_env("OZ_ADMIN_CRAWL_MAX_PAGES") or positive_int_env("OZ_CRAWLER_MAX_PAGES") or 128


def default_recrawl_interval_hours() -> int:
    return positive_int_env("OZ_ADMIN_RECRAWL_INTERVAL_HOURS") or 24


def default_crawl_concurrent_requests() -> int:
    return positive_int_env("OZ_CRAWLER_CONCURRENCY") or 6


def positive_int_env(name: str) -> int | None:
    try:
        value = int(os.environ.get(name, ""))
    except ValueError:
        return None
    return value if value > 0 else None


def load_admin_snapshot(storage: RegistryStorage) -> dict[str, list[dict[str, Any]]]:
    return {
        "users": db_rows(
            """
            select email, role, password_set_at::text as password_set_at,
                   created_at::text as created_at, last_login_at::text as last_login_at,
                   disabled_at::text as disabled_at
            from users
            order by created_at desc
            limit 100
            """
        ),
        "usage_events": db_rows(
            """
            select coalesce(u.email, '') as email, e.event, e.library, e.query_length, e.result_count,
                   e.created_at::text as created_at
            from usage_events e
            left join users u on u.id = e.user_id
            order by e.created_at desc
            limit 200
            """
        ),
        "audit_logs": db_rows(
            """
            select coalesce(u.email, '') as email, a.action, a.created_at::text as created_at
            from auth_audit_logs a
            left join users u on u.id = a.user_id
            order by a.created_at desc
            limit 200
            """
        ),
        "admin_actions": db_rows(
            """
            select coalesce(u.email, '') as email, a.action, a.target_type, a.target,
                   a.created_at::text as created_at
            from admin_action_logs a
            left join users u on u.id = a.user_id
            order by a.created_at desc
            limit 200
            """
        ),
        "promotions": db_rows(
            """
            select vendor, library, version, ref_sha, pack_key, source_url,
                   promoted_at::text as promoted_at
            from catalog_promotions
            order by promoted_at desc
            limit 200
            """
        ),
        "freshness_policies": db_rows(
            """
            select vendor, library, version, source_url, recrawl_interval_hours, enabled,
                   updated_at::text as updated_at
            from freshness_policies
            order by updated_at desc
            limit 200
            """
        ),
        "library_profiles": db_rows(
            """
            select v.name as vendor, l.name as library, p.allowed_hosts, p.required_topics,
                   p.expected_symbols, p.source_file_patterns, p.needs_js, p.include_source_files,
                   p.target_language, p.updated_at::text as updated_at
            from library_profiles p
            join libraries l on l.id = p.library_id
            join vendors v on v.id = l.vendor_id
            order by p.updated_at desc
            limit 200
            """
        ),
        "index_requests": db_rows(
            """
            select library_name, vendor_hint, source_url_hint, requesting_user, request_count,
                   status, created_at::text as created_at
            from index_requests
            order by updated_at desc
            limit 200
            """
        ),
        "telemetry": db_telemetry_rows(),
        "crawler_jobs": db_rows(
            """
            select j.id, v.name as vendor, l.name as library_name, j.version, j.source_url, j.status,
                   j.embedding_status, j.last_error, j.pack_key, j.ref_sha, j.queued_at::text as queued_at,
                   j.finished_at::text as finished_at
            from crawler_jobs j
            left join libraries l on l.id = j.library_id
            left join vendors v on v.id = l.vendor_id
            order by j.queued_at desc
            limit 200
            """
        ),
        "embedding_jobs": db_rows(
            """
            select e.id, v.name as vendor, l.name as library, lv.version, e.status, e.mode,
                   e.pending_chunks, e.cached_chunks, e.embedded_chunks, e.failed_chunks,
                   e.total_tokens, e.voyage_batch_id, e.updated_at::text as updated_at, e.error
            from embedding_jobs e
            left join library_versions lv on lv.id = e.version_id
            left join libraries l on l.id = lv.library_id
            left join vendors v on v.id = l.vendor_id
            order by e.updated_at desc
            limit 200
            """
        ),
        "quality_runs": db_rows(
            """
            select v.name as vendor, l.name as library, q.version, q.passed, q.metrics,
                   q.created_at::text as created_at
            from quality_runs q
            join libraries l on l.id = q.library_id
            join vendors v on v.id = l.vendor_id
            order by q.created_at desc
            limit 200
            """
        ),
        "eval_runs": db_rows(
            """
            select v.name as vendor, l.name as library, e.version, e.eval_type, e.passed, e.metrics,
                   e.created_at::text as created_at
            from eval_runs e
            join libraries l on l.id = e.library_id
            join vendors v on v.id = l.vendor_id
            order by e.created_at desc
            limit 200
            """
        ),
        "search_quality_runs": db_rows(
            """
            select v.name as vendor, l.name as library, s.version, s.passed,
                   s.precision_at_1, s.precision_at_5, s.mrr, s.materialization_rate,
                   s.zero_result_rate, s.junk_top5_rate, s.created_at::text as created_at
            from search_quality_runs s
            join libraries l on l.id = s.library_id
            join vendors v on v.id = l.vendor_id
            order by s.created_at desc
            limit 200
            """
        ),
        "agent_context_stats": db_rows(
            """
            select v.name as vendor, l.name as library, lv.version,
                   count(distinct ao.id)::bigint as operation_count,
                   count(distinct ce.id)::bigint as example_count,
                   count(distinct ar.id)::bigint as recipe_count,
                   count(distinct ao.id) filter (where ao.embedding is not null)::bigint as embedded_operations,
                   count(distinct ce.id) filter (where ce.embedding is not null)::bigint as embedded_examples,
                   count(distinct sm.id) filter (where sm.embedding is not null)::bigint as embedded_sdk_methods,
                   count(distinct ar.id) filter (where ar.embedding is not null)::bigint as embedded_recipes,
                   round(avg(ar.confidence)::numeric, 3) as avg_recipe_confidence,
                   round(avg(ar.quality_score)::numeric, 3) as avg_recipe_quality
            from libraries l
            join vendors v on v.id = l.vendor_id
            left join refs r on r.library_id = l.id and r.channel = 'latest'
            left join library_versions lv on lv.id = coalesce(l.default_version_id, r.version_id)
            left join api_operations ao on ao.version_id = lv.id
            left join code_examples ce on ce.version_id = lv.id
            left join sdk_methods sm on sm.version_id = lv.id
            left join agent_recipes ar on ar.version_id = lv.id
            group by v.name, l.name, lv.version
            order by v.name asc, l.name asc
            limit 200
            """
        ),
        "pack_builds": db_rows(
            """
            select v.name as vendor, l.name as library, p.version, p.pack_sha, p.pack_key,
                   p.byte_size, p.storage_tier, p.download_count,
                   p.last_downloaded_at::text as last_downloaded_at,
                   p.created_at::text as created_at
            from pack_builds p
            join libraries l on l.id = p.library_id
            join vendors v on v.id = l.vendor_id
            order by p.created_at desc
            limit 200
            """
        ),
        "backup_runs": db_rows(
            """
            select backup_key, byte_size, sha256, status, started_at::text as started_at,
                   restore_verified_at::text as restore_verified_at, last_error
            from backup_runs
            order by started_at desc
            limit 200
            """
        ),
        "crawl_job_logs": db_rows(
            """
            select c.job_id, c.level, c.message, c.metadata_json, c.created_at::text as created_at
            from crawl_job_logs c
            order by c.created_at desc
            limit 300
            """
        ),
        "system_checks": db_rows(
            """
            select check_name, status, message, metadata_json, created_at::text as created_at
            from system_checks
            order by created_at desc
            limit 200
            """
        ),
        "ops_alerts": db_rows(
            """
            select severity, status, title, body, metadata_json,
                   delivery_status, delivery_error,
                   created_at::text as created_at, resolved_at::text as resolved_at
            from ops_alerts
            order by status asc, created_at desc
            limit 200
            """
        ),
        "slo_reports": db_rows(
            """
            select passed, api_health_ok_rate, search_quality_pass_rate,
                   crawler_success_rate, pack_signature_coverage, backup_fresh,
                   window_start::text as window_start, window_end::text as window_end,
                   created_at::text as created_at
            from slo_reports
            order by created_at desc
            limit 200
            """
        ),
    }


def db_rows(sql: str) -> list[dict[str, Any]]:
    store = AuthStore.from_env()
    if store is None:
        return []
    try:
        return store.execute(sql)
    except Exception:
        return []


def db_telemetry_rows() -> list[dict[str, Any]]:
    rows = db_rows(
        """
        select event, query_length, result_count, library_names, properties, created_at::text as created_at
        from telemetry_events
        order by created_at desc
        limit 200
        """
    )
    output: list[dict[str, Any]] = []
    for row in rows:
        properties = row.get("properties")
        if isinstance(properties, str):
            try:
                properties = json.loads(properties)
            except json.JSONDecodeError:
                properties = {}
        if not isinstance(properties, dict):
            properties = {
                "query_length": row.get("query_length"),
                "result_count": row.get("result_count"),
                "library_names": row.get("library_names") or [],
            }
        output.append({"event": row.get("event"), "properties": properties, "created_at": row.get("created_at")})
    return output


def aggregate_index_requests(requests: list[dict[str, Any]]) -> list[dict[str, Any]]:
    grouped: dict[tuple[str, str, str], dict[str, Any]] = {}
    for request in requests:
        library = str(request.get("library_name") or request.get("requested_library") or "")
        vendor = str(request.get("vendor_hint") or "")
        source = str(request.get("source_url_hint") or "")
        key = (library, vendor, source)
        row = grouped.setdefault(
            key,
            {
                "library_name": library,
                "vendor_hint": vendor,
                "source_url_hint": source,
                "request_count": 0,
                "requesting_users": set(),
                "latest_created_at": "",
            },
        )
        row["request_count"] += 1
        user = str(request.get("requesting_user") or "")
        if user:
            row["requesting_users"].add(user)
        created_at = str(request.get("created_at") or "")
        if created_at > row["latest_created_at"]:
            row["latest_created_at"] = created_at
    rows = []
    for row in grouped.values():
        row["requesting_user"] = ", ".join(sorted(row.pop("requesting_users")))
        row["vendor"] = row.get("vendor_hint", "")
        row["source_url"] = row.get("source_url_hint", "")
        row["count"] = row.get("request_count", 0)
        rows.append(row)
    rows.sort(key=lambda row: (int(row["request_count"]), str(row["latest_created_at"])), reverse=True)
    return rows


def enrich_admin_snapshot(snapshot: dict[str, list[dict[str, Any]]]) -> None:
    for section in (
        "freshness_policies",
        "library_profiles",
        "promotions",
        "quality_runs",
        "eval_runs",
        "search_quality_runs",
        "agent_context_stats",
        "pack_builds",
    ):
        for row in snapshot.get(section, []):
            row["library_label"] = library_label(row)
    for row in snapshot.get("crawler_jobs", []):
        row["library_label"] = library_label(row)
        status = str(row.get("status") or "")
        if row.get("embedding_status"):
            status = f"{status} / {row.get('embedding_status')}"
        row["status_label"] = status
        row["error"] = row.get("error") or row.get("last_error") or ""
    for row in snapshot.get("embedding_jobs", []):
        row["library_label"] = library_label(row, include_version=True)
    for row in snapshot.get("admin_actions", []):
        target_parts = [str(row.get("target_type") or ""), str(row.get("target") or "")]
        row["target_label"] = "/".join(part for part in target_parts if part)


def library_label(row: dict[str, Any], *, include_version: bool = False) -> str:
    vendor = str(row.get("vendor") or "")
    library = str(row.get("library") or row.get("library_name") or "")
    label = f"{vendor}/{library}".strip("/")
    if include_version and row.get("version"):
        label = f"{label}@{row.get('version')}"
    return label


def catalog_health_rows(
    catalog: list[dict[str, Any]],
    crawler_jobs: list[dict[str, Any]],
    telemetry: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    rows: dict[str, dict[str, Any]] = {}
    for entry in catalog:
        vendor = str(entry.get("vendor") or "")
        library = str(entry.get("library") or "")
        full = f"{vendor}/{library}".strip("/")
        row = rows.setdefault(
            full,
            {
                "library": full,
                "indexed_at": "",
                "versions": 0,
                "pulls": 0,
                "failures": 0,
            },
        )
        row["versions"] = int(row["versions"]) + 1
        indexed_at = str(entry.get("indexed_at") or entry.get("updated_at") or "")
        if indexed_at > str(row.get("indexed_at") or ""):
            row["indexed_at"] = indexed_at
    for event in telemetry:
        if event.get("event") != "pull_completed":
            continue
        library = str((event.get("properties") or {}).get("library") or "")
        if library in rows:
            rows[library]["pulls"] = int(rows[library]["pulls"]) + 1
    for job in crawler_jobs:
        if str(job.get("status") or "") != "failed":
            continue
        full = library_label(job)
        if full in rows:
            rows[full]["failures"] = int(rows[full]["failures"]) + 1
    return sorted(rows.values(), key=lambda row: str(row.get("library") or ""))


def top_zero_result_queries(telemetry: list[dict[str, Any]]) -> list[dict[str, Any]]:
    counts: dict[int, int] = {}
    for event in telemetry:
        properties = event.get("properties") or {}
        if event.get("event") != "suggest_query" or int(properties.get("result_count") or 0) != 0:
            continue
        query_length = int(properties.get("query_length") or 0)
        counts[query_length] = counts.get(query_length, 0) + 1
    return [
        {"query_length": query_length, "count": count}
        for query_length, count in sorted(counts.items(), key=lambda item: (-item[1], item[0]))[:20]
    ]
