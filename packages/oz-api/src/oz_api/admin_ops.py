from __future__ import annotations

import json
import os
from typing import Any
from urllib.parse import urlparse

from oz_api.auth import AuthPrincipal
from oz_api.auth_store import AuthStore
from oz_api.queue import crawler_job_event, enqueue_crawler_job
from oz_api.storage import RegistryStorage


def submit_index_request(
    storage: RegistryStorage,
    payload: dict[str, Any],
    principal: AuthPrincipal | None,
    *,
    fallback_user: str = "api",
) -> dict[str, Any]:
    event = {
        "library_name": clean(payload.get("library_name")),
        "vendor_hint": clean(payload.get("vendor_hint") or payload.get("vendor")),
        "source_url_hint": clean(payload.get("source_url_hint") or payload.get("source_url")),
        "requesting_user": principal.email if principal else clean(payload.get("requesting_user")) or fallback_user,
    }
    store = AuthStore.from_env()
    if store is not None:
        store.execute(
            """
            with updated as (
              update index_requests
              set request_count = request_count + 1, updated_at = now()
              where coalesce(library_name, '') = :library_name
                and coalesce(vendor_hint, '') = :vendor_hint
                and coalesce(source_url_hint, '') = :source_url_hint
                and status in ('queued', 'approved')
              returning id
            )
            insert into index_requests (
              library_name, vendor_hint, source_url_hint, requesting_user, request_count, status
            )
            select :library_name, :vendor_hint, :source_url_hint, :requesting_user, 1, 'queued'
            where not exists (select 1 from updated)
            """,
            event,
        )
    log_admin_action(
        principal,
        "index_request_created",
        target_type="library",
        target=library_target(event["vendor_hint"], event["library_name"]),
        metadata=event,
    )
    return event


def approve_crawl(
    storage: RegistryStorage,
    payload: dict[str, Any],
    principal: AuthPrincipal | None,
) -> dict[str, Any]:
    profile = require_profile_for_crawl(payload)
    if profile:
        payload = {**payload, "profile": profile}
    event = enqueue_crawler_job(storage, payload, principal=principal)
    upsert_freshness_policy(payload, principal)
    log_admin_action(
        principal,
        "crawl_enqueued",
        target_type="library",
        target=library_target(event.get("vendor"), event.get("library_name")),
        metadata=event,
    )
    return event


def upsert_library_profile(
    payload: dict[str, Any],
    principal: AuthPrincipal | None,
) -> dict[str, Any]:
    store = require_db_store()
    vendor = clean(payload.get("vendor") or payload.get("vendor_hint"))
    library = clean(payload.get("library_name") or payload.get("library"))
    source_url = clean(payload.get("source_url") or payload.get("source_url_hint"))
    if not vendor or not library or not source_url:
        raise ValueError("vendor, library_name, and source_url are required")
    row = store.one(
        """
        with vendor_row as (
          insert into vendors(name)
          values (:vendor)
          on conflict (name) do update set name = excluded.name
          returning id
        ),
        library_row as (
          insert into libraries(vendor_id, name, description, source_url)
          select id, :library, :description, :source_url
          from vendor_row
          on conflict (vendor_id, name) do update
          set description = excluded.description,
              source_url = excluded.source_url,
              updated_at = now()
          returning id
        ),
        source_row as (
          insert into library_sources(library_id, source_url, source_type, priority)
          select id, :source_url, :source_type, :priority
          from library_row
          on conflict (library_id, source_url) do update
          set source_type = excluded.source_type,
              priority = excluded.priority,
              enabled = true,
              updated_at = now()
        )
        insert into library_profiles (
          library_id, allowed_hosts, allowed_paths, denied_paths, source_priority,
          required_topics, expected_symbols, min_quality_score, min_documents,
          max_junk_ratio, created_by, updated_at
        )
        select id, cast(:allowed_hosts as jsonb), cast(:allowed_paths as jsonb),
               cast(:denied_paths as jsonb), cast(:source_priority as jsonb),
               cast(:required_topics as jsonb), cast(:expected_symbols as jsonb),
               :min_quality_score, :min_documents, :max_junk_ratio,
               cast(:created_by as uuid), now()
        from library_row
        on conflict (library_id) do update
        set allowed_hosts = excluded.allowed_hosts,
            allowed_paths = excluded.allowed_paths,
            denied_paths = excluded.denied_paths,
            source_priority = excluded.source_priority,
            required_topics = excluded.required_topics,
            expected_symbols = excluded.expected_symbols,
            min_quality_score = excluded.min_quality_score,
            min_documents = excluded.min_documents,
            max_junk_ratio = excluded.max_junk_ratio,
            updated_at = now()
        returning library_id
        """,
        profile_params(payload, principal, vendor, library, source_url),
    )
    if not row:
        raise RuntimeError("library profile was not saved")
    upsert_freshness_policy(payload, principal)
    result = get_library_profile(vendor, library) or {}
    log_admin_action(
        principal,
        "library_profile_upserted",
        target_type="library",
        target=library_target(vendor, library),
        metadata=result,
    )
    return result


def record_catalog_promotion(entry: dict[str, Any], job: dict[str, Any], quality: dict[str, Any] | None = None) -> None:
    store = AuthStore.from_env()
    if store is None:
        raise RuntimeError("DATABASE_URL or OZ_DATABASE_URL is required")
    job_id = clean(job.get("db_job_id")) or None
    store.execute(
        """
        insert into catalog_promotions (
          vendor, library, version, ref_sha, pack_key, source_url, job_id, quality_json
        )
        values (
          :vendor, :library, :version, :ref_sha, :pack_key, :source_url,
          cast(:job_id as bigint), cast(:quality_json as jsonb)
        )
        """,
        {
            "vendor": clean(entry.get("vendor")),
            "library": clean(entry.get("library")),
            "version": clean(entry.get("version")) or "latest",
            "ref_sha": clean(entry.get("ref_sha")),
            "pack_key": clean(entry.get("pack_path")),
            "source_url": first_source_url(entry),
            "job_id": job_id,
            "quality_json": json.dumps(quality or {}, sort_keys=True),
        },
    )
    if quality and "passed" in quality:
        record_quality_run(entry, job, quality)
    record_pack_build(entry, job)


def require_profile_for_crawl(payload: dict[str, Any]) -> dict[str, Any] | None:
    store = AuthStore.from_env()
    if store is None:
        raise RuntimeError("DATABASE_URL or OZ_DATABASE_URL is required")
    vendor = clean(payload.get("vendor") or payload.get("vendor_hint"))
    library = clean(payload.get("library_name") or payload.get("library"))
    source_url = clean(payload.get("source_url") or payload.get("source_url_hint"))
    profile = get_library_profile(vendor, library)
    if profile is None:
        raise ValueError(f"no production library profile found for {library_target(vendor, library)}")
    if not source_allowed(source_url, profile):
        raise ValueError("source_url is rejected by the library profile")
    return profile


def get_library_profile(vendor: str, library: str) -> dict[str, Any] | None:
    store = AuthStore.from_env()
    if store is None or not vendor or not library:
        return None
    row = store.one(
        """
        select v.name as vendor, l.name as library, l.source_url,
               p.allowed_hosts, p.allowed_paths, p.denied_paths, p.source_priority,
               p.required_topics, p.expected_symbols, p.min_quality_score,
               p.min_documents, p.max_junk_ratio
        from library_profiles p
        join libraries l on l.id = p.library_id
        join vendors v on v.id = l.vendor_id
        where v.name = :vendor and l.name = :library
        """,
        {"vendor": vendor, "library": library},
    )
    return decode_profile_row(row) if row else None


def mark_crawler_job_started(job: dict[str, Any]) -> None:
    update_crawler_job(job, "running", started=True)


def mark_crawler_job_completed(job: dict[str, Any], *, pack_key: str, ref_sha: str) -> None:
    update_crawler_job(
        job,
        "completed",
        finished=True,
        pack_key=pack_key,
        ref_sha=ref_sha,
        embedding_status="embeddings_applied",
    )


def mark_crawler_job_embedding_waiting(
    job: dict[str, Any],
    *,
    pack_key: str,
    ref_sha: str,
    status: str,
    embedding_job_id: int | None = None,
) -> None:
    update_crawler_job(
        job,
        "batch_running",
        pack_key=pack_key,
        ref_sha=ref_sha,
        embedding_status=status,
        embedding_job_id=embedding_job_id,
    )


def mark_crawler_job_failed(job: dict[str, Any], error: str) -> None:
    update_crawler_job(job, "failed", finished=True, error=error[:2000])


def update_crawler_job(
    job: dict[str, Any],
    status: str,
    *,
    started: bool = False,
    finished: bool = False,
    pack_key: str | None = None,
    ref_sha: str | None = None,
    embedding_status: str | None = None,
    embedding_job_id: int | None = None,
    error: str | None = None,
) -> None:
    job_id = clean(job.get("db_job_id"))
    if not job_id:
        return
    store = AuthStore.from_env()
    if store is None:
        return
    fields = ["status = :status"]
    params: dict[str, Any] = {"job_id": job_id, "status": status}
    if started:
        fields.append("started_at = coalesce(started_at, now())")
        fields.append("attempts = attempts + 1")
    if finished:
        fields.append("finished_at = now()")
    if pack_key is not None:
        fields.append("pack_key = :pack_key")
        params["pack_key"] = pack_key
    if ref_sha is not None:
        fields.append("ref_sha = :ref_sha")
        params["ref_sha"] = ref_sha
    if embedding_status is not None:
        fields.append("embedding_status = :embedding_status")
        params["embedding_status"] = embedding_status
    if embedding_job_id is not None:
        fields.append("embedding_job_id = :embedding_job_id")
        params["embedding_job_id"] = embedding_job_id
    if error is not None:
        fields.append("last_error = :last_error")
        params["last_error"] = error
    try:
        store.execute(
            f"update crawler_jobs set {', '.join(fields)} where id = cast(:job_id as bigint)",
            params,
        )
        record_crawler_job_log(
            job,
            "error" if status == "failed" else "info",
            f"job marked {status}",
            {"status": status, "pack_key": pack_key, "ref_sha": ref_sha, "error": error},
        )
        if status == "completed":
            store.execute(
                """
                update library_versions lv
                set last_crawled_at = now(), crawl_error_count = 0
                from crawler_jobs j
                where j.id = cast(:job_id as bigint)
                  and lv.library_id = j.library_id
                  and lv.version = coalesce(nullif(j.version, ''), lv.version)
                """,
                {"job_id": job_id},
            )
        if status == "failed":
            store.execute(
                """
                update library_versions lv
                set crawl_error_count = crawl_error_count + 1
                from crawler_jobs j
                where j.id = cast(:job_id as bigint)
                  and lv.library_id = j.library_id
                  and lv.version = coalesce(nullif(j.version, ''), lv.version)
                """,
                {"job_id": job_id},
            )
    except Exception:
        return


def record_crawler_job_log(
    job: dict[str, Any],
    level: str,
    message: str,
    metadata: dict[str, Any] | None = None,
) -> None:
    job_id = clean(job.get("db_job_id"))
    if not job_id:
        return
    store = AuthStore.from_env()
    if store is None:
        return
    try:
        store.execute(
            """
            insert into crawl_job_logs (job_id, level, message, metadata_json)
            values (
              cast(:job_id as bigint), :level, :message, cast(:metadata as jsonb)
            )
            """,
            {
                "job_id": job_id,
                "level": level or "info",
                "message": message[:1000],
                "metadata": json.dumps(metadata or {}, sort_keys=True),
            },
        )
    except Exception:
        return


def record_quality_run(entry: dict[str, Any], job: dict[str, Any], quality: dict[str, Any]) -> None:
    store = AuthStore.from_env()
    if store is None:
        raise RuntimeError("DATABASE_URL or OZ_DATABASE_URL is required")
    store.execute(
        """
        insert into quality_runs (
          job_id, library_id, version, passed, metrics, errors, warnings
        )
        select cast(:job_id as bigint), l.id, :version, :passed,
               cast(:metrics as jsonb), cast(:errors as jsonb), cast(:warnings as jsonb)
        from libraries l
        join vendors v on v.id = l.vendor_id
        where v.name = :vendor and l.name = :library
        """,
        {
            "job_id": clean(job.get("db_job_id")) or None,
            "vendor": clean(entry.get("vendor")),
            "library": clean(entry.get("library")),
            "version": clean(entry.get("version")) or "latest",
            "passed": bool(quality.get("passed")),
            "metrics": json.dumps(quality.get("metrics") or {}, sort_keys=True),
            "errors": json.dumps(quality.get("errors") or [], sort_keys=True),
            "warnings": json.dumps(quality.get("warnings") or [], sort_keys=True),
        },
    )


def record_pack_build(entry: dict[str, Any], job: dict[str, Any]) -> None:
    store = AuthStore.from_env()
    if store is None:
        raise RuntimeError("DATABASE_URL or OZ_DATABASE_URL is required")
    pack_key = clean(entry.get("pack_path"))
    pack_sha = clean(entry.get("ref_sha"))
    signature_key_id = clean(job.get("signing_key_id")) or os.environ.get("OZ_PACK_SIGNING_KEY_ID", "")
    if not pack_key or not pack_sha:
        raise RuntimeError("pack_key and ref_sha are required before recording pack build")
    store.execute(
        """
        insert into pack_builds (library_id, version, pack_sha, pack_key, signature_key_id)
        select l.id, :version, :pack_sha, :pack_key, :signature_key_id
        from libraries l
        join vendors v on v.id = l.vendor_id
        where v.name = :vendor and l.name = :library
        on conflict (library_id, version, pack_sha) do update
        set pack_key = excluded.pack_key,
            signature_key_id = excluded.signature_key_id
        """,
        {
            "vendor": clean(entry.get("vendor")),
            "library": clean(entry.get("library")),
            "version": clean(entry.get("version")) or "latest",
            "pack_sha": pack_sha,
            "pack_key": pack_key,
            "signature_key_id": clean(signature_key_id) or None,
        },
    )


def record_eval_run(
    entry: dict[str, Any],
    *,
    eval_type: str,
    passed: bool,
    metrics: dict[str, Any] | None = None,
) -> None:
    store = AuthStore.from_env()
    if store is None:
        raise RuntimeError("DATABASE_URL or OZ_DATABASE_URL is required")
    store.execute(
        """
        insert into eval_runs (library_id, version, eval_type, passed, metrics)
        select l.id, :version, :eval_type, :passed, cast(:metrics as jsonb)
        from libraries l
        join vendors v on v.id = l.vendor_id
        where v.name = :vendor and l.name = :library
        """,
        {
            "vendor": clean(entry.get("vendor")),
            "library": clean(entry.get("library")),
            "version": clean(entry.get("version")) or "latest",
            "eval_type": eval_type,
            "passed": passed,
            "metrics": json.dumps(metrics or {}, sort_keys=True),
        },
    )


def upsert_freshness_policy(payload: dict[str, Any], principal: AuthPrincipal | None) -> None:
    store = AuthStore.from_env()
    if store is None:
        return
    vendor = clean(payload.get("vendor") or payload.get("vendor_hint"))
    library = clean(payload.get("library_name") or payload.get("library"))
    source_url = clean(payload.get("source_url") or payload.get("source_url_hint"))
    version = clean(payload.get("version")) or "latest"
    if not vendor or not library or not source_url:
        return
    try:
        store.execute(
            """
            insert into freshness_policies (
              vendor, library, version, source_url, recrawl_interval_hours, created_by, updated_at
            )
            values (
              :vendor, :library, :version, :source_url, :interval_hours, cast(:created_by as uuid), now()
            )
            on conflict (vendor, library, version) do update
            set source_url = excluded.source_url,
                recrawl_interval_hours = excluded.recrawl_interval_hours,
                enabled = true,
                updated_at = now()
            """,
            {
                "vendor": vendor,
                "library": library,
                "version": version,
                "source_url": source_url,
                "interval_hours": int_value(payload.get("recrawl_interval_hours"), default=24, minimum=1),
                "created_by": principal.user_id if principal else None,
            },
        )
    except Exception:
        return


def set_library_default_version(payload: dict[str, Any], principal: AuthPrincipal | None) -> None:
    store = AuthStore.from_env()
    if store is None:
        raise RuntimeError("database is unavailable")
    vendor = clean(payload.get("vendor"))
    library = clean(payload.get("library_name") or payload.get("library"))
    version = clean(payload.get("version"))
    if not vendor or not library or not version:
        raise RuntimeError("vendor, library, and version are required")
    row = store.one(
        """
        select lv.id
        from library_versions lv
        join libraries l on l.id = lv.library_id
        join vendors v on v.id = l.vendor_id
        where v.name = :vendor and l.name = :library and lv.version = :version
          and lv.archived_at is null
        """,
        {"vendor": vendor, "library": library, "version": version},
    )
    if not row:
        raise RuntimeError(f"{vendor}/{library}@{version} is not an active indexed version")
    store.execute(
        """
        update libraries l
        set default_version_id = :version_id,
            updated_at = now()
        from vendors v
        where v.id = l.vendor_id and v.name = :vendor and l.name = :library
        """,
        {"version_id": row["id"], "vendor": vendor, "library": library},
    )
    log_admin_action(
        principal,
        "library_default_version_set",
        target_type="library",
        target=f"{vendor}/{library}",
        metadata={"version": version},
    )


def promote_library_version(payload: dict[str, Any], principal: AuthPrincipal | None) -> None:
    store = AuthStore.from_env()
    if store is None:
        raise RuntimeError("database is unavailable")
    vendor = clean(payload.get("vendor"))
    library = clean(payload.get("library_name") or payload.get("library"))
    version = clean(payload.get("version"))
    if not vendor or not library or not version:
        raise RuntimeError("vendor, library, and version are required")
    row = store.one(
        """
        select l.id as library_id, lv.id as version_id, lv.ref_sha
        from library_versions lv
        join libraries l on l.id = lv.library_id
        join vendors v on v.id = l.vendor_id
        where v.name = :vendor and l.name = :library and lv.version = :version
          and lv.archived_at is null
        """,
        {"vendor": vendor, "library": library, "version": version},
    )
    if not row:
        raise RuntimeError(f"{vendor}/{library}@{version} is not an active indexed version")
    store.execute(
        """
        insert into refs(library_id, channel, version_id, ref_sha)
        values (:library_id, 'latest', :version_id, :ref_sha)
        on conflict (library_id, channel) do update
          set version_id = excluded.version_id,
              ref_sha = excluded.ref_sha,
              updated_at = now()
        """,
        {"library_id": row["library_id"], "version_id": row["version_id"], "ref_sha": row["ref_sha"]},
    )
    log_admin_action(
        principal,
        "library_version_promoted",
        target_type="library",
        target=f"{vendor}/{library}",
        metadata={"version": version},
    )


def log_admin_action(
    principal: AuthPrincipal | None,
    action: str,
    *,
    target_type: str = "",
    target: str = "",
    metadata: dict[str, Any] | None = None,
) -> None:
    store = AuthStore.from_env()
    if store is None:
        return
    try:
        store.execute(
            """
            insert into admin_action_logs (user_id, action, target_type, target, metadata_json)
            values (
              cast(:user_id as uuid), :action, :target_type, :target, cast(:metadata as jsonb)
            )
            """,
            {
                "user_id": principal.user_id if principal else None,
                "action": action,
                "target_type": target_type or None,
                "target": target or None,
                "metadata": json.dumps(metadata or {}, sort_keys=True),
            },
        )
    except Exception:
        return


def clean(value: Any) -> str:
    return str(value or "").strip()


def require_db_store() -> AuthStore:
    store = AuthStore.from_env()
    if store is None:
        raise RuntimeError("DATABASE_URL or OZ_DATABASE_URL is required")
    return store


def profile_params(
    payload: dict[str, Any],
    principal: AuthPrincipal | None,
    vendor: str,
    library: str,
    source_url: str,
) -> dict[str, Any]:
    allowed_hosts = list_values(payload.get("allowed_hosts")) or [urlparse(source_url).netloc]
    allowed_paths = list_values(payload.get("allowed_paths")) or [urlparse(source_url).path or "/"]
    return {
        "vendor": vendor,
        "library": library,
        "description": clean(payload.get("description")) or f"Documentation crawled from {source_url}.",
        "source_url": source_url,
        "source_type": clean(payload.get("source_type")) or "official_docs",
        "priority": int_value(payload.get("priority"), default=100, minimum=1),
        "allowed_hosts": json.dumps(allowed_hosts, sort_keys=True),
        "allowed_paths": json.dumps(allowed_paths, sort_keys=True),
        "denied_paths": json.dumps(list_values(payload.get("denied_paths")), sort_keys=True),
        "source_priority": json.dumps(
            list_values(payload.get("source_priority") or payload.get("preferred_urls")),
            sort_keys=True,
        ),
        "required_topics": json.dumps(list_values(payload.get("required_topics")), sort_keys=True),
        "expected_symbols": json.dumps(list_values(payload.get("expected_symbols")), sort_keys=True),
        "min_quality_score": float_value(payload.get("min_quality_score"), default=0.35, minimum=0),
        "min_documents": int_value(payload.get("min_documents"), default=2, minimum=1),
        "max_junk_ratio": float_value(payload.get("max_junk_ratio"), default=0.25, minimum=0),
        "created_by": principal.user_id if principal else None,
    }


def decode_profile_row(row: dict[str, Any]) -> dict[str, Any]:
    return {
        "vendor": clean(row.get("vendor")),
        "library": clean(row.get("library")),
        "source_url": clean(row.get("source_url")),
        "allowed_hosts": json_values(row.get("allowed_hosts")),
        "allowed_paths": json_values(row.get("allowed_paths")),
        "denied_paths": json_values(row.get("denied_paths")),
        "source_priority": json_values(row.get("source_priority")),
        "preferred_urls": json_values(row.get("source_priority")),
        "required_topics": json_values(row.get("required_topics")),
        "expected_symbols": json_values(row.get("expected_symbols")),
        "min_quality_score": float(row.get("min_quality_score") or 0.35),
        "min_documents": int(row.get("min_documents") or 2),
        "max_junk_ratio": float(row.get("max_junk_ratio") or 0.25),
    }


def source_allowed(source_url: str, profile: dict[str, Any]) -> bool:
    parsed = urlparse(source_url)
    host = parsed.netloc.lower()
    path = parsed.path.lower() or "/"
    allowed_hosts = [item.lower() for item in profile.get("allowed_hosts", [])]
    allowed_paths = [item.lower() for item in profile.get("allowed_paths", [])]
    denied_paths = [item.lower() for item in profile.get("denied_paths", [])]
    if parsed.scheme not in {"http", "https"} or not host:
        return False
    if allowed_hosts and not any(host == item or host.endswith(f".{item}") for item in allowed_hosts):
        return False
    if denied_paths and any(path_matches_profile(path, item, root_matches_all=False) for item in denied_paths):
        return False
    if allowed_paths and not any(path_matches_profile(path, item, root_matches_all=True) for item in allowed_paths):
        return False
    return True


def path_matches_profile(path: str, pattern: str, *, root_matches_all: bool) -> bool:
    normalized = pattern.lower().strip()
    if not normalized:
        return False
    if normalized == "/":
        return root_matches_all or path == "/"
    return path.startswith(normalized)


def list_values(value: Any) -> list[str]:
    if isinstance(value, list):
        return [clean(item) for item in value if clean(item)]
    return [item.strip() for item in str(value or "").replace("\n", ",").split(",") if item.strip()]


def json_values(value: Any) -> list[str]:
    if isinstance(value, list):
        return [clean(item) for item in value if clean(item)]
    if not isinstance(value, str):
        return []
    try:
        parsed = json.loads(value)
    except json.JSONDecodeError:
        return []
    return list_values(parsed)


def first_source_url(entry: dict[str, Any]) -> str:
    urls = entry.get("source_urls")
    if isinstance(urls, list) and urls:
        return clean(urls[0])
    return clean(entry.get("source_url"))


def library_target(vendor: Any, library: Any) -> str:
    vendor_text = clean(vendor)
    library_text = clean(library)
    return f"{vendor_text}/{library_text}" if vendor_text and library_text else library_text


def int_value(value: Any, *, default: int, minimum: int) -> int:
    try:
        parsed = int(value)
    except (TypeError, ValueError):
        return default
    return max(minimum, parsed)


def float_value(value: Any, *, default: float, minimum: float) -> float:
    try:
        parsed = float(value)
    except (TypeError, ValueError):
        return default
    return max(minimum, parsed)
