#!/usr/bin/env python3
from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path


def main() -> None:
    root = Path(__file__).resolve().parents[1]
    seeds = json.loads((root / "registry" / "seed_libraries.json").read_text(encoding="utf-8"))
    queue = root / "registry" / "admin" / "crawler_jobs.jsonl"
    queue.parent.mkdir(parents=True, exist_ok=True)
    with queue.open("a", encoding="utf-8") as file:
        for seed in seeds:
            file.write(
                json.dumps(
                    {
                        "created_at": datetime.now(timezone.utc).isoformat(),
                        "status": "queued",
                        "vendor": seed["vendor"],
                        "library_name": seed["library"],
                        "version": seed["version"],
                        "source_url": seed["source_url"],
                    },
                    sort_keys=True,
                )
                + "\n"
            )
    print(f"enqueued {len(seeds)} seed crawl jobs")


if __name__ == "__main__":
    main()

