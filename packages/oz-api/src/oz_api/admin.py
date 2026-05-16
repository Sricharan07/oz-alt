from __future__ import annotations

import html
from typing import Any
from urllib.parse import quote

from oz_api.storage import RegistryStorage


def render_admin(storage: RegistryStorage) -> str:
    catalog = storage.load_catalog()
    index_requests = storage.read_admin_events("index_requests")
    telemetry = storage.read_admin_events("telemetry")
    crawler_jobs = storage.read_admin_events("crawler_jobs")
    aggregated_requests = aggregate_index_requests(index_requests)
    rows = "\n".join(
        f"<tr><td>{esc(entry.get('vendor'))}/{esc(entry.get('library'))}</td><td>{esc(entry.get('version'))}</td><td>{esc(entry.get('description',''))}</td></tr>"
        for entry in catalog
    )
    request_rows = "\n".join(render_index_request_row(request) for request in aggregated_requests)
    health_rows = "\n".join(render_catalog_health_row(entry, crawler_jobs, telemetry) for entry in catalog)
    job_rows = "\n".join(render_crawler_job_row(job) for job in crawler_jobs[-50:])
    zero_result_rows = "\n".join(render_zero_result_row(row) for row in top_zero_result_queries(telemetry))
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
    a.button {{ border: 1px solid #c7cbd1; border-radius: 6px; color: #202124; padding: 4px 8px; text-decoration: none; }}
  </style>
</head>
<body>
  <h1>Oz Admin</h1>
  <div class="metric">Libraries: {len(catalog)}</div>
  <div class="metric">Index requests: {len(index_requests)}</div>
  <div class="metric">Telemetry events: {len(telemetry)}</div>
  <div class="metric">Crawler jobs: {len(crawler_jobs)}</div>
  <h2>Index Requests</h2>
  <table><thead><tr><th>Library</th><th>Vendor</th><th>Source</th><th>Requests</th><th>Requested by</th><th></th></tr></thead><tbody>{request_rows}</tbody></table>
  <h2>Library Catalog</h2>
  <table><thead><tr><th>Library</th><th>Version</th><th>Description</th></tr></thead><tbody>{rows}</tbody></table>
  <h2>Catalog Health</h2>
  <table><thead><tr><th>Library</th><th>Last crawled</th><th>Versions</th><th>Pulls</th><th>Failures</th></tr></thead><tbody>{health_rows}</tbody></table>
  <h2>Zero-result Suggest Queries</h2>
  <table><thead><tr><th>Query length</th><th>Count</th></tr></thead><tbody>{zero_result_rows}</tbody></table>
  <h2>Crawler Jobs</h2>
  <table><thead><tr><th>Library</th><th>Status</th><th>Source</th><th>Error</th></tr></thead><tbody>{job_rows}</tbody></table>
  <h2>Queues</h2>
  <p><a href="/admin/index-requests">Index requests JSON</a> · <a href="/admin/crawler-jobs">Crawler jobs JSON</a> · <a href="/admin/telemetry">Telemetry JSON</a></p>
</body>
</html>"""


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


def render_index_request_row(request: dict[str, Any]) -> str:
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
            '<a class="button" href="/admin/enqueue-crawl?'
            f"library_name={url_component(library_raw)}&vendor={url_component(vendor_raw)}&source_url={url_component(source_raw)}"
            '">Approve crawl</a>'
        )
    return f"<tr><td>{library}</td><td>{vendor}</td><td>{source}</td><td>{count}</td><td>{user}</td><td>{approve}</td></tr>"


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
    return (
        f"<tr><td>{esc(job.get('vendor'))}/{esc(library)}</td>"
        f"<td>{esc(job.get('status'))}</td><td>{esc(job.get('source_url'))}</td>"
        f"<td>{esc(job.get('error') or job.get('last_error') or '')}</td></tr>"
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


def esc(value: Any) -> str:
    return html.escape(str(value or ""), quote=True)


def url_component(value: str) -> str:
    return quote(value, safe="")
