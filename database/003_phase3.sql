-- Run once in Supabase SQL Editor AFTER 001_phase1.sql and 002_phase2.sql.
-- Draft content only: no OAuth connections or automatic publishing.
create table if not exists public.content_posts (
 id uuid primary key default gen_random_uuid(),
 user_id uuid not null references auth.users(id) on delete cascade,
 business_id uuid not null references public.businesses(id) on delete cascade,
 scheduled_date date not null,
 scheduled_time time not null default '10:00',
 platform text not null check (platform in ('LinkedIn','Instagram','Facebook','X')),
 content_type text not null default 'Single image',
 content_pillar text not null default '',
 category text not null default '',
 title text not null default '',
 caption text not null default '',
 hashtags text not null default '',
 cta text not null default '',
 graphic_prompt text not null default '',
 status text not null default 'draft' check (status in ('draft','approved')),
 created_at timestamptz not null default now(),
 updated_at timestamptz not null default now()
);
create index if not exists idx_content_posts_owner_month on public.content_posts (user_id,business_id,scheduled_date);
alter table public.content_posts enable row level security;
drop policy if exists "content select own" on public.content_posts;
create policy "content select own" on public.content_posts for select to authenticated
using (user_id = (select auth.uid()) and exists (select 1 from public.businesses b where b.id=business_id and b.user_id=(select auth.uid())));
drop policy if exists "content insert own" on public.content_posts;
create policy "content insert own" on public.content_posts for insert to authenticated
with check (user_id = (select auth.uid()) and exists (select 1 from public.businesses b where b.id=business_id and b.user_id=(select auth.uid())));
drop policy if exists "content update own" on public.content_posts;
create policy "content update own" on public.content_posts for update to authenticated
using (user_id = (select auth.uid()) and exists (select 1 from public.businesses b where b.id=business_id and b.user_id=(select auth.uid())))
with check (user_id = (select auth.uid()) and exists (select 1 from public.businesses b where b.id=business_id and b.user_id=(select auth.uid())));
drop policy if exists "content delete own" on public.content_posts;
create policy "content delete own" on public.content_posts for delete to authenticated
using (user_id = (select auth.uid()) and exists (select 1 from public.businesses b where b.id=business_id and b.user_id=(select auth.uid())));
