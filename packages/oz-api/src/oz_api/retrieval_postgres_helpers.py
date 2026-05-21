from __future__ import annotations

import logging
import re
from typing import Any

from oz_api.observability import observe_duration
from oz_api.ranking import planned_chunk_score
from oz_api.storage import normalize_query
from oz_api.versions import (
    VersionResolutionError,
    available_versions,
    latest_entry,
    version_matches,
)

LOGGER = logging.getLogger(__name__)


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
