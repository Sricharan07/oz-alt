from __future__ import annotations

import re
from dataclasses import dataclass, field


@dataclass(frozen=True)
class QueryIntent:
    name: str
    content_type: str
    symbols: list[str]
    important_terms: list[str] = field(default_factory=list)
    phrases: list[str] = field(default_factory=list)
    slugs: list[str] = field(default_factory=list)
    preferred_content_types: list[str] = field(default_factory=list)
    negative_content_types: list[str] = field(default_factory=list)


ERROR_RE = re.compile(r"\b(?:ERR_[A-Z0-9_]+|[A-Z][A-Za-z0-9]*Error|[45]\d{2})\b")
SYMBOL_RE = re.compile(
    r"\b[A-Z][A-Za-z0-9]*(?:\.[A-Za-z_$][\w$]*)?\b"
    r"|\b[a-z_$][A-Za-z0-9_$]*[A-Z][A-Za-z0-9_$]*(?:\.[A-Za-z_$][\w$]*)?\b"
    r"|\b[a-z_$][\w$]*\([^)]*\)"
)
CLI_RE = re.compile(r"(?:^|\s)(?:\$|npx|npm|pnpm|yarn|cargo|pip|uv|docker|kubectl|aws|oz)\s+", re.I)
CONFIG_RE = re.compile(
    r"\b(config|configure|configuration|yaml|toml|env|environment variable|setting|next\.config|remotePatterns)\b",
    re.I,
)
API_TERMS = ("api of", "method", "function", "class", "parameter", "signature", "return")
EXAMPLE_TERMS = ("how do i", "example", "show me", "sample", "snippet", "code")
CLI_TERMS_RE = re.compile(r"\b(cli|command line|install command|terminal command)\b", re.I)
PHRASE_CANDIDATES = (
    "route handler",
    "route handlers",
    "server action",
    "server actions",
    "server component",
    "server components",
    "client component",
    "client components",
    "use client",
    "use server",
    "search params",
    "route groups",
    "cache tags",
    "remote patterns",
    "app router",
    "post body",
    "response json",
)
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
    "app",
    "router",
    "server",
    "servers",
    "action",
    "actions",
    "component",
    "components",
    "client",
    "route",
    "routes",
    "handler",
    "handlers",
    "body",
    "post",
    "url",
    "json",
    "yaml",
    "http",
    "https",
    "next",
    "nextjs",
    "next.js",
    "js",
}
TERM_STOPWORDS = SYMBOL_STOPWORDS | {
    "value",
    "values",
    "work",
    "works",
    "using",
    "implement",
    "read",
    "set",
    "return",
    "difference",
    "between",
    "external",
    "domains",
}


def classify_query(query: str) -> QueryIntent:
    return plan_query(query)


def plan_query(query: str) -> QueryIntent:
    lowered = query.lower()
    symbols = query_symbols(query)
    phrases = query_phrases(query)
    important_terms = query_terms(query, phrases=phrases, symbols=symbols)
    slugs = query_slugs(phrases, symbols, important_terms)
    preferred: list[str] = []
    negative: list[str] = []
    if ERROR_RE.search(query) or any(token in lowered for token in (" error", "exception", "traceback", "failed", "failure")):
        preferred = ["error_ref", "api_reference", "code_example"]
        negative = ["cli", "config"]
        return QueryIntent("error", "error_ref", symbols, important_terms, phrases, slugs, preferred, negative)
    if CLI_RE.search(query) or CLI_TERMS_RE.search(query):
        preferred = ["cli", "code_example"]
        negative = ["config"]
        return QueryIntent("cli", "cli", symbols, important_terms, phrases, slugs, preferred, negative)
    is_config = bool(CONFIG_RE.search(query))
    api_query = any(token in lowered for token in API_TERMS)
    example_query = any(token in lowered for token in EXAMPLE_TERMS)
    if is_config:
        preferred = ["config", "api_reference", "code_example"]
        negative = ["cli"]
        return QueryIntent("config", "config", symbols, important_terms, phrases, slugs, preferred, negative)
    if example_query:
        preferred = ["code_example", "api_reference", "prose"]
        negative = ["cli", "config"]
        return QueryIntent("example", "code_example", symbols, important_terms, phrases, slugs, preferred, negative)
    if symbols or api_query:
        preferred = ["api_reference", "code_example", "prose"]
        negative = ["cli", "config"]
        return QueryIntent("api", "api_reference", symbols, important_terms, phrases, slugs, preferred, negative)
    if any(token in lowered for token in ("what is", "explain", "why", "concept", "overview", "guide")):
        preferred = ["prose", "api_reference", "code_example"]
        negative = ["cli", "config"]
        return QueryIntent("prose", "prose", symbols, important_terms, phrases, slugs, preferred, negative)
    return QueryIntent("neutral", "prose", symbols, important_terms, phrases, slugs, ["prose", "api_reference"], ["cli"])


def intent_name(query: str) -> str:
    return classify_query(query).content_type


def query_symbols(query: str) -> list[str]:
    symbols: list[str] = []
    for match in SYMBOL_RE.finditer(query):
        value = match.group(0).strip()
        if value.endswith("()"):
            value = value[:-2]
        if value.lower().endswith(".js") and value.count(".") == 1:
            continue
        if len(value) < 2 or value.lower() in SYMBOL_STOPWORDS:
            continue
        if value.isupper() and len(value) <= 4 and not value.startswith("ERR_"):
            continue
        if value and value not in symbols:
            symbols.append(value)
    return symbols[:8]


def query_phrases(query: str) -> list[str]:
    lowered = query.lower()
    phrases: list[str] = []
    for phrase in PHRASE_CANDIDATES:
        if phrase in lowered and phrase not in phrases:
            phrases.append(phrase)
    for match in re.finditer(r"`([^`]{2,80})`|\"([^\"]{2,80})\"", query):
        phrase = (match.group(1) or match.group(2) or "").strip()
        if phrase and phrase.lower() not in {item.lower() for item in phrases}:
            phrases.append(phrase)
    return phrases[:12]


def query_terms(query: str, *, phrases: list[str], symbols: list[str]) -> list[str]:
    output: list[str] = []
    seen: set[str] = set()
    protected = {compact_key(value) for value in symbols}
    protected.update(compact_key(value) for value in phrases)
    for raw in re.findall(r"[A-Za-z0-9_]+", query):
        for value in term_variants(raw):
            key = compact_key(value)
            if not key or key in seen:
                continue
            if key not in protected and (value.lower() in TERM_STOPWORDS or len(key) <= 1):
                continue
            seen.add(key)
            output.append(value.lower())
    return output[:24]


def term_variants(raw: str) -> list[str]:
    compact = compact_key(raw)
    split = re.sub(r"([a-z0-9])([A-Z])", r"\1 \2", raw.replace("_", " "))
    values = [compact]
    values.extend(part.lower() for part in split.split())
    return [value for value in values if value]


def query_slugs(phrases: list[str], symbols: list[str], terms: list[str]) -> list[str]:
    output: list[str] = []
    for value in [*phrases, *symbols]:
        slug = slugify(value)
        if slug and slug not in output:
            output.append(slug)
    for term in terms:
        if len(term) < 3 or term in TERM_STOPWORDS:
            continue
        slug = slugify(term)
        if slug and slug not in output:
            output.append(slug)
    for first, second in zip(terms, terms[1:]):
        if first in TERM_STOPWORDS or second in TERM_STOPWORDS:
            continue
        slug = slugify(f"{first} {second}")
        if slug and slug not in output:
            output.append(slug)
    return output[:16]


def compact_key(value: str) -> str:
    return re.sub(r"[^a-z0-9]+", "", value.lower())


def slugify(value: str) -> str:
    return re.sub(r"[^a-z0-9]+", "-", value.lower()).strip("-")
