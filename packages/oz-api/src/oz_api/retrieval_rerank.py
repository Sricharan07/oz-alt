from __future__ import annotations

import hashlib
import json
import os
from typing import Any
from urllib import request

from oz_api.retrieval_context import RetrievalContext
from oz_api.redis_store import redis_client
from oz_api.storage import normalize_query

RERANK_CACHE_VERSION = "search-rank-v2"

def maybe_rerank(
    ctx: RetrievalContext,
    route: str,
    query: str,
    fingerprint: str,
    rows: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    if len(rows) < 2 or clear_winner(rows):
        return rows

    cache_key = rerank_cache_key(route, query, fingerprint)
    cached = get_rerank_cache(cache_key)
    if cached is not None:
        return cached

    reranked = openai_rerank(ctx.openai_api_key, query, rows[:20]) or rows
    put_rerank_cache(cache_key, reranked)
    return reranked

def clear_winner(rows: list[dict[str, Any]]) -> bool:
    scores = [float(row.get("score", 0) or 0) for row in rows[:3]]
    return len(scores) == 3 and all(score > 0.85 for score in scores)

def boost_named_suggestions(query: str, rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    query_terms = set(normalize_query(query))
    if not query_terms:
        return rows
    boosted: list[dict[str, Any]] = []
    for row in rows:
        copy = dict(row)
        library_terms = set(normalize_query(str(copy.get("library") or "")))
        vendor_terms = set(normalize_query(str(copy.get("vendor") or "")))
        score = float(copy.get("score", 0) or 0)
        if library_terms and library_terms.issubset(query_terms):
            score += 25.0
        if vendor_terms and vendor_terms.issubset(query_terms):
            score += 10.0
        copy["score"] = score
        boosted.append(copy)
    boosted.sort(
        key=lambda row: (
            -float(row.get("score", 0) or 0),
            str(row.get("vendor") or ""),
            str(row.get("library") or ""),
            str(row.get("version") or ""),
        )
    )
    return boosted

def openai_rerank(api_key: str | None, query: str, rows: list[dict[str, Any]]) -> list[dict[str, Any]] | None:
    if not api_key:
        return None
    payload = {
        "model": os.environ.get("OZ_RERANK_MODEL", "gpt-4o-mini"),
        "messages": [
            {
                "role": "system",
                "content": "Rank documentation search results for a coding agent. Return JSON array of zero-based indexes only.",
            },
            {"role": "user", "content": json.dumps({"query": query, "results": rows})},
        ],
        "temperature": 0,
    }
    data = json.dumps(payload).encode("utf-8")
    req = request.Request(
        "https://api.openai.com/v1/chat/completions",
        data=data,
        headers={"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"},
        method="POST",
    )
    try:
        with request.urlopen(req, timeout=8) as response:
            body = json.loads(response.read().decode("utf-8"))
        content = body["choices"][0]["message"]["content"]
        order = json.loads(content)
        if not isinstance(order, list):
            return None
        ranked = [rows[idx] for idx in order if isinstance(idx, int) and 0 <= idx < len(rows)]
        seen = {id(row) for row in ranked}
        ranked.extend(row for row in rows if id(row) not in seen)
        return ranked
    except Exception:
        return None

def rerank_cache_key(route: str, query: str, fingerprint: str) -> str:
    digest = hashlib.sha256(f"{RERANK_CACHE_VERSION}\0{route}\0{query}\0{fingerprint}".encode("utf-8")).hexdigest()
    return f"rerank:{digest}"

def get_rerank_cache(cache_key: str) -> list[dict[str, Any]] | None:
    return get_redis_rerank_cache(cache_key)

def put_rerank_cache(cache_key: str, rows: list[dict[str, Any]]) -> None:
    put_redis_rerank_cache(cache_key, rows)


def get_redis_rerank_cache(cache_key: str) -> list[dict[str, Any]] | None:
    client = redis_client()
    if client is None:
        return None
    try:
        payload = client.get(cache_key)
    except Exception:
        return None
    if not payload:
        return None
    try:
        parsed = json.loads(payload)
    except Exception:
        return None
    return parsed if isinstance(parsed, list) else None


def put_redis_rerank_cache(cache_key: str, rows: list[dict[str, Any]]) -> bool:
    client = redis_client()
    if client is None:
        return False
    try:
        client.setex(cache_key, 7 * 24 * 60 * 60, json.dumps(rows, sort_keys=True))
        return True
    except Exception:
        return False
