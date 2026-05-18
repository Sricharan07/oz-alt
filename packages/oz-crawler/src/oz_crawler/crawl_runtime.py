from __future__ import annotations

import hashlib
import json
import os
import random
import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Callable
from urllib.parse import urlparse


ProgressCallback = Callable[[dict[str, Any]], None]


def int_env(name: str, default: int, *, minimum: int = 0) -> int:
    try:
        return max(minimum, int(os.environ.get(name, str(default))))
    except ValueError:
        return default


def float_env(name: str, default: float, *, minimum: float = 0.0) -> float:
    try:
        return max(minimum, float(os.environ.get(name, str(default))))
    except ValueError:
        return default


def max_page_bytes() -> int:
    return int_env("OZ_MAX_PAGE_BYTES", 2_000_000, minimum=1)


def retry_attempts() -> int:
    return int_env("OZ_CRAWLER_RETRY_ATTEMPTS", 3, minimum=1)


def retry_base_delay() -> float:
    return float_env("OZ_CRAWLER_RETRY_BASE_DELAY_SECONDS", 0.35, minimum=0.0)


@dataclass
class DeadLetter:
    url: str
    stage: str
    error: str
    attempts: int = 1
    status: int | None = None
    retry_after: float | None = None
    transient: bool = False

    def as_dict(self) -> dict[str, Any]:
        return {
            "url": self.url,
            "stage": self.stage,
            "error": self.error[:1000],
            "attempts": self.attempts,
            "status": self.status,
            "retry_after": self.retry_after,
            "transient": self.transient,
        }


@dataclass
class HostLimiter:
    per_host_delay: float = field(default_factory=lambda: float_env("OZ_CRAWLER_PER_HOST_DELAY_SECONDS", 0.25))
    next_allowed: dict[str, float] = field(default_factory=dict)

    def wait(self, url: str) -> None:
        host = urlparse(url).netloc.lower()
        now = time.monotonic()
        delay = self.next_allowed.get(host, 0.0) - now
        if delay > 0:
            time.sleep(delay)
        self.next_allowed[host] = time.monotonic() + self.per_host_delay

    def backoff(self, url: str, retry_after: float | None = None) -> None:
        host = urlparse(url).netloc.lower()
        delay = retry_after if retry_after and retry_after > 0 else self.per_host_delay * 2
        self.next_allowed[host] = max(self.next_allowed.get(host, 0.0), time.monotonic() + delay)


@dataclass
class FetchCache:
    root: Path | None

    def metadata(self, url: str) -> dict[str, Any]:
        if self.root is None:
            return {}
        path = self.meta_path(url)
        if not path.exists():
            return {}
        try:
            value = json.loads(path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            return {}
        return value if isinstance(value, dict) else {}

    def conditional_headers(self, url: str) -> dict[str, str]:
        meta = self.metadata(url)
        headers: dict[str, str] = {}
        if meta.get("etag"):
            headers["If-None-Match"] = str(meta["etag"])
        if meta.get("last_modified"):
            headers["If-Modified-Since"] = str(meta["last_modified"])
        return headers

    def cached_body(self, url: str) -> bytes | None:
        if self.root is None:
            return None
        path = self.body_path(url)
        try:
            return path.read_bytes() if path.exists() else None
        except OSError:
            return None

    def store(self, url: str, body: bytes, headers: dict[str, str], status: int) -> None:
        if self.root is None or status != 200:
            return
        self.root.mkdir(parents=True, exist_ok=True)
        self.body_path(url).write_bytes(body)
        meta = {
            "url": url,
            "etag": headers.get("etag"),
            "last_modified": headers.get("last-modified"),
            "content_type": headers.get("content-type"),
            "body_sha256": hashlib.sha256(body).hexdigest(),
            "checked_at": int(time.time()),
        }
        self.meta_path(url).write_text(json.dumps(meta, sort_keys=True) + "\n", encoding="utf-8")

    def key(self, url: str) -> str:
        return hashlib.sha256(url.encode("utf-8")).hexdigest()

    def meta_path(self, url: str) -> Path:
        assert self.root is not None
        return self.root / f"{self.key(url)}.json"

    def body_path(self, url: str) -> Path:
        assert self.root is not None
        return self.root / f"{self.key(url)}.body"


@dataclass
class CrawlRunState:
    root: Path | None = None
    progress_callback: ProgressCallback | None = None
    completed_urls: set[str] = field(default_factory=set)
    dead_letters: list[DeadLetter] = field(default_factory=list)
    restored_pages: list[dict[str, str]] = field(default_factory=list)
    limiter: HostLimiter = field(default_factory=HostLimiter)
    cache: FetchCache = field(default_factory=lambda: FetchCache(None))

    @classmethod
    def create(cls, root: Path | None, progress_callback: ProgressCallback | None = None) -> "CrawlRunState":
        state = cls(root=root, progress_callback=progress_callback, cache=FetchCache(root / "http-cache" if root else None))
        state.load()
        return state

    def load(self) -> None:
        if self.root is None:
            return
        pages_path = self.root / "pages.jsonl"
        if pages_path.exists():
            for line in pages_path.read_text(encoding="utf-8").splitlines():
                if not line.strip():
                    continue
                try:
                    row = json.loads(line)
                except json.JSONDecodeError:
                    continue
                if isinstance(row, dict) and row.get("source_url") and row.get("html"):
                    self.restored_pages.append({"source_url": str(row["source_url"]), "html": str(row["html"])})
                    self.completed_urls.add(str(row["source_url"]))
        dead_path = self.root / "dead_letters.jsonl"
        if dead_path.exists():
            for line in dead_path.read_text(encoding="utf-8").splitlines():
                if line.strip():
                    try:
                        row = json.loads(line)
                    except json.JSONDecodeError:
                        continue
                    self.dead_letters.append(
                        DeadLetter(
                            url=str(row.get("url") or ""),
                            stage=str(row.get("stage") or "fetch"),
                            error=str(row.get("error") or ""),
                            attempts=int(row.get("attempts") or 1),
                            status=int(row["status"]) if row.get("status") is not None else None,
                            retry_after=float(row["retry_after"]) if row.get("retry_after") is not None else None,
                            transient=bool(row.get("transient")),
                        )
                    )

    def record_page(self, source_url: str, html: str, title: str | None = None) -> None:
        if source_url in self.completed_urls:
            return
        self.completed_urls.add(source_url)
        if self.root is not None:
            self.root.mkdir(parents=True, exist_ok=True)
            row = {"source_url": source_url, "html": html, "title": title or ""}
            with (self.root / "pages.jsonl").open("a", encoding="utf-8") as handle:
                handle.write(json.dumps(row, sort_keys=True) + "\n")
        self.emit_progress()

    def record_dead_letter(
        self,
        url: str,
        *,
        stage: str,
        error: str,
        attempts: int = 1,
        status: int | None = None,
        retry_after: float | None = None,
        transient: bool = False,
    ) -> None:
        letter = DeadLetter(url, stage, error, attempts=attempts, status=status, retry_after=retry_after, transient=transient)
        self.dead_letters.append(letter)
        if self.root is not None:
            self.root.mkdir(parents=True, exist_ok=True)
            with (self.root / "dead_letters.jsonl").open("a", encoding="utf-8") as handle:
                handle.write(json.dumps(letter.as_dict(), sort_keys=True) + "\n")
        if retry_after:
            self.limiter.backoff(url, retry_after)
        self.emit_progress()

    def emit_progress(self) -> None:
        if self.progress_callback is not None:
            self.progress_callback(self.summary())

    def summary(self) -> dict[str, Any]:
        by_status: dict[str, int] = {}
        by_stage: dict[str, int] = {}
        for letter in self.dead_letters:
            if letter.status is not None:
                by_status[str(letter.status)] = by_status.get(str(letter.status), 0) + 1
            by_stage[letter.stage] = by_stage.get(letter.stage, 0) + 1
        return {
            "completed_urls": len(self.completed_urls),
            "dead_letters": len(self.dead_letters),
            "dead_letter_items": [letter.as_dict() for letter in self.dead_letters[-50:]],
            "dead_letters_by_status": by_status,
            "dead_letters_by_stage": by_stage,
        }

    def write_artifacts(self, target: Path) -> None:
        (target / "_crawl_state.json").write_text(json.dumps(self.summary(), indent=2, sort_keys=True) + "\n", encoding="utf-8")
        (target / "_crawl_errors.jsonl").write_text(
            "".join(json.dumps(letter.as_dict(), sort_keys=True) + "\n" for letter in self.dead_letters),
            encoding="utf-8",
        )


def retry_delay(attempt: int, retry_after: float | None = None) -> float:
    if retry_after is not None and retry_after > 0:
        return retry_after
    base = retry_base_delay()
    return min(8.0, base * (2 ** max(0, attempt - 1))) + random.uniform(0, base)
