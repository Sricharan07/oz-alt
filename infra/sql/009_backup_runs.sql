create table if not exists backup_runs (
  id bigserial primary key,
  backup_key text not null,
  byte_size bigint not null default 0,
  sha256 text not null default '',
  status text not null default 'started',
  started_at timestamptz not null default now(),
  finished_at timestamptz,
  restore_verified_at timestamptz,
  last_error text
);

alter table backup_runs
  drop constraint if exists backup_runs_status_check;

alter table backup_runs
  add constraint backup_runs_status_check
  check (status in ('started', 'uploaded', 'verified', 'failed'));

create index if not exists backup_runs_started_idx on backup_runs(started_at desc);
