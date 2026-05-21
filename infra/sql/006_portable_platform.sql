create table if not exists library_sources (
  id bigserial primary key,
  library_id bigint not null references libraries(id) on delete cascade,
  source_url text not null,
  source_type text not null default 'website_url',
  priority integer not null default 100,
  enabled boolean not null default true,
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now(),
  unique (library_id, source_url)
);

create table if not exists library_profiles (
  id bigserial primary key,
  library_id bigint not null references libraries(id) on delete cascade unique,
  allowed_hosts jsonb not null default '[]'::jsonb,
  allowed_paths jsonb not null default '[]'::jsonb,
  denied_paths jsonb not null default '[]'::jsonb,
  source_priority jsonb not null default '[]'::jsonb,
  required_topics jsonb not null default '[]'::jsonb,
  expected_symbols jsonb not null default '[]'::jsonb,
  source_file_patterns jsonb not null default '[]'::jsonb,
  min_quality_score double precision not null default 0.35,
  min_documents integer not null default 2,
  max_junk_ratio double precision not null default 0.25,
  needs_js boolean not null default false,
  include_source_files boolean not null default false,
  target_language text not null default 'en',
  created_by uuid references users(id) on delete set null,
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now()
);

create table if not exists crawl_job_logs (
  id bigserial primary key,
  job_id bigint references crawler_jobs(id) on delete cascade,
  level text not null default 'info',
  message text not null,
  metadata_json jsonb not null default '{}'::jsonb,
  created_at timestamptz not null default now()
);

create table if not exists crawl_artifacts (
  id bigserial primary key,
  job_id bigint references crawler_jobs(id) on delete cascade,
  artifact_type text not null,
  uri text not null,
  byte_size bigint,
  created_at timestamptz not null default now()
);

create table if not exists quality_runs (
  id bigserial primary key,
  job_id bigint references crawler_jobs(id) on delete set null,
  library_id bigint references libraries(id) on delete cascade,
  version text not null default 'latest',
  passed boolean not null,
  metrics jsonb not null default '{}'::jsonb,
  errors jsonb not null default '[]'::jsonb,
  warnings jsonb not null default '[]'::jsonb,
  created_at timestamptz not null default now()
);

create table if not exists eval_runs (
  id bigserial primary key,
  library_id bigint references libraries(id) on delete cascade,
  version text not null default 'latest',
  eval_type text not null,
  passed boolean not null,
  metrics jsonb not null default '{}'::jsonb,
  created_at timestamptz not null default now()
);

create table if not exists pack_builds (
  id bigserial primary key,
  library_id bigint references libraries(id) on delete cascade,
  version text not null,
  pack_sha text not null,
  pack_key text not null,
  signature_key_id text,
  byte_size bigint,
  created_at timestamptz not null default now(),
  unique (library_id, version, pack_sha)
);

create table if not exists usage_daily (
  day date not null,
  user_id uuid references users(id) on delete cascade,
  event text not null,
  library text,
  count bigint not null default 0,
  primary key (day, user_id, event, library)
);

create index if not exists library_sources_library_idx on library_sources(library_id);
create index if not exists crawl_job_logs_job_idx on crawl_job_logs(job_id, created_at desc);
create index if not exists quality_runs_library_idx on quality_runs(library_id, version, created_at desc);
create index if not exists eval_runs_library_idx on eval_runs(library_id, version, created_at desc);
create index if not exists pack_builds_library_idx on pack_builds(library_id, version, created_at desc);
