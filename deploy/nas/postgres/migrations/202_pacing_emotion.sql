-- Pacing & Emotion Curve Modeling

CREATE TABLE IF NOT EXISTS pacing_blueprints (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    project_id UUID NOT NULL REFERENCES projects(id) ON DELETE CASCADE,
    volume_no INTEGER NOT NULL,
    blueprint JSONB NOT NULL DEFAULT '{}'::jsonb,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    UNIQUE (project_id, volume_no)
);

CREATE INDEX IF NOT EXISTS idx_pacing_blueprints_project
    ON pacing_blueprints(project_id, volume_no);

CREATE TABLE IF NOT EXISTS chapter_emotions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    project_id UUID NOT NULL REFERENCES projects(id) ON DELETE CASCADE,
    chapter_no INTEGER NOT NULL,
    tension REAL NOT NULL DEFAULT 0.5 CHECK (tension >= 0 AND tension <= 1),
    emotion TEXT NOT NULL DEFAULT 'neutral',
    emotion_intensity REAL NOT NULL DEFAULT 0.5 CHECK (emotion_intensity >= 0 AND emotion_intensity <= 1),
    pacing_type TEXT NOT NULL DEFAULT 'normal' CHECK (pacing_type IN ('buildup', 'climax', 'breather', 'transition', 'climax_buildup', 'resolution', 'normal')),
    word_count INTEGER,
    metadata JSONB DEFAULT '{}'::jsonb,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    UNIQUE (project_id, chapter_no)
);

CREATE INDEX IF NOT EXISTS idx_chapter_emotions_project_chapter
    ON chapter_emotions(project_id, chapter_no);

CREATE INDEX IF NOT EXISTS idx_chapter_emotions_pacing
    ON chapter_emotions(project_id, pacing_type, chapter_no);
