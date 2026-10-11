# Context & Workflow Tools — 章节上下文与生成流水线

> Source: `novel-os-mcp/src/novel_os_mcp/tools/context.py`
> Dependencies: `db`, `auth`, `context_service`, `workflow_service`, `context_weight_service`, `review_service`

---

## workflow.prepare_chapter_context

```python
@mcp.tool(name="workflow.prepare_chapter_context")
async def workflow_prepare_chapter_context(
    workspace: str, project: str, chapter_no: int,
    purpose: str = "draft", focus: list[str] | None = None,
    budget: dict | None = None, volume_no: int | None = None,
    scope_refs: list[str] | None = None, scope_types: list[str] | None = None,
    active_event_keys: list[str] | None = None,
    pov_mode: str = "omniscient", pass_number: int | None = None,
    previous_context: dict | None = None,
) -> dict[str, Any]
```

**Purpose:** Build chapter context pack and return `workflow_guide` with 14 structured steps.

**Pass numbers:** 1=outline, 2=draft, 3=polish, 4=verify.

**Workflow Guide Steps:**

| Step | Name | Tool | Next |
|------|------|------|------|
| 1 | 预检 | `workflow.preflight_generation` | next_step |
| 2 | 获取上下文包 | `_agent_evaluate` | next_step |
| 3 | 生成初稿并记录 | `_agent_evaluate` | next_step |
| 4 | 内容校验 | `workflow.validate_content` | next_step |
| 5 | 启动审核 | `review.start_job` | next_step |
| 6 | 等待审核完成 | `discussion_room.get_updates` | wait_for_async (5s/240 retries) |
| 7 | 获取审核结论 | `discussion_room.get_session` | next_step |
| 8 | 审核结论判定 | `_agent_evaluate` | goto_step:7 on fail |
| 9 | 润色终稿 | `pipeline.generate(task_type="polish")` | next_step |
| 10 | 保存终稿到本地 | `_agent_evaluate` | next_step |
| 11 | 提交章节 | `workflow.submit_chapter_commit` | next_step |
| 12 | 记录情绪节奏 | `pacing.record_emotion` | next_step |
| 13 | 记录角色弧光 | `arc.record_*` | next_step |
| 14 | 维护情节线/伏笔 | `plot.thread.advance` / `foreshadowing.*` | wait_user_confirm |

**DB Tables:** 18+ tables across context, rules, entities, summaries, foreshadowing, chapters, etc.
**Service:** `context_service.prepare_chapter_context()`

---

## workflow.validate_context_pack

```python
async def workflow_validate_context_pack(
    workspace: str, project: str,
    context_pack_id: str | None = None, chapter_no: int | None = None,
) -> dict[str, Any]
```

**Purpose:** Validate context pack data quality and consistency.

---

## context.list_packs / context.get_pack

```python
# List
async def context_list_packs(
    workspace: str, project: str,
    chapter_no: int | None = None, purpose: str | None = None, limit: int = 50,
) -> list[dict[str, Any]]

# Get
async def context_get_pack(
    workspace: str, project: str,
    context_pack_id: str | None = None, chapter_no: int | None = None,
) -> dict[str, Any]
```

**Purpose:** List/get context pack records by chapter or ID.

**DB Tables:** `context_packs` | **Service:** `context_service`

---

## workflow.preflight_generation

```python
async def workflow_preflight_generation(
    workspace: str, project: str, chapter_no: int,
    purpose: str = "draft", focus: list[str] | None = None,
    budget: dict | None = None, volume_no: int | None = None,
    scope_refs: list[str] | None = None, scope_types: list[str] | None = None,
    active_event_keys: list[str] | None = None, pov_mode: str = "omniscient",
) -> dict[str, Any]
```

**Purpose:** Preflight check — verify generation conditions, budget, and context completeness. Returns preflight report with `total_sections`, `blocking_issues`, etc.

---

## workflow.prepare_segment_context

```python
async def workflow_prepare_segment_context(
    workspace: str, project: str, chapter_no: int, segment: str,
    purpose: str = "draft", focus: list[str] | None = None,
    budget: dict | None = None, volume_no: int | None = None,
    ...
) -> dict[str, Any]
```

**Purpose:** Build context for a specific chapter segment. Supports fine-grained control.

---

## workflow.submit_chapter_commit

```python
async def workflow_submit_chapter_commit(
    workspace: str, project: str, chapter_no: int,
    title: str | None, local_files: list[dict], commit: dict,
) -> dict[str, Any]
```

**Purpose:** Submit chapter completion confirmation. **Review must be done first** (via `review.start_job`).

**Scope:** `write`

---

## workflow.list_audit_logs

```python
async def workflow_list_audit_logs(
    workspace: str, project: str,
    action: str | None = None, resource_type: str | None = None, limit: int = 50,
) -> list[dict[str, Any]]
```

**Purpose:** List operation audit logs. Filter by action and resource type.

**DB Tables:** `audit_logs`

---

## workflow.validate_content

```python
async def workflow_validate_content(
    workspace: str, project: str, chapter_no: int, content: str,
) -> dict[str, Any]
```

**Purpose:** Validate generated content — check forbidden words, character survival, setting consistency, and KB consistency.

**Scope:** `write` | **Content limit:** 50000 chars

---

## workflow.learn_from_review

```python
async def workflow_learn_from_review(
    workspace: str, project: str, review_job_id: str,
    create_revision_tasks: bool = True, create_rule_proposals: bool = True,
    block_on_critical: bool = True,
) -> dict[str, Any]
```

**Purpose:** Learn from review results — auto-create revision tasks and rule proposals to improve future generation quality.

---

## workflow.get_chapter_generation_prompt

```python
async def workflow_get_chapter_generation_prompt(
    workspace: str, project: str, chapter_no: int,
    focus: list[str] | None = None, volume_no: int | None = None,
    pov_mode: str = "third_person_limited", pass_number: int = 2,
) -> dict[str, Any]
```

**Purpose:** Generate standard chapter creation prompt for subagent, including full flow guide and tool call templates.

**Returns:** `{ok, chapter_no, prompt, context_pack_id, file_hint, review_config, steps, workflow_guide}`

---

## Interactive Chapter Session (11-step system)

| Tool | Purpose |
|------|---------|
| `workflow.start_chapter_generation(workspace, project, chapter_no, ...)` | Start session (max 3 active) → returns `session_id` |
| `workflow.next_step(session_id, result?)` | Advance to next step; validates current step via DB |
| `workflow.jump_to_step(session_id, step_no)` | Jump to specific step |
| `workflow.get_current_step(session_id)` | Get current step info and instruction |
| `workflow.pause_session(session_id)` | Pause session |
| `workflow.resume_session(session_id)` | Resume paused session |
| `workflow.list_sessions(workspace, project)` | List active sessions |
| `workflow.abort_chapter_generation(session_id)` | Abort session |

**Session steps (CHAPTER_STEPS):**
1. 预检 (preflight_generation)
2. 获取上下文 (prepare_chapter_context)
3. 创作正文 (2500-4000 words)
4. 记录元数据 (pipeline.run_full with summary)
5. 校验内容 (validate_content)
6. 保存本地文件
7. 审核修订循环 (review.start_job → aggregate → revise → re-review, max 3 rounds)
8. 提交完成 (submit_chapter_commit)
9. 维护 (arc.*, kb.world.*, plot.*, foreshadowing.*)
10. 从审核学习 (learn_from_review, optional)
11. 压缩上下文 (context_compression.auto_compress, optional)

---

## chapter.reset

```python
async def chapter_reset(
    workspace: str, project: str, chapter_no: int, keep_entities: bool = True,
) -> dict[str, Any]
```

**Purpose:** Reset chapter — delete ALL auxiliary data. `keep_entities=True` keeps character/faction/location entities.

**Deleted tables:** generation_passes, chapter_plans, chapter_emotions, chapter_style_metrics, chapter_summaries, review_jobs + review_reports, chapter_commits, character_arcs, causality_chains, world_snapshots, context_packs, compressed_contexts, state_snapshots (if !keep_entities), chapters, workflow_sessions. Total: 15+ tables.

---

## project.reset

```python
async def project_reset(
    workspace: str, project: str, keep_entities: bool = True,
    delete_local_files: bool = True,
) -> dict[str, Any]
```

**Purpose:** Reset entire project — clear all chapter data, reviews, arcs, world state, delete local files. Preserves project config, model config, user settings.

**Logic:** Iterates all chapters calling `chapter_reset()`, then deletes project-level data: foreshadowing, plot_threads, causality_chains, character_arcs, etc. If `!keep_entities`, also deletes state_entities, entity_relationships. Resets volumes to "planned" status.
