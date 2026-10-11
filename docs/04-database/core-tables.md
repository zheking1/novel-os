# Core & Knowledge Base Tables

## Projects & Chapters

### `projects`
| Column | Type | Constraints |
|---|---|---|
| id | UUID | PK |
| workspace_id | UUID | FK workspaces(id) CASCADE |
| slug | TEXT | NOT NULL |
| title | TEXT | NOT NULL |
| description | TEXT |  |
| status | TEXT | NOT NULL, DEFAULT active |
| settings | JSONB | NOT NULL, DEFAULT {} |
| created_at | TIMESTAMPTZ | NOT NULL, DEFAULT now() |
| updated_at | TIMESTAMPTZ | NOT NULL, DEFAULT now() |

### `chapters`
| Column | Type | Constraints |
|---|---|---|
| id | UUID | PK |
| project_id | UUID | NOT NULL, FK projects(id) CASCADE |
| chapter_no | INTEGER | NOT NULL |
| volume_no | INTEGER |  |
| title | TEXT |  |
| status | TEXT | NOT NULL, DEFAULT planned |
| word_count | INTEGER | NOT NULL, DEFAULT 0 |
| source_path | TEXT |  |
| local_path_hint | TEXT |  |
| content_hash | TEXT |  |
| created_at | TIMESTAMPTZ | NOT NULL, DEFAULT now() |
| updated_at | TIMESTAMPTZ | NOT NULL, DEFAULT now() |
**UNIQUE**: (project_id, chapter_no) | **Indexes**: idx_chapters_project_no, idx_chapters_project_status

### `chapter_summaries`
| Column | Type | Constraints |
|---|---|---|
| id | UUID | PK |
| project_id | UUID | NOT NULL, FK projects(id) CASCADE |
| chapter_id | UUID | NOT NULL, FK chapters(id) CASCADE |
| summary_type | TEXT | NOT NULL, DEFAULT chapter |
| content | TEXT | NOT NULL |
| metadata | JSONB | NOT NULL, DEFAULT {} |
| created_at | TIMESTAMPTZ | NOT NULL, DEFAULT now() |
**UNIQUE**: (chapter_id, summary_type)

### `chapter_commits`
| Column | Type | Constraints |
|---|---|---|
| id | UUID | PK |
| project_id | UUID | NOT NULL, FK projects(id) CASCADE |
| chapter_id | UUID | NOT NULL, FK chapters(id) CASCADE |
| commit_no | INTEGER | NOT NULL |
| payload | JSONB | NOT NULL |
| accepted | BOOLEAN | NOT NULL, DEFAULT false |
| accepted_at | TIMESTAMPTZ |  |
| accepted_by | UUID | FK users(id) SET NULL |
| created_by | UUID | FK users(id) SET NULL |
| created_at | TIMESTAMPTZ | NOT NULL, DEFAULT now() |
**UNIQUE**: (chapter_id, commit_no)

### `volumes`
| Column | Type | Constraints |
|---|---|---|
| id | UUID | PK |
| project_id | UUID | NOT NULL, FK projects(id) CASCADE |
| volume_no | INTEGER | NOT NULL |
| title | TEXT |  |
| outline | TEXT |  |
| start_chapter_no | INTEGER |  |
| end_chapter_no | INTEGER |  |
| summary | TEXT |  |
| goals | JSONB | NOT NULL, DEFAULT [] |
| status | TEXT | NOT NULL, DEFAULT planned |
| metadata | JSONB | NOT NULL, DEFAULT {} |
| created_at | TIMESTAMPTZ | NOT NULL, DEFAULT now() |
| updated_at | TIMESTAMPTZ | NOT NULL, DEFAULT now() |
**UNIQUE**: (project_id, volume_no) | **Indexes**: idx_volumes_project_status, idx_volumes_chapter_range

### `plot_threads`
| Column | Type | Constraints |
|---|---|---|
| id | UUID | PK |
| project_id | UUID | NOT NULL, FK projects(id) CASCADE |
| key | TEXT | NOT NULL |
| title | TEXT | NOT NULL |
| thread_type | TEXT | NOT NULL, DEFAULT side |
| status | TEXT | NOT NULL, DEFAULT open |
| importance | TEXT | NOT NULL, DEFAULT medium |
| volume_no | INTEGER |  |
| start_chapter_no | INTEGER |  |
| current_chapter_no | INTEGER |  |
| last_advanced_chapter_no | INTEGER |  |
| expected_next_chapter_no | INTEGER |  |
| stalled_after_chapters | INTEGER | NOT NULL, DEFAULT 20 |
| related_entity_ids | TEXT[] | DEFAULT {} |
| related_foreshadowing_ids | TEXT[] | DEFAULT {} |
| metadata | JSONB | NOT NULL, DEFAULT {} |
| created_at | TIMESTAMPTZ | NOT NULL, DEFAULT now() |
| updated_at | TIMESTAMPTZ | NOT NULL, DEFAULT now() |
**UNIQUE**: (project_id, key) | **Indexes**: idx_plot_threads_project_status, idx_plot_threads_progress

### `chapter_plans`
| Column | Type | Constraints |
|---|---|---|
| id | UUID | PK |
| project_id | UUID | NOT NULL, FK projects(id) CASCADE |
| chapter_id | UUID | FK chapters(id) SET NULL |
| chapter_no | INTEGER | NOT NULL |
| plan | JSONB | NOT NULL |
| status | TEXT | NOT NULL, DEFAULT planned |
| created_by | UUID | FK users(id) SET NULL |
| created_at | TIMESTAMPTZ | NOT NULL, DEFAULT now() |
| updated_at | TIMESTAMPTZ | NOT NULL, DEFAULT now() |
**Indexes**: idx_chapter_plans_project_status

## Events & Characters

### `events`
| Column | Type | Constraints |
|---|---|---|
| id | UUID | PK |
| project_id | UUID | NOT NULL, FK projects(id) CASCADE |
| chapter_id | UUID | FK chapters(id) SET NULL |
| event_order | INTEGER |  |
| title | TEXT |  |
| summary | TEXT | NOT NULL |
| occurred_at_label | TEXT |  |
| characters | TEXT[] | NOT NULL, DEFAULT {} |
| locations | TEXT[] | NOT NULL, DEFAULT {} |
| metadata | JSONB | NOT NULL, DEFAULT {} |
| created_at | TIMESTAMPTZ | NOT NULL, DEFAULT now() |
**Indexes**: idx_events_project_chapter, idx_events_characters(GIN), idx_events_locations(GIN)

### `characters`
| Column | Type | Constraints |
|---|---|---|
| id | UUID | PK |
| project_id | UUID | NOT NULL, FK projects(id) CASCADE |
| name | TEXT | NOT NULL |
| aliases | TEXT[] | NOT NULL, DEFAULT {} |
| role | TEXT |  |
| profile | JSONB | NOT NULL, DEFAULT {} |
| created_at | TIMESTAMPTZ | NOT NULL, DEFAULT now() |
| updated_at | TIMESTAMPTZ | NOT NULL, DEFAULT now() |
**UNIQUE**: (project_id, name) | **Indexes**: idx_characters_project_role

### `character_states`
| Column | Type | Constraints |
|---|---|---|
| id | UUID | PK |
| project_id | UUID | NOT NULL, FK projects(id) CASCADE |
| character_id | UUID | NOT NULL, FK characters(id) CASCADE |
| chapter_id | UUID | FK chapters(id) SET NULL |
| state | JSONB | NOT NULL |
| is_current | BOOLEAN | NOT NULL, DEFAULT true |
| created_at | TIMESTAMPTZ | NOT NULL, DEFAULT now() |
**Indexes**: idx_character_states_current

## Rules & Foreshadowing

### `canon_rules`
| Column | Type | Constraints |
|---|---|---|
| id | UUID | PK |
| project_id | UUID | NOT NULL, FK projects(id) CASCADE |
| rule_key | TEXT | NOT NULL |
| rule_type | TEXT | NOT NULL |
| scope | TEXT | NOT NULL, DEFAULT global |
| scope_type | TEXT | NOT NULL, DEFAULT global |
| scope_ref | TEXT |  |
| scope_config | JSONB | NOT NULL, DEFAULT {} |
| title | TEXT | NOT NULL |
| content | TEXT | NOT NULL |
| severity | TEXT | NOT NULL, DEFAULT warning |
| status | TEXT | NOT NULL, DEFAULT active |
| version | INTEGER | NOT NULL, DEFAULT 1 |
| priority | INTEGER | NOT NULL, DEFAULT 100 |
| effective_chapter_no | INTEGER |  |
| expire_chapter_no | INTEGER |  |
| effective_volume_no | INTEGER |  |
| expire_volume_no | INTEGER |  |
| is_temporary | BOOLEAN | NOT NULL, DEFAULT false |
| active_from_event | TEXT |  |
| expire_on_event | TEXT |  |
| conflict_policy | TEXT | NOT NULL, DEFAULT priority |
| supersedes_rule_ids | TEXT[] | DEFAULT {} |
| blocked_by_rule_ids | TEXT[] | DEFAULT {} |
| metadata | JSONB | NOT NULL, DEFAULT {} |
| created_at | TIMESTAMPTZ | NOT NULL, DEFAULT now() |
| updated_at | TIMESTAMPTZ | NOT NULL, DEFAULT now() |
**UNIQUE**: (project_id, rule_key) | **Indexes**: idx_canon_rules_project_status, idx_canon_rules_project_severity, idx_canon_rules_scope_lifecycle, idx_canon_rules_priority, idx_canon_rules_scope_config(GIN)

### `rule_versions`
| Column | Type | Constraints |
|---|---|---|
| id | UUID | PK |
| project_id | UUID | NOT NULL, FK projects(id) CASCADE |
| rule_id | UUID | NOT NULL, FK canon_rules(id) CASCADE |
| version | INTEGER | NOT NULL |
| content | TEXT | NOT NULL |
| change_reason | TEXT |  |
| source | TEXT |  |
| created_at | TIMESTAMPTZ | NOT NULL, DEFAULT now() |
**UNIQUE**: (rule_id, version)

### `foreshadowing`
| Column | Type | Constraints |
|---|---|---|
| id | UUID | PK |
| project_id | UUID | NOT NULL, FK projects(id) CASCADE |
| key | TEXT | NOT NULL |
| title | TEXT | NOT NULL |
| status | TEXT | NOT NULL, DEFAULT planted |
| importance | TEXT | NOT NULL, DEFAULT medium |
| planted_chapter_id | UUID | FK chapters(id) SET NULL |
| payoff_chapter_id | UUID | FK chapters(id) SET NULL |
| expected_payoff_range | TEXT |  |
| parent_foreshadowing_id | UUID | FK foreshadowing(id) SET NULL |
| related_foreshadowing_ids | TEXT[] | DEFAULT {} |
| trigger_on_payoff_ids | TEXT[] | DEFAULT {} |
| blocks_payoff_until_ids | TEXT[] | DEFAULT {} |
| layer | TEXT | NOT NULL, DEFAULT visible |
| must_payoff | BOOLEAN | NOT NULL, DEFAULT false |
| payoff_deadline_chapter | INTEGER |  |
| payoff_deadline_volume | INTEGER |  |
| overdue_policy | TEXT | NOT NULL, DEFAULT warn |
| payload | JSONB | NOT NULL, DEFAULT {} |
| created_at | TIMESTAMPTZ | NOT NULL, DEFAULT now() |
| updated_at | TIMESTAMPTZ | NOT NULL, DEFAULT now() |
**UNIQUE**: (project_id, key) | **Indexes**: Multiple foreshadowing indexes

### `canon_documents`
| Column | Type | Constraints |
|---|---|---|
| id | UUID | PK |
| project_id | UUID | NOT NULL, FK projects(id) CASCADE |
| doc_type | TEXT | NOT NULL |
| key | TEXT | NOT NULL |
| title | TEXT | NOT NULL |
| content | TEXT | NOT NULL |
| content_hash | TEXT | NOT NULL |
| status | TEXT | NOT NULL, DEFAULT active |
| version | INTEGER | NOT NULL, DEFAULT 1 |
| scope | JSONB | NOT NULL, DEFAULT {} |
| review_status | TEXT | NOT NULL, DEFAULT approved |
| source_type | TEXT | NOT NULL, DEFAULT manual |
| source_id | TEXT |  |
| related_rule_ids | TEXT[] | DEFAULT {} |
| is_deleted | BOOLEAN | NOT NULL, DEFAULT false |
| metadata | JSONB | NOT NULL, DEFAULT {} |
| created_by | UUID | FK users(id) SET NULL |
| updated_by | UUID | FK users(id) SET NULL |
| created_at | TIMESTAMPTZ | NOT NULL, DEFAULT now() |
| updated_at | TIMESTAMPTZ | NOT NULL, DEFAULT now() |
**Generated**: search_vector TSVECTOR | **UNIQUE**: (project_id, doc_type, key) | **Indexes**: GIN

### `canon_document_versions`
| Column | Type | Constraints |
|---|---|---|
| id | UUID | PK |
| project_id | UUID | NOT NULL, FK projects(id) CASCADE |
| document_id | UUID | NOT NULL, FK canon_documents(id) CASCADE |
| version | INTEGER | NOT NULL |
| title | TEXT | NOT NULL |
| content | TEXT | NOT NULL |
| content_hash | TEXT | NOT NULL |
| status | TEXT | NOT NULL |
| scope | JSONB | NOT NULL, DEFAULT {} |
| review_status | TEXT | NOT NULL |
| source_type | TEXT | NOT NULL, DEFAULT manual |
| source_id | TEXT |  |
| related_rule_ids | TEXT[] | DEFAULT {} |
| metadata | JSONB | NOT NULL, DEFAULT {} |
| change_reason | TEXT |  |
| created_by | UUID | FK users(id) SET NULL |
| created_at | TIMESTAMPTZ | NOT NULL, DEFAULT now() |
**UNIQUE**: (document_id, version) | **Indexes**: idx_canon_document_versions_document

## Users & Workspaces

### `users`
| Column | Type | Constraints |
|---|---|---|
| id | UUID | PK |
| username | TEXT | NOT NULL, UNIQUE |
| display_name | TEXT |  |
| email | TEXT | UNIQUE |
| password_hash | VARCHAR(255) | BCrypt |
| last_login_at | TIMESTAMPTZ |  |
| status | TEXT | NOT NULL, DEFAULT active |
| created_at | TIMESTAMPTZ | NOT NULL, DEFAULT now() |
| updated_at | TIMESTAMPTZ | NOT NULL, DEFAULT now() |
**Indexes**: idx_users_username | **Seed**: admin/123456

### `workspaces`
| Column | Type | Constraints |
|---|---|---|
| id | UUID | PK |
| slug | TEXT | NOT NULL, UNIQUE |
| name | TEXT | NOT NULL |
| owner_user_id | UUID | FK users(id) SET NULL |
| settings | JSONB | NOT NULL, DEFAULT {} |
| created_at | TIMESTAMPTZ |  |
| updated_at | TIMESTAMPTZ |  |

### `workspace_members`
| Column | Type | Constraints |
|---|---|---|
| workspace_id | UUID | NOT NULL, FK workspaces(id) CASCADE |
| user_id | UUID | NOT NULL, FK users(id) CASCADE |
| role | TEXT | NOT NULL, DEFAULT reader |
| created_at | TIMESTAMPTZ |  |
**PRIMARY KEY**: (workspace_id, user_id)

### `api_tokens`
| Column | Type | Constraints |
|---|---|---|
| id | UUID | PK |
| user_id | UUID | NOT NULL, FK users(id) CASCADE |
| workspace_id | UUID | FK workspaces(id) CASCADE |
| project_id | UUID | FK projects(id) CASCADE |
| name | TEXT | NOT NULL |
| token_hash | TEXT | NOT NULL, UNIQUE |
| scopes | TEXT[] | DEFAULT {} |
| expires_at | TIMESTAMPTZ |  |
| last_used_at | TIMESTAMPTZ |  |
| revoked_at | TIMESTAMPTZ |  |

### `project_members`
| Column | Type | Constraints |
|---|---|---|
| project_id | UUID | NOT NULL, FK projects(id) CASCADE |
| user_id | UUID | NOT NULL, FK users(id) CASCADE |
| role | TEXT | NOT NULL, DEFAULT reader |
| created_at | TIMESTAMPTZ |  |
**PRIMARY KEY**: (project_id, user_id)

### `local_project_bindings`
| Column | Type | Constraints |
|---|---|---|
| id | UUID | PK |
| project_id | UUID | NOT NULL, FK projects(id) CASCADE |
| user_id | UUID | NOT NULL, FK users(id) CASCADE |
| client_id | TEXT | NOT NULL |
| local_root_hint | TEXT |  |
| manifest | JSONB | NOT NULL, DEFAULT {} |
| last_sync_at | TIMESTAMPTZ |  |
| created_at | TIMESTAMPTZ |  |
| updated_at | TIMESTAMPTZ |  |
**UNIQUE**: (project_id, user_id, client_id)

## State Entities & Relationships

### `state_entities`
| Column | Type | Constraints |
|---|---|---|
| id | UUID | PK |
| project_id | UUID | NOT NULL, FK projects(id) CASCADE |
| entity_type | TEXT | NOT NULL |
| name | TEXT | NOT NULL |
| aliases | TEXT[] | DEFAULT {} |
| summary | TEXT |  |
| description | TEXT |  |
| portrait_url | TEXT |  |
| profile | JSONB | NOT NULL, DEFAULT {} |
| lifecycle_status | TEXT | NOT NULL, DEFAULT active |
| importance | TEXT | NOT NULL, DEFAULT medium |
| tags | TEXT[] | DEFAULT {} |
| first_seen_chapter_no | INTEGER |  |
| last_seen_chapter_no | INTEGER |  |
| first_seen_volume_no | INTEGER |  |
| last_seen_volume_no | INTEGER |  |
| source_type | TEXT | NOT NULL, DEFAULT manual |
| source_id | TEXT |  |
| metadata | JSONB | DEFAULT {} |
| created_at | TIMESTAMPTZ |  |
| updated_at | TIMESTAMPTZ |  |
**UNIQUE**: (project_id, entity_type, name) | **Indexes**: GIN on tags, metadata

### `state_snapshots`
| Column | Type | Constraints |
|---|---|---|
| id | UUID | PK |
| project_id | UUID | NOT NULL, FK projects(id) CASCADE |
| entity_id | UUID | NOT NULL, FK state_entities(id) CASCADE |
| chapter_id | UUID | FK chapters(id) SET NULL |
| state | JSONB | NOT NULL |
| is_current | BOOLEAN | NOT NULL, DEFAULT true |
| source_commit_id | UUID | FK chapter_commits(id) SET NULL |
| effective_chapter_no | INTEGER |  |
| expire_chapter_no | INTEGER |  |
| effective_volume_no | INTEGER |  |
| expire_volume_no | INTEGER |  |
| duration_type | TEXT | NOT NULL, DEFAULT persistent |
| expires_on_event | TEXT |  |
| confidence | NUMERIC(5,4) |  |
| source_type | TEXT | NOT NULL, DEFAULT chapter_commit |
| source_id | TEXT |  |
| change_reason | TEXT |  |
| metadata | JSONB | DEFAULT {} |
| created_at | TIMESTAMPTZ |  |
**Indexes**: idx_state_snapshots_current, idx_state_snapshots_current_lifecycle, idx_state_snapshots_source, idx_state_snapshots_metadata(GIN)

### `entity_relationships`
| Column | Type | Constraints |
|---|---|---|
| id | UUID | PK |
| project_id | UUID | NOT NULL, FK projects(id) CASCADE |
| source_entity_id | UUID | NOT NULL, FK state_entities(id) CASCADE |
| target_entity_id | UUID | NOT NULL, FK state_entities(id) CASCADE |
| relation_type | TEXT | NOT NULL |
| attitude | TEXT |  |
| intensity | NUMERIC(5,4) |  |
| known_by_source | BOOLEAN | NOT NULL, DEFAULT true |
| known_by_target | BOOLEAN | NOT NULL, DEFAULT true |
| known_by_reader | BOOLEAN | NOT NULL, DEFAULT true |
| status | TEXT | NOT NULL, DEFAULT active |
| source_chapter_no | INTEGER |  |
| source_chapter_id | UUID | FK chapters(id) SET NULL |
| source_commit_id | UUID | FK chapter_commits(id) SET NULL |
| metadata | JSONB | DEFAULT {} |
| created_at | TIMESTAMPTZ |  |
| updated_at | TIMESTAMPTZ |  |
**UNIQUE**: (project_id, source_entity_id, target_entity_id, relation_type) | **Indexes**: GIN

## Review & Revision

### `review_jobs`
| Column | Type | Constraints |
|---|---|---|
| id | UUID | PK |
| project_id | UUID | NOT NULL, FK projects(id) CASCADE |
| chapter_id | UUID | NOT NULL, FK chapters(id) CASCADE |
| status | TEXT | CHECK: pending/running/complete/failed/aggregated/blocked/resolved |
| status_reason | TEXT |  |
| config | JSONB | NOT NULL, DEFAULT {} |
| blocked_at | TIMESTAMP |  |
| resolved_at | TIMESTAMP |  |
| aggregated_at | TIMESTAMP |  |
| created_by | UUID | FK users(id) SET NULL |
| created_at | TIMESTAMPTZ |  |
| updated_at | TIMESTAMPTZ |  |

### `review_reports`
| Column | Type | Constraints |
|---|---|---|
| id | UUID | PK |
| project_id | UUID | NOT NULL, FK projects(id) CASCADE |
| review_job_id | UUID | FK review_jobs(id) CASCADE |
| chapter_id | UUID | NOT NULL, FK chapters(id) CASCADE |
| model_id | TEXT |  |
| report_type | TEXT | NOT NULL, DEFAULT model |
| score | NUMERIC(5,2) |  |
| findings | JSONB | NOT NULL, DEFAULT [] |
| summary | TEXT |  |
| created_at | TIMESTAMPTZ |  |
**Indexes**: idx_review_reports_job, idx_review_reports_chapter

### `revision_tasks`
| Column | Type | Constraints |
|---|---|---|
| id | UUID | PK |
| project_id | UUID | NOT NULL, FK projects(id) CASCADE |
| chapter_id | UUID | NOT NULL, FK chapters(id) CASCADE |
| review_job_id | UUID | FK review_jobs(id) SET NULL |
| title | TEXT | NOT NULL |
| description | TEXT |  |
| severity | TEXT | NOT NULL, DEFAULT medium |
| status | TEXT | NOT NULL, DEFAULT open |
| metadata | JSONB | DEFAULT {} |
| created_at | TIMESTAMPTZ |  |
| updated_at | TIMESTAMPTZ |  |
**Indexes**: idx_revision_tasks_project_status

### `revision_task_history`
| Column | Type | Constraints |
|---|---|---|
| id | UUID | PK |
| revision_task_id | UUID | NOT NULL |
| old_status | VARCHAR(50) |  |
| new_status | VARCHAR(50) | NOT NULL |
| changed_by | VARCHAR(255) |  |
| change_reason | TEXT |  |
| metadata | JSONB |  |
| created_at | TIMESTAMP | DEFAULT NOW() |

### `review_council_configs`
| Column | Type | Constraints |
|---|---|---|
| id | UUID | PK |
| project_id | UUID | NOT NULL, FK projects(id) CASCADE |
| name | TEXT | NOT NULL |
| config | JSONB | NOT NULL |
| is_active | BOOLEAN | NOT NULL, DEFAULT false |
| created_at | TIMESTAMPTZ |  |
| updated_at | TIMESTAMPTZ |  |
**UNIQUE**: (project_id, name)

### `review_model_metrics`
| Column | Type | Constraints |
|---|---|---|
| id | UUID | PK |
| model_id | VARCHAR(255) | NOT NULL |
| project_id | UUID | NOT NULL |
| total_reports | INTEGER | DEFAULT 0 |
| human_confirmed | INTEGER | DEFAULT 0 |
| human_rejected | INTEGER | DEFAULT 0 |
| rule_proposals_created | INTEGER | DEFAULT 0 |
| rule_proposals_approved | INTEGER | DEFAULT 0 |
| revision_tasks_created | INTEGER | DEFAULT 0 |
| revision_tasks_completed | INTEGER | DEFAULT 0 |
| agreement_with_consensus | FLOAT | DEFAULT 0 |
| average_score | FLOAT |  |
| last_calculated_at | TIMESTAMP |  |
| created_at | TIMESTAMP |  |
| updated_at | TIMESTAMP |  |
**UNIQUE**: (model_id, project_id)

## Rule Proposals (TWO versions exist)
**v1 (authoritative, init/020)**: with UUID FKs, `agreement` JSONB, `status` DEFAULT proposed

### `rule_proposals_v1`
| Column | Type | Constraints |
|---|---|---|
| id | UUID | PK |
| project_id | UUID | NOT NULL, FK projects(id) CASCADE |
| source_type | TEXT | NOT NULL |
| source_id | UUID |  |
| proposal_type | TEXT | NOT NULL |
| target_rule_id | UUID | FK canon_rules(id) SET NULL |
| title | TEXT | NOT NULL |
| content | TEXT | NOT NULL |
| confidence | NUMERIC(5,4) |  |
| agreement | JSONB | NOT NULL, DEFAULT {} |
| status | TEXT | NOT NULL, DEFAULT proposed |
| created_by | UUID | FK users(id) SET NULL |
| approved_by | UUID | FK users(id) SET NULL |
| resolved_at | TIMESTAMPTZ |  |
**v2 (migrations/120)**: standalone, no FKs, VARCHAR columns

### `rule_proposals_v2`
| Column | Type | Constraints |
|---|---|---|
| id | UUID | PK |
| project_id | UUID | NOT NULL |
| chapter_id | UUID |  |
| review_job_id | UUID |  |
| revision_task_id | UUID |  |
| proposal_type | VARCHAR(50) | NOT NULL, values: style/canon/character/plot/lesson |
| title | VARCHAR(500) | NOT NULL |
| content | TEXT | NOT NULL |
| confidence | FLOAT | DEFAULT 0.5 |
| source_model_id | VARCHAR(255) |  |
| source_finding_key | TEXT |  |
| status | VARCHAR(50) | DEFAULT pending |
| reviewed_by | VARCHAR(255) |  |
| reviewed_at | TIMESTAMP |  |
| review_notes | TEXT |  |
| auto_apply | BOOLEAN | DEFAULT FALSE |
| auto_applied_at | TIMESTAMP |  |
| created_by | VARCHAR(255) |  |
| created_at | TIMESTAMP |  |
| updated_at | TIMESTAMP |  |
**Indexes (v2)**: idx_rule_proposals_status, idx_rule_proposals_type, idx_rule_proposals_project

## Reference Sources & Audit

### `reference_sources`
| Column | Type | Constraints |
|---|---|---|
| id | UUID | PK |
| workspace_id | UUID | FK workspaces(id) CASCADE |
| project_id | UUID | FK projects(id) CASCADE |
| source_type | TEXT | NOT NULL |
| name | TEXT | NOT NULL |
| source_uri | TEXT |  |
| license | TEXT |  |
| metadata | JSONB | DEFAULT {} |
| created_at | TIMESTAMPTZ |  |
| updated_at | TIMESTAMPTZ |  |

### `reference_items`
| Column | Type | Constraints |
|---|---|---|
| id | UUID | PK |
| source_id | UUID | NOT NULL, FK reference_sources(id) CASCADE |
| project_id | UUID | FK projects(id) CASCADE |
| item_type | TEXT | NOT NULL |
| key | TEXT | NOT NULL |
| title | TEXT |  |
| content | TEXT | NOT NULL |
| metadata | JSONB | DEFAULT {} |
| created_at | TIMESTAMPTZ |  |
| updated_at | TIMESTAMPTZ |  |

### `audit_logs`
| Column | Type | Constraints |
|---|---|---|
| id | UUID | PK |
| workspace_id | UUID | FK workspaces(id) SET NULL |
| project_id | UUID | FK projects(id) SET NULL |
| user_id | UUID | FK users(id) SET NULL |
| action | TEXT | NOT NULL |
| resource_type | TEXT |  |
| resource_id | UUID |  |
| payload | JSONB | NOT NULL, DEFAULT {} |
| created_at | TIMESTAMPTZ |  |

## Legacy Knowledge Base (190_extensible_categories system)

### `categories`
| Column | Type | Constraints |
|---|---|---|
| id | UUID | PK |
| slug | VARCHAR(50) | UNIQUE NOT NULL |
| name | VARCHAR(100) | NOT NULL |
| name_en | VARCHAR(100) |  |
| description | TEXT |  |
| icon | VARCHAR(50) |  |
| color | VARCHAR(20) |  |
| sort_order | INTEGER | DEFAULT 0 |
| parent_id | UUID | FK categories(id) |
| level | INTEGER | DEFAULT 0 |
| config | JSONB | DEFAULT {} |
| is_system | BOOLEAN | DEFAULT false |
| is_active | BOOLEAN | DEFAULT true |
| created_at | TIMESTAMPTZ |  |
| updated_at | TIMESTAMPTZ |  |
10 system cats + 22 PRESETS subcats

### `tags`
| Column | Type | Constraints |
|---|---|---|
| id | UUID | PK |
| slug | VARCHAR(50) | UNIQUE NOT NULL |
| name | VARCHAR(100) | NOT NULL |
| category | VARCHAR(50) |  |
| description | TEXT |  |
| color | VARCHAR(20) |  |
| usage_count | INTEGER | DEFAULT 0 |
| is_recommended | BOOLEAN | DEFAULT false |
| is_active | BOOLEAN | DEFAULT true |
| created_at | TIMESTAMPTZ |  |

### `knowledge_base`
| Column | Type | Constraints |
|---|---|---|
| id | UUID | PK |
| code | VARCHAR(50) |  |
| title | VARCHAR(200) | NOT NULL |
| content | TEXT | NOT NULL |
| summary | TEXT |  |
| detail | TEXT |  |
| examples | TEXT |  |
| counter_examples | TEXT |  |
| metadata | JSONB | DEFAULT {} |
| source | VARCHAR(50) | DEFAULT manual |
| source_file | VARCHAR(200) |  |
| category_id | UUID | FK categories(id) |
| applicable_genres | TEXT[] | DEFAULT {} |
| applicable_skills | TEXT[] | DEFAULT {} |
| level | VARCHAR(20) | DEFAULT knowledge |
| status | VARCHAR(20) | DEFAULT active |
| view_count | INTEGER | DEFAULT 0 |
| use_count | INTEGER | DEFAULT 0 |
| last_reviewed_at | TIMESTAMPTZ | (194) |
| reviewed_by | UUID | FK users(id) (194) |
| review_version | INTEGER | DEFAULT 1 (194) |
| search_vector | TSVECTOR | GENERATED |
| created_at | TIMESTAMPTZ |  |
| updated_at | TIMESTAMPTZ |  |
**Generated**: search_vector = to_tsvector(title + content) | **Indexes**: GIN on search, genres, skills, metadata

### `knowledge_tags`
| Column | Type | Constraints |
|---|---|---|
| knowledge_id | UUID | FK knowledge_base(id) CASCADE |
| tag_id | UUID | FK tags(id) CASCADE |
| created_at | TIMESTAMPTZ |  |
**PRIMARY KEY**: (knowledge_id, tag_id)

### `knowledge_vectors`
| Column | Type | Constraints |
|---|---|---|
| id | UUID | PK |
| knowledge_id | UUID | NOT NULL, FK knowledge_base(id) CASCADE |
| qdrant_collection | VARCHAR(100) | NOT NULL |
| qdrant_point_id | VARCHAR(100) |  |
| vector_model | VARCHAR(50) | DEFAULT text-embedding-3-small |
| dimension | INTEGER | DEFAULT 1536 |
| created_at | TIMESTAMPTZ |  |
**UNIQUE**: (knowledge_id, qdrant_collection)
