from __future__ import annotations

import logging
from typing import Any

from oz_api.auth_store import AuthStore
from oz_api.storage import RegistryStorage
from oz_api.versions import available_versions, resolve_catalog_entry

LOGGER = logging.getLogger(__name__)


def public_library_rows(storage: RegistryStorage) -> list[dict[str, Any]]:
    rows = db_rows(
        """
        select v.name as vendor, l.name as library, l.description, l.source_url,
               lv.version, lv.ref_sha, coalesce(lv.indexed_at, lv.last_crawled_at)::text as indexed_at,
               lv.last_crawled_at::text as last_crawled_at,
               lv.benchmark_score, coalesce(ts.value, 0) as trust_score,
	               count(c.id)::bigint as chunk_count,
	               coalesce(sum(c.token_count), 0)::bigint as token_count,
	               count(distinct c.path)::bigint as file_count,
	               (select count(*) from api_operations ao where ao.version_id = lv.id)::bigint as operation_count,
	               (select count(*) from code_examples ce where ce.version_id = lv.id)::bigint as example_count,
	               (select count(*) from agent_recipes ar where ar.version_id = lv.id)::bigint as recipe_count,
	               coalesce(max(pb.byte_size), 0)::bigint as pack_bytes
        from libraries l
        join vendors v on v.id = l.vendor_id
        left join refs r on r.library_id = l.id and r.channel = 'latest'
        join library_versions lv on lv.library_id = l.id
          and (
            (:version = '' and lv.id = coalesce(l.default_version_id, r.version_id))
            or (:version <> '' and lv.version = :version)
          )
        left join chunks c on c.version_id = lv.id and c.dedupe_canonical = true
        left join trust_scores ts on ts.library_id = l.id
        left join pack_builds pb on pb.library_id = l.id and pb.version = lv.version and pb.pack_sha = lv.ref_sha
        group by v.name, l.name, l.description, l.source_url, lv.version, lv.ref_sha,
                 lv.indexed_at, lv.last_crawled_at, lv.benchmark_score, ts.value
        order by v.name, l.name
        """,
        {"version": ""},
    )
    if rows:
        return [normalize_counts(row) for row in rows]
    return catalog_rows(storage)


def public_library_detail(
    storage: RegistryStorage,
    vendor: str,
    library: str,
    version: str | None = None,
) -> dict[str, Any] | None:
    detail = db_library_detail(vendor, library, version)
    if detail is not None:
        return hydrate_pack_bytes(storage, detail)
    return catalog_detail(storage, vendor, library, version)


def db_library_detail(vendor: str, library: str, version: str | None) -> dict[str, Any] | None:
    row = one_row(
        """
        select l.id as library_id, v.name as vendor, l.name as library, l.description, l.source_url,
               l.version_strategy, lv.id as version_id, lv.version, lv.ref_sha, lv.pack_key,
               coalesce(lv.indexed_at, lv.last_crawled_at)::text as indexed_at,
               lv.last_crawled_at::text as last_crawled_at,
               lv.pull_count, lv.benchmark_score, lv.drift_score,
               coalesce(ts.value, 0) as trust_score,
	               count(c.id)::bigint as chunk_count,
	               coalesce(sum(c.token_count), 0)::bigint as token_count,
	               count(distinct c.path)::bigint as file_count,
	               (select count(*) from api_operations ao where ao.version_id = lv.id)::bigint as operation_count,
	               (select count(*) from code_examples ce where ce.version_id = lv.id)::bigint as example_count,
	               (select count(*) from agent_recipes ar where ar.version_id = lv.id)::bigint as recipe_count,
	               coalesce(max(pb.byte_size), 0)::bigint as pack_bytes
        from libraries l
        join vendors v on v.id = l.vendor_id
        left join refs r on r.library_id = l.id and r.channel = 'latest'
        left join library_versions lv on lv.id = coalesce(l.default_version_id, r.version_id)
        left join chunks c on c.version_id = lv.id and c.dedupe_canonical = true
        left join trust_scores ts on ts.library_id = l.id
        left join pack_builds pb on pb.library_id = l.id and pb.version = lv.version and pb.pack_sha = lv.ref_sha
        where v.name = :vendor and l.name = :library
          and (:version = '' or lv.version = :version)
        group by l.id, v.name, l.name, l.description, l.source_url, l.version_strategy,
                 lv.id, lv.version, lv.ref_sha, lv.pack_key, lv.indexed_at, lv.last_crawled_at,
                 lv.pull_count, lv.benchmark_score, lv.drift_score, ts.value
        order by lv.indexed_at desc nulls last
        limit 1
        """,
        {"vendor": vendor, "library": library, "version": version or ""},
    )
    if row is None:
        return None
    row = normalize_counts(row)
    version_id = row.get("version_id")
    row["versions"] = db_rows(
        """
        select lv.version, lv.ref_sha, coalesce(lv.indexed_at, lv.last_crawled_at)::text as indexed_at,
               lv.last_crawled_at::text as last_crawled_at, lv.benchmark_score,
               lv.archived_at::text as archived_at,
               count(c.id)::bigint as chunk_count,
               coalesce(sum(c.token_count), 0)::bigint as token_count
        from library_versions lv
        left join chunks c on c.version_id = lv.id and c.dedupe_canonical = true
        where lv.library_id = :library_id
        group by lv.id
        order by lv.archived_at nulls first, lv.indexed_at desc nulls last, lv.version desc
        """,
        {"library_id": row["library_id"]},
    )
    row["sources"] = db_rows(
        """
        select source_url, source_type, priority, enabled, updated_at::text as updated_at
        from library_sources
        where library_id = :library_id
        order by enabled desc, priority asc, source_url asc
        """,
        {"library_id": row["library_id"]},
    )
    row["content_types"] = db_rows(
        """
        select content_type, count(*)::bigint as chunk_count, coalesce(sum(token_count), 0)::bigint as token_count
        from chunks
        where version_id = :version_id and dedupe_canonical = true
        group by content_type
        order by chunk_count desc, content_type asc
        """,
        {"version_id": version_id},
    )
    row["top_files"] = db_rows(
        """
        select path, count(*)::bigint as chunk_count, coalesce(sum(token_count), 0)::bigint as token_count
        from chunks
        where version_id = :version_id and dedupe_canonical = true
        group by path
        order by chunk_count desc, token_count desc, path asc
        limit 25
        """,
        {"version_id": version_id},
    )
    row["agent_context"] = db_rows(
        """
        select 'operations' as kind, count(*)::bigint as count, count(*) filter (where embedding is not null)::bigint as embedded_count
        from api_operations
        where version_id = :version_id
        union all
        select 'examples' as kind, count(*)::bigint as count, count(*) filter (where embedding is not null)::bigint as embedded_count
        from code_examples
        where version_id = :version_id
        union all
        select 'sdk_methods' as kind, count(*)::bigint as count, count(*) filter (where embedding is not null)::bigint as embedded_count
        from sdk_methods
        where version_id = :version_id
        union all
        select 'recipes' as kind, count(*)::bigint as count, count(*) filter (where embedding is not null)::bigint as embedded_count
        from agent_recipes
        where version_id = :version_id
        """,
        {"version_id": version_id},
    )
    row["top_operations"] = db_rows(
        """
        select operation_name, operation_kind, '' as sdk_class, '' as sdk_method, endpoint, confidence, quality_score
        from api_operations
        where version_id = :version_id
        order by quality_score desc, confidence desc, operation_name asc
        limit 25
        """,
        {"version_id": version_id},
    )
    row["quality"] = db_rows(
        """
        select passed, metrics, created_at::text as created_at
        from quality_runs
        where library_id = :library_id and version = :version
        order by created_at desc
        limit 5
        """,
        {"library_id": row["library_id"], "version": row["version"]},
    )
    row["evals"] = db_rows(
        """
        select eval_type, passed, metrics, created_at::text as created_at
        from eval_runs
        where library_id = :library_id and version = :version
        order by created_at desc
        limit 5
        """,
        {"library_id": row["library_id"], "version": row["version"]},
    )
    return row


def catalog_rows(storage: RegistryStorage) -> list[dict[str, Any]]:
    rows = []
    for entry in storage.load_catalog():
        rows.append(
            normalize_counts(
                {
                    "vendor": entry.get("vendor"),
                    "library": entry.get("library"),
                    "description": entry.get("description") or "",
                    "source_url": first_source(entry),
                    "version": entry.get("version"),
                    "ref_sha": entry.get("ref_sha"),
                    "indexed_at": entry.get("indexed_at"),
                    "last_crawled_at": entry.get("indexed_at"),
                    "chunk_count": 0,
                    "token_count": 0,
	                    "file_count": 0,
	                    "operation_count": 0,
	                    "example_count": 0,
	                    "recipe_count": 0,
	                    "pack_bytes": 0,
                    "benchmark_score": 0,
                    "trust_score": 0,
                }
            )
        )
    return sorted(rows, key=lambda row: (str(row.get("vendor")), str(row.get("library"))))


def catalog_detail(storage: RegistryStorage, vendor: str, library: str, version: str | None) -> dict[str, Any] | None:
    matches = [entry for entry in storage.load_catalog() if entry.get("vendor") == vendor and entry.get("library") == library]
    entry = resolve_catalog_entry(matches, version)
    if entry is None:
        return None
    row = normalize_counts(
        {
            "vendor": vendor,
            "library": library,
            "description": entry.get("description") or "",
            "source_url": first_source(entry),
            "version": entry.get("version"),
            "ref_sha": entry.get("ref_sha"),
            "pack_key": entry.get("pack_path"),
            "indexed_at": entry.get("indexed_at"),
            "last_crawled_at": entry.get("indexed_at"),
            "chunk_count": 0,
            "token_count": 0,
            "file_count": 0,
            "pack_bytes": 0,
            "benchmark_score": 0,
            "trust_score": 0,
            "versions": [{"version": item.get("version"), "ref_sha": item.get("ref_sha")} for item in matches],
            "sources": [{"source_url": source, "source_type": "catalog", "enabled": True} for source in entry.get("source_urls", [])],
            "content_types": [],
	            "top_files": [],
	            "agent_context": [],
	            "top_operations": [],
	            "quality": [],
            "evals": [],
            "available_versions": available_versions(matches),
        }
    )
    return row


def db_rows(sql: str, params: dict[str, Any] | None = None) -> list[dict[str, Any]]:
    store = AuthStore.from_env()
    if store is None:
        return []
    try:
        return store.execute(sql, params or {})
    except Exception:
        LOGGER.exception("public_catalog_query_failed")
        return []


def one_row(sql: str, params: dict[str, Any]) -> dict[str, Any] | None:
    rows = db_rows(sql, params)
    return rows[0] if rows else None


def normalize_counts(row: dict[str, Any]) -> dict[str, Any]:
    output = dict(row)
    for key in ("chunk_count", "token_count", "file_count", "operation_count", "example_count", "recipe_count", "pack_bytes", "pull_count"):
        try:
            output[key] = int(output.get(key) or 0)
        except (TypeError, ValueError):
            output[key] = 0
    for key in ("benchmark_score", "trust_score", "drift_score"):
        try:
            output[key] = float(output.get(key) or 0)
        except (TypeError, ValueError):
            output[key] = 0.0
    return output


def first_source(entry: dict[str, Any]) -> str:
    sources = entry.get("source_urls") or []
    if isinstance(sources, list) and sources:
        return str(sources[0])
    return ""


def hydrate_pack_bytes(storage: RegistryStorage, row: dict[str, Any]) -> dict[str, Any]:
    if int(row.get("pack_bytes") or 0) > 0:
        return row
    vendor = str(row.get("vendor") or "")
    library = str(row.get("library") or "")
    version = str(row.get("version") or "latest")
    if not vendor or not library:
        return row
    try:
        pack_body = storage.get_pack_bytes(vendor, library, version)
    except Exception:
        LOGGER.exception("public_catalog_pack_size_lookup_failed")
        return row
    if pack_body is None:
        return row
    output = dict(row)
    output["pack_bytes"] = len(pack_body)
    return output
