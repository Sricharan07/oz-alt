#!/usr/bin/env bash
set -euo pipefail

repo_root="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$repo_root"
PYTHON="${PYTHON:-$(command -v python3.13 || command -v python3.12 || command -v python3.11 || command -v python3)}"

cargo build -p oz >/dev/null

tmp_home="$(mktemp -d)"
trap 'rm -rf "$tmp_home"' EXIT

oz() {
  OZ_DISABLE_KEYCHAIN=1 HOME="$tmp_home" target/debug/oz "$@"
}

oz dev registry build-packs >/dev/null
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
precision_total=0
precision_count=0
for task in "${tasks[@]}"; do
  scope="${task%%|*}"
  query="${task#*|}"
  output="$(oz search "$query" "$scope" --json)"
  metrics="$(OZ_EVAL_OUTPUT="$output" "$PYTHON" - "$scope" "$repo_root" <<'PY'
import json
import pathlib
import os
import sys

scope = sys.argv[1]
repo = pathlib.Path(sys.argv[2])
vendor, library = scope.split("/", 1)
data = json.loads(os.environ["OZ_EVAL_OUTPUT"])
results = data.get("results", [])
top = results[:5]
prefix = f".codo/vendors/{vendor}/{library}@"
scope_hits = sum(1 for row in top if str(row.get("path", "")).startswith(prefix))
existing = sum(1 for row in top if (repo / str(row.get("path", ""))).exists())
print(len(results), len(top), scope_hits, existing)
PY
)"
  read -r count top_count scope_hits existing_count <<<"$metrics"
  if [[ "$count" -lt 1 || "$top_count" -lt 1 ]]; then
    echo "eval failed: ${scope} query returned no paths" >&2
    exit 1
  fi
  if [[ "$existing_count" -lt "$top_count" ]]; then
    echo "eval failed: ${scope} returned non-materialized path" >&2
    exit 1
  fi
  precision_total=$((precision_total + scope_hits))
  precision_count=$((precision_count + top_count))
  passed=$((passed + 1))
done

precision_pct=$((precision_total * 100 / precision_count))
if [[ "$precision_pct" -lt 60 ]]; then
  echo "eval failed: precision@5 ${precision_pct}% is below 60%" >&2
  exit 1
fi

echo "agent task eval ok: ${passed}/${#tasks[@]} precision@5=${precision_pct}%"
