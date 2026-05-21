from __future__ import annotations

import re
from typing import Any

from oz_api.retrieval_packet_code_extract import *  # noqa: F403
from oz_api.retrieval_packet_terms import *  # noqa: F403


def schema_fragment_penalty(row: dict[str, Any], block: dict[str, str]) -> float:
    path = source_id(row).lower()
    language = canonical_language(str(block.get("language") or ""))
    code = (block.get("code") or "").lower()
    if language not in {"yaml", "json"} and "openapi:" not in code and "components:" not in code:
        return 0.0
    if "schema" in path or "openapi" in path or "api-reference" in path:
        return 1400.0
    return 800.0


DOMAIN_STOP_TERMS = {
    "audio",
    "available",
    "choose",
    "client",
    "detect",
    "failed",
    "fetch",
    "generation",
    "handle",
    "latency",
    "model",
    "models",
    "quality",
    "recover",
    "request",
    "requests",
    "response",
    "speech",
    "synthesis",
    "tradeoffs",
    "using",
}


def query_domain_mismatch_penalty(row: dict[str, Any], query: str) -> float:
    terms = {
        term
        for term in meaningful_query_terms(query.lower())
        if term not in DOMAIN_STOP_TERMS and len(term) >= 5
    }
    if not terms:
        return 0.0
    text = " ".join(
        [
            str(row.get("title") or ""),
            str(row.get("matched_path") or row.get("path") or ""),
            str(row.get("library") or ""),
            str(row.get("_matched_text") or row.get("snippet") or "")[:1500],
        ]
    ).lower()
    missing = [term for term in terms if term not in text]
    return min(1800.0, 650.0 * len(missing))


def first_code_block(rows: list[dict[str, Any]], predicate: Any) -> dict[str, str] | None:
    for row in rows:
        text = context_source_text(row) if not row.get("snippet") else str(row.get("snippet") or "").strip()
        if not text:
            continue
        for block in extract_code_blocks(text):
            if predicate(block, row, text):
                return {**block, "source": source_id(row)}
    return None


def first_inline_install_command(rows: list[dict[str, Any]]) -> dict[str, str] | None:
    for row in rows:
        text = str(row.get("snippet") or "").strip()
        if not text:
            continue
        command = inline_install_command(text)
        if command:
            return {"language": "bash", "code": command, "source": source_id(row)}
    return None


def inline_install_command(text: str) -> str:
    match = re.search(
        r"(?<![A-Za-z0-9_-])((?:python(?:3)?\s+-m\s+pip|pip(?:3)?|uv)\s+install\s+[^`\n]+|(?:npm|pnpm|yarn)\s+(?:install|add)\s+[^`\n]+)",
        text,
        flags=re.I,
    )
    if not match:
        return ""
    command = re.sub(r"\s+", " ", match.group(1)).strip()
    return re.sub(r"\s+(?:when|to|and|or|but|if)\b.*$", "", command, flags=re.I).strip()


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


def packet_row_score(row: dict[str, Any], query: str) -> float:
    score = float(row.get("score") or 0)
    text = (context_source_text(row) if not row.get("snippet") else str(row.get("snippet") or "")).lower()
    path = str(row.get("matched_path") or row.get("path") or "").lower()
    title = str(row.get("title") or "").lower()
    role = str(row.get("role") or row.get("content_type") or "")
    query_lower = query.lower()
    query_terms = meaningful_query_terms(query_lower)
    for term in query_terms:
        if term in title:
            score += 520
        elif term in path:
            score += 420
        elif term in text:
            score += 90
    if "knowledge base" in query_lower and ("knowledge base" in title or "knowledge-base" in path):
        score += 640
    if "webhook" in query_lower and ("webhook" in title or "webhook" in path):
        score += 640
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
        if "api key" in text or "environment variable" in text:
            score += 170
        if "client()" in text or re.search(r"\b[A-Z][A-Za-z0-9_]*Client\s*\(", text):
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
