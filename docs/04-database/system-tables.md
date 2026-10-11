# System-Level Tables

## System Evolution

### `system_evolution_proposals`
| Column | Type | Constraints |
|---|---|---|
| id | UUID | PK |
| title | TEXT | NOT NULL |
| description | TEXT | NOT NULL |
| proposal_type | TEXT | NOT NULL, CHECK: create/update/delete/merge |
| target_entity_type | TEXT | NOT NULL, CHECK: style_profile/prompt_template/model_profile/knowledge_item/setting_item/genre_config |
| target_entity_id | UUID |  |
| target_entity_key | TEXT |  |
| proposed_content | JSONB | NOT NULL |
| evolution_reason | TEXT | NOT NULL |
| evidence | JSONB |  |
| source_project_id | UUID | FK projects(id) SET NULL |
| source_chapter_no | INTEGER |  |
| status | TEXT | NOT NULL, DEFAULT draft, flow: draft->ai_reviewing->ai_reviewed->pending_admin->admin_approved/rejected->applied |
| ai_review_result | JSONB |  |
| ai_retry_count | INTEGER | DEFAULT 0 |
| ai_last_error | TEXT |  |
| admin_review_result | JSONB |  |
| submitted_by | UUID | FK users(id) SET NULL |
| ai_submitter | TEXT |  |
| applied_at | TIMESTAMPTZ |  |
| applied_version | INTEGER |  |
| metadata | JSONB | NOT NULL, DEFAULT {} |
| created_at | TIMESTAMPTZ | NOT NULL |
| updated_at | TIMESTAMPTZ | NOT NULL |
**Indexes**: idx_evolution_proposals_status, target_entity, created, ai_submitter

## Global Rules (222_runtime_tables)

### `global_rules`
| Column | Type | Constraints |
|---|---|---|
| id | UUID | PK |
| rule_key | TEXT | NOT NULL, UNIQUE |
| rule_type | TEXT | NOT NULL — creative / compliance / polish |
| title | TEXT | NOT NULL |
| content | TEXT | NOT NULL |
| severity | TEXT | NOT NULL, DEFAULT warning |
| status | TEXT | NOT NULL, DEFAULT active（软删除置 inactive） |
| metadata | JSONB | NOT NULL, DEFAULT {} |
| source_project_id | UUID | FK projects(id) SET NULL |
| promoted_from_rule_id | UUID | FK canon_rules(id) SET NULL |
| promoted_by | TEXT | |
| discussion_id | TEXT | |
| created_at | TIMESTAMPTZ | NOT NULL |
| updated_at | TIMESTAMPTZ | NOT NULL |

跨项目生效的规则，由 `global_rules.*` 工具维护。项目规则经 `global_rules.promote` 升级而来，溯源字段记录来源项目与规则。
**Indexes**: idx_global_rules_status_type, idx_global_rules_source_project
**Trigger**: update_global_rules_updated_at（复用 220 的 `update_updated_at_column`）

## Evolution Logs (222_runtime_tables)

### `evolution_logs`
| Column | Type | Constraints |
|---|---|---|
| id | UUID | PK |
| source_type | TEXT | NOT NULL — discussion_room / agent / user |
| source_id | TEXT | session_id / chapter_no / username |
| action | TEXT | NOT NULL — INSERT / UPDATE / DELETE / ROLLBACK |
| target_table | TEXT | NOT NULL |
| target_id | TEXT | |
| old_value | JSONB | 回滚依据 |
| new_value | JSONB | |
| risk_level | TEXT | low / medium / high / info |
| risk_reason | TEXT | |
| auto_applied | BOOLEAN | DEFAULT false |
| proposal_id | UUID | FK system_evolution_proposals(id) SET NULL |
| created_at | TIMESTAMPTZ | DEFAULT now() |
| created_by | TEXT | |

gatekeeper 门禁的审计表：所有进化产出先经 `services/gatekeeper.py` 风险评估再落表，管理员可据此回滚。
**Indexes**: idx_evolution_logs_created, source, risk, target, created_by

## System Style Profiles

### `system_style_profiles`
| Column | Type | Constraints |
|---|---|---|
| id | UUID | PK |
| profile_key | TEXT | NOT NULL, UNIQUE |
| display_name | TEXT | NOT NULL |
| narrative_pov | TEXT | NOT NULL, DEFAULT third_limited |
| tense | TEXT | NOT NULL, DEFAULT past |
| tone | TEXT | NOT NULL |
| target_metrics | JSONB | NOT NULL, DEFAULT {} |
| description | TEXT |  |
| characteristics | JSONB |  |
| sample_paragraphs | TEXT[] |  |
| applicable_genres | TEXT[] |  |
| version | INTEGER | NOT NULL, DEFAULT 1 |
| version_history | JSONB | NOT NULL, DEFAULT [] |
| status | TEXT | NOT NULL, DEFAULT active, CHECK: active/deprecated/draft |
| created_from_proposal_id | UUID | FK system_evolution_proposals(id) SET NULL |
| created_at | TIMESTAMPTZ | NOT NULL |
| updated_at | TIMESTAMPTZ | NOT NULL |
**Indexes**: idx_system_style_profiles_status, idx_system_style_profiles_genres(GIN)
**Trigger**: maintain_style_profile_version | **Seed**: 5 profiles

## System Prompt Templates

### `system_prompt_templates`
| Column | Type | Constraints |
|---|---|---|
| id | UUID | PK |
| template_key | TEXT | NOT NULL, UNIQUE |
| template_name | TEXT | NOT NULL |
| template_content | TEXT | NOT NULL |
| description | TEXT |  |
| template_type | TEXT | NOT NULL |
| genre | TEXT |  |
| scene | TEXT |  |
| variables | JSONB | NOT NULL, DEFAULT [] |
| version | INTEGER | NOT NULL, DEFAULT 1 |
| version_history | JSONB | NOT NULL, DEFAULT [] |
| status | TEXT | NOT NULL, DEFAULT active |
| created_from_proposal_id | UUID | FK system_evolution_proposals(id) SET NULL |
| created_at | TIMESTAMPTZ | NOT NULL |
| updated_at | TIMESTAMPTZ | NOT NULL |
**Indexes**: idx_system_prompt_templates_type, idx_system_prompt_templates_genre
**Trigger**: maintain_prompt_template_version | **Seed**: 4 templates

## System Model Profiles

### `system_model_profiles`
| Column | Type | Constraints |
|---|---|---|
| id | UUID | PK |
| profile_key | TEXT | NOT NULL, UNIQUE |
| display_name | TEXT | NOT NULL |
| provider | TEXT | NOT NULL |
| model_name | TEXT | NOT NULL |
| task_types | TEXT[] | NOT NULL |
| default_params | JSONB | NOT NULL, DEFAULT {} |
| cost_config | JSONB | NOT NULL, DEFAULT {} |
| rate_limit_config | JSONB | NOT NULL, DEFAULT {} |
| recommended_for | JSONB |  |
| version | INTEGER | NOT NULL, DEFAULT 1 |
| version_history | JSONB | NOT NULL, DEFAULT [] |
| status | TEXT | NOT NULL, DEFAULT active |
| created_from_proposal_id | UUID | FK system_evolution_proposals(id) SET NULL |
| created_at | TIMESTAMPTZ | NOT NULL |
| updated_at | TIMESTAMPTZ | NOT NULL |
**Indexes**: idx_system_model_profiles_status, idx_system_model_profiles_task_types(GIN)
**Trigger**: maintain_model_profile_version | **Seed**: 4 profiles

## System Notifications

### `system_notifications`
| Column | Type | Constraints |
|---|---|---|
| id | UUID | PK |
| user_id | UUID | FK users(id) CASCADE |
| is_global | BOOLEAN | NOT NULL, DEFAULT FALSE |
| type | TEXT | NOT NULL, CHECK: evolution_proposal/system_update/ai_review_completed/admin_review_required |
| title | TEXT | NOT NULL |
| content | TEXT | NOT NULL |
| related_proposal_id | UUID | FK system_evolution_proposals(id) CASCADE |
| is_read | BOOLEAN | NOT NULL, DEFAULT FALSE |
| read_at | TIMESTAMPTZ |  |
| expires_at | TIMESTAMPTZ | NOT NULL, DEFAULT now()+90d |
| created_at | TIMESTAMPTZ | NOT NULL |
**Indexes**: idx_system_notifications_user, global, expires
**Function**: cleanup_expired_notifications()

## Project-Level Prompt Templates (from 160_p7_enhancement)

### `prompt_templates`
| Column | Type | Constraints |
|---|---|---|
| id | UUID | PK |
| project_id | UUID | NOT NULL |
| template_key | VARCHAR(255) | NOT NULL |
| name | VARCHAR(500) | NOT NULL |
| description | TEXT |  |
| template_content | TEXT | NOT NULL |
| template_type | VARCHAR(50) | DEFAULT system |
| variables | JSONB | DEFAULT [] |
| genre | VARCHAR(100) |  |
| scene | VARCHAR(100) |  |
| version | INTEGER | DEFAULT 1 |
| is_active | BOOLEAN | DEFAULT TRUE |
| is_system | BOOLEAN | DEFAULT FALSE |
| usage_count | INTEGER | DEFAULT 0 |
| last_used_at | TIMESTAMP |  |
| created_by | VARCHAR(255) |  |
| created_at | TIMESTAMP |  |
| updated_at | TIMESTAMP |  |
**UNIQUE**: (project_id, template_key)

### `prompt_template_versions`
| Column | Type | Constraints |
|---|---|---|
| id | UUID | PK |
| template_id | UUID | NOT NULL |
| version | INTEGER | NOT NULL |
| template_content | TEXT | NOT NULL |
| variables | JSONB | DEFAULT [] |
| change_summary | TEXT |  |
| created_by | VARCHAR(255) |  |
| created_at | TIMESTAMP |  |
**UNIQUE**: (template_id, version)

### `prompt_template_usage_logs`
| Column | Type | Constraints |
|---|---|---|
| id | UUID | PK |
| template_id | UUID | NOT NULL |
| project_id | UUID | NOT NULL |
| variables_used | JSONB | DEFAULT {} |
| rendered_content | TEXT |  |
| tokens_used | INTEGER |  |
| created_by | VARCHAR(255) |  |
| created_at | TIMESTAMP |  |

## Context & Reference

### `context_weight_configs`
| Column | Type | Constraints |
|---|---|---|
| id | UUID | PK |
| project_id | UUID | NOT NULL |
| config_name | VARCHAR(255) | NOT NULL |
| profile | VARCHAR(100) | DEFAULT default |
| weights | JSONB | NOT NULL, DEFAULT {} |
| max_total_tokens | INTEGER | DEFAULT 8000 |
| priority_order | JSONB | DEFAULT [] |
| is_active | BOOLEAN | DEFAULT TRUE |
| created_at | TIMESTAMP |  |
| updated_at | TIMESTAMP |  |
**UNIQUE**: (project_id, config_name, profile)

### `reference_materials`
| Column | Type | Constraints |
|---|---|---|
| id | UUID | PK |
| project_id | UUID | NOT NULL |
| material_key | VARCHAR(255) | NOT NULL |
| title | VARCHAR(500) | NOT NULL |
| content | TEXT |  |
| material_type | VARCHAR(50) | NOT NULL |
| category | VARCHAR(100) |  |
| tags | TEXT[] | DEFAULT {} |
| source_url | TEXT |  |
| source_credit | VARCHAR(500) |  |
| file_path | VARCHAR(1000) |  |
| usage_count | INTEGER | DEFAULT 0 |
| favorite | BOOLEAN | DEFAULT FALSE |
| metadata | JSONB | DEFAULT {} |
| created_by | VARCHAR(255) |  |
| created_at | TIMESTAMP |  |
| updated_at | TIMESTAMP |  |
**UNIQUE**: (project_id, material_key)

### `reader_expectations`
| Column | Type | Constraints |
|---|---|---|
| id | UUID | PK |
| project_id | UUID | NOT NULL |
| expectation_key | VARCHAR(255) | NOT NULL |
| title | VARCHAR(500) | NOT NULL |
| description | TEXT |  |
| expectation_type | VARCHAR(50) | NOT NULL |
| status | VARCHAR(50) | DEFAULT active |
| chapter_no | INTEGER |  |
| payoff_chapter_no | INTEGER |  |
| importance | VARCHAR(50) | DEFAULT medium |
| tags | TEXT[] | DEFAULT {} |
| metadata | JSONB | DEFAULT {} |
| created_by | VARCHAR(255) |  |
| created_at | TIMESTAMP |  |
| updated_at | TIMESTAMP |  |
**UNIQUE**: (project_id, expectation_key)
