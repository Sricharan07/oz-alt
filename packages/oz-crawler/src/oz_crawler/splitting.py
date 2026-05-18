from __future__ import annotations

import re
from dataclasses import replace
from typing import Iterable
from urllib.parse import urlparse

from oz_crawler.normalize import NormalizedPage
from oz_crawler.content_types import classify_content_type


FRONTMATTER_BLOCK = re.compile(r"(?ms)^---\s*\n(.*?)\n---\s*\n")


def split_llms_full(text: str, *, source_url: str) -> list[NormalizedPage]:
    matches = list(FRONTMATTER_BLOCK.finditer(text))
    if not matches:
        return [NormalizedPage(title=title_from_markdown(text, source_url), markdown=text.strip() + "\n", source_url=source_url)]

    pages: list[NormalizedPage] = []
    for index, match in enumerate(matches):
        body_start = match.end()
        body_end = matches[index + 1].start() if index + 1 < len(matches) else len(text)
        frontmatter = parse_frontmatter(match.group(1))
        body = text[body_start:body_end].strip()
        if not body:
            continue
        page_url = frontmatter.get("url") or source_url
        title = frontmatter.get("title") or title_from_markdown(body, page_url)
        markdown = body.strip() + "\n"
        pages.append(NormalizedPage(title=title, markdown=markdown, source_url=page_url))
    return pages


def parse_frontmatter(text: str) -> dict[str, str]:
    output: dict[str, str] = {}
    for line in text.splitlines():
        if ":" not in line:
            continue
        key, value = line.split(":", 1)
        output[key.strip()] = value.strip().strip("\"'")
    return output


def title_from_markdown(markdown: str, fallback: str) -> str:
    for line in markdown.splitlines():
        match = re.match(r"^#\s+(.+)$", line.strip())
        if match:
            return match.group(1).strip()
    return fallback


def assign_page_paths(pages: Iterable[NormalizedPage]) -> list[NormalizedPage]:
    output: list[NormalizedPage] = []
    seen: dict[str, int] = {}
    for page in pages:
        content_type = classify_content_type(page.source_url, page.markdown)
        path = document_path(page.source_url, page.title, content_type)
        count = seen.get(path, 0)
        seen[path] = count + 1
        if count:
            stem, suffix = path.rsplit(".", 1)
            path = f"{stem}-{count + 1}.{suffix}"
        output.append(replace(page, path=path, content_type=content_type))
    return output


def document_path(source_url: str, title: str, content_type: str) -> str:
    parsed = urlparse(source_url)
    url_path = parsed.path.strip("/")
    if source_url.startswith("oz-artifact:"):
        return source_url.removeprefix("oz-artifact:")

    prefix = {
        "api_reference": "api-reference",
        "types": "api-reference",
        "code_example": "examples",
        "example": "examples",
        "config": "guides",
        "cli": "guides",
        "error_ref": "guides",
        "prose": "guides",
        "index": "guides",
        "guide": "guides",
    }.get(content_type, "guides")

    if url_path:
        slug = slug_from_url_path(url_path)
    else:
        slug = slugify(title or parsed.netloc or "page")
    return f"{prefix}/{slug}.md"


def slug_from_url_path(path: str) -> str:
    parts = [part for part in path.split("/") if part and part not in {"docs", "reference"}]
    if not parts:
        return "index"
    return "/".join(slugify(part.removesuffix(".html").removesuffix(".md")) for part in parts)


def slugify(value: str) -> str:
    slug = re.sub(r"[^A-Za-z0-9._-]+", "-", value.lower()).strip("-._")
    return slug or "page"
