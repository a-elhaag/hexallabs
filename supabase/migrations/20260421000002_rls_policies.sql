-- Enable RLS on every public table.
-- Frontend Supabase client uses anon role and is subject to these policies.
-- FastAPI connects with Postgres user that has BYPASSRLS (service role or DB owner) and
-- enforces user_id scoping in application code.
--
-- Idempotent: drops each policy before recreating so the file can be re-applied safely.

alter table public.users              enable row level security;
alter table public.sessions           enable row level security;
alter table public.queries            enable row level security;
alter table public.messages           enable row level security;
alter table public.peer_reviews       enable row level security;
alter table public.relay_handoffs     enable row level security;
alter table public.workflows          enable row level security;
alter table public.workflow_runs      enable row level security;
alter table public.workflow_node_runs enable row level security;
alter table public.prompt_lens_entries enable row level security;

-- users: a row is readable/updatable by that user.
drop policy if exists "users_self_select" on public.users;
create policy "users_self_select" on public.users
  for select using (auth.uid() = id);

drop policy if exists "users_self_update" on public.users;
create policy "users_self_update" on public.users
  for update using (auth.uid() = id);

-- sessions: owned directly by user_id.
drop policy if exists "sessions_owner_all" on public.sessions;
create policy "sessions_owner_all" on public.sessions
  for all using (auth.uid() = user_id) with check (auth.uid() = user_id);

-- queries: user_id denormalized for fast scoping.
drop policy if exists "queries_owner_all" on public.queries;
create policy "queries_owner_all" on public.queries
  for all using (auth.uid() = user_id) with check (auth.uid() = user_id);

-- messages: scoped through parent query.
drop policy if exists "messages_owner_all" on public.messages;
create policy "messages_owner_all" on public.messages
  for all using (
    exists (
      select 1 from public.queries q
      where q.id = messages.query_id and q.user_id = auth.uid()
    )
  )
  with check (
    exists (
      select 1 from public.queries q
      where q.id = messages.query_id and q.user_id = auth.uid()
    )
  );

-- peer_reviews: scoped through parent query.
drop policy if exists "peer_reviews_owner_all" on public.peer_reviews;
create policy "peer_reviews_owner_all" on public.peer_reviews
  for all using (
    exists (
      select 1 from public.queries q
      where q.id = peer_reviews.query_id and q.user_id = auth.uid()
    )
  )
  with check (
    exists (
      select 1 from public.queries q
      where q.id = peer_reviews.query_id and q.user_id = auth.uid()
    )
  );

-- relay_handoffs: scoped through parent query.
drop policy if exists "relay_handoffs_owner_all" on public.relay_handoffs;
create policy "relay_handoffs_owner_all" on public.relay_handoffs
  for all using (
    exists (
      select 1 from public.queries q
      where q.id = relay_handoffs.query_id and q.user_id = auth.uid()
    )
  )
  with check (
    exists (
      select 1 from public.queries q
      where q.id = relay_handoffs.query_id and q.user_id = auth.uid()
    )
  );

-- workflows: owned directly by user_id.
drop policy if exists "workflows_owner_all" on public.workflows;
create policy "workflows_owner_all" on public.workflows
  for all using (auth.uid() = user_id) with check (auth.uid() = user_id);

-- workflow_runs: scoped through parent workflow.
drop policy if exists "workflow_runs_owner_all" on public.workflow_runs;
create policy "workflow_runs_owner_all" on public.workflow_runs
  for all using (
    exists (
      select 1 from public.workflows w
      where w.id = workflow_runs.workflow_id and w.user_id = auth.uid()
    )
  )
  with check (
    exists (
      select 1 from public.workflows w
      where w.id = workflow_runs.workflow_id and w.user_id = auth.uid()
    )
  );

-- workflow_node_runs: scoped through parent run → workflow.
drop policy if exists "workflow_node_runs_owner_all" on public.workflow_node_runs;
create policy "workflow_node_runs_owner_all" on public.workflow_node_runs
  for all using (
    exists (
      select 1
      from public.workflow_runs r
      join public.workflows w on w.id = r.workflow_id
      where r.id = workflow_node_runs.workflow_run_id and w.user_id = auth.uid()
    )
  )
  with check (
    exists (
      select 1
      from public.workflow_runs r
      join public.workflows w on w.id = r.workflow_id
      where r.id = workflow_node_runs.workflow_run_id and w.user_id = auth.uid()
    )
  );

-- prompt_lens_entries: scoped through parent query.
drop policy if exists "prompt_lens_entries_owner_all" on public.prompt_lens_entries;
create policy "prompt_lens_entries_owner_all" on public.prompt_lens_entries
  for all using (
    exists (
      select 1 from public.queries q
      where q.id = prompt_lens_entries.query_id and q.user_id = auth.uid()
    )
  )
  with check (
    exists (
      select 1 from public.queries q
      where q.id = prompt_lens_entries.query_id and q.user_id = auth.uid()
    )
  );
