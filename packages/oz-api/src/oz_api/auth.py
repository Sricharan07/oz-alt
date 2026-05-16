from __future__ import annotations

import base64
import hashlib
import hmac
import json
import os
import time
from typing import Any

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
