from __future__ import annotations

import argparse
import json
import os
from dataclasses import dataclass
from datetime import datetime, timezone
from http import HTTPStatus
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from typing import Any
from urllib.parse import parse_qs, urlparse

from oz_api.admin import esc, load_admin_snapshot, render_admin
from oz_api.admin_ops import approve_crawl, log_admin_action, submit_index_request, upsert_library_profile
from oz_api.auth import (
    AuthError,
    SESSION_COOKIE,
    accept_password_token,
    authenticate_password,
    approve_device_code,
    bearer_token,
    change_principal_password,
    create_password_account,
    create_password_invite,
    create_password_reset,
    csrf_token,
    exchange_device_code,
    list_cli_sessions,
    principal_from_bearer,
    principal_from_session,
    production_env,
    refresh_cli_token,
    revoke_cli_session,
    revoke_web_session,
    set_user_disabled,
    start_device_authorization,
    verify_csrf,
)
from oz_api.limits import index_request_allowed, rate_limit_allowed
from oz_api.freshness import stale_libraries_from_payload
from oz_api.metrics import metrics_authorized, render_prometheus_metrics
from oz_api.retrieval import (
    RetrievalContext,
    search as retrieval_search,
    suggest as retrieval_suggest,
    unique_libraries_to_pull as retrieval_unique_libraries_to_pull,
)
from oz_api.queue import crawler_job_event, missing_required_crawler_fields
from oz_api.server_helpers import bulk_refs_payload, cookie_domain, first_form_values, secure_cookie, single_ref_payload
from oz_api.storage import RegistryStorage
from oz_api.telemetry import sanitize_telemetry
from oz_api.usage import record_telemetry_event, record_usage_event, usage_summary
from oz_api.web_pages import (
    admin_result_page,
    cookie_header,
    public_markdown_html,
    render_account_page,
    render_dashboard,
    render_device_page,
    render_login_page,
    render_password_token_page,
    render_signup_page,
    status_page,
)


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


def build_handler(state: ServerState) -> type[BaseHTTPRequestHandler]:
    class OzHandler(BaseHTTPRequestHandler):
        server_version = "oz-api/0.1"

        def do_GET(self) -> None:
            try:
                if not is_authorized(self, state):
                    path = urlparse(self.path).path
                    if path.startswith("/admin") or path in {"/dashboard", "/device", "/account"}:
                        self.send_html(render_login_page(), status=HTTPStatus.UNAUTHORIZED)
                    else:
                        self.send_json({"error": "unauthorized"}, status=HTTPStatus.UNAUTHORIZED)
                    return
                route_get(self, state)
            except Exception as exc:  # pragma: no cover - defensive server boundary
                self.send_json({"error": str(exc)}, status=HTTPStatus.INTERNAL_SERVER_ERROR)

        def do_POST(self) -> None:
            try:
                if not request_rate_limit_allowed(self):
                    self.send_json({"error": "rate limited"}, status=HTTPStatus.TOO_MANY_REQUESTS)
                    return
                if not is_authorized(self, state):
                    self.send_json({"error": "unauthorized"}, status=HTTPStatus.UNAUTHORIZED)
                    return
                route_post(self, state)
            except Exception as exc:  # pragma: no cover - defensive server boundary
                self.send_json({"error": str(exc)}, status=HTTPStatus.INTERNAL_SERVER_ERROR)

        def read_body(self) -> str:
            length = int(self.headers.get("Content-Length", "0"))
            if length == 0:
                return ""
            return self.rfile.read(length).decode("utf-8")

        def read_json(self) -> dict[str, Any]:
            body = self.read_body()
            if not body:
                return {}
            return json.loads(body)

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

        def send_redirect(self, location: str, *, cookies: list[str] | None = None) -> None:
            self.send_response(HTTPStatus.FOUND)
            self.send_header("Location", location)
            self.send_header("Cache-Control", "public, max-age=31536000, immutable")
            for cookie in cookies or []:
                self.send_header("Set-Cookie", cookie)
            self.end_headers()

        def send_html(self, html: str, *, status: HTTPStatus = HTTPStatus.OK) -> None:
            body = html.encode("utf-8")
            self.send_response(status)
            self.send_header("Content-Type", "text/html; charset=utf-8")
            self.send_header("Content-Length", str(len(body)))
            self.end_headers()
            self.wfile.write(body)

        def send_text(
            self,
            text: str,
            *,
            content_type: str = "text/plain; charset=utf-8",
            status: HTTPStatus = HTTPStatus.OK,
        ) -> None:
            body = text.encode("utf-8")
            self.send_response(status)
            self.send_header("Content-Type", content_type)
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
    if path in {
        "/health",
        "/catalog",
        "/privacy",
        "/terms",
        "/status",
        "/metrics",
        "/login",
        "/login/",
        "/signup",
        "/signup/",
        "/invite",
        "/invite/",
        "/reset-password",
        "/reset-password/",
        "/dashboard",
        "/dashboard/",
        "/device",
        "/device/",
        "/auth/device",
        "/auth/device/start",
        "/auth/token",
        "/auth/device/token",
        "/auth/refresh",
    }:
        return True
    token = bearer_token(handler.headers)
    if path.startswith("/admin"):
        principal = principal_for_handler(handler)
        return (bool(state.bearer_token) and token == state.bearer_token) or (
            principal is not None and principal.is_admin
        )
    return (bool(state.bearer_token) and token == state.bearer_token) or principal_for_handler(handler) is not None


def request_rate_limit_allowed(handler: BaseHTTPRequestHandler) -> bool:
    path = urlparse(handler.path).path
    identity = handler.client_address[0] if handler.client_address else "unknown"
    if path.startswith("/admin"):
        return rate_limit_allowed(f"admin:{path}", identity, limit=60, window_seconds=60) or not production_env()
    if path in {"/suggest", "/search"}:
        return rate_limit_allowed(f"api:{path}", identity, limit=120, window_seconds=60) or not production_env()
    if path.startswith("/auth/") or path in {"/login", "/signup", "/invite", "/reset-password"}:
        return rate_limit_allowed(f"auth:{path}", identity, limit=30, window_seconds=60) or not production_env()
    return rate_limit_allowed(f"post:{path}", identity, limit=120, window_seconds=60) or not production_env()


def principal_for_handler(handler: BaseHTTPRequestHandler):
    return principal_from_bearer(handler.headers) or principal_from_session(cookie_token(handler, SESSION_COOKIE))


def cookie_token(handler: BaseHTTPRequestHandler, name: str) -> str | None:
    prefix = f"{name}="
    for part in (handler.headers.get("Cookie") or "").split(";"):
        cookie = part.strip()
        if cookie.startswith(prefix):
            return cookie[len(prefix) :]
    return None


def route_get(handler: BaseHTTPRequestHandler, state: ServerState) -> None:
    parsed = urlparse(handler.path)
    path = parsed.path.strip("/")
    parts = path.split("/") if path else []
    principal = principal_for_handler(handler)

    if parsed.path == "/health":
        handler.send_json({"ok": True, "service": "oz-api"})
        return

    if parsed.path == "/catalog":
        handler.send_json(state.storage.load_catalog_document())
        return

    if parsed.path in {"/privacy", "/terms"}:
        handler.send_html(public_markdown_html(parsed.path))
        return

    if parsed.path == "/status":
        handler.send_html(status_page())
        return

    if parsed.path == "/metrics":
        if not metrics_authorized(handler.headers):
            handler.send_json({"error": "not found"}, status=HTTPStatus.NOT_FOUND)
            return
        handler.send_text(render_prometheus_metrics(), content_type="text/plain; version=0.0.4; charset=utf-8")
        return

    if parsed.path in {"/login", "/login/"}:
        handler.send_html(render_login_page())
        return

    if parsed.path in {"/signup", "/signup/"}:
        handler.send_html(render_signup_page())
        return

    if parsed.path in {"/invite", "/invite/", "/reset-password", "/reset-password/"}:
        params = parse_qs(parsed.query)
        token = params.get("token", [""])[0]
        handler.send_html(render_password_token_page(token, reset=parsed.path.startswith("/reset-password")))
        return

    if parsed.path in {"/dashboard", "/dashboard/"}:
        if principal is None:
            handler.send_html(render_login_page(), status=HTTPStatus.UNAUTHORIZED)
            return
        handler.send_html(render_dashboard(principal, usage_summary(principal)))
        return

    if parsed.path in {"/account", "/account/"}:
        if principal is None:
            handler.send_html(render_login_page("Sign in before opening account settings."), status=HTTPStatus.UNAUTHORIZED)
            return
        handler.send_html(
            render_account_page(
                principal,
                csrf=csrf_token(cookie_token(handler, SESSION_COOKIE)),
                cli_sessions=list_cli_sessions(principal),
            )
        )
        return

    if parsed.path in {"/device", "/device/"}:
        if principal is None:
            handler.send_html(render_login_page("Sign in before approving a CLI device."), status=HTTPStatus.UNAUTHORIZED)
            return
        params = parse_qs(parsed.query)
        session = cookie_token(handler, SESSION_COOKIE)
        handler.send_html(render_device_page(principal, params.get("code", [""])[0], csrf=csrf_token(session)))
        return

    if parsed.path == "/admin/logout":
        revoke_web_session(cookie_token(handler, SESSION_COOKIE))
        handler.send_redirect(
            "/dashboard",
            cookies=[
                cookie_header(
                    SESSION_COOKIE,
                    "",
                    path="/",
                    max_age=0,
                    http_only=True,
                    secure=secure_cookie(),
                    domain=cookie_domain(),
                )
            ],
        )
        return

    if parsed.path in {"/admin", "/admin/"}:
        handler.send_html(render_admin(state.storage, csrf=csrf_token(cookie_token(handler, SESSION_COOKIE))))
        return

    if parsed.path == "/admin/enqueue-crawl":
        handler.send_html("<!doctype html><p>Use the admin approve form.</p>", status=HTTPStatus.METHOD_NOT_ALLOWED)
        return

    if parsed.path == "/refs":
        handler.send_json(bulk_refs_payload(state, parsed.query))
        return

    if len(parts) == 3 and parts[0] == "refs":
        vendor, library = parts[1], parts[2]
        payload = single_ref_payload(state, vendor, library)
        if payload is None:
            handler.send_json({"error": "library not indexed"}, status=HTTPStatus.NOT_FOUND)
            return
        handler.send_json(payload)
        return

    if len(parts) == 4 and parts[0] == "pack":
        _, vendor, library, version = parts
        record_usage_event(principal, "pack_download", library=f"{vendor}/{library}@{version}")
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
        handler.send_json(load_admin_snapshot(state.storage)["index_requests"])
        return

    if parsed.path == "/admin/telemetry":
        handler.send_json(load_admin_snapshot(state.storage)["telemetry"])
        return

    if parsed.path == "/admin/crawler-jobs":
        handler.send_json(load_admin_snapshot(state.storage)["crawler_jobs"])
        return

    if parsed.path == "/admin/usage":
        handler.send_json(load_admin_snapshot(state.storage)["usage_events"])
        return

    if parsed.path == "/admin/actions":
        handler.send_json(load_admin_snapshot(state.storage)["admin_actions"])
        return

    if parsed.path == "/admin/promotions":
        handler.send_json(load_admin_snapshot(state.storage)["promotions"])
        return

    if parsed.path == "/admin/freshness":
        handler.send_json(load_admin_snapshot(state.storage)["freshness_policies"])
        return

    if parsed.path == "/admin/quality":
        handler.send_json(load_admin_snapshot(state.storage)["quality_runs"])
        return

    if parsed.path == "/admin/evals":
        handler.send_json(load_admin_snapshot(state.storage)["eval_runs"])
        return

    if parsed.path == "/admin/packs":
        handler.send_json(load_admin_snapshot(state.storage)["pack_builds"])
        return

    handler.send_json({"error": "not found"}, status=HTTPStatus.NOT_FOUND)


def route_post(handler: BaseHTTPRequestHandler, state: ServerState) -> None:
    parsed = urlparse(handler.path)

    if parsed.path in {"/login", "/login/"}:
        form = parse_qs(handler.read_body())
        email = form.get("email", [""])[0]
        password = form.get("password", [""])[0]
        try:
            session, _principal = authenticate_password(
                email,
                password,
                ip=handler.client_address[0] if handler.client_address else "",
                user_agent=handler.headers.get("User-Agent", ""),
            )
        except (AuthError, RuntimeError) as exc:
            handler.send_html(render_login_page(str(exc)), status=HTTPStatus.BAD_REQUEST)
            return
        handler.send_redirect(
            "/dashboard",
            cookies=[
                cookie_header(
                    SESSION_COOKIE,
                    session,
                    path="/",
                    max_age=30 * 24 * 60 * 60,
                    http_only=True,
                    secure=secure_cookie(),
                    domain=cookie_domain(),
                )
            ],
        )
        return

    if parsed.path in {"/signup", "/signup/"}:
        form = parse_qs(handler.read_body())
        email = form.get("email", [""])[0]
        password = form.get("password", [""])[0]
        confirm = form.get("confirm_password", [""])[0]
        if password != confirm:
            handler.send_html(render_signup_page("passwords_do_not_match"), status=HTTPStatus.BAD_REQUEST)
            return
        try:
            session, _principal = create_password_account(
                email,
                password,
                ip=handler.client_address[0] if handler.client_address else "",
                user_agent=handler.headers.get("User-Agent", ""),
            )
        except (AuthError, RuntimeError) as exc:
            handler.send_html(render_signup_page(str(exc)), status=HTTPStatus.BAD_REQUEST)
            return
        handler.send_redirect(
            "/dashboard",
            cookies=[
                cookie_header(
                    SESSION_COOKIE,
                    session,
                    path="/",
                    max_age=30 * 24 * 60 * 60,
                    http_only=True,
                    secure=secure_cookie(),
                    domain=cookie_domain(),
                )
            ],
        )
        return

    if parsed.path in {"/invite", "/invite/", "/reset-password", "/reset-password/"}:
        form = parse_qs(handler.read_body())
        token = form.get("token", [""])[0]
        password = form.get("password", [""])[0]
        confirm = form.get("confirm_password", [""])[0]
        reset = parsed.path.startswith("/reset-password")
        if password != confirm:
            handler.send_html(render_password_token_page(token, error="passwords_do_not_match", reset=reset), status=HTTPStatus.BAD_REQUEST)
            return
        try:
            session, _principal = accept_password_token(
                token,
                password,
                ip=handler.client_address[0] if handler.client_address else "",
                user_agent=handler.headers.get("User-Agent", ""),
            )
        except (AuthError, RuntimeError) as exc:
            handler.send_html(render_password_token_page(token, error=str(exc), reset=reset), status=HTTPStatus.BAD_REQUEST)
            return
        handler.send_redirect(
            "/dashboard",
            cookies=[
                cookie_header(
                    SESSION_COOKIE,
                    session,
                    path="/",
                    max_age=30 * 24 * 60 * 60,
                    http_only=True,
                    secure=secure_cookie(),
                    domain=cookie_domain(),
                )
            ],
        )
        return

    if parsed.path in {"/account/password", "/account/password/"}:
        principal = principal_for_handler(handler)
        if principal is None:
            handler.send_html(render_login_page("Sign in before changing password."), status=HTTPStatus.UNAUTHORIZED)
            return
        form = parse_qs(handler.read_body())
        session = cookie_token(handler, SESSION_COOKIE)
        if not verify_csrf(session, form.get("csrf", [""])[0]):
            handler.send_html(
                render_account_page(
                    principal,
                    csrf=csrf_token(session),
                    error="Invalid CSRF token.",
                    cli_sessions=list_cli_sessions(principal),
                ),
                status=HTTPStatus.FORBIDDEN,
            )
            return
        current = form.get("current_password", [""])[0]
        new_password = form.get("new_password", [""])[0]
        confirm = form.get("confirm_password", [""])[0]
        if new_password != confirm:
            handler.send_html(
                render_account_page(
                    principal,
                    csrf=csrf_token(session),
                    error="passwords_do_not_match",
                    cli_sessions=list_cli_sessions(principal),
                ),
                status=HTTPStatus.BAD_REQUEST,
            )
            return
        try:
            change_principal_password(
                principal,
                current,
                new_password,
                ip=handler.client_address[0] if handler.client_address else "",
                user_agent=handler.headers.get("User-Agent", ""),
            )
        except (AuthError, RuntimeError) as exc:
            handler.send_html(
                render_account_page(
                    principal,
                    csrf=csrf_token(session),
                    error=str(exc),
                    cli_sessions=list_cli_sessions(principal),
                ),
                status=HTTPStatus.BAD_REQUEST,
            )
            return
        handler.send_html(
            render_account_page(
                principal,
                csrf=csrf_token(session),
                message="Password updated.",
                cli_sessions=list_cli_sessions(principal),
            )
        )
        return

    if parsed.path in {"/account/cli-sessions/revoke", "/account/cli-sessions/revoke/"}:
        principal = principal_for_handler(handler)
        if principal is None:
            handler.send_html(render_login_page("Sign in before changing CLI sessions."), status=HTTPStatus.UNAUTHORIZED)
            return
        form = parse_qs(handler.read_body())
        session = cookie_token(handler, SESSION_COOKIE)
        if not verify_csrf(session, form.get("csrf", [""])[0]):
            handler.send_html(render_account_page(principal, csrf=csrf_token(session), error="Invalid CSRF token.", cli_sessions=list_cli_sessions(principal)), status=HTTPStatus.FORBIDDEN)
            return
        try:
            revoke_cli_session(
                principal,
                form.get("token_id", [""])[0],
                ip=handler.client_address[0] if handler.client_address else "",
                user_agent=handler.headers.get("User-Agent", ""),
            )
        except (AuthError, RuntimeError) as exc:
            handler.send_html(render_account_page(principal, csrf=csrf_token(session), error=str(exc), cli_sessions=list_cli_sessions(principal)), status=HTTPStatus.BAD_REQUEST)
            return
        handler.send_html(render_account_page(principal, csrf=csrf_token(session), message="CLI session revoked.", cli_sessions=list_cli_sessions(principal)))
        return

    if parsed.path in {"/device", "/device/"}:
        principal = principal_for_handler(handler)
        if principal is None:
            handler.send_html(render_login_page("Sign in before approving a CLI device."), status=HTTPStatus.UNAUTHORIZED)
            return
        form = parse_qs(handler.read_body())
        session = cookie_token(handler, SESSION_COOKIE)
        if not verify_csrf(session, form.get("csrf", [""])[0]):
            handler.send_html(render_device_page(principal, error="Invalid CSRF token."), status=HTTPStatus.FORBIDDEN)
            return
        code = form.get("user_code", [""])[0]
        try:
            approve_device_code(
                code,
                principal,
                ip=handler.client_address[0] if handler.client_address else "",
                user_agent=handler.headers.get("User-Agent", ""),
            )
        except (AuthError, RuntimeError) as exc:
            handler.send_html(
                render_device_page(principal, code, csrf=csrf_token(session), error=str(exc)),
                status=HTTPStatus.BAD_REQUEST,
            )
            return
        handler.send_html(
            render_device_page(
                principal,
                "",
                csrf=csrf_token(session),
                message="Device approved. You can return to the CLI.",
            )
        )
        return

    if parsed.path == "/admin/enqueue-crawl":
        form = parse_qs(handler.read_body())
        if not verify_csrf(cookie_token(handler, SESSION_COOKIE), form.get("csrf", [""])[0]):
            handler.send_html("<!doctype html><p>Invalid CSRF token.</p>", status=HTTPStatus.FORBIDDEN)
            return
        payload = {
            "library_name": form.get("library_name", [""])[0],
            "vendor": form.get("vendor", [""])[0],
            "source_url": form.get("source_url", [""])[0],
            "version": form.get("version", ["latest"])[0],
            "max_pages": form.get("max_pages", ["128"])[0],
            "recrawl_interval_hours": form.get("recrawl_interval_hours", ["24"])[0],
            "fetcher": form.get("fetcher", [""])[0],
            "concurrent_requests": form.get("concurrent_requests", [""])[0],
            "download_delay": form.get("download_delay", [""])[0],
            "robots_txt": form.get("robots_txt", [""])[0],
        }
        missing = missing_required_crawler_fields(crawler_job_event(payload))
        if missing:
            handler.send_html(
                f"<!doctype html><p>Missing crawler job fields: {esc(', '.join(missing))}</p>",
                status=HTTPStatus.BAD_REQUEST,
            )
            return
        approve_crawl(state.storage, payload, principal_for_handler(handler))
        handler.send_html(
            "<!doctype html><meta http-equiv=\"refresh\" content=\"0; url=/admin\">",
            status=HTTPStatus.ACCEPTED,
        )
        return

    if parsed.path == "/admin/library-profile":
        form = parse_qs(handler.read_body())
        if not verify_csrf(cookie_token(handler, SESSION_COOKIE), form.get("csrf", [""])[0]):
            handler.send_html("<!doctype html><p>Invalid CSRF token.</p>", status=HTTPStatus.FORBIDDEN)
            return
        try:
            upsert_library_profile(first_form_values(form), principal_for_handler(handler))
        except Exception as exc:
            handler.send_html(f"<!doctype html><p>{esc(str(exc))}</p>", status=HTTPStatus.BAD_REQUEST)
            return
        handler.send_html(
            "<!doctype html><meta http-equiv=\"refresh\" content=\"0; url=/admin\">",
            status=HTTPStatus.ACCEPTED,
        )
        return

    if parsed.path == "/admin/users/invite":
        form = parse_qs(handler.read_body())
        principal = principal_for_handler(handler)
        if not verify_csrf(cookie_token(handler, SESSION_COOKIE), form.get("csrf", [""])[0]):
            handler.send_html("<!doctype html><p>Invalid CSRF token.</p>", status=HTTPStatus.FORBIDDEN)
            return
        try:
            result = create_password_invite(
                form.get("email", [""])[0],
                form.get("role", ["user"])[0],
                principal,
            )
            log_admin_action(
                principal,
                "password_invite_created",
                target_type="user",
                target=result["email"],
                metadata={"role": result["role"]},
            )
        except (AuthError, RuntimeError) as exc:
            handler.send_html(admin_result_page("Invite failed", str(exc)), status=HTTPStatus.BAD_REQUEST)
            return
        handler.send_html(
            admin_result_page(
                "User invite",
                f"Invite for {esc(result['email'])}",
                link=result["url"],
            )
        )
        return

    if parsed.path == "/admin/users/reset-password":
        form = parse_qs(handler.read_body())
        principal = principal_for_handler(handler)
        if not verify_csrf(cookie_token(handler, SESSION_COOKIE), form.get("csrf", [""])[0]):
            handler.send_html("<!doctype html><p>Invalid CSRF token.</p>", status=HTTPStatus.FORBIDDEN)
            return
        try:
            result = create_password_reset(form.get("email", [""])[0], principal)
            log_admin_action(
                principal,
                "password_reset_created",
                target_type="user",
                target=result["email"],
            )
        except (AuthError, RuntimeError) as exc:
            handler.send_html(admin_result_page("Reset failed", str(exc)), status=HTTPStatus.BAD_REQUEST)
            return
        handler.send_html(
            admin_result_page(
                "Password reset",
                f"Reset link for {esc(result['email'])}",
                link=result["url"],
            )
        )
        return

    if parsed.path in {"/admin/users/disable", "/admin/users/enable"}:
        form = parse_qs(handler.read_body())
        principal = principal_for_handler(handler)
        if not verify_csrf(cookie_token(handler, SESSION_COOKIE), form.get("csrf", [""])[0]):
            handler.send_html("<!doctype html><p>Invalid CSRF token.</p>", status=HTTPStatus.FORBIDDEN)
            return
        disabled = parsed.path.endswith("/disable")
        try:
            user = set_user_disabled(form.get("email", [""])[0], disabled, principal)
            log_admin_action(
                principal,
                "user_disabled" if disabled else "user_enabled",
                target_type="user",
                target=user.email,
            )
        except (AuthError, RuntimeError) as exc:
            handler.send_html(admin_result_page("User update failed", str(exc)), status=HTTPStatus.BAD_REQUEST)
            return
        handler.send_html(
            "<!doctype html><meta http-equiv=\"refresh\" content=\"0; url=/admin\">",
            status=HTTPStatus.ACCEPTED,
        )
        return

    payload = handler.read_json()

    if parsed.path in {"/auth/device", "/auth/device/start"}:
        try:
            handler.send_json(
                start_device_authorization(
                    ip=handler.client_address[0] if handler.client_address else "",
                    user_agent=handler.headers.get("User-Agent", ""),
                )
            )
        except (AuthError, RuntimeError) as exc:
            status = HTTPStatus.TOO_MANY_REQUESTS if str(exc) == "rate_limited" else HTTPStatus.BAD_REQUEST
            handler.send_json({"error": str(exc)}, status=status)
        return

    if parsed.path in {"/auth/token", "/auth/device/token"}:
        token = exchange_device_code(
            str(payload.get("device_code") or ""),
            machine_id=str(payload.get("machine_id") or ""),
        )
        if token.get("error"):
            status = HTTPStatus.BAD_REQUEST
            if token.get("error") in {"authorization_pending", "slow_down"}:
                status = HTTPStatus.PRECONDITION_REQUIRED
            handler.send_json(token, status=status)
            return
        handler.send_json(token)
        return

    if parsed.path == "/auth/refresh":
        token = refresh_cli_token(str(payload.get("refresh_token") or ""))
        if token.get("error"):
            handler.send_json(token, status=HTTPStatus.UNAUTHORIZED)
            return
        handler.send_json(token)
        return

    if parsed.path == "/auth/logout":
        revoke_web_session(cookie_token(handler, SESSION_COOKIE))
        handler.send_json({"ok": True})
        return

    if parsed.path == "/auth/device/approve":
        principal = principal_for_handler(handler)
        if principal is None:
            handler.send_json({"error": "unauthorized"}, status=HTTPStatus.UNAUTHORIZED)
            return
        try:
            handler.send_json(
                approve_device_code(
                    str(payload.get("user_code") or ""),
                    principal,
                    ip=handler.client_address[0] if handler.client_address else "",
                    user_agent=handler.headers.get("User-Agent", ""),
                )
            )
        except (AuthError, RuntimeError) as exc:
            handler.send_json({"error": str(exc)}, status=HTTPStatus.BAD_REQUEST)
        return

    if parsed.path == "/suggest":
        query = str(payload.get("query", ""))
        max_results = int(payload.get("max_results", 10))
        ctx = RetrievalContext.from_env(state.storage)
        results = retrieval_suggest(
            ctx,
            query,
            max_results,
            fingerprint=str(payload.get("project_fingerprint", "")),
        )
        record_usage_event(
            principal_for_handler(handler),
            "suggest",
            query_length=len(query),
            result_count=len(results),
            project_fingerprint=str(payload.get("project_fingerprint", "")),
        )
        handler.send_json(
            {
                "results": results,
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
        record_usage_event(
            principal_for_handler(handler),
            "search",
            library=str(library_scope or "") or None,
            query_length=len(query),
            result_count=len(results),
            project_fingerprint=str(payload.get("project_fingerprint", "")),
        )
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
        if not index_request_allowed(requesting_user):
            handler.send_json({"error": "rate limited"}, status=HTTPStatus.TOO_MANY_REQUESTS)
            return
        request = submit_index_request(
            state.storage,
            payload,
            principal_for_handler(handler),
            fallback_user=requesting_user,
        )
        handler.send_json({"ok": True, "request": request})
        return

    if parsed.path == "/crawler/enqueue":
        missing = missing_required_crawler_fields(crawler_job_event(payload))
        if missing:
            handler.send_json(
                {"error": "missing crawler job fields", "fields": missing},
                status=HTTPStatus.BAD_REQUEST,
            )
            return
        event = approve_crawl(state.storage, payload, principal_for_handler(handler))
        handler.send_json({"ok": True, "job": event})
        return

    if parsed.path == "/telemetry":
        telemetry = sanitize_telemetry(payload)
        principal = principal_for_handler(handler)
        record_telemetry_event(principal, telemetry)
        record_usage_event(
            principal,
            str(telemetry["event"] or "telemetry"),
            library=str(telemetry["properties"].get("library") or telemetry["properties"].get("library_scope") or "") or None,
            query_length=telemetry["properties"].get("query_length"),
            result_count=telemetry["properties"].get("result_count"),
            properties=telemetry["properties"],
        )
        handler.send_json({"ok": True})
        return

    handler.send_json({"error": "not found"}, status=HTTPStatus.NOT_FOUND)


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

    display_host = "127.0.0.1" if args.host in {"0.0.0.0", "::"} else args.host
    os.environ.setdefault("OZ_PUBLIC_BASE_URL", f"http://{display_host}:{args.port}")
    os.environ.setdefault("OZ_APP_URL", f"http://{display_host}:{args.port}")

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
