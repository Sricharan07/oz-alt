#!/usr/bin/env python3
from __future__ import annotations

import json
import os
import shutil
import subprocess
import time
import urllib.error
import urllib.parse
import urllib.request
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from openai import OpenAI


EVAL_DIR = Path(__file__).resolve().parent
HARNESS_ROOT = EVAL_DIR.parent
REPO_ROOT = HARNESS_ROOT.parent
ROOT = REPO_ROOT
ENV_PATH = HARNESS_ROOT / ".env"
EVAL_ENV_PATH = EVAL_DIR / ".env"
EVAL_API_KEY_PATH = EVAL_DIR / ".oz_eval_api_key"
OUT_DIR = EVAL_DIR / ".ingestion_work" / "evals"
OZ_EVAL_WORKSPACE = EVAL_DIR / ".ingestion_work" / "oz-workspace"
OZ_LIBRARY_NAME_DEFAULT = "Next.js"
OZ_VERSION_HINT_DEFAULT = "canary"
OZ_MCP_URL_DEFAULT = "http://localhost:8090/api/v2/mcp"
OZ_CONTEXT_ID_FALLBACK = ""
LIBRARY_ID = os.getenv("OZ_EVAL_LIBRARY_ID", "/vercel/next")
CTX7_ID = os.getenv("CTX7_LIBRARY_ID", "/vercel/next.js")

QUERIES = [
    "How to setup app router",
    "How to create a page with app/page.tsx",
    "How to add nested layouts in App Router",
    "How to navigate between pages with Link in App Router",
    "How to define a route handler in app/api",
    "How to use generateStaticParams",
    "How to redirect in App Router",
    "How to configure images in next.config.js",
    "How to use Server Actions in App Router",
    "How to fetch data in Server Components",
    "How to use generateMetadata",
    "How to set up Jest for Next.js",
    "How to test app-dir routes in the Next.js repo?",
    "How to use @next/routing resolveRoutes?",
    "How does Next.js internal router-server work?",
    "How to use revalidateTag",
    "How to set up parallel routes",
    "How to create dynamic routes in App Router",
    "How to migrate from Pages Router to App Router",
    "How to configure TypeScript in Next.js App Router",
]

METRICS = [
    "relevance",
    "actionability",
    "code_utility",
    "token_efficiency",
    "source_grounding",
    "overall",
]


@dataclass
class CommandResult:
    command: list[str]
    stdout: str
    stderr: str
    exit_code: int
    duration_ms: int


def load_env(path: Path, *, override: bool = False) -> None:
    if not path.exists():
        return
    for line in path.read_text(encoding="utf-8").splitlines():
        s = line.strip()
        if not s or s.startswith("#") or "=" not in s:
            continue
        key, value = s.split("=", 1)
        key = key.strip()
        value = value.strip().strip('"').strip("'")
        if key and (override or key not in os.environ):
            os.environ[key] = value


def run_command(cmd: list[str], timeout: int = 120) -> CommandResult:
    if cmd and cmd[0] == "ctx7" and not shutil.which("ctx7"):
        return run_context7_api_compatible(cmd, timeout=timeout)
    return run_subprocess(cmd, timeout=timeout, cwd=ROOT, env=os.environ.copy())


def run_subprocess(
    cmd: list[str],
    *,
    timeout: int = 120,
    cwd: Path,
    env: dict[str, str],
) -> CommandResult:
    start = datetime.now(timezone.utc)
    try:
        proc = subprocess.run(
            cmd,
            cwd=cwd,
            env=env,
            capture_output=True,
            text=True,
            timeout=timeout,
        )
        stdout = proc.stdout
        stderr = proc.stderr
        exit_code = proc.returncode
    except FileNotFoundError as exc:
        stdout = ""
        stderr = str(exc)
        exit_code = 127
    except subprocess.TimeoutExpired as exc:
        stdout = exc.stdout if isinstance(exc.stdout, str) else ""
        stderr = f"timeout after {timeout}s"
        exit_code = 124
    end = datetime.now(timezone.utc)
    duration_ms = int((end - start).total_seconds() * 1000)
    return CommandResult(
        command=cmd,
        stdout=stdout,
        stderr=stderr,
        exit_code=exit_code,
        duration_ms=duration_ms,
    )


def run_context7_api_compatible(cmd: list[str], *, timeout: int = 120) -> CommandResult:
    started = datetime.now(timezone.utc)
    api_key = (
        os.getenv("CONTEXT7_API_KEY")
        or os.getenv("CTX7_API_KEY")
        or os.getenv("CTX7_TOKEN")
        or ""
    ).strip()
    if len(cmd) < 4 or cmd[1] != "docs":
        return CommandResult(cmd, "", "unsupported ctx7 command shape", 2, 0)
    if not api_key:
        return CommandResult(
            cmd,
            "",
            "ctx7 CLI is not installed and CONTEXT7_API_KEY/CTX7_API_KEY is not set",
            127,
            0,
        )
    library_id = cmd[2]
    query = " ".join(cmd[3:]).strip()
    params = urllib.parse.urlencode({"libraryId": library_id, "query": query, "type": "json"})
    req = urllib.request.Request(
        f"https://context7.com/api/v2/context?{params}",
        headers={
            "Accept": "application/json",
            "Authorization": f"Bearer {api_key}",
            "User-Agent": "oz-eval-harness/1.0",
        },
        method="GET",
    )
    stdout = ""
    stderr = ""
    exit_code = 0
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            payload = json.loads(resp.read().decode("utf-8"))
            stdout = context7_payload_to_text(payload)
    except urllib.error.HTTPError as exc:
        stderr = f"Context7 HTTP {exc.code}: {exc.read().decode('utf-8', errors='replace')[:2000]}"
        exit_code = 1
    except Exception as exc:
        stderr = str(exc)
        exit_code = 1
    duration_ms = int((datetime.now(timezone.utc) - started).total_seconds() * 1000)
    return CommandResult(cmd, stdout, stderr, exit_code, duration_ms)


def context7_payload_to_text(payload: dict[str, Any]) -> str:
    parts: list[str] = []
    for snippet in payload.get("codeSnippets") or []:
        if not isinstance(snippet, dict):
            continue
        title = snippet.get("codeTitle") or snippet.get("pageTitle") or snippet.get("pageId")
        if title:
            parts.append(f"## {title}")
        description = snippet.get("codeDescription")
        if description:
            parts.append(str(description))
        for code in snippet.get("codeList") or []:
            if isinstance(code, dict) and code.get("code"):
                language = str(code.get("language") or "").strip()
                parts.append(f"```{language}\n{code.get('code')}\n```")
        source = snippet.get("source") or snippet.get("url") or snippet.get("pageId")
        if source:
            parts.append(f"Source: {source}")
    for snippet in payload.get("infoSnippets") or []:
        if not isinstance(snippet, dict):
            continue
        title = snippet.get("title") or snippet.get("pageTitle") or snippet.get("pageId")
        if title:
            parts.append(f"## {title}")
        content = snippet.get("content")
        if content:
            parts.append(str(content))
        source = snippet.get("source") or snippet.get("url") or snippet.get("pageId")
        if source:
            parts.append(f"Source: {source}")
    if isinstance(payload.get("rules"), dict):
        parts.append("## Rules")
        parts.append(json.dumps(payload["rules"], ensure_ascii=False, indent=2))
    return "\n\n".join(part.strip() for part in parts if str(part).strip())


def _load_local_mcp_config() -> tuple[str | None, str | None]:
    candidates = [
        ROOT / ".mcp.json",
        ROOT.parent / "Test-Next" / ".mcp.json",
    ]
    for path in candidates:
        if not path.exists():
            continue
        try:
            payload = json.loads(path.read_text(encoding="utf-8"))
        except Exception:
            continue
        servers = payload.get("mcpServers")
        if not isinstance(servers, dict):
            continue
        server = servers.get("oz")
        if not isinstance(server, dict):
            server = next((item for item in servers.values() if isinstance(item, dict)), None)
        if not isinstance(server, dict):
            continue
        url = str(server.get("url") or "").strip() or None
        headers = server.get("headers") if isinstance(server.get("headers"), dict) else {}
        api_key = str(headers.get("X-API-Key") or headers.get("x-api-key") or "").strip()
        auth = str(headers.get("Authorization") or headers.get("authorization") or "").strip()
        if not api_key and auth.lower().startswith("bearer "):
            api_key = auth.split(" ", 1)[1].strip()
        return url, api_key or None
    return None, None


def _load_eval_api_key_file() -> str:
    key_path = Path(os.environ.get("OZ_EVAL_API_KEY_FILE") or EVAL_API_KEY_PATH)
    try:
        return key_path.read_text(encoding="utf-8").strip()
    except FileNotFoundError:
        return ""


def _oz_mcp_settings() -> tuple[str, str, str, str, str]:
    config_url, config_key = _load_local_mcp_config()
    mcp_url = (
        os.getenv("OZ_MCP_URL")
        or os.getenv("MCP_URL")
        or config_url
        or "oz-cli"
    ).strip()
    if oz_eval_backend() == "api":
        api_key = (
            os.getenv("OZ_API_KEY")
            or os.getenv("MCP_API_KEY")
            or os.getenv("API_KEY")
            or _load_eval_api_key_file()
            or config_key
            or ""
        ).strip()
    else:
        api_key = ""
    library_name = (os.getenv("OZ_EVAL_LIBRARY_NAME") or OZ_LIBRARY_NAME_DEFAULT).strip()
    version_hint = (os.getenv("OZ_VERSION_HINT") or OZ_VERSION_HINT_DEFAULT).strip()
    context_id = (os.getenv("OZ_CONTEXT_ID") or OZ_CONTEXT_ID_FALLBACK).strip()
    return mcp_url, api_key, library_name, version_hint, context_id


def oz_eval_backend() -> str:
    return (os.getenv("OZ_EVAL_OZ_BACKEND") or os.getenv("OZ_BACKEND") or "local").strip().lower()


def oz_library_scopes(library_name: str) -> list[str]:
    raw = (
        os.getenv("OZ_EVAL_LIBRARY_SCOPES")
        or os.getenv("OZ_EVAL_LIBRARY_SCOPE")
        or os.getenv("OZ_LIBRARY_SCOPE")
        or ""
    ).strip()
    if raw:
        scopes = [item.strip().strip("/") for item in raw.split(",") if item.strip()]
        if scopes:
            return scopes
    normalized = library_name.strip().lower()
    if "smallest" in normalized:
        return ["smallest-ai/atoms", "smallest-ai/waves", "smallest-ai/python-sdk"]
    if "next" in normalized:
        return ["vercel/next.js"]
    return [library_name.strip().strip("/")]


def oz_query_scope() -> str:
    return (os.getenv("OZ_EVAL_QUERY_SCOPE") or "").strip().strip("/")


def oz_bin_path() -> Path:
    raw = (os.getenv("OZ_BIN") or "").strip()
    if raw:
        path = Path(raw).expanduser()
        if path.exists():
            return path.resolve()
    local = REPO_ROOT / "target" / "debug" / "oz"
    if not local.exists():
        run_subprocess(["cargo", "build", "-p", "oz"], timeout=180, cwd=REPO_ROOT, env=os.environ.copy())
    if local.exists():
        return local
    found = shutil.which("oz")
    if found:
        return Path(found)
    raise SystemExit("Oz binary not found. Run `cargo build -p oz` or set OZ_BIN.")


def oz_eval_env(api_key: str) -> dict[str, str]:
    env = os.environ.copy()
    env["OZ_DISABLE_KEYCHAIN"] = "1"
    env["PATH"] = f"{REPO_ROOT / 'target' / 'debug'}{os.pathsep}{env.get('PATH', '')}"
    home = OZ_EVAL_WORKSPACE / ".home"
    home.mkdir(parents=True, exist_ok=True)
    env["HOME"] = str(home)
    # Keep query text out of telemetry during benchmark runs.
    env.setdefault("OZ_TELEMETRY", "0")
    if api_key:
        env["OZ_API_KEY"] = api_key
    elif oz_eval_backend() != "api":
        for key in ("OZ_API_KEY", "MCP_API_KEY", "API_KEY"):
            env.pop(key, None)
    return env


_OZ_PREPARED_KEY: tuple[str, tuple[str, ...], str] | None = None


def prepare_oz_workspace(*, api_key: str, library_name: str) -> tuple[Path, dict[str, str], list[str]]:
    global _OZ_PREPARED_KEY
    oz_bin = oz_bin_path()
    scopes = oz_library_scopes(library_name)
    backend = oz_eval_backend()
    key = (str(oz_bin), tuple(scopes), backend)
    env = oz_eval_env(api_key)
    workspace = Path(os.getenv("OZ_EVAL_WORKSPACE") or OZ_EVAL_WORKSPACE)
    workspace.mkdir(parents=True, exist_ok=True)
    if _OZ_PREPARED_KEY == key and (workspace / ".codo").exists():
        return oz_bin, env, scopes

    run_subprocess([str(oz_bin), "init"], timeout=60, cwd=workspace, env=env)
    if backend == "api":
        api_url = (os.getenv("OZ_API_URL") or os.getenv("OZ_EVAL_API_URL") or "https://api.tryoz.dev").strip()
        run_subprocess([str(oz_bin), "config", "set", "api_url", api_url], timeout=60, cwd=workspace, env=env)
        if api_key:
            run_subprocess([str(oz_bin), "config", "set", "auth_token", api_key], timeout=60, cwd=workspace, env=env)
    else:
        # Force the local registry path even if the developer's real home has an API config.
        run_subprocess([str(oz_bin), "config", "unset", "api_url"], timeout=60, cwd=workspace, env=env)
        run_subprocess([str(oz_bin), "config", "unset", "auth_token"], timeout=60, cwd=workspace, env=env)

    if backend != "api":
        for scope in scopes:
            result = run_subprocess([str(oz_bin), "pull", scope], timeout=180, cwd=workspace, env=env)
            if result.exit_code != 0:
                raise RuntimeError(f"oz pull {scope} failed: {result.stderr.strip() or result.stdout.strip()}")
    _OZ_PREPARED_KEY = key
    return oz_bin, env, scopes


def call_mcp_tool(
    *,
    mcp_url: str,
    api_key: str,
    tool_name: str,
    arguments: dict[str, Any],
    request_id: str,
    timeout: int = 120,
) -> tuple[dict[str, Any], int]:
    started = time.perf_counter()
    payload = {
        "jsonrpc": "2.0",
        "id": request_id,
        "method": "tools/call",
        "params": {"name": tool_name, "arguments": arguments},
    }
    req = urllib.request.Request(
        mcp_url,
        data=json.dumps(payload).encode("utf-8"),
        headers={"Content-Type": "application/json", "X-API-Key": api_key},
        method="POST",
    )
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            body = json.loads(resp.read().decode("utf-8"))
    except urllib.error.HTTPError as exc:
        raw = exc.read().decode("utf-8", errors="replace")
        raise RuntimeError(f"MCP HTTP {exc.code}: {raw}") from exc
    duration_ms = int((time.perf_counter() - started) * 1000)
    if body.get("error"):
        raise RuntimeError(f"MCP JSON-RPC error: {body['error']}")
    result = body.get("result")
    if not isinstance(result, dict):
        raise RuntimeError(f"MCP response missing result: {body}")
    if result.get("isError"):
        raise RuntimeError(f"MCP tool error: {result.get('structuredContent') or result}")
    return result, duration_ms


def _mcp_content_text(result: dict[str, Any]) -> str:
    content = result.get("content")
    if not isinstance(content, list):
        return ""
    parts: list[str] = []
    for item in content:
        if isinstance(item, dict) and item.get("type") == "text":
            parts.append(str(item.get("text") or ""))
    return "\n".join(part for part in parts if part).strip()


def retrieve_with_oz(
    *,
    query: str,
    mcp_url: str,
    api_key: str,
    library_name: str,
    version_hint: str,
    fallback_context_id: str,
    index: int,
) -> CommandResult:
    stdout = ""
    stderr = ""
    total_ms = 0
    exit_code = 0
    command = ["oz", "context", query]
    try:
        oz_bin, env, _scopes = prepare_oz_workspace(api_key=api_key, library_name=library_name)
        max_tokens = (os.getenv("OZ_EVAL_MAX_TOKENS") or "2000").strip()
        max_results = (os.getenv("OZ_EVAL_MAX_RESULTS") or "8").strip()
        scope = oz_query_scope()
        command = [
            str(oz_bin),
            "context",
            query,
            *([scope] if scope else []),
            "--json",
            "--max-results",
            max_results,
            "--max-tokens",
            max_tokens,
        ]
        result = run_subprocess(command, timeout=120, cwd=Path(os.getenv("OZ_EVAL_WORKSPACE") or OZ_EVAL_WORKSPACE), env=env)
        total_ms = result.duration_ms
        exit_code = result.exit_code
        stderr = result.stderr
        stdout = oz_json_to_text(result.stdout) if result.stdout.strip().startswith("{") else result.stdout
    except Exception as exc:
        exit_code = 1
        stderr = str(exc)
    return CommandResult(
        command=command,
        stdout=stdout,
        stderr=stderr,
        exit_code=exit_code,
        duration_ms=total_ms,
    )


def oz_json_to_text(text: str) -> str:
    try:
        payload = json.loads(text)
    except Exception:
        return text
    if isinstance(payload, dict) and (
        isinstance(payload.get("codeSnippets"), list) or isinstance(payload.get("infoSnippets"), list)
    ):
        return context7_payload_to_text(payload)
    rows = payload.get("results") if isinstance(payload, dict) else None
    if not isinstance(rows, list):
        return text
    parts: list[str] = []
    for row in rows:
        if not isinstance(row, dict):
            continue
        path = str(row.get("path") or "").strip()
        line = row.get("line")
        content_type = str(row.get("content_type") or "").strip()
        header = path
        if line:
            header += f":{line}"
        if content_type:
            header += f" ({content_type})"
        if header:
            parts.append(f"## {header}")
        snippet = str(row.get("snippet") or "").strip()
        if snippet:
            parts.append(snippet)
    return "\n\n".join(parts).strip()


def estimate_tokens(text: str) -> int:
    return max(1, round(len(text) / 4))


def clean_output(text: str) -> str:
    lines = []
    for line in text.splitlines():
        if line.startswith("[RETRIEVE]"):
            continue
        lines.append(line.rstrip())
    return "\n".join(lines).strip()


def judge_query(client: OpenAI, model: str, query: str, ours: str, context7: str) -> dict[str, Any]:
    prompt = f"""
You are judging two retrieval outputs for a coding agent that needs compact, correct, high-signal context.

Query:
{query}

Output A (Oz CLI: oz pull -> oz context):
{ours}

Output B (context7):
{context7}

Score both outputs from 1 to 10 on these metrics:
- relevance
- actionability
- code_utility
- token_efficiency
- source_grounding
- overall

Guidance:
- Prefer answers that directly help a coding agent act.
- Reward concrete setup steps, code examples, and low-noise context.
- Penalize irrelevant snippets, misleading examples, verbosity, and weak grounding.
- `token_efficiency` means useful signal per token, not just shortness.

Return strict JSON with this shape:
{{
  "ours": {{"relevance": 0, "actionability": 0, "code_utility": 0, "token_efficiency": 0, "source_grounding": 0, "overall": 0}},
  "context7": {{"relevance": 0, "actionability": 0, "code_utility": 0, "token_efficiency": 0, "source_grounding": 0, "overall": 0}},
  "winner_by_metric": {{"relevance": "ours|context7|tie", "actionability": "...", "code_utility": "...", "token_efficiency": "...", "source_grounding": "...", "overall": "..."}},
  "overall_winner": "ours|context7|tie",
  "summary": "2-4 sentence comparison"
}}
""".strip()
    resp = client.responses.create(
        model=model,
        input=prompt,
        text={"format": {"type": "json_object"}},
    )
    out = getattr(resp, "output_text", "") or "{}"
    return json.loads(out)


def aggregate(rows: list[dict[str, Any]]) -> dict[str, Any]:
    totals = {
        "ours": {metric: 0.0 for metric in METRICS},
        "context7": {metric: 0.0 for metric in METRICS},
        "wins": {"ours": 0, "context7": 0, "tie": 0},
        "wins_by_metric": {metric: {"ours": 0, "context7": 0, "tie": 0} for metric in METRICS},
        "timing_ms": {"ours": 0, "context7": 0},
        "output_tokens_est": {"ours": 0, "context7": 0},
    }
    for row in rows:
        judge = row["judge"]
        for side in ("ours", "context7"):
            for metric in METRICS:
                totals[side][metric] += float(judge[side][metric])
            totals["timing_ms"][side] += int(row[side]["duration_ms"])
            totals["output_tokens_est"][side] += int(row[side]["tokens_est"])
        totals["wins"][judge["overall_winner"]] += 1
        for metric in METRICS:
            totals["wins_by_metric"][metric][judge["winner_by_metric"][metric]] += 1

    n = max(1, len(rows))
    averages = {
        "ours": {metric: round(totals["ours"][metric] / n, 2) for metric in METRICS},
        "context7": {metric: round(totals["context7"][metric] / n, 2) for metric in METRICS},
        "avg_timing_ms": {
            "ours": round(totals["timing_ms"]["ours"] / n, 1),
            "context7": round(totals["timing_ms"]["context7"] / n, 1),
        },
        "avg_output_tokens_est": {
            "ours": round(totals["output_tokens_est"]["ours"] / n, 1),
            "context7": round(totals["output_tokens_est"]["context7"] / n, 1),
        },
        "overall_wins": totals["wins"],
        "wins_by_metric": totals["wins_by_metric"],
    }
    return averages


def make_report(run_id: str, rows: list[dict[str, Any]], summary: dict[str, Any]) -> str:
    lines = [
        f"# Retrieval Comparison: Oz CLI ({LIBRARY_ID}) vs Context7",
        "",
        f"- Run ID: `{run_id}`",
        f"- Timestamp: `{datetime.now(timezone.utc).isoformat()}`",
        f"- Queries: `{len(rows)}`",
        "",
        "## Aggregate",
        "",
        f"- Overall wins: oz={summary['overall_wins']['ours']}, context7={summary['overall_wins']['context7']}, tie={summary['overall_wins']['tie']}",
        f"- Avg output tokens est: oz={summary['avg_output_tokens_est']['ours']}, context7={summary['avg_output_tokens_est']['context7']}",
        f"- Avg latency ms: oz={summary['avg_timing_ms']['ours']}, context7={summary['avg_timing_ms']['context7']}",
        "",
        "| Metric | Oz | Context7 | Winner Count (oz/context7/tie) |",
        "| --- | ---: | ---: | --- |",
    ]
    for metric in METRICS:
        wins = summary["wins_by_metric"][metric]
        lines.append(
            f"| {metric} | {summary['ours'][metric]} | {summary['context7'][metric]} | {wins['ours']}/{wins['context7']}/{wins['tie']} |"
        )

    lines.extend(["", "## Per Query", ""])
    for idx, row in enumerate(rows, 1):
        judge = row["judge"]
        lines.extend(
            [
                f"### {idx}. {row['query']}",
                f"- Overall winner: `{judge['overall_winner']}`",
                f"- Oz: latency={row['ours']['duration_ms']}ms, tokens≈{row['ours']['tokens_est']}",
                f"- Context7: latency={row['context7']['duration_ms']}ms, tokens≈{row['context7']['tokens_est']}",
                f"- Judge summary: {judge['summary']}",
                "",
            ]
        )
    return "\n".join(lines).strip() + "\n"


def main() -> None:
    global LIBRARY_ID, CTX7_ID
    load_env(ENV_PATH)
    load_env(EVAL_ENV_PATH, override=True)
    LIBRARY_ID = os.getenv("OZ_EVAL_LIBRARY_ID", LIBRARY_ID)
    CTX7_ID = os.getenv("CTX7_LIBRARY_ID", CTX7_ID)
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        raise SystemExit("OPENAI_API_KEY missing after loading .env")
    model = os.getenv("MODEL_BENCHMARK_JUDGE", "gpt-5.5")
    client = OpenAI(api_key=api_key)
    mcp_url, oz_api_key, library_name, version_hint, fallback_context_id = _oz_mcp_settings()
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    run_id = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    json_path = OUT_DIR / f"{run_id}_oz_next_js_vs_context7.json"
    md_path = OUT_DIR / f"{run_id}_oz_next_js_vs_context7.md"
    limit_raw = str(os.getenv("EVAL_QUERY_LIMIT") or "").strip()
    queries = QUERIES
    if limit_raw:
        try:
            queries = QUERIES[: max(1, int(limit_raw))]
        except ValueError:
            queries = QUERIES

    rows: list[dict[str, Any]] = []
    for idx, query in enumerate(queries, 1):
        ctx7_cmd = ["ctx7", "docs", CTX7_ID, query]
        ours_res = retrieve_with_oz(
            query=query,
            mcp_url=mcp_url,
            api_key=oz_api_key,
            library_name=library_name,
            version_hint=version_hint,
            fallback_context_id=fallback_context_id,
            index=idx,
        )
        ctx7_res = run_command(ctx7_cmd)
        ours_text = clean_output(ours_res.stdout)
        ctx7_text = clean_output(ctx7_res.stdout)
        if not ctx7_text and ctx7_res.stderr:
            ctx7_text = f"Context7 command failed: {ctx7_res.stderr}"
        if not ours_text and ours_res.stderr:
            ours_text = f"Oz CLI command failed: {ours_res.stderr}"
        judge = judge_query(client, model, query, ours_text, ctx7_text)
        rows.append(
            {
                "index": idx,
                "query": query,
                "ours": {
                    "command": ours_res.command,
                    "duration_ms": ours_res.duration_ms,
                    "exit_code": ours_res.exit_code,
                    "stdout": ours_text,
                    "stderr": ours_res.stderr,
                    "tokens_est": estimate_tokens(ours_text),
                },
                "context7": {
                    "command": ctx7_cmd,
                    "duration_ms": ctx7_res.duration_ms,
                    "exit_code": ctx7_res.exit_code,
                    "stdout": ctx7_text,
                    "stderr": ctx7_res.stderr,
                    "tokens_est": estimate_tokens(ctx7_text),
                },
                "judge": judge,
            }
        )

    summary = aggregate(rows)
    payload = {
        "libraryId": LIBRARY_ID,
        "context7Id": CTX7_ID,
        "oz": {
            "mcpUrl": mcp_url,
            "libraryName": library_name,
            "versionHint": version_hint,
            "fallbackContextId": fallback_context_id,
            "tools": ["oz pull", "oz context"],
        },
        "runId": run_id,
        "queries": queries,
        "metrics": METRICS,
        "model": model,
        "summary": summary,
        "rows": rows,
    }
    json_path.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    md_path.write_text(make_report(run_id, rows, summary), encoding="utf-8")
    print(json.dumps({"json": str(json_path), "report": str(md_path), "summary": summary}, indent=2))


if __name__ == "__main__":
    main()
