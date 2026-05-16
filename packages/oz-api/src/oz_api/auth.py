from __future__ import annotations

import base64
import hashlib
import hmac
import json
import os
import time
from typing import Any
from urllib import request, parse

_JWT_SECRET_CACHE: str | None = None


def jwt_secret() -> str:
    global _JWT_SECRET_CACHE
    if _JWT_SECRET_CACHE:
        return _JWT_SECRET_CACHE
    direct_secret = os.environ.get("OZ_JWT_SECRET")
    if direct_secret:
        _JWT_SECRET_CACHE = direct_secret
        return direct_secret
    secret_arn = os.environ.get("OZ_JWT_SECRET_ARN")
    if secret_arn:
        try:
            import boto3  # type: ignore

            response = boto3.client("secretsmanager").get_secret_value(SecretId=secret_arn)
            _JWT_SECRET_CACHE = str(response.get("SecretString") or "")
            if _JWT_SECRET_CACHE:
                return _JWT_SECRET_CACHE
        except Exception:
            pass
    _JWT_SECRET_CACHE = os.environ.get("OZ_JWT_SECRET", "local-dev-secret")
    return _JWT_SECRET_CACHE


def issue_token(subject: str, *, expires_in: int = 86400, secret: str | None = None) -> str:
    now = int(time.time())
    header = {"alg": "HS256", "typ": "JWT"}
    payload = {
        "sub": subject,
        "iat": now,
        "exp": now + expires_in,
        "iss": "oz-api",
        "aud": "oz-cli",
    }
    signing_input = f"{b64_json(header)}.{b64_json(payload)}"
    signature = sign(signing_input.encode("ascii"), secret or jwt_secret())
    return f"{signing_input}.{signature}"


def verify_token(token: str, *, secret: str | None = None) -> bool:
    parts = token.split(".")
    if len(parts) != 3:
        return False
    signing_input = f"{parts[0]}.{parts[1]}".encode("ascii")
    expected = sign(signing_input, secret or jwt_secret())
    if not hmac.compare_digest(expected, parts[2]):
        return False
    try:
        payload = json.loads(b64_decode(parts[1]))
    except Exception:
        return False
    return int(payload.get("exp", 0)) > int(time.time()) and payload.get("iss") == "oz-api"


def bearer_token(headers: dict[str, str] | Any) -> str | None:
    authorization = header_value(headers, "Authorization")
    if not authorization:
        return None
    prefix = "Bearer "
    if not authorization.startswith(prefix):
        return None
    return authorization[len(prefix) :]


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


def oauth_configured() -> bool:
    return bool(
        os.environ.get("OZ_OAUTH_DEVICE_AUTH_URL")
        and os.environ.get("OZ_OAUTH_TOKEN_URL")
        and os.environ.get("OZ_OAUTH_CLIENT_ID")
    )


def oauth_required() -> bool:
    return os.environ.get("OZ_REQUIRE_OAUTH", "").lower() in {"1", "true", "yes", "on"}


def start_device_authorization() -> dict[str, Any]:
    if not oauth_configured():
        if oauth_required():
            raise RuntimeError("OAuth device flow is required but not configured")
        return {
            "device_code": "local-device-code",
            "user_code": "LOCAL-OZ",
            "verification_uri": os.environ.get("OZ_VERIFY_URL", "http://127.0.0.1:8765/auth/verify"),
            "interval": 1,
            "expires_in": 600,
        }

    body = {
        "client_id": os.environ["OZ_OAUTH_CLIENT_ID"],
        "scope": os.environ.get("OZ_OAUTH_SCOPE", "openid profile email"),
    }
    return post_form(os.environ["OZ_OAUTH_DEVICE_AUTH_URL"], body)


def exchange_device_code(device_code: str) -> dict[str, Any]:
    if not oauth_configured():
        if oauth_required():
            raise RuntimeError("OAuth device flow is required but not configured")
        if device_code != "local-device-code":
            return {"error": "invalid_device_code"}
        return {"access_token": issue_token("local-dev-device"), "token_type": "Bearer", "expires_in": 86400}

    provider = post_form(
        os.environ["OZ_OAUTH_TOKEN_URL"],
        {
            "grant_type": "urn:ietf:params:oauth:grant-type:device_code",
            "client_id": os.environ["OZ_OAUTH_CLIENT_ID"],
            "device_code": device_code,
        },
        tolerate_http_error=True,
    )
    if provider.get("error"):
        return provider

    provider_access_token = str(provider.get("access_token") or "")
    if not provider_access_token:
        return {"error": "invalid_token_response"}
    subject = f"oauth:{hashlib.sha256(provider_access_token.encode('utf-8')).hexdigest()[:32]}"
    expires_in = int(provider.get("expires_in") or 86400)
    return {
        "access_token": issue_token(subject, expires_in=expires_in),
        "token_type": "Bearer",
        "expires_in": expires_in,
    }


def post_form(url: str, body: dict[str, Any], *, tolerate_http_error: bool = False) -> dict[str, Any]:
    data = parse.urlencode(body).encode("utf-8")
    req = request.Request(
        url,
        data=data,
        headers={"content-type": "application/x-www-form-urlencoded", "accept": "application/json"},
        method="POST",
    )
    try:
        with request.urlopen(req, timeout=10) as response:
            return json.loads(response.read().decode("utf-8"))
    except Exception as exc:
        if tolerate_http_error and hasattr(exc, "read"):
            try:
                return json.loads(exc.read().decode("utf-8"))  # type: ignore[attr-defined]
            except Exception:
                pass
        raise
