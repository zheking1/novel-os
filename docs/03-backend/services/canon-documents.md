# CanonService - 权威文档管理服务

## 概述

`CanonService` 管理小说创作中的权威文档 (世界规则、角色设定、力量体系等)。支持版本化更新、内容哈希校验、全文搜索、归档/恢复和完整版本历史追踪。

**源码路径**: `novel-os-mcp/src/novel_os_mcp/services/canon.py` (529行)

## 注入依赖

```python
CanonService(db: Database)
```

## 一、数据类型

### 文档类型 (doc_type)

任意字符串标识文档类别，典型值: `world_rule`, `character_sheet`, `power_system`, `race_setting`, `magic_system`, `timeline`, `geography`

### 状态枚举

| status | 说明 |
|--------|------|
| `draft` | 草稿 |
| `active` | 活跃 (生效中) |
| `deprecated` | 已废弃 |
| `archived` | 已归档 |

| review_status | 说明 |
|--------------|------|
| `pending` | 待审核 |
| `approved` | 已审核通过 |
| `rejected` | 已驳回 |
| `needs_review` | 需要重新审核 |

## 二、文档 CRUD

### `upsert_document()` - 创建/更新权威文档

```python
async def upsert_document(
    project_id: str,
    doc_type: str,           # 文档类型
    key: str,                # 业务键 (唯一标识)
    title: str,
    content: str,
    username: str,           # 操作者
    status: str = "active",
    scope: dict[str, Any] | None = None,          # 作用范围 (JSONB)
    review_status: str = "approved",
    source_type: str = "manual",
    source_id: str | None = None,
    related_rule_ids: list[str] | None = None,     # 关联规则
    metadata: dict[str, Any] | None = None,
    change_reason: str | None = None,              # 变更原因
) -> dict[str, Any]
```

**完整事务流程**:

```
BEGIN TRANSACTION
  ├── 验证 status (draft/active/deprecated/archived)
  ├── 验证 review_status (pending/approved/rejected/needs_review)
  ├── 计算 content_hash = SHA-256(content)
  ├── 通过 users 表获取 user_id
  ├── FOR UPDATE 锁定 (project_id, doc_type, key)
  │
  ├── 文档不存在:
  │   └── INSERT INTO canon_documents (version=1)
  │       - 记录 created_by, updated_by
  │
  ├── 文档已存在:
  │   └── UPDATE canon_documents (version=current_version+1)
  │       - 更新 title, content, content_hash, status, scope, review_status...
  │       - 更新 updated_by
  │
  └── INSERT INTO canon_document_versions (版本历史)
      - (project_id, document_id, version, title, content,
         content_hash, status, scope, review_status, source_type,
         source_id, related_rule_ids, metadata, change_reason, created_by)
      - ON CONFLICT (document_id, version) DO NOTHING
COMMIT
```

### `get_document()` - 获取文档

```python
async def get_document(
    project_id: str,
    document_id: str | None = None,    # 模式1: 按ID查找
    doc_type: str | None = None,       # 模式2: 按 doc_type+key 查找
    key: str | None = None,            # 模式3: 按 key 查找 (返回最新)
) -> dict[str, Any]
```

### `list_documents()` - 列出文档

```python
async def list_documents(
    project_id: str,
    doc_types: list[str] | None = None,   # 类型过滤
    statuses: list[str] | None = None,    # 状态过滤
    review_status: str | None = None,     # 审核状态过滤
    query: str | None = None,             # 搜索关键词
    limit: int = 100,
    offset: int = 0,
) -> list[dict[str, Any]]
```

**搜索策略** (当 query 不为空):

1. `search_vector @@ plainto_tsquery('simple', query)` — PostgreSQL 全文搜索
2. `title ILIKE '%query%'` — 标题模糊匹配 (回退)
3. `key ILIKE '%query%'` — 键模糊匹配 (回退)

排序: 非搜索模式 → `updated_at DESC`；搜索模式 → `ts_rank(...) DESC, updated_at DESC`

动态过滤使用 `ANY($N::text[])` 实现可选参数。

## 三、归档与恢复

### `archive_document()` - 归档

```python
async def archive_document(
    project_id: str,
    username: str,
    document_id: str | None = None,
    doc_type: str | None = None,
    key: str | None = None,
    reason: str | None = None,
) -> dict[str, Any]
```

1. FOR UPDATE 锁定文档
2. version = current_version + 1
3. 更新 status = 'archived', updated_by
4. 插入版本历史记录 (change_reason=reason)

### `restore_document()` - 恢复到指定版本

```python
async def restore_document(
    project_id: str,
    version: int,             # 目标版本号
    username: str,
    document_id: str | None = None,
    doc_type: str | None = None,
    key: str | None = None,
    reason: str | None = None,
) -> dict[str, Any]
```

1. FOR UPDATE 锁定当前文档
2. 从 `canon_document_versions` 获取目标版本
3. 将当前文档的 title/content/content_hash/status/scope/review_status 恢复为目标版本的值
4. version = current_version + 1 (不是目标版本号!)
5. source_type = 'restore'
6. 插入新的版本历史记录

## 四、版本历史

### `list_document_versions()` - 列出版本历史

```python
async def list_document_versions(
    project_id: str,
    document_id: str | None = None,
    doc_type: str | None = None,
    key: str | None = None,
    limit: int = 50,
) -> list[dict[str, Any]]
```

按 `version DESC` 排序，返回每个版本的完整快照。

## 五、内部查询方法

### `_fetch_document()` - 三模式查询

```python
async def _fetch_document(
    project_id: str,
    document_id: str | None = None,
    doc_type: str | None = None,
    key: str | None = None,
) -> dict
```

| 模式 | 查询条件 | 用途 |
|------|---------|------|
| ID模式 | `id = $document_id` | 已知 UUID |
| 类型+键模式 | `doc_type = $dt AND key = $k` | 精确查找 |
| 仅键模式 | `key = $k ORDER BY updated_at DESC LIMIT 1` | 模糊查找 (返回最新) |

### `_fetch_document_for_update()` - 行锁查询

与 `_fetch_document()` 逻辑相同，但添加 `FOR UPDATE` 和后端连接参数 `conn`。

## 六、内容哈希

### `_content_hash()`

```python
@staticmethod
def _content_hash(content: str) -> str:
    return hashlib.sha256(content.encode("utf-8")).hexdigest()
```

用于快速检测内容是否变更，存储于 `content_hash` 字段。

## 涉及的数据库表

| 表名 | 操作 | 说明 |
|------|------|------|
| `canon_documents` | SELECT / INSERT / UPDATE (FOR UPDATE) | 主文档表 |
| `canon_document_versions` | INSERT ON CONFLICT DO NOTHING / SELECT | 版本历史表 |
| `users` | SELECT | 获取 user_id 和 username |