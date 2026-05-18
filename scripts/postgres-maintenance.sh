#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
COMPOSE_FILE="${OZ_COMPOSE_FILE:-infra/docker/docker-compose.aws-ec2.yml}"
ENV_FILE="${OZ_ENV_FILE:-.env.production}"

if [ -f "$ROOT/$ENV_FILE" ]; then
  set -a
  # shellcheck disable=SC1090
  . "$ROOT/$ENV_FILE"
  set +a
fi

cd "$ROOT"

psql_exec() {
  if [ -n "${DATABASE_URL:-${OZ_DATABASE_URL:-}}" ] && command -v psql >/dev/null 2>&1; then
    local url="${DATABASE_URL:-${OZ_DATABASE_URL:-}}"
    psql "$url" "$@"
  else
    docker compose -f "$COMPOSE_FILE" exec -T postgres psql -U oz -d oz "$@"
  fi
}

sql_escape() {
  printf "%s" "$1" | sed "s/'/''/g"
}

record_started() {
  psql_exec -qAt -c "insert into maintenance_runs (kind, status) values ('postgres_vector_maintenance', 'started') returning id;"
}

record_failed() {
  local message="$1"
  psql_exec -c "update maintenance_runs set status = 'failed', finished_at = now(), last_error = '$(sql_escape "$message")' where id = $run_id;" >/dev/null || true
}

record_completed() {
  local metrics="$1"
  psql_exec -c "update maintenance_runs set status = 'completed', finished_at = now(), metrics_json = '$(sql_escape "$metrics")'::jsonb where id = $run_id;" >/dev/null
}

run_id="$(record_started)"

if ! psql_exec -v ON_ERROR_STOP=1 <<'SQL'
vacuum (analyze) vendors;
vacuum (analyze) libraries;
vacuum (analyze) library_versions;
vacuum (analyze) refs;
vacuum (analyze) chunks;
vacuum (analyze) embedding_cache;
SQL
then
  record_failed "vacuum analyze failed"
  exit 1
fi

reindexed=0
for index_name in chunks_embedding_idx chunks_version_embedding_idx; do
  exists="$(psql_exec -qAt -c "select to_regclass('public.${index_name}') is not null;")"
  if [ "$exists" = "t" ]; then
    if ! psql_exec -v ON_ERROR_STOP=1 -c "reindex index concurrently ${index_name};"; then
      record_failed "reindex failed for ${index_name}"
      exit 1
    fi
    reindexed=$((reindexed + 1))
  fi
done

record_completed "{\"reindexed_indexes\": $reindexed}"
echo "postgres maintenance ok: reindexed_indexes=$reindexed"
