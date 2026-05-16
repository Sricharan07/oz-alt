#!/usr/bin/env bash
set -euo pipefail

repo_root="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$repo_root"

version="${1:-dev}"
dist_dir="dist/oz-$version"
mkdir -p "$dist_dir"

cargo build --release -p oz
cp target/release/oz "$dist_dir/oz"
cp README.md "$dist_dir/README.md"
cp PRD.md "$dist_dir/PRD.md"

tar -C dist -czf "dist/oz-$version-$(uname -s)-$(uname -m).tar.gz" "oz-$version"
echo "wrote dist/oz-$version-$(uname -s)-$(uname -m).tar.gz"

