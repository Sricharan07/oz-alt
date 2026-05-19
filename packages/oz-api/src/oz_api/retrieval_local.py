from __future__ import annotations

from typing import Any

from oz_api.ranking import local_chunk_score, local_markdown_score
from oz_api.retrieval_common import read_jsonl
from oz_api.storage import RegistryStorage, normalize_query
from oz_api.versions import latest_entry, parse_versioned_scope, resolve_catalog_entry

def suggest_from_catalog(storage: RegistryStorage, query: str, max_results: int) -> list[dict[str, Any]]:
    terms = normalize_query(query)
    rows: list[tuple[int, dict[str, Any]]] = []
    for entry in default_catalog_entries(storage):
        haystack = " ".join(
            [
                entry.get("vendor", ""),
                entry.get("library", ""),
                entry.get("version", ""),
                entry.get("description", ""),
                " ".join(entry.get("keywords", [])),
            ]
        ).lower()
        score = sum(haystack.count(term) for term in terms)
        if score:
            rows.append((score, entry))
    rows.sort(key=lambda item: (-item[0], item[1].get("vendor", ""), item[1].get("library", "")))
    return [
        {
            "vendor": entry["vendor"],
            "library": entry["library"],
            "version": entry["version"],
            "score": score,
            "reason": entry.get("description", ""),
        }
        for score, entry in rows[:max_results]
    ]

def search_from_fixtures(
    storage: RegistryStorage,
    query: str,
    *,
    library_scope: str | None,
    max_results: int,
    content_types: list[str] | None = None,
    fixtures_root: Any | None = None,
) -> list[dict[str, Any]]:
    terms = normalize_query(query)
    scope = parse_versioned_scope(library_scope)
    root = fixtures_root or storage.fixtures_root
    selected_versions = selected_fixture_versions(storage, scope, fixtures_root=root)
    hits: list[dict[str, Any]] = []

    for fixture in root.glob("*/*/*"):
        if not fixture.is_dir():
            continue
        vendor, library, version = fixture.parts[-3:]
        if (vendor, library, version) not in selected_versions:
            continue
        chunk_path = fixture / "_chunks.jsonl"
        if chunk_path.exists():
            for row in read_jsonl(chunk_path):
                if content_types and str(row.get("content_type") or "guide") not in content_types:
                    continue
                score = local_chunk_score(row, terms)
                if score <= 0:
                    continue
                hits.append(
                    {
                        "path": f".codo/vendors/{vendor}/{library}@{version}/{row.get('path')}",
                        "line": int(row.get("start_line") or 1),
                        "score": score,
                        "library": f"{vendor}/{library}",
                        "vendor": vendor,
                        "version": version,
                        "matched_path": row.get("path"),
                        "source_anchor": row.get("source_anchor") or row.get("source_url"),
                        "content_type": row.get("content_type", "guide"),
                        "heading_path": row.get("heading_path", []),
                        "symbols": row.get("symbols", []),
                        "token_count": int(row.get("token_count") or 0),
                        "_matched_text": row.get("text", ""),
                        "_parent_text": row.get("text", ""),
                    }
                )
            for row in symbol_rows(fixture):
                if content_types and str(row.get("content_type") or "api_reference") not in content_types:
                    continue
                score = local_chunk_score(row, terms)
                if score <= 0:
                    continue
                hits.append(
                    {
                        "path": f".codo/vendors/{vendor}/{library}@{version}/{row.get('path')}",
                        "line": 1,
                        "score": score,
                        "library": f"{vendor}/{library}",
                        "vendor": vendor,
                        "version": version,
                        "matched_path": row.get("path"),
                        "source_anchor": row.get("source_anchor") or row.get("source_url"),
                        "content_type": row.get("content_type", "api_reference"),
                        "heading_path": row.get("heading_path", []),
                        "symbols": row.get("symbols", []),
                        "token_count": int(row.get("token_count") or 0),
                        "_matched_text": row.get("text", ""),
                        "_parent_text": row.get("text", ""),
                    }
                )
            continue
        for path in fixture.rglob("*.md"):
            if content_types and "guide" not in content_types:
                continue
            relative = path.relative_to(fixture)
            content = path.read_text(encoding="utf-8")
            score = local_markdown_score(content, relative.as_posix(), terms)
            if score <= 0:
                continue
            hits.append(
                {
                    "path": f".codo/vendors/{vendor}/{library}@{version}/{relative.as_posix()}",
                    "line": 1,
                    "score": score,
                    "library": f"{vendor}/{library}",
                    "vendor": vendor,
                    "version": version,
                    "matched_path": relative.as_posix(),
                    "source_anchor": None,
                    "content_type": "guide",
                    "heading_path": [],
                    "symbols": [],
                    "token_count": 0,
                    "_matched_text": content,
                    "_parent_text": content,
                }
            )

    hits.sort(key=lambda hit: (-hit["score"], hit["path"], hit["line"]))
    deduped: list[dict[str, Any]] = []
    seen: set[str] = set()
    for hit in hits:
        key = str(hit["path"])
        if key in seen:
            continue
        seen.add(key)
        deduped.append(hit)
        if len(deduped) >= max_results:
            break
    return deduped


def default_catalog_entries(storage: RegistryStorage) -> list[dict[str, Any]]:
    by_library: dict[tuple[str, str], list[dict[str, Any]]] = {}
    for entry in storage.load_catalog():
        key = (str(entry.get("vendor") or ""), str(entry.get("library") or ""))
        by_library.setdefault(key, []).append(entry)
    output = [latest for entries in by_library.values() if (latest := latest_entry(entries))]
    return output


def selected_fixture_versions(
    storage: RegistryStorage,
    scope: Any,
    *,
    fixtures_root: Any | None = None,
) -> set[tuple[str, str, str]]:
    root = fixtures_root or storage.fixtures_root
    fixtures = [
        (path.parts[-3], path.parts[-2], path.parts[-1])
        for path in root.glob("*/*/*")
        if path.is_dir()
    ]
    if scope.vendor and scope.library:
        matches = [
            {"vendor": vendor, "library": library, "version": version}
            for vendor, library, version in fixtures
            if vendor == scope.vendor and library == scope.library
        ]
        selected = resolve_catalog_entry(matches, scope.version)
        return {
            (str(selected["vendor"]), str(selected["library"]), str(selected["version"]))
        } if selected else set()

    grouped: dict[tuple[str, str], list[dict[str, Any]]] = {}
    for vendor, library, version in fixtures:
        grouped.setdefault((vendor, library), []).append({"vendor": vendor, "library": library, "version": version})
    return {
        (str(selected["vendor"]), str(selected["library"]), str(selected["version"]))
        for entries in grouped.values()
        if (selected := latest_entry(entries))
    }


def symbol_rows(fixture: Any) -> list[dict[str, Any]]:
    symbols_dir = fixture / "_symbols"
    if not symbols_dir.exists():
        return []
    rows: list[dict[str, Any]] = []
    for path in sorted(symbols_dir.glob("*.md")):
        text = path.read_text(encoding="utf-8", errors="replace")
        symbol = path.stem
        rows.append(
            {
                "path": path.relative_to(fixture).as_posix(),
                "text": text,
                "heading_path": [symbol],
                "symbols": [symbol],
                "content_type": "api_reference",
                "quality_score": 1.0,
            }
        )
    return rows
