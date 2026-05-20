alter table libraries
  add column if not exists aliases jsonb not null default '[]'::jsonb;

create index if not exists libraries_aliases_idx
  on libraries using gin(aliases);
