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
from urllib.robotparser import RobotFileParser


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

    def wait(self, url: str, min_delay: float | None = None) -> None:
        host = urlparse(url).netloc.lower()
        now = time.monotonic()
        delay = self.next_allowed.get(host, 0.0) - now
        if delay > 0:
            time.sleep(delay)
        self.next_allowed[host] = time.monotonic() + max(self.per_host_delay, float(min_delay or 0))

    def backoff(self, url: str, retry_after: float | None = None) -> None:
        host = urlparse(url).netloc.lower()
        delay = retry_after if retry_after and retry_after > 0 else self.per_host_delay * 2
        self.next_allowed[host] = max(self.next_allowed.get(host, 0.0), time.monotonic() + delay)


@dataclass
class RobotsPolicy:
    user_agent: str = "oz-crawler/0.1"
    parsers: dict[str, RobotFileParser | None] = field(default_factory=dict)

    def allowed(self, url: str) -> bool:
        parser = self.parser_for(url)
        return True if parser is None else parser.can_fetch(self.user_agent, url)

    def crawl_delay(self, url: str) -> float | None:
        parser = self.parser_for(url)
        if parser is None:
            return None
        try:
            value = parser.crawl_delay(self.user_agent)
            return float(value) if value is not None else None
        except (TypeError, ValueError):
            return None

    def parser_for(self, url: str) -> RobotFileParser | None:
        parsed = urlparse(url)
        if parsed.scheme not in {"http", "https"} or not parsed.netloc:
            return None
        key = f"{parsed.scheme}://{parsed.netloc}"
        if key in self.parsers:
            return self.parsers[key]
        parser = RobotFileParser()
        parser.set_url(f"{key}/robots.txt")
        try:
            from oz_crawler.security import fetch_public_url

            response = fetch_public_url(
                f"{key}/robots.txt",
                timeout=10,
                max_bytes=200_000,
                attempts=1,
                user_agent=self.user_agent,
            )
            parser.parse(response.body.decode("utf-8", errors="replace").splitlines())
        except Exception:
            self.parsers[key] = None
            return None
        self.parsers[key] = parser
        return parser


@dataclass
class RawObjectStore:
    root: Path | None = None
    s3_bucket: str | None = None
    s3_prefix: str = "oz/raw"

    @classmethod
    def create(cls, checkpoint_root: Path | None) -> "RawObjectStore":
        bucket = os.environ.get("OZ_RAW_OBJECT_S3_BUCKET")
        prefix = os.environ.get("OZ_RAW_OBJECT_S3_PREFIX", "oz/raw").strip("/")
        root_value = os.environ.get("OZ_RAW_OBJECT_ROOT")
        root = Path(root_value).expanduser() if root_value else (checkpoint_root / "raw-objects" if checkpoint_root else None)
        return cls(root=root, s3_bucket=bucket, s3_prefix=prefix)

    def put(self, url: str, body: bytes, headers: dict[str, str]) -> dict[str, Any]:
        body_sha = hashlib.sha256(body).hexdigest()
        etag = clean_key_part(headers.get("etag") or "no-etag")
        checked_at = str(int(time.time()))
        key = f"{self.s3_prefix}/{hashlib.sha256(url.encode('utf-8')).hexdigest()}/{etag}/{checked_at}-{body_sha}.body"
        if self.s3_bucket:
            self.put_s3(key, body)
            return {"raw_object_key": f"s3://{self.s3_bucket}/{key}", "raw_object_sha256": body_sha, "raw_object_store": "s3"}
        if self.root is not None:
            path = self.root / key
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_bytes(body)
            return {"raw_object_key": key, "raw_object_sha256": body_sha, "raw_object_store": "local"}
        return {"raw_object_key": key, "raw_object_sha256": body_sha, "raw_object_store": "disabled"}

    def put_s3(self, key: str, body: bytes) -> None:
        try:
            import boto3  # type: ignore
        except Exception as exc:  # pragma: no cover - optional production dependency
            raise RuntimeError("OZ_RAW_OBJECT_S3_BUCKET requires boto3 to be installed") from exc
        boto3.client("s3").put_object(Bucket=self.s3_bucket, Key=key, Body=body)


def clean_key_part(value: str) -> str:
    cleaned = "".join(ch if ch.isalnum() or ch in {"-", "_", "."} else "-" for ch in value.strip())
    return cleaned.strip("-")[:80] or "none"


@dataclass
class FetchCache:
    root: Path | None
    raw_store: RawObjectStore = field(default_factory=RawObjectStore)

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
        if status != 200:
            return
        raw_object = self.raw_store.put(url, body, headers)
        if self.root is None:
            return
        self.root.mkdir(parents=True, exist_ok=True)
        self.body_path(url).write_bytes(body)
        meta = {
            "url": url,
            "etag": headers.get("etag"),
            "last_modified": headers.get("last-modified"),
            "content_type": headers.get("content-type"),
            "body_sha256": hashlib.sha256(body).hexdigest(),
            **raw_object,
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

    def artifact_key(self, url: str) -> str:
        meta = self.metadata(url)
        if meta.get("raw_object_key"):
            return str(meta["raw_object_key"])
        return f"http-cache/{self.key(url)}.body"


@dataclass
class CrawlRunState:
    root: Path | None = None
    progress_callback: ProgressCallback | None = None
    completed_urls: set[str] = field(default_factory=set)
    dead_letters: list[DeadLetter] = field(default_factory=list)
    restored_pages: list[dict[str, str]] = field(default_factory=list)
    limiter: HostLimiter = field(default_factory=HostLimiter)
    robots: RobotsPolicy = field(default_factory=RobotsPolicy)
    cache: FetchCache = field(default_factory=lambda: FetchCache(None))

    @classmethod
    def create(cls, root: Path | None, progress_callback: ProgressCallback | None = None) -> "CrawlRunState":
        state = cls(
            root=root,
            progress_callback=progress_callback,
            cache=FetchCache(root / "http-cache" if root else None, RawObjectStore.create(root)),
        )
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
