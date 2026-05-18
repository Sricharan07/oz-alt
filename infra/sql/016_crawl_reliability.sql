alter table crawler_jobs
  add column if not exists progress_json jsonb not null default '{}'::jsonb,
  add column if not exists dead_letter_json jsonb not null default '[]'::jsonb,
  add column if not exists source_stats_json jsonb not null default '{}'::jsonb,
  add column if not exists failure_kind text;

alter table library_profiles
  add column if not exists source_file_patterns jsonb not null default '[]'::jsonb,
  add column if not exists needs_js boolean not null default false,
  add column if not exists include_source_files boolean not null default false,
  add column if not exists target_language text not null default 'en';

create index if not exists crawler_jobs_progress_gin_idx
  on crawler_jobs using gin(progress_json);
