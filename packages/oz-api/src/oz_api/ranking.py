from __future__ import annotations

import re
from typing import Any


CONTENT_TYPE_BONUS = {
    "api_reference": 5.0,
    "code_example": 3.0,
    "config": 2.5,
    "cli": 2.5,
    "error_ref": 2.0,
    "prose": 0.0,
    "types": 3.5,
    "example": 2.0,
    "guide": 0.0,
    "index": -8.0,
}


def local_chunk_score(row: dict[str, Any], terms: list[str]) -> float:
    text = str(row.get("text") or "").lower()
    path = str(row.get("path") or "").lower()
    headings = " ".join(list_of_strings(row.get("heading_path"))).lower()
    symbols = " ".join(list_of_strings(row.get("symbols"))).lower()
    compact_path = compact(path)
    compact_symbols = compact(symbols)
    basename = compact(re.sub(r"\.[^.]+$", "", path.rsplit("/", 1)[-1]))

    text_hits = sum(text.count(term) for term in terms)
    distinct_text_hits = sum(1 for term in terms if term in text)
    path_hits = sum(1 for term in terms if term in path or compact(term) in compact_path)
    heading_hits = sum(1 for term in terms if term in headings)
    symbol_hits = sum(1 for term in terms if term in symbols or compact(term) in compact_symbols)
    exact_basename_hits = sum(1 for term in terms if compact(term) == basename)

    if text_hits == 0 and path_hits == 0 and heading_hits == 0 and symbol_hits == 0:
        return 0.0

    coverage = distinct_text_hits / max(len(terms), 1)
    score = float(min(text_hits, 80))
    score += distinct_text_hits * 18.0
    score += coverage * 40.0
    score += path_hits * 10.0
    score += heading_hits * 16.0
    score += symbol_hits * 35.0
    score += exact_basename_hits * exact_path_bonus(path, str(row.get("content_type") or "guide"), terms)
    score += CONTENT_TYPE_BONUS.get(str(row.get("content_type") or "guide"), 0.0)
    score += max(float(row.get("quality_score") or 1.0), 0.0) * 3.0
    score -= path_penalty(path)
    return round(score, 4)


def local_markdown_score(content: str, relative_path: str, terms: list[str]) -> float:
    lower = content.lower()
    path = relative_path.lower()
    compact_path = compact(path)
    text_hits = sum(lower.count(term) for term in terms)
    distinct_text_hits = sum(1 for term in terms if term in lower)
    path_hits = sum(1 for term in terms if term in path or compact(term) in compact_path)
    if text_hits == 0 and path_hits == 0:
        return 0.0
    coverage = distinct_text_hits / max(len(terms), 1)
    index_penalty = -8.0 if relative_path in {"INDEX.md", "README.md"} else 0.0
    score = min(text_hits, 80) + distinct_text_hits * 18.0 + coverage * 40.0 + path_hits * 10.0
    score += index_penalty - path_penalty(path)
    return round(float(score), 4)


def compact(value: str) -> str:
    return re.sub(r"[^a-z0-9]+", "", value.lower())


def path_penalty(path: str) -> float:
    noisy = ("changelog", "release-notes", "releases", "migration-guide")
    if any(token in path for token in noisy):
        return 60.0
    return 0.0


def exact_path_bonus(path: str, content_type: str, terms: list[str]) -> float:
    if "_symbols/" in path:
        return 220.0
    if path.startswith("api-reference/") or "/api-reference/" in path or content_type == "api_reference":
        return 180.0
    if path.startswith("examples/") and not {"example", "examples"}.intersection(terms):
        return 25.0
    return 60.0


def list_of_strings(value: Any) -> list[str]:
    if not isinstance(value, list):
        return []
    return [str(item) for item in value if str(item).strip()]
