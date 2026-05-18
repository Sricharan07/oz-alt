#!/usr/bin/env bash
set -euo pipefail

repo_root="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$repo_root"
pick_python() {
  if [[ -n "${PYTHON:-}" ]]; then
    printf '%s\n' "$PYTHON"
    return
  fi
  local candidate
  for candidate in python3.13 python3.12 python3.11 python3; do
    if ! command -v "$candidate" >/dev/null 2>&1; then
      continue
    fi
    if "$candidate" - <<'PY' >/dev/null 2>&1
import fastapi
import uvicorn
PY
    then
      command -v "$candidate"
      return
    fi
  done
  echo "No Python interpreter with fastapi and uvicorn is available." >&2
  echo "Install the API package first: python3 -m pip install -e packages/oz-api -e packages/oz-crawler" >&2
  exit 1
}
PYTHON="$(pick_python)"

cargo test --workspace
"$PYTHON" -m py_compile packages/oz-crawler/src/oz_crawler/*.py packages/oz-api/src/oz_api/*.py scripts/*.py
"$PYTHON" scripts/index-registry-to-db.py --dry-run >/dev/null
cargo build -p oz

tmp_home="$(mktemp -d)"
remote_home="$(mktemp -d)"
trap 'rm -rf "$tmp_home" "$remote_home"; kill "${server_pid:-}" >/dev/null 2>&1 || true' EXIT

oz() {
  OZ_DISABLE_KEYCHAIN=1 HOME="$tmp_home" target/debug/oz "$@"
}

oz dev registry build-packs
oz init
oz suggest "JWT authentication in Next.js middleware"
oz suggest "JWT authentication in Next.js middleware" --json >/dev/null
rm -rf .codo/vendors
oz search "middleware jwt cookies" vercel/next.js
oz search "middleware jwt cookies" vercel/next.js --json >/dev/null
oz status
oz doctor
oz install --codex

OZ_ENV=local PYTHONPATH=packages/oz-api/src "$PYTHON" -m oz_api.server --repo-root . --host 127.0.0.1 --port 8765 &
server_pid="$!"
sleep 1

curl -fsS http://127.0.0.1:8765/health >/dev/null
curl -fsS -X POST http://127.0.0.1:8765/suggest \
  -H 'content-type: application/json' \
  -d '{"query":"JWT authentication in Next.js middleware"}' >/dev/null
curl -fsS -X POST http://127.0.0.1:8765/search \
  -H 'content-type: application/json' \
  -d '{"query":"middleware jwt cookies","library_scope":"vercel/next.js","max_results":3}' >/dev/null
curl -fsS http://127.0.0.1:8765/refs/vercel/next.js >/dev/null
curl -fsS http://127.0.0.1:8765/admin >/dev/null

echo "local e2e ok"
