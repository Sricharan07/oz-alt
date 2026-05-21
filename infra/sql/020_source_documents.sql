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
  etag text,
  last_modified text,
  fetched_at timestamptz not null default now(),
  created_at timestamptz not null default now(),
  unique (version_id, source_document_key)
);

alter table chunks
  add column if not exists source_document_id bigint references source_documents(id) on delete set null;

create index if not exists source_documents_version_type_idx on source_documents(version_id, source_type, source_priority);
create index if not exists source_documents_canonical_url_idx on source_documents(version_id, md5(coalesce(canonical_url, '')));
create index if not exists chunks_source_document_idx on chunks(source_document_id);
