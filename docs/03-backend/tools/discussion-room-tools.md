# Discussion Room Tools — 多模型讨论室

> Source: `tools/discussion_room.py`
> Dependencies: `db`, `auth`, `llm_client`, `gatekeeper_service`
> Background Engine: `_run_discussion()` / `_continue_discussion()` — runs as asyncio background task

---

## 5-Phase Background Engine

讨论室采用 **5 阶段自动化后台讨论引擎**：

| Phase | 名称 | 描述 |
|-------|------|------|
| `topic_analysis` | 话题分析 | 控制模型分析用户意图 |
| `data_plan` | 数据需求 | 控制模型输出 `NEED:` 查询指令 |
| `analyze` | 数据分析 | 控制模型基于查询结果输出分析 |
| `propose` | 提案轮 | 讨论模型各自提案 |
| `consensus` | 共识总结 | 控制模型汇总达成共识 |

系统自动处理 `NEED:` 行的数据查询（支持 entities / pk / items / uk / schema / docs 六种数据源），回传给模型。如有异议进入多轮辩论（max 8 rounds）。完成时自动同步关联 `review_jobs` 状态。

---

## discussion_room.create_session

```python
@mcp.tool(name="discussion_room.create_session")
async def discussion_room_create_session(
    workspace: str, project: str, topic: str,
    model_keys: list[str] | None = None,
    rate_limit_delay: float = 3.0,
    rate_limit_retries: int = 3,
    data_source: str = "knowledge-entries",
    data_category: str | None = None,
    output_type: str = "knowledge",
) -> dict[str, Any]
```

**Purpose:** 创建讨论会话并启动后台自动讨论。

**Parameters:**
- `model_keys` — 指定参与模型列表（>=2 个），不传则从用户贡献的模型池自动选取（按近期使用次数升序，最少用过的优先）
- `data_source` — 数据来源类型：`knowledge-entries` / `canon` / `entities` / `rules` / `genres` / `relations` / `materials` / `tones`
- `data_category` — 数据分类筛选（配合 knowledge-entries）
- `output_type` — 输出模式：
  - `"knowledge"` — 输出 JSON 知识条目（知识库维护）
  - `"review"` — 输出自然语言审查结论（"完备"或"缺XX"）

**Scope:** `write`

**Returns:** `{session_id, topic, phase, control_model, discussion_models, message}`

**DB Tables:** `discussion_sessions` | **Background Engine:** `_run_discussion()`

---

## discussion_room.get_updates

```python
async def discussion_room_get_updates(session_id: str) -> dict[str, Any]
```

**Purpose:** 轻量轮询会话状态（不含全量 responses）。返回 `status`, `phase`, `round`, `consensus_reached`, `summary`(前200字), `model_status`(各模型响应计数和最后响应时间), `stalled`(>3分钟无响应标记为卡住)。

---

## discussion_room.get_session

```python
async def discussion_room_get_session(session_id: str) -> dict[str, Any]
```

**Purpose:** 获取完整会话记录（含所有 responses）。

---

## discussion_room.list_sessions

```python
async def discussion_room_list_sessions(
    workspace: str, project: str, status: str | None = None, limit: int = 20,
) -> dict[str, Any]
```

**Purpose:** 列出历史会话。`status` 可选: `running` / `completed` / `applied` / `rate_limited`。

---

## discussion_room.resume_session

```python
async def discussion_room_resume_session(
    workspace: str, project: str, session_id: str,
    new_topic: str = "", rate_limit_delay: float = 3.0,
    rate_limit_retries: int = 3,
) -> dict[str, Any]
```

**Purpose:** 从断点继续讨论。重置 state 为 running，可选追加新话题。

**Background Engine:** `_continue_discussion()`

---

## discussion_room.apply_results

```python
async def discussion_room_apply_results(
    workspace: str, project: str, session_id: str,
) -> dict[str, Any]
```

**Purpose:** 将讨论结果应用到知识库。解析 summary 中的 JSON 代码块，自动写入：
- `universal_knowledge`（通用知识条目）
- `setting_items`（设定条目）
- `canon_rules`（创作规则）
- `knowledge_entities`（知识实体）
- `state_snapshots`（状态快照）
- `global_rules`（全局规则）

同时对 `universal_knowledge` 写入使用 LLM 自动分类（匹配最佳 `ref_categories`）。所有变更写入 `system_evolution_proposals` 作为待审批提案，并创建 `audit_logs` 记录。

**Scope:** `write`

---

## discussion_room.delete_session

```python
async def discussion_room_delete_session(
    workspace: str, project: str, session_id: str,
) -> dict[str, bool | str]
```

**Purpose:** 物理删除会话。

---

## Model Pool 机制

讨论模型自动选取规则（`_pick_contributed_models()`）：
1. 查询所有 `task_types` 包含 review/analysis/draft/outline/polish/context 或 `is_contributed=true` 的 active 模型
2. 按近 7 天 discussion_room 使用次数升序排列（最少用的优先）
3. 去重同核心模型名（如 `openai/gpt-4` 和 `azure/gpt-4` 视为同核心）
4. 最多选 4 个