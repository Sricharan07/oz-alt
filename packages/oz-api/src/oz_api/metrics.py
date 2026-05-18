from __future__ import annotations

import os
from typing import Any

from oz_api.auth_store import AuthStore
from oz_api.observability import histogram_metric_values
from oz_api.redis_store import redis_client, redis_key
from oz_api.retrieval_metrics import retrieval_latency_metric_values


def metrics_authorized(headers: Any) -> bool:
    token = os.environ.get("OZ_METRICS_TOKEN", "").strip()
    if not token:
        return False
    expected = f"Bearer {token}"
    return str(headers.get("Authorization") or "") == expected


def render_prometheus_metrics() -> str:
    rows = collect_metric_values()
    lines = [
        "# HELP oz_build_info Static build metadata for this Oz deployment.",
        "# TYPE oz_build_info gauge",
        metric_line("oz_build_info", 1, {"service": "oz"}),
    ]
    for name, value in rows.items():
        lines.append(f"# TYPE {name} gauge")
        lines.append(metric_line(name, value))
    emitted_types = set()
    for (name, labels), value in retrieval_latency_metric_values().items():
        type_name, metric_type = prometheus_type(name)
        if type_name not in emitted_types:
            lines.append(f"# TYPE {type_name} {metric_type}")
            emitted_types.add(type_name)
        lines.append(metric_line(name, value, dict(labels)))
    for (name, labels), value in histogram_metric_values().items():
        type_name, metric_type = prometheus_type(name)
        if type_name not in emitted_types:
            lines.append(f"# TYPE {type_name} {metric_type}")
            emitted_types.add(type_name)
        lines.append(metric_line(name, value, dict(labels)))
    return "\n".join(lines) + "\n"


def prometheus_type(name: str) -> tuple[str, str]:
    for suffix in ("_bucket", "_sum", "_count"):
        if name.endswith(suffix):
            return name.removesuffix(suffix), "histogram"
    if name.endswith("_total"):
        return name, "counter"
    return name, "gauge"


def collect_metric_values() -> dict[str, float]:
    values: dict[str, float] = {
        "oz_redis_up": 1.0 if redis_up() else 0.0,
        "oz_crawler_queue_depth": float(redis_queue_depth()),
    }
    values.update(db_metrics())
    return values


def db_metrics() -> dict[str, float]:
    store = AuthStore.from_env()
    if store is None:
        return {"oz_postgres_up": 0.0}
    try:
        row = store.one(
            """
            select
              (select count(*) from libraries)::float as libraries,
              (select count(*) from chunks)::float as chunks,
              (select count(*) from crawler_jobs where status = 'queued')::float as crawler_queued,
              (select count(*) from crawler_jobs where status = 'running')::float as crawler_running,
              (select count(*) from crawler_jobs where status = 'failed')::float as crawler_failed_total,
              (select count(*) from search_quality_runs where created_at > now() - interval '7 days')::float as search_quality_runs_7d,
              (select count(*) from search_quality_runs where created_at > now() - interval '7 days' and passed)::float as search_quality_passed_7d,
              (select count(*) from system_checks where status = 'fail' and created_at > now() - interval '1 hour')::float as system_check_failures_1h,
              (select count(*) from ops_alerts where status = 'open')::float as open_alerts,
              (select count(*) from backup_runs where status = 'verified' and restore_verified_at > now() - interval '30 hours')::float as fresh_verified_backups
            """
        )
    except Exception:
        return {"oz_postgres_up": 0.0}
    row = row or {}
    search_total = float(row.get("search_quality_runs_7d") or 0)
    search_passed = float(row.get("search_quality_passed_7d") or 0)
    return {
        "oz_postgres_up": 1.0,
        "oz_libraries_total": float(row.get("libraries") or 0),
        "oz_chunks_total": float(row.get("chunks") or 0),
        "oz_crawler_jobs_queued": float(row.get("crawler_queued") or 0),
        "oz_crawler_jobs_running": float(row.get("crawler_running") or 0),
        "oz_crawler_jobs_failed_total": float(row.get("crawler_failed_total") or 0),
        "oz_search_quality_pass_rate_7d": search_passed / search_total if search_total else 0.0,
        "oz_system_check_failures_1h": float(row.get("system_check_failures_1h") or 0),
        "oz_open_alerts": float(row.get("open_alerts") or 0),
        "oz_fresh_verified_backups": float(row.get("fresh_verified_backups") or 0),
    }


def redis_up() -> bool:
    client = redis_client()
    if client is None:
        return False
    try:
        return bool(client.ping())
    except Exception:
        return False


def redis_queue_depth() -> int:
    client = redis_client()
    if client is None:
        return 0
    try:
        return int(client.llen(redis_key("OZ_CRAWLER_REDIS_QUEUE", "oz:crawler:jobs")))
    except Exception:
        return 0


def metric_line(name: str, value: float, labels: dict[str, str] | None = None) -> str:
    label_text = ""
    if labels:
        pairs = [f'{key}="{escape_label(value)}"' for key, value in sorted(labels.items())]
        label_text = "{" + ",".join(pairs) + "}"
    return f"{name}{label_text} {float(value):.6g}"


def escape_label(value: str) -> str:
    return value.replace("\\", "\\\\").replace('"', '\\"').replace("\n", "\\n")
