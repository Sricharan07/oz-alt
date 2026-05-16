#!/usr/bin/env bash
set -euo pipefail

repo_root="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$repo_root"

cargo test --workspace
python3 -m py_compile lambda_entry.py packages/oz-crawler/src/oz_crawler/*.py packages/oz-api/src/oz_api/*.py
cargo build -p oz

tmp_home="$(mktemp -d)"
remote_home="$(mktemp -d)"
trap 'rm -rf "$tmp_home" "$remote_home"; kill "${server_pid:-}" >/dev/null 2>&1 || true' EXIT

oz() {
  OZ_DISABLE_KEYCHAIN=1 HOME="$tmp_home" target/debug/oz "$@"
}

oz registry build-packs
oz init
oz suggest "JWT authentication in Next.js middleware"
oz suggest "JWT authentication in Next.js middleware" --json >/dev/null
rm -rf .codo/vendors
oz search "middleware jwt cookies" vercel/next.js
oz search "middleware jwt cookies" vercel/next.js --json >/dev/null
oz status
oz doctor
oz install --codex

PYTHONPATH=packages/oz-api/src python3 -m oz_api.server --repo-root . --host 127.0.0.1 --port 8765 &
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

OZ_DISABLE_KEYCHAIN=1 HOME="$remote_home" target/debug/oz login --api-url http://127.0.0.1:8765
OZ_DISABLE_KEYCHAIN=1 HOME="$remote_home" target/debug/oz init
rm -rf .codo/vendors
OZ_DISABLE_KEYCHAIN=1 HOME="$remote_home" target/debug/oz suggest "JWT authentication in Next.js middleware"
OZ_DISABLE_KEYCHAIN=1 HOME="$remote_home" target/debug/oz suggest "JWT authentication in Next.js middleware" --json >/dev/null
OZ_DISABLE_KEYCHAIN=1 HOME="$remote_home" target/debug/oz search "middleware jwt cookies" vercel/next.js
OZ_DISABLE_KEYCHAIN=1 HOME="$remote_home" target/debug/oz search "middleware jwt cookies" vercel/next.js --json >/dev/null
OZ_DISABLE_KEYCHAIN=1 HOME="$remote_home" target/debug/oz status

echo "local e2e ok"
