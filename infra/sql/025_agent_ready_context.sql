alter table source_documents
  add column if not exists source_type text not null default 'website_url',
  add column if not exists document_role text not null default 'unknown',
  add column if not exists product text not null default '',
  add column if not exists product_confidence double precision not null default 0,
  add column if not exists language text not null default '',
  add column if not exists content_markdown text not null default '',
  add column if not exists parallel_structured_json jsonb not null default '{}'::jsonb,
  add column if not exists content_sha text,
  add column if not exists raw_token_count integer not null default 0,
  add column if not exists clean_token_count integer not null default 0,
  add column if not exists chunk_coverage_ratio double precision not null default 0,
  add column if not exists coverage_json jsonb not null default '{}'::jsonb,
  add column if not exists raw_object_store text,
  add column if not exists raw_object_sha256 text;

alter table source_sections
  add column if not exists document_role text not null default 'unknown',
  add column if not exists product text not null default '',
  add column if not exists product_confidence double precision not null default 0,
  add column if not exists language text not null default '',
  add column if not exists depth integer not null default 0,
  add column if not exists content_sha text,
  add column if not exists has_code boolean not null default false,
  add column if not exists has_endpoint_shape boolean not null default false,
  add column if not exists has_signature_shape boolean not null default false;

alter table chunks
  add column if not exists source_section_id bigint references source_sections(id) on delete set null,
  add column if not exists contextual_prefix text not null default '',
  add column if not exists embedding_input_sha text;

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

drop table if exists context_snippets cascade;
drop table if exists agent_operation_examples cascade;
drop table if exists agent_operations cascade;
drop table if exists agent_recipes cascade;

create table if not exists code_examples (
  id bigserial primary key,
  version_id bigint not null references library_versions(id) on delete cascade,
  source_document_id bigint references source_documents(id) on delete set null,
  source_section_id bigint references source_sections(id) on delete set null,
  example_key text not null,
  source_type text not null default 'website_url',
  document_role text not null default 'unknown',
  product text not null default '',
  product_confidence double precision not null default 0,
  language text not null default '',
  title text not null,
  description text not null default '',
  caption text not null default '',
  code text not null,
  imports_json jsonb not null default '[]'::jsonb,
  symbols_json jsonb not null default '[]'::jsonb,
  task_tags_json jsonb not null default '[]'::jsonb,
  required_env_json jsonb not null default '[]'::jsonb,
  required_params_json jsonb not null default '[]'::jsonb,
  source_url text,
  source_anchor text,
  source_chunk_ids_json jsonb not null default '[]'::jsonb,
  token_count integer not null default 0,
  quality_score double precision not null default 1,
  confidence double precision not null default 0,
  metadata_json jsonb not null default '{}'::jsonb,
  embedding vector(1024),
  embedding_model text,
  embedding_dimensions integer,
  dedupe_cluster_id bigint,
  dedupe_canonical boolean not null default true,
  created_at timestamptz not null default now(),
  unique(version_id, example_key),
  search_document tsvector generated always as (
    setweight(to_tsvector('english', coalesce(title, '')), 'A') ||
    setweight(to_tsvector('english', coalesce(description, '')), 'A') ||
    setweight(to_tsvector('english', coalesce(caption, '')), 'A') ||
    setweight(to_tsvector('english', coalesce(product, '')), 'B') ||
    setweight(to_tsvector('english', coalesce(language, '')), 'B') ||
    setweight(to_tsvector('english', coalesce(task_tags_json::text, '')), 'A') ||
    setweight(to_tsvector('english', coalesce(symbols_json::text, '')), 'A') ||
    setweight(to_tsvector('english', coalesce(code, '')), 'B')
  ) stored
);

create table if not exists api_operations (
  id bigserial primary key,
  version_id bigint not null references library_versions(id) on delete cascade,
  source_document_id bigint references source_documents(id) on delete set null,
  source_section_id bigint references source_sections(id) on delete set null,
  operation_key text not null,
  product text not null default '',
  product_confidence double precision not null default 0,
  operation_id text not null default '',
  operation_name text not null,
  operation_kind text not null default 'operation',
  http_method text not null default '',
  endpoint text not null default '',
  route text not null default '',
  tags_json jsonb not null default '[]'::jsonb,
  summary text not null default '',
  description text not null default '',
  required_params_json jsonb not null default '[]'::jsonb,
  optional_params_json jsonb not null default '[]'::jsonb,
  request_schema_json jsonb not null default '{}'::jsonb,
  response_schema_json jsonb not null default '{}'::jsonb,
  errors_json jsonb not null default '[]'::jsonb,
  auth_requirements_json jsonb not null default '[]'::jsonb,
  source_url text,
  source_anchor text,
  source_chunk_ids_json jsonb not null default '[]'::jsonb,
  token_count integer not null default 0,
  quality_score double precision not null default 1,
  confidence double precision not null default 0,
  metadata_json jsonb not null default '{}'::jsonb,
  embedding vector(1024),
  embedding_model text,
  embedding_dimensions integer,
  dedupe_cluster_id bigint,
  dedupe_canonical boolean not null default true,
  created_at timestamptz not null default now(),
  unique(version_id, operation_key),
  search_document tsvector generated always as (
    setweight(to_tsvector('english', coalesce(operation_id, '')), 'A') ||
    setweight(to_tsvector('english', coalesce(operation_name, '')), 'A') ||
    setweight(to_tsvector('english', coalesce(operation_kind, '')), 'A') ||
    setweight(to_tsvector('english', coalesce(http_method, '') || ' ' || coalesce(endpoint, '')), 'A') ||
    setweight(to_tsvector('english', coalesce(tags_json::text, '')), 'B') ||
    setweight(to_tsvector('english', coalesce(product, '')), 'B') ||
    setweight(to_tsvector('english', coalesce(required_params_json::text, '')), 'B') ||
    setweight(to_tsvector('english', coalesce(optional_params_json::text, '')), 'B') ||
    setweight(to_tsvector('english', coalesce(summary, '') || ' ' || coalesce(description, '')), 'B')
  ) stored
);

create table if not exists sdk_methods (
  id bigserial primary key,
  version_id bigint not null references library_versions(id) on delete cascade,
  source_document_id bigint references source_documents(id) on delete set null,
  source_section_id bigint references source_sections(id) on delete set null,
  method_key text not null,
  product text not null default '',
  product_confidence double precision not null default 0,
  language text not null default '',
  import_path text not null default '',
  module_path text not null default '',
  sdk_class text not null default '',
  sdk_method text not null default '',
  symbol_name text not null,
  signature text not null default '',
  description text not null default '',
  required_params_json jsonb not null default '[]'::jsonb,
  optional_params_json jsonb not null default '[]'::jsonb,
  return_type text not null default '',
  errors_json jsonb not null default '[]'::jsonb,
  source_url text,
  source_anchor text,
  source_chunk_ids_json jsonb not null default '[]'::jsonb,
  public_api boolean not null default true,
  generated boolean not null default false,
  quality_score double precision not null default 1,
  confidence double precision not null default 0,
  metadata_json jsonb not null default '{}'::jsonb,
  embedding vector(1024),
  embedding_model text,
  embedding_dimensions integer,
  dedupe_cluster_id bigint,
  dedupe_canonical boolean not null default true,
  created_at timestamptz not null default now(),
  unique(version_id, method_key),
  search_document tsvector generated always as (
    setweight(to_tsvector('english', coalesce(symbol_name, '')), 'A') ||
    setweight(to_tsvector('english', coalesce(sdk_class, '')), 'A') ||
    setweight(to_tsvector('english', coalesce(sdk_method, '')), 'A') ||
    setweight(to_tsvector('english', coalesce(signature, '')), 'A') ||
    setweight(to_tsvector('english', coalesce(product, '')), 'B') ||
    setweight(to_tsvector('english', coalesce(language, '')), 'B') ||
    setweight(to_tsvector('english', coalesce(required_params_json::text, '')), 'B') ||
    setweight(to_tsvector('english', coalesce(optional_params_json::text, '')), 'B') ||
    setweight(to_tsvector('english', coalesce(description, '')), 'B')
  ) stored
);

create table if not exists agent_recipes (
  id bigserial primary key,
  version_id bigint not null references library_versions(id) on delete cascade,
  recipe_key text not null,
  product text not null default '',
  product_confidence double precision not null default 0,
  title text not null,
  task_kind text not null default 'operation',
  language text not null default '',
  summary text not null default '',
  code text,
  info text not null default '',
  required_env_json jsonb not null default '[]'::jsonb,
  required_params_json jsonb not null default '[]'::jsonb,
  source_api_operation_ids_json jsonb not null default '[]'::jsonb,
  source_sdk_method_ids_json jsonb not null default '[]'::jsonb,
  source_code_example_ids_json jsonb not null default '[]'::jsonb,
  source_section_ids_json jsonb not null default '[]'::jsonb,
  source_chunk_ids_json jsonb not null default '[]'::jsonb,
  source_urls_json jsonb not null default '[]'::jsonb,
  evidence_hash text not null default '',
  llm_model text not null default '',
  llm_enriched boolean not null default false,
  confidence double precision not null default 0,
  quality_score double precision not null default 1,
  token_count integer not null default 0,
  metadata_json jsonb not null default '{}'::jsonb,
  embedding vector(1024),
  embedding_model text,
  embedding_dimensions integer,
  dedupe_cluster_id bigint,
  dedupe_canonical boolean not null default true,
  created_at timestamptz not null default now(),
  unique(version_id, recipe_key),
  search_document tsvector generated always as (
    setweight(to_tsvector('english', coalesce(title, '')), 'A') ||
    setweight(to_tsvector('english', coalesce(task_kind, '')), 'A') ||
    setweight(to_tsvector('english', coalesce(product, '')), 'B') ||
    setweight(to_tsvector('english', coalesce(language, '')), 'B') ||
    setweight(to_tsvector('english', coalesce(summary, '')), 'B') ||
    setweight(to_tsvector('english', coalesce(code, '')), 'B') ||
    setweight(to_tsvector('english', coalesce(info, '')), 'B') ||
    setweight(to_tsvector('english', coalesce(required_env_json::text, '')), 'B') ||
    setweight(to_tsvector('english', coalesce(required_params_json::text, '')), 'B')
  ) stored
);

create index if not exists source_documents_version_type_role_idx on source_documents(version_id, source_type, document_role, source_priority);
create index if not exists source_documents_coverage_idx on source_documents(version_id, chunk_coverage_ratio);
create index if not exists index_tombstones_version_surface_idx on index_tombstones(version_id, surface_table, tombstoned_at desc);
create index if not exists source_sections_version_role_idx on source_sections(version_id, document_role, content_type, path);
create index if not exists source_sections_shape_idx on source_sections(version_id, has_code, has_endpoint_shape, has_signature_shape);
create index if not exists chunks_source_section_idx on chunks(source_section_id);
create index if not exists code_examples_version_role_idx on code_examples(version_id, document_role, language, product);
create index if not exists code_examples_dedupe_canonical_idx on code_examples(version_id, dedupe_canonical);
create index if not exists code_examples_search_idx on code_examples using gin(search_document);
create index if not exists code_examples_embedding_idx on code_examples using hnsw (embedding vector_cosine_ops);
create index if not exists api_operations_version_kind_idx on api_operations(version_id, operation_kind, product);
create index if not exists api_operations_dedupe_canonical_idx on api_operations(version_id, dedupe_canonical);
create index if not exists api_operations_source_section_idx on api_operations(source_section_id);
create index if not exists api_operations_endpoint_idx on api_operations(version_id, http_method, endpoint);
create index if not exists api_operations_search_idx on api_operations using gin(search_document);
create index if not exists api_operations_embedding_idx on api_operations using hnsw (embedding vector_cosine_ops);
create index if not exists sdk_methods_version_symbol_idx on sdk_methods(version_id, symbol_name, sdk_class, sdk_method);
create index if not exists sdk_methods_dedupe_canonical_idx on sdk_methods(version_id, dedupe_canonical);
create index if not exists sdk_methods_source_section_idx on sdk_methods(source_section_id);
create index if not exists sdk_methods_search_idx on sdk_methods using gin(search_document);
create index if not exists sdk_methods_embedding_idx on sdk_methods using hnsw (embedding vector_cosine_ops);
create index if not exists agent_recipes_version_kind_idx on agent_recipes(version_id, task_kind, product);
create index if not exists agent_recipes_dedupe_canonical_idx on agent_recipes(version_id, dedupe_canonical);
create index if not exists agent_recipes_search_idx on agent_recipes using gin(search_document);
create index if not exists agent_recipes_embedding_idx on agent_recipes using hnsw (embedding vector_cosine_ops);
