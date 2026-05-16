#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path
from typing import Any


def main() -> int:
    parser = argparse.ArgumentParser(description="Evaluate the agent pull -> rg/read workflow.")
    parser.add_argument("--repo-root", default=".", help="Repository root.")
    parser.add_argument("--api-url", default="", help="Optional Oz API URL. Defaults to local registry packs.")
    parser.add_argument("evals", nargs="*", default=["registry/evals/*.yaml"])
    args = parser.parse_args()

    repo = Path(args.repo_root).resolve()
    eval_files = expand_eval_files(repo, args.evals)
    if not eval_files:
        raise SystemExit("no eval files matched")

    oz = oz_binary(repo)
    tmp_home = Path(tempfile.mkdtemp(prefix="oz-eval-home-"))
    tmp_project = Path(tempfile.mkdtemp(prefix="oz-eval-project-"))
    env = os.environ.copy()
    env["HOME"] = str(tmp_home)
    env["OZ_DISABLE_KEYCHAIN"] = "1"

    try:
        if not args.api_url:
            attach_local_registry(repo, tmp_project)
        if args.api_url:
            run([str(oz), "login", "--api-url", args.api_url], cwd=tmp_project, env=env)
        run([str(oz), "init"], cwd=tmp_project, env=env)
        result = evaluate_all(repo, tmp_project, oz, env, eval_files)
    finally:
        shutil.rmtree(tmp_home, ignore_errors=True)
        shutil.rmtree(tmp_project, ignore_errors=True)
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0 if result["passed"] else 1


def expand_eval_files(repo: Path, patterns: list[str]) -> list[Path]:
    files: list[Path] = []
    for pattern in patterns:
        matches = sorted(repo.glob(pattern))
        files.extend(path for path in matches if path.is_file())
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


def evaluate_all(repo: Path, project: Path, oz: Path, env: dict[str, str], eval_files: list[Path]) -> dict[str, Any]:
    checks: list[dict[str, Any]] = []
    expected_hits = 0
    expected_total = 0
    junk_hits = 0
    for eval_file in eval_files:
        spec = json.loads(eval_file.read_text(encoding="utf-8"))
        library = spec["library"]
        version = spec.get("version")
        pull_spec = f"{library}@{version}" if version else library
        run([str(oz), "pull", pull_spec], cwd=project, env=env)
        root = vendor_root(project, library, version)
        for check in spec.get("checks", []):
            row = evaluate_check(project, root, check)
            checks.append({"library": library, **row})
            expected_hits += int(row["expected_file_hit"])
            expected_total += 1
            junk_hits += int(row["junk_hit"])
    expected_recall = expected_hits / expected_total if expected_total else 0.0
    passed = expected_recall >= 0.8 and junk_hits == 0 and all(row["must_include_passed"] for row in checks)
    return {
        "passed": passed,
        "expected_file_recall_at_5": round(expected_recall, 3),
        "junk_top5_rate": round(junk_hits / expected_total, 3) if expected_total else 0.0,
        "checks": checks,
    }


def vendor_root(project: Path, library: str, version: str | None) -> Path:
    vendor, name = library.split("/", 1)
    root = project / ".codo" / "vendors" / vendor
    if version:
        return root / f"{name}@{version}"
    matches = sorted(root.glob(f"{name}@*"))
    if not matches:
        raise RuntimeError(f"{library} was not materialized")
    return matches[-1]


def evaluate_check(project: Path, root: Path, check: dict[str, Any]) -> dict[str, Any]:
    pattern = "|".join(f"(?:{item})" for item in check.get("patterns", [])) or re.escape(check["query"])
    rg = subprocess.run(
        ["rg", "-l", "-i", "--glob", "*.md", pattern, str(root)],
        cwd=project,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=False,
    )
    files = [Path(line) for line in rg.stdout.splitlines() if line.strip()]
    top_files = ranked_files(project, files, check)[:5]
    relative_top = [path.relative_to(project).as_posix() for path in top_files]
    top_text = "\n".join(path.read_text(encoding="utf-8", errors="replace")[:12000] for path in top_files)
    expected = [str(item) for item in check.get("expected_files", [])]
    expected_hit = any(any(path.endswith(item) for path in relative_top) for item in expected)
    must_include_passed = all(re.search(str(item), top_text, re.I) for item in check.get("must_include", []))
    junk_hit = any(re.search(str(item), top_text, re.I) for item in check.get("must_not_include", []))
    return {
        "name": check.get("name", check.get("query", "")),
        "match_files": len(files),
        "top_files": relative_top,
        "expected_file_hit": expected_hit,
        "must_include_passed": must_include_passed,
        "junk_hit": junk_hit,
    }


def ranked_files(project: Path, files: list[Path], check: dict[str, Any]) -> list[Path]:
    patterns = [str(item) for item in check.get("patterns", [])] or [re.escape(str(check["query"]))]
    query_terms = [compact(term) for term in re.findall(r"[A-Za-z0-9_.-]+", str(check.get("query", ""))) if len(term) > 2]
    scored = []
    for path in files:
        text = path.read_text(encoding="utf-8", errors="replace")
        counts = [len(re.findall(pattern, text, re.I)) for pattern in patterns]
        distinct = sum(1 for count in counts if count > 0)
        occurrences = sum(min(count, 25) for count in counts)
        relative = path.relative_to(project).as_posix().lower()
        compact_path = compact(relative)
        path_hits = sum(1 for term in query_terms if term and term in compact_path)
        index_penalty = 1 if path.name in {"INDEX.md", "README.md"} else 0
        noise_penalty = 1 if any(token in relative for token in ("changelog", "release-notes", "migration-guide")) else 0
        scored.append((distinct, occurrences, path_hits, -index_penalty, -noise_penalty, relative, path))
    scored.sort(key=lambda row: (-row[0], -row[2], -row[1], -row[3], -row[4], row[5]))
    return [row[6] for row in scored]


def compact(value: str) -> str:
    return re.sub(r"[^a-z0-9]+", "", value.lower())


def run(command: list[str], *, cwd: Path, env: dict[str, str]) -> None:
    subprocess.run(command, cwd=cwd, env=env, check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)


if __name__ == "__main__":
    raise SystemExit(main())
