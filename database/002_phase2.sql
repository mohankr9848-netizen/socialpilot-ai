-- Run once in the same Supabase project as Phase 1.
create table if not exists public.business_research (
  id uuid primary key default gen_random_uuid(),
  user_id uuid not null references auth.users(id) on delete cascade,
  business_id uuid not null references public.businesses(id) on delete cascade,
  website text not null default '',
  facts jsonb not null default '{}'::jsonb,
  suggestions jsonb not null default '{}'::jsonb,
  warnings jsonb not null default '[]'::jsonb,
  approved boolean not null default false,
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now(),
  unique (business_id)
);
alter table public.business_research enable row level security;
-- The ownership check also verifies that the business belongs to the user.
drop policy if exists "research select own" on public.business_research;
create policy "research select own" on public.business_research for select to authenticated
using (user_id = (select auth.uid()) and exists (select 1 from public.businesses b where b.id = business_id and b.user_id = (select auth.uid())));
drop policy if exists "research insert own" on public.business_research;
create policy "research insert own" on public.business_research for insert to authenticated
with check (user_id = (select auth.uid()) and exists (select 1 from public.businesses b where b.id = business_id and b.user_id = (select auth.uid())));
drop policy if exists "research update own" on public.business_research;
create policy "research update own" on public.business_research for update to authenticated
using (user_id = (select auth.uid()) and exists (select 1 from public.businesses b where b.id = business_id and b.user_id = (select auth.uid())))
with check (user_id = (select auth.uid()) and exists (select 1 from public.businesses b where b.id = business_id and b.user_id = (select auth.uid())));
drop policy if exists "research delete own" on public.business_research;
create policy "research delete own" on public.business_research for delete to authenticated
using (user_id = (select auth.uid()) and exists (select 1 from public.businesses b where b.id = business_id and b.user_id = (select auth.uid())));
