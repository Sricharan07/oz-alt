from __future__ import annotations

from oz_api.redis_store import redis_client


def index_request_allowed(requesting_user: str, *, limit: int = 20) -> bool:
    return redis_index_request_allowed(requesting_user, limit=limit)


def rate_limit_allowed(scope: str, identity: str, *, limit: int, window_seconds: int = 60) -> bool:
    client = redis_client()
    if client is None:
        return False
    safe_scope = "".join(char if char.isalnum() or char in {":", "-", "_"} else "_" for char in scope)
    key = f"oz:rate:{safe_scope}:{identity or 'anonymous'}"
    try:
        count = int(client.incr(key))
        if count == 1:
            client.expire(key, window_seconds)
        return count <= limit
    except Exception:
        return False


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
    except Exception:
        return False
