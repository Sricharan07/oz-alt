from __future__ import annotations

import argparse
from pathlib import Path

from oz_crawler.crawl import CrawlOptions, crawl_single_page
from oz_crawler.worker import run_local_worker


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Crawl documentation into an Oz registry fixture.")
    subcommands = parser.add_subparsers(dest="command", required=True)

    crawl = subcommands.add_parser("crawl", help="Crawl one documentation URL.")
    crawl.add_argument("url", help="Documentation URL to fetch.")
    crawl.add_argument("--vendor", required=True, help="Registry vendor, for example vercel.")
    crawl.add_argument("--library", required=True, help="Registry library, for example next.js.")
    crawl.add_argument("--version", required=True, help="Documentation version, for example 15.")
    crawl.add_argument(
        "--out",
        type=Path,
        default=Path("registry/fixtures"),
        help="Fixture registry root. Defaults to registry/fixtures.",
    )
    crawl.add_argument(
        "--title",
        default=None,
        help="Optional title override for README.md and INDEX.md.",
    )
    crawl.add_argument(
        "--max-pages",
        type=int,
        default=1,
        help="Maximum same-site pages to crawl. Defaults to 1.",
    )
    crawl.add_argument(
        "--fetcher",
        choices=["auto", "http", "dynamic", "stealth", "stdlib"],
        default="auto",
        help="Scrapling fetcher mode. Defaults to auto.",
    )
    crawl.add_argument("--concurrency", type=int, default=6, help="Concurrent Scrapling requests.")
    crawl.add_argument("--delay", type=float, default=0.0, help="Per-domain download delay in seconds.")
    crawl.add_argument("--no-robots", action="store_true", help="Disable Scrapling robots.txt compliance.")
    crawl.add_argument("--crawldir", type=Path, default=None, help="Scrapling checkpoint directory.")
    crawl.add_argument("--headed", action="store_true", help="Run browser fetchers headed instead of headless.")

    worker = subcommands.add_parser("worker", help="Process local crawler queue jobs.")
    worker.add_argument(
        "--queue",
        type=Path,
        default=Path("registry/admin/crawler_jobs.jsonl"),
        help="JSONL queue path written by the local API.",
    )
    worker.add_argument(
        "--registry-root",
        type=Path,
        default=Path("registry/fixtures"),
        help="Fixture registry root.",
    )
    worker.add_argument("--max-pages", type=int, default=8)
    worker.add_argument(
        "--fetcher",
        choices=["auto", "http", "dynamic", "stealth", "stdlib"],
        default="auto",
        help="Scrapling fetcher mode for queued jobs.",
    )
    worker.add_argument("--concurrency", type=int, default=6)
    worker.add_argument("--delay", type=float, default=0.0)
    worker.add_argument("--no-robots", action="store_true")

    return parser


def main() -> None:
    parser = build_parser()
    args = parser.parse_args()

    if args.command == "crawl":
        target = crawl_single_page(
            url=args.url,
            registry_root=args.out,
            vendor=args.vendor,
            library=args.library,
            version=args.version,
            title=args.title,
            max_pages=args.max_pages,
            options=CrawlOptions(
                max_pages=args.max_pages,
                fetcher=args.fetcher,
                concurrent_requests=args.concurrency,
                download_delay=args.delay,
                robots_txt=not args.no_robots,
                crawldir=args.crawldir,
                headless=not args.headed,
            ),
        )
        print(target)
    elif args.command == "worker":
        processed = run_local_worker(
            queue_path=args.queue,
            registry_root=args.registry_root,
            max_pages=args.max_pages,
            fetcher=args.fetcher,
            concurrent_requests=args.concurrency,
            download_delay=args.delay,
            robots_txt=not args.no_robots,
        )
        print(f"processed {processed} crawler jobs")


if __name__ == "__main__":
    main()
