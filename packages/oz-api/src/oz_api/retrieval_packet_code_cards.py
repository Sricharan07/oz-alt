from __future__ import annotations

import re
import textwrap
from typing import Any

from oz_api.token_counting import token_count
from oz_api.retrieval_packet_terms import *  # noqa: F403
from oz_api.retrieval_packet_scoring import *  # noqa: F403
from oz_api.retrieval_packet_code_extract import *  # noqa: F403

VALID_CONTENT_TYPES = {"prose", "guide", "code_example", "api_reference", "config", "cli", "error_ref", "types", "example", "index"}
CONTEXT_MIN_TOKENS = 18

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


def info_snippet_card(row: dict[str, Any], text: str, budget: int, *, query: str = "") -> dict[str, Any]:
    prose = strip_code_blocks(text)
    if not prose.strip():
        prose = str(row.get("description") or "").strip()
    prose = trim_context_text_for_query(prose, query, min(max(budget, 1), 600))
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
    action_terms = query_code_action_terms(query.lower())
    languages = requested_languages(query)
    for block in leaf_code_blocks(blocks):
        code = block.get("code") or ""
        if languages and not code_block_matches_requested_language(block, code, languages):
            continue
        if not usable_code_block(block, query):
            continue
        next_code = focused_code_for_query(code, query, token_budget=620)
        if action_terms and not code_has_action_term(next_code or code, action_terms):
            continue
        focused.append({"language": block.get("language") or "", "code": next_code or code})
    return focused


def usable_code_block(block: dict[str, str], query: str) -> bool:
    code = (block.get("code") or "").strip()
    if not code:
        return False
    lowered = code.lower()
    query_lower = query.lower()
    raw_language = str(block.get("language") or "").lower()
    if raw_language in {"log", "logs", "promql"}:
        return False
    if raw_language in {"markdown", "md", "mdx"}:
        return False
    if "```" in code or "~~~" in code:
        return False
    if re.search(r"(?m)^\s{0,3}#{1,6}\s+\S", code) and "```" in code:
        return False
    if "websocketapp" in lowered and "stream" not in query_lower and "websocket" not in query_lower:
        return False
    if lowered.startswith(":param") or lowered.startswith("parameters") or "\n:param " in lowered[:800]:
        return False
    if lowered.count(":param") >= 2 and not any(term in query_lower for term in ("constructor", "class", "parameters", "schema", "request body")):
        return False
    language = canonical_language(str(block.get("language") or ""))
    if language in {"yaml", "json"} and not any(term in query_lower for term in ("schema", "openapi", "config", "configuration", "request body", "yaml", "json")):
        return False
    if not language and not code_like_block(code):
        return False
    return True


def focused_code_for_query(code: str, query: str, *, token_budget: int) -> str:
    lowered_query = query.lower()
    action_terms = query_code_action_terms(lowered_query)
    if action_terms:
        operation_terms = meaningful_query_terms(lowered_query) | task_profile_terms(lowered_query)[0] | action_terms
        focused = focused_lines_around_terms(code, operation_terms, token_budget)
        if focused and code_has_action_term(focused, action_terms):
            return focused
        if approximate_tokens(code) <= token_budget and code_has_action_term(code, action_terms):
            return code.strip()
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
    if approximate_tokens(code) <= token_budget:
        return code.strip()
    focused = focused_lines_around_terms(code, meaningful_query_terms(lowered_query) | task_profile_terms(lowered_query)[0], token_budget)
    return focused or trim_to_token_budget(code, token_budget)


def query_code_action_terms(lowered_query: str) -> set[str]:
    terms: set[str] = set()
    if "create" in lowered_query:
        terms.add("create")
    if re.search(r"(?<![a-z0-9])new(?![a-z0-9])", lowered_query) and "create" not in lowered_query:
        terms.add("new")
    if "build" in lowered_query and "create" not in lowered_query:
        terms.add("build")
    if re.search(r"(?<![a-z0-9])add(?![a-z0-9])", lowered_query) and "create" not in lowered_query:
        terms.add("add")
    if any(term in lowered_query for term in ("update", "edit", "patch", "modify")):
        terms.update({"update", "edit", "patch", "modify"})
    if any(term in lowered_query for term in ("delete", "remove", "destroy")):
        terms.update({"delete", "remove", "destroy"})
    if any(term in lowered_query for term in ("upload", "pdf", "document", "file")):
        terms.update({"upload", "pdf", "document", "file"})
    if any(term in lowered_query for term in ("stream", "streaming", "websocket", "sse")):
        terms.update({"stream", "streaming", "websocket", "sse"})
    if any(term in lowered_query for term in ("synthesize", "tts", "speech", "save to file")):
        terms.update({"synthesize", "tts", "speech", "save_as", "save"})
    if any(term in lowered_query for term in ("cookie", "cookies")):
        terms.update({"cookie", "cookies"})
    if "webhook" in lowered_query:
        terms.update({"webhook", "webhooks"})
    return terms


def code_has_action_term(code: str, action_terms: set[str]) -> bool:
    original = code
    lowered = code.lower()
    normalized = lowered.replace("_", " ").replace("-", " ")
    for term in action_terms:
        if code_action_term_match(original, lowered, normalized, term):
            return True
    return False


def code_action_term_match(original: str, lowered: str, normalized: str, term: str) -> bool:
    if term == "create":
        return (
            re.search(r"(?:^|[.\s])create[a-z0-9_]*\s*\(", original) is not None
            or re.search(r"\.[Cc]reate[a-zA-Z0-9_]*\s*\(", original) is not None
            or re.search(r"\b(def|function|async\s+function)\s+create[a-zA-Z0-9_]*\s*\(", original) is not None
            or re.search(r"(?m)^\s*(post|curl\s+-x\s+post)\b", lowered) is not None
            or re.search(r"(?m)\bpost\s+/", lowered) is not None
        )
    if term == "new":
        return re.search(r"\bnew\s+[A-Z_][A-Za-z0-9_]*\s*\(", lowered, re.IGNORECASE) is not None
    if term in {"build", "add", "update", "edit", "patch", "delete", "remove", "destroy"}:
        return (
            re.search(rf"(?:^|[.\s]){re.escape(term)}[a-z0-9_]*\s*\(", lowered) is not None
            or re.search(rf"(?m)^\s*(post|put|patch|delete|curl)\b.*\b{re.escape(term)}\b", lowered) is not None
        )
    if term in {"upload", "stream", "streaming", "websocket", "sse", "synthesize", "tts", "webhook", "webhooks"}:
        return term in lowered or term in normalized
    if term in {"pdf", "document", "file"}:
        return (
            re.search(rf"\b{re.escape(term)}\b", normalized) is not None
            or "multipart" in lowered
            or "files=" in lowered
            or ".pdf" in lowered
        )
    if term in {"cookie", "cookies"}:
        return "cookie" in lowered or "cookies" in lowered
    if term in {"save", "save_as"}:
        return "save_as" in lowered or re.search(r"(?:^|[.\s])save[a-z0-9_]*\s*\(", lowered) is not None
    return re.search(rf"\b{re.escape(term)}\b", normalized) is not None


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
        "get_current_user",
        "get_models",
        "get_languages",
        "get_voices",
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
    selected = prune_unused_imports(compact_code_lines(selected))
    if not selected:
        return ""
    focused = normalize_code_indentation(selected)
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
    selected = prune_unused_imports(compact_code_lines([*imports[:6], *selected]))
    return trim_to_token_budget(normalize_code_indentation(selected), token_budget)


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


def prune_unused_imports(lines: list[str]) -> list[str]:
    body = "\n".join(line for line in lines if not re.match(r"\s*(from\s+[\w.]+\s+import\s+.+|import\s+[\w.]+)", line))
    output: list[str] = []
    for line in lines:
        match = re.match(r"(\s*from\s+[\w.]+\s+import\s+)(.+)", line)
        if match:
            names = [part.strip().split(" as ", 1)[-1] for part in match.group(2).split(",")]
            used = [name for name in names if re.search(rf"\b{re.escape(name)}\b", body)]
            if used:
                output.append(match.group(1) + ", ".join(used))
            continue
        output.append(line)
    return output


def normalize_code_indentation(lines: list[str]) -> str:
    import_prefix: list[str] = []
    body: list[str] = []
    for line in lines:
        if re.match(r"\s*(from\s+[\w.]+\s+import\s+.+|import\s+[\w.]+)", line) and not body:
            import_prefix.append(line.strip())
        else:
            body.append(line.rstrip())
    nonblank_body = [line for line in body if line.strip()]
    min_indent = min((len(line) - len(line.lstrip()) for line in nonblank_body), default=0)
    if min_indent > 0:
        body = [line[min_indent:] if len(line) >= min_indent else line for line in body]
    parts = [*import_prefix]
    if import_prefix and any(line.strip() for line in body):
        parts.append("")
    parts.extend(body)
    return textwrap.dedent("\n".join(parts)).strip()


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
    if {"agent_recipe", "code_example", "api_operation", "sdk_method"} & modes:
        return "agent_context"
    if any(mode.startswith("vector") for mode in modes):
        return "hybrid_vector"
    return first_retrieval_mode(rows)


def context_source_text(row: dict[str, Any]) -> str:
    matched = clean_context_text(str(row.get("_matched_text") or ""))
    parent = clean_context_text(str(row.get("_parent_text") or ""))
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


def trim_context_text_for_query(text: str, query: str, budget: int) -> str:
    if approximate_tokens(text) <= budget:
        return text.strip()
    terms = context_focus_terms(query, text)
    if not terms:
        return trim_to_token_budget(text, budget)
    lowered = text.lower()
    positions = [lowered.find(term) for term in terms if lowered.find(term) >= 0]
    if not positions:
        return trim_to_token_budget(text, budget)
    position = min(positions)
    lines = text.splitlines()
    cursor = 0
    center = 0
    for index, line in enumerate(lines):
        if cursor <= position:
            center = index
        else:
            break
        cursor += len(line) + 1
    selected: list[str] = []
    tokens = 0
    for line in lines[max(0, center - 8) : min(len(lines), center + 24)]:
        line_tokens = approximate_tokens(line)
        if selected and tokens + line_tokens > budget:
            break
        selected.append(line)
        tokens += line_tokens
    snippet = "\n".join(selected).strip()
    if center > 8 and snippet:
        snippet = "...\n" + snippet
    return trim_to_token_budget(snippet, budget)


def context_focus_terms(query: str, text: str) -> list[str]:
    lowered = text.lower()
    output: list[str] = []
    seen: set[str] = set()
    for term in re.findall(r"[a-z][a-z0-9_]+", query.lower().replace("-", " ")):
        if len(term) < 5 or term in CONTEXT_REQUIRED_TERM_STOP_TERMS:
            continue
        if term in lowered and term not in seen:
            output.append(term)
            seen.add(term)
    return output


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
