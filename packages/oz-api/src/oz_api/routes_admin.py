from __future__ import annotations

from fastapi import APIRouter, Request
from fastapi.responses import HTMLResponse

from oz_api.admin import default_crawl_max_pages, load_admin_snapshot, render_admin
from oz_api.admin_ops import (
    approve_crawl,
    log_admin_action,
    promote_library_version,
    set_library_default_version,
    upsert_library_profile,
)
from oz_api.auth import (
    AuthError,
    create_password_invite,
    create_password_reset,
    csrf_token,
    set_user_disabled,
    verify_csrf,
)
from oz_api.auth_store import AuthStore, postgres_connection
from oz_api.embedding_jobs import cancel_embedding_job
from oz_api.html_utils import esc
from oz_api.http_context import first_form_value, principal_for_request, read_form_payload, session_cookie, state_from_request
from oz_api.queue import crawler_job_event, missing_required_crawler_fields
from oz_api.server_helpers import first_form_values
from oz_api.web_pages import admin_result_page

router = APIRouter()


@router.get("/admin", response_class=HTMLResponse)
@router.get("/admin/", response_class=HTMLResponse)
async def admin_home(request: Request) -> HTMLResponse:
    state = state_from_request(request)
    return HTMLResponse(render_admin(state.storage, csrf=csrf_token(session_cookie(request))))


@router.get("/admin/enqueue-crawl", response_class=HTMLResponse)
async def enqueue_crawl_get() -> HTMLResponse:
    return HTMLResponse("<!doctype html><p>Use the admin approve form.</p>", status_code=405)


@router.post("/admin/enqueue-crawl")
async def enqueue_crawl(request: Request) -> HTMLResponse:
    state = state_from_request(request)
    form = await read_form_payload(request)
    if not verify_csrf(session_cookie(request), first_form_value(form, "csrf")):
        return HTMLResponse("<!doctype html><p>Invalid CSRF token.</p>", status_code=403)
    payload = {
        "library_name": first_form_value(form, "library_name"),
        "vendor": first_form_value(form, "vendor"),
        "source_url": first_form_value(form, "source_url"),
        "version": first_form_value(form, "version", "latest"),
        "max_pages": first_form_value(form, "max_pages", str(default_crawl_max_pages())),
        "recrawl_interval_hours": first_form_value(form, "recrawl_interval_hours", "24"),
        "fetcher": first_form_value(form, "fetcher"),
        "concurrent_requests": first_form_value(form, "concurrent_requests"),
        "download_delay": first_form_value(form, "download_delay"),
        "robots_txt": first_form_value(form, "robots_txt"),
    }
    missing = missing_required_crawler_fields(crawler_job_event(payload))
    if missing:
        return HTMLResponse(
            f"<!doctype html><p>Missing crawler job fields: {esc(', '.join(missing))}</p>",
            status_code=400,
        )
    approve_crawl(state.storage, payload, principal_for_request(request))
    return HTMLResponse('<!doctype html><meta http-equiv="refresh" content="0; url=/admin">', status_code=202)


@router.post("/admin/library-profile")
async def library_profile(request: Request) -> HTMLResponse:
    form = await read_form_payload(request)
    if not verify_csrf(session_cookie(request), first_form_value(form, "csrf")):
        return HTMLResponse("<!doctype html><p>Invalid CSRF token.</p>", status_code=403)
    try:
        upsert_library_profile(first_form_values(form), principal_for_request(request))
    except Exception as exc:
        return HTMLResponse(f"<!doctype html><p>{esc(str(exc))}</p>", status_code=400)
    return HTMLResponse('<!doctype html><meta http-equiv="refresh" content="0; url=/admin">', status_code=202)


@router.post("/admin/default-version")
async def default_version(request: Request) -> HTMLResponse:
    form = await read_form_payload(request)
    if not verify_csrf(session_cookie(request), first_form_value(form, "csrf")):
        return HTMLResponse("<!doctype html><p>Invalid CSRF token.</p>", status_code=403)
    try:
        set_library_default_version(first_form_values(form), principal_for_request(request))
    except Exception as exc:
        return HTMLResponse(admin_result_page("Default version failed", str(exc)), status_code=400)
    return HTMLResponse('<!doctype html><meta http-equiv="refresh" content="0; url=/admin">', status_code=202)


@router.post("/admin/promote-version")
async def promote_version(request: Request) -> HTMLResponse:
    form = await read_form_payload(request)
    if not verify_csrf(session_cookie(request), first_form_value(form, "csrf")):
        return HTMLResponse("<!doctype html><p>Invalid CSRF token.</p>", status_code=403)
    try:
        promote_library_version(first_form_values(form), principal_for_request(request))
    except Exception as exc:
        return HTMLResponse(admin_result_page("Promote version failed", str(exc)), status_code=400)
    return HTMLResponse('<!doctype html><meta http-equiv="refresh" content="0; url=/admin">', status_code=202)


@router.post("/admin/users/invite")
async def invite_user(request: Request) -> HTMLResponse:
    form = await read_form_payload(request)
    principal = principal_for_request(request)
    if not verify_csrf(session_cookie(request), first_form_value(form, "csrf")):
        return HTMLResponse("<!doctype html><p>Invalid CSRF token.</p>", status_code=403)
    try:
        result = create_password_invite(
            first_form_value(form, "email"),
            first_form_value(form, "role", "user"),
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
        return HTMLResponse(admin_result_page("Invite failed", str(exc)), status_code=400)
    return HTMLResponse(admin_result_page("User invite", f"Invite for {esc(result['email'])}", link=result["url"]))


@router.post("/admin/users/reset-password")
async def reset_user_password(request: Request) -> HTMLResponse:
    form = await read_form_payload(request)
    principal = principal_for_request(request)
    if not verify_csrf(session_cookie(request), first_form_value(form, "csrf")):
        return HTMLResponse("<!doctype html><p>Invalid CSRF token.</p>", status_code=403)
    try:
        result = create_password_reset(first_form_value(form, "email"), principal)
        log_admin_action(principal, "password_reset_created", target_type="user", target=result["email"])
    except (AuthError, RuntimeError) as exc:
        return HTMLResponse(admin_result_page("Reset failed", str(exc)), status_code=400)
    return HTMLResponse(admin_result_page("Password reset", f"Reset link for {esc(result['email'])}", link=result["url"]))


@router.post("/admin/users/disable")
@router.post("/admin/users/enable")
async def set_disabled(request: Request) -> HTMLResponse:
    form = await read_form_payload(request)
    principal = principal_for_request(request)
    if not verify_csrf(session_cookie(request), first_form_value(form, "csrf")):
        return HTMLResponse("<!doctype html><p>Invalid CSRF token.</p>", status_code=403)
    disabled = request.url.path.endswith("/disable")
    try:
        user = set_user_disabled(first_form_value(form, "email"), disabled, principal)
        log_admin_action(
            principal,
            "user_disabled" if disabled else "user_enabled",
            target_type="user",
            target=user.email,
        )
    except (AuthError, RuntimeError) as exc:
        return HTMLResponse(admin_result_page("User update failed", str(exc)), status_code=400)
    return HTMLResponse('<!doctype html><meta http-equiv="refresh" content="0; url=/admin">', status_code=202)


@router.post("/admin/embedding-jobs/cancel")
async def cancel_admin_embedding_job(request: Request) -> HTMLResponse:
    form = await read_form_payload(request)
    principal = principal_for_request(request)
    if not verify_csrf(session_cookie(request), first_form_value(form, "csrf")):
        return HTMLResponse("<!doctype html><p>Invalid CSRF token.</p>", status_code=403)
    embedding_job_id = first_form_value(form, "embedding_job_id")
    store = AuthStore.from_env()
    connection = postgres_connection(store.database_url if store else None)
    if connection is None:
        return HTMLResponse(admin_result_page("Cancel failed", "Postgres connection is unavailable."), status_code=500)
    try:
        with connection:
            cancel_embedding_job(connection, int(embedding_job_id))
        log_admin_action(principal, "embedding_job_cancelled", target_type="embedding_job", target=embedding_job_id)
    except (TypeError, ValueError, RuntimeError) as exc:
        return HTMLResponse(admin_result_page("Cancel failed", str(exc)), status_code=400)
    return HTMLResponse('<!doctype html><meta http-equiv="refresh" content="0; url=/admin">', status_code=202)


@router.get("/admin/index-requests")
async def admin_index_requests(request: Request):
    return load_admin_snapshot(state_from_request(request).storage)["index_requests"]


@router.get("/admin/telemetry")
async def admin_telemetry(request: Request):
    return load_admin_snapshot(state_from_request(request).storage)["telemetry"]


@router.get("/admin/crawler-jobs")
async def admin_crawler_jobs(request: Request):
    return load_admin_snapshot(state_from_request(request).storage)["crawler_jobs"]


@router.get("/admin/crawl-job-logs")
async def admin_crawl_job_logs(request: Request):
    rows = load_admin_snapshot(state_from_request(request).storage)["crawl_job_logs"]
    job_id = request.query_params.get("job_id")
    if job_id:
        rows = [row for row in rows if str(row.get("job_id")) == job_id]
    return rows


@router.get("/admin/usage")
async def admin_usage(request: Request):
    return load_admin_snapshot(state_from_request(request).storage)["usage_events"]


@router.get("/admin/actions")
async def admin_actions(request: Request):
    return load_admin_snapshot(state_from_request(request).storage)["admin_actions"]


@router.get("/admin/promotions")
async def admin_promotions(request: Request):
    return load_admin_snapshot(state_from_request(request).storage)["promotions"]


@router.get("/admin/freshness")
async def admin_freshness(request: Request):
    return load_admin_snapshot(state_from_request(request).storage)["freshness_policies"]


@router.get("/admin/quality")
async def admin_quality(request: Request):
    return load_admin_snapshot(state_from_request(request).storage)["quality_runs"]


@router.get("/admin/evals")
async def admin_evals(request: Request):
    return load_admin_snapshot(state_from_request(request).storage)["eval_runs"]


@router.get("/admin/packs")
async def admin_packs(request: Request):
    return load_admin_snapshot(state_from_request(request).storage)["pack_builds"]
