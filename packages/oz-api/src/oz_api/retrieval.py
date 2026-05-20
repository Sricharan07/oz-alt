from __future__ import annotations

import json
import re
from typing import Any

from oz_api.retrieval_cache import get_cached_results, put_cached_results
from oz_api.retrieval_common import dedupe_search_results, latest_entry, unique_libraries_to_pull
from oz_api.retrieval_context import RetrievalContext
from oz_api.retrieval_experiments import rerank_enabled, retrieval_variant
from oz_api.retrieval_local import search_from_fixtures, suggest_from_catalog
from oz_api.retrieval_postgres import (
    postgres_connection,
    search_from_postgres,
    suggest_from_postgres,
    vector_literal,
)
from oz_api.rerank import boost_named_suggestions, maybe_rerank, strip_private_fields

CONTEXT_MIN_TOKENS = 18
VALID_CONTENT_TYPES = {"prose", "guide", "code_example", "api_reference", "config", "cli", "error_ref", "types", "example", "index"}


def suggest(ctx: RetrievalContext, query: str, max_results: int, fingerprint: str = "") -> list[dict[str, Any]]:
    variant = retrieval_variant(fingerprint)
    cached = get_cached_results("suggest", query, None, max_results, variant)
    if cached is not None:
        return cached
    rows = suggest_from_postgres(ctx, query, max_results, fingerprint)
    if rows is None:
        rows = suggest_from_catalog(ctx.storage, query, max_results)
    rows = boost_named_suggestions(query, rows)
    output = maybe_rerank(ctx, "suggest", query, fingerprint, rows) if rerank_enabled(variant) else rows
    put_cached_results("suggest", query, None, max_results, variant, output)
    return output


def search(
    ctx: RetrievalContext,
    query: str,
    *,
    library_scope: str | None,
    max_results: int,
    fingerprint: str = "",
    content_types: list[str] | None = None,
    keep_private: bool = False,
) -> list[dict[str, Any]]:
    variant = retrieval_variant(fingerprint)
    normalized_types = normalize_content_types(content_types)
    cache_scope = cache_scope_with_types(library_scope, normalized_types)
    cached = get_cached_results("search", query, cache_scope, max_results, variant)
    if cached is not None and not keep_private:
        return cached
    candidate_pool = max(max_results * 10, 50)
    rows = search_from_postgres(
        ctx,
        query,
        library_scope,
        candidate_pool,
        fingerprint,
        content_types=normalized_types,
    )
    if rows is None:
        rows = search_from_fixtures(
            ctx.storage,
            query,
            library_scope=library_scope,
            max_results=max_results,
            content_types=normalized_types,
        )
        for row in rows:
            row["retrieval_mode"] = "fixture_fallback"
            row["degraded"] = True
    reranked = (
        maybe_rerank(
            ctx,
            f"{'context' if keep_private else 'search'}:{library_scope or '*'}:{','.join(normalized_types or [])}",
            query,
            fingerprint,
            rows,
            strip_private=not keep_private,
        )
        if rerank_enabled(variant)
        else rows
    )
    output = dedupe_search_results(reranked, max_results)
    if not keep_private:
        output = strip_private_fields(output)
        put_cached_results("search", query, cache_scope, max_results, variant, output)
    return output


def context(
    ctx: RetrievalContext,
    query: str,
    *,
    library_scope: str | None,
    max_tokens: int,
    max_results: int,
    fingerprint: str = "",
    content_types: list[str] | None = None,
) -> dict[str, Any]:
    rows = search(
        ctx,
        query,
        library_scope=library_scope,
        max_results=max_results,
        fingerprint=fingerprint,
        content_types=content_types,
        keep_private=True,
    )
    snippets: list[dict[str, Any]] = []
    remaining = max(max_tokens, 1)
    retrieval_mode = first_retrieval_mode(rows)
    degraded = any(bool(row.get("degraded")) for row in rows)
    for row in rows:
        if remaining <= 0:
            break
        text = context_source_text(row)
        if not useful_context_text(text, row):
            continue
        metadata = {
            "path": row.get("path"),
            "line": row.get("line"),
            "score": row.get("score"),
            "library": row.get("library"),
            "vendor": row.get("vendor"),
            "version": row.get("version"),
            "matched_path": row.get("matched_path"),
            "source_anchor": bounded_string(row.get("source_anchor"), 240),
            "content_type": row.get("content_type"),
            "heading_path": bounded_list(row.get("heading_path") or [], 160),
            "symbols": row.get("symbols") or [],
            "retrieval_mode": row.get("retrieval_mode", retrieval_mode),
            "degraded": bool(row.get("degraded", degraded)),
        }
        metadata_tokens = approximate_tokens(json.dumps(metadata, sort_keys=True))
        snippet_budget = remaining - metadata_tokens
        if snippet_budget <= 0:
            break
        snippet = trim_to_token_budget(text, snippet_budget)
        tokens = approximate_tokens(snippet)
        if not snippet.strip() or tokens <= 0:
            continue
        remaining -= tokens + metadata_tokens
        snippets.append(
            {
                **metadata,
                "token_count": tokens,
                "snippet": snippet,
            }
        )
    return {
        "results": snippets,
        "retrieval_mode": retrieval_mode,
        "degraded": degraded,
    }


def normalize_content_types(values: list[str] | None) -> list[str] | None:
    if not values:
        return None
    output = []
    for value in values:
        normalized = str(value).strip()
        if normalized in VALID_CONTENT_TYPES and normalized not in output:
            output.append(normalized)
    return output or None


def cache_scope_with_types(scope: str | None, content_types: list[str] | None) -> str | None:
    if not content_types:
        return scope
    return f"{scope or '*'}|types={','.join(content_types)}"


def first_retrieval_mode(rows: list[dict[str, Any]]) -> str:
    for row in rows:
        mode = str(row.get("retrieval_mode") or "").strip()
        if mode:
            return mode
    return "unknown"


def context_source_text(row: dict[str, Any]) -> str:
    matched = clean_context_text(str(row.get("_matched_text") or ""))
    parent = clean_context_text(str(row.get("_parent_text") or ""))
    content_type = str(row.get("content_type") or "")
    if matched and useful_context_text(matched, row):
        return matched
    if content_type in {"code_example", "config", "cli", "error_ref"} and matched:
        return matched
    if content_type == "api_reference" and matched and row.get("symbols"):
        return matched
    return matched or parent


def clean_context_text(text: str) -> str:
    text = text.replace("\r\n", "\n").strip()
    text = re.sub(r"\A---\n.*?\n---\n+", "", text, flags=re.S)
    text = re.sub(r"\A\+\+\+\n.*?\n\+\+\+\n+", "", text, flags=re.S)
    text = re.sub(r"\n---\n(?:title|description|url|version):.*?\n---\n", "\n", text, flags=re.S)
    lines = []
    for line in text.splitlines():
        stripped = line.strip()
        if stripped.startswith("Source:") or stripped.startswith("**Source:**"):
            continue
        if stripped in {"---", "+++"} or stripped.startswith(("title:", "description:", "url:", "version:")):
            continue
        lines.append(line.rstrip())
    text = "\n".join(lines).strip()
    text = collapse_repeated_headings(text)
    text = re.sub(r"\n{3,}", "\n\n", text)
    return text


def collapse_repeated_headings(text: str) -> str:
    output: list[str] = []
    last_heading = ""
    for line in text.splitlines():
        stripped = line.strip()
        if stripped.startswith("#"):
            if stripped == last_heading:
                continue
            last_heading = stripped
        output.append(line)
    return "\n".join(output).strip()


def useful_context_text(text: str, row: dict[str, Any]) -> bool:
    if not text.strip():
        return False
    if low_signal_context_text(text):
        return False
    if str(row.get("content_type") or "") == "api_reference" and row.get("symbols"):
        return True
    return approximate_tokens(text) >= CONTEXT_MIN_TOKENS


def low_signal_context_text(text: str) -> bool:
    stripped = text.strip()
    lines = [line.strip() for line in stripped.splitlines() if line.strip()]
    if not lines:
        return True
    if len(lines) == 1 and re.match(r"^#{1,6}\s+", lines[0]):
        return True
    boilerplate_terms = (
        "index of all docs",
        "edit this page",
        "was this page helpful",
        "skip to main content",
        "on this page",
    )
    lowered = stripped.lower()
    if any(term in lowered for term in boilerplate_terms) and approximate_tokens(stripped) < 40:
        return True
    return False


def trim_to_token_budget(text: str, budget: int) -> str:
    if approximate_tokens(text) <= budget:
        return text.strip()
    selected: list[str] = []
    in_fence = False
    tokens = 0
    for line in text.splitlines():
        line_tokens = approximate_tokens(line)
        if selected and not in_fence and tokens + line_tokens > budget:
            break
        selected.append(line)
        tokens += line_tokens
        if line.strip().startswith("```"):
            in_fence = not in_fence
        if tokens >= budget and not in_fence:
            break
    if in_fence:
        selected.append("```")
    return "\n".join(selected).strip()


def approximate_tokens(text: str) -> int:
    return max(1, len(re.findall(r"\w+|[^\w\s]", text)))


def bounded_string(value: Any, max_chars: int) -> str:
    text = str(value or "")
    return text if len(text) <= max_chars else text[:max_chars].rstrip()


def bounded_list(value: list[Any], max_chars: int) -> list[str]:
    output: list[str] = []
    for item in value:
        output.append(bounded_string(item, max_chars))
    return output


__all__ = [
    "RetrievalContext",
    "latest_entry",
    "postgres_connection",
    "search",
    "suggest",
    "context",
    "unique_libraries_to_pull",
    "vector_literal",
]
