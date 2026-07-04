-- Style Consistency Fingerprinting

CREATE TABLE IF NOT EXISTS style_profiles (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    project_id UUID NOT NULL REFERENCES projects(id) ON DELETE CASCADE,
    profile_name TEXT NOT NULL DEFAULT 'default',
    narrative_pov TEXT NOT NULL DEFAULT 'third_limited' CHECK (narrative_pov IN ('first', 'second', 'third_limited', 'third_omniscient', 'multiple')),
    tense TEXT NOT NULL DEFAULT 'past' CHECK (tense IN ('past', 'present', 'mixed')),
    tone TEXT NOT NULL DEFAULT 'neutral',
    target_metrics JSONB DEFAULT '{}'::jsonb,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    UNIQUE (project_id, profile_name)
);

CREATE INDEX IF NOT EXISTS idx_style_profiles_project
    ON style_profiles(project_id, profile_name);

CREATE TABLE IF NOT EXISTS chapter_style_metrics (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    project_id UUID NOT NULL REFERENCES projects(id) ON DELETE CASCADE,
    chapter_no INTEGER NOT NULL,
    style_data JSONB NOT NULL DEFAULT '{}'::jsonb,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    UNIQUE (project_id, chapter_no)
);

CREATE INDEX IF NOT EXISTS idx_chapter_style_metrics_project
    ON chapter_style_metrics(project_id, chapter_no);
