from __future__ import annotations

import html
import json
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
        }
    )


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
            select severity, status, title, delivery_status, delivery_error,
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


def render_index_request_row(request: dict[str, Any], csrf: str = "") -> str:
    library_raw = str(request.get("library_name") or request.get("requested_library") or "")
    vendor_raw = str(request.get("vendor_hint") or "")
    source_raw = str(request.get("source_url_hint") or "")
    library = esc(library_raw)
    vendor = esc(vendor_raw)
    source = esc(source_raw)
    user = esc(request.get("requesting_user") or "")
    count = esc(request.get("request_count") or 1)
    approve = ""
    if library_raw and vendor_raw and source_raw:
        approve = (
            '<form method="post" action="/admin/enqueue-crawl">'
            f'<input type="hidden" name="csrf" value="{esc(csrf)}">'
            f'<input type="hidden" name="library_name" value="{esc(library_raw)}">'
            f'<input type="hidden" name="vendor" value="{esc(vendor_raw)}">'
            f'<input type="hidden" name="source_url" value="{esc(source_raw)}">'
            '<input type="hidden" name="version" value="latest">'
            '<button class="button" type="submit">Approve crawl</button>'
            "</form>"
        )
    return f"<tr><td>{library}</td><td>{vendor}</td><td>{source}</td><td>{count}</td><td>{user}</td><td>{approve}</td></tr>"


def render_catalog_row(entry: dict[str, Any], csrf: str) -> str:
    vendor = str(entry.get("vendor") or "")
    library = str(entry.get("library") or "")
    version = str(entry.get("version") or "latest")
    source = source_url_for_entry(entry)
    recrawl = ""
    if vendor and library and source:
        recrawl = (
            '<form method="post" action="/admin/enqueue-crawl">'
            f'<input type="hidden" name="csrf" value="{esc(csrf)}">'
            f'<input type="hidden" name="vendor" value="{esc(vendor)}">'
            f'<input type="hidden" name="library_name" value="{esc(library)}">'
            f'<input type="hidden" name="version" value="{esc(version)}">'
            f'<input type="hidden" name="source_url" value="{esc(source)}">'
            '<input type="hidden" name="max_pages" value="128">'
            '<input type="hidden" name="recrawl_interval_hours" value="24">'
            '<button class="button" type="submit">Recrawl</button>'
            "</form>"
        )
    return (
        f"<tr><td>{esc(vendor)}/{esc(library)}</td><td>{esc(version)}</td>"
        f"<td>{esc(entry.get('description', ''))}</td><td>{esc(source)}</td><td>{recrawl}</td></tr>"
    )


def render_catalog_health_row(
    entry: dict[str, Any],
    crawler_jobs: list[dict[str, Any]],
    telemetry: list[dict[str, Any]],
) -> str:
    vendor = str(entry.get("vendor") or "")
    library = str(entry.get("library") or "")
    full = f"{vendor}/{library}"
    failures = sum(
        1
        for job in crawler_jobs
        if str(job.get("vendor") or "") == vendor
        and str(job.get("library_name") or job.get("library") or "") == library
        and str(job.get("status") or "") == "failed"
    )
    pulls = sum(
        1
        for event in telemetry
        if event.get("event") == "pull_completed"
        and str((event.get("properties") or {}).get("library") or "") == full
    )
    return (
        f"<tr><td>{esc(full)}</td><td>{esc(entry.get('indexed_at') or '')}</td>"
        f"<td>1</td><td>{pulls}</td><td>{failures}</td></tr>"
    )


def render_crawler_job_row(job: dict[str, Any]) -> str:
    library = job.get("library_name") or job.get("library") or ""
    status = job.get("status")
    if job.get("embedding_status"):
        status = f"{status} / {job.get('embedding_status')}"
    return (
        f"<tr><td>{esc(job.get('vendor'))}/{esc(library)}</td>"
        f"<td>{esc(status)}</td><td>{esc(job.get('version'))}</td>"
        f"<td>{esc(job.get('source_url'))}</td><td>{esc(job.get('queued_at'))}</td>"
        f"<td>{esc(job.get('finished_at'))}</td>"
        f"<td>{esc(job.get('error') or job.get('last_error') or '')}</td></tr>"
    )


def render_embedding_job_row(row: dict[str, Any], csrf: str) -> str:
    library = f"{row.get('vendor')}/{row.get('library')}@{row.get('version')}"
    batch = str(row.get("voyage_batch_id") or "")
    action = embedding_job_action(row, csrf)
    return (
        f"<tr><td>{esc(library)}</td><td>{esc(row.get('status'))}</td>"
        f"<td>{esc(row.get('mode'))}</td><td>{esc(row.get('pending_chunks'))}</td>"
        f"<td>{esc(row.get('cached_chunks'))}</td><td>{esc(row.get('embedded_chunks'))}</td>"
        f"<td>{esc(row.get('failed_chunks'))}</td><td>{esc(row.get('total_tokens'))}</td>"
        f"<td>{esc(batch[:24])}</td><td>{esc(row.get('updated_at'))}</td>"
        f"<td>{esc(row.get('error') or '')}</td><td>{action}</td></tr>"
    )


def embedding_job_action(row: dict[str, Any], csrf: str) -> str:
    if row.get("status") not in {"batch_submitted", "batch_running", "batch_partial", "sync_embedding"}:
        return ""
    return (
        '<form method="post" action="/admin/embedding-jobs/cancel">'
        f'<input type="hidden" name="csrf" value="{esc(csrf)}">'
        f'<input type="hidden" name="embedding_job_id" value="{esc(row.get("id"))}">'
        '<button type="submit">Cancel</button>'
        "</form>"
    )


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


def render_zero_result_row(row: dict[str, Any]) -> str:
    return f"<tr><td>{esc(row.get('query_length'))}</td><td>{esc(row.get('count'))}</td></tr>"


def render_user_row(row: dict[str, Any], csrf: str) -> str:
    email = str(row.get("email") or "")
    disabled = bool(row.get("disabled_at"))
    disable_path = "/admin/users/enable" if disabled else "/admin/users/disable"
    disable_label = "Enable" if disabled else "Disable"
    actions = (
        '<div class="actions">'
        '<form method="post" action="/admin/users/reset-password">'
        f'<input type="hidden" name="csrf" value="{esc(csrf)}">'
        f'<input type="hidden" name="email" value="{esc(email)}">'
        '<button class="button" type="submit">Reset</button>'
        '</form>'
        f'<form method="post" action="{disable_path}">'
        f'<input type="hidden" name="csrf" value="{esc(csrf)}">'
        f'<input type="hidden" name="email" value="{esc(email)}">'
        f'<button class="button" type="submit">{disable_label}</button>'
        '</form>'
        '</div>'
    )
    return (
        f"<tr><td>{esc(row.get('email'))}</td><td>{esc(row.get('role'))}</td>"
        f"<td>{esc(row.get('password_set_at'))}</td><td>{esc(row.get('created_at'))}</td>"
        f"<td>{esc(row.get('last_login_at'))}</td><td>{esc(row.get('disabled_at'))}</td>"
        f"<td>{actions}</td></tr>"
    )


def render_usage_row(row: dict[str, Any]) -> str:
    return (
        f"<tr><td>{esc(row.get('email'))}</td><td>{esc(row.get('event'))}</td>"
        f"<td>{esc(row.get('library'))}</td><td>{esc(row.get('query_length'))}</td>"
        f"<td>{esc(row.get('result_count'))}</td><td>{esc(row.get('created_at'))}</td></tr>"
    )


def render_audit_row(row: dict[str, Any]) -> str:
    return (
        f"<tr><td>{esc(row.get('email'))}</td><td>{esc(row.get('action'))}</td>"
        f"<td>{esc(row.get('created_at'))}</td></tr>"
    )


def render_admin_action_row(row: dict[str, Any]) -> str:
    target = "/".join(part for part in [str(row.get("target_type") or ""), str(row.get("target") or "")] if part)
    return (
        f"<tr><td>{esc(row.get('email'))}</td><td>{esc(row.get('action'))}</td>"
        f"<td>{esc(target)}</td><td>{esc(row.get('created_at'))}</td></tr>"
    )


def render_promotion_row(row: dict[str, Any]) -> str:
    library = f"{row.get('vendor')}/{row.get('library')}"
    ref = str(row.get("ref_sha") or "")
    return (
        f"<tr><td>{esc(library)}</td><td>{esc(row.get('version'))}</td>"
        f"<td>{esc(ref[:12])}</td><td>{esc(row.get('pack_key'))}</td>"
        f"<td>{esc(row.get('promoted_at'))}</td></tr>"
    )


def render_policy_row(row: dict[str, Any]) -> str:
    library = f"{row.get('vendor')}/{row.get('library')}@{row.get('version') or 'latest'}"
    return (
        f"<tr><td>{esc(library)}</td><td>{esc(row.get('source_url'))}</td>"
        f"<td>{esc(row.get('recrawl_interval_hours'))}h</td><td>{esc(row.get('enabled'))}</td>"
        f"<td>{esc(row.get('updated_at'))}</td></tr>"
    )


def render_profile_row(row: dict[str, Any]) -> str:
    library = f"{row.get('vendor')}/{row.get('library')}"
    return (
        f"<tr><td>{esc(library)}</td><td>{esc(join_json_list(row.get('allowed_hosts')))}</td>"
        f"<td>{esc(join_json_list(row.get('required_topics')))}</td>"
        f"<td>{esc(join_json_list(row.get('expected_symbols')))}</td>"
        f"<td>{esc(join_json_list(row.get('source_file_patterns')))}</td>"
        f"<td>{esc(row.get('target_language'))}</td>"
        f"<td>{esc(row.get('needs_js'))}</td>"
        f"<td>{esc(row.get('include_source_files'))}</td>"
        f"<td>{esc(row.get('updated_at'))}</td></tr>"
    )


def render_quality_row(row: dict[str, Any]) -> str:
    library = f"{row.get('vendor')}/{row.get('library')}"
    return (
        f"<tr><td>{esc(library)}</td><td>{esc(row.get('version'))}</td>"
        f"<td>{esc(row.get('passed'))}</td><td>{esc(compact_json(row.get('metrics')))}</td>"
        f"<td>{esc(row.get('created_at'))}</td></tr>"
    )


def render_eval_row(row: dict[str, Any]) -> str:
    library = f"{row.get('vendor')}/{row.get('library')}"
    return (
        f"<tr><td>{esc(library)}</td><td>{esc(row.get('version'))}</td>"
        f"<td>{esc(row.get('eval_type'))}</td><td>{esc(row.get('passed'))}</td>"
        f"<td>{esc(compact_json(row.get('metrics')))}</td><td>{esc(row.get('created_at'))}</td></tr>"
    )


def render_search_quality_row(row: dict[str, Any]) -> str:
    library = f"{row.get('vendor')}/{row.get('library')}"
    return (
        f"<tr><td>{esc(library)}</td><td>{esc(row.get('version'))}</td>"
        f"<td>{esc(row.get('passed'))}</td><td>{esc(row.get('precision_at_1'))}</td>"
        f"<td>{esc(row.get('precision_at_5'))}</td><td>{esc(row.get('mrr'))}</td>"
        f"<td>{esc(row.get('materialization_rate'))}</td><td>{esc(row.get('zero_result_rate'))}</td>"
        f"<td>{esc(row.get('junk_top5_rate'))}</td><td>{esc(row.get('created_at'))}</td></tr>"
    )


def render_pack_row(row: dict[str, Any]) -> str:
    library = f"{row.get('vendor')}/{row.get('library')}"
    sha = str(row.get("pack_sha") or "")
    return (
        f"<tr><td>{esc(library)}</td><td>{esc(row.get('version'))}</td>"
        f"<td>{esc(sha[:12])}</td><td>{esc(row.get('pack_key'))}</td>"
        f"<td>{esc(row.get('byte_size'))}</td><td>{esc(row.get('storage_tier'))}</td>"
        f"<td>{esc(row.get('download_count'))}</td><td>{esc(row.get('last_downloaded_at'))}</td>"
        f"<td>{esc(row.get('created_at'))}</td></tr>"
    )


def render_backup_row(row: dict[str, Any]) -> str:
    sha = str(row.get("sha256") or "")
    return (
        f"<tr><td>{esc(row.get('status'))}</td><td>{esc(row.get('backup_key'))}</td>"
        f"<td>{esc(row.get('byte_size'))}</td><td>{esc(sha[:12])}</td>"
        f"<td>{esc(row.get('started_at'))}</td><td>{esc(row.get('restore_verified_at'))}</td>"
        f"<td>{esc(row.get('last_error'))}</td></tr>"
    )


def render_crawl_log_row(row: dict[str, Any]) -> str:
    return (
        f"<tr><td>{esc(row.get('job_id'))}</td><td>{esc(row.get('level'))}</td>"
        f"<td>{esc(row.get('message'))}</td><td>{esc(compact_json(row.get('metadata_json')))}</td>"
        f"<td>{esc(row.get('created_at'))}</td></tr>"
    )


def render_system_check_row(row: dict[str, Any]) -> str:
    return (
        f"<tr><td>{esc(row.get('check_name'))}</td><td>{esc(row.get('status'))}</td>"
        f"<td>{esc(row.get('message'))}</td><td>{esc(compact_json(row.get('metadata_json')))}</td>"
        f"<td>{esc(row.get('created_at'))}</td></tr>"
    )


def render_alert_row(row: dict[str, Any]) -> str:
    delivery = str(row.get("delivery_status") or "")
    if row.get("delivery_error"):
        delivery = f"{delivery}: {row.get('delivery_error')}"
    return (
        f"<tr><td>{esc(row.get('severity'))}</td><td>{esc(row.get('status'))}</td>"
        f"<td>{esc(row.get('title'))}</td><td>{esc(delivery)}</td>"
        f"<td>{esc(row.get('created_at'))}</td><td>{esc(row.get('resolved_at'))}</td></tr>"
    )


def render_slo_row(row: dict[str, Any]) -> str:
    window = f"{row.get('window_start')} to {row.get('window_end')}"
    return (
        f"<tr><td>{esc(row.get('passed'))}</td><td>{pct(row.get('api_health_ok_rate'))}</td>"
        f"<td>{pct(row.get('search_quality_pass_rate'))}</td>"
        f"<td>{pct(row.get('crawler_success_rate'))}</td>"
        f"<td>{pct(row.get('pack_signature_coverage'))}</td>"
        f"<td>{esc(row.get('backup_fresh'))}</td><td>{esc(window)}</td>"
        f"<td>{esc(row.get('created_at'))}</td></tr>"
    )


def pct(value: Any) -> str:
    try:
        return f"{float(value) * 100:.1f}%"
    except (TypeError, ValueError):
        return "0.0%"


def compact_json(value: Any) -> str:
    if isinstance(value, str):
        return value[:240]
    return json.dumps(value or {}, separators=(",", ":"), sort_keys=True)[:240]


def join_json_list(value: Any) -> str:
    if isinstance(value, list):
        return ", ".join(str(item) for item in value)
    if isinstance(value, str):
        try:
            parsed = json.loads(value)
        except json.JSONDecodeError:
            return value
        if isinstance(parsed, list):
            return ", ".join(str(item) for item in parsed)
    return ""


def source_url_for_entry(entry: dict[str, Any]) -> str:
    urls = entry.get("source_urls")
    if isinstance(urls, list) and urls:
        return str(urls[0] or "")
    return str(entry.get("source_url") or "")


def esc(value: Any) -> str:
    return html.escape(str(value or ""), quote=True)
