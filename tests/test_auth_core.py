from __future__ import annotations

import json
import os
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "packages" / "oz-api" / "src"))

from oz_api import auth  # noqa: E402


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


class AuthCoreTests(unittest.TestCase):
    def tearDown(self) -> None:
        auth._JWT_SECRET_CACHE = None

    def test_issued_token_round_trips_claims(self) -> None:
        with EnvPatch(OZ_ENV="", OZ_JWT_SECRET="test-secret"):
            token = auth.issue_token("user-1", role="admin", email="admin@example.com")
            claims = auth.token_claims(token)
        self.assertIsNotNone(claims)
        assert claims is not None
        self.assertEqual(claims["sub"], "user-1")
        self.assertEqual(claims["role"], "admin")
        self.assertEqual(claims["email"], "admin@example.com")

    def test_expired_token_is_rejected(self) -> None:
        with EnvPatch(OZ_ENV="", OZ_JWT_SECRET="test-secret"):
            token = auth.issue_token("user-1", expires_in=-1)
            self.assertIsNone(auth.token_claims(token))

    def test_tampered_token_is_rejected(self) -> None:
        with EnvPatch(OZ_ENV="", OZ_JWT_SECRET="test-secret"):
            token = auth.issue_token("user-1")
            header, payload, signature = token.split(".")
            decoded = json.loads(auth.b64_decode(payload))
            decoded["role"] = "admin"
            tampered = ".".join([header, auth.b64_json(decoded), signature])
            self.assertIsNone(auth.token_claims(tampered))

    def test_csrf_token_is_session_bound(self) -> None:
        with EnvPatch(OZ_ENV="", OZ_JWT_SECRET="test-secret"):
            submitted = auth.csrf_token("session-a")
            self.assertTrue(auth.verify_csrf("session-a", submitted))
            self.assertFalse(auth.verify_csrf("session-b", submitted))

    def test_password_policy_rejects_short_or_spaced_passwords(self) -> None:
        with self.assertRaises(auth.AuthError):
            auth.validate_password("short")
        with self.assertRaises(auth.AuthError):
            auth.validate_password("  long-enough-password  ")
        auth.validate_password("long-enough-password")

    def test_generated_device_code_normalizes_for_human_entry(self) -> None:
        code = auth.generate_user_code()
        self.assertRegex(code, r"^[A-Z2-9]{4}-[A-Z2-9]{4}$")
        self.assertEqual(auth.normalize_user_code(code.lower().replace("-", " ")), code.replace("-", ""))


if __name__ == "__main__":
    unittest.main()
