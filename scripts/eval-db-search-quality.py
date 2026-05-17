#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import os
import sys
from pathlib import Path
from typing import Any


def main() -> int:
    parser = argparse.ArgumentParser(description="Evaluate deployed Postgres search quality directly.")
    parser.add_argument("--repo-root", default=".")
    parser.add_argument("--record-db", action="store_true")
    parser.add_argument("--min-recall-at-5", type=float, default=0.85)
    parser.add_argument("--min-precision-at-5", type=float, default=0.75)
    parser.add_argument("--max-junk-top5-rate", type=float, default=0.0)
    parser.add_argument("--max-duplicate-top5-rate", type=float, default=0.0)
    parser.add_argument("--jury", action="store_true", help="Use the configured LLM judge for c7score-style scoring.")
    parser.add_argument("--min-jury-score", type=float, default=0.75)
    parser.add_argument("evals", nargs="*", default=["registry/evals/*.yaml"])
    args = parser.parse_args()

    repo = Path(args.repo_root).resolve()
    sys.path.insert(0, str(repo / "packages" / "oz-api" / "src"))

    from oz_api.retrieval import RetrievalContext, search  # noqa: PLC0415
    from oz_api.storage import RegistryStorage  # noqa: PLC0415

    storage = RegistryStorage.from_env(repo)
    ctx = RetrievalContext.from_env(storage)
    result = evaluate(
        repo,
        storage,
        ctx,
        search,
        expand_eval_files(repo, args.evals),
        min_recall_at_5=args.min_recall_at_5,
        min_precision_at_5=args.min_precision_at_5,
        max_junk_top5_rate=args.max_junk_top5_rate,
        max_duplicate_top5_rate=args.max_duplicate_top5_rate,
        jury=args.jury,
        min_jury_score=args.min_jury_score,
    )
    if args.record_db:
        record_db_results(repo, result)
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0 if result["passed"] else 1


def evaluate(
    repo: Path,
    storage: Any,
    ctx: Any,
    search_fn: Any,
    eval_files: list[Path],
    *,
    min_recall_at_5: float,
    min_precision_at_5: float,
    max_junk_top5_rate: float,
    max_duplicate_top5_rate: float,
    jury: bool,
    min_jury_score: float,
) -> dict[str, Any]:
    from oz_api.jury import judge_search_check  # noqa: PLC0415

    checks: list[dict[str, Any]] = []
    expected_hits = 0
    materialized_hits = 0
    duplicate_failures = 0
    junk_failures = 0
    junk_checks = 0
    reciprocal_sum = 0.0
    top1_hits = 0
    zero_results = 0
    content_failures = 0
    jury_scores: list[float] = []
    total = 0
    for eval_file in eval_files:
        spec = json.loads(eval_file.read_text(encoding="utf-8"))
        library = str(spec["library"])
        version = str(spec.get("version") or "latest")
        fixture = fixture_for_library(storage, library, version)
        for check in spec.get("checks", []):
            total += 1
            results = search_fn(ctx, str(check["query"]), library_scope=library, max_results=5, fingerprint="db-eval")
            top = results[:5]
            paths = [str(row.get("path") or "") for row in top]
            expected = [str(item) for item in check.get("expected_files", [])]
            ranks = [index + 1 for index, path in enumerate(paths) if any(path.endswith(item) for item in expected)]
            expected_hit = bool(ranks)
            expected_hits += int(expected_hit)
            top1_hits += int(bool(ranks) and ranks[0] == 1)
            reciprocal_sum += 1.0 / ranks[0] if ranks else 0.0
            zero_results += int(not results)
            duplicate = len(paths) != len(set(paths))
            duplicate_failures += int(duplicate)
            contents = [read_result_content(fixture, path) for path in paths]
            jury_result = judge_search_check(check, paths, [content or "" for content in contents]) if jury else {}
            if jury_result:
                jury_scores.append(float(jury_result.get("score") or 0))
            existing_count = sum(1 for content in contents if content is not None)
            materialized_hits += int(existing_count == len(top))
            required = [str(item).lower() for item in check.get("must_include", [])]
            banned = [str(item).lower() for item in check.get("must_not_include", [])]
            banned.extend(str(item).lower() for item in check.get("banned_content", []))
            joined = "\n".join(content or "" for content in contents).lower()
            content_ok = all(term in joined for term in required)
            content_failures += int(required and not content_ok)
            junk = any(term in joined for term in banned)
            junk_checks += int(bool(banned))
            junk_failures += int(junk)
            checks.append(
                {
                    "library": library,
                    "version": version,
                    "name": check.get("name", check["query"]),
                    "paths": paths,
                    "expected_files": expected,
                    "expected_file_hit": expected_hit,
                    "duplicate_top5": duplicate,
                    "junk_top5": junk,
                    "required_content_hit": content_ok,
                    "materialized_top5": f"{existing_count}/{len(top)}",
                    "top_rerank_scores": [row.get("rerank_score") for row in top[:5]],
                    "jury": jury_result,
                }
            )
    precision_at_5 = expected_hits / total if total else 0.0
    materialization = materialized_hits / total if total else 0.0
    duplicate_rate = duplicate_failures / total if total else 0.0
    junk_rate = junk_failures / max(junk_checks, 1)
    content_rate = 1 - (content_failures / total if total else 0.0)
    jury_score = sum(jury_scores) / len(jury_scores) if jury_scores else 0.0
    passed = (
        precision_at_5 >= min_recall_at_5
        and precision_at_5 >= min_precision_at_5
        and materialization == 1.0
        and duplicate_rate <= max_duplicate_top5_rate
        and junk_rate <= max_junk_top5_rate
        and content_rate == 1.0
        and (not jury or jury_score >= min_jury_score)
    )
    return {
        "passed": passed,
        "precision_at_1": round(top1_hits / total if total else 0.0, 3),
        "expected_file_precision_at_5": round(precision_at_5, 3),
        "expected_file_recall_at_5": round(precision_at_5, 3),
        "mrr": round(reciprocal_sum / total if total else 0.0, 3),
        "materialization_rate": round(materialization, 3),
        "zero_result_rate": round(zero_results / total if total else 0.0, 3),
        "junk_top5_rate": round(junk_rate, 3),
        "duplicate_top5_rate": round(duplicate_rate, 3),
        "content_requirement_rate": round(content_rate, 3),
        "jury_score": round(jury_score, 3) if jury else None,
        "checks": checks,
    }


def fixture_for_library(storage: Any, library: str, version: str) -> Path:
    catalog = storage.load_catalog()
    vendor, name = library.split("/", 1)
    for entry in catalog:
        if entry.get("vendor") == vendor and entry.get("library") == name and str(entry.get("version")) == version:
            return storage.repo_root / str(entry.get("fixture_path") or "")
    return storage.fixtures_root / vendor / name / version


def read_result_content(fixture: Path, result_path: str) -> str | None:
    if ".codo/vendors/" in result_path:
        after_version = result_path.split("@", 1)[1].lstrip("/")
        relative = after_version.split("/", 1)[1] if "/" in after_version else ""
    else:
        relative = result_path
    target = fixture / relative
    if not target.exists() or not target.is_file():
        return None
    return target.read_text(encoding="utf-8", errors="replace")


def expand_eval_files(repo: Path, patterns: list[str]) -> list[Path]:
    files: list[Path] = []
    for pattern in patterns:
        files.extend(path for path in sorted(repo.glob(pattern)) if path.is_file())
    return files


def record_db_results(repo: Path, result: dict[str, Any]) -> None:
    from oz_api.ops import record_search_quality_run  # noqa: PLC0415

    grouped: dict[tuple[str, str], list[dict[str, Any]]] = {}
    for check in result["checks"]:
        grouped.setdefault((check["library"], check["version"]), []).append(check)
    for (library, version), checks in grouped.items():
        record_search_quality_run(library, version, {**result, "checks": checks}, eval_type="semantic_search_db")


if __name__ == "__main__":
    raise SystemExit(main())
