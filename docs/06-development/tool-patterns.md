# MCP 工具开发模式

## 工具命名

```python
# 正确 — 用点分隔
@mcp.tool(name="user.create")

# 错误 — 用下划线
@mcp.tool(name="user_create")
```

函数名用下划线，工具名用点：
```python
@mcp.tool(name="prompt.template.upsert")
async def prompt_template_upsert(workspace: str, project: str, ...):
    ...
```

## 必需参数

```python
# 项目作用域工具必须包含 workspace 和 project
@mcp.tool(name="rules.upsert")
async def rules_upsert(workspace: str, project: str, rule_key: str, ...):

# 全局工具不需要 project
@mcp.tool(name="user.create")
async def user_create(username: str, ...):
```

## 返回值格式

```python
# 始终返回 dict
return {"ok": True, "template_key": "my_template"}

# 错误：抛异常而非返回错误值
raise ValueError("Template not found")
```

### Delete 工具模式
```python
# 错误 — 返回 bool 会导致 "structured_content must be dict or None"
return await service.delete(project_id, key)

# 正确 — 包装为 dict
deleted = await service.delete(project_id, key)
return {"ok": deleted, "key": key}
```

## Workflow Guide 模式

多步骤工具返回 `workflow_guide`：
```python
return {
    "ok": True,
    "session_id": session_id,
    "workflow_guide": {
        "title": "Chapter Generation",
        "current_step": 1,
        "total_steps": 14,
        "steps": [
            {"step_no": 1, "name": "preflight", "tool": "workflow.preflight_generation",
             "next": "next_step", "description": "..."},
            {"step_no": 2, "name": "context", "tool": "workflow.prepare_chapter_context",
             "next": "next_step"},
            {"step_no": 5, "name": "review", "tool": "review.start_job",
             "next": "wait_for_async", "poll": {"tool": "review.list_reports", "interval": 5, "field": "status", "until": "complete", "max_retries": 30}},
        ]
    }
}
```

### step.next 值含义
| next | 行为 |
|------|------|
| `next_step` | 立即执行下一步 |
| `wait_user_confirm` | 暂停等用户回应 |
| `wait_for_async` | 不断轮询 `poll.tool`，直到 `poll.until` |
| `repeat_until_done` | 批量步骤，循环到全部完成 |

### 条件跳转 goto_step
```python
if step has goto_step:
    执行 tool → ok==false → 跳到 goto_step 重试（最多 max_loops 次）
```

## 工具注册

```python
# tools/__init__.py — 导入即注册
from . import auth       # 触发 @mcp.tool 装饰器
from . import canon
from . import plot
# ... 全部 30 个模块
```

## 服务注入

```python
# tools/xxx.py 中通过 deps 获取服务
from ..deps import rules_service, compliance_service, db

@mcp.tool(name="rules.list")
async def rules_list(workspace: str, project: str, ...):
    principal = await get_principal("read")
    project_id = await auth_service.resolve_project_id(workspace, project, principal, "read")
    return await rules_service.list_rules(project_id, ...)
```

## 参数验证

```python
from ..tool_auth import validate_required, validate_length

@mcp.tool(name="canon.doc.upsert")
async def canon_doc_upsert(workspace: str, project: str, doc_type: str, key: str, title: str, content: str, ...):
    validate_required({"doc_type": doc_type, "key": key, "title": title, "content": content})
    validate_length({"title": (1, 200), "content": (1, 50000)}, {"title": title, "content": content})
```