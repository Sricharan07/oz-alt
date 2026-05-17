from __future__ import annotations

import argparse
import hashlib
import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from oz_api.retrieval import RetrievalContext, postgres_connection, vector_literal
from oz_api.storage import RegistryStorage


@dataclass(frozen=True)
class IndexStats:
    libraries: int = 0
    versions: int = 0
    chunks: int = 0
    embedded_chunks: int = 0

    def as_dict(self) -> dict[str, int]:
        return {
            "libraries": self.libraries,
            "versions": self.versions,
            "chunks": self.chunks,
            "embedded_chunks": self.embedded_chunks,
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
        write_catalog_and_chunks(PostgresWriter(connection), storage, catalog)
    return stats


def count_registry(storage: RegistryStorage, catalog: list[dict[str, Any]]) -> IndexStats:
    chunks = 0
    embedded = 0
    for entry in catalog:
        for row in chunk_rows(storage, entry):
            chunks += 1
            if valid_embedding(row.get("embedding")):
                embedded += 1
    return IndexStats(libraries=len(catalog), versions=len(catalog), chunks=chunks, embedded_chunks=embedded)


def write_catalog_and_chunks(writer: "IndexWriter", storage: RegistryStorage, catalog: list[dict[str, Any]]) -> None:
    for entry in catalog:
        vendor_id = writer.upsert_vendor(str(entry["vendor"]))
        library_id = writer.upsert_library(vendor_id, entry)
        version_id = writer.upsert_version(library_id, entry)
        writer.upsert_ref(library_id, version_id, str(entry.get("ref_sha") or "unknown"))

        fixture = fixture_path(storage, entry)
        line_cache: dict[str, str] = {}
        current_chunk_shas: list[str] = []
        for row in chunk_rows(storage, entry):
            chunk_sha = chunk_sha_for_row(entry, row)
            current_chunk_shas.append(chunk_sha)
            start_line, end_line = row_line_span(row) or line_span(fixture, row, line_cache)
            embedding = embedding_for_chunk(row)
            writer.upsert_chunk(
                version_id,
                path=str(row.get("path") or "README.md"),
                start_line=start_line,
                end_line=end_line,
                source_url=str(row.get("source_url") or ""),
                ordinal=int(row.get("ordinal") or 1),
                chunk_sha=chunk_sha,
                heading_path=list_of_strings(row.get("heading_path")),
                symbols=list_of_strings(row.get("symbols")),
                content_type=str(row.get("content_type") or "guide"),
                quality_score=float(row.get("quality_score") or 1.0),
                content=str(row.get("text") or ""),
                embedding=embedding,
            )
        writer.delete_stale_chunks(version_id, current_chunk_shas)


def chunk_rows(storage: RegistryStorage, entry: dict[str, Any]) -> list[dict[str, Any]]:
    chunks_path = fixture_path(storage, entry) / "_chunks.jsonl"
    if not chunks_path.exists():
        return []
    rows: list[dict[str, Any]] = []
    seen_chunk_shas: set[str] = set()
    for line in chunks_path.read_text(encoding="utf-8").splitlines():
        if line.strip():
            row = json.loads(line)
            if not is_indexable_chunk(row):
                continue
            chunk_sha = chunk_sha_for_row(entry, row)
            if chunk_sha in seen_chunk_shas:
                continue
            seen_chunk_shas.add(chunk_sha)
            rows.append(row)
    return rows


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


def valid_embedding(value: Any) -> bool:
    return isinstance(value, list) and len(value) == 1536 and all(isinstance(item, (int, float)) for item in value)


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


def embedding_for_chunk(row: dict[str, Any]) -> list[float] | None:
    existing = row.get("embedding")
    if valid_embedding(existing):
        return [float(value) for value in existing]
    text = str(row.get("text") or "")
    if not text:
        return None
    try:
        from oz_crawler.embeddings import embedding_for_text  # type: ignore
    except ImportError:
        return None
    generated = embedding_for_text(text)
    if valid_embedding(generated):
        return generated
    return None


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

    def upsert_chunk(
        self,
        version_id: int,
        *,
        path: str,
        start_line: int,
        end_line: int | None,
        source_url: str,
        ordinal: int,
        chunk_sha: str,
        heading_path: list[str],
        symbols: list[str],
        content_type: str,
        quality_score: float,
        content: str,
        embedding: list[float] | None,
    ) -> None:
        raise NotImplementedError


class PostgresWriter(IndexWriter):
    def __init__(self, connection: Any) -> None:
        self.connection = connection

    def scalar(self, sql: str, params: tuple[Any, ...]) -> int:
        with self.connection.cursor() as cursor:
            cursor.execute(sql, params)
            row = cursor.fetchone()
        return int(row[0])

    def execute(self, sql: str, params: tuple[Any, ...]) -> None:
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
            insert into libraries(vendor_id, name, description, source_url)
            values (%s, %s, %s, %s)
            on conflict (vendor_id, name) do update
              set description = excluded.description,
                  source_url = excluded.source_url,
                  updated_at = now()
            returning id
            """,
            (
                vendor_id,
                str(entry["library"]),
                str(entry.get("description") or ""),
                first_source_url(entry),
            ),
        )

    def upsert_version(self, library_id: int, entry: dict[str, Any]) -> int:
        return self.scalar(
            """
            insert into library_versions(library_id, version, ref_sha, pack_key, indexed_at, last_crawled_at)
            values (%s, %s, %s, %s, nullif(%s, '')::timestamptz, now())
            on conflict (library_id, version) do update
              set ref_sha = excluded.ref_sha,
                  pack_key = excluded.pack_key,
                  indexed_at = excluded.indexed_at,
                  last_crawled_at = now()
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

    def upsert_chunk(
        self,
        version_id: int,
        *,
        path: str,
        start_line: int,
        end_line: int | None,
        source_url: str,
        ordinal: int,
        chunk_sha: str,
        heading_path: list[str],
        symbols: list[str],
        content_type: str,
        quality_score: float,
        content: str,
        embedding: list[float] | None,
    ) -> None:
        vector = vector_literal(embedding) if embedding else None
        self.execute(
            """
            insert into chunks(
              version_id, path, start_line, end_line, source_url, ordinal, chunk_sha,
              heading_path, symbols, content_type, quality_score, content, embedding
            )
            values (%s, %s, %s, %s, %s, %s, %s, %s::jsonb, %s::jsonb, %s, %s, %s, %s::vector)
            on conflict (version_id, chunk_sha) do update
              set path = excluded.path,
                  start_line = excluded.start_line,
                  end_line = excluded.end_line,
                  source_url = excluded.source_url,
                  ordinal = excluded.ordinal,
                  heading_path = excluded.heading_path,
                  symbols = excluded.symbols,
                  content_type = excluded.content_type,
                  quality_score = excluded.quality_score,
                  content = excluded.content,
                  embedding = excluded.embedding
            """,
            (
                version_id,
                path,
                start_line,
                end_line,
                source_url,
                ordinal,
                chunk_sha,
                json.dumps(heading_path),
                json.dumps(symbols),
                content_type,
                quality_score,
                content,
                vector,
            ),
        )


def first_source_url(entry: dict[str, Any]) -> str | None:
    urls = entry.get("source_urls")
    if isinstance(urls, list) and urls:
        return str(urls[0])
    source = entry.get("source_url")
    return str(source) if source else None


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
