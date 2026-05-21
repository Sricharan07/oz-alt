from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Any
from urllib.parse import urlparse, urldefrag

from oz_api.agent_embeddings import ensure_agent_card_embeddings
from oz_api.embeddings import embedding_dimensions as configured_embedding_dimensions
from oz_api.embedding_jobs import EmbeddingEnsureResult, ensure_version_embeddings
from oz_api.indexer_surfaces import SurfaceIndexMixin
from oz_api.observability import observe_duration
from oz_api.recipe_compiler import build_agent_recipes_from_surfaces, validate_agent_recipes
from oz_api.retrieval import RetrievalContext, postgres_connection, vector_literal
from oz_api.storage import RegistryStorage
from oz_api.trust import first_source_url, trust_score_for_entry
from oz_api.versions import compare_versions
from oz_crawler.content_types import block_content_type, classify_content_type
from oz_crawler.normalize import clean_markdown
from oz_crawler.token_counting import token_count


from oz_api.indexer_artifacts import *  # noqa: F403

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

    def rebuild_agent_surfaces(self, version_id: int, *, fixture: Path, embed_agent_cards: bool = False) -> None:
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
        contextual_prefix: str,
        embedding_input_sha: str | None,
        embedding_model: str | None,
        embedding_dimensions: int | None,
        content: str,
        embedding: list[float] | None,
    ) -> None:
        raise NotImplementedError


class PostgresWriter(SurfaceIndexMixin, IndexWriter):
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

    def tombstone_stale_rows(
        self,
        table_name: str,
        key_column: str,
        version_id: int,
        current_keys: list[str],
        *,
        content_column: str = "content_sha",
    ) -> None:
        allowed = {
            ("source_documents", "source_document_key"),
            ("chunks", "chunk_sha"),
            ("source_sections", "section_key"),
            ("code_examples", "example_key"),
            ("api_operations", "operation_key"),
            ("sdk_methods", "method_key"),
            ("agent_recipes", "recipe_key"),
        }
        if (table_name, key_column) not in allowed:
            raise ValueError(f"unsupported stale tombstone surface: {table_name}.{key_column}")
        predicate = "" if not current_keys else f"and not ({key_column} = any(%s::text[]))"
        params: tuple[Any, ...] = (version_id,) if not current_keys else (version_id, sorted(set(current_keys)))
        self.execute(
            f"""
            insert into index_tombstones(version_id, surface_table, row_id, row_key, content_sha, payload_json)
            select version_id, %s, id, {key_column}, {content_column}, to_jsonb({table_name})
            from {table_name}
            where version_id = %s
              {predicate}
            """,
            (table_name, *params),
        )

    def delete_stale_rows(
        self,
        table_name: str,
        key_column: str,
        version_id: int,
        current_keys: list[str],
        *,
        content_column: str = "content_sha",
    ) -> None:
        self.tombstone_stale_rows(table_name, key_column, version_id, current_keys, content_column=content_column)
        if current_keys:
            self.execute(
                f"delete from {table_name} where version_id = %s and not ({key_column} = any(%s::text[]))",
                (version_id, sorted(set(current_keys))),
            )
            return
        self.execute(f"delete from {table_name} where version_id = %s", (version_id,))

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
        self.delete_stale_rows("chunks", "chunk_sha", version_id, current_chunk_shas)

    def upsert_source_document(self, version_id: int, source: dict[str, Any]) -> int:
        return self.scalar(
            """
            insert into source_documents(
              version_id, source_document_key, source_type, document_role,
              canonical_url, source_url, path, title, product, product_confidence,
              language, content_markdown, parallel_structured_json, content_sha, raw_token_count, clean_token_count,
              chunk_coverage_ratio, coverage_json,
              source_priority, discovered_from, raw_artifact_key, raw_object_store, raw_object_sha256,
              etag, last_modified, metadata_json, fetched_at
            )
            values (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s::jsonb, %s, %s, %s, %s, %s::jsonb, %s, %s, %s, %s, %s, %s, %s, %s::jsonb, now())
            on conflict (version_id, source_document_key) do update
              set source_type = excluded.source_type,
                  document_role = excluded.document_role,
                  canonical_url = excluded.canonical_url,
                  source_url = excluded.source_url,
                  path = excluded.path,
                  title = excluded.title,
                  product = excluded.product,
                  product_confidence = excluded.product_confidence,
                  language = excluded.language,
                  content_markdown = excluded.content_markdown,
                  parallel_structured_json = excluded.parallel_structured_json,
                  content_sha = excluded.content_sha,
                  raw_token_count = excluded.raw_token_count,
                  clean_token_count = excluded.clean_token_count,
                  chunk_coverage_ratio = excluded.chunk_coverage_ratio,
                  coverage_json = excluded.coverage_json,
                  source_priority = excluded.source_priority,
                  discovered_from = excluded.discovered_from,
                  raw_artifact_key = excluded.raw_artifact_key,
                  raw_object_store = excluded.raw_object_store,
                  raw_object_sha256 = excluded.raw_object_sha256,
                  etag = excluded.etag,
                  last_modified = excluded.last_modified,
                  metadata_json = excluded.metadata_json,
                  fetched_at = now()
            returning id
            """,
            (
                version_id,
                str(source["source_document_key"]),
                str(source.get("source_type") or "website_url"),
                str(source.get("document_role") or "unknown"),
                nullable_string(source.get("canonical_url")),
                nullable_string(source.get("source_url")),
                nullable_string(source.get("path")),
                nullable_string(source.get("title")),
                str(source.get("product") or ""),
                float(source.get("product_confidence") or 0),
                str(source.get("language") or ""),
                str(source.get("content_markdown") or ""),
                json.dumps(source.get("parallel_structured_json") if isinstance(source.get("parallel_structured_json"), (dict, list)) else {}, sort_keys=True),
                nullable_string(source.get("content_sha")),
                int(source.get("raw_token_count") or 0),
                int(source.get("clean_token_count") or 0),
                float(source.get("chunk_coverage_ratio") or 0),
                json.dumps(source.get("coverage_json") if isinstance(source.get("coverage_json"), dict) else {}, sort_keys=True),
                int(source.get("source_priority") or 50),
                nullable_string(source.get("discovered_from")),
                nullable_string(source.get("raw_artifact_key")),
                nullable_string(source.get("raw_object_store")),
                nullable_string(source.get("raw_object_sha256")),
                nullable_string(source.get("etag")),
                nullable_string(source.get("last_modified")),
                json.dumps(source.get("metadata_json") if isinstance(source.get("metadata_json"), dict) else {}, sort_keys=True),
            ),
        )

    def delete_stale_source_documents(self, version_id: int, current_source_keys: list[str]) -> None:
        self.delete_stale_rows("source_documents", "source_document_key", version_id, current_source_keys)

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
              insert into dedupe_clusters(
                version_id, cluster_key, surface_table, canonical_row_id,
                member_ids_json, canonical_chunk_id, member_count, method
              )
              select version_id, cluster_key, 'chunks', ids[1], to_jsonb(ids), ids[1], member_count, 'normalized_exact'
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
              insert into dedupe_clusters(
                version_id, cluster_key, surface_table, canonical_row_id,
                member_ids_json, canonical_chunk_id, member_count, method
              )
              select %s, cluster_key, 'chunks', canonical_id, to_jsonb(ids), canonical_id, cardinality(ids), 'vector_cosine_0.95'
              from clusters
              on conflict (version_id, cluster_key) do update
                set surface_table = excluded.surface_table,
                    canonical_row_id = excluded.canonical_row_id,
                    member_ids_json = excluded.member_ids_json,
                    canonical_chunk_id = excluded.canonical_chunk_id,
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
        self.execute(
            """
            update dedupe_clusters
               set surface_table = 'chunks',
                   canonical_row_id = canonical_chunk_id,
                   member_ids_json = coalesce(member_ids_json, '[]'::jsonb)
             where version_id = %s
               and surface_table = 'chunks'
            """,
            (version_id,),
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
        contextual_prefix: str,
        embedding_input_sha: str | None,
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
              quality_score, token_count, source_anchor, contextual_prefix, embedding_input_sha,
              embedding_model, embedding_dimensions, metadata_json, content, embedding
            )
            values (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s::jsonb, %s::jsonb, %s, %s, %s, %s, %s, %s, %s, %s, %s::jsonb, %s, %s::vector)
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
                  contextual_prefix = excluded.contextual_prefix,
                  embedding_input_sha = excluded.embedding_input_sha,
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
                contextual_prefix,
                embedding_input_sha,
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
