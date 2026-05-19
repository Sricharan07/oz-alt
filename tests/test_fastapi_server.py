from __future__ import annotations

import os
import sys
import unittest
from pathlib import Path

from fastapi.testclient import TestClient

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "packages" / "oz-api" / "src"))
sys.path.insert(0, str(ROOT / "packages" / "oz-crawler" / "src"))

from oz_api.http_context import ServerState  # noqa: E402
from oz_api.server import create_app  # noqa: E402


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


class FastApiServerTests(unittest.TestCase):
    def client(self, *, require_auth: bool = False) -> TestClient:
        state = ServerState(repo_root=ROOT, require_auth=require_auth, bearer_token="test-token")
        return TestClient(create_app(state))

    def test_health_and_catalog_are_public(self) -> None:
        with self.client(require_auth=True) as client:
            health = client.get("/health")
            catalog = client.get("/catalog")
            libraries = client.get("/libraries")
            libraries_json = client.get("/libraries.json")
        self.assertEqual(health.status_code, 200)
        self.assertEqual(health.json()["service"], "oz-api")
        self.assertEqual(catalog.status_code, 200)
        self.assertIn("libraries", catalog.json())
        self.assertEqual(libraries.status_code, 200)
        self.assertIn("Libraries", libraries.text)
        self.assertEqual(libraries_json.status_code, 200)
        self.assertIn("libraries", libraries_json.json())

    def test_library_detail_page_is_public(self) -> None:
        with self.client(require_auth=True) as client:
            response = client.get("/libraries/facebook/react")
            payload = client.get("/api/libraries/facebook/react")
        self.assertIn(response.status_code, {200, 404})
        self.assertIn(payload.status_code, {200, 404})
        if response.status_code == 200:
            self.assertIn("oz pull facebook/react", response.text)

    def test_request_id_is_returned_and_status_json_is_public(self) -> None:
        with self.client(require_auth=True) as client:
            health = client.get("/health", headers={"x-request-id": "test-request-id"})
            status = client.get("/status.json")

        self.assertEqual(health.headers.get("x-request-id"), "test-request-id")
        self.assertEqual(status.status_code, 200)
        self.assertEqual(status.json()["service"], "oz")
        self.assertIn("components", status.json())

    def test_protected_refs_require_auth_when_enabled(self) -> None:
        with self.client(require_auth=True) as client:
            unauthorized = client.get("/refs/openai/openai-node")
            authorized = client.get("/refs/openai/openai-node", headers={"Authorization": "Bearer test-token"})
        self.assertEqual(unauthorized.status_code, 401)
        self.assertIn(authorized.status_code, {200, 404})

    def test_admin_get_unauthorized_renders_login(self) -> None:
        with self.client(require_auth=True) as client:
            response = client.get("/admin")
        self.assertEqual(response.status_code, 401)
        self.assertIn("Oz Login", response.text)

    def test_metrics_hide_when_token_missing(self) -> None:
        with EnvPatch(OZ_METRICS_TOKEN=None):
            with self.client() as client:
                response = client.get("/metrics")
        self.assertEqual(response.status_code, 404)

    def test_invalid_json_returns_bad_request(self) -> None:
        with self.client() as client:
            response = client.post("/suggest", content="{", headers={"content-type": "application/json"})
        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.json()["error"], "invalid JSON payload")

    def test_large_post_body_returns_payload_too_large(self) -> None:
        with EnvPatch(OZ_MAX_REQUEST_BODY_BYTES="4"):
            with self.client() as client:
                response = client.post("/suggest", content='{"query":"too large"}', headers={"content-type": "application/json"})
        self.assertEqual(response.status_code, 413)
        self.assertEqual(response.json()["error"], "request_body_too_large")

    def test_context_route_returns_snippets_and_retrieval_mode(self) -> None:
        with self.client() as client:
            response = client.post(
                "/context",
                json={
                    "query": "middleware jwt cookies",
                    "library_scope": "vercel/next.js",
                    "max_tokens": 800,
                    "max_results": 2,
                },
            )

        self.assertEqual(response.status_code, 200)
        payload = response.json()
        self.assertIn("retrieval_mode", payload)
        self.assertGreaterEqual(len(payload["results"]), 1)
        self.assertIn("snippet", payload["results"][0])
        self.assertNotIn("title:", payload["results"][0]["snippet"])


if __name__ == "__main__":
    unittest.main()
