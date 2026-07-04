ALTER TABLE foreshadowing ADD COLUMN IF NOT EXISTS parent_foreshadowing_id UUID REFERENCES foreshadowing(id) ON DELETE SET NULL;
ALTER TABLE foreshadowing ADD COLUMN IF NOT EXISTS related_foreshadowing_ids TEXT[] NOT NULL DEFAULT ARRAY[]::TEXT[];
ALTER TABLE foreshadowing ADD COLUMN IF NOT EXISTS trigger_on_payoff_ids TEXT[] NOT NULL DEFAULT ARRAY[]::TEXT[];
ALTER TABLE foreshadowing ADD COLUMN IF NOT EXISTS blocks_payoff_until_ids TEXT[] NOT NULL DEFAULT ARRAY[]::TEXT[];
ALTER TABLE foreshadowing ADD COLUMN IF NOT EXISTS layer TEXT NOT NULL DEFAULT 'visible';
ALTER TABLE foreshadowing ADD COLUMN IF NOT EXISTS must_payoff BOOLEAN NOT NULL DEFAULT false;
ALTER TABLE foreshadowing ADD COLUMN IF NOT EXISTS payoff_deadline_chapter INTEGER;
ALTER TABLE foreshadowing ADD COLUMN IF NOT EXISTS payoff_deadline_volume INTEGER;
ALTER TABLE foreshadowing ADD COLUMN IF NOT EXISTS overdue_policy TEXT NOT NULL DEFAULT 'warn';

CREATE INDEX IF NOT EXISTS idx_foreshadowing_parent
  ON foreshadowing(project_id, parent_foreshadowing_id);

CREATE INDEX IF NOT EXISTS idx_foreshadowing_layer_status
  ON foreshadowing(project_id, layer, status);

CREATE INDEX IF NOT EXISTS idx_foreshadowing_deadline
  ON foreshadowing(project_id, payoff_deadline_chapter, status);
