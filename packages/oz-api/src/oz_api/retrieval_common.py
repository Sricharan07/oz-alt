from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from oz_api.storage import RegistryStorage

def unique_libraries_to_pull(results: list[dict[str, Any]]) -> list[dict[str, str]]:
    seen: set[tuple[str, str, str]] = set()
    output: list[dict[str, str]] = []
    for result in results:
        vendor = result["vendor"]
        library = result["library"].split("/", 1)[1]
        version = result["version"]
        key = (vendor, library, version)
        if key in seen:
            continue
        seen.add(key)
        output.append({"vendor": vendor, "library": library, "version": version})
    return output

def dedupe_search_results(results: list[dict[str, Any]], max_results: int) -> list[dict[str, Any]]:
    by_file: dict[str, dict[str, Any]] = {}
    order: list[str] = []
    for result in results:
        path = str(result.get("path") or "")
        if not path:
            continue
        if path not in by_file:
            by_file[path] = result
            order.append(path)
            continue
        existing = by_file[path]
        if score_value(result.get("score")) > score_value(existing.get("score")):
            by_file[path] = result
    return [by_file[path] for path in order][:max_results]

def latest_entry(storage: RegistryStorage, vendor: str, library: str) -> dict[str, Any] | None:
    matches = [
        entry
        for entry in storage.load_catalog()
        if entry.get("vendor") == vendor and entry.get("library") == library
    ]
    if not matches:
        return None
    matches.sort(key=lambda entry: entry.get("version", ""))
    return matches[-1]

def parse_scope(scope: str | None) -> tuple[str | None, str | None]:
    if not scope:
        return None, None
    if "/" not in scope:
        return "npm", scope
    vendor, library = scope.split("/", 1)
    return vendor, library

def score_value(value: Any) -> float:
    if isinstance(value, int | float):
        return float(value)
    if isinstance(value, dict):
        for key in ("rerank_score", "score", "hybrid", "combined", "fts"):
            nested = value.get(key)
            if isinstance(nested, int | float):
                return float(nested)
    return 0.0

def read_jsonl(path: Path) -> list[dict[str, Any]]:
    if not path.exists():
        return []
    rows: list[dict[str, Any]] = []
    for line in path.read_text(encoding="utf-8").splitlines():
        if line.strip():
            rows.append(json.loads(line))
    return rows
