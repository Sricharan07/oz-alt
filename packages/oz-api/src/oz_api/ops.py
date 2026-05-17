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
