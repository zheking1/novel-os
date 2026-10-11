# 降级系统

## 概述

Novel OS 的降级系统由两个服务组成：

- **DependencyHealthService**：对 Qdrant、Redis、PostgreSQL 进行健康检查
- **DegradationModeService**：管理 5 级降级状态，为各功能提供降级策略

降级系统的设计目标是：当外部依赖不可用时，服务仍能以降级模式继续运行，而非直接崩溃。

---

## DependencyHealthService

### 初始化

```python
health_service = DependencyHealthService(settings)
```

### 健康检查方法

#### check_qdrant_health()

通过 HTTP GET `/healthz` 端点检查 Qdrant：

```python
async def check_qdrant_health():
    async with httpx.AsyncClient(timeout=5.0) as client:
        response = await client.get(f"{qdrant_url}/healthz", headers=headers)
        if response.status_code == 200:
            return {"healthy": True, "url": qdrant_url, "status": "operational"}
        return {"healthy": False, "url": qdrant_url, "status": f"http_{code}"}
```

- 若有 `QDRANT_API_KEY`，在请求头中附加 `api-key`
- 超时 5 秒
- 异常时返回 `{"healthy": False, "error": str(exc)}`

#### check_redis_health()

通过 `PING` 命令检查 Redis：

```python
async def check_redis_health():
    client = redis.Redis(host=..., port=..., db=..., password=..., socket_timeout=5.0)
    await client.ping()
    await client.aclose()
    return {"healthy": True, "url": redis_url, "status": "operational"}
```

- socket_timeout 5 秒
- 使用 `redis.asyncio` 异步客户端

#### check_database_health()

通过执行 `SELECT 1` 检查 PostgreSQL：

```python
async def check_database_health():
    db = Database(settings)
    await db.connect()
    await db.fetchrow("SELECT 1 as health")
    await db.close()
    return {"healthy": True, "status": "operational"}
```

- 独立创建 `Database` 实例而非使用 `deps.db`
- 连接后立即关闭

#### get_all_health()

综合所有检查：

```python
await health_service.get_all_health()
# returns: {
#     "healthy": True/False,
#     "qdrant": {...},
#     "redis": {...},
#     "database": {...},
#     "degradation_mode": True/False,
# }
```

#### get_degradation_plan(failed_services)

根据失败的服务列表生成降级方案：

```python
plan = health_service.get_degradation_plan(["qdrant"])
# returns: {
#     "degradation_level": 1,
#     "available_services": ["redis", "database"],
#     "degraded_services": ["qdrant"],
#     "actions": [
#         {"service": "qdrant", "action": "fallback_to_pg_fulltext",
#          "description": "使用 PostgreSQL 全文检索替代向量搜索"},
#     ],
# }
```

| 失败服务 | 降级动作 |
|---|---|
| `qdrant` | 回退到 PostgreSQL 全文检索 |
| `redis` | 回退到进程内存缓存 |

---

## DegradationModeService

### 5 级降级模型

| 级别 | 常量 | 含义 |
|---|---|---|
| 0 | `LEVEL_NORMAL` | 全部正常，无需降级 |
| 1 | `LEVEL_REDIS_DEGRADED` | Redis 不可用，缓存回退到内存 |
| 2 | `LEVEL_QDRANT_DEGRADED` | Qdrant 不可用，向量搜索回退到全文检索 |
| 3 | `LEVEL_BOTH_DEGRADED` | Redis 和 Qdrant 均不可用 |
| 4 | `LEVEL_CRITICAL` | 数据库不可用，服务严重降级 |

### 初始化与状态

```python
degradation_service = DegradationModeService(settings)
# 当前状态：
degradation_service.current_level      # → int (0-4)
degradation_service.degraded_services  # → set[str]
```

### update_status()

执行所有健康检查并更新降级状态：

```python
status = await degradation_service.update_status()
# returns: {"level": 2, "degraded_services": ["qdrant"], "health": {...}, "can_continue": True}
```

状态判定逻辑：
1. 数据库不健康 → `LEVEL_CRITICAL`（`can_continue = False`）
2. Qdrant 和 Redis 都不健康 → `LEVEL_BOTH_DEGRADED`
3. 仅 Qdrant 不健康 → `LEVEL_QDRANT_DEGRADED`
4. 仅 Redis 不健康 → `LEVEL_REDIS_DEGRADED`
5. 全部健康 → `LEVEL_NORMAL`

### 状态查询方法

```python
degradation_service.is_qdrant_degraded()   # → bool
degradation_service.is_redis_degraded()    # → bool
degradation_service.is_database_degraded() # → bool
```

### get_fallback_strategy(feature)

获取特定功能的降级策略：

```python
strategy = degradation_service.get_fallback_strategy("vector_search")
# Qdrant 正常时 → "qdrant"
# Qdrant 降级时 → "pg_fulltext_search"
```

| 功能 | 正常策略 | 降级策略 |
|---|---|---|
| `vector_search` | `qdrant` | `pg_fulltext_search` |
| `cache` | `redis` | `memory_cache` |
| `database_write` | `readwrite` | `readonly` |
| 未定义的功能 | — | `unavailable` |

---

## 依赖关系

```text
DependencyHealthService
    ↓
DegradationModeService
    ↓ (被工具模块调用)
tools/system.py → system.health 工具
```

两个服务在 `deps.py` 中分别实例化，与主业务服务并行存在。目前降级状态不自动注入到各业务服务中 — 由工具模块手动检查降级状态后选择相应的执行路径。

---

## 架构要点

- **独立检查**：每个依赖的健康检查完全独立，互相不阻塞
- **慢降级**：依赖恢复正常后，`update_status()` 可重新提升降级级别
- **非自动注入**：降级状态需业务层主动查询，不在框架层自动切换实现
- **数据库致命**：数据库不健康时 `can_continue = False`，服务基本不可用