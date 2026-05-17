from __future__ import annotations

import os
import socket
import sys
import threading
import unittest
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
        server = OneShotHttpServer(seen_host)
        server.start()

        try:
            with EnvPatch(OZ_CRAWLER_ALLOW_PRIVATE_NETWORKS="1"), patch(
                "oz_crawler.security.socket.getaddrinfo",
                return_value=[(socket.AF_INET, socket.SOCK_STREAM, 6, "", ("127.0.0.1", server.port))],
            ):
                response = security.fetch_public_url(f"http://example.test:{server.port}/docs")
        finally:
            server.stop()
        self.assertEqual(response.body, b"ok")
        self.assertEqual(seen_host, [f"example.test:{server.port}"])

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


class OneShotHttpServer:
    def __init__(self, seen_host: list[str]) -> None:
        self.seen_host = seen_host
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.sock.bind(("127.0.0.1", 0))
        self.sock.listen(1)
        self.port = int(self.sock.getsockname()[1])
        self.thread = threading.Thread(target=self._serve_once, daemon=True)

    def start(self) -> None:
        self.thread.start()

    def stop(self) -> None:
        try:
            self.sock.close()
        finally:
            self.thread.join(timeout=2)

    def _serve_once(self) -> None:
        try:
            conn, _addr = self.sock.accept()
        except OSError:
            return
        with conn:
            data = b""
            while b"\r\n\r\n" not in data:
                chunk = conn.recv(4096)
                if not chunk:
                    break
                data += chunk
            self.seen_host.append(host_header(data))
            conn.sendall(
                b"HTTP/1.1 200 OK\r\n"
                b"Content-Type: text/plain\r\n"
                b"Content-Length: 2\r\n"
                b"Connection: close\r\n"
                b"\r\n"
                b"ok"
            )


def host_header(request_bytes: bytes) -> str:
    for line in request_bytes.decode("iso-8859-1", errors="replace").split("\r\n"):
        if line.lower().startswith("host:"):
            return line.split(":", 1)[1].strip()
    return ""


if __name__ == "__main__":
    unittest.main()
