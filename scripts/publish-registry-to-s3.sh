#!/usr/bin/env bash
set -euo pipefail

if [[ $# -lt 1 ]]; then
  echo "usage: scripts/publish-registry-to-s3.sh s3://bucket[/prefix]" >&2
  exit 2
fi

destination="${1%/}"
repo_root="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$repo_root"

aws s3 cp registry/catalog.json "$destination/catalog.json" \
  --content-type application/json \
  --cache-control "public, max-age=300"

aws s3 sync registry/packs "$destination/packs" \
  --exclude "*" \
  --include "*.ozpack" \
  --content-type application/vnd.oz.pack \
  --cache-control "public, max-age=31536000, immutable"
