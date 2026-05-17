#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
COMPOSE_FILE="${OZ_COMPOSE_FILE:-infra/docker/docker-compose.aws-ec2.yml}"
ENV_FILE="${OZ_ENV_FILE:-.env.production}"
TIMESTAMP="$(date -u +%Y%m%dT%H%M%SZ)"
TMP_DIR="$(mktemp -d)"
trap 'rm -rf "$TMP_DIR"' EXIT

if [ -f "$ROOT/$ENV_FILE" ]; then
  set -a
  # shellcheck disable=SC1090
  . "$ROOT/$ENV_FILE"
  set +a
fi

BUCKET="${OZ_BACKUP_BUCKET:-${OZ_PACKS_BUCKET:-}}"
PREFIX="${OZ_BACKUP_PREFIX:-backups/postgres}"
VERIFY_RESTORE="${OZ_VERIFY_BACKUP_RESTORE:-1}"

if [ -z "$BUCKET" ]; then
  echo "OZ_BACKUP_BUCKET or OZ_PACKS_BUCKET is required" >&2
  exit 2
fi

cd "$ROOT"

dump_file="$TMP_DIR/oz-$TIMESTAMP.dump"
backup_key="$PREFIX/oz-$TIMESTAMP.dump"

sql_escape() {
  printf "%s" "$1" | sed "s/'/''/g"
}

psql_exec() {
  docker compose -f "$COMPOSE_FILE" exec -T postgres psql -U oz -d oz "$@"
}

record_started() {
  psql_exec -At -c "insert into backup_runs (backup_key, status) values ('$(sql_escape "$backup_key")', 'started') returning id;"
}

record_failed() {
  local message="$1"
  psql_exec -c "update backup_runs set status = 'failed', finished_at = now(), last_error = '$(sql_escape "$message")' where id = $run_id;" >/dev/null || true
}

run_id="$(record_started)"

if ! docker compose -f "$COMPOSE_FILE" exec -T postgres pg_dump -U oz -d oz -Fc > "$dump_file"; then
  record_failed "pg_dump failed"
  exit 1
fi

byte_size="$(wc -c < "$dump_file" | tr -d ' ')"
sha256="$(sha256sum "$dump_file" | awk '{print $1}')"

if ! aws s3 cp "$dump_file" "s3://$BUCKET/$backup_key" >/dev/null; then
  record_failed "s3 upload failed"
  exit 1
fi

psql_exec -c "update backup_runs set status = 'uploaded', byte_size = $byte_size, sha256 = '$sha256', finished_at = now() where id = $run_id;" >/dev/null

if [ "$VERIFY_RESTORE" = "1" ]; then
  restore_db="oz_restore_check_${TIMESTAMP//[^0-9A-Za-z_]/_}"
  cleanup_restore() {
    docker compose -f "$COMPOSE_FILE" exec -T postgres dropdb -U oz --if-exists "$restore_db" >/dev/null 2>&1 || true
  }
  cleanup_restore
  docker compose -f "$COMPOSE_FILE" exec -T postgres createdb -U oz "$restore_db"
  if ! docker compose -f "$COMPOSE_FILE" exec -T postgres pg_restore -U oz -d "$restore_db" < "$dump_file" >/dev/null; then
    cleanup_restore
    record_failed "restore verification failed"
    exit 1
  fi
  if ! docker compose -f "$COMPOSE_FILE" exec -T postgres psql -U oz -d "$restore_db" -At -c "select count(*) from libraries;" >/dev/null; then
    cleanup_restore
    record_failed "restore verification query failed"
    exit 1
  fi
  cleanup_restore
  psql_exec -c "update backup_runs set status = 'verified', restore_verified_at = now() where id = $run_id;" >/dev/null
fi

echo "backup ok: s3://$BUCKET/$backup_key bytes=$byte_size sha256=$sha256"
