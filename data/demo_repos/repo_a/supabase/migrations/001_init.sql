create table public.users (
  id uuid primary key references auth.users (id) on delete cascade,
  email text not null unique,
  ho_ten text,
  created_at timestamptz not null default now()
);

create table public.consents (
  id uuid primary key default gen_random_uuid(),
  user_id uuid not null references public.users (id) on delete cascade,
  purpose text not null,
  policy_version text not null,
  accepted_at timestamptz not null default now()
);

create table public.products (
  id bigint generated always as identity primary key,
  ten_sp text not null,
  mo_ta text,
  gia integer not null
);
