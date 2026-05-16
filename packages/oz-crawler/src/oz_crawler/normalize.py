from __future__ import annotations

import re
from dataclasses import dataclass

try:
    from bs4 import BeautifulSoup
except ImportError:  # pragma: no cover - Lambda fallback when optional crawler deps are absent
    BeautifulSoup = None  # type: ignore

try:
    from markdownify import markdownify as md
except ImportError:  # pragma: no cover - Lambda fallback when optional crawler deps are absent
    md = None  # type: ignore


@dataclass(frozen=True)
class NormalizedPage:
    title: str
    markdown: str
    source_url: str


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
    for raw_line in markdown.splitlines():
        line = raw_line.rstrip()
        blank = not line.strip()
        if blank and previous_blank:
            continue
        lines.append(line)
        previous_blank = blank
    return "\n".join(lines).strip() + "\n"
