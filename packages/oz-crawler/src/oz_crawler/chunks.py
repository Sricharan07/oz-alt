from __future__ import annotations

import hashlib
import json
import os
import re
from dataclasses import dataclass, replace
from pathlib import Path
from typing import Any
from urllib.parse import urldefrag

from oz_crawler.content_types import block_content_type
from oz_crawler.normalize import NormalizedPage, clean_markdown
from oz_crawler.token_counting import token_count

FENCE_RE = re.compile(r"^\s*(`{3,}|~{3,})")
FULL_FENCE_RE = re.compile(r"^(`{3,}|~{3,})([^\n]*)\n(?P<body>.*)\n\1$", re.S)
MAX_HEADING_TEXT_CHARS = 160
MAX_SOURCE_ANCHOR_CHARS = 240


@dataclass(frozen=True)
class MarkdownChunk:
    text: str
    heading_path: list[str]
    start_line: int
    end_line: int
    content_type: str
    parent_key: str | None = None
    chunk_key: str | None = None


def write_chunks(target: Path, pages: list[NormalizedPage]) -> None:
    rows: list[dict[str, Any]] = []
    coverage_rows: list[dict[str, Any]] = []
    seen_chunk_shas: set[str] = set()
    seen_content_keys_by_path: dict[str, set[str]] = {}
    for page in pages:
        source_path = source_path_for_page(page)
        source_sections = chunk_source_sections(page, source_path)
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
                "source_kind": page.source_kind,
                "canonical_url": page.canonical_url or page.source_url,
                "source_document_key": source_document_key(page.canonical_url or page.source_url or page.path or page.title),
                "source_priority": page.source_priority,
                "discovered_from": page.discovered_from,
                "source_section_key": section_key,
                "metadata_json": metadata_json,
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


def chunk_source_sections(page: NormalizedPage, source_path: str) -> list[dict[str, Any]]:
    blocks = markdown_blocks(clean_markdown(page.markdown))
    sections: list[dict[str, Any]] = []
    for section in section_blocks(blocks):
        content = "\n\n".join(block[0] for block in section).strip()
        if not content:
            continue
        heading_path = next((block[3] for block in reversed(section) if block[3]), [])
        start_line = min(block[1] for block in section)
        end_line = max(block[2] for block in section)
        title = heading_path[-1] if heading_path else page.title or source_path.rsplit("/", 1)[-1]
        sections.append(
            {
                "section_key": stable_surface_key("section", source_path, str(start_line), title, content[:160]),
                "start_line": start_line,
                "end_line": end_line,
            }
        )
    return sections


def source_section_key_for_span(sections: list[dict[str, Any]], start_line: int, end_line: int) -> str:
    best_key = ""
    best_overlap = 0
    for section in sections:
        start = int(section.get("start_line") or 0)
        end = int(section.get("end_line") or 0)
        overlap = max(0, min(end, end_line) - max(start, start_line) + 1)
        if overlap > best_overlap:
            best_overlap = overlap
            best_key = str(section.get("section_key") or "")
    return best_key


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


def markdown_blocks(markdown: str) -> list[tuple[str, int, int, list[str]]]:
    output: list[tuple[str, int, int, list[str]]] = []
    current: list[str] = []
    start_line = 1
    in_code = False
    fence_marker = ""
    heading_path: list[str] = []
    block_heading = list(heading_path)
    for line_number, line in enumerate(markdown.splitlines(), start=1):
        marker = fence_marker_for_line(line)
        if marker:
            if not in_code:
                in_code = True
                fence_marker = marker[0]
            elif marker[0] == fence_marker:
                in_code = False
                fence_marker = ""
        if not in_code and not line.strip():
            if current:
                output.append(("\n".join(current).strip(), start_line, line_number - 1, block_heading))
                current = []
            continue
        if not current:
            start_line = line_number
            block_heading = list(heading_path)
        current.append(line)
        heading = heading_text(line)
        if heading is not None and not in_code:
            heading_path = update_heading_path(heading_path, line, heading)
            block_heading = list(heading_path)
    if current:
        output.append(("\n".join(current).strip(), start_line, start_line + len(current) - 1, block_heading))
    return output


def section_blocks(blocks: list[tuple[str, int, int, list[str]]]) -> list[list[tuple[str, int, int, list[str]]]]:
    sections: list[list[tuple[str, int, int, list[str]]]] = []
    current: list[tuple[str, int, int, list[str]]] = []
    for block in blocks:
        is_boundary = bool(re.match(r"^#{1,3}\s+", block[0].strip()))
        if current and is_boundary:
            sections.append(current)
            current = []
        current.append(block)
    if current:
        sections.append(current)
    return sections


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


def heading_text(line: str) -> str | None:
    match = re.match(r"^(#{1,6})\s+(.+)$", line.strip())
    if not match:
        return None
    heading = re.sub(r"\s+\{#[^}]+\}\s*$", "", match.group(2)).strip()
    return bounded_text(heading, MAX_HEADING_TEXT_CHARS)


def update_heading_path(current: list[str], line: str, heading: str) -> list[str]:
    level = len(re.match(r"^(#{1,6})", line.strip()).group(1))  # type: ignore[union-attr]
    return [*current[: max(level - 1, 0)], heading]


def source_anchor(source_url: str, heading_path: list[str], ordinal: int) -> str:
    base, _ = urldefrag(source_url)
    heading_slug = slugify(heading_path[-1]) if heading_path else "page"
    anchor = f"{shorten_anchor_base(base)}#{heading_slug}-_snippet_{ordinal}"
    if len(anchor) <= MAX_SOURCE_ANCHOR_CHARS:
        return anchor
    suffix = f"-_snippet_{ordinal}"
    available = max(16, MAX_SOURCE_ANCHOR_CHARS - len(shorten_anchor_base(base)) - len("#") - len(suffix))
    return f"{shorten_anchor_base(base)}#{heading_slug[:available].strip('-') or 'page'}{suffix}"


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


def bounded_text(value: str, max_chars: int) -> str:
    normalized = re.sub(r"\s+", " ", value).strip()
    if len(normalized) <= max_chars:
        return normalized
    digest = hashlib.sha256(normalized.encode("utf-8")).hexdigest()[:8]
    return normalized[: max_chars - 9].rstrip(" -") + "-" + digest


def shorten_anchor_base(base: str) -> str:
    if len(base) <= 150:
        return base
    digest = hashlib.sha256(base.encode("utf-8")).hexdigest()[:10]
    return base[:139].rstrip("/#?&=-") + "-" + digest


def source_path_for_page(page: NormalizedPage) -> str:
    if page.path:
        return page.path
    if page.source_url.startswith("oz-artifact:"):
        return page.source_url.removeprefix("oz-artifact:")
    return f"guides/{slugify(page.title or page.source_url)}.md"


def source_document_key(value: str) -> str:
    text = str(value or "").rstrip("/")
    if "#" in text and re.search(r"(?:^|/)(?:llms|llms-full)\.txt#|(?:openapi|swagger)\.(?:json|ya?ml)#", text.lower()):
        return text
    return text.split("#", 1)[0].rstrip("/")


def stable_chunk_sha(target: Path, source_path: str, ordinal: int, text: str) -> str:
    vendor, library, version = target.parts[-3:]
    payload = "\0".join([vendor, library, version, source_path, str(ordinal), text])
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()


def stable_surface_key(prefix: str, *parts: str) -> str:
    digest = hashlib.sha256("\0".join(str(part) for part in parts).encode("utf-8")).hexdigest()[:32]
    return f"{prefix}:{digest}"


def content_hash(text: str) -> str:
    normalized = re.sub(r"\s+", " ", text.strip())
    return hashlib.sha256(normalized.encode("utf-8")).hexdigest()


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
