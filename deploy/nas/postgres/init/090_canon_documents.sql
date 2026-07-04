CREATE TABLE IF NOT EXISTS canon_documents (
  id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
  project_id UUID NOT NULL REFERENCES projects(id) ON DELETE CASCADE,
  doc_type TEXT NOT NULL,
  key TEXT NOT NULL,
  title TEXT NOT NULL,
  content TEXT NOT NULL,
  content_hash TEXT NOT NULL,
  status TEXT NOT NULL DEFAULT 'active',
  version INTEGER NOT NULL DEFAULT 1,
  scope JSONB NOT NULL DEFAULT '{}'::jsonb,
  review_status TEXT NOT NULL DEFAULT 'approved',
  source_type TEXT NOT NULL DEFAULT 'manual',
  source_id TEXT,
  related_rule_ids TEXT[] NOT NULL DEFAULT ARRAY[]::TEXT[],
  metadata JSONB NOT NULL DEFAULT '{}'::jsonb,
  created_by UUID REFERENCES users(id) ON DELETE SET NULL,
  updated_by UUID REFERENCES users(id) ON DELETE SET NULL,
  created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
  updated_at TIMESTAMPTZ NOT NULL DEFAULT now(),
  search_vector TSVECTOR GENERATED ALWAYS AS (
    to_tsvector('simple', coalesce(title, '') || ' ' || coalesce(key, '') || ' ' || coalesce(content, ''))
  ) STORED,
  UNIQUE(project_id, doc_type, key)
);

CREATE TABLE IF NOT EXISTS canon_document_versions (
  id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
  project_id UUID NOT NULL REFERENCES projects(id) ON DELETE CASCADE,
  document_id UUID NOT NULL REFERENCES canon_documents(id) ON DELETE CASCADE,
  version INTEGER NOT NULL,
  title TEXT NOT NULL,
  content TEXT NOT NULL,
  content_hash TEXT NOT NULL,
  status TEXT NOT NULL,
  scope JSONB NOT NULL DEFAULT '{}'::jsonb,
  review_status TEXT NOT NULL,
  source_type TEXT NOT NULL DEFAULT 'manual',
  source_id TEXT,
  related_rule_ids TEXT[] NOT NULL DEFAULT ARRAY[]::TEXT[],
  metadata JSONB NOT NULL DEFAULT '{}'::jsonb,
  change_reason TEXT,
  created_by UUID REFERENCES users(id) ON DELETE SET NULL,
  created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
  UNIQUE(document_id, version)
);

CREATE INDEX IF NOT EXISTS idx_canon_documents_project_type_status
  ON canon_documents(project_id, doc_type, status);

CREATE INDEX IF NOT EXISTS idx_canon_documents_project_review
  ON canon_documents(project_id, review_status);

CREATE INDEX IF NOT EXISTS idx_canon_documents_scope
  ON canon_documents USING GIN(scope);

CREATE INDEX IF NOT EXISTS idx_canon_documents_search
  ON canon_documents USING GIN(search_vector);

CREATE INDEX IF NOT EXISTS idx_canon_document_versions_document
  ON canon_document_versions(document_id, version DESC);
