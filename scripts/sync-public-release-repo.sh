#!/usr/bin/env bash
set -euo pipefail

repo="${OZ_PUBLIC_REPO:-Sricharan07/oz}"
repo_root="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
tmp_dir="$(mktemp -d)"
trap 'rm -rf "$tmp_dir"' EXIT

if ! command -v gh >/dev/null 2>&1; then
  echo "gh CLI is required" >&2
  exit 2
fi

if ! gh repo view "$repo" >/dev/null 2>&1; then
  gh repo create "$repo" --public --description "Oz CLI public releases"
fi

gh repo clone "$repo" "$tmp_dir/repo" -- --depth 1
cd "$tmp_dir/repo"

mkdir -p scripts
cp "$repo_root/public-release/README.md" README.md
cp "$repo_root/scripts/install-release.sh" scripts/install-release.sh
chmod 0755 scripts/install-release.sh

git add README.md scripts/install-release.sh
if git diff --cached --quiet; then
  echo "public release repo already up to date: $repo"
  exit 0
fi

git commit -m "Update public installer"
git push origin HEAD
echo "synced public release repo: $repo"
