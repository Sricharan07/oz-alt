from __future__ import annotations

import logging
import os
from typing import Any

LOGGER = logging.getLogger(__name__)


def redis_client() -> Any | None:
    url = os.environ.get("OZ_REDIS_URL") or os.environ.get("REDIS_URL")
    if not url:
        return None
    try:
        import redis  # type: ignore
    except ImportError as exc:
        LOGGER.warning("redis package is unavailable: %s", exc)
        return None
    try:
        return redis.Redis.from_url(url, decode_responses=True)
    except Exception as exc:
        LOGGER.warning("failed to create redis client: %s", exc)
        return None


def redis_key(name: str, default: str) -> str:
    return os.environ.get(name, default)
