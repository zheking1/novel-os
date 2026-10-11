# Model Tools — 模型配置、路由与成本追踪

> Source: `tools/model.py`
> Dependencies: `db`, `auth`, `model_cost_service`

---

## model.profile — 模型配置

### model.profile.upsert

```python
@mcp.tool(name="model.profile.upsert")
async def model_profile_upsert(
    profile_key: str, display_name: str | None = None,
    provider: str | None = None, model_name: str | None = None,
    task_types: list[str] | None = None, tier: str | None = None,
    default_params: dict | None = None, cost_config: dict | None = None,
    rate_limit_config: dict | None = None, is_default: bool | None = None,
    status: str | None = None, metadata: dict | None = None,
    is_contributed: bool | None = None,
) -> dict[str, Any]
```

**Purpose:** 创建/更新模型配置文件。**用户级别**——每个用户的模型配置独立。删除只需传 `status='inactive'` 即可软删除。

**Parameters:**
- `is_contributed` — 是否贡献给讨论室（设为 true 后该模型可被讨论室自动选用）
- `cost_config` — `{input_per_1k, output_per_1k, currency}`
- `rate_limit_config` — `{rpm, tpm, concurrency}`

**Scope:** `write`

### model.profile.list

```python
async def model_profile_list(
    task_type: str | None = None, status: str = "active", tier: str | None = None,
) -> list[dict[str, Any]]
```

**Purpose:** 列出当前用户的所有模型配置。按 task_type / status / tier 过滤。

**DB Tables:** `model_profiles` | **Service:** `model_cost_service`

---

## model.route — 模型路由

### model.route

```python
async def model_route(
    workspace: str, project: str, task_type: str,
    chapter_no: int | None = None, volume_no: int | None = None,
) -> dict[str, Any]
```

**Purpose:** 根据任务类型和上下文章节，路由到最匹配的模型配置。返回推荐模型 key 和配置信息。

### model.route_rule.upsert

```python
async def model_route_rule_upsert(
    workspace: str, project: str, task_type: str, profile_key: str,
    priority: int = 100, conditions: dict | None = None,
    fallback_profile_keys: list[str] | None = None,
    status: str = "active", metadata: dict | None = None,
) -> dict[str, Any]
```

**Purpose:** 创建/更新项目级模型路由规则。`conditions` 按 chapter/volume 等条件匹配。

**Scope:** `write`

### model.route_rule.list

```python
async def model_route_rule_list(
    workspace: str, project: str, task_type: str | None = None,
    status: str = "active",
) -> list[dict[str, Any]]
```

**DB Tables:** `model_route_rules` | **Service:** `model_cost_service`

---

## model.auto_assign

```python
async def model_auto_assign(workspace: str, project: str) -> dict[str, Any]
```

**Purpose:** 自动分析所有模型名称推断其能力，建议任务分配。返回每个模型的 `suggested_tasks` 和 `current_tasks` 对比，agent 确认后调用 `model.profile.upsert` 更新。

**模型名称推断规则：**
- 包含 `embed/e5/bge/gte/text-embedding` → `embedding`
- 包含 `rerank/bge-rerank` → `rerank`
- 包含 `deepseek/glm-z1/qwen3/qwen2.5/glm4` → `analysis`
- 包含 `instruct/chat/deepseek/qwen/glm` → `review`
- 包含 `qwen2.5/qwen3/deepseek` → `context`

**Scope:** `write`

---

## cost — 成本追踪

### cost.record_usage

```python
async def cost_record_usage(
    workspace: str, project: str, task_type: str,
    profile_key: str | None = None, provider: str | None = None,
    model_name: str | None = None, source_type: str | None = None,
    source_id: str | None = None, input_tokens: int = 0,
    output_tokens: int = 0, cached_tokens: int = 0,
    total_tokens: int | None = None, cost_amount: float | None = None,
    currency: str = "USD", latency_ms: int | None = None,
    success: bool = True, error_code: str | None = None,
    metadata: dict | None = None,
) -> dict[str, Any]
```

**Purpose:** 记录一次模型调用的 token 用量和费用。用于成本追踪和统计。

**Scope:** `write`

### cost.report

```python
async def cost_report(
    workspace: str, project: str, group_by: str = "day",
    task_types: list[str] | None = None, profile_keys: list[str] | None = None,
    from_date: str | None = None, to_date: str | None = None,
) -> dict[str, Any]
```

**Purpose:** 生成费用报表。`group_by`: `day` / `week` / `month`。支持按 task_type 和 profile_key 过滤。

**DB Tables:** `cost_logs` | **Service:** `model_cost_service`