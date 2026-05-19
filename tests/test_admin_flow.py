from __future__ import annotations

import os
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "packages" / "oz-api" / "src"))

from oz_api import admin  # noqa: E402
from oz_api.admin_templates import render_admin_template  # noqa: E402


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


class AdminFlowTests(unittest.TestCase):
    def test_admin_crawl_default_uses_production_crawler_limit(self) -> None:
        with EnvPatch(OZ_ADMIN_CRAWL_MAX_PAGES=None, OZ_CRAWLER_MAX_PAGES="10000"):
            self.assertEqual(admin.default_crawl_max_pages(), 10000)

    def test_admin_recrawl_buttons_do_not_hardcode_small_page_limit(self) -> None:
        html = render_admin_template(
            {
                "csrf": "csrf",
                "snapshot": empty_snapshot(),
                "catalog": [
                    {
                        "vendor": "vercel",
                        "library": "next.js",
                        "version": "15",
                        "description": "Next docs",
                        "source_urls": ["https://nextjs.org/docs"],
                    }
                ],
                "index_requests": [],
                "telemetry": [],
                "crawler_jobs": [],
                "aggregated_requests": [
                    {
                        "vendor": "vercel",
                        "library_name": "next.js",
                        "source_url": "https://nextjs.org/docs",
                        "count": 1,
                        "requesting_user": "user@example.com",
                    }
                ],
                "catalog_health": [],
                "zero_result_queries": [],
                "crawl_max_pages": 10000,
                "crawl_recrawl_interval_hours": 24,
                "crawl_concurrent_requests": 6,
            }
        )

        self.assertIn('name="max_pages" type="number" value="10000"', html)
        self.assertIn('name="max_pages" value="10000"', html)
        self.assertNotIn('name="max_pages" value="128"', html)


def empty_snapshot() -> dict[str, list[dict[str, object]]]:
    keys = [
        "usage_events",
        "users",
        "embedding_jobs",
        "quality_runs",
        "eval_runs",
        "search_quality_runs",
        "ops_alerts",
        "backup_runs",
        "system_checks",
        "slo_reports",
        "audit_logs",
        "freshness_policies",
        "library_profiles",
        "promotions",
        "pack_builds",
        "admin_actions",
        "crawl_job_logs",
        "crawler_jobs",
        "index_requests",
        "telemetry",
    ]
    return {key: [] for key in keys}


if __name__ == "__main__":
    unittest.main()
