alter table chunks
  add column if not exists heading_path jsonb not null default '[]'::jsonb,
  add column if not exists symbols jsonb not null default '[]'::jsonb,
  add column if not exists content_type text not null default 'guide',
  add column if not exists quality_score double precision not null default 1;

drop index if exists chunks_search_document_idx;

alter table chunks
  drop column if exists search_document;

alter table chunks
  add column search_document tsvector generated always as (
    setweight(to_tsvector('english', coalesce(path, '')), 'A') ||
    setweight(to_tsvector('english', coalesce(heading_path::text, '')), 'A') ||
    setweight(to_tsvector('english', coalesce(symbols::text, '')), 'A') ||
    setweight(to_tsvector('english', coalesce(content_type, '')), 'C') ||
    setweight(to_tsvector('english', coalesce(content, '')), 'B')
  ) stored;

create index if not exists chunks_search_document_idx on chunks using gin(search_document);
create index if not exists chunks_content_type_idx on chunks(content_type);

create or replace function content_type_score(value text)
returns double precision
language sql
immutable
as $$
  select case coalesce(value, '')
    when 'api_reference' then 0.18
    when 'types' then 0.14
    when 'example' then 0.08
    when 'index' then -0.12
    else 0
  end
$$;
