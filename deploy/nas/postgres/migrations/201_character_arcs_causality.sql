-- Character Arc Tracking
-- Tracks dynamic character evolution

CREATE TABLE IF NOT EXISTS character_arcs (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    project_id UUID NOT NULL REFERENCES projects(id) ON DELETE CASCADE,
    entity_id UUID NOT NULL REFERENCES state_entities(id) ON DELETE CASCADE,
    chapter_no INTEGER NOT NULL,
    arc_type TEXT NOT NULL CHECK (arc_type IN ('emotion', 'relationship', 'power', 'personality', 'goal', 'custom')),
    state JSONB NOT NULL DEFAULT '{}'::jsonb,
    change_summary TEXT,
    trigger_event TEXT,
    metadata JSONB DEFAULT '{}'::jsonb,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE INDEX IF NOT EXISTS idx_character_arcs_project_entity
    ON character_arcs(project_id, entity_id, arc_type);

CREATE INDEX IF NOT EXISTS idx_character_arcs_chapter
    ON character_arcs(project_id, chapter_no);

CREATE INDEX IF NOT EXISTS idx_character_arcs_type_chapter
    ON character_arcs(project_id, arc_type, chapter_no);

-- Causality Chain Tracking
-- Tracks causal relationships between events

CREATE TABLE IF NOT EXISTS causality_chains (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    project_id UUID NOT NULL REFERENCES projects(id) ON DELETE CASCADE,
    cause_event_id UUID,
    cause_chapter_no INTEGER,
    cause_title TEXT,
    effect_event_id UUID,
    effect_chapter_no INTEGER,
    effect_title TEXT,
    causal_type TEXT NOT NULL DEFAULT 'direct' CHECK (causal_type IN ('direct', 'indirect', 'triggered', 'enabled', 'prevented')),
    strength REAL NOT NULL DEFAULT 1.0 CHECK (strength >= 0 AND strength <= 1),
    description TEXT,
    metadata JSONB DEFAULT '{}'::jsonb,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE INDEX IF NOT EXISTS idx_causality_chains_project
    ON causality_chains(project_id, cause_chapter_no, effect_chapter_no);

CREATE INDEX IF NOT EXISTS idx_causality_chains_cause
    ON causality_chains(project_id, cause_event_id);

CREATE INDEX IF NOT EXISTS idx_causality_chains_effect
    ON causality_chains(project_id, effect_event_id);

-- Multi-Pass Generation
-- Records each generation pass for pipeline tracking

CREATE TABLE IF NOT EXISTS generation_passes (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    project_id UUID NOT NULL REFERENCES projects(id) ON DELETE CASCADE,
    chapter_no INTEGER NOT NULL,
    pass_number INTEGER NOT NULL CHECK (pass_number BETWEEN 1 AND 4),
    pass_type TEXT NOT NULL CHECK (pass_type IN ('planning', 'drafting', 'polishing', 'verification')),
    content TEXT,
    status TEXT NOT NULL DEFAULT 'done',
    metadata JSONB DEFAULT '{}'::jsonb,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE INDEX IF NOT EXISTS idx_generation_passes_project_chapter
    ON generation_passes(project_id, chapter_no, pass_number);
