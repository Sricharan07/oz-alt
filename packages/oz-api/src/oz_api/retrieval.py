from __future__ import annotations

import re
from typing import Any

from oz_api.retrieval_cache import get_cached_results, put_cached_results
from oz_api.retrieval_common import dedupe_search_results, latest_entry, unique_libraries_to_pull
from oz_api.retrieval_context import RetrievalContext
from oz_api.retrieval_experiments import rerank_enabled, retrieval_variant
from oz_api.retrieval_local import search_from_fixtures, suggest_from_catalog
from oz_api.retrieval_postgres import (
    agent_context_from_postgres,
    postgres_connection,
    search_from_postgres,
    suggest_from_postgres,
    vector_literal,
)
from oz_api.rerank import boost_named_suggestions, maybe_rerank, strip_private_fields
from oz_api.token_counting import token_count
from oz_api.versions import parse_versioned_scope

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
    normalized_types = normalize_content_types(content_types)
    variant = retrieval_variant(fingerprint)
    candidate_pool = max(max_results * 4, 24)
    scopes = context_candidate_scopes(ctx, library_scope, query)
    retrieval_queries = context_retrieval_queries(query)
    agent_rows: list[dict[str, Any]] = []
    search_rows: list[dict[str, Any]] = []
    for retrieval_query in retrieval_queries:
        for scope in scopes:
            scoped_agent_rows = agent_context_from_postgres(
                ctx,
                retrieval_query,
                scope,
                candidate_pool,
                fingerprint,
                content_types=normalized_types,
            )
            if scoped_agent_rows:
                agent_rows.extend(mark_retrieval_query(scoped_agent_rows, retrieval_query))
            scoped_search = search(
                ctx,
                retrieval_query,
                library_scope=scope,
                max_results=candidate_pool,
                fingerprint=fingerprint,
                content_types=normalized_types,
                keep_private=True,
            )
            if scoped_search:
                search_rows.extend(mark_retrieval_query(scoped_search, retrieval_query))
    search_rows = [row for row in search_rows if str(row.get("retrieval_mode") or "") != "fixture_fallback"]
    candidate_rows = merge_context_candidates(agent_rows, search_rows)
    candidate_rows = score_context_candidates_for_packet(candidate_rows, query)
    candidate_rows.sort(key=lambda row: (-float(row.get("score") or 0), str(row.get("path") or ""), int(row.get("line") or 1)))
    reranked = (
        maybe_rerank(
            ctx,
            f"context:{library_scope or '*'}:{','.join(normalized_types or [])}",
            query,
            fingerprint,
            candidate_rows,
            strip_private=False,
        )
        if candidate_rows and rerank_enabled(variant)
        else candidate_rows
    )
    rows = reranked[: max(max_results * 3, 12)]
    snippets: list[dict[str, Any]] = []
    remaining = max(max_tokens, 1)
    retrieval_mode = context_retrieval_mode(rows)
    candidate_modes = sorted(
        {
            str(row.get("retrieval_mode") or "").strip()
            for row in rows
            if str(row.get("retrieval_mode") or "").strip()
        }
    )
    degraded = bool(rows) and all(bool(row.get("degraded")) for row in rows)
    for row in rows:
        if remaining <= 0:
            break
        text = context_source_text(row)
        if not useful_context_text(text, row):
            continue
        metadata = {
            "path": row.get("path"),
            "line": row.get("line"),
            "end_line": row.get("end_line"),
            "score": row.get("score"),
            "library": row.get("library"),
            "vendor": row.get("vendor"),
            "version": row.get("version"),
            "matched_path": row.get("matched_path"),
            "source_anchor": bounded_string(row.get("source_anchor"), 240),
            "content_type": row.get("content_type"),
            "role": row.get("role") or row.get("content_type"),
            "title": bounded_string(row.get("title"), 180),
            "description": bounded_string(row.get("description"), 320),
            "applies_to": bounded_list(row.get("applies_to") or [], 120),
            "entities": bounded_list(row.get("entities") or [], 120),
            "task_tags": bounded_list(row.get("task_tags") or [], 120),
            "source_metadata": bounded_metadata(row.get("metadata_json") or {}),
            "heading_path": bounded_list(row.get("heading_path") or [], 160),
            "symbols": row.get("symbols") or [],
            "retrieval_mode": row.get("retrieval_mode", retrieval_mode),
            "degraded": bool(row.get("degraded", degraded)),
        }
        # max_tokens is a context-content budget. Metadata is already bounded
        # field-by-field and must not starve multi-facet answers.
        metadata_tokens = 0
        snippet_budget = remaining
        if snippet_budget <= 0:
            break
        snippet = trim_context_text_for_query(text, query, snippet_budget)
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
    packet_rows = rows
    packet = context_packet(packet_rows, query=query, max_tokens=max_tokens, max_results=max_results)
    return {
        **packet,
        "results": snippets,
        "retrieval_mode": retrieval_mode,
        "candidate_retrieval_modes": candidate_modes,
        "degraded": degraded,
    }


RELATED_LIBRARY_LIMIT = 4


def context_candidate_scopes(ctx: RetrievalContext, library_scope: str | None, query: str) -> list[str | None]:
    if not library_scope:
        return [None]
    scopes: list[str | None] = [library_scope]
    for related in related_library_scopes(ctx, library_scope, query):
        if related not in scopes:
            scopes.append(related)
    return scopes


def mark_retrieval_query(rows: list[dict[str, Any]], retrieval_query: str) -> list[dict[str, Any]]:
    return [{**row, "_retrieval_query": retrieval_query} for row in rows]


def context_retrieval_queries(query: str) -> list[str]:
    """Generate generic retrieval probes for task-shaped context requests."""

    lowered = query.lower()
    candidates = [query]
    if any(term in lowered for term in ("install", "setup", "quickstart", "initialize", "initialise", "authenticate", "api key", "credential", "environment variable")):
        candidates.append("installation quickstart setup api key environment variables initialize client import")
    if any(term in lowered for term in ("create", "new", "build", "add")):
        candidates.append("create new build add example required parameters response")
    if any(term in lowered for term in ("list", "available", "all", "search")):
        candidates.append("list available all search retrieve collection example")
    if any(term in lowered for term in ("get", "fetch", "retrieve", "details", "read")):
        candidates.append("get fetch retrieve details read identifier response")
    if any(term in lowered for term in ("update", "edit", "patch", "modify")):
        candidates.append("update edit patch modify required parameters example")
    if any(term in lowered for term in ("delete", "remove", "destroy")):
        candidates.append("delete remove destroy identifier example")
    if any(term in lowered for term in ("upload", "file", "pdf", "document", "image", "audio")):
        candidates.append("upload file document input multipart example required parameters")
    if any(term in lowered for term in ("stream", "streaming", "realtime", "websocket", "sse", "chunk", "chunks")):
        candidates.append("stream streaming realtime websocket sse chunks example")
    if any(term in lowered for term in ("config", "configuration", "env", "base url", "base_url", "host", "timeout")):
        candidates.append("configuration environment variables base_url host timeout client options")
    if any(term in lowered for term in ("test", "mock", "pytest", "jest", "spec")):
        candidates.append("testing mock unit test integration test example")
    if any(term in lowered for term in ("request body", "required fields", "required parameters", "schema")):
        candidates.append("request body required fields schema parameters response schema")
    if any(term in lowered for term in ("failed", "failure", "recover", "retry", "exception", "error")):
        candidates.append("error handling exceptions retry failed request status response")
    if any(term in lowered for term in ("request id", "request ids", "metadata", "debug", "debugging", "logs", "logging")):
        candidates.append("request id response metadata headers logs debugging")
    output: list[str] = []
    seen: set[str] = set()
    for candidate in candidates:
        normalized = re.sub(r"\s+", " ", candidate).strip()
        key = normalized.lower()
        if normalized and key not in seen:
            output.append(normalized)
            seen.add(key)
    return output[:6]


def query_has_term(lowered_query: str, term: str) -> bool:
    if re.fullmatch(r"[a-z0-9]+", term) and len(term) <= 4:
        return re.search(rf"(?<![a-z0-9]){re.escape(term)}(?![a-z0-9])", lowered_query) is not None
    return term in lowered_query


def related_library_scopes(ctx: RetrievalContext, library_scope: str, query: str) -> list[str]:
    parsed = parse_versioned_scope(library_scope)
    if not parsed.vendor or not parsed.library:
        return []
    if parsed.version:
        return []
    connection = postgres_connection(ctx.database_url)
    if connection is None:
        return []
    query_terms = set(query_library_terms(query))
    if not query_terms:
        return []
    try:
        with connection:
            with connection.cursor() as cursor:
                cursor.execute(
                    """
                    select l.name, lv.version, coalesce(l.aliases, '[]'::jsonb), coalesce(l.description, '')
                    from libraries l
                    join vendors v on v.id = l.vendor_id
                    join refs r on r.library_id = l.id and r.channel = 'latest'
                    join library_versions lv on lv.id = coalesce(l.default_version_id, r.version_id)
                         and lv.archived_at is null
                    where v.name = %s and l.name <> %s
                    """,
                    (parsed.vendor, parsed.library),
                )
                rows = cursor.fetchall()
    except Exception:
        return []
    scored: list[tuple[int, str]] = []
    for name, version, aliases, description in rows:
        terms = library_specific_terms(parsed.vendor, str(name), aliases, str(description or ""))
        if not terms:
            continue
        hits = query_terms & terms
        if not hits:
            continue
        scope = f"{parsed.vendor}/{name}"
        scored.append((len(hits), scope))
    scored.sort(key=lambda item: (-item[0], item[1]))
    return [scope for _score, scope in scored[:RELATED_LIBRARY_LIMIT]]


from oz_api.retrieval_packet import *  # noqa: F403
