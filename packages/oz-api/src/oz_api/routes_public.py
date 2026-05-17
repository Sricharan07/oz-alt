from __future__ import annotations

from fastapi import APIRouter, Request
from fastapi.responses import HTMLResponse, JSONResponse, Response

from oz_api.http_context import state_from_request
from oz_api.metrics import metrics_authorized, render_prometheus_metrics
from oz_api.web_pages import public_markdown_html, render_home_page, render_login_page, render_signup_page, status_page

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


@router.get("/privacy", response_class=HTMLResponse)
@router.get("/terms", response_class=HTMLResponse)
async def public_document(request: Request) -> HTMLResponse:
    return HTMLResponse(public_markdown_html(request.url.path))


@router.get("/status", response_class=HTMLResponse)
async def status() -> HTMLResponse:
    return HTMLResponse(status_page())


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
