drop index if exists chunks_source_anchor_idx;

create index if not exists chunks_source_anchor_hash_idx
  on chunks(version_id, md5(coalesce(source_anchor, '')));
