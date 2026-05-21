from __future__ import annotations

import hashlib
import re
from typing import Any
from urllib.parse import urldefrag

from oz_crawler.content_types import block_content_type
from oz_crawler.normalize import NormalizedPage, clean_markdown
from oz_crawler.token_counting import token_count

MarkdownBlock = tuple[str, int, int, list[str]]

FENCE_RE = re.compile(r"^\s*(`{3,}|~{3,})")
HEADING_RE = re.compile(r"^(#{1,6})\s+(.+)$")
ENDPOINT_RE = re.compile(
    r"(?im)(?:^|[`>\s])(?:GET|POST|PUT|PATCH|DELETE|HEAD|OPTIONS)\s+"
    r"(?:https?://[^\s`'\"<>)]+|/[A-Za-z0-9_./:{}?&=%+-]+)"
)
CURL_RE = re.compile(r"(?im)^\s*(?:\$?\s*)curl\s+")
SIGNATURE_RE = re.compile(
    r"(?m)(?:^|\s)(?:async\s+)?(?:def|function|class|interface|type|const|let|var)\s+"
    r"[A-Za-z_$][A-Za-z0-9_$]*\s*(?:\(|=|:|extends|implements)"
)
DOTTED_CALL_RE = re.compile(r"\b[A-Za-z_$][A-Za-z0-9_$]*\.[A-Za-z_$][A-Za-z0-9_$]*\s*\(")
MAX_HEADING_TEXT_CHARS = 160
MAX_SOURCE_ANCHOR_CHARS = 240


def source_sections_for_page(page: NormalizedPage) -> list[dict[str, Any]]:
    path = source_path_for_page(page)
    source_key = source_document_key(page.canonical_url or page.source_url or path)
    metadata = normalized_section_metadata(page)
    blocks = markdown_blocks(clean_markdown(page.markdown))
    output: list[dict[str, Any]] = []
    for index, section in enumerate(section_blocks(blocks), start=1):
        content = "\n\n".join(block[0] for block in section).strip()
        if not content:
            continue
        heading_path = next((block[3] for block in reversed(section) if block[3]), [])
        start_line = min(block[1] for block in section)
        end_line = max(block[2] for block in section)
        title = heading_path[-1] if heading_path else page.title or path.rsplit("/", 1)[-1]
        section_key = section_key_for(path, start_line, title, content)
        flags = section_shape_flags(content, title)
        output.append(
            {
                "section_key": section_key,
                "source_document_key": source_key,
                "path": path,
                "title": title,
                "heading_path": heading_path,
                "depth": len(heading_path),
                "source_url": page.source_url,
                "source_anchor": source_anchor(page.canonical_url or page.source_url, heading_path, index),
                "document_role": metadata["document_role"],
                "content_type": block_content_type(page.source_url, content, page.content_type),
                "product": metadata["product"],
                "product_confidence": metadata["product_confidence"],
                "language": metadata["language"],
                "start_line": start_line,
                "end_line": end_line,
                "content": content,
                "content_sha": content_hash(content),
                "has_code": flags["has_code"],
                "has_endpoint_shape": flags["has_endpoint_shape"],
                "has_signature_shape": flags["has_signature_shape"],
                "token_count": token_count(content),
                "quality_score": page.quality_score,
                "metadata_json": {
                    **metadata,
                    "content_sha": content_hash(content),
                    "has_code": flags["has_code"],
                    "has_endpoint_shape": flags["has_endpoint_shape"],
                    "has_signature_shape": flags["has_signature_shape"],
                },
            }
        )
    return output


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


def source_section_key_for_line(sections: list[dict[str, Any]], line_number: int) -> str:
    for section in sections:
        if int(section.get("start_line") or 0) <= line_number <= int(section.get("end_line") or 0):
            return str(section.get("section_key") or "")
    return ""


def markdown_blocks(markdown: str) -> list[MarkdownBlock]:
    output: list[MarkdownBlock] = []
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


def section_blocks(blocks: list[MarkdownBlock]) -> list[list[MarkdownBlock]]:
    sections: list[list[MarkdownBlock]] = []
    current: list[MarkdownBlock] = []
    for block in blocks:
        is_boundary = bool(re.match(r"^#{1,3}\s+", block[0].strip()))
        if current and is_boundary:
            sections.append(current)
            current = []
        current.append(block)
    if current:
        sections.append(current)
    return sections


def heading_text(line: str) -> str | None:
    match = HEADING_RE.match(line.strip())
    if not match:
        return None
    heading = re.sub(r"\s+\{#[^}]+\}\s*$", "", match.group(2)).strip()
    return bounded_text(heading, MAX_HEADING_TEXT_CHARS)


def update_heading_path(current: list[str], line: str, heading: str) -> list[str]:
    match = re.match(r"^(#{1,6})", line.strip())
    level = len(match.group(1)) if match else 1
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


def stable_surface_key(prefix: str, *parts: str) -> str:
    digest = hashlib.sha256("\0".join(str(part) for part in parts).encode("utf-8")).hexdigest()[:32]
    return f"{prefix}:{digest}"


def content_hash(text: str) -> str:
    normalized = re.sub(r"\s+", " ", text.strip())
    return hashlib.sha256(normalized.encode("utf-8")).hexdigest()


def section_key_for(path: str, start_line: int, title: str, content: str) -> str:
    return stable_surface_key("section", path, str(start_line), title, content[:160])


def section_shape_flags(content: str, title: str = "") -> dict[str, bool]:
    haystack = f"{title}\n{content}"
    return {
        "has_code": has_code_fence(content),
        "has_endpoint_shape": has_endpoint_shape(haystack),
        "has_signature_shape": has_signature_shape(haystack),
    }


def has_code_fence(text: str) -> bool:
    return bool(re.search(r"(?m)^\s*(?:`{3,}|~{3,})", text))


def has_endpoint_shape(text: str) -> bool:
    lowered = text.lower()
    if ENDPOINT_RE.search(text) or CURL_RE.search(text):
        return True
    return bool(("request" in lowered and "response" in lowered and re.search(r"\b(endpoint|parameter|status code|body)\b", lowered)))


def has_signature_shape(text: str) -> bool:
    if SIGNATURE_RE.search(text) or DOTTED_CALL_RE.search(text):
        return True
    return bool(re.search(r"(?m)^\s*(?:pub\s+)?(?:fn|func)\s+[A-Za-z_][\w]*\s*\(", text))


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


def slugify(value: str) -> str:
    slug = re.sub(r"[^A-Za-z0-9]+", "-", value.lower()).strip("-")
    return slug[:100] or "source"


def normalized_section_metadata(page: NormalizedPage) -> dict[str, Any]:
    metadata = dict(page.source_metadata or {})
    source_type = normalized_source_type(metadata.get("source_type") or page.source_type)
    metadata["source_type"] = source_type
    role = metadata.get("document_role") or infer_document_role(source_type, page.path or "", page.source_url, page.markdown)
    metadata["document_role"] = normalize_document_role(role)
    metadata.setdefault("product", "")
    try:
        metadata["product_confidence"] = float(metadata.get("product_confidence") or 0)
    except (TypeError, ValueError):
        metadata["product_confidence"] = 0.0
    metadata.setdefault("language", "")
    return metadata


def normalize_document_role(value: Any) -> str:
    raw = str(value or "").strip().lower().replace("-", "_")
    if raw == "cookbook":
        raw = "example"
    if raw == "api_spec":
        raw = "api_reference"
    if raw in {
        "readme",
        "guide",
        "api_reference",
        "example",
        "test",
        "sdk_source",
        "type_definition",
        "changelog",
        "troubleshooting",
        "config",
        "unknown",
    }:
        return raw
    return "unknown"


def infer_document_role(source_type: str, path: str, source_url: str, text: str) -> str:
    haystack = f"{path} {source_url}".lower()
    if source_type == "openapi" or "openapi" in haystack or "swagger" in haystack:
        return "api_reference"
    if re.search(r"(^|/)(readme|index)\.(md|mdx|txt)$", haystack) or haystack.rsplit("/", 1)[-1].startswith("readme"):
        return "readme"
    if re.search(r"(^|/)(examples?|samples?|cookbook|recipes?)(/|$)", haystack):
        return "example"
    if re.search(r"(^|/)(tests?|specs?)(/|$)|[_-](test|spec)\.", haystack):
        return "test"
    if re.search(r"(^|/)(api-reference|reference|api)(/|$)", haystack):
        return "api_reference"
    if path.endswith((".d.ts", ".pyi")) or "type definitions" in text[:1000].lower():
        return "type_definition"
    if re.search(r"(^|/)(src|lib|packages|pkg)(/|$)", haystack) and path.endswith((".py", ".ts", ".tsx", ".js", ".jsx", ".go", ".rs")):
        return "sdk_source"
    if "changelog" in haystack or "release" in haystack:
        return "changelog"
    if any(term in haystack for term in ("troubleshooting", "errors", "error-codes")):
        return "troubleshooting"
    if re.search(r"(\.env|config|configuration|package\.json|tsconfig|docker-compose)", haystack):
        return "config"
    if re.search(r"(^|/)(docs?|guides?|learn)(/|$)", haystack):
        return "guide"
    return "unknown"


def normalized_source_type(value: Any) -> str:
    raw = str(value or "").strip().lower().replace("-", "_")
    if raw in {"github", "website_url", "llms_txt", "openapi"}:
        return raw
    return "website_url"
