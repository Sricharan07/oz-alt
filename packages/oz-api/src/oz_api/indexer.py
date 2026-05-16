from __future__ import annotations

import argparse
import hashlib
import json
import os
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from oz_api.retrieval import RetrievalContext, execute_data_api, postgres_connection, vector_literal
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
    data_api = DataApiWriter(ctx)
    if data_api.available:
        write_catalog_and_chunks(data_api, storage, catalog)
        return stats

    connection = postgres_connection(ctx.database_url)
    if connection is None:
        raise RuntimeError(
            "No database connection configured. Set OZ_DATABASE_URL, or OZ_DB_RESOURCE_ARN and OZ_DB_SECRET_ARN."
        )
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
            start_line, end_line = line_span(fixture, row, line_cache)
            embedding = embedding_for_chunk(row)
            writer.upsert_chunk(
                version_id,
                path=str(row.get("path") or "README.md"),
                start_line=start_line,
                end_line=end_line,
                source_url=str(row.get("source_url") or ""),
                ordinal=int(row.get("ordinal") or 1),
                chunk_sha=chunk_sha,
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
    if not os.environ.get("OPENAI_API_KEY"):
        return None
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
        content: str,
        embedding: list[float] | None,
    ) -> None:
        vector = vector_literal(embedding) if embedding else None
        self.execute(
            """
            insert into chunks(version_id, path, start_line, end_line, source_url, ordinal, chunk_sha, content, embedding)
            values (%s, %s, %s, %s, %s, %s, %s, %s, %s::vector)
            on conflict (version_id, chunk_sha) do update
              set path = excluded.path,
                  start_line = excluded.start_line,
                  end_line = excluded.end_line,
                  source_url = excluded.source_url,
                  ordinal = excluded.ordinal,
                  content = excluded.content,
                  embedding = excluded.embedding
            """,
            (version_id, path, start_line, end_line, source_url, ordinal, chunk_sha, content, vector),
        )


class DataApiWriter(IndexWriter):
    def __init__(self, ctx: RetrievalContext) -> None:
        self.ctx = ctx
        self.available = bool(ctx.db_resource_arn and ctx.db_secret_arn)

    def scalar(self, sql: str, params: list[dict[str, Any]]) -> int:
        rows = execute_data_api(self.ctx, sql, params)
        if not rows:
            raise RuntimeError("Aurora Data API statement returned no rows")
        return int(numeric_data_api_field(rows[0][0]))

    def execute(self, sql: str, params: list[dict[str, Any]]) -> None:
        rows = execute_data_api(self.ctx, sql, params)
        if rows is None:
            raise RuntimeError("Aurora Data API statement failed")

    def upsert_vendor(self, vendor: str) -> int:
        return self.scalar(
            """
            insert into vendors(name)
            values (:vendor)
            on conflict (name) do update set name = excluded.name
            returning id
            """,
            [string_param("vendor", vendor)],
        )

    def upsert_library(self, vendor_id: int, entry: dict[str, Any]) -> int:
        return self.scalar(
            """
            insert into libraries(vendor_id, name, description, source_url)
            values (:vendor_id, :library, :description, :source_url)
            on conflict (vendor_id, name) do update
              set description = excluded.description,
                  source_url = excluded.source_url,
                  updated_at = now()
            returning id
            """,
            [
                long_param("vendor_id", vendor_id),
                string_param("library", str(entry["library"])),
                string_param("description", str(entry.get("description") or "")),
                nullable_string_param("source_url", first_source_url(entry)),
            ],
        )

    def upsert_version(self, library_id: int, entry: dict[str, Any]) -> int:
        return self.scalar(
            """
            insert into library_versions(library_id, version, ref_sha, pack_key, indexed_at, last_crawled_at)
            values (:library_id, :version, :ref_sha, :pack_key, nullif(:indexed_at, '')::timestamptz, now())
            on conflict (library_id, version) do update
              set ref_sha = excluded.ref_sha,
                  pack_key = excluded.pack_key,
                  indexed_at = excluded.indexed_at,
                  last_crawled_at = now()
            returning id
            """,
            [
                long_param("library_id", library_id),
                string_param("version", str(entry["version"])),
                string_param("ref_sha", str(entry.get("ref_sha") or "unknown")),
                string_param("pack_key", str(entry.get("pack_path") or "")),
                string_param("indexed_at", str(entry.get("indexed_at") or "")),
            ],
        )

    def upsert_ref(self, library_id: int, version_id: int, ref_sha: str) -> None:
        self.execute(
            """
            insert into refs(library_id, channel, version_id, ref_sha)
            values (:library_id, 'latest', :version_id, :ref_sha)
            on conflict (library_id, channel) do update
              set version_id = excluded.version_id,
                  ref_sha = excluded.ref_sha,
                  updated_at = now()
            """,
            [
                long_param("library_id", library_id),
                long_param("version_id", version_id),
                string_param("ref_sha", ref_sha),
            ],
        )

    def delete_stale_chunks(self, version_id: int, current_chunk_shas: list[str]) -> None:
        chunk_shas = sorted(set(current_chunk_shas))
        params = [long_param("version_id", version_id)]
        if not chunk_shas:
            self.execute("delete from chunks where version_id = :version_id", params)
            return

        placeholders = []
        for index, chunk_sha in enumerate(chunk_shas):
            name = f"chunk_sha_{index}"
            placeholders.append(f":{name}")
            params.append(string_param(name, chunk_sha))
        self.execute(
            f"""
            delete from chunks
            where version_id = :version_id
              and chunk_sha not in ({", ".join(placeholders)})
            """,
            params,
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
        content: str,
        embedding: list[float] | None,
    ) -> None:
        params = [
            long_param("version_id", version_id),
            string_param("path", path),
            long_param("start_line", start_line),
            nullable_long_param("end_line", end_line),
            nullable_string_param("source_url", source_url or None),
            long_param("ordinal", ordinal),
            string_param("chunk_sha", chunk_sha),
            string_param("content", content),
        ]
        if embedding:
            params.append(string_param("embedding", vector_literal(embedding)))
            embedding_sql = "(:embedding)::vector"
        else:
            embedding_sql = "null"

        self.execute(
            f"""
            insert into chunks(version_id, path, start_line, end_line, source_url, ordinal, chunk_sha, content, embedding)
            values (:version_id, :path, :start_line, :end_line, :source_url, :ordinal, :chunk_sha, :content, {embedding_sql})
            on conflict (version_id, chunk_sha) do update
              set path = excluded.path,
                  start_line = excluded.start_line,
                  end_line = excluded.end_line,
                  source_url = excluded.source_url,
                  ordinal = excluded.ordinal,
                  content = excluded.content,
                  embedding = excluded.embedding
            """,
            params,
        )


def first_source_url(entry: dict[str, Any]) -> str | None:
    urls = entry.get("source_urls")
    if isinstance(urls, list) and urls:
        return str(urls[0])
    source = entry.get("source_url")
    return str(source) if source else None


def string_param(name: str, value: str) -> dict[str, Any]:
    return {"name": name, "value": {"stringValue": value}}


def nullable_string_param(name: str, value: str | None) -> dict[str, Any]:
    if value is None:
        return {"name": name, "value": {"isNull": True}}
    return string_param(name, value)


def long_param(name: str, value: int) -> dict[str, Any]:
    return {"name": name, "value": {"longValue": int(value)}}


def nullable_long_param(name: str, value: int | None) -> dict[str, Any]:
    if value is None:
        return {"name": name, "value": {"isNull": True}}
    return long_param(name, value)


def numeric_data_api_field(field: dict[str, Any]) -> float:
    if "longValue" in field:
        return float(field["longValue"])
    if "doubleValue" in field:
        return float(field["doubleValue"])
    if "stringValue" in field:
        return float(field["stringValue"])
    return 0.0


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Index Oz registry fixtures into Postgres/Aurora.")
    parser.add_argument("--repo-root", default=".", help="Repository root containing registry/catalog.json.")
    parser.add_argument("--dry-run", action="store_true", help="Only count catalog libraries and chunks.")
    args = parser.parse_args(argv)

    stats = index_registry(Path(args.repo_root).resolve(), dry_run=args.dry_run)
    print(json.dumps(stats.as_dict(), indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
