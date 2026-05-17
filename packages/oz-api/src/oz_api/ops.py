from __future__ import annotations

import json
from typing import Any

from oz_api.auth_store import AuthStore


def record_search_quality_run(
    library: str,
    version: str,
    result: dict[str, Any],
    *,
    eval_type: str = "semantic_search",
) -> None:
    vendor, name = split_library(library)
    store = AuthStore.from_env()
    if store is None:
        return
    metrics = result_metrics(result)
    store.execute(
        """
        insert into search_quality_runs (
          library_id, version, eval_type, passed, precision_at_1, precision_at_5,
          mrr, materialization_rate, zero_result_rate, junk_top5_rate, metrics
        )
        select l.id, :version, :eval_type, :passed, :precision_at_1, :precision_at_5,
               :mrr, :materialization_rate, :zero_result_rate, :junk_top5_rate,
               cast(:metrics as jsonb)
        from libraries l
        join vendors v on v.id = l.vendor_id
        where v.name = :vendor and l.name = :library
        """,
        {
            "vendor": vendor,
            "library": name,
            "version": version or "latest",
            "eval_type": eval_type,
            "passed": bool(result.get("passed")),
            "precision_at_1": metrics["precision_at_1"],
            "precision_at_5": metrics["precision_at_5"],
            "mrr": metrics["mrr"],
            "materialization_rate": metrics["materialization_rate"],
            "zero_result_rate": metrics["zero_result_rate"],
            "junk_top5_rate": metrics["junk_top5_rate"],
            "metrics": json.dumps(result, sort_keys=True),
        },
    )


def record_system_check(check_name: str, status: str, message: str, metadata: dict[str, Any] | None = None) -> None:
    store = AuthStore.from_env()
    if store is None:
        return
    store.execute(
        """
        insert into system_checks (check_name, status, message, metadata_json)
        values (:check_name, :status, :message, cast(:metadata as jsonb))
        """,
        {
            "check_name": check_name,
            "status": status if status in {"ok", "warn", "fail"} else "fail",
            "message": message[:1000],
            "metadata": json.dumps(metadata or {}, sort_keys=True),
        },
    )


def record_ops_alert(
    *,
    fingerprint: str,
    severity: str,
    title: str,
    body: str,
    metadata: dict[str, Any] | None = None,
    delivery_status: str | None = None,
    delivery_error: str | None = None,
) -> None:
    store = AuthStore.from_env()
    if store is None:
        return
    store.execute(
        """
        insert into ops_alerts (
          fingerprint, severity, status, title, body, metadata_json,
          delivery_status, delivery_error, delivered_at
        )
        values (
          :fingerprint, :severity, 'open', :title, :body, cast(:metadata as jsonb),
          :delivery_status, :delivery_error,
          case when :delivery_status = 'delivered' then now() else null end
        )
        on conflict (fingerprint) do update
        set severity = excluded.severity,
            status = 'open',
            title = excluded.title,
            body = excluded.body,
            metadata_json = excluded.metadata_json,
            delivery_status = excluded.delivery_status,
            delivery_error = excluded.delivery_error,
            delivered_at = coalesce(excluded.delivered_at, ops_alerts.delivered_at),
            resolved_at = null,
            updated_at = now()
        """,
        {
            "fingerprint": fingerprint[:240],
            "severity": severity if severity in {"info", "warning", "critical"} else "warning",
            "title": title[:240],
            "body": body[:4000],
            "metadata": json.dumps(metadata or {}, sort_keys=True),
            "delivery_status": delivery_status,
            "delivery_error": (delivery_error or "")[:1000] or None,
        },
    )


def resolve_ops_alerts(prefix: str) -> int:
    store = AuthStore.from_env()
    if store is None:
        return 0
    rows = store.execute(
        """
        update ops_alerts
        set status = 'resolved', resolved_at = now(), updated_at = now()
        where fingerprint like :prefix and status = 'open'
        returning id
        """,
        {"prefix": f"{prefix}%"},
    )
    return len(rows)


def record_slo_report(result: dict[str, Any]) -> None:
    store = AuthStore.from_env()
    if store is None:
        return
    metrics = result.get("metrics") if isinstance(result.get("metrics"), dict) else {}
    store.execute(
        """
        insert into slo_reports (
          window_start, window_end, passed, api_health_ok_rate, search_quality_pass_rate,
          crawler_success_rate, pack_signature_coverage, backup_fresh, metrics
        )
        values (
          cast(:window_start as timestamptz),
          cast(:window_end as timestamptz),
          :passed,
          :api_health_ok_rate,
          :search_quality_pass_rate,
          :crawler_success_rate,
          :pack_signature_coverage,
          :backup_fresh,
          cast(:metrics as jsonb)
        )
        """,
        {
            "window_start": result["window_start"],
            "window_end": result["window_end"],
            "passed": bool(result.get("passed")),
            "api_health_ok_rate": float(metrics.get("api_health_ok_rate") or 0),
            "search_quality_pass_rate": float(metrics.get("search_quality_pass_rate") or 0),
            "crawler_success_rate": float(metrics.get("crawler_success_rate") or 0),
            "pack_signature_coverage": float(metrics.get("pack_signature_coverage") or 0),
            "backup_fresh": bool(metrics.get("backup_fresh")),
            "metrics": json.dumps(metrics, sort_keys=True),
        },
    )


def result_metrics(result: dict[str, Any]) -> dict[str, float]:
    checks = result.get("checks") if isinstance(result.get("checks"), list) else []
    total = len(checks)
    top1_hits = 0
    reciprocal_sum = 0.0
    zero_results = 0
    for check in checks:
        if not isinstance(check, dict):
            continue
        paths = [str(item) for item in check.get("paths", []) if item]
        expected = [str(item) for item in check.get("expected_files", []) if item]
        if not paths:
            zero_results += 1
        ranks = [
            idx + 1
            for idx, path in enumerate(paths)
            if any(path.endswith(expected_path) for expected_path in expected)
        ]
        if ranks:
            reciprocal_sum += 1.0 / ranks[0]
            top1_hits += int(ranks[0] == 1)
    return {
        "precision_at_1": top1_hits / total if total else float(result.get("precision_at_1") or 0),
        "precision_at_5": float(
            result.get("expected_file_precision_at_5")
            or result.get("precision_at_5")
            or result.get("expected_file_recall_at_5")
            or 0
        ),
        "mrr": reciprocal_sum / total if total else float(result.get("mrr") or 0),
        "materialization_rate": float(result.get("materialization_rate") or 0),
        "zero_result_rate": zero_results / total if total else float(result.get("zero_result_rate") or 0),
        "junk_top5_rate": float(result.get("junk_top5_rate") or 0),
    }


def split_library(library: str) -> tuple[str, str]:
    if "/" not in library:
        return "", library
    vendor, name = library.split("/", 1)
    return vendor, name
