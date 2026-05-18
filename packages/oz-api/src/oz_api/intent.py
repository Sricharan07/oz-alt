from __future__ import annotations

import re
from dataclasses import dataclass


@dataclass(frozen=True)
class QueryIntent:
    name: str
    content_type: str
    symbols: list[str]


ERROR_RE = re.compile(r"\b(?:ERR_[A-Z0-9_]+|[A-Z][A-Za-z0-9]*Error|[45]\d{2})\b")
SYMBOL_RE = re.compile(
    r"\b[A-Z][A-Za-z0-9]*(?:\.[A-Za-z_$][\w$]*)?\b"
    r"|\b[a-z_$][A-Za-z0-9_$]*[A-Z][A-Za-z0-9_$]*(?:\.[A-Za-z_$][\w$]*)?\b"
    r"|\b[a-z_$][\w$]*\([^)]*\)"
)
CLI_RE = re.compile(r"(?:^|\s)(?:\$|npx|npm|pnpm|yarn|cargo|pip|uv|docker|kubectl|aws|oz)\s+", re.I)
CONFIG_RE = re.compile(r"\b(config|configure|yaml|toml|json|env|environment variable|option|setting)\b", re.I)
API_TERMS = ("api of", "method", "function", "class", "parameter", "signature", "return")
EXAMPLE_TERMS = ("how do i", "example", "show me", "sample", "snippet", "code")
SYMBOL_STOPWORDS = {
    "a",
    "i",
    "the",
    "in",
    "on",
    "at",
    "to",
    "of",
    "for",
    "with",
    "from",
    "by",
    "and",
    "or",
    "if",
    "then",
    "else",
    "how",
    "what",
    "why",
    "when",
    "where",
    "which",
    "who",
    "is",
    "are",
    "was",
    "were",
    "do",
    "does",
    "did",
    "can",
    "should",
    "could",
    "would",
    "will",
    "use",
    "using",
    "read",
    "write",
    "set",
    "get",
    "create",
    "make",
    "add",
    "remove",
    "update",
    "api",
    "json",
    "yaml",
    "http",
    "https",
}


def classify_query(query: str) -> QueryIntent:
    lowered = query.lower()
    symbols = query_symbols(query)
    if ERROR_RE.search(query) or any(token in lowered for token in (" error", "exception", "traceback", "failed", "failure")):
        return QueryIntent("error", "error_ref", symbols)
    if CLI_RE.search(query) or any(token in lowered for token in ("command", "cli", "install command")):
        return QueryIntent("cli", "cli", symbols)
    if CONFIG_RE.search(query):
        return QueryIntent("config", "config", symbols)
    api_query = any(token in lowered for token in API_TERMS)
    example_query = any(token in lowered for token in EXAMPLE_TERMS)
    if symbols and api_query:
        return QueryIntent("api", "api_reference", symbols)
    if example_query:
        return QueryIntent("example", "code_example", symbols)
    if symbols or api_query:
        return QueryIntent("api", "api_reference", symbols)
    if any(token in lowered for token in ("what is", "explain", "why", "concept", "overview", "guide")):
        return QueryIntent("prose", "prose", symbols)
    return QueryIntent("neutral", "prose", symbols)


def intent_name(query: str) -> str:
    return classify_query(query).content_type


def query_symbols(query: str) -> list[str]:
    symbols: list[str] = []
    for match in SYMBOL_RE.finditer(query):
        value = match.group(0).strip()
        if value.endswith("()"):
            value = value[:-2]
        if len(value) < 2 or value.lower() in SYMBOL_STOPWORDS:
            continue
        if value and value not in symbols:
            symbols.append(value)
    return symbols[:8]
