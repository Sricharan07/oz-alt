#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any
from urllib.parse import urlparse

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "packages" / "oz-api" / "src"))

from oz_api.admin_ops import upsert_library_profile  # noqa: E402


def main() -> int:
    parser = argparse.ArgumentParser(description="Seed production library profiles from registry/library_profiles.json.")
    parser.add_argument("--repo-root", type=Path, default=ROOT)
    parser.add_argument("--profiles", type=Path, default=None)
    args = parser.parse_args()

    path = args.profiles or args.repo_root / "registry" / "library_profiles.json"
    document = json.loads(path.read_text(encoding="utf-8"))
    rows = document.get("libraries", [])
    if not isinstance(rows, list):
        raise SystemExit("library_profiles.json must contain a libraries array")

    count = 0
    for row in rows:
        if not isinstance(row, dict):
            continue
        payload = profile_payload(row)
        upsert_library_profile(payload, None)
        count += 1
    print(json.dumps({"seeded_profiles": count}, sort_keys=True))
    return 0


def profile_payload(row: dict[str, Any]) -> dict[str, Any]:
    vendor, library = split_library(str(row.get("library") or ""))
    source_url = first_source_url(row)
    return {
        "vendor": vendor,
        "library_name": library,
        "source_url": source_url,
        "source_type": "official_docs",
        "allowed_hosts": row.get("allowed_hosts") or [urlparse(source_url).netloc],
        "allowed_paths": row.get("allowed_paths") or [urlparse(source_url).path or "/"],
        "denied_paths": row.get("denied_paths") or [],
        "preferred_urls": row.get("preferred_urls") or [source_url],
        "required_topics": row.get("required_topics") or [],
        "expected_symbols": row.get("expected_symbols") or [],
        "min_quality_score": row.get("min_quality_score", 0.35),
        "min_documents": row.get("min_documents", 2),
        "max_junk_ratio": row.get("max_junk_ratio", 0.25),
        "recrawl_interval_hours": row.get("recrawl_interval_hours", 24),
    }


def split_library(value: str) -> tuple[str, str]:
    if "/" not in value:
        raise ValueError(f"library must be vendor/name: {value}")
    vendor, library = value.split("/", 1)
    if not vendor or not library:
        raise ValueError(f"library must be vendor/name: {value}")
    return vendor, library


def first_source_url(row: dict[str, Any]) -> str:
    preferred = row.get("preferred_urls")
    if isinstance(preferred, list) and preferred:
        return str(preferred[0])
    hosts = row.get("allowed_hosts")
    paths = row.get("allowed_paths")
    host = str(hosts[0]) if isinstance(hosts, list) and hosts else ""
    path = str(paths[0]) if isinstance(paths, list) and paths else "/"
    if not host:
        raise ValueError(f"profile has no preferred_urls or allowed_hosts: {row.get('library')}")
    return f"https://{host}{path}"


if __name__ == "__main__":
    raise SystemExit(main())
