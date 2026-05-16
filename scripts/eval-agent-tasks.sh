#!/usr/bin/env bash
set -euo pipefail

repo_root="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$repo_root"

cargo build -p oz >/dev/null

tmp_home="$(mktemp -d)"
trap 'rm -rf "$tmp_home"' EXIT

oz() {
  OZ_DISABLE_KEYCHAIN=1 HOME="$tmp_home" target/debug/oz "$@"
}

oz registry build-packs >/dev/null
oz init >/dev/null
rm -rf .codo/vendors

tasks=(
  "vercel/next.js|middleware jwt cookies"
  "stripe/stripe|webhook signature checkout session"
  "prisma/prisma|schema migrate relation client"
  "facebook/react|state effect component transition"
  "tailwindlabs/tailwindcss|utility class responsive theme"
  "tiangolo/fastapi|dependency response model route"
  "django/django|model view middleware migration"
  "expressjs/express|router middleware request response"
  "honojs/hono|route middleware context request"
  "openai/openai-node|client chat completions streaming"
)

passed=0
for task in "${tasks[@]}"; do
  scope="${task%%|*}"
  query="${task#*|}"
  output="$(oz search "$query" "$scope" --json)"
  count="$(python3 -c 'import json,sys; print(len(json.load(sys.stdin)["results"]))' <<<"$output")"
  if [[ "$count" -lt 1 ]]; then
    echo "eval failed: ${scope} query returned no paths" >&2
    exit 1
  fi
  passed=$((passed + 1))
done

echo "agent task eval ok: ${passed}/${#tasks[@]}"
