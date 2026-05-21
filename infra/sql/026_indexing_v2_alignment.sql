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

alter table source_documents
  add column if not exists content_markdown text not null default '',
  add column if not exists parallel_structured_json jsonb not null default '{}'::jsonb,
  add column if not exists raw_object_store text,
  add column if not exists raw_object_sha256 text;

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

alter table dedupe_clusters
  add column if not exists surface_table text not null default 'chunks',
  add column if not exists canonical_row_id bigint,
  add column if not exists member_ids_json jsonb not null default '[]'::jsonb;

alter table api_operations
  add column if not exists source_section_id bigint references source_sections(id) on delete set null,
  add column if not exists source_chunk_ids_json jsonb not null default '[]'::jsonb,
  add column if not exists dedupe_cluster_id bigint,
  add column if not exists dedupe_canonical boolean not null default true;

alter table sdk_methods
  add column if not exists source_section_id bigint references source_sections(id) on delete set null,
  add column if not exists dedupe_cluster_id bigint,
  add column if not exists dedupe_canonical boolean not null default true;

alter table code_examples
  add column if not exists dedupe_cluster_id bigint,
  add column if not exists dedupe_canonical boolean not null default true;

alter table agent_recipes
  add column if not exists dedupe_cluster_id bigint,
  add column if not exists dedupe_canonical boolean not null default true;

create index if not exists source_sections_shape_idx
  on source_sections(version_id, has_code, has_endpoint_shape, has_signature_shape);

create index if not exists index_tombstones_version_surface_idx
  on index_tombstones(version_id, surface_table, tombstoned_at desc);

drop index if exists source_documents_version_kind_idx;

alter table source_documents
  drop column if exists source_kind;

create index if not exists source_documents_version_type_idx
  on source_documents(version_id, source_type, source_priority);

create index if not exists chunks_source_section_idx
  on chunks(source_section_id);

create index if not exists chunks_embedding_input_sha_idx
  on chunks(embedding_input_sha);

create index if not exists dedupe_clusters_surface_idx
  on dedupe_clusters(version_id, surface_table, cluster_key);

create index if not exists api_operations_source_section_idx
  on api_operations(source_section_id);

create index if not exists sdk_methods_source_section_idx
  on sdk_methods(source_section_id);

create index if not exists code_examples_dedupe_canonical_idx
  on code_examples(version_id, dedupe_canonical);

create index if not exists api_operations_dedupe_canonical_idx
  on api_operations(version_id, dedupe_canonical);

create index if not exists sdk_methods_dedupe_canonical_idx
  on sdk_methods(version_id, dedupe_canonical);

create index if not exists agent_recipes_dedupe_canonical_idx
  on agent_recipes(version_id, dedupe_canonical);
