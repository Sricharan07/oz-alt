from __future__ import annotations

from typing import Any

ALLOWED_PROPERTY_KEYS = {
    "anonymous_user_id",
    "command",
    "duration_ms",
    "library",
    "library_scope",
    "library_names",
    "libraries",
    "query_length",
    "result_count",
    "scope",
    "status",
}


def sanitize_telemetry(payload: dict[str, Any]) -> dict[str, Any]:
    event = safe_string(payload.get("event"), max_length=80)
    properties = payload.get("properties")
    if not isinstance(properties, dict):
        properties = {}

    sanitized: dict[str, Any] = {}
    for key in ALLOWED_PROPERTY_KEYS:
        if key not in properties:
            continue
        value = sanitize_property(key, properties[key])
        if value is not None:
            sanitized[key] = value

    return {"event": event, "properties": sanitized}


def sanitize_property(key: str, value: Any) -> Any | None:
    if key in {"query_length", "result_count", "duration_ms"}:
        try:
            return max(0, int(value))
        except (TypeError, ValueError):
            return None
    if key in {"library_names", "libraries"}:
        if not isinstance(value, list):
            return None
        return [safe_string(item, max_length=120) for item in value[:25] if safe_string(item, max_length=120)]
    if key in {"anonymous_user_id", "command", "library", "library_scope", "scope", "status"}:
        return safe_string(value, max_length=120)
    return None


def safe_string(value: Any, *, max_length: int) -> str:
    text = str(value or "").strip()
    return text[:max_length]
