#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import os
import shutil
import subprocess
import tempfile
from pathlib import Path
from typing import Any


def main() -> int:
    parser = argparse.ArgumentParser(description="Evaluate oz search expected-file quality.")
    parser.add_argument("--repo-root", default=".")
    parser.add_argument("--api-url", default="")
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
        result = evaluate_search(tmp_project, oz, env, eval_files)
    finally:
        shutil.rmtree(tmp_home, ignore_errors=True)
        shutil.rmtree(tmp_project, ignore_errors=True)
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0 if result["passed"] else 1


def evaluate_search(project: Path, oz: Path, env: dict[str, str], eval_files: list[Path]) -> dict[str, Any]:
    rows: list[dict[str, Any]] = []
    precision_hits = 0
    precision_total = 0
    materialized = 0
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
            expected_hit = any(
                any(str(row.get("path", "")).endswith(item) for item in expected)
                for row in top
            )
            existing_count = sum(1 for row in top if (project / str(row.get("path", ""))).exists())
            rows.append(
                {
                    "library": library,
                    "name": check.get("name", check["query"]),
                    "results": len(results),
                    "expected_file_hit": expected_hit,
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
    return {
        "passed": precision >= 0.7 and materialization == 1.0,
        "expected_file_precision_at_5": round(precision, 3),
        "materialization_rate": round(materialization, 3),
        "checks": rows,
    }


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


def run(command: list[str], *, cwd: Path, env: dict[str, str]) -> None:
    subprocess.run(command, cwd=cwd, env=env, check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)


if __name__ == "__main__":
    raise SystemExit(main())
