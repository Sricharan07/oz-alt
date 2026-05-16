from __future__ import annotations

import hashlib
import json
import os
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Any
from urllib import request

from oz_api.storage import RegistryStorage, normalize_query

_OPENAI_API_KEY_CACHE: str | None = None


@dataclass(frozen=True)
class RetrievalContext:
    storage: RegistryStorage
    database_url: str | None = None
    db_resource_arn: str | None = None
    db_secret_arn: str | None = None
    db_name: str = "oz"
    rerank_table: str | None = None
    openai_api_key: str | None = None

    @classmethod
    def from_env(cls, storage: RegistryStorage) -> "RetrievalContext":
        return cls(
            storage=storage,
            database_url=os.environ.get("OZ_DATABASE_URL") or os.environ.get("DATABASE_URL"),
            db_resource_arn=os.environ.get("OZ_DB_RESOURCE_ARN"),
            db_secret_arn=os.environ.get("OZ_DB_SECRET_ARN"),
            db_name=os.environ.get("OZ_DB_NAME", "oz"),
            rerank_table=os.environ.get("OZ_RERANK_TABLE"),
            openai_api_key=openai_api_key_from_env(),
        )


def suggest(ctx: RetrievalContext, query: str, max_results: int, fingerprint: str = "") -> list[dict[str, Any]]:
    rows = suggest_from_postgres(ctx, query, max_results, fingerprint)
    if rows is None:
        rows = suggest_from_catalog(ctx.storage, query, max_results)
    rows = boost_named_suggestions(query, rows)
    return maybe_rerank(ctx, "suggest", query, fingerprint, rows)


def search(
    ctx: RetrievalContext,
    query: str,
    *,
    library_scope: str | None,
    max_results: int,
    fingerprint: str = "",
) -> list[dict[str, Any]]:
    rows = search_from_postgres(ctx, query, library_scope, max_results, fingerprint)
    if rows is None:
        rows = search_from_fixtures(ctx.storage, query, library_scope=library_scope, max_results=max_results)
    return maybe_rerank(ctx, f"search:{library_scope or '*'}", query, fingerprint, rows)


def suggest_from_catalog(storage: RegistryStorage, query: str, max_results: int) -> list[dict[str, Any]]:
    terms = normalize_query(query)
    rows: list[tuple[int, dict[str, Any]]] = []
    for entry in storage.load_catalog():
        haystack = " ".join(
            [
                entry.get("vendor", ""),
                entry.get("library", ""),
                entry.get("version", ""),
                entry.get("description", ""),
                " ".join(entry.get("keywords", [])),
            ]
        ).lower()
        score = sum(haystack.count(term) for term in terms)
        if score:
            rows.append((score, entry))
    rows.sort(key=lambda item: (-item[0], item[1].get("vendor", ""), item[1].get("library", "")))
    return [
        {
            "vendor": entry["vendor"],
            "library": entry["library"],
            "version": entry["version"],
            "score": score,
            "reason": entry.get("description", ""),
        }
        for score, entry in rows[:max_results]
    ]


def search_from_fixtures(
    storage: RegistryStorage,
    query: str,
    *,
    library_scope: str | None,
    max_results: int,
) -> list[dict[str, Any]]:
    terms = normalize_query(query)
    scope_vendor, scope_library = parse_scope(library_scope)
    hits: list[dict[str, Any]] = []

    for fixture in storage.fixtures_root.glob("*/*/*"):
        if not fixture.is_dir():
            continue
        vendor, library, version = fixture.parts[-3:]
        if scope_vendor and (vendor != scope_vendor or library != scope_library):
            continue
        chunk_path = fixture / "_chunks.jsonl"
        if chunk_path.exists():
            for row in read_jsonl(chunk_path):
                normalized = str(row.get("text", "")).lower()
                score = sum(1 for term in terms if term in normalized)
                if score == 0:
                    continue
                hits.append(
                    {
                        "path": f".codo/vendors/{vendor}/{library}@{version}/{row.get('path')}",
                        "line": 1,
                        "score": score,
                        "library": f"{vendor}/{library}",
                        "vendor": vendor,
                        "version": version,
                    }
                )
            continue
        for path in fixture.rglob("*.md"):
            relative = path.relative_to(fixture)
            for line_number, line in enumerate(path.read_text(encoding="utf-8").splitlines(), start=1):
                normalized = line.lower()
                score = sum(1 for term in terms if term in normalized)
                if score == 0:
                    continue
                hits.append(
                    {
                        "path": f".codo/vendors/{vendor}/{library}@{version}/{relative.as_posix()}",
                        "line": line_number,
                        "score": score,
                        "library": f"{vendor}/{library}",
                        "vendor": vendor,
                        "version": version,
                    }
                )

    hits.sort(key=lambda hit: (-hit["score"], hit["path"], hit["line"]))
    deduped: list[dict[str, Any]] = []
    seen: set[tuple[str, int | None]] = set()
    for hit in hits:
        key = (str(hit["path"]), hit.get("line"))
        if key in seen:
            continue
        seen.add(key)
        deduped.append(hit)
        if len(deduped) >= max_results:
            break
    return deduped


def suggest_from_postgres(
    ctx: RetrievalContext,
    query: str,
    max_results: int,
    fingerprint: str,
) -> list[dict[str, Any]] | None:
    data_api_rows = suggest_from_data_api(ctx, query, max_results)
    if data_api_rows is not None:
        return data_api_rows

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
                0::float8 as vector_score
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
                greatest(1 - (c.embedding <=> %s::vector), 0) as vector_score
              from chunks c
              join library_versions lv on lv.id = c.version_id
              join libraries l on l.id = lv.library_id
              join vendors v on v.id = l.vendor_id
              where c.embedding is not null
              order by c.embedding <=> %s::vector
              limit %s
            ),
            ranked as (
              select vendor, library, version, max(reason) as reason, max(fts_score) + max(vector_score) as score
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
              ) as score,
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
    data_api_rows = search_from_data_api(ctx, query, library_scope, max_results)
    if data_api_rows is not None:
        return data_api_rows

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
                v.name || '/' || l.name as library,
                v.name as vendor,
                lv.version
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
                v.name || '/' || l.name as library,
                v.name as vendor,
                lv.version
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
              select path, start_line, max(fts_score) + max(vector_score) as score, library, vendor, version
              from (
                select * from fts_candidates
                union all
                select * from vector_candidates
              ) candidates
              group by path, start_line, library, vendor, version
            )
            select path, start_line, score, library, vendor, version
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
              greatest(ts_rank_cd(c.search_document, websearch_to_tsquery('english', %s)), 0) as score,
              v.name || '/' || l.name as library,
              v.name as vendor,
              lv.version
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
        return [
            {
                "path": row[0],
                "line": row[1],
                "score": float(row[2]),
                "library": row[3],
                "vendor": row[4],
                "version": row[5],
            }
            for row in rows
        ]
    except Exception:
        return None


def suggest_from_data_api(
    ctx: RetrievalContext,
    query: str,
    max_results: int,
) -> list[dict[str, Any]] | None:
    terms = normalized_tsquery(query)
    embedding = embedding_for_query(ctx, query)
    vector = vector_literal(embedding) if embedding else None
    candidates = candidate_limit(max_results)
    params: list[dict[str, Any]] = [
        {"name": "terms", "value": {"stringValue": terms}},
        {"name": "max_results", "value": {"longValue": max_results}},
    ]
    if vector:
        params.append({"name": "embedding", "value": {"stringValue": vector}})
        params.append({"name": "candidate_limit", "value": {"longValue": candidates}})
        sql = """
            with fts_candidates as (
              select
                v.name as vendor,
                l.name as library,
                lv.version,
                coalesce(l.description, '') as reason,
                greatest(
                  coalesce(ts_rank_cd(l.search_document, websearch_to_tsquery('english', :terms)), 0),
                  coalesce(ts_rank_cd(c.search_document, websearch_to_tsquery('english', :terms)), 0)
                ) as fts_score,
                0::float8 as vector_score
              from libraries l
              join vendors v on v.id = l.vendor_id
              join library_versions lv on lv.library_id = l.id
              left join chunks c on c.version_id = lv.id
              where l.search_document @@ websearch_to_tsquery('english', :terms)
                 or c.search_document @@ websearch_to_tsquery('english', :terms)
              order by fts_score desc, v.name asc, l.name asc
              limit :candidate_limit
            ),
            vector_candidates as (
              select
                v.name as vendor,
                l.name as library,
                lv.version,
                coalesce(l.description, '') as reason,
                0::float8 as fts_score,
                greatest(1 - (c.embedding <=> (:embedding)::vector), 0) as vector_score
              from chunks c
              join library_versions lv on lv.id = c.version_id
              join libraries l on l.id = lv.library_id
              join vendors v on v.id = l.vendor_id
              where c.embedding is not null
              order by c.embedding <=> (:embedding)::vector
              limit :candidate_limit
            ),
            ranked as (
              select vendor, library, version, max(reason) as reason, max(fts_score) + max(vector_score) as score
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
            limit :max_results
        """
    else:
        sql = """
            select
              v.name as vendor,
              l.name as library,
              lv.version,
              max(
                greatest(
                  coalesce(ts_rank_cd(l.search_document, websearch_to_tsquery('english', :terms)), 0),
                  coalesce(ts_rank_cd(c.search_document, websearch_to_tsquery('english', :terms)), 0)
                )
              ) as score,
              coalesce(l.description, '') as reason
            from libraries l
            join vendors v on v.id = l.vendor_id
            join library_versions lv on lv.library_id = l.id
            left join chunks c on c.version_id = lv.id
            where l.search_document @@ websearch_to_tsquery('english', :terms)
               or c.search_document @@ websearch_to_tsquery('english', :terms)
            group by v.name, l.name, lv.version, l.description
            order by score desc, v.name asc, l.name asc, lv.version asc
            limit :max_results
        """
    rows = execute_data_api(ctx, sql, params)
    if rows is None:
        return None
    return [
        {
            "vendor": string_field(row[0]),
            "library": string_field(row[1]),
            "version": string_field(row[2]),
            "score": numeric_field(row[3]),
            "reason": string_field(row[4]),
        }
        for row in rows
    ]


def search_from_data_api(
    ctx: RetrievalContext,
    query: str,
    library_scope: str | None,
    max_results: int,
) -> list[dict[str, Any]] | None:
    terms = normalized_tsquery(query)
    embedding = embedding_for_query(ctx, query)
    vector = vector_literal(embedding) if embedding else None
    scope_vendor, scope_library = parse_scope(library_scope)
    where_scope = ""
    candidates = candidate_limit(max_results)
    params: list[dict[str, Any]] = [
        {"name": "terms", "value": {"stringValue": terms}},
        {"name": "max_results", "value": {"longValue": max_results}},
    ]
    if vector:
        params.append({"name": "embedding", "value": {"stringValue": vector}})
        params.append({"name": "candidate_limit", "value": {"longValue": candidates}})
    if scope_vendor:
        where_scope = "and v.name = :vendor and l.name = :library"
        params.extend(
            [
                {"name": "vendor", "value": {"stringValue": scope_vendor}},
                {"name": "library", "value": {"stringValue": scope_library or ""}},
            ]
        )
    if vector:
        sql = f"""
            with fts_candidates as (
              select
                '.codo/vendors/' || v.name || '/' || l.name || '@' || lv.version || '/' || c.path as path,
                c.start_line,
                greatest(ts_rank_cd(c.search_document, websearch_to_tsquery('english', :terms)), 0) as fts_score,
                0::float8 as vector_score,
                v.name || '/' || l.name as library,
                v.name as vendor,
                lv.version
              from chunks c
              join library_versions lv on lv.id = c.version_id
              join libraries l on l.id = lv.library_id
              join vendors v on v.id = l.vendor_id
              where c.search_document @@ websearch_to_tsquery('english', :terms)
              {where_scope}
              order by fts_score desc, path asc, c.start_line asc
              limit :candidate_limit
            ),
            vector_candidates as (
              select
                '.codo/vendors/' || v.name || '/' || l.name || '@' || lv.version || '/' || c.path as path,
                c.start_line,
                0::float8 as fts_score,
                greatest(1 - (c.embedding <=> (:embedding)::vector), 0) as vector_score,
                v.name || '/' || l.name as library,
                v.name as vendor,
                lv.version
              from chunks c
              join library_versions lv on lv.id = c.version_id
              join libraries l on l.id = lv.library_id
              join vendors v on v.id = l.vendor_id
              where c.embedding is not null
              {where_scope}
              order by c.embedding <=> (:embedding)::vector
              limit :candidate_limit
            ),
            ranked as (
              select path, start_line, max(fts_score) + max(vector_score) as score, library, vendor, version
              from (
                select * from fts_candidates
                union all
                select * from vector_candidates
              ) candidates
              group by path, start_line, library, vendor, version
            )
            select path, start_line, score, library, vendor, version
            from ranked
            order by score desc, path asc, start_line asc
            limit :max_results
        """
    else:
        sql = f"""
            select
              '.codo/vendors/' || v.name || '/' || l.name || '@' || lv.version || '/' || c.path as path,
              c.start_line,
              greatest(ts_rank_cd(c.search_document, websearch_to_tsquery('english', :terms)), 0) as score,
              v.name || '/' || l.name as library,
              v.name as vendor,
              lv.version
            from chunks c
            join library_versions lv on lv.id = c.version_id
            join libraries l on l.id = lv.library_id
            join vendors v on v.id = l.vendor_id
            where c.search_document @@ websearch_to_tsquery('english', :terms)
            {where_scope}
            order by score desc, path asc, c.start_line asc
            limit :max_results
        """
    rows = execute_data_api(ctx, sql, params)
    if rows is None:
        return None
    return [
        {
            "path": string_field(row[0]),
            "line": int(numeric_field(row[1])),
            "score": numeric_field(row[2]),
            "library": string_field(row[3]),
            "vendor": string_field(row[4]),
            "version": string_field(row[5]),
        }
        for row in rows
    ]


def execute_data_api(
    ctx: RetrievalContext,
    sql: str,
    parameters: list[dict[str, Any]],
) -> list[list[dict[str, Any]]] | None:
    if not ctx.db_resource_arn or not ctx.db_secret_arn:
        return None
    client = rds_data_client()
    if client is None:
        return None
    try:
        response = client.execute_statement(
            resourceArn=ctx.db_resource_arn,
            secretArn=ctx.db_secret_arn,
            database=ctx.db_name,
            sql=sql,
            parameters=parameters,
        )
        return list(response.get("records", []))
    except Exception:
        return None


def string_field(field: dict[str, Any]) -> str:
    if "stringValue" in field:
        return str(field["stringValue"])
    if "longValue" in field:
        return str(field["longValue"])
    if "doubleValue" in field:
        return str(field["doubleValue"])
    return ""


def numeric_field(field: dict[str, Any]) -> float:
    if "doubleValue" in field:
        return float(field["doubleValue"])
    if "longValue" in field:
        return float(field["longValue"])
    if "stringValue" in field:
        try:
            return float(field["stringValue"])
        except ValueError:
            return 0.0
    return 0.0


def maybe_rerank(
    ctx: RetrievalContext,
    route: str,
    query: str,
    fingerprint: str,
    rows: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    if len(rows) < 2 or clear_winner(rows):
        return rows

    cache_key = rerank_cache_key(route, query, fingerprint)
    cached = get_rerank_cache(ctx, cache_key)
    if cached is not None:
        return cached

    reranked = openai_rerank(ctx.openai_api_key, query, rows[:20]) or rows
    put_rerank_cache(ctx, cache_key, reranked)
    return reranked


def clear_winner(rows: list[dict[str, Any]]) -> bool:
    scores = [float(row.get("score", 0) or 0) for row in rows[:3]]
    return len(scores) == 3 and all(score > 0.85 for score in scores)


def boost_named_suggestions(query: str, rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    query_terms = set(normalize_query(query))
    if not query_terms:
        return rows
    boosted: list[dict[str, Any]] = []
    for row in rows:
        copy = dict(row)
        library_terms = set(normalize_query(str(copy.get("library") or "")))
        vendor_terms = set(normalize_query(str(copy.get("vendor") or "")))
        score = float(copy.get("score", 0) or 0)
        if library_terms and library_terms.issubset(query_terms):
            score += 25.0
        if vendor_terms and vendor_terms.issubset(query_terms):
            score += 10.0
        copy["score"] = score
        boosted.append(copy)
    boosted.sort(
        key=lambda row: (
            -float(row.get("score", 0) or 0),
            str(row.get("vendor") or ""),
            str(row.get("library") or ""),
            str(row.get("version") or ""),
        )
    )
    return boosted


def openai_rerank(api_key: str | None, query: str, rows: list[dict[str, Any]]) -> list[dict[str, Any]] | None:
    if not api_key:
        return None
    payload = {
        "model": os.environ.get("OZ_RERANK_MODEL", "gpt-4o-mini"),
        "messages": [
            {
                "role": "system",
                "content": "Rank documentation search results for a coding agent. Return JSON array of zero-based indexes only.",
            },
            {"role": "user", "content": json.dumps({"query": query, "results": rows})},
        ],
        "temperature": 0,
    }
    data = json.dumps(payload).encode("utf-8")
    req = request.Request(
        "https://api.openai.com/v1/chat/completions",
        data=data,
        headers={"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"},
        method="POST",
    )
    try:
        with request.urlopen(req, timeout=8) as response:
            body = json.loads(response.read().decode("utf-8"))
        content = body["choices"][0]["message"]["content"]
        order = json.loads(content)
        if not isinstance(order, list):
            return None
        ranked = [rows[idx] for idx in order if isinstance(idx, int) and 0 <= idx < len(rows)]
        seen = {id(row) for row in ranked}
        ranked.extend(row for row in rows if id(row) not in seen)
        return ranked
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


def openai_api_key_from_env() -> str | None:
    direct = normalized_openai_api_key(os.environ.get("OPENAI_API_KEY"))
    if direct:
        return direct

    secret_arn = os.environ.get("OPENAI_API_KEY_SECRET_ARN") or os.environ.get("OZ_OPENAI_API_KEY_SECRET_ARN")
    if not secret_arn:
        return None

    global _OPENAI_API_KEY_CACHE
    if _OPENAI_API_KEY_CACHE is not None:
        return _OPENAI_API_KEY_CACHE

    try:
        import boto3  # type: ignore

        response = boto3.client("secretsmanager").get_secret_value(SecretId=secret_arn)
    except Exception:
        return None

    value = secret_value_text(response)
    key = normalized_openai_api_key(value)
    if not key:
        key = normalized_openai_api_key_from_json(value)
    if key:
        _OPENAI_API_KEY_CACHE = key
    return key


def secret_value_text(response: dict[str, Any]) -> str:
    if response.get("SecretString"):
        return str(response["SecretString"])
    binary = response.get("SecretBinary")
    if isinstance(binary, bytes):
        return binary.decode("utf-8", errors="replace")
    return ""


def normalized_openai_api_key(value: str | None) -> str | None:
    key = str(value or "").strip()
    return key if key.startswith("sk-") else None


def normalized_openai_api_key_from_json(value: str) -> str | None:
    try:
        payload = json.loads(value)
    except Exception:
        return None
    if not isinstance(payload, dict):
        return None
    for field in ("OPENAI_API_KEY", "openai_api_key", "api_key"):
        key = normalized_openai_api_key(payload.get(field))
        if key:
            return key
    return None


def normalized_tsquery(query: str) -> str:
    terms = normalize_query(query)
    if terms:
        return " OR ".join(terms)
    return query.strip() or "documentation"


def candidate_limit(max_results: int) -> int:
    return max(max_results * 10, 50)


def rerank_cache_key(route: str, query: str, fingerprint: str) -> str:
    digest = hashlib.sha256(f"{route}\0{query}\0{fingerprint}".encode("utf-8")).hexdigest()
    return f"rerank:{digest}"


def get_rerank_cache(ctx: RetrievalContext, cache_key: str) -> list[dict[str, Any]] | None:
    client = dynamodb_client()
    if client is None or not ctx.rerank_table:
        return None
    try:
        response = client.get_item(TableName=ctx.rerank_table, Key={"cache_key": {"S": cache_key}})
        item = response.get("Item")
        if not item:
            return None
        expires_at = int(item.get("expires_at", {}).get("N", "0"))
        if expires_at < int(time.time()):
            return None
        return json.loads(item["payload"]["S"])
    except Exception:
        return None


def put_rerank_cache(ctx: RetrievalContext, cache_key: str, rows: list[dict[str, Any]]) -> None:
    client = dynamodb_client()
    if client is None or not ctx.rerank_table:
        return
    try:
        client.put_item(
            TableName=ctx.rerank_table,
            Item={
                "cache_key": {"S": cache_key},
                "expires_at": {"N": str(int(time.time()) + 7 * 24 * 60 * 60)},
                "payload": {"S": json.dumps(rows, sort_keys=True)},
            },
        )
    except Exception:
        return


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


def dynamodb_client() -> Any | None:
    try:
        import boto3  # type: ignore
    except ImportError:
        return None
    try:
        return boto3.client("dynamodb")
    except Exception:
        return None


def rds_data_client() -> Any | None:
    try:
        import boto3  # type: ignore
    except ImportError:
        return None
    try:
        return boto3.client("rds-data")
    except Exception:
        return None


def unique_libraries_to_pull(results: list[dict[str, Any]]) -> list[dict[str, str]]:
    seen: set[tuple[str, str, str]] = set()
    output: list[dict[str, str]] = []
    for result in results:
        vendor = result["vendor"]
        library = result["library"].split("/", 1)[1]
        version = result["version"]
        key = (vendor, library, version)
        if key in seen:
            continue
        seen.add(key)
        output.append({"vendor": vendor, "library": library, "version": version})
    return output


def latest_entry(storage: RegistryStorage, vendor: str, library: str) -> dict[str, Any] | None:
    matches = [
        entry
        for entry in storage.load_catalog()
        if entry.get("vendor") == vendor and entry.get("library") == library
    ]
    if not matches:
        return None
    matches.sort(key=lambda entry: entry.get("version", ""))
    return matches[-1]


def parse_scope(scope: str | None) -> tuple[str | None, str | None]:
    if not scope:
        return None, None
    if "/" not in scope:
        return "npm", scope
    vendor, library = scope.split("/", 1)
    return vendor, library


def read_jsonl(path: Path) -> list[dict[str, Any]]:
    if not path.exists():
        return []
    rows: list[dict[str, Any]] = []
    for line in path.read_text(encoding="utf-8").splitlines():
        if line.strip():
            rows.append(json.loads(line))
    return rows
