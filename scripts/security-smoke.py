#!/usr/bin/env python3
from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "packages" / "oz-crawler" / "src"))

from oz_crawler.security import UnsafeCrawlerUrl, assert_public_http_url, public_address  # noqa: E402


def main() -> int:
    blocked = [
        "http://127.0.0.1/docs",
        "http://localhost/docs",
        "http://10.0.0.1/docs",
        "http://169.254.169.254/latest/meta-data",
        "http://[::1]/docs",
        "http://[fe80::1]/docs",
    ]
    for url in blocked:
        try:
            assert_public_http_url(url)
        except UnsafeCrawlerUrl:
            continue
        raise SystemExit(f"unsafe crawler URL was not blocked: {url}")

    assert public_address("8.8.8.8")
    assert not public_address("127.0.0.1")
    assert not public_address("169.254.169.254")
    assert not public_address("10.0.0.1")
    assert_public_http_url("https://docs.python.org/3/")
    print("security smoke ok")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
