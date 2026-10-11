# Gatekeeper 服务 — 进化安全门禁

**源码**: `novel-os-mcp/src/novel_os_mcp/services/gatekeeper.py` (123 行)

## 概述

Gatekeeper 是 AI 驱动数据进化的安全门禁。在任何自动修改执行前，评估操作风险并决定是否允许自动应用或需要管理员复核。

所有操作变更记录到 `evolution_logs` 表，支持回滚。

## 数据库表

| 表名 | 说明 |
|------|------|
| `evolution_logs` | 进化操作日志 |

---

## 风险等级定义

| 等级 | 标识 | 自动应用 | 说明 |
|------|------|------|------|
| HIGH | `"high"` | false | 高危操作，阻止自动执行，仅管理员可从 Web UI 操作 |
| MEDIUM | `"medium"` | false | 中等风险，需管理员复核 |
| LOW | `"low"` | true | 低风险，自动放行 |

---

## 核心方法：assess

### 函数签名

```python
async def assess(
    project_id, action, target_table, content, source_type,
    source_id="", old_value=None, created_by=""
) -> dict
```

| 参数 | 说明 |
|------|------|
| `action` | `INSERT` / `UPDATE` / `DELETE` |
| `target_table` | 目标数据库表名 |
| `content` | 新内容 dict |
| `source_type` | 来源类型 (`discussion_room` / `single_model` 等) |
| `old_value` | 旧值 (用于回滚) |

### 返回 log_entry

```json
{
  "id": "evolution_logs UUID",
  "source_type": "...",
  "action": "UPDATE",
  "target_table": "...",
  "risk_level": "low|medium|high",
  "risk_reason": "...",
  "auto_applied": true|false
}
```

---

## 规则系统 (_rule_based_assess)

### 表分类

| 分类 | 表名 | 说明 |
|------|------|------|
| **project_tables** | `project_knowledge`, `canon_rules`, `state_entities`, `state_snapshots` | 项目级表 |
| **global_tables** | `global_rules`, `universal_knowledge` | 全局共享表 |
| **dangerous_tables** | `users`, `workspaces`, `projects`, `api_tokens`, `user_sessions`, `system_settings`, `system_evolution_proposals`, `model_profiles` | 危险表（系统级） |

### 规则优先级

1. **DELETE 操作** → **HIGH** — 一律拦截，只允许管理员手动执行
2. **dangerous_tables** → **HIGH** — 禁止自动写入系统表，仅管理员可从 Web UI 操作
3. **危险关键词** → **HIGH** — 内容包含以下关键词之一即拦截:
   - `os.`, `exec(`, `eval(`, `__import__`, `subprocess`
   - `rm -rf`, `drop table`, `truncate`, `shutdown`, `reboot`
4. **global_tables + UPDATE** → **MEDIUM** — 修改已有全局数据需管理员复核
5. **project_tables** → **LOW** — 项目级表无风险，自动放行
6. **global_tables + discussion_room** → **LOW** — 讨论室多模型共识 + 内容无风险标记，自动放行
7. **global_tables (其他来源)** → **MEDIUM** — 单模型建议的全局变更需复核
8. **其他** → **LOW** — 默认无风险

---

## 日志查询 (list_logs)

支持按 `source_type`、`risk_level`、`target_table`、`created_by` 过滤。

---

## 回滚 (rollback)

从 `evolution_logs` 恢复 `old_value`:

| 操作类型 | 回滚行为 |
|------|------|
| `INSERT` / `UPDATE` | `DELETE FROM {table} WHERE id=target_id` |
| `DELETE` | `INSERT INTO {table} (cols) VALUES (old_vals)` |

回滚后记录一条新的 `evolution_logs` 记录（`action='ROLLBACK'`, `risk_level='info'`）。

**限制**: `old_value` 为 None 时无法回滚。

---

## 工作流引导

1. AI 建议任何数据变更 → `assess()` 评估风险
2. LOW → 自动应用
3. MEDIUM/HIGH → 进入管理员复核队列
4. 管理员 → `list_logs()` 查看变更历史
5. 需要恢复 → `rollback()` 回滚到旧值