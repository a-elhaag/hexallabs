-- 0001_workspace_columns.sql
-- Adds the workspace_kind and artifact columns on executions for the
-- generative-workspace feature. Idempotent — safe to run multiple times.
--
-- Apply with:
--   psql "$DATABASE_URL" -f backend/migrations/0001_workspace_columns.sql

ALTER TABLE executions
    ADD COLUMN IF NOT EXISTS workspace_kind TEXT,
    ADD COLUMN IF NOT EXISTS artifact       JSONB;

-- Enforce the closed enum at the DB layer. Dropped-and-recreated so the
-- constraint stays in sync when the enum grows.
ALTER TABLE executions
    DROP CONSTRAINT IF EXISTS executions_workspace_kind_check;

ALTER TABLE executions
    ADD CONSTRAINT executions_workspace_kind_check
    CHECK (workspace_kind IS NULL
           OR workspace_kind IN ('chat','code','spreadsheet','diagram','document'));
