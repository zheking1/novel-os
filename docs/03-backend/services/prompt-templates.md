# Prompt Templates 服务 — Prompt 模板托管

**源码**: `novel-os-mcp/src/novel_os_mcp/p7_services.py` (PrompTemplateService 类)

## 概述

Prompt Templates 服务管理项目级 Prompt 模板的全生命周期：CRUD、版本历史、变量渲染、使用统计。

---

## 模板属性

| 字段 | 类型 | 说明 |
|------|------|------|
| `template_key` | str | 业务键 (project-scoped 唯一) |
| `name` | str | 模板名称 |
| `template_content` | str | 模板正文 (含 `{{变量}}` 占位) |
| `description` | str\|None | 描述 |
| `template_type` | str | 类型: `system` / `user` / `analysis` / `generation` |
| `variables` | list[dict] | JSONB，变量定义列表 |
| `genre` | str\|None | 适用题材 |
| `scene` | str\|None | 适用场景 |
| `version` | int | 自动递增的版本号 |
| `is_active` | bool | 是否激活 |
| `usage_count` | int | 使用次数 |
| `last_used_at` | datetime | 最后使用时间 |

## 数据库表

| 表名 | 说明 |
|------|------|
| `prompt_templates` | 主模板表 |
| `prompt_template_versions` | 版本历史表 |
| `prompt_template_usage_logs` | 使用日志表 |

---

## 版本管理

### upsert_template

创建或更新模板（`ON CONFLICT (project_id, template_key)`）。更新时 `version` 自动 +1。

旧版本内容记录在 `prompt_template_versions` 表中。

### get_version_history

查询指定模板的完整版本历史:

- JOIN `prompt_template_versions` 和 `prompt_templates`
- 按 `version DESC` 排序
- 返回每个版本的 `template_content`、`variables`、`change_summary`、`created_by`、`created_at`

---

## 模板渲染

### render_template

渲染模板并记录使用:

1. 获取模板
2. 简单字符串替换: `{{变量名}}` → 变量值
3. UPDATE `usage_count += 1`, `last_used_at = NOW()`
4. 返回 `{template_key, rendered_content, variables_used}`

**注意**: 当前使用简单字符串替换，不支持条件逻辑或循环。

---

## 列表查询

### list_templates

按 `genre`、`scene`、`template_type`、`is_active` 过滤。

### list_templates_by_workspace

跨项目列出模板（用于未选择项目时的视图）:

- JOIN `projects` 表获取 `project_slug` 和 `project_title`
- 按 `workspace_id` 过滤

### delete_template

软删除 (`is_active = false`)，系统模板 (`is_system=true`) 不可删除。MCP 工具版本返回 `{ok, template_key, name}`。

---

## 上下文权重配置 (ContextWeightService)

独立子服务，管理上下文组装的权重配置。

### upsert_config

| 参数 | 类型 | 说明 |
|------|------|------|
| `config_name` | str | 配置名称 |
| `weights` | dict[str→float] | 各上下文模块的权重 |
| `profile` | str | 配置档案 (默认 "default") |
| `max_total_tokens` | int | 最大总 token 数 (默认 8000) |
| `priority_order` | list[str] | 上下文注入优先级 |

唯一键: `(project_id, config_name, profile)`。

### 使用场景

在每次 LLM 调用前，根据 `config_name` + `profile` 的权重配置，按比例分配各上下文模块（角色弧光、因果链、风格、节奏等）的 token 预算。

---

## 工作流引导

1. 创建模板 → `prompt.template.upsert(template_key, template_content, variables=...)`
2. 使用模板 → `prompt.template.render(template_key, variables={...})`
3. 查看历史 → `prompt.template.get_version_history(template_key)`
4. 上下文配置 → `context_weight.upsert_config(config_name, weights, profile)`