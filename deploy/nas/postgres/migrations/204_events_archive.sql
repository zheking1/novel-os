-- Events Archive Table for Cold Data Archiving

CREATE TABLE IF NOT EXISTS events_archive (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    project_id UUID NOT NULL REFERENCES projects(id) ON DELETE CASCADE,
    chapter_id UUID NOT NULL,
    event_order INTEGER NOT NULL,
    title TEXT,
    summary TEXT,
    characters TEXT[] DEFAULT '{}',
    locations TEXT[] DEFAULT '{}',
    metadata JSONB DEFAULT '{}'::jsonb,
    archived_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE INDEX IF NOT EXISTS idx_events_archive_project
    ON events_archive(project_id, chapter_id);
