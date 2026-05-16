from __future__ import annotations

import hashlib
import json
import re
from pathlib import Path
from typing import Any

from oz_crawler.embeddings import row_with_embedding
from oz_crawler.normalize import NormalizedPage


def write_chunks(target: Path, pages: list[NormalizedPage]) -> None:
    rows: list[dict[str, Any]] = []
    seen_chunk_shas: set[str] = set()
    for page in pages:
        source_path = source_path_for_page(page)
        for idx, chunk in enumerate(chunk_markdown(page.markdown), start=1):
            chunk_sha = stable_chunk_sha(target, source_path, idx, chunk)
            if chunk_sha in seen_chunk_shas:
                continue
            seen_chunk_shas.add(chunk_sha)
            row = row_with_embedding(
                {
                    "id": f"{source_path}#{idx}",
                    "path": source_path,
                    "source_url": page.source_url,
                    "ordinal": idx,
                    "text": chunk,
                },
                chunk,
            )
            row["chunk_sha"] = chunk_sha
            rows.append(row)
    (target / "_chunks.jsonl").write_text(
        "".join(json.dumps(row, sort_keys=True) + "\n" for row in rows),
        encoding="utf-8",
    )


def chunk_markdown(markdown: str, *, max_tokens: int = 1000) -> list[str]:
    chunks: list[str] = []
    current: list[str] = []
    current_tokens = 0
    for block in markdown_blocks(markdown):
        block_tokens = token_count(block)
        heading_boundary = re.match(r"^#{2,3}\s+", block)
        if current and (heading_boundary or current_tokens + block_tokens > max_tokens):
            chunks.append("\n\n".join(current).strip())
            current = []
            current_tokens = 0
        if block_tokens > max_tokens:
            chunks.extend(split_large_block(block, max_tokens=max_tokens))
            continue
        current.append(block)
        current_tokens += block_tokens
    if current:
        chunks.append("\n\n".join(current).strip())
    return [chunk for chunk in chunks if chunk]


def markdown_blocks(markdown: str) -> list[str]:
    blocks: list[str] = []
    current: list[str] = []
    in_code = False
    for line in markdown.splitlines():
        if line.startswith("```"):
            in_code = not in_code
        if not in_code and not line.strip():
            if current:
                blocks.append("\n".join(current).strip())
                current = []
            continue
        current.append(line)
    if current:
        blocks.append("\n".join(current).strip())
    return blocks


def split_large_block(block: str, *, max_tokens: int) -> list[str]:
    chunks: list[str] = []
    current: list[str] = []
    current_tokens = 0
    for line in block.splitlines():
        line_tokens = token_count(line)
        if current and current_tokens + line_tokens > max_tokens:
            chunks.append("\n".join(current).strip())
            current = []
            current_tokens = 0
        current.append(line)
        current_tokens += line_tokens
    if current:
        chunks.append("\n".join(current).strip())
    return chunks


def token_count(text: str) -> int:
    return max(1, len(re.findall(r"\w+|[^\w\s]", text)))


def source_path_for_page(page: NormalizedPage) -> str:
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
