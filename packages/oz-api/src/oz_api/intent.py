from __future__ import annotations

import re
from dataclasses import dataclass


@dataclass(frozen=True)
class QueryIntent:
    name: str
    content_type: str
    symbols: list[str]


ERROR_RE = re.compile(r"\b(?:ERR_[A-Z0-9_]+|[A-Z][A-Za-z0-9]*Error|[45]\d{2})\b")
SYMBOL_RE = re.compile(r"\b[A-Z][A-Za-z0-9]*(?:\.[A-Za-z_$][\w$]*)?\b|\b[a-z_$][\w$]*\([^)]*\)")
CLI_RE = re.compile(r"(?:^|\s)(?:\$|npx|npm|pnpm|yarn|cargo|pip|uv|docker|kubectl|aws|oz)\s+", re.I)
CONFIG_RE = re.compile(r"\b(config|configure|yaml|toml|json|env|environment variable|option|setting)\b", re.I)


def classify_query(query: str) -> QueryIntent:
    lowered = query.lower()
    symbols = query_symbols(query)
    if ERROR_RE.search(query) or any(token in lowered for token in (" error", "exception", "traceback", "failed", "failure")):
        return QueryIntent("error", "error_ref", symbols)
    if CLI_RE.search(query) or any(token in lowered for token in ("command", "cli", "install command")):
        return QueryIntent("cli", "cli", symbols)
    if CONFIG_RE.search(query):
        return QueryIntent("config", "config", symbols)
    if symbols or any(token in lowered for token in ("api of", "method", "function", "class", "parameter", "signature", "return")):
        return QueryIntent("api", "api_reference", symbols)
    if any(token in lowered for token in ("how do i", "example", "show me", "sample", "snippet", "code")):
        return QueryIntent("example", "code_example", symbols)
    if any(token in lowered for token in ("what is", "explain", "why", "concept", "overview", "guide")):
        return QueryIntent("prose", "prose", symbols)
    return QueryIntent("neutral", "prose", symbols)


def intent_name(query: str) -> str:
    return classify_query(query).content_type


def query_symbols(query: str) -> list[str]:
    symbols: list[str] = []
    for match in SYMBOL_RE.finditer(query):
        value = match.group(0).strip()
        if value.lower() in {"api", "json", "yaml", "http", "https"}:
            continue
        if value.endswith("()"):
            value = value[:-2]
        if value and value not in symbols:
            symbols.append(value)
    return symbols[:8]
