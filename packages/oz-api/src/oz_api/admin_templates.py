from __future__ import annotations

import json
from typing import Any

from jinja2 import Environment
from markupsafe import Markup


ADMIN_TEMPLATE = r"""<!doctype html>
<html>
<head>
  <meta charset="utf-8">
  <title>Oz Admin</title>
  <style>
    body { font-family: ui-sans-serif, system-ui, sans-serif; margin: 24px; color: #202124; }
    h1 { font-size: 24px; }
    h2 { margin-top: 28px; font-size: 16px; }
    table { border-collapse: collapse; width: 100%; }
    th, td { border-bottom: 1px solid #d8dee4; padding: 8px; text-align: left; font-size: 14px; vertical-align: top; }
    .metric { display: inline-block; margin-right: 24px; font-size: 14px; }
    form { margin: 0; }
    .inline { display: inline; }
    .grid { display: grid; grid-template-columns: repeat(2, minmax(280px, 1fr)); gap: 16px; }
    .panel { border: 1px solid #d8dee4; border-radius: 8px; padding: 14px; }
    label { display: block; color: #51565c; font-size: 13px; margin: 8px 0 4px; }
    input, select { box-sizing: border-box; width: 100%; border: 1px solid #c7cbd1; border-radius: 6px; padding: 8px 10px; font: inherit; background: #fff; }
    button.button { border: 1px solid #c7cbd1; border-radius: 6px; color: #202124; background: #fff; padding: 4px 8px; font: inherit; cursor: pointer; }
    button.primary { margin-top: 10px; border: 0; border-radius: 6px; color: #fff; background: #202124; padding: 8px 10px; font: inherit; cursor: pointer; }
    .actions { display: flex; gap: 6px; align-items: center; flex-wrap: wrap; }
  </style>
</head>
<body>
  <h1>Oz Admin</h1>
  <form method="post" action="/admin/logout" class="inline">
    <input type="hidden" name="csrf" value="{{ csrf }}">
    <button class="button" type="submit">Log out</button>
  </form>

  <div class="metric">Libraries: {{ catalog|length }}</div>
  <div class="metric">Index requests: {{ index_requests|length }}</div>
  <div class="metric">Telemetry events: {{ telemetry|length }}</div>
  <div class="metric">Usage events: {{ snapshot.usage_events|length }}</div>
  <div class="metric">Users: {{ snapshot.users|length }}</div>
  <div class="metric">Crawler jobs: {{ crawler_jobs|length }}</div>
  <div class="metric">Embedding jobs: {{ snapshot.embedding_jobs|length }}</div>
  <div class="metric">Quality runs: {{ snapshot.quality_runs|length }}</div>
  <div class="metric">Eval runs: {{ snapshot.eval_runs|length }}</div>
  <div class="metric">Search quality: {{ snapshot.search_quality_runs|length }}</div>
  <div class="metric">Open alerts: {{ snapshot.ops_alerts|selectattr("status", "equalto", "open")|list|length }}</div>
  <div class="metric">Backups: {{ snapshot.backup_runs|length }}</div>

  {{ table("System Checks", ["Check", "Status", "Message", "Metadata", "Created"], snapshot.system_checks, ["check_name", "status", "message", "metadata_json", "created_at"]) }}
  {{ table("Operations Alerts", ["Severity", "Status", "Title", "Body", "Metadata", "Delivery", "Delivery Error", "Created", "Resolved"], snapshot.ops_alerts, ["severity", "status", "title", "body", "metadata_json", "delivery_status", "delivery_error", "created_at", "resolved_at"]) }}
  {{ table("SLO Reports", ["Passed", "API health", "Search quality", "Crawler success", "Pack signatures", "Backup fresh", "Window", "Created"], snapshot.slo_reports, ["passed", "api_health_ok_rate", "search_quality_pass_rate", "crawler_success_rate", "pack_signature_coverage", "backup_fresh", "window", "created_at"]) }}

  <h2>Operations</h2>
  <div class="grid">
    <form class="panel" method="post" action="/admin/enqueue-crawl">
      <input type="hidden" name="csrf" value="{{ csrf }}">
      <h2>Queue Crawl</h2>
      {{ input("vendor", "Vendor", required=True) }}
      {{ input("library_name", "Library", required=True) }}
      {{ input("version", "Version", value="latest", required=True) }}
      {{ input("source_url", "Source URL", type="url", required=True) }}
      {{ input("max_pages", "Max pages", type="number", value=crawl_max_pages) }}
      {{ input("recrawl_interval_hours", "Recrawl interval hours", type="number", value=crawl_recrawl_interval_hours) }}
      {{ input("concurrent_requests", "Concurrent requests", type="number", value=crawl_concurrent_requests) }}
      <label for="fetcher">Fetcher</label>
      <select id="fetcher" name="fetcher"><option value="">profile default</option><option value="auto">auto</option><option value="dynamic">dynamic</option><option value="stealth">stealth</option><option value="stdlib">stdlib</option></select>
      <button class="primary" type="submit">Queue crawl</button>
    </form>
    <form class="panel" method="post" action="/admin/library-profile">
      <input type="hidden" name="csrf" value="{{ csrf }}">
      <h2>Create Library Profile</h2>
      {{ input("profile_vendor", "Vendor", name="vendor", required=True) }}
      {{ input("profile_library", "Library", name="library_name", required=True) }}
      {{ input("profile_source_url", "Source URL", name="source_url", type="url", required=True) }}
      {{ input("allowed_hosts", "Allowed hosts", placeholder="nextjs.org, github.com") }}
      {{ input("allowed_paths", "Allowed paths", placeholder="/docs, /vercel/next.js/tree/canary/docs") }}
      {{ input("denied_paths", "Denied paths", placeholder="/blog, /showcase") }}
      {{ input("required_topics", "Required topics", placeholder="routing, middleware, cookies") }}
      {{ input("expected_symbols", "Expected symbols", placeholder="NextRequest, NextResponse") }}
      {{ input("source_file_patterns", "Source file patterns", placeholder="/src/, *.ts, *.py") }}
      {{ input("target_language", "Target language", value="en") }}
      <label><input name="needs_js" type="checkbox" value="1"> Needs JavaScript rendering</label>
      <label><input name="include_source_files" type="checkbox" value="1"> Include documented source files</label>
      <button class="primary" type="submit">Save profile</button>
    </form>
    <form class="panel" method="post" action="/admin/users/invite">
      <input type="hidden" name="csrf" value="{{ csrf }}">
      <h2>Create User Invite</h2>
      {{ input("invite_email", "Email", name="email", type="email", required=True) }}
      <label for="invite_role">Role</label>
      <select id="invite_role" name="role"><option value="user">user</option><option value="admin">admin</option></select>
      <button class="primary" type="submit">Create invite</button>
    </form>
    <form class="panel" method="post" action="/admin/default-version">
      <input type="hidden" name="csrf" value="{{ csrf }}">
      <h2>Default Version</h2>
      {{ input("default_vendor", "Vendor", name="vendor", required=True) }}
      {{ input("default_library", "Library", name="library_name", required=True) }}
      {{ input("default_version", "Version", name="version", required=True) }}
      <button type="submit">Set default</button>
    </form>
    <form class="panel" method="post" action="/admin/promote-version">
      <input type="hidden" name="csrf" value="{{ csrf }}">
      <h2>Promote / Rollback</h2>
      {{ input("promote_vendor", "Vendor", name="vendor", required=True) }}
      {{ input("promote_library", "Library", name="library_name", required=True) }}
      {{ input("promote_version", "Version", name="version", required=True) }}
      <button type="submit">Point latest here</button>
    </form>
  </div>

  <h2>Index Requests</h2>
  <table><thead><tr><th>Library</th><th>Vendor</th><th>Source</th><th>Requests</th><th>Requested by</th><th></th></tr></thead><tbody>
  {% for row in aggregated_requests %}
    <tr>
      <td>{{ row.library_name }}</td><td>{{ row.vendor }}</td><td>{{ row.source_url }}</td><td>{{ row.count }}</td><td>{{ row.requesting_user }}</td>
      <td>
        <form method="post" action="/admin/enqueue-crawl">
          <input type="hidden" name="csrf" value="{{ csrf }}">
          <input type="hidden" name="library_name" value="{{ row.library_name }}">
          <input type="hidden" name="vendor" value="{{ row.vendor }}">
          <input type="hidden" name="source_url" value="{{ row.source_url }}">
          <input type="hidden" name="version" value="latest">
          <input type="hidden" name="max_pages" value="{{ crawl_max_pages }}">
          <input type="hidden" name="recrawl_interval_hours" value="{{ crawl_recrawl_interval_hours }}">
          <input type="hidden" name="concurrent_requests" value="{{ crawl_concurrent_requests }}">
          <button class="button" type="submit">Queue crawl</button>
        </form>
      </td>
    </tr>
  {% endfor %}
  </tbody></table>

  <h2>Users</h2>
  <table><thead><tr><th>Email</th><th>Role</th><th>Password set</th><th>Created</th><th>Last login</th><th>Disabled</th><th></th></tr></thead><tbody>
  {% for row in snapshot.users[:50] %}
    <tr>
      <td>{{ row.email }}</td><td>{{ row.role }}</td><td>{{ row.password_set_at }}</td><td>{{ row.created_at }}</td><td>{{ row.last_login_at }}</td><td>{{ row.disabled_at }}</td>
      <td class="actions">
        <form method="post" action="/admin/users/reset-password"><input type="hidden" name="csrf" value="{{ csrf }}"><input type="hidden" name="email" value="{{ row.email }}"><button class="button" type="submit">Reset</button></form>
        {% if row.disabled_at %}
          <form method="post" action="/admin/users/enable"><input type="hidden" name="csrf" value="{{ csrf }}"><input type="hidden" name="email" value="{{ row.email }}"><button class="button" type="submit">Enable</button></form>
        {% else %}
          <form method="post" action="/admin/users/disable"><input type="hidden" name="csrf" value="{{ csrf }}"><input type="hidden" name="email" value="{{ row.email }}"><button class="button" type="submit">Disable</button></form>
        {% endif %}
      </td>
    </tr>
  {% endfor %}
  </tbody></table>

  {{ table("Recent Usage", ["User", "Event", "Library", "Query length", "Results", "Created"], snapshot.usage_events, ["email", "event", "library", "query_length", "result_count", "created_at"]) }}
  {{ table("Audit Logs", ["User", "Action", "Created"], snapshot.audit_logs, ["email", "action", "created_at"]) }}

  <h2>Library Catalog</h2>
  <table><thead><tr><th>Library</th><th>Version</th><th>Description</th><th>Source</th><th></th></tr></thead><tbody>
  {% for row in catalog %}
    <tr>
      <td>{{ row.vendor }}/{{ row.library }}</td><td>{{ row.version }}</td><td>{{ row.description }}</td><td>{{ row.source_urls|first_item }}</td>
      <td><form method="post" action="/admin/enqueue-crawl"><input type="hidden" name="csrf" value="{{ csrf }}"><input type="hidden" name="vendor" value="{{ row.vendor }}"><input type="hidden" name="library_name" value="{{ row.library }}"><input type="hidden" name="version" value="{{ row.version }}"><input type="hidden" name="source_url" value="{{ row.source_urls|first_item }}"><input type="hidden" name="max_pages" value="{{ crawl_max_pages }}"><input type="hidden" name="recrawl_interval_hours" value="{{ crawl_recrawl_interval_hours }}"><input type="hidden" name="concurrent_requests" value="{{ crawl_concurrent_requests }}"><button class="button" type="submit">Recrawl</button></form></td>
    </tr>
  {% endfor %}
  </tbody></table>

  {{ table("Catalog Health", ["Library", "Last crawled", "Versions", "Pulls", "Failures"], catalog_health, ["library", "indexed_at", "versions", "pulls", "failures"]) }}
  {{ table("Freshness Policies", ["Library", "Source", "Interval", "Enabled", "Updated"], snapshot.freshness_policies, ["library_label", "source_url", "recrawl_interval_hours", "enabled", "updated_at"]) }}
  {{ table("Library Profiles", ["Library", "Allowed Hosts", "Required Topics", "Expected Symbols", "Source Patterns", "Lang", "JS", "Source", "Updated"], snapshot.library_profiles, ["library_label", "allowed_hosts", "required_topics", "expected_symbols", "source_file_patterns", "target_language", "needs_js", "include_source_files", "updated_at"]) }}
  {{ table("Promotion History", ["Library", "Version", "Ref", "Pack", "Promoted"], snapshot.promotions, ["library_label", "version", "ref_sha", "pack_key", "promoted_at"]) }}
  {{ table("Quality Runs", ["Library", "Version", "Passed", "Metrics", "Created"], snapshot.quality_runs, ["library_label", "version", "passed", "metrics", "created_at"]) }}
  {{ table("Eval Runs", ["Library", "Version", "Type", "Passed", "Metrics", "Created"], snapshot.eval_runs, ["library_label", "version", "eval_type", "passed", "metrics", "created_at"]) }}
  {{ table("Search Quality Runs", ["Library", "Version", "Passed", "P@1", "P@5", "MRR", "Materialized", "Zero", "Junk", "Created"], snapshot.search_quality_runs, ["library_label", "version", "passed", "precision_at_1", "precision_at_5", "mrr", "materialization_rate", "zero_result_rate", "junk_top5_rate", "created_at"]) }}
  {{ table("Agent Context Index", ["Library", "Version", "Operations", "Examples", "Recipes", "Embedded Ops", "Embedded Recipes", "Recipe Confidence", "Recipe Quality"], snapshot.get("agent_context_stats", []), ["library_label", "version", "operation_count", "example_count", "recipe_count", "embedded_operations", "embedded_recipes", "avg_recipe_confidence", "avg_recipe_quality"]) }}
  {{ table("Pack Builds", ["Library", "Version", "Pack SHA", "Key", "Bytes", "Tier", "Downloads", "Last Download", "Created"], snapshot.pack_builds, ["library_label", "version", "pack_sha", "pack_key", "byte_size", "storage_tier", "download_count", "last_downloaded_at", "created_at"]) }}

  <h2>Embedding Jobs</h2>
  <table><thead><tr><th>Library</th><th>Status</th><th>Mode</th><th>Pending</th><th>Cached</th><th>Embedded</th><th>Failed</th><th>Tokens</th><th>Batch</th><th>Updated</th><th>Error</th><th>Action</th></tr></thead><tbody>
  {% for row in snapshot.embedding_jobs[:50] %}
    <tr>
      <td>{{ row.library_label }}</td><td>{{ row.status }}</td><td>{{ row.mode }}</td><td>{{ row.pending_chunks }}</td><td>{{ row.cached_chunks }}</td><td>{{ row.embedded_chunks }}</td><td>{{ row.failed_chunks }}</td><td>{{ row.total_tokens }}</td><td>{{ row.voyage_batch_id }}</td><td>{{ row.updated_at }}</td><td>{{ row.error }}</td>
      <td>{% if row.status in ["batch_submitted", "batch_running", "batch_partial", "sync_embedding"] %}<form method="post" action="/admin/embedding-jobs/cancel"><input type="hidden" name="csrf" value="{{ csrf }}"><input type="hidden" name="embedding_job_id" value="{{ row.id }}"><button class="button" type="submit">Cancel</button></form>{% endif %}</td>
    </tr>
  {% endfor %}
  </tbody></table>

  {{ table("Backup Runs", ["Status", "Key", "Bytes", "SHA256", "Started", "Verified", "Error"], snapshot.backup_runs, ["status", "backup_key", "byte_size", "sha256", "started_at", "restore_verified_at", "last_error"]) }}
  {{ table("Zero-result Suggest Queries", ["Query length", "Count"], zero_result_queries, ["query_length", "count"]) }}
  {{ table("Crawler Jobs", ["Library", "Status", "Version", "Source", "Queued", "Finished", "Error"], snapshot.crawler_jobs, ["library_label", "status_label", "version", "source_url", "queued_at", "finished_at", "error"]) }}
  {{ table("Crawl Logs", ["Job", "Level", "Message", "Metadata", "Created"], snapshot.crawl_job_logs, ["job_id", "level", "message", "metadata_json", "created_at"]) }}
  {{ table("Admin Actions", ["User", "Action", "Target", "Created"], snapshot.admin_actions, ["email", "action", "target_label", "created_at"]) }}

  <h2>Queues</h2>
  <p><a href="/admin/index-requests">Index requests JSON</a> · <a href="/admin/crawler-jobs">Crawler jobs JSON</a> · <a href="/admin/crawl-job-logs">Crawl logs JSON</a> · <a href="/admin/telemetry">Telemetry JSON</a> · <a href="/admin/usage">Usage JSON</a> · <a href="/admin/actions">Actions JSON</a> · <a href="/admin/promotions">Promotions JSON</a> · <a href="/admin/freshness">Freshness JSON</a> · <a href="/admin/quality">Quality JSON</a> · <a href="/admin/evals">Evals JSON</a> · <a href="/admin/packs">Packs JSON</a></p>
</body>
</html>"""


def render_admin_template(context: dict[str, Any]) -> str:
    env = Environment(autoescape=True)
    env.globals["table"] = render_table
    env.globals["input"] = render_input
    env.filters["first_item"] = first_item
    return env.from_string(ADMIN_TEMPLATE).render(**context)


def render_table(title: str, headers: list[str], rows: list[dict[str, Any]], fields: list[str]) -> str:
    env = Environment(autoescape=True)
    template = env.from_string(
        """
        <h2>{{ title }}</h2>
        <table><thead><tr>{% for header in headers %}<th>{{ header }}</th>{% endfor %}</tr></thead><tbody>
        {% for row in rows[:limit] %}
          <tr>{% for field in fields %}<td>{{ value(row, field) }}</td>{% endfor %}</tr>
        {% endfor %}
        </tbody></table>
        """
    )
    return Markup(template.render(title=title, headers=headers, rows=rows, fields=fields, value=value_for_field, limit=200))


def render_input(
    element_id: str,
    label: str,
    *,
    name: str | None = None,
    type: str = "text",
    value: str = "",
    placeholder: str = "",
    required: bool = False,
) -> str:
    env = Environment(autoescape=True)
    template = env.from_string(
        """
        <label for="{{ element_id }}">{{ label }}</label>
        <input id="{{ element_id }}" name="{{ name }}" type="{{ type }}" value="{{ value }}" placeholder="{{ placeholder }}"{% if required %} required{% endif %}>
        """
    )
    return Markup(
        template.render(
            element_id=element_id,
            label=label,
            name=name or element_id,
            type=type,
            value=value,
            placeholder=placeholder,
            required=required,
        )
    )


def value_for_field(row: dict[str, Any], field: str) -> str:
    if field == "window":
        return f"{row.get('window_start') or ''} to {row.get('window_end') or ''}"
    if field == "delivery":
        base = str(row.get("delivery_status") or "")
        error = str(row.get("delivery_error") or "")
        return f"{base}: {error}" if error else base
    value = row.get(field)
    if isinstance(value, (dict, list)):
        return compact_json(value)
    return str(value or "")


def first_item(value: Any) -> str:
    if isinstance(value, list) and value:
        return str(value[0])
    return str(value or "")


def compact_json(value: Any) -> str:
    if isinstance(value, str):
        try:
            value = json.loads(value)
        except json.JSONDecodeError:
            return value
    return json.dumps(value, sort_keys=True, separators=(",", ":"))[:500]
