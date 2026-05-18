create table if not exists maintenance_runs (
  id bigserial primary key,
  kind text not null,
  status text not null,
  started_at timestamptz not null default now(),
  finished_at timestamptz,
  metrics_json jsonb not null default '{}'::jsonb,
  last_error text,
  check (status in ('started', 'completed', 'failed'))
);

create index if not exists maintenance_runs_kind_started_idx
  on maintenance_runs(kind, started_at desc);

alter table pack_builds
  add column if not exists storage_tier text not null default 'hot',
  add column if not exists download_count bigint not null default 0,
  add column if not exists last_downloaded_at timestamptz;

alter table pack_builds
  drop constraint if exists pack_builds_storage_tier_check;

alter table pack_builds
  add constraint pack_builds_storage_tier_check
  check (storage_tier in ('hot', 'cold'));

create index if not exists pack_builds_storage_tier_idx
  on pack_builds(storage_tier, last_downloaded_at);
