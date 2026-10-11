# LLM 客户端

## 概述

`LLMClient` 是 Novel OS 统一的 LLM 调用接口。它从数据库 `model_profiles` 表动态读取模型配置，通过 OpenAI 兼容 API 调用 `/v1/chat/completions`。支持两种调用模式：按 task_type 路由自动选择模型，或按 profile_key 指定特定模型。

---

## 初始化

```python
llm_client = LLMClient(db)
```

维护 `_clients: dict[str, httpx.AsyncClient]` 缓存 HTTP 客户端（按 `api_url` 去重），timeout 120 秒。

---

## 模型配置查询

### _get_config(project_id, task_type)

按任务类型自动选择最合适的模型：

```sql
SELECT profile_key, provider, model_name, default_params, tier
FROM model_profiles
WHERE status = 'active'
  AND $1 = ANY(task_types)
ORDER BY is_default DESC, tier
LIMIT 1
```

- `task_types` 是 PostgreSQL 数组字段，使用 `ANY` 操作符匹配
- 排序优先级：`is_default DESC`（默认模型优先）→ `tier`（低 tier 优先）
- `task_type` 示例值：`outline`、`draft`、`polish`、`review`、`compress` 等
- 注意：此查询不按 `project_id` 过滤，模型配置是用户级的（user-level）

### chat_with_profile 的模型选择

按指定 `profile_key` 精确匹配：

```sql
SELECT profile_key, provider, model_name, default_params
FROM model_profiles
WHERE profile_key = $1 AND status = 'active'
```

可选传入 `user_id` 进一步限定范围。

---

## chat() — 核心调用

```python
result = await llm_client.chat(
    project_id="uuid-xxx",
    task_type="draft",
    messages=[{"role": "system", "content": "..."}, {"role": "user", "content": "..."}],
    temperature=0.7,
    max_tokens=4096,
)
# returns: {
#     "text": "生成的文本内容",
#     "model": "gpt-4",
#     "usage": {"prompt_tokens": 100, "completion_tokens": 200, "total_tokens": 300},
#     "profile_key": "default-gpt4",
# }
```

### 调用流程

1. `_get_config(project_id, task_type)` → 获取配置
2. 解析 `default_params`（jsonb，可能以字符串返回，需要 `json.loads`）
3. 提取 `api_url`、`api_key`、`model_name`
4. 拼接完整 URL：若 URL 不以 `/chat/completions` 结尾，追加 `/chat/completions`
5. 获取/创建缓存的 `httpx.AsyncClient`
6. `POST {url}`，请求体：
```json
{
  "model": "model_name",
  "messages": [...],
  "temperature": 0.7,
  "max_tokens": 4096
}
```
7. 检查 HTTP 状态码，非 200 时记录错误并抛出 `RuntimeError`
8. 解析 `choices[0].message.content` 和 `usage`

---

## chat_simple() — 快捷包装

```python
result = await llm_client.chat_simple(
    project_id="uuid",
    task_type="outline",
    system_prompt="你是一个小说大纲生成器",
    user_prompt="请为修仙小说生成大纲",
    temperature=0.7,
    max_tokens=4096,
)
```

内部将 system_prompt 和 user_prompt 组装为标准 messages 数组后调用 `chat()`。

---

## chat_with_profile() — 指定模型调用

```python
result = await llm_client.chat_with_profile(
    user_id=None,
    profile_key="claude-opus",
    messages=[...],
    temperature=0.7,
    max_tokens=4096,
)
```

绕过 task_type 路由，直接按 profile_key 调用模型。用于多模型辩论场景（KnowledgeCouncilService 用不同模型讨论同一议题）。

与 `chat()` 的区别：
- 不经过 task_type → model 路由
- 可指定 `user_id` 限定模型归属
- 除此之外的 API 调用逻辑完全相同

---

## 依赖关系

```text
LLMClient --> ContextCompressionService  (章节/弧/卷压缩)
          --> KnowledgeAuditService      (知识审计)
          --> KnowledgeCouncilService    (知识多方辩论)
          --> ai_reviewer (init)         (AI 审阅器)
```

---

## 错误处理

- **无匹配模型**：`_get_config` 返回 None → `chat()` 抛出 `ValueError("No active model profile found for task_type=...")`
- **缺少 API 配置**：`api_url` 或 `api_key` 为空 → `ValueError("API URL or key not configured for profile '...'")`
- **API 返回非 200**：抛出 `RuntimeError("LLM API returned {code}: {body[:500]}")`
- **model_profiles 中的 `default_params`**：asyncpg 可能将 jsonb 返回为字符串，需在代码中 `json.loads` 二次解析