from __future__ import annotations

import re
from typing import Any

CONTEXT_MIN_TOKENS = 18

from oz_api.retrieval_packet_terms import *  # noqa: F403
from oz_api.retrieval_packet_scoring import *  # noqa: F403
from oz_api.retrieval_packet_code_extract import *  # noqa: F403
from oz_api.retrieval_packet_code_cards import *  # noqa: F403

FENCE_RE = re.compile(r"(?ms)^\s*(`{3,}|~{3,})[ \t]*([^\n`]*)\n(?P<code>.*?)(?:^\s*\1\s*$)")
FENCE_START_RE = re.compile(r"(?m)^\s*(`{3,}|~{3,})[ \t]*([^\n`]*)\n")


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
    max_info = min(max_results, 5 if max_results >= 5 else max_results)
    ordered = sorted(rows, key=lambda row: packet_row_score(row, query), reverse=True)
    required_terms = context_required_terms(query, ordered)
    for row in ordered:
        if remaining <= 0:
            break
        text = context_source_text(row) if not row.get("snippet") else str(row.get("snippet") or "").strip()
        if not text:
            continue
        row_source = source_id(row)
        if row_source and row_source in seen_sources:
            continue
        if low_value_context_row(row, query):
            continue
        title_lower = str(row.get("title") or "").lower()
        code_blocks = code_blocks_satisfying_context_terms(extract_code_blocks(text), required_terms)
        if code_blocks and row_satisfies_context_terms(row, required_terms):
            card = code_snippet_card(row, text, code_blocks, remaining, query=query)
            key = card_code_key(card) or card_key(card)
            if key and key not in seen_code and card.get("codeList") and len(code_snippets) < max_code:
                seen_code.add(key)
                seen_sources.update(card_sources(card))
                remaining -= int(card.get("codeTokens") or 0)
                code_snippets.append(card)
                if len(code_snippets) >= max_code:
                    continue
        info = info_snippet_card(row, text, remaining, query=query)
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


def card_code_key(card: dict[str, Any]) -> str:
    code = "\n".join(str(item.get("code") or "") for item in card.get("codeList") or [])
    normalized = re.sub(r"\s+", " ", code.strip().lower())
    return normalized[:500]


def low_value_context_row(row: dict[str, Any], query: str) -> bool:
    query_lower = query.lower()
    path = str(row.get("matched_path") or row.get("path") or "").lower()
    title = str(row.get("title") or "").lower()
    source = str(row.get("source_anchor") or row.get("source_url") or "").lower()
    text = f"{path} {title} {source}"
    config_query = any(
        term in query_lower
        for term in (
            "install",
            "dependency",
            "package",
            "configuration",
            "config",
            "pubspec",
            "package.json",
            "requirements",
            "environment",
        )
    )
    if not config_query and any(
        term in text
        for term in (
            "pubspec.yaml",
            "package.json",
            "package-lock.json",
            "pnpm-lock",
            "yarn.lock",
            "requirements.txt",
            "pyproject.toml",
            "setup.py",
        )
    ):
        return True
    if "smoke" not in query_lower and ("smoke.html" in text or "smoke-test" in text or "smoke test" in title):
        return True
    return False

