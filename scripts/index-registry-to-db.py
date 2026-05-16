#!/usr/bin/env python3
from __future__ import annotations

import sys
from pathlib import Path


def main() -> int:
    repo_root = Path(__file__).resolve().parents[1]
    sys.path.insert(0, str(repo_root / "packages" / "oz-api" / "src"))
    sys.path.insert(0, str(repo_root / "packages" / "oz-crawler" / "src"))

    from oz_api.indexer import main as indexer_main

    return indexer_main()


if __name__ == "__main__":
    raise SystemExit(main())
