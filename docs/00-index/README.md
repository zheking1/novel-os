# Novel OS — 项目文档总索引

## 项目概述

Novel OS 是一个**长篇中文网络小说智能创作助手**系统。它帮助作者管理庞杂的世界设定、角色关系、情节线索和章节生成，通过 AI 驱动的知识库、向量检索、自动审核和多人讨论室等机制，确保长篇连载中的设定一致性、情节合理性和创作效率。

系统由 4 个 Docker 容器组成，部署在一台 NAS 服务器上，前端为纯静态 SPA（Python stdlib 服务），后端为 FastMCP 工具服务器。

---

## 快速导航

| 分类 | 文档 | 说明 |
|------|------|------|
| **架构** | [01-architecture/overview.md](../01-architecture/overview.md) | 系统架构全景：容器拓扑、数据流、网络、设计决策 |
| **架构** | [01-architecture/technology-stack.md](../01-architecture/technology-stack.md) | 技术栈详解：前端/后端/数据库/基础设施，选型原因 |
| **前端** | [novel-os-web/docs/development-guide.md](../../novel-os-web/docs/development-guide.md) | 前端开发指南：页面模式、部署流程、菜单结构 |
| **前端** | [novel-os-web/docs/api-conventions.md](../../novel-os-web/docs/api-conventions.md) | API 约定：MCP 工具命名、参数规范、返回值格式 |
| **前端** | [novel-os-web/docs/troubleshooting.md](../../novel-os-web/docs/troubleshooting.md) | 常见问题排查：12 类典型问题及修复方案 |
| **前端** | [02-frontend/pages/](../02-frontend/pages/) | 各功能页面的详细设计与使用说明 |
| **后端** | [03-backend/services/](../03-backend/services/) | MCP 服务层架构与服务模块说明 |
| **后端** | [03-backend/tools/](../03-backend/tools/) | MCP 工具清单与每个工具的详细文档 |
| **后端** | [03-backend/tone-system.md](../03-backend/tone-system.md) | 调性系统：`ref_tones` 数据模型、`tone.*` 工具、页面与消费链路 |
| **数据库** | [04-database/](../04-database/) | 数据库表结构、迁移方案、索引策略 |
| **部署** | [05-deployment/](../05-deployment/) | 部署流程：NAS 部署、Docker Compose、HTTPS 配置 |
| **开发** | [06-development/](../06-development/) | 开发环境搭建、本地运行、调试技巧 |
| **规划** | [07-planning/roadmap.md](../07-planning/roadmap.md) | **总开发计划**：待办总表、优先级、依赖、阶段划分、验收标准 |
| **规划** | [07-planning/](../07-planning/) | 各功能的需求 / 设计 / 开发计划子文档 |
| **修复** | [08-fix-plans/](../08-fix-plans/) | Bug 修复方案与复盘记录 |
| **凭证** | [09-credentials/](../09-credentials/) | 服务器凭证、数据库账号、API 密钥索引 |

---

## 使用指南

### 新 Agent / 新开发者阅读顺序

1. **先读架构** — `01-architecture/overview.md` 了解整体拓扑和数据流
2. **再看技术栈** — `01-architecture/technology-stack.md` 了解选型背景和限制
3. **然后读 API 约定** — `novel-os-web/docs/api-conventions.md` 掌握核心调用模式
4. **接着读开发指南** — `novel-os-web/docs/development-guide.md` 了解代码结构和添加页面的流程
5. **最后读排查指南** — `novel-os-web/docs/troubleshooting.md` 熟悉高频坑位

### 做功能开发时的推荐流程

1. 先看 [07-planning/roadmap.md](../07-planning/roadmap.md) 确认该项的优先级、依赖与所处阶段，再在 `07-planning/` 下写功能设计文档（若预计工作量 >30 分钟）
2. 根据功能修改前端页面（`novel-os-web/js/pages/`）和/或 MCP 工具（`novel-os-mcp/src/novel_os_mcp/tools/`）
3. 本地测试验证
4. 按 `05-deployment/` 的流程部署到 NAS
5. 在 `08-fix-plans/` 记录遇到的新问题及其修复方案

### Agent 会话必读规则

每个会话开始前三件事：
- 查看 `novel-os-web/docs/development-guide.md`
- 查看 `novel-os-web/docs/api-conventions.md`
- 查看 `novel-os-web/docs/troubleshooting.md`

---

## 关键联络信息

| 项目 | 值 |
|------|-----|
| **NAS IP** | `${NAS_HOST}` |
| **SSH 用户** | `root` |
| **项目路径** | `/opt/novel-os/` |
| **Web 服务地址** | `http://${NAS_HOST}:8790` |
| **MCP 服务地址** | `http://${NAS_HOST}:8787/mcp` |
| **PostgreSQL** | `${NAS_HOST}:5432` |
| **Qdrant HTTP** | `${NAS_HOST}:6333` |
| **Qdrant gRPC** | `${NAS_HOST}:6334` |
| **Docker 网络** | `novel_net` (bridge, `172.20.0.0/16`) |

> 所有密码、Token、密钥等敏感信息请参见 [09-credentials/](../09-credentials/) 目录。