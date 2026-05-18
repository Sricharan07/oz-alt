from __future__ import annotations

import re
from dataclasses import dataclass
from functools import cmp_to_key
from typing import Any


CHANNEL_ALIASES = {"latest", "stable", "current", "default"}
_SEMVER_RE = re.compile(r"^v?(\d+)(?:\.(\d+))?(?:\.(\d+))?(?:[-+][0-9A-Za-z.-]+)?$")
_FULL_VERSION_RE = re.compile(r"^v?\d+\.\d+(?:\.\d+)?(?:[-+][0-9A-Za-z.-]+)?$", re.I)
_PREFIX_VERSION_RE = re.compile(r"^v\d+(?:\.\d+){0,2}(?:[-+][0-9A-Za-z.-]+)?$", re.I)


@dataclass(frozen=True)
class VersionedScope:
    vendor: str | None
    library: str | None
    version: str | None = None


class VersionResolutionError(Exception):
    def __init__(self, code: str, message: str, *, status_code: int = 404, payload: dict[str, Any] | None = None) -> None:
        super().__init__(message)
        self.code = code
        self.status_code = status_code
        self.payload = payload or {}

    def response_payload(self) -> dict[str, Any]:
        return {"error": self.code, "message": str(self), **self.payload}


def parse_versioned_scope(scope: str | None) -> VersionedScope:
    if not scope:
        return VersionedScope(None, None, None)
    value = scope.strip().strip("/")
    if not value:
        return VersionedScope(None, None, None)

    version: str | None = None
    if "@" in value:
        value, version = value.rsplit("@", 1)

    parts = [part for part in value.split("/") if part]
    if version is None and len(parts) >= 3 and looks_like_version(parts[-1]):
        version = parts.pop()

    if len(parts) == 1:
        return VersionedScope("npm", parts[0], normalize_requested_version(version))
    if len(parts) >= 2:
        return VersionedScope(parts[0], "/".join(parts[1:]), normalize_requested_version(version))
    return VersionedScope(None, None, normalize_requested_version(version))


def parse_scope(scope: str | None) -> tuple[str | None, str | None]:
    parsed = parse_versioned_scope(scope)
    return parsed.vendor, parsed.library


def normalize_library_id(value: str) -> str:
    parsed = parse_versioned_scope(value)
    if not parsed.vendor or not parsed.library:
        return value.strip().strip("/")
    base = f"{parsed.vendor}/{parsed.library}"
    return f"{base}@{parsed.version}" if parsed.version else base


def looks_like_version(value: str) -> bool:
    text = value.strip()
    if not text:
        return False
    return bool(_FULL_VERSION_RE.match(text) or _PREFIX_VERSION_RE.match(text) or text.lower() in CHANNEL_ALIASES)


def normalize_requested_version(version: str | None) -> str | None:
    if version is None:
        return None
    cleaned = version.strip()
    if not cleaned or cleaned.lower() in CHANNEL_ALIASES:
        return None
    return cleaned


def latest_entry(entries: list[dict[str, Any]]) -> dict[str, Any] | None:
    candidates = [entry for entry in entries if not entry.get("archived_at")]
    if not candidates:
        candidates = entries
    if not candidates:
        return None
    return sorted(candidates, key=cmp_to_key(compare_entry_versions))[-1]


def resolve_catalog_entry(
    entries: list[dict[str, Any]],
    requested_version: str | None,
) -> dict[str, Any] | None:
    if not entries:
        return None
    request = normalize_requested_version(requested_version)
    if request is None:
        return latest_entry(entries)
    matches = [entry for entry in entries if version_matches(str(entry.get("version") or ""), request)]
    if not matches:
        return None
    return latest_entry(matches)


def available_versions(entries: list[dict[str, Any]]) -> list[str]:
    versions = {str(entry.get("version") or "") for entry in entries if str(entry.get("version") or "")}
    return sorted(versions, key=cmp_to_key(compare_versions), reverse=True)


def version_matches(candidate: str, requested: str) -> bool:
    candidate_text = normalize_version_text(candidate)
    request_text = normalize_version_text(requested)
    if candidate_text == request_text:
        return True

    request_parts = numeric_parts(request_text)
    candidate_parts = numeric_parts(candidate_text)
    if not request_parts or not candidate_parts:
        return candidate_text == request_text
    if len(request_parts) > len(candidate_parts):
        return False
    return candidate_parts[: len(request_parts)] == request_parts


def major_version_delta(left: str, right: str) -> int | None:
    left_parts = numeric_parts(normalize_version_text(left))
    right_parts = numeric_parts(normalize_version_text(right))
    if not left_parts or not right_parts:
        return None
    return abs(left_parts[0] - right_parts[0])


def compare_versions(left: str, right: str) -> int:
    left_key = version_sort_key(left)
    right_key = version_sort_key(right)
    return (left_key > right_key) - (left_key < right_key)


def compare_entry_versions(left: dict[str, Any], right: dict[str, Any]) -> int:
    return compare_versions(str(left.get("version") or ""), str(right.get("version") or ""))


def version_sort_key(version: str) -> tuple[int, tuple[int, ...], str]:
    text = normalize_version_text(version)
    numbers = numeric_parts(text)
    if numbers:
        padded = tuple([*numbers[:4], *([0] * max(0, 4 - len(numbers)))])
        return (2, padded, text)
    if text in CHANNEL_ALIASES:
        return (1, (0, 0, 0, 0), text)
    return (0, (0, 0, 0, 0), text)


def normalize_version_text(version: str) -> str:
    return version.strip().lower().removeprefix("v")


def numeric_parts(version: str) -> tuple[int, ...]:
    match = _SEMVER_RE.match(version)
    if not match:
        return ()
    parts = [int(part) for part in match.groups() if part is not None]
    return tuple(parts)
