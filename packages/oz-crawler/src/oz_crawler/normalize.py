from __future__ import annotations

from dataclasses import dataclass

from bs4 import BeautifulSoup
from markdownify import markdownify as md


@dataclass(frozen=True)
class NormalizedPage:
    title: str
    markdown: str
    source_url: str


def normalize_html(html: str, *, source_url: str, title: str | None = None) -> NormalizedPage:
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

