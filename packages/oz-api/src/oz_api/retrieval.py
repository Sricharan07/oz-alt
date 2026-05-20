from __future__ import annotations

import re
from typing import Any

from oz_api.context_cards import select_context_snippets
from oz_api.retrieval_cache import get_cached_results, put_cached_results
from oz_api.retrieval_common import dedupe_search_results, latest_entry, unique_libraries_to_pull
from oz_api.retrieval_context import RetrievalContext
from oz_api.retrieval_experiments import rerank_enabled, retrieval_variant
from oz_api.retrieval_local import context_snippets_from_fixtures, search_from_fixtures, suggest_from_catalog
from oz_api.retrieval_postgres import (
    context_snippets_from_postgres,
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
    candidate_pool = max(max_results * 4, 24)
    scopes = context_candidate_scopes(ctx, library_scope, query)
    retrieval_queries = context_retrieval_queries(query)
    snippet_rows: list[dict[str, Any]] = []
    search_rows: list[dict[str, Any]] = []
    for retrieval_query in retrieval_queries:
        for scope in scopes:
            scoped_snippets = context_snippets_from_postgres(
                ctx,
                retrieval_query,
                scope,
                candidate_pool,
                fingerprint,
                content_types=normalized_types,
            )
            if scoped_snippets:
                snippet_rows.extend(mark_retrieval_query(scoped_snippets, retrieval_query))
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
    search_rows_are_fixture_fallback = bool(search_rows) and all(
        str(row.get("retrieval_mode") or "") == "fixture_fallback" for row in search_rows
    )
    candidate_rows: list[dict[str, Any]]
    if snippet_rows or (search_rows and not search_rows_are_fixture_fallback):
        candidate_rows = merge_context_candidates(snippet_rows or [], search_rows or [])
        candidate_rows = score_context_candidates_for_packet(candidate_rows, query)
        rows = select_context_snippets(
            candidate_rows,
            query,
            max_results=max(max_results * 3, 12),
            max_tokens=max(max_tokens * 2, max_tokens),
        )
    else:
        candidate_rows = []
        rows = context_snippets_from_fixtures(
            ctx.storage,
            query,
            library_scope=library_scope,
            max_results=max(max_results * 3, 12),
            max_tokens=max(max_tokens * 2, max_tokens),
            content_types=normalized_types,
        )
    snippets: list[dict[str, Any]] = []
    remaining = max(max_tokens, 1)
    retrieval_mode = context_retrieval_mode(candidate_rows or rows)
    candidate_modes = sorted(
        {
            str(row.get("retrieval_mode") or "").strip()
            for row in (candidate_rows or rows)
            if str(row.get("retrieval_mode") or "").strip()
        }
    )
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
    packet = context_packet(snippets, query=query, max_tokens=max_tokens, max_results=max_results)
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
    """Generate source-backed retrieval probes for task-shaped context requests.

    The original user query stays first and remains the only query used to score
    the final packet. Supplemental probes just widen recall for common docs
    facets such as setup, request schemas, streaming, and file output.
    """

    lowered = query.lower()
    candidates = [query]
    if any(term in lowered for term in ("install", "setup", "quickstart", "initialize", "initialise", "authenticate", "api key", "credential", "environment variable")):
        candidates.append("installation quickstart setup api key environment variables initialize client")
    if any(term in lowered for term in ("default configuration", "initialize", "initialise", "client")):
        candidates.append("initialize client default configuration import client constructor")
    if any(term in lowered for term in ("custom host", "api host", "host endpoint", "base url", "base_url", "endpoint")):
        candidates.append("configuration host base_url endpoint client custom api host")
    if any(term in lowered for term in ("verify", "validate", "valid")) and any(term in lowered for term in ("api key", "credential", "token")):
        candidates.append("verify api key lightweight request list models list voices client call")
    if text_to_speech_query(lowered):
        candidates.append("text to speech tts synthesize synthesis generate speech audio python example")
    if any(term in lowered for term in ("stream", "streaming", "chunk", "chunks", "long input", "long text")):
        candidates.append("streaming text to speech synthesize_streaming chunks continue_stream auto_flush websocket")
    if any(term in lowered for term in ("save", "wav", "mp3", "file", "write")) and any(term in lowered for term in ("audio", "speech", "tts", "synthesis")):
        candidates.append("save generated audio wav mp3 output_format writeframes bytes file")
    if any(term in lowered for term in ("voiceid", "voice id", "voice_id", "voice")):
        candidates.append("voice_id voiceId voices list voices get voices synthesize request")
    if any(term in lowered for term in ("request body", "required fields", "required parameters", "schema")):
        candidates.append("request body required fields schema parameters text voiceId model")
    if any(term in lowered for term in ("speed", "consistency", "similarity", "enhancement", "optional synthesis", "controls")):
        candidates.append("speed consistency similarity enhancement synthesis controls optional parameters")
    if any(term in lowered for term in ("failed", "failure", "recover", "retry", "exception", "error")):
        candidates.append("error handling exceptions retry failed request status response")
    if any(term in lowered for term in ("request id", "request ids", "metadata", "debug", "debugging", "logs")):
        candidates.append("request id response metadata headers logs debugging")
    if any(term in lowered for term in ("list", "available", "fetch", "details", "retrieve", "get ")) and "agent" in lowered:
        candidates.append("list agents get agent retrieve agent details agent_id")
    if any(term in lowered for term in ("create", "new", "build")) and "agent" in lowered:
        candidates.append("create agent new_agent create_agent agent request python")
    output: list[str] = []
    seen: set[str] = set()
    for candidate in candidates:
        normalized = re.sub(r"\s+", " ", candidate).strip()
        key = normalized.lower()
        if normalized and key not in seen:
            output.append(normalized)
            seen.add(key)
    return output[:6]


def text_to_speech_query(lowered_query: str) -> bool:
    return (
        "text-to-speech" in lowered_query
        or "text to speech" in lowered_query
        or "tts" in lowered_query
        or "synthesize" in lowered_query
        or "synthesis" in lowered_query
        or "generate speech" in lowered_query
        or ("speech" in lowered_query and "audio" in lowered_query)
    )


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


GENERIC_LIBRARY_TERMS = {
    "api",
    "client",
    "core",
    "docs",
    "documentation",
    "example",
    "examples",
    "guide",
    "library",
    "main",
    "node",
    "python",
    "sdk",
    "source",
    "types",
}


def query_library_terms(query: str) -> list[str]:
    return [
        term
        for term in re.findall(r"[a-z][a-z0-9]+", query.lower())
        if len(term) >= 3 and term not in GENERIC_LIBRARY_TERMS
    ]


def library_specific_terms(vendor: str, library: str, aliases: Any, description: str) -> set[str]:
    vendor_terms = set(query_library_terms(vendor.replace("-", " ").replace("/", " ")))
    raw_aliases = aliases if isinstance(aliases, list) else []
    values = [library, *[str(item) for item in raw_aliases], description]
    terms: set[str] = set()
    for value in values:
        for term in query_library_terms(str(value).replace("-", " ").replace("/", " ").replace(".", " ")):
            if term not in vendor_terms:
                terms.add(term)
    return terms


def merge_context_candidates(snippet_rows: list[dict[str, Any]], search_rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    merged: list[dict[str, Any]] = []
    seen: set[str] = set()
    for row in [*snippet_rows, *search_rows]:
        key = context_candidate_key(row)
        if key in seen:
            continue
        seen.add(key)
        merged.append(row)
    return merged


def context_candidate_key(row: dict[str, Any]) -> str:
    matched_path = str(row.get("matched_path") or row.get("relative_path") or row.get("path") or "")
    line = int(row.get("line") or row.get("start_line") or 1)
    title = str(row.get("title") or "")
    role = str(row.get("role") or row.get("content_type") or "")
    return f"{matched_path}:{line}:{role}:{title}"


def score_context_candidates_for_packet(rows: list[dict[str, Any]], query: str) -> list[dict[str, Any]]:
    return [{**row, "score": float(row.get("score") or 0) + context_packet_candidate_boost(row, query, rows)} for row in rows]


def context_packet_candidate_boost(row: dict[str, Any], query: str, rows: list[dict[str, Any]]) -> float:
    query_lower = query.lower()
    score = row_library_query_boost(row, query) + row_language_query_boost(row, query) + row_task_query_boost(row, query)
    setup_query = any(term in query_lower for term in ("install", "initialize", "authenticate", "api key", "environment", "credential", "setup", "quickstart"))
    if not setup_query:
        return score
    text = str(row.get("_matched_text") or row.get("snippet") or row.get("content") or "")
    text_lower = text.lower()
    path = str(row.get("matched_path") or row.get("relative_path") or row.get("path") or "").lower()
    title = str(row.get("title") or "").lower()
    role = str(row.get("role") or row.get("content_type") or "")
    code_blocks = extract_code_blocks(text)
    code_lower = "\n".join(block["code"] for block in code_blocks).lower()
    target_text = code_lower or text_lower
    if "readme" in path or "quickstart" in path or "getting-started" in path:
        score += 340.0
    if any(term in title for term in ("getting started", "quickstart", "installation", "api key", "creating your first", "first ")):
        score += 260.0
    if role in {"code_example", "workflow", "cli"}:
        score += 160.0
    if re.search(r"\b[A-Z][A-Z0-9_]*(?:API_KEY|TOKEN|SECRET|KEY)\b", text) or "api key" in text_lower or "access_token" in text_lower:
        score += 220.0
    if re.search(r"\bfrom\s+[\w.]+\s+import\s+\w*Client\b", target_text) or re.search(r"\b\w*Client\s*\(", target_text):
        score += 180.0
    scope_terms = library_scope_terms(rows, query)
    own_hits = sum(1 for term in scope_terms if term in target_text)
    if own_hits:
        score += 420.0 + own_hits * 70.0
    provider_hits = {term for term in PROVIDER_CLIENT_TERMS if term in f"{code_lower} {path} {title}"}
    unrequested_provider_hits = {term for term in provider_hits if term not in query_lower}
    if unrequested_provider_hits and not own_hits:
        score -= 1450.0
    elif unrequested_provider_hits:
        score -= 450.0
    if "basellmclient" in code_lower or "standalone openai client" in text_lower:
        score -= 500.0
    return score


LANGUAGE_ALIASES = {
    "python": {"python", "py"},
    "typescript": {"typescript", "ts", "tsx"},
    "javascript": {"javascript", "js", "jsx", "node"},
    "rust": {"rust", "rs"},
    "go": {"go", "golang"},
    "ruby": {"ruby", "rb"},
    "php": {"php"},
    "java": {"java"},
    "csharp": {"csharp", "c#", "cs"},
    "swift": {"swift"},
    "kotlin": {"kotlin"},
}


def row_language_query_boost(row: dict[str, Any], query: str) -> float:
    requested = requested_languages(query)
    if not requested:
        return 0.0
    text_content = str(row.get("_matched_text") or row.get("snippet") or row.get("content") or "")
    block_languages = [block.get("language", "") for block in extract_code_blocks(text_content)]
    explicit_languages = {
        lang
        for lang in [canonical_language(str(row.get("code_language") or "")), *(canonical_language(lang) for lang in block_languages)]
        if lang
    }
    score = 0.0
    if explicit_languages:
        if explicit_languages & requested:
            score += 820.0
        else:
            score -= 780.0
    text = " ".join(
        [
            str(row.get("code_language") or ""),
            str(row.get("matched_path") or row.get("path") or ""),
            str(row.get("library") or ""),
            str(row.get("title") or ""),
            text_content[:800],
        ]
    ).lower()
    for lang in requested:
        aliases = LANGUAGE_ALIASES.get(lang, {lang})
        if any(re.search(rf"(?<![a-z0-9]){re.escape(alias)}(?![a-z0-9])", text) for alias in aliases):
            score += 220.0 if explicit_languages else 520.0
        else:
            score -= 180.0
    for lang, aliases in LANGUAGE_ALIASES.items():
        if lang in requested:
            continue
        if any(re.search(rf"(?<![a-z0-9]){re.escape(alias)}(?![a-z0-9])", text) for alias in aliases):
            score -= 120.0
    return score


def requested_languages(query: str) -> set[str]:
    lowered = query.lower()
    output: set[str] = set()
    for lang, aliases in LANGUAGE_ALIASES.items():
        if any(re.search(rf"(?<![a-z0-9]){re.escape(alias)}(?![a-z0-9])", lowered) for alias in aliases):
            output.add(lang)
    return output


def canonical_language(value: str) -> str:
    lowered = value.lower().strip()
    if not lowered:
        return ""
    normalized = lowered.removeprefix("language-")
    for language, aliases in LANGUAGE_ALIASES.items():
        if normalized == language or normalized in aliases:
            return language
    if normalized in {"yaml", "yml", "toml", "json", "bash", "sh", "shell", "dart", "html", "css"}:
        return normalized
    return ""


def row_library_query_boost(row: dict[str, Any], query: str) -> float:
    library = str(row.get("library") or "")
    if "/" not in library:
        return 0.0
    vendor, name = library.split("/", 1)
    query_terms = set(query_library_terms(query))
    if not query_terms:
        return 0.0
    terms = library_specific_terms(vendor, name, [], "")
    hits = query_terms & terms
    if not hits:
        return 0.0
    score = 850.0 + len(hits) * 120.0
    path = str(row.get("matched_path") or row.get("path") or "").lower()
    title = str(row.get("title") or "").lower()
    if any(term in f"{path} {title}" for term in hits):
        score += 220.0
    return score


QUERY_STOP_TERMS = {
    "about",
    "after",
    "available",
    "before",
    "configuration",
    "default",
    "details",
    "does",
    "from",
    "generated",
    "generating",
    "handle",
    "into",
    "locally",
    "output",
    "plain",
    "python",
    "request",
    "requests",
    "response",
    "safe",
    "smallest",
    "using",
    "what",
    "when",
    "with",
}


def row_task_query_boost(row: dict[str, Any], query: str) -> float:
    lowered = query.lower()
    text = " ".join(
        [
            str(row.get("title") or ""),
            str(row.get("matched_path") or row.get("relative_path") or row.get("path") or ""),
            str(row.get("description") or ""),
            str(row.get("role") or row.get("content_type") or ""),
            " ".join(str(item) for item in row.get("task_tags") or []),
            " ".join(str(item) for item in row.get("entities") or []),
            str(row.get("_matched_text") or row.get("snippet") or row.get("content") or "")[:5000],
        ]
    ).lower()
    positive, negative = task_profile_terms(lowered)
    score = 0.0
    for term in positive:
        if term and term in text:
            score += 260.0 if len(term) >= 8 else 160.0
    for term in negative:
        if term and term in text:
            score -= 520.0 if len(term) >= 8 else 320.0
    query_terms = meaningful_query_terms(lowered)
    direct_hits = sum(1 for term in query_terms if term in text)
    score += min(420.0, direct_hits * 70.0)
    return score


def task_profile_terms(lowered_query: str) -> tuple[set[str], set[str]]:
    positive: set[str] = set()
    negative: set[str] = set()
    if text_to_speech_query(lowered_query):
        positive.update({"text-to-speech", "text to speech", "tts", "synthesize", "synthesis", "speech", "audio", "voice"})
        negative.update({"speech-to-text", "speech to text", "stt", "transcribe", "transcription", "diarization"})
    if any(term in lowered_query for term in ("stream", "streaming", "chunk", "chunks", "long input", "long text")):
        positive.update({"stream", "streaming", "chunk", "chunks", "synthesize_streaming", "continue_stream", "auto_flush", "websocket", "buffer"})
    if any(term in lowered_query for term in ("save", "wav", "mp3", "file", "write")) and any(term in lowered_query for term in ("audio", "speech", "tts", "synthesis")):
        positive.update({"save", "saved", "file", "wav", "mp3", "output_format", "writeframes", "write", "bytes"})
    if any(term in lowered_query for term in ("voiceid", "voice id", "voice_id", "voice")):
        positive.update({"voiceid", "voice_id", "voice id", "voices", "get_voices", "list voices"})
    if any(term in lowered_query for term in ("request body", "required fields", "required parameters", "schema")):
        positive.update({"request body", "required", "schema", "parameters", "field", "fields", "model", "voiceid", "voice_id"})
    if any(term in lowered_query for term in ("speed", "consistency", "similarity", "enhancement", "optional synthesis", "controls")):
        positive.update({"speed", "consistency", "similarity", "enhancement", "controls", "optional"})
    if any(term in lowered_query for term in ("failed", "failure", "recover", "retry", "exception", "error")):
        positive.update({"error", "exception", "retry", "failed", "failure", "status", "recover"})
    if any(term in lowered_query for term in ("request id", "request ids", "metadata", "debug", "debugging", "logs")):
        positive.update({"request id", "request_id", "metadata", "headers", "debug", "logs", "logging"})
    if any(term in lowered_query for term in ("list", "available", "fetch", "details", "retrieve", "get ")) and "agent" in lowered_query:
        positive.update({"list_agents", "get_agent", "retrieve", "details", "agent_id", "agents"})
        if "create" not in lowered_query and "new" not in lowered_query:
            negative.update({"create_agent", "new_agent", "creating your first"})
    if any(term in lowered_query for term in ("create", "new", "build")) and "agent" in lowered_query:
        positive.update({"create_agent", "new_agent", "create", "agent"})
    if any(term in lowered_query for term in ("custom host", "api host", "host endpoint", "base url", "base_url", "endpoint")):
        positive.update({"configuration", "host", "base_url", "base url", "endpoint"})
    return positive, negative


def meaningful_query_terms(lowered_query: str) -> set[str]:
    terms = {
        term
        for term in re.findall(r"[a-z][a-z0-9_]+", lowered_query.replace("-", " "))
        if len(term) >= 4 and term not in QUERY_STOP_TERMS and term not in GENERIC_LIBRARY_TERMS
    }
    if "api key" in lowered_query:
        terms.add("api_key")
    if "voice id" in lowered_query:
        terms.add("voice_id")
    return terms


FENCE_RE = re.compile(r"(?ms)^\s*(`{3,}|~{3,})([A-Za-z0-9_+.#-]*)\n(?P<code>.*?)(?:^\s*\1\s*$)")


def context_packet(
    rows: list[dict[str, Any]],
    *,
    query: str,
    max_tokens: int,
    max_results: int,
) -> dict[str, Any]:
    code_snippets: list[dict[str, Any]] = []
    info_snippets: list[dict[str, Any]] = []
    remaining = max(max_tokens, 1)
    seen_code: set[str] = set()
    seen_info: set[str] = set()
    seen_sources: set[str] = set()
    max_code = max(1, min(max_results, 3 if max_results >= 5 else max_results))
    max_info = max(0, max_results - max_code)
    ordered = sorted(rows, key=lambda row: packet_row_score(row, query), reverse=True)
    has_setup_composite = False
    for card in composite_code_cards(ordered, query, remaining):
        key = card_key(card)
        if not key or key in seen_code:
            continue
        seen_code.add(key)
        seen_sources.update(card_sources(card))
        has_setup_composite = has_setup_composite or card.get("codeId") == "oz:composite:setup"
        remaining -= int(card.get("codeTokens") or 0)
        code_snippets.append(card)
        if remaining <= 0 or len(code_snippets) >= max_code:
            break
    for row in ordered:
        if remaining <= 0:
            break
        text = str(row.get("snippet") or "").strip()
        if not text:
            continue
        row_source = source_id(row)
        if row_source and row_source in seen_sources:
            continue
        title_lower = str(row.get("title") or "").lower()
        if has_setup_composite and any(term in title_lower for term in ("installation", "dependencies")):
            continue
        code_blocks = extract_code_blocks(text)
        if code_blocks:
            card = code_snippet_card(row, text, code_blocks, remaining, query=query)
            key = card_key(card)
            if key and key not in seen_code and len(code_snippets) < max_code:
                seen_code.add(key)
                seen_sources.update(card_sources(card))
                remaining -= int(card.get("codeTokens") or 0)
                code_snippets.append(card)
                if len(code_snippets) >= max_code:
                    continue
        info = info_snippet_card(row, text, remaining)
        key = card_key(info)
        if (
            key
            and key not in seen_info
            and info.get("content")
            and int(info.get("contentTokens") or 0) >= (35 if code_snippets else CONTEXT_MIN_TOKENS)
            and len(info_snippets) < max_info
        ):
            seen_info.add(key)
            seen_sources.update(card_sources(info))
            remaining -= int(info.get("contentTokens") or 0)
            info_snippets.append(info)
        if len(code_snippets) + len(info_snippets) >= max_results:
            break
    return {
        "codeSnippets": code_snippets[:max_code],
        "infoSnippets": info_snippets[:max_info],
    }


def composite_code_cards(rows: list[dict[str, Any]], query: str, budget: int) -> list[dict[str, Any]]:
    query_lower = query.lower()
    output: list[dict[str, Any]] = []
    if any(term in query_lower for term in ("install", "setup", "authenticate", "api key", "environment", "credential", "quickstart")):
        card = setup_composite_card(rows, query, budget)
        if card:
            output.append(card)
    if any(term in query_lower for term in ("custom host", "api host", "host endpoint", "endpoint", "base url", "base_url", "host")):
        card = host_composite_card(rows, budget)
        if card:
            output.insert(0, card)
    return output


def setup_composite_card(rows: list[dict[str, Any]], query: str, budget: int) -> dict[str, Any] | None:
    install = first_code_block(rows, lambda block, row, text: install_command(block["code"]))
    env_vars = env_var_names(rows, query=query)
    init = best_code_block(
        rows,
        lambda block, row, text: (
            bool(re.search(r"\bfrom\s+[\w.]+\s+import\s+\w*Client\b", block["code"]))
            or bool(re.search(r"\b\w*Client\s*\(", block["code"]))
        )
        and not generated_context_path(str(row.get("matched_path") or row.get("path") or "").lower()),
        lambda block, row, text: setup_init_block_score(block, row, query, rows),
    )
    if not install and not env_vars and not init:
        return None
    code_list: list[dict[str, str]] = []
    if install:
        code_list.append({"language": install.get("language") or "bash", "code": trim_to_token_budget(install["code"], 160)})
    if env_vars:
        exports = "\n".join(f'export {name}="<your-{name.lower().replace("_", "-")}>"' for name in env_vars[:3])
        code_list.append({"language": "bash", "code": exports})
    if init:
        code_list.append(
            {
                "language": init.get("language") or "python",
                "code": focused_code_for_query(init["code"], query, token_budget=420),
            }
        )
    content = "\n\n".join(item["code"] for item in code_list)
    tokens = approximate_tokens(content)
    if tokens <= 0 or tokens > budget + 120:
        code_list = bounded_code_list(code_list, budget)
        content = "\n\n".join(item["code"] for item in code_list)
        tokens = approximate_tokens(content)
    return {
        "codeTitle": "Install, authenticate, and initialize",
        "codeDescription": "A compact setup path assembled from the highest-ranked official setup, credential, and client-initialization snippets.",
        "codeId": "oz:composite:setup",
        "codeLanguage": code_list[0].get("language") if code_list else "",
        "codeTokens": tokens,
        "pageTitle": "Setup",
        "codeList": code_list,
        "source": composite_sources([install, init], rows),
    }


def host_composite_card(rows: list[dict[str, Any]], budget: int) -> dict[str, Any] | None:
    config = first_code_block(
        rows,
        lambda block, row, text: (
            ("configuration" in block["code"].lower() and "host" in block["code"].lower())
            or bool(re.search(r"\bhost\s*=", block["code"]))
        ),
    )
    client = first_code_block(
        rows,
        lambda block, row, text: "client(config" in block["code"].lower()
        or "client(configuration" in block["code"].lower()
        or "configuration(" in block["code"].lower(),
    )
    if not config and not client:
        return None
    code_list: list[dict[str, str]] = []
    for block in (config, client):
        if block and block["code"] not in {item["code"] for item in code_list}:
            code_list.append({"language": block.get("language") or "python", "code": trim_to_token_budget(block["code"], 900)})
    content = "\n\n".join(item["code"] for item in code_list)
    tokens = approximate_tokens(content)
    if tokens <= 0 or tokens > budget + 120:
        code_list = bounded_code_list(code_list, budget)
        content = "\n\n".join(item["code"] for item in code_list)
        tokens = approximate_tokens(content)
    return {
        "codeTitle": "Configure a custom API host",
        "codeDescription": "Shows the source-backed configuration host override and the adjacent client-configuration pattern when available.",
        "codeId": "oz:composite:custom-host",
        "codeLanguage": code_list[0].get("language") if code_list else "",
        "codeTokens": tokens,
        "pageTitle": "Configuration",
        "codeList": code_list,
        "source": composite_sources([config, client], rows),
    }


def first_code_block(rows: list[dict[str, Any]], predicate: Any) -> dict[str, str] | None:
    for row in rows:
        text = str(row.get("snippet") or "").strip()
        if not text:
            continue
        for block in extract_code_blocks(text):
            if predicate(block, row, text):
                return {**block, "source": source_id(row)}
    return None


def best_code_block(rows: list[dict[str, Any]], predicate: Any, scorer: Any) -> dict[str, str] | None:
    best: tuple[float, dict[str, str]] | None = None
    for row in rows:
        text = str(row.get("snippet") or "").strip()
        if not text:
            continue
        for block in extract_code_blocks(text):
            if not predicate(block, row, text):
                continue
            scored = (float(scorer(block, row, text)), {**block, "source": source_id(row)})
            if best is None or scored[0] > best[0]:
                best = scored
    return best[1] if best else None


PROVIDER_CLIENT_TERMS = {
    "anthropic",
    "azure",
    "bedrock",
    "cohere",
    "gemini",
    "google",
    "groq",
    "mistral",
    "openai",
    "vertex",
}


def setup_init_block_score(block: dict[str, str], row: dict[str, Any], query: str, rows: list[dict[str, Any]]) -> float:
    code = block["code"]
    code_lower = code.lower()
    query_lower = query.lower()
    path = str(row.get("matched_path") or row.get("path") or "").lower()
    title = str(row.get("title") or "").lower()
    source = source_id(row).lower()
    metadata = row.get("source_metadata") if isinstance(row.get("source_metadata"), dict) else row.get("metadata_json")
    metadata_text = " ".join(str(value).lower() for value in (metadata or {}).values())
    score = packet_row_score(row, query)
    if re.search(r"\bfrom\s+[\w.]+\s+import\s+\w*Client\b", code):
        score += 420
    if re.search(r"\b\w*Client\s*\(", code):
        score += 220
    if re.search(r"\bConfiguration\s*\(", code) or re.search(r"\bConfig\w*\s*\(", code):
        score += 120
    if "api_key" in code_lower or "access_token" in code_lower or "token" in code_lower:
        score += 160
    if "readme" in path or "quickstart" in path or "getting-started" in path:
        score += 420
    scope_terms = library_scope_terms(rows, query)
    own_hits = sum(1 for term in scope_terms if term and term in code_lower)
    if own_hits:
        score += 520 + own_hits * 80
    elif scope_terms and any(term in f"{path} {source} {metadata_text}" for term in scope_terms):
        score += 120
    provider_hits = {term for term in PROVIDER_CLIENT_TERMS if term in f"{code_lower} {path} {title}"}
    unrequested_provider_hits = {term for term in provider_hits if term not in query_lower}
    if unrequested_provider_hits:
        score -= 900
    if provider_hits and provider_hits.issubset(unrequested_provider_hits) and not own_hits:
        score -= 500
    if "basellmclient" in code_lower or "standalone openai client" in code_lower:
        score -= 420
    return score


GENERIC_SCOPE_TERMS = {
    "api",
    "client",
    "docs",
    "documentation",
    "examples",
    "guide",
    "library",
    "latest",
    "main",
    "python",
    "sdk",
    "source",
}


def library_scope_terms(rows: list[dict[str, Any]], query: str) -> set[str]:
    terms: set[str] = set()
    for row in rows[:12]:
        for value in (row.get("library"), row.get("vendor")):
            text = str(value or "").lower()
            for term in re.findall(r"[a-z][a-z0-9]+", text.replace(".", " ").replace("-", " ").replace("/", " ")):
                if len(term) >= 4 and term not in GENERIC_SCOPE_TERMS:
                    terms.add(term)
        metadata = row.get("source_metadata") if isinstance(row.get("source_metadata"), dict) else row.get("metadata_json")
        if isinstance(metadata, dict):
            for key in ("product", "package", "module", "framework"):
                for term in re.findall(r"[a-z][a-z0-9]+", str(metadata.get(key) or "").lower()):
                    if len(term) >= 4 and term not in GENERIC_SCOPE_TERMS:
                        terms.add(term)
    for term in re.findall(r"[a-z][a-z0-9]+", query.lower()):
        if len(term) >= 4 and term not in GENERIC_SCOPE_TERMS and term not in PROVIDER_CLIENT_TERMS:
            terms.add(term)
    expanded = set(terms)
    for term in terms:
        if term.endswith("ai") and len(term) > 4:
            expanded.add(term[:-2])
        expanded.add(term.replace("_", ""))
    return expanded


def install_command(code: str) -> bool:
    lowered = code.lower()
    return "pip install" in lowered or "npm install" in lowered or "pnpm add" in lowered or "yarn add" in lowered


def env_var_names(rows: list[dict[str, Any]], query: str = "") -> list[str]:
    scores: dict[str, int] = {}
    query_terms = {term for term in re.findall(r"[a-z][a-z0-9]+", query.lower()) if len(term) >= 4}
    for row in rows:
        text = str(row.get("snippet") or "")
        for name in re.findall(r"\b[A-Z][A-Z0-9_]*(?:API_KEY|TOKEN|SECRET|KEY)\b", text):
            lowered = name.lower()
            score = scores.get(name, 0) + 1
            if query_terms and any(term in lowered for term in query_terms):
                score += 100
            if name in {"API_KEY", "TOKEN", "SECRET", "KEY", "BEARER_TOKEN"}:
                score -= 20
            if query_terms and not any(term in lowered for term in query_terms) and "_" in name:
                score -= 30
            scores[name] = score
    ordered = [name for name, _score in sorted(scores.items(), key=lambda item: (-item[1], item[0]))]
    query_matched = [name for name in ordered if query_terms and any(term in name.lower() for term in query_terms)]
    return query_matched or ordered


def composite_sources(blocks: list[dict[str, str] | None], rows: list[dict[str, Any]]) -> str:
    sources = [str(block.get("source") or "").strip() for block in blocks if block]
    return ", ".join(dict.fromkeys(source for source in sources if source))


def packet_row_score(row: dict[str, Any], query: str) -> float:
    score = float(row.get("score") or 0)
    text = str(row.get("snippet") or "").lower()
    path = str(row.get("matched_path") or row.get("path") or "").lower()
    title = str(row.get("title") or "").lower()
    role = str(row.get("role") or row.get("content_type") or "")
    query_lower = query.lower()
    setup_query = any(term in query_lower for term in ("install", "initialize", "authenticate", "api key", "environment", "credential", "setup", "quickstart"))
    credential_query = any(term in query_lower for term in ("api key", "authenticate", "auth", "credential", "environment", "secret"))
    host_query = any(term in query_lower for term in ("custom host", "api host", "host endpoint", "endpoint", "base url", "base_url", "host"))
    if role in {"code_example", "cli"}:
        score += 90
    if "readme" in path or "llms" in path:
        score += 160
    if "quickstart" in path or "getting-started" in path or "installation" in title:
        score += 120
    if setup_query:
        if "pip install" in text or "npm install" in text:
            score += 260
        if "api key" in text or "smallest_api_key" in text or "environment variable" in text:
            score += 170
        if "client()" in text or "atomsclient" in text or "wavesclient" in text:
            score += 140
        if role == "cli":
            score += 160
        if any(term in title for term in ("installation", "api key", "environment", "authenticate", "credential")):
            score += 180
        if generated_context_path(path) and not any(term in title for term in ("installation", "api key", "environment", "authenticate", "credential")):
            score -= 340
    if credential_query:
        if any(term in title for term in ("api key", "environment", "authenticate", "credential", "secret")):
            score += 360
        if re.search(r"\b[A-Z][A-Z0-9_]*(?:API_KEY|TOKEN|SECRET|KEY)\b", str(row.get("snippet") or "")):
            score += 160
        if "api key" in text or "environment variable" in text or "export " in text:
            score += 180
    if host_query:
        if "configuration" in text and ("host" in text or "base url" in text or "endpoint" in text):
            score += 520
        if re.search(r"\bhost\s*=", str(row.get("snippet") or "")) or "base_url" in text or "base url" in text:
            score += 360
        if "configuration" in title:
            score += 260
    if "```" in text:
        score += 60
    if generated_context_path(path) and not any(term in query_lower for term in ("schema", "request body", "response", "model", "class")):
        score -= 320
    return score


def generated_context_path(path: str) -> bool:
    return (
        "api-reference/source/" in path
        or "/models/" in path
        or path.endswith("-init-py.md")
        or "response" in path
        or "request" in path
    )


def extract_code_blocks(text: str) -> list[dict[str, str]]:
    blocks: list[dict[str, str]] = []
    for match in FENCE_RE.finditer(text):
        code = match.group("code").strip()
        if not code:
            continue
        blocks.append(
            {
                "language": (match.group(2) or "").strip(),
                "code": code,
            }
        )
    return blocks


def code_snippet_card(
    row: dict[str, Any],
    text: str,
    code_blocks: list[dict[str, str]],
    budget: int,
    *,
    query: str,
) -> dict[str, Any]:
    description = str(row.get("description") or first_prose_before_code(text) or "").strip()
    code_list = bounded_code_list(focused_code_blocks_for_query(code_blocks, query), budget)
    content = "\n\n".join(block["code"] for block in code_list)
    tokens = approximate_tokens(description + "\n" + content)
    return {
        "codeTitle": context_card_title(row, default="Code example"),
        "codeDescription": bounded_string(description, 420),
        "codeId": source_id(row),
        "codeLanguage": code_list[0].get("language") if code_list else str(row.get("code_language") or ""),
        "codeTokens": tokens,
        "pageTitle": page_title(row),
        "codeList": code_list,
        "source": source_id(row),
    }


def info_snippet_card(row: dict[str, Any], text: str, budget: int) -> dict[str, Any]:
    prose = strip_code_blocks(text)
    if not prose.strip():
        prose = str(row.get("description") or "").strip()
    prose = trim_to_token_budget(prose, min(max(budget, 1), 600))
    return {
        "title": context_card_title(row, default="Documentation"),
        "pageId": source_id(row),
        "pageTitle": page_title(row),
        "content": prose,
        "contentTokens": approximate_tokens(prose) if prose else 0,
        "source": source_id(row),
    }


def bounded_code_list(blocks: list[dict[str, str]], budget: int) -> list[dict[str, str]]:
    output: list[dict[str, str]] = []
    remaining = max(budget, 1)
    for block in blocks:
        code = trim_to_token_budget(block["code"], min(remaining, 900))
        if not code.strip():
            continue
        output.append({"language": block.get("language") or "", "code": code})
        remaining -= approximate_tokens(code)
        if remaining <= 0 or len(output) >= 3:
            break
    return output


def focused_code_blocks_for_query(blocks: list[dict[str, str]], query: str) -> list[dict[str, str]]:
    focused: list[dict[str, str]] = []
    for block in blocks:
        code = block.get("code") or ""
        next_code = focused_code_for_query(code, query, token_budget=620)
        focused.append({"language": block.get("language") or "", "code": next_code or code})
    return focused


def focused_code_for_query(code: str, query: str, *, token_budget: int) -> str:
    if approximate_tokens(code) <= token_budget:
        return code.strip()
    lowered_query = query.lower()
    setup_like = any(
        term in lowered_query
        for term in (
            "install",
            "setup",
            "initialize",
            "initialise",
            "authenticate",
            "api key",
            "environment",
            "configuration",
            "custom host",
            "api host",
            "endpoint",
        )
    )
    if setup_like:
        focused = focused_setup_code(code, lowered_query, token_budget)
        if focused:
            return focused
    focused = focused_lines_around_terms(code, meaningful_query_terms(lowered_query) | task_profile_terms(lowered_query)[0], token_budget)
    return focused or trim_to_token_budget(code, token_budget)


def focused_setup_code(code: str, lowered_query: str, token_budget: int) -> str:
    lines = code.splitlines()
    selected: list[str] = []
    import_lines = [line for line in lines if re.match(r"\s*(from\s+[\w.]+\s+import\s+.+|import\s+[\w.]+)", line)]
    selected.extend(import_lines[:6])
    triggers = (
        "client(",
        "configuration(",
        "config(",
        "api_key",
        "access_token",
        "token",
        "host=",
        "base_url",
        "base url",
        "os.getenv",
        "getenv",
    )
    skip_call_terms = ("create_agent(", "new_agent(", "synthesize(", "transcribe(")
    for index, line in enumerate(lines):
        lowered = line.lower()
        if any(term in lowered for term in triggers):
            if any(term in lowered for term in skip_call_terms) and not any(term in lowered_query for term in ("create", "new", "synthesize", "transcribe")):
                continue
            selected.extend(code_statement_window(lines, index))
        elif "api key" in lowered or "environment variable" in lowered:
            selected.append(line)
    selected = compact_code_lines(selected)
    if not selected:
        return ""
    focused = "\n".join(selected)
    return trim_to_token_budget(focused, token_budget)


def focused_lines_around_terms(code: str, terms: set[str], token_budget: int) -> str:
    normalized_terms = {term.lower() for term in terms if len(term) >= 3}
    if not normalized_terms:
        return ""
    lines = code.splitlines()
    selected_indexes: set[int] = set()
    for index, line in enumerate(lines):
        lowered = line.lower()
        if any(term in lowered for term in normalized_terms):
            for offset in range(-4, 9):
                candidate = index + offset
                if 0 <= candidate < len(lines):
                    selected_indexes.add(candidate)
            selected_indexes.update(range(index, min(len(lines), index + len(code_statement_window(lines, index)))))
    if not selected_indexes:
        return ""
    selected = [lines[index] for index in sorted(selected_indexes)]
    imports = [line for line in lines if re.match(r"\s*(from\s+[\w.]+\s+import\s+.+|import\s+[\w.]+)", line)]
    selected = compact_code_lines([*imports[:6], *selected])
    return trim_to_token_budget("\n".join(selected), token_budget)


def code_statement_window(lines: list[str], start: int) -> list[str]:
    output = [lines[start]]
    paren_balance = lines[start].count("(") + lines[start].count("[") + lines[start].count("{")
    paren_balance -= lines[start].count(")") + lines[start].count("]") + lines[start].count("}")
    base_indent = len(lines[start]) - len(lines[start].lstrip())
    for index in range(start + 1, min(len(lines), start + 28)):
        line = lines[index]
        stripped = line.strip()
        indent = len(line) - len(line.lstrip())
        if not stripped:
            if paren_balance <= 0:
                break
            output.append(line)
            continue
        if paren_balance <= 0 and indent <= base_indent and re.match(r"\w", stripped):
            break
        output.append(line)
        paren_balance += line.count("(") + line.count("[") + line.count("{")
        paren_balance -= line.count(")") + line.count("]") + line.count("}")
        if paren_balance <= 0 and index > start and stripped.endswith((")", "]", "}")):
            break
    return output


def compact_code_lines(lines: list[str]) -> list[str]:
    output: list[str] = []
    seen: set[str] = set()
    blank = False
    for line in lines:
        key = line.strip()
        if not key:
            if not blank and output:
                output.append("")
                blank = True
            continue
        if key in seen:
            continue
        seen.add(key)
        output.append(line.rstrip())
        blank = False
    while output and not output[-1].strip():
        output.pop()
    return output


def first_prose_before_code(text: str) -> str:
    before = FENCE_RE.split(text, maxsplit=1)[0]
    before = re.sub(r"^#{1,6}\s+", "", before.strip())
    lines = [line.strip() for line in before.splitlines() if line.strip()]
    return " ".join(lines[-3:])[:420]


def strip_code_blocks(text: str) -> str:
    return clean_context_text(FENCE_RE.sub("", text))


def context_card_title(row: dict[str, Any], *, default: str) -> str:
    title = str(row.get("title") or "").strip()
    if title:
        return bounded_string(re.sub(r"^(Example|Reference|Command|Concept|Workflow):\s*", "", title), 180)
    heading = row.get("heading_path") or []
    if isinstance(heading, list) and heading:
        return bounded_string(str(heading[-1]), 180)
    path = str(row.get("matched_path") or row.get("path") or "")
    return bounded_string(path.rsplit("/", 1)[-1].replace("-", " ").replace(".md", "").title() or default, 180)


def source_id(row: dict[str, Any]) -> str:
    return str(row.get("source_anchor") or row.get("matched_path") or row.get("path") or "").strip()


def page_title(row: dict[str, Any]) -> str:
    heading = row.get("heading_path") or []
    if isinstance(heading, list) and heading:
        return " > ".join(str(item) for item in heading[-3:])
    return context_card_title(row, default="Documentation")


def card_key(card: dict[str, Any]) -> str:
    for key in ("codeId", "pageId", "source"):
        value = str(card.get(key) or "").strip()
        if value:
            return value + ":" + str(card.get("codeTitle") or card.get("title") or "")
    return ""


def card_sources(card: dict[str, Any]) -> set[str]:
    raw = str(card.get("source") or card.get("codeId") or card.get("pageId") or "")
    return {part.strip() for part in raw.split(",") if part.strip()}


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


def context_retrieval_mode(rows: list[dict[str, Any]]) -> str:
    modes = {str(row.get("retrieval_mode") or "").strip() for row in rows}
    modes.discard("")
    if any(mode.startswith("vector") for mode in modes) and "context_snippets" in modes:
        return "hybrid_context_vector"
    if any(mode.startswith("vector") for mode in modes):
        return "hybrid_vector"
    if "context_snippets" in modes:
        return "context_snippets"
    return first_retrieval_mode(rows)


def context_source_text(row: dict[str, Any]) -> str:
    matched = clean_context_text(str(row.get("_matched_text") or ""))
    parent = clean_context_text(str(row.get("_parent_text") or ""))
    if row.get("retrieval_mode") == "context_snippets":
        return format_context_card_text(row, matched)
    content_type = str(row.get("content_type") or "")
    if matched and useful_context_text(matched, row):
        return matched
    if content_type in {"code_example", "config", "cli", "error_ref"} and matched:
        return matched
    if content_type == "api_reference" and matched and row.get("symbols"):
        return matched
    return matched or parent


def format_context_card_text(row: dict[str, Any], matched: str) -> str:
    title = str(row.get("title") or "").strip()
    description = str(row.get("description") or "").strip()
    constraints = [str(item).strip() for item in row.get("constraints") or [] if str(item).strip()]
    parts: list[str] = []
    if title and title.lower() not in matched[:240].lower():
        parts.append(f"## {title}")
    if description and description.lower() not in matched[:400].lower():
        parts.append(description)
    if matched:
        parts.append(matched)
    if constraints:
        constraint_text = "\n".join(f"- {item}" for item in constraints[:3])
        if constraint_text.lower() not in "\n".join(parts).lower():
            parts.append("Constraints:\n" + constraint_text)
    return clean_context_text("\n\n".join(parts))


def clean_context_text(text: str) -> str:
    text = text.replace("\r\n", "\n").strip()
    text = re.sub(r"\A---\n.*?\n---\n+", "", text, flags=re.S)
    text = re.sub(r"\A\+\+\+\n.*?\n\+\+\+\n+", "", text, flags=re.S)
    text = re.sub(r"\n---\n(?:title|description|url|version):.*?\n---\n", "\n", text, flags=re.S)
    lines = []
    for line in text.splitlines():
        stripped = line.strip()
        lowered = stripped.lower()
        if stripped.startswith("Source:") or stripped.startswith("**Source:**"):
            continue
        if re.match(r"^>?\s*for an index of all .*documentation, see .*/llms(?:[-.]full)?\.txt", lowered):
            continue
        if re.match(r"^>?\s*for a semantic overview of .*documentation, see .*/sitemap\.md", lowered):
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
        if not selected and not in_fence and line_tokens > budget:
            return trim_long_line(line, budget)
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


def trim_long_line(line: str, budget: int) -> str:
    parts = re.findall(r"\S+\s*", line)
    selected: list[str] = []
    tokens = 0
    for part in parts:
        part_tokens = approximate_tokens(part)
        if selected and tokens + part_tokens > budget:
            break
        selected.append(part.rstrip())
        tokens += part_tokens
        if tokens >= budget:
            break
    return " ".join(value.strip() for value in selected if value.strip()).strip()


def approximate_tokens(text: str) -> int:
    return token_count(text)


def bounded_string(value: Any, max_chars: int) -> str:
    text = str(value or "")
    return text if len(text) <= max_chars else text[:max_chars].rstrip()


def bounded_list(value: list[Any], max_chars: int) -> list[str]:
    output: list[str] = []
    for item in value:
        output.append(bounded_string(item, max_chars))
    return output


def bounded_metadata(value: Any) -> dict[str, Any]:
    if not isinstance(value, dict):
        return {}
    allowed = {
        "source_type",
        "source_kind",
        "product",
        "current",
        "deprecated",
        "legacy",
        "protocol",
        "language",
        "framework",
        "endpoint",
        "method",
        "operation_id",
        "channel",
        "action",
        "message",
    }
    return {key: value[key] for key in allowed if key in value}


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
