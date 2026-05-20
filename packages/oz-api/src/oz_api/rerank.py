from __future__ import annotations

import hashlib
import json
import logging
import os
import re
from typing import Any
from urllib import request

from oz_api.intent import plan_query
from oz_api.observability import observe_duration
from oz_api.redis_store import redis_client
from oz_api.retrieval_context import RetrievalContext
from oz_api.storage import normalize_query

LOGGER = logging.getLogger(__name__)
RERANK_CACHE_VERSION = "search-rank-v9"


def maybe_rerank(
    ctx: RetrievalContext,
    route: str,
    query: str,
    fingerprint: str,
    rows: list[dict[str, Any]],
    *,
    strip_private: bool = True,
) -> list[dict[str, Any]]:
    if len(rows) < 2 or clear_winner(rows):
        boosted = boost_query_matches(query, rows)
        return strip_private_fields(boosted) if strip_private else boosted

    cache_key = rerank_cache_key(route, query, fingerprint, rows)
    cached = get_rerank_cache(cache_key)
    if cached is not None:
        return cached

    limit = min(len(rows), int(os.environ.get("OZ_RERANK_CANDIDATES", "50")))
    candidates = rows[:limit]
    reranked = cross_encoder_rerank(ctx, query, candidates) or candidates
    if len(reranked) < len(rows):
        seen = {id(row) for row in reranked}
        reranked.extend(row for row in rows if id(row) not in seen)
    boosted = boost_query_matches(query, reranked)
    cleaned = strip_private_fields(boosted) if strip_private else boosted
    put_rerank_cache(cache_key, cleaned)
    return cleaned


def clear_winner(rows: list[dict[str, Any]]) -> bool:
    scores = [float(row.get("score", 0) or 0) for row in rows[:3]]
    return len(scores) == 3 and scores[0] > 0 and scores[0] >= scores[1] * 1.6 and scores[1] >= scores[2] * 1.2


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


def cross_encoder_rerank(ctx: RetrievalContext, query: str, rows: list[dict[str, Any]]) -> list[dict[str, Any]] | None:
    provider = os.environ.get("OZ_RERANK_PROVIDER", "jina").strip().lower()
    documents = [rerank_document(row) for row in rows]
    if provider in {"zeroentropy", "zero-entropy", "zerank", "zerank-2"}:
        scores = zeroentropy_scores(ctx.zeroentropy_api_key, query, documents)
    elif provider == "cohere":
        scores = cohere_scores(ctx.cohere_api_key, query, documents)
    else:
        scores = jina_scores(ctx.jina_api_key, query, documents)
    if not scores:
        return None
    indexed = {index: score for index, score in scores if 0 <= index < len(rows)}
    ranked: list[dict[str, Any]] = []
    for index, score in sorted(indexed.items(), key=lambda item: (-item[1], item[0])):
        copy = dict(rows[index])
        copy["score"] = round(float(copy.get("score", 0) or 0) + float(score) * 100.0, 4)
        copy["rerank_score"] = round(float(score), 6)
        ranked.append(copy)
    ranked.extend(dict(row) for index, row in enumerate(rows) if index not in indexed)
    return ranked


def boost_query_matches(query: str, rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    plan = plan_query(query)
    symbols = [normalize_key(symbol) for symbol in plan.symbols]
    terms = [normalize_key(term) for term in plan.important_terms]
    boosted: list[dict[str, Any]] = []
    for row in rows:
        copy = dict(row)
        copy["score"] = round(float(copy.get("score", 0) or 0) + exact_match_bonus(symbols, terms, copy), 4)
        boosted.append(copy)
    boosted.sort(key=lambda row: (-float(row.get("score", 0) or 0), str(row.get("path") or "")))
    return boosted


def exact_match_bonus(symbols: list[str], terms: list[str], row: dict[str, Any]) -> float:
    path = normalize_key(str(row.get("path") or ""))
    matched_path = normalize_key(str(row.get("matched_path") or ""))
    content_type = str(row.get("content_type") or "")
    heading_text = normalize_key(json.dumps(row.get("heading_path") or []))
    symbol_text = normalize_key(json.dumps(row.get("symbols") or []))

    bonus = 0.0
    for symbol in symbols:
        if not symbol:
            continue
        if symbol in symbol_text or symbol in path or symbol in matched_path:
            bonus += 30.0
        elif symbol in heading_text:
            bonus += 16.0
    if content_type == "api_reference" and symbols:
        bonus += 8.0
    if terms and all(term in path or term in matched_path for term in terms[:3]):
        bonus += 8.0
    return min(bonus, 54.0)


def normalize_key(value: str) -> str:
    return re.sub(r"[^a-z0-9]+", "", value.lower())


def rerank_document(row: dict[str, Any]) -> str:
    private = row.get("_rerank_text")
    if private:
        return str(private)[:8000]
    return "\n".join(
        [
            f"path: {row.get('path', '')}",
            f"library: {row.get('library', '')}",
            f"reason: {row.get('reason', '')}",
            f"content_type: {row.get('content_type', '')}",
        ]
    )[:8000]


def jina_scores(api_key: str | None, query: str, documents: list[str]) -> list[tuple[int, float]] | None:
    url = os.environ.get("OZ_JINA_RERANK_URL", "https://api.jina.ai/v1/rerank")
    if not api_key and url == "https://api.jina.ai/v1/rerank":
        return None
    payload = {
        "model": os.environ.get("OZ_RERANK_MODEL", "jina-reranker-v3"),
        "query": query,
        "documents": documents,
        "top_n": len(documents),
    }
    headers = {"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"}
    if not api_key:
        headers.pop("Authorization", None)
    return request_scores(url, payload, headers, provider="jina")


def cohere_scores(api_key: str | None, query: str, documents: list[str]) -> list[tuple[int, float]] | None:
    if not api_key:
        return None
    payload = {
        "model": os.environ.get("OZ_RERANK_MODEL", "rerank-v3.5"),
        "query": query,
        "documents": documents,
        "top_n": len(documents),
    }
    headers = {"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"}
    return request_scores("https://api.cohere.com/v2/rerank", payload, headers, provider="cohere")


def zeroentropy_scores(api_key: str | None, query: str, documents: list[str]) -> list[tuple[int, float]] | None:
    if not api_key:
        return None
    payload = {
        "model": os.environ.get("OZ_RERANK_MODEL", "zerank-2"),
        "query": query,
        "documents": documents,
        "top_n": len(documents),
        "latency": os.environ.get("OZ_ZEROENTROPY_LATENCY", "fast"),
    }
    headers = {"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"}
    url = os.environ.get("OZ_ZEROENTROPY_RERANK_URL", "https://api.zeroentropy.dev/v1/models/rerank")
    return request_scores(url, payload, headers, provider="zeroentropy")


def request_scores(
    url: str,
    payload: dict[str, Any],
    headers: dict[str, str],
    *,
    provider: str,
) -> list[tuple[int, float]] | None:
    req = request.Request(url, data=json.dumps(payload).encode("utf-8"), headers=headers, method="POST")
    try:
        with observe_duration("oz_rerank_request_duration_seconds", {"provider": provider}):
            with request.urlopen(req, timeout=rerank_timeout_seconds()) as response:
                body = json.loads(response.read().decode("utf-8"))
    except Exception as exc:
        LOGGER.info("rerank request failed: %s", exc)
        return None
    return parse_rerank_results(body.get("results"))


def rerank_timeout_seconds() -> float:
    try:
        return max(0.05, int(os.environ.get("OZ_RERANK_TIMEOUT_MS", "300")) / 1000.0)
    except ValueError:
        return 0.3


def parse_rerank_results(results: Any) -> list[tuple[int, float]] | None:
    if not isinstance(results, list):
        return None
    output: list[tuple[int, float]] = []
    for item in results:
        if not isinstance(item, dict):
            continue
        index = numeric_int(item.get("index"))
        score = numeric_float(item.get("relevance_score", item.get("score", item.get("rerank_score"))))
        if index is not None and score is not None:
            output.append((index, score))
    return output


def numeric_int(value: Any) -> int | None:
    if isinstance(value, bool):
        return None
    if isinstance(value, int):
        return value
    if isinstance(value, str) and value.isdigit():
        return int(value)
    return None


def numeric_float(value: Any) -> float | None:
    if isinstance(value, bool):
        return None
    if isinstance(value, (int, float)):
        return float(value)
    if isinstance(value, str):
        try:
            return float(value)
        except ValueError:
            return None
    return None


def strip_private_fields(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    return [{key: value for key, value in row.items() if not key.startswith("_")} for row in rows]


def rerank_cache_key(route: str, query: str, fingerprint: str, rows: list[dict[str, Any]] | None = None) -> str:
    provider = os.environ.get("OZ_RERANK_PROVIDER", "jina").strip().lower()
    model = os.environ.get("OZ_RERANK_MODEL", "").strip()
    latency = os.environ.get("OZ_ZEROENTROPY_LATENCY", "").strip()
    corpus = rerank_candidate_digest(rows or [])
    digest = hashlib.sha256(
        f"{RERANK_CACHE_VERSION}\0{provider}\0{model}\0{latency}\0{route}\0{query}\0{fingerprint}\0{corpus}".encode(
            "utf-8"
        )
    ).hexdigest()
    return f"rerank:{digest}"


def rerank_candidate_digest(rows: list[dict[str, Any]]) -> str:
    payload = [
        [
            str(row.get("path") or ""),
            str(row.get("source_anchor") or ""),
            str(row.get("content_type") or ""),
            str(row.get("token_count") or ""),
        ]
        for row in rows[: int(os.environ.get("OZ_RERANK_CANDIDATES", "50"))]
    ]
    return hashlib.sha256(json.dumps(payload, separators=(",", ":"), sort_keys=True).encode("utf-8")).hexdigest()


def get_rerank_cache(cache_key: str) -> list[dict[str, Any]] | None:
    client = redis_client()
    if client is None:
        return None
    try:
        payload = client.get(cache_key)
    except Exception as exc:
        LOGGER.info("rerank cache read failed: %s", exc)
        return None
    if not payload:
        return None
    try:
        parsed = json.loads(payload)
    except (TypeError, json.JSONDecodeError):
        return None
    return parsed if isinstance(parsed, list) else None


def put_rerank_cache(cache_key: str, rows: list[dict[str, Any]]) -> bool:
    client = redis_client()
    if client is None:
        return False
    try:
        client.setex(cache_key, 7 * 24 * 60 * 60, json.dumps(rows, sort_keys=True))
        return True
    except Exception as exc:
        LOGGER.info("rerank cache write failed: %s", exc)
        return False
