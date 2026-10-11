# Performance 服务 — 性能优化服务

**源码**: `novel-os-mcp/src/novel_os_mcp/performance.py` (288 行)

## 概述

Performance 模块提供 4 个性能优化子服务：批量查询、查询优化、请求限流和性能指标采集。

---

## 一、批量查询服务 (BatchQueryService)

### 概述

将多个查询排队合并，减少数据库往返次数。

### 核心机制

- 使用 `asyncio.Lock` 保护的查询队列 `_query_queue`
- 队列满 10 条自动 flush
- 在单个连接中顺序执行所有排队的查询

### queue_query

将查询加入队列:

```python
await service.queue_query(
    query="SELECT ...",
    params=(...),
    callback=optional_callback  # SELECT 结果回调
)
```

当队列达到 10 条时，自动触发 `_flush()`。

### _flush

批量执行所有排队查询:
- SELECT 查询 → `conn.fetch(query, *params)` → 调用 callback
- 其他查询 → `conn.execute(query, *params)`
- 异常静默处理（不阻断其他查询）

---

## 二、查询优化服务 (QueryOptimizationService)

### 批量获取方法

| 方法 | SQL 优化 | 说明 |
|------|------|------|
| `batch_get_chapters()` | `WHERE chapter_no IN (...)` | 批量获取章节 |
| `batch_get_characters()` | `WHERE id IN (...)` | 批量获取角色 |
| `batch_get_events()` | `WHERE chapter_id IN (...)` + `ORDER BY chapter_id, event_order` | 批量获取事件 |
| `get_chapter_range()` | `WHERE chapter_no BETWEEN start AND end` | 连续章节范围查询 |
| `search_canon_documents()` | `WHERE (title ILIKE OR key ILIKE)` + 可选 `doc_type IN (...)` | 规范文档搜索 |

### get_foreshadowing_stats

聚合查询获取伏笔统计:

```sql
SELECT
    COUNT(*) AS total,
    SUM(CASE WHEN status='planted' THEN 1 ELSE 0 END) AS planted,
    SUM(CASE WHEN status='developing' THEN 1 ELSE 0 END) AS developing,
    SUM(CASE WHEN status='ready_to_payoff' THEN 1 ELSE 0 END) AS ready_to_payoff,
    SUM(CASE WHEN status='paid_off' THEN 1 ELSE 0 END) AS paid_off,
    SUM(CASE WHEN status='abandoned' THEN 1 ELSE 0 END) AS abandoned,
    SUM(CASE WHEN importance IN ('high','critical') THEN 1 ELSE 0 END) AS high_importance
FROM foreshadowing WHERE project_id = $1
```

**优化**: 一次查询替代多次 count。

---

## 三、请求限流服务 (RequestThrottlingService)

### 概述

使用 `asyncio.Semaphore` 控制并发，防止对外部 API 过载。

### register_limit

注册限流规则:

| 参数 | 默认值 | 说明 |
|------|------|------|
| `key` | - | 限流标识 |
| `max_concurrent` | 10 | 最大并发数 |
| `rate_limit_per_second` | 30 | 每秒最大请求数 (预留参数) |

### acquire / release

- `acquire(key)`: 获取许可 (await semaphore)
- `release(key)`: 释放许可 (semaphore.release())

**使用模式**:
```python
await throttling.acquire("api_calls")
try:
    result = await make_api_call()
finally:
    throttling.release("api_calls")
```

---

## 四、性能指标服务 (PerformanceMetricsService)

### 概述

收集操作的平均、最小、最大和 P95 耗时。

### start_timer / end_timer

```python
metrics.start_timer("db_query")
# ... 执行操作 ...
duration = metrics.end_timer("db_query")
# duration = 耗时秒数
```

### get_metrics

获取所有操作的统计信息:

```json
{
  "db_query": {
    "count": 100,
    "min": 0.001,
    "max": 0.5,
    "avg": 0.012,
    "p95": 0.035
  }
}
```

P95 计算条件: 至少有 20 次记录时才产出。

### reset

清空所有指标和计时器。

---

## 工作流引导

1. 高频查询 → `BatchQueryService.queue_query()` 合并批次
2. 批量数据获取 → `QueryOptimizationService.batch_get_*()` 减少 N+1 问题
3. API 调用保护 → `RequestThrottlingService.register_limit()` + `acquire/release`
4. 性能监控 → `PerformanceMetricsService.start_timer/end_timer` → `get_metrics()` 分析