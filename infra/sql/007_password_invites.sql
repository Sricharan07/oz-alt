alter table users
  add column if not exists password_hash text,
  add column if not exists password_set_at timestamptz,
  add column if not exists last_login_at timestamptz;

create table if not exists password_tokens (
  id uuid primary key default gen_random_uuid(),
  user_id uuid not null references users(id) on delete cascade,
  token_hash text not null unique,
  purpose text not null,
  expires_at timestamptz not null,
  consumed_at timestamptz,
  created_by uuid references users(id) on delete set null,
  created_at timestamptz not null default now()
);

alter table password_tokens
  drop constraint if exists password_tokens_purpose_check;

alter table password_tokens
  add constraint password_tokens_purpose_check
  check (purpose in ('invite', 'reset'));

create index if not exists password_tokens_user_id_idx on password_tokens(user_id);
create index if not exists password_tokens_expires_at_idx on password_tokens(expires_at);
create index if not exists password_tokens_active_idx
  on password_tokens(user_id, purpose, expires_at)
  where consumed_at is null;

create table if not exists password_login_attempts (
  id bigserial primary key,
  email_hash text not null,
  ip_hash text,
  success boolean not null default false,
  created_at timestamptz not null default now()
);

create index if not exists password_login_attempts_email_idx
  on password_login_attempts(email_hash, created_at desc);

create index if not exists password_login_attempts_ip_idx
  on password_login_attempts(ip_hash, created_at desc)
  where ip_hash is not null;
