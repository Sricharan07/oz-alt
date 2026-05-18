from __future__ import annotations

import os
from urllib.parse import parse_qs

from oz_api.retrieval import latest_entry as retrieval_latest_entry
from oz_api.retrieval_context import RetrievalContext
from oz_api.retrieval_postgres import ref_from_postgres
from oz_api.versions import available_versions, major_version_delta, parse_versioned_scope, resolve_catalog_entry


def read_catalog_generated_at(state) -> str | None:
    return state.storage.catalog_generated_at()


def bulk_refs_payload(state, query: str) -> dict:
    params = parse_qs(query)
    stale_libraries: list[dict] = []
    for raw in params.get("library", []):
        parsed = parse_pulled_library(raw)
        if parsed is None:
            continue
        vendor, library, version = parsed
        entry = single_ref_payload(state, vendor, library, None, count_usage=False)
        if entry is None or entry.get("error"):
            continue
        newer_version = str(entry.get("version") or "")
        if newer_version and newer_version != version:
            stale_libraries.append(
                {
                    "vendor": vendor,
                    "library": library,
                    "version": version,
                    "newer_version": newer_version,
                    "ref_sha": entry.get("ref_sha"),
                    "breaking_changes_likely": bool((major_version_delta(version, newer_version) or 0) > 0),
                }
            )
    return {
        "stale_libraries": stale_libraries,
        "fingerprint": params.get("fingerprint", [""])[0],
        "catalog_generated_at": read_catalog_generated_at(state),
    }


def single_ref_payload(
    state,
    vendor: str,
    library: str,
    requested_version: str | None = None,
    *,
    count_usage: bool = True,
) -> dict | None:
    db_ref = ref_from_postgres(
        RetrievalContext.from_env(state.storage),
        vendor,
        library,
        requested_version,
        count_usage=count_usage,
    )
    if db_ref is not None:
        return db_ref
    matches = [
        entry
        for entry in state.storage.load_catalog()
        if entry.get("vendor") == vendor and entry.get("library") == library
    ]
    entry = resolve_catalog_entry(matches, requested_version)
    if entry is None:
        if matches:
            return {
                "error": "version_not_found",
                "vendor": vendor,
                "library": library,
                "requested_version": requested_version,
                "available_versions": available_versions(matches),
            }
        return None
    return {
        "vendor": vendor,
        "library": library,
        "version": entry["version"],
        "ref_sha": entry.get("ref_sha", "local"),
        "available_versions": available_versions(matches),
    }


def parse_pulled_library(value: str) -> tuple[str, str, str] | None:
    parsed = parse_versioned_scope(value)
    if not parsed.vendor or not parsed.library or not parsed.version:
        return None
    return parsed.vendor, parsed.library, parsed.version


def first_form_values(form: dict[str, list[str]]) -> dict[str, str]:
    return {key: values[0] if values else "" for key, values in form.items()}


def secure_cookie() -> bool:
    value = os.environ.get("OZ_COOKIE_SECURE")
    if value:
        return value.lower() in {"1", "true", "yes", "on"}
    public_url = os.environ.get("OZ_PUBLIC_BASE_URL") or os.environ.get("OZ_APP_URL") or ""
    return public_url.startswith("https://")


def cookie_domain() -> str | None:
    value = os.environ.get("OZ_COOKIE_DOMAIN", "").strip()
    return value or None
