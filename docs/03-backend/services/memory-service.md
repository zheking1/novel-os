# MemoryService - 记忆与实体状态服务

## 概述

`MemoryService` 是 Novel OS 的状态管理核心，负责实体 CRUD、时间序列状态快照、实体关系管理和语义向量搜索。

**源码路径**: `novel-os-mcp/src/novel_os_mcp/services/memory.py` (1032行)

## 注入依赖

```python
MemoryService(db, embedding_service=None, vector_index=None)
```

## 一、实体管理 (state_entities)

### 实体类型

`character`, `location`, `faction`, `item`, `event`, `concept`, `creature`, `artifact`

### 生命周期状态

`active`, `dead`, `exited`, `destroyed`, `dormant`, `unknown`, `archived`

### upsert_entity()

创建或更新实体。唯一约束: `(project_id, entity_type, name)`。

更新策略 (ON CONFLICT DO UPDATE):
- aliases/tags: 若传入则为新值，否则保留旧值
- profile: `旧 || 新` (JSONB 深度合并)
- summary/description/portrait_url: COALESCE(新, 旧)
- first_seen: LEAST
- last_seen: GREATEST
- lifecycle_status/importance/source_type: 直接覆盖
- metadata: `旧 || 新` 合并

### list_entities()

支持过滤: entity_type, lifecycle_status, query (ILIKE name或别名匹配), tags (数组交集 `&&`), include_archived。

LEFT JOIN LATERAL 获取 current snapshot 的 id 和 state。

### get_entity()

三模式查询: entity_id 或 entity_type+name。返回时含 current snapshot 详情 (effective/expire 章节/卷, duration_type, expires_on_event, confidence, change_reason)。

### get_state()

快捷方法，通过 entity_type + name 获取完整 state_snapshot。

### bulk_patch_entities()

批量更新实体，允许字段: aliases, profile, lifecycle_status, importance, tags, first_seen/last_seen_chapter_no/volume_no, source_type, source_id, metadata。

## 二、状态快照 (state_snapshots)

### upsert_snapshot()

时间序列状态追踪。核心参数:

| 参数 | 说明 |
|------|------|
| `state` | JSONB 状态体 |
| `is_current` | 是否当前状态 (true 时自动将旧快照设为 false) |
| `chapter_no`, `chapter_id` | 关联章节 |
| `effective_chapter_no`, `expire_chapter_no` | 生效范围 |
| `effective_volume_no`, `expire_volume_no` | 卷范围 |
| `duration_type` | persistent / temporary / permanent / conditional |
| `expires_on_event` | 事件触发后过期 |
| `confidence` | 置信度 0.0-1.0 |
| `source_commit_id` | 来源提交 |

事务流程: 解析实体 (create_if_missing=True) → 若 is_current 则全部旧 snapshots 设为 false → INSERT 新 snapshot → 返回时附加 entity_type 和 name。

### list_snapshots()

支持: entity_id / entity_type+name 过滤, current_only 模式, current_chapter_no 有效期过滤, include_expired 开关。

### get_snapshot_at_chapter()

获取特定章节时的有效状态快照。查询: effective_chapter_no <= target AND expire_chapter_no >= target (或 NULL)。

### get_entity_state_timeline()

返回实体在章节区间内的状态变更时间线。使用 `DISTINCT ON (effective_chapter_no, chapter_id)` 去重。

## 三、实体关系 (entity_relationships)

### upsert_relationship()

唯一约束: `(project_id, source_entity_id, target_entity_id, relation_type)`

双方实体均可 create_if_missing。冲突时更新: attitude, intensity, known_by 标志, status, metadata (合并)。

### list_relationships()

支持: entity_id (源或目标), entity_type+name 组合过滤, relation_type, status, include_reader_hidden。

## 四、语义搜索

### search()

两种模式:
1. **语义搜索**: 通过 `embedding_service` 做向量查询 → Qdrant → PostgreSQL 回取 chunk
2. **关键词回退**: `search_vector @@ plainto_tsquery('simple', query)`

### semantic_search()

完整流程: embed query → Qdrant search (limit*2 过取) → 提取 point_ids → PostgreSQL 查询 memory_chunks (按 qdrant_point_id) → 合并 score → 按 score 降序 → 截取 limit。

### vectorize_chunk()

为单个 chunk 生成 embedding 并存储到 Qdrant，更新 PostgreSQL 的 qdrant_collection/point_id。

### vectorize_pending_chunks()

批量处理 qdrant_point_id IS NULL 的 chunks (每次 batch_size=10)。

### pending_vector_chunks() / mark_vector_indexed()

查询/标记待向量化的 chunks。

## 五、章节总结

### recent_summaries()

获取当前章节之前的 N 个章节摘要，按 chapter_no DESC 排序后 reverse 为正序。

## 六、状态重建 rebuild_projection()

从 chapter_commits 增量重建状态投影:

1. 可选: 清空所有 is_current
2. 分批查询 accepted 的 commits (batch_size=100)
3. 解析 payload 中的 character_state_changes 和 world_state_changes
4. 为每个 change: upsert entity → 清空旧 snapshot → INSERT 新 snapshot
5. 循环直到所有 commit 处理完毕

## 七、涉及的数据库表

| 表 | 操作 |
|---|------|
| `state_entities` | SELECT / INSERT / UPDATE (ON CONFLICT) |
| `state_snapshots` | SELECT / INSERT / UPDATE (is_current) |
| `entity_relationships` | SELECT / INSERT / UPDATE (ON CONFLICT) |
| `memory_chunks` | SELECT / UPDATE (qdrant 标记) |
| `chapters` | SELECT |
| `chapter_summaries` | SELECT (JOIN chapters) |
| `chapter_commits` | SELECT (rebuild) |