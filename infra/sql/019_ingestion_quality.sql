create or replace function compact_key_sql(value text)
returns text
language sql
immutable
as $$
  select regexp_replace(lower(coalesce(value, '')), '[^a-z0-9]+', '', 'g')
$$;

create or replace function compact_basename(value text)
returns text
language sql
immutable
as $$
  select compact_key_sql(regexp_replace(regexp_replace(coalesce(value, ''), '^.*/', ''), '\.[^.]+$', ''))
$$;

alter table chunks
  add column if not exists content_sha text;

update chunks
set content_sha = encode(digest(regexp_replace(trim(content), '[[:space:]]+', ' ', 'g'), 'sha256'), 'hex')
where content_sha is null;

create index if not exists chunks_content_sha_idx on chunks(content_sha);

alter table embedding_cache
  add column if not exists content_sha text;

update embedding_cache
set content_sha = chunk_sha
where content_sha is null;

alter table embedding_cache
  alter column content_sha set not null;

create index if not exists embedding_cache_content_sha_idx on embedding_cache(content_sha);
