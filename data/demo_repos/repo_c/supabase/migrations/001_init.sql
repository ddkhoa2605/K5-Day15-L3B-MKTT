create table public.users (
  id uuid primary key references auth.users (id) on delete cascade,
  ten text,
  so_dt_kh text,
  email text unique,
  created_at timestamptz not null default now()
);

create table public.san (
  id bigint generated always as identity primary key,
  ten_san text not null,
  dia_chi text not null
);

create table public.bookings (
  id bigint generated always as identity primary key,
  user_id uuid not null references public.users (id) on delete cascade,
  san_id bigint not null references public.san (id),
  vi_tri_gan_nhat text,
  gio_bat_dau timestamptz not null,
  created_at timestamptz not null default now()
);
