from __future__ import annotations

import http.cookiejar
import json
import os
import re
import secrets
import shutil
import string
import subprocess
import tempfile
import urllib.parse
import urllib.request
from pathlib import Path
from typing import Any


def temp_workspace(prefix: str) -> tuple[Path, Path, Path]:
    return (
        Path(tempfile.mkdtemp(prefix=f"{prefix}-home-")),
        Path(tempfile.mkdtemp(prefix=f"{prefix}-project-")),
        Path(tempfile.mkdtemp(prefix=f"{prefix}-npm-")),
    )


def smoke_env(home: Path) -> dict[str, str]:
    env = os.environ.copy()
    env["HOME"] = str(home)
    env["OZ_DISABLE_KEYCHAIN"] = "1"
    return env


def cleanup_paths(*paths: Path) -> None:
    for path in paths:
        shutil.rmtree(path, ignore_errors=True)


def npm_install(prefix: Path, package: str = "@hiringbae/oz@latest") -> Path:
    run(["npm", "install", "--prefix", str(prefix), package])
    return prefix / "node_modules" / ".bin" / "oz"


def create_cli_auth(app_url: str, api_url: str, *, label: str = "beta-smoke") -> dict[str, str]:
    suffix = "".join(secrets.choice(string.ascii_lowercase + string.digits) for _ in range(10))
    email = f"{label}+{suffix}@tryoz.dev"
    password = f"OzBetaSmoke!{suffix}9"
    jar = http.cookiejar.CookieJar()
    opener = urllib.request.build_opener(urllib.request.HTTPCookieProcessor(jar))
    form(opener, f"{app_url}/signup", {"email": email, "password": password, "confirm_password": password})
    device = json_request(opener, f"{api_url}/auth/device", {"client_name": label})
    device_page = get(opener, f"{app_url}/device?code={urllib.parse.quote(str(device['user_code']))}")
    form(
        opener,
        f"{app_url}/device",
        {"csrf": hidden_value(device_page, "csrf"), "user_code": str(device["user_code"]), "action": "approve"},
    )
    token = json_request(opener, f"{api_url}/auth/token", {"device_code": device["device_code"]})
    refreshed = json_request(opener, f"{api_url}/auth/refresh", {"refresh_token": token["refresh_token"]})
    return {
        "email": email,
        "access_token": str(refreshed["access_token"]),
        "refresh_token": str(refreshed.get("refresh_token") or token["refresh_token"]),
    }


def configure_cli(oz: Path, api_url: str, auth: dict[str, str], env: dict[str, str]) -> None:
    run([str(oz), "config", "set", "api_url", api_url], env=env)
    run([str(oz), "config", "set", "auth_token", "--", auth["access_token"]], env=env)
    run([str(oz), "config", "set", "refresh_token", "--", auth["refresh_token"]], env=env)


def json_request(opener: urllib.request.OpenerDirector, url: str, payload: dict[str, object]) -> dict[str, Any]:
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


def get(opener: urllib.request.OpenerDirector, url: str) -> str:
    with opener.open(url, timeout=30) as response:
        return response.read().decode("utf-8", "replace")


def hidden_value(html: str, name: str) -> str:
    match = re.search(rf'name="{re.escape(name)}"\s+value="([^"]*)"', html)
    if not match:
        raise SystemExit(f"missing hidden input: {name}")
    return match.group(1)


def run(
    command: list[str],
    *,
    cwd: Path | None = None,
    env: dict[str, str] | None = None,
    echo: bool = True,
) -> str:
    result = subprocess.run(command, cwd=cwd, env=env, check=True, text=True, capture_output=True)
    output = result.stdout + result.stderr
    if echo:
        print(output, end="")
    return output
