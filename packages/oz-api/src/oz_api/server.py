from __future__ import annotations

import argparse
import html
import json
from dataclasses import dataclass
from datetime import datetime, timezone
from http import HTTPStatus
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from typing import Any
from urllib.parse import parse_qs, urlparse

from oz_api.auth import bearer_token, exchange_device_code, start_device_authorization, verify_token
from oz_api.limits import index_request_allowed
from oz_api.freshness import stale_libraries_from_payload
from oz_api.retrieval import (
    RetrievalContext,
    latest_entry as retrieval_latest_entry,
    search as retrieval_search,
    suggest as retrieval_suggest,
    unique_libraries_to_pull as retrieval_unique_libraries_to_pull,
)
from oz_api.storage import RegistryStorage
from oz_api.telemetry import sanitize_telemetry


@dataclass(frozen=True)
class ServerState:
    repo_root: Path
    require_auth: bool = False
    bearer_token: str = "local-dev-token"

    @property
    def storage(self) -> RegistryStorage:
        return RegistryStorage.from_env(self.repo_root)

    @property
    def registry_root(self) -> Path:
        return self.storage.registry_root

    @property
    def fixtures_root(self) -> Path:
        return self.storage.fixtures_root

    @property
    def packs_root(self) -> Path:
        return self.storage.packs_root

    @property
    def catalog_path(self) -> Path:
        return self.storage.catalog_path

    @property
    def admin_root(self) -> Path:
        return self.storage.admin_root


def build_handler(state: ServerState) -> type[BaseHTTPRequestHandler]:
    class OzHandler(BaseHTTPRequestHandler):
        server_version = "oz-api/0.1"

        def do_GET(self) -> None:
            try:
                if not is_authorized(self, state):
                    self.send_json({"error": "unauthorized"}, status=HTTPStatus.UNAUTHORIZED)
                    return
                route_get(self, state)
            except Exception as exc:  # pragma: no cover - defensive server boundary
                self.send_json({"error": str(exc)}, status=HTTPStatus.INTERNAL_SERVER_ERROR)

        def do_POST(self) -> None:
            try:
                if not is_authorized(self, state):
                    self.send_json({"error": "unauthorized"}, status=HTTPStatus.UNAUTHORIZED)
                    return
                route_post(self, state)
            except Exception as exc:  # pragma: no cover - defensive server boundary
                self.send_json({"error": str(exc)}, status=HTTPStatus.INTERNAL_SERVER_ERROR)

        def read_json(self) -> dict[str, Any]:
            length = int(self.headers.get("Content-Length", "0"))
            if length == 0:
                return {}
            body = self.rfile.read(length)
            return json.loads(body.decode("utf-8"))

        def send_json(self, payload: Any, *, status: HTTPStatus = HTTPStatus.OK) -> None:
            body = json.dumps(payload, indent=2, sort_keys=True).encode("utf-8")
            self.send_response(status)
            self.send_header("Content-Type", "application/json")
            self.send_header("Content-Length", str(len(body)))
            self.end_headers()
            self.wfile.write(body)

        def send_bytes(self, payload: bytes, *, content_type: str) -> None:
            self.send_response(HTTPStatus.OK)
            self.send_header("Content-Type", content_type)
            self.send_header("Content-Length", str(len(payload)))
            self.send_header("Cache-Control", "public, max-age=31536000, immutable")
            self.end_headers()
            self.wfile.write(payload)

        def send_redirect(self, location: str) -> None:
            self.send_response(HTTPStatus.FOUND)
            self.send_header("Location", location)
            self.send_header("Cache-Control", "public, max-age=31536000, immutable")
            self.end_headers()

        def send_html(self, html: str, *, status: HTTPStatus = HTTPStatus.OK) -> None:
            body = html.encode("utf-8")
            self.send_response(status)
            self.send_header("Content-Type", "text/html; charset=utf-8")
            self.send_header("Content-Length", str(len(body)))
            self.end_headers()
            self.wfile.write(body)

        def log_message(self, format: str, *args: Any) -> None:
            return

    return OzHandler


def is_authorized(handler: BaseHTTPRequestHandler, state: ServerState) -> bool:
    if not state.require_auth:
        return True
    path = urlparse(handler.path).path
    if path in {"/health", "/auth/device", "/auth/token", "/auth/verify"}:
        return True
    token = bearer_token(handler.headers)
    return token == state.bearer_token or (token is not None and verify_token(token))


def render_admin(state: ServerState) -> str:
    catalog = state.storage.load_catalog()
    index_requests = state.storage.read_admin_events("index_requests")
    telemetry = state.storage.read_admin_events("telemetry")
    crawler_jobs = state.storage.read_admin_events("crawler_jobs")
    rows = "\n".join(
        f"<tr><td>{esc(entry.get('vendor'))}/{esc(entry.get('library'))}</td><td>{esc(entry.get('version'))}</td><td>{esc(entry.get('description',''))}</td></tr>"
        for entry in catalog
    )
    request_rows = "\n".join(
        render_index_request_row(request)
        for request in sorted(index_requests, key=lambda row: str(row.get("created_at", "")), reverse=True)
    )
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
  <table><thead><tr><th>Library</th><th>Vendor</th><th>Source</th><th>Requested by</th><th></th></tr></thead><tbody>{request_rows}</tbody></table>
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


def render_index_request_row(request: dict[str, Any]) -> str:
    library = esc(request.get("library_name") or request.get("requested_library") or "")
    vendor = esc(request.get("vendor_hint") or "")
    source = esc(request.get("source_url_hint") or "")
    user = esc(request.get("requesting_user") or "")
    approve = ""
    if library and source:
        approve = (
            "<a class=\"button\" href=\"/admin/enqueue-crawl?"
            f"library_name={url_component(library)}&vendor={url_component(vendor)}&source_url={url_component(source)}"
            "\">Approve crawl</a>"
        )
    return f"<tr><td>{library}</td><td>{vendor}</td><td>{source}</td><td>{user}</td><td>{approve}</td></tr>"


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
    from urllib.parse import quote

    return quote(value, safe="")


def read_catalog_generated_at(state: ServerState) -> str | None:
    return state.storage.catalog_generated_at()


def route_get(handler: BaseHTTPRequestHandler, state: ServerState) -> None:
    parsed = urlparse(handler.path)
    path = parsed.path.strip("/")
    parts = path.split("/") if path else []

    if parsed.path == "/health":
        handler.send_json({"ok": True, "service": "oz-api"})
        return

    if parsed.path in {"/admin", "/admin/"}:
        handler.send_html(render_admin(state))
        return

    if parsed.path == "/admin/enqueue-crawl":
        params = parse_qs(parsed.query)
        event = {
            "created_at": now(),
            "status": "queued",
            "library_name": params.get("library_name", [""])[0],
            "vendor": params.get("vendor", [""])[0],
            "source_url": params.get("source_url", [""])[0],
        }
        state.storage.append_admin_event("crawler_jobs", event)
        handler.send_html(
            "<!doctype html><meta http-equiv=\"refresh\" content=\"0; url=/admin\">",
            status=HTTPStatus.ACCEPTED,
        )
        return

    if parsed.path == "/refs":
        handler.send_json(bulk_refs_payload(state, parsed.query))
        return

    if len(parts) == 3 and parts[0] == "refs":
        vendor, library = parts[1], parts[2]
        entry = retrieval_latest_entry(state.storage, vendor, library)
        if entry is None:
            handler.send_json({"error": "library not indexed"}, status=HTTPStatus.NOT_FOUND)
            return
        handler.send_json(
            {
                "vendor": vendor,
                "library": library,
                "version": entry["version"],
                "ref_sha": entry.get("ref_sha", "local"),
            }
        )
        return

    if len(parts) == 4 and parts[0] == "pack":
        _, vendor, library, version = parts
        pack_url = state.storage.get_pack_url(vendor, library, version)
        if pack_url:
            handler.send_redirect(pack_url)
            return
        pack_bytes = state.storage.get_pack_bytes(vendor, library, version)
        if pack_bytes is None:
            handler.send_json({"error": "pack not found"}, status=HTTPStatus.NOT_FOUND)
            return
        handler.send_bytes(pack_bytes, content_type="application/vnd.oz.pack")
        return

    if parsed.path == "/admin/index-requests":
        handler.send_json(state.storage.read_admin_events("index_requests"))
        return

    if parsed.path == "/admin/telemetry":
        handler.send_json(state.storage.read_admin_events("telemetry"))
        return

    if parsed.path == "/admin/crawler-jobs":
        handler.send_json(state.storage.read_admin_events("crawler_jobs"))
        return

    handler.send_json({"error": "not found"}, status=HTTPStatus.NOT_FOUND)


def route_post(handler: BaseHTTPRequestHandler, state: ServerState) -> None:
    parsed = urlparse(handler.path)
    payload = handler.read_json()

    if parsed.path == "/auth/device":
        handler.send_json(start_device_authorization())
        return

    if parsed.path == "/auth/token":
        token = exchange_device_code(str(payload.get("device_code") or ""))
        if token.get("error"):
            status = HTTPStatus.BAD_REQUEST
            if token.get("error") in {"authorization_pending", "slow_down"}:
                status = HTTPStatus.BAD_REQUEST
            handler.send_json(token, status=status)
            return
        handler.send_json(token)
        return

    if parsed.path == "/suggest":
        query = str(payload.get("query", ""))
        max_results = int(payload.get("max_results", 10))
        ctx = RetrievalContext.from_env(state.storage)
        handler.send_json(
            {
                "results": retrieval_suggest(
                    ctx,
                    query,
                    max_results,
                    fingerprint=str(payload.get("project_fingerprint", "")),
                ),
                "stale_libraries": stale_libraries_from_payload(state.storage, payload),
            }
        )
        return

    if parsed.path == "/search":
        query = str(payload.get("query", ""))
        library_scope = payload.get("library_scope")
        max_results = int(payload.get("max_results", 20))
        ctx = RetrievalContext.from_env(state.storage)
        results = retrieval_search(
            ctx,
            query,
            library_scope=library_scope,
            max_results=max_results,
            fingerprint=str(payload.get("project_fingerprint", "")),
        )
        libraries_to_pull = retrieval_unique_libraries_to_pull(results)
        handler.send_json(
            {
                "results": results,
                "libraries_to_pull": libraries_to_pull,
                "stale_libraries": stale_libraries_from_payload(state.storage, payload),
            }
        )
        return

    if parsed.path == "/index-request":
        requesting_user = str(payload.get("requesting_user", "local"))
        if not index_request_allowed(state.storage, requesting_user):
            handler.send_json({"error": "rate limited"}, status=HTTPStatus.TOO_MANY_REQUESTS)
            return
        event = {
            "created_at": now(),
            "library_name": payload.get("library_name"),
            "vendor_hint": payload.get("vendor_hint"),
            "source_url_hint": payload.get("source_url_hint"),
            "requesting_user": requesting_user,
        }
        state.storage.append_admin_event("index_requests", event)
        handler.send_json({"ok": True})
        return

    if parsed.path == "/crawler/enqueue":
        event = {
            "created_at": now(),
            "status": "queued",
            "library_name": payload.get("library_name"),
            "vendor": payload.get("vendor"),
            "source_url": payload.get("source_url"),
        }
        state.storage.append_admin_event("crawler_jobs", event)
        handler.send_json({"ok": True, "job": event})
        return

    if parsed.path == "/telemetry":
        telemetry = sanitize_telemetry(payload)
        event = {
            "created_at": now(),
            "event": telemetry["event"],
            "properties": telemetry["properties"],
        }
        state.storage.append_admin_event("telemetry", event)
        handler.send_json({"ok": True})
        return

    handler.send_json({"error": "not found"}, status=HTTPStatus.NOT_FOUND)


def bulk_refs_payload(state: ServerState, query: str) -> dict[str, Any]:
    params = parse_qs(query)
    stale_libraries: list[dict[str, Any]] = []
    for raw in params.get("library", []):
        parsed = parse_pulled_library(raw)
        if parsed is None:
            continue
        vendor, library, version = parsed
        entry = retrieval_latest_entry(state.storage, vendor, library)
        if entry is None:
            continue
        newer_version = str(entry.get("version") or "")
        if newer_version and newer_version != version:
            stale_libraries.append(
                {
                    "vendor": vendor,
                    "library": library,
                    "version": version,
                    "newer_version": newer_version,
                    "ref_sha": entry.get("ref_sha"),
                }
            )
    return {
        "stale_libraries": stale_libraries,
        "fingerprint": params.get("fingerprint", [""])[0],
        "catalog_generated_at": read_catalog_generated_at(state),
    }


def parse_pulled_library(value: str) -> tuple[str, str, str] | None:
    if "@" not in value or "/" not in value:
        return None
    name, version = value.rsplit("@", 1)
    vendor, library = name.split("/", 1)
    if not vendor or not library or not version:
        return None
    return vendor, library, version


def suggest(state: ServerState, query: str, max_results: int) -> list[dict[str, Any]]:
    terms = normalize_query(query)
    rows: list[tuple[int, dict[str, Any]]] = []
    for entry in load_catalog(state):
        haystack = " ".join(
            [
                entry.get("vendor", ""),
                entry.get("library", ""),
                entry.get("version", ""),
                entry.get("description", ""),
                " ".join(entry.get("keywords", [])),
            ]
        ).lower()
        score = sum(haystack.count(term) for term in terms)
        if score:
            rows.append((score, entry))
    rows.sort(key=lambda item: (-item[0], item[1].get("vendor", ""), item[1].get("library", "")))
    return [
        {
            "vendor": entry["vendor"],
            "library": entry["library"],
            "version": entry["version"],
            "score": score,
            "reason": entry.get("description", ""),
        }
        for score, entry in rows[:max_results]
    ]


def search(
    state: ServerState,
    query: str,
    *,
    library_scope: str | None,
    max_results: int,
) -> list[dict[str, Any]]:
    terms = normalize_query(query)
    scope_vendor, scope_library = parse_scope(library_scope)
    hits: list[dict[str, Any]] = []

    for fixture in state.fixtures_root.glob("*/*/*"):
        if not fixture.is_dir():
            continue
        vendor, library, version = fixture.parts[-3:]
        if scope_vendor and (vendor != scope_vendor or library != scope_library):
            continue
        chunk_path = fixture / "_chunks.jsonl"
        if chunk_path.exists():
            for row in read_jsonl(chunk_path):
                normalized = str(row.get("text", "")).lower()
                score = sum(1 for term in terms if term in normalized)
                if score == 0:
                    continue
                hits.append(
                    {
                        "path": f".codo/vendors/{vendor}/{library}@{version}/{row.get('path')}",
                        "line": 1,
                        "score": score,
                        "library": f"{vendor}/{library}",
                        "vendor": vendor,
                        "version": version,
                    }
                )
            continue
        for path in fixture.rglob("*.md"):
            relative = path.relative_to(fixture)
            for line_number, line in enumerate(path.read_text(encoding="utf-8").splitlines(), start=1):
                normalized = line.lower()
                score = sum(1 for term in terms if term in normalized)
                if score == 0:
                    continue
                hits.append(
                    {
                        "path": f".codo/vendors/{vendor}/{library}@{version}/{relative.as_posix()}",
                        "line": line_number,
                        "score": score,
                        "library": f"{vendor}/{library}",
                        "vendor": vendor,
                        "version": version,
                    }
                )

    hits.sort(key=lambda hit: (-hit["score"], hit["path"], hit["line"]))
    return hits[:max_results]


def unique_libraries_to_pull(results: list[dict[str, Any]]) -> list[dict[str, str]]:
    seen: set[tuple[str, str, str]] = set()
    output: list[dict[str, str]] = []
    for result in results:
        vendor = result["vendor"]
        library = result["library"].split("/", 1)[1]
        version = result["version"]
        key = (vendor, library, version)
        if key in seen:
            continue
        seen.add(key)
        output.append({"vendor": vendor, "library": library, "version": version})
    return output


def latest_entry(state: ServerState, vendor: str, library: str) -> dict[str, Any] | None:
    matches = [
        entry
        for entry in load_catalog(state)
        if entry.get("vendor") == vendor and entry.get("library") == library
    ]
    if not matches:
        return None
    matches.sort(key=lambda entry: entry.get("version", ""))
    return matches[-1]


def load_catalog(state: ServerState) -> list[dict[str, Any]]:
    if not state.catalog_path.exists():
        return discover_catalog(state)
    data = json.loads(state.catalog_path.read_text(encoding="utf-8"))
    return list(data.get("libraries", []))


def discover_catalog(state: ServerState) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for fixture in state.fixtures_root.glob("*/*/*"):
        if not fixture.is_dir():
            continue
        vendor, library, version = fixture.parts[-3:]
        description = read_description(fixture, library)
        rows.append(
            {
                "vendor": vendor,
                "library": library,
                "version": version,
                "description": description,
                "keywords": normalize_query(description),
                "fixture_path": str(fixture.relative_to(state.repo_root)),
                "pack_path": None,
                "ref_sha": "local",
            }
        )
    return rows


def read_description(fixture: Path, library: str) -> str:
    readme = fixture / "README.md"
    if readme.exists():
        for line in readme.read_text(encoding="utf-8").splitlines():
            stripped = line.strip()
            if stripped and not stripped.startswith("#"):
                return stripped
    return f"{library} documentation"


def normalize_query(query: str) -> list[str]:
    terms: list[str] = []
    current: list[str] = []
    for char in query.lower():
        if char.isalnum() or char == "_":
            current.append(char)
        elif current:
            terms.append("".join(current))
            current.clear()
    if current:
        terms.append("".join(current))
    return terms


def parse_scope(scope: str | None) -> tuple[str | None, str | None]:
    if not scope:
        return None, None
    if "/" not in scope:
        return "npm", scope
    vendor, library = scope.split("/", 1)
    return vendor, library


def append_jsonl(path: Path, event: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8") as file:
        file.write(json.dumps(event, sort_keys=True) + "\n")


def read_jsonl(path: Path) -> list[dict[str, Any]]:
    if not path.exists():
        return []
    rows: list[dict[str, Any]] = []
    for line in path.read_text(encoding="utf-8").splitlines():
        if line.strip():
            rows.append(json.loads(line))
    return rows


def now() -> str:
    return datetime.now(timezone.utc).isoformat()


def main() -> None:
    parser = argparse.ArgumentParser(description="Run the local Oz registry API.")
    parser.add_argument("--repo-root", type=Path, default=Path.cwd())
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--port", type=int, default=8765)
    parser.add_argument("--require-auth", action="store_true")
    parser.add_argument("--bearer-token", default="local-dev-token")
    args = parser.parse_args()

    state = ServerState(
        repo_root=args.repo_root.resolve(),
        require_auth=args.require_auth,
        bearer_token=args.bearer_token,
    )
    server = ThreadingHTTPServer((args.host, args.port), build_handler(state))
    print(f"oz-api listening on http://{args.host}:{args.port}")
    server.serve_forever()


if __name__ == "__main__":
    main()
