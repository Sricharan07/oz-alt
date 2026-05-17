from __future__ import annotations

import os
from typing import Any


def redis_client() -> Any | None:
    url = os.environ.get("OZ_REDIS_URL") or os.environ.get("REDIS_URL")
    if not url:
        return None
    try:
        import redis  # type: ignore
    except ImportError:
        return None
    try:
        return redis.Redis.from_url(url, decode_responses=True)
    except Exception:
        return None


def redis_key(name: str, default: str) -> str:
    return os.environ.get(name, default)
