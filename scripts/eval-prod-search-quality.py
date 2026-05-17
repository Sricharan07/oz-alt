#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

from prod_smoke_support import cleanup_paths, configure_cli, create_cli_auth, npm_install, run, smoke_env, temp_workspace


def main() -> int:
    parser = argparse.ArgumentParser(description="Evaluate production oz search through the published npm CLI.")
    parser.add_argument("--repo-root", default=".")
    parser.add_argument("--app-url", default="https://app.tryoz.dev")
    parser.add_argument("--api-url", default="https://api.tryoz.dev")
    parser.add_argument("--write-json", default="", help="Optional path for the result JSON.")
    parser.add_argument("evals", nargs="*", default=["registry/evals/*.yaml"])
    args = parser.parse_args()

    repo = Path(args.repo_root).resolve()
    eval_files = expand_eval_files(repo, args.evals)
    tmp_home, tmp_project, tmp_install = temp_workspace("oz-prod-search")
    try:
        oz = npm_install(tmp_install)
        auth = create_cli_auth(args.app_url, args.api_url, label="beta-smoke")
        env = smoke_env(tmp_home)
        configure_cli(oz, args.api_url, auth, env)
        run([str(oz), "init"], cwd=tmp_project, env=env)
        result = evaluate(tmp_project, oz, env, eval_files)
        result["auth_email"] = auth["email"]
    finally:
        cleanup_paths(tmp_home, tmp_project, tmp_install)

    payload = json.dumps(result, indent=2, sort_keys=True)
    if args.write_json:
        Path(args.write_json).write_text(payload + "\n", encoding="utf-8")
    print(payload)
    return 0 if result["passed"] else 1


def evaluate(project: Path, oz: Path, env: dict[str, str], eval_files: list[Path]) -> dict[str, Any]:
    checks: list[dict[str, Any]] = []
    expected_hits = 0
    materialized_checks = 0
    top1_hits = 0
    reciprocal_sum = 0.0
    zero_results = 0
    for eval_file in eval_files:
        spec = json.loads(eval_file.read_text(encoding="utf-8"))
        library = str(spec["library"])
        version = str(spec.get("version") or "latest")
        for check in spec.get("checks", []):
            query = str(check["query"])
            output = run([str(oz), "search", query, library, "--json"], cwd=project, env=env, echo=False)
            data = json.loads(output)
            results = data.get("results", [])
            top = results[:5]
            expected = [str(item) for item in check.get("expected_files", [])]
            paths = [str(row.get("path", "")) for row in top]
            hit_ranks = [idx + 1 for idx, path in enumerate(paths) if any(path.endswith(item) for item in expected)]
            existing = sum(1 for path in paths if (project / path).exists())
            expected_hits += int(bool(hit_ranks))
            top1_hits += int(bool(hit_ranks) and hit_ranks[0] == 1)
            reciprocal_sum += (1.0 / hit_ranks[0]) if hit_ranks else 0.0
            zero_results += int(not results)
            materialized_checks += int(existing == len(paths) and bool(paths))
            checks.append(
                {
                    "library": library,
                    "version": version,
                    "name": str(check.get("name") or query),
                    "query": query,
                    "results": len(results),
                    "paths": paths,
                    "expected_files": expected,
                    "expected_file_hit": bool(hit_ranks),
                    "materialized_top5": f"{existing}/{len(paths)}",
                    "first_path": paths[0] if paths else "",
                }
            )
    total = len(checks)
    precision = expected_hits / total if total else 0.0
    materialization = materialized_checks / total if total else 0.0
    return {
        "passed": precision >= 0.75 and materialization == 1.0,
        "precision_at_1": round(top1_hits / total, 3) if total else 0.0,
        "expected_file_precision_at_5": round(precision, 3),
        "mrr": round(reciprocal_sum / total, 3) if total else 0.0,
        "materialization_rate": round(materialization, 3),
        "zero_result_rate": round(zero_results / total, 3) if total else 0.0,
        "checks": checks,
    }


def expand_eval_files(repo: Path, patterns: list[str]) -> list[Path]:
    files: list[Path] = []
    for pattern in patterns:
        files.extend(path for path in sorted(repo.glob(pattern)) if path.is_file())
    if not files:
        raise SystemExit("no eval files matched")
    return files


if __name__ == "__main__":
    raise SystemExit(main())
