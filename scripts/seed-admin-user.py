#!/usr/bin/env python3
from __future__ import annotations

import argparse
import os
import sys
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT / "packages" / "oz-api" / "src"))

from oz_api.auth import create_password_invite, set_user_role  # noqa: E402


def main() -> int:
    parser = argparse.ArgumentParser(description="Seed or promote an Oz admin user.")
    parser.add_argument("email", help="Admin email address.")
    parser.add_argument("--invite", action="store_true", help="Print a one-time password setup link.")
    args = parser.parse_args()

    has_direct_db = bool(os.environ.get("OZ_DATABASE_URL") or os.environ.get("DATABASE_URL"))
    if not has_direct_db:
        print(
            "missing database configuration: set DATABASE_URL or OZ_DATABASE_URL",
            file=sys.stderr,
        )
        return 2

    principal = set_user_role(args.email, "admin")
    print(f"seeded admin: {principal.email} ({principal.user_id})")
    if args.invite:
        invite = create_password_invite(args.email, "admin")
        print(invite["url"])
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
