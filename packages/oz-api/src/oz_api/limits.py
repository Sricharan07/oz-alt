from __future__ import annotations

import logging
import os
import time

from oz_api.redis_store import redis_client

LOGGER = logging.getLogger(__name__)
_REDIS_FAILURES = 0
_REDIS_CIRCUIT_OPEN_UNTIL = 0.0


def index_request_allowed(requesting_user: str, *, limit: int = 20) -> bool:
    return redis_index_request_allowed(requesting_user, limit=limit)


def rate_limit_allowed(scope: str, identity: str, *, limit: int, window_seconds: int = 60) -> bool:
    if redis_circuit_open():
        LOGGER.warning("redis rate-limit circuit open; allowing request scope=%s", scope)
        return True
    client = redis_client()
    if client is None:
        return redis_unavailable_decision(scope, record_failure=True)
    safe_scope = "".join(char if char.isalnum() or char in {":", "-", "_"} else "_" for char in scope)
    key = f"oz:rate:{safe_scope}:{identity or 'anonymous'}"
    try:
        count = int(client.incr(key))
        if count == 1:
            client.expire(key, window_seconds)
        reset_redis_failures()
        return count <= limit
    except Exception as exc:
        LOGGER.warning("redis rate limit failed for scope=%s: %s", scope, exc)
        return redis_unavailable_decision(scope, record_failure=True)


def redis_index_request_allowed(requesting_user: str, *, limit: int) -> bool:
    if redis_circuit_open():
        LOGGER.warning("redis rate-limit circuit open; allowing index request")
        return True
    client = redis_client()
    if client is None:
        return redis_unavailable_decision("index-request", record_failure=True)
    key = f"oz:rate:index-request:{requesting_user or 'anonymous'}"
    try:
        count = int(client.incr(key))
        if count == 1:
            client.expire(key, 60 * 60)
        reset_redis_failures()
        return count <= limit
    except Exception as exc:
        LOGGER.warning("redis index-request rate limit failed: %s", exc)
        return redis_unavailable_decision("index-request", record_failure=True)


def redis_unavailable_decision(scope: str, *, record_failure: bool = False) -> bool:
    if record_failure and note_redis_failure() and redis_circuit_open():
        return True
    if scope.startswith(("auth:", "admin:", "index-request")):
        return False
    return True


def note_redis_failure() -> bool:
    global _REDIS_FAILURES, _REDIS_CIRCUIT_OPEN_UNTIL
    _REDIS_FAILURES += 1
    threshold = int_env("OZ_REDIS_RATE_LIMIT_CIRCUIT_FAILURES", 3)
    if _REDIS_FAILURES >= threshold:
        _REDIS_CIRCUIT_OPEN_UNTIL = time.time() + int_env("OZ_REDIS_RATE_LIMIT_CIRCUIT_SECONDS", 60)
        LOGGER.warning("redis rate-limit circuit opened after %s consecutive failures", _REDIS_FAILURES)
        return True
    return False


def redis_circuit_open() -> bool:
    return _REDIS_CIRCUIT_OPEN_UNTIL > time.time()


def reset_redis_failures() -> None:
    global _REDIS_FAILURES, _REDIS_CIRCUIT_OPEN_UNTIL
    _REDIS_FAILURES = 0
    _REDIS_CIRCUIT_OPEN_UNTIL = 0.0


def int_env(name: str, default: int) -> int:
    try:
        return int(os.environ.get(name, str(default)))
    except ValueError:
        return default
