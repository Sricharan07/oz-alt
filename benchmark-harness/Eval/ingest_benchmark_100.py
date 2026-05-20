#!/usr/bin/env python3
from __future__ import annotations

import argparse
import csv
import json
import os
import re
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
from collections import defaultdict
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
CSV_PATH = (
    ROOT
    / "Benchmark-Docs-5000"
    / "frequently_used_5000_libraries_baememory_crawler_urls"
    / "Crawler URLs-Table 1.csv"
)
OUT_DIR = ROOT / ".ingestion_work" / "benchmark_ingest"

CANONICAL_ID_RE = re.compile(r"^/[a-z0-9][a-z0-9._-]*/[a-z0-9][a-z0-9._-]*$")
GITHUB_REPO_RE = re.compile(r"^https://github\.com/([^/#?]+)/([^/#?]+)")
CANONICAL_OVERRIDES = {
    "/vercel/next.js": "/vercel/next",
}
VERCEL_IDS = {
    "/vercel/next.js",
    "/vercel/ai",
    "/websites/vercel",
    "@vercel/webpack-asset-relocator-loader",
    "@vercel/nft",
}
SOURCE_PRIORITY = [
    "official_docs",
    "documentation",
    "docs",
    "getting_started",
    "quickstart",
    "installation",
    "api_reference",
    "reference",
    "docs_section",
    "guide",
    "guides",
    "tutorial",
    "tutorials",
    "homepage",
    "package",
    "github_repo",
    "github_readme",
]


@dataclass(frozen=True)
class SelectedLibrary:
    rank: int
    source_library_id: str
    canonical_library_id: str
    name: str
    source_type: str
    url: str
    fetch_ok: str
    http_status: str
    source_config: dict[str, Any]


def _utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _http_json(
    method: str,
    url: str,
    *,
    token: str | None = None,
    payload: dict[str, Any] | None = None,
    timeout: int = 120,
) -> Any:
    headers = {"Accept": "application/json"}
    data = None
    if payload is not None:
        data = json.dumps(payload).encode("utf-8")
        headers["Content-Type"] = "application/json"
    if token:
        headers["Authorization"] = f"Bearer {token}"
    request = urllib.request.Request(url, data=data, headers=headers, method=method)
    try:
        with urllib.request.urlopen(request, timeout=timeout) as response:
            body = response.read().decode("utf-8")
    except urllib.error.HTTPError as exc:
        body = exc.read().decode("utf-8", errors="replace")
        raise RuntimeError(f"{method} {url} failed: HTTP {exc.code}: {body}") from exc
    if not body:
        return None
    return json.loads(body)


def _operator_token(base_url: str, email: str, password: str) -> str:
    payload = {"email": email, "password": password}
    try:
        response = _http_json("POST", f"{base_url}/api/internal/operator/auth/login", payload=payload)
    except RuntimeError as exc:
        if "HTTP 401" not in str(exc):
            raise
        register_payload = dict(payload)
        register_payload["full_name"] = "Codex Benchmark Ingest"
        response = _http_json("POST", f"{base_url}/api/internal/operator/auth/register", payload=register_payload)
    token = str((response or {}).get("access_token") or "").strip()
    if not token:
        raise RuntimeError("Operator auth did not return an access token")
    return token


def _read_rows() -> list[dict[str, str]]:
    with CSV_PATH.open(newline="", encoding="utf-8-sig") as handle:
        return list(csv.DictReader(handle))


def _github_canonical(repo_url: str) -> str | None:
    match = GITHUB_REPO_RE.match(str(repo_url or "").strip())
    if not match:
        return None
    owner = match.group(1).strip().lower()
    repo = match.group(2).strip().lower()
    repo = repo[:-4] if repo.endswith(".git") else repo
    candidate = f"/{owner}/{repo}"
    return candidate if CANONICAL_ID_RE.match(candidate) else None


def _canonical_library_id(row: dict[str, str]) -> str | None:
    raw = str(row.get("Package / Library ID") or "").strip().lower()
    if raw in CANONICAL_OVERRIDES:
        return CANONICAL_OVERRIDES[raw]
    if CANONICAL_ID_RE.match(raw):
        return raw
    return _github_canonical(str(row.get("Official GitHub Repo URL") or ""))


def _is_vercel_library(library_id: str, name: str) -> bool:
    raw = str(library_id or "").strip()
    return raw in VERCEL_IDS or raw.startswith("/vercel/") or raw.startswith("@vercel/") or "vercel" in name.lower()


def _source_score(row: dict[str, str], *, allow_unvalidated: bool) -> tuple[int, int, str]:
    source_type = str(row.get("Source Type") or "").strip()
    fetch_ok = str(row.get("Fetch OK") or "").strip()
    priority = SOURCE_PRIORITY.index(source_type) if source_type in SOURCE_PRIORITY else 999
    validated = 0 if fetch_ok == "YES" else 1000
    if allow_unvalidated and source_type in {"github_repo", "github_readme", "package"}:
        validated = 500
    return (validated + priority, int(str(row.get("Priority") or "999") or 999), source_type)


def _select_source(rows: list[dict[str, str]], *, allow_unvalidated: bool, max_pages: int, max_files: int) -> tuple[str, str, str, dict[str, Any]] | None:
    candidates = []
    for row in rows:
        url = str(row.get("URL") or "").strip()
        source_type = str(row.get("Source Type") or "").strip()
        if not url or source_type in {"github_issues", "github_releases", "context7"}:
            continue
        if str(row.get("Fetch OK") or "").strip() != "YES" and not allow_unvalidated:
            continue
        candidates.append((_source_score(row, allow_unvalidated=allow_unvalidated), row))
    if not candidates:
        return None
    _, row = sorted(candidates, key=lambda item: item[0])[0]
    source_type = str(row.get("Source Type") or "").strip()
    url = str(row.get("URL") or "").strip()
    if source_type in {"github_repo", "github_readme"}:
        repo_url = str(row.get("Official GitHub Repo URL") or "").strip() or url.split("#", 1)[0]
        return (
            "git_public",
            url,
            str(row.get("Fetch OK") or "").strip(),
            {"repo_url": repo_url, "max_files": max_files, "include_globs": ["README*", "docs/**", "*.md", "*.mdx"]},
        )
    page_cap = min(max_pages, 3) if source_type == "package" or "npmjs.com/package/" in url else max_pages
    return ("url", url, str(row.get("Fetch OK") or "").strip(), {"start_url": url, "max_pages": page_cap})


def select_libraries(limit: int, max_pages: int, max_files: int) -> list[SelectedLibrary]:
    rows = _read_rows()
    grouped: dict[str, list[dict[str, str]]] = defaultdict(list)
    first: dict[str, dict[str, str]] = {}
    for row in rows:
        library_id = str(row.get("Package / Library ID") or "").strip()
        if not library_id:
            continue
        grouped[library_id].append(row)
        first.setdefault(library_id, row)

    vercel_ids = [
        library_id
        for library_id, row in first.items()
        if _is_vercel_library(library_id, str(row.get("Library") or ""))
    ]
    vercel_ids = sorted(vercel_ids, key=lambda item: int(str(first[item].get("Global Rank") or "999999") or 999999))
    remaining = max(0, limit - len(vercel_ids))

    selected_ids: list[str] = []
    for library_id, row in sorted(first.items(), key=lambda item: int(str(item[1].get("Global Rank") or "999999") or 999999)):
        if library_id in vercel_ids:
            continue
        canonical = _canonical_library_id(row)
        if not canonical:
            continue
        if not _select_source(grouped[library_id], allow_unvalidated=False, max_pages=max_pages, max_files=max_files):
            continue
        selected_ids.append(library_id)
        if len(selected_ids) >= remaining:
            break
    selected_ids.extend(vercel_ids)

    selected: list[SelectedLibrary] = []
    for library_id in selected_ids:
        row = first[library_id]
        canonical = _canonical_library_id(row)
        if not canonical:
            raise RuntimeError(f"Could not canonicalize {library_id}")
        source = _select_source(
            grouped[library_id],
            allow_unvalidated=library_id in vercel_ids,
            max_pages=max_pages,
            max_files=max_files,
        )
        if source is None:
            raise RuntimeError(f"Could not select source for {library_id}")
        source_type, url, fetch_ok, source_config = source
        selected.append(
            SelectedLibrary(
                rank=int(str(row.get("Global Rank") or "999999") or 999999),
                source_library_id=library_id,
                canonical_library_id=canonical,
                name=str(row.get("Library") or canonical).strip() or canonical,
                source_type=source_type,
                url=url,
                fetch_ok=fetch_ok,
                http_status=str(row.get("HTTP Status") or "").strip(),
                source_config=source_config,
            )
        )
    return selected[:limit]


def create_and_sync(base_url: str, token: str, item: SelectedLibrary, *, trigger_sync: bool) -> dict[str, Any]:
    payload = {
        "name": item.name,
        "library_id": item.canonical_library_id,
        "source_type": item.source_type,
        "source_config": item.source_config,
        "version_mode": "auto",
    }
    created = _http_json("POST", f"{base_url}/api/internal/operator/sources", token=token, payload=payload)
    result = {"selected": item.__dict__, "source": created, "sync": None, "error": None}
    if not trigger_sync:
        return result
    source_id = str(created.get("id") or "").strip()
    if not source_id:
        raise RuntimeError(f"Source create response missing id for {item.canonical_library_id}")
    try:
        sync = _http_json("POST", f"{base_url}/api/internal/operator/sources/{source_id}/sync", token=token)
        result["sync"] = sync
    except RuntimeError as exc:
        result["error"] = str(exc)
    return result


def poll_runs(base_url: str, token: str, queued: list[dict[str, Any]], *, interval: int, timeout: int) -> None:
    run_ids = [
        str((item.get("sync") or {}).get("run_id") or "").strip()
        for item in queued
        if isinstance(item.get("sync"), dict)
    ]
    run_ids = [run_id for run_id in run_ids if run_id]
    if not run_ids:
        print("[poll] no run ids to poll")
        return
    terminal = {"completed", "failed", "skipped", "cancelled"}
    started = time.monotonic()
    while True:
        counts: dict[str, int] = defaultdict(int)
        statuses: dict[str, dict[str, Any]] = {}
        for run_id in run_ids:
            try:
                status = _http_json("GET", f"{base_url}/api/internal/operator/sync-runs/{run_id}", token=token)
            except RuntimeError as exc:
                counts["poll_error"] += 1
                statuses[run_id] = {"run_id": run_id, "status": "poll_error", "error": str(exc)}
                continue
            state = str(status.get("status") or "unknown")
            counts[state] += 1
            statuses[run_id] = status
        print(f"[poll] {int(time.monotonic() - started)}s {dict(sorted(counts.items()))}", flush=True)
        for item in queued:
            sync = item.get("sync") or {}
            run_id = str(sync.get("run_id") or "")
            if run_id and run_id in statuses:
                item["latest_sync"] = statuses[run_id]
        if all(str(statuses.get(run_id, {}).get("status") or "") in terminal for run_id in run_ids):
            return
        if time.monotonic() - started >= timeout:
            print("[poll] timeout reached", flush=True)
            return
        time.sleep(interval)


def write_report(results: list[dict[str, Any]]) -> Path:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    path = OUT_DIR / f"{datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%SZ')}_benchmark_100_ingest.json"
    payload = {
        "generated_at": _utc_now(),
        "csv_path": str(CSV_PATH),
        "total": len(results),
        "created_or_existing": sum(1 for item in results if item.get("source")),
        "sync_triggered": sum(1 for item in results if item.get("sync")),
        "errors": [item for item in results if item.get("error")],
        "results": results,
    }
    path.write_text(json.dumps(payload, indent=2, default=str), encoding="utf-8")
    return path


def main() -> int:
    parser = argparse.ArgumentParser(description="Queue 100 benchmark libraries into local Oz.")
    parser.add_argument("--base-url", default=os.getenv("OZ_BASE_URL", "http://localhost:8090").rstrip("/"))
    parser.add_argument("--email", default=os.getenv("OZ_OPERATOR_EMAIL", "codex-benchmark-ingest@hiringbae.com"))
    parser.add_argument("--password", default=os.getenv("OZ_OPERATOR_PASSWORD", "TempPass123!"))
    parser.add_argument("--limit", type=int, default=100)
    parser.add_argument("--max-pages", type=int, default=80)
    parser.add_argument("--max-files", type=int, default=500)
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--no-sync", action="store_true")
    parser.add_argument("--poll", action="store_true")
    parser.add_argument("--poll-interval", type=int, default=15)
    parser.add_argument("--poll-timeout", type=int, default=3600)
    args = parser.parse_args()

    selected = select_libraries(limit=args.limit, max_pages=args.max_pages, max_files=args.max_files)
    print(f"[select] selected {len(selected)} libraries from {CSV_PATH}")
    print("[select] vercel:", [item.canonical_library_id for item in selected if _is_vercel_library(item.source_library_id, item.name)])
    if args.dry_run:
        for item in selected:
            print(json.dumps(item.__dict__, sort_keys=True))
        return 0

    token = _operator_token(args.base_url, args.email, args.password)
    results: list[dict[str, Any]] = []
    for index, item in enumerate(selected, 1):
        print(f"[{index:03d}/{len(selected):03d}] {item.canonical_library_id} {item.source_type} {item.url}", flush=True)
        try:
            results.append(create_and_sync(args.base_url, token, item, trigger_sync=not args.no_sync))
        except Exception as exc:
            results.append({"selected": item.__dict__, "source": None, "sync": None, "error": str(exc)})
            print(f"[error] {item.canonical_library_id}: {exc}", flush=True)
    if args.poll and not args.no_sync:
        poll_runs(args.base_url, token, results, interval=args.poll_interval, timeout=args.poll_timeout)
    report = write_report(results)
    print(f"[report] {report}")
    errors = [item for item in results if item.get("error")]
    print(f"[summary] total={len(results)} sync_triggered={sum(1 for item in results if item.get('sync'))} errors={len(errors)}")
    return 1 if errors else 0


if __name__ == "__main__":
    raise SystemExit(main())
