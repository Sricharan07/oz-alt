from __future__ import annotations

import argparse
import logging
import os
import time
from contextlib import asynccontextmanager
from pathlib import Path
from collections.abc import AsyncIterator
from typing import Awaitable, Callable

import uvicorn
from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import HTMLResponse, JSONResponse, Response

from oz_api.auth import jwt_secret, production_env
from oz_api.db import close_postgres_pools
from oz_api.http_context import (
    ServerState,
    BodyTooLarge,
    content_length_too_large,
    install_body_limit,
    is_authorized_request,
    request_rate_limit_allowed,
    unauthorized_is_html,
)
from oz_api.observability import (
    configure_logging,
    log_extra,
    new_request_id,
    observe_histogram,
    reset_trace_context,
    set_trace_context,
    should_sample,
)
from oz_api.routes_admin import router as admin_router
from oz_api.routes_api import router as api_router
from oz_api.routes_public import router as public_router
from oz_api.routes_web import router as web_router
from oz_api.web_pages import render_login_page

LOGGER = logging.getLogger(__name__)


def create_app(state: ServerState | None = None) -> FastAPI:
    app = FastAPI(title="Oz API", version="0.1.0", docs_url=None, redoc_url=None, lifespan=app_lifespan)
    app.state.oz_state = state or ServerState(repo_root=Path.cwd())
    install_exception_handlers(app)
    install_middleware(app)
    app.include_router(public_router)
    app.include_router(web_router)
    app.include_router(admin_router)
    app.include_router(api_router)
    return app


@asynccontextmanager
async def app_lifespan(_app: FastAPI) -> AsyncIterator[None]:
    try:
        if production_env():
            jwt_secret()
        yield
    finally:
        close_postgres_pools()


def install_exception_handlers(app: FastAPI) -> None:
    @app.exception_handler(HTTPException)
    async def http_exception(_request: Request, exc: HTTPException) -> JSONResponse:
        return JSONResponse({"error": exc.detail}, status_code=exc.status_code)


def install_middleware(app: FastAPI) -> None:
    @app.middleware("http")
    async def auth_rate_limit_and_errors(
        request: Request,
        call_next: Callable[[Request], Awaitable[Response]],
    ) -> Response:
        started = time.perf_counter()
        request_id = request.headers.get("x-request-id") or new_request_id()
        sampled = should_sample(request_id, explicit=request.headers.get("x-oz-debug") == "1")
        tokens = set_trace_context(request_id, sampled=sampled)
        state: ServerState = request.app.state.oz_state
        response: Response | None = None
        try:
            if request.method in {"POST", "PUT", "PATCH"}:
                if content_length_too_large(request):
                    response = JSONResponse({"error": "request_body_too_large"}, status_code=413)
                    return response
                install_body_limit(request)
            if request.method == "POST" and not request_rate_limit_allowed(request):
                response = JSONResponse(
                    {"error": "rate_limited"},
                    status_code=429,
                    headers={"Retry-After": "60", "RateLimit-Limit": "60", "RateLimit-Remaining": "0", "RateLimit-Reset": "60"},
                )
                return response
            if not is_authorized_request(request, state):
                if unauthorized_is_html(request):
                    response = HTMLResponse(render_login_page(), status_code=401)
                    return response
                response = JSONResponse({"error": "unauthorized"}, status_code=401)
                return response
            response = await call_next(request)
            return response
        except Exception as exc:  # pragma: no cover - ASGI server boundary
            if isinstance(exc, BodyTooLarge):
                response = JSONResponse({"error": "request_body_too_large"}, status_code=413)
                return response
            if isinstance(exc, HTTPException):
                response = JSONResponse({"error": exc.detail}, status_code=exc.status_code)
                return response
            LOGGER.exception("unhandled request error", extra=log_extra(path=request.url.path, method=request.method))
            response = JSONResponse({"error": str(exc)}, status_code=500)
            return response
        finally:
            elapsed = time.perf_counter() - started
            status_code = getattr(response, "status_code", 500)
            observe_histogram(
                "oz_http_request_duration_seconds",
                elapsed,
                {
                    "method": request.method,
                    "path": route_label(request.url.path),
                    "status": str(status_code),
                },
            )
            if response is not None:
                response.headers["x-request-id"] = request_id
            LOGGER.info(
                "request completed",
                extra=log_extra(
                    method=request.method,
                    path=request.url.path,
                    status=status_code,
                    elapsed_ms=round(elapsed * 1000, 3),
                    sampled=sampled,
                ),
            )
            reset_trace_context(tokens)


def build_state(args: argparse.Namespace) -> ServerState:
    display_host = "127.0.0.1" if args.host in {"0.0.0.0", "::"} else args.host
    os.environ.setdefault("OZ_PUBLIC_BASE_URL", f"http://{display_host}:{args.port}")
    os.environ.setdefault("OZ_APP_URL", f"http://{display_host}:{args.port}")
    if production_env() and args.bearer_token == "local-dev-token":
        raise RuntimeError("refusing to start production API with local-dev-token bearer token")
    return ServerState(
        repo_root=args.repo_root.resolve(),
        require_auth=args.require_auth,
        bearer_token=args.bearer_token,
    )


def main() -> None:
    parser = argparse.ArgumentParser(description="Run the Oz registry API.")
    parser.add_argument("--repo-root", type=Path, default=Path.cwd())
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--port", type=int, default=8765)
    parser.add_argument("--require-auth", action="store_true")
    parser.add_argument("--bearer-token", default=os.environ.get("OZ_BEARER_TOKEN", ""))
    args = parser.parse_args()

    configure_logging()
    app = create_app(build_state(args))
    print(f"oz-api listening on http://{args.host}:{args.port}")
    uvicorn.run(app, host=args.host, port=args.port, log_level=os.environ.get("OZ_UVICORN_LOG_LEVEL", "info"))


def route_label(path: str) -> str:
    if path.startswith("/pack/"):
        return "/pack/:vendor/:library"
    if path.startswith("/refs/"):
        return "/refs/:vendor/:library"
    if path.startswith("/admin"):
        return "/admin"
    if path.startswith("/libraries"):
        return "/libraries"
    if path.startswith("/api/libraries/"):
        return "/api/libraries/:vendor/:library"
    if path in {"/suggest", "/search", "/context", "/telemetry", "/health", "/catalog", "/metrics", "/status", "/status.json"}:
        return path
    return "other"


if __name__ == "__main__":
    main()
