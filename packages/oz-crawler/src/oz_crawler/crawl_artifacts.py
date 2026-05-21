from __future__ import annotations

import hashlib
import json
import re
from pathlib import Path
from typing import Any
from urllib.parse import urlparse

from oz_crawler.corpus_surfaces import normalized_metadata
from oz_crawler.normalize import NormalizedPage, clean_markdown
from oz_crawler.token_counting import token_count


def write_source_documents(target: Path, pages: list[NormalizedPage]) -> None:
    rows: list[dict[str, Any]] = []
    seen: set[str] = set()
    for page in pages:
        key = canonical_source_key(page)
        if key in seen:
            continue
        seen.add(key)
        metadata = normalized_metadata(page)
        clean = clean_markdown(page.markdown)
        rows.append(
            {
                "source_document_key": key,
                "source_type": metadata.get("source_type") or page.source_type,
                "document_role": metadata.get("document_role") or "unknown",
                "canonical_url": page.canonical_url or page.source_url,
                "source_url": page.source_url,
                "path": page.path,
                "title": page.title,
                "product": metadata.get("product") or "",
                "product_confidence": metadata.get("product_confidence") or 0,
                "language": metadata.get("language") or "",
                "content_markdown": clean,
                "parallel_structured_json": metadata.get("parallel_structured_json") or metadata.get("operation") or {},
                "content_sha": page_content_key(clean),
                "raw_token_count": token_count(page.markdown),
                "clean_token_count": token_count(clean),
                "source_priority": page.source_priority,
                "discovered_from": page.discovered_from,
                "raw_artifact_key": metadata.get("raw_artifact_key") or "",
                "raw_object_store": metadata.get("raw_object_store") or "",
                "raw_object_sha256": metadata.get("raw_object_sha256") or "",
                "etag": metadata.get("etag") or "",
                "last_modified": metadata.get("last_modified") or "",
                "metadata_json": metadata,
            }
        )
    (target / "_sources.jsonl").write_text("".join(json.dumps(row, sort_keys=True) + "\n" for row in rows), encoding="utf-8")


def write_user_manifest(
    target: Path,
    *,
    vendor: str,
    library: str,
    version: str,
    pages: list[NormalizedPage],
    source_url: str,
) -> None:
    oz_dir = target / ".oz"
    oz_dir.mkdir(parents=True, exist_ok=True)
    manifest = {
        "schema_version": 1,
        "vendor": vendor,
        "library": library,
        "version": version,
        "source_url": source_url,
        "document_count": len(pages),
        "sources": [
            {
                "path": page.path,
                "source_url": page.source_url,
                "canonical_url": page.canonical_url or page.source_url,
                "source_type": (page.source_metadata or {}).get("source_type") or page.source_type,
                "metadata_json": page.source_metadata or {},
            }
            for page in pages
        ],
    }
    (oz_dir / "manifest.json").write_text(json.dumps(manifest, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def canonical_source_key(page: NormalizedPage) -> str:
    value = page.canonical_url or page.source_url or page.path or page.title
    text = str(value).rstrip("/")
    if preserves_virtual_source_fragment(text, page.source_type, page.source_metadata):
        return text
    return text.split("#", 1)[0].rstrip("/")


def preserves_virtual_source_fragment(url: str, fallback_source_type: str | None, metadata: dict[str, Any] | None) -> bool:
    parsed = urlparse(url)
    if not parsed.fragment:
        return False
    source_type = str((metadata or {}).get("source_type") or fallback_source_type or "").lower()
    if source_type in {"llms_txt", "openapi"}:
        return True
    return bool(re.search(r"(?:^|/)(?:llms|llms-full)\.txt$", parsed.path.lower()))


def page_content_key(markdown: str) -> str:
    return hashlib.sha256(re.sub(r"\s+", " ", markdown.strip()).encode("utf-8")).hexdigest()
