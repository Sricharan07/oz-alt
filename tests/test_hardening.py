from __future__ import annotations

import os
import socket
import sys
import threading
import unittest
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "packages" / "oz-api" / "src"))
sys.path.insert(0, str(ROOT / "packages" / "oz-crawler" / "src"))

from oz_api import auth, limits  # noqa: E402
from oz_api.admin import render_alert_row, render_catalog_row, render_user_row  # noqa: E402
from oz_crawler import security  # noqa: E402


class EnvPatch:
    def __init__(self, **updates: str | None) -> None:
        self.updates = updates
        self.original: dict[str, str | None] = {}

    def __enter__(self) -> None:
        for key, value in self.updates.items():
            self.original[key] = os.environ.get(key)
            if value is None:
                os.environ.pop(key, None)
            else:
                os.environ[key] = value

    def __exit__(self, *_exc: object) -> None:
        for key, value in self.original.items():
            if value is None:
                os.environ.pop(key, None)
            else:
                os.environ[key] = value


class HardeningTests(unittest.TestCase):
    def tearDown(self) -> None:
        auth._JWT_SECRET_CACHE = None
        security.resolved_addresses.cache_clear()

    def test_production_rejects_placeholder_jwt_secret(self) -> None:
        with EnvPatch(OZ_ENV="production", OZ_JWT_SECRET="local-compose-jwt-secret-change-me"):
            with self.assertRaisesRegex(RuntimeError, "non-placeholder"):
                auth.jwt_secret()

    def test_production_accepts_strong_jwt_secret(self) -> None:
        strong = "x" * 64
        with EnvPatch(OZ_ENV="production", OZ_JWT_SECRET=strong):
            self.assertEqual(auth.jwt_secret(), strong)

    def test_rate_limit_degrades_open_for_search_when_redis_unavailable(self) -> None:
        with patch("oz_api.limits.redis_client", return_value=None):
            self.assertTrue(limits.rate_limit_allowed("api:/search", "127.0.0.1", limit=1))
            self.assertTrue(limits.rate_limit_allowed("post:/telemetry", "127.0.0.1", limit=1))

    def test_rate_limit_degrades_closed_for_auth_and_admin(self) -> None:
        with patch("oz_api.limits.redis_client", return_value=None):
            self.assertFalse(limits.rate_limit_allowed("auth:/login", "127.0.0.1", limit=1))
            self.assertFalse(limits.rate_limit_allowed("admin:/admin/users", "127.0.0.1", limit=1))
            self.assertFalse(limits.index_request_allowed("user@example.com"))

    def test_public_target_blocks_any_private_dns_answer(self) -> None:
        security.resolved_addresses.cache_clear()
        with patch(
            "oz_crawler.security.socket.getaddrinfo",
            return_value=[
                (0, 0, 0, "", ("93.184.216.34", 443)),
                (0, 0, 0, "", ("127.0.0.1", 443)),
            ],
        ):
            with self.assertRaises(security.UnsafeCrawlerUrl):
                security.resolve_public_fetch_target("https://docs.example.com/reference")

    def test_public_target_pins_resolved_address(self) -> None:
        security.resolved_addresses.cache_clear()
        with patch(
            "oz_crawler.security.socket.getaddrinfo",
            return_value=[(0, 0, 0, "", ("93.184.216.34", 443))],
        ):
            target = security.resolve_public_fetch_target("https://docs.example.com/reference?q=1")
        self.assertEqual(target.address, "93.184.216.34")
        self.assertEqual(target.host, "docs.example.com")
        self.assertEqual(target.host_header, "docs.example.com")
        self.assertEqual(target.path, "/reference?q=1")

    def test_pinned_http_fetch_preserves_host_header(self) -> None:
        seen_host: list[str] = []

        class Handler(BaseHTTPRequestHandler):
            def do_GET(self) -> None:
                seen_host.append(self.headers.get("Host", ""))
                body = b"ok"
                self.send_response(200)
                self.send_header("Content-Type", "text/plain")
                self.send_header("Content-Length", str(len(body)))
                self.end_headers()
                self.wfile.write(body)

            def log_message(self, _format: str, *_args: object) -> None:
                return

        server = ThreadingHTTPServer(("127.0.0.1", 0), Handler)
        thread = threading.Thread(target=server.serve_forever, daemon=True)
        thread.start()
        try:
            port = server.server_address[1]
            with EnvPatch(OZ_CRAWLER_ALLOW_PRIVATE_NETWORKS="1"), patch(
                "oz_crawler.security.socket.getaddrinfo",
                return_value=[(socket.AF_INET, socket.SOCK_STREAM, 6, "", ("127.0.0.1", port))],
            ):
                response = security.fetch_public_url(f"http://example.test:{port}/docs")
        finally:
            server.shutdown()
            thread.join(timeout=2)
            server.server_close()
        self.assertEqual(response.body, b"ok")
        self.assertEqual(seen_host, [f"example.test:{port}"])

    def test_admin_rows_escape_dynamic_values(self) -> None:
        malicious = '<script>alert("x")</script>'
        html = "\n".join(
            [
                render_alert_row({"severity": malicious, "status": malicious, "title": malicious}),
                render_user_row({"email": malicious, "role": malicious}, csrf=malicious),
                render_catalog_row(
                    {
                        "vendor": malicious,
                        "library": malicious,
                        "version": malicious,
                        "description": malicious,
                        "source_urls": [malicious],
                    },
                    csrf=malicious,
                ),
            ]
        )
        self.assertNotIn("<script>", html)
        self.assertIn("&lt;script&gt;", html)


if __name__ == "__main__":
    unittest.main()
