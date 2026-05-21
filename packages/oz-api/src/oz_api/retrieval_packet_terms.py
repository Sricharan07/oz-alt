from __future__ import annotations

import re
from typing import Any

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
    required_terms = context_required_terms(query, rows)
    return [
        {
            **row,
            "score": float(row.get("score") or 0)
            + context_packet_candidate_boost(row, query, rows)
            + context_required_term_boost(row, required_terms),
        }
        for row in rows
    ]


CONTEXT_REQUIRED_TERM_STOP_TERMS = GENERIC_LIBRARY_TERMS | {
    "about",
    "after",
    "agent",
    "agents",
    "answer",
    "available",
    "before",
    "build",
    "call",
    "code",
    "configuration",
    "default",
    "create",
    "details",
    "does",
    "docs",
    "example",
    "examples",
    "from",
    "generated",
    "give",
    "guide",
    "handle",
    "help",
    "implement",
    "implementation",
    "into",
    "locally",
    "make",
    "need",
    "output",
    "please",
    "python",
    "request",
    "requests",
    "response",
    "safe",
    "show",
    "snippet",
    "snippets",
    "tool",
    "tools",
    "using",
    "want",
    "what",
    "when",
    "with",
}


def context_required_terms(query: str, rows: list[dict[str, Any]]) -> set[str]:
    """Rare query terms that exist in candidates must dominate context ranking.

    The context pipeline intentionally broadens a query with generic probes so it
    can recover setup/example/operation evidence. Without this guard, generic
    probe hits can outrank the row that contains the actual user term, e.g.
    "webhook". Terms are selected from the query only when at least one
    candidate contains them and they are not so common that they stop being
    discriminative.
    """

    raw_terms = {
        term
        for term in re.findall(r"[a-z][a-z0-9_]+", query.lower().replace("-", " "))
        if len(term) >= 5 and term not in CONTEXT_REQUIRED_TERM_STOP_TERMS
    }
    if not raw_terms or not rows:
        return set()
    row_texts = [context_row_search_text(row) for row in rows]
    terms: set[str] = set()
    max_common = max(3, int(len(row_texts) * 0.65))
    for term in raw_terms:
        hits = sum(1 for text in row_texts if term in text)
        specific_term = len(term) >= 7 or "_" in term or term.endswith(("hook", "hooks"))
        if 0 < hits <= max_common or (hits > 0 and specific_term):
            terms.add(term)
    return terms


def context_row_search_text(row: dict[str, Any]) -> str:
    content = str(row.get("_matched_text") or row.get("snippet") or row.get("content") or "")
    if len(content) > 2600:
        content = content[:2600]
    values = [
        str(row.get("title") or ""),
        str(row.get("description") or ""),
        str(row.get("matched_path") or row.get("relative_path") or row.get("path") or ""),
        " ".join(str(item) for item in row.get("heading_path") or []),
        " ".join(str(item) for item in row.get("symbols") or []),
        " ".join(str(item) for item in row.get("entities") or []),
        " ".join(str(item) for item in row.get("task_tags") or []),
        str(row.get("code") or ""),
        content,
    ]
    return " ".join(values).lower()


def context_required_term_boost(row: dict[str, Any], required_terms: set[str]) -> float:
    if not required_terms:
        return 0.0
    text = context_row_search_text(row)
    hits = {term for term in required_terms if term in text}
    if not hits:
        return -1800.0
    score = len(hits) * 1800.0
    if hits == required_terms:
        score += 650.0
    return score


def row_satisfies_context_terms(row: dict[str, Any], required_terms: set[str]) -> bool:
    if not required_terms:
        return True
    text = context_row_search_text(row)
    return any(term in text for term in required_terms)


def code_blocks_satisfying_context_terms(blocks: list[dict[str, str]], required_terms: set[str]) -> list[dict[str, str]]:
    blocks = leaf_code_blocks(blocks)
    if not required_terms:
        return blocks
    output: list[dict[str, str]] = []
    for block in blocks:
        code = (block.get("code") or "").lower()
        if any(term in code for term in required_terms):
            output.append(block)
    return output


def leaf_code_blocks(blocks: list[dict[str, str]]) -> list[dict[str, str]]:
    from oz_api.retrieval_packet_code_extract import extract_code_blocks

    output: list[dict[str, str]] = []
    for block in blocks:
        code = block.get("code") or ""
        inner = extract_code_blocks(code) if "```" in code or "~~~" in code else []
        if inner:
            output.extend(leaf_code_blocks(inner))
        else:
            output.append(block)
    return output


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
    if text_lower.lstrip().startswith(":param") or "\n:param " in text_lower[:600]:
        score -= 900.0
    if inline_install_command(text) or "pip install" in text_lower or "npm install" in text_lower:
        score += 1450.0
    if "install" in query_lower and any(term in title for term in ("installation", "dependencies", "install")):
        score += 900.0
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
            score += 520.0 if "_" in term else (320.0 if len(term) >= 8 else 180.0)
    for term in negative:
        if term and term in text:
            score -= 620.0 if len(term) >= 8 else 380.0
    query_terms = meaningful_query_terms(lowered)
    direct_hits = sum(1 for term in query_terms if term in text)
    score += min(420.0, direct_hits * 70.0)
    return score


def task_profile_terms(lowered_query: str) -> tuple[set[str], set[str]]:
    positive: set[str] = set()
    negative: set[str] = set()
    if any(term in lowered_query for term in ("install", "setup", "quickstart", "initialize", "initialise", "authenticate", "api key", "credential", "environment variable")):
        positive.update({"install", "installation", "pip install", "npm install", "api key", "api_key", "environment variable", "client", "configuration", "quickstart"})
    if any(term in lowered_query for term in ("requirements.txt", "requirements", "pin", "version range", "safe version", "dependency")):
        positive.update({"requirements.txt", "requirements", "pin", "pinned", "version", "major version", "pip install", "install"})
    if any(term in lowered_query for term in ("create", "new", "build", "add")):
        positive.update({"create", "new", "build", "add", "required", "response", "example"})
    if any(term in lowered_query for term in ("list", "available", "all", "search")):
        positive.update({"list", "available", "all", "search", "collection", "response"})
    if any(term in lowered_query for term in ("get", "fetch", "retrieve", "details", "read")):
        positive.update({"get", "fetch", "retrieve", "details", "read", "identifier", "response"})
    if any(term in lowered_query for term in ("update", "edit", "patch", "modify")):
        positive.update({"update", "edit", "patch", "modify", "required", "response"})
    if any(term in lowered_query for term in ("delete", "remove", "destroy")):
        positive.update({"delete", "remove", "destroy", "identifier", "response"})
    if any(term in lowered_query for term in ("upload", "file", "pdf", "document", "image", "audio")):
        positive.update({"upload", "file", "document", "multipart", "input", "example"})
    if "knowledge base" in lowered_query or "knowledgebase" in lowered_query:
        positive.update({"knowledge base", "kb", "document", "add document", "adding documents"})
    if "webhook" in lowered_query:
        positive.update({"webhook", "webhooks", "endpoint", "subscriptions", "agent"})
    if any(term in lowered_query for term in ("stream", "streaming", "chunk", "chunks", "realtime", "websocket", "sse")):
        positive.update({"stream", "streaming", "chunk", "chunks", "realtime", "websocket", "sse", "buffer"})
    if any(term in lowered_query for term in ("model", "choose", "quality", "latency", "tradeoff", "trade-off", "available")):
        positive.update({"model", "models", "available", "quality", "latency", "tradeoff"})
    if any(term in lowered_query for term in ("request body", "required fields", "required parameters", "schema")):
        positive.update({"request body", "required", "schema", "parameters", "field", "fields"})
    if any(term in lowered_query for term in ("speed", "consistency", "similarity", "enhancement", "optional", "controls")):
        positive.update({"speed", "consistency", "similarity", "enhancement", "controls", "optional"})
    if any(term in lowered_query for term in ("failed", "failure", "recover", "retry", "exception", "error")):
        positive.update({"error", "exception", "retry", "failed", "failure", "status", "recover"})
    if any(term in lowered_query for term in ("request id", "request ids", "metadata", "debug", "debugging", "logs")):
        positive.update({"request id", "request_id", "metadata", "headers", "debug", "logs", "logging"})
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

