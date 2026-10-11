# System Tools — 系统级工具

> Source: `tools/system.py`, `tools/admin.py`, `tools/system_assets.py`, `tools/system_evolution.py`, `tools/system_notifications.py`
> Dependencies: `db`, `auth`, `cache_service`, `backup_service`, `_health_service`, `_degradation_service`

---

## cache — Redis 缓存管理

### cache.health

```python
@mcp.tool(name="cache.health")
async def cache_health() -> dict[str, Any]
```

**Purpose:** 检查 Redis 连接状态。返回 `{redis: "connected"|"disconnected", healthy: bool}`

### cache.get_stats

```python
async def cache_get_stats(workspace: str, project: str) -> dict[str, Any]
```

**Purpose:** 获取项目缓存统计（各类缓存 key 数量、内存占用等）。

### cache.get

```python
async def cache_get(
    workspace: str, project: str, target: str, target_id: str,
    profile: str | None = None, pov: str | None = None,
) -> dict[str, Any] | None
```

**Purpose:** 获取缓存内容。`target`: `canon` / `entity` / `chapter` / `rules` / `context`。`context` 需要指定 `profile` + `pov`。

### cache.invalidate

```python
async def cache_invalidate(
    workspace: str, project: str, target: str, target_id: str | None = None,
) -> dict[str, Any]
```

**Purpose:** 使缓存失效。`target`: `canon` / `entity` / `chapter` / `rules` / `context` / `all`。`entity`/`canon`/`chapter` 需传 `target_id`。

### cache.warm

```python
async def cache_warm(
    workspace: str, project: str, chapter_nos: list[int],
    profiles: list[str] | None = None, povs: list[str] | None = None,
) -> dict[str, Any]
```

**Purpose:** 预热上下文缓存。默认 `profiles=["standard","detailed"]`, `povs=["narrator"]`。

**DB Tables:** — (Redis keys) | **Service:** `cache_service`

---

## backup / restore — 备份与恢复

### backup.create

```python
async def backup_create(
    workspace: str | None = None, project: str | None = None,
    backup_type: str = "incremental", storage_path: str | None = None,
) -> dict[str, Any]
```

**Purpose:** 创建备份记录。`backup_type`: `full` / `incremental`。**Scope:** `admin`

### backup.list

```python
async def backup_list(
    workspace: str | None = None, project: str | None = None,
    backup_type: str | None = None, status: str | None = None,
    limit: int = 100,
) -> list[dict[str, Any]]
```

### backup.schedule.upsert

```python
async def backup_schedule_upsert(
    schedule_name: str, workspace: str | None = None,
    project: str | None = None, backup_type: str = "incremental",
    schedule_type: str = "daily", retention_count: int = 7,
    retention_days: int = 30, enabled: bool = True,
) -> dict[str, Any]
```

**Purpose:** 创建/更新自动备份计划。`schedule_type`: `daily` / `weekly` / `monthly`。**Scope:** `admin`

### backup.schedule.list

```python
async def backup_schedule_list(
    workspace: str | None = None, project: str | None = None,
) -> list[dict[str, Any]]
```

### restore.list

```python
async def restore_list(workspace: str, project: str, limit: int = 100) -> list[dict[str, Any]]
```

**DB Tables:** `backup_records`, `backup_schedules`, `restore_records` | **Service:** `backup_service`

---

## system — 系统健康

### system.health

```python
async def system_health() -> dict[str, Any]
```

**Purpose:** 获取系统全面健康状态（DB、Redis、Qdrant、MCP 服务等）。

### system.degradation_status

```python
async def system_degradation_status() -> dict[str, Any]
```

**Purpose:** 获取当前降级状态。

### system.degradation_plan

```python
async def system_degradation_plan(failed_services: list[str]) -> dict[str, Any]
```

**Purpose:** 根据失败的服务获取降级方案。

### system.fallback_strategy

```python
async def system_fallback_strategy(feature: str) -> str
```

**Purpose:** 获取特定功能的降级策略文本。

**Service:** `_health_service`, `_degradation_service`

---

## admin — 管理健康检查

### admin.health

```python
async def admin_health() -> dict[str, Any]
```

**Purpose:** 管理级健康检查。验证 DB、Redis、Qdrant 连接状态，返回 `{status, healthy, database, mcp, redis, qdrant, latency}`。

**Source:** `tools/admin.py`

---

## system.style_profile — 系统级文风档案

> Source: `tools/system_assets.py`

### system.style_profile.list

```python
async def system_style_profile_list(
    workspace: str, genre: str | None = None, status: str = "active",
    limit: int = 50, offset: int = 0, project: str | None = None,
) -> dict[str, Any]
```

### system.style_profile.get

```python
async def system_style_profile_get(
    workspace: str, profile_key: str, project: str | None = None,
) -> dict[str, Any]
```

### system.style_profile.fork

```python
async def system_style_profile_fork(
    workspace: str, profile_key: str, new_name: str,
    project: str | None = None,
) -> dict[str, Any]
```

**Purpose:** 从系统级文风 fork 到用户/项目级。

**DB Tables:** `system_style_profiles`

---

## system.prompt_template — 系统级 Prompt 模板

> Source: `tools/system_assets.py`

### system.prompt_template.list

```python
async def system_prompt_template_list(
    workspace: str, template_type: str | None = None, genre: str | None = None,
    status: str = "active", limit: int = 50, offset: int = 0,
    project: str | None = None,
) -> dict[str, Any]
```

### system.prompt_template.get

```python
async def system_prompt_template_get(
    workspace: str, template_key: str, project: str | None = None,
) -> dict[str, Any]
```

### system.prompt_template.fork

```python
async def system_prompt_template_fork(
    workspace: str, template_key: str, new_name: str,
    project: str | None = None,
) -> dict[str, Any]
```

**DB Tables:** `system_prompt_templates`

---

## system.model_profile — 系统级模型配置

> Source: `tools/system_assets.py`

### system.model_profile.list

```python
async def system_model_profile_list(
    workspace: str, task_type: str | None = None, status: str = "active",
    limit: int = 50, offset: int = 0, project: str | None = None,
) -> dict[str, Any]
```

### system.model_profile.get

```python
async def system_model_profile_get(
    workspace: str, profile_key: str, project: str | None = None,
) -> dict[str, Any]
```

### system.model_profile.fork

```python
async def system_model_profile_fork(
    workspace: str, profile_key: str, new_name: str,
    project: str | None = None,
) -> dict[str, Any]
```

**DB Tables:** `system_model_profiles`

---

## system.evolution — 系统进化提案

> Source: `tools/system_evolution.py`

### system.evolution.propose

```python
async def system_evolution_propose(
    workspace: str, title: str, description: str, proposal_type: str,
    target_entity_type: str, proposed_content: dict[str, Any],
    evolution_reason: str, target_entity_key: str | None = None,
    target_entity_id: str | None = None, evidence: dict | None = None,
    source_project_id: str | None = None, source_chapter_no: int | None = None,
    metadata: dict | None = None, project: str | None = None,
) -> dict[str, Any]
```

**Purpose:** 创建系统级进化提案。提案创建后自动进入 AI 初审队列。

**Parameters:**
- `proposal_type` — `create` / `update` / `delete` / `merge`
- `target_entity_type` — `style_profile` / `prompt_template` / `model_profile` / `knowledge_item` / `setting_item` / `genre_config`

### system.evolution.list

```python
async def system_evolution_list(
    workspace: str, status: str | None = None,
    target_entity_type: str | None = None, proposal_type: str | None = None,
    limit: int = 50, offset: int = 0, project: str | None = None,
) -> dict[str, Any]
```

### system.evolution.get

```python
async def system_evolution_get(workspace: str, proposal_id: str) -> dict[str, Any]
```

### system.evolution.ai_review

> ⚠️ 该工具**不在** `tools/system_evolution.py`，实际注册于 `services/ai_reviewer.py`，由 `ai_reviewer_worker` 以 `"tool": "system.evolution.ai_review"` 调用。

```python
async def system_evolution_ai_review(
    workspace: str, proposal_id: str, action: str, reason: str | None = None,
    review_detail: dict | None = None,
) -> dict[str, Any]
```

**Purpose:** AI 自动初审。`action`: `approve` / `reject` / `request_changes`。

### system.evolution.admin_review

```python
async def system_evolution_admin_review(
    workspace: str, proposal_id: str, action: str, reason: str | None = None,
    modified_content: dict | None = None,
) -> dict[str, Any]
```

**Purpose:** 管理员终审。`action`: `approve` / `reject`。批准后自动执行变更。

### ~~system.evolution.apply~~（不存在）

> ⚠️ 代码中没有这个工具。`system_evolution.py` 实际注册 6 个：
> `system.evolution.propose` / `.list` / `.get` / `.admin_review` / `.get_history` / `.retry_ai_review`。
> 提案执行由 `system.evolution.admin_review` 批准后自动触发，无需单独的 apply。

**Service:** SystemEvolutionService

---

## system.notification — 站内通知

> Source: `tools/system_notifications.py`

### system.notification.list

```python
async def system_notification_list(
    workspace: str, project: str | None = None, is_unread_only: bool = False,
    notification_type: str | None = None, limit: int = 50, offset: int = 0,
) -> dict[str, Any]
```

**Purpose:** 获取用户的站内通知列表。`notification_type`: `evolution_proposal` / `system_update` / `ai_review_completed` / `admin_review_required`。

### system.notification.mark_read

```python
async def system_notification_mark_read(
    notification_id: str | None = None,
) -> dict[str, Any]
```

**Purpose:** 标记通知为已读。不传 ID 则全部已读。

### system.notification.mark_all_read

```python
async def system_notification_mark_all_read() -> dict[str, Any]
```

### system.notification.delete

```python
async def system_notification_delete(notification_id: str) -> dict[str, Any]
```

### system.notification.get_unread_count

```python
async def system_notification_get_unread_count() -> dict[str, Any]
```

**DB Tables:** `system_notifications`