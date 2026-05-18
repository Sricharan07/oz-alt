alter table libraries
  add column if not exists default_version_id bigint,
  add column if not exists redirected_to_library_id bigint references libraries(id) on delete set null,
  add column if not exists version_strategy text not null default 'semver';

do $$
begin
  alter table libraries
    add constraint libraries_default_version_fk
    foreign key (default_version_id) references library_versions(id) on delete set null;
exception when duplicate_object then
  null;
end
$$;

alter table library_versions
  add column if not exists last_requested_at timestamptz,
  add column if not exists archived_at timestamptz,
  add column if not exists version_rank integer,
  add column if not exists drift_score double precision not null default 0;

create index if not exists libraries_default_version_idx
  on libraries(default_version_id)
  where default_version_id is not null;

create index if not exists libraries_redirected_to_idx
  on libraries(redirected_to_library_id)
  where redirected_to_library_id is not null;

create index if not exists library_versions_active_idx
  on library_versions(library_id, archived_at, version);

create index if not exists library_versions_requested_idx
  on library_versions(last_requested_at desc nulls last);

create index if not exists chunks_version_embedding_idx
  on chunks using hnsw (embedding vector_cosine_ops)
  where embedding is not null;

alter table freshness_policies
  add column if not exists version text not null default 'latest';

do $$
begin
  alter table freshness_policies drop constraint if exists freshness_policies_vendor_library_key;
exception when undefined_object then
  null;
end
$$;

create unique index if not exists freshness_policies_vendor_library_version_key
  on freshness_policies(vendor, library, version);
