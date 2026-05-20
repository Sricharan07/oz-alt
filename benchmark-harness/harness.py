#!/usr/bin/env python3
from __future__ import annotations

import argparse
import datetime as dt
import json
import os
import re
import shutil
import signal
import subprocess
import sys
import tempfile
import time
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
HARNESS = Path(__file__).resolve().parent
CASES_PATH = HARNESS / "cases.json"
RUNS = HARNESS / "runs"
AGENT_PROMPT = HARNESS / "prompts" / "agent_task.md"
JUDGE_RUBRIC = HARNESS / "prompts" / "judge_rubric.md"


def main() -> int:
    parser = argparse.ArgumentParser(description="Run Oz agent documentation benchmarks.")
    sub = parser.add_subparsers(dest="cmd", required=True)

    validate = sub.add_parser("validate", help="Validate benchmark case definitions.")
    validate.add_argument("--cases", default=str(CASES_PATH))

    run = sub.add_parser("run", help="Run benchmark cases.")
    run.add_argument("--cases", default=str(CASES_PATH))
    run.add_argument("--mode", choices=["retrieval", "agent"], default="retrieval")
    run.add_argument("--case", dest="case_id", default="", help="Run one case id.")
    run.add_argument("--library", default="", help="Run one library, for example vercel/next.js.")
    run.add_argument("--limit", type=int, default=0, help="Limit number of cases.")
    run.add_argument("--oz-bin", default=os.environ.get("OZ_BIN", ""))
    run.add_argument("--skip-build", action="store_true")
    run.add_argument("--build-packs", action="store_true", help="Run oz dev registry build-packs before cases.")
    run.add_argument("--agent-model", default="gpt-5.4-mini")
    run.add_argument("--agent-timeout", type=int, default=1800)
    run.add_argument("--command-timeout", type=int, default=120, help="Timeout for each Oz command in seconds.")
    run.add_argument("--max-results", type=int, default=10)
    run.add_argument("--read-results", type=int, default=1, help="Number of search results to read from disk.")
    run.add_argument("--window-lines", type=int, default=80, help="Maximum lines to read around each search hit.")
    run.add_argument("--context-tokens", type=int, default=2000)
    run.add_argument("--strict", action="store_true", help="Fail the run when quality gates do not pass.")
    run.add_argument("--min-hit-at-5", type=float, default=0.8, help="Strict gate for expected-path hit@5.")
    run.add_argument("--min-required-terms", type=float, default=0.8, help="Strict gate for required-term coverage.")
    run.add_argument("--min-materialized", type=float, default=1.0, help="Gate for materialized top-5 paths.")
    run.add_argument("--max-search-tokens", type=float, default=500.0, help="Strict gate for average compact search tokens.")
    run.add_argument("--out", default="")

    summarize = sub.add_parser("summarize", help="Summarize a benchmark run directory.")
    summarize.add_argument("run_dir")

    args = parser.parse_args()
    if args.cmd == "validate":
        cases = load_cases(Path(args.cases))
        errors = validate_cases(cases)
        if errors:
            for error in errors:
                print(error, file=sys.stderr)
            return 1
        print(f"ok: {len(flatten_cases(cases))} cases")
        return 0
    if args.cmd == "run":
        return run_benchmark(args)
    if args.cmd == "summarize":
        summary = summarize_run(Path(args.run_dir))
        print(json.dumps(summary, indent=2, sort_keys=True))
        return 0
    raise AssertionError(args.cmd)


def load_cases(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def flatten_cases(spec: dict[str, Any]) -> list[dict[str, Any]]:
    out: list[dict[str, Any]] = []
    for lib in spec.get("libraries", []):
        library = str(lib["library"])
        version = str(lib.get("version", "latest"))
        for case in lib.get("cases", []):
            row = dict(case)
            row["library"] = library
            row["version"] = version
            out.append(row)
    return out


def validate_cases(spec: dict[str, Any]) -> list[str]:
    errors: list[str] = []
    ids: set[str] = set()
    libraries = spec.get("libraries")
    if not isinstance(libraries, list) or not libraries:
        errors.append("cases.json must contain non-empty libraries list")
        return errors
    for lib in libraries:
        library = str(lib.get("library", ""))
        cases = lib.get("cases")
        if not re.fullmatch(r"[^/\s]+/[^@\s]+", library):
            errors.append(f"invalid library id: {library}")
        if not isinstance(cases, list) or len(cases) != 10:
            errors.append(f"{library} must have exactly 10 cases")
            continue
        for case in cases:
            case_id = str(case.get("id", ""))
            if not re.fullmatch(r"[a-z0-9][a-z0-9-]+", case_id):
                errors.append(f"{library}: invalid case id {case_id!r}")
            if case_id in ids:
                errors.append(f"duplicate case id: {case_id}")
            ids.add(case_id)
            for key in ("query", "expected_paths", "required_terms"):
                if key not in case:
                    errors.append(f"{case_id}: missing {key}")
            if not str(case.get("query", "")).strip():
                errors.append(f"{case_id}: empty query")
    return errors


def run_benchmark(args: argparse.Namespace) -> int:
    spec = load_cases(Path(args.cases))
    errors = validate_cases(spec)
    if errors:
        for error in errors:
            print(error, file=sys.stderr)
        return 1

    cases = flatten_cases(spec)
    if args.case_id:
        cases = [case for case in cases if case["id"] == args.case_id]
    if args.library:
        cases = [case for case in cases if case["library"] == args.library]
    if args.limit:
        cases = cases[: args.limit]
    if not cases:
        print("no cases selected", file=sys.stderr)
        return 1

    oz_bin = resolve_oz_bin(args.oz_bin, skip_build=args.skip_build)
    if args.build_packs:
        run_cmd(
            [str(oz_bin), "dev", "registry", "build-packs"],
            cwd=ROOT,
            env=bench_env(Path(tempfile.mkdtemp(prefix="oz-bench-home-")), oz_bin=oz_bin),
        )

    run_id = dt.datetime.now(dt.timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    run_dir = Path(args.out) if args.out else RUNS / run_id
    run_dir.mkdir(parents=True, exist_ok=True)
    results: list[dict[str, Any]] = []

    for index, case in enumerate(cases, start=1):
        print(f"[{index}/{len(cases)}] {case['id']} {case['library']}", file=sys.stderr)
        case_result = run_case(case, run_dir, oz_bin, args)
        results.append(case_result)
        write_json(run_dir / "summary.json", aggregate_results(run_id, results))

    summary = aggregate_results(run_id, results, args)
    write_json(run_dir / "summary.json", summary)
    print(json.dumps(summary, indent=2, sort_keys=True))
    return 0 if summary["passed"] else 1


def resolve_oz_bin(value: str, *, skip_build: bool) -> Path:
    if value:
        path = Path(value).expanduser().resolve()
        if not path.exists():
            raise SystemExit(f"oz binary not found: {path}")
        return path
    path = ROOT / "target" / "debug" / "oz"
    if not path.exists() and not skip_build:
        run_cmd(["cargo", "build", "-p", "oz"], cwd=ROOT)
    if not path.exists():
        raise SystemExit("oz binary not found; run cargo build -p oz or pass --oz-bin")
    return path


def run_case(case: dict[str, Any], run_dir: Path, oz_bin: Path, args: argparse.Namespace) -> dict[str, Any]:
    case_dir = run_dir / "cases" / case["id"]
    workspace = case_dir / "workspace"
    home = case_dir / "home"
    case_dir.mkdir(parents=True, exist_ok=True)
    workspace.mkdir(parents=True, exist_ok=True)
    home.mkdir(parents=True, exist_ok=True)
    write_json(case_dir / "case.json", case)
    (workspace / "README.md").write_text(
        f"# Benchmark Workspace\n\nCase: {case['id']}\nLibrary: {case['library']}\n",
        encoding="utf-8",
    )

    env = bench_env(home, oz_bin=oz_bin)
    run_cmd([str(oz_bin), "init"], cwd=workspace, env=env, timeout=args.command_timeout)
    pull = run_cmd_capture([str(oz_bin), "pull", case["library"]], cwd=workspace, env=env, timeout=args.command_timeout)
    write_text(case_dir / "oz_pull.out", pull.stdout)
    write_text(case_dir / "oz_pull.err", pull.stderr)

    search = run_cmd_capture(
        [
            str(oz_bin),
            "search",
            case["query"],
            case["library"],
            "--compact-json",
            "--max-results",
            str(args.max_results),
        ],
        cwd=workspace,
        env=env,
        timeout=args.command_timeout,
    )
    write_text(case_dir / "oz_search.raw", search.stdout)
    write_text(case_dir / "oz_search.err", search.stderr)
    search_json = parse_json_or_empty(search.stdout)
    write_json(case_dir / "oz_search.json", search_json)

    context = run_cmd_capture(
        [
            str(oz_bin),
            "context",
            case["query"],
            case["library"],
            "--json",
            "--max-results",
            "8",
            "--max-tokens",
            str(args.context_tokens),
        ],
        cwd=workspace,
        env=env,
        timeout=args.command_timeout,
    )
    write_text(case_dir / "oz_context.raw", context.stdout)
    write_text(case_dir / "oz_context.err", context.stderr)
    context_json = parse_json_or_empty(context.stdout)
    write_json(case_dir / "oz_context.json", context_json)

    read_files = read_top_files(
        workspace,
        search_json,
        limit=args.read_results,
        window_lines=args.window_lines,
    )
    write_json(case_dir / "read_files.json", read_files)
    metrics = score_retrieval(case, workspace, search_json, context_json, read_files)
    write_json(case_dir / "retrieval_metrics.json", metrics)

    agent = {"ran": False, "ok": None, "answer_exists": False}
    if args.mode == "agent":
        agent = run_agent(case, case_dir, workspace, oz_bin, env, args)

    write_judge_packet(case, case_dir, metrics, read_files, agent)
    result = {
        "case_id": case["id"],
        "library": case["library"],
        "query": case["query"],
        "metrics": metrics,
        "agent": agent,
        "case_dir": str(case_dir),
    }
    write_json(case_dir / "result.json", result)
    return result


def bench_env(home: Path, *, oz_bin: Path | None = None) -> dict[str, str]:
    env = os.environ.copy()
    env["HOME"] = str(home)
    env["OZ_DISABLE_KEYCHAIN"] = "1"
    env["OZ_TELEMETRY"] = "off"
    path_prefix = oz_bin.parent if oz_bin else ROOT / "target" / "debug"
    env["PATH"] = f"{path_prefix}{os.pathsep}{env.get('PATH', '')}"
    env.pop("OZ_API_URL", None)
    return env


def run_agent(case: dict[str, Any], case_dir: Path, workspace: Path, oz_bin: Path, env: dict[str, str], args: argparse.Namespace) -> dict[str, Any]:
    if not shutil.which("codex"):
        return {"ran": False, "ok": False, "answer_exists": False, "error": "codex executable not found"}
    prompt_template = AGENT_PROMPT.read_text(encoding="utf-8")
    prompt = (
        prompt_template.replace("{case_id}", case["id"])
        .replace("{library}", case["library"])
        .replace("{library_prefix}", case["library"])
        .replace("{query}", case["query"])
    )
    prompt += (
        "\n\nExecution details:\n"
        f"- Use this exact Oz binary if needed: `{oz_bin}`\n"
        f"- Current workspace: `{workspace}`\n"
        "- Write only `benchmark_answer.json` unless you need scratch notes.\n"
    )
    write_text(case_dir / "agent_prompt.md", prompt)
    cmd = [
        "codex",
        "exec",
        "--json",
        "--sandbox",
        "workspace-write",
        "--skip-git-repo-check",
        "--model",
        args.agent_model,
        "-C",
        str(workspace),
        "-o",
        str(case_dir / "agent_final.txt"),
        "-",
    ]
    agent_env = env.copy()
    codex_home = os.environ.get("CODEX_HOME")
    if codex_home:
        agent_env["CODEX_HOME"] = codex_home
    else:
        agent_env["CODEX_HOME"] = str(Path.home() / ".codex")
    proc = run_cmd_capture(cmd, cwd=workspace, env=agent_env, input_text=prompt, timeout=args.agent_timeout, check=False)
    write_text(case_dir / "agent_stdout.jsonl", proc.stdout)
    write_text(case_dir / "agent_stderr.log", proc.stderr)
    answer_src = workspace / "benchmark_answer.json"
    answer_dst = case_dir / "benchmark_answer.json"
    answer_exists = answer_src.exists()
    if answer_exists:
        shutil.copy2(answer_src, answer_dst)
    return {
        "ran": True,
        "ok": proc.returncode == 0 and answer_exists,
        "returncode": proc.returncode,
        "answer_exists": answer_exists,
        "model": args.agent_model,
    }


def read_top_files(
    workspace: Path,
    search_json: dict[str, Any],
    *,
    limit: int,
    window_lines: int,
) -> list[dict[str, Any]]:
    out: list[dict[str, Any]] = []
    for row in search_json.get("results", [])[:limit]:
        rel = str(row.get("path") or "")
        path = workspace / rel
        text = ""
        exists = path.exists()
        start_line = int(row.get("line") or 1)
        end_line = int(row.get("end_line") or start_line)
        window_start = start_line
        window_end = end_line
        if exists:
            text, window_start, window_end = read_line_window(
                path,
                start_line=start_line,
                end_line=end_line,
                window_lines=window_lines,
            )
        out.append(
            {
                "path": rel,
                "line": start_line,
                "end_line": end_line,
                "window_start": window_start,
                "window_end": window_end,
                "exists": exists,
                "tokens_est": estimate_tokens(text),
                "preview": text[:2400],
            }
        )
    return out


def read_line_window(
    path: Path,
    *,
    start_line: int,
    end_line: int,
    window_lines: int,
) -> tuple[str, int, int]:
    lines = path.read_text(encoding="utf-8", errors="ignore").splitlines()
    if not lines:
        return "", 1, 1
    max_lines = max(20, window_lines)
    first = max(1, min(start_line, len(lines)))
    last = max(first, min(end_line, len(lines)))
    first = max(1, first - 8)
    if last - first + 1 > max_lines:
        last = first + max_lines - 1
    else:
        last = min(len(lines), max(last, first + max_lines - 1))
    selected = lines[first - 1 : last]
    return "\n".join(selected), first, last


def score_retrieval(
    case: dict[str, Any],
    workspace: Path,
    search_json: dict[str, Any],
    context_json: dict[str, Any],
    read_files: list[dict[str, Any]],
) -> dict[str, Any]:
    results = search_json.get("results", [])
    paths = [str(row.get("path") or "") for row in results]
    top5 = paths[:5]
    expected = [str(item) for item in case.get("expected_paths", [])]
    required_terms = [str(item) for item in case.get("required_terms", [])]
    banned_terms = [str(item).lower() for item in case.get("banned_terms", [])]
    expected_ranks = [idx + 1 for idx, path in enumerate(paths) if path_matches_any(path, expected)]
    top5_joined = "\n".join(item.get("preview", "") for item in read_files).lower()
    context_text = json.dumps(context_json, ensure_ascii=False).lower()
    required_found = [term for term in required_terms if term.lower() in top5_joined or term.lower() in context_text]
    banned_found = [term for term in banned_terms if term in top5_joined or term in context_text]
    materialized_top5 = sum(1 for path in top5 if (workspace / path).exists())
    return {
        "result_count": len(results),
        "top5_paths": top5,
        "expected_paths": expected,
        "expected_path_hit_at_1": bool(expected_ranks and expected_ranks[0] == 1),
        "expected_path_hit_at_5": any(rank <= 5 for rank in expected_ranks),
        "best_expected_rank": expected_ranks[0] if expected_ranks else None,
        "materialized_top5": f"{materialized_top5}/{min(5, len(results))}",
        "materialized_top5_rate": materialized_top5 / max(1, min(5, len(results))),
        "required_terms": required_terms,
        "required_terms_found": required_found,
        "required_terms_found_rate": len(required_found) / max(1, len(required_terms)),
        "banned_terms_found": banned_found,
        "oz_search_output_tokens_est": estimate_tokens(json.dumps(search_json)),
        "oz_context_output_tokens_est": estimate_tokens(json.dumps(context_json)),
        "docs_read_tokens_est": sum(int(item.get("tokens_est", 0)) for item in read_files),
        "docs_read_mode": "line_windows",
        "docs_read_results": len(read_files),
    }


def path_matches_any(path: str, expected: list[str]) -> bool:
    normalized = path.replace("\\", "/").lower()
    for item in expected:
        needle = item.replace("\\", "/").lower()
        if normalized.endswith(needle) or needle in normalized:
            return True
    return False


def write_judge_packet(
    case: dict[str, Any],
    case_dir: Path,
    metrics: dict[str, Any],
    read_files: list[dict[str, Any]],
    agent: dict[str, Any],
) -> None:
    answer_path = case_dir / "benchmark_answer.json"
    answer = answer_path.read_text(encoding="utf-8", errors="ignore") if answer_path.exists() else "(no agent answer)"
    rubric = JUDGE_RUBRIC.read_text(encoding="utf-8")
    lines = [
        "# Judge Packet",
        "",
        "## Case",
        "",
        f"- ID: `{case['id']}`",
        f"- Library: `{case['library']}`",
        f"- Query: {case['query']}",
        f"- Intent: `{case.get('intent', '')}`",
        f"- Expected paths: {case.get('expected_paths', [])}",
        f"- Required terms: {case.get('required_terms', [])}",
        "",
        "## Retrieval Metrics",
        "",
        "```json",
        json.dumps(metrics, indent=2, sort_keys=True),
        "```",
        "",
        "## Agent",
        "",
        "```json",
        json.dumps(agent, indent=2, sort_keys=True),
        "```",
        "",
        "## Agent Answer",
        "",
        "```json",
        answer,
        "```",
        "",
        "## Read Evidence",
        "",
    ]
    for item in read_files:
        lines.extend(
            [
                f"### {item.get('path')}",
                "",
                f"- Exists: {item.get('exists')}",
                f"- Tokens estimate: {item.get('tokens_est')}",
                f"- Window: {item.get('window_start')}-{item.get('window_end')}",
                "",
                "```md",
                str(item.get("preview", ""))[:2400],
                "```",
                "",
            ]
        )
    lines.extend(["## Rubric", "", rubric])
    write_text(case_dir / "judge_packet.md", "\n".join(lines).strip() + "\n")


def aggregate_results(run_id: str, results: list[dict[str, Any]], args: argparse.Namespace | None = None) -> dict[str, Any]:
    metrics = [row["metrics"] for row in results]
    count = len(metrics)
    retrieval = {
        "expected_path_hit_at_1": avg(metrics, "expected_path_hit_at_1"),
        "expected_path_hit_at_5": avg(metrics, "expected_path_hit_at_5"),
        "materialized_top5_rate": avg(metrics, "materialized_top5_rate"),
        "required_terms_found_rate": avg(metrics, "required_terms_found_rate"),
        "avg_search_tokens_est": avg(metrics, "oz_search_output_tokens_est"),
        "avg_context_tokens_est": avg(metrics, "oz_context_output_tokens_est"),
        "avg_docs_read_tokens_est": avg(metrics, "docs_read_tokens_est"),
    }
    strict = bool(args and args.strict)
    gates = {
        "materialized_top5_rate": {
            "value": retrieval["materialized_top5_rate"],
            "threshold": args.min_materialized if args else 1.0,
            "passed": retrieval["materialized_top5_rate"] >= (args.min_materialized if args else 1.0),
            "strict": True,
        },
        "expected_path_hit_at_5": {
            "value": retrieval["expected_path_hit_at_5"],
            "threshold": args.min_hit_at_5 if args else 0.8,
            "passed": retrieval["expected_path_hit_at_5"] >= (args.min_hit_at_5 if args else 0.8),
            "strict": strict,
        },
        "required_terms_found_rate": {
            "value": retrieval["required_terms_found_rate"],
            "threshold": args.min_required_terms if args else 0.8,
            "passed": retrieval["required_terms_found_rate"] >= (args.min_required_terms if args else 0.8),
            "strict": strict,
        },
        "avg_search_tokens_est": {
            "value": retrieval["avg_search_tokens_est"],
            "threshold": args.max_search_tokens if args else 500.0,
            "passed": retrieval["avg_search_tokens_est"] <= (args.max_search_tokens if args else 500.0),
            "strict": strict,
        },
    }
    passed = all(gate["passed"] for gate in gates.values() if gate["strict"])
    return {
        "run_id": run_id,
        "case_count": count,
        "passed": passed,
        "gates": gates,
        "retrieval": retrieval,
        "agent": {
            "answer_exists_rate": avg([row.get("agent", {}) for row in results], "answer_exists"),
            "ok_rate": avg([row.get("agent", {}) for row in results], "ok"),
        },
        "results": results,
    }


def summarize_run(run_dir: Path) -> dict[str, Any]:
    summary = run_dir / "summary.json"
    if summary.exists():
        return json.loads(summary.read_text(encoding="utf-8"))
    results = [json.loads(path.read_text(encoding="utf-8")) for path in sorted((run_dir / "cases").glob("*/result.json"))]
    return aggregate_results(run_dir.name, results)


def avg(rows: list[dict[str, Any]], key: str) -> float:
    if not rows:
        return 0.0
    values: list[float] = []
    for row in rows:
        value = row.get(key)
        if isinstance(value, bool):
            values.append(1.0 if value else 0.0)
        elif isinstance(value, (int, float)):
            values.append(float(value))
    if not values:
        return 0.0
    return round(sum(values) / len(values), 4)


def estimate_tokens(text: str) -> int:
    return max(1, (len(text) + 3) // 4)


def parse_json_or_empty(text: str) -> dict[str, Any]:
    try:
        return json.loads(text)
    except Exception:
        return {"results": [], "parse_error": text[:1000]}


def run_cmd(cmd: list[str], cwd: Path, env: dict[str, str] | None = None, timeout: int = 300) -> None:
    proc = run_cmd_capture(cmd, cwd=cwd, env=env, timeout=timeout)
    if proc.returncode != 0:
        raise RuntimeError(proc.stderr or proc.stdout or f"command failed: {cmd}")


def run_cmd_capture(
    cmd: list[str],
    cwd: Path,
    env: dict[str, str] | None = None,
    input_text: str | None = None,
    timeout: int = 300,
    check: bool = True,
) -> subprocess.CompletedProcess[str]:
    stdout_file = tempfile.NamedTemporaryFile("w+", encoding="utf-8", delete=False)
    stderr_file = tempfile.NamedTemporaryFile("w+", encoding="utf-8", delete=False)
    stdin_handle = subprocess.PIPE if input_text is not None else subprocess.DEVNULL
    try:
        proc = subprocess.Popen(
            cmd,
            cwd=cwd,
            env=env,
            stdin=stdin_handle,
            stdout=stdout_file,
            stderr=stderr_file,
            text=True,
            start_new_session=True,
        )
        if input_text is not None and proc.stdin is not None:
            proc.stdin.write(input_text)
            proc.stdin.close()
        timed_out = False
        deadline = time.monotonic() + max(1, timeout)
        returncode = None
        while time.monotonic() < deadline:
            returncode = proc.poll()
            if returncode is not None:
                break
            time.sleep(0.05)
        if returncode is None:
            timed_out = True
            try:
                os.killpg(proc.pid, signal.SIGTERM)
            except Exception:
                proc.terminate()
            kill_deadline = time.monotonic() + 5
            while time.monotonic() < kill_deadline:
                returncode = proc.poll()
                if returncode is not None:
                    break
                time.sleep(0.05)
            if returncode is None:
                try:
                    os.killpg(proc.pid, signal.SIGKILL)
                except Exception:
                    proc.kill()
                while returncode is None:
                    returncode = proc.poll()
                    time.sleep(0.05)
        stdout_file.flush()
        stderr_file.flush()
        stdout = Path(stdout_file.name).read_text(encoding="utf-8", errors="ignore")
        stderr = Path(stderr_file.name).read_text(encoding="utf-8", errors="ignore")
        if timed_out:
            stderr = (stderr + "\n" if stderr else "") + f"command timed out after {timeout}s"
    finally:
        stdout_name = stdout_file.name
        stderr_name = stderr_file.name
        stdout_file.close()
        stderr_file.close()
        Path(stdout_name).unlink(missing_ok=True)
        Path(stderr_name).unlink(missing_ok=True)
    proc = subprocess.CompletedProcess(cmd, returncode, stdout, stderr)
    if check and proc.returncode != 0:
        raise RuntimeError(proc.stderr or proc.stdout or f"command failed: {cmd}")
    return proc


def write_json(path: Path, value: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def write_text(path: Path, value: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(value, encoding="utf-8")


if __name__ == "__main__":
    raise SystemExit(main())
