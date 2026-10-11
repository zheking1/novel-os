# Content & Writing Tables

## Context Compression

### `compressed_contexts`
| Column | Type | Constraints |
|---|---|---|
| id | UUID | PK |
| project_id | UUID | NOT NULL, FK projects(id) CASCADE |
| compression_layer | TEXT | NOT NULL, CHECK: chapter_batch/arc/volume/series |
| arc_key | TEXT |  |
| volume_no | INTEGER |  |
| chapter_range_start | INTEGER |  |
| chapter_range_end | INTEGER |  |
| content | TEXT | NOT NULL |
| source_count | INTEGER | NOT NULL, DEFAULT 0 |
| token_estimate | INTEGER | NOT NULL, DEFAULT 0 |
| metadata | JSONB | DEFAULT {} |
| created_at | TIMESTAMPTZ | NOT NULL |
| updated_at | TIMESTAMPTZ | NOT NULL |
**UNIQUE**: (project_id, compression_layer, chapter_range_start, chapter_range_end)
**Indexes**: 4 partial indexes

## Pacing & Emotion

### `pacing_blueprints`
| Column | Type | Constraints |
|---|---|---|
| id | UUID | PK |
| project_id | UUID | NOT NULL, FK projects(id) CASCADE |
| volume_no | INTEGER | NOT NULL |
| blueprint | JSONB | NOT NULL, DEFAULT {} |
| created_at | TIMESTAMPTZ |  |
| updated_at | TIMESTAMPTZ |  |
**UNIQUE**: (project_id, volume_no)

### `chapter_emotions`
| Column | Type | Constraints |
|---|---|---|
| id | UUID | PK |
| project_id | UUID | NOT NULL, FK projects(id) CASCADE |
| chapter_no | INTEGER | NOT NULL |
| tension | REAL | NOT NULL, DEFAULT 0.5, CHECK 0<=t<=1 |
| emotion | TEXT | NOT NULL, DEFAULT neutral |
| emotion_intensity | REAL | NOT NULL, DEFAULT 0.5, CHECK 0<=i<=1 |
| pacing_type | TEXT | NOT NULL, DEFAULT normal, CHECK: buildup/climax/breather/transition/climax_buildup/resolution/normal |
| word_count | INTEGER |  |
| metadata | JSONB | DEFAULT {} |
| created_at | TIMESTAMPTZ |  |
| updated_at | TIMESTAMPTZ |  |
**UNIQUE**: (project_id, chapter_no) | **Indexes**: idx_chapter_emotions_project_chapter, idx_chapter_emotions_pacing

## Style Profiles & Metrics

### `style_profiles`
| Column | Type | Constraints |
|---|---|---|
| id | UUID | PK |
| project_id | UUID | NOT NULL, FK projects(id) CASCADE |
| profile_name | TEXT | NOT NULL, DEFAULT default |
| narrative_pov | TEXT | NOT NULL, DEFAULT third_limited, CHECK: first/second/third_limited/third_omniscient/multiple |
| tense | TEXT | NOT NULL, DEFAULT past, CHECK: past/present/mixed |
| tone | TEXT | NOT NULL, DEFAULT neutral |
| target_metrics | JSONB | DEFAULT {} |
| created_at | TIMESTAMPTZ |  |
| updated_at | TIMESTAMPTZ |  |
**UNIQUE**: (project_id, profile_name)

### `chapter_style_metrics`
| Column | Type | Constraints |
|---|---|---|
| id | UUID | PK |
| project_id | UUID | NOT NULL, FK projects(id) CASCADE |
| chapter_no | INTEGER | NOT NULL |
| style_data | JSONB | NOT NULL, DEFAULT {} |
| created_at | TIMESTAMPTZ |  |
| updated_at | TIMESTAMPTZ |  |
**UNIQUE**: (project_id, chapter_no)

## Character Arcs & Causality

### `character_arcs`
| Column | Type | Constraints |
|---|---|---|
| id | UUID | PK |
| project_id | UUID | NOT NULL, FK projects(id) CASCADE |
| entity_id | UUID | NOT NULL, FK state_entities(id) CASCADE |
| chapter_no | INTEGER | NOT NULL |
| arc_type | TEXT | NOT NULL, CHECK: emotion/relationship/power/personality/goal/custom |
| state | JSONB | NOT NULL, DEFAULT {} |
| change_summary | TEXT |  |
| trigger_event | TEXT |  |
| metadata | JSONB | DEFAULT {} |
| created_at | TIMESTAMPTZ | NOT NULL |
**Indexes**: idx_character_arcs_project_entity, idx_character_arcs_chapter, idx_character_arcs_type_chapter

### `causality_chains`
| Column | Type | Constraints |
|---|---|---|
| id | UUID | PK |
| project_id | UUID | NOT NULL, FK projects(id) CASCADE |
| cause_event_id | UUID |  |
| cause_chapter_no | INTEGER |  |
| cause_title | TEXT |  |
| effect_event_id | UUID |  |
| effect_chapter_no | INTEGER |  |
| effect_title | TEXT |  |
| causal_type | TEXT | NOT NULL, DEFAULT direct, CHECK: direct/indirect/triggered/enabled/prevented |
| strength | REAL | NOT NULL, DEFAULT 1.0, CHECK 0<=s<=1 |
| description | TEXT |  |
| metadata | JSONB | DEFAULT {} |
| created_at | TIMESTAMPTZ | NOT NULL |
**Indexes**: 3 indexes

## Generation Passes

### `generation_passes`
| Column | Type | Constraints |
|---|---|---|
| id | UUID | PK |
| project_id | UUID | NOT NULL, FK projects(id) CASCADE |
| chapter_no | INTEGER | NOT NULL |
| pass_number | INTEGER | NOT NULL, CHECK 1<=p<=4 |
| pass_type | TEXT | NOT NULL, CHECK: planning/drafting/polishing/verification |
| content | TEXT |  |
| status | TEXT | NOT NULL, DEFAULT done |
| metadata | JSONB | DEFAULT {} |
| created_at | TIMESTAMPTZ | NOT NULL |
| updated_at | TIMESTAMPTZ | NOT NULL |
**Indexes**: idx_generation_passes_project_chapter

## Chapter Tools

### `chapter_annotations`
| Column | Type | Constraints |
|---|---|---|
| id | UUID | PK |
| project_id | UUID | NOT NULL |
| chapter_id | UUID | NOT NULL |
| chapter_no | INTEGER | NOT NULL |
| annotation_type | VARCHAR(50) | NOT NULL, comment/note/revision/question |
| content | TEXT | NOT NULL |
| anchor_start | INTEGER |  |
| anchor_end | INTEGER |  |
| parent_id | UUID |  |
| resolve_status | VARCHAR(50) | DEFAULT open |
| resolved_by | VARCHAR(255) |  |
| resolved_at | TIMESTAMP |  |
| created_by | VARCHAR(255) |  |
| created_at | TIMESTAMP |  |
| updated_at | TIMESTAMP |  |

### `chapter_versions`
| Column | Type | Constraints |
|---|---|---|
| id | UUID | PK |
| project_id | UUID | NOT NULL |
| chapter_id | UUID | NOT NULL |
| chapter_no | INTEGER | NOT NULL |
| version_no | INTEGER | NOT NULL |
| content | TEXT | NOT NULL |
| word_count | INTEGER |  |
| change_summary | TEXT |  |
| created_by | VARCHAR(255) |  |
| created_at | TIMESTAMP |  |
**UNIQUE**: (chapter_id, version_no)

### `writing_stats`
| Column | Type | Constraints |
|---|---|---|
| id | UUID | PK |
| project_id | UUID | NOT NULL |
| stat_date | DATE | NOT NULL |
| stat_type | VARCHAR(50) | NOT NULL, daily/volume/arc |
| chapter_no | INTEGER |  |
| volume_no | INTEGER |  |
| word_count | INTEGER | DEFAULT 0 |
| chapters_completed | INTEGER | DEFAULT 0 |
| metadata | JSONB | DEFAULT {} |
| created_at | TIMESTAMP |  |
**UNIQUE**: (project_id, stat_date, stat_type, chapter_no)

### `proper_nouns`
| Column | Type | Constraints |
|---|---|---|
| id | UUID | PK |
| project_id | UUID | NOT NULL |
| noun_key | VARCHAR(255) | NOT NULL |
| noun_value | VARCHAR(500) | NOT NULL |
| noun_type | VARCHAR(50) | NOT NULL, character_name/place_name/faction_name/item_name/term |
| aliases | TEXT[] | DEFAULT {} |
| description | TEXT |  |
| locked | BOOLEAN | DEFAULT FALSE |
| usage_count | INTEGER | DEFAULT 0 |
| first_chapter_no | INTEGER |  |
| created_by | VARCHAR(255) |  |
| created_at | TIMESTAMP |  |
| updated_at | TIMESTAMP |  |
**UNIQUE**: (project_id, noun_key)

### `fulltext_search_records`
| Column | Type | Constraints |
|---|---|---|
| id | UUID | PK |
| project_id | UUID | NOT NULL |
| source_type | VARCHAR(50) | NOT NULL |
| source_id | UUID | NOT NULL |
| source_key | VARCHAR(255) |  |
| title | VARCHAR(500) |  |
| content | TEXT |  |
| search_vector | tsvector |  |
| metadata | JSONB | DEFAULT {} |
| updated_at | TIMESTAMP |  |
**UNIQUE**: (source_type, source_id) | **Trigger**: trg_fulltext_search_vector
