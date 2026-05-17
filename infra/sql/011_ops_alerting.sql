create table if not exists ops_alerts (
  id uuid primary key default gen_random_uuid(),
  fingerprint text not null unique,
  severity text not null,
  status text not null default 'open',
  title text not null,
  body text not null,
  metadata_json jsonb not null default '{}'::jsonb,
  delivery_status text,
  delivery_error text,
  delivered_at timestamptz,
  resolved_at timestamptz,
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now()
);

alter table ops_alerts
  drop constraint if exists ops_alerts_severity_check;

alter table ops_alerts
  add constraint ops_alerts_severity_check
  check (severity in ('info', 'warning', 'critical'));

alter table ops_alerts
  drop constraint if exists ops_alerts_status_check;

alter table ops_alerts
  add constraint ops_alerts_status_check
  check (status in ('open', 'resolved'));

create index if not exists ops_alerts_status_created_idx
  on ops_alerts(status, created_at desc);

create table if not exists slo_reports (
  id uuid primary key default gen_random_uuid(),
  window_start timestamptz not null,
  window_end timestamptz not null,
  passed boolean not null,
  api_health_ok_rate double precision not null,
  search_quality_pass_rate double precision not null,
  crawler_success_rate double precision not null,
  pack_signature_coverage double precision not null,
  backup_fresh boolean not null,
  metrics jsonb not null default '{}'::jsonb,
  created_at timestamptz not null default now()
);

create index if not exists slo_reports_created_idx
  on slo_reports(created_at desc);
