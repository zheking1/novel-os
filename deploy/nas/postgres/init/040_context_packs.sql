CREATE TABLE IF NOT EXISTS context_packs (
  id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
  project_id UUID NOT NULL REFERENCES projects(id) ON DELETE CASCADE,
  chapter_no INTEGER NOT NULL,
  purpose TEXT NOT NULL DEFAULT 'draft',
  focus TEXT[] NOT NULL DEFAULT ARRAY[]::TEXT[],
  budget JSONB NOT NULL DEFAULT '{}'::jsonb,
  sections JSONB NOT NULL DEFAULT '[]'::jsonb,
  retrieval_audit JSONB NOT NULL DEFAULT '[]'::jsonb,
  warnings JSONB NOT NULL DEFAULT '[]'::jsonb,
  created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE INDEX IF NOT EXISTS idx_context_packs_project_chapter
  ON context_packs(project_id, chapter_no, created_at DESC);

