ALTER TABLE volumes ADD COLUMN IF NOT EXISTS start_chapter_no INTEGER;
ALTER TABLE volumes ADD COLUMN IF NOT EXISTS end_chapter_no INTEGER;
ALTER TABLE volumes ADD COLUMN IF NOT EXISTS summary TEXT;
ALTER TABLE volumes ADD COLUMN IF NOT EXISTS goals JSONB NOT NULL DEFAULT '[]'::jsonb;

CREATE INDEX IF NOT EXISTS idx_volumes_project_status
  ON volumes(project_id, status, volume_no);

CREATE INDEX IF NOT EXISTS idx_volumes_chapter_range
  ON volumes(project_id, start_chapter_no, end_chapter_no);

ALTER TABLE plot_threads ADD COLUMN IF NOT EXISTS volume_no INTEGER;
ALTER TABLE plot_threads ADD COLUMN IF NOT EXISTS start_chapter_no INTEGER;
ALTER TABLE plot_threads ADD COLUMN IF NOT EXISTS current_chapter_no INTEGER;
ALTER TABLE plot_threads ADD COLUMN IF NOT EXISTS last_advanced_chapter_no INTEGER;
ALTER TABLE plot_threads ADD COLUMN IF NOT EXISTS expected_next_chapter_no INTEGER;
ALTER TABLE plot_threads ADD COLUMN IF NOT EXISTS stalled_after_chapters INTEGER NOT NULL DEFAULT 20;
ALTER TABLE plot_threads ADD COLUMN IF NOT EXISTS related_entity_ids TEXT[] NOT NULL DEFAULT ARRAY[]::TEXT[];
ALTER TABLE plot_threads ADD COLUMN IF NOT EXISTS related_foreshadowing_ids TEXT[] NOT NULL DEFAULT ARRAY[]::TEXT[];

CREATE INDEX IF NOT EXISTS idx_plot_threads_project_status
  ON plot_threads(project_id, status, thread_type, importance);

CREATE INDEX IF NOT EXISTS idx_plot_threads_progress
  ON plot_threads(project_id, volume_no, last_advanced_chapter_no);
