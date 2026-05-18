from __future__ import annotations

import html
import json
from typing import Any

from oz_api.auth_store import AuthStore
from oz_api.storage import RegistryStorage


def render_admin(storage: RegistryStorage, csrf: str = "") -> str:
    snapshot = load_admin_snapshot(storage)
    catalog = storage.load_catalog()
    index_requests = snapshot["index_requests"]
    telemetry = snapshot["telemetry"]
    crawler_jobs = snapshot["crawler_jobs"]
    aggregated_requests = aggregate_index_requests(index_requests)
    rows = "\n".join(
        render_catalog_row(entry, csrf)
        for entry in catalog
    )
    request_rows = "\n".join(render_index_request_row(request, csrf) for request in aggregated_requests)
    health_rows = "\n".join(render_catalog_health_row(entry, crawler_jobs, telemetry) for entry in catalog)
    job_rows = "\n".join(render_crawler_job_row(job) for job in crawler_jobs[-50:])
    zero_result_rows = "\n".join(render_zero_result_row(row) for row in top_zero_result_queries(telemetry))
    user_rows = "\n".join(render_user_row(row, csrf) for row in snapshot["users"][:50])
    usage_rows = "\n".join(render_usage_row(row) for row in snapshot["usage_events"][:50])
    audit_rows = "\n".join(render_audit_row(row) for row in snapshot["audit_logs"][:50])
    admin_action_rows = "\n".join(render_admin_action_row(row) for row in snapshot["admin_actions"][:50])
    promotion_rows = "\n".join(render_promotion_row(row) for row in snapshot["promotions"][:50])
    policy_rows = "\n".join(render_policy_row(row) for row in snapshot["freshness_policies"][:50])
    profile_rows = "\n".join(render_profile_row(row) for row in snapshot["library_profiles"][:100])
    quality_rows = "\n".join(render_quality_row(row) for row in snapshot["quality_runs"][:50])
    eval_rows = "\n".join(render_eval_row(row) for row in snapshot["eval_runs"][:50])
    search_quality_rows = "\n".join(render_search_quality_row(row) for row in snapshot["search_quality_runs"][:50])
    pack_rows = "\n".join(render_pack_row(row) for row in snapshot["pack_builds"][:50])
    embedding_job_rows = "\n".join(render_embedding_job_row(row, csrf) for row in snapshot["embedding_jobs"][:50])
    backup_rows = "\n".join(render_backup_row(row) for row in snapshot["backup_runs"][:50])
    crawl_log_rows = "\n".join(render_crawl_log_row(row) for row in snapshot["crawl_job_logs"][:80])
    system_check_rows = "\n".join(render_system_check_row(row) for row in snapshot["system_checks"][:50])
    alert_rows = "\n".join(render_alert_row(row) for row in snapshot["ops_alerts"][:50])
    slo_rows = "\n".join(render_slo_row(row) for row in snapshot["slo_reports"][:50])
    return f"""<!doctype html>
<html>
<head>
  <meta charset="utf-8">
  <title>Oz Admin</title>
  <style>
    body {{ font-family: ui-sans-serif, system-ui, sans-serif; margin: 24px; color: #202124; }}
    h1 {{ font-size: 24px; }}
    h2 {{ margin-top: 28px; font-size: 16px; }}
    table {{ border-collapse: collapse; width: 100%; }}
    th, td {{ border-bottom: 1px solid #d8dee4; padding: 8px; text-align: left; font-size: 14px; }}
    .metric {{ display: inline-block; margin-right: 24px; font-size: 14px; }}
    form {{ margin: 0; }}
    .grid {{ display: grid; grid-template-columns: repeat(2, minmax(280px, 1fr)); gap: 16px; }}
    .panel {{ border: 1px solid #d8dee4; border-radius: 8px; padding: 14px; }}
    label {{ display: block; color: #51565c; font-size: 13px; margin: 8px 0 4px; }}
    input, select {{ box-sizing: border-box; width: 100%; border: 1px solid #c7cbd1; border-radius: 6px; padding: 8px 10px; font: inherit; background: #fff; }}
    button.button {{ border: 1px solid #c7cbd1; border-radius: 6px; color: #202124; background: #fff; padding: 4px 8px; font: inherit; cursor: pointer; }}
    button.primary {{ margin-top: 10px; border: 0; border-radius: 6px; color: #fff; background: #202124; padding: 8px 10px; font: inherit; cursor: pointer; }}
    .actions {{ display: flex; gap: 6px; align-items: center; }}
  </style>
</head>
<body>
  <h1>Oz Admin</h1>
  <p><a href="/admin/logout">Log out</a></p>
  <div class="metric">Libraries: {len(catalog)}</div>
  <div class="metric">Index requests: {len(index_requests)}</div>
  <div class="metric">Telemetry events: {len(telemetry)}</div>
  <div class="metric">Usage events: {len(snapshot["usage_events"])}</div>
  <div class="metric">Users: {len(snapshot["users"])}</div>
  <div class="metric">Crawler jobs: {len(crawler_jobs)}</div>
  <div class="metric">Embedding jobs: {len(snapshot["embedding_jobs"])}</div>
  <div class="metric">Quality runs: {len(snapshot["quality_runs"])}</div>
  <div class="metric">Eval runs: {len(snapshot["eval_runs"])}</div>
  <div class="metric">Search quality: {len(snapshot["search_quality_runs"])}</div>
  <div class="metric">Open alerts: {sum(1 for row in snapshot["ops_alerts"] if str(row.get("status")) == "open")}</div>
  <div class="metric">Backups: {len(snapshot["backup_runs"])}</div>
  <h2>System Checks</h2>
  <table><thead><tr><th>Check</th><th>Status</th><th>Message</th><th>Metadata</th><th>Created</th></tr></thead><tbody>{system_check_rows}</tbody></table>
  <h2>Operations Alerts</h2>
  <table><thead><tr><th>Severity</th><th>Status</th><th>Title</th><th>Delivery</th><th>Created</th><th>Resolved</th></tr></thead><tbody>{alert_rows}</tbody></table>
  <h2>SLO Reports</h2>
  <table><thead><tr><th>Passed</th><th>API health</th><th>Search quality</th><th>Crawler success</th><th>Pack signatures</th><th>Backup fresh</th><th>Window</th><th>Created</th></tr></thead><tbody>{slo_rows}</tbody></table>
  <h2>Operations</h2>
  <div class="grid">
    <form class="panel" method="post" action="/admin/enqueue-crawl">
      <input type="hidden" name="csrf" value="{esc(csrf)}">
      <h2>Queue Crawl</h2>
      <label for="vendor">Vendor</label>
      <input id="vendor" name="vendor" required>
      <label for="library_name">Library</label>
      <input id="library_name" name="library_name" required>
      <label for="version">Version</label>
      <input id="version" name="version" value="latest" required>
      <label for="source_url">Source URL</label>
      <input id="source_url" name="source_url" type="url" required>
      <label for="max_pages">Max pages</label>
      <input id="max_pages" name="max_pages" type="number" min="1" max="1000" value="128">
      <label for="recrawl_interval_hours">Recrawl interval hours</label>
      <input id="recrawl_interval_hours" name="recrawl_interval_hours" type="number" min="1" value="24">
      <button class="primary" type="submit">Queue crawl</button>
    </form>
    <form class="panel" method="post" action="/admin/library-profile">
      <input type="hidden" name="csrf" value="{esc(csrf)}">
      <h2>Create Library Profile</h2>
      <label for="profile_vendor">Vendor</label>
      <input id="profile_vendor" name="vendor" required>
      <label for="profile_library">Library</label>
      <input id="profile_library" name="library_name" required>
      <label for="profile_source_url">Source URL</label>
      <input id="profile_source_url" name="source_url" type="url" required>
      <label for="allowed_hosts">Allowed hosts</label>
      <input id="allowed_hosts" name="allowed_hosts" placeholder="nextjs.org, github.com">
      <label for="allowed_paths">Allowed paths</label>
      <input id="allowed_paths" name="allowed_paths" placeholder="/docs, /vercel/next.js/tree/canary/docs">
      <label for="denied_paths">Denied paths</label>
      <input id="denied_paths" name="denied_paths" placeholder="/blog, /showcase">
      <label for="required_topics">Required topics</label>
      <input id="required_topics" name="required_topics" placeholder="routing, middleware, cookies">
      <label for="expected_symbols">Expected symbols</label>
      <input id="expected_symbols" name="expected_symbols" placeholder="NextRequest, NextResponse">
      <button class="primary" type="submit">Save profile</button>
    </form>
    <form class="panel" method="post" action="/admin/users/invite">
      <input type="hidden" name="csrf" value="{esc(csrf)}">
      <h2>Create User Invite</h2>
      <label for="invite_email">Email</label>
      <input id="invite_email" name="email" type="email" required>
      <label for="invite_role">Role</label>
      <select id="invite_role" name="role">
        <option value="user">user</option>
        <option value="admin">admin</option>
      </select>
      <button class="primary" type="submit">Create invite</button>
    </form>
    <form class="panel" method="post" action="/admin/default-version">
      <input type="hidden" name="csrf" value="{esc(csrf)}">
      <h2>Default Version</h2>
      <label for="default_vendor">Vendor</label>
      <input id="default_vendor" name="vendor" required>
      <label for="default_library">Library</label>
      <input id="default_library" name="library_name" required>
      <label for="default_version">Version</label>
      <input id="default_version" name="version" required>
      <button type="submit">Set default</button>
    </form>
    <form class="panel" method="post" action="/admin/promote-version">
      <input type="hidden" name="csrf" value="{esc(csrf)}">
      <h2>Promote / Rollback</h2>
      <label for="promote_vendor">Vendor</label>
      <input id="promote_vendor" name="vendor" required>
      <label for="promote_library">Library</label>
      <input id="promote_library" name="library_name" required>
      <label for="promote_version">Version</label>
      <input id="promote_version" name="version" required>
      <button type="submit">Point latest here</button>
    </form>
  </div>
  <h2>Index Requests</h2>
  <table><thead><tr><th>Library</th><th>Vendor</th><th>Source</th><th>Requests</th><th>Requested by</th><th></th></tr></thead><tbody>{request_rows}</tbody></table>
  <h2>Users</h2>
  <table><thead><tr><th>Email</th><th>Role</th><th>Password set</th><th>Created</th><th>Last login</th><th>Disabled</th><th></th></tr></thead><tbody>{user_rows}</tbody></table>
  <h2>Recent Usage</h2>
  <table><thead><tr><th>User</th><th>Event</th><th>Library</th><th>Query length</th><th>Results</th><th>Created</th></tr></thead><tbody>{usage_rows}</tbody></table>
  <h2>Audit Logs</h2>
  <table><thead><tr><th>User</th><th>Action</th><th>Created</th></tr></thead><tbody>{audit_rows}</tbody></table>
  <h2>Library Catalog</h2>
  <table><thead><tr><th>Library</th><th>Version</th><th>Description</th><th>Source</th><th></th></tr></thead><tbody>{rows}</tbody></table>
  <h2>Catalog Health</h2>
  <table><thead><tr><th>Library</th><th>Last crawled</th><th>Versions</th><th>Pulls</th><th>Failures</th></tr></thead><tbody>{health_rows}</tbody></table>
  <h2>Freshness Policies</h2>
  <table><thead><tr><th>Library</th><th>Source</th><th>Interval</th><th>Enabled</th><th>Updated</th></tr></thead><tbody>{policy_rows}</tbody></table>
  <h2>Library Profiles</h2>
  <table><thead><tr><th>Library</th><th>Allowed Hosts</th><th>Required Topics</th><th>Expected Symbols</th><th>Updated</th></tr></thead><tbody>{profile_rows}</tbody></table>
  <h2>Promotion History</h2>
  <table><thead><tr><th>Library</th><th>Version</th><th>Ref</th><th>Pack</th><th>Promoted</th></tr></thead><tbody>{promotion_rows}</tbody></table>
  <h2>Quality Runs</h2>
  <table><thead><tr><th>Library</th><th>Version</th><th>Passed</th><th>Metrics</th><th>Created</th></tr></thead><tbody>{quality_rows}</tbody></table>
  <h2>Eval Runs</h2>
  <table><thead><tr><th>Library</th><th>Version</th><th>Type</th><th>Passed</th><th>Metrics</th><th>Created</th></tr></thead><tbody>{eval_rows}</tbody></table>
  <h2>Search Quality Runs</h2>
  <table><thead><tr><th>Library</th><th>Version</th><th>Passed</th><th>P@1</th><th>P@5</th><th>MRR</th><th>Materialized</th><th>Zero</th><th>Junk</th><th>Created</th></tr></thead><tbody>{search_quality_rows}</tbody></table>
  <h2>Pack Builds</h2>
  <table><thead><tr><th>Library</th><th>Version</th><th>Pack SHA</th><th>Key</th><th>Bytes</th><th>Created</th></tr></thead><tbody>{pack_rows}</tbody></table>
  <h2>Embedding Jobs</h2>
  <table><thead><tr><th>Library</th><th>Status</th><th>Mode</th><th>Pending</th><th>Cached</th><th>Embedded</th><th>Failed</th><th>Tokens</th><th>Batch</th><th>Updated</th><th>Error</th><th>Action</th></tr></thead><tbody>{embedding_job_rows}</tbody></table>
  <h2>Backup Runs</h2>
  <table><thead><tr><th>Status</th><th>Key</th><th>Bytes</th><th>SHA256</th><th>Started</th><th>Verified</th><th>Error</th></tr></thead><tbody>{backup_rows}</tbody></table>
  <h2>Zero-result Suggest Queries</h2>
  <table><thead><tr><th>Query length</th><th>Count</th></tr></thead><tbody>{zero_result_rows}</tbody></table>
  <h2>Crawler Jobs</h2>
  <table><thead><tr><th>Library</th><th>Status</th><th>Version</th><th>Source</th><th>Queued</th><th>Finished</th><th>Error</th></tr></thead><tbody>{job_rows}</tbody></table>
  <h2>Crawl Logs</h2>
  <table><thead><tr><th>Job</th><th>Level</th><th>Message</th><th>Metadata</th><th>Created</th></tr></thead><tbody>{crawl_log_rows}</tbody></table>
  <h2>Admin Actions</h2>
  <table><thead><tr><th>User</th><th>Action</th><th>Target</th><th>Created</th></tr></thead><tbody>{admin_action_rows}</tbody></table>
  <h2>Queues</h2>
  <p><a href="/admin/index-requests">Index requests JSON</a> · <a href="/admin/crawler-jobs">Crawler jobs JSON</a> · <a href="/admin/crawl-job-logs">Crawl logs JSON</a> · <a href="/admin/telemetry">Telemetry JSON</a> · <a href="/admin/usage">Usage JSON</a> · <a href="/admin/actions">Actions JSON</a> · <a href="/admin/promotions">Promotions JSON</a> · <a href="/admin/freshness">Freshness JSON</a> · <a href="/admin/quality">Quality JSON</a> · <a href="/admin/evals">Evals JSON</a> · <a href="/admin/packs">Packs JSON</a></p>
</body>
</html>"""


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
                   p.expected_symbols, p.updated_at::text as updated_at
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
                   p.byte_size, p.created_at::text as created_at
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
        rows.append(row)
    rows.sort(key=lambda row: (int(row["request_count"]), str(row["latest_created_at"])), reverse=True)
    return rows


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
        f"<td>{esc(row.get('byte_size'))}</td><td>{esc(row.get('created_at'))}</td></tr>"
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
