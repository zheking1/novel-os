CREATE TABLE IF NOT EXISTS vector_index_jobs (
  id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
  project_id UUID NOT NULL REFERENCES projects(id) ON DELETE CASCADE,
  source_type TEXT NOT NULL,
  source_id UUID,
  chunk_id UUID REFERENCES memory_chunks(id) ON DELETE CASCADE,
  collection TEXT NOT NULL,
  status TEXT NOT NULL DEFAULT 'pending',
  error TEXT,
  created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
  updated_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE INDEX IF NOT EXISTS idx_vector_index_jobs_status
  ON vector_index_jobs(project_id, status, created_at);

