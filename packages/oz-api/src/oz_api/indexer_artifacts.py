from __future__ import annotations

import hashlib
import json
import os
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Any
from urllib.parse import urldefrag, urlparse

from oz_api.embedding_jobs import EmbeddingEnsureResult
from oz_api.retrieval import RetrievalContext, postgres_connection
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
        from oz_api.indexer import PostgresWriter

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
        for source in source_document_rows(fixture):
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
                contextual_prefix=str(row.get("contextual_prefix") or ""),
                embedding_input_sha=nullable_string(row.get("embedding_input_sha")),
                embedding_model=nullable_string(row.get("embedding_model")) if embedding else None,
                embedding_dimensions=(int(row.get("embedding_dimensions") or 0) or None) if embedding else None,
                content=str(row.get("text") or ""),
                embedding=embedding,
            )
        writer.delete_stale_chunks(version_id, current_chunk_shas)
        writer.resolve_parent_chunks(version_id)
        writer.rebuild_agent_surfaces(version_id, fixture=fixture)
        result = writer.ensure_embeddings(version_id, crawler_job_id=optional_int(entry.get("crawler_job_id")))
        embedding_results.append(result)
        if result.complete:
            writer.resolve_parent_chunks(version_id)
            writer.rebuild_dedupe_clusters(version_id)
            writer.rebuild_agent_surfaces(version_id, fixture=fixture, embed_agent_cards=True)
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
    enriched["contextual_prefix"] = str(enriched.get("contextual_prefix") or "").strip()
    enriched["embedding_input_sha"] = str(enriched.get("embedding_input_sha") or "") or normalized_content_hash(
        f"{enriched['contextual_prefix']}\n\n{text}" if enriched["contextual_prefix"] else text
    )
    return enriched


def source_document_rows(fixture: Path) -> list[dict[str, Any]]:
    source_path = fixture / "_sources.jsonl"
    output: list[dict[str, Any]] = []
    seen: set[str] = set()
    coverage_by_key = source_coverage_rows(fixture)
    if not source_path.exists():
        raise RuntimeError(f"{fixture} is missing _sources.jsonl; indexing requires canonical source document artifacts")
    for line in source_path.read_text(encoding="utf-8").splitlines():
        if not line.strip():
            continue
        source = json.loads(line)
        key = source_document_key_for_row(source)
        if not key or key in seen:
            continue
        source["source_document_key"] = key
        metadata = source.get("metadata_json") if isinstance(source.get("metadata_json"), dict) else {}
        source.setdefault("source_type", metadata.get("source_type") or "website_url")
        source.setdefault("document_role", metadata.get("document_role") or "unknown")
        source.setdefault("product", metadata.get("product") or "")
        source.setdefault("product_confidence", metadata.get("product_confidence") or 0)
        source.setdefault("language", metadata.get("language") or "")
        source.setdefault("content_markdown", source.get("content_markdown") or "")
        source.setdefault(
            "parallel_structured_json",
            source.get("parallel_structured_json") or metadata.get("parallel_structured_json") or metadata.get("operation") or {},
        )
        source.setdefault("content_sha", "")
        source.setdefault("raw_token_count", 0)
        source.setdefault("clean_token_count", 0)
        source.setdefault("raw_artifact_key", metadata.get("raw_artifact_key") or "")
        source.setdefault("raw_object_store", metadata.get("raw_object_store") or "")
        source.setdefault("raw_object_sha256", metadata.get("raw_object_sha256") or "")
        source.setdefault("etag", metadata.get("etag") or "")
        source.setdefault("last_modified", metadata.get("last_modified") or "")
        if key in coverage_by_key:
            source["clean_token_count"] = int(coverage_by_key[key].get("clean_token_count") or source.get("clean_token_count") or 0)
            source["chunk_coverage_ratio"] = float(coverage_by_key[key].get("coverage_ratio") or 0)
            source["coverage_json"] = coverage_by_key[key]
            source["metadata_json"] = {**metadata, "chunk_coverage": coverage_by_key[key]}
        output.append(source)
        seen.add(key)
    return output


def source_coverage_rows(fixture: Path) -> dict[str, dict[str, Any]]:
    output: dict[str, dict[str, Any]] = {}
    for row in jsonl_rows(fixture / "_chunk_coverage.jsonl"):
        key = str(row.get("source_document_key") or "")
        if key:
            output[key] = row
    return output


def row_metadata_value(row: dict[str, Any], key: str, default: Any) -> Any:
    metadata = row.get("metadata_json") if isinstance(row.get("metadata_json"), dict) else {}
    value = metadata.get(key, row.get(key, default))
    return default if value in (None, "") else value


def jsonl_rows(path: Path) -> list[dict[str, Any]]:
    if not path.exists():
        return []
    output: list[dict[str, Any]] = []
    for line in path.read_text(encoding="utf-8").splitlines():
        if not line.strip():
            continue
        value = json.loads(line)
        if isinstance(value, dict):
            output.append(value)
    return output


def source_section_rows(fixture: Path) -> list[dict[str, Any]]:
    rows = jsonl_rows(fixture / "_source_sections.jsonl")
    if not rows:
        raise RuntimeError(f"{fixture} is missing _source_sections.jsonl; indexing requires canonical section artifacts")
    return [normalize_surface_row(row) for row in rows]


def code_example_rows(fixture: Path) -> list[dict[str, Any]]:
    return [normalize_surface_row(row) for row in jsonl_rows(fixture / "_code_examples.jsonl")]


def api_operation_rows(fixture: Path) -> list[dict[str, Any]]:
    return [normalize_surface_row(row) for row in jsonl_rows(fixture / "_api_operations.jsonl")]


def sdk_method_rows(fixture: Path) -> list[dict[str, Any]]:
    return [normalize_surface_row(row) for row in jsonl_rows(fixture / "_sdk_methods.jsonl")]


def normalize_surface_row(row: dict[str, Any]) -> dict[str, Any]:
    output = dict(row)
    metadata = output.get("metadata_json") if isinstance(output.get("metadata_json"), dict) else {}
    output["metadata_json"] = metadata
    output.setdefault("source_type", metadata.get("source_type") or "website_url")
    output.setdefault("document_role", metadata.get("document_role") or "unknown")
    output.setdefault("product", metadata.get("product") or "")
    output.setdefault("product_confidence", metadata.get("product_confidence") or 0)
    output.setdefault("language", metadata.get("language") or "")
    return output


def field(row: Any, key: str, default: Any = None) -> Any:
    if isinstance(row, dict):
        return row.get(key, default)
    return getattr(row, key, default)


def source_document_key_from_surface(row: dict[str, Any]) -> str:
    return source_document_key_for_row(row)


def list_json(value: Any) -> str:
    if isinstance(value, list):
        return json.dumps(value, sort_keys=True)
    if value in (None, ""):
        return "[]"
    return json.dumps([value], sort_keys=True)


def dict_json(value: Any) -> str:
    if isinstance(value, dict):
        return json.dumps(value, sort_keys=True)
    if value in (None, ""):
        return "{}"
    return json.dumps(value, sort_keys=True)


def text_for_search(*values: Any) -> str:
    parts: list[str] = []
    for value in values:
        if isinstance(value, (dict, list)):
            parts.append(json.dumps(value, ensure_ascii=False, sort_keys=True))
        elif value is not None:
            parts.append(str(value))
    return "\n".join(part for part in parts if part.strip())


def source_document_key_for_row(row: dict[str, Any]) -> str:
    value = row.get("source_document_key") or row.get("canonical_url") or row.get("source_url") or row.get("path") or ""
    text = str(value).rstrip("/")
    if preserves_virtual_source_fragment(text, row):
        return text
    return text.split("#", 1)[0].rstrip("/")


def preserves_virtual_source_fragment(url: str, row: dict[str, Any]) -> bool:
    parsed = urlparse(url)
    if not parsed.fragment:
        return False
    metadata = row.get("metadata_json") if isinstance(row.get("metadata_json"), dict) else {}
    source_type = str(row.get("source_type") or metadata.get("source_type") or "").lower()
    if source_type in {"llms_txt", "openapi"}:
        return True
    return bool(
        re.search(r"(?:^|/)(?:llms|llms-full)\.txt$", parsed.path.lower())
        or re.search(r"(?:openapi|swagger)\.(?:json|ya?ml)$", parsed.path.lower())
    )


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
