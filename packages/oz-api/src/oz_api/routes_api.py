from __future__ import annotations

import time

from fastapi import APIRouter, Request
from fastapi.responses import JSONResponse, RedirectResponse, Response

from oz_api.admin_ops import approve_crawl, submit_index_request
from oz_api.auth import (
    AuthError,
    approve_device_code,
    change_principal_password,
    csrf_token,
    exchange_device_code,
    list_cli_sessions,
    list_web_sessions,
    refresh_cli_token,
    revoke_cli_session,
    revoke_web_session_by_id,
    start_device_authorization,
    verify_csrf,
)
from oz_api.freshness import stale_libraries_from_payload
from oz_api.http_context import client_ip, principal_for_request, read_json_payload, session_cookie, state_from_request
from oz_api.limits import index_request_allowed
from oz_api.queue import crawler_job_event, missing_required_crawler_fields
from oz_api.retrieval_experiments import retrieval_variant
from oz_api.retrieval_metrics import record_retrieval_latency
from oz_api.retrieval import (
    RetrievalContext,
    context as retrieval_context,
    search as retrieval_search,
    suggest as retrieval_suggest,
    unique_libraries_to_pull as retrieval_unique_libraries_to_pull,
)
from oz_api.server_helpers import bulk_refs_payload, single_ref_payload
from oz_api.telemetry import sanitize_telemetry
from oz_api.usage import (
    recent_usage_events,
    record_pack_download_metrics,
    record_telemetry_event,
    record_usage_event,
    usage_daily_rows,
    usage_summary,
    usage_totals,
)
from oz_api.versions import VersionResolutionError

router = APIRouter()


@router.get("/api/console/account")
async def console_account(request: Request):
    principal = principal_for_request(request)
    if principal is None:
        return JSONResponse({"error": "unauthorized"}, status_code=401)
    session = session_cookie(request)
    return {
        "user": principal_payload(principal),
        "csrf": csrf_token(session),
        "web_sessions": list_web_sessions(principal, session),
        "cli_sessions": list_cli_sessions(principal),
        "usage": {
            "totals": usage_totals(principal),
            "summary": usage_summary(principal),
            "daily": usage_daily_rows(principal),
            "recent_events": recent_usage_events(principal),
        },
    }


@router.post("/api/console/cli-sessions/revoke")
async def console_revoke_cli_session(request: Request):
    principal = principal_for_request(request)
    if principal is None:
        return JSONResponse({"error": "unauthorized"}, status_code=401)
    payload = await read_json_payload(request)
    csrf_error = verify_console_csrf(request, payload)
    if csrf_error is not None:
        return csrf_error
    try:
        revoke_cli_session(
            principal,
            str(payload.get("token_id") or ""),
            ip=client_ip(request),
            user_agent=request.headers.get("user-agent", ""),
        )
    except (AuthError, RuntimeError) as exc:
        return JSONResponse({"error": str(exc)}, status_code=400)
    return {"ok": True}


@router.post("/api/console/web-sessions/revoke")
async def console_revoke_web_session(request: Request):
    principal = principal_for_request(request)
    if principal is None:
        return JSONResponse({"error": "unauthorized"}, status_code=401)
    payload = await read_json_payload(request)
    csrf_error = verify_console_csrf(request, payload)
    if csrf_error is not None:
        return csrf_error
    try:
        revoke_web_session_by_id(
            principal,
            str(payload.get("session_id") or ""),
            ip=client_ip(request),
            user_agent=request.headers.get("user-agent", ""),
        )
    except (AuthError, RuntimeError) as exc:
        return JSONResponse({"error": str(exc)}, status_code=400)
    return {"ok": True}


@router.post("/api/console/password")
async def console_change_password(request: Request):
    principal = principal_for_request(request)
    if principal is None:
        return JSONResponse({"error": "unauthorized"}, status_code=401)
    payload = await read_json_payload(request)
    csrf_error = verify_console_csrf(request, payload)
    if csrf_error is not None:
        return csrf_error
    new_password = str(payload.get("new_password") or "")
    if new_password != str(payload.get("confirm_password") or ""):
        return JSONResponse({"error": "passwords_do_not_match"}, status_code=400)
    try:
        change_principal_password(
            principal,
            str(payload.get("current_password") or ""),
            new_password,
            ip=client_ip(request),
            user_agent=request.headers.get("user-agent", ""),
        )
    except (AuthError, RuntimeError) as exc:
        return JSONResponse({"error": str(exc)}, status_code=400)
    return {"ok": True}


@router.post("/api/console/device/approve")
async def console_approve_device(request: Request):
    principal = principal_for_request(request)
    if principal is None:
        return JSONResponse({"error": "unauthorized"}, status_code=401)
    payload = await read_json_payload(request)
    csrf_error = verify_console_csrf(request, payload)
    if csrf_error is not None:
        return csrf_error
    code = str(payload.get("user_code") or "").strip()
    if not code:
        return JSONResponse({"error": "device_code_required"}, status_code=400)
    try:
        approve_device_code(
            code,
            principal,
            ip=client_ip(request),
            user_agent=request.headers.get("user-agent", ""),
        )
    except (AuthError, RuntimeError) as exc:
        return JSONResponse({"error": str(exc)}, status_code=400)
    return {"ok": True}


def principal_payload(principal) -> dict[str, str | bool]:
    return {
        "id": principal.user_id,
        "email": principal.email,
        "role": principal.role,
        "is_admin": principal.is_admin,
    }


def verify_console_csrf(request: Request, payload: dict[str, object]) -> JSONResponse | None:
    submitted = str(payload.get("csrf") or request.headers.get("x-csrf-token") or "")
    if verify_csrf(session_cookie(request), submitted):
        return None
    return JSONResponse({"error": "invalid_csrf"}, status_code=403)


@router.get("/refs")
async def refs(request: Request):
    return bulk_refs_payload(state_from_request(request), request.url.query)


@router.get("/refs/{vendor}/{library}")
async def single_ref(request: Request, vendor: str, library: str):
    requested_version = request.query_params.get("version")
    try:
        payload = single_ref_payload(state_from_request(request), vendor, library, requested_version)
    except VersionResolutionError as exc:
        return JSONResponse(exc.response_payload(), status_code=exc.status_code)
    if payload is None:
        return JSONResponse({"error": "library_not_found", "vendor": vendor, "library": library}, status_code=404)
    if payload.get("error"):
        return JSONResponse(payload, status_code=404)
    return payload


@router.get("/pack/{vendor}/{library}/{version}")
async def pack(request: Request, vendor: str, library: str, version: str):
    state = state_from_request(request)
    principal = principal_for_request(request)
    try:
        resolved = single_ref_payload(state, vendor, library, version)
    except VersionResolutionError as exc:
        return JSONResponse(exc.response_payload(), status_code=exc.status_code)
    if resolved is None:
        return JSONResponse({"error": "library_not_found", "vendor": vendor, "library": library}, status_code=404)
    if resolved.get("error"):
        return JSONResponse(resolved, status_code=404)
    canonical_version = str(resolved["version"])
    record_usage_event(principal, "pack_download", library=f"{vendor}/{library}@{canonical_version}")
    record_pack_download_metrics(vendor, library, canonical_version)
    pack_url = state.storage.get_pack_url(vendor, library, canonical_version)
    if pack_url:
        return RedirectResponse(pack_url, status_code=302)
    pack_bytes = state.storage.get_pack_bytes(vendor, library, canonical_version)
    if pack_bytes is None:
        return JSONResponse(
            {"error": "pack_not_found", "vendor": vendor, "library": library, "version": canonical_version},
            status_code=404,
        )
    return Response(
        pack_bytes,
        media_type="application/vnd.oz.pack",
        headers={"Cache-Control": "public, max-age=31536000, immutable"},
    )


@router.post("/auth/device")
@router.post("/auth/device/start")
async def auth_device_start(request: Request):
    try:
        return start_device_authorization(ip=client_ip(request), user_agent=request.headers.get("user-agent", ""))
    except (AuthError, RuntimeError) as exc:
        status = 429 if str(exc) == "rate_limited" else 400
        headers = {"Retry-After": "60", "RateLimit-Limit": "30", "RateLimit-Remaining": "0", "RateLimit-Reset": "60"} if status == 429 else None
        return JSONResponse({"error": str(exc)}, status_code=status, headers=headers)


@router.post("/auth/token")
@router.post("/auth/device/token")
async def auth_device_token(request: Request):
    payload = await read_json_payload(request)
    token = exchange_device_code(
        str(payload.get("device_code") or ""),
        machine_id=str(payload.get("machine_id") or ""),
    )
    if token.get("error"):
        status = 400
        if token.get("error") in {"authorization_pending", "slow_down"}:
            status = 428
        return JSONResponse(token, status_code=status)
    return token


@router.post("/auth/refresh")
async def auth_refresh(request: Request):
    payload = await read_json_payload(request)
    token = refresh_cli_token(str(payload.get("refresh_token") or ""))
    if token.get("error"):
        return JSONResponse(token, status_code=401)
    return token


@router.post("/auth/device/approve")
async def auth_device_approve(request: Request):
    principal = principal_for_request(request)
    if principal is None:
        return JSONResponse({"error": "unauthorized"}, status_code=401)
    payload = await read_json_payload(request)
    try:
        return approve_device_code(
            str(payload.get("user_code") or ""),
            principal,
            ip=client_ip(request),
            user_agent=request.headers.get("user-agent", ""),
        )
    except (AuthError, RuntimeError) as exc:
        return JSONResponse({"error": str(exc)}, status_code=400)


@router.post("/suggest")
async def suggest(request: Request):
    started = time.perf_counter()
    state = state_from_request(request)
    payload = await read_json_payload(request)
    query = str(payload.get("query", ""))
    max_results = bounded_int(payload.get("max_results"), default=10, minimum=1, maximum=50)
    fingerprint = str(payload.get("project_fingerprint", ""))
    variant = retrieval_variant(fingerprint)
    ctx = RetrievalContext.from_env(state.storage)
    try:
        results = retrieval_suggest(ctx, query, max_results, fingerprint=fingerprint)
        record_usage_event(
            principal_for_request(request),
            "suggest",
            query_length=len(query),
            result_count=len(results),
            project_fingerprint=fingerprint,
        )
        return {
            "results": results,
            "stale_libraries": stale_libraries_from_payload(state.storage, payload),
        }
    finally:
        record_retrieval_latency("suggest", variant, time.perf_counter() - started)


@router.post("/search")
async def search(request: Request):
    started = time.perf_counter()
    state = state_from_request(request)
    payload = await read_json_payload(request)
    query = str(payload.get("query", ""))
    library_scope = payload.get("library_scope")
    max_results = bounded_int(payload.get("max_results"), default=20, minimum=1, maximum=50)
    fingerprint = str(payload.get("project_fingerprint", ""))
    content_types = content_type_payload(payload)
    variant = retrieval_variant(fingerprint)
    ctx = RetrievalContext.from_env(state.storage)
    try:
        results = retrieval_search(
            ctx,
            query,
            library_scope=library_scope,
            max_results=max_results,
            fingerprint=fingerprint,
            content_types=content_types,
        )
    except VersionResolutionError as exc:
        return JSONResponse(exc.response_payload(), status_code=exc.status_code)
    finally:
        record_retrieval_latency("search", variant, time.perf_counter() - started)
    record_usage_event(
        principal_for_request(request),
        "search",
        library=str(library_scope or "") or None,
        query_length=len(query),
        result_count=len(results),
        project_fingerprint=fingerprint,
    )
    return {
        "results": results,
        "libraries_to_pull": retrieval_unique_libraries_to_pull(results),
        "stale_libraries": stale_libraries_from_payload(state.storage, payload),
        "retrieval_mode": retrieval_mode(results),
        "degraded": any(bool(row.get("degraded")) for row in results),
    }


@router.post("/context")
async def context(request: Request):
    started = time.perf_counter()
    state = state_from_request(request)
    payload = await read_json_payload(request)
    query = str(payload.get("query", ""))
    library_scope = payload.get("library_scope")
    max_tokens = bounded_int(payload.get("max_tokens"), default=2000, minimum=100, maximum=8000)
    max_results = bounded_int(payload.get("max_results"), default=8, minimum=1, maximum=20)
    fingerprint = str(payload.get("project_fingerprint", ""))
    content_types = content_type_payload(payload)
    variant = retrieval_variant(fingerprint)
    ctx = RetrievalContext.from_env(state.storage)
    try:
        result = retrieval_context(
            ctx,
            query,
            library_scope=library_scope,
            max_tokens=max_tokens,
            max_results=max_results,
            fingerprint=fingerprint,
            content_types=content_types,
        )
    except VersionResolutionError as exc:
        return JSONResponse(exc.response_payload(), status_code=exc.status_code)
    finally:
        record_retrieval_latency("context", variant, time.perf_counter() - started)
    rows = result.get("results", [])
    result_count = len(result.get("codeSnippets", [])) + len(result.get("infoSnippets", [])) or len(rows)
    record_usage_event(
        principal_for_request(request),
        "context",
        library=str(library_scope or "") or None,
        query_length=len(query),
        result_count=result_count,
        project_fingerprint=fingerprint,
    )
    return {
        **result,
        "libraries_to_pull": retrieval_unique_libraries_to_pull(rows),
        "stale_libraries": stale_libraries_from_payload(state.storage, payload),
    }


def bounded_int(value: object, *, default: int, minimum: int, maximum: int) -> int:
    try:
        parsed = int(value) if value is not None else default
    except (TypeError, ValueError):
        parsed = default
    return max(minimum, min(maximum, parsed))


def content_type_payload(payload: dict[str, object]) -> list[str] | None:
    raw = payload.get("content_types", payload.get("content_type"))
    if raw is None:
        return None
    if isinstance(raw, str):
        values = [raw]
    elif isinstance(raw, list):
        values = [str(item) for item in raw]
    else:
        return None
    return [value for value in values if value.strip()] or None


def retrieval_mode(results: list[dict[str, object]]) -> str:
    for row in results:
        mode = str(row.get("retrieval_mode") or "")
        if mode:
            return mode
    return "unknown"


@router.post("/index-request")
async def index_request(request: Request):
    state = state_from_request(request)
    payload = await read_json_payload(request)
    requesting_user = str(payload.get("requesting_user", "local"))
    if not index_request_allowed(requesting_user):
        return JSONResponse(
            {"error": "rate_limited"},
            status_code=429,
            headers={"Retry-After": "3600", "RateLimit-Limit": "20", "RateLimit-Remaining": "0", "RateLimit-Reset": "3600"},
        )
    event = submit_index_request(
        state.storage,
        payload,
        principal_for_request(request),
        fallback_user=requesting_user,
    )
    return {"ok": True, "request": event}


@router.post("/crawler/enqueue")
async def crawler_enqueue(request: Request):
    state = state_from_request(request)
    payload = await read_json_payload(request)
    missing = missing_required_crawler_fields(crawler_job_event(payload))
    if missing:
        return JSONResponse({"error": "missing crawler job fields", "fields": missing}, status_code=400)
    event = approve_crawl(state.storage, payload, principal_for_request(request))
    return {"ok": True, "job": event}


@router.post("/telemetry")
async def telemetry(request: Request):
    payload = await read_json_payload(request)
    telemetry_payload = sanitize_telemetry(payload)
    principal = principal_for_request(request)
    record_telemetry_event(principal, telemetry_payload)
    properties = telemetry_payload["properties"]
    record_usage_event(
        principal,
        str(telemetry_payload["event"] or "telemetry"),
        library=str(properties.get("library") or properties.get("library_scope") or "") or None,
        query_length=properties.get("query_length"),
        result_count=properties.get("result_count"),
        properties=properties,
    )
    return {"ok": True}
