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

from oz_api.admin import esc, render_admin
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
from oz_api.queue import crawler_job_event, enqueue_crawler_job, missing_required_crawler_fields
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
    return (bool(state.bearer_token) and token == state.bearer_token) or (token is not None and verify_token(token))


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
        handler.send_html(render_admin(state.storage))
        return

    if parsed.path == "/admin/enqueue-crawl":
        params = parse_qs(parsed.query)
        payload = {
            "library_name": params.get("library_name", [""])[0],
            "vendor": params.get("vendor", [""])[0],
            "source_url": params.get("source_url", [""])[0],
        }
        missing = missing_required_crawler_fields(crawler_job_event(payload))
        if missing:
            handler.send_html(
                f"<!doctype html><p>Missing crawler job fields: {esc(', '.join(missing))}</p>",
                status=HTTPStatus.BAD_REQUEST,
            )
            return
        enqueue_crawler_job(state.storage, payload)
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
        missing = missing_required_crawler_fields(crawler_job_event(payload))
        if missing:
            handler.send_json(
                {"error": "missing crawler job fields", "fields": missing},
                status=HTTPStatus.BAD_REQUEST,
            )
            return
        event = enqueue_crawler_job(state.storage, payload)
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
