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
  content_type text not null default 'prose',
  start_line integer not null default 1,
  end_line integer,
  content text not null,
  token_count integer not null default 0,
  quality_score double precision not null default 1,
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

create table if not exists context_snippets (
  id bigserial primary key,
  version_id bigint not null references library_versions(id) on delete cascade,
  source_section_id bigint references source_sections(id) on delete cascade,
  primary_chunk_id bigint references chunks(id) on delete set null,
  snippet_key text not null,
  path text not null,
  source_url text,
  source_anchor text,
  title text not null,
  description text not null default '',
  role text not null default 'concept',
  applies_to jsonb not null default '[]'::jsonb,
  entities jsonb not null default '[]'::jsonb,
  task_tags jsonb not null default '[]'::jsonb,
  heading_path jsonb not null default '[]'::jsonb,
  symbols jsonb not null default '[]'::jsonb,
  code_language text,
  code text,
  constraints jsonb not null default '[]'::jsonb,
  related_chunk_ids jsonb not null default '[]'::jsonb,
  start_line integer not null default 1,
  end_line integer,
  content text not null,
  token_count integer not null default 0,
  quality_score double precision not null default 1,
  created_at timestamptz not null default now(),
  unique (version_id, snippet_key),
  search_document tsvector generated always as (
    setweight(to_tsvector('english', coalesce(path, '')), 'A') ||
    setweight(to_tsvector('english', coalesce(title, '')), 'A') ||
    setweight(to_tsvector('english', coalesce(description, '')), 'A') ||
    setweight(to_tsvector('english', coalesce(entities::text, '')), 'A') ||
    setweight(to_tsvector('english', coalesce(task_tags::text, '')), 'A') ||
    setweight(to_tsvector('english', coalesce(applies_to::text, '')), 'B') ||
    setweight(to_tsvector('english', coalesce(heading_path::text, '')), 'B') ||
    setweight(to_tsvector('english', coalesce(symbols::text, '')), 'A') ||
    setweight(to_tsvector('english', coalesce(role, '')), 'C') ||
    setweight(to_tsvector('english', coalesce(content, '')), 'B') ||
    setweight(to_tsvector('english', coalesce(code, '')), 'B')
  ) stored
);

create index if not exists source_sections_version_path_idx on source_sections(version_id, path, start_line);
create index if not exists source_sections_document_idx on source_sections(source_document_id);
create index if not exists source_sections_search_idx on source_sections using gin(search_document);

create index if not exists context_snippets_version_role_idx on context_snippets(version_id, role, path);
create index if not exists context_snippets_section_idx on context_snippets(source_section_id);
create index if not exists context_snippets_chunk_idx on context_snippets(primary_chunk_id);
create index if not exists context_snippets_search_idx on context_snippets using gin(search_document);
create index if not exists context_snippets_entities_idx on context_snippets using gin(entities);
create index if not exists context_snippets_task_tags_idx on context_snippets using gin(task_tags);
