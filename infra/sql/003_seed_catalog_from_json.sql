-- Load registry/catalog.json through your migration runner as JSON and upsert it with this shape:
--
-- select oz_upsert_catalog(:catalog_json::jsonb);

create or replace function oz_upsert_catalog(catalog jsonb)
returns void
language plpgsql
as $$
declare
  item jsonb;
  vendor_row_id bigint;
  library_row_id bigint;
  version_row_id bigint;
begin
  for item in select * from jsonb_array_elements(catalog->'libraries')
  loop
    insert into vendors(name)
    values (item->>'vendor')
    on conflict (name) do update set name = excluded.name
    returning id into vendor_row_id;

    insert into libraries(vendor_id, name, description, source_url)
    values (
      vendor_row_id,
      item->>'library',
      coalesce(item->>'description', ''),
      coalesce((item->'source_urls')->>0, null)
    )
    on conflict (vendor_id, name) do update
      set description = excluded.description,
          source_url = excluded.source_url,
          updated_at = now()
    returning id into library_row_id;

    insert into library_versions(library_id, version, ref_sha, pack_key, indexed_at)
    values (
      library_row_id,
      item->>'version',
      coalesce(item->>'ref_sha', 'unknown'),
      item->>'pack_path',
      nullif(item->>'indexed_at', '')::timestamptz
    )
    on conflict (library_id, version) do update
      set ref_sha = excluded.ref_sha,
          pack_key = excluded.pack_key,
          indexed_at = excluded.indexed_at
    returning id into version_row_id;

    insert into refs(library_id, channel, version_id, ref_sha)
    values (library_row_id, 'latest', version_row_id, coalesce(item->>'ref_sha', 'unknown'))
    on conflict (library_id, channel) do update
      set version_id = excluded.version_id,
          ref_sha = excluded.ref_sha,
          updated_at = now();
  end loop;
end;
$$;
