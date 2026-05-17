#!/usr/bin/env python3
from __future__ import annotations

import argparse
import http.cookiejar
import json
import os
import secrets
import shutil
import string
import subprocess
import tempfile
import urllib.parse
import urllib.request
from pathlib import Path


def main() -> int:
    parser = argparse.ArgumentParser(description="Run the production beta install/login/pull/search smoke test.")
    parser.add_argument("--app-url", default="https://app.tryoz.dev")
    parser.add_argument("--api-url", default="https://api.tryoz.dev")
    parser.add_argument("--library", default="facebook/react")
    parser.add_argument("--query", default="useEffect cleanup dependency array")
    parser.add_argument("--grep", default="cleanup|dependency")
    args = parser.parse_args()

    tmp_home = Path(tempfile.mkdtemp(prefix="oz-beta-home-"))
    tmp_project = Path(tempfile.mkdtemp(prefix="oz-beta-project-"))
    tmp_install = Path(tempfile.mkdtemp(prefix="oz-beta-npm-"))
    try:
        npm_install(tmp_install)
        oz = tmp_install / "node_modules" / ".bin" / "oz"
        auth = create_cli_auth(args.app_url, args.api_url)
        env = os.environ.copy()
        env["HOME"] = str(tmp_home)
        env["OZ_DISABLE_KEYCHAIN"] = "1"
        run([str(oz), "config", "set", "api_url", args.api_url], env=env)
        run([str(oz), "config", "set", "auth_token", "--", auth["access_token"]], env=env)
        run([str(oz), "config", "set", "refresh_token", "--", auth["refresh_token"]], env=env)
        run([str(oz), "--version"], env=env)
        run([str(oz), "init"], cwd=tmp_project, env=env)
        run([str(oz), "doctor"], cwd=tmp_project, env=env)
        run([str(oz), "pull", args.library], cwd=tmp_project, env=env)
        search = run([str(oz), "search", args.query, args.library], cwd=tmp_project, env=env)
        if ".codo/vendors/" not in search:
            raise SystemExit("search did not return materialized .codo paths")
        grep = run(["rg", "-n", args.grep, ".codo/vendors"], cwd=tmp_project, env=env)
        if not grep.strip():
            raise SystemExit("rg did not find expected documentation content")
        print(json.dumps({"ok": True, "email": auth["email"], "project": str(tmp_project)}, indent=2))
        return 0
    finally:
        shutil.rmtree(tmp_home, ignore_errors=True)
        shutil.rmtree(tmp_install, ignore_errors=True)


def npm_install(prefix: Path) -> None:
    run(["npm", "install", "--prefix", str(prefix), "@hiringbae/oz@latest"])


def create_cli_auth(app_url: str, api_url: str) -> dict[str, str]:
    suffix = "".join(secrets.choice(string.ascii_lowercase + string.digits) for _ in range(10))
    email = f"beta-smoke+{suffix}@tryoz.dev"
    password = f"OzBetaSmoke!{suffix}9"
    jar = http.cookiejar.CookieJar()
    opener = urllib.request.build_opener(urllib.request.HTTPCookieProcessor(jar))
    form(opener, f"{app_url}/signup", {"email": email, "password": password, "confirm_password": password})
    device = json_request(opener, f"{api_url}/auth/device", {"client_name": "beta-smoke"})
    form(opener, f"{app_url}/device", {"user_code": device["user_code"], "action": "approve"})
    token = json_request(opener, f"{api_url}/auth/token", {"device_code": device["device_code"]})
    refreshed = json_request(opener, f"{api_url}/auth/refresh", {"refresh_token": token["refresh_token"]})
    return {
        "email": email,
        "access_token": refreshed["access_token"],
        "refresh_token": refreshed.get("refresh_token") or token["refresh_token"],
    }


def json_request(opener: urllib.request.OpenerDirector, url: str, payload: dict[str, object]) -> dict[str, object]:
    req = urllib.request.Request(
        url,
        data=json.dumps(payload).encode(),
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    with opener.open(req, timeout=30) as response:
        return json.loads(response.read())


def form(opener: urllib.request.OpenerDirector, url: str, payload: dict[str, str]) -> str:
    req = urllib.request.Request(
        url,
        data=urllib.parse.urlencode(payload).encode(),
        headers={"Content-Type": "application/x-www-form-urlencoded"},
        method="POST",
    )
    with opener.open(req, timeout=30) as response:
        return response.read().decode("utf-8", "replace")


def run(
    command: list[str],
    *,
    cwd: Path | None = None,
    env: dict[str, str] | None = None,
) -> str:
    result = subprocess.run(command, cwd=cwd, env=env, check=True, text=True, capture_output=True)
    output = result.stdout + result.stderr
    print(output, end="")
    return output


if __name__ == "__main__":
    raise SystemExit(main())
