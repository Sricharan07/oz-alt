from __future__ import annotations

from typing import Any

from oz_api.ranking import local_chunk_score, local_markdown_score
from oz_api.retrieval_common import parse_scope, read_jsonl
from oz_api.storage import RegistryStorage, normalize_query

def suggest_from_catalog(storage: RegistryStorage, query: str, max_results: int) -> list[dict[str, Any]]:
    terms = normalize_query(query)
    rows: list[tuple[int, dict[str, Any]]] = []
    for entry in storage.load_catalog():
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
) -> list[dict[str, Any]]:
    terms = normalize_query(query)
    scope_vendor, scope_library = parse_scope(library_scope)
    hits: list[dict[str, Any]] = []

    for fixture in storage.fixtures_root.glob("*/*/*"):
        if not fixture.is_dir():
            continue
        vendor, library, version = fixture.parts[-3:]
        if scope_vendor and (vendor != scope_vendor or library != scope_library):
            continue
        chunk_path = fixture / "_chunks.jsonl"
        if chunk_path.exists():
            for row in read_jsonl(chunk_path):
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
                    }
                )
            for row in symbol_rows(fixture):
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
                    }
                )
            continue
        for path in fixture.rglob("*.md"):
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
