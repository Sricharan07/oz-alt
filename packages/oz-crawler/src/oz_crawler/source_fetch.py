from __future__ import annotations

import json
import logging
import os
from urllib.parse import ParseResult, urlparse

from oz_crawler.crawl_runtime import CrawlRunState, max_page_bytes, retry_attempts
from oz_crawler.security import CrawlerFetchError, assert_public_http_url, fetch_public_url
from oz_crawler.text import decode_text_response

LOGGER = logging.getLogger(__name__)


def parse_http_url(url: str) -> ParseResult | None:
    try:
        parsed = urlparse(url)
        hostname = parsed.hostname
    except ValueError:
        return None
    if parsed.scheme not in {"http", "https"} or not parsed.netloc or not hostname:
        return None
    if "[" in parsed.netloc or "]" in parsed.netloc:
        return None
    return parsed


def github_repo(url: str) -> list[tuple[str, str]]:
    parsed = urlparse(url)
    if parsed.netloc.lower() != "github.com":
        return []
    parts = [part for part in parsed.path.split("/") if part]
    if len(parts) >= 2:
        return [(parts[0], parts[1].removesuffix(".git"))]
    return []


def fetch_json(url: str, *, state: CrawlRunState | None = None):
    text = fetch_text(url, state=state)
    if not text:
        return None
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        return None


def fetch_text(url: str, *, state: CrawlRunState | None = None) -> str | None:
    try:
        assert_public_http_url(url)
        if state is not None and robots_enabled():
            if not state.robots.allowed(url):
                state.record_dead_letter(url, stage="robots", error="blocked by robots.txt", attempts=1)
                return None
            state.limiter.wait(url, state.robots.crawl_delay(url))
        extra_headers = state.cache.conditional_headers(url) if state else {}
        response = fetch_public_url(
            url,
            timeout=20,
            max_bytes=max_page_bytes(),
            extra_headers=extra_headers,
            attempts=retry_attempts(),
        )
        if response.status == 304 and state is not None:
            cached = state.cache.cached_body(url)
            if cached is not None:
                return decode_text_response(cached, response.headers.get("content-type"))
            return None
        if state is not None:
            state.cache.store(url, response.body, response.headers, response.status)
        return decode_text_response(response.body, response.headers.get("content-type"))
    except CrawlerFetchError as exc:
        if state is not None:
            state.record_dead_letter(
                url,
                stage="source_fetch",
                error=str(exc),
                attempts=retry_attempts(),
                status=exc.status,
                retry_after=exc.retry_after,
                transient=exc.transient,
            )
        LOGGER.info("optional source fetch failed for %s: %s", url, exc)
        return None
    except Exception as exc:
        if state is not None:
            state.record_dead_letter(url, stage="source_fetch", error=str(exc), attempts=1)
        LOGGER.info("optional source fetch failed for %s: %s", url, exc)
        return None


def robots_enabled() -> bool:
    return os.environ.get("OZ_CRAWLER_ROBOTS", "1").lower() not in {"0", "false", "no"}
