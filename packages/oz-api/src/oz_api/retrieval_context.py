from __future__ import annotations

import json
import os
from dataclasses import dataclass
from typing import Any

from oz_api.storage import RegistryStorage

_OPENAI_API_KEY_CACHE: str | None = None


@dataclass(frozen=True)
class RetrievalContext:
    storage: RegistryStorage
    database_url: str | None = None
    redis_url: str | None = None
    openai_api_key: str | None = None
    voyage_api_key: str | None = None
    jina_api_key: str | None = None
    cohere_api_key: str | None = None
    zeroentropy_api_key: str | None = None

    @classmethod
    def from_env(cls, storage: RegistryStorage) -> "RetrievalContext":
        return cls(
            storage=storage,
            database_url=os.environ.get("OZ_DATABASE_URL") or os.environ.get("DATABASE_URL"),
            redis_url=os.environ.get("OZ_REDIS_URL") or os.environ.get("REDIS_URL"),
            openai_api_key=openai_api_key_from_env(),
            voyage_api_key=normalized_api_key(os.environ.get("VOYAGE_API_KEY") or os.environ.get("OZ_VOYAGE_API_KEY")),
            jina_api_key=normalized_api_key(os.environ.get("JINA_API_KEY") or os.environ.get("OZ_JINA_API_KEY")),
            cohere_api_key=normalized_api_key(os.environ.get("COHERE_API_KEY") or os.environ.get("OZ_COHERE_API_KEY")),
            zeroentropy_api_key=normalized_api_key(
                os.environ.get("ZEROENTROPY_API_KEY") or os.environ.get("OZ_ZEROENTROPY_API_KEY")
            ),
        )

def openai_api_key_from_env() -> str | None:
    direct = normalized_openai_api_key(os.environ.get("OPENAI_API_KEY"))
    if direct:
        return direct

    secret_arn = os.environ.get("OPENAI_API_KEY_SECRET_ARN") or os.environ.get("OZ_OPENAI_API_KEY_SECRET_ARN")
    if not secret_arn:
        return None

    global _OPENAI_API_KEY_CACHE
    if _OPENAI_API_KEY_CACHE is not None:
        return _OPENAI_API_KEY_CACHE

    try:
        import boto3  # type: ignore

        response = boto3.client("secretsmanager").get_secret_value(SecretId=secret_arn)
    except Exception:
        return None

    value = secret_value_text(response)
    key = normalized_openai_api_key(value)
    if not key:
        key = normalized_openai_api_key_from_json(value)
    if key:
        _OPENAI_API_KEY_CACHE = key
    return key

def secret_value_text(response: dict[str, Any]) -> str:
    if response.get("SecretString"):
        return str(response["SecretString"])
    binary = response.get("SecretBinary")
    if isinstance(binary, bytes):
        return binary.decode("utf-8", errors="replace")
    return ""

def normalized_openai_api_key(value: str | None) -> str | None:
    key = str(value or "").strip()
    return key if key.startswith("sk-") else None

def normalized_api_key(value: str | None) -> str | None:
    key = str(value or "").strip()
    return key or None

def normalized_openai_api_key_from_json(value: str) -> str | None:
    try:
        payload = json.loads(value)
    except Exception:
        return None
    if not isinstance(payload, dict):
        return None
    for field in ("OPENAI_API_KEY", "openai_api_key", "api_key"):
        key = normalized_openai_api_key(payload.get(field))
        if key:
            return key
    return None
