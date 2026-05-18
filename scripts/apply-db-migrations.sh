#!/usr/bin/env bash
set -euo pipefail

repo_root="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$repo_root"

if [[ -z "${DATABASE_URL:-}" ]]; then
  echo "DATABASE_URL is required" >&2
  exit 2
fi

psql "$DATABASE_URL" -v ON_ERROR_STOP=1 <<'SQL'
create table if not exists schema_migrations (
  filename text primary key,
  checksum text not null,
  applied_at timestamptz not null default now()
);
SQL

for migration in infra/sql/*.sql; do
  filename="$(basename "$migration")"
  if [[ ! "$filename" =~ ^[A-Za-z0-9_.-]+$ ]]; then
    echo "unsafe migration filename: ${filename}" >&2
    exit 2
  fi
  checksum="$(python3 - "$migration" <<'PY'
from __future__ import annotations

import hashlib
import sys
from pathlib import Path

print(hashlib.sha256(Path(sys.argv[1]).read_bytes()).hexdigest())
PY
)"
  if [[ "$(psql "$DATABASE_URL" -v ON_ERROR_STOP=1 -tAc "select 1 from schema_migrations where filename = '$filename'")" == "1" ]]; then
    echo "skipping ${migration}"
    continue
  fi
  echo "applying ${migration}"
  psql "$DATABASE_URL" -v ON_ERROR_STOP=1 -f "$migration"
  psql "$DATABASE_URL" -v ON_ERROR_STOP=1 <<SQL
insert into schema_migrations(filename, checksum)
values ('$filename', '$checksum')
on conflict (filename) do update set
  checksum = excluded.checksum,
  applied_at = now();
SQL
done
