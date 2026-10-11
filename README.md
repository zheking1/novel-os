# Novel OS

> 一个面向 AI 辅助长篇小说创作的「操作系统」：把设定、剧情、伏笔、人物状态、审查规则全部持久化，让 AI 在写到第 300 章时仍然记得第 3 章埋下的那颗钉子。

[![Python](https://img.shields.io/badge/python-3.11%2B-blue)](https://www.python.org/)
[![MCP](https://img.shields.io/badge/protocol-MCP-green)](https://modelcontextprotocol.io)
[![License](https://img.shields.io/badge/license-MIT-lightgrey)](LICENSE)

---

## 为什么需要它

直接用大模型写长篇，通常会在第 10 章左右开始崩坏：

| 问题 | 根因 |
| --- | --- |
| 人设漂移、地名前后矛盾 | 设定只存在于对话上下文里，窗口一滚动就丢 |
| 伏笔埋了不收、收了不响 | 没有任何东西在跟踪伏笔的生命周期 |
| 写到后面越来越水 / 越来越重复 | 缺少节奏、新颖度、风格的量化反馈 |
| 每次开新对话都要重讲一遍世界观 | 故事状态没有被持久化成可查询的数据 |
| 改一章，连累前面十章 | 没有因果链和实体快照，影响面只能靠人脑推演 |

Novel OS 的做法是：**把「创作过程」本身变成结构化数据 + 一组可被 AI 调用的工具**。模型不再靠记忆维持一致性，而是随时查询与写回一个真实的状态库。

---

## 核心能力

- **正典与规则（Canon / Rules）** — 世界观、设定条目、硬规则与软规则分层存储，生成时可被强制注入
- **实体与状态快照（Entities / Snapshots / Relations）** — 角色、地点、势力的属性与生命周期，支持任意章节时间点的状态回溯与关系图谱
- **剧情引擎（Plot）** — 卷 → 情节线 → 伏笔 → 章节大纲，伏笔带 `must_payoff` / `payoff_deadline` 与**逾期检测**
- **动态上下文打包（Context）** — 按 token 预算自动挑选「本章真正需要知道的」设定、实体、近期摘要，而不是把全库塞进提示词
- **生成与审查闭环（Pipeline / Compliance / Review）** — 生成 → 合规校验 → 评审报告 → 修订，支持多模型评审会
- **风格与节奏分析** — 风格指纹（style fingerprint）、节奏曲线（pacing）、新颖度（novelty）、因果链一致性（causality）
- **知识库（KB）** — 题材策略、用户知识（UK）、参考资料、向量检索（Qdrant）+ 知识缺口检测
- **多智能体讨论室（Discussion Room）** — 让多个模型对同一章/同一设定会诊，再汇总结论
- **系统进化（System Evolution）** — 从评审结果中沉淀规则提案，反哺写作规则库

---

## 架构

```
┌──────────────────────────────────────────────────────────────┐
│                        浏览器 (SPA)                           │
│   原生 JS + Tailwind + D3，hash 路由，无打包器，~90 个页面     │
└───────────────────────────┬──────────────────────────────────┘
                            │  POST /api/tool
                            ▼
┌──────────────────────────────────────────────────────────────┐
│              novel-os-web/server.py   (:8790)                 │
│   静态服务 · 登录与 Session · MCP 代理 · 权限校验              │
└───────────────────────────┬──────────────────────────────────┘
                            │  MCP over HTTP
                            ▼
┌──────────────────────────────────────────────────────────────┐
│                 novel-os-mcp   (:8787/mcp)                    │
│                 FastMCP · ~380 个工具                          │
│  tools/ (30 个域模块)  →  services/ (19 个业务服务)  →  db.py   │
└───────┬──────────────────┬──────────────────┬────────────────┘
        ▼                  ▼                  ▼
   PostgreSQL 16       Qdrant            Redis
   (+ pgvector)     向量检索/记忆      缓存 + MCP Session
```

**关键设计：前端没有 REST 业务接口。** 页面上每一个操作，最终都是一次 `ApiClient.callTool('域.资源.动作', args)` → `/api/tool` → MCP 工具。因此 MCP 服务端是唯一的业务真相来源，Web 控制台与任意 AI 客户端（Claude / Cursor / 自研 Agent）调用的是同一套工具、同一份数据。

---

## 目录结构

```
.
├── novel-os-mcp/               # MCP 服务端（全部业务逻辑）
│   └── src/novel_os_mcp/
│       ├── main.py             # 入口
│       ├── mcp_core.py         # FastMCP 实例 + Agent 工作协议
│       ├── db.py               # asyncpg 连接池，裸 SQL，无 ORM
│       ├── deps.py             # 服务单例装配
│       ├── tools/              # 30 个按域拆分的工具模块
│       ├── services/           # 19 个业务服务
│       └── *.py                # 领域服务（kb / causality / pacing / style …）
├── novel-os-web/               # Web 控制台
│   ├── index.html              # 单页外壳 + 脚本清单
│   ├── server.py               # 静态服务 + 认证 + MCP 代理
│   └── js/{core,utils,components,pages}/
├── deploy/nas/                 # Docker Compose 部署 + 建表 SQL + 运维脚本
└── docs/                       # 92 篇设计文档（架构 / 前端 / 后端 / 数据库 / 部署 / 规划）
```

---

## 快速开始

### 前置条件

- Docker 与 Docker Compose v2
- 一个 Redis 实例（可与下列服务共用网络）
- 可选：OpenAI 兼容的 LLM / Embedding 接口（用于生成、审查、向量化）

### 1. 准备部署目录

```bash
git clone <your-repo-url> novels
cd novels/deploy/nas
cp .env.example .env
```

编辑 `.env`，至少修改这几项（**请勿使用默认口令**）：

```bash
POSTGRES_PASSWORD=
QDRANT_API_KEY=
REDIS_PASSWORD=
NOVEL_OS_AUTH_MODE=dev      # 仅用于本地试用；正式部署请改为 token
```

### 2. 启动基础设施

```bash
docker compose up -d postgres qdrant
sh ./scripts/init-qdrant.sh      # 初始化向量集合
```

### 3. 启动应用

```bash
docker compose -f docker-compose.yml -f docker-compose.app.example.yml up -d --build
```

### 4. 访问

| 服务 | 地址 |
| --- | --- |
| Web 控制台 | `http://127.0.0.1:8790` |
| MCP 端点 | `http://127.0.0.1:8787/mcp` |
| Adminer（可选） | `docker compose --profile admin up -d adminer` → `127.0.0.1:8088` |

默认管理员账号在 `postgres/init` 的种子数据中创建，**登录后请立即改密码**。

---

## 环境变量

| 变量 | 说明 | 默认 |
| --- | --- | --- |
| `DATABASE_URL` | PostgreSQL 连接串 | `postgresql://…@postgres:5432/novel_os` |
| `QDRANT_URL` / `QDRANT_API_KEY` | 向量库地址与密钥 | `http://qdrant:6333` |
| `REDIS_URL` / `REDIS_HOST` / `REDIS_PORT` / `REDIS_PASSWORD` | 缓存与 Session | — |
| `NOVEL_OS_AUTH_MODE` | `dev` 或 `token` | `dev` |
| `NOVEL_OS_DEV_USER` / `NOVEL_OS_DEV_WORKSPACE` / `NOVEL_OS_DEV_SCOPES` | dev 模式下的身份 | `admin` / `default` |
| `NOVEL_PROJECTS_DIR` | 稿件存放目录 | `/app/projects` |
| `NOVEL_OS_MCP_URL` | Web 端转发 MCP 的目标地址 | `http://novel-os-mcp:8787/mcp` |
| `NOVEL_OS_MCP_TOOL_WHITELIST` | 只注册指定前缀的工具（逗号分隔） | 全部 |

完整列表见 `deploy/nas/.env.example` 与 `novel-os-mcp/README.md`。

---

## 作为 MCP 服务接入你的 AI 客户端

MCP 服务端以 HTTP transport 暴露在 `/mcp`，任何支持 MCP 的客户端都能直接接进来，与你自己的 Agent 共享同一份故事状态。

```json
{
  "mcpServers": {
    "novel-os": {
      "url": "http://127.0.0.1:8787/mcp",
      "headers": {
        "apiKey": "<your-api-key>"
      }
    }
  }
}
```

工具命名遵循 `域.资源.动作`，例如：

```
auth.whoami
workspace.list / project.create
kb.entity.create / kb.uk.search / kb.world.get
state.entity.upsert / state.snapshot.upsert / state.relationship.upsert
plot.upsert_foreshadowing / plot.thread.advance / plot.create_chapter_plan
volume.upsert / graph.get_subgraph
prompt.template.render / model.profile.list
```

> 多数工具会返回 `workflow_guide` 字段，告诉调用方**下一步该做什么**。Agent 应当遵循它，这是本项目工具链的设计约定。

---

## 核心概念

| 概念 | 含义 |
| --- | --- |
| **Workspace** | 顶层空间，可包含多个项目，支持成员协作 |
| **Project** | 一部作品。其下挂载正典、实体、剧情、章节、知识包 |
| **Canon / Rules** | 正典设定与写作规则，分硬约束与软风格 |
| **Entity / Snapshot** | 故事实体（角色/地点/势力）及其在某一章节的状态快照 |
| **Volume / Thread / Foreshadowing** | 卷、情节线、伏笔，构成剧情骨架 |
| **Chapter Plan / Chapter** | 章节大纲与成稿，含版本与批注 |
| **UK / PK** | 用户知识库 / 项目知识包，可跨项目复用 |
| **Context Pack** | 按 token 预算动态组装的「本章所需上下文」 |

---

## 开发指南

```bash
# MCP 服务端（本地开发）
cd novel-os-mcp
pip install -e .
novel-os-mcp          # 或 python -m novel_os_mcp.main

# Web 控制台
cd novel-os-web
python server.py      # 监听 :8790
```

新增一个功能通常要动四处，请先读这几份文档：

1. `novel-os-web/docs/development-guide.md` — 架构、页面范式、部署流程
2. `novel-os-web/docs/api-conventions.md` — 工具命名、参数与返回值约定
3. `novel-os-web/docs/troubleshooting.md` — 已知坑与排查

需要留意的硬性约定：

- 工具名用**点号**（`user.create`），前端方法用 **camelCase**（`ApiClient.userList()`）
- 删除类工具**必须返回 dict**：`return {"ok": deleted, "key": key}`；返回 `bool` 会触发 FastMCP 的 `structured_content must be a dict` 错误
- 页面的 `init()` 必须 `return true`，否则会被路由回退成占位页
- API 调用一律使用**业务键**（如 `template_key`），不要传 UUID
- 改 JS 需重建 `novel-os-web`，改 MCP 需重建 `novel-os-mcp`；**先上传源文件再 build**，容器内改动会丢失

更多设计文档见 [`docs/00-index/README.md`](docs/00-index/README.md)。

---

## 安全须知

- `NOVEL_OS_AUTH_MODE=dev` 仅供本地/内网试用，**不要**在公网环境使用
- 默认配置下 PostgreSQL、Qdrant、MCP、Web 均绑定 `127.0.0.1`；需要对外暴露时请走 nginx 反向代理并启用 TLS
- 不要把 `.env` 提交进仓库
- 不要让写作 Agent 直连数据库或文件系统，所有操作都应经由 MCP 工具

---

## 路线图

- [x] 补齐仓库缺失的建表 SQL：`global_rules`、`evolution_logs`、`rule_summaries`，并额外补上代码已在读写的 `ref_tones` / `ref_tone_rules`（见 `deploy/nas/postgres/migrations/222_*.sql`、`223_*.sql`）
- [x] 合并 `docs/` 与 `novel-os-web/docs/` 中的重复文档（规划类统一收进 `docs/07-planning/`）
- [x] 完善工具目录：补齐 `novel.wizard.*` 6 个工具与 `tone.*` 5 个工具，修正页面索引中与实际不符的工具名
- [x] 修复前端断链：新增 `model-cost` 页面、修正 `auto-search` 对象名，后端补注册 `kb.auto.search` / `kb.uk.get` / `setting.genre.upsert`
- [x] 开启动态上下文预算（默认启用，并受调用方预算钳制，不会超出窗口或撑爆 section）
- [x] 进化门禁改为真正的拦截式评估：先评估后写入，中/高风险转为待管理员审批的延迟写入
- [x] 替换 `ai_reviewer` 中的模拟评分：LLM 不可用时返回「未评分」而非伪装通过的假分数
- [x] 清理死代码：删除 `js/core/router.js`、7 个未被引用的旧页面、孤儿路由分支
- [x] 补齐知识审核页 `knowledge-review`（此前为占位页）
- [ ] 补齐 `novel-os-mcp/docs/TOOLS.md`（当前仅 13 个分组、无参数签名）
- [ ] 英文 i18n 补齐
- [ ] 章节生成流程的可视化编排
- [ ] 插件化的题材策略包

进行中的开发计划见 [`docs/07-planning/roadmap.md`](docs/07-planning/roadmap.md)。

欢迎提交 Issue 与 PR。

---

## 许可证

[MIT](LICENSE) © Novel OS contributors
