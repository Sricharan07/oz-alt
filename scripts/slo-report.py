#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "packages" / "oz-api" / "src"))
sys.path.insert(0, str(ROOT / "scripts"))

from ops_notifier import deliver_alert  # noqa: E402
from oz_api.auth_store import AuthStore  # noqa: E402
from oz_api.ops import record_ops_alert, record_slo_report, resolve_ops_alerts  # noqa: E402


def main() -> int:
    parser = argparse.ArgumentParser(description="Compute and record Oz SLO evidence from production tables.")
    parser.add_argument("--window-hours", type=int, default=24)
    parser.add_argument("--api-health-target", type=float, default=0.995)
    parser.add_argument("--search-quality-target", type=float, default=1.0)
    parser.add_argument("--crawler-success-target", type=float, default=0.95)
    parser.add_argument("--pack-signature-target", type=float, default=1.0)
    args = parser.parse_args()

    result = build_report(args)
    record_slo_report(result)
    if result["passed"]:
        resolved = resolve_ops_alerts("slo:")
        result["resolved_alerts"] = resolved
        print(json.dumps(result, indent=2, sort_keys=True))
        return 0
    delivery_status, delivery_error = deliver_alert({"service": "oz", "severity": "warning", **result})
    record_ops_alert(
        fingerprint=f"slo:{args.window_hours}h",
        severity="warning",
        title="Oz SLO report failed",
        body=json.dumps(result, indent=2, sort_keys=True),
        metadata=result,
        delivery_status=delivery_status,
        delivery_error=delivery_error,
    )
    print(json.dumps(result, indent=2, sort_keys=True))
    return 1


def build_report(args: argparse.Namespace) -> dict[str, Any]:
    end = datetime.now(timezone.utc)
    start = end - timedelta(hours=args.window_hours)
    metrics = collect_metrics(start, end)
    passed = (
        metrics["api_health_ok_rate"] >= args.api_health_target
        and metrics["search_quality_pass_rate"] >= args.search_quality_target
        and metrics["crawler_success_rate"] >= args.crawler_success_target
        and metrics["pack_signature_coverage"] >= args.pack_signature_target
        and metrics["backup_fresh"]
    )
    return {
        "passed": passed,
        "window_start": start.isoformat(),
        "window_end": end.isoformat(),
        "targets": {
            "api_health_ok_rate": args.api_health_target,
            "search_quality_pass_rate": args.search_quality_target,
            "crawler_success_rate": args.crawler_success_target,
            "pack_signature_coverage": args.pack_signature_target,
            "backup_fresh": True,
        },
        "metrics": metrics,
    }


def collect_metrics(start: datetime, end: datetime) -> dict[str, Any]:
    store = AuthStore.from_env()
    if store is None:
        raise SystemExit("DATABASE_URL or OZ_DATABASE_URL is required")
    params = {"start": start.isoformat(), "end": end.isoformat()}
    api = store.one(
        """
        select count(*) as total,
               count(*) filter (where status = 'ok') as ok
        from system_checks
        where check_name = 'api_health'
          and created_at >= cast(:start as timestamptz)
          and created_at < cast(:end as timestamptz)
        """,
        params,
    ) or {}
    search = store.one(
        """
        select count(*) as total,
               count(*) filter (where passed) as passed
        from search_quality_runs
        where created_at >= cast(:start as timestamptz)
          and created_at < cast(:end as timestamptz)
        """,
        params,
    ) or {}
    crawler = store.one(
        """
        with latest as (
          select library_id, status,
                 row_number() over (partition by library_id order by queued_at desc, id desc) rn
          from crawler_jobs
        )
        select count(*) as total,
               count(*) filter (where status = 'completed') as passed
        from latest
        where rn = 1
        """,
        params,
    ) or {}
    packs = store.one(
        """
        with latest as (
          select library_id, version, metrics,
                 row_number() over (partition by library_id, version order by created_at desc, id desc) rn
          from eval_runs
          where eval_type = 'pack_materialization'
        )
        select count(*) as total,
               count(*) filter (where metrics #>> '{metrics,has_signature}' = 'true') as signed
        from latest
        where rn = 1
        """
    ) or {}
    backup = store.one(
        """
        select count(*) as fresh
        from backup_runs
        where status = 'verified'
          and restore_verified_at > now() - interval '30 hours'
        """
    ) or {}
    return {
        "api_health_ok_rate": ratio(api.get("ok"), api.get("total"), default=1.0),
        "search_quality_pass_rate": ratio(search.get("passed"), search.get("total"), default=1.0),
        "crawler_success_rate": ratio(crawler.get("passed"), crawler.get("total"), default=1.0),
        "pack_signature_coverage": ratio(packs.get("signed"), packs.get("total"), default=0.0),
        "backup_fresh": int(backup.get("fresh") or 0) > 0,
        "raw": {"api": api, "search": search, "crawler": crawler, "packs": packs, "backup": backup},
    }


def ratio(numerator: Any, denominator: Any, *, default: float) -> float:
    total = int(denominator or 0)
    if total == 0:
        return default
    return int(numerator or 0) / total


if __name__ == "__main__":
    raise SystemExit(main())
