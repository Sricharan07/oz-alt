from __future__ import annotations

import sys
import unittest
from pathlib import Path
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "packages" / "oz-api" / "src"))

from oz_api import public_catalog  # noqa: E402


class FakeStore:
    def __init__(self) -> None:
        self.calls: list[dict[str, object]] = []

    def execute(self, sql: str, params: dict[str, object]) -> list[dict[str, object]]:
        self.calls.append({"sql": sql, "params": params})
        return [
            {
                "vendor": "vercel",
                "library": "next.js",
                "version": "15",
                "chunk_count": 1530,
                "token_count": 418787,
                "file_count": 286,
                "pack_bytes": 0,
            }
        ]


class FakeStorage:
    def load_catalog(self) -> list[dict[str, object]]:
        return []

    def get_pack_bytes(self, vendor: str, library: str, version: str) -> bytes | None:
        if (vendor, library, version) == ("vercel", "next.js", "15"):
            return b"pack-bytes"
        return None


class PublicCatalogTests(unittest.TestCase):
    def test_library_rows_query_uses_latest_version_params(self) -> None:
        store = FakeStore()
        with patch.object(public_catalog.AuthStore, "from_env", return_value=store):
            rows = public_catalog.public_library_rows(FakeStorage())

        self.assertEqual(rows[0]["chunk_count"], 1530)
        self.assertEqual(rows[0]["token_count"], 418787)
        self.assertEqual(store.calls[0]["params"], {"version": ""})

    def test_detail_hydrates_pack_bytes_from_storage_when_db_has_no_size(self) -> None:
        row = {
            "vendor": "vercel",
            "library": "next.js",
            "version": "15",
            "pack_bytes": 0,
        }

        hydrated = public_catalog.hydrate_pack_bytes(FakeStorage(), row)

        self.assertEqual(hydrated["pack_bytes"], len(b"pack-bytes"))


if __name__ == "__main__":
    unittest.main()
