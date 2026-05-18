create table if not exists audit_retention_runs (
  id bigserial primary key,
  status text not null,
  export_key text,
  auth_rows integer not null default 0,
  admin_rows integer not null default 0,
  retention_days integer not null,
  started_at timestamptz not null default now(),
  finished_at timestamptz,
  last_error text,
  check (status in ('started', 'exported', 'pruned', 'failed'))
);

create index if not exists audit_retention_runs_started_idx
  on audit_retention_runs(started_at desc);

