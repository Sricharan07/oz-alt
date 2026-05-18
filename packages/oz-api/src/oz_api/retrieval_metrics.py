from __future__ import annotations

import logging
import os

from oz_api.redis_store import redis_client

LOGGER = logging.getLogger(__name__)
BUCKETS_SECONDS = (0.05, 0.1, 0.25, 0.5, 1.0, 2.5, 5.0, 10.0)


def record_retrieval_latency(route: str, variant: str, elapsed_seconds: float, *, cache_hit: bool = False) -> None:
    client = redis_client()
    if client is None:
        return
    try:
        pipe = client.pipeline()
        prefix = metric_prefix(route, variant)
        pipe.incrbyfloat(f"{prefix}:sum", elapsed_seconds)
        pipe.incr(f"{prefix}:count")
        if cache_hit:
            pipe.incr(f"{prefix}:cache_hit")
        for bucket in BUCKETS_SECONDS:
            if elapsed_seconds <= bucket:
                pipe.incr(f"{prefix}:bucket:{bucket}")
        pipe.incr(f"{prefix}:bucket:+Inf")
        pipe.execute()
    except Exception as exc:
        LOGGER.info("retrieval latency metric write failed route=%s variant=%s: %s", route, variant, exc)


def retrieval_latency_metric_values() -> dict[tuple[str, tuple[tuple[str, str], ...]], float]:
    client = redis_client()
    if client is None:
        return {}
    output: dict[tuple[str, tuple[tuple[str, str], ...]], float] = {}
    try:
        keys = list(client.scan_iter("oz:metrics:retrieval:*:count"))
        for count_key in keys:
            parts = str(count_key).split(":")
            if len(parts) < 6:
                continue
            route = parts[3]
            variant = parts[4]
            prefix = ":".join(parts[:-1])
            labels = (("route", route), ("variant", variant))
            count = float(client.get(count_key) or 0)
            total = float(client.get(f"{prefix}:sum") or 0)
            output[("oz_retrieval_latency_seconds_count", labels)] = count
            output[("oz_retrieval_latency_seconds_sum", labels)] = total
            output[("oz_retrieval_cache_hits_total", labels)] = float(client.get(f"{prefix}:cache_hit") or 0)
            cumulative = 0.0
            for bucket in [*BUCKETS_SECONDS, "+Inf"]:
                value = float(client.get(f"{prefix}:bucket:{bucket}") or 0)
                cumulative = max(cumulative, value)
                output[("oz_retrieval_latency_seconds_bucket", (*labels, ("le", str(bucket))))] = cumulative
    except Exception as exc:
        LOGGER.info("retrieval latency metric read failed: %s", exc)
    return output


def metric_prefix(route: str, variant: str) -> str:
    return f"oz:metrics:retrieval:{safe_label(route)}:{safe_label(variant)}"


def safe_label(value: str) -> str:
    return "".join(char if char.isalnum() or char in {"_", "-"} else "_" for char in value)[:80] or "unknown"


def retrieval_statement_timeout_ms() -> int:
    try:
        return max(1, int(os.environ.get("OZ_RETRIEVAL_STATEMENT_TIMEOUT_MS", "1500")))
    except ValueError:
        return 1500
