#!/usr/bin/env bash
set -euo pipefail

repo_root="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$repo_root"

version="${1:-dev}"
repo="${OZ_REPO:-Sricharan07/oz}"
dist_dir="dist/oz-$version"
mkdir -p "$dist_dir"

cargo build --release -p oz
cp target/release/oz "$dist_dir/oz"

os="$(uname -s | tr '[:upper:]' '[:lower:]')"
arch="$(uname -m)"
case "$os-$arch" in
  darwin-arm64|darwin-aarch64) target="darwin-arm64" ;;
  darwin-x86_64) target="darwin-x64" ;;
  linux-aarch64|linux-arm64) target="linux-arm64" ;;
  linux-x86_64) target="linux-x64" ;;
  *) target="$os-$arch" ;;
esac

binary_asset="dist/oz-$target"
cp "$dist_dir/oz" "$binary_asset"
chmod 0755 "$binary_asset"
binary_sha="$(shasum -a 256 "$binary_asset" | awk '{print $1}')"
printf '%s  %s\n' "$binary_sha" "$(basename "$binary_asset")" > "$binary_asset.sha256"

archive="dist/oz-$target.tar.gz"
tar -C "$dist_dir" -czf "$archive" oz
sha="$(shasum -a 256 "$archive" | awk '{print $1}')"
printf '%s  %s\n' "$sha" "$(basename "$archive")" > "$archive.sha256"

mkdir -p dist/homebrew
python3 - "$version" "$target" "$sha" "$repo" > dist/homebrew/oz.rb <<'PY'
import sys

version, target, sha, repo = sys.argv[1:5]
print(f'''class Oz < Formula
  desc "Version-pinned documentation registry CLI for coding agents"
  homepage "https://github.com/{repo}"
  url "https://github.com/{repo}/releases/download/v{version}/oz-{target}.tar.gz"
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
echo "wrote $binary_asset"
echo "wrote $binary_asset.sha256"
echo "wrote dist/homebrew/oz.rb"
