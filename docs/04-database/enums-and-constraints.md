# Enums, CHECK Constraints & Relationships

## All CHECK Constraints

| Table | Column | CHECK Constraint |
|---|---|---|
| review_jobs | status | IN (pending, running, complete, failed, aggregated, blocked, resolved) |
| compressed_contexts | compression_layer | IN (chapter_batch, arc, volume, series) |
| character_arcs | arc_type | IN (emotion, relationship, power, personality, goal, custom) |
| causality_chains | causal_type | IN (direct, indirect, triggered, enabled, prevented) |
| causality_chains | strength | >= 0 AND <= 1 |
| generation_passes | pass_number | BETWEEN 1 AND 4 |
| generation_passes | pass_type | IN (planning, drafting, polishing, verification) |
| chapter_emotions | tension | >= 0 AND <= 1 |
| chapter_emotions | emotion_intensity | >= 0 AND <= 1 |
| chapter_emotions | pacing_type | IN (buildup, climax, breather, transition, climax_buildup, resolution, normal) |
| style_profiles | narrative_pov | IN (first, second, third_limited, third_omniscient, multiple) |
| style_profiles | tense | IN (past, present, mixed) |
| setting_field_definitions | field_type | IN (text, textarea, select, multiselect, number, boolean, json) |
| setting_items | level | IN (knowledge, reminder, defect_compensation) |
| setting_category_relations | relation_type | IN (contains, related, conflicts) |
| system_evolution_proposals | proposal_type | IN (create, update, delete, merge) |
| system_evolution_proposals | target_entity_type | IN (style_profile, prompt_template, model_profile, knowledge_item, setting_item, genre_config) |
| system_style_profiles | status | IN (active, deprecated, draft) |
| system_notifications | type | IN (evolution_proposal, system_update, ai_review_completed, admin_review_required) |

## Generated Columns (TSVECTOR)

| Table | Expression |
|---|---|
| memory_chunks | to_tsvector(simple, content) STORED |
| canon_documents | to_tsvector(simple, coalesce(title)+coalesce(key)+coalesce(content)) STORED |
| knowledge_base | to_tsvector(simple, coalesce(title)+coalesce(content)) STORED |
| knowledge_entities | to_tsvector(simple, coalesce(name)+coalesce(content)) STORED |
| universal_knowledge | to_tsvector(simple, coalesce(topic)+coalesce(content)) STORED |
| fulltext_search_records | to_tsvector(chinese, coalesce(title)+coalesce(content)) via trigger |

## Views

| View | Description |
|---|---|
| v_setting_items_overview | Joins setting_items + setting_categories, shows item_code, core_summary, level, is_global, category_name, tags, skills, genres |
| v_genre_canonical_list | Shows canonical_genre, platform_tags, aliases, description, alias_count |

## Functions

| Function | Purpose | Parameters | Returns |
|---|---|---|---|
| fn_setting_items_bm25_search | Multi-weight BM25 search on setting items | p_query TEXT, p_workspace_id, p_category_id, p_level, p_skill, p_genre, p_limit, p_offset | TABLE with rank DOUBLE, highlight TEXT |
| fn_genre_resolve | Resolve a genre name to canonical | p_input TEXT | TABLE (canonical_genre, match_type, confidence) |
| fn_setting_items_csv_validate | Validate CSV import | p_csv_content TEXT | TABLE (row_number, is_valid, error_message, parsed_data) |
| update_fulltext_search_vector() | Trigger: auto-update search_vector | - | TRIGGER RETURN |
| update_updated_at_column() | Trigger: auto-update updated_at | - | TRIGGER RETURN |
| update_user_knowledge_updated_at() | Trigger for user_knowledge | - | TRIGGER RETURN |
| maintain_version_history() | Trigger: auto version history (system_style/prompt/model_profiles) | - | TRIGGER RETURN, keeps 10 versions |
| cleanup_expired_notifications() | Cleanup expired system_notifications after 90 days | - | INTEGER (deleted count) |

## Composite UNIQUE Constraints

| projects | (workspace_id, slug) |
| chapters | (project_id, chapter_no) |
| chapter_summaries | (chapter_id, summary_type) |
| chapter_commits | (chapter_id, commit_no) |
| characters | (project_id, name) |
| volumes | (project_id, volume_no) |
| plot_threads | (project_id, key) |
| canon_rules | (project_id, rule_key) |
| foreshadowing | (project_id, key) |
| canon_documents | (project_id, doc_type, key) |
| canon_document_versions | (document_id, version) |
| rule_versions | (rule_id, version) |
| review_council_configs | (project_id, name) - via unique index |
| state_entities | (project_id, entity_type, name) |
| entity_relationships | (project_id, source_entity_id, target_entity_id, relation_type) |
| user_knowledge | No explicit unique beyond PK |
| chapter_emotions | (project_id, chapter_no) |
| style_profiles | (project_id, profile_name) |
| chapter_style_metrics | (project_id, chapter_no) |
| compressed_contexts | (project_id, compression_layer, chapter_range_start, chapter_range_end) |
| generation_passes | None |
| chapter_versions | (chapter_id, version_no) |
| writing_stats | (project_id, stat_date, stat_type, chapter_no) |
| proper_nouns | (project_id, noun_key) |
| fulltext_search_records | (source_type, source_id) |
| prompt_templates | (project_id, template_key) |
| prompt_template_versions | (template_id, version) |
| context_weight_configs | (project_id, config_name, profile) |
| reference_materials | (project_id, material_key) |
| reader_expectations | (project_id, expectation_key) |
| model_profiles | (project_id, profile_key) |
| model_route_rules | (project_id, task_type, profile_key) |
| setting_categories | (workspace_id, slug) |
| setting_field_definitions | (category_id, field_key) |
| setting_items | (workspace_id, item_code), (category_id, item_code) |
| setting_category_relations | (parent_category_id, child_category_id) |
| project_knowledge | (project_id, category, key) |
| knowledge_relations | (from_entity_id, to_entity_id, relation_type) |
| knowledge_vectors | (knowledge_id, qdrant_collection) |
| offline_sync_sessions | None |
| relationship_graph_configs | (project_id, config_name) |
| skills | name UNIQUE |
| skill_steps | (skill_id, step_order) |
| pacing_blueprints | (project_id, volume_no) |
| local_project_bindings | (project_id, user_id, client_id) |
| workspace_members | PRIMARY KEY (workspace_id, user_id) |
| project_members | PRIMARY KEY (project_id, user_id) |
| knowledge_tags | PRIMARY KEY (knowledge_id, tag_id) |
| vector_index_status | (project_id, collection) |
| vector_index_config | (project_id, collection) |
| review_model_metrics | (model_id, project_id) |
| data_tier_config | (project_id, tier, table_name) |
| volume_archive_status | (project_id, volume_no) |
| project_knowledge_pack | project_id UNIQUE |
| genre_knowledge_config | genre UNIQUE |
| local_projects | project_id UNIQUE |
| chapter_index | (project_id, chapter_no) |

## Foreign Key Relationships (ON DELETE behavior)

### CASCADE (delete parent -> delete children)

| chapters.project_id | projects | All chapters, summaries, commits, events deleted |
| chapter_summaries.chapter_id | chapters | Summary deleted with chapter |
| chapter_commits.chapter_id | chapters | Commits deleted with chapter |
| events.project_id | projects | Events deleted with project |
| characters.project_id | projects | Characters deleted with project |
| character_states.character_id | characters | States deleted with character |
| canon_rules.project_id | projects | All rules deleted |
| rule_versions.rule_id | canon_rules | Versions deleted with rule |
| foreshadowing.project_id | projects | Foreshadowing deleted |
| review_jobs.project_id,chapter_id | projects,chapters | Jobs deleted with project/chapter |
| review_reports.project_id,chapter_id,review_job_id | projects,chapters,review_jobs | Reports cascade |
| revision_tasks.project_id,chapter_id | projects,chapters | Tasks cascade |
| review_council_configs.project_id | projects | Configs deleted |
| memory_chunks.project_id | projects | Chunks deleted with project |
| state_entities.project_id | projects | Entities deleted |
| state_snapshots.entity_id | state_entities | Snapshots deleted |
| entity_relationships.source/target_entity_id | state_entities | Relations deleted |
| workspace_members.workspace_id,user_id | workspaces,users | Membership deleted |
| project_members.project_id,user_id | projects,users | Membership deleted |
| rule_proposals.project_id | projects | Proposals deleted |
| volume_archive_status | projects | Volumes deleted |

## Views

| View | Description |
|---|---|
| v_setting_items_overview | Joins setting_items + setting_categories, shows item_code, core_summary, level, is_global, category_name, tags, skills, genres |
| v_genre_canonical_list | Shows canonical_genre, platform_tags, aliases, description, alias_count |

## Functions

| Function | Purpose |
|---|---|
| fn_setting_items_bm25_search | Multi-weight BM25 search on 4 fields (intent_synonyms=weight A, keywords=B, core_summary=C, detailed_expansion=D) |
| fn_genre_resolve | Resolve genre name to canonical with confidence (exact=1.0, platform_tag=0.95, alias=0.9, fuzzy) |
| fn_setting_items_csv_validate | Validate CSV import for setting items |
| update_fulltext_search_vector | Trigger: auto tsvector on insert/update for fulltext_search_records |
| update_updated_at_column | Trigger: auto now() on update for categories, knowledge_base, system tables |
| update_user_knowledge_updated_at | Trigger: auto now() for user_knowledge |
| maintain_version_history | Trigger: auto version backup (keeps 10) for system_style_profiles, system_prompt_templates, system_model_profiles |
| cleanup_expired_notifications | Cleanup function: deletes notifications past expires_at (90 days), returns deleted count |

## Composite UNIQUE Constraints (partial list)

Key business-key uniques enforce no-duplicate entries: (project_id, chapter_no), (project_id, key) for foreshadowing/plot_threads, (project_id, rule_key) for canon_rules, (project_id, doc_type, key) for canon_documents, (project_id, entity_type, name) for state_entities, (workspace_id, slug) for setting_categories, (workspace_id, item_code) for setting_items, (project_id, profile_key) for model_profiles, (project_id, template_key) for prompt_templates, (project_id, material_key) for reference_materials, (source_type, source_id) for fulltext_search_records, (project_id, category, key) for project_knowledge, (from_entity_id, to_entity_id, relation_type) for knowledge_relations

## Foreign Key ON DELETE Summary

**CASCADE pattern**: Most project-scoped tables (chapters, events, characters, canon_rules, foreshadowing, review_jobs, review_reports, state_entities, state_snapshots, entity_relationships, memory_chunks, model_profiles, etc.) cascade delete when the project is deleted.

**SET NULL pattern**: FKs referencing users typically SET NULL to preserve audit trails (chapter_commits.accepted_by/created_by, review_jobs.created_by, rule_proposals.created_by/approved_by, canon_documents.created_by/updated_by, audit_logs.user_id, state_snapshots FK chapters).

**Special**: workspaces.owner_user_id SET NULL (workspace survives user deletion). world_snapshots have no FK to projects (plain UUID).
