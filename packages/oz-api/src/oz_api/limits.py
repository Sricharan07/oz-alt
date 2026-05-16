from __future__ import annotations

from datetime import datetime, timedelta, timezone

from oz_api.storage import RegistryStorage


def index_request_allowed(storage: RegistryStorage, requesting_user: str, *, limit: int = 20) -> bool:
    cutoff = datetime.now(timezone.utc) - timedelta(hours=1)
    count = 0
    for event in storage.read_admin_events("index_requests"):
        if str(event.get("requesting_user") or "anonymous") != requesting_user:
            continue
        created_at = parse_datetime(str(event.get("created_at") or ""))
        if created_at is None or created_at < cutoff:
            continue
        count += 1
        if count >= limit:
            return False
    return True


def parse_datetime(value: str) -> datetime | None:
    if not value:
        return None
    try:
        parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError:
        return None
    if parsed.tzinfo is None:
        return parsed.replace(tzinfo=timezone.utc)
    return parsed
