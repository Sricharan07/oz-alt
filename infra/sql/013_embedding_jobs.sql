alter table crawler_jobs
  add column if not exists embedding_status text,
  add column if not exists embedding_job_id bigint,
  add column if not exists embedding_error text,
  add column if not exists embedding_started_at timestamptz,
  add column if not exists embedding_finished_at timestamptz;

create table if not exists embedding_cache (
  cache_key text primary key,
  provider text not null,
  model text not null,
  dimensions integer not null,
  input_type text not null,
  schema_version text not null,
  chunk_sha text not null,
  token_count integer not null default 0,
  embedding vector(1024) not null,
  created_at timestamptz not null default now()
);

create table if not exists embedding_jobs (
  id bigserial primary key,
  crawler_job_id bigint references crawler_jobs(id) on delete set null,
  version_id bigint references library_versions(id) on delete cascade,
  status text not null,
  mode text not null default 'sync',
  provider text not null,
  model text not null,
  dimensions integer not null,
  input_type text not null default 'document',
  schema_version text not null default 'v1',
  voyage_batch_id text,
  voyage_batch_ids jsonb not null default '[]'::jsonb,
  voyage_input_file_id text,
  voyage_output_file_id text,
  voyage_error_file_id text,
  total_chunks integer not null default 0,
  pending_chunks integer not null default 0,
  cached_chunks integer not null default 0,
  embedded_chunks integer not null default 0,
  failed_chunks integer not null default 0,
  total_tokens bigint not null default 0,
  error text,
  metadata_json jsonb not null default '{}'::jsonb,
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now(),
  submitted_at timestamptz,
  completed_at timestamptz,
  check (
    status in (
      'pending_chunks',
      'cache_lookup',
      'sync_embedding',
      'batch_submitted',
      'batch_running',
      'batch_partial',
      'batch_completed',
      'embeddings_applied',
      'dedupe_done',
      'eval_done',
      'promoted',
      'failed',
      'cancelled'
    )
  )
);

alter table embedding_jobs
  add column if not exists voyage_batch_ids jsonb not null default '[]'::jsonb;

create table if not exists embedding_job_items (
  id bigserial primary key,
  embedding_job_id bigint not null references embedding_jobs(id) on delete cascade,
  chunk_id bigint not null references chunks(id) on delete cascade,
  chunk_sha text not null,
  cache_key text not null,
  status text not null default 'pending',
  error text,
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now(),
  unique (embedding_job_id, chunk_id)
);

create index if not exists embedding_cache_chunk_sha_idx on embedding_cache(chunk_sha);
create index if not exists embedding_jobs_status_idx on embedding_jobs(status, updated_at);
create index if not exists embedding_jobs_crawler_job_idx on embedding_jobs(crawler_job_id);
create index if not exists embedding_jobs_version_idx on embedding_jobs(version_id);
create index if not exists embedding_job_items_job_status_idx on embedding_job_items(embedding_job_id, status);
create index if not exists crawler_jobs_embedding_status_idx on crawler_jobs(embedding_status);
