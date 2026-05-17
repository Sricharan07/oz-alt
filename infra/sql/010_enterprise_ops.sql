create table if not exists search_quality_runs (
  id bigserial primary key,
  library_id bigint references libraries(id) on delete cascade,
  version text not null default 'latest',
  eval_type text not null default 'semantic_search',
  passed boolean not null,
  precision_at_1 double precision not null default 0,
  precision_at_5 double precision not null default 0,
  mrr double precision not null default 0,
  materialization_rate double precision not null default 0,
  zero_result_rate double precision not null default 0,
  junk_top5_rate double precision not null default 0,
  metrics jsonb not null default '{}'::jsonb,
  created_at timestamptz not null default now()
);

create table if not exists system_checks (
  id bigserial primary key,
  check_name text not null,
  status text not null,
  message text not null default '',
  metadata_json jsonb not null default '{}'::jsonb,
  created_at timestamptz not null default now()
);

alter table system_checks
  drop constraint if exists system_checks_status_check;

alter table system_checks
  add constraint system_checks_status_check
  check (status in ('ok', 'warn', 'fail'));

create index if not exists search_quality_runs_library_idx
  on search_quality_runs(library_id, version, created_at desc);

create index if not exists search_quality_runs_created_idx
  on search_quality_runs(created_at desc);

create index if not exists system_checks_name_created_idx
  on system_checks(check_name, created_at desc);

create index if not exists system_checks_status_created_idx
  on system_checks(status, created_at desc);
