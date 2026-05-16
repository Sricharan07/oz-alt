#!/usr/bin/env bash
set -euo pipefail

repo="${OZ_REPO:-oz-docs/oz}"
version="${OZ_VERSION:-latest}"
install_dir="${OZ_INSTALL_DIR:-$HOME/.local/bin}"

os="$(uname -s | tr '[:upper:]' '[:lower:]')"
arch="$(uname -m)"
case "$os-$arch" in
  darwin-arm64|darwin-aarch64) asset="oz-darwin-arm64" ;;
  darwin-x86_64) asset="oz-darwin-x64" ;;
  linux-aarch64|linux-arm64) asset="oz-linux-arm64" ;;
  linux-x86_64) asset="oz-linux-x64" ;;
  msys*-x86_64|mingw*-x86_64|cygwin*-x86_64) asset="oz-win32-x64.exe" ;;
  *) echo "unsupported platform: $os-$arch" >&2; exit 1 ;;
esac

if [ "$version" = "latest" ]; then
  base_url="https://github.com/$repo/releases/latest/download"
else
  base_url="https://github.com/$repo/releases/download/v${version#v}"
fi

tmp_dir="$(mktemp -d)"
trap 'rm -rf "$tmp_dir"' EXIT

curl -fsSL "$base_url/$asset" -o "$tmp_dir/$asset"
if curl -fsSL "$base_url/$asset.sha256" -o "$tmp_dir/$asset.sha256"; then
  (cd "$tmp_dir" && shasum -a 256 -c "$asset.sha256")
fi

mkdir -p "$install_dir"
if [[ "$asset" == *.exe ]]; then
  cp "$tmp_dir/$asset" "$install_dir/oz.exe"
  chmod 0755 "$install_dir/oz.exe"
else
  cp "$tmp_dir/$asset" "$install_dir/oz"
  chmod 0755 "$install_dir/oz"
fi

echo "installed oz to $install_dir"
