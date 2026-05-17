from __future__ import annotations

import os
from urllib.parse import parse_qs

from oz_api.retrieval import latest_entry as retrieval_latest_entry


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
        entry = retrieval_latest_entry(state.storage, vendor, library)
        if entry is None:
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
                }
            )
    return {
        "stale_libraries": stale_libraries,
        "fingerprint": params.get("fingerprint", [""])[0],
        "catalog_generated_at": read_catalog_generated_at(state),
    }


def single_ref_payload(state, vendor: str, library: str) -> dict | None:
    entry = retrieval_latest_entry(state.storage, vendor, library)
    if entry is None:
        return None
    return {
        "vendor": vendor,
        "library": library,
        "version": entry["version"],
        "ref_sha": entry.get("ref_sha", "local"),
    }


def parse_pulled_library(value: str) -> tuple[str, str, str] | None:
    if "@" not in value or "/" not in value:
        return None
    name, version = value.rsplit("@", 1)
    vendor, library = name.split("/", 1)
    if not vendor or not library or not version:
        return None
    return vendor, library, version


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
