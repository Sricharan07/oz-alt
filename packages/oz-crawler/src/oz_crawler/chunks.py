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
    seen_chunk_shas: set[str] = set()
    seen_content_keys: set[str] = set()
    for page in pages:
        source_path = source_path_for_page(page)
        chunks = chunk_markdown(page.markdown, source_url=page.source_url, page_type=page.content_type)
        for idx, chunk in enumerate(chunks, start=1):
            chunk_key = scoped_chunk_key(source_path, chunk.chunk_key or str(idx))
            parent_chunk_key = scoped_chunk_key(source_path, chunk.parent_key) if chunk.parent_key else None
            chunk_sha = stable_chunk_sha(target, source_path, idx, chunk.text)
            content_sha = content_hash(chunk.text)
            content_key = normalized_chunk_key(chunk.text)
            if chunk_sha in seen_chunk_shas or content_key in seen_content_keys:
                continue
            seen_chunk_shas.add(chunk_sha)
            seen_content_keys.add(content_key)
            rows.append(
                {
                    "id": chunk_key,
                    "path": source_path,
                    "source_url": page.source_url,
                    "source_anchor": source_anchor(page.source_url, chunk.heading_path, idx),
                    "ordinal": idx,
                    "chunk_key": chunk_key,
                    "parent_chunk_key": parent_chunk_key,
                    "chunk_sha": chunk_sha,
                    "content_sha": content_sha,
                    "start_line": chunk.start_line + 4,
                    "end_line": chunk.end_line + 4,
                    "heading_path": chunk.heading_path,
                    "symbols": chunk_symbols(chunk.text, page.symbols),
                    "content_type": chunk.content_type,
                    "quality_score": page.quality_score,
                    "token_count": token_count(chunk.text),
                    "text": chunk.text,
                }
            )
    (target / "_chunks.jsonl").write_text(
        "".join(json.dumps(row, sort_keys=True) + "\n" for row in rows),
        encoding="utf-8",
    )


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
        if section_type == "api_reference" and len(section) > 1:
            children = chunk_section(section, source_url=source_url, page_type=section_type, max_tokens=max_tokens, parent_key=None)
            if len(children) > 1:
                parent_key = f"section-{section_idx}-{slugify(' '.join(heading_path) or 'api')}"
                chunks.append(
                    MarkdownChunk(
                        text=limit_section_text(section_text, max_tokens),
                        heading_path=heading_path,
                        start_line=section[0][1],
                        end_line=section[-1][2],
                        content_type="api_reference",
                        chunk_key=parent_key,
                    )
                )
                children = [replace(child, parent_key=parent_key) for child in children]
            chunks.extend(children)
        else:
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
    heading_path: list[str] = []
    block_heading = list(heading_path)
    for line_number, line in enumerate(markdown.splitlines(), start=1):
        if line.startswith("```"):
            in_code = not in_code
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
        if current and (heading_boundary or indivisible or current_tokens + block_tokens > max_tokens):
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
    fence = re.match(r"^```([^\n]*)\n(?P<body>.*)\n```$", text.strip(), re.S)
    if not fence:
        return split_large_block(block, page_type=page_type, parent_key=parent_key, max_tokens=max_tokens)
    language = fence.group(1).strip()
    body_lines = fence.group("body").splitlines()
    chunks: list[MarkdownChunk] = []
    current: list[str] = []
    current_tokens = token_count(f"```{language}\n```")
    current_start = start_line + 1
    body_budget = max(1, max_tokens - token_count(f"```{language}\n```") - 8)
    for offset, line in enumerate(body_lines, start=1):
        for segment in split_text_by_token_budget(line, body_budget):
            line_tokens = token_count(segment)
            if current and current_tokens + line_tokens > max_tokens:
                chunks.append(
                    MarkdownChunk(
                        text=f"```{language}\n" + "\n".join(current).strip() + "\n```",
                        heading_path=list(heading_path),
                        start_line=current_start - 1,
                        end_line=start_line + offset,
                        content_type=page_type,
                        parent_key=parent_key,
                    )
                )
                current = []
                current_tokens = token_count(f"```{language}\n```")
                current_start = start_line + offset
            current.append(segment)
            current_tokens += line_tokens
    if current:
        chunks.append(
            MarkdownChunk(
                text=f"```{language}\n" + "\n".join(current).strip() + "\n```",
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
    return re.sub(r"\s+\{#[^}]+\}\s*$", "", match.group(2)).strip()


def update_heading_path(current: list[str], line: str, heading: str) -> list[str]:
    level = len(re.match(r"^(#{1,6})", line.strip()).group(1))  # type: ignore[union-attr]
    return [*current[: max(level - 1, 0)], heading]


def source_anchor(source_url: str, heading_path: list[str], ordinal: int) -> str:
    base, _ = urldefrag(source_url)
    heading_slug = slugify(heading_path[-1]) if heading_path else "page"
    return f"{base}#{heading_slug}-_snippet_{ordinal}"


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
    return "```" in text


def source_path_for_page(page: NormalizedPage) -> str:
    if page.path:
        return page.path
    if page.source_url.startswith("oz-artifact:"):
        return page.source_url.removeprefix("oz-artifact:")
    return f"guides/{slugify(page.title or page.source_url)}.md"


def stable_chunk_sha(target: Path, source_path: str, ordinal: int, text: str) -> str:
    vendor, library, version = target.parts[-3:]
    payload = "\0".join([vendor, library, version, source_path, str(ordinal), text])
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()


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
