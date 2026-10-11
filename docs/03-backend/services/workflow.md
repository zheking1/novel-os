# WorkflowService - 交互式章节生成工作流

## 概述

`WorkflowService` 管理 Novel OS 中的写作工作流和任务系统。它提供工作流定义、步骤管理、任务跟踪、章节内容校验和提交完整性确认等功能。

**源码路径**: `novel-os-mcp/src/novel_os_mcp/services/workflow.py` (559行)

## 注入依赖

```python
WorkflowService(db: Database)
```

## 核心概念

### 数据模型层次

```
workflows (工作流定义)
  └── workflow_steps (步骤: name, step_type, step_order, config, dependencies)
       └── tasks (任务: title, task_type, priority, assigned_to, chapter_id)
            └── chapter_commits (章节提交)
                 └── audit_logs (审计日志)
```

## 一、工作流管理

### `create_workflow()`

```python
async def create_workflow(
    project_id: str,
    name: str,
    description: str | None = None,
    workflow_type: str = "sequential",
) -> dict[str, Any]
```

写入 `workflows` 表，初始状态 `active`。

### `get_workflows()`

```python
async def get_workflows(
    project_id: str,
    status: str | None = None,
) -> list[dict[str, Any]]
```

支持按 status 过滤 (active/completed/archived)。

### `update_workflow()`

```python
async def update_workflow(
    workflow_id: str,
    name: str | None = None,
    description: str | None = None,
    status: str | None = None,
) -> dict[str, Any]
```

动态构建 UPDATE SET 子句，仅更新非 None 字段。

## 二、工作流步骤管理

### `add_workflow_step()`

```python
async def add_workflow_step(
    workflow_id: str,
    name: str,
    step_type: str = "review",
    step_order: int = 0,
    config: dict[str, Any] | None = None,
    dependencies: list[str] | None = None,
) -> dict[str, Any]
```

支持的 `step_type` 值: `preflight`, `context`, `draft`, `validate`, `review`, `polish`, `save`, `commit`, `emotion`, `arc`, `plot_threads`

写入 `workflow_steps` 表，初始状态 `pending`。config 和 dependencies 以 JSONB 存储。

### `get_workflow_steps()`

```python
async def get_workflow_steps(workflow_id: str) -> list[dict[str, Any]]
```

按 `step_order` 排序返回所有步骤，含 `status`, `result`, `created_at`, `completed_at`。

### `update_step_status()`

```python
async def update_step_status(
    step_id: str,
    status: str,
    result: dict[str, Any] | None = None,
) -> dict[str, Any]
```

支持的状态: `pending`, `in_progress`, `completed`, `failed`, `skipped`

- status = `completed` → 同时写入 `result` (JSON) 和 `completed_at = NOW()`
- 其他状态 → 仅更新 status

## 三、任务管理 (Tasks)

### `create_task()`

```python
async def create_task(
    project_id: str,
    title: str,
    description: str | None = None,
    task_type: str = "writing",
    priority: str = "normal",
    assigned_to: str | None = None,
    chapter_id: str | None = None,
    due_date: str | None = None,
) -> dict[str, Any]
```

写入 `tasks` 表，初始状态 `todo`。

### `get_tasks()`

```python
async def get_tasks(
    project_id: str,
    status: str | None = None,
    assigned_to: str | None = None,
    task_type: str | None = None,
    limit: int = 50,
) -> list[dict[str, Any]]
```

排序规则 (SQL):

```sql
ORDER BY
  CASE priority
    WHEN 'urgent' THEN 0
    WHEN 'high' THEN 1
    WHEN 'normal' THEN 2
    ELSE 3
  END,
  created_at DESC
```

### `update_task()`

```python
async def update_task(
    task_id: str,
    status: str | None = None,
    assigned_to: str | None = None,
    priority: str | None = None,
) -> dict[str, Any]
```

status = `completed` → 同时设置 `completed_at = NOW()`。

### `get_task_stats()` - 任务统计

```python
async def get_task_stats(project_id: str) -> dict[str, Any]
```

返回:

```python
{
    "total": 25,
    "todo": 5,
    "in_progress": 8,
    "completed": 10,
    "overdue": 2,
}
```

其中 `overdue` = `due_date < NOW() AND status != 'completed'`。

## 四、章节内容校验 `validate_generated_content()`

对 AI 生成的章节正文进行三重自动检查:

### 检查 1: 禁词检查

1. 通过 `RulesService.list_rules(rule_type="forbidden", status="active")` 获取禁词规则
2. 遍历规则的 `patterns` 列表，在 content (小写) 中做子串匹配
3. 匹配到 → 记录 `{type: "forbidden_word", severity: rule.severity, rule_key, matched}`

### 检查 2: 角色存活检查

```sql
SELECT DISTINCT e.name FROM state_entities e
WHERE e.project_id = $1
  AND e.entity_type = 'character'
  AND e.lifecycle_status = 'dead'
```

- 若已死亡角色名出现在正文中 → `{type: "dead_character", severity: "error"}`
- 消息格式: `"Character '{name}' appears but is dead."`

### 检查 3: 设定一致性检查

1. 通过 `CanonService.list_documents(status="active", limit=20)` 获取活跃设定文档
2. 查询 active 角色列表
3. 对于每条设定文档:
   - 若 `doc.key` 在小写正文中出现 → 已引用，通过
   - 若标题包含本章角色名但 key 未在正文中出现 → `{type: "canon_missing_reference", severity: "warning"}`

### 返回值结构

```python
{
    "chapter_no": 42,
    "issues": [
        {"type": "forbidden_word", "severity": "critical", "rule_key": "x", "matched": "y"},
        {"type": "dead_character", "severity": "error", "name": "z", "message": "..."},
        {"type": "canon_missing_reference", "severity": "warning", "doc_key": "a", "doc_title": "b"},
    ],
    "passed": False,
    "issue_count": 3,
    "workflow_guide": {
        "phase": "内容校验",
        "passed": False,
        "description": "校验通过→提交章节；不通过→修订后再提交",
        "next_step": "修订正文",  # 或 "workflow.submit_chapter_commit"
        "issue_count": 3,
        "blocking_count": 2,  # severity in ('error', 'critical')
    },
}
```

## 五、章节提交 `submit_chapter_commit()`

### 方法签名

```python
async def submit_chapter_commit(
    project_id: str,
    chapter_no: int,
    title: str | None,
    local_files: list[dict[str, Any]],
    commit: dict[str, Any],
    username: str,
) -> dict[str, Any]
```

### 完整执行流程

```
Step 1: 解析 chapter_id
  ┌──────────────────────────────────┐
  │ 查询 chapters 表                     │
  │ 存在 → 使用已有 chapter_id              │
  │      → 更新 volume_no                 │
  │ 不存在 → 自动创建 chapter 记录:           │
  │      → 查找所属 volume (start/end chapter_no) │
  │      → 插入 chapters 表 status='draft'    │
  └──────────────────────────────────┘
                ↓
Step 2: 强制审核检查
  ┌──────────────────────────────────┐
  │ SELECT COUNT(*) FROM review_jobs           │
  │ WHERE chapter_id = $id                       │
  │ AND status IN ('completed', 'aggregated')   │
  │                                      │
  │ count == 0 → raise PermissionError    │
  │   "章节尚未完成审核，请先调用 review.start_job" │
  └──────────────────────────────────┘
                ↓
Step 3: 事务写入 (FOR UPDATE transaction)
  ├── 插入 chapter_commits 表
  │   - commit_no = COALESCE(MAX(commit_no)+1, 1)
  │   - payload = {title, local_files, ...commit}
  │   - accepted = true
  ├── 更新 chapters 表
  │   - status = 'completed'
  │   - title = COALESCE(new_title, old_title)
  ├── 回填 volumes.end_chapter_no
  │   - UPDATE volumes SET end_chapter_no = MAX(chapter_no)
  └── 插入 audit_logs 表
      - action = 'chapter_commit'
      - resource_type = 'chapter'
      - 关联 users 表获取 user_id
```

### 返回值结构

```python
{
    "chapter_no": 42,
    "commit_id": "uuid",
    "commit_no": 3,
    "accepted": true,
    "created_at": "iso-timestamp",
    "workflow_guide": {
        "phase": "章节提交完成",
        "description": "章节已提交，下一步执行数据维护",
        "next_actions": [
            {"tool": "kb.world.auto_update", "desc": "更新世界状态"},
            {"tool": "arc.record_emotion", "desc": "记录角色情感变化"},
            {"tool": "arc.record_power", "desc": "记录角色实力变化"},
            {"tool": "arc.record_relationship", "desc": "记录角色关系变化"},
            {"tool": "arc.record_personality", "desc": "记录角色性格变化"},
            {"tool": "plot.thread.advance", "desc": "推进剧情线"},
            {"tool": "foreshadowing.payoff", "desc": "回收到期伏笔"},
            {"tool": "workflow.learn_from_review", "desc": "从审核学习"},
        ],
    },
}
```

## 六、审计日志 `list_audit_logs()`

```python
async def list_audit_logs(
    project_id: str,
    action: str | None = None,
    resource_type: str | None = None,
    limit: int = 50,
) -> list[dict[str, Any]]
```

从 `audit_logs` 表查询，按 `created_at DESC` 排序。

## 涉及的数据库表

| 表名 | 操作 |
|------|------|
| `workflows` | INSERT / SELECT / UPDATE |
| `workflow_steps` | INSERT / SELECT / UPDATE |
| `tasks` | INSERT / SELECT / UPDATE |
| `chapters` | SELECT / INSERT / UPDATE |
| `volumes` | SELECT / UPDATE |
| `chapter_commits` | INSERT |
| `review_jobs` | SELECT (验证) |
| `audit_logs` | INSERT / SELECT |
| `state_entities` | SELECT (校验) |
| `canon_documents` | SELECT (通过 CanonService) |
| `canon_rules` | SELECT (通过 RulesService) |
| `users` | SELECT (JOIN 获取 user_id) |