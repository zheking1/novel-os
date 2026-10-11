# Character Arc 服务 — 角色弧光追踪服务

**源码**: `novel-os-mcp/src/novel_os_mcp/character_arc.py` (330 行)

## 概述

Character Arc 服务追踪长篇（2000 万+ 字）小说中的角色演变，覆盖情绪变化、关系进化、能力成长、性格转变等维度。支持按章节记录的弧光点，可用于上下文注入。

## 数据库表

| 表名 | 说明 |
|------|------|
| `character_arcs` | 角色弧光记录 |
| `state_entities` | 角色实体（外键关联） |

## 弧光类型 (Arc Types)

| 类型 | 常量值 | 说明 | 对应便捷方法 |
|------|------|------|------|
| 情绪 | `emotion` | 情绪状态变化 | `record_emotion()` |
| 关系 | `relationship` | 人际关系演变 | `record_relationship_change()` |
| 能力 | `power` | 技能/力量等级变化 | `record_power_change()` |
| 性格 | `personality` | 性格特质转变 | `record_personality_shift()` |
| 目标 | `goal` | 目标驱动变化 | 通用 `record_arc_point()` |
| 自定义 | `custom` | 自定义弧光类型 | 通用 `record_arc_point()` |

---

## 弧光记录 (Arc Recording)

### record_arc_point

核心记录方法，所有弧光类型统一入口。

**参数**:

| 参数 | 类型 | 说明 |
|------|------|------|
| `project_id` | str | 项目 UUID |
| `character_name` | str | 角色名（通过 `_resolve_character` 解析为 `state_entities` 实体） |
| `chapter_no` | int | 发生章节号 |
| `arc_type` | str | 弧光类型 |
| `state` | dict | 以 JSONB 存储的状态快照 |
| `change_summary` | str\|None | 变化摘要 |
| `trigger_event` | str\|None | 触发事件描述 |
| `metadata` | dict\|None | 扩展元数据 |

**角色解析 (_resolve_character)**：先在 `state_entities` 中查找 `project_id + entity_type='character' + name`。若不存在，自动创建实体（`ON CONFLICT` 处理并发安全）。

**返回值**：`{ok, character, id, chapter_no, arc_type, state, change_summary, trigger_event, metadata, created_at}`

### 便捷方法

| 方法 | 状态字段 | 说明 |
|------|------|------|
| `record_emotion()` | `{emotion, intensity}` | 记录情绪状态，`intensity` 为 0-1 浮点数 |
| `record_relationship_change()` | `{target, old_relation, new_relation}` | 记录关系变化 |
| `record_power_change()` | `{old_level, new_level, method}` | 记录能力等级变化 |
| `record_personality_shift()` | `{trait, old_value, new_value}` | 记录性格特质变化 |

---

## 弧光查询 (Arc Querying)

### get_character_arc

获取角色弧光历史记录，支持按 `arc_type`、`from_chapter`/`to_chapter` 过滤。

排序：`ORDER BY chapter_no`（按章节递增）。

### get_latest_arc_state

获取角色各弧光类型的最新状态。使用 `DISTINCT ON (arc_type) ORDER BY arc_type, chapter_no DESC` 获取每种弧光类型的最新记录。

**返回值示例**：
```json
{
  "character": "张三",
  "arc_state": {
    "emotion": {"state": {"emotion": "愤怒", "intensity": 0.8}, "chapter_no": 45, "change_summary": "..."},
    "power": {"state": {"old_level": "练气期", "new_level": "筑基期"}, "chapter_no": 32, "change_summary": "..."}
  }
}
```

### 专用查询

| 方法 | 说明 |
|------|------|
| `get_emotion_timeline()` | 情绪时间线（自动过滤 `arc_type='emotion'`） |
| `get_power_progression()` | 能力进阶时间线（自动过滤 `arc_type='power'`） |
| `get_relationship_evolution(target_name)` | 关系演变时间线，支持按目标角色过滤 |

---

## 上下文摘要 (Context-Friendly Summary)

### get_arc_summary_for_context

为 LLM 上下文注入生成压缩摘要，适用于多轮生成中的角色一致性。

**参数**：
- `current_chapter`：当前章节号
- `max_tokens`：最大 token 预算（默认 200，按 4 chars/token 估算）

**逻辑**：
1. 获取 `chapter_no <= current_chapter` 的最近 20 条记录
2. 反转顺序（时间正序）
3. 格式化为 `Ch.{chapter_no}: [{arc_type}] {change_summary}`
4. 按 `max_tokens * 4` 字符截断

**输出示例**：
```
== 张三 Arc ==
  Ch.12: [power] 练气期 → 筑基期
  Ch.15: [emotion] 愤怒 (intensity: 0.8)
  Ch.18: [relationship] 盟友 → 恋人 with 李四
```

---

## 工作流引导

1. 角色初登场 → `record_arc_point(arc_type="custom", state={...})`
2. 每章创作后 → `record_emotion()` 记录本章情绪
3. 关键节点 → `record_power_change()` / `record_relationship_change()`
4. 新章生成前 → `get_arc_summary_for_context()` 注入上下文
5. 阶段性检查 → `get_latest_arc_state()` 查看角色当前全貌