# Knowledge Base Tables

This file documents all 3 knowledge systems in the database.

## System 1: Legacy Knowledge Base (190_extensible_categories + 194_knowledge_user_review)

> ⚠️ **已废弃（2026-10-10，migration 224）**
>
> `categories`、`knowledge_tags`、`knowledge_vectors`、`setting_category_relations`、`genre_category_bindings`
> 已由 `224_drop_legacy_kb_tables.sql` 删除。旧 `knowledge.*` 工具、`knowledge_service.py`、
> `js/pages/knowledge.js` 此前也已全部移除，Python 代码中旧表引用数为 0。
>
> 当前活跃体系为 **System 2（ref_categories / universal_knowledge / project_knowledge）**。
>
> 保留未删：`knowledge_base`（孤儿表，按 category-unification 设计保留）、`tags`（未列入删除清单）。
> `knowledge_base` 原有的 `category_id → categories(id)` 外键已由 224 先行解除。
>
> 下方各表结构**仅作历史存档**，不要再按此开发。

### `categories`（已删）
| Column | Type | Constraints |
|---|---|---|
| id | UUID | PK |
| slug | VARCHAR(50) | UNIQUE NOT NULL |
| name | VARCHAR(100) | NOT NULL |
| name_en | VARCHAR(100) | |
| description | TEXT | |
| icon | VARCHAR(50) | |
| color | VARCHAR(20) | |
| sort_order | INTEGER | DEFAULT 0 |
| parent_id | UUID | FK -> categories(id) |
| level | INTEGER | DEFAULT 0 |
| config | JSONB | DEFAULT '{}' |
| is_system | BOOLEAN | DEFAULT false |
| is_active | BOOLEAN | DEFAULT true |
| created_at | TIMESTAMPTZ | DEFAULT now() |
| updated_at | TIMESTAMPTZ | DEFAULT now() |

**Seed**: 10 system categories + 22+ PRESETS subcategories (193).
**Trigger**: update_categories_updated_at (before update, set updated_at=now())
**Indexes**: idx_category_sort

### `tags`
| Column | Type | Constraints |
|---|---|---|
| id | UUID | PK |
| slug | VARCHAR(50) | UNIQUE NOT NULL |
| name | VARCHAR(100) | NOT NULL |
| category | VARCHAR(50) | |
| description | TEXT | |
| color | VARCHAR(20) | |
| usage_count | INTEGER | DEFAULT 0 |
| is_recommended | BOOLEAN | DEFAULT false |
| is_active | BOOLEAN | DEFAULT true |
| created_at | TIMESTAMPTZ | DEFAULT now() |

**Seed**: 19 tags across 5 categories.
**Indexes**: idx_tags_usage

### `knowledge_base`（已废弃，孤儿表保留未删）
| Column | Type | Constraints |
|---|---|---|
| id | UUID | PK |
| code | VARCHAR(50) | |
| title | VARCHAR(200) | NOT NULL |
| content | TEXT | NOT NULL |
| summary | TEXT | |
| detail | TEXT | |
| examples | TEXT | |
| counter_examples | TEXT | |
| metadata | JSONB | DEFAULT '{}' |
| source | VARCHAR(50) | DEFAULT 'manual' |
| source_file | VARCHAR(200) | |
| category_id | UUID | FK -> categories(id) |
| applicable_genres | TEXT[] | DEFAULT '{}' |
| applicable_skills | TEXT[] | DEFAULT '{}' |
| level | VARCHAR(20) | DEFAULT 'knowledge' |
| status | VARCHAR(20) | DEFAULT 'active' |
| view_count | INTEGER | DEFAULT 0 |
| use_count | INTEGER | DEFAULT 0 |
| last_reviewed_at | TIMESTAMPTZ | (added 194) |
| reviewed_by | UUID | FK -> users(id) (added 194) |
| review_version | INTEGER | DEFAULT 1 (added 194) |
| search_vector | TSVECTOR | GENERATED: to_tsvector(coalesce(title)+coalesce(content)) |
| created_at | TIMESTAMPTZ | DEFAULT now() |
| updated_at | TIMESTAMPTZ | DEFAULT now() |

**Trigger**: update_knowledge_base_updated_at
**Indexes**: idx_knowledge_search(GIN), idx_knowledge_category, idx_knowledge_source, idx_knowledge_genres(GIN), idx_knowledge_skills(GIN), idx_knowledge_metadata(GIN), idx_knowledge_code
**Migration**: 191 migrates opencode-sourced items to canon_documents

### `knowledge_tags`（已删）
| Column | Type | Constraints |
|---|---|---|
| knowledge_id | UUID | FK -> knowledge_base(id) ON DELETE CASCADE |
| tag_id | UUID | FK -> tags(id) ON DELETE CASCADE |
| created_at | TIMESTAMPTZ | DEFAULT now() |

**PRIMARY KEY**: (knowledge_id, tag_id)

### `knowledge_vectors`（已删）
| Column | Type | Constraints |
|---|---|---|
| id | UUID | PK |
| knowledge_id | UUID | NOT NULL, FK -> knowledge_base(id) ON DELETE CASCADE |
| qdrant_collection | VARCHAR(100) | NOT NULL |
| qdrant_point_id | VARCHAR(100) | |
| vector_model | VARCHAR(50) | DEFAULT 'text-embedding-3-small' |
| dimension | INTEGER | DEFAULT 1536 |
| created_at | TIMESTAMPTZ | DEFAULT now() |

**UNIQUE**: (knowledge_id, qdrant_collection)

### `user_knowledge` (194)
| Column | Type | Constraints |
|---|---|---|
| id | UUID | PK |
| user_id | UUID | NOT NULL, FK -> users(id) ON DELETE CASCADE |
| base_knowledge_id | UUID | FK -> knowledge_base(id) ON DELETE SET NULL |
| code | VARCHAR(50) | |
| title | VARCHAR(200) | NOT NULL |
| content | TEXT | NOT NULL |
| summary | TEXT | |
| detail | TEXT | |
| examples | TEXT | |
| counter_examples | TEXT | |
| metadata | JSONB | DEFAULT '{}' |
| category_id | UUID | FK -> categories(id) |
| applicable_genres | TEXT[] | DEFAULT '{}' |
| applicable_skills | TEXT[] | DEFAULT '{}' |
| level | VARCHAR(20) | DEFAULT 'knowledge' |
| status | VARCHAR(20) | DEFAULT 'draft' |
| review_status | VARCHAR(20) | DEFAULT 'pending' |
| review_comment | TEXT | |
| view_count | INTEGER | DEFAULT 0 |
| use_count | INTEGER | DEFAULT 0 |
| source | VARCHAR(50) | DEFAULT 'user' |
| created_at | TIMESTAMPTZ | DEFAULT now() |
| updated_at | TIMESTAMPTZ | DEFAULT now() |

**Trigger**: update_user_knowledge_updated_at
**Indexes**: idx_user_knowledge_user, idx_user_knowledge_base, idx_user_knowledge_category, idx_user_knowledge_status, idx_user_knowledge_review, idx_user_knowledge_code

### `knowledge_review` (194)
| Column | Type | Constraints |
|---|---|---|
| id | UUID | PK |
| user_knowledge_id | UUID | NOT NULL, FK -> user_knowledge(id) ON DELETE CASCADE |
| submitter_id | UUID | NOT NULL, FK -> users(id) |
| submit_time | TIMESTAMPTZ | DEFAULT now() |
| submit_reason | TEXT | |
| reviewer_id | UUID | FK -> users(id) |
| review_time | TIMESTAMPTZ | |
| review_status | VARCHAR(20) | DEFAULT 'pending' |
| review_comment | TEXT | |
| merged_base_id | UUID | FK -> knowledge_base(id) |
| version | INTEGER | DEFAULT 1 |
| created_at | TIMESTAMPTZ | DEFAULT now() |

**Indexes**: idx_knowledge_review_user, idx_knowledge_review_status, idx_knowledge_review_submitter, idx_knowledge_review_reviewer

---

## System 2: Reference Knowledge System (205_knowledge_base_system + 208_restructure + 210_restructure)

### `ref_categories`
| Column | Type | Constraints |
|---|---|---|
| id | UUID | PK |
| parent_id | UUID | FK -> ref_categories(id) ON DELETE SET NULL |
| slug | VARCHAR(50) | NOT NULL UNIQUE |
| name | VARCHAR(100) | NOT NULL |
| description | TEXT | |
| genre_tags | TEXT[] | DEFAULT '{}' |
| search_keywords | TEXT[] | DEFAULT '{}' |
| sort_order | INT | DEFAULT 0 |
| is_system | BOOLEAN | DEFAULT false |
| created_at | TIMESTAMPTZ | DEFAULT now() |

**Original 5 top-level** (205): history, era, genre, professional, writing (with subcategories).
**Restructured to 9 top-level** (208): character_ref, equipment, creature, world_setting, power_system, history_culture, plot_ref, writing_ref, general_material (each with 3-5 child categories).
**Further 3-4 level refinement** (210): trope_core/emotion/conflict/growth/daily/suspense under plot_trope; geo_natural/city/region/special under geography; personality_inner/social; item_cheat/treasure/world; struct_opening/middle/ending; style_platform/genre; char_protagonist/supporting/antagonist/group.
**Indexes**: idx_rc_parent, idx_rc_slug

### `ref_tones` (222_runtime_tables)
| Column | Type | Constraints |
|---|---|---|
| id | UUID | PK |
| slug | TEXT | NOT NULL UNIQUE |
| name | TEXT | NOT NULL |
| description | TEXT | NOT NULL, DEFAULT '' |
| is_active | BOOLEAN | NOT NULL, DEFAULT true |
| sort_order | INTEGER | NOT NULL, DEFAULT 0 |

故事基调（如"热血爽文 / 暗黑压抑 / 轻松搞笑"）。项目向导的 `tone_style` 选项来源，也是讨论室 `tones` 数据源之一。由 `tone.*` 工具维护，详见 [03-backend/tone-system.md](../03-backend/tone-system.md)。

### `ref_tone_rules` (222_runtime_tables)
| Column | Type | Constraints |
|---|---|---|
| id | UUID | PK |
| tone_slug | TEXT | NOT NULL |
| rule_type | TEXT | NOT NULL |
| title | TEXT | NOT NULL |
| content | TEXT | NOT NULL |
| severity | TEXT | NOT NULL, DEFAULT 'warning' |
| sort_order | INTEGER | NOT NULL, DEFAULT 0 |

基调关联的创作规则模板。项目创建时按所选基调批量写入 `canon_rules`。
**不建外键**：删除基调时由 `tone.delete` 工具先删规则再删基调，避免迁移在已存在孤儿行的库上失败。
**Indexes**: idx_ref_tone_rules_tone_slug

### `knowledge_entities`
| Column | Type | Constraints |
|---|---|---|
| id | UUID | PK |
| entity_type | VARCHAR(50) | NOT NULL |
| name | VARCHAR(200) | NOT NULL |
| aliases | TEXT[] | DEFAULT '{}' |
| summary | TEXT | |
| content | TEXT | NOT NULL |
| structured_data | JSONB | DEFAULT '{}' |
| source | VARCHAR(50) | DEFAULT 'manual' |
| source_url | TEXT | |
| reliability | FLOAT | DEFAULT 0.5 |
| genre_tags | TEXT[] | DEFAULT '{}' |
| era | VARCHAR(100) | |
| embedding_id | TEXT | |
| search_vector | TSVECTOR | GENERATED: to_tsvector(coalesce(name)+coalesce(content)) |
| status | VARCHAR(20) | DEFAULT 'active' |
| use_count | INT | DEFAULT 0 |
| created_at | TIMESTAMPTZ | DEFAULT now() |
| updated_at | TIMESTAMPTZ | DEFAULT now() |

**Indexes**: idx_ke_type, idx_ke_genre(GIN), idx_ke_search(GIN), idx_ke_embedding, idx_ke_name, idx_ke_status

### `knowledge_relations`
| Column | Type | Constraints |
|---|---|---|
| id | UUID | PK |
| from_entity_id | UUID | FK -> knowledge_entities(id) ON DELETE CASCADE |
| to_entity_id | UUID | FK -> knowledge_entities(id) ON DELETE CASCADE |
| relation_type | VARCHAR(50) | NOT NULL |
| relation_detail | VARCHAR(200) | |
| strength | FLOAT | DEFAULT 1.0 |
| metadata | JSONB | DEFAULT '{}' |
| created_at | TIMESTAMPTZ | DEFAULT now() |

**UNIQUE**: (from_entity_id, to_entity_id, relation_type)
**Indexes**: idx_kr_from, idx_kr_to, idx_kr_type

### `universal_knowledge`
| Column | Type | Constraints |
|---|---|---|
| id | UUID | PK |
| category_id | UUID | FK -> ref_categories(id) ON DELETE SET NULL |
| topic | VARCHAR(200) | NOT NULL |
| summary | TEXT | |
| content | TEXT | NOT NULL |
| structured_data | JSONB | DEFAULT '{}' |
| era | VARCHAR(100) | |
| year_range | INT[] | |
| genre_tags | TEXT[] | DEFAULT '{}' |
| source | VARCHAR(50) | DEFAULT 'manual' |
| source_url | TEXT | |
| reliability | FLOAT | DEFAULT 0.5 |
| last_verified_at | TIMESTAMPTZ | |
| embedding_id | TEXT | |
| search_vector | TSVECTOR | GENERATED: to_tsvector(coalesce(topic)+coalesce(content)) |
| tags | TEXT[] | DEFAULT '{}' |
| status | VARCHAR(20) | DEFAULT 'active' |
| use_count | INT | DEFAULT 0 |
| created_at | TIMESTAMPTZ | DEFAULT now() |
| updated_at | TIMESTAMPTZ | DEFAULT now() |

**Indexes**: idx_uk_genre(GIN), idx_uk_year, idx_uk_search(GIN), idx_uk_embedding, idx_uk_category, idx_uk_status
**Recategorization**: 208 restructured categories and 210 further refined

### `project_knowledge`
| Column | Type | Constraints |
|---|---|---|
| id | UUID | PK |
| project_id | UUID | NOT NULL |
| category | VARCHAR(50) | NOT NULL |
| key | VARCHAR(200) | NOT NULL |
| value | JSONB | NOT NULL |
| description | TEXT | |
| chapter_no | INT | |
| related_entry_ids | UUID[] | DEFAULT '{}' |
| tags | TEXT[] | DEFAULT '{}' |
| status | VARCHAR(20) | DEFAULT 'active' |
| created_at | TIMESTAMPTZ | DEFAULT now() |
| updated_at | TIMESTAMPTZ | DEFAULT now() |

**UNIQUE**: (project_id, category, key)
**Indexes**: idx_pk_project, idx_pk_category, idx_pk_status

### `world_snapshots`
| Column | Type | Constraints |
|---|---|---|
| id | UUID | PK |
| project_id | UUID | NOT NULL |
| chapter_no | INT | NOT NULL |
| story_time | VARCHAR(100) | |
| story_year | INT | |
| story_era | VARCHAR(100) | |
| story_progress | FLOAT | |
| world_state | JSONB | NOT NULL |
| character_count | INT | DEFAULT 0 |
| active_threads | TEXT[] | DEFAULT '{}' |
| relevant_knowledge_ids | UUID[] | DEFAULT '{}' |
| created_at | TIMESTAMPTZ | DEFAULT now() |

**Indexes**: idx_ws_project(project_id, chapter_no)

### `ref_search_jobs`
| Column | Type | Constraints |
|---|---|---|
| id | UUID | PK |
| project_id | UUID | |
| query_text | TEXT | NOT NULL |
| search_context | TEXT | |
| category_id | UUID | FK -> ref_categories(id) ON DELETE SET NULL |
| status | VARCHAR(20) | DEFAULT 'pending' |
| results_count | INT | DEFAULT 0 |
| entries_created | INT | DEFAULT 0 |
| error_message | TEXT | |
| triggered_by | VARCHAR(50) | |
| chapter_no | INT | |
| created_at | TIMESTAMPTZ | DEFAULT now() |
| completed_at | TIMESTAMPTZ | |

**Indexes**: idx_rsj_status, idx_rsj_project

### `ref_gap_logs`
| Column | Type | Constraints |
|---|---|---|
| id | UUID | PK |
| project_id | UUID | |
| gap_type | VARCHAR(50) | NOT NULL |
| description | TEXT | NOT NULL |
| context | TEXT | |
| entity_name | VARCHAR(200) | |
| entity_type | VARCHAR(50) | |
| resolved | BOOLEAN | DEFAULT false |
| resolved_by_entry_id | UUID | |
| resolved_at | TIMESTAMPTZ | |
| created_at | TIMESTAMPTZ | DEFAULT now() |

**Indexes**: idx_rgl_project, idx_rgl_resolved

---

## System 3: Genre & Knowledge Pack (207_knowledge_pack_system)

### `genre_knowledge_config`
| Column | Type | Constraints |
|---|---|---|
| id | UUID | PK |
| genre | VARCHAR(50) | NOT NULL UNIQUE |
| included_categories | TEXT[] | DEFAULT '{}' |
| excluded_categories | TEXT[] | DEFAULT '{}' |
| description | TEXT | |
| created_at | TIMESTAMP | DEFAULT NOW() |
| updated_at | TIMESTAMP | DEFAULT NOW() |

**Seed**: 8 types (Bow, End, v, ai, History, Super, City, Game, Unlimited) with per-genre category inclusion/exclusion rules.

### `project_knowledge_pack`
| Column | Type | Constraints |
|---|---|---|
| id | UUID | PK |
| project_id | UUID | NOT NULL UNIQUE |
| genre | VARCHAR(50) | |
| active_categories | TEXT[] | DEFAULT '{}' |
| custom_categories | JSONB | DEFAULT '{}' |
| created_at | TIMESTAMP | DEFAULT NOW() |
| updated_at | TIMESTAMP | DEFAULT NOW() |

**Indexes**: idx_project_pack_project

### `genre_canonical` (from 160_global_settings)
| Column | Type | Constraints |
|---|---|---|
| canonical_genre | TEXT | PRIMARY KEY |
| platform_tags | TEXT[] | DEFAULT '{}' |
| aliases | TEXT[] | DEFAULT '{}' |
| description | TEXT | |
| metadata | JSONB | DEFAULT '{}' |
| created_at | TIMESTAMPTZ | DEFAULT now() |
| updated_at | TIMESTAMPTZ | DEFAULT now() |

**Seed**: 15 canonical genres (City, Complex, Xianxia, Fantasy, SciFi, History, Suspense, Game, AncientRom, ModernRom, FantasyRom, Era, Farming, QuickTrans, Derivative).
**Indexes**: GIN on platform_tags, aliases.

---

## Knowledge System Architecture Notes

1. **3 independent knowledge systems** exist side by side:
   - **Legacy** (190): categories + knowledge_base + tags + vectors. Used by opencode imports (migrated to canon_documents in 191)
   - **Reference** (205): ref_categories + knowledge_entities + universal_knowledge + project_knowledge + world_snapshots + search_jobs + gap_logs. More structured, era-aware, genre-tagged.
   - **User knowledge** (194): user_knowledge + knowledge_review. Per-user private knowledge with review workflow.
   - **Pack system** (207): genre_knowledge_config + project_knowledge_pack. Genre-based category filtering.

2. **Category system duplication**: `categories` (190, hierarchical with parent_id) vs `ref_categories` (205, hierarchical with parent_id FK ON DELETE SET NULL) vs `setting_categories` (160, per-workspace). Three parallel category trees.

3. **NVECTOR generation**: Used in knowledge_base, knowledge_entities, universal_knowledge (via GENERATED ALWAYS AS to_tsvector...).

4. **Vector indexing**: knowledge_vectors maps Qdrant points. knowledge_entities has embedding_id for external embedding references.
