from __future__ import annotations

import base64
import json
import os
from pathlib import Path
from typing import Any

from oz_api.server import (
    ServerState,
    latest_entry,
    load_catalog,
    normalize_query,
    search,
    suggest,
    unique_libraries_to_pull,
)


def handler(event: dict[str, Any], context: Any) -> dict[str, Any]:
    state = ServerState(repo_root=Path(os.environ.get("OZ_REPO_ROOT", ".")).resolve())
    method = event.get("requestContext", {}).get("http", {}).get("method") or event.get("httpMethod", "GET")
    raw_path = event.get("rawPath") or event.get("path", "/")
    body = parse_body(event)

    if raw_path == "/health" and method == "GET":
        return json_response({"ok": True, "service": "oz-api"})

    if raw_path == "/auth/device" and method == "POST":
        return json_response(
            {
                "device_code": "lambda-device-code",
                "user_code": "OZ-LAMBDA",
                "verification_uri": os.environ.get("OZ_VERIFY_URL", "https://example.com/auth/verify"),
                "interval": 1,
                "expires_in": 600,
            }
        )

    if raw_path == "/auth/token" and method == "POST":
        if body.get("device_code") not in {"lambda-device-code", "local-device-code"}:
            return json_response({"error": "invalid device_code"}, status=400)
        return json_response({"access_token": os.environ.get("OZ_DEV_TOKEN", "local-dev-token"), "token_type": "Bearer"})

    if raw_path == "/suggest" and method == "POST":
        return json_response(
            {
                "results": suggest(state, str(body.get("query", "")), int(body.get("max_results", 10))),
                "stale_libraries": [],
            }
        )

    if raw_path == "/search" and method == "POST":
        results = search(
            state,
            str(body.get("query", "")),
            library_scope=body.get("library_scope"),
            max_results=int(body.get("max_results", 20)),
        )
        return json_response(
            {
                "results": results,
                "libraries_to_pull": unique_libraries_to_pull(results),
                "stale_libraries": [],
            }
        )

    if raw_path.startswith("/refs/") and method == "GET":
        _, _, vendor, library = raw_path.split("/", 3)
        entry = latest_entry(state, vendor, library)
        if entry is None:
            return json_response({"error": "library not indexed"}, status=404)
        return json_response(
            {
                "vendor": vendor,
                "library": library,
                "version": entry["version"],
                "ref_sha": entry.get("ref_sha", "local"),
            }
        )

    if raw_path == "/refs" and method == "GET":
        return json_response({"stale_libraries": []})

    if raw_path.startswith("/pack/") and method == "GET":
        _, _, vendor, library, version = raw_path.split("/", 4)
        pack_path = state.packs_root / vendor / library / f"{version}.ozpack"
        if not pack_path.exists():
            return json_response({"error": "pack not found"}, status=404)
        return {
            "statusCode": 200,
            "headers": {
                "content-type": "application/vnd.oz.pack",
                "cache-control": "public, max-age=31536000, immutable",
            },
            "isBase64Encoded": True,
            "body": base64.b64encode(pack_path.read_bytes()).decode("ascii"),
        }

    if raw_path == "/catalog" and method == "GET":
        return json_response({"libraries": load_catalog(state)})

    return json_response({"error": "not found"}, status=404)


def parse_body(event: dict[str, Any]) -> dict[str, Any]:
    raw = event.get("body")
    if not raw:
        return {}
    if event.get("isBase64Encoded"):
        raw = base64.b64decode(raw).decode("utf-8")
    return json.loads(raw)


def json_response(payload: Any, *, status: int = 200) -> dict[str, Any]:
    return {
        "statusCode": status,
        "headers": {"content-type": "application/json"},
        "body": json.dumps(payload, sort_keys=True),
    }

