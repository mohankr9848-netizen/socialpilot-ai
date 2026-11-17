create extension if not exists pgcrypto;
create table if not exists public.businesses (
 id uuid primary key default gen_random_uuid(),
 user_id uuid not null references auth.users(id) on delete cascade,
 name text not null check (length(name) between 1 and 200),
 website text not null default '', product_url text not null default '',
 description text not null default '', product_description text not null default '',
 industry text not null default '', audience text not null default '',
 market text not null default '', voice text not null default 'Professional',
 colors jsonb not null default '["#24468F", "#C62229"]'::jsonb,
 logo_path text, created_at timestamptz not null default now(),
 updated_at timestamptz not null default now()
);
alter table public.businesses enable row level security;
create policy "owners select businesses" on public.businesses for select to authenticated using (auth.uid() = user_id);
create policy "owners insert businesses" on public.businesses for insert to authenticated with check (auth.uid() = user_id);
create policy "owners update businesses" on public.businesses for update to authenticated using (auth.uid() = user_id) with check (auth.uid() = user_id);
create policy "owners delete businesses" on public.businesses for delete to authenticated using (auth.uid() = user_id);
insert into storage.buckets (id, name, public, file_size_limit, allowed_mime_types)
values ('brand-logos', 'brand-logos', false, 2000000, array['image/png','image/jpeg','image/webp'])
on conflict (id) do nothing;
create policy "owner logo read" on storage.objects for select to authenticated
using (bucket_id = 'brand-logos' and (storage.foldername(name))[1] = auth.uid()::text);
create policy "owner logo upload" on storage.objects for insert to authenticated
with check (bucket_id = 'brand-logos' and (storage.foldername(name))[1] = auth.uid()::text);
create policy "owner logo update" on storage.objects for update to authenticated
using (bucket_id = 'brand-logos' and (storage.foldername(name))[1] = auth.uid()::text)
with check (bucket_id = 'brand-logos' and (storage.foldername(name))[1] = auth.uid()::text);
create policy "owner logo delete" on storage.objects for delete to authenticated
using (bucket_id = 'brand-logos' and (storage.foldername(name))[1] = auth.uid()::text);
