#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import os
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path
from typing import Any
from urllib import request


def main() -> int:
    parser = argparse.ArgumentParser(description="Evaluate oz search expected-file quality.")
    parser.add_argument("--repo-root", default=".")
    parser.add_argument("--api-url", default="")
    parser.add_argument("--record-db", action="store_true", help="Record results in search_quality_runs when DB env is set.")
    parser.add_argument("--min-expected-recall-at-5", type=float, default=0.85)
    parser.add_argument("--min-precision-at-5", type=float, default=0.75)
    parser.add_argument("--max-junk-top5-rate", type=float, default=0.0)
    parser.add_argument("--max-duplicate-top5-rate", type=float, default=0.0)
    parser.add_argument("--jury", action="store_true", help="Use an OpenAI-compatible judge endpoint for c7score-style scoring.")
    parser.add_argument("--min-jury-score", type=float, default=0.75)
    parser.add_argument("evals", nargs="*", default=["registry/evals/*.yaml"])
    args = parser.parse_args()

    repo = Path(args.repo_root).resolve()
    eval_files = expand_eval_files(repo, args.evals)
    oz = oz_binary(repo)
    tmp_home = Path(tempfile.mkdtemp(prefix="oz-search-home-"))
    tmp_project = Path(tempfile.mkdtemp(prefix="oz-search-project-"))
    env = os.environ.copy()
    env["HOME"] = str(tmp_home)
    env["OZ_DISABLE_KEYCHAIN"] = "1"
    try:
        if not args.api_url:
            attach_local_registry(repo, tmp_project)
        if args.api_url:
            run([str(oz), "login", "--api-url", args.api_url], cwd=tmp_project, env=env)
        run([str(oz), "init"], cwd=tmp_project, env=env)
        result = evaluate_search(
            tmp_project,
            oz,
            env,
            eval_files,
            min_expected_recall_at_5=args.min_expected_recall_at_5,
            min_precision_at_5=args.min_precision_at_5,
            max_junk_top5_rate=args.max_junk_top5_rate,
            max_duplicate_top5_rate=args.max_duplicate_top5_rate,
            jury=args.jury,
            min_jury_score=args.min_jury_score,
        )
        if args.record_db:
            record_db_results(result)
    finally:
        shutil.rmtree(tmp_home, ignore_errors=True)
        shutil.rmtree(tmp_project, ignore_errors=True)
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0 if result["passed"] else 1


def evaluate_search(
    project: Path,
    oz: Path,
    env: dict[str, str],
    eval_files: list[Path],
    *,
    min_expected_recall_at_5: float,
    min_precision_at_5: float,
    max_junk_top5_rate: float,
    max_duplicate_top5_rate: float,
    jury: bool,
    min_jury_score: float,
) -> dict[str, Any]:
    rows: list[dict[str, Any]] = []
    precision_hits = 0
    precision_total = 0
    materialized = 0
    reciprocal_sum = 0.0
    top1_hits = 0
    zero_results = 0
    junk_checks = 0
    junk_failures = 0
    duplicate_failures = 0
    content_requirement_failures = 0
    jury_scores: list[float] = []
    for eval_file in eval_files:
        spec = json.loads(eval_file.read_text(encoding="utf-8"))
        library = spec["library"]
        version = spec.get("version")
        for check in spec.get("checks", []):
            output = subprocess.check_output(
                [str(oz), "search", str(check["query"]), library, "--json"],
                cwd=project,
                env=env,
                text=True,
                stderr=subprocess.STDOUT,
            )
            data = json.loads(output)
            results = data.get("results", [])
            top = results[:5]
            expected = [str(item) for item in check.get("expected_files", [])]
            banned_files = [str(item) for item in check.get("banned_files", [])]
            banned_content = [str(item).lower() for item in check.get("banned_content", [])]
            banned_content.extend(str(item).lower() for item in check.get("must_not_include", []))
            required_content = [str(item).lower() for item in check.get("must_include", [])]
            paths = [str(row.get("path", "")) for row in top]
            hit_ranks = [idx + 1 for idx, path in enumerate(paths) if any(path.endswith(item) for item in expected)]
            expected_hit = bool(hit_ranks)
            duplicate_top5 = len(paths) != len(set(paths))
            duplicate_failures += int(duplicate_top5)
            junk_hit = any(any(path.endswith(item) for item in banned_files) for path in paths)
            materialized_contents = read_result_contents(project, paths)
            jury_result = judge_check(check, paths, materialized_contents) if jury else {}
            if jury_result:
                jury_scores.append(float(jury_result.get("score") or 0))
            joined_content = "\n".join(materialized_contents).lower()
            content_requirement_hit = all(term in joined_content for term in required_content)
            content_requirement_failures += int(required_content and not content_requirement_hit)
            if banned_content:
                junk_checks += 1
                junk_hit = junk_hit or any(term in content.lower() for term in banned_content for content in materialized_contents)
            else:
                junk_checks += int(bool(banned_files))
            junk_failures += int(junk_hit)
            if hit_ranks:
                reciprocal_sum += 1.0 / hit_ranks[0]
                top1_hits += int(hit_ranks[0] == 1)
            else:
                zero_results += int(not results)
            existing_count = sum(1 for row in top if (project / str(row.get("path", ""))).exists())
            rows.append(
                {
                    "library": library,
                    "version": str(version or "latest"),
                    "name": check.get("name", check["query"]),
                    "results": len(results),
                    "paths": paths,
                    "expected_files": expected,
                    "expected_file_hit": expected_hit,
                    "banned_files": banned_files,
                    "junk_top5": junk_hit,
                    "duplicate_top5": duplicate_top5,
                    "required_content_hit": content_requirement_hit,
                    "jury": jury_result,
                    "materialized_top5": f"{existing_count}/{len(top)}",
                    "first_path": str(top[0].get("path", "")) if top else "",
                }
            )
            precision_hits += int(expected_hit)
            precision_total += 1
            materialized += int(existing_count == len(top))
        if version:
            vendor_root(project, library, version)
    precision = precision_hits / precision_total if precision_total else 0.0
    materialization = materialized / precision_total if precision_total else 0.0
    top1 = top1_hits / precision_total if precision_total else 0.0
    mrr = reciprocal_sum / precision_total if precision_total else 0.0
    zero_rate = zero_results / precision_total if precision_total else 0.0
    junk_top5_rate = junk_failures / max(junk_checks, 1)
    duplicate_top5_rate = duplicate_failures / precision_total if precision_total else 0.0
    content_requirement_rate = 1 - (content_requirement_failures / precision_total if precision_total else 0.0)
    jury_score = sum(jury_scores) / len(jury_scores) if jury_scores else 0.0
    passed = (
        precision >= min_expected_recall_at_5
        and precision >= min_precision_at_5
        and materialization == 1.0
        and junk_top5_rate <= max_junk_top5_rate
        and duplicate_top5_rate <= max_duplicate_top5_rate
        and content_requirement_rate == 1.0
        and (not jury or jury_score >= min_jury_score)
    )
    return {
        "passed": passed,
        "precision_at_1": round(top1, 3),
        "expected_file_precision_at_5": round(precision, 3),
        "expected_file_recall_at_5": round(precision, 3),
        "mrr": round(mrr, 3),
        "materialization_rate": round(materialization, 3),
        "zero_result_rate": round(zero_rate, 3),
        "junk_top5_rate": round(junk_top5_rate, 3),
        "duplicate_top5_rate": round(duplicate_top5_rate, 3),
        "content_requirement_rate": round(content_requirement_rate, 3),
        "jury_score": round(jury_score, 3) if jury else None,
        "thresholds": {
            "min_expected_recall_at_5": min_expected_recall_at_5,
            "min_precision_at_5": min_precision_at_5,
            "max_junk_top5_rate": max_junk_top5_rate,
            "max_duplicate_top5_rate": max_duplicate_top5_rate,
            "min_jury_score": min_jury_score if jury else None,
        },
        "checks": rows,
    }


def judge_check(check: dict[str, Any], paths: list[str], contents: list[str]) -> dict[str, Any]:
    api_key = os.environ.get("OZ_EVAL_JURY_API_KEY", "").strip()
    endpoint = os.environ.get("OZ_EVAL_JURY_URL", "").strip()
    model = os.environ.get("OZ_EVAL_JURY_MODEL", "").strip()
    if not api_key or not endpoint or not model:
        raise RuntimeError("jury eval requires OZ_EVAL_JURY_API_KEY, OZ_EVAL_JURY_URL, and OZ_EVAL_JURY_MODEL")
    snippets = [
        {"path": path, "content": contents[index][:2500] if index < len(contents) else ""}
        for index, path in enumerate(paths[:5])
    ]
    payload = {
        "model": model,
        "temperature": 0,
        "response_format": {"type": "json_object"},
        "messages": [
            {
                "role": "system",
                "content": (
                    "Score documentation search results for a coding agent. Return only JSON with "
                    "relevance, correctness, clarity, score, and reason. Scores are floats from 0 to 1."
                ),
            },
            {
                "role": "user",
                "content": json.dumps(
                    {
                        "query": check.get("query"),
                        "expected_files": check.get("expected_files", []),
                        "must_include": check.get("must_include", []),
                        "banned_files": check.get("banned_files", []),
                        "results": snippets,
                    },
                    sort_keys=True,
                ),
            },
        ],
    }
    body = request_json(endpoint, payload, {"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"})
    content = body.get("choices", [{}])[0].get("message", {}).get("content") if isinstance(body, dict) else None
    parsed = json.loads(content) if isinstance(content, str) else {}
    relevance = score_field(parsed, "relevance")
    correctness = score_field(parsed, "correctness")
    clarity = score_field(parsed, "clarity")
    score = score_field(parsed, "score")
    if score == 0 and any((relevance, correctness, clarity)):
        score = (relevance + correctness + clarity) / 3.0
    return {
        "relevance": round(relevance, 3),
        "correctness": round(correctness, 3),
        "clarity": round(clarity, 3),
        "score": round(score, 3),
        "reason": str(parsed.get("reason") or "")[:500] if isinstance(parsed, dict) else "",
    }


def score_field(payload: dict[str, Any], field: str) -> float:
    try:
        return max(0.0, min(float(payload.get(field) or 0), 1.0))
    except (TypeError, ValueError):
        return 0.0


def request_json(endpoint: str, payload: dict[str, Any], headers: dict[str, str]) -> dict[str, Any]:
    req = request.Request(endpoint, data=json.dumps(payload).encode("utf-8"), headers=headers, method="POST")
    with request.urlopen(req, timeout=float(os.environ.get("OZ_EVAL_JURY_TIMEOUT_SECONDS", "45"))) as response:
        body = json.loads(response.read().decode("utf-8"))
    return body if isinstance(body, dict) else {}


def record_db_results(result: dict[str, Any]) -> None:
    repo = Path(__file__).resolve().parents[1]
    sys_path = str(repo / "packages" / "oz-api" / "src")
    if sys_path not in sys.path:
        sys.path.insert(0, sys_path)
    from oz_api.ops import record_search_quality_run  # noqa: PLC0415

    by_library: dict[tuple[str, str], list[dict[str, Any]]] = {}
    for check in result.get("checks", []):
        if isinstance(check, dict):
            by_library.setdefault(
                (str(check.get("library") or ""), str(check.get("version") or "latest")),
                [],
            ).append(check)
    for (library, version), checks in by_library.items():
        if not library:
            continue
        subset = {**result, "checks": checks}
        record_search_quality_run(library, version, subset)


def expand_eval_files(repo: Path, patterns: list[str]) -> list[Path]:
    files: list[Path] = []
    for pattern in patterns:
        files.extend(path for path in sorted(repo.glob(pattern)) if path.is_file())
    return files


def oz_binary(repo: Path) -> Path:
    candidate = repo / "target" / "debug" / "oz"
    if candidate.exists():
        return candidate
    installed = shutil.which("oz")
    if installed:
        return Path(installed)
    run(["cargo", "build", "-p", "oz"], cwd=repo, env=os.environ.copy())
    return candidate


def attach_local_registry(repo: Path, project: Path) -> None:
    source = repo / "registry"
    target = project / "registry"
    try:
        os.symlink(source, target, target_is_directory=True)
    except OSError:
        shutil.copytree(source, target)


def vendor_root(project: Path, library: str, version: str | None) -> Path:
    vendor, name = library.split("/", 1)
    root = project / ".codo" / "vendors" / vendor
    if version:
        return root / f"{name}@{version}"
    matches = sorted(root.glob(f"{name}@*"))
    if not matches:
        raise RuntimeError(f"{library} was not materialized")
    return matches[-1]


def read_result_contents(project: Path, paths: list[str]) -> list[str]:
    contents: list[str] = []
    for path in paths:
        target = project / path
        if target.exists() and target.is_file():
            contents.append(target.read_text(encoding="utf-8", errors="replace"))
    return contents


def run(command: list[str], *, cwd: Path, env: dict[str, str]) -> None:
    subprocess.run(command, cwd=cwd, env=env, check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)


if __name__ == "__main__":
    raise SystemExit(main())
