#!/usr/bin/env bash
set -euo pipefail

limit="${1:-1000}"
failed=0

while IFS= read -r -d '' path; do
  lines="$(wc -l < "$path" | tr -d ' ')"
  if (( lines > limit )); then
    printf '%s %s\n' "$lines" "$path" >&2
    failed=1
  fi
done < <(
  find . \
    -path './.git' -prune -o \
    -path './.codo' -prune -o \
    -path './target' -prune -o \
    -path './dist' -prune -o \
    -path './third_party' -prune -o \
    -path './infra/cdk/node_modules' -prune -o \
    -path './infra/cdk/cdk.out' -prune -o \
    -type f \( \
      -name '*.rs' -o \
      -name '*.py' -o \
      -name '*.ts' -o \
      -name '*.tsx' -o \
      -name '*.js' -o \
      -name '*.jsx' -o \
      -name '*.html' -o \
      -name '*.sh' \
    \) -print0
)

if (( failed )); then
  echo "code files above ${limit} lines" >&2
  exit 1
fi

echo "line-count check ok: no first-party code file exceeds ${limit} lines"
