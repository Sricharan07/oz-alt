from __future__ import annotations

import re
from typing import Any

from oz_api.intent import QueryIntent, plan_query


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


def planned_chunk_score(row: dict[str, Any], query: str) -> float:
    plan = plan_query(query)
    terms = [compact(term) for term in plan.important_terms if compact(term)]
    base = local_chunk_score(row, terms)
    path = str(row.get("path") or "").lower()
    headings = " ".join(list_of_strings(row.get("heading_path"))).lower()
    symbols = " ".join(list_of_strings(row.get("symbols"))).lower()
    text = str(row.get("text") or "").lower()
    content_type = str(row.get("content_type") or "guide")
    score = base

    score += exact_entity_score(path, headings, symbols, text, plan)
    score += phrase_score(path, headings, text, plan)
    score += content_type_prior(content_type, path, plan)
    score -= broad_page_penalty(path, plan)
    return round(score, 4)


def exact_entity_score(path: str, headings: str, symbols: str, text: str, plan: QueryIntent) -> float:
    score = 0.0
    compact_path = compact(path)
    compact_headings = compact(headings)
    compact_symbols = compact(symbols)
    basename = compact(re.sub(r"\.[^.]+$", "", path.rsplit("/", 1)[-1]))
    for symbol in plan.symbols:
        key = compact(symbol)
        if not key:
            continue
        if "_symbols/" in path and basename == key:
            score += 260.0
        elif basename == key:
            score += 210.0
        elif key in compact_symbols:
            score += 120.0
        elif key in compact_path:
            score += 95.0
        elif key in compact_headings:
            score += 70.0
    for slug in plan.slugs:
        key = compact(slug)
        if not key:
            continue
        if basename == key:
            score += 180.0
        elif f"/{slug}.md" in path or f"/{slug}/" in path:
            score += 150.0
        elif key in compact_path:
            score += 55.0
    return min(score, 420.0)


def phrase_score(path: str, headings: str, text: str, plan: QueryIntent) -> float:
    score = 0.0
    for phrase in plan.phrases:
        lowered = phrase.lower()
        slug = re.sub(r"[^a-z0-9]+", "-", lowered).strip("-")
        if slug and (f"/{slug}.md" in path or f"/{slug}/" in path):
            score += 140.0
        if lowered in headings:
            score += 70.0
        if lowered in text:
            score += 35.0
    return min(score, 260.0)


def content_type_prior(content_type: str, path: str, plan: QueryIntent) -> float:
    score = 0.0
    if content_type in plan.preferred_content_types:
        score += 35.0
    if content_type in plan.negative_content_types:
        score -= 85.0
    if "/cli/" in path and "cli" not in plan.preferred_content_types:
        score -= 95.0
    if "/config/" in path and "config" not in plan.preferred_content_types:
        score -= 70.0
    if content_type == "api_reference" and plan.symbols:
        score += 30.0
    if content_type == "code_example" and plan.name in {"example", "config", "cli"}:
        score += 25.0
    return score


def broad_page_penalty(path: str, plan: QueryIntent) -> float:
    penalty = 0.0
    broad = ("sitemap", "project-structure", "migrating", "migration", "contribution", "community")
    if any(token in path for token in broad):
        wanted = any(token in " ".join(plan.important_terms + plan.phrases) for token in broad)
        if not wanted:
            penalty += 75.0
    if path.endswith("/next.md") and "cli" not in plan.preferred_content_types:
        penalty += 120.0
    return penalty


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
