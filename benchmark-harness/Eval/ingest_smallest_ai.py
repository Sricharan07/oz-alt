#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import os
import time
import urllib.error
import urllib.request
from collections import defaultdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
OUT_DIR = ROOT / ".ingestion_work" / "smallest_ingest"
EVAL_API_KEY_PATH = Path(__file__).resolve().with_name(".oz_eval_api_key")

LIBRARY_IDS = ["/smallest/py-sdk", "/smallest/node-sdk", "/smallest/cookbook", "/smallest/atoms", "/smallest/waves"]
LIBRARY_NAME = "Smallest AI"


def _utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _http_json(
    method: str,
    url: str,
    *,
    token: str | None = None,
    payload: dict[str, Any] | None = None,
    timeout: int = 180,
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
        response = _http_json(
            "POST",
            f"{base_url}/api/internal/operator/auth/register",
            payload={
                "email": email,
                "password": password,
                "full_name": "Codex Smallest Ingest",
            },
        )
    token = str((response or {}).get("access_token") or "").strip()
    if not token:
        raise RuntimeError("Operator auth did not return an access token")
    return token


def _create_eval_api_key(base_url: str, token: str, path: Path) -> str:
    payload = {
        "name": "smallest-eval-mcp-50",
        "scopes": ["query:read", "mcp:core", "mcp:traverse_client", "catalog:global_read"],
        "global_catalog_override": "enabled",
    }
    response = _http_json("POST", f"{base_url}/api/v2/api-keys", token=token, payload=payload)
    key = str((response or {}).get("key") or "").strip()
    if not key:
        raise RuntimeError("API key create response did not include key")
    path.write_text(key + "\n", encoding="utf-8")
    return key


def _source_payloads(max_pages: int, max_files: int, *, include_extras: bool) -> list[dict[str, Any]]:
    shared = {
        "version_mode": "fixed",
        "version": "latest",
        "language": "python",
    }
    git_include_globs = [
        "README*",
        "*.md",
        "*.mdx",
        "docs/**",
        "examples/**",
        "cookbook/**",
        "cookbooks/**",
        "**/*.py",
        "**/*.js",
        "**/*.jsx",
        "**/*.ts",
        "**/*.tsx",
        "pyproject.toml",
        "setup.py",
        "package.json",
    ]
    git_exclude_globs = [
        ".git/**",
        "__pycache__/**",
        ".pytest_cache/**",
        "node_modules/**",
        ".next/**",
        "dist/**",
        "build/**",
        "*.egg-info/**",
    ]

    def git_source(
        name: str,
        repo_url: str,
        description: str,
        *,
        library_id: str,
        package_identifiers: list[str],
    ) -> dict[str, Any]:
        return {
            **shared,
            "library_id": library_id,
            "package_identifiers": package_identifiers,
            "name": name,
            "source_type": "git_public",
            "source_config": {
                "repo_url": repo_url,
                "include_source_files": True,
                "include_globs": git_include_globs,
                "exclude_globs": git_exclude_globs,
                "max_files": max_files,
                "project_title": name,
                "project_description": description,
            },
        }

    def docs_source(
        name: str,
        start_url: str,
        llms_txt_url: str,
        description: str,
        *,
        library_id: str,
        package_identifiers: list[str],
    ) -> dict[str, Any]:
        canonical_start = start_url.rstrip("/") + "/"
        return {
            **shared,
            "library_id": library_id,
            "package_identifiers": package_identifiers,
            "name": name,
            "source_type": "url",
            "source_config": {
                "start_url": canonical_start,
                "allowed_prefixes": [canonical_start],
                "llms_txt_url": llms_txt_url,
                "max_pages": max_pages,
                "max_discovery_urls": max(1000, max_pages * 12),
                "full_sweep": True,
                "force_local_crawl": True,
                "fetch_render_mode": "selective",
                "extraction_mode": "hybrid",
                "project_title": name,
                "project_description": description,
            },
        }

    core = [
        git_source(
            "Smallest AI Python SDK",
            "https://github.com/smallest-inc/smallest-python-sdk",
            "Official Smallest AI Python SDK repository.",
            library_id="/smallest/py-sdk",
            package_identifiers=["smallestai", "smallest-python-sdk"],
        ),
        docs_source(
            "Smallest AI Atoms Docs",
            "https://docs.smallest.ai/atoms/",
            "https://docs.smallest.ai/atoms/llms.txt",
            "Official Smallest AI Atoms documentation.",
            library_id="/smallest/atoms",
            package_identifiers=["smallestai.atoms", "atoms"],
        ),
        docs_source(
            "Smallest AI Waves Docs",
            "https://docs.smallest.ai/waves/",
            "https://docs.smallest.ai/waves/llms.txt",
            "Official Smallest AI Waves documentation.",
            library_id="/smallest/waves",
            package_identifiers=["smallestai.waves", "waves"],
        ),
    ]
    if not include_extras:
        return core
    return [
        *core,
        git_source(
            "Smallest AI Node SDK",
            "https://github.com/smallest-inc/smallest-node-sdk",
            "Official Smallest AI Node SDK repository.",
            library_id="/smallest/node-sdk",
            package_identifiers=["smallest-node-sdk", "@smallest-ai/sdk", "smallestai-js"],
        ),
        git_source(
            "Smallest AI Cookbook",
            "https://github.com/smallest-inc/cookbook",
            "Official Smallest AI cookbook and usage recipes.",
            library_id="/smallest/cookbook",
            package_identifiers=["smallest-cookbook", "smallest-ai-cookbook", "smallestai-cookbook"],
        ),
        git_source(
            "Smallest AI Atoms SDK Example",
            "https://github.com/smallest-inc/atoms-sdk-example",
            "Official Smallest AI Atoms SDK example repository.",
            library_id="/smallest/atoms",
            package_identifiers=["smallestai.atoms", "atoms"],
        ),
        git_source(
            "Smallest AI Waves Examples",
            "https://github.com/smallest-inc/waves-examples",
            "Official Smallest AI Waves examples repository.",
            library_id="/smallest/waves",
            package_identifiers=["smallestai.waves", "waves"],
        ),
    ]


def _create_and_sync(base_url: str, token: str, payload: dict[str, Any], *, trigger_sync: bool) -> dict[str, Any]:
    created = _http_json("POST", f"{base_url}/api/internal/operator/sources", token=token, payload=payload)
    result = {"payload": payload, "source": created, "sync": None, "error": None}
    if not trigger_sync:
        return result
    source_id = str((created or {}).get("id") or "").strip()
    if not source_id:
        raise RuntimeError(f"Source create response missing id for {payload.get('name')}")
    result["sync"] = _http_json("POST", f"{base_url}/api/internal/operator/sources/{source_id}/sync", token=token)
    return result


def _poll_runs(base_url: str, token: str, results: list[dict[str, Any]], *, interval: int, timeout: int) -> None:
    run_ids = [
        str((item.get("sync") or {}).get("run_id") or "").strip()
        for item in results
        if isinstance(item.get("sync"), dict)
    ]
    run_ids = [item for item in run_ids if item]
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
        for item in results:
            run_id = str((item.get("sync") or {}).get("run_id") or "").strip()
            if run_id and run_id in statuses:
                item["latest_sync"] = statuses[run_id]
        print(f"[poll] {int(time.monotonic() - started)}s {dict(sorted(counts.items()))}", flush=True)
        if all(str(statuses.get(run_id, {}).get("status") or "") in terminal for run_id in run_ids):
            return
        if time.monotonic() - started >= timeout:
            print("[poll] timeout reached", flush=True)
            return
        time.sleep(interval)


def _write_report(results: list[dict[str, Any]], *, api_key_path: Path) -> Path:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    path = OUT_DIR / f"{datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%SZ')}_smallest_ai_ingest.json"
    payload = {
        "generated_at": _utc_now(),
        "library_ids": LIBRARY_IDS,
        "library_name": LIBRARY_NAME,
        "api_key_file": str(api_key_path),
        "total": len(results),
        "sync_triggered": sum(1 for item in results if item.get("sync")),
        "errors": [item for item in results if item.get("error")],
        "results": results,
    }
    path.write_text(json.dumps(payload, indent=2, default=str), encoding="utf-8")
    return path


def main() -> int:
    parser = argparse.ArgumentParser(description="Ingest Smallest AI repo and docs into local Oz.")
    parser.add_argument("--base-url", default=os.getenv("OZ_BASE_URL", "http://localhost:8090").rstrip("/"))
    parser.add_argument("--email", default=os.getenv("OZ_OPERATOR_EMAIL", "codex-smallest-ingest@hiringbae.com"))
    parser.add_argument("--password", default=os.getenv("OZ_OPERATOR_PASSWORD", "TempPass123!"))
    parser.add_argument("--max-pages", type=int, default=int(os.getenv("SMALLEST_INGEST_MAX_PAGES", "120")))
    parser.add_argument("--max-files", type=int, default=int(os.getenv("SMALLEST_INGEST_MAX_FILES", "1200")))
    parser.add_argument("--poll", action="store_true")
    parser.add_argument("--poll-interval", type=int, default=15)
    parser.add_argument("--poll-timeout", type=int, default=3600)
    parser.add_argument("--no-sync", action="store_true")
    parser.add_argument("--no-api-key", action="store_true")
    parser.add_argument("--include-extras", action="store_true")
    parser.add_argument(
        "--sync-source-id",
        action="append",
        default=[],
        help="Trigger sync for an existing source id instead of creating sources. May be repeated.",
    )
    args = parser.parse_args()

    token = _operator_token(args.base_url, args.email, args.password)
    if not args.no_api_key:
        key = _create_eval_api_key(args.base_url, token, EVAL_API_KEY_PATH)
        print(f"[auth] wrote eval MCP API key prefix {key[:16]} to {EVAL_API_KEY_PATH}")

    results: list[dict[str, Any]] = []
    sync_source_ids = [str(item or "").strip() for item in args.sync_source_id if str(item or "").strip()]
    if sync_source_ids:
        for index, source_id in enumerate(sync_source_ids, 1):
            print(f"[{index}/{len(sync_source_ids)}] sync existing source {source_id}", flush=True)
            try:
                sync = None
                if not args.no_sync:
                    sync = _http_json(
                        "POST",
                        f"{args.base_url}/api/internal/operator/sources/{source_id}/sync",
                        token=token,
                    )
                results.append(
                    {
                        "payload": {"source_id": source_id, "existing_source": True},
                        "source": {"id": source_id},
                        "sync": sync,
                        "error": None,
                    }
                )
            except Exception as exc:
                results.append({"payload": {"source_id": source_id, "existing_source": True}, "source": None, "sync": None, "error": str(exc)})
                print(f"[error] existing source {source_id}: {exc}", flush=True)
    else:
        payloads = _source_payloads(args.max_pages, args.max_files, include_extras=args.include_extras)
        for index, payload in enumerate(payloads, 1):
            print(f"[{index}/{len(payloads)}] {payload['source_type']} {payload['name']}", flush=True)
            try:
                results.append(_create_and_sync(args.base_url, token, payload, trigger_sync=not args.no_sync))
            except Exception as exc:
                results.append({"payload": payload, "source": None, "sync": None, "error": str(exc)})
                print(f"[error] {payload['name']}: {exc}", flush=True)

    if args.poll and not args.no_sync:
        _poll_runs(args.base_url, token, results, interval=args.poll_interval, timeout=args.poll_timeout)

    report = _write_report(results, api_key_path=EVAL_API_KEY_PATH)
    errors = [item for item in results if item.get("error")]
    print(f"[report] {report}")
    print(f"[summary] total={len(results)} sync_triggered={sum(1 for item in results if item.get('sync'))} errors={len(errors)}")
    return 1 if errors else 0


if __name__ == "__main__":
    raise SystemExit(main())
