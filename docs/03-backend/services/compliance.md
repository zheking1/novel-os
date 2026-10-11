# ComplianceService - 合规检查服务

## 概述

`ComplianceService` 负责对 AI 生成的文本内容进行合规性检查。它封装了 `RulesService` 的 compliance 类型规则，提供模式匹配（关键词/正则）、内容审查、违规阻断和修订任务创建功能。

**源码路径**: `novel-os-mcp/src/novel_os_mcp/services/compliance.py` (307行)

## 注入依赖

```python
ComplianceService(db: Database, rules_service: RulesService)
```

## 一、合规规则管理

### `upsert_rule()` - 创建/更新合规规则

```python
async def upsert_rule(
    project_id: str,
    rule_key: str,              # 业务键
    title: str,
    content: str,               # 规则内容 (也可作为默认模式)
    category: str = "custom",   # 分类标签
    patterns: list[str] | None = None,  # 匹配模式列表 (优先级高于 content)
    match_type: str = "keyword",        # keyword / contains / regex
    severity: str = "critical",         # critical / blocking / warning / info
    status: str = "active",
    scope_type: str = "global",
    scope_ref: str | None = None,
    priority: int = 5,
    case_sensitive: bool = False,
    hint: str | None = None,            # 违规后的提示信息
    metadata: dict[str, Any] | None = None,
    username: str | None = None,
) -> dict[str, Any]
```

**实现**: 调用 `RulesService.upsert_rule()`，将 category/patterns/match_type/case_sensitive/hint 包装到 metadata 中，写入 audit_log。

### `list_rules()` - 列出合规规则

```python
async def list_rules(
    project_id: str,
    status: str = "active",
    categories: list[str] | None = None,  # 分类过滤
    chapter_no: int | None = None,
    volume_no: int | None = None,
) -> dict[str, Any]
```

先查 `rule_type='compliance'` 的规则，再按 categories 做内存过滤。

## 二、合规检查 `check()`

### 方法签名

```python
async def check(
    project_id: str,
    text: str | None = None,              # 纯文本输入
    content_items: list[dict[str, Any]] | None = None,  # 结构化输入 [{ref, text, metadata}]
    chapter_no: int | None = None,
    volume_no: int | None = None,
    scope_refs: list[str] | None = None,
    scope_types: list[str] | None = None,
    review_job_id: str | None = None,     # 关联的审核任务
    create_revision_task: bool = False,   # 是否创建修订任务
    username: str | None = None,
) -> dict[str, Any]
```

### 检查算法 (完整流程)

```
Step 1: 标准化输入
  ┌────────────────────────────────────┐
  │ _content_items(text, content_items)    │
  │ 将 text 和 content_items 统一为列表    │
  │ 每项: {ref, text, metadata}           │
  │ 无输入 → raise ValueError             │
  └────────────────────────────────────┘
                ↓
Step 2: 获取生效规则
  ┌────────────────────────────────────┐
  │ RulesService.list_effective_rules(    │
  │   rule_types=["compliance"],           │
  │   chapter_no, volume_no,              │
  │   scope_refs, scope_types)            │
  └────────────────────────────────────┘
                ↓
Step 3: 逐规则检查
  ┌────────────────────────────────────┐
  │ for rule in effective_rules:            │
  │   metadata = rule.metadata             │
  │   match_type = metadata.match_type     │
  │   case_sensitive = metadata.case_sensitive │
  │   patterns = _normalize_patterns(       │
  │     metadata.patterns, rule.content)    │
  │                                        │
  │   for pattern in patterns:             │
  │     for item in content_items:         │
  │       matches = _matches_for_pattern(  │
  │         item.text, pattern,            │
  │         match_type, case_sensitive)    │
  │                                        │
  │       for match in matches:            │
  │         → finding: {                   │
  │             type: "compliance_match",  │
  │             rule_id, rule_key,         │
  │             pattern, matched_text,     │
  │             item_ref, start, end,      │
  │             excerpt (前后24字符窗口),    │
  │             hint (u: metadata.hint)}   │
  └────────────────────────────────────┘
                ↓
Step 4: 阻断判断
  ┌────────────────────────────────────┐
  │ critical_count = sum(1 for f in findings │
  │   if f.severity in {"critical","blocker","blocking"}) │
  │ blocked = critical_count > 0          │
  └────────────────────────────────────┘
                ↓
Step 5: 创建修订任务 (如果有阻断且 create_revision_task)
  ┌────────────────────────────────────┐
  │ 事务内:                               │
  │   ├── 验证 review_job 存在              │
  │   ├── 为每个 critical finding 创建       │
  │   │   revision_task                    │
  │   │   (title, description=hint,        │
  │   │    severity='blocking',            │
  │   │    metadata=整个finding)            │
  │   └── 更新 review_job status='blocked' │
  └────────────────────────────────────┘
                ↓
Step 6: 审计日志 (仅在 blocked 或 create_revision_task 时)
  ┌────────────────────────────────────┐
  │ _audit("compliance.check",            │
  │   payload: {blocked, critical_count,  │
  │   finding_count, checked_items,       │
  │   created_revision_tasks})           │
  └────────────────────────────────────┘
```

### 返回值结构

```python
{
    "ok": True,                  # 未被阻断
    "blocked": False,
    "critical_count": 0,
    "finding_count": 3,
    "findings": [
        {
            "type": "compliance_match",
            "rule_id": "uuid",
            "rule_key": "ban_x",
            "title": "禁止提及XX",
            "severity": "critical",
            "category": "sensitive",
            "match_type": "keyword",
            "pattern": "XX",
            "matched_text": "XX",
            "item_ref": "text",
            "start": 42,
            "end": 44,
            "excerpt": "...前后文...",
            "hint": "请使用YY替代",
        }
    ],
    "checked_items": [{"ref": "text", "chars": 5000}],
    "rules_checked": 12,
    "excluded_rules": [...],
    "created_revision_tasks": 0,
}
```

## 三、模式匹配引擎

### `_matches_for_pattern()` - 核心匹配逻辑

```python
@staticmethod
def _matches_for_pattern(
    text: str,
    pattern: str,
    match_type: str,      # "keyword" / "contains" / "regex"
    case_sensitive: bool,
) -> list[dict[str, int | str]]
```

**三种匹配模式**:

| match_type | 实现 |
|-----------|------|
| `keyword` | 不区分大小写 (默认): `haystack.find(needle.lower())` 循环查找所有出现位置 |
| `contains` | 同 keyword |
| `regex` | `re.finditer(pattern, text, flags)` — 若 case_sensitive=False 则加 re.IGNORECASE |

**注意**: `str.find()` 方法在 `case_sensitive=True` 时使用原文本比较。

### `_normalize_patterns()` - 模式标准化

```python
@staticmethod
def _normalize_patterns(
    patterns: list[str] | None,
    content: str | None,
) -> list[str]
```

优先级: patterns 非空且有效 → 使用 patterns，否则使用 rule.content 作为默认模式。

### `_excerpt()` - 上下文摘录

```python
@staticmethod
def _excerpt(text: str, start: int, end: int, window: int = 24) -> str:
```

提取匹配位置前后各 24 个字符的上下文窗口。

### `_content_items()` - 输入标准化

将 `text` 字符串和 `content_items` 列表统一为标准格式:

```python
[
    {"ref": "text", "text": text},           # 纯文本
    {"ref": "path/to/file.md", "text": "...", "metadata": {}},  # 结构化输入
]
```

ref 优先级: `item.ref` > `item.path_hint` > `item_N`

## 四、审计日志 `_audit()`

```python
async def _audit(
    project_id: str,
    username: str | None,
    action: str,
    resource_type: str,
    resource_id: str | None,
    payload: dict[str, Any],
) -> None
```

写入 `audit_logs` 表，通过 `users` 表 JOIN 获取 user_id。若 username 为 None，user_id 也为 NULL。

## 五、涉及的表与操作

| 表名 | 操作 | 说明 |
|------|------|------|
| `canon_rules` | 通过 RulesService INSERT/UPDATE | 合规规则存储 |
| `audit_logs` | INSERT | 规则变更和检查审计 |
| `review_jobs` | SELECT / UPDATE | 验证审核任务，设置为 blocked |
| `revision_tasks` | INSERT | 为阻断 finding 创建修订任务 |
| `users` | SELECT (JOIN) | 获取 user_id 用于审计 |