# Qdrant 向量索引

## 概述

`VectorIndex` 封装 `AsyncQdrantClient`，提供向量数据的增删查操作。作为 Novel OS 记忆系统和知识检索的核心组件，负责存储和检索文本的向量化表示。

---

## 初始化

```python
vector_index = VectorIndex(settings)
```

- `_client` 为懒加载的 `AsyncQdrantClient`
- 连接参数来自 `settings.qdrant_url` 和 `settings.qdrant_api_key`

---

## 集合配置

集合名称通过配置文件定义：

| 配置项 | 默认值 | 用途 |
|---|---|---|
| `QDRANT_MEMORY_COLLECTION` | `novel_memory_chunks` | 叙事记忆分块向量索引 |
| `QDRANT_REFERENCE_COLLECTION` | `novel_reference_chunks` | 参考材料分块向量索引 |

---

## upsert_memory_point

```python
await vector_index.upsert_memory_point(
    collection="novel_memory_chunks",
    point_id="uuid-xxx",
    vector=[0.1, 0.2, ...],
    payload={"project_id": "uuid", "text": "..."}
)
```

内部调用 `AsyncQdrantClient.upsert`，使用 `models.PointStruct` 构造点数据：
- `id`: 唯一标识符（字符串）
- `vector`: 浮点向量列表
- `payload`: 任意 JSON 序列化字典

支持覆盖更新（相同 id 会替换已有向量和 payload）。

---

## search

```python
results = await vector_index.search(
    collection="novel_memory_chunks",
    vector=[0.1, 0.2, ...],
    limit=10,
    project_id="uuid-xxx"
)
# returns: [{"id": "uuid", "score": 0.95, "payload": {...}}, ...]
```

### 查询参数

| 参数 | 类型 | 说明 |
|---|---|---|
| `collection` | `str` | 集合名称 |
| `vector` | `list[float]` | 查询向量 |
| `limit` | `int` | 返回最大结果数 |
| `project_id` | `str | None` | 可选的 project_id 过滤 |

### 过滤逻辑

当 `project_id` 不为 None 时，构造 Qdrant Filter：

```python
models.Filter(
    must=[
        models.FieldCondition(
            key="project_id",
            match=models.MatchValue(value=project_id),
        )
    ]
)
```

这保证检索结果仅限于指定项目，实现多租户隔离。

### 返回值

每个结果项包含：
- `id`: 点 ID（转为字符串）
- `score`: 相似度分数
- `payload`: 存储时的原始 payload 字典

查询调用 `AsyncQdrantClient.search`，传入 `query_vector`、`query_filter`、`limit`、`with_payload=True`。

---

## 依赖关系

`VectorIndex` 被以下服务依赖：

```text
VectorIndex --> MemoryService     (记忆存储与语义搜索)
            --> NoveltyService    (新颖性检测，搜索已有内容)
```

---

## 架构要点

- 懒加载客户端：首次访问 `client` 属性时才创建连接
- 无连接池复用：`AsyncQdrantClient` 由 qdrant_client 库内部管理
- 不管理集合的创建/删除：集合由运维层面（数据库迁移/手动初始化）管理
- 字符串 ID: 所有 point_id 以字符串形式存储和返回