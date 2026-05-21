create extension if not exists vector;
create extension if not exists pgcrypto;

create or replace function compact_key_sql(value text)
returns text
language sql
immutable
as $$
  select regexp_replace(lower(coalesce(value, '')), '[^a-z0-9]+', '', 'g')
$$;

create or replace function compact_basename(value text)
returns text
language sql
immutable
as $$
  select compact_key_sql(regexp_replace(regexp_replace(coalesce(value, ''), '^.*/', ''), '\.[^.]+$', ''))
$$;

create or replace function content_type_score(value text)
returns double precision
language sql
immutable
as $$
  select case coalesce(value, '')
    when 'api_reference' then 0.18
    when 'code_example' then 0.14
    when 'config' then 0.10
    when 'cli' then 0.10
    when 'error_ref' then 0.12
    when 'types' then 0.10
    when 'example' then 0.08
    when 'index' then -0.16
    else 0
  end
$$;

create or replace function content_type_intent_score(value text, intent text)
returns double precision
language sql
immutable
as $$
  select case coalesce(intent, '')
    when 'code_example' then case coalesce(value, '') when 'code_example' then 0.32 when 'config' then 0.08 when 'cli' then 0.08 else 0 end
    when 'api_reference' then case coalesce(value, '') when 'api_reference' then 0.34 when 'types' then 0.16 else 0 end
    when 'error_ref' then case coalesce(value, '') when 'error_ref' then 0.36 when 'api_reference' then 0.08 else 0 end
    when 'cli' then case coalesce(value, '') when 'cli' then 0.34 when 'code_example' then 0.10 else 0 end
    when 'config' then case coalesce(value, '') when 'config' then 0.34 when 'code_example' then 0.08 else 0 end
    when 'prose' then case coalesce(value, '') when 'prose' then 0.22 when 'guide' then 0.12 else 0 end
    else 0
  end
$$;

create table if not exists vendors (
  id bigserial primary key,
  name text not null unique,
  display_name text,
  created_at timestamptz not null default now()
);

create table if not exists libraries (
  id bigserial primary key,
  vendor_id bigint not null references vendors(id) on delete cascade,
  name text not null,
  description text not null default '',
  source_url text,
  aliases jsonb not null default '[]'::jsonb,
  default_version_id bigint,
  redirected_to_library_id bigint references libraries(id) on delete set null,
  version_strategy text not null default 'semver',
  search_document tsvector generated always as (
    setweight(to_tsvector('english', coalesce(name, '')), 'A') ||
    setweight(to_tsvector('english', coalesce(aliases::text, '')), 'A') ||
    setweight(to_tsvector('english', coalesce(description, '')), 'B')
  ) stored,
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now(),
  unique (vendor_id, name)
);

create table if not exists library_versions (
  id bigserial primary key,
  library_id bigint not null references libraries(id) on delete cascade,
  version text not null,
  ref_sha text not null,
  commit_sha text,
  pack_key text,
  indexed_at timestamptz,
  last_crawled_at timestamptz,
  crawl_error_count integer not null default 0,
  pull_count bigint not null default 0,
  last_requested_at timestamptz,
  benchmark_score double precision not null default 0,
  archived_at timestamptz,
  version_rank integer,
  drift_score double precision not null default 0,
  created_at timestamptz not null default now(),
  unique (library_id, version)
);

do $$
begin
  alter table libraries
    add constraint libraries_default_version_fk
    foreign key (default_version_id) references library_versions(id) on delete set null;
exception when duplicate_object then
  null;
end
$$;

create table if not exists refs (
  id bigserial primary key,
  library_id bigint not null references libraries(id) on delete cascade,
  channel text not null default 'latest',
  version_id bigint not null references library_versions(id) on delete cascade,
  ref_sha text not null,
  updated_at timestamptz not null default now(),
  unique (library_id, channel)
);

create table if not exists commits (
  sha text primary key,
  tree_sha text not null,
  parent_sha text,
  library_id bigint not null references libraries(id) on delete cascade,
  version_id bigint not null references library_versions(id) on delete cascade,
  committed_at timestamptz not null default now()
);

create table if not exists trees (
  sha text primary key,
  children jsonb not null,
  created_at timestamptz not null default now()
);

create table if not exists blobs_meta (
  sha256 text primary key,
  byte_size bigint not null,
  content_type text,
  first_seen_at timestamptz not null default now()
);

create table if not exists source_documents (
  id bigserial primary key,
  version_id bigint not null references library_versions(id) on delete cascade,
  source_document_key text not null,
  source_type text not null default 'website_url',
  document_role text not null default 'unknown',
  canonical_url text,
  source_url text,
  path text,
  title text,
  product text not null default '',
  product_confidence double precision not null default 0,
  language text not null default '',
  content_markdown text not null default '',
  parallel_structured_json jsonb not null default '{}'::jsonb,
  content_sha text,
  raw_token_count integer not null default 0,
  clean_token_count integer not null default 0,
  chunk_coverage_ratio double precision not null default 0,
  coverage_json jsonb not null default '{}'::jsonb,
  source_priority integer not null default 50,
  discovered_from text,
  raw_artifact_key text,
  raw_object_store text,
  raw_object_sha256 text,
  metadata_json jsonb not null default '{}'::jsonb,
  etag text,
  last_modified text,
  fetched_at timestamptz not null default now(),
  created_at timestamptz not null default now(),
  unique (version_id, source_document_key)
);

create table if not exists index_tombstones (
  id bigserial primary key,
  version_id bigint not null references library_versions(id) on delete cascade,
  surface_table text not null,
  row_id bigint,
  row_key text not null,
  content_sha text,
  payload_json jsonb not null default '{}'::jsonb,
  tombstoned_at timestamptz not null default now()
);

create table if not exists chunks (
  id bigserial primary key,
  version_id bigint not null references library_versions(id) on delete cascade,
  source_document_id bigint references source_documents(id) on delete set null,
  path text not null,
  start_line integer not null default 1,
  end_line integer,
  source_url text,
  ordinal integer not null default 1,
  chunk_key text,
  chunk_sha text not null,
  content_sha text,
  heading_path jsonb not null default '[]'::jsonb,
  symbols jsonb not null default '[]'::jsonb,
  content_type text not null default 'prose',
  quality_score double precision not null default 1,
  content text not null,
  embedding vector(1024),
  parent_chunk_id bigint references chunks(id) on delete set null,
  parent_chunk_key text,
  token_count integer not null default 0,
  source_anchor text,
  contextual_prefix text not null default '',
  embedding_input_sha text,
  metadata_json jsonb not null default '{}'::jsonb,
  embedding_model text,
  embedding_dimensions integer,
  dedupe_cluster_id bigint,
  dedupe_canonical boolean not null default true,
  search_document tsvector generated always as (
    setweight(to_tsvector('english', coalesce(path, '')), 'A') ||
    setweight(to_tsvector('english', coalesce(heading_path::text, '')), 'A') ||
    setweight(to_tsvector('english', coalesce(symbols::text, '')), 'A') ||
    setweight(to_tsvector('english', coalesce(content_type, '')), 'C') ||
    setweight(to_tsvector('english', coalesce(content, '')), 'B')
  ) stored,
  created_at timestamptz not null default now(),
  unique (version_id, chunk_sha)
);

create table if not exists source_sections (
  id bigserial primary key,
  version_id bigint not null references library_versions(id) on delete cascade,
  source_document_id bigint references source_documents(id) on delete set null,
  section_key text not null,
  path text not null,
  source_url text,
  source_anchor text,
  title text not null,
  heading_path jsonb not null default '[]'::jsonb,
  document_role text not null default 'unknown',
  content_type text not null default 'prose',
  product text not null default '',
  product_confidence double precision not null default 0,
  language text not null default '',
  depth integer not null default 0,
  start_line integer not null default 1,
  end_line integer,
  content text not null,
  content_sha text,
  has_code boolean not null default false,
  has_endpoint_shape boolean not null default false,
  has_signature_shape boolean not null default false,
  token_count integer not null default 0,
  quality_score double precision not null default 1,
  metadata_json jsonb not null default '{}'::jsonb,
  created_at timestamptz not null default now(),
  unique (version_id, section_key),
  search_document tsvector generated always as (
    setweight(to_tsvector('english', coalesce(path, '')), 'A') ||
    setweight(to_tsvector('english', coalesce(title, '')), 'A') ||
    setweight(to_tsvector('english', coalesce(heading_path::text, '')), 'A') ||
    setweight(to_tsvector('english', coalesce(content_type, '')), 'C') ||
    setweight(to_tsvector('english', coalesce(content, '')), 'B')
  ) stored
);

alter table chunks
  add column if not exists source_section_id bigint references source_sections(id) on delete set null;

create table if not exists dedupe_clusters (
  id bigserial primary key,
  version_id bigint not null references library_versions(id) on delete cascade,
  cluster_key text not null,
  surface_table text not null default 'chunks',
  canonical_row_id bigint,
  member_ids_json jsonb not null default '[]'::jsonb,
  canonical_chunk_id bigint references chunks(id) on delete set null,
  member_count integer not null default 1,
  method text not null,
  created_at timestamptz not null default now(),
  unique (version_id, cluster_key)
);

create table if not exists trust_scores (
  id bigserial primary key,
  library_id bigint not null references libraries(id) on delete cascade,
  value double precision not null default 0,
  signals_json jsonb not null default '{}'::jsonb,
  calculated_at timestamptz not null default now(),
  unique (library_id)
);

create table if not exists users (
  id uuid primary key default gen_random_uuid(),
  subject text not null unique,
  telemetry_opt_out boolean not null default false,
  created_at timestamptz not null default now(),
  last_seen_at timestamptz
);

create table if not exists index_requests (
  id bigserial primary key,
  library_name text,
  vendor_hint text,
  source_url_hint text,
  requesting_user text,
  request_count integer not null default 1,
  status text not null default 'queued',
  last_error text,
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now()
);

create table if not exists telemetry_events (
  id bigserial primary key,
  event text not null,
  anonymous_user_id text,
  library_names text[] not null default '{}',
  query_length integer,
  result_count integer,
  properties jsonb not null default '{}',
  created_at timestamptz not null default now()
);

create table if not exists suggest_logs (
  id bigserial primary key,
  query_hash text not null,
  fingerprint_hash text not null,
  result_count integer not null,
  reranked boolean not null default false,
  created_at timestamptz not null default now()
);

create table if not exists crawler_jobs (
  id bigserial primary key,
  library_id bigint references libraries(id) on delete set null,
  source_url text not null,
  status text not null default 'queued',
  attempts integer not null default 0,
  max_pages integer not null default 128,
  last_error text,
  progress_json jsonb not null default '{}'::jsonb,
  dead_letter_json jsonb not null default '[]'::jsonb,
  source_stats_json jsonb not null default '{}'::jsonb,
  failure_kind text,
  queued_at timestamptz not null default now(),
  started_at timestamptz,
  finished_at timestamptz
);
