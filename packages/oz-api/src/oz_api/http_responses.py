from __future__ import annotations

from fastapi.responses import RedirectResponse

from oz_api.auth import SESSION_COOKIE
from oz_api.server_helpers import cookie_domain, secure_cookie


WEB_SESSION_MAX_AGE_SECONDS = 30 * 24 * 60 * 60


def redirect_with_session(location: str, session_token: str) -> RedirectResponse:
    response = RedirectResponse(location, status_code=302)
    response.set_cookie(
        SESSION_COOKIE,
        session_token,
        max_age=WEB_SESSION_MAX_AGE_SECONDS,
        path="/",
        httponly=True,
        secure=secure_cookie(),
        domain=cookie_domain(),
        samesite="lax",
    )
    return response


def redirect_clearing_session(location: str) -> RedirectResponse:
    response = RedirectResponse(location, status_code=302)
    response.delete_cookie(
        SESSION_COOKIE,
        path="/",
        domain=cookie_domain(),
        secure=secure_cookie(),
        httponly=True,
        samesite="lax",
    )
    return response
