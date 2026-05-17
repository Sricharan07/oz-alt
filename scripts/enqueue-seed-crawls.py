#!/usr/bin/env python3
from __future__ import annotations

import json
import os
import sys
import argparse
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "packages" / "oz-api" / "src"))

from oz_api.admin_ops import approve_crawl  # noqa: E402
from oz_api.storage import RegistryStorage  # noqa: E402


def main() -> None:
    parser = argparse.ArgumentParser(description="Queue crawler jobs for registry seed libraries.")
    parser.add_argument("--repo-root", type=Path, default=Path(os.environ.get("OZ_REPO_ROOT", ROOT)))
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()

    seeds = json.loads((args.repo_root / "registry" / "seed_libraries.json").read_text(encoding="utf-8"))
    storage = RegistryStorage.from_env(args.repo_root.resolve())
    count = 0
    for seed in seeds:
        payload = {
            "vendor": seed["vendor"],
            "library_name": seed["library"],
            "version": seed["version"],
            "source_url": seed["source_url"],
            "max_pages": os.environ.get("OZ_CRAWLER_MAX_PAGES", "128"),
            "fetcher": os.environ.get("OZ_CRAWLER_FETCHER", "auto"),
            "concurrent_requests": os.environ.get("OZ_CRAWLER_CONCURRENCY", "6"),
            "download_delay": os.environ.get("OZ_CRAWLER_DELAY", "0"),
            "robots_txt": os.environ.get("OZ_CRAWLER_ROBOTS", "1"),
        }
        if not args.dry_run:
            approve_crawl(storage, payload, None)
        count += 1
    verb = "would enqueue" if args.dry_run else "enqueued"
    print(f"{verb} {count} seed crawl jobs")


if __name__ == "__main__":
    main()
