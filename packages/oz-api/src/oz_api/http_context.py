from __future__ import annotations

import json
import os
from json import JSONDecodeError
from dataclasses import dataclass
from pathlib import Path
from typing import Any
from urllib.parse import parse_qs

from fastapi import HTTPException, Request

from oz_api.auth import (
    SESSION_COOKIE,
    bearer_token,
    principal_from_bearer,
    principal_from_session,
    production_env,
)
from oz_api.limits import rate_limit_allowed
from oz_api.storage import RegistryStorage


PUBLIC_PATHS = {
    "/",
    "/health",
    "/catalog",
    "/privacy",
    "/terms",
    "/status",
    "/status.json",
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
}

HTML_AUTH_PATHS = {
    "/dashboard",
    "/dashboard/",
    "/device",
    "/device/",
    "/account",
    "/account/",
}


class BodyTooLarge(Exception):
    pass


@dataclass(frozen=True)
class ServerState:
    repo_root: Path
    require_auth: bool = False
    bearer_token: str = ""

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


def state_from_request(request: Request) -> ServerState:
    return request.app.state.oz_state


def client_ip(request: Request) -> str:
    forwarded = request.headers.get("x-forwarded-for", "")
    if forwarded:
        return forwarded.split(",", 1)[0].strip()
    return request.client.host if request.client else "unknown"


def principal_for_request(request: Request):
    return principal_from_bearer(request.headers) or principal_from_session(session_cookie(request))


def session_cookie(request: Request) -> str | None:
    return request.cookies.get(SESSION_COOKIE)


def is_authorized_request(request: Request, state: ServerState) -> bool:
    if not state.require_auth:
        return True
    path = request.url.path
    if path in PUBLIC_PATHS or path.startswith("/libraries") or path.startswith("/api/libraries/"):
        return True
    token = bearer_token(request.headers)
    if path.startswith("/admin"):
        principal = principal_for_request(request)
        return (bool(state.bearer_token) and token == state.bearer_token) or (
            principal is not None and principal.is_admin
        )
    return (bool(state.bearer_token) and token == state.bearer_token) or principal_for_request(request) is not None


def unauthorized_is_html(request: Request) -> bool:
    path = request.url.path
    return request.method == "GET" and (path.startswith("/admin") or path in HTML_AUTH_PATHS)


def request_rate_limit_allowed(request: Request) -> bool:
    path = request.url.path
    principal = principal_for_request(request)
    identity = principal.user_id if principal is not None else client_ip(request)
    if path.startswith("/admin"):
        return rate_limit_allowed(f"admin:{path}", identity, limit=60, window_seconds=60) or not production_env()
    if path in {"/suggest", "/search"}:
        return rate_limit_allowed(f"api:{path}", identity, limit=120, window_seconds=60) or not production_env()
    if path.startswith("/auth/") or path in {"/login", "/signup", "/invite", "/reset-password"}:
        return rate_limit_allowed(f"auth:{path}", identity, limit=30, window_seconds=60) or not production_env()
    return rate_limit_allowed(f"post:{path}", identity, limit=120, window_seconds=60) or not production_env()


async def read_json_payload(request: Request) -> dict[str, Any]:
    body = await request.body()
    if len(body) > request_body_limit_bytes():
        raise HTTPException(status_code=413, detail="request body too large")
    if not body:
        return {}
    try:
        payload = json.loads(body)
    except JSONDecodeError as exc:
        raise HTTPException(status_code=400, detail="invalid JSON payload") from exc
    if not isinstance(payload, dict):
        raise HTTPException(status_code=400, detail="JSON payload must be an object")
    return payload


async def read_form_payload(request: Request) -> dict[str, list[str]]:
    body = await request.body()
    if len(body) > request_body_limit_bytes():
        raise HTTPException(status_code=413, detail="request body too large")
    return parse_qs(body.decode("utf-8"), keep_blank_values=True)


def first_form_value(form: dict[str, list[str]], name: str, default: str = "") -> str:
    values = form.get(name)
    if not values:
        return default
    return values[0]


def request_body_limit_bytes() -> int:
    try:
        return max(1, int(os.environ.get("OZ_MAX_REQUEST_BODY_BYTES", "1048576")))
    except ValueError:
        return 1048576


def content_length_too_large(request: Request) -> bool:
    raw = request.headers.get("content-length")
    if not raw:
        return False
    try:
        return int(raw) > request_body_limit_bytes()
    except ValueError:
        return True


def install_body_limit(request: Request) -> None:
    original_receive = request._receive  # type: ignore[attr-defined]
    limit = request_body_limit_bytes()
    received = 0

    async def limited_receive():
        nonlocal received
        message = await original_receive()
        if message.get("type") == "http.request":
            body = message.get("body") or b""
            received += len(body)
            if received > limit:
                raise BodyTooLarge("request body too large")
        return message

    request._receive = limited_receive  # type: ignore[attr-defined]
