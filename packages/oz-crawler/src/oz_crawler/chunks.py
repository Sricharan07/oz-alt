from __future__ import annotations

import hashlib
import json
import os
import re
from dataclasses import dataclass, replace
from pathlib import Path
from typing import Any
from urllib import request

from oz_crawler.content_types import block_content_type
from oz_crawler.normalize import NormalizedPage, clean_markdown
from oz_crawler.sections import (
    content_hash,
    heading_text,
    markdown_blocks,
    section_blocks,
    source_anchor,
    source_document_key,
    source_path_for_page,
    source_section_key_for_span,
    source_sections_for_page,
)
from oz_crawler.token_counting import token_count

FENCE_RE = re.compile(r"^\s*(`{3,}|~{3,})")
FULL_FENCE_RE = re.compile(r"^(`{3,}|~{3,})([^\n]*)\n(?P<body>.*)\n\1$", re.S)


@dataclass(frozen=True)
class MarkdownChunk:
    text: str
    heading_path: list[str]
    start_line: int
    end_line: int
    content_type: str
    parent_key: str | None = None
    chunk_key: str | None = None


@dataclass
class ContextualPrefixCache:
    path: Path
    values: dict[str, str]

    @classmethod
    def create(cls, target: Path) -> "ContextualPrefixCache":
        path = target / ".oz" / "contextual-prefix-cache.jsonl"
        values: dict[str, str] = {}
        if path.exists():
            for line in path.read_text(encoding="utf-8").splitlines():
                if not line.strip():
                    continue
                try:
                    row = json.loads(line)
                except json.JSONDecodeError:
                    continue
                key = str(row.get("key") or "")
                value = str(row.get("prefix") or "")
                if key and value:
                    values[key] = value
        return cls(path=path, values=values)

    def get(self, key: str) -> str:
        return self.values.get(key, "")

    def set(self, key: str, prefix: str) -> None:
        value = prefix.strip()
        if not key or not value:
            return
        if self.values.get(key) == value:
            return
        self.values[key] = value
        self.path.parent.mkdir(parents=True, exist_ok=True)
        with self.path.open("a", encoding="utf-8") as handle:
            handle.write(json.dumps({"key": key, "prefix": value}, sort_keys=True) + "\n")


def write_chunks(target: Path, pages: list[NormalizedPage]) -> None:
    rows: list[dict[str, Any]] = []
    coverage_rows: list[dict[str, Any]] = []
    seen_chunk_shas: set[str] = set()
    seen_content_keys_by_path: dict[str, set[str]] = {}
    prefix_cache = ContextualPrefixCache.create(target)
    for page in pages:
        source_path = source_path_for_page(page)
        source_sections = source_sections_for_page(page)
        chunks = chunk_markdown(page.markdown, source_url=page.source_url, page_type=page.content_type)
        page_rows: list[dict[str, Any]] = []
        path_content_keys = seen_content_keys_by_path.setdefault(source_path, set())
        for idx, chunk in enumerate(chunks, start=1):
            chunk_key = scoped_chunk_key(source_path, chunk.chunk_key or str(idx))
            parent_chunk_key = scoped_chunk_key(source_path, chunk.parent_key) if chunk.parent_key else None
            chunk_sha = stable_chunk_sha(target, source_path, idx, chunk.text)
            content_sha = content_hash(chunk.text)
            content_key = normalized_chunk_key(chunk.text)
            if chunk_sha in seen_chunk_shas or content_key in path_content_keys:
                continue
            seen_chunk_shas.add(chunk_sha)
            path_content_keys.add(content_key)
            section_key = source_section_key_for_span(source_sections, chunk.start_line, chunk.end_line)
            metadata_json = dict(page.source_metadata or {})
            if section_key:
                metadata_json["source_section_key"] = section_key
            contextual_prefix = chunk_contextual_prefix(page, source_path, chunk, prefix_cache)
            embedding_input_sha = content_hash(f"{contextual_prefix}\n\n{chunk.text}" if contextual_prefix else chunk.text)
            row = {
                "id": chunk_key,
                "path": source_path,
                "source_url": page.source_url,
                "source_anchor": source_anchor(page.source_url, chunk.heading_path, idx),
                "ordinal": idx,
                "chunk_key": chunk_key,
                "parent_chunk_key": parent_chunk_key,
                "chunk_sha": chunk_sha,
                "content_sha": content_sha,
                "start_line": chunk.start_line,
                "end_line": chunk.end_line,
                "heading_path": chunk.heading_path,
                "symbols": chunk_symbols(chunk.text, page.symbols),
                "content_type": chunk.content_type,
                "quality_score": page.quality_score,
                "canonical_url": page.canonical_url or page.source_url,
                "source_document_key": source_document_key(page.canonical_url or page.source_url or page.path or page.title),
                "source_priority": page.source_priority,
                "discovered_from": page.discovered_from,
                "source_section_key": section_key,
                "metadata_json": metadata_json,
                "contextual_prefix": contextual_prefix,
                "embedding_input_sha": embedding_input_sha,
                "token_count": token_count(chunk.text),
                "text": chunk.text,
            }
            rows.append(row)
            page_rows.append(row)
        coverage_rows.append(chunk_coverage_row(page, page_rows))
    (target / "_chunks.jsonl").write_text(
        "".join(json.dumps(row, sort_keys=True) + "\n" for row in rows),
        encoding="utf-8",
    )
    (target / "_chunk_coverage.jsonl").write_text(
        "".join(json.dumps(row, sort_keys=True) + "\n" for row in coverage_rows),
        encoding="utf-8",
    )


def chunk_contextual_prefix(
    page: NormalizedPage,
    source_path: str,
    chunk: MarkdownChunk,
    cache: ContextualPrefixCache | None = None,
) -> str:
    cache_key = contextual_prefix_cache_key(page, source_path, chunk)
    if cache is not None:
        cached = cache.get(cache_key)
        if cached:
            return cached
    llm_prefix = llm_chunk_contextual_prefix(page, source_path, chunk)
    if llm_prefix:
        if cache is not None:
            cache.set(cache_key, llm_prefix)
        return llm_prefix
    return deterministic_chunk_contextual_prefix(page, source_path, chunk)


def contextual_prefix_cache_key(page: NormalizedPage, source_path: str, chunk: MarkdownChunk) -> str:
    payload = {
        "schema": 1,
        "model": os.environ.get("OZ_CONTEXTUAL_PREFIX_LLM_MODEL", "gpt-4.1-mini"),
        "title": page.title,
        "source_url": page.source_url,
        "source_path": source_path,
        "document_sha": content_hash(clean_markdown(page.markdown)),
        "chunk_sha": content_hash(chunk.text),
        "heading_path": chunk.heading_path,
    }
    return hashlib.sha256(json.dumps(payload, sort_keys=True).encode("utf-8")).hexdigest()


def deterministic_chunk_contextual_prefix(page: NormalizedPage, source_path: str, chunk: MarkdownChunk) -> str:
    metadata = page.source_metadata or {}
    parts = [
        f"Document: {page.title}".strip(),
        f"Path: {source_path}",
    ]
    role = str(metadata.get("document_role") or "").strip()
    if role:
        parts.append(f"Role: {role}")
    product = str(metadata.get("product") or "").strip()
    if product:
        parts.append(f"Product: {product}")
    if chunk.heading_path:
        parts.append("Section: " + " > ".join(chunk.heading_path[-4:]))
    if chunk.content_type and chunk.content_type != "prose":
        parts.append(f"Content type: {chunk.content_type}")
    prefix = ". ".join(part for part in parts if part and not part.endswith(":")) + "."
    return limit_section_text(prefix, 100)


def llm_chunk_contextual_prefix(page: NormalizedPage, source_path: str, chunk: MarkdownChunk) -> str:
    if os.environ.get("OZ_CONTEXTUAL_PREFIX_LLM_ENABLED", "").lower() not in {"1", "true", "yes", "on"}:
        return ""
    key = os.environ.get("OPENAI_API_KEY") or os.environ.get("OZ_OPENAI_API_KEY")
    if not key:
        return ""
    document = clean_markdown(page.markdown)
    payload = {
        "model": os.environ.get("OZ_CONTEXTUAL_PREFIX_LLM_MODEL", "gpt-4.1-mini"),
        "input": [
            {
                "role": "system",
                "content": (
                    "Write one concise 50-100 token context prefix for embedding a documentation chunk. "
                    "Use only the document metadata and chunk. Do not add facts not present in the evidence. "
                    "Return plain text only."
                ),
            },
            {
                "role": "user",
                "content": json.dumps(
                    {
                        "title": page.title,
                        "path": source_path,
                        "source_url": page.source_url,
                        "metadata": page.source_metadata or {},
                        "heading_path": chunk.heading_path,
                        "document_excerpt": document[:12000],
                        "chunk": chunk.text[:4000],
                    },
                    ensure_ascii=False,
                ),
            },
        ],
        "temperature": 0,
        "max_output_tokens": 140,
    }
    req = request.Request(
        "https://api.openai.com/v1/responses",
        data=json.dumps(payload).encode("utf-8"),
        headers={"Authorization": f"Bearer {key}", "Content-Type": "application/json"},
        method="POST",
    )
    try:
        with request.urlopen(req, timeout=float(os.environ.get("OZ_CONTEXTUAL_PREFIX_LLM_TIMEOUT_SECONDS", "8"))) as response:
            parsed = json.loads(response.read().decode("utf-8"))
    except Exception:
        return ""
    text = extract_response_text(parsed)
    return valid_contextual_prefix(text, page, chunk)


def extract_response_text(parsed: dict[str, Any]) -> str:
    if isinstance(parsed.get("output_text"), str):
        return parsed["output_text"].strip()
    output = parsed.get("output")
    if not isinstance(output, list):
        return ""
    parts: list[str] = []
    for item in output:
        if not isinstance(item, dict):
            continue
        for content in item.get("content") or []:
            if isinstance(content, dict) and isinstance(content.get("text"), str):
                parts.append(content["text"])
    return "\n".join(parts).strip()


def valid_contextual_prefix(text: str, page: NormalizedPage, chunk: MarkdownChunk) -> str:
    prefix = re.sub(r"\s+", " ", text.strip().strip('"'))
    if not prefix:
        return ""
    if token_count(prefix) > 120:
        prefix = limit_section_text(prefix, 110)
    high_risk = {
        token
        for token in re.findall(r"\b[A-Z][A-Za-z0-9_]+\.[A-Za-z0-9_]+|/[A-Za-z0-9_./{}:-]+|[A-Z][A-Z0-9_]{3,}\b", prefix)
        if token not in {"HTTP", "HTTPS", "JSON", "REST", "SDK", "API", "URL"}
    }
    evidence = f"{page.title}\n{page.source_url}\n{json.dumps(page.source_metadata or {}, sort_keys=True)}\n{chunk.text}"
    compact_evidence = re.sub(r"[^a-z0-9]+", "", evidence.lower())
    for token in high_risk:
        if re.sub(r"[^a-z0-9]+", "", token.lower()) not in compact_evidence:
            return ""
    return prefix


def chunk_coverage_row(page: NormalizedPage, rows: list[dict[str, Any]]) -> dict[str, Any]:
    markdown = clean_markdown(page.markdown)
    lines = markdown.splitlines()
    content_lines = {idx for idx, line in enumerate(lines, start=1) if line.strip() and not heading_text(line)}
    covered_lines: set[int] = set()
    for row in rows:
        start = int(row.get("start_line") or 0)
        end = int(row.get("end_line") or 0)
        if start <= 0 or end < start:
            continue
        covered_lines.update(range(start, end + 1))
    covered_content_lines = content_lines & covered_lines
    fence_spans = code_fence_spans(lines)
    code_fence_lines = {line for start, end in fence_spans for line in range(start, end + 1)}
    covered_code_fence_lines = code_fence_lines & covered_lines
    uncovered = sorted(content_lines - covered_lines)
    source_key = source_document_key(page.canonical_url or page.source_url or page.path or page.title)
    return {
        "source_document_key": source_key,
        "path": source_path_for_page(page),
        "source_url": page.source_url,
        "canonical_url": page.canonical_url or page.source_url,
        "clean_line_count": len(content_lines),
        "covered_line_count": len(covered_content_lines),
        "coverage_ratio": ratio(len(covered_content_lines), len(content_lines)),
        "uncovered_ranges": line_ranges(uncovered),
        "code_fence_count": len(fence_spans),
        "code_fence_line_count": len(code_fence_lines),
        "covered_code_fence_line_count": len(covered_code_fence_lines),
        "code_fence_coverage_ratio": ratio(len(covered_code_fence_lines), len(code_fence_lines)),
        "clean_token_count": token_count(markdown),
        "chunk_count": len(rows),
    }


def code_fence_spans(lines: list[str]) -> list[tuple[int, int]]:
    spans: list[tuple[int, int]] = []
    in_code = False
    fence_marker = ""
    start_line = 0
    for line_number, line in enumerate(lines, start=1):
        marker = fence_marker_for_line(line)
        if not marker:
            continue
        if not in_code:
            in_code = True
            fence_marker = marker[0]
            start_line = line_number
        elif marker[0] == fence_marker:
            spans.append((start_line, line_number))
            in_code = False
            fence_marker = ""
            start_line = 0
    if in_code and start_line:
        spans.append((start_line, len(lines)))
    return spans


def line_ranges(lines: list[int]) -> list[dict[str, int]]:
    if not lines:
        return []
    ranges: list[dict[str, int]] = []
    start = previous = lines[0]
    for line in lines[1:]:
        if line == previous + 1:
            previous = line
            continue
        ranges.append({"start": start, "end": previous})
        start = previous = line
    ranges.append({"start": start, "end": previous})
    return ranges


def ratio(numerator: int, denominator: int) -> float:
    if denominator <= 0:
        return 1.0
    return round(numerator / denominator, 4)


def chunk_markdown(
    markdown: str,
    *,
    source_url: str = "",
    page_type: str = "prose",
    max_tokens: int = 650,
) -> list[MarkdownChunk]:
    max_tokens = min(max_tokens, max_chunk_tokens())
    markdown = clean_markdown(markdown)
    blocks = markdown_blocks(markdown)
    sections = section_blocks(blocks)
    chunks: list[MarkdownChunk] = []
    for section_idx, section in enumerate(sections, start=1):
        section_text = "\n\n".join(block[0] for block in section).strip()
        heading_path = next((block[3] for block in reversed(section) if block[3]), [])
        section_type = block_content_type(source_url, section_text, page_type)
        chunks.extend(chunk_section(section, source_url=source_url, page_type=section_type, max_tokens=max_tokens, parent_key=None))
    return [chunk for chunk in enforce_chunk_token_limit(chunks, max_tokens) if chunk.text.strip()]


def enforce_chunk_token_limit(chunks: list[MarkdownChunk], max_tokens: int) -> list[MarkdownChunk]:
    output: list[MarkdownChunk] = []
    split_budget = max(50, max_tokens - 32)
    for chunk in chunks:
        if token_count(chunk.text) <= max_tokens:
            output.append(chunk)
            continue
        block = (chunk.text, chunk.start_line, chunk.end_line, chunk.heading_path)
        if has_code_fence(chunk.text):
            pieces = split_large_indivisible_block(
                block,
                page_type=chunk.content_type,
                parent_key=chunk.parent_key,
                max_tokens=split_budget,
            )
        else:
            pieces = split_large_block(
                block,
                page_type=chunk.content_type,
                parent_key=chunk.parent_key,
                max_tokens=split_budget,
            )
        output.extend(pieces)
    return output


def chunk_section(
    blocks: list[tuple[str, int, int, list[str]]],
    *,
    source_url: str,
    page_type: str,
    max_tokens: int,
    parent_key: str | None,
) -> list[MarkdownChunk]:
    chunks: list[MarkdownChunk] = []
    current: list[tuple[str, int, int, list[str]]] = []
    current_tokens = 0
    overlap: list[tuple[str, int, int, list[str]]] = []
    for block in blocks:
        block_type = block_content_type(source_url, block[0], page_type)
        block_tokens = token_count(block[0])
        indivisible = block_type in {"code_example", "config", "cli", "error_ref"} or has_code_fence(block[0])
        heading_boundary = bool(re.match(r"^#{2,4}\s+", block[0].strip()))
        should_flush = heading_boundary or current_tokens + block_tokens > max_tokens or (indivisible and not blocks_only_headings(current))
        if current and should_flush:
            append_joined_chunk(chunks, current, source_url=source_url, page_type=page_type, parent_key=parent_key)
            overlap = last_overlap(current)
            current = [] if indivisible else overlap
            current_tokens = sum(token_count(item[0]) for item in current)
        if block_tokens > max_tokens and not indivisible:
            chunks.extend(split_large_block(block, page_type=page_type, parent_key=parent_key, max_tokens=max_tokens))
            current = []
            current_tokens = 0
            continue
        if block_tokens > max_tokens and indivisible:
            chunks.extend(split_large_indivisible_block(block, page_type=block_type, parent_key=parent_key, max_tokens=max_tokens))
            current = []
            current_tokens = 0
            continue
        current.append(block)
        current_tokens += block_tokens
    if current:
        append_joined_chunk(chunks, current, source_url=source_url, page_type=page_type, parent_key=parent_key)
    return chunks


def split_large_indivisible_block(
    block: tuple[str, int, int, list[str]],
    *,
    page_type: str,
    parent_key: str | None,
    max_tokens: int,
) -> list[MarkdownChunk]:
    text, start_line, _, heading_path = block
    fence = FULL_FENCE_RE.match(text.strip())
    if not fence:
        return split_large_block(block, page_type=page_type, parent_key=parent_key, max_tokens=max_tokens)
    marker = fence.group(1)
    language = fence.group(2).strip()
    body_lines = fence.group("body").splitlines()
    chunks: list[MarkdownChunk] = []
    current: list[str] = []
    current_tokens = token_count(f"{marker}{language}\n{marker}")
    current_start = start_line + 1
    body_budget = max(1, max_tokens - token_count(f"{marker}{language}\n{marker}") - 8)
    for offset, line in enumerate(body_lines, start=1):
        for segment in split_text_by_token_budget(line, body_budget):
            line_tokens = token_count(segment)
            if current and current_tokens + line_tokens > max_tokens:
                chunks.append(
                    MarkdownChunk(
                        text=f"{marker}{language}\n" + "\n".join(current).strip() + f"\n{marker}",
                        heading_path=list(heading_path),
                        start_line=current_start - 1,
                        end_line=start_line + offset,
                        content_type=page_type,
                        parent_key=parent_key,
                    )
                )
                current = []
                current_tokens = token_count(f"{marker}{language}\n{marker}")
                current_start = start_line + offset
            current.append(segment)
            current_tokens += line_tokens
    if current:
        chunks.append(
            MarkdownChunk(
                text=f"{marker}{language}\n" + "\n".join(current).strip() + f"\n{marker}",
                heading_path=list(heading_path),
                start_line=current_start - 1,
                end_line=start_line + len(body_lines) + 1,
                content_type=page_type,
                parent_key=parent_key,
            )
        )
    return chunks


def split_large_block(
    block: tuple[str, int, int, list[str]],
    *,
    page_type: str,
    parent_key: str | None,
    max_tokens: int,
) -> list[MarkdownChunk]:
    text, start_line, _, heading_path = block
    chunks: list[MarkdownChunk] = []
    current: list[str] = []
    current_tokens = 0
    current_start = start_line
    for offset, line in enumerate(text.splitlines()):
        for segment in split_text_by_token_budget(line, max_tokens):
            line_tokens = token_count(segment)
            if current and current_tokens + line_tokens > max_tokens:
                chunks.append(
                    MarkdownChunk(
                        text="\n".join(current).strip(),
                        heading_path=list(heading_path),
                        start_line=current_start,
                        end_line=start_line + offset - 1,
                        content_type=page_type,
                        parent_key=parent_key,
                    )
                )
                current = []
                current_tokens = 0
                current_start = start_line + offset
            current.append(segment)
            current_tokens += line_tokens
    if current:
        chunks.append(
            MarkdownChunk(
                text="\n".join(current).strip(),
                heading_path=list(heading_path),
                start_line=current_start,
                end_line=current_start + len(current) - 1,
                content_type=page_type,
                parent_key=parent_key,
            )
        )
    return chunks


def join_chunk(
    blocks: list[tuple[str, int, int, list[str]]],
    *,
    source_url: str,
    page_type: str,
    parent_key: str | None,
) -> MarkdownChunk:
    text = "\n\n".join(block[0] for block in blocks).strip()
    heading_path = next((block[3] for block in reversed(blocks) if block[3]), [])
    return MarkdownChunk(
        text=text,
        heading_path=list(heading_path),
        start_line=blocks[0][1],
        end_line=blocks[-1][2],
        content_type=block_content_type(source_url, text, page_type),
        parent_key=parent_key,
    )


def append_joined_chunk(
    chunks: list[MarkdownChunk],
    blocks: list[tuple[str, int, int, list[str]]],
    *,
    source_url: str,
    page_type: str,
    parent_key: str | None,
) -> None:
    chunk = join_chunk(blocks, source_url=source_url, page_type=page_type, parent_key=parent_key)
    if useful_chunk_text(chunk.text):
        chunks.append(chunk)


def useful_chunk_text(text: str) -> bool:
    non_heading = "\n".join(line for line in text.splitlines() if not re.match(r"^#{1,6}\s+", line.strip())).strip()
    if not non_heading:
        return False
    return bool(non_heading)


def blocks_only_headings(blocks: list[tuple[str, int, int, list[str]]]) -> bool:
    return bool(blocks) and all(heading_text(block[0]) is not None for block in blocks)


def last_overlap(blocks: list[tuple[str, int, int, list[str]]]) -> list[tuple[str, int, int, list[str]]]:
    if not blocks:
        return []
    overlap: list[tuple[str, int, int, list[str]]] = []
    tokens = 0
    for block in reversed(blocks):
        tokens += token_count(block[0])
        if tokens > 80:
            break
        overlap.insert(0, block)
    return overlap


def limit_section_text(text: str, max_tokens: int) -> str:
    if token_count(text) <= max_tokens:
        return text
    lines: list[str] = []
    total = 0
    for line in text.splitlines():
        total += token_count(line)
        if total > max_tokens:
            break
        lines.append(line)
    return "\n".join(lines).strip()


def has_code_fence(text: str) -> bool:
    return bool(re.search(r"(?m)^\s*(?:`{3,}|~{3,})", text))


def fence_marker_for_line(line: str) -> str:
    match = FENCE_RE.match(line)
    return match.group(1) if match else ""


def stable_chunk_sha(target: Path, source_path: str, ordinal: int, text: str) -> str:
    vendor, library, version = target.parts[-3:]
    payload = "\0".join([vendor, library, version, source_path, str(ordinal), text])
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()


def normalized_chunk_key(text: str) -> str:
    normalized = re.sub(r"\s+", " ", text.strip().lower())
    return hashlib.sha256(normalized.encode("utf-8")).hexdigest()


def chunk_symbols(text: str, page_symbols: tuple[str, ...] | list[str]) -> list[str]:
    output: list[str] = []
    for symbol in page_symbols:
        value = str(symbol).strip()
        if not value or value in output:
            continue
        if symbol_in_text(value, text):
            output.append(value)
    return output


def symbol_in_text(symbol: str, text: str) -> bool:
    escaped = re.escape(symbol)
    prefix = r"(?<![A-Za-z0-9_$])" if re.match(r"^[A-Za-z0-9_$]", symbol) else ""
    suffix = r"(?![A-Za-z0-9_$])" if re.search(r"[A-Za-z0-9_$]$", symbol) else ""
    flags = 0 if any(char.isupper() for char in symbol) else re.I
    return bool(re.search(prefix + escaped + suffix, text, flags))


def split_text_by_token_budget(text: str, max_tokens: int) -> list[str]:
    if token_count(text) <= max_tokens:
        return [text]
    remaining = text
    chunks: list[str] = []
    while remaining:
        segment_size = max(1, min(len(remaining), int(len(remaining) * max_tokens / max(token_count(remaining), 1))))
        segment = remaining[:segment_size]
        while token_count(segment) > max_tokens and segment_size > 1:
            segment_size = max(1, int(segment_size * 0.8))
            segment = remaining[:segment_size]
        chunks.append(segment)
        remaining = remaining[segment_size:]
    return chunks


def slugify(value: str) -> str:
    slug = re.sub(r"[^A-Za-z0-9]+", "-", value.lower()).strip("-")
    return slug or "page"


def scoped_chunk_key(source_path: str, key: str) -> str:
    return f"{source_path}#{key}"


def max_chunk_tokens() -> int:
    try:
        return max(200, min(1200, int(os.environ.get("OZ_MAX_CHUNK_TOKENS", "650"))))
    except ValueError:
        return 650
