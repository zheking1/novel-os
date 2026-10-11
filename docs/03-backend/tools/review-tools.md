# Review Tools — 章节审核与修订管理

> Source: `tools/review.py`
> Dependencies: `db`, `auth`, `review_service`, `discussion_room`

---

## review.start_job

```python
@mcp.tool(name="review.start_job")
async def review_start_job(
    workspace: str, project: str, chapter_no: int,
    dimensions: list[str],
    local_files: list[dict[str, Any]] | None = None,
    chapter_content: str | None = None,
) -> dict[str, Any]
```

**Purpose:** 启动审核任务（讨论室模式）。**必须传入 `chapter_content`（章节全文）**——系统不存全文，需 agent 从 `pipeline.generate` 结果中提取传入。自动添加 `ai_detection` 维度。从用户审核委员会中选取 >=2 个模型启动多模型讨论。

**Returns:** `{session_id, review_job_id, control_model, discussion_models, dimensions, workflow_guide}`

**Scope:** `write`

**DB Tables:** `review_jobs`, `discussion_sessions` | **Service:** `ReviewService`

---

## review.list_jobs

```python
async def review_list_jobs(
    workspace: str, project: str,
    status: str | None = None, limit: int = 100,
) -> list[dict[str, Any]]
```

**Purpose:** 列出审核任务。可按状态过滤。

**Scope:** `read`

---

## review.aggregate

```python
async def review_aggregate(
    workspace: str, project: str, review_job_id: str,
    create_revision_tasks: bool = True,
) -> dict[str, Any]
```

**Purpose:** 汇总审核结果。整合讨论室中的多模型意见，生成综合报告，可选创建修订任务。

**Scope:** `write`

---

## review.list_revision_tasks

```python
async def review_list_revision_tasks(
    workspace: str, project: str,
    status: str | None = None, severity: list[str] | None = None,
    limit: int = 100, offset: int = 0,
    task_id: str | None = None,
) -> list[dict[str, Any]]
```

**Purpose:** 列出修订任务。支持按状态/严重度/ID 过滤。

---

## review.update_revision_task

```python
async def review_update_revision_task(
    workspace: str, project: str, task_id: str,
    status: str | None = None, resolution: str | None = None,
) -> dict[str, Any]
```

---

## review.upsert_council_config

```python
async def review_upsert_council_config(
    name: str = "默认审核委员会",
    config: dict[str, Any] = {},
    is_active: bool = False,
) -> dict[str, Any]
```

**Purpose:** 创建/更新用户审核委员会配置。`config` 格式：`{"models": [{"key": "...", "dimensions": [...]}, ...]}`。

**Scope:** `write`

---

## review.list_council_configs

```python
async def review_list_council_configs() -> list[dict[str, Any]]
```

**Purpose:** 列出当前用户的审核委员会配置。

---

## review.council.dispatch

```python
async def review_council_dispatch(review_job_id: str) -> dict[str, Any]
```

**Purpose:** 获取活跃委员会配置中的待审核模型列表，用于并行分发。

---

## review.submit_model_report

```python
async def review_submit_model_report(
    workspace: str, project: str, review_job_id: str, model_id: str,
    content: str | None = None, score: float | None = None,
    summary: str | None = None, findings: list[dict] | None = None,
    local_report_file: dict | None = None,
) -> dict[str, Any]
```

**Purpose:** 提交章节正文给模型审核，或直接提交审核报告。传入 `content` 时系统自动拉取上下文并调用 LLM 审核；不传则直接存储。

**Scope:** `write`

---

## review.extract_rule_proposals

```python
async def review_extract_rule_proposals(
    workspace: str, project: str, review_job_id: str,
    create_proposals: bool = True, min_confidence: float = 0.7,
) -> dict[str, Any]
```

**Purpose:** 从审核结果中提取规则提案。分析审核报告中的模式问题，生成创作规则建议。

---

## review.extract_state_updates

```python
async def review_extract_state_updates(
    workspace: str, project: str, review_job_id: str,
) -> dict[str, Any]
```

**Purpose:** 从审核结果中提取实体状态更新。

---

## review.extract_foreshadowing_updates

```python
async def review_extract_foreshadowing_updates(
    workspace: str, project: str, review_job_id: str,
) -> dict[str, Any]
```

**Purpose:** 从审核结果中提取伏笔状态更新。

---

## review.evaluate_model_quality

```python
async def review_evaluate_model_quality(
    workspace: str, project: str, review_job_id: str | None = None,
) -> dict[str, Any]
```

**Purpose:** 评估各模型的审核质量（对比聚合结果，计算偏差）。

---

## review.submit_evolution_proposals

```python
async def review_submit_evolution_proposals(
    workspace: str, project: str, review_job_id: str,
    auto_submit: bool = True,
) -> dict[str, Any]
```

**Purpose:** 从审核结果中提交进化提案到 `system_evolution_proposals`。

**DB Tables:** `review_jobs`, `review_reports`, `review_council_configs`, `revision_tasks` | **Service:** `ReviewService`