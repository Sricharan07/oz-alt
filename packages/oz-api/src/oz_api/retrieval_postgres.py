from __future__ import annotations

import logging
import re
from functools import cmp_to_key
from typing import Any

from oz_api.embeddings import embedding_for_query
from oz_api.db import postgres_connection
from oz_api.intent import plan_query
from oz_api.observability import observe_duration
from oz_api.ranking import planned_chunk_score
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
                       coalesce(ts_rank_cd(setweight(to_tsvector('english', coalesce(l.aliases::text, '')), 'A'), websearch_to_tsquery('english', %s)), 0),
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
                 or setweight(to_tsvector('english', coalesce(l.aliases::text, '')), 'A') @@ websearch_to_tsquery('english', %s)
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
        params: list[Any] = [terms, terms, terms, terms, terms, terms, candidates, vector, vector, candidates, max_results]
    else:
        sql = """
            select v.name as vendor, l.name as library, lv.version,
                   max(greatest(
                     coalesce(ts_rank_cd(l.search_document, websearch_to_tsquery('english', %s)), 0),
                     coalesce(ts_rank_cd(setweight(to_tsvector('english', coalesce(l.aliases::text, '')), 'A'), websearch_to_tsquery('english', %s)), 0),
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
               or setweight(to_tsvector('english', coalesce(l.aliases::text, '')), 'A') @@ websearch_to_tsquery('english', %s)
               or c.search_document @@ websearch_to_tsquery('english', %s)
            group by v.name, l.name, lv.version, l.description
            order by score desc, v.name asc, l.name asc, lv.version asc
            limit %s
        """
        params = [terms, terms, terms, terms, terms, terms, max_results]
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
    content_types: list[str] | None = None,
) -> list[dict[str, Any]] | None:
    connection = postgres_connection(ctx.database_url)
    if connection is None:
        return None
    query_plan = plan_query(query)
    terms = normalized_tsquery(query_plan.important_terms or query)
    intent = query_plan.content_type
    legacy_requested = legacy_query(query)
    query_intent = query_plan
    symbol_pattern = like_pattern(query_intent.symbols) if query_intent.symbols else "__oz_no_exact_symbol_match__"
    exact_symbol_keys = [compact_key(symbol) for symbol in query_intent.symbols if compact_key(symbol)]
    exact_symbol_paths = [f"_symbols/{symbol}.md".lower() for symbol in query_intent.symbols]
    exact_path_patterns = [f"%/{slug}.md" for slug in query_intent.slugs if slug]
    exact_path_patterns.extend(f"%/{slug}/%" for slug in query_intent.slugs if slug)
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
    content_filter = "and c.content_type = any(%s)" if content_types else ""
    candidates = candidate_limit(max_results)
    params: list[Any] = [terms, terms, terms, terms, intent, terms]
    if scope_vendor:
        params.extend([scope_vendor, scope_library, scope_version_id])
    if content_types:
        params.append(content_types)
    params.append(candidates)
    vector_cte = empty_vector_cte()
    if vector:
        vector_cte = vector_candidate_cte(where_scope, content_filter)
        params.extend([vector, intent])
        if scope_vendor:
            params.extend([scope_vendor, scope_library, scope_version_id])
        if content_types:
            params.append(content_types)
        params.append(candidates)
    params.extend(
        [
            exact_symbol_paths,
            exact_symbol_keys,
            exact_symbol_keys,
            exact_path_patterns,
            [compact_key(phrase) for phrase in query_intent.phrases if compact_key(phrase)],
            intent,
            exact_symbol_paths,
            exact_symbol_keys,
            exact_symbol_keys,
            exact_path_patterns,
            [compact_key(phrase) for phrase in query_intent.phrases if compact_key(phrase)],
            symbol_pattern,
            symbol_pattern,
            symbol_pattern,
        ]
    )
    if scope_vendor:
        params.extend([scope_vendor, scope_library, scope_version_id])
    if content_types:
        params.append(content_types)
    params.extend([candidates, max_results])
    sql = f"""
        with fts_candidates as (
          select *
          from (
            select ranked_fts.*,
                   1.0 / (60 + row_number() over (order by fts_score desc, path asc, start_line asc)) as rrf_score
            from (
              {candidate_select(fielded_fts_score_expr(), "0::float8", "0::float8")}
              where c.search_document @@ websearch_to_tsquery('english', %s)
                and coalesce(c.dedupe_canonical, true)
                {where_scope}
                {content_filter}
            ) ranked_fts
          ) fused_fts
          order by fts_score desc, path asc, start_line asc
          limit %s
        ),
        vector_candidates as (
          {vector_cte}
        ),
        exact_candidates as (
          select *
          from (
            select ranked_exact.*,
                   1.0 / (60 + row_number() over (order by exact_score desc, path asc, start_line asc)) as rrf_score
            from (
              {candidate_select("0::float8", "0::float8", exact_score_expr())}
              where coalesce(c.dedupe_canonical, true)
                and (
                  lower(c.path) = any(%s::text[])
                  or compact_basename(c.path) = any(%s::text[])
                  or exists (
                    select 1
                    from jsonb_array_elements_text(c.symbols) symbol_value
                    where compact_key_sql(symbol_value) = any(%s::text[])
                  )
                  or c.path ilike any(%s::text[])
                  or exists (
                    select 1
                    from jsonb_array_elements_text(c.heading_path) heading_value
                    where compact_key_sql(heading_value) = any(%s::text[])
                  )
                  or c.path ilike %s
                  or c.symbols::text ilike %s
                  or c.heading_path::text ilike %s
                )
                {where_scope}
                {content_filter}
            ) ranked_exact
          ) fused_exact
          order by exact_score desc, path asc, start_line asc
          limit %s
        ),
        ranked_chunks as (
          select path, start_line, matched_path, source_anchor, token_count,
                 library, vendor, version, relative_path, heading_path, symbols,
                 content_type, quality_score, content, parent_content, metadata_json,
                 (sum(rrf_score) * 900.0)
                 + (max(fts_score) * 2.4) + (max(vector_score) * 2.8) + (max(exact_score) * 3.0)
                 + (max(quality_score) * 0.15) + max(type_score)
                 + least(max(coalesce(token_count, 0)), 2000) / 20000.0 as score
          from (
            select * from fts_candidates
            union all
            select * from vector_candidates
            union all
            select * from exact_candidates
          ) candidates
          group by path, start_line, matched_path, source_anchor, token_count,
                   library, vendor, version, relative_path, heading_path, symbols,
                   content_type, quality_score, content, parent_content, metadata_json
        ),
        ranked_files as (
          select distinct on (path)
                 path, start_line, score, library, vendor, version, relative_path,
                 heading_path, symbols, content_type, quality_score, content,
                 matched_path, source_anchor, token_count, parent_content, metadata_json
          from ranked_chunks
          order by path, score desc, start_line asc
        )
        select path, start_line, score, library, vendor, version, relative_path,
               heading_path, symbols, content_type, quality_score, content,
               matched_path, source_anchor, token_count, parent_content, metadata_json
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
        mode = "vector_candidates" if vector else "fts_symbol_fallback"
        return score_postgres_rows(rows, query, retrieval_mode=mode, degraded=not bool(vector))
    except VersionResolutionError:
        raise
    except Exception as exc:
        LOGGER.warning("postgres search failed: %s", exc)
        if vector_enabled:
            LOGGER.warning("retrying postgres search with FTS/symbol fallback only")
            return search_from_postgres(
                ctx,
                query,
                library_scope,
                max_results,
                fingerprint,
                vector_enabled=False,
                content_types=content_types,
            )
        return None


def agent_context_from_postgres(
    ctx: RetrievalContext,
    query: str,
    library_scope: str | None,
    max_results: int,
    fingerprint: str,
    *,
    content_types: list[str] | None = None,
    vector_enabled: bool = True,
) -> list[dict[str, Any]] | None:
    connection = postgres_connection(ctx.database_url)
    if connection is None:
        return None
    query_plan = plan_query(query)
    terms = normalized_tsquery(query_plan.important_terms or query)
    compact_terms = [
        compact_key(value)
        for value in [*query_plan.symbols, *query_plan.phrases, *query_plan.slugs, *query_plan.important_terms]
        if compact_key(value)
    ] or ["__oz_no_agent_match__"]
    exact_patterns = [f"%{key}%" for key in compact_terms]
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
    candidates = max(max_results * 8, 40)
    params: list[Any] = []

    def add_scope_params() -> None:
        if scope_vendor:
            params.extend([scope_vendor, scope_library, scope_version_id])

    def vector_expr(alias: str) -> str:
        if not vector:
            return "0::float8"
        return f"case when {alias}.embedding is not null then greatest(1 - ({alias}.embedding <=> %s::vector), 0) else 0 end"

    recipe_vector = vector_expr("ar")
    params.extend([terms, query_plan.content_type, compact_terms, exact_patterns])
    if vector:
        params.append(vector)
    params.extend([terms, exact_patterns])
    add_scope_params()
    params.append(candidates)

    example_vector = vector_expr("ce")
    params.extend([terms, compact_terms, exact_patterns])
    if vector:
        params.append(vector)
    params.extend([terms, exact_patterns])
    add_scope_params()
    params.append(candidates)

    api_vector = vector_expr("ao")
    params.extend([terms, query_plan.content_type, compact_terms, exact_patterns])
    if vector:
        params.append(vector)
    params.extend([terms, exact_patterns, exact_patterns])
    add_scope_params()
    params.append(candidates)

    sdk_vector = vector_expr("sm")
    params.extend([terms, compact_terms, exact_patterns])
    if vector:
        params.append(vector)
    params.extend([terms, exact_patterns])
    add_scope_params()
    params.append(candidates)

    params.extend([terms, exact_patterns, terms, exact_patterns])
    add_scope_params()
    params.append(candidates)

    chunk_vector = "0::float8"
    params.extend([terms, query_plan.content_type])
    if vector:
        chunk_vector = "case when c.embedding is not null then greatest(1 - (c.embedding <=> %s::vector), 0) else 0 end"
        params.append(vector)
    params.extend([terms, exact_patterns])
    add_scope_params()
    params.extend([candidates, max_results])

    sql = f"""
      with recipe_candidates as (
        select
          '.codo/vendors/' || v.name || '/' || l.name || '@' || lv.version || '/AGENT_RECIPES.md' as path,
          1 as start_line,
          (
            greatest(coalesce(ts_rank_cd(ar.search_document, websearch_to_tsquery('english', %s)), 0), 0) * 85.0
            + case when ar.task_kind = %s then 220.0 else 0.0 end
            + case when compact_key_sql(ar.title) = any(%s::text[]) then 160.0 else 0.0 end
            + case when compact_key_sql(ar.title || ' ' || ar.summary || ' ' || ar.info) ilike any(%s::text[]) then 90.0 else 0.0 end
            + ({recipe_vector} * 300.0)
            + greatest(coalesce(ar.confidence, 0), 0) * 80.0
            + greatest(coalesce(ar.quality_score, 1), 0) * 16.0
          ) as score,
          v.name || '/' || l.name as library,
          v.name as vendor,
          lv.version,
          'AGENT_RECIPES.md' as relative_path,
          '[]'::jsonb as heading_path,
          jsonb_build_array(ar.title, ar.task_kind) as symbols,
          ar.task_kind as role,
          ar.quality_score,
          concat_ws(E'\n\n', ar.summary, ar.info, ar.code) as content,
          'AGENT_RECIPES.md' as matched_path,
          coalesce(ar.source_urls_json->>0, '') as source_anchor,
          ar.token_count,
          ar.title,
          ar.info as description,
          case when ar.product <> '' then jsonb_build_array(ar.product) else '[]'::jsonb end as applies_to,
          jsonb_build_array(ar.title, ar.task_kind) as entities,
          jsonb_build_array(ar.task_kind) as task_tags,
          ar.language as code_language,
          ar.code,
          ar.required_params_json as constraints,
          1 as end_line,
          ar.metadata_json || jsonb_build_object('surface', 'agent_recipe', 'recipe_id', ar.id, 'source_urls', ar.source_urls_json) as metadata_json
        from agent_recipes ar
        join library_versions lv on lv.id = ar.version_id
        join libraries l on l.id = lv.library_id
        join vendors v on v.id = l.vendor_id
        left join refs r on r.library_id = l.id and r.channel = 'latest'
        where (
          ar.search_document @@ websearch_to_tsquery('english', %s)
          or compact_key_sql(ar.title || ' ' || ar.summary || ' ' || ar.info) ilike any(%s::text[])
          {"or ar.embedding is not null" if vector else ""}
        )
        {where_scope}
        order by score desc, ar.title asc
        limit %s
      ),
      example_candidates as (
        select
          '.codo/vendors/' || v.name || '/' || l.name || '@' || lv.version || '/' || coalesce(sd.path, 'CODE_EXAMPLES.md') as path,
          coalesce(ss.start_line, 1) as start_line,
          (
            greatest(coalesce(ts_rank_cd(ce.search_document, websearch_to_tsquery('english', %s)), 0), 0) * 80.0
            + case when compact_key_sql(ce.title) = any(%s::text[]) then 150.0 else 0.0 end
            + case when compact_key_sql(ce.title || ' ' || ce.description || ' ' || ce.caption || ' ' || ce.code) ilike any(%s::text[]) then 95.0 else 0.0 end
            + ({example_vector} * 270.0)
            + case when ce.document_role in ('example', 'readme', 'guide', 'test') then 60.0 else 0.0 end
            + greatest(coalesce(ce.confidence, 0), 0) * 70.0
            + greatest(coalesce(ce.quality_score, 1), 0) * 14.0
          ) as score,
          v.name || '/' || l.name as library,
          v.name as vendor,
          lv.version,
          coalesce(sd.path, 'CODE_EXAMPLES.md') as relative_path,
          coalesce(ss.heading_path, '[]'::jsonb) as heading_path,
          ce.symbols_json as symbols,
          'code_example' as role,
          ce.quality_score,
          concat_ws(E'\n\n', ce.description, ce.caption, ce.code) as content,
          coalesce(sd.path, 'CODE_EXAMPLES.md') as matched_path,
          coalesce(ce.source_anchor, ce.source_url, '') as source_anchor,
          ce.token_count,
          ce.title,
          concat_ws(E'\n', ce.description, ce.caption) as description,
          case when ce.product <> '' then jsonb_build_array(ce.product) else '[]'::jsonb end as applies_to,
          ce.symbols_json as entities,
          ce.task_tags_json as task_tags,
          ce.language as code_language,
          ce.code,
          ce.required_params_json as constraints,
          coalesce(ss.end_line, ss.start_line, 1) as end_line,
          ce.metadata_json || jsonb_build_object('surface', 'code_example', 'code_example_id', ce.id) as metadata_json
        from code_examples ce
        join library_versions lv on lv.id = ce.version_id
        join libraries l on l.id = lv.library_id
        join vendors v on v.id = l.vendor_id
        left join refs r on r.library_id = l.id and r.channel = 'latest'
        left join source_documents sd on sd.id = ce.source_document_id
        left join source_sections ss on ss.id = ce.source_section_id
        where (
          ce.search_document @@ websearch_to_tsquery('english', %s)
          or compact_key_sql(ce.title || ' ' || ce.description || ' ' || ce.caption || ' ' || ce.code) ilike any(%s::text[])
          {"or ce.embedding is not null" if vector else ""}
        )
        {where_scope}
        order by score desc, ce.title asc
        limit %s
      ),
      api_candidates as (
        select
          '.codo/vendors/' || v.name || '/' || l.name || '@' || lv.version || '/' || coalesce(sd.path, 'API_OPERATIONS.md') as path,
          1 as start_line,
          (
            greatest(coalesce(ts_rank_cd(ao.search_document, websearch_to_tsquery('english', %s)), 0), 0) * 80.0
            + case when ao.operation_kind = %s then 170.0 else 0.0 end
            + case when compact_key_sql(ao.operation_name || ' ' || ao.operation_id || ' ' || ao.endpoint) = any(%s::text[]) then 150.0 else 0.0 end
            + case when compact_key_sql(ao.operation_name || ' ' || ao.operation_id || ' ' || ao.endpoint || ' ' || ao.summary || ' ' || ao.description) ilike any(%s::text[]) then 95.0 else 0.0 end
            + ({api_vector} * 250.0)
            + greatest(coalesce(ao.confidence, 0), 0) * 70.0
            + greatest(coalesce(ao.quality_score, 1), 0) * 12.0
          ) as score,
          v.name || '/' || l.name as library,
          v.name as vendor,
          lv.version,
          coalesce(sd.path, 'API_OPERATIONS.md') as relative_path,
          '[]'::jsonb as heading_path,
          jsonb_build_array(ao.operation_id, ao.operation_name, ao.http_method, ao.endpoint) as symbols,
          ao.operation_kind as role,
          ao.quality_score,
          concat_ws(E'\n\n', ao.summary, ao.description, 'Endpoint: ' || ao.http_method || ' ' || ao.endpoint, 'Required params: ' || ao.required_params_json::text, 'Optional params: ' || ao.optional_params_json::text, 'Responses: ' || ao.response_schema_json::text, 'Errors: ' || ao.errors_json::text) as content,
          coalesce(sd.path, 'API_OPERATIONS.md') as matched_path,
          coalesce(ao.source_anchor, ao.source_url, '') as source_anchor,
          ao.token_count,
          ao.operation_name as title,
          ao.description,
          case when ao.product <> '' then jsonb_build_array(ao.product) else '[]'::jsonb end as applies_to,
          jsonb_build_array(ao.operation_id, ao.operation_name, ao.http_method, ao.endpoint) as entities,
          ao.tags_json || jsonb_build_array(ao.operation_kind) as task_tags,
          '' as code_language,
          null::text as code,
          ao.required_params_json as constraints,
          1 as end_line,
          ao.metadata_json || jsonb_build_object('surface', 'api_operation', 'api_operation_id', ao.id, 'http_method', ao.http_method, 'endpoint', ao.endpoint) as metadata_json
        from api_operations ao
        join library_versions lv on lv.id = ao.version_id
        join libraries l on l.id = lv.library_id
        join vendors v on v.id = l.vendor_id
        left join refs r on r.library_id = l.id and r.channel = 'latest'
        left join source_documents sd on sd.id = ao.source_document_id
        where (
          ao.search_document @@ websearch_to_tsquery('english', %s)
          or compact_key_sql(ao.operation_name || ' ' || ao.operation_id || ' ' || ao.endpoint || ' ' || ao.summary || ' ' || ao.description) ilike any(%s::text[])
          or compact_key_sql(ao.required_params_json::text || ' ' || ao.optional_params_json::text) ilike any(%s::text[])
          {"or ao.embedding is not null" if vector else ""}
        )
        {where_scope}
        order by score desc, ao.operation_name asc
        limit %s
      ),
      sdk_candidates as (
        select
          '.codo/vendors/' || v.name || '/' || l.name || '@' || lv.version || '/' || coalesce(sd.path, 'SDK_METHODS.md') as path,
          1 as start_line,
          (
            greatest(coalesce(ts_rank_cd(sm.search_document, websearch_to_tsquery('english', %s)), 0), 0) * 75.0
            + case when compact_key_sql(sm.symbol_name || ' ' || sm.sdk_class || ' ' || sm.sdk_method) = any(%s::text[]) then 170.0 else 0.0 end
            + case when compact_key_sql(sm.symbol_name || ' ' || sm.signature || ' ' || sm.description) ilike any(%s::text[]) then 95.0 else 0.0 end
            + ({sdk_vector} * 240.0)
            + case when sm.public_api then 65.0 else -180.0 end
            - case when sm.generated then 80.0 else 0.0 end
            + greatest(coalesce(sm.confidence, 0), 0) * 70.0
            + greatest(coalesce(sm.quality_score, 1), 0) * 12.0
          ) as score,
          v.name || '/' || l.name as library,
          v.name as vendor,
          lv.version,
          coalesce(sd.path, 'SDK_METHODS.md') as relative_path,
          '[]'::jsonb as heading_path,
          jsonb_build_array(sm.symbol_name, sm.sdk_class, sm.sdk_method, sm.import_path) as symbols,
          'sdk_method' as role,
          sm.quality_score,
          concat_ws(E'\n\n', sm.signature, sm.description, 'Required params: ' || sm.required_params_json::text, 'Optional params: ' || sm.optional_params_json::text, 'Returns: ' || sm.return_type) as content,
          coalesce(sd.path, 'SDK_METHODS.md') as matched_path,
          coalesce(sm.source_anchor, sm.source_url, '') as source_anchor,
          greatest(1, length(concat_ws(E'\n', sm.signature, sm.description)) / 4)::integer as token_count,
          sm.symbol_name as title,
          sm.description,
          case when sm.product <> '' then jsonb_build_array(sm.product) else '[]'::jsonb end as applies_to,
          jsonb_build_array(sm.symbol_name, sm.sdk_class, sm.sdk_method, sm.import_path) as entities,
          jsonb_build_array('sdk_method') as task_tags,
          sm.language as code_language,
          null::text as code,
          sm.required_params_json as constraints,
          1 as end_line,
          sm.metadata_json || jsonb_build_object('surface', 'sdk_method', 'sdk_method_id', sm.id, 'public_api', sm.public_api, 'generated', sm.generated) as metadata_json
        from sdk_methods sm
        join library_versions lv on lv.id = sm.version_id
        join libraries l on l.id = lv.library_id
        join vendors v on v.id = l.vendor_id
        left join refs r on r.library_id = l.id and r.channel = 'latest'
        left join source_documents sd on sd.id = sm.source_document_id
        where (
          sm.search_document @@ websearch_to_tsquery('english', %s)
          or compact_key_sql(sm.symbol_name || ' ' || sm.sdk_class || ' ' || sm.sdk_method || ' ' || sm.signature || ' ' || sm.description) ilike any(%s::text[])
          {"or sm.embedding is not null" if vector else ""}
        )
        {where_scope}
        order by score desc, sm.symbol_name asc
        limit %s
      ),
      section_candidates as (
        select
          '.codo/vendors/' || v.name || '/' || l.name || '@' || lv.version || '/' || ss.path as path,
          ss.start_line,
          (
            greatest(coalesce(ts_rank_cd(ss.search_document, websearch_to_tsquery('english', %s)), 0), 0) * 45.0
            + case when compact_key_sql(ss.title || ' ' || ss.path) ilike any(%s::text[]) then 60.0 else 0.0 end
            + greatest(coalesce(ss.quality_score, 1), 0) * 8.0
          ) as score,
          v.name || '/' || l.name as library,
          v.name as vendor,
          lv.version,
          ss.path as relative_path,
          ss.heading_path,
          '[]'::jsonb as symbols,
          coalesce(ss.content_type, ss.document_role, 'prose') as role,
          ss.quality_score,
          ss.content,
          ss.path as matched_path,
          coalesce(ss.source_anchor, ss.source_url, '') as source_anchor,
          ss.token_count,
          ss.title,
          '' as description,
          case when ss.product <> '' then jsonb_build_array(ss.product) else '[]'::jsonb end as applies_to,
          ss.heading_path as entities,
          jsonb_build_array(ss.document_role, ss.content_type) as task_tags,
          ss.language as code_language,
          null::text as code,
          '[]'::jsonb as constraints,
          ss.end_line,
          ss.metadata_json || jsonb_build_object('surface', 'source_section', 'source_section_id', ss.id) as metadata_json
        from source_sections ss
        join library_versions lv on lv.id = ss.version_id
        join libraries l on l.id = lv.library_id
        join vendors v on v.id = l.vendor_id
        left join refs r on r.library_id = l.id and r.channel = 'latest'
        where (
          ss.search_document @@ websearch_to_tsquery('english', %s)
          or compact_key_sql(ss.title || ' ' || ss.path || ' ' || ss.content) ilike any(%s::text[])
        )
        {where_scope}
        order by score desc, ss.path asc, ss.start_line asc
        limit %s
      ),
      chunk_candidates as (
        select
          '.codo/vendors/' || v.name || '/' || l.name || '@' || lv.version || '/' || c.path as path,
          c.start_line,
          (
            greatest(coalesce(ts_rank_cd(c.search_document, websearch_to_tsquery('english', %s)), 0), 0) * 35.0
            + content_type_intent_score(c.content_type, %s) * 90.0
            + ({chunk_vector} * 180.0)
            + greatest(coalesce(c.quality_score, 1), 0) * 6.0
          ) as score,
          v.name || '/' || l.name as library,
          v.name as vendor,
          lv.version,
          c.path as relative_path,
          c.heading_path,
          c.symbols,
          c.content_type as role,
          c.quality_score,
          c.content,
          c.path as matched_path,
          coalesce(c.source_anchor, c.source_url, '') as source_anchor,
          c.token_count,
          coalesce(c.heading_path->>-1, c.path) as title,
          '' as description,
          case when coalesce(c.metadata_json->>'product', '') <> '' then jsonb_build_array(c.metadata_json->>'product') else '[]'::jsonb end as applies_to,
          c.symbols as entities,
          jsonb_build_array(c.content_type) as task_tags,
          coalesce(c.metadata_json->>'language', '') as code_language,
          null::text as code,
          '[]'::jsonb as constraints,
          c.end_line,
          c.metadata_json || jsonb_build_object('surface', 'chunk', 'chunk_id', c.id) as metadata_json
        from chunks c
        join library_versions lv on lv.id = c.version_id
        join libraries l on l.id = lv.library_id
        join vendors v on v.id = l.vendor_id
        left join refs r on r.library_id = l.id and r.channel = 'latest'
        where coalesce(c.dedupe_canonical, true)
          and (
            c.search_document @@ websearch_to_tsquery('english', %s)
            or compact_key_sql(c.path || ' ' || c.heading_path::text || ' ' || c.symbols::text) ilike any(%s::text[])
            {"or c.embedding is not null" if vector else ""}
          )
        {where_scope}
        order by score desc, c.path asc, c.start_line asc
        limit %s
      )
      select * from recipe_candidates
      union all select * from example_candidates
      union all select * from api_candidates
      union all select * from sdk_candidates
      union all select * from section_candidates
      union all select * from chunk_candidates
      order by score desc, path asc, start_line asc
      limit %s
    """
    try:
        with observe_duration("oz_db_query_duration_seconds", {"operation": "agent_context", "mode": "hybrid" if vector else "fts"}):
            with connection:
                with connection.cursor() as cursor:
                    cursor.execute(f"set local statement_timeout = {retrieval_statement_timeout_ms()}")
                    cursor.execute(sql, tuple(params))
                    rows = cursor.fetchall()
                    mark_context_versions_requested(cursor, rows)
        return score_agent_context_rows(rows, degraded=not bool(vector))
    except VersionResolutionError:
        raise
    except Exception as exc:
        LOGGER.warning("postgres typed agent context failed: %s", exc)
        if vector_enabled:
            LOGGER.warning("retrying typed agent context with FTS fallback only")
            return agent_context_from_postgres(
                ctx,
                query,
                library_scope,
                max_results,
                fingerprint,
                content_types=content_types,
                vector_enabled=False,
            )
        return None


def candidate_select(fts_score: str, vector_score: str, exact_score: str) -> str:
    return f"""
        select
          '.codo/vendors/' || v.name || '/' || l.name || '@' || lv.version || '/' || coalesce(p.path, c.path) as path,
          coalesce(p.start_line, c.start_line) as start_line,
          c.path as matched_path,
          coalesce(c.source_anchor, c.source_url) as source_anchor,
          c.token_count,
          {fts_score} as fts_score,
          {vector_score} as vector_score,
          {exact_score} as exact_score,
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
          coalesce(p.content, c.content) as parent_content,
          c.metadata_json
        from chunks c
        join library_versions lv on lv.id = c.version_id
        join libraries l on l.id = lv.library_id
        join vendors v on v.id = l.vendor_id
        left join refs r on r.library_id = l.id and r.channel = 'latest'
        left join chunks p on p.id = c.parent_chunk_id
    """


def fielded_fts_score_expr() -> str:
    return """
        greatest(
          (ts_rank_cd(setweight(to_tsvector('english', coalesce(c.path, '')), 'A'), websearch_to_tsquery('english', %s)) * 8.0) +
          (ts_rank_cd(setweight(to_tsvector('english', coalesce(c.heading_path::text, '')), 'A'), websearch_to_tsquery('english', %s)) * 6.0) +
          (ts_rank_cd(setweight(to_tsvector('english', coalesce(c.symbols::text, '')), 'A'), websearch_to_tsquery('english', %s)) * 8.0) +
          (ts_rank_cd(to_tsvector('english', coalesce(c.content, '')), websearch_to_tsquery('english', %s)) * 1.5),
          0
        )
    """


def exact_score_expr() -> str:
    return """
        case
          when lower(c.path) = any(%s::text[]) then 8.0
          when left(c.path, 9) = '_symbols/' and compact_basename(c.path) = any(%s::text[]) then 7.5
          when exists (
            select 1
            from jsonb_array_elements_text(c.symbols) symbol_value
            where compact_key_sql(symbol_value) = any(%s::text[])
          ) then 6.0
          when c.path ilike any(%s::text[]) then 5.5
          when exists (
            select 1
            from jsonb_array_elements_text(c.heading_path) heading_value
            where compact_key_sql(heading_value) = any(%s::text[])
          ) then 4.5
          else 1.0
        end
    """


def vector_candidate_cte(where_scope: str, content_filter: str) -> str:
    return f"""
        select *
        from (
          select ranked_vector.*,
                 1.0 / (60 + row_number() over (order by vector_score desc, path asc, start_line asc)) as rrf_score
          from (
            {candidate_select("0::float8", "greatest(1 - (c.embedding <=> %s::vector), 0)", "0::float8")}
            where c.embedding is not null
              and coalesce(c.dedupe_canonical, true)
              {where_scope}
              {content_filter}
          ) ranked_vector
        ) fused_vector
        order by vector_score desc, path asc, start_line asc
        limit %s
    """


def empty_vector_cte() -> str:
    return """
        select null::text as path, null::integer as start_line, null::text as matched_path,
               null::text as source_anchor, null::integer as token_count,
               0::float8 as fts_score, 0::float8 as vector_score, 0::float8 as exact_score,
               0::float8 as quality_score, 0::float8 as type_score,
               null::text as library, null::text as vendor, null::text as version,
               null::text as relative_path, '[]'::jsonb as heading_path, '[]'::jsonb as symbols,
               null::text as content_type, null::text as content, null::text as parent_content,
               '{}'::jsonb as metadata_json,
               0::float8 as rrf_score
        where false
    """


def vector_literal(values: list[float]) -> str:
    return "[" + ",".join(f"{value:.8g}" for value in values) + "]"


def normalized_tsquery(query: str | list[str]) -> str:
    terms = query if isinstance(query, list) else normalize_query(query)
    if terms:
        return " OR ".join(terms)
    return query.strip() if isinstance(query, str) and query.strip() else "documentation"


def like_pattern(values: list[str]) -> str:
    compact = [value for value in values if value]
    if not compact:
        return "%"
    return "%" + "%".join(compact[:4]) + "%"


def compact_key(value: str) -> str:
    return re.sub(r"[^a-z0-9]+", "", value.lower())


def legacy_query(query: str) -> bool:
    return bool(re.search(r"\b(?:legacy|deprecated|old|previous|migration|migrate|v\d+|version\s+\d+)\b", query, re.I))


def candidate_limit(max_results: int) -> int:
    return max(max_results * 10, 50)


def score_postgres_rows(
    rows: list[Any],
    query: str,
    *,
    retrieval_mode: str,
    degraded: bool,
) -> list[dict[str, Any]]:
    scored: list[dict[str, Any]] = []
    for row in rows:
        metadata = row[16] if len(row) > 16 and isinstance(row[16], dict) else {}
        chunk = {
            "path": row[6],
            "heading_path": row[7],
            "symbols": row[8],
            "content_type": row[9],
            "quality_score": row[10],
            "text": row[11],
        }
        score = float(row[2]) + (planned_chunk_score(chunk, query) / 4.0)
        if metadata.get("current") is True:
            score += 20.0
        if (metadata.get("deprecated") is True or metadata.get("legacy") is True) and not legacy_query(query):
            score -= 240.0
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
                "heading_path": row[7] or [],
                "symbols": row[8] or [],
                "token_count": int(row[14] or 0),
                "retrieval_mode": retrieval_mode,
                "degraded": degraded,
                "_matched_text": row[11] or "",
                "_parent_text": row[15] or "",
                "metadata_json": metadata,
                "_rerank_text": rerank_text(row),
            }
        )
    scored.sort(key=lambda item: (-float(item["score"]), str(item["path"]), int(item.get("line") or 1)))
    return scored


def score_agent_context_rows(rows: list[Any], *, degraded: bool) -> list[dict[str, Any]]:
    output: list[dict[str, Any]] = []
    for row in rows:
        metadata = row[24] if len(row) > 24 and isinstance(row[24], dict) else {}
        surface = str(metadata.get("surface") or "agent_context")
        role = row[9] or metadata.get("operation_kind") or surface
        code = row[21]
        content = row[11] or ""
        content_type = "code_example" if surface in {"code_example", "agent_recipe"} and code else ("api_reference" if surface in {"api_operation", "sdk_method"} else str(role or "prose"))
        output.append(
            {
                "path": row[0],
                "line": row[1],
                "end_line": row[23],
                "score": round(float(row[2] or 0), 4),
                "library": row[3],
                "vendor": row[4],
                "version": row[5],
                "relative_path": row[6],
                "heading_path": row[7] or [],
                "symbols": row[8] or [],
                "content_type": content_type,
                "role": role,
                "quality_score": row[10],
                "matched_path": row[12],
                "source_anchor": row[13],
                "token_count": int(row[14] or 0),
                "title": row[15] or "",
                "description": row[16] or "",
                "applies_to": row[17] or [],
                "entities": row[18] or [],
                "task_tags": row[19] or [],
                "code_language": row[20],
                "code": code,
                "constraints": row[22] or [],
                "metadata_json": metadata,
                "retrieval_mode": surface,
                "degraded": degraded,
                "_matched_text": content,
                "_parent_text": "",
                "_rerank_text": "\n".join(
                    [
                        f"title: {row[15] or ''}",
                        f"description: {row[16] or ''}",
                        f"path: {row[6] or ''}",
                        f"role: {role or ''}",
                        f"entities: {row[18] or []}",
                        content,
                    ]
                ),
            }
        )
    output.sort(key=lambda item: (-float(item["score"]), str(item["path"]), int(item.get("line") or 1)))
    return output


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


def mark_context_versions_requested(cursor: Any, rows: list[Any]) -> None:
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
