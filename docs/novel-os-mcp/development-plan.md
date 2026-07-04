# Novel OS MCP 开发计划

本文档是后续开发 Novel OS MCP、Web 控制台、本地 AI skill 的执行计划。

它基于 `requirements-and-dev-brief.md`，用于记录：

- 阶段目标
- 任务拆分
- 当前进度
- 依赖关系
- 交付物
- 验收标准
- 后续开发顺序

## 新窗口交接入口

如果在新窗口继续开发，请先阅读：

- [HANDOFF.md](./HANDOFF.md)
- [handoff-current-state.md](./handoff-current-state.md)
- [handoff-requirements-summary.md](./handoff-requirements-summary.md)
- [handoff-architecture.md](./handoff-architecture.md)
- [handoff-development-standards.md](./handoff-development-standards.md)
- [handoff-deployment-runbook.md](./handoff-deployment-runbook.md)
- [handoff-next-tasks.md](./handoff-next-tasks.md)

## 进度状态说明

```text
TODO        未开始
DOING       正在做
DONE        已完成
BLOCKED     阻塞
DEFERRED    推迟到后续阶段
```

## 总体进度

| 阶段 | 名称 | 状态 | 说明 |
| --- | --- | --- | --- |
| Phase 0 | 基础部署与需求基线 | DONE | NAS 基础服务、MCP 初版、Web 登录、需求文档已完成 |
| Phase 1 | P0 数据模型与迁移 | DOING | Canon、状态时效、伏笔、规则范围、实体关系已完成；上下文 Profile 等待实现 |
| Phase 2 | P0 MCP 核心工具 | DOING | Canon、实体/状态/关系、剧情线、卷、伏笔、规则增强、上下文增强、同步、审查学习、合规审查、模型与成本工具已完成（本地代码）；待 NAS 部署验证 |
| Phase 3 | Web 数据维护台 | TODO | 将 Web 从调试台升级为小说数据后台 |
| Phase 4 | 本地 AI Skill 对接 | TODO | 初始化导入、上下文拉取、章节提交、审查提交 |
| Phase 5 | 审查闭环与规则演化 | TODO | 多模型审查、聚合、修订任务、规则提案审批 |
| Phase 6 | 性能、容灾与运维 | TODO | 增量索引、缓存、备份、日志、限流、降级 |
| Phase 7 | P1 创作效率增强 | TODO | 批量工具、商业看板、协作批注、Prompt 模板 |
| Phase 8 | P2 远期扩展 | DEFERRED | 分布式、图谱、模板市场、增强离线 |

## 当前执行指针

更新时间：2026-06-27

当前主线：Phase 1 + Phase 2 的 P0 基础能力。

当前最近任务：

```text
DONE: Phase 2.10 模型与成本工具（本地代码完成，待 NAS 冒烟验证）
DONE: Phase 2.9 合规审查工具
DONE: Phase 1.1 Canon 文档表
DONE: Phase 1.2 Canon 文档版本表
DONE: Phase 1.3 实体关系表
DONE: Phase 1.4 状态时效字段
DONE: Phase 1.5 伏笔关联字段
DONE: Phase 1.6 规则作用域与临时规则字段
DONE: Phase 2.1 Canon 工具
DONE: Phase 2.2 实体工具
DONE: Phase 2.3 剧情线和卷工具
DONE: Phase 2.4 伏笔增强工具
DONE: Phase 2.5 规则增强工具
DONE: Phase 2.6 上下文包增强工具
DONE: Phase 2.7 本地同步工具
DONE: Phase 2.8 审查学习工具
```

当前原则：

- 先补数据模型，再补 MCP 工具，再改 Web 页面，最后接入本地 skill。
- 不把正文、大纲、细纲等人工可编辑文本存进 MCP；MCP 只保存结构化数据、路径、哈希、状态、摘要和索引。
- 每完成一个任务，必须同步更新本文档的状态、完成时间、涉及文件、验证结果和遗留问题。
- Phase 1/2/3/4 是第一条可用生产链路，必须优先于 P1/P2 功能。

## 开发进度日志

| 时间 | 事件 | 状态 | 备注 |
| --- | --- | --- | --- |
| 2026-06-25 | 创建开发计划 | DONE | 根据 `requirements-and-dev-brief.md` 拆分 Phase 0-8 |
| 2026-06-25 | 确认当前开发主线 | DONE | 优先实现 Canon、状态、伏笔、规则范围、上下文包、Web 维护台 |
| 2026-06-25 | Phase 1.1/1.2 Canon 文档与版本表本地实现 | DONE | 新增迁移、服务层、MCP 工具和工具文档 |
| 2026-06-26 | Phase 1.4 状态时效字段本地实现 | DONE | 新增状态生命周期迁移，提交状态保存有效期，上下文包过滤过期状态并提示即将过期状态 |
| 2026-06-26 | Phase 1.5 伏笔关联字段本地实现 | DONE | 新增伏笔父子关联、连锁字段、层级字段、回收截止字段和逾期标记 |
| 2026-06-26 | Phase 1.6 规则作用域与临时规则字段本地实现 | DONE | 新增规则范围、生命周期、临时规则、优先级和冲突策略字段，上下文包按章节过滤有效规则 |
| 2026-06-26 | Phase 2.1 Canon 工具本地实现 | DONE | `canon.doc.upsert/list/get/archive/history/restore` 已注册并通过编译 |
| 2026-06-26 | Phase 1.1/1.2/1.4/1.5/1.6/2.1 NAS 部署验证 | DONE | SQL 迁移已执行，MCP 容器已重建启动，Phase 1 schema 验证通过 |
| 2026-06-26 | Phase 1.3 实体关系表完成 | DONE | 新增实体生命周期字段、`entity_relationships` 表和验证脚本，NAS schema 验证通过 |
| 2026-06-26 | Phase 2.2 实体工具完成 | DONE | `state.entity/*`、`state.snapshot/*`、`state.relationship/*` 已注册，NAS service 冒烟测试通过 |
| 2026-06-26 | 修复历史 `projects` schema 兼容问题 | DONE | 补齐 `slug/title/status/id default`，迁移重放不再报 `projects.slug` 错误，项目创建冒烟测试通过 |
| 2026-06-26 | Phase 2.3 剧情线和卷工具完成 | DONE | `volume.*`、`plot.thread.*` 已注册，NAS schema 与 service 冒烟测试通过 |
| 2026-06-26 | Phase 2.4 伏笔增强工具完成 | DONE | `foreshadowing.bulk_status_update/check_overdue/link/payoff` 已注册，NAS service 冒烟测试通过 |
| 2026-06-26 | Phase 2.5 规则增强工具本地实现 | DONE | `rules.list_effective/check_conflict/bulk_toggle/resolve_conflict` 已注册，支持范围、生命周期、临时规则、显式阻塞/覆盖和批量启停 |
| 2026-06-27 | Phase 2.6 上下文包增强工具本地实现 | DONE | `workflow.validate_context_pack/preflight_generation/prepare_segment_context` 已注册，`prepare_chapter_context` 增强规则有效列表、POV 伏笔过滤、状态生命周期过滤和预检 |
| 2026-06-27 | Phase 2.5/2.6 NAS 部署验证 | DONE | MCP 容器已重建；state、plot、foreshadowing、rules、context 五组 Phase 2 冒烟测试全部通过 |
| 2026-06-27 | Phase 2.7 本地同步工具完成 | DONE | `sync.import_local_manifest/import_initial_project_pack/submit_file_hashes/list_conflicts/resolve_conflict/export_project_pack` 已注册；本地编译通过，NAS 新增 sync 冒烟与 Phase 2 组合冒烟全部通过 |
| 2026-06-27 | Phase 2.8 审查学习工具完成 | DONE | `review.extract_rule_proposals/extract_state_updates/extract_foreshadowing_updates/evaluate_model_quality` 与 `workflow.learn_from_review` 已注册；审查可生成修订任务、规则提案、状态/伏笔建议，并用 critical 阻断下一章；NAS 新增 review learning 冒烟与 Phase 2 组合冒烟全部通过 |
| 2026-06-27 | Phase 2.9 合规审查工具完成 | DONE | `compliance.rule.upsert/list` 与 `compliance.check` 已注册；合规规则复用可演化规则表，critical/blocking 命中可阻断生成、创建 blocking 修订任务并写入审计日志；NAS 新增 compliance 冒烟与 Phase 2 组合冒烟全部通过 |
| 2026-06-27 | Phase 2.10 模型与成本工具完成 | DONE | `model.profile.upsert/list`、`model.route`、`model.route_rule.upsert/list`、`cost.record_usage/report` 已注册；新增 model_profiles/model_route_rules/model_usage_records 三张表；支持模型分层、路由规则、fallback、成本估算与多维度统计；NAS 冒烟测试通过 |
| 2026-06-27 | Phase 3 Web 数据维护台开始 | DOING | 新增项目选择器下拉菜单、导航面板结构、Canon 文档 CRUD 面板（upsert/list/get/archive）；Web 已部署测试 |
| 2026-06-27 | Phase 3.2 Web 规则面板 | DONE | 规则列表、有效规则、冲突检查、提案管理（列表/批准/拒绝）、Compliance 规则列表与文本检查；Web 已部署 |
| 2026-06-28 | Phase 3.3 Web 实体面板 | DONE | 实体列表与详情（增删改查、筛选、搜索）、状态快照（添加/列表）、关系管理（添加/列表、态度、强度、可见性）；Web 已部署到 NAS |
| 2026-06-27 | Phase 3 Web 伏笔面板 | TODO | 伏笔看板、状态批量更新 |
| 2026-06-27 | Phase 3 Web 剧情面板 | TODO | 卷管理、剧情线、章节计划 |
| 2026-06-27 | Phase 3 Web 审查中心 | TODO | 审查任务、修订任务、规则提案 |
| 2026-06-27 | Phase 3 Web 模型面板 | TODO | 模型配置、成本看板 |

## 阶段门禁

Phase 1 完成前，不进入大规模 Web 改造：

- Canon 文档、实体关系、状态时效、伏笔关联、规则作用域、上下文 Profile 至少完成 P0 表结构。
- 所有迁移必须可重复执行或有明确版本号。
- 不允许破坏已有工作区、项目、规则、伏笔、审查任务数据。

Phase 2 完成前，不进入本地 skill 深度自动化：

- MCP 必须提供稳定的 CRUD、上下文生成、提交、审查、同步工具。
- 工具返回必须结构化，错误必须可读，不能只返回 Python 异常栈。
- 每个工具必须验证 workspace/project 权限和 project 数据隔离。

Phase 3 完成前，不宣布 Web 控制台可生产使用：

- Web 必须支持项目选择、设定集维护、实体维护、伏笔维护、规则维护、审查中心、上下文预览。
- Web 不负责小说初始化，只负责维护 MCP 中的数据。
- 中英文切换不能影响功能可用性。

Phase 4 完成前，不宣布本地写作闭环完成：

- 本地 skill 必须能导入初始化设定、拉取上下文包、提交章节 commit、提交审查报告。
- draft/final 必须隔离，草稿不能污染正式状态。
- 本地文件与 MCP 必须通过路径、哈希、commit 状态建立同步契约。

Phase 5 完成前，不宣布规则自动进化闭环完成：

- 多模型审查报告必须能聚合。
- Critical/Warning/Info 必须分级处理。
- 审查只能生成修订任务、状态提案、规则提案，不能自动改写硬 Canon。
- 规则提案必须经过权限校验和审批流程。

## Phase 0：基础部署与需求基线

目标：完成 NAS 基础部署、MCP 初版、Web 初版、需求文档。

状态：DONE

### 已完成

| 任务 | 状态 | 交付物 |
| --- | --- | --- |
| NAS Docker Compose 基础目录 | DONE | `/opt/novel-os` |
| PostgreSQL + pgvector | DONE | `novel-postgres` |
| Qdrant | DONE | `novel-qdrant` |
| Redis 连接配置 | DONE | 复用已有 Redis |
| Adminer 配置 | DONE | `adminer:latest` |
| novel-os-mcp 初版 | DONE | `novel-os-mcp` |
| novel-os-web 初版 | DONE | `novel-os-web` |
| Web 登录/账号/token 配置 | DONE | `/api/setup`、`/api/login`、`/api/account` |
| Web 中英文切换 | DONE | `index.html` i18n |
| Web token 失效修复 | DONE | 重新绑定 Web admin token |
| 本地 skill 初版 | DONE | `skills/novel-os-local` |
| 需求与开发简报 | DONE | `requirements-and-dev-brief.md` |

### 当前已有 MCP 工具

| 模块 | 工具 |
| --- | --- |
| admin | `admin.health` |
| auth | `auth.whoami`、`auth.create_api_token`、`auth.list_api_tokens`、`auth.revoke_api_token` |
| user | `user.create`、`user.list` |
| workspace | `workspace.create`、`workspace.list`、`workspace.add_member` |
| project | `project.create`、`project.list`、`project.add_member`、`project.list_members`、`project.register_local_binding` |
| canon | `canon.doc.upsert`、`canon.doc.list`、`canon.doc.get`、`canon.doc.archive`、`canon.doc.history`、`canon.doc.restore` |
| rules | `rules.list`、`rules.upsert`、`rules.propose`、`rules.list_proposals`、`rules.apply_proposal` |
| plot | `plot.upsert_foreshadowing`、`plot.list_foreshadowing`、`plot.create_chapter_plan`、`plot.list_chapter_plans` |
| memory | `memory.search`、`memory.get_state`、`memory.get_recent_summaries`、`memory.rebuild_projection`、`memory.pending_vector_chunks`、`memory.upsert_vector`、`memory.vector_search` |
| reference | `reference.source_create`、`reference.item_add`、`reference.search` |
| workflow | `workflow.prepare_chapter_context`、`workflow.submit_chapter_commit` |
| review | `review.start_job`、`review.upsert_council_config`、`review.list_council_configs`、`review.submit_model_report`、`review.aggregate`、`review.list_revision_tasks`、`review.update_revision_task` |

## Phase 1：P0 数据模型与迁移

目标：补齐能支撑小说长期数据维护的表结构。

状态：DONE

### 1.1 Canon 文档表

状态：DONE

新增表建议：`canon_documents`

字段：

```text
id
project_id
doc_type
key
title
content
content_hash
status
version
scope
review_status
source_type
source_id
related_rule_ids
metadata
created_by
updated_by
created_at
updated_at
```

交付物：

- 新增迁移 SQL
- MCP Service 方法
- MCP 工具：
  - `canon.doc.upsert`
  - `canon.doc.list`
  - `canon.doc.get`
  - `canon.doc.archive`
  - `canon.doc.history`
  - `canon.doc.restore`

验收标准：

- 同一项目内 `doc_type + key` 唯一。
- 修改 active Canon 自动生成版本。
- Web 可读取列表和详情。
- 可按类型、状态、关键字筛选。

完成时间：2026-06-25

涉及文件：

- `deploy/nas/postgres/init/090_canon_documents.sql`
- `novel-os-mcp/src/novel_os_mcp/services.py`
- `novel-os-mcp/src/novel_os_mcp/main.py`
- `novel-os-mcp/docs/TOOLS.md`
- `docs/novel-os-mcp/tool-schema.md`

验证结果：

- 本地 `python -m compileall novel-os-mcp\src` 通过。
- 已实现 `canon.doc.upsert/list/get/archive/history/restore`。
- NAS 已执行 `scripts/apply-schema.sh`。
- NAS 已重建并启动 `novel-os-mcp` 容器。
- `verify-phase1-schema.sh` 验证 Canon 表、状态字段、伏笔字段、规则字段均已存在。

遗留问题：

- 待 Web 设定集页面接入。

### 1.2 Canon 文档版本表

状态：DONE

新增表建议：`canon_document_versions`

用途：

- 保存 Canon 历史版本。
- 支持回滚。
- 支持差异对比。

验收标准：

- 每次更新 active 文档生成版本记录。
- 记录修改人、修改原因、来源。

完成时间：2026-06-25

涉及文件：

- `deploy/nas/postgres/init/090_canon_documents.sql`
- `novel-os-mcp/src/novel_os_mcp/services.py`

验证结果：

- upsert、archive、restore 均会写入 `canon_document_versions`。
- NAS 已执行 `scripts/apply-schema.sh`。
- `verify-phase1-schema.sh` 验证 `canon_document_versions` 表存在。

遗留问题：

- 待 Web 设定集页面接入版本历史和恢复入口。

### 1.3 实体关系表

状态：DONE

新增表建议：`entity_relationships`

字段：

```text
source_entity_id
target_entity_id
relation_type
attitude
intensity
known_by_source
known_by_target
known_by_reader
status
source_chapter
source_commit_id
metadata
```

实际同步扩展：

- `state_entities` 增加 `lifecycle_status`、`importance`、`tags`、首末出场章节/卷、来源和 `metadata`。
- `entity_relationships` 增加可见性字段、状态字段、来源章节/提交和元数据。

验收标准：

- 支持人物、势力、地点、道具之间的关系。
- 不自动把推断写成硬事实。
- MCP 已能维护关系；Web 查看和编辑关系在 Phase 3 接入。

完成时间：2026-06-26

涉及文件：

- `deploy/nas/postgres/init/130_entity_relationships.sql`
- `deploy/nas/scripts/verify-phase2-state-schema.sh`
- `deploy/nas/scripts/verify-phase2-state-tools.sh`
- `novel-os-mcp/src/novel_os_mcp/services.py`
- `novel-os-mcp/src/novel_os_mcp/main.py`
- `novel-os-mcp/docs/TOOLS.md`
- `docs/novel-os-mcp/tool-schema.md`

验证结果：

- 本地 `python -m compileall novel-os-mcp\src` 通过。
- NAS 已执行 `scripts/apply-schema.sh`。
- `verify-phase2-state-schema.sh` 验证 `entity_relationships` 表和 `state_entities` 生命周期字段存在。
- `verify-phase2-state-tools.sh` 通过实体、快照、关系 service 级冒烟测试。

遗留问题：

- 待 Phase 3 Web 实体页面接入关系编辑。
- 待后续实现退场实体自动降级定时任务。

### 1.4 状态时效字段

状态：DONE

需要扩展：`state_snapshots`

新增字段：

```text
effective_chapter
expire_chapter
effective_volume
expire_volume
duration_type
expires_on_event
confidence
source_type
source_id
change_reason
```

验收标准：

- 过期状态默认不进入上下文包。
- 即将过期状态可提示。
- 状态来源可追踪。

完成时间：2026-06-26

涉及文件：

- `deploy/nas/postgres/init/100_state_snapshot_lifecycle.sql`
- `novel-os-mcp/src/novel_os_mcp/services.py`

验证结果：

- 本地 `python -m compileall novel-os-mcp\src` 通过。
- `memory.rebuild_projection` 写入状态生命周期字段。
- `workflow.prepare_chapter_context` 按当前章节过滤过期状态。
- 3 章内将过期状态会写入上下文包 `warnings`。
- NAS 已执行 `scripts/apply-schema.sh`。
- `verify-phase1-schema.sh` 验证状态生命周期字段存在。

遗留问题：

- 待 Web 实体页面展示过期状态提醒。

### 1.5 伏笔关联字段

状态：DONE

需要扩展：`foreshadowing`

新增字段：

```text
parent_foreshadowing_id
related_foreshadowing_ids
trigger_on_payoff_ids
blocks_payoff_until_ids
layer
must_payoff
payoff_deadline_chapter
payoff_deadline_volume
overdue_policy
```

验收标准：

- 支持父子伏笔。
- 支持明线/暗线/幕后伏笔。
- 支持逾期告警。

完成时间：2026-06-26

涉及文件：

- `deploy/nas/postgres/init/110_foreshadowing_links.sql`
- `novel-os-mcp/src/novel_os_mcp/services.py`
- `novel-os-mcp/src/novel_os_mcp/main.py`

验证结果：

- 本地 `python -m compileall novel-os-mcp\src` 通过。
- `plot.upsert_foreshadowing` 支持父子伏笔、关联伏笔、触发关系、阻塞关系、层级、强制回收和回收截止章节。
- `plot.list_foreshadowing` 支持层级过滤和按当前章节返回 `is_overdue`。
- NAS 已执行 `scripts/apply-schema.sh`。
- `verify-phase1-schema.sh` 验证伏笔关联字段存在。

遗留问题：

- 待 Phase 2.4 补齐伏笔批量状态、逾期检查、回收工具。
- 待 Phase 3 Web 伏笔看板接入。

### 1.6 规则作用域与临时规则字段

状态：DONE

需要扩展：`canon_rules`

新增字段：

```text
scope_type
scope_ref
effective_chapter_no
expire_chapter_no
effective_volume_no
expire_volume_no
active_from_event
expire_on_event
priority
is_temporary
conflict_policy
scope_config
supersedes_rule_ids
blocked_by_rule_ids
```

验收标准：

- 支持全局、分卷、剧情线、章节、角色、势力规则。
- 支持临时规则。
- 支持规则冲突检测。

完成时间：2026-06-26

涉及文件：

- `deploy/nas/postgres/init/120_rule_scope_lifecycle.sql`
- `novel-os-mcp/src/novel_os_mcp/services.py`
- `novel-os-mcp/src/novel_os_mcp/main.py`

验证结果：

- 本地 `python -m compileall novel-os-mcp\src` 通过。
- `rules.upsert` 支持规则范围、优先级、生命周期、临时规则、事件触发和冲突策略字段。
- `rules.list` 支持按章节/分卷过滤当前有效规则。
- `workflow.prepare_chapter_context` 已传入当前章节号，只加载当前章节有效规则。
- NAS 已执行 `scripts/apply-schema.sh`。
- `verify-phase1-schema.sh` 验证规则作用域与生命周期字段存在。

遗留问题：

- 待补齐规则冲突检测工具和 Web 冲突提示。

### 1.7 上下文 Profile 表

状态：TODO

新增表建议：`context_profiles`

用途：

- 保存不同章节类型/审查类型的上下文预算。
- 支持项目/分卷/剧情线覆盖。

验收标准：

- 能配置 `daily_chapter`、`battle_chapter`、`payoff_chapter` 等 profile。
- 上下文包生成时可指定 profile。

### 1.8 读者期待库

状态：TODO

新增表建议：`expectation_hooks`

用途：

- 存储长线悬念、未兑现承诺、读者期待。
- 支撑商业节奏审查。

验收标准：

- 可创建、关闭、标记逾期。
- 可进入上下文包。

### 1.9 Prompt 模板表

状态：TODO

新增表建议：`prompt_templates`

验收标准：

- 支持模板版本。
- 支持模板变量。
- 支持按项目/题材/分卷生效。

### 1.10 日志与任务表增强

状态：TODO

需要补齐：

- 全链路日志表或扩展 `audit_logs`
- 模型调用统计表
- token 成本统计表
- 同步任务/失败重试队列表
- 批量操作日志表

验收标准：

- 每次重要操作可追踪。
- Web 可按项目、时间、操作类型查询。

## Phase 2：P0 MCP 核心工具

目标：实现 Web 和本地 skill 都能调用的数据维护工具。

状态：TODO

### 2.1 Canon 工具

状态：DONE

工具：

```text
canon.doc.upsert
canon.doc.list
canon.doc.get
canon.doc.archive
canon.doc.history
canon.doc.restore
```

验收标准：

- 可维护基础设定、世界观、力量体系、金手指、商业定位、禁忌等。
- 版本正确。
- 权限正确。

完成时间：2026-06-26

涉及文件：

- `novel-os-mcp/src/novel_os_mcp/main.py`
- `novel-os-mcp/src/novel_os_mcp/services.py`
- `novel-os-mcp/docs/TOOLS.md`
- `docs/novel-os-mcp/tool-schema.md`

验证结果：

- 本地 `python -m compileall novel-os-mcp\src` 通过。
- 读工具使用 `read` 权限，写/归档/恢复工具使用 `write` 权限。
- 所有 Canon 工具通过 `auth.resolve_project_id` 校验 workspace/project 隔离。
- NAS 已重建并启动 `novel-os-mcp` 容器。

遗留问题：

- 待 Web 设定集页面接入。

### 2.2 实体工具

状态：DONE

工具：

```text
state.entity.upsert
state.entity.list
state.entity.get
state.entity.bulk_patch
state.relationship.upsert
state.relationship.list
state.snapshot.upsert
state.snapshot.list
```

验收标准：

- 支持人物、势力、地点、道具。
- 支持状态过期。
- 支持批量修改。

完成时间：2026-06-26

涉及文件：

- `deploy/nas/postgres/init/130_entity_relationships.sql`
- `deploy/nas/scripts/verify-phase2-state-schema.sh`
- `deploy/nas/scripts/verify-phase2-state-tools.sh`
- `novel-os-mcp/src/novel_os_mcp/services.py`
- `novel-os-mcp/src/novel_os_mcp/main.py`
- `novel-os-mcp/docs/TOOLS.md`
- `docs/novel-os-mcp/tool-schema.md`

验证结果：

- 本地 `python -m compileall novel-os-mcp\src` 通过。
- NAS 已重建并启动 `novel-os-mcp` 容器。
- `verify-phase2-state-schema.sh` 验证实体生命周期字段和关系表存在。
- `verify-phase2-state-tools.sh` 通过 service 级冒烟测试：
  - 临时项目创建。
  - `state.entity` 等价 service upsert/list。
  - `state.snapshot` 等价 service upsert/list。
  - `state.relationship` 等价 service upsert/list。
  - 测试结束删除临时项目。

遗留问题：

- 待 Phase 3 Web 实体页面接入。
- 待实现退场实体自动降级任务。
- NAS 历史 `projects` 表存在旧 schema 问题：`020_multi_user_workspace.sql` 重放时仍提示 `column "slug" named in key does not exist`；本次新增迁移不受影响，但后续应单独清理。

### 2.3 剧情线和卷工具

状态：DONE

工具：

```text
volume.upsert
volume.list
plot.thread.upsert
plot.thread.list
plot.thread.advance
plot.thread.check_stalled
```

验收标准：

- 可维护主线、支线、情感线、对抗线。
- 可检测长时间未推进剧情线。

完成时间：2026-06-26

涉及文件：

- `deploy/nas/postgres/init/020_multi_user_workspace.sql`
- `deploy/nas/postgres/init/140_plot_thread_progress.sql`
- `deploy/nas/scripts/verify-phase2-plot-schema.sh`
- `deploy/nas/scripts/verify-phase2-plot-tools.sh`
- `novel-os-mcp/src/novel_os_mcp/services.py`
- `novel-os-mcp/src/novel_os_mcp/main.py`
- `novel-os-mcp/docs/TOOLS.md`
- `docs/novel-os-mcp/tool-schema.md`

验证结果：

- 本地 `python -m compileall novel-os-mcp\src` 通过。
- NAS `scripts/apply-schema.sh` 重放通过，历史 `projects.slug` 错误已消失。
- 工作区/项目创建 service 冒烟测试通过。
- `verify-phase2-plot-schema.sh` 验证 `volumes`、`plot_threads` 进度字段存在。
- `verify-phase2-plot-tools.sh` 通过卷、剧情线创建、推进、停滞检测 service 级冒烟测试。

遗留问题：

- 待 Phase 3 Web 剧情线/卷页面接入。
- Phase 2.6 已加入上下文预检框架；当前卷已进入上下文预算，剧情线停滞注入待后续剧情线预检增强。

### 2.4 伏笔增强工具

状态：DONE

工具：

```text
foreshadowing.bulk_status_update
foreshadowing.check_overdue
foreshadowing.link
foreshadowing.payoff
```

验收标准：

- 支持逾期告警。
- 支持关联伏笔。
- 支持批量处理。

完成时间：2026-06-26

涉及文件：

- `novel-os-mcp/src/novel_os_mcp/services.py`
- `novel-os-mcp/src/novel_os_mcp/main.py`
- `novel-os-mcp/docs/TOOLS.md`
- `docs/novel-os-mcp/tool-schema.md`
- `deploy/nas/scripts/verify-phase2-foreshadowing-tools.sh`

验证结果：

- 本地 `python -m compileall novel-os-mcp\src` 通过。
- NAS 已重建并启动 `novel-os-mcp` 容器。
- `verify-phase2-foreshadowing-tools.sh` 通过 service 级冒烟测试：
  - 创建伏笔。
  - 建立关联和 payoff 触发关系。
  - 检查逾期伏笔。
  - 回收伏笔并触发关联伏笔。
  - 批量归档伏笔。

遗留问题：

- 待 Phase 3 Web 伏笔看板接入。
- Phase 2.6 已让上下文过滤 `paid_off/abandoned/archived` 伏笔并注入逾期告警。

### 2.5 规则增强工具

状态：DONE

工具：

```text
rules.check_conflict
rules.bulk_toggle
rules.resolve_conflict
rules.list_effective
```

验收标准：

- 已能计算当前章节/当前角色/当前分卷有效规则。
- 已能检测显式阻塞、显式覆盖、同范围同优先级结构冲突。
- 已能处理章节/分卷生命周期、事件激活/失效、临时规则。
- 已能批量启停规则、设置优先级、执行 supersede/block/disable 解决动作。

涉及文件：

```text
novel-os-mcp/src/novel_os_mcp/services.py
novel-os-mcp/src/novel_os_mcp/main.py
deploy/nas/scripts/verify-phase2-rules-tools.sh
novel-os-mcp/docs/TOOLS.md
docs/novel-os-mcp/tool-schema.md
```

验证：

```text
python -m compileall novel-os-mcp/src
sh scripts/verify-phase2-rules-tools.sh
```

遗留问题：

- 深度语义审查仍由 Phase 5 多模型审查系统负责；当前 `rules.check_conflict` 只做结构冲突和 `metadata.keywords` 轻量命中。
- Phase 2.6 已让上下文包调用 `rules.list_effective`，避免过期、被阻塞、被覆盖的规则进入生成上下文。

### 2.6 上下文包增强工具

状态：DONE

工具：

```text
workflow.prepare_chapter_context
workflow.validate_context_pack
workflow.preflight_generation
workflow.prepare_segment_context
```

已增强：

- `workflow.prepare_chapter_context` 支持 `volume_no`、`scope_refs`、`scope_types`、`active_event_keys`、`pov_mode`。
- 规则通过 `rules.list_effective` 注入，显式 superseded/blocked 规则进入 warnings 而不进入有效规则。
- 状态按章节/分卷有效期过滤，并提示即将过期状态。
- 伏笔默认排除 `paid_off/abandoned/archived`，并按 POV 过滤隐藏层级。
- `workflow.validate_context_pack` 检查必需 section、token 预算、核心规则和阻断式逾期伏笔。
- `workflow.preflight_generation` 在生成前创建上下文包并返回 `can_generate`。
- `workflow.prepare_segment_context` 支持 opening/middle/ending 分段上下文。
- retrieval audit 记录规则、状态、摘要、伏笔、记忆来源计数。

验收标准：

- POV 过滤不加载隐藏伏笔。
- Critical 规则可进入上下文并被校验。
- 过期状态不进入上下文。
- 超预算时返回 validation error，后续 Phase 6 再做自动压缩。

涉及文件：

```text
novel-os-mcp/src/novel_os_mcp/services.py
novel-os-mcp/src/novel_os_mcp/main.py
deploy/nas/scripts/verify-phase2-context-tools.sh
novel-os-mcp/docs/TOOLS.md
docs/novel-os-mcp/tool-schema.md
```

验证：

```text
python -m compileall novel-os-mcp/src
sh scripts/verify-phase2-context-tools.sh
```

遗留问题：

- 上下文自动去重和超预算自动压缩仍需在 Phase 6 性能/缓存/压缩阶段增强。
- 检索评分阈值需要等向量检索权重和 Qdrant 召回策略进一步稳定后实现。

### 2.7 本地同步工具

状态：DONE

工具：

```text
sync.import_local_manifest
sync.import_initial_project_pack
sync.submit_file_hashes
sync.list_conflicts
sync.resolve_conflict
sync.export_project_pack
```

验收标准：

- 支持本地初始化数据导入。DONE
- 支持哈希变化提示。DONE
- 支持冲突解决。DONE
- 支持项目 JSON 导出。DONE

能力说明：

- MCP 不保存正文、大纲、细纲等长篇可编辑文本，只保存本地路径提示、hash、字数和结构化项目数据。
- `sync.submit_file_hashes` 默认发现冲突后不覆盖 MCP 记录，需要显式解决或 `accept_conflicts=true`。
- `sync.resolve_conflict(action="accept_local")` 可接受本地章节 hash，也可在提供本地 Canon 内容时更新 Canon 文档。
- `sync.export_project_pack` 导出 Canon、规则、实体、当前状态快照、伏笔、卷、剧情线和可选本地绑定信息。

涉及文件：

```text
novel-os-mcp/src/novel_os_mcp/services.py
novel-os-mcp/src/novel_os_mcp/main.py
deploy/nas/scripts/verify-phase2-sync-tools.sh
novel-os-mcp/docs/TOOLS.md
docs/novel-os-mcp/tool-schema.md
```

验证：

```text
python -m compileall novel-os-mcp/src
sh scripts/verify-phase2-sync-tools.sh
sh scripts/verify-phase2-state-tools.sh
sh scripts/verify-phase2-plot-tools.sh
sh scripts/verify-phase2-foreshadowing-tools.sh
sh scripts/verify-phase2-rules-tools.sh
sh scripts/verify-phase2-context-tools.sh
sh scripts/verify-phase2-sync-tools.sh
docker compose -f docker-compose.yml -f docker-compose.app.example.yml ps novel-os-mcp
```

遗留问题：

- 本地 skill 还未接入这些同步工具，后续 Phase 4 需要把初始化包导入、hash 增量提交、冲突展示和导出备份串到本地工作流。
- Web 端还未做项目包导入导出和冲突解决页面，后续 Phase 3 补齐。

### 2.8 审查学习工具

状态：DONE

工具：

```text
review.extract_rule_proposals
review.extract_state_updates
review.extract_foreshadowing_updates
review.evaluate_model_quality
workflow.learn_from_review
```

验收标准：

- 审查报告可生成修订任务。DONE
- 可生成规则提案。DONE
- 可生成状态/伏笔提案。DONE
- Critical 问题可阻断下一章。DONE

能力说明：

- `workflow.learn_from_review` 聚合模型报告、生成 revision tasks、生成规则提案、抽取状态/伏笔建议、评估模型质量。
- `critical/blocker` 会标准化为 `blocking`，`error/major` 会标准化为 `high`，避免不同模型严重级别命名不一致。
- 规则提案批准时会读取 `agreement.rule`，按真实 `rule_type/scope_type/scope_ref/severity/priority/lifecycle` 创建规则，不再固定创建 `style` 规则。
- 状态和伏笔只生成结构化建议，不直接改写正式事实，继续保持“审查不自动改 Canon/状态/伏笔”的底线。

涉及文件：

```text
novel-os-mcp/src/novel_os_mcp/services.py
novel-os-mcp/src/novel_os_mcp/main.py
deploy/nas/scripts/verify-phase2-review-learning-tools.sh
novel-os-mcp/docs/TOOLS.md
docs/novel-os-mcp/tool-schema.md
```

验证：

```text
python -m compileall novel-os-mcp/src
sh scripts/verify-phase2-review-learning-tools.sh
sh scripts/verify-phase2-state-tools.sh
sh scripts/verify-phase2-plot-tools.sh
sh scripts/verify-phase2-foreshadowing-tools.sh
sh scripts/verify-phase2-rules-tools.sh
sh scripts/verify-phase2-context-tools.sh
sh scripts/verify-phase2-sync-tools.sh
sh scripts/verify-phase2-review-learning-tools.sh
docker compose -f docker-compose.yml -f docker-compose.app.example.yml ps novel-os-mcp
```

遗留问题：

- 状态/伏笔建议暂时以结构化结果返回，后续 Web/审批任务阶段需要补“采纳建议后写入正式状态/伏笔”的人工确认入口。
- 模型质量评估目前基于分数与问题严重级别，后续需要接入人工复核准确率后再做动态权重自动调整。

### 2.9 合规审查工具

状态：DONE

工具：

```text
compliance.check
compliance.rule.upsert
compliance.rule.list
```

验收标准：

- 合规 critical 阻断生成。DONE
- 支持项目自定义禁区。DONE
- 支持审计。DONE

能力说明：

- 合规规则复用 `canon_rules`，固定 `rule_type=compliance`，匹配配置写入 `metadata.category/patterns/match_type/case_sensitive/hint`。
- `compliance.check` 只检查调用方传入的 `text/content_items`，不读取或保存本地正文全文。
- 命中 `critical/blocker/blocking` 级别时返回 `blocked=true`，用于生成前预检或审查后阻断。
- 传入 `review_job_id` 且 `create_revision_task=true` 时，会创建 blocking 修订任务、标记审查任务 blocked，并写入 `audit_logs`。

涉及文件：

```text
novel-os-mcp/src/novel_os_mcp/services.py
novel-os-mcp/src/novel_os_mcp/main.py
deploy/nas/scripts/verify-phase2-compliance-tools.sh
novel-os-mcp/docs/TOOLS.md
docs/novel-os-mcp/tool-schema.md
```

验证：

```text
python -m compileall novel-os-mcp/src
sh scripts/verify-phase2-compliance-tools.sh
sh scripts/verify-phase2-state-tools.sh
sh scripts/verify-phase2-plot-tools.sh
sh scripts/verify-phase2-foreshadowing-tools.sh
sh scripts/verify-phase2-rules-tools.sh
sh scripts/verify-phase2-context-tools.sh
sh scripts/verify-phase2-sync-tools.sh
sh scripts/verify-phase2-review-learning-tools.sh
sh scripts/verify-phase2-compliance-tools.sh
docker compose -f docker-compose.yml -f docker-compose.app.example.yml ps novel-os-mcp
```

遗留问题：

- 当前是关键词/包含/正则的确定性规则检查；更复杂的价值观、平台尺度、地域宗教风险仍需要接入模型审查维度。
- 合规阻断只创建修订任务，不自动修改正文，后续由 Web 审查中心或本地 skill 引导人工修订。

### 2.10 模型与成本工具

状态：DONE（本地代码完成，待 NAS 冒烟验证）

工具：

```text
model.profile.upsert
model.profile.list
model.route
model.route_rule.upsert
model.route_rule.list
cost.record_usage
cost.report
```

新增表：

```text
model_profiles
model_route_rules
model_usage_records
```

验收标准：

- 支持模型分层（cheap/standard/premium/local）。
- 支持 token 成本统计（按日/任务类型/模型/Profile/服务商分层）。
- 支持模型路由规则和 fallback。
- 不保存 API key。
- 支持多项目隔离。

新增文件：

- `deploy/nas/postgres/init/150_model_cost.sql`
- `deploy/nas/scripts/verify-phase2-model-cost-tools.sh`
- `services.py` 中新增 `ModelCostService`
- `main.py` 中新增 7 个 MCP 工具

## Phase 3：Web 数据维护台

目标：把 Web 从 MCP 调试台升级为小说数据后台。

状态：TODO

### 3.1 Web 结构重构

状态：TODO

页面结构：

```text
项目选择器
项目总览
设定集
人物/势力/地点/道具
剧情线
伏笔看板
规则库
审查中心
上下文包预览
参考库
模型配置
同步与审计
账号设置
调试工具
```

验收标准：

- 常用维护操作不需要手写 JSON。
- 调试工具保留，但不是主界面。

### 3.2 项目选择器

状态：TODO

能力：

- 列出工作区。
- 列出小说项目。
- 保存当前选择。
- 切换小说时刷新所有数据。

### 3.3 设定集页面

状态：TODO

维护：

- 基础设定。
- 世界观。
- 力量体系。
- 金手指。
- 角色设定。
- 商业定位。
- 文风基准。
- 禁忌规则。

能力：

- 列表。
- 筛选。
- 编辑。
- 版本。
- 状态。
- 来源。

### 3.4 实体页面

状态：TODO

对象：

- 人物。
- 势力。
- 地点。
- 道具。

能力：

- 状态查看。
- 当前状态编辑。
- 关系编辑。
- 过期状态提示。
- 批量导入。

### 3.5 伏笔看板

状态：TODO

能力：

- 按状态筛选。
- 按重要度筛选。
- 按卷筛选。
- 显示逾期。
- 批量归档。
- 关联伏笔。

### 3.6 规则库

状态：TODO

能力：

- 当前生效规则。
- 临时规则。
- 规则冲突。
- 规则提案。
- 审批/拒绝。
- 批量启用/禁用。

### 3.7 审查中心

状态：TODO

能力：

- 审查任务列表。
- 模型报告。
- 聚合报告。
- Critical 阻断项。
- 修订任务。
- 规则提案。
- 模型质量统计。

### 3.8 上下文包预览

状态：TODO

能力：

- 选择章节。
- 选择 context profile。
- 选择 POV。
- 显示 token 占比。
- 显示被裁剪/去重内容。
- 显示冲突和警告。

### 3.9 同步与审计页面

状态：TODO

能力：

- 本地绑定。
- 文件哈希状态。
- 同步冲突。
- 操作审计。
- 日志查询。
- 备份状态。

### 3.10 模型与成本页面

状态：TODO

能力：

- 模型 profile。
- 模型用途。
- 并发限制。
- token 成本。
- 每日成本预估。
- 异常告警。

## Phase 4：本地 AI Skill 对接

目标：让本地 AI 工具成为实际写作入口。

状态：TODO

### 4.1 初始化数据导入契约

状态：TODO

本地初始化输出：

```text
project_profile
canon_documents
rules
entities
relationships
plot_threads
foreshadowing
volumes
chapter_plan_seed
local_files
```

验收标准：

- 本地初始化后可一键导入 MCP。
- Web 能看到导入的数据。

### 4.2 本地目录规范

状态：TODO

目录建议：

```text
.novel-os/
设定集/
大纲/
细纲/
正文/
草稿/
审查报告/
导出/
```

验收标准：

- 本地工具能计算文件哈希。
- 能提交 manifest。

### 4.3 上下文拉取命令

状态：TODO

命令能力：

- 指定章节。
- 指定 profile。
- 指定 POV。
- 保存上下文包到本地。
- 支持离线缓存。

### 4.4 章节提交命令

状态：TODO

提交类型：

- draft commit
- review commit
- final commit
- rollback commit

验收标准：

- draft 不污染正式状态。
- final 更新状态、摘要、伏笔。

### 4.5 多模型审查提交

状态：TODO

能力：

- 本地读取审查 council 配置。
- 调用多个模型。
- 标准化报告 JSON。
- 提交 MCP。
- 保存本地 Markdown。

### 4.6 离线写作兜底

状态：TODO

能力：

- 本地缓存最近上下文。
- 断网生成草稿。
- 恢复后批量同步。
- 展示冲突。

## Phase 5：审查闭环与规则演化

目标：把审查从“报告”变成“长期改进系统”。

状态：TODO

### 5.1 审查任务生命周期

状态：TODO

状态：

```text
pending
running
complete
failed
aggregated
blocked
resolved
```

验收标准：

- 每个审查任务状态清晰。
- Critical 可阻断下一章。

### 5.2 多模型聚合

状态：TODO

能力：

- 多报告合并。
- 共识/分歧。
- 按模型权重。
- 按维度权重。
- 生成最终结论。

### 5.3 修订任务生成

状态：TODO

能力：

- 从 findings 创建 revision tasks。
- severity 分级。
- 支持分配负责人。
- 支持状态流转。

### 5.4 规则提案生成

状态：TODO

能力：

- 从重复问题生成 lesson。
- 从风格问题生成 style。
- 从设定问题生成 canon/character/plot 提案。
- 进入 Web 审批。

### 5.5 审查模型质量评估

状态：TODO

指标：

- 人工确认率。
- 人工驳回率。
- 规则提案通过率。
- 修订任务完成率。
- 与其他模型一致度。

验收标准：

- 低质量模型可降权。

## Phase 6：性能、容灾与运维

目标：保证 NAS 长期运行、可恢复、可观测。

状态：TODO

### 6.1 增量向量索引

状态：TODO

验收标准：

- 单章提交不触发全量重建。
- 仅新增/修改内容入队。

### 6.2 上下文缓存

状态：TODO

缓存对象：

- Canon 摘要。
- 当前人物状态。
- 最近章节摘要。
- 当前规则摘要。

失效条件：

- Canon 更新。
- 规则更新。
- final commit。
- 伏笔状态更新。

### 6.3 冷热归档任务

状态：TODO

能力：

- active/recent/archive/deep_archive。
- 定时降级。
- 手动恢复。

### 6.4 备份恢复

状态：TODO

能力：

- PostgreSQL 定时备份。
- Web 用户配置备份。
- 项目 JSON 导出。
- 恢复脚本。

### 6.5 依赖降级

状态：TODO

降级：

- Qdrant -> PostgreSQL 全文检索。
- Redis -> 限制并发。
- 模型 API -> 备用模型/草稿模式。

### 6.6 发布回滚

状态：TODO

能力：

- 发布前备份。
- 迁移可重复执行。
- 5 分钟回滚流程。

### 6.7 压测

状态：TODO

目标：

- 1000 卷模拟数据。
- 2000 万字等价摘要。
- 10 万记忆块。
- 5000 实体。
- 1000 伏笔。

## Phase 7：P1 创作效率增强

状态：TODO

任务：

| 任务 | 状态 |
| --- | --- |
| Prompt 模板托管 | TODO |
| 连载统计看板 | TODO |
| 读者期待库 | TODO |
| 素材库增强 | TODO |
| 工程包导入导出 | TODO |
| 协作批注系统 | TODO |
| 上下文权重编辑器 | TODO |
| 批量预生成细纲 | TODO |
| 专有名词锁定 | TODO |
| 多版本正文差异对比 | TODO |
| 全局冲突看板 | TODO |
| 全书时间线校验 | TODO |
| 全局跨模块检索 | TODO |

## Phase 8：P2 远期扩展

状态：DEFERRED

任务：

| 任务 | 状态 |
| --- | --- |
| 人物/势力关系图谱 | DEFERRED |
| 题材模板市场 | DEFERRED |
| 增强离线完整创作模式 | DEFERRED |
| 分布式 MCP 水平扩展 | DEFERRED |
| 多剧情分支合并 | DEFERRED |
| 外部通知集成 | DEFERRED |

## 当前最近开发顺序

后续建议严格按以下顺序推进：

```text
1. Phase 1.1 Canon 文档表和工具
2. Phase 1.4 状态时效字段
3. Phase 1.5 伏笔关联字段
4. Phase 1.6 规则作用域与临时规则
5. Phase 2.1 Canon 工具
6. Phase 2.2 实体工具
7. Phase 2.3 剧情线和卷工具
8. Phase 2.4 伏笔增强工具
9. Phase 2.6 上下文包增强
10. Phase 3.1 Web 结构重构
11. Phase 3.3 Web 设定集页面
12. Phase 4.1 本地初始化数据导入
```

原因：

- Canon 文档是 Web 数据维护的基础。
- 状态、伏笔、规则范围是上下文包质量的基础。
- 上下文包增强前必须有可用数据。
- Web 改造必须建立在稳定 MCP 工具之上。

## 每次开发后必须更新的内容

每完成一个任务，必须更新本文档：

- 任务状态。
- 完成时间。
- 涉及文件。
- 已部署环境。
- 验证结果。
- 遗留问题。

建议记录格式：

```text
完成时间：
涉及文件：
部署位置：
验证命令：
验证结果：
遗留问题：
下一步：
```
