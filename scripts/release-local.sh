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

os="$(uname -s | tr '[:upper:]' '[:lower:]')"
arch="$(uname -m)"
case "$os-$arch" in
  darwin-arm64|darwin-aarch64) target="darwin-arm64" ;;
  darwin-x86_64) target="darwin-x64" ;;
  linux-aarch64|linux-arm64) target="linux-arm64" ;;
  linux-x86_64) target="linux-x64" ;;
  *) target="$os-$arch" ;;
esac

archive="dist/oz-$target.tar.gz"
tar -C "$dist_dir" -czf "$archive" oz README.md PRD.md
sha="$(shasum -a 256 "$archive" | awk '{print $1}')"
printf '%s  %s\n' "$sha" "$(basename "$archive")" > "$archive.sha256"

mkdir -p dist/homebrew
python3 - "$version" "$target" "$sha" > dist/homebrew/oz.rb <<'PY'
import sys

version, target, sha = sys.argv[1:4]
print(f'''class Oz < Formula
  desc "Version-pinned documentation registry CLI for coding agents"
  homepage "https://github.com/oz-docs/oz"
  url "https://github.com/oz-docs/oz/releases/download/v{version}/oz-{target}.tar.gz"
  sha256 "{sha}"
  version "{version}"
  license "MIT"

  def install
    bin.install "oz"
  end

  test do
    system "#{{bin}}/oz", "--help"
  end
end''')
PY

echo "wrote $archive"
echo "wrote $archive.sha256"
echo "wrote dist/homebrew/oz.rb"
