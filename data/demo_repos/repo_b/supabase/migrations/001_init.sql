create table public.users (
  id uuid primary key references auth.users (id) on delete cascade,
  email text not null unique,
  ho_ten text,
  sdt text,
  created_at timestamptz not null default now()
);

create table public.consents (
  id uuid primary key default gen_random_uuid(),
  user_id uuid not null references public.users (id) on delete cascade,
  purpose text not null,
  policy_version text not null,
  accepted_at timestamptz not null default now()
);

create table public.chat_messages (
  id bigint generated always as identity primary key,
  user_id uuid not null references public.users (id) on delete cascade,
  role text not null,
  noi_dung text not null,
  created_at timestamptz not null default now()
);
