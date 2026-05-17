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


@dataclass(frozen=True)
class NormalizedPage:
    title: str
    markdown: str
    source_url: str
    path: str | None = None
    content_type: str = "guide"
    quality_score: float = 1.0
    symbols: tuple[str, ...] = ()


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
    for raw_line in sanitize_secret_tokens(markdown).splitlines():
        line = raw_line.rstrip()
        blank = not line.strip()
        if blank and previous_blank:
            continue
        lines.append(line)
        previous_blank = blank
    return "\n".join(lines).strip() + "\n"


def sanitize_secret_tokens(text: str) -> str:
    sanitized = text
    for pattern, replacement in SECRET_TOKEN_PATTERNS:
        sanitized = pattern.sub(replacement, sanitized)
    return sanitized
