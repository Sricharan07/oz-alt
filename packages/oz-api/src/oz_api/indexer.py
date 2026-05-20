from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Any
from urllib.parse import urldefrag

from oz_api.context_cards import build_context_snippets, build_source_sections
from oz_api.embeddings import embedding_dimensions as configured_embedding_dimensions
from oz_api.embedding_jobs import EmbeddingEnsureResult, ensure_version_embeddings
from oz_api.observability import observe_duration
from oz_api.retrieval import RetrievalContext, postgres_connection, vector_literal
from oz_api.storage import RegistryStorage
from oz_api.trust import first_source_url, trust_score_for_entry
from oz_api.versions import compare_versions
from oz_crawler.content_types import block_content_type, classify_content_type
from oz_crawler.normalize import clean_markdown
from oz_crawler.token_counting import token_count


@dataclass(frozen=True)
class IndexStats:
    libraries: int = 0
    versions: int = 0
    chunks: int = 0
    embedded_chunks: int = 0
    pending_embedding_chunks: int = 0

    def as_dict(self) -> dict[str, int]:
        return {
            "libraries": self.libraries,
            "versions": self.versions,
            "chunks": self.chunks,
            "embedded_chunks": self.embedded_chunks,
            "pending_embedding_chunks": self.pending_embedding_chunks,
        }


def index_registry(repo_root: Path, *, dry_run: bool = False) -> IndexStats:
    storage = RegistryStorage.from_env(repo_root)
    catalog = storage.load_catalog()
    stats = count_registry(storage, catalog)
    if dry_run:
        return stats

    ctx = RetrievalContext.from_env(storage)
    connection = postgres_connection(ctx.database_url)
    if connection is None:
        raise RuntimeError("No database connection configured. Set OZ_DATABASE_URL or DATABASE_URL.")
    with connection:
        writer = PostgresWriter(connection)
        results = write_catalog_and_chunks(writer, storage, catalog)
        embedded_chunks = writer.count_embedded_chunks()
        if require_embeddings() and embedded_chunks < stats.chunks:
            raise RuntimeError(f"embedding requirement failed: {embedded_chunks}/{stats.chunks} chunks have embeddings")
        return IndexStats(
            libraries=stats.libraries,
            versions=stats.versions,
            chunks=stats.chunks,
            embedded_chunks=embedded_chunks,
            pending_embedding_chunks=sum(result.pending_chunks for result in results if not result.complete),
        )


class VersionOrder:
    def __init__(self, version: str) -> None:
        self.version = version

    def __lt__(self, other: object) -> bool:
        if not isinstance(other, VersionOrder):
            return NotImplemented
        return compare_versions(self.version, other.version) < 0


def count_registry(storage: RegistryStorage, catalog: list[dict[str, Any]]) -> IndexStats:
    chunks = 0
    embedded = 0
    for entry in catalog:
        for row in chunk_rows(storage, entry):
            chunks += 1
            if valid_embedding(row.get("embedding")):
                embedded += 1
    return IndexStats(libraries=len(catalog), versions=len(catalog), chunks=chunks, embedded_chunks=embedded)


def write_catalog_and_chunks(
    writer: "IndexWriter",
    storage: RegistryStorage,
    catalog: list[dict[str, Any]],
) -> list[EmbeddingEnsureResult]:
    embedding_results: list[EmbeddingEnsureResult] = []
    for entry in catalog:
        vendor_id = writer.upsert_vendor(str(entry["vendor"]))
        library_id = writer.upsert_library(vendor_id, entry)
        version_id = writer.upsert_version(library_id, entry)
        writer.upsert_ref(library_id, version_id, str(entry.get("ref_sha") or "unknown"))
        writer.upsert_trust_score(library_id, trust_score_for_entry(entry))

        fixture = fixture_path(storage, entry)
        line_cache: dict[str, str] = {}
        current_chunk_shas: list[str] = []
        rows = chunk_rows(storage, entry)
        source_ids: dict[str, int] = {}
        current_source_keys: list[str] = []
        for source in source_document_rows(fixture, rows):
            source_id = writer.upsert_source_document(version_id, source)
            key = str(source["source_document_key"])
            source_ids[key] = source_id
            current_source_keys.append(key)
        writer.delete_stale_source_documents(version_id, current_source_keys)
        for row in rows:
            chunk_sha = chunk_sha_for_row(entry, row)
            current_chunk_shas.append(chunk_sha)
            start_line, end_line = row_line_span(row) or line_span(fixture, row, line_cache)
            existing_embedding = row.get("embedding")
            embedding = [float(value) for value in existing_embedding] if valid_embedding(existing_embedding) else None
            writer.upsert_chunk(
                version_id,
                path=str(row.get("path") or "README.md"),
                start_line=start_line,
                end_line=end_line,
                source_url=str(row.get("source_url") or ""),
                source_document_id=source_ids.get(source_document_key_for_row(row)),
                ordinal=int(row.get("ordinal") or 1),
                chunk_key=str(row.get("chunk_key") or row.get("id") or ""),
                parent_chunk_key=nullable_string(row.get("parent_chunk_key")),
                chunk_sha=chunk_sha,
                content_sha=content_sha_for_row(row),
                heading_path=list_of_strings(row.get("heading_path")),
                symbols=list_of_strings(row.get("symbols")),
                content_type=str(row.get("content_type") or "prose"),
                quality_score=float(row.get("quality_score") or 1.0),
                token_count=int(row.get("token_count") or token_count(str(row.get("text") or ""))),
                source_anchor=nullable_string(row.get("source_anchor")),
                metadata_json=row.get("metadata_json") if isinstance(row.get("metadata_json"), dict) else {},
                embedding_model=nullable_string(row.get("embedding_model")) if embedding else None,
                embedding_dimensions=(int(row.get("embedding_dimensions") or 0) or None) if embedding else None,
                content=str(row.get("text") or ""),
                embedding=embedding,
            )
        writer.delete_stale_chunks(version_id, current_chunk_shas)
        writer.resolve_parent_chunks(version_id)
        writer.rebuild_context_index(version_id)
        result = writer.ensure_embeddings(version_id, crawler_job_id=optional_int(entry.get("crawler_job_id")))
        embedding_results.append(result)
        if result.complete:
            writer.resolve_parent_chunks(version_id)
            writer.rebuild_dedupe_clusters(version_id)
            writer.rebuild_context_index(version_id)
            writer.set_benchmark_score(version_id, benchmark_score_for_fixture(fixture, rows))
    return embedding_results


def chunk_rows(storage: RegistryStorage, entry: dict[str, Any]) -> list[dict[str, Any]]:
    chunks_path = fixture_path(storage, entry) / "_chunks.jsonl"
    fixture = fixture_path(storage, entry)
    rows: list[dict[str, Any]] = []
    seen_chunk_shas: set[str] = set()
    if chunks_path.exists():
        for line in chunks_path.read_text(encoding="utf-8").splitlines():
            if line.strip():
                row = json.loads(line)
                append_unique_chunk_row(entry, row, rows, seen_chunk_shas)
    for row in symbol_chunk_rows(fixture):
        append_unique_chunk_row(entry, row, rows, seen_chunk_shas)
    rows = add_parent_chunks(entry, fixture, rows)
    return [enrich_chunk_row(entry, row) for row in rows]


def append_unique_chunk_row(
    entry: dict[str, Any],
    row: dict[str, Any],
    rows: list[dict[str, Any]],
    seen_chunk_shas: set[str],
) -> None:
    if not is_indexable_chunk(row):
        return
    chunk_sha = chunk_sha_for_row(entry, row)
    if chunk_sha in seen_chunk_shas:
        return
    seen_chunk_shas.add(chunk_sha)
    rows.append(row)


def enrich_chunk_row(entry: dict[str, Any], row: dict[str, Any]) -> dict[str, Any]:
    enriched = dict(row)
    path = str(enriched.get("path") or "README.md")
    text = limit_to_token_budget(clean_markdown(str(enriched.get("text") or "")).strip(), index_chunk_token_limit())
    source_url = str(enriched.get("source_url") or "")
    enriched["path"] = path
    enriched["source_url"] = source_url
    enriched["text"] = text
    enriched["chunk_key"] = str(enriched.get("chunk_key") or enriched.get("id") or f"{path}#{enriched.get('ordinal') or 1}")
    enriched["content_type"] = canonical_content_type(path, source_url, text, str(enriched.get("content_type") or ""))
    enriched["content_sha"] = content_sha_for_row(enriched)
    enriched["token_count"] = token_count(text)
    enriched["source_anchor"] = nullable_string(enriched.get("source_anchor")) or source_anchor_for_row(entry, enriched)
    enriched["source_document_key"] = source_document_key_for_row(enriched)
    enriched["metadata_json"] = enriched.get("metadata_json") if isinstance(enriched.get("metadata_json"), dict) else {}
    return enriched


def source_document_rows(fixture: Path, rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    source_path = fixture / "_sources.jsonl"
    output: list[dict[str, Any]] = []
    seen: set[str] = set()
    if source_path.exists():
        for line in source_path.read_text(encoding="utf-8").splitlines():
            if not line.strip():
                continue
            source = json.loads(line)
            key = source_document_key_for_row(source)
            if not key or key in seen:
                continue
            source["source_document_key"] = key
            output.append(source)
            seen.add(key)
    for row in rows:
        key = source_document_key_for_row(row)
        if not key or key in seen:
            continue
        output.append(
            {
                "source_document_key": key,
                "source_kind": str(row.get("source_kind") or "website"),
                "canonical_url": str(row.get("canonical_url") or row.get("source_url") or ""),
                "source_url": str(row.get("source_url") or ""),
                "path": str(row.get("path") or ""),
                "title": first_heading(str(row.get("text") or "")) or Path(str(row.get("path") or "")).stem,
                "source_priority": int(row.get("source_priority") or 50),
                "discovered_from": nullable_string(row.get("discovered_from")),
                "metadata_json": row.get("metadata_json") if isinstance(row.get("metadata_json"), dict) else {},
            }
        )
        seen.add(key)
    return output


def source_document_key_for_row(row: dict[str, Any]) -> str:
    value = row.get("source_document_key") or row.get("canonical_url") or row.get("source_url") or row.get("path") or ""
    return str(value).split("#", 1)[0].rstrip("/")


def first_heading(text: str) -> str:
    for line in text.splitlines():
        match = re.match(r"^#\s+(.+)$", line.strip())
        if match:
            return match.group(1).strip()
    return ""


def canonical_content_type(path: str, source_url: str, text: str, existing: str) -> str:
    normalized = existing.strip().lower()
    if path.startswith("_symbols/"):
        return "api_reference"
    inferred_page = classify_content_type(source_url or path, text)
    inferred_block = block_content_type(source_url or path, text, inferred_page)
    if normalized in {"code_example", "config", "cli", "error_ref"}:
        return normalized
    if inferred_block in {"api_reference", "code_example", "config", "cli", "error_ref"}:
        return inferred_block
    if normalized == "api_reference":
        return normalized
    if normalized in {"prose", "guide"}:
        return "prose" if inferred_page == "prose" else inferred_page
    return inferred_page if inferred_page != "index" else "prose"


def source_anchor_for_row(entry: dict[str, Any], row: dict[str, Any]) -> str:
    path = str(row.get("path") or "README.md")
    source_url = str(row.get("source_url") or "").strip()
    if source_url:
        base, _ = urldefrag(source_url)
    else:
        base = f"oz://{entry.get('vendor')}/{entry.get('library')}/{entry.get('version')}/{path}"
    headings = list_of_strings(row.get("heading_path"))
    label = headings[-1] if headings else Path(path).stem
    ordinal = int(row.get("ordinal") or 1)
    return f"{base}#{slugify(label)}-_snippet_{ordinal}"


def add_parent_chunks(entry: dict[str, Any], fixture: Path, rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    output = list(rows)
    existing_keys = {str(row.get("chunk_key") or "") for row in output}
    paths_with_explicit_parents = {str(row.get("path") or "") for row in output if row.get("parent_chunk_key")}
    groups: dict[str, list[dict[str, Any]]] = {}
    for row in output:
        path = str(row.get("path") or "README.md")
        if path in paths_with_explicit_parents:
            continue
        if row.get("content_type") == "api_reference" and not path.startswith("_symbols/") and int(row.get("ordinal") or 1) > 0:
            groups.setdefault(path, []).append(row)
    for path, children in sorted(groups.items()):
        meaningful_children = unique_meaningful_children(children)
        if len(meaningful_children) < 2:
            continue
        parent_key = f"{path}#parent-api-reference"
        for child in meaningful_children:
            if str(child.get("chunk_key") or "") != parent_key:
                child["parent_chunk_key"] = child.get("parent_chunk_key") or parent_key
        if parent_key in existing_keys:
            continue
        parent = parent_chunk_row(entry, fixture, path, parent_key, meaningful_children)
        existing_keys.add(parent_key)
        output.append(parent)
    return output


def unique_meaningful_children(children: list[dict[str, Any]]) -> list[dict[str, Any]]:
    output: list[dict[str, Any]] = []
    seen: set[str] = set()
    for child in children:
        text = str(child.get("text") or "").strip()
        if token_count(text) < 12:
            continue
        key = normalized_content_hash(text)
        if key in seen:
            continue
        seen.add(key)
        output.append(child)
    return output


def parent_chunk_row(
    entry: dict[str, Any],
    fixture: Path,
    path: str,
    parent_key: str,
    children: list[dict[str, Any]],
) -> dict[str, Any]:
    content = limit_to_token_budget(parent_content(fixture, path, children), index_chunk_token_limit())
    source_url = first_non_empty(str(row.get("source_url") or "") for row in children)
    headings = list_of_strings(children[0].get("heading_path")) if children else [Path(path).stem]
    symbols = sorted({symbol for row in children for symbol in list_of_strings(row.get("symbols"))})
    end_lines = [int(row.get("end_line") or 0) for row in children if int(row.get("end_line") or 0) > 0]
    row = {
        "id": parent_key,
        "path": path,
        "source_url": source_url,
        "ordinal": 0,
        "chunk_key": parent_key,
        "start_line": min(int(row.get("start_line") or 1) for row in children) if children else 1,
        "end_line": max(end_lines) if end_lines else None,
        "heading_path": headings,
        "symbols": symbols,
        "content_type": "api_reference",
        "quality_score": max(float(row.get("quality_score") or 1.0) for row in children) if children else 1.0,
        "token_count": token_count(content),
        "text": content,
    }
    row["source_anchor"] = source_anchor_for_row(entry, row)
    return row


def parent_content(fixture: Path, path: str, children: list[dict[str, Any]]) -> str:
    joined = "\n\n".join(str(row.get("text") or "").strip() for row in children if str(row.get("text") or "").strip())
    return joined


def index_chunk_token_limit() -> int:
    try:
        return max(100, int(os.environ.get("OZ_MAX_CHUNK_TOKENS", "1200")))
    except ValueError:
        return 1200


def limit_to_token_budget(text: str, max_tokens: int) -> str:
    text = text.strip()
    if token_count(text) <= max_tokens:
        return text
    low = 0
    high = len(text)
    best = ""
    while low <= high:
        mid = (low + high) // 2
        candidate = text[:mid].rstrip()
        if "\n" in candidate:
            candidate = candidate.rsplit("\n", 1)[0].rstrip() or text[:mid].rstrip()
        if token_count(candidate) <= max_tokens:
            best = candidate
            low = mid + 1
        else:
            high = mid - 1
    return best.strip() or text[: max(1, max_tokens)].strip()


def first_non_empty(values: Any) -> str:
    for value in values:
        text = str(value or "").strip()
        if text:
            return text
    return ""


def symbol_chunk_rows(fixture: Path) -> list[dict[str, Any]]:
    symbols_dir = fixture / "_symbols"
    if not symbols_dir.exists():
        return []
    rows: list[dict[str, Any]] = []
    for path in sorted(symbols_dir.glob("*.md")):
        text = path.read_text(encoding="utf-8", errors="replace").strip()
        if not text:
            continue
        symbol = path.stem
        relative = path.relative_to(fixture).as_posix()
        rows.append(
            {
                "id": f"symbol-{symbol}",
                "path": relative,
                "source_url": symbol_source_url(text),
                "source_anchor": symbol_source_anchor(text, symbol),
                "ordinal": 1,
                "chunk_key": f"symbol-{symbol}",
                "start_line": 1,
                "end_line": len(text.splitlines()),
                "heading_path": [symbol],
                "symbols": [symbol],
                "content_type": "api_reference",
                "quality_score": 1.0,
                "token_count": token_count(text),
                "text": text,
            }
        )
    return rows


def symbol_source_url(text: str) -> str:
    for line in text.splitlines():
        if line.startswith("**Source:**"):
            return line.split("**Source:**", 1)[1].strip()
    return ""


def symbol_source_anchor(text: str, symbol: str) -> str:
    source_url = symbol_source_url(text)
    if not source_url:
        return ""
    return f"{source_url}#_symbol_{symbol}"


def is_indexable_chunk(row: dict[str, Any]) -> bool:
    text = str(row.get("text") or "")
    return bool(text.strip()) and "\x00" not in text


def fixture_path(storage: RegistryStorage, entry: dict[str, Any]) -> Path:
    fixture = entry.get("fixture_path")
    if fixture:
        return storage.repo_root / str(fixture)
    return storage.fixtures_root / str(entry["vendor"]) / str(entry["library"]) / str(entry["version"])


def line_span(fixture: Path, row: dict[str, Any], cache: dict[str, str]) -> tuple[int, int | None]:
    path = str(row.get("path") or "README.md")
    text = str(row.get("text") or "")
    if path not in cache:
        source_path = fixture / path
        cache[path] = source_path.read_text(encoding="utf-8") if source_path.exists() else ""

    source = cache[path]
    if not source or not text:
        return 1, None

    index = source.find(text)
    if index < 0:
        index = source.find(text[:160])
    if index < 0:
        return 1, None

    start = source[:index].count("\n") + 1
    end = start + text.count("\n")
    return start, end


def row_line_span(row: dict[str, Any]) -> tuple[int, int | None] | None:
    start = row.get("start_line")
    if not isinstance(start, int) or start < 1:
        return None
    end = row.get("end_line")
    return start, end if isinstance(end, int) and end >= start else None


def list_of_strings(value: Any) -> list[str]:
    if not isinstance(value, list):
        return []
    return [str(item) for item in value if str(item).strip()]


def merge_metadata(*values: Any) -> dict[str, Any]:
    merged: dict[str, Any] = {}
    for value in values:
        if isinstance(value, dict):
            merged.update(value)
    return merged


def valid_embedding(value: Any) -> bool:
    return (
        isinstance(value, list)
        and len(value) == configured_embedding_dimensions()
        and all(isinstance(item, (int, float)) for item in value)
    )


def nullable_string(value: Any) -> str | None:
    text = str(value or "").strip()
    return text or None


def optional_int(value: Any) -> int | None:
    if value is None or value == "":
        return None
    try:
        return int(value)
    except (TypeError, ValueError):
        return None


def slugify(value: str) -> str:
    slug = re.sub(r"[^A-Za-z0-9]+", "-", value.lower()).strip("-")
    return slug[:120] or "snippet"


def benchmark_score_for_fixture(fixture: Path, rows: list[dict[str, Any]]) -> float:
    quality = quality_report(fixture)
    if quality:
        return benchmark_from_quality(quality, rows)
    content_types = {str(row.get("content_type") or "") for row in rows}
    score = 0.45
    score += min(len(rows), 80) / 80 * 0.25
    score += min(len([row for row in rows if row.get("content_type") == "api_reference"]), 20) / 20 * 0.12
    score += min(len(content_types), 6) / 6 * 0.12
    score += 0.06 if any(str(row.get("path") or "").startswith("_symbols/") for row in rows) else 0
    return clamp_score(score)


def quality_report(fixture: Path) -> dict[str, Any]:
    path = fixture / "_quality.json"
    if not path.exists():
        return {}
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return {}
    return data if isinstance(data, dict) else {}


def benchmark_from_quality(quality: dict[str, Any], rows: list[dict[str, Any]]) -> float:
    metrics = quality.get("metrics") if isinstance(quality.get("metrics"), dict) else {}
    score = 0.35
    score += 0.25 if quality.get("passed") else 0
    score += min(float(metrics.get("required_topic_coverage") or metrics.get("topic_coverage") or 0), 1) * 0.15
    score += min(float(metrics.get("required_symbol_coverage") or metrics.get("symbol_coverage") or 0), 1) * 0.15
    score += min(float(metrics.get("accepted_pages") or len(rows)), 80) / 80 * 0.06
    score += min(len({str(row.get("content_type") or "") for row in rows}), 6) / 6 * 0.04
    return clamp_score(score)


def clamp_score(value: float) -> float:
    return round(max(0.0, min(float(value), 1.0)), 4)


def require_embeddings() -> bool:
    return os.environ.get("OZ_REQUIRE_EMBEDDINGS", "").strip().lower() in {"1", "true", "yes"}


def env_int(name: str, default: int) -> int:
    try:
        return int(os.environ.get(name, str(default)))
    except ValueError:
        return default


def chunk_sha_for_row(entry: dict[str, Any], row: dict[str, Any]) -> str:
    existing = str(row.get("chunk_sha") or "")
    if len(existing) == 64 and all(char in "0123456789abcdef" for char in existing.lower()):
        return existing
    payload = "\0".join(
        [
            str(entry.get("vendor") or ""),
            str(entry.get("library") or ""),
            str(entry.get("version") or ""),
            str(row.get("path") or "README.md"),
            str(row.get("ordinal") or 1),
            str(row.get("text") or ""),
        ]
    )
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()


def content_sha_for_row(row: dict[str, Any]) -> str:
    existing = str(row.get("content_sha") or "")
    if len(existing) == 64 and all(char in "0123456789abcdef" for char in existing.lower()):
        return existing
    return normalized_content_hash(str(row.get("text") or row.get("content") or ""))


def normalized_content_hash(text: str) -> str:
    normalized = re.sub(r"\s+", " ", text.strip())
    return hashlib.sha256(normalized.encode("utf-8")).hexdigest()


class IndexWriter:
    def upsert_vendor(self, vendor: str) -> int:
        raise NotImplementedError

    def upsert_library(self, vendor_id: int, entry: dict[str, Any]) -> int:
        raise NotImplementedError

    def upsert_version(self, library_id: int, entry: dict[str, Any]) -> int:
        raise NotImplementedError

    def upsert_ref(self, library_id: int, version_id: int, ref_sha: str) -> None:
        raise NotImplementedError

    def delete_stale_chunks(self, version_id: int, current_chunk_shas: list[str]) -> None:
        raise NotImplementedError

    def upsert_source_document(self, version_id: int, source: dict[str, Any]) -> int:
        raise NotImplementedError

    def delete_stale_source_documents(self, version_id: int, current_source_keys: list[str]) -> None:
        raise NotImplementedError

    def count_embedded_chunks(self) -> int:
        raise NotImplementedError

    def upsert_trust_score(self, library_id: int, score: tuple[float, dict[str, Any]]) -> None:
        raise NotImplementedError

    def resolve_parent_chunks(self, version_id: int) -> None:
        raise NotImplementedError

    def rebuild_dedupe_clusters(self, version_id: int) -> None:
        raise NotImplementedError

    def rebuild_context_index(self, version_id: int) -> None:
        raise NotImplementedError

    def set_benchmark_score(self, version_id: int, score: float) -> None:
        raise NotImplementedError

    def ensure_embeddings(self, version_id: int, *, crawler_job_id: int | None) -> EmbeddingEnsureResult:
        raise NotImplementedError

    def upsert_chunk(
        self,
        version_id: int,
        *,
        path: str,
        start_line: int,
        end_line: int | None,
        source_url: str,
        source_document_id: int | None,
        ordinal: int,
        chunk_key: str | None,
        parent_chunk_key: str | None,
        chunk_sha: str,
        content_sha: str,
        heading_path: list[str],
        symbols: list[str],
        content_type: str,
        quality_score: float,
        token_count: int,
        source_anchor: str | None,
        metadata_json: dict[str, Any],
        embedding_model: str | None,
        embedding_dimensions: int | None,
        content: str,
        embedding: list[float] | None,
    ) -> None:
        raise NotImplementedError


class PostgresWriter(IndexWriter):
    def __init__(self, connection: Any) -> None:
        self.connection = connection

    def scalar(self, sql: str, params: tuple[Any, ...]) -> int:
        with observe_duration("oz_db_query_duration_seconds", {"operation": "indexer_scalar", "mode": sql_operation(sql)}):
            with self.connection.cursor() as cursor:
                cursor.execute(sql, params)
                row = cursor.fetchone()
        return int(row[0])

    def execute(self, sql: str, params: tuple[Any, ...]) -> None:
        with observe_duration("oz_db_query_duration_seconds", {"operation": "indexer_execute", "mode": sql_operation(sql)}):
            with self.connection.cursor() as cursor:
                cursor.execute(sql, params)

    def upsert_vendor(self, vendor: str) -> int:
        return self.scalar(
            """
            insert into vendors(name)
            values (%s)
            on conflict (name) do update set name = excluded.name
            returning id
            """,
            (vendor,),
        )

    def upsert_library(self, vendor_id: int, entry: dict[str, Any]) -> int:
        return self.scalar(
            """
            insert into libraries(vendor_id, name, description, source_url, aliases)
            values (%s, %s, %s, %s, %s::jsonb)
            on conflict (vendor_id, name) do update
              set description = excluded.description,
                  source_url = excluded.source_url,
                  aliases = excluded.aliases,
                  updated_at = now()
            returning id
            """,
            (
                vendor_id,
                str(entry["library"]),
                str(entry.get("description") or ""),
                first_source_url(entry),
                json.dumps(list_of_strings(entry.get("aliases")), sort_keys=True),
            ),
        )

    def upsert_version(self, library_id: int, entry: dict[str, Any]) -> int:
        return self.scalar(
            """
            insert into library_versions(library_id, version, ref_sha, pack_key, indexed_at, last_crawled_at, archived_at)
            values (%s, %s, %s, %s, nullif(%s, '')::timestamptz, now(), null)
            on conflict (library_id, version) do update
              set ref_sha = excluded.ref_sha,
                  pack_key = excluded.pack_key,
                  indexed_at = excluded.indexed_at,
                  last_crawled_at = now(),
                  archived_at = null
            returning id
            """,
            (
                library_id,
                str(entry["version"]),
                str(entry.get("ref_sha") or "unknown"),
                str(entry.get("pack_path") or ""),
                str(entry.get("indexed_at") or ""),
            ),
        )

    def upsert_ref(self, library_id: int, version_id: int, ref_sha: str) -> None:
        self.execute(
            """
            insert into refs(library_id, channel, version_id, ref_sha)
            values (%s, 'latest', %s, %s)
            on conflict (library_id, channel) do update
              set version_id = excluded.version_id,
                  ref_sha = excluded.ref_sha,
                  updated_at = now()
            """,
            (library_id, version_id, ref_sha),
        )
        self.archive_excess_versions(library_id, keep=int(os.environ.get("OZ_MAX_VERSIONS_PER_LIBRARY", "20")))

    def archive_excess_versions(self, library_id: int, *, keep: int) -> None:
        if keep <= 0:
            return
        with self.connection.cursor() as cursor:
            cursor.execute(
                "select id, version from library_versions where library_id = %s",
                (library_id,),
            )
            rows = [{"id": row[0], "version": row[1]} for row in cursor.fetchall()]
            rows.sort(key=lambda row: VersionOrder(str(row["version"])), reverse=True)
            for rank, row in enumerate(rows, start=1):
                cursor.execute(
                    """
                    update library_versions
                    set archived_at = case when %s > %s then coalesce(archived_at, now()) else null end,
                        version_rank = %s
                    where id = %s
                    """,
                    (rank, keep, rank, row["id"]),
                )

    def delete_stale_chunks(self, version_id: int, current_chunk_shas: list[str]) -> None:
        chunk_shas = sorted(set(current_chunk_shas))
        if not chunk_shas:
            self.execute("delete from chunks where version_id = %s", (version_id,))
            return
        placeholders = ", ".join(["%s"] * len(chunk_shas))
        self.execute(
            f"delete from chunks where version_id = %s and chunk_sha not in ({placeholders})",
            (version_id, *chunk_shas),
        )

    def upsert_source_document(self, version_id: int, source: dict[str, Any]) -> int:
        return self.scalar(
            """
            insert into source_documents(
              version_id, source_document_key, source_kind, canonical_url, source_url,
              path, title, source_priority, discovered_from, metadata_json, fetched_at
            )
            values (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s::jsonb, now())
            on conflict (version_id, source_document_key) do update
              set source_kind = excluded.source_kind,
                  canonical_url = excluded.canonical_url,
                  source_url = excluded.source_url,
                  path = excluded.path,
                  title = excluded.title,
                  source_priority = excluded.source_priority,
                  discovered_from = excluded.discovered_from,
                  metadata_json = excluded.metadata_json,
                  fetched_at = now()
            returning id
            """,
            (
                version_id,
                str(source["source_document_key"]),
                str(source.get("source_kind") or "website"),
                nullable_string(source.get("canonical_url")),
                nullable_string(source.get("source_url")),
                nullable_string(source.get("path")),
                nullable_string(source.get("title")),
                int(source.get("source_priority") or 50),
                nullable_string(source.get("discovered_from")),
                json.dumps(source.get("metadata_json") if isinstance(source.get("metadata_json"), dict) else {}, sort_keys=True),
            ),
        )

    def delete_stale_source_documents(self, version_id: int, current_source_keys: list[str]) -> None:
        keys = sorted(set(current_source_keys))
        if not keys:
            self.execute("delete from source_documents where version_id = %s", (version_id,))
            return
        placeholders = ", ".join(["%s"] * len(keys))
        self.execute(
            f"delete from source_documents where version_id = %s and source_document_key not in ({placeholders})",
            (version_id, *keys),
        )

    def count_embedded_chunks(self) -> int:
        with self.connection.cursor() as cursor:
            cursor.execute("select count(*) from chunks where embedding is not null")
            return int(cursor.fetchone()[0])

    def upsert_trust_score(self, library_id: int, score: tuple[float, dict[str, Any]]) -> None:
        value, signals = score
        self.execute(
            """
            insert into trust_scores(library_id, value, signals_json, calculated_at)
            values (%s, %s, %s::jsonb, now())
            on conflict (library_id) do update
              set value = excluded.value,
                  signals_json = excluded.signals_json,
                  calculated_at = now()
            """,
            (library_id, value, json.dumps(signals, sort_keys=True)),
        )

    def resolve_parent_chunks(self, version_id: int) -> None:
        self.execute(
            """
            update chunks child
            set parent_chunk_id = parent.id
            from chunks parent
            where child.version_id = %s
              and parent.version_id = child.version_id
              and child.parent_chunk_key is not null
              and parent.chunk_key = child.parent_chunk_key
              and parent.id <> child.id
            """,
            (version_id,),
        )

    def rebuild_dedupe_clusters(self, version_id: int) -> None:
        chunk_count = self.scalar_int("select count(*) from chunks where version_id = %s", (version_id,))
        self.execute("delete from dedupe_clusters where version_id = %s", (version_id,))
        self.execute(
            """
            update chunks
            set dedupe_cluster_id = null,
                dedupe_canonical = true
            where version_id = %s
            """,
            (version_id,),
        )
        self.execute(
            """
            with grouped as (
              select version_id,
                     md5(regexp_replace(lower(content), '\\s+', ' ', 'g')) as cluster_key,
                     array_agg(
                       id order by
                         case
                           when path like '_symbols/%%' then 0
                           when path like 'api-reference/%%' then 1
                           when path like 'guides/%%' then 2
                           when path like 'examples/%%' then 3
                           else 9
                         end asc,
                         quality_score desc,
                         token_count desc,
                         id asc
                     ) as ids,
                     count(*) as member_count
              from chunks
              where version_id = %s
              group by version_id, md5(regexp_replace(lower(content), '\\s+', ' ', 'g'))
              having count(*) > 1
            ),
            inserted as (
              insert into dedupe_clusters(version_id, cluster_key, canonical_chunk_id, member_count, method)
              select version_id, cluster_key, ids[1], member_count, 'normalized_exact'
              from grouped
              returning id, canonical_chunk_id, cluster_key
            )
            update chunks c
            set dedupe_cluster_id = inserted.id,
                dedupe_canonical = c.id = inserted.canonical_chunk_id
            from inserted
            where c.version_id = %s
              and md5(regexp_replace(lower(c.content), '\\s+', ' ', 'g')) = inserted.cluster_key
            """,
            (version_id, version_id),
        )
        max_vector_chunks = env_int("OZ_DEDUPE_VECTOR_MAX_CHUNKS", 5000)
        if max_vector_chunks > 0 and chunk_count > max_vector_chunks:
            return
        self.execute(
            """
            with pairs as (
              select c.id as left_id,
                     n.id as right_id,
                     case
                       when (
                         case
                           when c.path like '_symbols/%%' then 0
                           when c.path like 'api-reference/%%' then 1
                           when c.path like 'guides/%%' then 2
                           when c.path like 'examples/%%' then 3
                           else 9
                         end
                       ) < (
                         case
                           when n.path like '_symbols/%%' then 0
                           when n.path like 'api-reference/%%' then 1
                           when n.path like 'guides/%%' then 2
                           when n.path like 'examples/%%' then 3
                           else 9
                         end
                       ) then c.id
                       when (
                         case
                           when c.path like '_symbols/%%' then 0
                           when c.path like 'api-reference/%%' then 1
                           when c.path like 'guides/%%' then 2
                           when c.path like 'examples/%%' then 3
                           else 9
                         end
                       ) > (
                         case
                           when n.path like '_symbols/%%' then 0
                           when n.path like 'api-reference/%%' then 1
                           when n.path like 'guides/%%' then 2
                           when n.path like 'examples/%%' then 3
                           else 9
                         end
                       ) then n.id
                       when c.quality_score > n.quality_score then c.id
                       when c.quality_score < n.quality_score then n.id
                       when c.token_count >= n.token_count then c.id
                       else n.id
                     end as canonical_id
              from chunks c
              join lateral (
                select id, path, quality_score, token_count, embedding
                from chunks candidate
                where candidate.version_id = c.version_id
                  and candidate.id <> c.id
                  and candidate.embedding is not null
                  and candidate.dedupe_cluster_id is null
                order by candidate.embedding <=> c.embedding
                limit 5
              ) n on true
              where c.version_id = %s
                and c.embedding is not null
                and c.dedupe_cluster_id is null
                and c.id < n.id
                and (c.embedding <=> n.embedding) <= 0.05
            ),
            clusters as (
              select canonical_id,
                     'vector:' || canonical_id::text as cluster_key,
                     array_agg(left_id) || array_agg(right_id) as ids
              from pairs
              group by canonical_id
            ),
            inserted as (
              insert into dedupe_clusters(version_id, cluster_key, canonical_chunk_id, member_count, method)
              select %s, cluster_key, canonical_id, cardinality(ids), 'vector_cosine_0.95'
              from clusters
              on conflict (version_id, cluster_key) do update
                set canonical_chunk_id = excluded.canonical_chunk_id,
                    member_count = excluded.member_count
              returning id, canonical_chunk_id, cluster_key
            )
            update chunks c
            set dedupe_cluster_id = inserted.id,
                dedupe_canonical = c.id = inserted.canonical_chunk_id
            from inserted
            where c.version_id = %s
              and c.dedupe_cluster_id is null
              and (
                c.id = inserted.canonical_chunk_id
                or exists (
                  select 1
                  from pairs
                  where pairs.canonical_id = inserted.canonical_chunk_id
                    and c.id in (pairs.left_id, pairs.right_id)
                )
              )
            """,
            (version_id, version_id, version_id),
        )

    def rebuild_context_index(self, version_id: int) -> None:
        rows = self.context_chunk_rows(version_id)
        sections = build_source_sections(rows)
        snippets = build_context_snippets(rows, self.replace_source_sections(version_id, sections))
        self.replace_context_snippets(version_id, snippets)

    def context_chunk_rows(self, version_id: int) -> list[dict[str, Any]]:
        with self.connection.cursor() as cursor:
            cursor.execute(
                """
                select c.id, c.source_document_id, c.path, c.start_line, c.end_line, c.source_url,
                       c.ordinal, c.chunk_key, c.parent_chunk_key, c.chunk_sha, c.content_sha,
                       c.heading_path, c.symbols, c.content_type, c.quality_score, c.token_count,
                       c.source_anchor, c.content, c.dedupe_canonical,
                       coalesce(sd.title, '') as source_title,
                       coalesce(sd.source_kind, '') as source_kind,
                       coalesce(sd.source_priority, 50) as source_priority,
                       coalesce(c.metadata_json, '{}'::jsonb) as chunk_metadata_json,
                       coalesce(sd.metadata_json, '{}'::jsonb) as source_metadata_json
                from chunks c
                left join source_documents sd on sd.id = c.source_document_id
                where c.version_id = %s
                order by c.path asc, c.start_line asc, c.ordinal asc, c.id asc
                """,
                (version_id,),
            )
            rows = cursor.fetchall()
        output: list[dict[str, Any]] = []
        for row in rows:
            output.append(
                {
                    "id": row[0],
                    "source_document_id": row[1],
                    "path": row[2],
                    "start_line": row[3],
                    "end_line": row[4],
                    "source_url": row[5],
                    "ordinal": row[6],
                    "chunk_key": row[7],
                    "parent_chunk_key": row[8],
                    "chunk_sha": row[9],
                    "content_sha": row[10],
                    "heading_path": row[11] or [],
                    "symbols": row[12] or [],
                    "content_type": row[13],
                    "quality_score": row[14],
                    "token_count": row[15],
                    "source_anchor": row[16],
                    "content": row[17],
                    "dedupe_canonical": row[18],
                    "source_title": row[19],
                    "source_kind": row[20],
                    "source_priority": row[21],
                    "metadata_json": merge_metadata(row[22], row[23]),
                }
            )
        return output

    def replace_source_sections(self, version_id: int, sections: list[Any]) -> dict[str, int]:
        self.execute("delete from context_snippets where version_id = %s", (version_id,))
        self.execute("delete from source_sections where version_id = %s", (version_id,))
        section_ids: dict[str, int] = {}
        for section in sections:
            section_id = self.scalar(
                """
                insert into source_sections(
                  version_id, source_document_id, section_key, path, source_url, source_anchor,
                  title, heading_path, content_type, start_line, end_line, content, token_count,
                  quality_score, metadata_json
                )
                values (%s, %s, %s, %s, %s, %s, %s, %s::jsonb, %s, %s, %s, %s, %s, %s, %s::jsonb)
                on conflict (version_id, section_key) do update
                  set source_document_id = excluded.source_document_id,
                      path = excluded.path,
                      source_url = excluded.source_url,
                      source_anchor = excluded.source_anchor,
                      title = excluded.title,
                      heading_path = excluded.heading_path,
                      content_type = excluded.content_type,
                      start_line = excluded.start_line,
                      end_line = excluded.end_line,
                      content = excluded.content,
                      token_count = excluded.token_count,
                      quality_score = excluded.quality_score,
                      metadata_json = excluded.metadata_json
                returning id
                """,
                (
                    version_id,
                    section.source_document_id,
                    section.section_key,
                    section.path,
                    section.source_url,
                    section.source_anchor,
                    section.title,
                    json.dumps(section.heading_path),
                    section.content_type,
                    section.start_line,
                    section.end_line,
                    section.content,
                    section.token_count,
                    section.quality_score,
                    json.dumps(section.metadata_json, sort_keys=True),
                ),
            )
            section_ids[section.section_key] = section_id
        return section_ids

    def replace_context_snippets(self, version_id: int, snippets: list[Any]) -> None:
        self.execute("delete from context_snippets where version_id = %s", (version_id,))
        for snippet in snippets:
            self.execute(
                """
                insert into context_snippets(
                  version_id, source_section_id, primary_chunk_id, snippet_key, path, source_url,
                  source_anchor, title, description, role, applies_to, entities, task_tags,
                  heading_path, symbols, code_language, code, constraints, related_chunk_ids,
                  start_line, end_line, content, token_count, quality_score, metadata_json
                )
                values (
                  %s, %s, %s, %s, %s, %s,
                  %s, %s, %s, %s, %s::jsonb, %s::jsonb, %s::jsonb,
                  %s::jsonb, %s::jsonb, %s, %s, %s::jsonb, %s::jsonb,
                  %s, %s, %s, %s, %s, %s::jsonb
                )
                on conflict (version_id, snippet_key) do update
                  set source_section_id = excluded.source_section_id,
                      primary_chunk_id = excluded.primary_chunk_id,
                      path = excluded.path,
                      source_url = excluded.source_url,
                      source_anchor = excluded.source_anchor,
                      title = excluded.title,
                      description = excluded.description,
                      role = excluded.role,
                      applies_to = excluded.applies_to,
                      entities = excluded.entities,
                      task_tags = excluded.task_tags,
                      heading_path = excluded.heading_path,
                      symbols = excluded.symbols,
                      code_language = excluded.code_language,
                      code = excluded.code,
                      constraints = excluded.constraints,
                      related_chunk_ids = excluded.related_chunk_ids,
                      start_line = excluded.start_line,
                      end_line = excluded.end_line,
                      content = excluded.content,
                      token_count = excluded.token_count,
                      quality_score = excluded.quality_score,
                      metadata_json = excluded.metadata_json
                """,
                (
                    version_id,
                    snippet.source_section_id,
                    snippet.primary_chunk_id,
                    snippet.snippet_key,
                    snippet.path,
                    snippet.source_url,
                    snippet.source_anchor,
                    snippet.title,
                    snippet.description,
                    snippet.role,
                    json.dumps(snippet.applies_to),
                    json.dumps(snippet.entities),
                    json.dumps(snippet.task_tags),
                    json.dumps(snippet.heading_path),
                    json.dumps(snippet.symbols),
                    snippet.code_language,
                    snippet.code,
                    json.dumps(snippet.constraints),
                    json.dumps(snippet.related_chunk_ids),
                    snippet.start_line,
                    snippet.end_line,
                    snippet.content,
                    snippet.token_count,
                    snippet.quality_score,
                    json.dumps(snippet.metadata_json, sort_keys=True),
                ),
            )

    def scalar_int(self, sql: str, params: tuple[Any, ...]) -> int:
        with self.connection.cursor() as cursor:
            cursor.execute(sql, params)
            row = cursor.fetchone()
        return int(row[0] or 0) if row else 0

    def set_benchmark_score(self, version_id: int, score: float) -> None:
        self.execute(
            "update library_versions set benchmark_score = %s where id = %s",
            (clamp_score(score), version_id),
        )

    def ensure_embeddings(self, version_id: int, *, crawler_job_id: int | None) -> EmbeddingEnsureResult:
        return ensure_version_embeddings(self.connection, version_id, crawler_job_id=crawler_job_id)

    def upsert_chunk(
        self,
        version_id: int,
        *,
        path: str,
        start_line: int,
        end_line: int | None,
        source_url: str,
        source_document_id: int | None,
        ordinal: int,
        chunk_key: str | None,
        parent_chunk_key: str | None,
        chunk_sha: str,
        content_sha: str,
        heading_path: list[str],
        symbols: list[str],
        content_type: str,
        quality_score: float,
        token_count: int,
        source_anchor: str | None,
        metadata_json: dict[str, Any],
        embedding_model: str | None,
        embedding_dimensions: int | None,
        content: str,
        embedding: list[float] | None,
    ) -> None:
        vector = vector_literal(embedding) if embedding else None
        self.execute(
            """
            insert into chunks(
              version_id, source_document_id, path, start_line, end_line, source_url, ordinal, chunk_key,
              parent_chunk_key, chunk_sha, content_sha, heading_path, symbols, content_type,
              quality_score, token_count, source_anchor, embedding_model,
              embedding_dimensions, metadata_json, content, embedding
            )
            values (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s::jsonb, %s::jsonb, %s, %s, %s, %s, %s, %s, %s::jsonb, %s, %s::vector)
            on conflict (version_id, chunk_sha) do update
              set source_document_id = excluded.source_document_id,
                  path = excluded.path,
                  start_line = excluded.start_line,
                  end_line = excluded.end_line,
                  source_url = excluded.source_url,
                  ordinal = excluded.ordinal,
                  chunk_key = excluded.chunk_key,
                  parent_chunk_key = excluded.parent_chunk_key,
                  content_sha = excluded.content_sha,
                  heading_path = excluded.heading_path,
                  symbols = excluded.symbols,
                  content_type = excluded.content_type,
                  quality_score = excluded.quality_score,
                  token_count = excluded.token_count,
                  source_anchor = excluded.source_anchor,
                  metadata_json = excluded.metadata_json,
                  embedding_model = coalesce(excluded.embedding_model, chunks.embedding_model),
                  embedding_dimensions = coalesce(excluded.embedding_dimensions, chunks.embedding_dimensions),
                  content = excluded.content,
                  embedding = coalesce(excluded.embedding, chunks.embedding)
            """,
            (
                version_id,
                source_document_id,
                path,
                start_line,
                end_line,
                source_url,
                ordinal,
                chunk_key,
                parent_chunk_key,
                chunk_sha,
                content_sha,
                json.dumps(heading_path),
                json.dumps(symbols),
                content_type,
                quality_score,
                token_count,
                source_anchor,
                embedding_model,
                embedding_dimensions,
                json.dumps(metadata_json, sort_keys=True),
                content,
                vector,
            ),
        )


def sql_operation(sql: str) -> str:
    first = (sql.strip().split(None, 1) or ["unknown"])[0].lower()
    return first if first in {"select", "insert", "update", "delete", "with"} else "other"


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Index Oz registry fixtures into Postgres.")
    parser.add_argument("--repo-root", default=".", help="Repository root containing registry/catalog.json.")
    parser.add_argument("--dry-run", action="store_true", help="Only count catalog libraries and chunks.")
    args = parser.parse_args(argv)

    stats = index_registry(Path(args.repo_root).resolve(), dry_run=args.dry_run)
    print(json.dumps(stats.as_dict(), indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
