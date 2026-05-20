create table if not exists agent_operations (
  id bigserial primary key,
  version_id bigint not null references library_versions(id) on delete cascade,
  operation_key text not null,
  product text not null default '',
  operation_name text not null,
  operation_kind text not null default 'operation',
  sdk_class text not null default '',
  sdk_method text not null default '',
  import_path text not null default '',
  language text not null default '',
  endpoint text not null default '',
  http_method text not null default '',
  route text not null default '',
  required_params jsonb not null default '[]'::jsonb,
  optional_params jsonb not null default '[]'::jsonb,
  request_schema jsonb not null default '{}'::jsonb,
  response_schema jsonb not null default '{}'::jsonb,
  errors jsonb not null default '[]'::jsonb,
  auth_requirements jsonb not null default '[]'::jsonb,
  source_urls jsonb not null default '[]'::jsonb,
  source_chunk_ids jsonb not null default '[]'::jsonb,
  confidence double precision not null default 0,
  quality_score double precision not null default 1,
  content text not null default '',
  embedding vector(1024),
  embedding_model text,
  embedding_dimensions integer,
  metadata_json jsonb not null default '{}'::jsonb,
  created_at timestamptz not null default now(),
  unique (version_id, operation_key),
  search_document tsvector generated always as (
    setweight(to_tsvector('english', coalesce(operation_name, '')), 'A') ||
    setweight(to_tsvector('english', coalesce(operation_kind, '')), 'A') ||
    setweight(to_tsvector('english', coalesce(sdk_class, '')), 'A') ||
    setweight(to_tsvector('english', coalesce(sdk_method, '')), 'A') ||
    setweight(to_tsvector('english', coalesce(endpoint, '')), 'A') ||
    setweight(to_tsvector('english', coalesce(product, '')), 'B') ||
    setweight(to_tsvector('english', coalesce(required_params::text, '')), 'B') ||
    setweight(to_tsvector('english', coalesce(optional_params::text, '')), 'B') ||
    setweight(to_tsvector('english', coalesce(content, '')), 'B')
  ) stored
);

create table if not exists agent_operation_examples (
  id bigserial primary key,
  version_id bigint not null references library_versions(id) on delete cascade,
  operation_id bigint references agent_operations(id) on delete cascade,
  example_key text not null,
  product text not null default '',
  title text not null,
  language text not null default '',
  content text not null,
  source_url text,
  source_chunk_ids jsonb not null default '[]'::jsonb,
  token_count integer not null default 0,
  quality_score double precision not null default 1,
  metadata_json jsonb not null default '{}'::jsonb,
  created_at timestamptz not null default now(),
  unique (version_id, example_key),
  search_document tsvector generated always as (
    setweight(to_tsvector('english', coalesce(title, '')), 'A') ||
    setweight(to_tsvector('english', coalesce(product, '')), 'B') ||
    setweight(to_tsvector('english', coalesce(language, '')), 'B') ||
    setweight(to_tsvector('english', coalesce(content, '')), 'B')
  ) stored
);

create table if not exists agent_recipes (
  id bigserial primary key,
  version_id bigint not null references library_versions(id) on delete cascade,
  operation_id bigint references agent_operations(id) on delete cascade,
  recipe_key text not null,
  product text not null default '',
  title text not null,
  task_kind text not null default 'operation',
  language text not null default '',
  content text not null,
  code text,
  info text not null default '',
  source_urls jsonb not null default '[]'::jsonb,
  source_chunk_ids jsonb not null default '[]'::jsonb,
  confidence double precision not null default 0,
  quality_score double precision not null default 1,
  token_count integer not null default 0,
  embedding vector(1024),
  embedding_model text,
  embedding_dimensions integer,
  metadata_json jsonb not null default '{}'::jsonb,
  created_at timestamptz not null default now(),
  unique (version_id, recipe_key),
  search_document tsvector generated always as (
    setweight(to_tsvector('english', coalesce(title, '')), 'A') ||
    setweight(to_tsvector('english', coalesce(task_kind, '')), 'A') ||
    setweight(to_tsvector('english', coalesce(product, '')), 'B') ||
    setweight(to_tsvector('english', coalesce(language, '')), 'B') ||
    setweight(to_tsvector('english', coalesce(content, '')), 'B') ||
    setweight(to_tsvector('english', coalesce(code, '')), 'B') ||
    setweight(to_tsvector('english', coalesce(info, '')), 'B')
  ) stored
);

create index if not exists agent_operations_version_kind_idx on agent_operations(version_id, operation_kind, product);
create index if not exists agent_operations_search_idx on agent_operations using gin(search_document);
create index if not exists agent_operations_source_chunks_idx on agent_operations using gin(source_chunk_ids);
create index if not exists agent_operations_embedding_idx on agent_operations using hnsw (embedding vector_cosine_ops);
create index if not exists agent_operation_examples_version_language_idx on agent_operation_examples(version_id, language, product);
create index if not exists agent_operation_examples_search_idx on agent_operation_examples using gin(search_document);
create index if not exists agent_recipes_version_kind_idx on agent_recipes(version_id, task_kind, product);
create index if not exists agent_recipes_search_idx on agent_recipes using gin(search_document);
create index if not exists agent_recipes_source_chunks_idx on agent_recipes using gin(source_chunk_ids);
create index if not exists agent_recipes_embedding_idx on agent_recipes using hnsw (embedding vector_cosine_ops);
