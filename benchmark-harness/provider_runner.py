#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import os
import re
import subprocess
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path
from typing import Any

from harness import estimate_tokens, flatten_cases, load_cases, path_matches_any, write_json


HARNESS = Path(__file__).resolve().parent
PROVIDERS = HARNESS / "providers"


def main() -> int:
    parser = argparse.ArgumentParser(description="Run external context providers against Oz benchmark cases.")
    parser.add_argument("--cases", default=str(HARNESS / "cases.json"))
    parser.add_argument("--provider", required=True, help="Provider config path or name under benchmark-harness/providers.")
    parser.add_argument("--library", default="", help="Filter to one library, for example vercel/next.js.")
    parser.add_argument("--case", dest="case_id", default="", help="Run one case id.")
    parser.add_argument("--limit", type=int, default=0)
    parser.add_argument("--out", required=True)
    parser.add_argument("--delay", type=float, default=0.35)
    parser.add_argument("--timeout", type=int, default=60)
    parser.add_argument("--max-tokens", type=int, default=2000)
    args = parser.parse_args()

    config = load_provider_config(args.provider)
    spec = load_cases(Path(args.cases))
    cases = flatten_cases(spec)
    if args.library:
        cases = [case for case in cases if case["library"] == args.library]
    if args.case_id:
        cases = [case for case in cases if case["id"] == args.case_id]
    if args.limit:
        cases = cases[: args.limit]
    if not cases:
        raise SystemExit("no cases selected")

    out_dir = Path(args.out)
    out_dir.mkdir(parents=True, exist_ok=True)
    raw_results: list[dict[str, Any]] = []
    scored_results: list[dict[str, Any]] = []

    for index, case in enumerate(cases, start=1):
        print(f"[{index}/{len(cases)}] {config['name']} {case['id']} {case['library']}", file=sys.stderr, flush=True)
        started = time.monotonic()
        raw = run_provider_case(config, case, timeout=args.timeout, max_tokens=args.max_tokens)
        raw["latency_ms"] = int((time.monotonic() - started) * 1000)
        raw["provider"] = config["name"]
        raw["case_id"] = case["id"]
        raw["library"] = case["library"]
        raw["query"] = case["query"]
        score = score_provider_case(config, case, raw)
        raw_results.append(raw)
        scored_results.append(score)
        write_json(out_dir / f"{config['name']}_raw_results.json", raw_results)
        write_json(out_dir / f"{config['name']}_case_scores.json", scored_results)
        if args.delay > 0 and index < len(cases):
            time.sleep(args.delay)

    summary = summarize_provider(config["name"], scored_results)
    summary["provider_config"] = str(config.get("_path", ""))
    summary["case_count"] = len(scored_results)
    summary["results"] = scored_results
    write_json(out_dir / f"{config['name']}_summary.json", summary)
    print(json.dumps(summary, indent=2, sort_keys=True))
    return 0 if summary[config["name"]]["ok_rate"] > 0 else 1


def load_provider_config(value: str) -> dict[str, Any]:
    path = Path(value)
    if not path.exists():
        candidate = PROVIDERS / value
        if candidate.suffix != ".json":
            candidate = candidate.with_suffix(".json")
        path = candidate
    if not path.exists():
        raise SystemExit(f"provider config not found: {value}")
    config = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(config.get("name"), str) or not config["name"]:
        raise SystemExit(f"{path}: missing provider name")
    if config.get("kind") not in {"context7_api", "command"}:
        raise SystemExit(f"{path}: unsupported provider kind {config.get('kind')!r}")
    config["_path"] = str(path)
    return config


def run_provider_case(config: dict[str, Any], case: dict[str, Any], *, timeout: int, max_tokens: int) -> dict[str, Any]:
    kind = config["kind"]
    if kind == "context7_api":
        return run_context7_api(config, case, timeout=timeout)
    if kind == "command":
        return run_command_provider(config, case, timeout=timeout, max_tokens=max_tokens)
    raise AssertionError(kind)


def run_context7_api(config: dict[str, Any], case: dict[str, Any], *, timeout: int) -> dict[str, Any]:
    api_key_env = str(config.get("api_key_env") or "CONTEXT7_API_KEY")
    api_key = os.environ.get(api_key_env, "").strip()
    if not api_key:
        raise SystemExit(f"{api_key_env} is required for provider {config['name']}")
    library_id = str(config.get("library_id_template") or "/{library}").format(**case)
    params = urllib.parse.urlencode(
        {
            "libraryId": library_id,
            "query": str(case["query"]),
            "type": str(config.get("response_type") or "json"),
            "fast": bool_string(config.get("fast", "false")),
        }
    )
    request = urllib.request.Request(
        f"{config.get('url', 'https://context7.com/api/v2/context')}?{params}",
        headers={
            "Authorization": f"Bearer {api_key}",
            "Accept": "application/json",
            "User-Agent": "oz-benchmark-harness/2.0",
        },
        method="GET",
    )
    status, content_type, headers, body = fetch_url(request, timeout=timeout)
    data = parse_json(body)
    return {
        "ok": status == 200,
        "status": status,
        "content_type": content_type,
        "headers": rate_limit_headers(headers),
        "data": data if isinstance(data, dict) else {"raw": body[:30000]},
    }


def run_command_provider(config: dict[str, Any], case: dict[str, Any], *, timeout: int, max_tokens: int) -> dict[str, Any]:
    values = {**case, "max_tokens": max_tokens}
    command = [expand_template(str(part), values) for part in config.get("command", [])]
    if not command:
        raise SystemExit(f"{config['name']}: command provider requires command")
    env = os.environ.copy()
    for key, value in dict(config.get("env") or {}).items():
        env[str(key)] = expand_template(str(value), values)
    proc = subprocess.run(
        command,
        cwd=str(Path(config.get("cwd") or os.getcwd()).expanduser()),
        env=env,
        stdin=subprocess.DEVNULL,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        timeout=timeout,
        check=False,
    )
    data = parse_json(proc.stdout)
    return {
        "ok": proc.returncode == 0,
        "status": 200 if proc.returncode == 0 else 0,
        "returncode": proc.returncode,
        "stdout": proc.stdout[:50000],
        "stderr": proc.stderr[:10000],
        "data": data if isinstance(data, dict) else {"raw": proc.stdout[:50000]},
    }


def fetch_url(request: urllib.request.Request, *, timeout: int, retries: int = 3) -> tuple[int, str, dict[str, str], str]:
    for attempt in range(retries):
        try:
            with urllib.request.urlopen(request, timeout=timeout) as response:
                return (
                    int(response.status),
                    response.headers.get("Content-Type", ""),
                    dict(response.headers.items()),
                    response.read().decode("utf-8", "replace"),
                )
        except urllib.error.HTTPError as exc:
            body = exc.read().decode("utf-8", "replace")
            if exc.code == 429 and attempt + 1 < retries:
                retry_after = float(exc.headers.get("Retry-After") or 2**attempt)
                time.sleep(max(1.0, retry_after))
                continue
            return int(exc.code), exc.headers.get("Content-Type", ""), dict(exc.headers.items()), body
        except urllib.error.URLError as exc:
            if attempt + 1 >= retries:
                return 0, "", {}, str(exc)
            time.sleep(2**attempt)
    return 0, "", {}, ""


def score_provider_case(config: dict[str, Any], case: dict[str, Any], raw: dict[str, Any]) -> dict[str, Any]:
    normalized = normalize_provider_output(config, raw)
    text = normalized["text"]
    sources = normalized["sources"]
    expected = [str(item) for item in case.get("expected_paths", [])]
    required_terms = [str(item) for item in case.get("required_terms", [])]
    banned_terms = [str(item).lower() for item in case.get("banned_terms", [])]
    lower_text = text.lower()
    required_found = [term for term in required_terms if term.lower() in lower_text]
    banned_found = [term for term in banned_terms if term in lower_text]
    expected_hits = [item for item in expected if source_matches_expected(item, sources, text)]
    return {
        "provider": config["name"],
        "case_id": case["id"],
        "library": case["library"],
        "query": case["query"],
        "ok": bool(raw.get("ok")),
        "status": raw.get("status"),
        "latency_ms": raw.get("latency_ms", 0),
        "output_tokens_est": estimate_tokens(text),
        "raw_tokens_est": estimate_tokens(json.dumps(raw.get("data", {}), ensure_ascii=False)),
        "required_terms": required_terms,
        "required_terms_found": required_found,
        "required_terms_found_rate": len(required_found) / max(1, len(required_terms)),
        "banned_terms_found": banned_found,
        "expected_source_hits": expected_hits,
        "expected_source_signal": bool(expected_hits),
        "source_count": len(sources),
        "snippet_count": normalized["snippet_count"],
    }


def normalize_provider_output(config: dict[str, Any], raw: dict[str, Any]) -> dict[str, Any]:
    if config["kind"] == "context7_api":
        data = raw.get("data") if isinstance(raw.get("data"), dict) else {}
        return normalize_context7(data)
    data = raw.get("data") if isinstance(raw.get("data"), dict) else {}
    text = ""
    sources: list[str] = []
    if isinstance(data.get("results"), list):
        parts: list[str] = []
        for row in data["results"]:
            if not isinstance(row, dict):
                continue
            for key in ("path", "source", "url", "title"):
                if row.get(key):
                    sources.append(str(row[key]))
                    parts.append(str(row[key]))
            for key in ("content", "text", "snippet", "preview"):
                if row.get(key):
                    parts.append(str(row[key]))
        text = "\n".join(parts)
    else:
        text = str(data.get("raw") or raw.get("stdout") or "")
    sources.extend(re.findall(r"\.codo/vendors/[^\s:)]+", text))
    return {"text": text, "sources": sorted(set(sources)), "snippet_count": len(sources)}


def normalize_context7(data: dict[str, Any]) -> dict[str, Any]:
    parts: list[str] = []
    sources: list[str] = []
    snippet_count = 0
    for snippet in data.get("codeSnippets") or []:
        if not isinstance(snippet, dict):
            continue
        snippet_count += 1
        for key in ("codeTitle", "codeDescription", "codeLanguage", "codeId", "pageTitle", "pageId"):
            value = snippet.get(key)
            if value:
                parts.append(str(value))
        for key in ("codeId", "pageId", "source", "url"):
            value = snippet.get(key)
            if value:
                sources.append(str(value))
        for code in snippet.get("codeList") or []:
            if isinstance(code, dict):
                parts.append(str(code.get("language") or ""))
                parts.append(str(code.get("code") or ""))
    for snippet in data.get("infoSnippets") or []:
        if not isinstance(snippet, dict):
            continue
        snippet_count += 1
        for key in ("title", "pageTitle", "pageId", "breadcrumb", "content"):
            value = snippet.get(key)
            if value:
                parts.append(str(value))
        for key in ("pageId", "source", "url"):
            value = snippet.get(key)
            if value:
                sources.append(str(value))
    if isinstance(data.get("rules"), dict):
        parts.append(json.dumps(data["rules"], ensure_ascii=False))
    return {"text": "\n".join(parts), "sources": sorted(set(sources)), "snippet_count": snippet_count}


def summarize_provider(name: str, results: list[dict[str, Any]]) -> dict[str, Any]:
    return {
        name: {
            "ok_count": sum(1 for row in results if row.get("ok")),
            "ok_rate": avg(results, "ok"),
            "expected_source_signal_rate": avg(results, "expected_source_signal"),
            "required_terms_found_rate": avg(results, "required_terms_found_rate"),
            "avg_context_tokens_est": avg(results, "output_tokens_est"),
            "avg_raw_tokens_est": avg(results, "raw_tokens_est"),
            "avg_latency_ms": avg(results, "latency_ms"),
            "avg_snippet_count": avg(results, "snippet_count"),
        }
    }


def source_matches_expected(expected: str, sources: list[str], text: str) -> bool:
    if path_matches_any("\n".join(sources), [expected]):
        return True
    expected_slug = slug(expected)
    source_blob = "\n".join(slug(source) for source in sources)
    if expected_slug and expected_slug in source_blob:
        return True
    basename = slug(Path(expected).stem)
    if len(basename) >= 5 and basename in source_blob:
        return True
    important = [part for part in slug(expected).split("-") if len(part) >= 4]
    if important and sum(1 for part in important if part in source_blob) >= min(2, len(important)):
        return True
    if basename and len(basename) >= 5 and basename in slug(text):
        return True
    return False


def slug(value: str) -> str:
    value = value.lower().replace("_", "-")
    value = value.replace(".md", "").replace(".mdx", "")
    value = re.sub(r"\b0[1-9]-", "", value)
    return "".join(ch if ch.isalnum() else "-" for ch in value).strip("-")


def rate_limit_headers(headers: dict[str, str]) -> dict[str, str]:
    return {key: value for key, value in headers.items() if key.lower().startswith(("x-ratelimit", "ratelimit", "retry-after"))}


def parse_json(text: str) -> Any:
    try:
        return json.loads(text)
    except Exception:
        return None


def expand_template(value: str, values: dict[str, Any]) -> str:
    expanded = value
    for key, replacement in values.items():
        expanded = expanded.replace("{" + key + "}", str(replacement))
    return os.path.expandvars(expanded)


def avg(rows: list[dict[str, Any]], key: str) -> float:
    values: list[float] = []
    for row in rows:
        value = row.get(key)
        if isinstance(value, bool):
            values.append(1.0 if value else 0.0)
        elif isinstance(value, (int, float)):
            values.append(float(value))
    return round(sum(values) / len(values), 4) if values else 0.0


def bool_string(value: Any) -> str:
    if isinstance(value, bool):
        return "true" if value else "false"
    text = str(value).strip().lower()
    return "true" if text in {"1", "true", "yes"} else "false"


if __name__ == "__main__":
    raise SystemExit(main())
