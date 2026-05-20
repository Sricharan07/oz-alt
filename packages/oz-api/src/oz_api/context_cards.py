from __future__ import annotations

import hashlib
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Iterable


MAX_SECTION_TOKENS = 1800
MAX_SNIPPET_TOKENS = 900
SECTION_SNIPPET_TYPES = {"prose", "guide"}
CHUNK_SNIPPET_TYPES = {"api_reference", "code_example", "config", "cli", "error_ref"}

IDENT_RE = re.compile(r"\b[A-Za-z_$][A-Za-z0-9_$]*(?:\.[A-Za-z_$][A-Za-z0-9_$]*)?\b")
FENCE_RE = re.compile(r"(?ms)^\s*(`{3,}|~{3,})([A-Za-z0-9_+.-]*)\n(?P<code>.*?)(?:^\s*\1\s*$)")
SENTENCE_RE = re.compile(r"(?s)([^.!?\n][^.!?\n]{20,220}[.!?])")
CONSTRAINT_RE = re.compile(
    r"(?is)\b(?:must|must not|cannot|can't|can not|only|required|requires|unsupported|not supported|deprecated|warning|good to know)\b[^.\n]*(?:[.\n]|$)"
)

APPLIES_PATTERNS: tuple[tuple[str, str], ...] = (
    ("App Router", r"\bapp router\b|/app/|api-reference/app/|guides/app/"),
    ("Pages Router", r"\bpages router\b|/pages/|api-reference/pages/|guides/pages/"),
    ("Server Components", r"\bserver components?\b"),
    ("Client Components", r"\bclient components?\b|\buse client\b"),
    ("Server Actions", r"\bserver actions?\b|\buse server\b"),
    ("Route Handlers", r"\broute handlers?\b|file-conventions/route\b"),
    ("Proxy", r"\bproxy\b|\bmiddleware\b"),
    ("TypeScript", r"\btypescript\b|\.d\.ts\b|\btypedroutes\b"),
    ("OpenAPI", r"\bopenapi\b|\bswagger\b"),
)

TASK_PATTERNS: tuple[tuple[str, str], ...] = (
    ("authentication", r"\bauth(?:entication|orization)?\b|\bsession\b|\bjwt\b"),
    ("cookies", r"\bcookies?\b|nextrequest|nextresponse"),
    ("routing", r"\broute\b|\brouting\b|\bsegments?\b|\blayouts?\b"),
    ("data-fetching", r"\bfetch\b|\bdata fetching\b|getstatic|getserver"),
    ("mutation", r"\bmutat(?:e|ion)|server action|form action"),
    ("cache", r"\bcache\b|revalidate|cachetag|cachelife"),
    ("metadata", r"\bmetadata\b|opengraph|robots|sitemap"),
    ("image", r"\bimage\b|remotePatterns|imageResponse"),
    ("navigation", r"\bnavigation\b|router|link|search params"),
    ("configuration", r"\bconfig\b|next\.config|environment variable|\.env\b"),
    ("cli", r"\bcli\b|command line|\bnpm\b|\bnpx\b|\byarn\b|\bpnpm\b"),
    ("errors", r"\berror\b|exception|failed|failure|status code"),
    ("forms", r"\bforms?\b|\bsubmissions?\b"),
    ("typescript", r"\btypescript\b|typedroutes|types?\b"),
    ("observability", r"\binstrumentation\b|opentelemetry|web vitals|analytics"),
)

ENTITY_STOPWORDS = {
    "the",
    "and",
    "for",
    "with",
    "from",
    "this",
    "that",
    "next",
    "app",
    "pages",
    "router",
    "server",
    "client",
    "component",
    "components",
    "route",
    "routes",
    "guide",
    "docs",
    "api",
    "reference",
    "function",
    "functions",
    "config",
    "configuration",
}


@dataclass(frozen=True)
class SourceSection:
    section_key: str
    source_document_id: int | None
    path: str
    source_url: str
    source_anchor: str
    title: str
    heading_path: list[str]
    content_type: str
    start_line: int
    end_line: int | None
    content: str
    token_count: int
    quality_score: float


@dataclass(frozen=True)
class ContextSnippet:
    snippet_key: str
    section_key: str
    source_section_id: int | None
    primary_chunk_id: int | None
    path: str
    source_url: str
    source_anchor: str
    title: str
    description: str
    role: str
    applies_to: list[str]
    entities: list[str]
    task_tags: list[str]
    heading_path: list[str]
    symbols: list[str]
    code_language: str | None
    code: str | None
    constraints: list[str]
    related_chunk_ids: list[int]
    start_line: int
    end_line: int | None
    content: str
    token_count: int
    quality_score: float


def build_source_sections(rows: list[dict[str, Any]]) -> list[SourceSection]:
    grouped: dict[str, list[dict[str, Any]]] = {}
    for row in rows:
        if not indexable_context_row(row):
            continue
        grouped.setdefault(section_key(row), []).append(row)
    sections: list[SourceSection] = []
    for key, group in sorted(grouped.items(), key=lambda item: (str(item[1][0].get("path") or ""), int(item[1][0].get("start_line") or 1))):
        group = sorted(group, key=lambda row: (int(row.get("start_line") or 1), int(row.get("ordinal") or 1)))
        first = group[0]
        title = section_title(first)
        content = trim_to_token_budget(join_unique(row_text(row) for row in group), MAX_SECTION_TOKENS)
        if not content.strip():
            continue
        sections.append(
            SourceSection(
                section_key=key,
                source_document_id=optional_int(first.get("source_document_id")),
                path=str(first.get("path") or "README.md"),
                source_url=str(first.get("source_url") or ""),
                source_anchor=str(first.get("source_anchor") or ""),
                title=title,
                heading_path=list_of_strings(first.get("heading_path")),
                content_type=dominant_content_type(group),
                start_line=min(int(row.get("start_line") or 1) for row in group),
                end_line=max_optional_int(row.get("end_line") for row in group),
                content=content,
                token_count=approximate_tokens(content),
                quality_score=max(float(row.get("quality_score") or 1.0) for row in group),
            )
        )
    return sections


def build_context_snippets(rows: list[dict[str, Any]], section_ids: dict[str, int]) -> list[ContextSnippet]:
    output: list[ContextSnippet] = []
    seen: set[str] = set()
    section_groups: dict[str, list[dict[str, Any]]] = {}
    for row in rows:
        if not indexable_context_row(row):
            continue
        section_groups.setdefault(section_key(row), []).append(row)

    for key, group in sorted(section_groups.items(), key=lambda item: (str(item[1][0].get("path") or ""), int(item[1][0].get("start_line") or 1))):
        group = sorted(group, key=lambda row: (int(row.get("start_line") or 1), int(row.get("ordinal") or 1)))
        section = section_snippet_from_group(key, group, section_ids.get(key))
        if section and section.snippet_key not in seen:
            seen.add(section.snippet_key)
            output.append(section)
        for row in group:
            snippet = chunk_snippet_from_row(row, section_ids.get(key), key)
            if snippet and snippet.snippet_key not in seen:
                seen.add(snippet.snippet_key)
                output.append(snippet)
    return output


def section_snippet_from_group(key: str, group: list[dict[str, Any]], source_section_id: int | None) -> ContextSnippet | None:
    if not group:
        return None
    first = group[0]
    role = section_role(group)
    content_type = dominant_content_type(group)
    if len(group) < 2 and content_type not in SECTION_SNIPPET_TYPES:
        return None
    content = trim_to_token_budget(join_unique(row_text(row) for row in group), MAX_SNIPPET_TOKENS)
    if low_signal(content):
        return None
    heading_path = list_of_strings(first.get("heading_path"))
    title = agent_title(first, role=role, prefix="")
    symbols = unique_strings(symbol for row in group for symbol in list_of_strings(row.get("symbols")))
    entities = entity_list(first, content, symbols=symbols)
    task_tags = task_tag_list(first, content)
    chunk_ids = [int(row["id"]) for row in group if optional_int(row.get("id"))]
    return ContextSnippet(
        snippet_key=f"{key}#section",
        section_key=key,
        source_section_id=source_section_id,
        primary_chunk_id=chunk_ids[0] if chunk_ids else None,
        path=str(first.get("path") or "README.md"),
        source_url=str(first.get("source_url") or ""),
        source_anchor=str(first.get("source_anchor") or ""),
        title=title,
        description=description_for(content, heading_path),
        role=role,
        applies_to=applies_to_list(first, content),
        entities=entities,
        task_tags=task_tags,
        heading_path=heading_path,
        symbols=symbols,
        code_language=first_code_block(content)[0],
        code=first_code_block(content)[1],
        constraints=constraint_list(content),
        related_chunk_ids=chunk_ids[:24],
        start_line=min(int(row.get("start_line") or 1) for row in group),
        end_line=max_optional_int(row.get("end_line") for row in group),
        content=content,
        token_count=approximate_tokens(content),
        quality_score=max(float(row.get("quality_score") or 1.0) for row in group),
    )


def chunk_snippet_from_row(row: dict[str, Any], source_section_id: int | None, key: str) -> ContextSnippet | None:
    content_type = str(row.get("content_type") or "prose")
    content = trim_to_token_budget(row_text(row), MAX_SNIPPET_TOKENS)
    if content_type not in CHUNK_SNIPPET_TYPES and not list_of_strings(row.get("symbols")):
        return None
    if low_signal(content):
        return None
    role = role_for_content_type(content_type, content)
    heading_path = list_of_strings(row.get("heading_path"))
    symbols = list_of_strings(row.get("symbols"))
    code_language, code = first_code_block(content)
    chunk_id = optional_int(row.get("id"))
    snippet_key = str(row.get("chunk_key") or f"{row.get('path')}#{row.get('ordinal')}")
    return ContextSnippet(
        snippet_key=f"{snippet_key}#chunk",
        section_key=key,
        source_section_id=source_section_id,
        primary_chunk_id=chunk_id,
        path=str(row.get("path") or "README.md"),
        source_url=str(row.get("source_url") or ""),
        source_anchor=str(row.get("source_anchor") or ""),
        title=agent_title(row, role=role),
        description=description_for(content, heading_path),
        role=role,
        applies_to=applies_to_list(row, content),
        entities=entity_list(row, content, symbols=symbols),
        task_tags=task_tag_list(row, content),
        heading_path=heading_path,
        symbols=symbols,
        code_language=code_language,
        code=code,
        constraints=constraint_list(content),
        related_chunk_ids=[chunk_id] if chunk_id else [],
        start_line=int(row.get("start_line") or 1),
        end_line=optional_int(row.get("end_line")),
        content=content,
        token_count=approximate_tokens(content),
        quality_score=float(row.get("quality_score") or 1.0),
    )


def select_context_snippets(rows: list[dict[str, Any]], query: str, *, max_results: int, max_tokens: int) -> list[dict[str, Any]]:
    facets = query_facets(query)
    selected: list[dict[str, Any]] = []
    covered: set[str] = set()
    used_paths: dict[str, int] = {}
    used_titles: set[str] = set()
    remaining = max(max_tokens, 1)
    candidates = sorted(rows, key=lambda row: float(row.get("score") or 0), reverse=True)
    while candidates and len(selected) < max_results and remaining > 0:
        best_index = -1
        best_score = float("-inf")
        for index, row in enumerate(candidates):
            adjusted = assembly_score(row, facets=facets, covered=covered, used_paths=used_paths, used_titles=used_titles)
            if adjusted > best_score:
                best_score = adjusted
                best_index = index
        if best_index < 0:
            break
        row = candidates.pop(best_index)
        text = str(row.get("_matched_text") or row.get("content") or "").strip()
        tokens = approximate_tokens(text)
        if tokens <= 0 or tokens > remaining + 80:
            text = trim_to_token_budget(text, remaining)
            tokens = approximate_tokens(text)
        if not text.strip() or tokens <= 0:
            continue
        selected.append(row)
        remaining -= tokens
        path = str(row.get("matched_path") or row.get("path") or "")
        title = str(row.get("title") or "")
        used_paths[path] = used_paths.get(path, 0) + 1
        if title:
            used_titles.add(title.lower())
        covered.update(row_facets(row, facets))
    return selected


def assembly_score(
    row: dict[str, Any],
    *,
    facets: set[str],
    covered: set[str],
    used_paths: dict[str, int],
    used_titles: set[str],
) -> float:
    score = float(row.get("score") or 0)
    row_coverage = row_facets(row, facets)
    new_coverage = row_coverage - covered
    score += len(new_coverage) * 140.0
    if new_coverage:
        score += 60.0
    role = str(row.get("role") or row.get("content_type") or "")
    if role in {"code_example", "api_reference", "workflow"}:
        score += 25.0
    path = str(row.get("matched_path") or row.get("path") or "")
    score -= used_paths.get(path, 0) * 85.0
    if str(row.get("title") or "").lower() in used_titles:
        score -= 55.0
    token_count = int(row.get("token_count") or 0)
    if token_count < 35:
        score -= 35.0
    if token_count > 1100:
        score -= 20.0
    return score


def query_facets(query: str) -> set[str]:
    lowered = query.lower()
    facets: set[str] = set()
    for tag, pattern in TASK_PATTERNS + APPLIES_PATTERNS:
        if re.search(pattern, lowered, re.I):
            facets.add(normalize_facet(tag))
    for value in IDENT_RE.findall(query):
        if keep_entity(value):
            facets.add(normalize_facet(value))
    for word in re.findall(r"[A-Za-z][A-Za-z0-9_-]{3,}", query):
        if keep_entity(word):
            facets.add(normalize_facet(word))
    return {facet for facet in facets if facet}


def row_facets(row: dict[str, Any], facets: set[str]) -> set[str]:
    if not facets:
        return set()
    values: list[str] = []
    for key in ("title", "description", "path", "matched_path", "content_type", "role", "_matched_text", "content"):
        values.append(str(row.get(key) or ""))
    for key in ("entities", "task_tags", "applies_to", "symbols", "heading_path"):
        raw = row.get(key)
        if isinstance(raw, list):
            values.extend(str(item) for item in raw)
        else:
            values.append(str(raw or ""))
    blob = normalize_facet(" ".join(values))
    return {facet for facet in facets if facet and facet in blob}


def section_key(row: dict[str, Any]) -> str:
    heading_path = list_of_strings(row.get("heading_path"))
    source_document_id = str(row.get("source_document_id") or "")
    path = str(row.get("path") or "README.md")
    if heading_path:
        key = "\0".join([source_document_id, path, *heading_path])
    else:
        key = "\0".join([source_document_id, path, "top"])
    digest = hashlib.sha256(key.encode("utf-8")).hexdigest()[:24]
    return f"{path}#section-{digest}"


def section_title(row: dict[str, Any]) -> str:
    heading_path = list_of_strings(row.get("heading_path"))
    if heading_path:
        return heading_path[-1]
    path = str(row.get("path") or "README.md")
    return humanize_path(path)


def agent_title(row: dict[str, Any], *, role: str, prefix: str = "") -> str:
    base = section_title(row)
    applies = applies_to_list(row, row_text(row))
    entities = entity_list(row, row_text(row), symbols=list_of_strings(row.get("symbols")))
    if role == "code_example":
        action = "Example"
    elif role == "api_reference":
        action = "Reference"
    elif role == "config":
        action = "Configure"
    elif role == "cli":
        action = "Command"
    elif role == "error_ref":
        action = "Troubleshoot"
    elif role == "workflow":
        action = "Workflow"
    else:
        action = "Concept"
    subject_parts = []
    if entities:
        subject_parts.append(entities[0])
    if applies:
        subject_parts.append(applies[0])
    subject = " in ".join(subject_parts[:2])
    if subject and subject.lower() not in base.lower():
        return clean_title(f"{prefix}{action}: {base} ({subject})")
    return clean_title(f"{prefix}{action}: {base}")


def role_for_content_type(content_type: str, content: str) -> str:
    if content_type in {"api_reference", "config", "cli", "error_ref", "code_example"}:
        return content_type
    if FENCE_RE.search(content):
        return "code_example"
    if any(term in content.lower() for term in ("step ", "first,", "next,", "finally", "how to")):
        return "workflow"
    return "concept"


def section_role(group: list[dict[str, Any]]) -> str:
    types = [str(row.get("content_type") or "prose") for row in group]
    if any(kind == "code_example" for kind in types):
        return "workflow"
    if any(kind == "api_reference" for kind in types):
        return "api_reference"
    if any(kind == "config" for kind in types):
        return "config"
    if any(kind == "cli" for kind in types):
        return "cli"
    if any(kind == "error_ref" for kind in types):
        return "error_ref"
    return "workflow" if len(group) > 1 else "concept"


def dominant_content_type(group: list[dict[str, Any]]) -> str:
    counts: dict[str, int] = {}
    for row in group:
        kind = str(row.get("content_type") or "prose")
        counts[kind] = counts.get(kind, 0) + 1
    if not counts:
        return "prose"
    return sorted(counts.items(), key=lambda item: (-item[1], item[0]))[0][0]


def description_for(content: str, heading_path: list[str]) -> str:
    for sentence in SENTENCE_RE.findall(strip_code_fences(content)):
        sentence = clean_inline(sentence)
        if len(sentence) >= 24:
            return sentence[:260].rstrip()
    if heading_path:
        return " > ".join(heading_path[-3:])
    return ""


def applies_to_list(row: dict[str, Any], content: str) -> list[str]:
    blob = " ".join([str(row.get("path") or ""), " ".join(list_of_strings(row.get("heading_path"))), content[:1800]])
    output = []
    for label, pattern in APPLIES_PATTERNS:
        if re.search(pattern, blob, re.I):
            output.append(label)
    return unique_strings(output)[:8]


def task_tag_list(row: dict[str, Any], content: str) -> list[str]:
    blob = " ".join([str(row.get("path") or ""), " ".join(list_of_strings(row.get("heading_path"))), content[:2200]])
    output = []
    for tag, pattern in TASK_PATTERNS:
        if re.search(pattern, blob, re.I):
            output.append(tag)
    return unique_strings(output)[:10]


def entity_list(row: dict[str, Any], content: str, *, symbols: list[str]) -> list[str]:
    values: list[str] = []
    values.extend(symbols)
    path = str(row.get("path") or "")
    values.extend(part for part in re.split(r"[/_.#-]+", path) if keep_entity(part))
    for heading in list_of_strings(row.get("heading_path")):
        values.extend(part for part in re.split(r"[^A-Za-z0-9_$]+", heading) if keep_entity(part))
    for ident in IDENT_RE.findall(content[:2500]):
        if keep_entity(ident):
            values.append(ident)
    return unique_strings(values)[:16]


def constraint_list(content: str) -> list[str]:
    output = []
    for match in CONSTRAINT_RE.finditer(strip_code_fences(content)):
        text = clean_inline(match.group(0))
        if 18 <= len(text) <= 260:
            output.append(text)
    return unique_strings(output)[:5]


def first_code_block(content: str) -> tuple[str | None, str | None]:
    match = FENCE_RE.search(content)
    if not match:
        return None, None
    language = match.group(2).strip() or None
    code = match.group("code").strip()
    return language, code[:4000] if code else None


def indexable_context_row(row: dict[str, Any]) -> bool:
    if not bool(row.get("dedupe_canonical", True)):
        return False
    if int(row.get("ordinal") or 1) == 0:
        return False
    if str(row.get("content_type") or "") == "index":
        return False
    text = row_text(row)
    return not low_signal(text)


def low_signal(text: str) -> bool:
    stripped = text.strip()
    if approximate_tokens(stripped) < 12:
        return True
    lowered = stripped.lower()
    if "index of all docs" in lowered and approximate_tokens(stripped) < 80:
        return True
    return False


def row_text(row: dict[str, Any]) -> str:
    return str(row.get("content") or row.get("text") or "").strip()


def join_unique(values: Iterable[str]) -> str:
    output: list[str] = []
    seen: set[str] = set()
    for value in values:
        text = value.strip()
        if not text:
            continue
        key = re.sub(r"\s+", " ", text.lower())
        if key in seen:
            continue
        seen.add(key)
        output.append(text)
    return "\n\n".join(output)


def trim_to_token_budget(text: str, max_tokens: int) -> str:
    text = text.strip()
    if approximate_tokens(text) <= max_tokens:
        return text
    output: list[str] = []
    tokens = 0
    in_fence = False
    for line in text.splitlines():
        line_tokens = approximate_tokens(line)
        if output and not in_fence and tokens + line_tokens > max_tokens:
            break
        output.append(line)
        tokens += line_tokens
        if line.strip().startswith("```"):
            in_fence = not in_fence
        if tokens >= max_tokens and not in_fence:
            break
    if in_fence:
        output.append("```")
    return "\n".join(output).strip()


def strip_code_fences(text: str) -> str:
    return FENCE_RE.sub(" ", text)


def clean_inline(text: str) -> str:
    return re.sub(r"\s+", " ", text).strip(" -")


def clean_title(text: str) -> str:
    return re.sub(r"\s+", " ", text).strip()[:180]


def humanize_path(path: str) -> str:
    stem = Path(path).stem
    return clean_title(re.sub(r"[-_]+", " ", stem).title() or "Documentation")


def keep_entity(value: str) -> bool:
    value = value.strip("`'\".,:;()[]{}")
    if len(value) < 3:
        return False
    if value.lower() in ENTITY_STOPWORDS:
        return False
    if value.isdigit():
        return False
    return True


def normalize_facet(value: str) -> str:
    return re.sub(r"[^a-z0-9]+", "", value.lower())


def optional_int(value: Any) -> int | None:
    try:
        return int(value) if value is not None else None
    except (TypeError, ValueError):
        return None


def max_optional_int(values: Iterable[Any]) -> int | None:
    ints = [value for value in (optional_int(item) for item in values) if value is not None]
    return max(ints) if ints else None


def list_of_strings(value: Any) -> list[str]:
    if isinstance(value, list):
        return [str(item) for item in value if str(item).strip()]
    return []


def unique_strings(values: Iterable[str]) -> list[str]:
    output: list[str] = []
    seen: set[str] = set()
    for value in values:
        text = str(value).strip()
        if not text:
            continue
        key = text.lower()
        if key in seen:
            continue
        seen.add(key)
        output.append(text)
    return output


def approximate_tokens(text: str) -> int:
    if not text:
        return 0
    return max(1, len(re.findall(r"\w+|[^\w\s]", text)))
