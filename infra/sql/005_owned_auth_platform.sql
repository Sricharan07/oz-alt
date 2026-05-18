alter table users
  add column if not exists email text,
  add column if not exists name text,
  add column if not exists role text not null default 'user',
  add column if not exists disabled_at timestamptz;

create unique index if not exists users_email_unique
  on users (lower(email))
  where email is not null;

alter table users
  drop constraint if exists users_role_check;

alter table users
  add constraint users_role_check check (role in ('user', 'admin'));

create table if not exists web_sessions (
  id uuid primary key default gen_random_uuid(),
  user_id uuid not null references users(id) on delete cascade,
  session_hash text not null unique,
  expires_at timestamptz not null,
  revoked_at timestamptz,
  created_at timestamptz not null default now()
);

create index if not exists web_sessions_user_id_idx on web_sessions(user_id);
create index if not exists web_sessions_expires_at_idx on web_sessions(expires_at);

create table if not exists device_codes (
  id uuid primary key default gen_random_uuid(),
  user_code_hash text not null unique,
  device_code_hash text not null unique,
  user_id uuid references users(id) on delete cascade,
  status text not null default 'pending',
  expires_at timestamptz not null,
  created_at timestamptz not null default now(),
  approved_at timestamptz,
  denied_at timestamptz,
  consumed_at timestamptz
);

alter table device_codes
  add column if not exists ip_hash text;

alter table device_codes
  drop constraint if exists device_codes_status_check;

alter table device_codes
  add constraint device_codes_status_check
  check (status in ('pending', 'approved', 'denied', 'expired', 'consumed'));

create index if not exists device_codes_expires_at_idx on device_codes(expires_at);
create index if not exists device_codes_user_id_idx on device_codes(user_id);
create index if not exists device_codes_ip_hash_idx on device_codes(ip_hash);

create table if not exists cli_refresh_tokens (
  id uuid primary key default gen_random_uuid(),
  user_id uuid not null references users(id) on delete cascade,
  token_hash text not null unique,
  machine_id text,
  expires_at timestamptz not null,
  revoked_at timestamptz,
  last_used_at timestamptz,
  created_at timestamptz not null default now()
);

create index if not exists cli_refresh_tokens_user_id_idx on cli_refresh_tokens(user_id);
create index if not exists cli_refresh_tokens_expires_at_idx on cli_refresh_tokens(expires_at);

create table if not exists auth_audit_logs (
  id bigserial primary key,
  user_id uuid references users(id) on delete set null,
  action text not null,
  ip_hash text,
  user_agent text,
  metadata_json jsonb not null default '{}'::jsonb,
  created_at timestamptz not null default now()
);

create index if not exists auth_audit_logs_user_id_idx on auth_audit_logs(user_id);
create index if not exists auth_audit_logs_created_at_idx on auth_audit_logs(created_at);

create table if not exists usage_events (
  id bigserial primary key,
  user_id uuid references users(id) on delete set null,
  event text not null,
  library text,
  query_length integer,
  result_count integer,
  project_fingerprint_hash text,
  properties jsonb not null default '{}'::jsonb,
  created_at timestamptz not null default now()
);

create index if not exists usage_events_user_id_idx on usage_events(user_id);
create index if not exists usage_events_created_at_idx on usage_events(created_at);
create index if not exists usage_events_event_idx on usage_events(event);

alter table crawler_jobs
  add column if not exists requested_by uuid references users(id) on delete set null,
  add column if not exists version text not null default 'latest',
  add column if not exists queue_message_id text,
  add column if not exists fetcher text,
  add column if not exists concurrent_requests integer,
  add column if not exists download_delay double precision,
  add column if not exists robots_txt boolean,
  add column if not exists pack_key text,
  add column if not exists ref_sha text;

create index if not exists crawler_jobs_requested_by_idx on crawler_jobs(requested_by);
create index if not exists crawler_jobs_status_idx on crawler_jobs(status);
create index if not exists crawler_jobs_queued_at_idx on crawler_jobs(queued_at);

create table if not exists admin_action_logs (
  id bigserial primary key,
  user_id uuid references users(id) on delete set null,
  action text not null,
  target_type text,
  target text,
  metadata_json jsonb not null default '{}'::jsonb,
  created_at timestamptz not null default now()
);

create index if not exists admin_action_logs_user_id_idx on admin_action_logs(user_id);
create index if not exists admin_action_logs_created_at_idx on admin_action_logs(created_at);

create table if not exists catalog_promotions (
  id bigserial primary key,
  vendor text not null,
  library text not null,
  version text not null,
  ref_sha text,
  pack_key text,
  source_url text,
  job_id bigint references crawler_jobs(id) on delete set null,
  quality_json jsonb not null default '{}'::jsonb,
  promoted_at timestamptz not null default now()
);

create index if not exists catalog_promotions_library_idx
  on catalog_promotions(vendor, library, version, promoted_at desc);

create table if not exists freshness_policies (
  id bigserial primary key,
  vendor text not null,
  library text not null,
  version text not null default 'latest',
  source_url text not null,
  recrawl_interval_hours integer not null default 24,
  enabled boolean not null default true,
  created_by uuid references users(id) on delete set null,
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now(),
  unique (vendor, library, version)
);

create index if not exists freshness_policies_enabled_idx on freshness_policies(enabled);
