# Entity & State 表详细设计

> 域: User & Workspace / 子域: 故事运行态实体、状态快照、实体关系
>
> 共 3 张表。这些表用于跟踪故事运行时的实体状态变化。

---

## 1. state_entities

**用途**: 故事运行态实体 — character/location/faction/item/concept/event 等实体，含摘要、描述、档案、别名、标签、重要性、生命周期状态、首次/最后出场章节。

> **重要**: character 和 faction 类实体请使用此表（通过 `state.entity.upsert`），而非 `kb.pk.upsert`（knowledge_entities）。

| 列名 | 类型 | 约束 | 描述 |
|------|------|------|------|
| `id` | `UUID` | **PK**, DEFAULT gen_random_uuid() | 主键 |
| `workspace_id` | `UUID` | **FK** -> workspaces(id), NOT NULL | 所属工作区 |
| `project_id` | `UUID` | **FK** -> projects(id), NOT NULL | 所属项目 |
| `entity_type` | `VARCHAR(50)` | NOT NULL, CHECK (IN: character, location, faction, item, concept, event, custom) | 实体类型 |
| `name` | `VARCHAR(500)` | NOT NULL | 实体名称 |
| `summary` | `TEXT` | 可空 | 实体摘要 |
| `description` | `TEXT` | 可空 | 实体详细描述 |
| `profile` | `JSONB` | DEFAULT "{}" | 实体档案（JSONB，灵活存储属性） |
| `aliases` | `TEXT[]` | DEFAULT "{}" | 别名列表 |
| `tags` | `TEXT[]` | DEFAULT "{}" | 标签列表 |
| `importance` | `INTEGER` | DEFAULT 3, CHECK (1-10) | 重要性 1-10 |
| `lifecycle_status` | `VARCHAR(50)` | DEFAULT "active", CHECK (IN: active, dormant, deceased, destroyed, archived, emerging) | 生命周期状态 |
| `first_seen_chapter_no` | `INTEGER` | 可空 | 首次出场章节编号 |
| `last_seen_chapter_no` | `INTEGER` | 可空 | 最后出场章节编号 |
| `source_kb_entity_id` | `UUID` | 可空 | 来源知识库实体 ID（如从 kb 导入） |
| `created_at` | `TIMESTAMPTZ` | DEFAULT now() | 创建时间 |
| `updated_at` | `TIMESTAMPTZ` | DEFAULT now() | 更新时间 |
| `metadata` | `JSONB` | DEFAULT "{}" | 扩展元数据 |

**唯一约束**: `uq_state_entities_name` UNIQUE (project_id, entity_type, name)

**索引**:
- `idx_state_entities_project` ON (project_id)
- `idx_state_entities_type` ON (entity_type)
- `idx_state_entities_lifecycle` ON (lifecycle_status)
- `idx_state_entities_tags` USING GIN (tags)

---

## 2. state_snapshots

**用途**: 实体状态快照 — 按章节记录实体的摘要、描述、档案、外观、关系、动机变化。每次章节结束后为涉及的实体创建快照。

| 列名 | 类型 | 约束 | 描述 |
|------|------|------|------|
| `id` | `UUID` | **PK**, DEFAULT gen_random_uuid() | 主键 |
| `entity_id` | `UUID` | **FK** -> state_entities(id) ON DELETE CASCADE, NOT NULL | 关联实体 |
| `chapter_no` | `INTEGER` | NOT NULL | 所属章节编号 |
| `snapshot_type` | `VARCHAR(50)` | DEFAULT "chapter_end", CHECK (IN: chapter_end, manual, event_trigger, volume_end) | 快照类型 |
| `summary` | `TEXT` | 可空 | 该时间点实体的摘要 |
| `description` | `TEXT` | 可空 | 该时间点的描述 |
| `profile` | `JSONB` | DEFAULT "{}" | 该时间点的档案（JSONB） |
| `appearance_state` | `TEXT` | 可空 | 外观状态描述 |
| `location` | `VARCHAR(500)` | 可空 | 当前位置 |
| `emotional_state` | `VARCHAR(255)` | 可空 | 情绪状态 |
| `physical_condition` | `VARCHAR(255)` | 可空 | 身体状况 |
| `relationships` | `JSONB` | DEFAULT "{}" | 关系状态快照（JSONB） |
| `motivations` | `TEXT[]` | DEFAULT "{}" | 当前动机列表 |
| `knowledge` | `JSONB` | DEFAULT "{}" | 知识状态（JSONB） |
| `goals` | `TEXT[]` | DEFAULT "{}" | 当前目标列表 |
| `inventory` | `JSONB` | DEFAULT "{}" | 物品/装备（JSONB） |
| `delta_from_previous` | `JSONB` | DEFAULT "{}" | 与上一快照的差异 |
| `created_at` | `TIMESTAMPTZ` | DEFAULT now() | 快照时间 |
| `metadata` | `JSONB` | DEFAULT "{}" | 扩展元数据 |

**唯一约束**: `uq_state_snapshots` UNIQUE (entity_id, chapter_no, snapshot_type)

**索引**:
- `idx_state_snapshots_entity` ON (entity_id)
- `idx_state_snapshots_chapter` ON (chapter_no)

---

## 3. entity_relationships

**用途**: 实体关系管理 — 定义故事实体之间的动态关系，支持关系类型、强度、方向性描述。

| 列名 | 类型 | 约束 | 描述 |
|------|------|------|------|
| `id` | `UUID` | **PK**, DEFAULT gen_random_uuid() | 主键 |
| `project_id` | `UUID` | **FK** -> projects(id), NOT NULL | 所属项目 |
| `source_entity_id` | `UUID` | **FK** -> state_entities(id) ON DELETE CASCADE, NOT NULL | 源实体 |
| `target_entity_id` | `UUID` | **FK** -> state_entities(id) ON DELETE CASCADE, NOT NULL | 目标实体 |
| `relationship_type` | `VARCHAR(100)` | NOT NULL | 关系类型：ally / enemy / family / lover / mentor / rival / subordinate / neutral / custom |
| `strength` | `INTEGER` | DEFAULT 5, CHECK (1-10) | 关系强度 1-10 |
| `direction` | `VARCHAR(20)` | DEFAULT "bidirectional", CHECK (IN: unidirectional, bidirectional) | 方向性 |
| `description` | `TEXT` | 可空 | 关系描述 |
| `history_summary` | `TEXT` | 可空 | 关系历史摘要 |
| `established_chapter_no` | `INTEGER` | 可空 | 关系建立的章节编号 |
| `last_affected_chapter_no` | `INTEGER` | 可空 | 最后影响章节编号 |
| `status` | `VARCHAR(50)` | DEFAULT "active", CHECK (IN: active, strained, broken, dormant, evolving) | 关系状态 |
| `tags` | `TEXT[]` | DEFAULT "{}" | 标签 |
| `created_at` | `TIMESTAMPTZ` | DEFAULT now() | 创建时间 |
| `updated_at` | `TIMESTAMPTZ` | DEFAULT now() | 更新时间 |
| `metadata` | `JSONB` | DEFAULT "{}" | 扩展元数据 |

**唯一约束**: `uq_entity_relationships` UNIQUE (source_entity_id, target_entity_id, relationship_type)

**CHECK 约束**: `chk_no_self_relation` CHECK (source_entity_id <> target_entity_id)

**索引**:
- `idx_entity_rel_source` ON (source_entity_id)
- `idx_entity_rel_target` ON (target_entity_id)
- `idx_entity_rel_type` ON (relationship_type)
- `idx_entity_rel_project` ON (project_id)
- `idx_entity_rel_tags` USING GIN (tags)

---

> **最后更新**: 2026-07-28
