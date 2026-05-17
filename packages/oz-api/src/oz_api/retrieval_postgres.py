from __future__ import annotations

import json
import os
from typing import Any
from urllib import request

from oz_api.ranking import local_chunk_score
from oz_api.retrieval_common import parse_scope
from oz_api.retrieval_context import RetrievalContext
from oz_api.storage import normalize_query

def suggest_from_postgres(
    ctx: RetrievalContext,
    query: str,
    max_results: int,
    fingerprint: str,
) -> list[dict[str, Any]] | None:
    connection = postgres_connection(ctx.database_url)
    if connection is None:
        return None
    terms = normalized_tsquery(query)
    embedding = embedding_for_query(ctx, query)
    vector = vector_literal(embedding) if embedding else None
    candidates = candidate_limit(max_results)
    if vector:
        sql = """
            with fts_candidates as (
              select
                v.name as vendor,
                l.name as library,
                lv.version,
                coalesce(l.description, '') as reason,
                greatest(
                  coalesce(ts_rank_cd(l.search_document, websearch_to_tsquery('english', %s)), 0),
                  coalesce(ts_rank_cd(c.search_document, websearch_to_tsquery('english', %s)), 0)
                ) as fts_score,
                0::float8 as vector_score,
                greatest(coalesce(c.quality_score, 1), 0) as quality_score,
                content_type_score(c.content_type) as type_score
              from libraries l
              join vendors v on v.id = l.vendor_id
              join library_versions lv on lv.library_id = l.id
              left join chunks c on c.version_id = lv.id
              where l.search_document @@ websearch_to_tsquery('english', %s)
                 or c.search_document @@ websearch_to_tsquery('english', %s)
              order by fts_score desc, v.name asc, l.name asc
              limit %s
            ),
            vector_candidates as (
              select
                v.name as vendor,
                l.name as library,
                lv.version,
                coalesce(l.description, '') as reason,
                0::float8 as fts_score,
                greatest(1 - (c.embedding <=> %s::vector), 0) as vector_score,
                greatest(coalesce(c.quality_score, 1), 0) as quality_score,
                content_type_score(c.content_type) as type_score
              from chunks c
              join library_versions lv on lv.id = c.version_id
              join libraries l on l.id = lv.library_id
              join vendors v on v.id = l.vendor_id
              where c.embedding is not null
              order by c.embedding <=> %s::vector
              limit %s
            ),
            ranked as (
              select
                vendor,
                library,
                version,
                max(reason) as reason,
                max(fts_score) + max(vector_score) + (max(quality_score) * 0.15) + max(type_score) as score
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
            select
              v.name as vendor,
              l.name as library,
              lv.version,
              max(
                greatest(
                  coalesce(ts_rank_cd(l.search_document, websearch_to_tsquery('english', %s)), 0),
                  coalesce(ts_rank_cd(c.search_document, websearch_to_tsquery('english', %s)), 0)
                )
              ) + (max(greatest(coalesce(c.quality_score, 1), 0)) * 0.15) + max(content_type_score(c.content_type)) as score,
              coalesce(l.description, '') as reason
            from libraries l
            join vendors v on v.id = l.vendor_id
            join library_versions lv on lv.library_id = l.id
            left join chunks c on c.version_id = lv.id
            where l.search_document @@ websearch_to_tsquery('english', %s)
               or c.search_document @@ websearch_to_tsquery('english', %s)
            group by v.name, l.name, lv.version, l.description
            order by score desc, v.name asc, l.name asc, lv.version asc
            limit %s
        """
        params = [terms, terms, terms, terms, max_results]
    try:
        with connection:
            with connection.cursor() as cursor:
                cursor.execute(sql, tuple(params))
                rows = cursor.fetchall()
        return [
            {
                "vendor": row[0],
                "library": row[1],
                "version": row[2],
                "score": float(row[3]),
                "reason": row[4],
            }
            for row in rows
        ]
    except Exception:
        return None

def search_from_postgres(
    ctx: RetrievalContext,
    query: str,
    library_scope: str | None,
    max_results: int,
    fingerprint: str,
) -> list[dict[str, Any]] | None:
    connection = postgres_connection(ctx.database_url)
    if connection is None:
        return None
    terms = normalized_tsquery(query)
    embedding = embedding_for_query(ctx, query)
    vector = vector_literal(embedding) if embedding else None
    scope_vendor, scope_library = parse_scope(library_scope)
    where_scope = ""
    candidates = candidate_limit(max_results)
    if vector:
        where_scope = "and v.name = %s and l.name = %s" if scope_vendor else ""
        fts_params: list[Any] = [terms, terms]
        vector_params: list[Any] = [vector]
        if scope_vendor:
            fts_params.extend([scope_vendor, scope_library])
            vector_params.extend([scope_vendor, scope_library])
        fts_params.append(candidates)
        vector_params.extend([vector, candidates, max_results])
        params = fts_params + vector_params
        sql = f"""
            with fts_candidates as (
              select
                '.codo/vendors/' || v.name || '/' || l.name || '@' || lv.version || '/' || c.path as path,
                c.start_line,
                greatest(ts_rank_cd(c.search_document, websearch_to_tsquery('english', %s)), 0) as fts_score,
                0::float8 as vector_score,
                greatest(coalesce(c.quality_score, 1), 0) as quality_score,
                content_type_score(c.content_type) as type_score,
                v.name || '/' || l.name as library,
                v.name as vendor,
                lv.version,
                c.path as relative_path,
                c.heading_path,
                c.symbols,
                c.content_type,
                c.content
              from chunks c
              join library_versions lv on lv.id = c.version_id
              join libraries l on l.id = lv.library_id
              join vendors v on v.id = l.vendor_id
              where c.search_document @@ websearch_to_tsquery('english', %s)
              {where_scope}
              order by fts_score desc, path asc, c.start_line asc
              limit %s
            ),
            vector_candidates as (
              select
                '.codo/vendors/' || v.name || '/' || l.name || '@' || lv.version || '/' || c.path as path,
                c.start_line,
                0::float8 as fts_score,
                greatest(1 - (c.embedding <=> %s::vector), 0) as vector_score,
                greatest(coalesce(c.quality_score, 1), 0) as quality_score,
                content_type_score(c.content_type) as type_score,
                v.name || '/' || l.name as library,
                v.name as vendor,
                lv.version,
                c.path as relative_path,
                c.heading_path,
                c.symbols,
                c.content_type,
                c.content
              from chunks c
              join library_versions lv on lv.id = c.version_id
              join libraries l on l.id = lv.library_id
              join vendors v on v.id = l.vendor_id
              where c.embedding is not null
              {where_scope}
              order by c.embedding <=> %s::vector
              limit %s
            ),
            ranked as (
              select
                path,
                start_line,
                max(fts_score) + max(vector_score) + (max(quality_score) * 0.15) + max(type_score) as score,
                library,
                vendor,
                version,
                relative_path,
                heading_path,
                symbols,
                content_type,
                max(quality_score) as quality_score,
                content
              from (
                select * from fts_candidates
                union all
                select * from vector_candidates
              ) candidates
              group by path, start_line, library, vendor, version, relative_path, heading_path, symbols, content_type, content
            )
            select path, start_line, score, library, vendor, version, relative_path, heading_path, symbols, content_type, quality_score, content
            from ranked
            order by score desc, path asc, start_line asc
            limit %s
        """
    else:
        if scope_vendor:
            where_scope = "and v.name = %s and l.name = %s"
            params = [terms, terms, scope_vendor, scope_library, max_results]
        else:
            params = [terms, terms, max_results]
        sql = f"""
            select
              '.codo/vendors/' || v.name || '/' || l.name || '@' || lv.version || '/' || c.path as path,
              c.start_line,
              greatest(ts_rank_cd(c.search_document, websearch_to_tsquery('english', %s)), 0)
                + (greatest(coalesce(c.quality_score, 1), 0) * 0.15)
                + content_type_score(c.content_type) as score,
              v.name || '/' || l.name as library,
              v.name as vendor,
              lv.version,
              c.path as relative_path,
              c.heading_path,
              c.symbols,
              c.content_type,
              greatest(coalesce(c.quality_score, 1), 0) as quality_score,
              c.content
            from chunks c
            join library_versions lv on lv.id = c.version_id
            join libraries l on l.id = lv.library_id
            join vendors v on v.id = l.vendor_id
            where c.search_document @@ websearch_to_tsquery('english', %s)
            {where_scope}
            order by score desc, path asc, c.start_line asc
            limit %s
        """
    try:
        with connection:
            with connection.cursor() as cursor:
                cursor.execute(sql, tuple(params))
                rows = cursor.fetchall()
        return score_postgres_rows(rows, query)
    except Exception:
        return None

def embedding_for_query(ctx: RetrievalContext, query: str) -> list[float] | None:
    if not ctx.openai_api_key:
        return None
    payload = {
        "model": os.environ.get("OZ_EMBEDDING_MODEL", "text-embedding-3-small"),
        "input": query,
    }
    req = request.Request(
        "https://api.openai.com/v1/embeddings",
        data=json.dumps(payload).encode("utf-8"),
        headers={
            "Authorization": f"Bearer {ctx.openai_api_key}",
            "Content-Type": "application/json",
        },
        method="POST",
    )
    try:
        with request.urlopen(req, timeout=8) as response:
            body = json.loads(response.read().decode("utf-8"))
        embedding = body["data"][0]["embedding"]
        if isinstance(embedding, list):
            return [float(value) for value in embedding]
    except Exception:
        return None
    return None

def vector_literal(values: list[float]) -> str:
    return "[" + ",".join(f"{value:.8g}" for value in values) + "]"

def normalized_tsquery(query: str) -> str:
    terms = normalize_query(query)
    if terms:
        return " OR ".join(terms)
    return query.strip() or "documentation"

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
            }
        )
    scored.sort(key=lambda item: (-float(item["score"]), str(item["path"]), int(item.get("line") or 1)))
    return scored

def postgres_connection(database_url: str | None) -> Any | None:
    if not database_url:
        return None
    try:
        import psycopg  # type: ignore
    except ImportError:
        return None
    try:
        return psycopg.connect(database_url)
    except Exception:
        return None
