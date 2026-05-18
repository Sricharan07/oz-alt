#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import statistics
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import Any
from urllib import request


def main() -> int:
    parser = argparse.ArgumentParser(description="Run a small retrieval load test against an Oz API deployment.")
    parser.add_argument("--url", default="https://api.tryoz.dev/search")
    parser.add_argument("--query", default="middleware cookies authentication")
    parser.add_argument("--library", default="vercel/next.js")
    parser.add_argument("--requests", type=int, default=100)
    parser.add_argument("--concurrency", type=int, default=10)
    parser.add_argument("--token", default="")
    args = parser.parse_args()

    started = time.perf_counter()
    with ThreadPoolExecutor(max_workers=max(1, args.concurrency)) as pool:
        futures = [pool.submit(call_search, args) for _ in range(max(1, args.requests))]
        results = [future.result() for future in as_completed(futures)]
    elapsed = time.perf_counter() - started
    latencies = sorted(result["latency_ms"] for result in results)
    statuses: dict[int, int] = {}
    for result in results:
        statuses[int(result["status"])] = statuses.get(int(result["status"]), 0) + 1
    summary = {
        "requests": len(results),
        "concurrency": args.concurrency,
        "elapsed_seconds": round(elapsed, 3),
        "rps": round(len(results) / elapsed, 3) if elapsed else 0,
        "statuses": statuses,
        "latency_ms": {
            "p50": percentile(latencies, 50),
            "p95": percentile(latencies, 95),
            "p99": percentile(latencies, 99),
            "max": round(max(latencies), 3) if latencies else 0,
        },
    }
    print(json.dumps(summary, indent=2, sort_keys=True))
    return 0 if all(status < 500 for status in statuses) else 1


def call_search(args: argparse.Namespace) -> dict[str, Any]:
    payload = json.dumps(
        {
            "query": args.query,
            "library_scope": args.library,
            "max_results": 5,
            "project_fingerprint": "load-test",
        }
    ).encode("utf-8")
    headers = {"Content-Type": "application/json", "x-oz-debug": "1"}
    if args.token:
        headers["Authorization"] = f"Bearer {args.token}"
    req = request.Request(args.url, data=payload, headers=headers, method="POST")
    started = time.perf_counter()
    try:
        with request.urlopen(req, timeout=10) as response:
            response.read()
            status = int(response.status)
    except Exception as exc:
        status = getattr(getattr(exc, "fp", None), "status", 599)
    return {"status": status, "latency_ms": round((time.perf_counter() - started) * 1000, 3)}


def percentile(values: list[float], p: int) -> float:
    if not values:
        return 0.0
    if len(values) == 1:
        return round(values[0], 3)
    return round(statistics.quantiles(values, n=100, method="inclusive")[p - 1], 3)


if __name__ == "__main__":
    raise SystemExit(main())
