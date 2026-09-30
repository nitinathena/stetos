-- Run this in the Supabase SQL Editor (Project -> SQL Editor -> New query).
--
-- Row Level Security is enabled with NO policies defined. That's
-- intentional: the browser never talks to Supabase directly in this app -
-- only the server-side Python functions (api/predict.py, api/sync.py) and
-- Next.js server components read/write this table, using the
-- SUPABASE_SERVICE_ROLE_KEY, which bypasses RLS entirely by design. If you
-- later want the browser to query this table directly, you'd add explicit
-- policies here first.

create table if not exists predictions (
  id bigint generated always as identity primary key,
  filename text not null,
  source text not null check (source in ('supabase_sync', 'user_upload')),
  prediction text not null check (prediction in ('normal', 'abnormal')),
  confidence double precision not null check (confidence >= 0 and confidence <= 1),
  created_at timestamptz not null default now()
);

-- Sync route looks up "has this filename already been processed" on every
-- run - keep that fast as the table grows.
create index if not exists predictions_filename_idx on predictions (filename);

-- Dashboard's recent-predictions table and time-series chart both order by
-- this.
create index if not exists predictions_created_at_idx on predictions (created_at desc);

alter table predictions enable row level security;
