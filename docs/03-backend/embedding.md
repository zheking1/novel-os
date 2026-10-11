# 嵌入与重排序服务

## 概述

`EmbeddingService` 和 `RerankService` 提供文本向量化和结果重排序能力。两者均从数据库 `model_profiles` 表动态读取模型配置，而非硬编码或环境变量。

---

## EmbeddingService

### 初始化

```python
embedding_service = EmbeddingService(db)
```

内部维护 `_clients: dict[str, httpx.AsyncClient]` 缓存 HTTP 客户端（按 `provider:api_url` 为 key），timeout 30 秒。

### 模型配置查询

`_get_config(project_id)` 从 `model_profiles` 表查询：

```sql
SELECT id::text, provider, model_name, default_params, metadata
FROM model_profiles
WHERE project_id = $1
  AND status = 'active'
  AND 'embedding' = ANY(task_types)
ORDER BY is_default DESC, tier
LIMIT 1
```

- 按 `is_default DESC` 优先，再按 `tier` 排序（低 tier = 优先）
- `task_types` 是 PostgreSQL 数组，使用 `ANY` 操作符匹配包含 `'embedding'` 的记录
- `default_params` 字段（jsonb）包含 `api_url`、`api_key`、`dimensions` 等连接参数

### 嵌入调用

```python
await embedding_service.embed(project_id, texts: list[str])  # → list[list[float]]
await embedding_service.embed_single(project_id, text)        # → list[float]
```

#### 标准流程（非 siliconflow 提供商）

1. 从 config 解析 `api_url`、`api_key`、`dimensions`（默认 1024）
2. `POST {api_url}/v1/embeddings`
3. 请求体：
```json
{
  "model": "配置的model_name",
  "input": ["text1", "text2", ...],
  "dimensions": 1024
}
```
4. 响应 `data[].embedding` 按 `index` 排序后返回

#### SiliconFlow 特殊处理

硅基流动 API 不支持数组输入的 input，每个文本需单独请求：

```python
for text in texts:
    POST /v1/embeddings {"model": "...", "input": "单个文本字符串"}
    → 收集 data[0]["embedding"]
```

无 config 或 api_url/api_key 为空时返回空列表 `[]`。API 错误时记录日志并返回空 embedding。

---

## RerankService

### 初始化

```python
rerank_service = RerankService(db)
```

同样维护 `_clients` 缓存，timeout 30 秒。

### 模型配置查询

`_get_config(project_id)` 查询逻辑与 EmbeddingService 相同，仅 `task_types` 过滤条件为 `'rerank' = ANY(task_types)`：

```sql
SELECT id::text, provider, model_name, default_params, metadata
FROM model_profiles
WHERE project_id = $1
  AND status = 'active'
  AND 'rerank' = ANY(task_types)
ORDER BY is_default DESC, tier
LIMIT 1
```

### 重排序调用

```python
await rerank_service.rerank(project_id, query, documents, top_n=5)
# → [{"index": 0, "score": 0.95, "text": "..."}, ...]
```

#### 调用流程

1. 获取 config，若不存在或无 api_url/api_key → **降级到无操作**，返回 `score=1.0` 的等分值
2. `POST {api_url}/v1/rerank`
3. 请求体：
```json
{
  "model": "配置的model_name",
  "query": "查询文本",
  "documents": ["doc1", "doc2", ...],
  "top_n": 5
}
```
4. 解析 `results[].relevance_score` 和 `index` 构建返回列表，按 `relevance_score` 降序排序

#### 降级策略

未配置 rerank 模型时自动降级，返回前 `top_n` 个文档且分数均为 1.0。API 异常时同样降级返回等分值，不中断调用链。

---

## 资源清理

两个服务均提供 `close()` 方法，关闭所有缓存的 httpx 客户端：

```python
await embedding_service.close()
await rerank_service.close()
```