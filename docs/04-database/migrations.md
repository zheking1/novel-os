# Migration History

## Init Scripts (18 files)

| Ord | File | Changes |
|---|---|---|
| 001 | 001_extensions.sql | Extensions: vector, pg_trgm, uuid-ossp |
| 010 | 010_core_schema.sql | projects, chapters, chapter_summaries, chapter_commits, events, characters, character_states, canon_rules, rule_versions, foreshadowing, review_jobs, review_reports, memory_chunks |
| 020 | 020_multi_user_workspace.sql | users, workspaces, workspace_members, api_tokens, project_members, local_project_bindings, state_entities, state_snapshots, rule_proposals, volumes, plot_threads, chapter_plans, review_council_configs, revision_tasks, reference_sources, reference_items, audit_logs. ALTER projects +workspace_id/slug/settings |
| 030 | 030_seed_default_admin.sql | Seed: admin/123456 user + default workspace |
| 040 | 040_context_packs.sql | context_packs |
| 050 | 050_vector_index.sql | vector_index_jobs |
| 060 | 060_commit_audit_columns.sql | ALTER chapter_commits +accepted_by/created_by FK users; ALTER review_jobs +created_by |
| 070 | 070_project_scoped_tokens.sql | ALTER api_tokens +project_id FK projects CASCADE |
| 080 | 080_long_term_service_constraints.sql | Indexes on review_council/revision/reference tables |
| 090 | 090_canon_documents.sql | canon_documents (search_vector TSVECTOR) + canon_document_versions |
| 100 | 100_state_snapshot_lifecycle.sql | ALTER state_snapshots +duration info/confidence/metadata; 3 indexes |
| 110 | 110_foreshadowing_links.sql | ALTER foreshadowing +parent/layer/deadline/overdue fields; 3 indexes |
| 120 | 120_rule_scope_lifecycle.sql | ALTER canon_rules +scope management/conflict policy/lifecycle; 3 indexes |
| 130 | 130_entity_relationships.sql | ALTER state_entities +lifecycle fields; NEW entity_relationships table |
| 140 | 140_plot_thread_progress.sql | ALTER volumes +start/end/summary/goals; ALTER plot_threads +progress fields |
| 150 | 150_model_cost.sql | model_profiles + model_route_rules + model_usage_records |
| 160 | 160_global_settings.sql | setting_categories/field_definitions/items, genre_canonical, setting_category_relations. Functions: BM25 search, genre resolve, CSV validate. Views: items overview, genre list. Seed: 9 cats + 6 items + 15 genres |
| 195 | 195_add_password.sql | ALTER users +password_hash VARCHAR(255), last_login_at. Default password=123456 (bcrypt) |

## Migration Scripts (30 files from novel-os-mcp/ + deploy/nas/)

| Order | File | Changes |
|---|---|---|
| 120 | 120_review_lifecycle.sql | ALTER review_jobs +status fields + CHECK constraint. NEW: revision_task_history, review_model_metrics, rule_proposals (v2 standalone) |
| 130 | 130_vector_index_queue.sql | vector_index_tasks (priority/attempts), vector_index_status (tracking), vector_index_config, memory_chunk_index_history |
| 140 | 140_data_tier_archive.sql | data_tier_config, archive_history, volume_archive_status, archive_schedules |
| 150 | 150_backup_restore.sql | backup_records, backup_schedules, restore_records, project_export_records |
| 160 | 160_p7_enhancement.sql | prompt_templates (+versions +usage_logs), context_weight_configs, reference_materials, reader_expectations, chapter_annotations, chapter_versions, writing_stats, proper_nouns, fulltext_search_records (with trigger) |
| 170 | 170_p8_extended.sql | offline_sync_sessions, offline_change_queue, voice_drafts, relationship_graph_configs, template_marketplace, automated_test_results, performance_test_results |
| 180 | 180_performance_indexes.sql | Performance indexes: projects, chapters, events (GIN), characters, canon_rules, foreshadowing, review_jobs, review_reports, canon_documents, memory_chunks, context_cache, chapter_plans, prompt_templates + ANALYZE |
| 190 | 190_extensible_categories.sql | categories (hierarchical, 10 seed), tags (19 seed), knowledge_base (search_vector TSVECTOR), knowledge_tags, knowledge_vectors |
| 191 | 191_knowledge_to_canon.sql | Migration: knowledge_base (source=opencode) rows to canon_documents |
| 192 | 192_add_review_rules_category.sql | INSERT categories: review_rules slug |
| 193 | 193_presets_categories.sql | PRESETS categories: world_design, reader_analysis, plot_templates + 22+ subcategories |
| 194 | 194_knowledge_user_review.sql | user_knowledge, knowledge_review. ALTER knowledge_base +last_reviewed_at, reviewed_by, review_version |
| 200 | 200_context_compression.sql | compressed_contexts (chapter_batch/arc/volume/series layers, UNIQUE on layer+range) |
| 201 | 201_character_arcs_causality.sql | character_arcs (emotion/relationship/power/personality/goal/custom), causality_chains (direct/indirect/triggered/enabled/prevented), generation_passes (1-4 pass pipeline) |
| 202 | 202_pacing_emotion.sql | pacing_blueprints, chapter_emotions (tension REAL, emotion, intensity, pacing_type CHECK) |
| 203 | 203_style_fingerprint.sql | style_profiles (narrative_pov CHECK, tense CHECK, tone), chapter_style_metrics |
| 204 | 204_events_archive.sql | events_archive |
| 205 | 205_knowledge_base_system.sql | ref_categories (5 top-level + subs), knowledge_entities, knowledge_relations, universal_knowledge, project_knowledge, world_snapshots, ref_search_jobs, ref_gap_logs |
| 206 | 206_local_storage_index.sql | local_projects, chapter_index, review_index, setting_index |
| 207 | 207_knowledge_pack_system.sql | genre_knowledge_config (8 types), project_knowledge_pack |
| 208 | 208_restructure_knowledge_categories.sql | Restructure: 9 new top-level ref_categories (character_ref, equipment, creature, world_setting, power_system, history_culture, plot_ref, writing_ref, general_material) + child categories |
| 209 | 209_fix_child_category_parent_id.sql | Fix: UPDATE ref_categories SET parent_id = correct parent for all child categories |
| 210a | 210_entity_fields.sql | ALTER state_entities +summary, description, portrait_url |
| 210b | 210_restructure_categories.sql | Further subcategories for plot_trope (trope_core/emotion/conflict/growth/daily/suspense), char_template (protagonist/supporting/antagonist/group), geography (natural/city/region/special), personality (inner/social), special_item (cheat/treasure/world), structure (opening/middle/ending), style (platform/genre). NEW: knowledge_tags table (items + tags) |
| 211a | 211_recategorize_items.sql | UPDATE universal_knowledge: re-categorize items by content analysis |
| 211b | 211_canon_is_deleted.sql | ALTER canon_documents +is_deleted BOOLEAN DEFAULT false |
| 212 | 212_skill_management.sql | skills (name UNIQUE, trigger_words, tool_hints, embedding_id) + skill_steps (UNIQUE skill_id+step_order) |
| 213 | 213_model_profiles_user_id.sql | ALTER model_profiles +user_id TEXT + index |
| 220 | 220_system_evolution.sql | system_evolution_proposals (7-status flow), system_style_profiles (version_history JSONB, 10-limit trigger), system_prompt_templates, system_model_profiles, system_notifications (90-day expiry), ALTER model_profiles +is_system +forked_from_system_key. Functions: maintain_version_history, cleanup_expired_notifications. 4 triggers on version tables |
| 221 | 221_system_evolution_seed.sql | Seed: 5 system_style_profiles (xuanhuan_heroic, xianxia_cultivation, urban_supernatural, sci_fi_space, wuxia_jianghu), 4 system_prompt_templates (chapter_outline, battle_scene, character_profile, chapter_review), 4 system_model_profiles (creative_writing, fast_generation, professional_review, local_backup) |
| 222 | 222_runtime_tables.sql | 补齐代码已读写但仓库缺失的 4 张表：`global_rules` (rule_key UNIQUE, rule_type creative/compliance/polish, source_project_id FK projects, promoted_from_rule_id FK canon_rules)、`evolution_logs` (old/new_value JSONB, proposal_id FK system_evolution_proposals)、`ref_tones` (slug UNIQUE)、`ref_tone_rules` (tone_slug，不建外键)。ALTER canon_rules +promotion_status/promoted_to_global_id/discussion_id。复用 220 的 `update_updated_at_column` 触发器 |
| 223 | 223_rule_summaries.sql | `rule_summaries` (project_id FK projects CASCADE, rule_group, genre, summary, source_rule_ids TEXT[])，供动态规则检索方案使用，当前代码尚未引用 |
| 224 | 224_drop_legacy_kb_tables.sql | **破坏性**。删除旧知识体系 5 张废弃表：`knowledge_tags`、`knowledge_vectors`、`setting_category_relations`、`genre_category_bindings`、`categories`。先动态解除 `knowledge_base.category_id → categories(id)` 外键，否则 DROP 会被拒绝。执行前必须逐表 `pg_dump --data-only` 备份 |
| 225 | 225_runtime_tables_2.sql | 补齐代码已读写但仓库缺失的 4 张表：`discussion_sessions`（多模型讨论室会话，消息存 responses JSONB 数组）、`tasks`（写作任务，priority 用 CASE 排序）、`workflows`、`workflow_steps`。并 ALTER 补齐列漂移：`review_jobs` +chapter_no/session_id/aggregated_at、`review_reports` +reviewer_model/raw_content。列定义均由源码 SQL 反推 |

## Schema Evolution Summary

1. **Core (001-060)**: Users, workspaces, projects, chapters, events, characters, rules, foreshadowing, reviews
2. **State & Relationships (090-140)**: Canon documents, entity lifecycles, entity relationships, state snapshots, plot threads
3. **Settings & Models (150-160)**: Model profiles/costs, global setting system with BM25 search, genre canonical mapping
4. **Review & Knowledge (120-194)**: Review lifecycle, vector indexing, data tiers, backup/restore, prompt templates, knowledge base (3 systems: knowledge_base, ref_categories, user_knowledge)
5. **Content Quality (200-204)**: Context compression, character arcs, causality, pacing/emotions, style fingerprinting, events archive
6. **Infrastructure (205-213)**: Knowledge entity system, local storage indexes, knowledge packs, category restructuring, skill management, model user binding
7. **System Evolution (220-221)**: AI-driven system evolution (proposals with status flow), system-level profiles (style/prompt/model), notifications, version history triggers
8. **Runtime Completeness (222-223)**: 补齐代码已读写但仓库缺失建表 SQL 的运行时表（global_rules / evolution_logs / ref_tones / ref_tone_rules）+ canon_rules 规则升级字段 + 规则归纳摘要表
