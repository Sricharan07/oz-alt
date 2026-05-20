from __future__ import annotations

import re
from dataclasses import dataclass

try:
    from bs4 import BeautifulSoup
except ImportError:  # pragma: no cover - optional parser dependency
    BeautifulSoup = None  # type: ignore

try:
    from markdownify import markdownify as md
except ImportError:  # pragma: no cover - optional Markdown dependency
    md = None  # type: ignore


SECRET_TOKEN_PATTERNS: tuple[tuple[re.Pattern[str], str], ...] = (
    (re.compile(r"sk_(test|live)_[A-Za-z0-9]{3,}"), r"sk_\1_REDACTED"),
    (re.compile(r"rk_(test|live)_[A-Za-z0-9]{3,}"), r"rk_\1_REDACTED"),
    (re.compile(r"pk_(test|live)_[A-Za-z0-9]{3,}"), r"pk_\1_REDACTED"),
    (re.compile(r"whsec_[A-Za-z0-9]{3,}"), "whsec_REDACTED"),
    (re.compile(r"sk-proj-[A-Za-z0-9_-]{12,}"), "sk-proj-REDACTED"),
    (re.compile(r"sk-[A-Za-z0-9_-]{20,}"), "sk-REDACTED"),
    (re.compile(r"\bAKIA[0-9A-Z]{16}\b"), "AKIA_REDACTED"),
    (re.compile(r"\bASIA[0-9A-Z]{16}\b"), "ASIA_REDACTED"),
    (re.compile(r"\bgh[pousr]_[A-Za-z0-9_]{20,}\b"), "gh_REDACTED"),
    (re.compile(r"\bnpm_[A-Za-z0-9]{20,}\b"), "npm_REDACTED"),
    (re.compile(r"\bxox[baprs]-[A-Za-z0-9-]{20,}\b"), "xox_REDACTED"),
    (re.compile(r"sk_(test|live)_REDACTED(?:\.\.\.[A-Za-z0-9]+)?(?:sk_(?:test|live)_REDACTED)?"), r"sk_\1_REDACTED"),
    (re.compile(r"rk_(test|live)_REDACTED(?:\.\.\.[A-Za-z0-9]+)?(?:rk_(?:test|live)_REDACTED)?"), r"rk_\1_REDACTED"),
    (re.compile(r"pk_(test|live)_REDACTED(?:\.\.\.[A-Za-z0-9]+)?(?:pk_(?:test|live)_REDACTED)?"), r"pk_\1_REDACTED"),
    (re.compile(r"sk_(test|live)_REDACTED(?:_(?:test|live)_REDACTED)+"), r"sk_\1_REDACTED"),
    (re.compile(r"rk_(test|live)_REDACTED(?:_(?:test|live)_REDACTED)+"), r"rk_\1_REDACTED"),
    (re.compile(r"pk_(test|live)_REDACTED(?:_(?:test|live)_REDACTED)+"), r"pk_\1_REDACTED"),
)

BOILERPLATE_LINE_PATTERNS: tuple[re.Pattern[str], ...] = (
    re.compile(r"^(?:edit this page|was this page helpful\??|on this page|skip to main content)$", re.I),
    re.compile(r"^(?:previous|next)(?:\s*/\s*(?:previous|next))?$", re.I),
    re.compile(r"^(?:view|edit) (?:on|in) github$", re.I),
    re.compile(r"^>?\s*for an index of all (?:available )?.*documentation, see .*/(?:llms|llms-full)\.txt", re.I),
    re.compile(r"^>?\s*for an index of all docs\b", re.I),
    re.compile(r"^>?\s*for a semantic overview of .*documentation, see .*/sitemap\.md", re.I),
    re.compile(r"^(?:toggle navigation|open navigation|close navigation)$", re.I),
    re.compile(r"^(?:copy page|copy code|copy link)$", re.I),
    re.compile(r"^(?:sponsors?|blog)$", re.I),
    re.compile(r"^(?:last updated|updated)\s*:?\s+.+$", re.I),
    re.compile(r"^</?(?:Intro|InlineToc|TableOfContents|Cards?|Card|Steps?|Tabs?|Tab|FileTree|PagesOnly|AppOnly|PagesRouter|AppRouter)\b[^>]*?/?>$", re.I),
)
FENCE_RE = re.compile(r"^\s*(`{3,}|~{3,})")


@dataclass(frozen=True)
class NormalizedPage:
    title: str
    markdown: str
    source_url: str
    path: str | None = None
    content_type: str = "prose"
    quality_score: float = 1.0
    symbols: tuple[str, ...] = ()
    source_kind: str = "website"
    canonical_url: str | None = None
    source_priority: int = 50
    discovered_from: str | None = None


def normalize_html(html: str, *, source_url: str, title: str | None = None) -> NormalizedPage:
    if BeautifulSoup is None or md is None:
        return normalize_html_fallback(html, source_url=source_url, title=title)

    soup = BeautifulSoup(html, "html.parser")

    for selector in ["script", "style", "noscript", "svg", "nav", "footer", "header"]:
        for element in soup.select(selector):
            element.decompose()

    page_title = title or read_title(soup) or source_url
    main = soup.find("main") or soup.find("article") or soup.body or soup
    markdown = md(str(main), heading_style="ATX", bullets="-")
    markdown = clean_markdown(markdown)

    return NormalizedPage(title=page_title, markdown=markdown, source_url=source_url)


def read_title(soup: BeautifulSoup) -> str:
    heading = soup.find("h1")
    if heading:
        return heading.get_text(" ", strip=True)
    if soup.title:
        return soup.title.get_text(" ", strip=True)
    return ""


def normalize_html_fallback(html: str, *, source_url: str, title: str | None = None) -> NormalizedPage:
    page_title = title or regex_title(html) or source_url
    body = re.sub(r"(?is)<(script|style|noscript|svg|nav|footer|header).*?</\1>", "", html)
    body = re.sub(r"(?i)<br\s*/?>", "\n", body)
    body = re.sub(r"(?i)</(p|div|section|article|li|h[1-6])>", "\n", body)
    body = re.sub(r"(?is)<[^>]+>", "", body)
    body = re.sub(r"&nbsp;", " ", body)
    body = re.sub(r"&amp;", "&", body)
    body = re.sub(r"&lt;", "<", body)
    body = re.sub(r"&gt;", ">", body)
    return NormalizedPage(title=page_title, markdown=clean_markdown(body), source_url=source_url)


def regex_title(html: str) -> str:
    for pattern in (r"(?is)<h1[^>]*>(.*?)</h1>", r"(?is)<title[^>]*>(.*?)</title>"):
        match = re.search(pattern, html)
        if match:
            return re.sub(r"(?is)<[^>]+>", "", match.group(1)).strip()
    return ""


def clean_markdown(markdown: str) -> str:
    lines: list[str] = []
    previous_blank = False
    in_code = False
    fence_marker = ""
    for raw_line in strip_frontmatter(sanitize_secret_tokens(markdown)).splitlines():
        line = raw_line.rstrip()
        stripped = line.strip()
        marker = fence_marker_for_line(line)
        if marker:
            if not in_code:
                in_code = True
                fence_marker = marker[0]
            elif marker[0] == fence_marker:
                in_code = False
                fence_marker = ""
        if not in_code and is_markdown_separator(stripped):
            continue
        if not in_code and is_boilerplate_line(stripped):
            continue
        blank = not line.strip()
        if blank and previous_blank:
            continue
        lines.append(line)
        previous_blank = blank
    return "\n".join(lines).strip() + "\n"


def fence_marker_for_line(line: str) -> str:
    match = FENCE_RE.match(line)
    return match.group(1) if match else ""


def strip_frontmatter(markdown: str) -> str:
    text = markdown.lstrip()
    for marker in ("---", "+++"):
        if not text.startswith(marker + "\n"):
            continue
        end = text.find("\n" + marker + "\n", len(marker) + 1)
        if end >= 0 and looks_like_frontmatter(text[len(marker) + 1 : end]):
            return text[end + len(marker) + 2 :]
    return markdown


def looks_like_frontmatter(payload: str) -> bool:
    lines = [line.strip() for line in payload.splitlines() if line.strip()]
    if not lines:
        return False
    if any(line.startswith(("#", "```")) for line in lines):
        return False
    return any(re.match(r"^[A-Za-z_][A-Za-z0-9_-]*\s*:", line) for line in lines)


def is_markdown_separator(stripped_line: str) -> bool:
    return bool(re.match(r"^(?:-{3,}|\*{3,}|_{3,})$", stripped_line))


def is_boilerplate_line(stripped_line: str) -> bool:
    if not stripped_line:
        return False
    normalized = re.sub(r"\s+", " ", stripped_line.strip(" -*_"))
    if re.match(r"^\[(?:edit this page|view on github|previous|next|copy)\]\([^)]*\)$", normalized, re.I):
        return True
    return any(pattern.search(normalized) for pattern in BOILERPLATE_LINE_PATTERNS)


def sanitize_secret_tokens(text: str) -> str:
    sanitized = text
    for pattern, replacement in SECRET_TOKEN_PATTERNS:
        sanitized = pattern.sub(replacement, sanitized)
    return sanitized
