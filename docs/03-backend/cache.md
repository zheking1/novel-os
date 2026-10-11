# Redis 缓存系统

## 概述

`CacheService` 封装基于 Redis 的多类型上下文缓存，用于加速频繁读取的小说数据和上下文包组装。缓存以 project 为维度组织，使用前缀区分类型，通过索引（Redis Set）追踪所有缓存键。

---

## 初始化

```python
cache_service = CacheService(settings)
```

- 使用 `settings.redis_db`（默认 db=0）连接 Redis
- `_client` 为懒加载的 `redis.asyncio.Redis` 实例（`decode_responses=True`，自动将字节转为字符串）

### 连接检查

```python
await cache_service.ping()  # → True/False
```

---

## 缓存键前缀与格式

| 前缀 | 常量 | 用途 | 键格式 |
|---|---|---|---|
| `canon:` | `PREFIX_CANON` | Canon 摘要 | `canon:{project_id}:{canon_id}` |
| `entity:` | `PREFIX_ENTITY_STATE` | 实体状态 | `entity:{project_id}:{entity_id}` |
| `chapter:` | `PREFIX_CHAPTER_SUMMARY` | 章节摘要 | `chapter:{project_id}:{chapter_no}` |
| `rules:` | `PREFIX_RULES` | 规则摘要 | `rules:{project_id}:{scope}` |
| `ctx:` | `PREFIX_CONTEXT` | 完整上下文包 | `ctx:{project_id}:{chapter_no}:{profile}:{pov}` |
| `idx:` | `PREFIX_INDEX` | 缓存索引 | `idx:{project_id}` |

键生成方法 `_make_key(prefix, project_id, *parts)` 使用空格拼接 parts：
```
{prefix}{project_id}:{part1} {part2} {part3}
```

### TTL 策略

- **默认 TTL**：3600 秒（1 小时）
- **最大 TTL**：86400 秒（24 小时），用于上下文包缓存
- 除上下包外，其他类型均使用默认 TTL
- 所有 `set_*` 方法均接受 `ttl` 参数覆盖

---

## 各类型缓存方法

### Canon 摘要

```python
await cache.get_canon_summary(project_id, canon_id)    # → dict | None
await cache.set_canon_summary(project_id, canon_id, summary, ttl=None)
await cache.invalidate_canon(project_id, canon_id)
```

### 实体状态

```python
await cache.get_entity_state(project_id, entity_id)    # → dict | None
await cache.set_entity_state(project_id, entity_id, state, ttl=None)
await cache.invalidate_entity(project_id, entity_id)
```

### 章节摘要

```python
await cache.get_chapter_summary(project_id, chapter_no)  # → dict | None
await cache.set_chapter_summary(project_id, chapter_no, summary, ttl=None)
await cache.invalidate_chapter(project_id, chapter_no)
```

### 规则摘要

```python
await cache.get_rules_summary(project_id, scope="effective")  # → list[dict] | None
await cache.set_rules_summary(project_id, scope, rules, ttl=None)
await cache.invalidate_rules(project_id)  # 删除所有 scope 的规则缓存
```

规则失效使用 `SCAN` 模式匹配 `rules:{project_id}:*` 批量清除。

### 上下文包 (Context Pack)

```python
await cache.get_context_pack(project_id, chapter_no, profile, pov)  # → dict | None
await cache.set_context_pack(project_id, chapter_no, profile, pov, context, ttl=None)
await cache.invalidate_context_pack(project_id, chapter_no=None)
```

上下文包使用 MAX_TTL（24 小时）。失效时支持按章节（删除 `ctx:{project_id}:{chapter_no}:*`）或按项目（删除 `ctx:{project_id}:*`）批量清除。

---

## 批量失效方法

业务逻辑变更时触发级联缓存失效：

| 方法 | 触发时机 | 失效的缓存 |
|---|---|---|
| `invalidate_on_canon_update(p, canon_id)` | Canon 更新 | canon + 所有上下文包 |
| `invalidate_on_rules_update(p)` | 规则变更 | rules（所有 scope）+ 所有上下文包 |
| `invalidate_on_final_commit(p, chapter_no)` | 章节定稿 | chapter 摘要 + 该章节上下文包 |
| `invalidate_on_foreshadowing_update(p)` | 伏笔状态变更 | 所有上下文包 |

---

## 索引管理

Redis Set `idx:{project_id}` 记录项目所有缓存键，支持：

- `_update_index(project_id, key)` — `SADD key` 到索引
- `_remove_from_index(project_id, key)` — `SREM key` 从索引移除
- `_cleanup_index(project_id, pattern)` — 按模式批量 `SREM` 清理
- `get_project_cache_keys(project_id)` — `SMEMBERS` 获取所有键

### get_cache_stats(project_id)

```python
await cache.get_cache_stats(project_id)
# → {
#     "project_id": "...",
#     "total_keys": 150,
#     "by_type": {"canon": 12, "entity": 45, "chapter": 60, "rules": 3, "context": 25, "other": 5},
#     "expired_cleaned": 3,
#   }
```

统计逻辑：
1. `SMEMBERS idx:{project_id}` 获取所有键
2. 按前缀分类计数
3. `EXISTS` 逐个验证，收集已过期键
4. 批量 `SREM` 清理过期键

---

## 缓存预热

```python
await cache.warm_context_cache(project_id, chapter_nos=[1,2,3], profiles=["draft"], povs=["third_person"])
# → {"warmed": 5, "total": 9}
```

为未缓存的三元组创建 pending 标记键 `{key}:pending`（TTL 5 分钟），供后台任务识别需延迟加载的上下文。

---

## 清除项目缓存

```python
await cache.clear_project_cache(project_id)  # → 删除的键数量
```

使用 `SCAN` 模式匹配 `*:{project_id}:*` 删除所有键，同时删除索引 `idx:{project_id}`。

---

## 架构要点

- Redis 连接失败不阻塞服务（每个方法内部异常自行处理，`get_*` 返回 `None`）
- 字符串存储 JSON（`json.dumps`），读取时 `json.loads` 反序列化
- 无锁设计：依赖 Redis 单线程原子性，无分布式锁
- 所有写操作同时更新索引 Set，保证索引完整性