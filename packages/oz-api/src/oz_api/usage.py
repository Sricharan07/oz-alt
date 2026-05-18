from __future__ import annotations

import hashlib
import json
from typing import Any

from oz_api.auth import AuthPrincipal
from oz_api.auth_store import AuthStore


def record_usage_event(
    principal: AuthPrincipal | None,
    event: str,
    *,
    library: str | None = None,
    query_length: int | None = None,
    result_count: int | None = None,
    project_fingerprint: str = "",
    properties: dict[str, Any] | None = None,
) -> None:
    store = AuthStore.from_env()
    if store is None:
        return
    try:
        store.execute(
            """
            insert into usage_events (
              user_id,
              event,
              library,
              query_length,
              result_count,
              project_fingerprint_hash,
              properties
            )
            values (
              cast(:user_id as uuid),
              :event,
              :library,
              :query_length,
              :result_count,
              :project_fingerprint_hash,
              cast(:properties as jsonb)
            )
            """,
            {
                "user_id": principal.user_id if principal else None,
                "event": event[:120],
                "library": library[:240] if library else None,
                "query_length": query_length,
                "result_count": result_count,
                "project_fingerprint_hash": sha256(project_fingerprint) if project_fingerprint else None,
                "properties": json.dumps(properties or {}, sort_keys=True),
            },
        )
        store.execute(
            """
            insert into usage_daily (day, user_id, event, library, count)
            values (current_date, cast(:user_id as uuid), :event, :library, 1)
            on conflict (day, user_id, event, library) do update
            set count = usage_daily.count + 1
            """,
            {
                "user_id": principal.user_id if principal else None,
                "event": event[:120],
                "library": library[:240] if library else "",
            },
        )
    except Exception:
        return


def record_pack_download_metrics(vendor: str, library: str, version: str) -> None:
    store = AuthStore.from_env()
    if store is None:
        return
    try:
        store.execute(
            """
            update pack_builds pb
            set download_count = pb.download_count + 1,
                last_downloaded_at = now(),
                storage_tier = 'hot'
            from libraries l
            join vendors v on v.id = l.vendor_id
            where pb.library_id = l.id
              and v.name = :vendor
              and l.name = :library
              and pb.version = :version
            """,
            {"vendor": vendor, "library": library, "version": version},
        )
    except Exception:
        return


def record_telemetry_event(principal: AuthPrincipal | None, telemetry: dict[str, Any]) -> None:
    store = AuthStore.from_env()
    if store is None:
        return
    properties = telemetry.get("properties")
    if not isinstance(properties, dict):
        properties = {}
    try:
        store.execute(
            """
            insert into telemetry_events (
              event,
              anonymous_user_id,
              library_names,
              query_length,
              result_count,
              properties
            )
            values (
              :event,
              :anonymous_user_id,
              cast(:library_names as text[]),
              :query_length,
              :result_count,
              cast(:properties as jsonb)
            )
            """,
            {
                "event": str(telemetry.get("event") or "telemetry")[:80],
                "anonymous_user_id": anonymous_user_id(principal, properties),
                "library_names": pg_text_array(library_names(properties)),
                "query_length": properties.get("query_length"),
                "result_count": properties.get("result_count"),
                "properties": json.dumps(properties, sort_keys=True),
            },
        )
    except Exception:
        return


def usage_summary(principal: AuthPrincipal, *, limit: int = 20) -> list[dict[str, Any]]:
    store = AuthStore.from_env()
    if store is None:
        return []
    try:
        return store.execute(
            """
            select event, coalesce(library, '') as library, sum(count)::bigint as count
            from usage_daily
            where user_id = cast(:user_id as uuid)
              and day >= current_date - interval '30 days'
            group by event, library
            order by sum(count) desc, event asc, library asc
            limit :limit
            """,
            {"user_id": principal.user_id, "limit": limit},
        )
    except Exception:
        return []


def sha256(value: str) -> str:
    return hashlib.sha256(value.encode("utf-8")).hexdigest()


def anonymous_user_id(principal: AuthPrincipal | None, properties: dict[str, Any]) -> str | None:
    if principal is not None:
        return sha256(principal.user_id)
    raw = str(properties.get("anonymous_user_id") or "").strip()
    return raw[:120] or None


def library_names(properties: dict[str, Any]) -> list[str]:
    names: list[str] = []
    for key in ("library_names", "libraries"):
        value = properties.get(key)
        if isinstance(value, list):
            names.extend(str(item).strip()[:120] for item in value if str(item).strip())
    for key in ("library", "library_scope"):
        value = str(properties.get(key) or "").strip()
        if value:
            names.append(value[:120])
    return sorted(set(names))


def pg_text_array(values: list[str]) -> str:
    escaped = []
    for value in values:
        text = value.replace("\\", "\\\\").replace('"', '\\"')
        escaped.append(f'"{text}"')
    return "{" + ",".join(escaped) + "}"
