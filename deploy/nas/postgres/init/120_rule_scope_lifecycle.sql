ALTER TABLE canon_rules ADD COLUMN IF NOT EXISTS scope_type TEXT NOT NULL DEFAULT 'global';
ALTER TABLE canon_rules ADD COLUMN IF NOT EXISTS scope_ref TEXT;
ALTER TABLE canon_rules ADD COLUMN IF NOT EXISTS scope_config JSONB NOT NULL DEFAULT '{}'::jsonb;
ALTER TABLE canon_rules ADD COLUMN IF NOT EXISTS priority INTEGER NOT NULL DEFAULT 100;
ALTER TABLE canon_rules ADD COLUMN IF NOT EXISTS effective_chapter_no INTEGER;
ALTER TABLE canon_rules ADD COLUMN IF NOT EXISTS expire_chapter_no INTEGER;
ALTER TABLE canon_rules ADD COLUMN IF NOT EXISTS effective_volume_no INTEGER;
ALTER TABLE canon_rules ADD COLUMN IF NOT EXISTS expire_volume_no INTEGER;
ALTER TABLE canon_rules ADD COLUMN IF NOT EXISTS is_temporary BOOLEAN NOT NULL DEFAULT false;
ALTER TABLE canon_rules ADD COLUMN IF NOT EXISTS active_from_event TEXT;
ALTER TABLE canon_rules ADD COLUMN IF NOT EXISTS expire_on_event TEXT;
ALTER TABLE canon_rules ADD COLUMN IF NOT EXISTS conflict_policy TEXT NOT NULL DEFAULT 'priority';
ALTER TABLE canon_rules ADD COLUMN IF NOT EXISTS supersedes_rule_ids TEXT[] NOT NULL DEFAULT ARRAY[]::TEXT[];
ALTER TABLE canon_rules ADD COLUMN IF NOT EXISTS blocked_by_rule_ids TEXT[] NOT NULL DEFAULT ARRAY[]::TEXT[];

CREATE INDEX IF NOT EXISTS idx_canon_rules_scope_lifecycle
  ON canon_rules(project_id, status, scope_type, effective_chapter_no, expire_chapter_no);

CREATE INDEX IF NOT EXISTS idx_canon_rules_priority
  ON canon_rules(project_id, status, priority);

CREATE INDEX IF NOT EXISTS idx_canon_rules_scope_config
  ON canon_rules USING GIN(scope_config);
