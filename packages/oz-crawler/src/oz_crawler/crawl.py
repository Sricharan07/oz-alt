from __future__ import annotations

import json
import re
import shutil
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any
from urllib.request import Request, urlopen
from urllib.parse import urljoin, urlparse
from xml.etree import ElementTree

from oz_crawler.embeddings import row_with_embedding
from oz_crawler.normalize import NormalizedPage, normalize_html

try:
    from bs4 import BeautifulSoup
except ImportError:  # pragma: no cover - Lambda fallback when optional crawler deps are absent
    BeautifulSoup = None  # type: ignore


@dataclass(frozen=True)
class CrawlResult:
    target: Path
    page: NormalizedPage


def crawl_single_page(
    *,
    url: str,
    registry_root: Path,
    vendor: str,
    library: str,
    version: str,
    title: str | None = None,
    max_pages: int = 1,
) -> Path:
    pages = crawl_pages(url, title=title, max_pages=max_pages)
    if not pages:
        raise RuntimeError(f"no pages crawled from {url}")

    target = registry_root / vendor / library / version
    if target.exists():
        shutil.rmtree(target)
    (target / "_symbols").mkdir(parents=True, exist_ok=True)
    (target / "guides").mkdir(parents=True, exist_ok=True)
    (target / "api-reference").mkdir(parents=True, exist_ok=True)
    (target / "examples").mkdir(parents=True, exist_ok=True)

    page_title = title or pages[0].title or f"{library} {version}"
    (target / "README.md").write_text(
        f"# {page_title}\n\nDocumentation crawled from {url}.\n",
        encoding="utf-8",
    )
    (target / "api-reference" / "README.md").write_text(
        f"# {page_title} API Reference\n\nAPI reference entries extracted from {url}.\n",
        encoding="utf-8",
    )
    (target / "examples" / "README.md").write_text(
        f"# {page_title} Examples\n\nRunnable examples extracted from {url}.\n",
        encoding="utf-8",
    )
    guide_links: list[tuple[str, str]] = []
    for page in pages:
        slug = slugify(page.title or page.source_url)
        relative = f"guides/{slug}.md"
        guide_links.append((relative, page.title or page.source_url))
        (target / relative).write_text(
            f"# {page.title}\n\n**Source:** {page.source_url}\n\n{page.markdown}",
            encoding="utf-8",
        )
    write_chunks(target, pages)
    write_symbols(target, pages)
    (target / "INDEX.md").write_text(
        build_index(title=page_title, source_url=url, guide_links=guide_links),
        encoding="utf-8",
    )
    (target / "_meta.json").write_text(
        json.dumps(
            {
                "vendor": vendor,
                "library": library,
                "version": version,
                "source_urls": [url],
                "indexed_at": datetime.now(timezone.utc).isoformat(),
                "ref_sha": "local-crawl",
            },
            indent=2,
            sort_keys=True,
        )
        + "\n",
        encoding="utf-8",
    )

    return target


def crawl_pages(url: str, *, title: str | None, max_pages: int) -> list[NormalizedPage]:
    first_html = fetch_html(url)
    first_page = normalize_html(first_html, source_url=url, title=title)
    pages = [first_page]
    if max_pages <= 1:
        return pages

    discovered = discover_declared_doc_links(url)
    discovered.extend(discover_same_site_links(url, first_html))
    seen = {url}
    for linked_url in dedupe(discovered):
        if len(pages) >= max_pages:
            break
        if linked_url in seen:
            continue
        seen.add(linked_url)
        try:
            html = fetch_html(linked_url)
        except Exception:
            continue
        pages.append(normalize_html(html, source_url=linked_url))
    return pages


def fetch_html(url: str) -> str:
    try:
        from scrapling.fetchers import Fetcher
    except ImportError:
        req = Request(url, headers={"User-Agent": "oz-crawler/0.1"})
        with urlopen(req, timeout=20) as response:
            return response.read().decode("utf-8", errors="replace")

    page = Fetcher.get(url)
    html = extract_html(page)
    if not html.strip():
        raise RuntimeError(f"Scrapling fetched {url}, but no HTML content was found on the response object")
    return html


def fetch_text_optional(url: str) -> str | None:
    try:
        return fetch_html(url)
    except Exception:
        return None


def extract_html(page: Any) -> str:
    for attr in ("html", "content", "body", "text"):
        value = getattr(page, attr, None)
        if callable(value):
            value = value()
        if isinstance(value, bytes):
            return value.decode("utf-8", errors="replace")
        if isinstance(value, str) and value.strip():
            return value
    return str(page)


def discover_same_site_links(url: str, html: str) -> list[str]:
    parsed = urlparse(url)
    if BeautifulSoup is None:
        return discover_same_site_links_fallback(url, html)
    soup = BeautifulSoup(html, "html.parser")
    seen: set[str] = set()
    output: list[str] = []
    for anchor in soup.select("a[href]"):
        href = anchor.get("href")
        if not href:
            continue
        absolute = urljoin(url, href).split("#", 1)[0]
        parsed_absolute = urlparse(absolute)
        if parsed_absolute.netloc != parsed.netloc:
            continue
        if absolute in seen or absolute == url:
            continue
        seen.add(absolute)
        output.append(absolute)
    return output


def discover_same_site_links_fallback(url: str, html: str) -> list[str]:
    parsed = urlparse(url)
    seen: set[str] = set()
    output: list[str] = []
    for href in re.findall(r"(?i)<a[^>]+href=['\"]([^'\"]+)['\"]", html):
        absolute = urljoin(url, href).split("#", 1)[0]
        parsed_absolute = urlparse(absolute)
        if parsed_absolute.netloc != parsed.netloc:
            continue
        if absolute in seen or absolute == url:
            continue
        seen.add(absolute)
        output.append(absolute)
    return output


def discover_declared_doc_links(url: str) -> list[str]:
    parsed = urlparse(url)
    base = f"{parsed.scheme}://{parsed.netloc}"
    links: list[str] = []

    for name in ("/llms-full.txt", "/llms.txt"):
        text = fetch_text_optional(base + name)
        if text:
            links.extend(extract_urls(text, base_url=base))

    sitemap = fetch_text_optional(base + "/sitemap.xml")
    if sitemap:
        links.extend(extract_sitemap_urls(sitemap))

    return [link for link in links if same_netloc(link, parsed.netloc)]


def same_netloc(url: str, netloc: str) -> bool:
    try:
        return urlparse(url).netloc == netloc
    except ValueError:
        return False


def extract_urls(text: str, *, base_url: str) -> list[str]:
    urls = re.findall(r"https?://[^\s)>\"]+", text)
    markdown_links = re.findall(r"\[[^\]]+\]\(([^)]+)\)", text)
    for link in markdown_links:
        urls.append(urljoin(base_url, link))
    return urls


def extract_sitemap_urls(xml: str) -> list[str]:
    try:
        root = ElementTree.fromstring(xml)
    except ElementTree.ParseError:
        return []
    urls: list[str] = []
    for element in root.iter():
        if element.tag.endswith("loc") and element.text:
            urls.append(element.text.strip())
    return urls


def dedupe(values: list[str]) -> list[str]:
    seen: set[str] = set()
    output: list[str] = []
    for value in values:
        value = value.split("#", 1)[0]
        if value in seen:
            continue
        seen.add(value)
        output.append(value)
    return output


def build_index(*, title: str, source_url: str, guide_links: list[tuple[str, str]]) -> str:
    lines = [
        f"# {title} Documentation Index",
        "",
        f"- [README](README.md) - normalized documentation fetched from {source_url}.",
    ]
    for relative, page_title in guide_links:
        lines.append(f"- [{page_title}]({relative}) - crawled guide page.")
    lines.extend(
        [
            "- [Symbols](_symbols/) - extracted public API entries from code examples.",
            "",
        ]
    )
    return "\n".join(lines)


def write_symbols(target: Path, pages: list[NormalizedPage]) -> None:
    symbols = extract_symbols(pages)
    for symbol, payload in symbols.items():
        (target / "_symbols" / f"{symbol}.md").write_text(payload, encoding="utf-8")


def write_chunks(target: Path, pages: list[NormalizedPage]) -> None:
    rows: list[dict[str, Any]] = []
    for page in pages:
        slug = slugify(page.title or page.source_url)
        source_path = f"guides/{slug}.md"
        for idx, chunk in enumerate(chunk_markdown(page.markdown), start=1):
            rows.append(
                row_with_embedding(
                    {
                        "id": f"{source_path}#{idx}",
                        "path": source_path,
                        "source_url": page.source_url,
                        "ordinal": idx,
                        "text": chunk,
                    },
                    chunk,
                )
            )
    (target / "_chunks.jsonl").write_text(
        "".join(json.dumps(row, sort_keys=True) + "\n" for row in rows),
        encoding="utf-8",
    )


def chunk_markdown(markdown: str, *, max_chars: int = 4000) -> list[str]:
    chunks: list[str] = []
    current: list[str] = []
    current_size = 0
    for line in markdown.splitlines():
        starts_heading = line.startswith("## ")
        if starts_heading and current:
            chunks.append("\n".join(current).strip())
            current = []
            current_size = 0
        current.append(line)
        current_size += len(line) + 1
        if current_size >= max_chars:
            chunks.append("\n".join(current).strip())
            current = []
            current_size = 0
    if current:
        chunks.append("\n".join(current).strip())
    return [chunk for chunk in chunks if chunk]


def extract_symbols(pages: list[NormalizedPage]) -> dict[str, str]:
    output: dict[str, str] = {}
    for page in pages:
        for language, code in code_blocks(page.markdown):
            for kind, symbol in find_symbols(code):
                output.setdefault(
                    symbol,
                    "\n".join(
                        [
                            f"# {symbol}",
                            "",
                            f"**Kind:** {kind}",
                            f"**Signature:** `{first_line(code)}`",
                            f"**Source:** {page.source_url}",
                            "",
                            "## Example",
                            "",
                            f"```{language or 'text'}",
                            code.strip(),
                            "```",
                            "",
                        ]
                    ),
                )
    return output


def code_blocks(markdown: str) -> list[tuple[str, str]]:
    pattern = re.compile(r"```([A-Za-z0-9_-]*)\n(.*?)```", re.DOTALL)
    return [(match.group(1), match.group(2)) for match in pattern.finditer(markdown)]


def find_symbols(code: str) -> list[tuple[str, str]]:
    patterns = [
        ("function", r"export\s+(?:async\s+)?function\s+([A-Za-z_$][\w$]*)"),
        ("class", r"(?:export\s+)?class\s+([A-Z][A-Za-z0-9_$]*)"),
        ("type", r"(?:export\s+)?(?:interface|type)\s+([A-Z][A-Za-z0-9_$]*)"),
        ("constant", r"export\s+const\s+([A-Za-z_$][\w$]*)"),
    ]
    symbols: list[tuple[str, str]] = []
    for kind, pattern in patterns:
        for match in re.finditer(pattern, code):
            symbol = match.group(1)
            if symbol.lower() not in SYMBOL_STOP_WORDS:
                symbols.append((kind, symbol))
    return symbols


SYMBOL_STOP_WORDS = {
    "and",
    "as",
    "for",
    "from",
    "in",
    "is",
    "of",
    "or",
    "that",
    "the",
    "to",
    "with",
}


def first_line(code: str) -> str:
    for line in code.splitlines():
        if line.strip():
            return line.strip()
    return ""


def slugify(value: str) -> str:
    slug = re.sub(r"[^A-Za-z0-9]+", "-", value.lower()).strip("-")
    return slug or "page"
