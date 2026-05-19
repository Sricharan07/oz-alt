#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "packages" / "oz-crawler" / "src"))

from oz_crawler.profiles import load_profile  # noqa: E402
from oz_crawler.validation import validate_fixture  # noqa: E402


def main() -> int:
    parser = argparse.ArgumentParser(description="Audit registry fixtures for production index quality invariants.")
    parser.add_argument("--repo-root", type=Path, default=Path("."))
    parser.add_argument("--catalog", default="registry/catalog.json")
    parser.add_argument("--fail-on-warning", action="store_true")
    args = parser.parse_args()

    repo = args.repo_root.resolve()
    catalog_path = repo / args.catalog
    if not catalog_path.exists():
        raise SystemExit(f"catalog not found: {catalog_path}")
    catalog_data = json.loads(catalog_path.read_text(encoding="utf-8"))
    catalog = catalog_data.get("libraries", catalog_data) if isinstance(catalog_data, dict) else catalog_data
    if not isinstance(catalog, list):
        raise SystemExit("catalog must be a list or an object with a libraries list")
    rows: list[dict[str, Any]] = []
    passed = True
    for entry in catalog:
        vendor = str(entry["vendor"])
        library = str(entry["library"])
        version = str(entry["version"])
        fixture = repo / str(entry.get("fixture_path") or f"registry/fixtures/{vendor}/{library}/{version}")
        profile = load_profile(repo / "registry", vendor, library)
        result = validate_fixture(fixture, profile)
        row = {
            "library": f"{vendor}/{library}",
            "version": version,
            "fixture": fixture.relative_to(repo).as_posix(),
            "passed": result.passed,
            "errors": result.errors,
            "warnings": result.warnings,
            "metrics": result.metrics,
        }
        rows.append(row)
        if not result.passed or (args.fail_on_warning and result.warnings):
            passed = False

    summary = {
        "passed": passed,
        "libraries": len(rows),
        "failed": [row for row in rows if not row["passed"]],
        "rows": rows,
    }
    print(json.dumps(summary, indent=2, sort_keys=True))
    return 0 if passed else 1


if __name__ == "__main__":
    raise SystemExit(main())
