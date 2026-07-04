ALTER TABLE api_tokens
  ADD COLUMN IF NOT EXISTS project_id UUID REFERENCES projects(id) ON DELETE CASCADE;

CREATE INDEX IF NOT EXISTS idx_api_tokens_project
  ON api_tokens(project_id)
  WHERE project_id IS NOT NULL;
