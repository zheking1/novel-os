# Novel OS 文档索引

更新时间：2026-06-27

本文档是 `docs/novel-os-mcp/` 目录下所有文档的索引，方便快速查找所需资料。

---

## 🚀 新窗口快速开始

第一次打开项目？按以下顺序阅读：

1. **[HANDOFF.md](./HANDOFF.md)** — 交接入口，总览
2. **[handoff-current-state.md](./handoff-current-state.md)** — 当前开发进度
3. **[handoff-requirements-summary.md](./handoff-requirements-summary.md)** — 需求摘要
4. **[handoff-architecture.md](./handoff-architecture.md)** — 技术架构
5. **[handoff-development-standards.md](./handoff-development-standards.md)** — 开发规范
6. **[handoff-deployment-runbook.md](./handoff-deployment-runbook.md)** — 部署运维
7. **[handoff-next-tasks.md](./handoff-next-tasks.md)** — 下一步任务

---

## 📑 文档分类索引

### 一、交接入门类

| 文档 | 说明 | 适用场景 |
|------|------|----------|
| [HANDOFF.md](./HANDOFF.md) | 新窗口交接入口，总览文档，一句话目标，阅读顺序 | 新窗口打开项目时第一个读 |
| [完善当前项目.md](./完善当前项目.md) | 本次对话的完整记录，包含项目分析、进度验证、部署信息 | 回顾本次对话的讨论内容 |

### 二、需求业务类

| 文档 | 说明 | 适用场景 |
|------|------|----------|
| [requirements-and-dev-brief.md](./requirements-and-dev-brief.md) | 完整需求与开发简报，系统目标、边界、功能模块详解 | 需要深入理解业务需求时 |
| [handoff-requirements-summary.md](./handoff-requirements-summary.md) | 需求摘要，提炼核心边界、数据分层、业务规则 | 快速了解需求全貌 |

### 三、技术架构类

| 文档 | 说明 | 适用场景 |
|------|------|----------|
| [architecture.md](./architecture.md) | 完整技术架构文档，模块划分、数据流、多用户模型 | 理解系统整体架构设计 |
| [handoff-architecture.md](./handoff-architecture.md) | 架构交接摘要，代码结构、核心文件、部署架构 | 快速了解技术架构和代码组织 |
| [data-model.md](./data-model.md) | 数据模型定义，所有数据库表结构说明 | 设计数据库表或理解表结构时 |
| [tool-schema.md](./tool-schema.md) | MCP 工具 Schema，所有工具的输入输出定义 | 查找工具接口定义时 |

### 四、开发计划类

| 文档 | 说明 | 适用场景 |
|------|------|----------|
| [development-plan.md](./development-plan.md) | 完整开发计划，Phase 0-8 详细任务、进度日志、验收标准 | 了解详细开发计划和历史进度 |
| [handoff-current-state.md](./handoff-current-state.md) | 当前开发状态，阶段状态一览、已完成能力、下一步 | 快速了解当前做到哪了 |
| [handoff-next-tasks.md](./handoff-next-tasks.md) | 后续开发任务拆分，Phase 2.10 详细设计 | 开始新任务前读，了解任务细节 |
| [implementation-plan.md](./implementation-plan.md) | 实现计划（英文版），推荐的实现顺序 | 参考原始实现规划 |

### 五、开发规范类

| 文档 | 说明 | 适用场景 |
|------|------|----------|
| [handoff-development-standards.md](./handoff-development-standards.md) | 开发规范，代码风格、MCP 工具规范、测试规范、迁移规范 | 写代码前必读，确保符合项目规范 |

### 六、部署运维类

| 文档 | 说明 | 适用场景 |
|------|------|----------|
| [handoff-deployment-runbook.md](./handoff-deployment-runbook.md) | 部署与运维交接，NAS 目录、容器配置、迁移、备份、冒烟测试 | 部署、运维、排障时使用 |

---

## ⚡ 关键信息速查

### 当前开发进度

```
NEXT: Phase 3 Web 数据维护台（或 Phase 1 上下文 Profile）
DONE: Phase 2.10 模型与成本工具（本地代码完成，待 NAS 验证）
```

- **Phase 0** ✅ DONE — 基础部署与需求基线
- **Phase 1** 🔄 DOING — P0 数据模型与迁移（上下文 Profile 待完成）
- **Phase 2** 🔄 DOING — P0 MCP 核心工具（2.1-2.10 本地代码完成，待 NAS 验证）
- **Phase 3** ⏳ TODO — Web 数据维护台
- **Phase 4** ⏳ TODO — 本地 AI Skill 对接
- **Phase 5** ⏳ TODO — 审查闭环与规则演化
- **Phase 6** ⏳ TODO — 性能、容灾与运维
- **Phase 7** ⏳ TODO — P1 创作效率增强
- **Phase 8** ⏸️ DEFERRED — P2 远期扩展

### 部署信息

| 项目 | 值 |
|------|-----|
| **NAS IP** | `${NAS_HOST}` |
| **NAS 工作目录** | `/opt/novel-os` |
| **本地工作目录** | `D:\Project\novels codex` |
| **MCP 地址（nginx 反代）** | `http://${NAS_HOST}:48083/mcp` |
| **MCP 内部地址** | `http://127.0.0.1:8787` |
| **PostgreSQL** | `5432` 端口，容器名 `novel-postgres` |
| **Qdrant** | `6333/6334` 端口，容器名 `novel-qdrant` |
| **Redis** | `6379` 端口，Host `${NAS_HOST}` |

### 核心技术栈

| 组件 | 技术 |
|------|------|
| MCP 服务 | Python + FastMCP |
| Web 控制台 | Python HTTP + HTML/JS |
| 数据库 | PostgreSQL 16 + pgvector |
| 向量数据库 | Qdrant |
| 缓存 | Redis |
| 部署 | Docker Compose |

### 项目结构速览

```
novel-os-mcp/src/novel_os_mcp/
  main.py          MCP tool 注册入口
  services.py      业务服务层
  auth.py          认证与权限
  db.py            数据库封装
  config.py        配置
  vector.py        Qdrant 向量接口

novel-os-web/
  server.py        Web 服务器
  index.html       Web 页面

deploy/nas/
  docker-compose.yml        基础服务
  docker-compose.app.example.yml  应用服务
  postgres/init/*.sql       SQL 迁移
  scripts/*.sh              运维脚本

skills/novel-os-local/      本地写作 skill
```

---

## 🎯 按场景找文档

### 我要开始写新功能

1. 读 [handoff-next-tasks.md](./handoff-next-tasks.md) — 了解当前任务
2. 读 [handoff-development-standards.md](./handoff-development-standards.md) — 了解开发规范
3. 读 [handoff-architecture.md](./handoff-architecture.md) — 了解代码结构
4. 参考 [tool-schema.md](./tool-schema.md) — 了解工具接口风格
5. 参考 [data-model.md](./data-model.md) — 了解数据模型

### 我要部署/更新 NAS

1. 读 [handoff-deployment-runbook.md](./handoff-deployment-runbook.md) — 部署运维手册

### 我要了解需求边界

1. 读 [handoff-requirements-summary.md](./handoff-requirements-summary.md) — 快速摘要
2. 读 [requirements-and-dev-brief.md](./requirements-and-dev-brief.md) — 完整需求

### 我要了解当前进度

1. 读 [handoff-current-state.md](./handoff-current-state.md) — 当前状态
2. 读 [development-plan.md](./development-plan.md) — 详细计划和历史

### 我要查数据库表结构

- 读 [data-model.md](./data-model.md) — 数据模型定义

### 我要查 MCP 工具接口

- 读 [tool-schema.md](./tool-schema.md) — 工具 Schema

---

## 📌 已完成的 MCP 工具清单

### 认证与用户
- `auth.whoami`, `auth.create_api_token`, `auth.list_api_tokens`, `auth.revoke_api_token`
- `user.create`, `user.list`
- `workspace.create`, `workspace.list`, `workspace.add_member`
- `project.create`, `project.list`, `project.add_member`, `project.list_members`, `project.register_local_binding`

### Canon 文档
- `canon.doc.upsert`, `canon.doc.list`, `canon.doc.get`, `canon.doc.archive`, `canon.doc.history`, `canon.doc.restore`

### 状态与实体
- `state.entity.upsert`, `state.entity.list`, `state.entity.get`, `state.entity.archive`
- `state.snapshot.create`, `state.snapshot.list`
- `state.relationship.upsert`, `state.relationship.list`

### 剧情与卷
- `volume.upsert`, `volume.list`
- `plot.thread.upsert`, `plot.thread.list`, `plot.thread.link_volume`, `plot.thread.update_progress`

### 伏笔
- `foreshadowing.bulk_status_update`, `foreshadowing.check_overdue`, `foreshadowing.link`, `foreshadowing.payoff`

### 规则
- `rules.list_effective`, `rules.check_conflict`, `rules.bulk_toggle`, `rules.resolve_conflict`, 等 9 个工具

### 工作流/上下文
- `workflow.prepare_chapter_context`, `workflow.validate_context_pack`, `workflow.preflight_generation`, `workflow.prepare_segment_context`, 等 5 个工具

### 本地同步
- `sync.import_local_manifest`, `sync.submit_file_hashes`, `sync.list_conflicts`, `sync.resolve_conflict`, `sync.export_project_pack`, 等 6 个工具

### 审查学习
- `review.extract_rule_proposals`, `review.extract_state_updates`, `review.extract_foreshadowing_updates`, `review.evaluate_model_quality`, 等 12 个工具

### 合规审查
- `compliance.rule.upsert`, `compliance.rule.list`, `compliance.check`

### 模型与成本
- `model.profile.upsert`, `model.profile.list`, `model.route`
- `model.route_rule.upsert`, `model.route_rule.list`
- `cost.record_usage`, `cost.report`
