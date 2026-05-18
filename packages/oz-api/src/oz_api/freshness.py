from __future__ import annotations

from typing import Any

from oz_api.storage import RegistryStorage
from oz_api.versions import latest_entry as latest_versioned_entry, major_version_delta


def stale_libraries_from_payload(storage: RegistryStorage, payload: dict[str, Any]) -> list[dict[str, Any]]:
    installed = payload.get("installed_libraries")
    if not isinstance(installed, list):
        return []

    stale: list[dict[str, Any]] = []
    for item in installed:
        parsed = parse_installed_library(item)
        if parsed is None:
            continue
        vendor, library, version, ref_sha = parsed
        latest = latest_catalog_entry(storage, vendor, library)
        if latest is None:
            continue
        newer_version = str(latest.get("version") or "")
        latest_ref = str(latest.get("ref_sha") or "")
        version_stale = newer_version and newer_version != version
        ref_stale = bool(ref_sha and latest_ref and ref_sha != latest_ref)
        if version_stale or ref_stale:
            stale.append(
                {
                    "vendor": vendor,
                    "library": library,
                    "version": version,
                    "newer_version": newer_version or version,
                    "ref_sha": latest_ref or None,
                    "breaking_changes_likely": bool(
                        version_stale and (major_version_delta(version, newer_version) or 0) > 0
                    ),
                }
            )
    return stale


def parse_installed_library(item: Any) -> tuple[str, str, str, str | None] | None:
    if isinstance(item, dict):
        vendor = str(item.get("vendor") or "")
        library = str(item.get("library") or "")
        version = str(item.get("version") or "")
        ref_sha = str(item.get("ref_sha") or "") or None
        if vendor and library and version:
            return vendor, library, version, ref_sha
        return None
    if not isinstance(item, str) or "@" not in item or "/" not in item:
        return None
    name, version = item.rsplit("@", 1)
    vendor, library = name.split("/", 1)
    if not vendor or not library or not version:
        return None
    return vendor, library, version, None


def latest_catalog_entry(storage: RegistryStorage, vendor: str, library: str) -> dict[str, Any] | None:
    matches = [
        entry
        for entry in storage.load_catalog()
        if entry.get("vendor") == vendor and entry.get("library") == library
    ]
    return latest_versioned_entry(matches)
