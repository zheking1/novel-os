# Novel OS API 接口文档

> 版本：v1.0
> 日期：2026-06-28
> 描述：MCP 工具接口规范，定义 MCP 服务的 API 端点、请求格式、响应格式

---

## 1. 接口概览

### 1.1 访问方式

Novel OS MCP 服务提供两种访问方式：

| 方式 | 说明 | 使用场景 |
|------|------|---------|
| **MCP 协议** | 使用 MCP SDK 调用 | 本地 AI Skill、Web 控制台 |
| **HTTP REST** | 直接 HTTP 请求 | 调试、Web 前端、第三方集成 |

### 1.2 MCP 协议端点

```
http://{host}:{port}/mcp
```

### 1.3 REST API 端点

```
http://{host}:{port}/api/v1/{namespace}/{action}
```

---

## 2. 认证与授权

### 2.1 开发模式（dev）

在 `.env` 中设置 `NOVEL_OS_AUTH_MODE=dev`：

```bash
# 自动创建开发用户，无需认证
NOVEL_OS_DEV_USER=admin
NOVEL_OS_DEV_WORKSPACE=default
NOVEL_OS_DEV_SCOPES=admin,read,write
```

### 2.2 生产模式（prod）

使用 API Token 认证：

```bash
# 请求头
Authorization: Bearer {api_token}
```

获取 Token：

```bash
# 创建 Token
curl -X POST http://localhost:8787/api/v1/auth/tokens \
  -H "Content-Type: application/json" \
  -d '{"name": "my-token", "scopes": ["read", "write"]}'
```

---

## 3. MCP 工具接口

### 3.1 调用格式

**请求**：

```json
{
  "jsonrpc": "2.0",
  "id": "unique-request-id",
  "method": "tools/call",
  "params": {
    "name": "canon.doc.list",
    "arguments": {
      "workspace": "my-workspace",
      "project": "my-novel",
      "doc_types": ["premise", "worldview"]
    }
  }
}
```

**响应**：

```json
{
  "jsonrpc": "2.0",
  "id": "unique-request-id",
  "result": {
    "content": [
      {
        "type": "text",
        "text": "[{\"id\": \"...\", \"title\": \"...\", ...}]"
      }
    ]
  }
}
```

### 3.2 错误格式

```json
{
  "jsonrpc": "2.0",
  "id": "unique-request-id",
  "error": {
    "code": -32602,
    "message": "Invalid params",
    "data": {
      "field": "workspace",
      "reason": "workspace is required"
    }
  }
}
```

---

## 4. 工具清单

### 4.1 身份与权限

| 工具名 | 说明 | 权限 |
|--------|------|------|
| `admin.health` | 健康检查 | read |
| `auth.whoami` | 当前身份 | read |
| `auth.create_api_token` | 创建 Token | admin |
| `auth.list_api_tokens` | 列出 Token | admin |
| `auth.revoke_api_token` | 撤销 Token | admin |
| `user.create` | 创建用户 | admin |
| `user.list` | 列出用户 | admin |
| `workspace.create` | 创建工作区 | admin |
| `workspace.list` | 列出工作区 | admin |
| `workspace.add_member` | 添加工作区成员 | admin |
| `project.create` | 创建项目 | write |
| `project.list` | 列出项目 | read |
| `project.add_member` | 添加项目成员 | admin |
| `project.list_members` | 列出项目成员 | admin |
| `project.register_local_binding` | 注册本地绑定 | write |

### 4.2 全局设定

| 工具名 | 说明 | 权限 |
|--------|------|------|
| `setting.category.list` | 列出分类 | read |
| `setting.category.get` | 获取分类详情 | read |
| `setting.category.upsert` | 创建/更新分类 | write |
| `setting.category.delete` | 删除分类 | write |
| `setting.item.list` | 列出设定项目 | read |
| `setting.item.get` | 获取设定详情 | read |
| `setting.item.upsert` | 创建/更新设定 | write |
| `setting.item.bulk_upsert` | 批量创建/更新 | write |
| `setting.item.delete` | 删除设定 | write |
| `setting.search` | BM25 检索 | read |
| `setting.genre.resolve` | 题材规范化 | read |
| `setting.genre.list` | 列出题材 | read |
| `setting.csv.import` | CSV 导入 | write |
| `setting.csv.export` | CSV 导出 | read |

### 4.3 Canon 文档

| 工具名 | 说明 | 权限 |
|--------|------|------|
| `canon.doc.upsert` | 创建/更新文档 | write |
| `canon.doc.list` | 列出文档 | read |
| `canon.doc.get` | 获取文档 | read |
| `canon.doc.archive` | 归档文档 | write |
| `canon.doc.history` | 版本历史 | read |
| `canon.doc.restore` | 恢复版本 | write |

### 4.4 实体与状态

| 工具名 | 说明 | 权限 |
|--------|------|------|
| `state.entity.upsert` | 创建/更新实体 | write |
| `state.entity.list` | 列出实体 | read |
| `state.entity.get` | 获取实体 | read |
| `state.entity.bulk_patch` | 批量修改 | write |
| `state.snapshot.upsert` | 创建状态快照 | write |
| `state.snapshot.list` | 列出快照 | read |
| `state.relationship.upsert` | 创建/更新关系 | write |
| `state.relationship.list` | 列出关系 | read |

### 4.5 剧情与伏笔

| 工具名 | 说明 | 权限 |
|--------|------|------|
| `volume.upsert` | 创建/更新卷 | write |
| `volume.list` | 列出卷 | read |
| `plot.thread.upsert` | 创建/更新剧情线 | write |
| `plot.thread.list` | 列出剧情线 | read |
| `plot.thread.advance` | 推进剧情线 | write |
| `plot.thread.check_stalled` | 检查停滞 | read |
| `plot.list_foreshadowing` | 列出伏笔 | read |
| `plot.upsert_foreshadowing` | 创建/更新伏笔 | write |
| `foreshadowing.bulk_status_update` | 批量更新伏笔 | write |
| `foreshadowing.check_overdue` | 检查逾期 | read |
| `foreshadowing.link` | 关联伏笔 | write |
| `foreshadowing.payoff` | 回收伏笔 | write |
| `plot.create_chapter_plan` | 创建章节计划 | write |
| `plot.list_chapter_plans` | 列出章节计划 | read |

### 4.6 规则

| 工具名 | 说明 | 权限 |
|--------|------|------|
| `rules.list` | 列出规则 | read |
| `rules.upsert` | 创建/更新规则 | write |
| `rules.list_effective` | 列出有效规则 | read |
| `rules.check_conflict` | 检查冲突 | read |
| `rules.resolve_conflict` | 解决冲突 | write |
| `rules.bulk_toggle` | 批量启停 | write |
| `rules.propose` | 创建提案 | write |
| `rules.list_proposals` | 列出提案 | read |
| `rules.apply_proposal` | 应用提案 | write |

### 4.7 合规审查

| 工具名 | 说明 | 权限 |
|--------|------|------|
| `compliance.rule.upsert` | 创建/更新规则 | write |
| `compliance.rule.list` | 列出规则 | read |
| `compliance.check` | 执行检查 | read/write |

### 4.8 上下文与工作流

| 工具名 | 说明 | 权限 |
|--------|------|------|
| `workflow.prepare_chapter_context` | 准备上下文 | read |
| `workflow.validate_context_pack` | 验证上下文 | read |
| `workflow.preflight_generation` | 预生成检查 | read |
| `workflow.prepare_segment_context` | 分段上下文 | read |
| `workflow.submit_chapter_commit` | 提交章节 | write |
| `workflow.learn_from_review` | 从审查学习 | write |

### 4.9 审查

| 工具名 | 说明 | 权限 |
|--------|------|------|
| `review.start_job` | 启动审查 | write |
| `review.upsert_council_config` | 配置审查 | write |
| `review.list_council_configs` | 列出配置 | read |
| `review.submit_model_report` | 提交报告 | write |
| `review.list_revision_tasks` | 列出修订任务 | read |
| `review.update_revision_task` | 更新任务 | write |
| `review.aggregate` | 聚合报告 | write |
| `review.extract_rule_proposals` | 提取规则提案 | write |
| `review.extract_state_updates` | 提取状态更新 | read |
| `review.extract_foreshadowing_updates` | 提取伏笔更新 | read |
| `review.evaluate_model_quality` | 评估模型 | read |

### 4.10 模型与成本

| 工具名 | 说明 | 权限 |
|--------|------|------|
| `model.profile.upsert` | 创建/更新模型 | write |
| `model.profile.list` | 列出模型 | read |
| `model.route` | 模型路由 | read |
| `model.route_rule.upsert` | 创建/更新路由 | write |
| `model.route_rule.list` | 列出路由 | read |
| `cost.record_usage` | 记录使用 | write |
| `cost.report` | 成本报表 | read |

### 4.11 同步

| 工具名 | 说明 | 权限 |
|--------|------|------|
| `sync.import_local_manifest` | 导入 manifest | write |
| `sync.import_initial_project_pack` | 导入项目包 | write |
| `sync.submit_file_hashes` | 提交哈希 | write |
| `sync.list_conflicts` | 列出冲突 | read |
| `sync.resolve_conflict` | 解决冲突 | write |
| `sync.export_project_pack` | 导出项目包 | read |

### 4.12 记忆

| 工具名 | 说明 | 权限 |
|--------|------|------|
| `memory.search` | 记忆搜索 | read |
| `memory.get_state` | 获取状态 | read |
| `memory.get_recent_summaries` | 获取摘要 | read |
| `memory.rebuild_projection` | 重建投影 | write |
| `memory.pending_vector_chunks` | 待索引块 | read |
| `memory.upsert_vector` | 更新向量 | write |
| `memory.vector_search` | 向量搜索 | read |

### 4.13 参考库

| 工具名 | 说明 | 权限 |
|--------|------|------|
| `reference.source_create` | 创建来源 | write |
| `reference.item_add` | 添加条目 | write |
| `reference.search` | 搜索参考 | read |

---

## 5. 通用请求/响应格式

### 5.1 列表请求

```json
{
  "workspace": "my-workspace",
  "project": "my-novel",
  "limit": 20,
  "offset": 0
}
```

### 5.2 列表响应

```json
{
  "success": true,
  "data": [
    {"id": "uuid-1", "name": "Item 1"},
    {"id": "uuid-2", "name": "Item 2"}
  ],
  "pagination": {
    "total": 100,
    "limit": 20,
    "offset": 0,
    "has_more": true
  }
}
```

### 5.3 详情请求

```json
{
  "workspace": "my-workspace",
  "project": "my-novel",
  "id": "uuid-xxx"
}
```

### 5.4 详情响应

```json
{
  "success": true,
  "data": {
    "id": "uuid-xxx",
    "name": "Item Name",
    "status": "active",
    "created_at": "2026-01-01T00:00:00Z",
    "updated_at": "2026-01-01T00:00:00Z"
  }
}
```

### 5.5 创建/更新请求

```json
{
  "workspace": "my-workspace",
  "project": "my-novel",
  "name": "New Item",
  "content": "Item content...",
  "tags": ["tag1", "tag2"]
}
```

### 5.6 创建/更新响应

```json
{
  "success": true,
  "data": {
    "id": "uuid-new",
    "name": "New Item",
    "created_at": "2026-01-01T00:00:00Z"
  }
}
```

### 5.7 错误响应

```json
{
  "success": false,
  "error": {
    "code": "VALIDATION_ERROR",
    "message": "Validation failed for field 'name'",
    "details": {
      "field": "name",
      "reason": "name is required"
    }
  }
}
```

---

## 6. 常用工具详细接口

### 6.1 setting.search - BM25 检索

**请求**：

```json
{
  "workspace": "my-workspace",
  "query": "主角修炼突破境界",
  "category_id": null,
  "level": null,
  "skill": "write",
  "genre": "玄幻",
  "limit": 20,
  "offset": 0
}
```

**响应**：

```json
{
  "success": true,
  "data": [
    {
      "id": "uuid-1",
      "category_id": "uuid-cat",
      "item_code": "GS-FINGER-001",
      "core_summary": "系统流金手指设定...",
      "level": "knowledge",
      "applicable_skills": ["write"],
      "applicable_genres": ["玄幻", "仙侠"],
      "rank": 8.5,
      "highlight": "...主角<mark>修炼</mark><mark>突破境界</mark>的系统..."
    }
  ],
  "pagination": {
    "total": 15,
    "limit": 20,
    "offset": 0,
    "has_more": false
  }
}
```

### 6.2 setting.genre.resolve - 题材规范化

**请求**：

```json
{
  "input_text": "东方玄幻"
}
```

**响应**：

```json
{
  "success": true,
  "data": [
    {
      "canonical_genre": "玄幻",
      "match_type": "platform_tag",
      "confidence": 0.95
    },
    {
      "canonical_genre": "仙侠",
      "match_type": "partial",
      "confidence": 0.7
    }
  ]
}
```

### 6.3 setting.csv.import - CSV 导入

**请求**：

```json
{
  "workspace": "my-workspace",
  "category_id": "uuid-cat",
  "csv_content": "item_code,keywords,core_summary\nGS-001,主角|升级,主角通过修炼提升境界..."
}
```

**响应**：

```json
{
  "success": true,
  "data": {
    "imported": 50,
    "errors": [
      {"row": 10, "error": "core_summary cannot be empty"}
    ],
    "total": 51
  }
}
```

### 6.4 workflow.prepare_chapter_context - 准备上下文

**请求**：

```json
{
  "workspace": "my-workspace",
  "project": "my-novel",
  "chapter_no": 233,
  "purpose": "draft",
  "focus": ["main_plot", "battle"],
  "budget": {
    "total_tokens": 20000
  },
  "volume_no": 5,
  "pov_mode": "protagonist"
}
```

**响应**：

```json
{
  "success": true,
  "data": {
    "context_pack_id": "cp-xxx",
    "chapter_no": 233,
    "profile": "daily_chapter",
    "pov_mode": "protagonist",
    "token_budget": {
      "total": 20000,
      "used": 15234,
      "remaining": 4766
    },
    "sections": {
      "canon": {"tokens": 3500, "pct": 23},
      "character_states": {"tokens": 2800, "pct": 18},
      "foreshadowings": {"tokens": 1500, "pct": 10},
      "recent_summaries": {"tokens": 4500, "pct": 30},
      "rules": {"tokens": 2200, "pct": 14},
      "review_lessons": {"tokens": 734, "pct": 5}
    },
    "truncated_items": [
      {"type": "foreshadowing", "id": "fs-003", "reason": "exceeded_foreshadowing_budget"}
    ]
  }
}
```

### 6.5 workflow.submit_chapter_commit - 提交章节

**请求**：

```json
{
  "workspace": "my-workspace",
  "project": "my-novel",
  "chapter_no": 233,
  "title": "瑶池秘宝",
  "commit": {
    "commit_type": "final_commit",
    "summary": "王林在瑶池获得秘宝...",
    "events": [...],
    "character_state_changes": [...],
    "foreshadowing_changes": [...],
    "next_chapter_hooks": [...]
  },
  "local_files": [
    {"path": "chapters/v001/ch0233.md", "hash": "abc123..."}
  ]
}
```

**响应**：

```json
{
  "success": true,
  "data": {
    "commit_id": "commit-xxx",
    "chapter_id": "chapter-xxx",
    "chapter_no": 233,
    "created_at": "2026-01-01T12:00:00Z",
    "updates": {
      "entity_states": 5,
      "foreshadowings": 2,
      "summaries": 1
    }
  }
}
```

### 6.6 review.start_job - 启动审查

**请求**：

```json
{
  "workspace": "my-workspace",
  "project": "my-novel",
  "chapter_no": 233,
  "local_files": [
    {"path": "chapters/v001/ch0233.md", "hash": "abc123..."}
  ],
  "dimensions": ["consistency", "pacing", "commercial"]
}
```

**响应**：

```json
{
  "success": true,
  "data": {
    "review_job_id": "review-xxx",
    "status": "pending",
    "models": ["gpt-4", "claude-3", "gemini-pro"],
    "dimensions": ["consistency", "pacing", "commercial"]
  }
}
```

### 6.7 review.submit_model_report - 提交审查报告

**请求**：

```json
{
  "workspace": "my-workspace",
  "project": "my-novel",
  "review_job_id": "review-xxx",
  "model_id": "gpt-4",
  "score": 7.5,
  "summary": "章节整体流畅，但战斗描写偏长",
  "findings": [
    {
      "dimension": "pacing",
      "severity": "warning",
      "description": "战斗描写超过800字",
      "suggestion": "压缩至500字以内"
    }
  ]
}
```

**响应**：

```json
{
  "success": true,
  "data": {
    "report_id": "report-xxx",
    "review_job_id": "review-xxx",
    "model_id": "gpt-4",
    "submitted_at": "2026-01-01T12:05:00Z",
    "pending_reports": 2
  }
}
```

---

## 7. Webhook（可选）

### 7.1 配置

```json
{
  "webhooks": [
    {
      "event": "commit.accepted",
      "url": "https://example.com/webhook",
      "secret": "your-webhook-secret"
    },
    {
      "event": "review.completed",
      "url": "https://example.com/webhook",
      "secret": "your-webhook-secret"
    }
  ]
}
```

### 7.2 事件格式

```json
{
  "event": "commit.accepted",
  "timestamp": "2026-01-01T12:00:00Z",
  "data": {
    "commit_id": "commit-xxx",
    "chapter_no": 233,
    "project_id": "project-xxx"
  }
}
```

---

## 8. 速率限制

| 端点类型 | 限制 | 说明 |
|---------|------|------|
| 读取操作 | 100/分钟 | list, get, search |
| 写入操作 | 50/分钟 | upsert, create, update |
| 上下文生成 | 20/分钟 | prepare_chapter_context |
| 审查提交 | 10/分钟 | review.submit_model_report |

超过限制返回 `429 Too Many Requests`。

---

## 9. SDK 使用示例

### 9.1 Python

```python
from mcp import Client

async def main():
    async with Client("http://localhost:8787/mcp") as client:
        # 列出 Canon 文档
        result = await client.call_tool(
            "canon.doc.list",
            {
                "workspace": "my-workspace",
                "project": "my-novel",
                "doc_types": ["premise", "worldview"]
            }
        )
        docs = json.loads(result.content[0].text)
        print(docs)

        # BM25 检索
        result = await client.call_tool(
            "setting.search",
            {
                "workspace": "my-workspace",
                "query": "主角修炼突破境界",
                "genre": "玄幻"
            }
        )
        items = json.loads(result.content[0].text)
        print(items)
```

### 9.2 TypeScript

```typescript
import { Client } from "@modelcontextprotocol/sdk/client";

async function main() {
  const client = new Client({
    transport: "http",
    url: "http://localhost:8787/mcp",
  });

  // 列出 Canon 文档
  const result = await client.callTool({
    name: "canon.doc.list",
    arguments: {
      workspace: "my-workspace",
      project: "my-novel",
      docTypes: ["premise", "worldview"],
    },
  });
  const docs = JSON.parse(result.content[0].text);
  console.log(docs);
}
```

---

## 10. 参考文档

- [novel-os-requirements.md](novel-os-requirements.md) - 需求规格说明书
- [novel-os-development-plan.md](novel-os-development-plan.md) - 开发计划
- [mcp-implementation-guide.md](mcp-implementation-guide.md) - MCP 实现规范
- [workflow-sequence.md](workflow-sequence.md) - 业务流程时序图
- [deployment-config.md](deployment-config.md) - 部署配置指南
