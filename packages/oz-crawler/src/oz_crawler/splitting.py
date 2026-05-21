from __future__ import annotations

import re
from dataclasses import replace
from typing import Iterable
from urllib.parse import urlparse

from oz_crawler.normalize import NormalizedPage, clean_markdown
from oz_crawler.content_types import classify_content_type


FENCE_RE = re.compile(r"^\s*(`{3,}|~{3,})")


def split_llms_full(text: str, *, source_url: str) -> list[NormalizedPage]:
    boundaries = llms_frontmatter_boundaries(text)
    if not boundaries:
        markdown = clean_markdown(text)
        heading_pages = split_llms_full_heading_pages(markdown, source_url=source_url)
        if heading_pages:
            return heading_pages
        return [
            NormalizedPage(
                title=title_from_markdown(markdown, source_url),
                markdown=markdown,
                source_url=source_url,
                canonical_url=source_url,
                source_kind="llms_txt",
                source_priority=20,
            )
        ]

    pages: list[NormalizedPage] = []
    for index, (start, end, frontmatter) in enumerate(boundaries):
        body_start = end
        body_end = boundaries[index + 1][0] if index + 1 < len(boundaries) else len(text)
        body = clean_markdown(text[body_start:body_end])
        if not body:
            continue
        page_url = frontmatter.get("url") or source_url
        title = frontmatter.get("title") or title_from_markdown(body, page_url)
        pages.append(
            NormalizedPage(
                title=title,
                markdown=body,
                source_url=page_url,
                canonical_url=page_url,
                source_kind="llms_txt",
                source_priority=20,
                discovered_from=source_url,
            )
        )
    return pages


def split_llms_full_heading_pages(markdown: str, *, source_url: str) -> list[NormalizedPage]:
    """Split concatenated llms-full content that lacks per-page frontmatter.

    Several generators publish llms-full.txt as one long Markdown document with
    repeated H1 page titles and no YAML boundaries. Treating that as one source
    document destroys anchors and document-level metadata, so we use H1 headings
    as a generic fallback while respecting code fences.
    """

    starts = h1_heading_line_indexes(markdown)
    if len(starts) < 2:
        return []

    lines = markdown.splitlines(keepends=True)
    preamble = lines[: starts[0]]
    seen_fragments: dict[str, int] = {}
    pages: list[NormalizedPage] = []
    for index, start in enumerate(starts):
        end = starts[index + 1] if index + 1 < len(starts) else len(lines)
        segment_lines = (preamble if index == 0 else []) + lines[start:end]
        body = clean_markdown("".join(segment_lines))
        if not body:
            continue
        title = title_from_markdown(body, source_url)
        fragment = unique_fragment(title, seen_fragments)
        page_url = f"{source_url}#{fragment}"
        pages.append(
            NormalizedPage(
                title=title,
                markdown=body,
                source_url=page_url,
                canonical_url=page_url,
                source_kind="llms_txt",
                source_priority=20,
                discovered_from=source_url,
            )
        )
    return pages if len(pages) > 1 else []


def h1_heading_line_indexes(markdown: str) -> list[int]:
    starts: list[int] = []
    in_fence = False
    fence_marker = ""
    for line_number, line in enumerate(markdown.splitlines(keepends=True)):
        marker = fence_marker_for_line(line)
        if marker:
            if not in_fence:
                in_fence = True
                fence_marker = marker[0]
            elif marker[0] == fence_marker:
                in_fence = False
                fence_marker = ""
        if in_fence:
            continue
        if re.match(r"^#\s+\S", line.strip()):
            starts.append(line_number)
    return starts


def unique_fragment(title: str, seen: dict[str, int]) -> str:
    base = slugify(title)
    count = seen.get(base, 0) + 1
    seen[base] = count
    return base if count == 1 else f"{base}-{count}"


def llms_frontmatter_boundaries(text: str) -> list[tuple[int, int, dict[str, str]]]:
    offsets = line_offsets(text)
    lines = text.splitlines(keepends=True)
    boundaries: list[tuple[int, int, dict[str, str]]] = []
    in_fence = False
    fence_marker = ""
    index = 0
    while index < len(lines):
        stripped = lines[index].strip()
        marker = fence_marker_for_line(lines[index])
        if marker:
            if not in_fence:
                in_fence = True
                fence_marker = marker[0]
            elif marker[0] == fence_marker:
                in_fence = False
                fence_marker = ""
        if in_fence or stripped != "---":
            index += 1
            continue
        close = index + 1
        payload_lines: list[str] = []
        while close < len(lines):
            if lines[close].strip() == "---":
                payload = "".join(payload_lines)
                frontmatter = parse_frontmatter(payload)
                if looks_like_llms_page_frontmatter(frontmatter):
                    boundaries.append((offsets[index], offsets[close] + len(lines[close]), frontmatter))
                    index = close
                    break
                break
            payload_lines.append(lines[close])
            close += 1
        index += 1
    return boundaries


def line_offsets(text: str) -> list[int]:
    offsets: list[int] = []
    offset = 0
    for line in text.splitlines(keepends=True):
        offsets.append(offset)
        offset += len(line)
    return offsets


def fence_marker_for_line(line: str) -> str:
    match = FENCE_RE.match(line)
    return match.group(1) if match else ""


def looks_like_llms_page_frontmatter(frontmatter: dict[str, str]) -> bool:
    if not frontmatter:
        return False
    keys = {key.lower() for key in frontmatter}
    return bool(keys & {"url", "title", "source", "path"})


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
        path = page.path or document_path(page.canonical_url or page.source_url, page.title, content_type)
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

    prefix = path_prefix_from_url(parsed.path, content_type)

    if parsed.fragment and re.search(r"(?:^|/)(?:llms|llms-full)\.txt$", parsed.path.lower()):
        slug = slugify(parsed.fragment)
    elif url_path:
        slug = slug_from_url_path(url_path)
    else:
        slug = slugify(title or parsed.netloc or "page")
    return f"{prefix}/{slug}.md"


def slug_from_url_path(path: str) -> str:
    parts = [part for part in path.split("/") if part and part not in {"docs", "reference"}]
    if not parts:
        return "index"
    return "/".join(slugify(part.removesuffix(".html").removesuffix(".md")) for part in parts)


def path_prefix_from_url(path: str, content_type: str) -> str:
    lower = path.lower()
    if re.search(r"(?:^|/)(?:api-reference|reference|api)(?:/|$)", lower):
        return "api-reference"
    if re.search(r"(?:^|/)(?:examples?|sample|tutorials?)(?:/|$)", lower):
        return "examples"
    if content_type in {"api_reference", "types"}:
        return "api-reference"
    if content_type in {"code_example", "example"} and not lower:
        return "examples"
    return "guides"


def slugify(value: str) -> str:
    slug = re.sub(r"[^A-Za-z0-9._-]+", "-", value.lower()).strip("-._")
    return slug or "page"
