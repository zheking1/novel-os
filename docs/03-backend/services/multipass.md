# Multi-Pass 服务 — 多轮生成管线服务

**源码**: `novel-os-mcp/src/novel_os_mcp/multipass.py` (315 行)

## 概述

Multi-Pass 服务管理长篇（2000 万+ 字）小说的 4 轮生成管线:

```
Pass 1: Planning    — 章节大纲、情绪曲线、节奏规划
Pass 2: Drafting    — 初稿生成
Pass 3: Polishing   — 风格一致性、对话润色
Pass 4: Verification — 连贯性检查、合规扫描
```

## 数据库表

| 表名 | 说明 |
|------|------|
| `chapter_plans` | 章节计划 (Pass 1 输出) |
| `generation_passes` | 各轮生成记录 (Pass 1-4) |

---

## 四轮管线详解

### Pass 1: Planning (规划阶段)

#### create_chapter_plan

创建章节大纲计划。每次新建计划会将旧计划标记为 `superseded`（保持历史记录）。

| 参数 | 类型 | 说明 |
|------|------|------|
| `chapter_no` | int | 章节号 |
| `volume_no` | int\|None | 卷号 |
| `plan` | dict | JSONB 大纲内容 |

Plan 结构建议:
```json
{
  "summary": "章节概要",
  "key_scenes": ["场景1", "场景2"],
  "emotion_target": "紧张",
  "pacing_type": "climax_buildup",
  "foreshadowing": ["伏笔key1"],
  "threads_to_advance": ["线程key1"]
}
```

#### get_chapter_plan

获取当前活跃（非 `superseded`）的章节计划。

---

### Pass 2-4: 生成记录 (Generation Passes)

#### create_generation_pass

记录一次生成轮次的结果。

| 参数 | 类型 | 说明 |
|------|------|------|
| `pass_number` | int | 轮次编号 (2=起草, 3=润色, 4=验证) |
| `pass_type` | str | 轮次类型 |
| `content` | str\|None | 生成内容 (Pass 4 中存 JSON 格式的 continuity 结果) |
| `metadata` | dict\|None | JSONB 元数据 |

**Pass 对应关系**:

| pass_number | pass_type | 说明 |
|------|------|------|
| 1 | `planning` | 计划 (通过 `create_chapter_plan` 存储) |
| 2 | `drafting` | 初稿 |
| 3 | `polishing` | 润色 |
| 4 | `verification` | 验证 (存储 continuity 检查结果) |

#### update_generation_pass

更新已记录的 pass (内容、元数据、状态)。动态构建 SET 子句，仅更新提供的字段。

---

### Pass 4: 连贯性检查 (Continuity Verification)

#### check_continuity

检查生成的正文是否与近期章节连贯一致。

**检查步骤**:

1. **近期上下文**: 获取 `chapter_no` 之前最近的 5 个章节摘要 (`chapter_summaries`, `summary_type='chapter'`)
2. **实体提取**: 使用简单正则 (`[【[]([^】\]]+)[】\]]` 和 `[""「]([^""」]+)[""」]`) 从正文中提取方括号和引号内的实体名（最多 20 个）
3. **实体状态**: 查询提取到的实体在 `state_snapshots` 中的当前状态 (`is_current=true`)

**返回值**:
```json
{
  "chapter_no": 50,
  "recent_summaries_count": 5,
  "entities_detected": ["张三", "李四", "神器"],
  "entity_states_found": 3,
  "entity_states": [{"name": "张三", "entity_type": "character", "state": {...}}],
  "recent_context": [{"chapter_no": 49, "title": "..."}, ...]
}
```

---

## 完整管线编排 (Full Pipeline)

### run_pipeline

一次调用执行完整的 4-pass 管线。

**参数**:

| 参数 | 类型 | 说明 |
|------|------|------|
| `plan` | dict | 大纲计划 (Pass 1) |
| `draft_content` | str | 初稿正文 (Pass 2) |
| `polished_content` | str\|None | 润色后正文 (Pass 3, 可选) |

**执行流程**:
1. **防御性处理**: 若 `plan` 为字符串，包装为 `{"summary": plan}`
2. Pass 1: 记录 `planning` (content=plan JSON, metadata=`{plan_keys: [...]}`)
3. Pass 2: 记录 `drafting` (metadata=`{word_count: len(draft)}`)
4. Pass 3: 记录 `polishing` (content=`polished_content or draft_content`, metadata=`{refined: bool}`)
5. Pass 4: 运行 `check_continuity()` → 记录 `verification` (content=continuity JSON, metadata=continuity)

**返回值**:
```json
{
  "ok": true,
  "chapter_no": 50,
  "passes": {
    "pass_1_plan": {...},
    "pass_2_draft": {...},
    "pass_3_polish": {...},
    "pass_4_verify": {...}
  },
  "continuity": {...}
}
```

---

### get_pipeline_status

查询当前章节的管线状态:

- `has_plan`: 是否有计划
- `passes_completed`: 已完成轮次数
- `pass_details`: 各轮次的 type/status/created_at
- `pipeline_complete`: 是否完成全部 4 轮

---

## 工作流引导

1. 开始新章 → `create_chapter_plan()` + `create_generation_pass(pass_number=1)`
2. AI 生成初稿 → `create_generation_pass(pass_number=2)`
3. AI 润色 → `create_generation_pass(pass_number=3)`
4. 连贯性检查 → `check_continuity()` + `create_generation_pass(pass_number=4)`
5. 一键管线 → `run_pipeline()` 自动完成全部 4 轮
6. 状态查询 → `get_pipeline_status()`