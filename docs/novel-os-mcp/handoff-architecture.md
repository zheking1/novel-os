# Novel OS MCP 技术架构交接

更新时间：2026-06-27

## 总体架构

```text
Local AI Skill / Author Tools
  - 保存正文、大纲、细纲、草稿、审查文档
  - 调用用户自己的模型 API
  - 生成摘要、结构化 commit、审查报告
        |
        | MCP tools over HTTP
        v
Novel OS MCP
  - FastMCP service
  - PostgreSQL structured data
  - Qdrant vector search
  - Redis connection reserved for cache/locks
        |
        v
Novel OS Web Console
  - 浏览器维护 MCP 数据
  - 当前为轻量控制台，Phase 3 需要重构为生产后台
```

部署在 NAS：

```text
/opt/novel-os
```

## 代码结构

```text
novel-os-mcp/
  src/novel_os_mcp/
    main.py       MCP tool 注册入口
    services.py   主要业务服务层
    auth.py       token、principal、workspace/project 权限
    db.py         asyncpg 数据库封装
    config.py     环境变量配置
    vector.py     Qdrant 向量接口
    utils.py      JSON/row helpers

novel-os-web/
  server.py       轻量 Python Web server，代理 MCP 调用
  index.html      当前 Web 页面

deploy/nas/
  docker-compose.yml
  docker-compose.app.example.yml
  postgres/init/*.sql
  scripts/*.sh

skills/novel-os-local/
  SKILL.md
  scripts/novel_local.py
  references/workflows.md
```

## 运行时组件

| 组件 | 用途 |
| --- | --- |
| PostgreSQL 16 + pgvector | 结构化数据、规则、状态、审查、摘要、任务 |
| Qdrant | memory/reference 向量检索 |
| Redis | 已配置连接，后续用于缓存、限流、分布式锁 |
| novel-os-mcp | MCP HTTP 服务，端口 8787 |
| novel-os-web | Web 控制台，端口 8790 |
| nginx | 用户已配置反代，配置在 `/home/docker/nginx/conf/conf.d/mcp.conf` |

## 数据库迁移

迁移文件位于：

```text
deploy/nas/postgres/init/
```

当前迁移：

```text
001_extensions.sql
010_core_schema.sql
020_multi_user_workspace.sql
030_seed_default_admin.sql
040_context_packs.sql
050_vector_index.sql
060_commit_audit_columns.sql
070_project_scoped_tokens.sql
080_long_term_service_constraints.sql
090_canon_documents.sql
100_state_snapshot_lifecycle.sql
110_foreshadowing_links.sql
120_rule_scope_lifecycle.sql
130_entity_relationships.sql
140_plot_thread_progress.sql
```

新增表或字段时必须：

- 使用 `CREATE TABLE IF NOT EXISTS` 或 `ALTER TABLE ... ADD COLUMN IF NOT EXISTS`。
- 保持向前兼容，不做破坏性字段删除。
- 给高频查询添加索引。
- 更新 schema 验证或工具冒烟脚本。

## 主要表分类

### 多用户与项目

- `users`
- `workspaces`
- `workspace_members`
- `project_members`
- `api_tokens`
- `local_project_bindings`
- `audit_logs`

### 小说结构

- `projects`
- `volumes`
- `chapters`
- `chapter_plans`
- `chapter_commits`
- `chapter_summaries`

### Canon 与规则

- `canon_documents`
- `canon_document_versions`
- `canon_rules`
- `rule_versions`
- `rule_proposals`

### 状态与关系

- `state_entities`
- `state_snapshots`
- `entity_relationships`
- 旧表：`characters`、`character_states` 仍存在，后续尽量使用新 state 表。

### 剧情与伏笔

- `plot_threads`
- `foreshadowing`
- `events`

### 审查

- `review_jobs`
- `review_reports`
- `revision_tasks`
- `review_council_configs`

### 记忆与向量

- `memory_chunks`
- `vector_index_jobs`
- `context_packs`
- `reference_sources`
- `reference_items`

## 服务层

`services.py` 当前包含多个服务类：

- `WorkspaceService`
- `CanonService`
- `RulesService`
- `ComplianceService`
- `PlotService`
- `MemoryService`
- `ContextService`
- `ReviewService`
- `WorkflowService`
- `SyncService`
- `ReferenceService`

开发新功能时优先延续这个模式：

```text
SQL/schema -> service method -> main.py MCP tool -> docs -> smoke script
```

不要把大量业务逻辑直接写在 `main.py` 的 tool 函数里。

## MCP 工具注册

工具入口在：

```text
novel-os-mcp/src/novel_os_mcp/main.py
```

当前工具大类：

- admin/auth/user/workspace/project
- canon
- rules
- compliance
- volume/plot/foreshadowing
- memory/vector
- state/entity/relationship
- reference
- workflow/context/commit
- sync
- review

工具列表可以通过：

```text
rg -n "@mcp.tool\\(name=" novel-os-mcp/src/novel_os_mcp/main.py
```

## 权限架构

每个 MCP tool 应执行：

```python
await db.connect()
principal = await auth.current_principal()
principal.require("read" or "write" or "admin")
project_id = await auth.resolve_project_id(workspace, project, principal, access="write" when mutating)
```

规则：

- 读工具要求 `read`。
- 写工具要求 `write`。
- 用户/工作区管理要求 `admin`。
- 所有项目数据必须通过 `project_id` 限定。
- token 可绑定 workspace/project，不能越权访问其他项目。

## 上下文包架构

核心入口：

- `workflow.prepare_chapter_context`
- `workflow.prepare_segment_context`
- `workflow.validate_context_pack`
- `workflow.preflight_generation`

上下文包应组装：

- Canon 摘要/硬规则
- 当前有效规则
- 当前人物/实体状态
- 当前剧情线
- 活跃伏笔
- 近期摘要
- 相关 memory chunks
- 审查经验/lesson
- warnings/retrieval audit

重要策略：

- 硬 Canon、当前状态、生效规则优先。
- 历史记忆通过向量检索和摘要压缩进入。
- POV 过滤隐藏伏笔和角色未知秘密。
- 过期状态、废弃伏笔、被 supersede/block 的规则不进上下文。

## 审查架构

流程：

```text
review.start_job
review.submit_model_report x N
review.aggregate
workflow.learn_from_review
rules.apply_proposal（人工审批）
```

审查结果可生成：

- `revision_tasks`
- `rule_proposals`
- state update proposals
- foreshadowing update proposals
- model quality stats

硬底线：

- 审查不能直接改硬 Canon。
- 审查不能直接改正文。
- Critical/Blocking 可阻断下一章。

## 合规架构

合规规则存储：

```text
canon_rules.rule_type = compliance
metadata.category
metadata.patterns
metadata.match_type
metadata.case_sensitive
metadata.hint
```

工具：

- `compliance.rule.upsert`
- `compliance.rule.list`
- `compliance.check`

当前合规检查是确定性规则匹配。复杂价值观/平台尺度判断后续应作为审查模型维度接入。

## 本地文件同步架构

本地文件不上传全文。MCP 接收：

- `path_hint`
- `sha256`
- `word_count`
- `kind`
- `chapter_no`
- `volume_no`
- structured commit

工具：

- `sync.import_local_manifest`
- `sync.import_initial_project_pack`
- `sync.submit_file_hashes`
- `sync.list_conflicts`
- `sync.resolve_conflict`
- `sync.export_project_pack`

冲突必须显式解决：

- keep_mcp
- accept_local
- mark_resolved

## 2000 万字规模设计要点

系统不能依赖“把全书塞进上下文”。必须依赖：

- 分层摘要
- 当前状态快照
- 有效规则过滤
- 伏笔/剧情线状态机
- 向量相关性检索
- 冷热数据归档
- 上下文包 token 预算
- 审查闭环

后续性能方向：

- 增量向量索引
- context pack 缓存
- high-frequency entity cache
- active/recent/archive/deep_archive 生命周期
- 列表分页和筛选
- Redis 锁与限流
