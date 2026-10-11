# Causality 服务 — 因果链追踪服务

**源码**: `novel-os-mcp/src/novel_os_mcp/causality.py` (296 行)

## 概述

Causality 服务追踪长篇（2000 万+ 字）小说中的因果关系链：

```
事件A → causes → 事件B → triggers → 伏笔C → payoff → 事件D
```

使用 **PostgreSQL 递归 CTE**（Common Table Expression）进行链式前向/后向遍历，无需 Python 递归。支持未解析因果和悬空效应的检测。

## 数据库表

| 表名 | 说明 |
|------|------|
| `causality_chains` | 因果链记录 |

## 因果类型 (Causal Types)

| 类型 | 常量值 | 说明 |
|------|------|------|
| 直接因果 | `direct` | A 直接导致 B |
| 间接因果 | `indirect` | A 间接导致 B |
| 触发 | `triggered` | A 触发了 B 的发生 |
| 赋能 | `enabled` | A 使得 B 成为可能 |
| 阻止/预防 | `prevented` | A 阻止了 B |

### 强度 (strength)

浮点数 0.0-1.0，表示因果关系的置信度/强度。默认 1.0。

---

## 因果记录 (Chain Recording)

### record_cause

记录单条因果关系：

| 参数 | 类型 | 说明 |
|------|------|------|
| `cause_event_id` | str\|None | 原因事件 ID |
| `cause_chapter_no` | int\|None | 原因事件章节号 |
| `cause_title` | str\|None | 原因事件标题 |
| `effect_event_id` | str\|None | 结果事件 ID |
| `effect_chapter_no` | int\|None | 结果事件章节号 |
| `effect_title` | str\|None | 结果事件标题 |
| `causal_type` | str | 因果类型 |
| `strength` | float | 强度 0-1 |
| `description` | str\|None | 描述 |

> `cause_event_id` 与 `effect_event_id` 不必同时非空；允许仅有章节号的宽松关联。

### record_chain

批量记录一条因果链。接收事件列表：

```python
chain = [
    {"chapter_no": 10, "title": "张三发现密道", "event_id": "uuid-1"},
    {"chapter_no": 12, "title": "张三进入密室", "causal_type": "direct"},
    {"chapter_no": 15, "title": "张三获得神器", "causal_type": "triggered", "strength": 0.8},
]
```

链长度需 >= 2，内部循环调用 `record_cause` 连接相邻事件。

---

## 链查询 — PostgreSQL 递归 CTE

### get_chain_from_event

**前向遍历**：从指定事件出发，沿 "原因→结果" 方向追踪因果链。

```sql
WITH RECURSIVE chain AS (
    -- 基础查询：以 cause_event_id = 目标事件 为起点
    SELECT ..., 1 AS depth FROM causality_chains WHERE cause_event_id = $2
    UNION ALL
    -- 递归：当前链的 effect_event_id 作为下一链的 cause_event_id
    SELECT ..., ch.depth + 1
    FROM causality_chains cc JOIN chain ch ON cc.cause_event_id = ch.effect_event_id
    WHERE ch.depth < $3   -- 深度限制
)
SELECT DISTINCT ON (id) * FROM chain ORDER BY id, depth
```

### get_chain_to_event

**后向追溯**：从指定事件出发，沿 "结果←原因" 方向反向追踪。

对称逻辑：起点用 `effect_event_id = 目标事件`，递归条件为 `cc.effect_event_id = ch.cause_event_id`。

### get_chains_in_chapter_range

按章节范围查询因果链，支持按 `causal_type` 过滤。

---

## 未解析/悬空检测

### find_unresolved_causes

**未解析原因**：一个原因事件没有记录任何后续影响（无子节点）。

```sql
-- 逻辑：某个 cause_event_id 下，没有以该事件为"原因"的进一步因果链
SELECT ... FROM causality_chains cc
WHERE NOT EXISTS (
    SELECT 1 FROM causality_chains cc2
    WHERE cc2.cause_event_id = cc.effect_event_id  -- 该效果没有作为下一步原因
)
```

此类事件可能存在未回收的伏笔或未展开的情节。

### find_dangling_effects

**悬空效应**：一个结果事件没有已知原因（无父节点）。

```sql
-- 逻辑：某个 effect_event_id 下，没有以该事件为"结果"的上一步因果链
WHERE NOT EXISTS (
    SELECT 1 FROM causality_chains cc2
    WHERE cc2.effect_event_id = cc.cause_event_id  -- 该原因没有上一步作为结果
)
```

此类事件可能缺少前情铺垫，造成剧情突兀。

---

## 上下文摘要 (Context-Friendly Summary)

### get_causality_summary_for_context

为 LLM 上下文注入生成近期因果摘要。

**参数**：
- `chapter_no`：目标章节
- `max_tokens`：最大 token 预算（默认 300）

**逻辑**：获取 `[chapter_no-20, chapter_no]` 范围内的最近 30 条因果链，格式化为：

```
== Recent Causality Chains ==
  张三发现密道 →[direct]→ 张三进入密室
  张三进入密室 →[triggered]→ 神器觉醒
```

---

## 工作流引导

1. 每章创作后 → `record_cause()` 记录关键因果
2. 多事件链 → `record_chain()` 批量导入
3. 伏笔回收检查 → `find_unresolved_causes()` 排查未展开的情节
4. 剧情合理性检查 → `find_dangling_effects()` 排查无铺垫事件
5. 新章生成前 → `get_causality_summary_for_context()` 注入上下文