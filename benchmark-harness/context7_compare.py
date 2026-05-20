#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import os
import time
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path
from typing import Any

from harness import estimate_tokens, flatten_cases, load_cases, path_matches_any, write_json


API_URL = "https://context7.com/api/v2/context"


def main() -> int:
    parser = argparse.ArgumentParser(description="Compare Oz benchmark cases against Context7 context API.")
    parser.add_argument("--cases", default=str(Path(__file__).resolve().parent / "cases.json"))
    parser.add_argument("--library", default="", help="Filter to one library, for example vercel/next.js.")
    parser.add_argument("--context7-library-id", default="", help="Override Context7 library id. Defaults to /<library>.")
    parser.add_argument("--oz-summary", default="", help="Optional Oz harness summary.json to include in output.")
    parser.add_argument("--out", required=True)
    parser.add_argument("--delay", type=float, default=0.35, help="Delay between API calls.")
    parser.add_argument("--timeout", type=int, default=60)
    parser.add_argument("--fast", choices=["true", "false"], default="false")
    args = parser.parse_args()

    api_key = os.environ.get("CONTEXT7_API_KEY", "").strip()
    if not api_key:
        raise SystemExit("CONTEXT7_API_KEY is required")

    spec = load_cases(Path(args.cases))
    cases = flatten_cases(spec)
    if args.library:
        cases = [case for case in cases if case["library"] == args.library]
    if not cases:
        raise SystemExit("no cases selected")

    out_dir = Path(args.out)
    out_dir.mkdir(parents=True, exist_ok=True)
    raw_results: list[dict[str, Any]] = []
    scored_results: list[dict[str, Any]] = []

    for index, case in enumerate(cases, start=1):
        print(f"[{index}/{len(cases)}] {case['id']} {case['library']}", flush=True)
        library_id = args.context7_library_id or f"/{case['library']}"
        started = time.monotonic()
        status, content_type, headers, payload_text = fetch_context7(
            api_key,
            library_id,
            str(case["query"]),
            fast=args.fast,
            timeout=args.timeout,
        )
        latency_ms = int((time.monotonic() - started) * 1000)
        data = parse_json(payload_text)
        raw = {
            "case_id": case["id"],
            "library": case["library"],
            "query": case["query"],
            "status": status,
            "content_type": content_type,
            "latency_ms": latency_ms,
            "rate_limit": rate_limit_headers(headers),
            "data": data if isinstance(data, dict) else {"raw": payload_text[:20000]},
        }
        score = score_context7_case(case, raw)
        raw_results.append(raw)
        scored_results.append(score)
        write_json(out_dir / "context7_raw_results.json", raw_results)
        write_json(out_dir / "context7_case_scores.json", scored_results)
        if args.delay > 0 and index < len(cases):
            time.sleep(args.delay)

    summary = summarize(scored_results)
    if args.oz_summary:
        oz_path = Path(args.oz_summary)
        if oz_path.exists():
            summary["oz"] = json.loads(oz_path.read_text(encoding="utf-8")).get("retrieval", {})
            summary["oz_summary"] = str(oz_path)
    summary["library"] = args.library or "all"
    summary["context7_library_id"] = args.context7_library_id or f"/{args.library}" if args.library else ""
    summary["case_count"] = len(scored_results)
    summary["results"] = scored_results
    write_json(out_dir / "context7_comparison_summary.json", summary)
    print(json.dumps(summary, indent=2, sort_keys=True))
    return 0 if summary["context7"]["ok_rate"] > 0 else 1


def fetch_context7(
    api_key: str,
    library_id: str,
    query: str,
    *,
    fast: str,
    timeout: int,
    retries: int = 3,
) -> tuple[int, str, dict[str, str], str]:
    params = urllib.parse.urlencode(
        {
            "libraryId": library_id,
            "query": query,
            "type": "json",
            "fast": fast,
        }
    )
    request = urllib.request.Request(
        f"{API_URL}?{params}",
        headers={
            "Authorization": f"Bearer {api_key}",
            "Accept": "application/json",
            "User-Agent": "oz-benchmark-harness/1.0",
        },
        method="GET",
    )
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


def score_context7_case(case: dict[str, Any], raw: dict[str, Any]) -> dict[str, Any]:
    data = raw.get("data") if isinstance(raw.get("data"), dict) else {}
    text = context7_text(data)
    sources = context7_sources(data)
    expected = [str(item) for item in case.get("expected_paths", [])]
    required_terms = [str(item) for item in case.get("required_terms", [])]
    banned_terms = [str(item).lower() for item in case.get("banned_terms", [])]
    required_found = [term for term in required_terms if term.lower() in text.lower()]
    banned_found = [term for term in banned_terms if term in text.lower()]
    expected_hits = [item for item in expected if source_matches_expected(item, sources, text)]
    code_snippets = data.get("codeSnippets") if isinstance(data.get("codeSnippets"), list) else []
    info_snippets = data.get("infoSnippets") if isinstance(data.get("infoSnippets"), list) else []
    return {
        "case_id": case["id"],
        "library": case["library"],
        "query": case["query"],
        "status": raw["status"],
        "latency_ms": raw["latency_ms"],
        "content_type": raw["content_type"],
        "output_tokens_est": estimate_tokens(json.dumps(data, ensure_ascii=False)),
        "code_snippets": len(code_snippets),
        "info_snippets": len(info_snippets),
        "required_terms": required_terms,
        "required_terms_found": required_found,
        "required_terms_found_rate": len(required_found) / max(1, len(required_terms)),
        "banned_terms_found": banned_found,
        "expected_source_hits": expected_hits,
        "expected_source_signal": bool(expected_hits),
        "source_count": len(sources),
    }


def summarize(results: list[dict[str, Any]]) -> dict[str, Any]:
    ok = [row for row in results if int(row.get("status") or 0) == 200]
    statuses: dict[str, int] = {}
    for row in results:
        key = str(row.get("status"))
        statuses[key] = statuses.get(key, 0) + 1
    return {
        "context7": {
            "ok_count": len(ok),
            "ok_rate": round(len(ok) / max(1, len(results)), 4),
            "statuses": statuses,
            "expected_source_signal_rate": avg(results, "expected_source_signal"),
            "required_terms_found_rate": avg(results, "required_terms_found_rate"),
            "avg_context_tokens_est": avg(results, "output_tokens_est"),
            "avg_latency_ms": avg(results, "latency_ms"),
            "avg_code_snippets": avg(results, "code_snippets"),
            "avg_info_snippets": avg(results, "info_snippets"),
        }
    }


def context7_text(data: dict[str, Any]) -> str:
    parts: list[str] = []
    for snippet in data.get("codeSnippets") or []:
        if not isinstance(snippet, dict):
            continue
        for key in ("codeTitle", "codeDescription", "codeLanguage", "codeId", "pageTitle"):
            value = snippet.get(key)
            if value:
                parts.append(str(value))
        for code in snippet.get("codeList") or []:
            if isinstance(code, dict):
                parts.append(str(code.get("language") or ""))
                parts.append(str(code.get("code") or ""))
    for snippet in data.get("infoSnippets") or []:
        if not isinstance(snippet, dict):
            continue
        for key in ("title", "pageTitle", "pageId", "breadcrumb", "content"):
            value = snippet.get(key)
            if value:
                parts.append(str(value))
    if isinstance(data.get("rules"), dict):
        parts.append(json.dumps(data["rules"], ensure_ascii=False))
    return "\n".join(parts)


def context7_sources(data: dict[str, Any]) -> list[str]:
    out: list[str] = []
    for snippet in data.get("codeSnippets") or []:
        if isinstance(snippet, dict):
            for key in ("codeId", "pageId", "source", "url"):
                if snippet.get(key):
                    out.append(str(snippet[key]))
    for snippet in data.get("infoSnippets") or []:
        if isinstance(snippet, dict):
            for key in ("pageId", "source", "url"):
                if snippet.get(key):
                    out.append(str(snippet[key]))
    return out


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
    value = value.replace("01-", "").replace("02-", "").replace("03-", "").replace("04-", "")
    return "".join(ch if ch.isalnum() else "-" for ch in value).strip("-")


def parse_json(text: str) -> Any:
    try:
        return json.loads(text)
    except Exception:
        return {"raw": text}


def rate_limit_headers(headers: dict[str, str]) -> dict[str, str]:
    wanted = {}
    for key, value in headers.items():
        low = key.lower()
        if low in {"ratelimit-limit", "ratelimit-remaining", "ratelimit-reset", "retry-after"}:
            wanted[key] = value
    return wanted


def avg(rows: list[dict[str, Any]], key: str) -> float:
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


if __name__ == "__main__":
    raise SystemExit(main())
