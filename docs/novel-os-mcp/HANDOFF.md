# Novel OS MCP 新窗口交接入口

更新时间：2026-06-27

本文档给重新打开的新开发窗口使用。新窗口 AI 应先读本文，再按任务读取关联文档，避免依赖旧聊天记录。

## 一句话目标

Novel OS MCP 是一个面向 2000 万字超长篇网文 AI 写作的中枢服务。它不保存作者可人工编辑的正文、大纲、细纲全文，而是保存规则、设定、人物/势力/道具状态、剧情线、伏笔、摘要、审查报告、修订任务、向量索引元数据和本地文件哈希引用。

核心原则：

```text
MCP 存全量结构化数据
AI 读局部上下文
规则库守底线
状态快照给当前事实
检索系统找相关历史
摘要系统压缩长期剧情
审查系统防止漂移
本地文件保存正文/大纲/细纲等可编辑产物
```

## 新窗口第一步

请按顺序阅读：

1. [handoff-current-state.md](./handoff-current-state.md)：当前完成到哪里，下一步做什么。
2. [handoff-requirements-summary.md](./handoff-requirements-summary.md)：需求边界和业务规则。
3. [handoff-architecture.md](./handoff-architecture.md)：技术架构、模块和数据分层。
4. [handoff-development-standards.md](./handoff-development-standards.md)：开发规范、代码规范、验证规范。
5. [handoff-deployment-runbook.md](./handoff-deployment-runbook.md)：NAS 部署、验证、回滚方式。
6. [handoff-next-tasks.md](./handoff-next-tasks.md)：下一批开发任务拆分。

已有长文档可作为深水区资料：

- [requirements-and-dev-brief.md](./requirements-and-dev-brief.md)
- [development-plan.md](./development-plan.md)
- [architecture.md](./architecture.md)
- [data-model.md](./data-model.md)
- [tool-schema.md](./tool-schema.md)
- [implementation-plan.md](./implementation-plan.md)

## 当前开发指针

```text
NEXT: Phase 3.3 实体面板
DOING: Phase 3.2 规则面板（已完成部署）
DONE: Phase 3.1 Canon 文档 + 项目选择器
```

## 目录速览

```text
novel-os-mcp/              MCP 服务源码，FastMCP + PostgreSQL + Qdrant
novel-os-web/              轻量 Web 控制台，当前不是完整生产后台
deploy/nas/                NAS Docker Compose、SQL 迁移、运维脚本、冒烟脚本
docs/novel-os-mcp/         需求、架构、计划、交接文档
skills/novel-os-local/     本地写作 skill 初版，尚未深度接入全部 MCP 工具
```

## 当前已部署环境

NAS 目标目录：

```text
/opt/novel-os
```

容器：

```text
novel-postgres
novel-qdrant
novel-os-mcp
novel-os-web
novel-adminer（可选 profile）
```

MCP 容器端口：

```text
127.0.0.1:8787 -> 8787
```

Web 容器端口：

```text
127.0.0.1:8790 -> 8790
```

外部访问通过用户已配置的 nginx 反代，nginx 配置文件在 NAS：

```text
/home/docker/nginx/conf/conf.d/mcp.conf
```

新窗口若需要部署，只能操作 NAS 的：

```text
/opt/novel-os
```

不要修改 NAS 其他目录，除非用户重新明确授权。

## 最近一次验证结果

2026-06-27，Phase 2 全套冒烟通过：

```text
phase2 state tools smoke ok
phase2 plot tools smoke ok
phase2 foreshadowing tools smoke ok
phase2 rules tools smoke ok
phase2 context tools smoke ok
phase2 sync tools smoke ok
phase2 review learning tools smoke ok
phase2 compliance tools smoke ok
novel-os-mcp Up, 127.0.0.1:8787->8787/tcp
```

## 必须遵守的边界

- 不把正文、大纲、细纲、草稿、审查 Markdown 等人工可编辑产物存入 MCP。
- MCP 只保存结构化数据、摘要、状态、规则、审查结构化结果、本地路径提示和哈希。
- 伏笔、规则、状态、设定可保存在 MCP，并可被 Web 维护。
- 审查系统只能生成修订任务、规则提案、状态/伏笔建议；不得自动修改硬 Canon。
- 多用户、多工作区、多小说必须隔离，所有表和工具必须通过 `workspace/project/project_id` 约束。
- 新增工具必须更新 `tool-schema.md`、`novel-os-mcp/docs/TOOLS.md`、`development-plan.md` 和 NAS 冒烟脚本。

## 新窗口继续开发的推荐动作

1. 读取 `handoff-next-tasks.md`。
2. 从 Phase 2.10 开始实现模型与成本工具。
3. 先设计数据表迁移，再写 service，再注册 MCP tool，再写冒烟脚本。
4. 本地运行：

```text
python -m compileall novel-os-mcp/src
```

5. 同步到 NAS `/opt/novel-os`，重建 `novel-os-mcp`。
6. 运行新冒烟脚本和 Phase 2 全套组合冒烟。
7. 更新交接文档和开发计划。
