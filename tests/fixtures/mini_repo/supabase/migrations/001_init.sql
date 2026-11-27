-- fixture tự viết cho test, không phải repo thật
create table if not exists public."Users" (
  id uuid primary key default gen_random_uuid(),
  email text unique not null,
  "Ho_Ten" text,
  created_at timestamptz default now()
);

create table bookings (
  id uuid primary key,
  user_id uuid references public."Users"(id) on delete cascade,
  vi_tri_gan_nhat text,
  gia numeric(10, 2),
  constraint bookings_gia_check check (gia >= 0)
);
