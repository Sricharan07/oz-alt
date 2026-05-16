from __future__ import annotations

import argparse
import json
from dataclasses import dataclass
from datetime import datetime, timezone
from http import HTTPStatus
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from typing import Any
from urllib.parse import parse_qs, urlparse


@dataclass(frozen=True)
class ServerState:
    repo_root: Path
    require_auth: bool = False
    bearer_token: str = "local-dev-token"

    @property
    def registry_root(self) -> Path:
        return self.repo_root / "registry"

    @property
    def fixtures_root(self) -> Path:
        return self.registry_root / "fixtures"

    @property
    def packs_root(self) -> Path:
        return self.registry_root / "packs"

    @property
    def catalog_path(self) -> Path:
        return self.registry_root / "catalog.json"

    @property
    def admin_root(self) -> Path:
        return self.registry_root / "admin"


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
    expected = f"Bearer {state.bearer_token}"
    return handler.headers.get("Authorization") == expected


def render_admin(state: ServerState) -> str:
    catalog = load_catalog(state)
    index_requests = read_jsonl(state.admin_root / "index_requests.jsonl")
    telemetry = read_jsonl(state.admin_root / "telemetry.jsonl")
    crawler_jobs = read_jsonl(state.admin_root / "crawler_jobs.jsonl")
    rows = "\n".join(
        f"<tr><td>{entry.get('vendor')}/{entry.get('library')}</td><td>{entry.get('version')}</td><td>{entry.get('description','')}</td></tr>"
        for entry in catalog
    )
    return f"""<!doctype html>
<html>
<head>
  <meta charset="utf-8">
  <title>Oz Admin</title>
  <style>
    body {{ font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif; margin: 32px; color: #172026; }}
    h1 {{ font-size: 24px; }}
    h2 {{ margin-top: 28px; font-size: 16px; }}
    table {{ border-collapse: collapse; width: 100%; }}
    th, td {{ border-bottom: 1px solid #d8dee4; padding: 8px; text-align: left; font-size: 14px; }}
    .metric {{ display: inline-block; margin-right: 24px; font-size: 14px; }}
  </style>
</head>
<body>
  <h1>Oz Admin</h1>
  <div class="metric">Libraries: {len(catalog)}</div>
  <div class="metric">Index requests: {len(index_requests)}</div>
  <div class="metric">Telemetry events: {len(telemetry)}</div>
  <div class="metric">Crawler jobs: {len(crawler_jobs)}</div>
  <h2>Library Catalog</h2>
  <table><thead><tr><th>Library</th><th>Version</th><th>Description</th></tr></thead><tbody>{rows}</tbody></table>
  <h2>Queues</h2>
  <p><a href="/admin/index-requests">Index requests JSON</a> · <a href="/admin/crawler-jobs">Crawler jobs JSON</a> · <a href="/admin/telemetry">Telemetry JSON</a></p>
</body>
</html>"""


def read_catalog_generated_at(state: ServerState) -> str | None:
    if not state.catalog_path.exists():
        return None
    data = json.loads(state.catalog_path.read_text(encoding="utf-8"))
    return data.get("generated_at")


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

    if parsed.path == "/refs":
        handler.send_json(
            {
                "stale_libraries": [],
                "fingerprint": parse_qs(parsed.query).get("fingerprint", [""])[0],
                "catalog_generated_at": read_catalog_generated_at(state),
            }
        )
        return

    if len(parts) == 3 and parts[0] == "refs":
        vendor, library = parts[1], parts[2]
        entry = latest_entry(state, vendor, library)
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
        pack_path = state.packs_root / vendor / library / f"{version}.ozpack"
        if not pack_path.exists():
            handler.send_json({"error": "pack not found"}, status=HTTPStatus.NOT_FOUND)
            return
        handler.send_bytes(pack_path.read_bytes(), content_type="application/vnd.oz.pack")
        return

    if parsed.path == "/admin/index-requests":
        handler.send_json(read_jsonl(state.admin_root / "index_requests.jsonl"))
        return

    if parsed.path == "/admin/telemetry":
        handler.send_json(read_jsonl(state.admin_root / "telemetry.jsonl"))
        return

    if parsed.path == "/admin/crawler-jobs":
        handler.send_json(read_jsonl(state.admin_root / "crawler_jobs.jsonl"))
        return

    handler.send_json({"error": "not found"}, status=HTTPStatus.NOT_FOUND)


def route_post(handler: BaseHTTPRequestHandler, state: ServerState) -> None:
    parsed = urlparse(handler.path)
    payload = handler.read_json()

    if parsed.path == "/auth/device":
        handler.send_json(
            {
                "device_code": "local-device-code",
                "user_code": "LOCAL-OZ",
                "verification_uri": "http://127.0.0.1:8765/auth/verify",
                "interval": 1,
                "expires_in": 600,
            }
        )
        return

    if parsed.path == "/auth/token":
        if payload.get("device_code") != "local-device-code":
            handler.send_json({"error": "invalid device_code"}, status=HTTPStatus.BAD_REQUEST)
            return
        handler.send_json(
            {
                "access_token": "local-dev-token",
                "token_type": "Bearer",
                "expires_in": 86400,
            }
        )
        return

    if parsed.path == "/suggest":
        query = str(payload.get("query", ""))
        max_results = int(payload.get("max_results", 10))
        handler.send_json({"results": suggest(state, query, max_results), "stale_libraries": []})
        return

    if parsed.path == "/search":
        query = str(payload.get("query", ""))
        library_scope = payload.get("library_scope")
        max_results = int(payload.get("max_results", 20))
        results = search(state, query, library_scope=library_scope, max_results=max_results)
        libraries_to_pull = unique_libraries_to_pull(results)
        handler.send_json({"results": results, "libraries_to_pull": libraries_to_pull, "stale_libraries": []})
        return

    if parsed.path == "/index-request":
        event = {
            "created_at": now(),
            "library_name": payload.get("library_name"),
            "vendor_hint": payload.get("vendor_hint"),
            "source_url_hint": payload.get("source_url_hint"),
            "requesting_user": payload.get("requesting_user", "local"),
        }
        append_jsonl(state.admin_root / "index_requests.jsonl", event)
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
        append_jsonl(state.admin_root / "crawler_jobs.jsonl", event)
        handler.send_json({"ok": True, "job": event})
        return

    if parsed.path == "/telemetry":
        event = {
            "created_at": now(),
            "event": payload.get("event"),
            "properties": payload.get("properties", {}),
        }
        append_jsonl(state.admin_root / "telemetry.jsonl", event)
        handler.send_json({"ok": True})
        return

    handler.send_json({"error": "not found"}, status=HTTPStatus.NOT_FOUND)


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
