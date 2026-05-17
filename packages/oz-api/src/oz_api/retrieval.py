from __future__ import annotations

from typing import Any

from oz_api.retrieval_common import dedupe_search_results, latest_entry, unique_libraries_to_pull
from oz_api.retrieval_context import RetrievalContext
from oz_api.retrieval_local import search_from_fixtures, suggest_from_catalog
from oz_api.retrieval_postgres import (
    postgres_connection,
    search_from_postgres,
    suggest_from_postgres,
    vector_literal,
)
from oz_api.rerank import boost_named_suggestions, maybe_rerank


def suggest(ctx: RetrievalContext, query: str, max_results: int, fingerprint: str = "") -> list[dict[str, Any]]:
    rows = suggest_from_postgres(ctx, query, max_results, fingerprint)
    if rows is None:
        rows = suggest_from_catalog(ctx.storage, query, max_results)
    rows = boost_named_suggestions(query, rows)
    return maybe_rerank(ctx, "suggest", query, fingerprint, rows)


def search(
    ctx: RetrievalContext,
    query: str,
    *,
    library_scope: str | None,
    max_results: int,
    fingerprint: str = "",
) -> list[dict[str, Any]]:
    candidate_pool = max(max_results * 10, 50)
    rows = search_from_postgres(ctx, query, library_scope, candidate_pool, fingerprint)
    if rows is None:
        rows = search_from_fixtures(ctx.storage, query, library_scope=library_scope, max_results=max_results)
    reranked = maybe_rerank(ctx, f"search:{library_scope or '*'}", query, fingerprint, rows)
    return dedupe_search_results(reranked, max_results)


__all__ = [
    "RetrievalContext",
    "latest_entry",
    "postgres_connection",
    "search",
    "suggest",
    "unique_libraries_to_pull",
    "vector_literal",
]
