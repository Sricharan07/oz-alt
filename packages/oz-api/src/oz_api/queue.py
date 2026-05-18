from __future__ import annotations

import json
import os
from datetime import datetime, timezone
from typing import TYPE_CHECKING, Any

from oz_api.auth_store import AuthStore
from oz_api.redis_store import redis_client, redis_key
from oz_api.storage import RegistryStorage

if TYPE_CHECKING:
    from oz_api.auth import AuthPrincipal


def enqueue_crawler_job(
    storage: RegistryStorage,
    payload: dict[str, Any],
    principal: "AuthPrincipal | None" = None,
) -> dict[str, Any]:
    event = crawler_job_event(payload)
    missing = missing_required_crawler_fields(event)
    if missing:
        raise ValueError(f"missing crawler job fields: {', '.join(missing)}")
    db_job_id = create_crawler_job_record(event, principal)
    if db_job_id:
        event["db_job_id"] = db_job_id
    message_id = send_redis_message(event)
    if message_id:
        event["queue_message_id"] = message_id
        event["queue_backend"] = "redis"
        update_crawler_job_queue_message(db_job_id, message_id)
    else:
        raise RuntimeError("Redis crawler queue is not configured")
    return event


def requeue_queued_crawler_jobs(*, limit: int = 10) -> int:
    store = AuthStore.from_env()
    if store is None:
        return 0
    rows = store.execute(
        """
        select j.id,
               j.source_url,
               j.version,
               j.max_pages,
               j.fetcher,
               j.concurrent_requests,
               j.download_delay,
               j.robots_txt,
               v.name as vendor,
               l.name as library_name,
               p.allowed_hosts,
               p.allowed_paths,
               p.denied_paths,
               p.source_priority,
               p.required_topics,
               p.expected_symbols,
               p.source_file_patterns,
               p.min_quality_score,
               p.min_documents,
               p.max_junk_ratio,
               p.needs_js,
               p.include_source_files,
               p.target_language
        from crawler_jobs j
        join libraries l on l.id = j.library_id
        join vendors v on v.id = l.vendor_id
        left join library_profiles p on p.library_id = l.id
        where j.status = 'queued'
        order by j.queued_at asc, j.id asc
        limit :limit
        """,
        {"limit": max(1, limit)},
    )
    requeued = 0
    for row in rows:
        event = queued_crawler_job_event(row)
        message_id = send_redis_message(event)
        if not message_id:
            continue
        update_crawler_job_queue_message(str(row["id"]), message_id)
        requeued += 1
    return requeued


def queued_crawler_job_event(row: dict[str, Any]) -> dict[str, Any]:
    event = {
        "created_at": now(),
        "status": "queued",
        "db_job_id": str(row["id"]),
        "library_name": row.get("library_name"),
        "vendor": row.get("vendor"),
        "source_url": row.get("source_url"),
        "version": row.get("version") or "latest",
        "max_pages": row.get("max_pages"),
        "fetcher": row.get("fetcher"),
        "concurrent_requests": row.get("concurrent_requests"),
        "download_delay": row.get("download_delay"),
        "robots_txt": row.get("robots_txt"),
    }
    profile = profile_from_row(row)
    if profile:
        event["profile"] = profile
    return strip_empty_values(event)


def profile_from_row(row: dict[str, Any]) -> dict[str, Any] | None:
    if row.get("allowed_hosts") is None:
        return None
    return {
        "allowed_hosts": row.get("allowed_hosts") or [],
        "allowed_paths": row.get("allowed_paths") or [],
        "denied_paths": row.get("denied_paths") or [],
        "source_priority": row.get("source_priority") or [],
        "required_topics": row.get("required_topics") or [],
        "expected_symbols": row.get("expected_symbols") or [],
        "source_file_patterns": row.get("source_file_patterns") or [],
        "min_quality_score": row.get("min_quality_score", 0.35),
        "min_documents": row.get("min_documents", 2),
        "max_junk_ratio": row.get("max_junk_ratio", 0.25),
        "needs_js": bool(row.get("needs_js")),
        "include_source_files": bool(row.get("include_source_files")),
        "target_language": row.get("target_language") or "en",
    }


def crawler_job_event(payload: dict[str, Any]) -> dict[str, Any]:
    return {
        "created_at": now(),
        "status": "queued",
        "library_name": payload.get("library_name") or payload.get("library"),
        "vendor": payload.get("vendor") or payload.get("vendor_hint"),
        "source_url": payload.get("source_url") or payload.get("source_url_hint"),
        "version": payload.get("version") or "latest",
        "max_pages": payload.get("max_pages"),
        "fetcher": payload.get("fetcher"),
        "concurrent_requests": payload.get("concurrent_requests"),
        "download_delay": payload.get("download_delay"),
        "robots_txt": payload.get("robots_txt"),
        "needs_js": payload.get("needs_js"),
        "include_source_files": payload.get("include_source_files"),
        "target_language": payload.get("target_language"),
        "profile": payload.get("profile"),
    }


def missing_required_crawler_fields(event: dict[str, Any]) -> list[str]:
    required = ["vendor", "library_name", "source_url"]
    return [field for field in required if not event.get(field)]


def send_redis_message(event: dict[str, Any]) -> str | None:
    client = redis_client()
    if client is None:
        return None
    queue_name = redis_key("OZ_CRAWLER_REDIS_QUEUE", "oz:crawler:jobs")
    message = json.dumps(strip_empty_values(event), sort_keys=True)
    try:
        length = client.rpush(queue_name, message)
    except Exception:
        return None
    return f"{queue_name}:{length}"


def create_crawler_job_record(event: dict[str, Any], principal: "AuthPrincipal | None") -> str | None:
    store = AuthStore.from_env()
    if store is None:
        raise RuntimeError("DATABASE_URL or OZ_DATABASE_URL is required")
    row = store.one(
        """
        with vendor_row as (
          insert into vendors(name)
          values (:vendor)
          on conflict (name) do update set name = excluded.name
          returning id
        ),
        library_row as (
          insert into libraries(vendor_id, name, description, source_url)
          select id, :library, :description, :source_url
          from vendor_row
          on conflict (vendor_id, name) do update
          set source_url = coalesce(excluded.source_url, libraries.source_url),
              updated_at = now()
          returning id
        )
        insert into crawler_jobs (
          library_id,
          source_url,
          status,
          max_pages,
          requested_by,
          version,
          fetcher,
          concurrent_requests,
          download_delay,
          robots_txt
        )
        select
          id,
          :source_url,
          'queued',
          :max_pages,
          cast(:requested_by as uuid),
          :version,
          :fetcher,
          :concurrent_requests,
          :download_delay,
          :robots_txt
        from library_row
        returning id
        """,
        {
            "vendor": str(event["vendor"]),
            "library": str(event["library_name"]),
            "description": f"Documentation crawled from {event['source_url']}.",
            "source_url": str(event["source_url"]),
            "max_pages": int_value(event.get("max_pages"), default=128, minimum=1),
            "requested_by": principal.user_id if principal else None,
            "version": str(event.get("version") or "latest"),
            "fetcher": event.get("fetcher"),
            "concurrent_requests": optional_int(event.get("concurrent_requests"), minimum=1),
            "download_delay": optional_float(event.get("download_delay"), minimum=0),
            "robots_txt": optional_bool(event.get("robots_txt")),
        },
    )
    if not row:
        raise RuntimeError("crawler job record was not created")
    return str(row["id"])


def update_crawler_job_queue_message(job_id: str | None, message_id: str) -> None:
    if not job_id:
        return
    store = AuthStore.from_env()
    if store is None:
        return
    try:
        store.execute(
            "update crawler_jobs set queue_message_id = :message_id where id = cast(:job_id as bigint)",
            {"message_id": message_id, "job_id": job_id},
        )
    except Exception:
        return


def strip_empty_values(event: dict[str, Any]) -> dict[str, Any]:
    return {key: value for key, value in event.items() if value is not None and value != ""}


def int_value(value: Any, *, default: int, minimum: int) -> int:
    parsed = optional_int(value, minimum=minimum)
    return parsed if parsed is not None else default


def optional_int(value: Any, *, minimum: int) -> int | None:
    if value is None or value == "":
        return None
    try:
        parsed = int(value)
    except (TypeError, ValueError):
        return None
    return max(minimum, parsed)


def optional_float(value: Any, *, minimum: float) -> float | None:
    if value is None or value == "":
        return None
    try:
        parsed = float(value)
    except (TypeError, ValueError):
        return None
    return max(minimum, parsed)


def optional_bool(value: Any) -> bool | None:
    if value is None or value == "":
        return None
    if isinstance(value, bool):
        return value
    return str(value).strip().lower() not in {"0", "false", "no", "off"}


def now() -> str:
    return datetime.now(timezone.utc).isoformat()
