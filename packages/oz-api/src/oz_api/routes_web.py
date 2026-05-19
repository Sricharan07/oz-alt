from __future__ import annotations

from fastapi import APIRouter, Request
from fastapi.responses import HTMLResponse

from oz_api.auth import (
    AuthError,
    accept_password_token,
    authenticate_password,
    approve_device_code,
    change_principal_password,
    create_password_account,
    csrf_token,
    list_cli_sessions,
    revoke_cli_session,
    revoke_web_session,
    verify_csrf,
)
from oz_api.http_context import client_ip, first_form_value, principal_for_request, read_form_payload, session_cookie
from oz_api.http_responses import redirect_clearing_session, redirect_with_session
from oz_api.usage import usage_summary
from oz_api.web_pages import (
    render_account_page,
    render_dashboard,
    render_device_page,
    render_login_page,
    render_password_token_page,
    render_signup_page,
)

router = APIRouter()


@router.post("/login")
@router.post("/login/")
async def login(request: Request):
    form = await read_form_payload(request)
    try:
        session, _principal = authenticate_password(
            first_form_value(form, "email"),
            first_form_value(form, "password"),
            ip=client_ip(request),
            user_agent=request.headers.get("user-agent", ""),
        )
    except (AuthError, RuntimeError) as exc:
        return HTMLResponse(render_login_page(str(exc)), status_code=400)
    return redirect_with_session(safe_next_path(first_form_value(form, "next")), session)


@router.post("/signup")
@router.post("/signup/")
async def signup(request: Request):
    form = await read_form_payload(request)
    password = first_form_value(form, "password")
    if password != first_form_value(form, "confirm_password"):
        return HTMLResponse(render_signup_page("passwords_do_not_match"), status_code=400)
    try:
        session, _principal = create_password_account(
            first_form_value(form, "email"),
            password,
            ip=client_ip(request),
            user_agent=request.headers.get("user-agent", ""),
        )
    except (AuthError, RuntimeError) as exc:
        return HTMLResponse(render_signup_page(str(exc)), status_code=400)
    return redirect_with_session(safe_next_path(first_form_value(form, "next")), session)


@router.get("/invite", response_class=HTMLResponse)
@router.get("/invite/", response_class=HTMLResponse)
@router.get("/reset-password", response_class=HTMLResponse)
@router.get("/reset-password/", response_class=HTMLResponse)
async def password_token_page(request: Request) -> HTMLResponse:
    token = request.query_params.get("token", "")
    return HTMLResponse(render_password_token_page(token, reset=request.url.path.startswith("/reset-password")))


@router.post("/invite")
@router.post("/invite/")
@router.post("/reset-password")
@router.post("/reset-password/")
async def accept_token(request: Request):
    form = await read_form_payload(request)
    token = first_form_value(form, "token")
    password = first_form_value(form, "password")
    reset = request.url.path.startswith("/reset-password")
    if password != first_form_value(form, "confirm_password"):
        return HTMLResponse(
            render_password_token_page(token, error="passwords_do_not_match", reset=reset),
            status_code=400,
        )
    try:
        session, _principal = accept_password_token(
            token,
            password,
            ip=client_ip(request),
            user_agent=request.headers.get("user-agent", ""),
        )
    except (AuthError, RuntimeError) as exc:
        return HTMLResponse(render_password_token_page(token, error=str(exc), reset=reset), status_code=400)
    return redirect_with_session("/dashboard", session)


@router.get("/dashboard", response_class=HTMLResponse)
@router.get("/dashboard/", response_class=HTMLResponse)
async def dashboard(request: Request) -> HTMLResponse:
    principal = principal_for_request(request)
    if principal is None:
        return HTMLResponse(render_login_page(), status_code=401)
    return HTMLResponse(render_dashboard(principal, usage_summary(principal)))


@router.get("/account", response_class=HTMLResponse)
@router.get("/account/", response_class=HTMLResponse)
async def account(request: Request) -> HTMLResponse:
    principal = principal_for_request(request)
    if principal is None:
        return HTMLResponse(render_login_page("Sign in before opening account settings."), status_code=401)
    session = session_cookie(request)
    return HTMLResponse(
        render_account_page(
            principal,
            csrf=csrf_token(session),
            cli_sessions=list_cli_sessions(principal),
        )
    )


@router.post("/account/password")
@router.post("/account/password/")
async def change_password(request: Request) -> HTMLResponse:
    principal = principal_for_request(request)
    if principal is None:
        return HTMLResponse(render_login_page("Sign in before changing password."), status_code=401)
    form = await read_form_payload(request)
    session = session_cookie(request)
    if not verify_csrf(session, first_form_value(form, "csrf")):
        return account_page_with_message(principal, session, error="Invalid CSRF token.", status_code=403)
    new_password = first_form_value(form, "new_password")
    if new_password != first_form_value(form, "confirm_password"):
        return account_page_with_message(principal, session, error="passwords_do_not_match", status_code=400)
    try:
        change_principal_password(
            principal,
            first_form_value(form, "current_password"),
            new_password,
            ip=client_ip(request),
            user_agent=request.headers.get("user-agent", ""),
        )
    except (AuthError, RuntimeError) as exc:
        return account_page_with_message(principal, session, error=str(exc), status_code=400)
    return account_page_with_message(principal, session, message="Password updated.")


@router.post("/account/cli-sessions/revoke")
@router.post("/account/cli-sessions/revoke/")
async def revoke_cli(request: Request) -> HTMLResponse:
    principal = principal_for_request(request)
    if principal is None:
        return HTMLResponse(render_login_page("Sign in before changing CLI sessions."), status_code=401)
    form = await read_form_payload(request)
    session = session_cookie(request)
    if not verify_csrf(session, first_form_value(form, "csrf")):
        return account_page_with_message(principal, session, error="Invalid CSRF token.", status_code=403)
    try:
        revoke_cli_session(
            principal,
            first_form_value(form, "token_id"),
            ip=client_ip(request),
            user_agent=request.headers.get("user-agent", ""),
        )
    except (AuthError, RuntimeError) as exc:
        return account_page_with_message(principal, session, error=str(exc), status_code=400)
    return account_page_with_message(principal, session, message="CLI session revoked.")


@router.get("/device", response_class=HTMLResponse)
@router.get("/device/", response_class=HTMLResponse)
async def device_page(request: Request) -> HTMLResponse:
    principal = principal_for_request(request)
    if principal is None:
        return HTMLResponse(render_login_page("Sign in before approving a CLI device."), status_code=401)
    session = session_cookie(request)
    return HTMLResponse(render_device_page(principal, request.query_params.get("code", ""), csrf=csrf_token(session)))


@router.post("/device")
@router.post("/device/")
async def approve_device(request: Request) -> HTMLResponse:
    principal = principal_for_request(request)
    if principal is None:
        return HTMLResponse(render_login_page("Sign in before approving a CLI device."), status_code=401)
    form = await read_form_payload(request)
    session = session_cookie(request)
    if not verify_csrf(session, first_form_value(form, "csrf")):
        return HTMLResponse(render_device_page(principal, error="Invalid CSRF token."), status_code=403)
    code = first_form_value(form, "user_code")
    try:
        approve_device_code(
            code,
            principal,
            ip=client_ip(request),
            user_agent=request.headers.get("user-agent", ""),
        )
    except (AuthError, RuntimeError) as exc:
        return HTMLResponse(render_device_page(principal, code, csrf=csrf_token(session), error=str(exc)), status_code=400)
    return HTMLResponse(
        render_device_page(
            principal,
            "",
            csrf=csrf_token(session),
            message="Device approved. You can return to the CLI.",
        )
    )


@router.get("/admin/logout")
async def admin_logout_get() -> HTMLResponse:
    return HTMLResponse("<!doctype html><p>Use the logout button from the admin page.</p>", status_code=405)


@router.post("/admin/logout")
async def admin_logout(request: Request):
    form = await read_form_payload(request)
    if not verify_csrf(session_cookie(request), first_form_value(form, "csrf")):
        return HTMLResponse("<!doctype html><p>Invalid CSRF token.</p>", status_code=403)
    revoke_web_session(session_cookie(request))
    return redirect_clearing_session("/dashboard")


@router.post("/auth/logout")
async def auth_logout(request: Request) -> dict[str, bool]:
    revoke_web_session(session_cookie(request))
    return {"ok": True}


def account_page_with_message(principal, session: str | None, *, error: str = "", message: str = "", status_code: int = 200):
    return HTMLResponse(
        render_account_page(
            principal,
            csrf=csrf_token(session),
            error=error,
            message=message,
            cli_sessions=list_cli_sessions(principal),
        ),
        status_code=status_code,
    )


def safe_next_path(value: str) -> str:
    if not value:
        return "/dashboard"
    if value.startswith("/") and not value.startswith("//") and "\n" not in value and "\r" not in value:
        return value
    return "/dashboard"
