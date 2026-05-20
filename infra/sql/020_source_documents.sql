create table if not exists source_documents (
  id bigserial primary key,
  version_id bigint not null references library_versions(id) on delete cascade,
  source_document_key text not null,
  source_kind text not null default 'website',
  canonical_url text,
  source_url text,
  path text,
  title text,
  source_priority integer not null default 50,
  discovered_from text,
  raw_artifact_key text,
  etag text,
  last_modified text,
  fetched_at timestamptz not null default now(),
  created_at timestamptz not null default now(),
  unique (version_id, source_document_key)
);

alter table chunks
  add column if not exists source_document_id bigint references source_documents(id) on delete set null;

create index if not exists source_documents_version_kind_idx on source_documents(version_id, source_kind, source_priority);
create index if not exists source_documents_canonical_url_idx on source_documents(version_id, md5(coalesce(canonical_url, '')));
create index if not exists chunks_source_document_idx on chunks(source_document_id);
