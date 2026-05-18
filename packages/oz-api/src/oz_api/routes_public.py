from __future__ import annotations

from datetime import datetime, timezone

from fastapi import APIRouter, Request
from fastapi.responses import HTMLResponse, JSONResponse, Response

from oz_api.http_context import state_from_request
from oz_api.metrics import collect_metric_values, metrics_authorized, render_prometheus_metrics
from oz_api.public_catalog import public_library_detail, public_library_rows
from oz_api.web_pages import (
    public_markdown_html,
    render_home_page,
    render_libraries_page,
    render_library_detail_page,
    render_login_page,
    render_signup_page,
    status_page,
)

router = APIRouter()


@router.get("/", response_class=HTMLResponse)
async def home() -> HTMLResponse:
    return HTMLResponse(render_home_page())


@router.get("/health")
async def health() -> dict[str, str | bool]:
    return {"ok": True, "service": "oz-api"}


@router.get("/catalog")
async def catalog(request: Request):
    return state_from_request(request).storage.load_catalog_document()


@router.get("/libraries", response_class=HTMLResponse)
@router.get("/libraries/", response_class=HTMLResponse)
async def libraries_page(request: Request) -> HTMLResponse:
    rows = public_library_rows(state_from_request(request).storage)
    return HTMLResponse(render_libraries_page(rows))


@router.get("/libraries.json")
async def libraries_json(request: Request) -> dict[str, object]:
    rows = public_library_rows(state_from_request(request).storage)
    return {"libraries": rows}


@router.get("/libraries/{vendor}/{library:path}", response_class=HTMLResponse)
async def library_page(request: Request, vendor: str, library: str):
    detail = public_library_detail(
        state_from_request(request).storage,
        vendor,
        library,
        request.query_params.get("version"),
    )
    if detail is None:
        return JSONResponse({"error": "library_not_found", "vendor": vendor, "library": library}, status_code=404)
    return HTMLResponse(render_library_detail_page(detail))


@router.get("/api/libraries/{vendor}/{library:path}")
async def library_json(request: Request, vendor: str, library: str):
    detail = public_library_detail(
        state_from_request(request).storage,
        vendor,
        library,
        request.query_params.get("version"),
    )
    if detail is None:
        return JSONResponse({"error": "library_not_found", "vendor": vendor, "library": library}, status_code=404)
    return detail


@router.get("/privacy", response_class=HTMLResponse)
@router.get("/terms", response_class=HTMLResponse)
async def public_document(request: Request) -> HTMLResponse:
    return HTMLResponse(public_markdown_html(request.url.path))


@router.get("/status", response_class=HTMLResponse)
async def status() -> HTMLResponse:
    return HTMLResponse(status_page())


@router.get("/status.json")
async def status_json() -> dict[str, object]:
    metrics = collect_metric_values()
    postgres_up = bool(metrics.get("oz_postgres_up"))
    redis_up = bool(metrics.get("oz_redis_up"))
    open_alerts = int(metrics.get("oz_open_alerts") or 0)
    status_value = "degraded" if open_alerts or not postgres_up or not redis_up else "operational"
    return {
        "status": status_value,
        "service": "oz",
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "components": {
            "api": {"status": "up"},
            "postgres": {"status": "up" if postgres_up else "down"},
            "redis": {"status": "up" if redis_up else "down"},
            "catalog": {"libraries": int(metrics.get("oz_libraries_total") or 0)},
            "crawler": {
                "queued": int(metrics.get("oz_crawler_jobs_queued") or 0),
                "running": int(metrics.get("oz_crawler_jobs_running") or 0),
            },
            "alerts": {"open": open_alerts},
            "backups": {"fresh_verified": bool(metrics.get("oz_fresh_verified_backups"))},
        },
    }


@router.get("/metrics")
async def metrics(request: Request) -> Response:
    if not metrics_authorized(request.headers):
        return JSONResponse({"error": "not found"}, status_code=404)
    return Response(
        render_prometheus_metrics(),
        media_type="text/plain; version=0.0.4; charset=utf-8",
    )


@router.get("/login", response_class=HTMLResponse)
@router.get("/login/", response_class=HTMLResponse)
async def login_page() -> HTMLResponse:
    return HTMLResponse(render_login_page())


@router.get("/signup", response_class=HTMLResponse)
@router.get("/signup/", response_class=HTMLResponse)
async def signup_page() -> HTMLResponse:
    return HTMLResponse(render_signup_page())
