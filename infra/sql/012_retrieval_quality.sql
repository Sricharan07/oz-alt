drop index if exists chunks_embedding_idx;

alter table chunks
  alter column embedding type vector(1024) using null,
  add column if not exists parent_chunk_id bigint references chunks(id) on delete set null,
  add column if not exists chunk_key text,
  add column if not exists parent_chunk_key text,
  add column if not exists token_count integer not null default 0,
  add column if not exists source_anchor text,
  add column if not exists embedding_model text,
  add column if not exists embedding_dimensions integer,
  add column if not exists dedupe_cluster_id bigint,
  add column if not exists dedupe_canonical boolean not null default true;

alter table library_versions
  add column if not exists benchmark_score double precision not null default 0;

create table if not exists dedupe_clusters (
  id bigserial primary key,
  version_id bigint not null references library_versions(id) on delete cascade,
  cluster_key text not null,
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

create index if not exists chunks_embedding_idx on chunks using hnsw (embedding vector_cosine_ops);
create index if not exists chunks_parent_idx on chunks(parent_chunk_id);
create index if not exists chunks_chunk_key_idx on chunks(version_id, chunk_key);
create index if not exists chunks_parent_key_idx on chunks(version_id, parent_chunk_key);
create index if not exists chunks_token_count_idx on chunks(version_id, token_count);
create index if not exists chunks_source_anchor_hash_idx on chunks(version_id, md5(coalesce(source_anchor, '')));
create index if not exists chunks_dedupe_canonical_idx on chunks(version_id, dedupe_canonical);
create index if not exists chunks_content_api_reference_idx on chunks(version_id, path) where content_type = 'api_reference';
create index if not exists chunks_content_code_example_idx on chunks(version_id, path) where content_type = 'code_example';
create index if not exists chunks_content_prose_idx on chunks(version_id, path) where content_type = 'prose';
create index if not exists chunks_content_config_idx on chunks(version_id, path) where content_type = 'config';
create index if not exists chunks_content_cli_idx on chunks(version_id, path) where content_type = 'cli';
create index if not exists chunks_content_error_ref_idx on chunks(version_id, path) where content_type = 'error_ref';
create index if not exists dedupe_clusters_version_idx on dedupe_clusters(version_id);
create index if not exists trust_scores_value_idx on trust_scores(value desc);
create index if not exists library_versions_benchmark_idx on library_versions(benchmark_score desc);

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
