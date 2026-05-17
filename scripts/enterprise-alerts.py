#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import subprocess
import sys
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "packages" / "oz-api" / "src"))
sys.path.insert(0, str(ROOT / "scripts"))

from ops_notifier import deliver_alert  # noqa: E402
from oz_api.ops import record_ops_alert, resolve_ops_alerts  # noqa: E402


def main() -> int:
    parser = argparse.ArgumentParser(description="Run enterprise checks and open/resolve operational alerts.")
    parser.add_argument("--api-url", default="https://api.tryoz.dev")
    parser.add_argument("--require-search-quality", action="store_true")
    parser.add_argument("--require-recent-backup-hours", type=int, default=30)
    args = parser.parse_args()

    result = run_enterprise_checks(args)
    failed = [row for row in result.get("checks", []) if row.get("status") != "ok"]
    if not failed:
        resolved = resolve_ops_alerts("enterprise_readiness:")
        print(json.dumps({"passed": True, "resolved_alerts": resolved}, sort_keys=True))
        return 0

    title = f"Oz enterprise readiness failed: {', '.join(str(row['name']) for row in failed)}"
    payload = {
        "service": "oz",
        "severity": "critical",
        "title": title,
        "failed_checks": failed,
        "passed": False,
    }
    delivery_status, delivery_error = deliver_alert(payload)
    record_ops_alert(
        fingerprint="enterprise_readiness:current",
        severity="critical",
        title=title,
        body=json.dumps(failed, indent=2, sort_keys=True),
        metadata={"failed_checks": failed},
        delivery_status=delivery_status,
        delivery_error=delivery_error,
    )
    print(json.dumps({"passed": False, "delivery_status": delivery_status, "failed_checks": failed}, sort_keys=True))
    return 1


def run_enterprise_checks(args: argparse.Namespace) -> dict[str, Any]:
    command = [
        sys.executable,
        str(ROOT / "scripts" / "enterprise-checks.py"),
        "--api-url",
        args.api_url,
        "--require-recent-backup-hours",
        str(args.require_recent_backup_hours),
    ]
    if args.require_search_quality:
        command.append("--require-search-quality")
    completed = subprocess.run(command, cwd=ROOT, text=True, capture_output=True, check=False)
    if completed.stdout:
        print(completed.stdout, end="")
    if completed.stderr:
        print(completed.stderr, file=sys.stderr, end="")
    try:
        return json.loads(completed.stdout)
    except json.JSONDecodeError:
        return {
            "passed": False,
            "checks": [
                {
                    "name": "enterprise_checks_process",
                    "status": "fail",
                    "message": completed.stderr or completed.stdout or "enterprise checks did not return JSON",
                }
            ],
        }


if __name__ == "__main__":
    raise SystemExit(main())
