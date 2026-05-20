alter table source_documents
  add column if not exists metadata_json jsonb not null default '{}'::jsonb;

alter table chunks
  add column if not exists metadata_json jsonb not null default '{}'::jsonb;

alter table source_sections
  add column if not exists metadata_json jsonb not null default '{}'::jsonb;

alter table context_snippets
  add column if not exists metadata_json jsonb not null default '{}'::jsonb;

create index if not exists source_documents_metadata_idx
  on source_documents using gin(metadata_json);

create index if not exists chunks_metadata_idx
  on chunks using gin(metadata_json);

create index if not exists context_snippets_metadata_idx
  on context_snippets using gin(metadata_json);
