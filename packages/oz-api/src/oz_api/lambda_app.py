from __future__ import annotations

import base64
import json
import os
from datetime import datetime, timezone
from pathlib import Path
from typing import Any
from urllib.parse import parse_qs

from oz_api.admin import esc, render_admin
from oz_api.auth import bearer_token, exchange_device_code, start_device_authorization, verify_token
from oz_api.freshness import stale_libraries_from_payload
from oz_api.limits import index_request_allowed
from oz_api.retrieval import (
    RetrievalContext,
    latest_entry,
    search,
    suggest,
    unique_libraries_to_pull,
)
from oz_api.queue import crawler_job_event, enqueue_crawler_job, missing_required_crawler_fields
from oz_api.storage import RegistryStorage
from oz_api.telemetry import sanitize_telemetry


def handler(event: dict[str, Any], context: Any) -> dict[str, Any]:
    storage = RegistryStorage.from_env(Path(os.environ.get("OZ_REPO_ROOT", ".")).resolve())
    retrieval = RetrievalContext.from_env(storage)
    method = event.get("requestContext", {}).get("http", {}).get("method") or event.get("httpMethod", "GET")
    raw_path = event.get("rawPath") or event.get("path", "/")
    body = parse_body(event)

    if raw_path == "/admin/login" and method == "GET":
        return admin_login_response()

    if raw_path == "/admin/login" and method == "POST":
        return admin_login_submit_response(event)

    if raw_path == "/admin/logout" and method == "GET":
        return admin_logout_response()

    if not is_authorized(event, raw_path):
        if raw_path.startswith("/admin"):
            return admin_login_response(status=401)
        return json_response({"error": "unauthorized"}, status=401)

    if raw_path == "/health" and method == "GET":
        return json_response({"ok": True, "service": "oz-api"})

    if raw_path == "/auth/device" and method == "POST":
        return json_response(start_device_authorization())

    if raw_path == "/auth/token" and method == "POST":
        token = exchange_device_code(str(body.get("device_code") or ""))
        if token.get("error"):
            return json_response(token, status=400)
        return json_response(token)

    if raw_path == "/suggest" and method == "POST":
        return json_response(
            {
                "results": suggest(
                    retrieval,
                    str(body.get("query", "")),
                    int(body.get("max_results", 10)),
                    fingerprint=str(body.get("project_fingerprint", "")),
                ),
                "stale_libraries": stale_libraries_from_payload(storage, body),
            }
        )

    if raw_path == "/search" and method == "POST":
        results = search(
            retrieval,
            str(body.get("query", "")),
            library_scope=body.get("library_scope"),
            max_results=int(body.get("max_results", 20)),
            fingerprint=str(body.get("project_fingerprint", "")),
        )
        return json_response(
            {
                "results": results,
                "libraries_to_pull": unique_libraries_to_pull(results),
                "stale_libraries": stale_libraries_from_payload(storage, body),
            }
        )

    if raw_path.startswith("/refs/") and method == "GET":
        _, _, vendor, library = raw_path.split("/", 3)
        entry = latest_entry(storage, vendor, library)
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
        return json_response(bulk_refs_payload(storage, event.get("rawQueryString", "")))

    if raw_path.startswith("/pack/") and method == "GET":
        _, _, vendor, library, version = raw_path.split("/", 4)
        pack_url = storage.get_pack_url(vendor, library, version)
        if pack_url:
            return {
                "statusCode": 302,
                "headers": {
                    "location": pack_url,
                    "cache-control": "public, max-age=31536000, immutable",
                },
                "body": "",
            }
        pack_bytes = storage.get_pack_bytes(vendor, library, version)
        if pack_bytes is None:
            return json_response({"error": "pack not found"}, status=404)
        return {
            "statusCode": 200,
            "headers": {
                "content-type": "application/vnd.oz.pack",
                "cache-control": "public, max-age=31536000, immutable",
            },
            "isBase64Encoded": True,
            "body": base64.b64encode(pack_bytes).decode("ascii"),
        }

    if raw_path == "/catalog" and method == "GET":
        return json_response({"libraries": storage.load_catalog()})

    if raw_path in {"/admin", "/admin/"} and method == "GET":
        return html_response(render_admin(storage))

    if raw_path == "/admin/enqueue-crawl" and method == "GET":
        params = parse_qs(event.get("rawQueryString", "") or "")
        payload = {
            "library_name": params.get("library_name", [""])[0],
            "vendor": params.get("vendor", [""])[0],
            "source_url": params.get("source_url", [""])[0],
        }
        missing = missing_required_crawler_fields(crawler_job_event(payload))
        if missing:
            return html_response(
                f"<!doctype html><p>Missing crawler job fields: {esc(', '.join(missing))}</p>",
                status=400,
            )
        enqueue_crawler_job(storage, payload)
        return html_response('<!doctype html><meta http-equiv="refresh" content="0; url=/admin">', status=202)

    if raw_path == "/admin/index-requests" and method == "GET":
        return json_response(storage.read_admin_events("index_requests"))

    if raw_path == "/admin/telemetry" and method == "GET":
        return json_response(storage.read_admin_events("telemetry"))

    if raw_path == "/admin/crawler-jobs" and method == "GET":
        return json_response(storage.read_admin_events("crawler_jobs"))

    if raw_path == "/index-request" and method == "POST":
        requesting_user = str(body.get("requesting_user", "lambda"))
        if not index_request_allowed(storage, requesting_user):
            return json_response({"error": "rate limited"}, status=429)
        storage.append_admin_event(
            "index_requests",
            {
                "created_at": now(),
                "library_name": body.get("library_name"),
                "vendor_hint": body.get("vendor_hint"),
                "source_url_hint": body.get("source_url_hint"),
                "requesting_user": requesting_user,
            },
        )
        return json_response({"ok": True})

    if raw_path == "/crawler/enqueue" and method == "POST":
        missing = missing_required_crawler_fields(crawler_job_event(body))
        if missing:
            return json_response({"error": "missing crawler job fields", "fields": missing}, status=400)
        event = enqueue_crawler_job(storage, body)
        return json_response({"ok": True, "job": event})

    if raw_path == "/telemetry" and method == "POST":
        telemetry = sanitize_telemetry(body)
        storage.append_admin_event(
            "telemetry",
            {
                "created_at": now(),
                "event": telemetry["event"],
                "properties": telemetry["properties"],
            },
        )
        return json_response({"ok": True})

    return json_response({"error": "not found"}, status=404)


def parse_body(event: dict[str, Any]) -> dict[str, Any]:
    raw = event.get("body")
    if not raw:
        return {}
    if event.get("isBase64Encoded"):
        raw = base64.b64decode(raw).decode("utf-8")
    content_type = header_value(event.get("headers") or {}, "Content-Type") or ""
    if "json" not in content_type.lower():
        return {}
    return json.loads(raw)


def is_authorized(event: dict[str, Any], raw_path: str) -> bool:
    if os.environ.get("OZ_REQUIRE_AUTH", "").lower() not in {"1", "true", "yes", "on"}:
        return True
    if raw_path in {"/health", "/auth/device", "/auth/token", "/auth/verify"}:
        return True
    token = bearer_token(event.get("headers") or {})
    if raw_path.startswith("/admin"):
        token = token or cookie_token(event, "oz_admin_token")
    dev_token = os.environ.get("OZ_DEV_TOKEN")
    return (bool(dev_token) and token == dev_token) or (token is not None and verify_token(token))


def cookie_token(event: dict[str, Any], name: str) -> str | None:
    cookies: list[str] = []
    raw_cookies = event.get("cookies")
    if isinstance(raw_cookies, list):
        cookies.extend(str(cookie) for cookie in raw_cookies)
    cookie_header = header_value(event.get("headers") or {}, "Cookie")
    if cookie_header:
        cookies.extend(part.strip() for part in cookie_header.split(";"))
    prefix = f"{name}="
    for cookie in cookies:
        if cookie.startswith(prefix):
            return cookie[len(prefix) :]
    return None


def header_value(headers: dict[str, str] | Any, key: str) -> str | None:
    if not hasattr(headers, "get"):
        return None
    return headers.get(key) or headers.get(key.lower())


def admin_login_response(*, status: int = 200, error: str = "") -> dict[str, Any]:
    error_html = f"<p class=\"error\">{esc(error)}</p>" if error else ""
    return html_response(
        f"""<!doctype html>
<html>
<head>
  <meta charset="utf-8">
  <title>Oz Admin Login</title>
  <style>
    body {{ margin: 0; min-height: 100vh; display: grid; place-items: center; background: #f7f7f4; color: #202124; font-family: ui-sans-serif, system-ui, sans-serif; }}
    main {{ width: min(420px, calc(100vw - 32px)); border: 1px solid #d8dee4; background: #fff; border-radius: 8px; padding: 24px; box-shadow: 0 16px 40px rgba(0,0,0,.08); }}
    h1 {{ margin: 0 0 16px; font-size: 22px; }}
    label {{ display: block; margin: 0 0 8px; font-size: 13px; color: #51565c; }}
    input {{ box-sizing: border-box; width: 100%; border: 1px solid #c7cbd1; border-radius: 6px; padding: 10px 12px; font: inherit; }}
    button {{ margin-top: 14px; width: 100%; border: 0; border-radius: 6px; background: #202124; color: #fff; padding: 10px 12px; font: inherit; cursor: pointer; }}
    .error {{ margin: 0 0 12px; color: #b42318; font-size: 13px; }}
  </style>
</head>
<body>
  <main>
    <h1>Oz Admin</h1>
    {error_html}
    <form method="post" action="/admin/login">
      <label for="token">Oz access token</label>
      <input id="token" name="token" type="password" autocomplete="current-password" autofocus>
      <button type="submit">Open admin</button>
    </form>
  </main>
</body>
</html>""",
        status=status,
    )


def admin_login_submit_response(event: dict[str, Any]) -> dict[str, Any]:
    token = parse_form_body(event).get("token", [""])[0].strip()
    if not token or not verify_token(token):
        return admin_login_response(status=401, error="Invalid or expired Oz token.")
    return {
        "statusCode": 303,
        "headers": {
            "location": "/admin",
            "set-cookie": (
                f"oz_admin_token={token}; Path=/admin; Max-Age=86400; "
                "HttpOnly; Secure; SameSite=Lax"
            ),
        },
        "body": "",
    }


def admin_logout_response() -> dict[str, Any]:
    return {
        "statusCode": 303,
        "headers": {
            "location": "/admin/login",
            "set-cookie": "oz_admin_token=; Path=/admin; Max-Age=0; HttpOnly; Secure; SameSite=Lax",
        },
        "body": "",
    }


def parse_form_body(event: dict[str, Any]) -> dict[str, list[str]]:
    raw = event.get("body") or ""
    if event.get("isBase64Encoded"):
        raw = base64.b64decode(raw).decode("utf-8")
    return parse_qs(raw)


def json_response(payload: Any, *, status: int = 200) -> dict[str, Any]:
    return {
        "statusCode": status,
        "headers": {"content-type": "application/json"},
        "body": json.dumps(payload, sort_keys=True),
    }


def html_response(body: str, *, status: int = 200) -> dict[str, Any]:
    return {
        "statusCode": status,
        "headers": {"content-type": "text/html; charset=utf-8"},
        "body": body,
    }


def now() -> str:
    return datetime.now(timezone.utc).isoformat()


def bulk_refs_payload(storage: RegistryStorage, query: str) -> dict[str, Any]:
    params = parse_qs(query or "")
    stale_libraries: list[dict[str, Any]] = []
    for raw in params.get("library", []):
        parsed = parse_pulled_library(raw)
        if parsed is None:
            continue
        vendor, library, version = parsed
        entry = latest_entry(storage, vendor, library)
        if entry is None:
            continue
        newer_version = str(entry.get("version") or "")
        if newer_version and newer_version != version:
            stale_libraries.append(
                {
                    "vendor": vendor,
                    "library": library,
                    "version": version,
                    "newer_version": newer_version,
                    "ref_sha": entry.get("ref_sha"),
                }
            )
    return {
        "stale_libraries": stale_libraries,
        "fingerprint": params.get("fingerprint", [""])[0],
        "catalog_generated_at": storage.catalog_generated_at(),
    }


def parse_pulled_library(value: str) -> tuple[str, str, str] | None:
    if "@" not in value or "/" not in value:
        return None
    name, version = value.rsplit("@", 1)
    vendor, library = name.split("/", 1)
    if not vendor or not library or not version:
        return None
    return vendor, library, version
