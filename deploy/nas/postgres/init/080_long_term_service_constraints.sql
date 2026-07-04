CREATE UNIQUE INDEX IF NOT EXISTS idx_review_council_project_name
  ON review_council_configs(project_id, name);

CREATE INDEX IF NOT EXISTS idx_revision_tasks_project_status
  ON revision_tasks(project_id, status, severity);

CREATE INDEX IF NOT EXISTS idx_reference_sources_workspace_project
  ON reference_sources(workspace_id, project_id, source_type);

CREATE INDEX IF NOT EXISTS idx_reference_items_project_type
  ON reference_items(project_id, item_type);
