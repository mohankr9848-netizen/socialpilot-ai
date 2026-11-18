-- Phase 4.5: run ONCE after 003_phase3.sql. No existing records are deleted.
create table if not exists public.business_products (
 id uuid primary key default gen_random_uuid(),
 user_id uuid not null references auth.users(id) on delete cascade,
 business_id uuid not null references public.businesses(id) on delete cascade,
 name text not null,
 url text not null,
 facts jsonb not null default '{}'::jsonb,
 approved boolean not null default false,
 created_at timestamptz not null default now(),
 updated_at timestamptz not null default now(),
 unique (business_id, url)
);
create index if not exists idx_business_products_owner on public.business_products(user_id, business_id);
alter table public.business_products enable row level security;
drop policy if exists "product owner select" on public.business_products;
create policy "product owner select" on public.business_products for select to authenticated
 using (user_id = (select auth.uid()) and exists (select 1 from public.businesses b where b.id = business_id and b.user_id = (select auth.uid())));
drop policy if exists "product owner insert" on public.business_products;
create policy "product owner insert" on public.business_products for insert to authenticated
 with check (user_id = (select auth.uid()) and exists (select 1 from public.businesses b where b.id = business_id and b.user_id = (select auth.uid())));
drop policy if exists "product owner update" on public.business_products;
create policy "product owner update" on public.business_products for update to authenticated
 using (user_id = (select auth.uid()) and exists (select 1 from public.businesses b where b.id = business_id and b.user_id = (select auth.uid())))
 with check (user_id = (select auth.uid()) and exists (select 1 from public.businesses b where b.id = business_id and b.user_id = (select auth.uid())));
drop policy if exists "product owner delete" on public.business_products;
create policy "product owner delete" on public.business_products for delete to authenticated
 using (user_id = (select auth.uid()) and exists (select 1 from public.businesses b where b.id = business_id and b.user_id = (select auth.uid())));
alter table public.content_posts add column if not exists content_brief jsonb not null default '{}'::jsonb;
