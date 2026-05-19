from __future__ import annotations

import hashlib
import json
import logging
import os
import re
import shutil
import sys
from dataclasses import dataclass, replace
from datetime import datetime, timezone
from pathlib import Path
from typing import Any
from urllib.parse import urljoin, urlparse
from xml.etree import ElementTree

from oz_crawler.chunks import write_chunks
from oz_crawler.crawl_runtime import CrawlRunState, ProgressCallback, max_page_bytes, retry_attempts
from oz_crawler.language import language_allowed
from oz_crawler.normalize import NormalizedPage, clean_markdown, normalize_html, sanitize_secret_tokens
from oz_crawler.profiles import LibraryProfile, load_profile, url_allowed_by_profile
from oz_crawler.quality import QualityResult, score_page
from oz_crawler.security import CrawlerFetchError, assert_public_http_url, fetch_public_url, pinned_fetch_required
from oz_crawler.splitting import assign_page_paths
from oz_crawler.sources import SourceArtifact, collect_source_artifacts
from oz_crawler.symbols import extract_page_symbol_names, write_symbols
from oz_crawler.text import decode_text_response, is_probably_binary_text, is_textual_url_candidate
from oz_crawler.validation import validate_fixture, write_validation
from oz_crawler.versioning import filter_current_version

LOGGER = logging.getLogger(__name__)

try:
    from bs4 import BeautifulSoup
except ImportError:  # pragma: no cover - optional parser dependency
    BeautifulSoup = None  # type: ignore


@dataclass(frozen=True)
class CrawlResult:
    target: Path
    page: NormalizedPage


@dataclass(frozen=True)
class CrawlOptions:
    max_pages: int = 1
    fetcher: str = "auto"
    concurrent_requests: int = 6
    download_delay: float = 0.0
    robots_txt: bool = True
    crawldir: Path | None = None
    headless: bool = True
    network_idle: bool = True
    require_profile: bool = False
    fail_on_validation: bool = False
    progress_callback: ProgressCallback | None = None

    @classmethod
    def from_env(cls, *, max_pages: int) -> "CrawlOptions":
        return cls(
            max_pages=max_pages,
            fetcher=os.environ.get("OZ_CRAWLER_FETCHER", "auto"),
            concurrent_requests=int(os.environ.get("OZ_CRAWLER_CONCURRENCY", "6")),
            download_delay=float(os.environ.get("OZ_CRAWLER_DELAY", "0")),
            robots_txt=os.environ.get("OZ_CRAWLER_ROBOTS", "1").lower() not in {"0", "false", "no"},
            crawldir=Path(os.environ["OZ_CRAWLER_CRAWLDIR"]) if os.environ.get("OZ_CRAWLER_CRAWLDIR") else None,
            headless=os.environ.get("OZ_CRAWLER_HEADLESS", "1").lower() not in {"0", "false", "no"},
            network_idle=os.environ.get("OZ_CRAWLER_NETWORK_IDLE", "1").lower() not in {"0", "false", "no"},
            require_profile=os.environ.get("OZ_CRAWLER_REQUIRE_PROFILE", "0").lower() in {"1", "true", "yes"},
            fail_on_validation=os.environ.get("OZ_CRAWLER_FAIL_ON_VALIDATION", "0").lower() in {"1", "true", "yes"},
        )


@dataclass
class CrawledPage:
    source_url: str
    html: str
    title: str | None = None


def crawl_single_page(
    *,
    url: str,
    registry_root: Path,
    vendor: str,
    library: str,
    version: str,
    title: str | None = None,
    max_pages: int = 1,
    options: CrawlOptions | None = None,
) -> Path:
    crawl_options = options or CrawlOptions.from_env(max_pages=max_pages)
    assert_public_http_url(url)
    profile = load_profile(registry_root, vendor, library)
    if crawl_options.require_profile and profile is None:
        raise RuntimeError(f"no library profile found for {vendor}/{library}")

    state = CrawlRunState.create(crawl_state_dir(crawl_options, vendor, library, version), crawl_options.progress_callback)
    pages = crawl_pages(url, title=title, options=crawl_options, profile=profile, state=state)
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
    artifacts = collect_source_artifacts(url, pages, profile=profile, state=state, max_documents=max(24, crawl_options.max_pages))
    artifact_pages = artifact_normalized_pages(artifacts)
    all_pages, rejected = prepare_pages(pages + artifact_pages, profile=profile, version=version)
    rejected.extend(dead_letter_rejections(state))
    if not all_pages:
        write_rejections(target, rejected)
        state.write_artifacts(target)
        raise RuntimeError(f"all crawled pages were rejected for {vendor}/{library}")

    guide_links: list[tuple[str, str]] = []
    for page in all_pages:
        relative = page.path or f"guides/{slugify(page.title or page.source_url)}.md"
        guide_links.append((relative, page.title or page.source_url))
        (target / relative).parent.mkdir(parents=True, exist_ok=True)
        (target / relative).write_text(
            f"# {page.title}\n\n**Source:** {page.source_url}\n\n{page.markdown}",
            encoding="utf-8",
        )
    write_rejections(target, rejected)
    state.write_artifacts(target)
    write_chunks(target, all_pages)
    write_symbols(target, all_pages, profile=profile)
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
                "profile": profile.key if profile else None,
                "rejected_pages": len(rejected),
            },
            indent=2,
            sort_keys=True,
        )
        + "\n",
        encoding="utf-8",
    )
    validation = validate_fixture(target, profile)
    write_validation(target, validation)
    if crawl_options.fail_on_validation and not validation.passed:
        raise RuntimeError("; ".join(validation.errors))

    return target


def artifact_normalized_pages(artifacts: list[SourceArtifact]) -> list[NormalizedPage]:
    return [
        NormalizedPage(
            title=sanitize_secret_tokens(artifact.title),
            markdown=clean_markdown(artifact.markdown),
            source_url=artifact.source_url,
            path=artifact.path,
        )
        for artifact in artifacts
        if artifact.markdown.strip()
    ]


def crawl_pages(
    url: str,
    *,
    title: str | None,
    options: CrawlOptions,
    profile: LibraryProfile | None = None,
    state: CrawlRunState | None = None,
) -> list[NormalizedPage]:
    if options.max_pages <= 0:
        return []
    if profile is not None and profile.needs_js and options.fetcher == "auto":
        options = replace(options, fetcher="dynamic")
    crawled = crawl_pages_with_scrapling(url, options=options, profile=profile, state=state)
    if crawled is None:
        crawled = crawl_pages_with_stdlib(url, options=options, profile=profile, state=state)
    return [normalize_html(page.html, source_url=page.source_url, title=title or page.title) for page in crawled]


def crawl_pages_with_scrapling(
    url: str,
    *,
    options: CrawlOptions,
    profile: LibraryProfile | None = None,
    state: CrawlRunState | None = None,
) -> list[CrawledPage] | None:
    assert_public_http_url(url)
    if options.fetcher.lower() == "stdlib" or pinned_fetch_required():
        return None
    ensure_vendored_scrapling_path()
    try:
        from scrapling.fetchers import AsyncDynamicSession, AsyncStealthySession, FetcherSession
        from scrapling.spiders import Spider
    except ImportError:
        return None

    parsed_seed = urlparse(url)
    seed_allowed_domains = {parsed_seed.netloc}
    max_pages = options.max_pages
    fetcher_mode = options.fetcher.lower()
    declared_links = discover_declared_doc_links(url)
    if profile is not None:
        declared_links.extend(profile.preferred_urls)

    class OzDocsSpider(Spider):  # type: ignore[misc, valid-type]
        name = "oz_docs"
        start_urls = [url]
        allowed_domains = seed_allowed_domains
        concurrent_requests = max(1, options.concurrent_requests)
        concurrent_requests_per_domain = per_host_concurrency(options.concurrent_requests)
        download_delay = max(0.0, options.download_delay)
        robots_txt_obey = options.robots_txt

        def __init__(self, *args: Any, **kwargs: Any) -> None:
            super().__init__(*args, **kwargs)
            self.pages: list[CrawledPage] = []
            self.seen: set[str] = {url}

        def configure_sessions(self, manager: Any) -> None:
            if fetcher_mode == "stealth":
                manager.add(
                    "default",
                    AsyncStealthySession(headless=options.headless, network_idle=options.network_idle),
                    default=True,
                )
            elif fetcher_mode == "dynamic":
                manager.add(
                    "default",
                    AsyncDynamicSession(headless=options.headless, network_idle=options.network_idle),
                    default=True,
                )
            elif fetcher_mode == "auto":
                manager.add("default", FetcherSession(impersonate="chrome"), default=True)
                manager.add(
                    "dynamic",
                    AsyncDynamicSession(headless=options.headless, network_idle=options.network_idle),
                    lazy=True,
                )
                manager.add(
                    "stealth",
                    AsyncStealthySession(headless=options.headless, network_idle=options.network_idle),
                    lazy=True,
                )
            else:
                manager.add("default", FetcherSession(impersonate="chrome"), default=True)

        async def parse(self, response: Any) -> Any:
            response_url = response_source_url(response, fallback=url)
            html = extract_html(response)
            if is_probably_binary_text(html):
                return
            if len(html.encode("utf-8")) > max_page_bytes():
                if state is not None:
                    state.record_dead_letter(response_url, stage="scrapling_fetch", error="page exceeded max byte size")
                return
            if html.strip() and len(self.pages) < max_pages:
                self.pages.append(CrawledPage(source_url=response_url, html=html, title=response_title(response)))
                if state is not None:
                    state.record_page(response_url, html, response_title(response))
                yield {"url": response_url, "bytes": len(html)}

            for link in candidate_doc_links(
                url,
                response_url,
                html,
                declared_links if response_url == url else [],
                profile=profile,
            ):
                if len(self.seen) >= max_pages:
                    break
                if link in self.seen:
                    continue
                self.seen.add(link)
                try:
                    sid = session_id_for_link(fetcher_mode, link)
                    kwargs: dict[str, Any] = {"callback": self.parse, "sid": sid}
                    if sid in {"dynamic", "stealth"} or fetcher_mode in {"dynamic", "stealth"}:
                        kwargs["network_idle"] = options.network_idle
                    yield response.follow(link, **kwargs)
                except TypeError:
                    yield response.follow(link, callback=self.parse)

    spider_kwargs: dict[str, Any] = {}
    if options.crawldir is not None:
        spider_kwargs["crawldir"] = str(options.crawldir)
    spider = OzDocsSpider(**spider_kwargs)
    try:
        spider.start()
    except Exception:
        if fetcher_mode != "auto":
            raise
        return None
    return spider.pages


def crawl_pages_with_stdlib(
    url: str,
    *,
    options: CrawlOptions,
    profile: LibraryProfile | None = None,
    state: CrawlRunState | None = None,
) -> list[CrawledPage]:
    assert_public_http_url(url)
    run_state = state or CrawlRunState.create(options.crawldir)
    pages = restored_pages(run_state)
    if pages:
        first_html = pages[0].html
    else:
        first_html = fetch_html_stdlib(url, state=run_state)
        pages = [CrawledPage(source_url=url, html=first_html)]
        run_state.record_page(url, first_html)
    if options.max_pages <= 1:
        return pages

    discovered = discover_declared_doc_links(url, fetcher="stdlib")
    if profile is not None:
        discovered.extend(profile.preferred_urls)
    discovered.extend(discover_same_site_links(url, first_html))
    seen = {page.source_url for page in pages} | {url}
    queue = candidate_doc_links(url, url, first_html, discovered, profile=profile)
    for page in list(pages):
        queue.extend(candidate_doc_links(url, page.source_url, page.html, [], profile=profile))
    for linked_url in dedupe(queue):
        if len(pages) >= options.max_pages:
            break
        if linked_url in seen:
            continue
        assert_public_http_url(linked_url)
        seen.add(linked_url)
        try:
            html = fetch_html_stdlib(linked_url, state=run_state)
        except CrawlerFetchError as exc:
            run_state.record_dead_letter(
                linked_url,
                stage="page_fetch",
                error=str(exc),
                attempts=retry_attempts(),
                status=exc.status,
                retry_after=exc.retry_after,
                transient=exc.transient,
            )
            LOGGER.info("skipping linked crawler URL %s: %s", linked_url, exc)
            continue
        except Exception as exc:
            run_state.record_dead_letter(linked_url, stage="page_fetch", error=str(exc), attempts=1)
            LOGGER.info("skipping linked crawler URL %s: %s", linked_url, exc)
            continue
        pages.append(CrawledPage(source_url=linked_url, html=html))
        run_state.record_page(linked_url, html)
    return pages


def fetch_html(url: str) -> str:
    assert_public_http_url(url)
    ensure_vendored_scrapling_path()
    try:
        from scrapling.fetchers import Fetcher
    except ImportError:
        return fetch_html_stdlib(url)
    if pinned_fetch_required():
        return fetch_html_stdlib(url)

    page = Fetcher.get(url, stealthy_headers=True)
    html = extract_html(page)
    if is_probably_binary_text(html) or not html.strip():
        raise RuntimeError(f"Scrapling fetched {url}, but no HTML content was found on the response object")
    return html


def ensure_vendored_scrapling_path() -> None:
    for ancestor in Path(__file__).resolve().parents:
        candidate = ancestor / "third_party" / "Scrapling"
        if (candidate / "scrapling").is_dir():
            candidate_text = str(candidate)
            if candidate_text not in sys.path:
                sys.path.insert(0, candidate_text)
            return


def fetch_html_stdlib(url: str, *, state: CrawlRunState | None = None) -> str:
    assert_public_http_url(url)
    if state is not None:
        state.limiter.wait(url)
    extra_headers = state.cache.conditional_headers(url) if state else {}
    extra_headers["Accept"] = "text/html, application/xhtml+xml, text/plain;q=0.5, */*;q=0.1"
    response = fetch_public_url(
        url,
        timeout=20,
        max_bytes=max_page_bytes(),
        extra_headers=extra_headers,
        attempts=retry_attempts(),
    )
    if response.status == 304 and state is not None:
        cached = state.cache.cached_body(url)
        if cached is None:
            raise RuntimeError(f"{url} returned 304 but no cached body exists")
        text = decode_text_response(cached, response.headers.get("content-type"))
        if text is None:
            raise RuntimeError(f"{url} cached response is not textual documentation")
        return text
    if state is not None:
        state.cache.store(url, response.body, response.headers, response.status)
    text = decode_text_response(response.body, response.headers.get("content-type"))
    if text is None:
        raise RuntimeError(f"{url} did not return textual documentation")
    return text


def fetch_text_optional(url: str, *, fetcher: str = "auto") -> str | None:
    try:
        if fetcher == "stdlib":
            return fetch_html_stdlib(url)
        return fetch_html(url)
    except Exception as exc:
        LOGGER.info("optional crawler fetch failed for %s: %s", url, exc)
        return None


def extract_html(page: Any) -> str:
    for attr in ("html", "content", "body", "text", "raw_body"):
        value = getattr(page, attr, None)
        if callable(value):
            value = value()
        if isinstance(value, bytes):
            return value.decode("utf-8", errors="replace")
        if isinstance(value, str) and value.strip():
            return value
    return str(page)


def response_source_url(response: Any, *, fallback: str) -> str:
    for attr in ("url", "final_url", "request_url"):
        value = getattr(response, attr, None)
        if value:
            return str(value)
    meta = getattr(response, "meta", None)
    if isinstance(meta, dict):
        for key in ("url", "final_url", "request_url"):
            if meta.get(key):
                return str(meta[key])
    return fallback


def response_title(response: Any) -> str | None:
    try:
        title = response.css("title::text").get("")
        return str(title) if title else None
    except (AttributeError, TypeError, ValueError):
        return None


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


def candidate_doc_links(
    seed_url: str,
    current_url: str,
    html: str,
    declared_links: list[str],
    *,
    profile: LibraryProfile | None = None,
) -> list[str]:
    parsed_seed = urlparse(seed_url)
    if parsed_seed.netloc.lower() == "github.com":
        return []
    links = []
    links.extend(declared_links)
    links.extend(discover_same_site_links(current_url, html))
    filtered = [
        link
        for link in dedupe(links)
        if is_crawlable_doc_url(link, parsed_seed.netloc)
        and public_crawl_target(link)
        and url_allowed_by_profile(link, profile)
        and same_site_or_subdomain(link, parsed_seed.netloc)
        and link != current_url
    ]
    preferred = set(profile.preferred_urls) if profile is not None else set()
    filtered.sort(key=lambda link: (0 if link in preferred else 1, -doc_url_score(link), len(link), link))
    return filtered


def prepare_pages(
    pages: list[NormalizedPage],
    *,
    profile: LibraryProfile | None,
    version: str = "latest",
) -> tuple[list[NormalizedPage], list[dict[str, Any]]]:
    accepted: list[NormalizedPage] = []
    rejected: list[dict[str, Any]] = []
    sanitized_pages = [
        replace(page, title=sanitize_secret_tokens(page.title), markdown=clean_markdown(page.markdown)) for page in pages
    ]
    unique_pages, duplicate_rejections = dedupe_pages_by_content(sanitized_pages)
    rejected.extend(duplicate_rejections)
    assigned_pages, version_rejections = filter_current_version(assign_page_paths(unique_pages), target_version=version)
    rejected.extend(version_rejections)
    for page in assigned_pages:
        if profile is not None and not language_allowed(page.markdown, profile.target_language):
            rejected.append(
                {
                    "title": page.title,
                    "source_url": page.source_url,
                    "score": 0,
                    "reasons": [f"language does not match target {profile.target_language}"],
                    "content_type": "language_mismatch",
                }
            )
            continue
        quality = score_page(page, profile)
        if not quality.accepted:
            rejected.append(rejection_row(page, quality))
            continue
        accepted.append(
            replace(
                page,
                quality_score=quality.score,
                content_type=quality.content_type,
                symbols=tuple(extract_page_symbol_names(page, profile=profile)),
            )
        )
    return accepted, rejected


def dedupe_pages_by_content(pages: list[NormalizedPage]) -> tuple[list[NormalizedPage], list[dict[str, Any]]]:
    seen: dict[str, NormalizedPage] = {}
    accepted: list[NormalizedPage] = []
    rejected: list[dict[str, Any]] = []
    for page in pages:
        key = page_content_key(page.markdown)
        canonical = seen.get(key)
        if canonical is not None:
            rejected.append(
                {
                    "title": page.title,
                    "source_url": page.source_url,
                    "score": 0,
                    "reasons": ["duplicate content", f"canonical source: {canonical.source_url}"],
                    "content_type": "duplicate",
                }
            )
            continue
        seen[key] = page
        accepted.append(page)
    return accepted, rejected


def page_content_key(markdown: str) -> str:
    normalized = re.sub(r"\s+", " ", markdown.strip().lower())
    return hashlib.sha256(normalized.encode("utf-8")).hexdigest()


def rejection_row(page: NormalizedPage, quality: QualityResult) -> dict[str, Any]:
    return {
        "title": page.title,
        "source_url": page.source_url,
        "score": quality.score,
        "reasons": quality.reasons,
        "content_type": quality.content_type,
    }


def dead_letter_rejections(state: CrawlRunState) -> list[dict[str, Any]]:
    return [
        {
            "title": letter.url,
            "source_url": letter.url,
            "score": 0,
            "reasons": [letter.error],
            "content_type": f"network_{letter.stage}",
            "attempts": letter.attempts,
            "status": letter.status,
            "transient": letter.transient,
        }
        for letter in state.dead_letters
    ]


def write_rejections(target: Path, rejected: list[dict[str, Any]]) -> None:
    path = target / "_rejected.jsonl"
    if not rejected:
        path.write_text("", encoding="utf-8")
        return
    path.write_text("".join(json.dumps(row, sort_keys=True) + "\n" for row in rejected), encoding="utf-8")


def is_crawlable_doc_url(url: str, netloc: str) -> bool:
    parsed = urlparse(url)
    if parsed.scheme not in {"http", "https"} or not parsed.netloc:
        return False
    if malformed_discovered_url(url):
        return False
    if not is_textual_url_candidate(url):
        return False
    path = parsed.path.lower()
    if path.endswith("/llms.txt") or path.endswith("/llms-full.txt"):
        return False
    if path.endswith("/sitemap.xml") or path.endswith("/sitemap_index.xml"):
        return False
    if any(part in path for part in ("/blog/", "/pricing", "/careers", "/login", "/signup", "/account")):
        return False
    if "/api/" in path and not re.search(r"(docs|documentation|reference|openapi|swagger)", path):
        return False
    query = parsed.query.lower()
    if query and re.search(r"(^|&)(image|img|og|product|screenshot|width|height)=", query):
        return False
    return same_site_or_subdomain(url, netloc)


def malformed_discovered_url(url: str) -> bool:
    parsed = urlparse(url)
    raw = f"{parsed.path}?{parsed.query}" if parsed.query else parsed.path
    return any(char in raw for char in ("[", "]", "(", ")", "'", '"', "\\"))


def same_site_or_subdomain(url: str, netloc: str) -> bool:
    try:
        host = urlparse(url).netloc
    except ValueError:
        return False
    return host == netloc or host.endswith(f".{netloc}")


def public_crawl_target(url: str) -> bool:
    try:
        assert_public_http_url(url)
    except ValueError:
        return False
    return True


def crawl_state_dir(options: CrawlOptions, vendor: str, library: str, version: str) -> Path | None:
    if options.crawldir is not None:
        return options.crawldir
    root = os.environ.get("OZ_CRAWLER_CHECKPOINT_DIR")
    if not root:
        return None
    safe = slugify(f"{vendor}-{library}-{version}")
    return Path(root) / safe


def restored_pages(state: CrawlRunState) -> list[CrawledPage]:
    return [
        CrawledPage(source_url=str(row["source_url"]), html=str(row["html"]), title=str(row.get("title") or "") or None)
        for row in state.restored_pages
    ]


def per_host_concurrency(global_concurrency: int) -> int:
    try:
        configured = int(os.environ.get("OZ_CRAWLER_PER_HOST_CONCURRENCY", "2"))
    except ValueError:
        configured = 2
    return max(1, min(max(1, global_concurrency), configured))


def doc_url_score(url: str) -> int:
    lower = url.lower()
    score = 0
    for token, weight in {
        "docs": 8,
        "documentation": 8,
        "guide": 7,
        "reference": 7,
        "api": 6,
        "sdk": 5,
        "examples": 5,
        "tutorial": 4,
        "quickstart": 4,
        "getting-started": 4,
        "llms": 3,
        "sitemap": 2,
    }.items():
        if token in lower:
            score += weight
    return score


def session_id_for_link(fetcher_mode: str, url: str) -> str:
    if fetcher_mode in {"stealth", "dynamic", "http"}:
        return "default"
    lower = url.lower()
    if any(token in lower for token in ("cloudflare", "captcha", "login", "protected")):
        return "stealth"
    if any(token in lower for token in ("app", "dashboard", "interactive")):
        return "dynamic"
    return "default"


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


def discover_declared_doc_links(url: str, *, fetcher: str = "auto") -> list[str]:
    parsed = urlparse(url)
    base = f"{parsed.scheme}://{parsed.netloc}"
    links: list[str] = []

    for name in ("/llms-full.txt", "/llms.txt"):
        text = fetch_text_optional(base + name, fetcher=fetcher)
        if text:
            links.extend(extract_urls(text, base_url=base))

    sitemap = fetch_text_optional(base + "/sitemap.xml", fetcher=fetcher)
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


def slugify(value: str) -> str:
    slug = re.sub(r"[^A-Za-z0-9]+", "-", value.lower()).strip("-")
    return slug or "page"
