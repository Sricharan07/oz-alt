from __future__ import annotations

import logging
from functools import cmp_to_key
from typing import Any

from oz_api.embeddings import embedding_for_query
from oz_api.db import postgres_connection
from oz_api.intent import classify_query, intent_name
from oz_api.observability import observe_duration
from oz_api.ranking import local_chunk_score
from oz_api.retrieval_context import RetrievalContext
from oz_api.retrieval_metrics import retrieval_statement_timeout_ms
from oz_api.storage import normalize_query
from oz_api.versions import (
    VersionResolutionError,
    available_versions,
    compare_versions,
    latest_entry,
    parse_versioned_scope,
    version_matches,
)

LOGGER = logging.getLogger(__name__)


def suggest_from_postgres(
    ctx: RetrievalContext,
    query: str,
    max_results: int,
    fingerprint: str,
    *,
    vector_enabled: bool = True,
) -> list[dict[str, Any]] | None:
    connection = postgres_connection(ctx.database_url)
    if connection is None:
        return None
    terms = normalized_tsquery(query)
    vector = vector_literal(embedding) if vector_enabled and (embedding := embedding_for_query(query)) else None
    candidates = candidate_limit(max_results)
    if vector:
        sql = """
            with fts_candidates as (
              select v.name as vendor, l.name as library, lv.version,
                     coalesce(l.description, '') as reason,
                     greatest(
                       coalesce(ts_rank_cd(l.search_document, websearch_to_tsquery('english', %s)), 0),
                       coalesce(ts_rank_cd(c.search_document, websearch_to_tsquery('english', %s)), 0)
                     ) as fts_score,
                     0::float8 as vector_score,
                     greatest(coalesce(c.quality_score, 1), 0) as quality_score,
                     coalesce(ts.value, 0) as trust_score,
                     coalesce(lv.benchmark_score, 0) as benchmark_score
              from libraries l
              join vendors v on v.id = l.vendor_id
              join refs r on r.library_id = l.id and r.channel = 'latest'
              join library_versions lv on lv.id = coalesce(l.default_version_id, r.version_id)
                   and lv.archived_at is null
              left join chunks c on c.version_id = lv.id and coalesce(c.dedupe_canonical, true)
              left join trust_scores ts on ts.library_id = l.id
              where l.search_document @@ websearch_to_tsquery('english', %s)
                 or c.search_document @@ websearch_to_tsquery('english', %s)
              order by fts_score desc, v.name asc, l.name asc
              limit %s
            ),
            vector_candidates as (
              select v.name as vendor, l.name as library, lv.version,
                     coalesce(l.description, '') as reason,
                     0::float8 as fts_score,
                     greatest(1 - (c.embedding <=> %s::vector), 0) as vector_score,
                     greatest(coalesce(c.quality_score, 1), 0) as quality_score,
                     coalesce(ts.value, 0) as trust_score,
                     coalesce(lv.benchmark_score, 0) as benchmark_score
              from chunks c
              join library_versions lv on lv.id = c.version_id and lv.archived_at is null
              join libraries l on l.id = lv.library_id
              join vendors v on v.id = l.vendor_id
              join refs r on r.library_id = l.id and r.channel = 'latest'
              left join trust_scores ts on ts.library_id = l.id
              where c.embedding is not null and coalesce(c.dedupe_canonical, true)
                and lv.id = coalesce(l.default_version_id, r.version_id)
              order by c.embedding <=> %s::vector
              limit %s
            ),
            ranked as (
              select vendor, library, version, max(reason) as reason,
                     (max(fts_score) * 2.0) + (max(vector_score) * 2.5)
                     + (max(quality_score) * 0.15) + (max(trust_score) * 0.08)
                     + (max(benchmark_score) * 0.10) as score
              from (
                select * from fts_candidates
                union all
                select * from vector_candidates
              ) candidates
              group by vendor, library, version
            )
            select vendor, library, version, score, reason
            from ranked
            order by score desc, vendor asc, library asc, version asc
            limit %s
        """
        params: list[Any] = [terms, terms, terms, terms, candidates, vector, vector, candidates, max_results]
    else:
        sql = """
            select v.name as vendor, l.name as library, lv.version,
                   max(greatest(
                     coalesce(ts_rank_cd(l.search_document, websearch_to_tsquery('english', %s)), 0),
                     coalesce(ts_rank_cd(c.search_document, websearch_to_tsquery('english', %s)), 0)
                   )) + (max(greatest(coalesce(c.quality_score, 1), 0)) * 0.15)
                   + (max(coalesce(ts.value, 0)) * 0.08)
                   + (max(coalesce(lv.benchmark_score, 0)) * 0.10) as score,
                   coalesce(l.description, '') as reason
            from libraries l
            join vendors v on v.id = l.vendor_id
            join refs r on r.library_id = l.id and r.channel = 'latest'
            join library_versions lv on lv.id = coalesce(l.default_version_id, r.version_id)
                 and lv.archived_at is null
            left join chunks c on c.version_id = lv.id and coalesce(c.dedupe_canonical, true)
            left join trust_scores ts on ts.library_id = l.id
            where l.search_document @@ websearch_to_tsquery('english', %s)
               or c.search_document @@ websearch_to_tsquery('english', %s)
            group by v.name, l.name, lv.version, l.description
            order by score desc, v.name asc, l.name asc, lv.version asc
            limit %s
        """
        params = [terms, terms, terms, terms, max_results]
    try:
        with observe_duration("oz_db_query_duration_seconds", {"operation": "suggest", "mode": "vector" if vector else "fts"}):
            with connection:
                with connection.cursor() as cursor:
                    cursor.execute(f"set local statement_timeout = {retrieval_statement_timeout_ms()}")
                    cursor.execute(sql, tuple(params))
                    rows = cursor.fetchall()
        return [
            {"vendor": row[0], "library": row[1], "version": row[2], "score": float(row[3]), "reason": row[4]}
            for row in rows
        ]
    except Exception as exc:
        LOGGER.warning("postgres suggest failed: %s", exc)
        if vector_enabled:
            LOGGER.warning("retrying postgres suggest with FTS fallback only")
            return suggest_from_postgres(ctx, query, max_results, fingerprint, vector_enabled=False)
        return None


def search_from_postgres(
    ctx: RetrievalContext,
    query: str,
    library_scope: str | None,
    max_results: int,
    fingerprint: str,
    *,
    vector_enabled: bool = True,
) -> list[dict[str, Any]] | None:
    connection = postgres_connection(ctx.database_url)
    if connection is None:
        return None
    terms = normalized_tsquery(query)
    intent = intent_name(query)
    query_intent = classify_query(query)
    symbol_pattern = like_pattern(query_intent.symbols or normalize_query(query)[:4])
    vector = vector_literal(embedding) if vector_enabled and (embedding := embedding_for_query(query)) else None
    scope = parse_versioned_scope(library_scope)
    scope_vendor, scope_library = scope.vendor, scope.library
    scope_version_id: int | None = None
    if scope_vendor and scope_library:
        scope_version_id = resolve_db_version_id(connection, scope_vendor, scope_library, scope.version)
    where_scope = (
        "and v.name = %s and l.name = %s and lv.id = %s"
        if scope_vendor
        else "and lv.id = coalesce(l.default_version_id, r.version_id) and lv.archived_at is null"
    )
    candidates = candidate_limit(max_results)
    params: list[Any] = [terms, intent, terms]
    if scope_vendor:
        params.extend([scope_vendor, scope_library, scope_version_id])
    params.append(candidates)
    vector_cte = empty_vector_cte()
    if vector:
        vector_cte = vector_candidate_cte(where_scope)
        params.extend([vector, intent])
        if scope_vendor:
            params.extend([scope_vendor, scope_library, scope_version_id])
        params.extend([vector, candidates])
    params.extend([intent, symbol_pattern, symbol_pattern, symbol_pattern])
    if scope_vendor:
        params.extend([scope_vendor, scope_library, scope_version_id])
    params.extend([candidates, max_results])
    sql = f"""
        with fts_candidates as (
          {candidate_select("greatest(ts_rank_cd(c.search_document, websearch_to_tsquery('english', %s)), 0)", "0::float8", "0::float8")}
          where c.search_document @@ websearch_to_tsquery('english', %s)
            and coalesce(c.dedupe_canonical, true)
            {where_scope}
          order by fts_score desc, path asc, start_line asc
          limit %s
        ),
        vector_candidates as (
          {vector_cte}
        ),
        symbol_candidates as (
          {candidate_select("0::float8", "0::float8", "1.0::float8")}
          where coalesce(c.dedupe_canonical, true)
            and (
              c.path ilike %s
              or c.symbols::text ilike %s
              or c.heading_path::text ilike %s
            )
            {where_scope}
          order by symbol_score desc, path asc, start_line asc
          limit %s
        ),
        ranked_chunks as (
          select path, start_line, matched_path, source_anchor, token_count,
                 library, vendor, version, relative_path, heading_path, symbols,
                 content_type, quality_score, content, parent_content,
                 (max(fts_score) * 2.4) + (max(vector_score) * 2.8) + (max(symbol_score) * 2.0)
                 + (max(quality_score) * 0.15) + max(type_score)
                 + least(max(coalesce(token_count, 0)), 2000) / 20000.0 as score
          from (
            select * from fts_candidates
            union all
            select * from vector_candidates
            union all
            select * from symbol_candidates
          ) candidates
          group by path, start_line, matched_path, source_anchor, token_count,
                   library, vendor, version, relative_path, heading_path, symbols,
                   content_type, quality_score, content, parent_content
        ),
        ranked_files as (
          select distinct on (path)
                 path, start_line, score, library, vendor, version, relative_path,
                 heading_path, symbols, content_type, quality_score, content,
                 matched_path, source_anchor, token_count, parent_content
          from ranked_chunks
          order by path, score desc, start_line asc
        )
        select path, start_line, score, library, vendor, version, relative_path,
               heading_path, symbols, content_type, quality_score, content,
               matched_path, source_anchor, token_count, parent_content
        from ranked_files
        order by score desc, path asc, start_line asc
        limit %s
    """
    try:
        with observe_duration("oz_db_query_duration_seconds", {"operation": "search", "mode": "vector" if vector else "fts_symbol"}):
            with connection:
                with connection.cursor() as cursor:
                    cursor.execute(f"set local statement_timeout = {retrieval_statement_timeout_ms()}")
                    cursor.execute(sql, tuple(params))
                    rows = cursor.fetchall()
                    mark_search_versions_requested(cursor, rows)
        return score_postgres_rows(rows, query)
    except VersionResolutionError:
        raise
    except Exception as exc:
        LOGGER.warning("postgres search failed: %s", exc)
        if vector_enabled:
            LOGGER.warning("retrying postgres search with FTS/symbol fallback only")
            return search_from_postgres(ctx, query, library_scope, max_results, fingerprint, vector_enabled=False)
        return None


def candidate_select(fts_score: str, vector_score: str, symbol_score: str) -> str:
    return f"""
        select
          '.codo/vendors/' || v.name || '/' || l.name || '@' || lv.version || '/' || coalesce(p.path, c.path) as path,
          coalesce(p.start_line, c.start_line) as start_line,
          c.path as matched_path,
          coalesce(c.source_anchor, c.source_url) as source_anchor,
          c.token_count,
          {fts_score} as fts_score,
          {vector_score} as vector_score,
          {symbol_score} as symbol_score,
          greatest(coalesce(c.quality_score, 1), 0) as quality_score,
          content_type_score(c.content_type) + content_type_intent_score(c.content_type, %s) as type_score,
          v.name || '/' || l.name as library,
          v.name as vendor,
          lv.version,
          coalesce(p.path, c.path) as relative_path,
          c.heading_path,
          c.symbols,
          c.content_type,
          c.content,
          coalesce(p.content, c.content) as parent_content
        from chunks c
        join library_versions lv on lv.id = c.version_id
        join libraries l on l.id = lv.library_id
        join vendors v on v.id = l.vendor_id
        left join refs r on r.library_id = l.id and r.channel = 'latest'
        left join chunks p on p.id = c.parent_chunk_id
    """


def vector_candidate_cte(where_scope: str) -> str:
    return f"""
        {candidate_select("0::float8", "greatest(1 - (c.embedding <=> %s::vector), 0)", "0::float8")}
        where c.embedding is not null
          and coalesce(c.dedupe_canonical, true)
          {where_scope}
        order by c.embedding <=> %s::vector
        limit %s
    """


def empty_vector_cte() -> str:
    return """
        select null::text as path, null::integer as start_line, null::text as matched_path,
               null::text as source_anchor, null::integer as token_count,
               0::float8 as fts_score, 0::float8 as vector_score, 0::float8 as symbol_score,
               0::float8 as quality_score, 0::float8 as type_score,
               null::text as library, null::text as vendor, null::text as version,
               null::text as relative_path, '[]'::jsonb as heading_path, '[]'::jsonb as symbols,
               null::text as content_type, null::text as content, null::text as parent_content
        where false
    """


def vector_literal(values: list[float]) -> str:
    return "[" + ",".join(f"{value:.8g}" for value in values) + "]"


def normalized_tsquery(query: str) -> str:
    terms = normalize_query(query)
    if terms:
        return " OR ".join(terms)
    return query.strip() or "documentation"


def like_pattern(values: list[str]) -> str:
    compact = [value for value in values if value]
    if not compact:
        return "%"
    return "%" + "%".join(compact[:4]) + "%"


def candidate_limit(max_results: int) -> int:
    return max(max_results * 10, 50)


def score_postgres_rows(rows: list[Any], query: str) -> list[dict[str, Any]]:
    terms = normalize_query(query)
    scored: list[dict[str, Any]] = []
    for row in rows:
        chunk = {
            "path": row[6],
            "heading_path": row[7],
            "symbols": row[8],
            "content_type": row[9],
            "quality_score": row[10],
            "text": row[11],
        }
        score = float(row[2]) + (local_chunk_score(chunk, terms) / 8.0)
        scored.append(
            {
                "path": row[0],
                "line": row[1],
                "score": round(score, 4),
                "library": row[3],
                "vendor": row[4],
                "version": row[5],
                "matched_path": row[12],
                "source_anchor": row[13],
                "content_type": row[9],
                "token_count": int(row[14] or 0),
                "_rerank_text": rerank_text(row),
            }
        )
    scored.sort(key=lambda item: (-float(item["score"]), str(item["path"]), int(item.get("line") or 1)))
    return scored


def rerank_text(row: Any) -> str:
    return "\n".join(
        [
            f"path: {row[0]}",
            f"matched_path: {row[12] or ''}",
            f"content_type: {row[9] or ''}",
            f"headings: {row[7] or []}",
            f"symbols: {row[8] or []}",
            str(row[15] or row[11] or ""),
        ]
    )


def mark_search_versions_requested(cursor: Any, rows: list[Any]) -> None:
    seen: set[tuple[str, str, str]] = set()
    for row in rows[:20]:
        vendor = str(row[4] or "")
        library_full = str(row[3] or "")
        version = str(row[5] or "")
        library = library_full.split("/", 1)[1] if "/" in library_full else library_full
        if vendor and library and version:
            seen.add((vendor, library, version))
    for vendor, library, version in seen:
        cursor.execute(
            """
            update library_versions lv
            set last_requested_at = now()
            from libraries l
            join vendors v on v.id = l.vendor_id
            where lv.library_id = l.id
              and v.name = %s
              and l.name = %s
              and lv.version = %s
            """,
            (vendor, library, version),
        )


def resolve_db_version_id(connection: Any, vendor: str, library: str, requested_version: str | None) -> int:
    with observe_duration("oz_db_query_duration_seconds", {"operation": "resolve_version", "mode": "scope"}):
        with connection.cursor() as cursor:
            cursor.execute(
                """
                select l.id as library_id,
                       l.redirected_to_library_id,
                       rl.name as redirected_library,
                       rv.name as redirected_vendor,
                       l.default_version_id,
                       r.version_id as latest_version_id,
                       lv.id as version_id,
                       lv.version,
                       lv.archived_at
                from libraries l
                join vendors v on v.id = l.vendor_id
                left join libraries rl on rl.id = l.redirected_to_library_id
                left join vendors rv on rv.id = rl.vendor_id
                left join refs r on r.library_id = l.id and r.channel = 'latest'
                left join library_versions lv on lv.library_id = l.id
                where v.name = %s and l.name = %s
                order by lv.created_at desc nulls last
                """,
                (vendor, library),
            )
            columns = [getattr(column, "name", column[0]) for column in cursor.description]
            rows = [dict(zip(columns, row, strict=False)) for row in cursor.fetchall()]

    if not rows:
        raise VersionResolutionError(
            "library_not_found",
            f"library {vendor}/{library} is not indexed",
            payload={"vendor": vendor, "library": library},
        )
    redirected = rows[0].get("redirected_to_library_id")
    if redirected:
        redirect_vendor = str(rows[0].get("redirected_vendor") or "")
        redirect_library = str(rows[0].get("redirected_library") or "")
        raise VersionResolutionError(
            "library_redirected",
            f"library {vendor}/{library} moved to {redirect_vendor}/{redirect_library}",
            status_code=301,
            payload={"vendor": vendor, "library": library, "redirect_library": f"{redirect_vendor}/{redirect_library}"},
        )

    versions = [
        {"id": row["version_id"], "version": row["version"], "archived_at": row.get("archived_at")}
        for row in rows
        if row.get("version_id") is not None and row.get("version")
    ]
    active_versions = [row for row in versions if not row.get("archived_at")]
    if not active_versions:
        raise VersionResolutionError(
            "library_not_finalized",
            f"library {vendor}/{library} exists but has no promoted version yet",
            status_code=202,
            payload={"vendor": vendor, "library": library},
        )

    if requested_version:
        matches = [row for row in active_versions if version_matches(str(row["version"]), requested_version)]
        selected = latest_entry(matches)
        if not selected:
            raise VersionResolutionError(
                "version_not_found",
                f"version {requested_version} is not indexed for {vendor}/{library}",
                payload={
                    "vendor": vendor,
                    "library": library,
                    "requested_version": requested_version,
                    "available_versions": available_versions(active_versions),
                },
            )
        return int(selected["id"])

    default_id = rows[0].get("default_version_id") or rows[0].get("latest_version_id")
    if default_id and any(int(row["id"]) == int(default_id) for row in active_versions):
        return int(default_id)
    selected = latest_entry(active_versions)
    if selected:
        return int(selected["id"])
    raise VersionResolutionError(
        "library_not_finalized",
        f"library {vendor}/{library} exists but has no promoted version yet",
        status_code=202,
        payload={"vendor": vendor, "library": library},
    )


def ref_from_postgres(
    ctx: RetrievalContext,
    vendor: str,
    library: str,
    requested_version: str | None = None,
    *,
    count_usage: bool = True,
) -> dict[str, Any] | None:
    connection = postgres_connection(ctx.database_url)
    if connection is None:
        return None
    with connection:
        version_id = resolve_db_version_id(connection, vendor, library, requested_version)
        with connection.cursor() as cursor:
            if count_usage:
                cursor.execute(
                    """
                    update library_versions
                    set last_requested_at = now(), pull_count = pull_count + 1
                    where id = %s
                    """,
                    (version_id,),
                )
            cursor.execute(
                """
                select v.name as vendor,
                       l.name as library,
                       lv.version,
                       lv.ref_sha,
                       lv.pack_key,
                       lv.pull_count,
                       lv.last_crawled_at::text,
                       lv.indexed_at::text,
                       array(
                         select av.version
                         from library_versions av
                         where av.library_id = l.id and av.archived_at is null
                       ) as versions
                from library_versions lv
                join libraries l on l.id = lv.library_id
                join vendors v on v.id = l.vendor_id
                where lv.id = %s
                """,
                (version_id,),
            )
            row = cursor.fetchone()
            if row is None:
                return None
            versions = sorted([str(item) for item in (row[8] or [])], key=cmp_to_key(compare_versions), reverse=True)
            return {
                "vendor": row[0],
                "library": row[1],
                "version": row[2],
                "ref_sha": row[3],
                "pack_key": row[4],
                "pull_count": int(row[5] or 0),
                "last_crawled_at": row[6],
                "indexed_at": row[7],
                "available_versions": versions,
            }
