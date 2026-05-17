#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json

from prod_smoke_support import cleanup_paths, configure_cli, create_cli_auth, npm_install, run, smoke_env, temp_workspace


def main() -> int:
    parser = argparse.ArgumentParser(description="Run the production beta install/login/pull/search smoke test.")
    parser.add_argument("--app-url", default="https://app.tryoz.dev")
    parser.add_argument("--api-url", default="https://api.tryoz.dev")
    parser.add_argument("--library", default="facebook/react")
    parser.add_argument("--query", default="useEffect cleanup dependency array")
    parser.add_argument("--grep", default="cleanup|dependency")
    args = parser.parse_args()

    tmp_home, tmp_project, tmp_install = temp_workspace("oz-beta")
    try:
        oz = npm_install(tmp_install)
        auth = create_cli_auth(args.app_url, args.api_url)
        env = smoke_env(tmp_home)
        configure_cli(oz, args.api_url, auth, env)
        run([str(oz), "--version"], env=env)
        run([str(oz), "init"], cwd=tmp_project, env=env)
        run([str(oz), "doctor"], cwd=tmp_project, env=env)
        run([str(oz), "pull", args.library], cwd=tmp_project, env=env)
        search = run([str(oz), "search", args.query, args.library], cwd=tmp_project, env=env)
        if ".codo/vendors/" not in search:
            raise SystemExit("search did not return materialized .codo paths")
        grep = run(["rg", "-n", "-m", "20", "--glob", "!_chunks.jsonl", args.grep, ".codo/vendors"], cwd=tmp_project, env=env)
        if not grep.strip():
            raise SystemExit("rg did not find expected documentation content")
        print(json.dumps({"ok": True, "email": auth["email"], "project": str(tmp_project)}, indent=2))
        return 0
    finally:
        cleanup_paths(tmp_home, tmp_project, tmp_install)


if __name__ == "__main__":
    raise SystemExit(main())
