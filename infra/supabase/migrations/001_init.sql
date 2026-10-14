create extension if not exists "pgcrypto";

create table if not exists public.users (
  id uuid primary key default gen_random_uuid(),
  email text unique,
  display_name text,
  role text not null default 'analyst',
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now()
);

create table if not exists public.fact_checks (
  id uuid primary key default gen_random_uuid(),
  user_id uuid references public.users(id) on delete set null,
  input_type text not null check (input_type in ('text', 'image')),
  status text not null check (status in ('queued', 'running', 'completed', 'failed')),
  original_input text not null,
  image_path text,
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now()
);

create table if not exists public.claims (
  id uuid primary key default gen_random_uuid(),
  fact_check_id uuid not null references public.fact_checks(id) on delete cascade,
  normalized_text text not null,
  entities jsonb not null default '[]'::jsonb,
  topic text,
  category text,
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now()
);

create table if not exists public.sources (
  id uuid primary key default gen_random_uuid(),
  domain text,
  title text,
  url text not null unique,
  tier text,
  credibility_score int,
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now()
);

create table if not exists public.evidence (
  id uuid primary key default gen_random_uuid(),
  fact_check_id uuid not null references public.fact_checks(id) on delete cascade,
  store text not null,
  text text not null,
  url text,
  raw jsonb not null default '{}'::jsonb,
  retrieval_score double precision,
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now()
);

create table if not exists public.agent_runs (
  id uuid primary key default gen_random_uuid(),
  fact_check_id uuid not null references public.fact_checks(id) on delete cascade,
  agent_name text not null,
  input jsonb not null default '{}'::jsonb,
  output jsonb not null default '{}'::jsonb,
  latency_ms int,
  token_usage jsonb not null default '{}'::jsonb,
  status text not null default 'ok',
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now()
);

create table if not exists public.verdicts (
  id uuid primary key default gen_random_uuid(),
  fact_check_id uuid not null unique references public.fact_checks(id) on delete cascade,
  verdict text not null,
  confidence double precision not null,
  explanation text not null,
  reasoning jsonb not null default '[]'::jsonb,
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now()
);

create table if not exists public.knowledge_graph_links (
  id uuid primary key default gen_random_uuid(),
  fact_check_id uuid not null references public.fact_checks(id) on delete cascade,
  neo4j_from text not null,
  neo4j_to text not null,
  rel_type text not null,
  payload jsonb not null default '{}'::jsonb,
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now()
);

create table if not exists public.evaluation_metrics (
  id uuid primary key default gen_random_uuid(),
  fact_check_id uuid references public.fact_checks(id) on delete cascade,
  metric_name text not null,
  value double precision not null,
  details jsonb not null default '{}'::jsonb,
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now()
);

create index if not exists fact_checks_user_created_idx on public.fact_checks (user_id, created_at desc);
create index if not exists evidence_fact_check_idx on public.evidence (fact_check_id);
create index if not exists sources_domain_idx on public.sources (domain);
create index if not exists agent_runs_fact_agent_idx on public.agent_runs (fact_check_id, agent_name);

alter table public.users enable row level security;
alter table public.fact_checks enable row level security;
alter table public.claims enable row level security;
alter table public.evidence enable row level security;
alter table public.sources enable row level security;
alter table public.agent_runs enable row level security;
alter table public.verdicts enable row level security;
alter table public.knowledge_graph_links enable row level security;
alter table public.evaluation_metrics enable row level security;

create policy fact_checks_owner on public.fact_checks
  for all using (user_id is null or user_id = auth.uid())
  with check (user_id is null or user_id = auth.uid());
