from __future__ import annotations

import hashlib
import json
import logging
import os
from typing import Any

from oz_api.retrieval_metrics import metric_prefix
from oz_api.redis_store import redis_client

LOGGER = logging.getLogger(__name__)
CACHE_VERSION = "retrieval-v5"


def get_cached_results(route: str, query: str, scope: str | None, max_results: int, variant: str) -> list[dict[str, Any]] | None:
    client = redis_client()
    if client is None:
        return None
    try:
        payload = client.get(cache_key(route, query, scope, max_results, variant))
    except Exception as exc:
        LOGGER.info("retrieval cache read failed route=%s: %s", route, exc)
        return None
    if not payload:
        return None
    try:
        parsed = json.loads(payload)
    except (TypeError, json.JSONDecodeError):
        return None
    if not isinstance(parsed, list):
        return None
    try:
        client.incr(f"{metric_prefix(route, variant)}:cache_hit")
    except Exception:
        pass
    return parsed


def put_cached_results(
    route: str,
    query: str,
    scope: str | None,
    max_results: int,
    variant: str,
    rows: list[dict[str, Any]],
) -> None:
    client = redis_client()
    if client is None:
        return
    ttl = cache_ttl_seconds()
    if ttl <= 0:
        return
    try:
        client.setex(cache_key(route, query, scope, max_results, variant), ttl, json.dumps(rows, sort_keys=True))
    except Exception as exc:
        LOGGER.info("retrieval cache write failed route=%s: %s", route, exc)


def cache_key(route: str, query: str, scope: str | None, max_results: int, variant: str) -> str:
    payload = "\0".join([CACHE_VERSION, route, query, scope or "", str(max_results), variant])
    return "oz:retrieval:" + hashlib.sha256(payload.encode("utf-8")).hexdigest()


def cache_ttl_seconds() -> int:
    try:
        return max(0, int(os.environ.get("OZ_RETRIEVAL_CACHE_TTL_SECONDS", "300")))
    except ValueError:
        return 300
