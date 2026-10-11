# RulesService - 规则系统

## 概述

`RulesService` 管理 Novel OS 中的创作规则系统，支持项目级规则 (`canon_rules` 表) 和全局规则 (`global_rules` 表)。规则具有生命周期管理、冲突检测、提案-审批流程和优先级排序功能。

**源码路径**: `novel-os-mcp/src/novel_os_mcp/services/rules.py` (946行)

## 注入依赖

```python
RulesService(db: Database)
```

## 一、规则数据结构

### 规则字段 (canon_rules 表)

| 字段 | 类型 | 说明 |
|------|------|------|
| `id` | UUID | 主键 |
| `rule_key` | TEXT | 业务键 (用于 API 调用) |
| `rule_type` | TEXT | 规则类型: canon/character/plot/style/forbidden/reveal_lock/lesson/compliance |
| `scope` | TEXT | 作用域 (兼容旧字段) |
| `scope_type` | TEXT | 新作用域: global/chapter/volume/character/plot-thread/project |
| `scope_ref` | TEXT | 作用域引用值 |
| `scope_config` | JSONB | 作用域配置 |
| `title` | TEXT | 规则标题 |
| `content` | TEXT | 规则内容 |
| `severity` | TEXT | 严重程度: info/warning/error/critical |
| `status` | TEXT | 状态: active/disabled/superseded/archived |
| `version` | INT | 版本号 (每次 upsert 自增) |
| `priority` | INT | 优先级 (越小越优先, 默认 100) |
| `effective_chapter_no` | INT | 生效起始章节 |
| `expire_chapter_no` | INT | 失效章节 |
| `effective_volume_no` | INT | 生效起始卷 |
| `expire_volume_no` | INT | 失效卷 |
| `is_temporary` | BOOL | 是否临时规则 |
| `active_from_event` | TEXT | 事件触发后生效 |
| `expire_on_event` | TEXT | 事件触发后失效 |
| `conflict_policy` | TEXT | 冲突策略: priority/error/warn |
| `supersedes_rule_ids` | TEXT[] | 取代的规则 ID 列表 |
| `blocked_by_rule_ids` | TEXT[] | 被哪些规则阻塞 |
| `metadata` | JSONB | 扩展元数据 (rule_group, genres, scene_types, keywords 等) |
| `is_deleted` | BOOL | 软删除标记 |

## 二、规则查询

### `list_rules()` - 通用规则列表

```python
async def list_rules(
    project_id: str,
    rule_types: list[str] | None,    # 类型过滤
    status: str | None = "active",   # active/disabled/superseded/archived
    chapter_no: int | None = None,   # 章节生命周期过滤
    volume_no: int | None = None,    # 卷生命周期过滤
) -> list[dict[str, Any]]
```

查询条件:
- `is_deleted = false`
- 可选的 status 过滤
- 可选的 rule_type = ANY($types) 过滤
- 章节/卷生命周期过滤 (effective ≤ $ch ≤ expire)
- 排序: `priority ASC, rule_type, rule_key`

### `list_effective_rules()` - 生效规则查询 (最重要)

```python
async def list_effective_rules(
    project_id: str,
    rule_types: list[str] | None = None,
    chapter_no: int | None = None,
    volume_no: int | None = None,
    scope_refs: list[str] | None = None,       # 作用域引用 (如角色名列表)
    scope_types: list[str] | None = None,       # 作用域类型过滤
    active_event_keys: list[str] | None = None, # 活跃事件键
    include_blocked: bool = False,
) -> dict[str, Any]
```

**执行流程**:

```
1. list_rules(status="active", chapter_no, volume_no)
       ↓
2. _filter_rules_for_context()
       ↓
   2.1 _rule_scope_matches() - 作用域匹配
       ├── scope_type=global → 总是匹配
       ├── scope_type=chapter → chapter_no == scope_ref
       ├── scope_type=volume → volume_no == scope_ref
       └── 其他 → scope_ref in scope_refs
       ↓
   2.2 _event_lifecycle_matches() - 事件生命周期
       ├── active_from_event 不在 active_event_keys → 排除
       └── expire_on_event 在 active_event_keys → 排除
       ↓
   2.3 冲突检测 (include_blocked=false 时)
       ├── 收集所有 active_identifiers
       ├── 收集所有 superseded_identifiers
       ├── 规则被 superseded → excluded (reason: "superseded")
       ├── 规则被 blocked → excluded (reason: "blocked")
       └── 其他 → kept
```

**返回值**:

```python
{
    "rules": [...],       # 生效的规则列表
    "excluded": [...],    # 被排除的规则列表 (含 excluded_reason)
    "count": 5,
    "excluded_count": 2,
}
```

### `list_active_global()` - 全局规则

```python
async def list_active_global(
    rule_type: str | None = None,
) -> list[dict[str, Any]]
```

从 `global_rules` 表查询 `status='active'` 的规则。用于 context 组装。

## 三、规则生命周期管理

### `upsert_rule()` - 创建/更新规则

```python
async def upsert_rule(
    project_id: str,
    rule_key: str,
    rule_type: str,
    title: str,
    content: str,
    scope: str = "global",
    severity: str = "warning",
    status: str = "active",
    metadata: dict[str, Any] | None = None,
    change_reason: str | None = None,
    source: str = "manual",
    # 新字段
    scope_type: str = "global",
    scope_ref: str | None = None,
    scope_config: dict[str, Any] | None = None,
    priority: int = 100,
    effective_chapter_no: int | None = None,
    expire_chapter_no: int | None = None,
    effective_volume_no: int | None = None,
    expire_volume_no: int | None = None,
    is_temporary: bool = False,
    active_from_event: str | None = None,
    expire_on_event: str | None = None,
    conflict_policy: str = "priority",
    supersedes_rule_ids: list[str] | None = None,
    blocked_by_rule_ids: list[str] | None = None,
) -> dict[str, Any]
```

**事务流程**:

```
BEGIN TRANSACTION
  ├── FOR UPDATE 锁定 (project_id, rule_key)
  ├── 不存在 → INSERT version=1
  ├── 存在 → UPDATE version=version+1
  └── INSERT INTO rule_versions (版本历史)
       ON CONFLICT (rule_id, version) DO NOTHING
COMMIT
```

版本历史通过 `rule_versions` 表追踪 (project_id, rule_id, version, content, change_reason, source)。

### `delete_rule()` - 软删除

```python
async def delete_rule(
    project_id: str,
    rule_key: str | None = None,
    rule_id: str | None = None,
) -> dict[str, Any]
```

设置 `is_deleted = true`，返回 `{deleted: True, rule_key, title}`。

## 四、冲突检测与解决

### `check_conflicts()` - 冲突检查

```python
async def check_conflicts(
    project_id: str,
    rule_types: list[str] | None = None,
    chapter_no: int | None = None,
    volume_no: int | None = None,
    scope_refs: list[str] | None = None,
    scope_types: list[str] | None = None,
    active_event_keys: list[str] | None = None,
    text: str | None = None,         # 可选: 检查文本中的关键词匹配
) -> dict[str, Any]
```

**冲突类型**:

| 类型 | 严重程度 | 说明 |
|------|---------|------|
| `blocked_by_active_rule` | warning | 规则被另一条活跃规则阻塞 |
| `supersedes_active_rule` | info | 规则取代了一条活跃规则 |
| `same_scope_same_priority` | warning | 同作用域、同生命周期、同优先级的多个不同内容规则 |

**关键词匹配**: 如果提供了 `text` 参数, 检查每条规则的 `metadata.keywords` 是否在文本中出现。

### `resolve_conflict()` - 冲突解决

```python
async def resolve_conflict(
    project_id: str,
    action: str,                      # disable / supersede / block / set_priority
    source_rule_key: str | None = None,
    source_rule_id: str | None = None,
    target_rule_keys: list[str] | None = None,
    target_rule_ids: list[str] | None = None,
    priority: int | None = None,
    reason: str | None = None,
) -> dict[str, Any]
```

**操作说明**:

| action | 效果 | 要求 |
|--------|------|------|
| `disable` | 目标规则 status='disabled' | target_keys 或 target_ids 必填 |
| `supersede` | 目标规则 status='superseded', source 规则 supersedes_rule_ids 追加目标 | source + target 必填 |
| `block` | 目标规则 blocked_by_rule_ids 追加 source | source + target 必填 |
| `set_priority` | source 规则 priority 更新 | source + priority 必填 |

所有操作在事务内执行，使用 FOR UPDATE 锁定 source 规则。

### `bulk_toggle_rules()` - 批量状态切换

```python
async def bulk_toggle_rules(
    project_id: str,
    status: str,                      # active/disabled/superseded/archived
    rule_keys: list[str] | None = None,
    rule_ids: list[str] | None = None,
    rule_types: list[str] | None = None,
    reason: str | None = None,
) -> list[dict[str, Any]]
```

至少提供 rule_keys、rule_ids 或 rule_types 之一。metadata 中记录 last_toggle_reason。

## 五、规则提案系统

### `propose_rule()` - 创建规则提案

```python
async def propose_rule(
    project_id: str,
    proposal: dict[str, Any],  # {source_type, proposal_type, title, content, confidence, agreement}
    username: str,
) -> dict[str, Any]
```

写入 `rule_proposals` 表，关联 users 表获取 author，状态 `proposed`。

### `apply_proposal()` - 审批提案

```python
async def apply_proposal(
    project_id: str,
    proposal_id: str,
    decision: str,       # approve / reject
    reason: str | None,
    username: str,
) -> dict[str, Any]
```

**事务流程**:

```
BEGIN
  ├── FOR UPDATE 锁定 proposal
  ├── decision="reject" → status='rejected', resolved_at=now()
  ├── decision="approve":
  │   ├── proposal_type="create" → INSERT canon_rules
  │   │   (从 agreement.rule 或 agreement.rule_candidate 提取规则数据)
  │   └── proposal_type="update" → UPDATE canon_rules
  │       (target_rule_id 必须存在)
  ├── INSERT rule_versions (version=1 for create, version+1 for update)
  └── UPDATE rule_proposals SET status='approved'
COMMIT
```

### `list_rule_proposals()` - 列出提案

```python
async def list_rule_proposals(
    project_id: str,
    status: str | None = "proposed",
    limit: int = 100,
) -> list[dict[str, Any]]
```

## 六、全局规则管理

### `upsert_global_rule()`

```python
async def upsert_global_rule(
    rule_key: str,
    rule_type: str,
    title: str,
    content: str,
    severity: str = "warning",
    status: str = "active",
    metadata: dict[str, Any] | None = None,
) -> dict[str, Any]
```

`ON CONFLICT (rule_key) DO UPDATE` 语法实现 upsert。

### `delete_global_rule()`

```python
async def delete_global_rule(rule_key: str) -> dict[str, Any]
```

软删除: 设置 `status = 'inactive'`。

### `promote_to_global()` - 项目规则提升为全局

```python
async def promote_to_global(
    project_id: str,
    rule_key: str,
    promoted_by: str = "",
    discussion_id: str = "",
) -> dict[str, Any]
```

1. 从 `canon_rules` 找到项目规则
2. INSERT INTO `global_rules` ON CONFLICT (rule_key) DO UPDATE
3. 记录 `source_project_id`, `promoted_from_rule_id`, `promoted_by`, `discussion_id`
4. 更新项目规则: `promotion_status='promoted'`, `promoted_to_global_id=...`

## 七、效用方法

### `_normalize_rule()` - 规则归一化

确保 `metadata`, `scope_config` 为 JSON 对象，`supersedes_rule_ids`, `blocked_by_rule_ids` 为列表。

### `_rule_scope_matches()` - 作用域匹配

```python
def _rule_scope_matches(
    rule, chapter_no, volume_no, scope_refs, scope_types,
) -> bool:
```

- global → 总是匹配
- 若 scope_types 不为空且 scope_type 不在其中 → 不匹配
- chapter → chapter_no == scope_ref
- volume → volume_no == scope_ref
- 其他 → scope_ref in scope_refs

## 涉及的数据库表

| 表名 | 操作 |
|------|------|
| `canon_rules` | SELECT / INSERT / UPDATE (FOR UPDATE) |
| `rule_versions` | INSERT ON CONFLICT DO NOTHING |
| `rule_proposals` | SELECT / INSERT / UPDATE (FOR UPDATE) |
| `global_rules` | SELECT / INSERT / UPDATE / ... |
| `users` | SELECT (JOIN 获取 user_id) |