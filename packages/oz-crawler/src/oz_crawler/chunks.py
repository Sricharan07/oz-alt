from __future__ import annotations

import hashlib
import json
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from oz_crawler.embeddings import row_with_embedding
from oz_crawler.normalize import NormalizedPage


@dataclass(frozen=True)
class MarkdownChunk:
    text: str
    heading_path: list[str]
    start_line: int
    end_line: int


def write_chunks(target: Path, pages: list[NormalizedPage]) -> None:
    rows: list[dict[str, Any]] = []
    seen_chunk_shas: set[str] = set()
    for page in pages:
        source_path = source_path_for_page(page)
        for idx, chunk in enumerate(chunk_markdown(page.markdown), start=1):
            chunk_sha = stable_chunk_sha(target, source_path, idx, chunk.text)
            if chunk_sha in seen_chunk_shas:
                continue
            seen_chunk_shas.add(chunk_sha)
            row = row_with_embedding(
                {
                    "id": f"{source_path}#{idx}",
                    "path": source_path,
                    "source_url": page.source_url,
                    "ordinal": idx,
                    "start_line": chunk.start_line + 4,
                    "end_line": chunk.end_line + 4,
                    "heading_path": chunk.heading_path,
                    "symbols": list(page.symbols),
                    "content_type": page.content_type,
                    "quality_score": page.quality_score,
                    "text": chunk.text,
                },
                chunk.text,
            )
            row["chunk_sha"] = chunk_sha
            rows.append(row)
    (target / "_chunks.jsonl").write_text(
        "".join(json.dumps(row, sort_keys=True) + "\n" for row in rows),
        encoding="utf-8",
    )


def chunk_markdown(markdown: str, *, max_tokens: int = 1000) -> list[MarkdownChunk]:
    chunks: list[MarkdownChunk] = []
    current: list[tuple[str, int, int, list[str]]] = []
    current_tokens = 0
    current_heading: list[str] = []
    for block, start_line, end_line in markdown_blocks(markdown):
        heading = heading_text(block)
        if heading is not None:
            current_heading = update_heading_path(current_heading, block, heading)
        block_tokens = token_count(block)
        heading_boundary = heading is not None and re.match(r"^#{2,3}\s+", block)
        if current and (heading_boundary or current_tokens + block_tokens > max_tokens):
            chunks.append(join_chunk(current))
            current = []
            current_tokens = 0
        if block_tokens > max_tokens:
            chunks.extend(split_large_block(block, heading_path=current_heading, start_line=start_line, max_tokens=max_tokens))
            continue
        current.append((block, start_line, end_line, list(current_heading)))
        current_tokens += block_tokens
    if current:
        chunks.append(join_chunk(current))
    return [chunk for chunk in chunks if chunk.text]


def markdown_blocks(markdown: str) -> list[tuple[str, int, int]]:
    blocks: list[tuple[str, int, int]] = []
    current: list[str] = []
    start_line = 1
    in_code = False
    for line_number, line in enumerate(markdown.splitlines(), start=1):
        if line.startswith("```"):
            in_code = not in_code
        if not in_code and not line.strip():
            if current:
                blocks.append(("\n".join(current).strip(), start_line, line_number - 1))
                current = []
            continue
        if not current:
            start_line = line_number
        current.append(line)
    if current:
        blocks.append(("\n".join(current).strip(), start_line, start_line + len(current) - 1))
    return blocks


def split_large_block(
    block: str,
    *,
    heading_path: list[str],
    start_line: int,
    max_tokens: int,
) -> list[MarkdownChunk]:
    chunks: list[MarkdownChunk] = []
    current: list[str] = []
    current_tokens = 0
    current_start = start_line
    for offset, line in enumerate(block.splitlines()):
        line_tokens = token_count(line)
        if current and current_tokens + line_tokens > max_tokens:
            chunks.append(
                MarkdownChunk(
                    text="\n".join(current).strip(),
                    heading_path=list(heading_path),
                    start_line=current_start,
                    end_line=start_line + offset - 1,
                )
            )
            current = []
            current_tokens = 0
            current_start = start_line + offset
        current.append(line)
        current_tokens += line_tokens
    if current:
        chunks.append(
            MarkdownChunk(
                text="\n".join(current).strip(),
                heading_path=list(heading_path),
                start_line=current_start,
                end_line=current_start + len(current) - 1,
            )
        )
    return chunks


def join_chunk(blocks: list[tuple[str, int, int, list[str]]]) -> MarkdownChunk:
    text = "\n\n".join(block[0] for block in blocks).strip()
    heading_path = next((block[3] for block in reversed(blocks) if block[3]), [])
    return MarkdownChunk(text=text, heading_path=list(heading_path), start_line=blocks[0][1], end_line=blocks[-1][2])


def heading_text(block: str) -> str | None:
    match = re.match(r"^(#{1,6})\s+(.+)$", block.strip())
    if not match:
        return None
    return re.sub(r"\s+\{#[^}]+\}\s*$", "", match.group(2)).strip()


def update_heading_path(current: list[str], block: str, heading: str) -> list[str]:
    level = len(re.match(r"^(#{1,6})", block.strip()).group(1))  # type: ignore[union-attr]
    base = current[: max(level - 1, 0)]
    base.append(heading)
    return base


def token_count(text: str) -> int:
    return max(1, len(re.findall(r"\w+|[^\w\s]", text)))


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


def slugify(value: str) -> str:
    slug = re.sub(r"[^A-Za-z0-9]+", "-", value.lower()).strip("-")
    return slug or "page"
