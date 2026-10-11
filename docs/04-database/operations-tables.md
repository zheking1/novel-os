# Operations & Infrastructure Tables

## Memory & Vector

### `memory_chunks`
| Column | Type | Constraints |
|---|---|---|
| id | UUID | PK |
| project_id | UUID | NOT NULL, FK projects(id) CASCADE |
| source_type | TEXT | NOT NULL |
| source_id | UUID |  |
| chunk_key | TEXT | NOT NULL |
| content | TEXT | NOT NULL |
| qdrant_collection | TEXT |  |
| qdrant_point_id | TEXT |  |
| metadata | JSONB | NOT NULL, DEFAULT {} |
| search_vector | TSVECTOR | GENERATED: to_tsvector(simple, content) |
| created_at | TIMESTAMPTZ | NOT NULL |
**UNIQUE**: (project_id, chunk_key) | **Indexes**: GIN(search_vector), GIN(metadata), idx_memory_chunks_source

### `memory_chunk_index_history`
| Column | Type | Constraints |
|---|---|---|
| id | UUID | PK |
| chunk_id | UUID | NOT NULL |
| project_id | UUID | NOT NULL |
| operation | VARCHAR(50) | DEFAULT index |
| old_point_id | VARCHAR(255) |  |
| new_point_id | VARCHAR(255) |  |
| collection | VARCHAR(255) |  |
| status | VARCHAR(50) | DEFAULT success |
| error_message | TEXT |  |
| indexed_at | TIMESTAMP |  |
**Indexes**: chunk, project, indexed_at

## Vector Index Management

### `vector_index_jobs`
| Column | Type | Constraints |
|---|---|---|
| id | UUID | PK |
| project_id | UUID | NOT NULL, FK projects(id) CASCADE |
| source_type | TEXT | NOT NULL |
| source_id | UUID |  |
| chunk_id | UUID | FK memory_chunks(id) CASCADE |
| collection | TEXT | NOT NULL |
| status | TEXT | NOT NULL, DEFAULT pending |
| error | TEXT |  |
| created_at | TIMESTAMPTZ | NOT NULL |
| updated_at | TIMESTAMPTZ | NOT NULL |

### `vector_index_tasks`
| Column | Type | Constraints |
|---|---|---|
| id | UUID | PK |
| project_id | UUID | NOT NULL |
| chunk_id | UUID | NOT NULL |
| collection | VARCHAR(255) | NOT NULL |
| status | VARCHAR(50) | DEFAULT pending |
| priority | INTEGER | DEFAULT 0 |
| attempts | INTEGER | DEFAULT 0 |
| max_attempts | INTEGER | DEFAULT 3 |
| error_message | TEXT |  |
| queued_at | TIMESTAMP |  |
| started_at | TIMESTAMP |  |
| completed_at | TIMESTAMP |  |
| last_error_at | TIMESTAMP |  |
| metadata | JSONB | DEFAULT {} |
| created_at | TIMESTAMP |  |
| updated_at | TIMESTAMP |  |

### `vector_index_status`
| Column | Type | Constraints |
|---|---|---|
| id | UUID | PK |
| project_id | UUID | NOT NULL |
| collection | VARCHAR(255) | NOT NULL |
| total_chunks | INTEGER | DEFAULT 0 |
| indexed_chunks | INTEGER | DEFAULT 0 |
| failed_chunks | INTEGER | DEFAULT 0 |
| last_indexed_at | TIMESTAMP |  |
| last_full_reindex_at | TIMESTAMP |  |
| is_incremental | BOOLEAN | DEFAULT TRUE |
| index_version | INTEGER | DEFAULT 1 |
| metadata | JSONB | DEFAULT {} |
| created_at | TIMESTAMP |  |
| updated_at | TIMESTAMP |  |
**UNIQUE**: (project_id, collection)

### `vector_index_config`
| Column | Type | Constraints |
|---|---|---|
| id | UUID | PK |
| project_id | UUID | NOT NULL |
| collection | VARCHAR(255) | NOT NULL |
| batch_size | INTEGER | DEFAULT 100 |
| retry_delay_seconds | INTEGER | DEFAULT 60 |
| max_concurrent | INTEGER | DEFAULT 5 |
| priority_enabled | BOOLEAN | DEFAULT TRUE |
| auto_retry | BOOLEAN | DEFAULT TRUE |
| enabled | BOOLEAN | DEFAULT TRUE |
| created_at | TIMESTAMP |  |
| updated_at | TIMESTAMP |  |
**UNIQUE**: (project_id, collection)

## Backup & Restore

### `backup_records`
| Column | Type | Constraints |
|---|---|---|
| id | UUID | PK |
| project_id | UUID |  |
| backup_type | VARCHAR(50) | NOT NULL, full/incremental/config/project_export |
| storage_path | TEXT |  |
| storage_type | VARCHAR(50) | DEFAULT local |
| status | VARCHAR(50) | DEFAULT pending, flow: pending->in_progress->completed/failed |
| file_size_bytes | BIGINT |  |
| file_count | INTEGER |  |
| checksum | VARCHAR(255) |  |
| compression_type | VARCHAR(50) |  |
| started_at | TIMESTAMP |  |
| completed_at | TIMESTAMP |  |
| error_message | TEXT |  |
| metadata | JSONB | DEFAULT {} |
| created_at | TIMESTAMP |  |

### `backup_schedules`
| Column | Type | Constraints |
|---|---|---|
| id | UUID | PK |
| schedule_name | VARCHAR(255) | NOT NULL |
| project_id | UUID |  |
| backup_type | VARCHAR(50) | NOT NULL, DEFAULT incremental |
| schedule_type | VARCHAR(50) | NOT NULL, DEFAULT daily |
| cron_expression | VARCHAR(100) |  |
| retention_count | INTEGER | DEFAULT 7 |
| retention_days | INTEGER | DEFAULT 30 |
| storage_path | TEXT |  |
| storage_type | VARCHAR(50) | DEFAULT local |
| enabled | BOOLEAN | DEFAULT TRUE |
| last_run_at | TIMESTAMP |  |
| next_run_at | TIMESTAMP |  |
| created_at | TIMESTAMP |  |
| updated_at | TIMESTAMP |  |

### `restore_records`
| Column | Type | Constraints |
|---|---|---|
| id | UUID | PK |
| backup_record_id | UUID | NOT NULL |
| project_id | UUID | NOT NULL |
| restore_type | VARCHAR(50) | NOT NULL, DEFAULT full |
| status | VARCHAR(50) | DEFAULT pending |
| tables_restored | JSONB | DEFAULT [] |
| records_restored_count | BIGINT |  |
| started_at | TIMESTAMP |  |
| completed_at | TIMESTAMP |  |
| error_message | TEXT |  |
| performed_by | VARCHAR(255) |  |
| metadata | JSONB | DEFAULT {} |
| created_at | TIMESTAMP |  |

### `project_export_records`
| Column | Type | Constraints |
|---|---|---|
| id | UUID | PK |
| project_id | UUID | NOT NULL |
| export_format | VARCHAR(50) | NOT NULL, DEFAULT json |
| export_type | VARCHAR(50) | NOT NULL, DEFAULT full |
| storage_path | TEXT |  |
| file_size_bytes | BIGINT |  |
| status | VARCHAR(50) | DEFAULT pending |
| started_at | TIMESTAMP |  |
| completed_at | TIMESTAMP |  |
| error_message | TEXT |  |
| metadata | JSONB | DEFAULT {} |
| created_at | TIMESTAMP |  |

## Archive & Data Tiers

### `data_tier_config`
| Column | Type | Constraints |
|---|---|---|
| id | UUID | PK |
| project_id | UUID | NOT NULL |
| tier | VARCHAR(50) | NOT NULL, DEFAULT active |
| table_name | VARCHAR(255) | NOT NULL |
| retention_days | INTEGER | DEFAULT 365 |
| archive_condition | JSONB | DEFAULT {} |
| auto_archive | BOOLEAN | DEFAULT TRUE |
| enabled | BOOLEAN | DEFAULT TRUE |
| created_at | TIMESTAMP |  |
| updated_at | TIMESTAMP |  |
**UNIQUE**: (project_id, tier, table_name)

### `archive_history`
| Column | Type | Constraints |
|---|---|---|
| id | UUID | PK |
| project_id | UUID | NOT NULL |
| table_name | VARCHAR(255) | NOT NULL |
| operation | VARCHAR(50) | NOT NULL, archive/restore/delete/tier_change |
| from_tier | VARCHAR(50) |  |
| to_tier | VARCHAR(50) |  |
| record_count | INTEGER | DEFAULT 0 |
| archive_path | TEXT |  |
| status | VARCHAR(50) | DEFAULT success |
| error_message | TEXT |  |
| performed_by | VARCHAR(255) |  |
| metadata | JSONB | DEFAULT {} |
| created_at | TIMESTAMP |  |

### `volume_archive_status`
| Column | Type | Constraints |
|---|---|---|
| id | UUID | PK |
| project_id | UUID | NOT NULL |
| volume_no | INTEGER | NOT NULL |
| volume_title | VARCHAR(500) |  |
| status | VARCHAR(50) | DEFAULT active |
| tier | VARCHAR(50) | DEFAULT active |
| chapter_count | INTEGER | DEFAULT 0 |
| word_count | INTEGER | DEFAULT 0 |
| archived_at | TIMESTAMP |  |
| archived_by | VARCHAR(255) |  |
| metadata | JSONB | DEFAULT {} |
| created_at | TIMESTAMP |  |
| updated_at | TIMESTAMP |  |
**UNIQUE**: (project_id, volume_no)

### `archive_schedules`
| Column | Type | Constraints |
|---|---|---|
| id | UUID | PK |
| project_id | UUID |  |
| schedule_name | VARCHAR(255) | NOT NULL |
| schedule_type | VARCHAR(50) | NOT NULL |
| cron_expression | VARCHAR(100) |  |
| tier_target | VARCHAR(50) | NOT NULL |
| tables_to_archive | JSONB | DEFAULT [] |
| retention_days | INTEGER | DEFAULT 365 |
| enabled | BOOLEAN | DEFAULT TRUE |
| last_run_at | TIMESTAMP |  |
| next_run_at | TIMESTAMP |  |
| created_at | TIMESTAMP |  |
| updated_at | TIMESTAMP |  |

## Setting System (Global 160)

### `setting_categories`
| Column | Type | Constraints |
|---|---|---|
| id | UUID | PK |
| workspace_id | UUID | NOT NULL, FK workspaces(id) CASCADE |
| name | TEXT | NOT NULL |
| slug | TEXT | NOT NULL |
| description | TEXT |  |
| icon | TEXT | DEFAULT 📁 |
| sort_order | INTEGER | NOT NULL, DEFAULT 0 |
| is_active | BOOLEAN | NOT NULL, DEFAULT TRUE |
| is_standard | BOOLEAN | NOT NULL, DEFAULT FALSE |
| metadata | JSONB | DEFAULT {} |
| created_by | UUID | FK users(id) SET NULL |
| created_at | TIMESTAMPTZ |  |
| updated_at | TIMESTAMPTZ |  |
**UNIQUE**: (workspace_id, slug) | **Seed**: 9 standard cats (genre-inference..review-rules)

### `setting_field_definitions`
| Column | Type | Constraints |
|---|---|---|
| id | UUID | PK |
| category_id | UUID | NOT NULL, FK setting_categories(id) CASCADE |
| field_name | TEXT | NOT NULL |
| field_key | TEXT | NOT NULL |
| field_type | TEXT | NOT NULL, CHECK: text/textarea/select/multiselect/number/boolean/json |
| options | JSONB | DEFAULT [] |
| is_required | BOOLEAN | DEFAULT FALSE |
| is_searchable | BOOLEAN | DEFAULT FALSE |
| default_value | TEXT |  |
| placeholder | TEXT |  |
| help_text | TEXT |  |
| sort_order | INTEGER | DEFAULT 0 |
| metadata | JSONB | DEFAULT {} |
| created_at | TIMESTAMPTZ |  |
| updated_at | TIMESTAMPTZ |  |
**UNIQUE**: (category_id, field_key) | **Seed**: 43 field definitions

### `setting_items`
| Column | Type | Constraints |
|---|---|---|
| id | UUID | PK |
| category_id | UUID | NOT NULL, FK setting_categories(id) CASCADE |
| workspace_id | UUID | NOT NULL, FK workspaces(id) CASCADE |
| item_code | TEXT |  |
| keywords | TEXT[] | DEFAULT {} |
| intent_synonyms | TEXT[] | DEFAULT {} |
| core_summary | TEXT | NOT NULL |
| detailed_expansion | TEXT |  |
| ai_instruction | TEXT |  |
| poison_points | TEXT[] | DEFAULT {} |
| level | TEXT | NOT NULL, DEFAULT knowledge, CHECK: knowledge/reminder/defect_compensation |
| applicable_skills | TEXT[] | DEFAULT {} |
| applicable_genres | TEXT[] | DEFAULT {} |
| data | JSONB | DEFAULT {} |
| tags | TEXT[] | DEFAULT {} |
| is_global | BOOLEAN | DEFAULT TRUE |
| sort_order | INTEGER | DEFAULT 0 |
| metadata | JSONB | DEFAULT {} |
| created_by | UUID | FK users(id) SET NULL |
| updated_by | UUID | FK users(id) SET NULL |
| created_at | TIMESTAMPTZ |  |
| updated_at | TIMESTAMPTZ |  |
**UNIQUE**: (workspace_id, item_code), (category_id, item_code) | **Indexes**: GIN on keywords, synonyms, points, tags, skills, genres | **Seed**: 6 items

### `setting_category_relations`
| Column | Type | Constraints |
|---|---|---|
| id | UUID | PK |
| parent_category_id | UUID | NOT NULL, FK setting_categories(id) CASCADE |
| child_category_id | UUID | NOT NULL, FK setting_categories(id) CASCADE |
| relation_type | TEXT | NOT NULL, DEFAULT contains, CHECK: contains/related/conflicts |
| metadata | JSONB | DEFAULT {} |
| created_at | TIMESTAMPTZ |  |
**UNIQUE**: (parent_category_id, child_category_id)

### `genre_canonical`
| Column | Type | Constraints |
|---|---|---|
| canonical_genre | TEXT | PK |
| platform_tags | TEXT[] | DEFAULT {} |
| aliases | TEXT[] | DEFAULT {} |
| description | TEXT |  |
| metadata | JSONB | DEFAULT {} |
| created_at | TIMESTAMPTZ |  |
| updated_at | TIMESTAMPTZ |  |
**Indexes**: GIN on platform_tags, aliases | **Seed**: 15 genres

## Model Management
### model_profiles
| providers | model_name | task_types | tier | is_default | is_system | forked_from_system_key | user_id | status |
|---|---|---|---|---|---|---|---|---|---|
Key columns: profile_key (UNIQUE with project_id), provider, model_name, task_types (TEXT[]), tier (standard/premium), default_params/cost_config/rate_limit_config (JSONB), is_system (boolean, from 220), forked_from_system_key (from 220), user_id (from 213)
UNIQUE: (project_id, profile_key)

### model_route_rules
UNIQUE: (project_id, task_type, profile_key)

### model_usage_records
Tracks: input_tokens, output_tokens, cached_tokens, total_tokens, cost_amount NUMERIC(12,6), currency, latency_ms, success

## Knowledge Entity System (205)
### ref_categories: Knowledge categories (history, era, genre, professional, writing) with child subcategories (historical_figure, politics, xianxia, etc.). parent_id self-FK.
### knowledge_entities: entity_type, name, aliases, summary, content, structured_data (JSONB), source, source_url, reliability (FLOAT), genre_tags, era, embedding_id, search_vector TSVECTOR (GENERATED), status
### knowledge_relations: from_entity_id FK knowledge_entities CASCADE, to_entity_id FK knowledge_entities CASCADE, relation_type, strength
UNIQUE: (from_entity_id, to_entity_id, relation_type)
### universal_knowledge: category_id FK ref_categories SET NULL, topic, summary, content, structured_data (JSONB), era, year_range (INT[]), genre_tags, source, source_url, reliability (FLOAT), last_verified_at, embedding_id, search_vector TSVECTOR (GENERATED), tags, status, use_count
### project_knowledge: project_id, category, key, value (JSONB), description, chapter_no, related_entry_ids (UUID[]), tags, status
UNIQUE: (project_id, category, key)
### world_snapshots: project_id, chapter_no, story_time, story_year, story_era, story_progress, world_state (JSONB), character_count, active_threads (TEXT[]), relevant_knowledge_ids (UUID[])
### ref_search_jobs: project_id, query_text, search_context, category_id FK ref_categories SET NULL, status, results_count, entries_created, error_message, triggered_by, chapter_no, completed_at
### ref_gap_logs: project_id, gap_type, description, context, entity_name, entity_type, resolved (BOOLEAN), resolved_by_entry_id, resolved_at

## Knowledge Pack System (207)
### genre_knowledge_config: id, genre (VARCHAR(50) UNIQUE), included_categories (TEXT[]), excluded_categories (TEXT[]), description
Seed: 8 types (18: Mahmoud/snd/star/aolty/abi/jmt/lu/science)
### project_knowledge_pack: id, project_id UNIQUE, genre, active_categories (TEXT[]), custom_categories (JSONB)

## User Knowledge (194)
### user_knowledge: id PK, user_id FK users CASCADE, base_knowledge_id FK knowledge_base SET NULL, code, title, content, summary, detail, examples, counter_examples, metadata (JSONB), category_id FK categories, applicable_genres (TEXT[]), applicable_skills (TEXT[]), level (knowledge/reminder/defect_compensation), status (draft/active/submitted), review_status (pending/approved/rejected), review_comment, view_count, use_count, source, created_at, updated_at
Trigger: update_user_knowledge_updated_at
### knowledge_review: id PK, user_knowledge_id FK user_knowledge CASCADE, submitter_id FK users, submit_time, submit_reason, reviewer_id FK users, review_time, review_status (pending/approved/rejected), review_comment, merged_base_id FK knowledge_base, version, created_at

## Events Archive (204)
### events_archive: id PK, project_id FK projects CASCADE, chapter_id NOT NULL, event_order INT NOT NULL, title, summary, characters (TEXT[]), locations (TEXT[]), metadata (JSONB), archived_at

## Skills (212)
### skills: id PK, name (VARCHAR(100) UNIQUE), description, content, trigger_words (TEXT[]), tool_hints (TEXT[]), embedding_id, is_active, sort_order
### skill_steps: id PK, skill_id FK skills CASCADE, step_order INT NOT NULL, step_name VARCHAR(100) NOT NULL, tool_name, description, parameters (JSONB), optional (BOOLEAN), conditional
UNIQUE: (skill_id, step_order)

## Local Storage (206, 207)
### local_projects: id PK, project_id UNIQUE, local_root VARCHAR(500) NOT NULL, last_scan_at, file_count, total_words, chapter_count
### chapter_index: id PK, project_id, chapter_no, volume_no, title, status, word_count, summary, local_path, outline_path, pov_mode
UNIQUE: (project_id, chapter_no)
### review_index: id PK, project_id, chapter_id FK chapter_index CASCADE, chapter_no, model_name, score (FLOAT 0-100), passed (BOOLEAN), issues (JSONB), summary, local_path
### setting_index: id PK, project_id, category, name (VARCHAR(200) NOT NULL), keywords (TEXT[]), summary, local_path, structured_data (JSONB)

## Offline (170)
### offline_sync_sessions: id PK, project_id, session_name, description, status (active/syncing/completed/partial/failed), total_changes, synced_changes, created_by, synced_at
### offline_change_queue: id PK, session_id, change_type (upsert/delete/archive), entity_type, entity_id, change_data (JSONB), status (pending/synced/failed/conflict), conflict_reason, synced_at
### voice_drafts: id PK, project_id, chapter_no, audio_data (TEXT base64), transcription TEXT NOT NULL, confidence FLOAT, duration_seconds, status (draft/converted/merged/discarded), converted_to_chapter_id
### relationship_graph_configs: id PK, project_id, config_name, layout_type (force/hierarchical/circular), node_colors (JSONB), edge_styles (JSONB), visible_entity_types (TEXT[]), visible_relationship_types (TEXT[]), is_default
UNIQUE: (project_id, config_name)
### template_marketplace: id PK, template_id, project_id, template_key, category, tags (TEXT[]), download_count, rating (FLOAT), is_featured (BOOLEAN), is_verified (BOOLEAN)

## Tests (170)
### automated_test_results: id PK, project_id, test_suite, test_name, status (passed/failed/skipped), duration_ms, error_message, stack_trace
### performance_test_results: id PK, project_id, test_name, test_type (load/stress/endurance/memory), metric_name, metric_value (FLOAT), metric_unit, threshold_value, threshold_exceeded (BOOLEAN), test_config (JSONB)
