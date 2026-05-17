from __future__ import annotations

import base64
import hashlib
import hmac
import json
import logging
import os
import re
import secrets
import time
from dataclasses import dataclass
from typing import Any
from urllib.parse import quote

from oz_api.auth_store import AuthStore

ACCESS_TOKEN_TTL_SECONDS = 15 * 60
CLI_REFRESH_TOKEN_TTL_SECONDS = 90 * 24 * 60 * 60
DEVICE_CODE_TTL_SECONDS = 10 * 60
WEB_SESSION_TTL_SECONDS = 30 * 24 * 60 * 60
PASSWORD_TOKEN_TTL_SECONDS = 7 * 24 * 60 * 60
PASSWORD_MIN_LENGTH = 12
SESSION_COOKIE = "oz_session"
PLACEHOLDER_JWT_SECRETS = {
    "",
    "local-dev-secret",
    "local-compose-jwt-secret-change-me",
}

_JWT_SECRET_CACHE: str | None = None
LOGGER = logging.getLogger(__name__)


@dataclass(frozen=True)
class AuthPrincipal:
    user_id: str
    email: str
    role: str

    @property
    def is_admin(self) -> bool:
        return self.role == "admin"


def jwt_secret() -> str:
    global _JWT_SECRET_CACHE
    if _JWT_SECRET_CACHE:
        return _JWT_SECRET_CACHE
    direct_secret = os.environ.get("OZ_JWT_SECRET")
    if direct_secret:
        validate_jwt_secret(direct_secret)
        _JWT_SECRET_CACHE = direct_secret
        return direct_secret
    secret_arn = os.environ.get("OZ_JWT_SECRET_ARN")
    if secret_arn:
        try:
            import boto3  # type: ignore

            response = boto3.client("secretsmanager").get_secret_value(SecretId=secret_arn)
            _JWT_SECRET_CACHE = str(response.get("SecretString") or "")
            if _JWT_SECRET_CACHE:
                validate_jwt_secret(_JWT_SECRET_CACHE)
                return _JWT_SECRET_CACHE
        except Exception as exc:
            LOGGER.warning("failed to load OZ_JWT_SECRET_ARN: %s", exc)
    if production_env():
        raise RuntimeError("OZ_JWT_SECRET or OZ_JWT_SECRET_ARN is required in production")
    _JWT_SECRET_CACHE = os.environ.get("OZ_JWT_SECRET", "local-dev-secret")
    return _JWT_SECRET_CACHE


def validate_jwt_secret(secret: str) -> None:
    if not production_env():
        return
    if secret in PLACEHOLDER_JWT_SECRETS or len(secret) < 32:
        raise RuntimeError("OZ_JWT_SECRET must be a non-placeholder secret with at least 32 characters in production")


def authenticate_password(email: str, password: str, *, ip: str = "", user_agent: str = "") -> tuple[str, AuthPrincipal]:
    email = normalize_email(email)
    store = require_auth_store()
    enforce_password_login_rate_limit(store, email, ip)
    row = store.one(
        """
        select id::text as user_id, email, role, password_hash, disabled_at is not null as disabled
        from users
        where lower(email) = lower(:email)
        """,
        {"email": email},
    )
    valid = bool(row and not row.get("disabled") and row.get("password_hash")) and verify_password(
        password,
        str(row.get("password_hash") or ""),
    )
    record_password_attempt(store, email, ip, success=valid)
    if not valid or not row:
        audit("password_login_failed", ip=ip, user_agent=user_agent, metadata={"email_hash": safe_hash(email)})
        raise AuthError("invalid_email_or_password")
    principal = AuthPrincipal(
        user_id=str(row["user_id"]),
        email=str(row["email"] or ""),
        role=str(row["role"] or "user"),
    )
    session = create_web_session(principal, ip=ip, user_agent=user_agent, action="password_login")
    return session, principal


def verify_principal_password(principal: AuthPrincipal, password: str) -> bool:
    row = require_auth_store().one(
        """
        select password_hash
        from users
        where id = cast(:user_id as uuid)
          and disabled_at is null
        """,
        {"user_id": principal.user_id},
    )
    return bool(row and row.get("password_hash")) and verify_password(password, str(row.get("password_hash") or ""))


def change_principal_password(
    principal: AuthPrincipal,
    current_password: str,
    new_password: str,
    *,
    ip: str = "",
    user_agent: str = "",
) -> None:
    if not verify_principal_password(principal, current_password):
        audit("password_change_failed", user_id=principal.user_id, ip=ip, user_agent=user_agent)
        raise AuthError("invalid_current_password")
    set_user_password(principal.user_id, new_password)
    audit("password_changed", user_id=principal.user_id, ip=ip, user_agent=user_agent)


def create_password_account(email: str, password: str, *, ip: str = "", user_agent: str = "") -> tuple[str, AuthPrincipal]:
    if not signup_enabled():
        raise AuthError("signup_disabled")
    email = normalize_email(email)
    validate_password(password)
    password_hash = hash_password(password)
    row = require_auth_store().one(
        """
        insert into users (subject, email, role, password_hash, password_set_at, last_seen_at, last_login_at)
        select :subject, :email, 'user', :password_hash, now(), now(), now()
        where not exists (
          select 1 from users where lower(email) = lower(:email)
        )
        returning id::text as user_id, email, role
        """,
        {"subject": f"email:{email}", "email": email, "password_hash": password_hash},
    )
    if not row:
        raise AuthError("account_exists")
    principal = AuthPrincipal(user_id=str(row["user_id"]), email=str(row["email"] or ""), role=str(row["role"] or "user"))
    session = create_web_session(principal, ip=ip, user_agent=user_agent, action="password_signup")
    return session, principal


def create_password_invite(email: str, role: str, actor: AuthPrincipal | None = None) -> dict[str, str]:
    if role not in {"user", "admin"}:
        raise AuthError("invalid_role")
    user = set_user_role(email, role)
    return create_password_token(user, "invite", actor)


def create_password_reset(email: str, actor: AuthPrincipal | None = None) -> dict[str, str]:
    email = normalize_email(email)
    row = require_auth_store().one(
        """
        select id::text as user_id, email, role
        from users
        where lower(email) = lower(:email)
          and disabled_at is null
        """,
        {"email": email},
    )
    if not row:
        raise AuthError("user_not_found")
    user = AuthPrincipal(user_id=str(row["user_id"]), email=str(row["email"] or ""), role=str(row["role"] or "user"))
    return create_password_token(user, "reset", actor)


def create_password_token(user: AuthPrincipal, purpose: str, actor: AuthPrincipal | None = None) -> dict[str, str]:
    if purpose not in {"invite", "reset"}:
        raise AuthError("invalid_password_token_purpose")
    token = secrets.token_urlsafe(36)
    store = require_auth_store()
    store.execute(
        """
        update password_tokens
        set consumed_at = now()
        where user_id = cast(:user_id as uuid)
          and purpose = :purpose
          and consumed_at is null
        """,
        {"user_id": user.user_id, "purpose": purpose},
    )
    store.execute(
        """
        insert into password_tokens (user_id, token_hash, purpose, expires_at, created_by)
        values (
          cast(:user_id as uuid), :token_hash, :purpose,
          now() + make_interval(secs => :ttl), cast(:created_by as uuid)
        )
        """,
        {
            "user_id": user.user_id,
            "token_hash": token_hash(token),
            "purpose": purpose,
            "ttl": PASSWORD_TOKEN_TTL_SECONDS,
            "created_by": actor.user_id if actor else None,
        },
    )
    audit(
        f"password_{purpose}_created",
        user_id=actor.user_id if actor else None,
        metadata={"target_user_hash": safe_hash(user.email), "role": user.role},
    )
    path = "invite" if purpose == "invite" else "reset-password"
    return {
        "email": user.email,
        "role": user.role,
        "purpose": purpose,
        "url": f"{public_app_url()}/{path}?token={quote(token)}",
    }


def accept_password_token(
    token: str,
    password: str,
    *,
    ip: str = "",
    user_agent: str = "",
) -> tuple[str, AuthPrincipal]:
    validate_password(password)
    store = require_auth_store()
    row = store.one(
        """
        update password_tokens
        set consumed_at = now()
        where token_hash = :token_hash
          and consumed_at is null
          and expires_at > now()
        returning user_id::text as user_id, purpose
        """,
        {"token_hash": token_hash(token)},
    )
    if not row:
        raise AuthError("invalid_or_expired_token")
    principal = set_user_password(str(row["user_id"]), password)
    audit(
        f"password_{row.get('purpose')}_accepted",
        user_id=principal.user_id,
        ip=ip,
        user_agent=user_agent,
    )
    session = create_web_session(principal, ip=ip, user_agent=user_agent, action="password_login")
    return session, principal


def set_user_password(user_id: str, password: str) -> AuthPrincipal:
    password_hash = hash_password(password)
    row = require_auth_store().one(
        """
        update users
        set password_hash = :password_hash,
            password_set_at = now(),
            disabled_at = null,
            last_seen_at = now()
        where id = cast(:user_id as uuid)
        returning id::text as user_id, email, role
        """,
        {"user_id": user_id, "password_hash": password_hash},
    )
    if not row:
        raise AuthError("user_not_found")
    return AuthPrincipal(user_id=str(row["user_id"]), email=str(row["email"] or ""), role=str(row["role"] or "user"))


def set_user_disabled(email: str, disabled: bool, actor: AuthPrincipal | None = None) -> AuthPrincipal:
    row = require_auth_store().one(
        """
        update users
        set disabled_at = case when :disabled then now() else null end
        where lower(email) = lower(:email)
        returning id::text as user_id, email, role
        """,
        {"email": normalize_email(email), "disabled": disabled},
    )
    if not row:
        raise AuthError("user_not_found")
    user = AuthPrincipal(user_id=str(row["user_id"]), email=str(row["email"] or ""), role=str(row["role"] or "user"))
    if disabled:
        require_auth_store().execute(
            """
            update web_sessions set revoked_at = now()
            where user_id = cast(:user_id as uuid) and revoked_at is null
            """,
            {"user_id": user.user_id},
        )
        require_auth_store().execute(
            """
            update cli_refresh_tokens set revoked_at = now()
            where user_id = cast(:user_id as uuid) and revoked_at is null
            """,
            {"user_id": user.user_id},
        )
    audit(
        "user_disabled" if disabled else "user_enabled",
        user_id=actor.user_id if actor else None,
        metadata={"target_user_hash": safe_hash(user.email)},
    )
    return user


def start_device_authorization(*, ip: str = "", user_agent: str = "") -> dict[str, Any]:
    device_code = secrets.token_urlsafe(36)
    user_code = generate_user_code()
    store = require_auth_store()
    enforce_device_rate_limit(store, ip)
    store.execute(
        """
        insert into device_codes (device_code_hash, user_code_hash, expires_at, ip_hash)
        values (:device_hash, :user_hash, now() + make_interval(secs => :ttl), :ip_hash)
        """,
        {
            "device_hash": token_hash(device_code),
            "user_hash": token_hash(normalize_user_code(user_code)),
            "ttl": DEVICE_CODE_TTL_SECONDS,
            "ip_hash": safe_hash(ip) if ip else None,
        },
    )
    audit("device_code_started", ip=ip, user_agent=user_agent)
    verification_uri = f"{public_app_url()}/device"
    return {
        "device_code": device_code,
        "user_code": user_code,
        "verification_uri": verification_uri,
        "verification_uri_complete": f"{verification_uri}?code={quote(user_code)}",
        "interval": 5,
        "expires_in": DEVICE_CODE_TTL_SECONDS,
    }


def approve_device_code(user_code: str, principal: AuthPrincipal, *, ip: str = "", user_agent: str = "") -> dict[str, Any]:
    code = normalize_user_code(user_code)
    row = require_auth_store().one(
        """
        update device_codes
        set status = 'approved', user_id = cast(:user_id as uuid), approved_at = now()
        where user_code_hash = :user_hash
          and status = 'pending'
          and expires_at > now()
        returning id
        """,
        {"user_hash": token_hash(code), "user_id": principal.user_id},
    )
    if not row:
        raise AuthError("invalid_or_expired_user_code")
    audit("device_code_approved", user_id=principal.user_id, ip=ip, user_agent=user_agent)
    return {"ok": True}


def exchange_device_code(device_code: str, *, machine_id: str = "") -> dict[str, Any]:
    store = require_auth_store()
    row = store.one(
        """
        select d.id, d.status, d.user_id::text as user_id, d.expires_at < now() as expired,
               u.email, u.role, u.disabled_at is not null as disabled
        from device_codes d
        left join users u on u.id = d.user_id
        where d.device_code_hash = :device_hash
        """,
        {"device_hash": token_hash(device_code)},
    )
    if not row:
        return {"error": "invalid_device_code"}
    if row.get("expired"):
        mark_device_status(str(row["id"]), "expired")
        return {"error": "expired_token"}
    if row["status"] == "pending":
        return {"error": "authorization_pending"}
    if row["status"] == "denied":
        return {"error": "access_denied"}
    if row["status"] == "consumed":
        return {"error": "expired_token"}
    if row.get("disabled") or not row.get("user_id"):
        return {"error": "access_denied"}

    mark_device_status(str(row["id"]), "consumed")
    refresh_token = secrets.token_urlsafe(48)
    store.execute(
        """
        insert into cli_refresh_tokens (user_id, token_hash, machine_id, expires_at, last_used_at)
        values (cast(:user_id as uuid), :token_hash, :machine_id, now() + make_interval(secs => :ttl), now())
        """,
        {
            "user_id": row["user_id"],
            "token_hash": token_hash(refresh_token),
            "machine_id": machine_id or None,
            "ttl": CLI_REFRESH_TOKEN_TTL_SECONDS,
        },
    )
    access_token = issue_token(str(row["user_id"]), role=str(row["role"] or "user"), email=str(row["email"] or ""))
    audit("cli_device_login", user_id=str(row["user_id"]), metadata={"machine_id_hash": safe_hash(machine_id) if machine_id else None})
    return {
        "access_token": access_token,
        "refresh_token": refresh_token,
        "token_type": "Bearer",
        "expires_in": ACCESS_TOKEN_TTL_SECONDS,
    }


def refresh_cli_token(refresh_token: str) -> dict[str, Any]:
    store = require_auth_store()
    row = store.one(
        """
        select t.id::text as token_id, t.user_id::text as user_id, u.email, u.role, u.disabled_at is not null as disabled
        from cli_refresh_tokens t
        join users u on u.id = t.user_id
        where t.token_hash = :token_hash
          and t.revoked_at is null
          and t.expires_at > now()
        """,
        {"token_hash": token_hash(refresh_token)},
    )
    if not row or row.get("disabled"):
        return {"error": "invalid_refresh_token"}
    new_refresh = secrets.token_urlsafe(48)
    store.execute(
        """
        update cli_refresh_tokens
        set token_hash = :new_hash, last_used_at = now()
        where id = cast(:token_id as uuid)
        """,
        {"new_hash": token_hash(new_refresh), "token_id": row["token_id"]},
    )
    return {
        "access_token": issue_token(str(row["user_id"]), role=str(row["role"] or "user"), email=str(row["email"] or "")),
        "refresh_token": new_refresh,
        "token_type": "Bearer",
        "expires_in": ACCESS_TOKEN_TTL_SECONDS,
    }


def list_cli_sessions(principal: AuthPrincipal) -> list[dict[str, Any]]:
    return require_auth_store().execute(
        """
        select id::text as id,
               coalesce(machine_id, '') as machine_id,
               created_at::text as created_at,
               last_used_at::text as last_used_at,
               expires_at::text as expires_at,
               revoked_at::text as revoked_at
        from cli_refresh_tokens
        where user_id = cast(:user_id as uuid)
        order by created_at desc
        limit 50
        """,
        {"user_id": principal.user_id},
    )


def revoke_cli_session(principal: AuthPrincipal, token_id: str, *, ip: str = "", user_agent: str = "") -> None:
    row = require_auth_store().one(
        """
        update cli_refresh_tokens
        set revoked_at = coalesce(revoked_at, now())
        where id = cast(:token_id as uuid)
          and user_id = cast(:user_id as uuid)
        returning id::text as id, machine_id
        """,
        {"token_id": token_id, "user_id": principal.user_id},
    )
    if not row:
        raise AuthError("cli_session_not_found")
    audit(
        "cli_session_revoked",
        user_id=principal.user_id,
        ip=ip,
        user_agent=user_agent,
        metadata={"token_id": str(row.get("id") or ""), "machine_id_hash": safe_hash(str(row.get("machine_id") or ""))},
    )


def principal_from_bearer(headers: dict[str, str] | Any) -> AuthPrincipal | None:
    token = bearer_token(headers)
    if not token:
        return None
    claims = token_claims(token)
    if not claims:
        return None
    principal = AuthPrincipal(
        user_id=str(claims.get("sub") or ""),
        email=str(claims.get("email") or ""),
        role=str(claims.get("role") or "user"),
    )
    store = AuthStore.from_env()
    if store is None:
        return principal
    row = store.one(
        """
        select id::text as user_id, email, role
        from users
        where id = cast(:user_id as uuid)
          and disabled_at is null
        """,
        {"user_id": principal.user_id},
    )
    if not row:
        return None
    return AuthPrincipal(user_id=str(row["user_id"]), email=str(row["email"] or ""), role=str(row["role"] or "user"))


def principal_from_session(session_token: str | None) -> AuthPrincipal | None:
    if not session_token:
        return None
    store = AuthStore.from_env()
    if store is None:
        return None
    row = store.one(
        """
        select u.id::text as user_id, u.email, u.role
        from web_sessions s
        join users u on u.id = s.user_id
        where s.session_hash = :session_hash
          and s.revoked_at is null
          and s.expires_at > now()
          and u.disabled_at is null
        """,
        {"session_hash": token_hash(session_token)},
    )
    if not row:
        return None
    return AuthPrincipal(user_id=str(row["user_id"]), email=str(row["email"] or ""), role=str(row["role"] or "user"))


def revoke_web_session(session_token: str | None) -> None:
    if not session_token:
        return
    store = AuthStore.from_env()
    if store is None:
        return
    store.execute(
        "update web_sessions set revoked_at = now() where session_hash = :session_hash and revoked_at is null",
        {"session_hash": token_hash(session_token)},
    )


def csrf_token(session_token: str | None, action: str = "web") -> str:
    if not session_token:
        return ""
    return hmac.new(
        jwt_secret().encode("utf-8"),
        f"csrf:{action}:{token_hash(session_token)}".encode("utf-8"),
        hashlib.sha256,
    ).hexdigest()


def verify_csrf(session_token: str | None, submitted: str, action: str = "web") -> bool:
    expected = csrf_token(session_token, action)
    return bool(expected) and hmac.compare_digest(expected, submitted)


def issue_token(subject: str, *, role: str = "user", email: str = "", expires_in: int = ACCESS_TOKEN_TTL_SECONDS, secret: str | None = None) -> str:
    now = int(time.time())
    header = {"alg": "HS256", "typ": "JWT"}
    payload = {
        "sub": subject,
        "role": role,
        "email": email,
        "jti": secrets.token_urlsafe(16),
        "iat": now,
        "exp": now + expires_in,
        "iss": "oz-api",
        "aud": "oz-cli",
    }
    signing_input = f"{b64_json(header)}.{b64_json(payload)}"
    signature = sign(signing_input.encode("ascii"), secret or jwt_secret())
    return f"{signing_input}.{signature}"


def token_claims(token: str, *, secret: str | None = None) -> dict[str, Any] | None:
    parts = token.split(".")
    if len(parts) != 3:
        return None
    signing_input = f"{parts[0]}.{parts[1]}".encode("ascii")
    expected = sign(signing_input, secret or jwt_secret())
    if not hmac.compare_digest(expected, parts[2]):
        return None
    try:
        payload = json.loads(b64_decode(parts[1]))
    except (json.JSONDecodeError, ValueError):
        return None
    if int(payload.get("exp", 0)) <= int(time.time()) or payload.get("iss") != "oz-api":
        return None
    return payload


def bearer_token(headers: dict[str, str] | Any) -> str | None:
    authorization = header_value(headers, "Authorization")
    if not authorization:
        return None
    prefix = "Bearer "
    if not authorization.startswith(prefix):
        return None
    return authorization[len(prefix) :]


def upsert_user(email: str) -> AuthPrincipal:
    email = normalize_email(email)
    row = require_auth_store().one(
        """
        insert into users (subject, email, role, last_seen_at)
        values (:subject, :email, 'user', now())
        on conflict (subject) do update
        set email = excluded.email, last_seen_at = now()
        returning id::text as user_id, email, role
        """,
        {"subject": f"email:{email}", "email": email},
    )
    if not row:
        raise AuthError("user_upsert_failed")
    return AuthPrincipal(user_id=str(row["user_id"]), email=str(row["email"] or ""), role=str(row["role"] or "user"))


def set_user_role(email: str, role: str) -> AuthPrincipal:
    if role not in {"user", "admin"}:
        raise AuthError("invalid_role")
    user = upsert_user(email)
    row = require_auth_store().one(
        """
        update users
        set role = :role
        where id = cast(:user_id as uuid)
        returning id::text as user_id, email, role
        """,
        {"user_id": user.user_id, "role": role},
    )
    if not row:
        raise AuthError("user_role_update_failed")
    audit("user_role_set", user_id=str(row["user_id"]), metadata={"role": role})
    return AuthPrincipal(user_id=str(row["user_id"]), email=str(row["email"] or ""), role=str(row["role"] or "user"))


def audit(
    action: str,
    *,
    user_id: str | None = None,
    ip: str = "",
    user_agent: str = "",
    metadata: dict[str, Any] | None = None,
) -> None:
    store = AuthStore.from_env()
    if store is None:
        return
    try:
        store.execute(
            """
            insert into auth_audit_logs (user_id, action, ip_hash, user_agent, metadata_json)
            values (cast(:user_id as uuid), :action, :ip_hash, :user_agent, cast(:metadata as jsonb))
            """,
            {
                "user_id": user_id,
                "action": action,
                "ip_hash": safe_hash(ip) if ip else None,
                "user_agent": user_agent[:240] if user_agent else None,
                "metadata": json.dumps(metadata or {}, sort_keys=True),
            },
        )
    except Exception as exc:
        LOGGER.warning("failed to write auth audit action=%s: %s", action, exc)
        return


def enforce_device_rate_limit(store: AuthStore, ip: str) -> None:
    if not ip:
        return
    count = count_recent(
        store,
        "device_codes",
        "ip_hash = :ip_hash",
        {"ip_hash": safe_hash(ip)},
        window_seconds=10 * 60,
    )
    if count >= 20:
        raise AuthError("rate_limited")


def enforce_password_login_rate_limit(store: AuthStore, email: str, ip: str) -> None:
    email_hash = safe_hash(email)
    email_count = count_recent(
        store,
        "password_login_attempts",
        "email_hash = :email_hash and success = false",
        {"email_hash": email_hash},
        window_seconds=15 * 60,
    )
    if email_count >= 8:
        raise AuthError("rate_limited")
    if not ip:
        return
    ip_count = count_recent(
        store,
        "password_login_attempts",
        "ip_hash = :ip_hash and success = false",
        {"ip_hash": safe_hash(ip)},
        window_seconds=15 * 60,
    )
    if ip_count >= 30:
        raise AuthError("rate_limited")


def record_password_attempt(store: AuthStore, email: str, ip: str, *, success: bool) -> None:
    store.execute(
        """
        insert into password_login_attempts (email_hash, ip_hash, success)
        values (:email_hash, :ip_hash, :success)
        """,
        {"email_hash": safe_hash(email), "ip_hash": safe_hash(ip) if ip else None, "success": success},
    )


def count_recent(
    store: AuthStore,
    table: str,
    where_sql: str,
    parameters: dict[str, Any],
    *,
    window_seconds: int,
) -> int:
    row = store.one(
        f"""
        select count(*) as count
        from {table}
        where {where_sql}
          and created_at > now() - make_interval(secs => :window_seconds)
        """,
        {**parameters, "window_seconds": window_seconds},
    )
    return int(row.get("count") or 0) if row else 0


def create_web_session(
    principal: AuthPrincipal,
    *,
    ip: str = "",
    user_agent: str = "",
    action: str = "web_login",
) -> str:
    session = secrets.token_urlsafe(40)
    require_auth_store().execute(
        """
        insert into web_sessions (user_id, session_hash, expires_at)
        values (cast(:user_id as uuid), :session_hash, now() + make_interval(secs => :ttl))
        """,
        {"user_id": principal.user_id, "session_hash": token_hash(session), "ttl": WEB_SESSION_TTL_SECONDS},
    )
    require_auth_store().execute(
        """
        update users
        set last_seen_at = now(), last_login_at = now()
        where id = cast(:user_id as uuid)
        """,
        {"user_id": principal.user_id},
    )
    audit(action, user_id=principal.user_id, ip=ip, user_agent=user_agent)
    return session


def mark_device_status(device_id: str, status: str) -> None:
    field = "consumed_at" if status == "consumed" else "denied_at" if status == "denied" else None
    timestamp_sql = f", {field} = now()" if field else ""
    require_auth_store().execute(
        f"update device_codes set status = :status{timestamp_sql} where id = cast(:id as uuid)",
        {"status": status, "id": device_id},
    )


def require_auth_store() -> AuthStore:
    store = AuthStore.from_env()
    if store is None:
        raise RuntimeError("owned auth requires DATABASE_URL or OZ_DATABASE_URL")
    return store


def signup_enabled() -> bool:
    return os.environ.get("OZ_SIGNUP_DISABLED", "").lower() not in {"1", "true", "yes", "on"}


def production_env() -> bool:
    return os.environ.get("OZ_ENV", "").lower() in {"prod", "production"}


def public_base_url() -> str:
    value = os.environ.get("OZ_PUBLIC_BASE_URL") or os.environ.get("OZ_API_URL")
    if value:
        return value.rstrip("/")
    if production_env():
        raise RuntimeError("OZ_PUBLIC_BASE_URL is required in production")
    return "http://127.0.0.1:8765"


def public_app_url() -> str:
    return (os.environ.get("OZ_APP_URL") or public_base_url()).rstrip("/")


def normalize_email(email: str) -> str:
    value = email.strip().lower()
    if not re.match(r"^[^@\s]+@[^@\s]+\.[^@\s]+$", value):
        raise AuthError("invalid_email")
    return value


def generate_user_code() -> str:
    alphabet = "ABCDEFGHJKLMNPQRSTUVWXYZ23456789"
    raw = "".join(secrets.choice(alphabet) for _ in range(8))
    return f"{raw[:4]}-{raw[4:]}"


def normalize_user_code(value: str) -> str:
    return re.sub(r"[^A-Z0-9]", "", value.upper())


def validate_password(password: str) -> None:
    if len(password) < PASSWORD_MIN_LENGTH:
        raise AuthError(f"password_must_be_at_least_{PASSWORD_MIN_LENGTH}_characters")
    if password.strip() != password:
        raise AuthError("password_cannot_start_or_end_with_space")


def hash_password(password: str) -> str:
    validate_password(password)
    try:
        from argon2 import PasswordHasher  # type: ignore
    except ImportError as exc:
        raise RuntimeError("argon2-cffi is required for password auth") from exc
    return PasswordHasher(time_cost=3, memory_cost=65536, parallelism=2).hash(password)


def verify_password(password: str, password_hash: str) -> bool:
    if not password_hash:
        return False
    try:
        from argon2 import PasswordHasher  # type: ignore
        from argon2.exceptions import Argon2Error, VerifyMismatchError  # type: ignore
    except ImportError:
        return False
    try:
        return PasswordHasher().verify(password_hash, password)
    except VerifyMismatchError:
        return False
    except (Argon2Error, ValueError):
        return False


def token_hash(value: str) -> str:
    return hmac.new(jwt_secret().encode("utf-8"), value.encode("utf-8"), hashlib.sha256).hexdigest()


def safe_hash(value: str) -> str:
    return hashlib.sha256(value.encode("utf-8")).hexdigest()


def header_value(headers: dict[str, str] | Any, key: str) -> str | None:
    if hasattr(headers, "get"):
        return headers.get(key) or headers.get(key.lower())
    return None


def b64_json(value: dict[str, Any]) -> str:
    return b64_encode(json.dumps(value, separators=(",", ":"), sort_keys=True).encode("utf-8"))


def b64_encode(value: bytes) -> str:
    return base64.urlsafe_b64encode(value).decode("ascii").rstrip("=")


def b64_decode(value: str) -> bytes:
    padding = "=" * ((4 - len(value) % 4) % 4)
    return base64.urlsafe_b64decode((value + padding).encode("ascii"))


def sign(value: bytes, secret: str) -> str:
    return b64_encode(hmac.new(secret.encode("utf-8"), value, hashlib.sha256).digest())


class AuthError(RuntimeError):
    pass
