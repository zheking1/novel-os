# Specialized Services — 专项服务集合

**源码**:
- `novel-os-mcp/src/novel_os_mcp/p7_services.py` (976 行)
- `novel-os-mcp/src/novel_os_mcp/p8_services.py` (480 行)

## 概述

本文档涵盖 8 个专项服务，按源码文件组织。

---

## 一、参考素材服务 (ReferenceMaterialService)

**位置**: `p7_services.py`

### 概述

管理项目级参考素材库，支持多种素材类型、分类、标签、来源记录和收藏。

### 素材属性

| 字段 | 说明 |
|------|------|
| `material_key` | 业务键 |
| `material_type` | 素材类型 |
| `category` | 分类 |
| `tags` | 标签数组 |
| `source_url` | 来源 URL |
| `source_credit` | 来源鸣谢 |
| `favorite` | 是否收藏 |
| `usage_count` | 使用计数 |

### 方法

| 方法 | 说明 |
|------|------|
| `upsert_material()` | 创建/更新素材 |
| `get_material()` | 获取素材详情 |
| `list_materials()` | 列表查询 (支持 `search`: ILIKE 全文搜索、`tags`: 数组交集 `&&`) |
| `toggle_favorite()` | 切换收藏状态 (`favorite = NOT favorite`) |
| `delete_material()` | 物理删除 |

### 数据库表

`reference_materials`

---

## 二、读者期待服务 (ReaderExpectationService)

**位置**: `p7_services.py`

### 概述

管理读者期待（reader expectations），追踪哪些情节线索或元素是读者预期会被回收的。

### 属性

| 字段 | 说明 |
|------|------|
| `expectation_key` | 业务键 |
| `expectation_type` | 期待类型 |
| `chapter_no` | 关联章节 |
| `payoff_chapter_no` | 回收章节 |
| `status` | `active` / `fulfilled` / `abandoned` |

### 方法

| 方法 | 说明 |
|------|------|
| `upsert_expectation()` | 创建/更新期待 |
| `list_expectations()` | 按 `status`/`type`/`importance` 过滤 |
| `mark_fulfilled()` | 标记为已回收 (`status='fulfilled'`, 记录 `payoff_chapter_no`) |

### 数据库表

`reader_expectations`

---

## 三、章节批注服务 (ChapterAnnotationService)

**位置**: `p7_services.py`

### 概述

管理章节内联批注，支持锚点定位（`anchor_start`/`anchor_end`）和父子批注关系。

### 属性

| 字段 | 说明 |
|------|------|
| `annotation_type` | 批注类型 (comment/revision/flag) |
| `content` | 批注内容 |
| `anchor_start` | 正文起始位置 (char offset) |
| `anchor_end` | 正文结束位置 (char offset) |
| `parent_id` | 父批注 ID (嵌套回复) |
| `resolve_status` | 解决状态 (`open`/`resolved`) |
| `resolved_by` / `resolved_at` | 解决人和时间 |

### 方法

| 方法 | 说明 |
|------|------|
| `create_annotation()` | 创建批注 |
| `list_annotations()` | 按 `chapter_id`/`type`/`resolve_status` 过滤，按 `chapter_no, anchor_start, created_at` 排序 |
| `resolve_annotation()` | 标记为已解决 |

### 数据库表

`chapter_annotations`

---

## 四、专有名词服务 (ProperNounService)

**位置**: `p7_services.py`

### 概述

管理项目专属名词字典（人名、地名、术语等），确保写作中的名词一致性。

### 属性

| 字段 | 说明 |
|------|------|
| `noun_key` | 名词标识 |
| `noun_value` | 名词标准值 |
| `noun_type` | 类型 (character/location/term) |
| `aliases` | 别名列表 |
| `locked` | 是否锁定 (锁定名词不允许使用别名) |
| `first_chapter_no` | 首次出现章节 |
| `usage_count` | 使用计数 |

### check_consistency 方法

检查文本中名词使用是否与字典一致:

1. 遍历所有名词
2. 检查正文中是否使用了标准值或别名
3. `locked=true` 的名词若使用了别名 → 标记为 `inconsistent`

### 数据库表

`proper_nouns`

---

## 五、全文检索服务 (FulltextSearchService)

**位置**: `p7_services.py`

### 概述

跨模块全文搜索，使用 PostgreSQL `tsvector` + `tsquery`。

### 核心

- **索引**: 数据写入时调用 `index_record()` 更新 `fulltext_search_records` 表
- **搜索**: 使用 `plainto_tsquery('chinese', query)` → `ts_rank` 排序 → `ts_headline` 高亮摘录

### search 方法

- `query`: 自然语言查询
- `source_types`: 过滤来源模块
- 返回: `rank` (相关性分数)、`snippet` (高亮摘录, MaxWords=50, MinWords=20)

### 数据库表

`fulltext_search_records` (含 `search_vector` tsvector 列，需要 update trigger 维护)

---

## 六、关系图谱服务 (RelationshipGraphService)

**位置**: `p8_services.py`

### 概述

提供实体关系可视化数据（nodes + edges 格式），用于前端图谱渲染。

### get_graph_data

获取全项目关系图谱:

1. 查询 `state_entities` (lifecycle_status='active') → nodes
2. 查询 `entity_relationships` (status IN 'active','known') → edges

**Nodes**: `{id, type, name, profile[:200]}`

**Edges**: `{id, source, target, type, attitude, intensity, visibility}`

### get_subgraph

以某实体为中心获取子图（depth=2）:

1. 获取与中心实体有直接关系的所有实体
2. 获取这些实体之间的所有关系

### get_timeline_data

获取实体状态变化时间线:

- 从 `state_snapshots` 表查询，按 `chapter_no, volume_no, created_at` 排序
- 支持按 `entity_id` 过滤

### 数据库表

`state_entities`, `entity_relationships`, `state_snapshots`

---

## 七、模板市场服务 (TemplateMarketService)

**位置**: `p8_services.py`

### 概述

Prompt 模板的分享和发现平台。模板发布后可在市场中被其他项目发现和使用。

### publish_template

发布模板到市场: 更新 `prompt_templates.metadata` 添加 `marketplace: {category, tags, published: true}`。

### discover_templates

发现市场模板: 按 `category`、`tags`、`search` 过滤，按 `usage_count DESC` 排序。

### 数据库表

`prompt_templates` (metadata JSONB 字段中存储 marketplace 信息)

---

## 八、离线增强服务 (OfflineEnhancementService)

**位置**: `p8_services.py`

### 概述

支持离线写作场景的会话管理和变更队列同步。

### create_offline_session

创建离线写作会话（`offline_sync_sessions` 表）。

### queue_offline_changes

将离线变更加入队列（`offline_change_queue` 表）：

| 字段 | 说明 |
|------|------|
| `change_type` | `upsert` / `delete` |
| `entity_type` | `state_entity` / `state_snapshot` / `foreshadowing` |
| `entity_id` | 目标实体 ID |
| `change_data` | JSONB 变更数据 |

### sync_offline_session

同步离线会话的核心方法:

1. 获取所有 `pending` 状态的变更
2. 逐条执行:
   - `upsert` → `_apply_upsert()`：根据 entity_type 写入对应表
   - `delete` → `_apply_delete()`：软删除
3. 更新变更状态为 `synced` 或 `failed`
4. 更新会话状态 (`completed` / `partial`)

**支持的实体类型**:

| entity_type | upsert 行为 | delete 行为 |
|------|------|------|
| `state_entity` | INSERT ... ON CONFLICT UPDATE profile | `isarchived = true` |
| `state_snapshot` | INSERT (is_current=true) | 不处理 |
| `foreshadowing` | INSERT ... ON CONFLICT DO NOTHING | `payoff_status = 'cancelled'` |

### 数据库表

`offline_sync_sessions`, `offline_change_queue`

---

## 九、语音输入服务 (VoiceInputService)

**位置**: `p8_services.py`

### 概述

管理语音转文字的写作草稿。

### save_voice_draft

保存语音草稿:
- `audio_data`: base64 编码的音频数据
- `transcription`: 转录文本

### list_voice_drafts

按 `chapter_no` 过滤语音草稿列表。

### 数据库表

`voice_drafts`

---

## 工作流引导

- **素材管理**: `reference.upsert_material()` → `reference.list_materials(search="关键词")` → `reference.toggle_favorite()`
- **读者期待**: `reader_expectation.upsert()` → `reader_expectation.mark_fulfilled()`
- **批注**: `annotation.create()` → `annotation.resolve()`
- **名词管理**: `proper_noun.upsert()` → `proper_noun.check_consistency(text)`
- **全文搜索**: `fulltext.search(query)` → 跨模块检索
- **关系图谱**: `graph.get_data()` / `graph.get_subgraph()` 可视化
- **模板市场**: `template_market.publish()` / `template_market.discover()`
- **离线同步**: 创建 session → queue changes → sync
- **语音输入**: `voice.save_draft()` → 转录文本