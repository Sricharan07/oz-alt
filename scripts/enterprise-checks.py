#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import os
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any
from urllib.request import urlopen

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "packages" / "oz-api" / "src"))

from oz_api.auth_store import AuthStore  # noqa: E402
from oz_api.ops import record_system_check  # noqa: E402
from oz_api.redis_store import redis_client  # noqa: E402


def main() -> int:
    parser = argparse.ArgumentParser(description="Run Oz enterprise readiness checks and record results.")
    parser.add_argument("--api-url", default=os.environ.get("OZ_API_URL", ""))
    parser.add_argument("--require-recent-backup-hours", type=int, default=30)
    parser.add_argument("--require-search-quality", action="store_true")
    args = parser.parse_args()

    rows = run_checks(args)
    print(json.dumps({"passed": all(row["status"] == "ok" for row in rows), "checks": rows}, indent=2, sort_keys=True))
    return 0 if all(row["status"] == "ok" for row in rows) else 1


def run_checks(args: argparse.Namespace) -> list[dict[str, Any]]:
    rows = [
        check_database(),
        check_redis(),
        check_api_health(args.api_url),
        check_catalog_profiles(),
        check_latest_crawls(),
        check_quality_and_evals(),
        check_pack_signatures(),
        check_crawl_logs(),
        check_recent_verified_backup(args.require_recent_backup_hours),
    ]
    if args.require_search_quality:
        rows.append(check_search_quality())
    for row in rows:
        record_system_check(row["name"], row["status"], row["message"], row.get("metadata") or {})
    return rows


def check_database() -> dict[str, Any]:
    store = AuthStore.from_env()
    if store is None:
        return row("database", "fail", "DATABASE_URL is not configured")
    try:
        value = store.one("select 1 as ok")
    except Exception as exc:
        return row("database", "fail", str(exc))
    return row("database", "ok", "Postgres is reachable", {"ok": value})


def check_redis() -> dict[str, Any]:
    client = redis_client()
    if client is None:
        return row("redis", "fail", "Redis URL is not configured")
    try:
        pong = client.ping()
    except Exception as exc:
        return row("redis", "fail", str(exc))
    return row("redis", "ok", "Redis is reachable", {"ping": bool(pong)})


def check_api_health(api_url: str) -> dict[str, Any]:
    if not api_url:
        return row("api_health", "warn", "api URL not provided")
    try:
        with urlopen(api_url.rstrip("/") + "/health", timeout=10) as response:
            body = response.read().decode("utf-8", "replace")
    except Exception as exc:
        return row("api_health", "fail", str(exc))
    return row("api_health", "ok", "API health endpoint is reachable", {"body": body[:200]})


def check_catalog_profiles() -> dict[str, Any]:
    data = counts(
        """
        select
          (select count(*) from libraries) as libraries,
          (select count(*) from library_profiles) as profiles,
          (select count(*) from freshness_policies where enabled) as freshness
        """
    )
    status = "ok" if data.get("libraries", 0) > 0 and data["profiles"] >= data["libraries"] else "fail"
    return row("catalog_profiles", status, "Every library should have a production profile", data)


def check_latest_crawls() -> dict[str, Any]:
    data = counts(
        """
        with ranked as (
          select library_id, status, row_number() over (partition by library_id order by queued_at desc, id desc) rn
          from crawler_jobs
        )
        select
          (select count(*) from libraries) as libraries,
          count(*) filter (where rn = 1 and status = 'completed') as completed_latest,
          count(*) filter (where rn = 1 and status <> 'completed') as non_completed_latest
        from ranked
        where rn = 1
        """
    )
    status = "ok" if data.get("libraries", 0) == data.get("completed_latest", -1) else "fail"
    return row("latest_crawls", status, "Latest crawl per library should be completed", data)


def check_quality_and_evals() -> dict[str, Any]:
    data = counts(
        """
        with latest as (
          select id, library_id, version, queued_at
          from (
            select j.*,
                   row_number() over (partition by j.library_id order by j.queued_at desc, j.id desc) rn
            from crawler_jobs j
            where j.status = 'completed'
          ) ranked
          where rn = 1
        )
        select
          count(*) as latest_completed_jobs,
          count(*) filter (
            where exists (
              select 1 from quality_runs q
              where q.job_id = latest.id and q.passed
            )
          ) as latest_quality_passed,
          count(*) filter (
            where not exists (
              select 1 from quality_runs q
              where q.job_id = latest.id and q.passed
            )
          ) as latest_quality_missing,
          count(*) filter (
            where not exists (
              select 1 from eval_runs e
              where e.library_id = latest.library_id
                and e.version = latest.version
                and e.eval_type = 'pack_materialization'
                and e.passed
                and e.created_at >= latest.queued_at
            )
          ) as missing_pack_eval,
          count(*) filter (
            where exists (
              select 1 from eval_runs e
              where e.library_id = latest.library_id
                and e.version = latest.version
                and not e.passed
                and e.created_at >= latest.queued_at
            )
          ) as latest_eval_failed
        from latest
        """
    )
    status = (
        "ok"
        if data.get("latest_completed_jobs", 0) > 0
        and data.get("latest_quality_missing", 1) == 0
        and data.get("missing_pack_eval", 1) == 0
        and data.get("latest_eval_failed", 1) == 0
        else "fail"
    )
    return row("quality_evals", status, "Latest completed crawls should have passing quality and eval gates", data)


def check_pack_signatures() -> dict[str, Any]:
    data = counts(
        """
        with latest as (
          select library_id, version, metrics,
                 row_number() over (partition by library_id, version order by created_at desc, id desc) rn
          from eval_runs
          where eval_type = 'pack_materialization'
        )
        select
          count(*) as pack_materialization_evals,
          count(*) filter (where metrics #>> '{metrics,has_signature}' = 'true') as signed_pack_evals
        from latest
        where rn = 1
        """
    )
    status = (
        "ok"
        if data.get("pack_materialization_evals", 0) > 0
        and data["signed_pack_evals"] == data["pack_materialization_evals"]
        else "fail"
    )
    return row("pack_signatures", status, "Every latest pack materialization eval should report a signature", data)


def check_crawl_logs() -> dict[str, Any]:
    data = counts("select count(*) as crawl_job_logs from crawl_job_logs")
    status = "ok" if data.get("crawl_job_logs", 0) > 0 else "fail"
    return row("crawl_logs", status, "Crawler jobs should write step logs", data)


def check_recent_verified_backup(hours: int) -> dict[str, Any]:
    data = counts(
        """
        select
          count(*) filter (where status = 'verified') as verified_backups,
          count(*) filter (
            where status = 'verified' and restore_verified_at > now() - make_interval(hours => :hours)
          ) as recent_verified_backups
        from backup_runs
        """,
        {"hours": hours},
    )
    status = "ok" if data.get("recent_verified_backups", 0) > 0 else "fail"
    return row("verified_backup", status, "A verified backup should exist inside the recovery window", data)


def check_search_quality() -> dict[str, Any]:
    data = counts(
        """
        select
          count(*) as search_quality_runs,
          count(*) filter (where passed) as search_quality_passed
        from search_quality_runs
        where created_at > now() - interval '7 days'
        """
    )
    status = "ok" if data.get("search_quality_runs", 0) > 0 and data["search_quality_runs"] == data["search_quality_passed"] else "fail"
    return row("search_quality", status, "Recent search quality run should pass", data)


def counts(sql: str, params: dict[str, Any] | None = None) -> dict[str, Any]:
    store = AuthStore.from_env()
    if store is None:
        return {}
    result = store.one(sql, params or {})
    return {key: int(value) if isinstance(value, int) or str(value).isdigit() else value for key, value in (result or {}).items()}


def row(name: str, status: str, message: str, metadata: dict[str, Any] | None = None) -> dict[str, Any]:
    return {
        "name": name,
        "status": status,
        "message": message,
        "metadata": metadata or {},
        "checked_at": datetime.now(timezone.utc).isoformat(),
    }


if __name__ == "__main__":
    raise SystemExit(main())
