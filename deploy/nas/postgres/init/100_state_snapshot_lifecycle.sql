ALTER TABLE state_snapshots ADD COLUMN IF NOT EXISTS effective_chapter_no INTEGER;
ALTER TABLE state_snapshots ADD COLUMN IF NOT EXISTS expire_chapter_no INTEGER;
ALTER TABLE state_snapshots ADD COLUMN IF NOT EXISTS effective_volume_no INTEGER;
ALTER TABLE state_snapshots ADD COLUMN IF NOT EXISTS expire_volume_no INTEGER;
ALTER TABLE state_snapshots ADD COLUMN IF NOT EXISTS duration_type TEXT NOT NULL DEFAULT 'persistent';
ALTER TABLE state_snapshots ADD COLUMN IF NOT EXISTS expires_on_event TEXT;
ALTER TABLE state_snapshots ADD COLUMN IF NOT EXISTS confidence NUMERIC(5,4);
ALTER TABLE state_snapshots ADD COLUMN IF NOT EXISTS source_type TEXT NOT NULL DEFAULT 'chapter_commit';
ALTER TABLE state_snapshots ADD COLUMN IF NOT EXISTS source_id TEXT;
ALTER TABLE state_snapshots ADD COLUMN IF NOT EXISTS change_reason TEXT;
ALTER TABLE state_snapshots ADD COLUMN IF NOT EXISTS metadata JSONB NOT NULL DEFAULT '{}'::jsonb;

CREATE INDEX IF NOT EXISTS idx_state_snapshots_current_lifecycle
  ON state_snapshots(project_id, is_current, effective_chapter_no, expire_chapter_no);

CREATE INDEX IF NOT EXISTS idx_state_snapshots_source
  ON state_snapshots(project_id, source_type, source_id);

CREATE INDEX IF NOT EXISTS idx_state_snapshots_metadata
  ON state_snapshots USING GIN(metadata);
