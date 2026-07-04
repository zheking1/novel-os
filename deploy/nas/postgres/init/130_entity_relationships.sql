ALTER TABLE state_entities ADD COLUMN IF NOT EXISTS lifecycle_status TEXT NOT NULL DEFAULT 'active';
ALTER TABLE state_entities ADD COLUMN IF NOT EXISTS importance TEXT NOT NULL DEFAULT 'medium';
ALTER TABLE state_entities ADD COLUMN IF NOT EXISTS tags TEXT[] NOT NULL DEFAULT ARRAY[]::TEXT[];
ALTER TABLE state_entities ADD COLUMN IF NOT EXISTS first_seen_chapter_no INTEGER;
ALTER TABLE state_entities ADD COLUMN IF NOT EXISTS last_seen_chapter_no INTEGER;
ALTER TABLE state_entities ADD COLUMN IF NOT EXISTS first_seen_volume_no INTEGER;
ALTER TABLE state_entities ADD COLUMN IF NOT EXISTS last_seen_volume_no INTEGER;
ALTER TABLE state_entities ADD COLUMN IF NOT EXISTS source_type TEXT NOT NULL DEFAULT 'manual';
ALTER TABLE state_entities ADD COLUMN IF NOT EXISTS source_id TEXT;
ALTER TABLE state_entities ADD COLUMN IF NOT EXISTS metadata JSONB NOT NULL DEFAULT '{}'::jsonb;

CREATE INDEX IF NOT EXISTS idx_state_entities_project_lifecycle
  ON state_entities(project_id, lifecycle_status, entity_type);

CREATE INDEX IF NOT EXISTS idx_state_entities_tags
  ON state_entities USING GIN(tags);

CREATE INDEX IF NOT EXISTS idx_state_entities_metadata
  ON state_entities USING GIN(metadata);

CREATE TABLE IF NOT EXISTS entity_relationships (
  id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
  project_id UUID NOT NULL REFERENCES projects(id) ON DELETE CASCADE,
  source_entity_id UUID NOT NULL REFERENCES state_entities(id) ON DELETE CASCADE,
  target_entity_id UUID NOT NULL REFERENCES state_entities(id) ON DELETE CASCADE,
  relation_type TEXT NOT NULL,
  attitude TEXT,
  intensity NUMERIC(5,4),
  known_by_source BOOLEAN NOT NULL DEFAULT true,
  known_by_target BOOLEAN NOT NULL DEFAULT true,
  known_by_reader BOOLEAN NOT NULL DEFAULT true,
  status TEXT NOT NULL DEFAULT 'active',
  source_chapter_no INTEGER,
  source_chapter_id UUID REFERENCES chapters(id) ON DELETE SET NULL,
  source_commit_id UUID REFERENCES chapter_commits(id) ON DELETE SET NULL,
  metadata JSONB NOT NULL DEFAULT '{}'::jsonb,
  created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
  updated_at TIMESTAMPTZ NOT NULL DEFAULT now(),
  UNIQUE(project_id, source_entity_id, target_entity_id, relation_type)
);

CREATE INDEX IF NOT EXISTS idx_entity_relationships_project_source
  ON entity_relationships(project_id, source_entity_id, status);

CREATE INDEX IF NOT EXISTS idx_entity_relationships_project_target
  ON entity_relationships(project_id, target_entity_id, status);

CREATE INDEX IF NOT EXISTS idx_entity_relationships_metadata
  ON entity_relationships USING GIN(metadata);
