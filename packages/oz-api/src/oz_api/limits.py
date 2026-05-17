from __future__ import annotations

import logging

from oz_api.redis_store import redis_client

LOGGER = logging.getLogger(__name__)


def index_request_allowed(requesting_user: str, *, limit: int = 20) -> bool:
    return redis_index_request_allowed(requesting_user, limit=limit)


def rate_limit_allowed(scope: str, identity: str, *, limit: int, window_seconds: int = 60) -> bool:
    client = redis_client()
    if client is None:
        return redis_unavailable_decision(scope)
    safe_scope = "".join(char if char.isalnum() or char in {":", "-", "_"} else "_" for char in scope)
    key = f"oz:rate:{safe_scope}:{identity or 'anonymous'}"
    try:
        count = int(client.incr(key))
        if count == 1:
            client.expire(key, window_seconds)
        return count <= limit
    except Exception as exc:
        LOGGER.warning("redis rate limit failed for scope=%s: %s", scope, exc)
        return redis_unavailable_decision(scope)


def redis_index_request_allowed(requesting_user: str, *, limit: int) -> bool:
    client = redis_client()
    if client is None:
        return False
    key = f"oz:rate:index-request:{requesting_user or 'anonymous'}"
    try:
        count = int(client.incr(key))
        if count == 1:
            client.expire(key, 60 * 60)
        return count <= limit
    except Exception as exc:
        LOGGER.warning("redis index-request rate limit failed: %s", exc)
        return False


def redis_unavailable_decision(scope: str) -> bool:
    if scope.startswith(("auth:", "admin:")):
        return False
    return True
