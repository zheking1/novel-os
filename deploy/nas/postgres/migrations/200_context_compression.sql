-- Progressive Context Compression
-- Layered memory: chapter → arc → volume → series

CREATE TABLE IF NOT EXISTS compressed_contexts (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    project_id UUID NOT NULL REFERENCES projects(id) ON DELETE CASCADE,
    compression_layer TEXT NOT NULL CHECK (compression_layer IN ('chapter_batch', 'arc', 'volume', 'series')),
    arc_key TEXT,
    volume_no INTEGER,
    chapter_range_start INTEGER,
    chapter_range_end INTEGER,
    content TEXT NOT NULL,
    source_count INTEGER NOT NULL DEFAULT 0,
    token_estimate INTEGER NOT NULL DEFAULT 0,
    metadata JSONB DEFAULT '{}'::jsonb,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT now(),

    UNIQUE (project_id, compression_layer, chapter_range_start, chapter_range_end)
);

CREATE INDEX IF NOT EXISTS idx_compressed_contexts_project_layer
    ON compressed_contexts(project_id, compression_layer);

CREATE INDEX IF NOT EXISTS idx_compressed_contexts_chapter_range
    ON compressed_contexts(project_id, chapter_range_start, chapter_range_end);

CREATE INDEX IF NOT EXISTS idx_compressed_contexts_volume
    ON compressed_contexts(project_id, volume_no) WHERE compression_layer = 'volume';

CREATE INDEX IF NOT EXISTS idx_compressed_contexts_arc_key
    ON compressed_contexts(project_id, arc_key) WHERE compression_layer = 'arc';
