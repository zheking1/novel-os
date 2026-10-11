# 系统架构全景

## 容器拓扑

Novel OS 由 4 个 Docker 容器组成，全部运行在 NAS（`${NAS_HOST}`）上，通过 `novel_net` bridge 网络互联。

```
┌──────────────────────────────────────────────────────────┐
│  NAS (${NAS_HOST})                                     │
│                                                          │
│  ┌─────────────┐  ┌──────────────┐  ┌───────────────┐  │
│  │ novel-      │  │ novel-qdrant │  │ novel-os-web  │  │
│  │ postgres    │  │ :6333 (HTTP) │  │ :8790         │  │
│  │ :5432       │  │ :6334 (gRPC) │  │               │  │
│  │ pgvector+   │  │              │  │ Python stdlib │  │
│  │ pg16        │  └──────────────┘  │ + vanilla JS  │  │
│  └─────────────┘                     └───────────────┘  │
│                                                          │
│  ┌──────────────────────────────────────────────────┐   │
│  │ novel-os-mcp :8787                               │   │
│  │ FastMCP >= 2.0.0 (SSE)                           │   │
│  │ 40+ MCP tools: kb, state, plot, review, ...      │   │
│  └──────────────────────────────────────────────────┘   │
│                                                          │
│  Docker Network: novel_net (bridge, 172.20.0.0/16)      │
└──────────────────────────────────────────────────────────┘
```

### 容器职责

| 容器 | 端口 | 镜像 | 职责 |
|------|------|------|------|
| `novel-postgres` | 5432 | `pgvector/pgvector:pg16` | 关系型数据存储，含向量检索扩展 |
| `novel-qdrant` | 6333/6334 | `qdrant/qdrant:latest` | 向量数据库，语义检索与知识库 |
| `novel-os-mcp` | 8787 | 自构建 `novel-os-mcp:latest` | MCP 工具服务器，核心业务逻辑 |
| `novel-os-web` | 8790 | 自构建 `novel-os-web:latest` | Web 服务器 + SPA 前端 + 认证代理 |

> 还有一个 `novel-adminer` 容器（profiles: admin），仅在需要数据库 Web 管理界面时启动。

---

## 数据流

```
外部用户                 NAS 服务器 (${NAS_HOST})
─────────              ─────────────────────────────

┌─────────┐           ┌──────────────────────────────────────┐
│ Browser │──HTTPS───→│ Nginx (SSL 终端)                      │
│ (SPA)   │           │   ↓ 反向代理 :8790                    │
└─────────┘           │ novel-os-web (server.py)              │
                      │   ├─ 静态文件服务 (HTML/JS/CSS)       │
                      │   ├─ 会话认证 (Cookie-based)          │
                      │   ├─ 用户/Token 管理 (→ Postgres)     │
                      │   └─ MCP 中继 (→ novel-os-mcp:8787)   │
                      │           │                           │
                      │           ↓ SSE (JSON-RPC)            │
                      │ novel-os-mcp (FastMCP)                │
                      │   ├─ tool_auth — 权限校验             │
                      │   ├─ tools/* — 40+ 业务工具           │
                      │   ├─ services/* — 业务服务层          │
                      │   └─ 外部调用:                        │
                      │       ├─→ Postgres (asyncpg)          │
                      │       ├─→ Qdrant (向量检索)           │
                      │       └─→ Redis (缓存/会话)           │
                      └──────────────────────────────────────┘
                                      │
                                      ↓ Redis (NAS 主机上)
                                      │  - 缓存
                                      │  - Agent 会话状态
                                      │  - 任务队列

                                      ↓ LLM API (OpenAI 兼容)
                                         - 内容生成
                                         - 向量嵌入
                                         - AI 审核
```

### 请求生命周期（以一次 API 调用为例）

1. 用户在浏览器中触发操作（如"列出提示词模板"）
2. SPA 前端调用 `ApiClient.promptTemplate.list(workspace)`（`js/core/api-client.js`）
3. `ApiClient` 发送 `POST /api/tool` 到 `server.py`，附带 Cookie 会话
4. `server.py` 验证 Cookie → 从数据库获取用户 MCP Token
5. `server.py` 构建 JSON-RPC 请求，通过 SSE 发送到 `novel-os-mcp:8787/mcp`
6. `novel-os-mcp` 校验 Token 权限，执行对应工具函数
7. 工具函数通过 `asyncpg` 查询 PostgreSQL，将结果返回到 `server.py`
8. `server.py` 以 JSON 格式返回给前端
9. 前端更新 DOM 展示数据

---

## 两组件架构详解

### 组件 1：Python Web 服务器 + 纯 JavaScript SPA 前端

**运行容器**：`novel-os-web`

```
server.py (ThreadingHTTPServer)
├─ GET  /            → 返回 index.html (SPA 入口)
├─ GET  /spa         → 返回 spa.html
├─ GET  /js/*        → 静态 JS 文件
├─ GET  /css/*       → 静态 CSS 文件
├─ GET  /i18n/*      → 国际化 JSON
├─ GET  /health      → 健康检查
├─ GET  /api/me      → 当前用户认证状态
├─ POST /api/login   → 用户登录（pbkdf2/bcrypt）
├─ POST /api/logout  → 清除会话
├─ POST /api/setup   → 首次初始化（创建管理员）
├─ POST /api/tool    → **MCP 工具调用中继**（核心入口）
├─ POST /api/account → 密码修改
├─ POST /api/captcha → 数学验证码
├─ POST /api/register→ 用户注册
└─ POST /api/admin/setting → 管理员设置
```

**关键设计决策**：
- `server.py` 不是 REST 服务器——它唯一的业务 API 端点 `/api/tool` 是一个通用的 MCP 调用中继
- 所有功能调用统一通过 `ApiClient.callTool('tool.name', args)` → `/api/tool` → `novel-os-mcp`
- `server.py` 的核心角色是：**认证代理 + 静态文件服务 + MCP 中继**

### 组件 2：Python FastMCP SSE 后端

**运行容器**：`novel-os-mcp`

```
main.py
├─ FastMCP 服务器 (端口 8787, SSE 传输)
├─ tool_auth.py — API Token 认证中间件
├─ tools/
│   ├─ auth.py          — 认证与 Token 管理
│   ├─ kb.py            — 知识库 CRUD
│   ├─ memory.py        — 实体状态管理 (state.entity.*)
│   ├─ plot.py          — 情节管理 (伏笔/情节线/章节大纲)
│   ├─ prompt.py        — 提示词模板
│   ├─ model.py         — 模型配置
│   ├─ review.py        — AI 审核
│   ├─ setting.py       — 系统设置
│   ├─ skill.py         — 技能管理
│   ├─ graph.py         — 知识图谱
│   ├─ novel_gen.py     — 章节生成
│   ├─ novel_wizard.py  — 小说创建向导
│   ├─ discussion_room.py — 多人讨论室
│   ├─ system.py        — 系统工具 (health/cache/backup)
│   ├─ canon.py         — 正典管理
│   ├─ archive.py       — 归档
│   ├─ sync.py          — 同步
│   ├─ local.py         — 本地文件操作
│   ├─ admin.py         — 管理工具
│   └─ ...              — 更多工具模块
└─ services/
    ├─ workspace.py     — 工作区/项目管理
    ├─ memory.py        — 实体状态服务
    ├─ plot.py          — 情节服务
    ├─ review.py        — 审核服务
    ├─ canon.py         — 正典服务
    ├─ context.py       — 上下文组装
    ├─ backup.py        — 备份
    └─ ...              — 更多服务模块
```

---

## 关键设计决策

### 1. 无 REST 端点，全部通过 MCP callTool

系统中**不存在** `/api/users`、`/api/projects` 等 REST 端点。所有功能 API 调用统一走：

```
前端: ApiClient.callTool('user.list', args)
  → POST /api/tool { tool: "user.list", arguments: {...} }
  → server.py 中继到 MCP
  → novel-os-mcp 执行 user.list 工具
  → 返回结果到前端
```

这保证了前后端之间只有一种 API 模式，简化了调用链路和权限管理。

### 2. 无打包器/构建步骤

前端是**纯静态文件**，无需 Webpack、Vite 或任何构建工具：
- JavaScript 文件通过 `<script>` 标签直接加载
- CSS 通过 Tailwind CDN 引入
- 所有源码即部署文件，无需编译

### 3. 无 TypeScript

整个前端使用纯 JavaScript（IIFE 模块模式），目的是保持极简工具链，降低部署复杂度。

### 4. Python 服务器充当认证代理

`server.py` 不实现业务逻辑，它的核心职责是：
- 管理用户会话（Cookie-based）
- 为每个用户管理 MCP API Token
- 将经过认证的前端请求中继到 MCP 后端
- 这样 MCP 后端不需要处理浏览器会话，只需验证 API Token

### 5. 业务 Key 优于 UUID

API 调用中使用业务 Key（如 `template_key`、`username`）而非内部 UUID，提高可读性和调试效率。

---

## 外部依赖

### Redis

Redis 部署在 NAS 宿主机上（非容器化），用于：
- 请求缓存（减少数据库和 LLM 重复调用）
- Agent 会话状态保持
- 异步任务队列

连接信息通过 `.env` 环境变量配置：`REDIS_HOST`、`REDIS_PORT`、`REDIS_PASSWORD`、`REDIS_DB`。

### LLM API

Novel OS 通过 OpenAI 兼容协议调用外部 LLM API，用于：
- 章节内容生成
- 文本向量嵌入（embedding）
- AI 审核与质量评估
- 讨论室多角色对话

LLM 连接配置通过 `model.profile` 工具族管理，支持配置多个模型端点。

---

## 网络架构

```
Docker Network: novel_net
├─ 类型: bridge
├─ 子网: 172.20.0.0/16
├─ 成员:
│   ├─ novel-postgres  (内部 DNS: postgres)
│   ├─ novel-qdrant     (内部 DNS: qdrant)
│   ├─ novel-os-mcp     (内部 DNS: novel-os-mcp)
│   └─ novel-os-web     (内部 DNS: novel-os-web)
└─ 外部访问:
    ├─ 外部 → Nginx → :8790 (novel-os-web)
    └─ 外部 → :8787 (novel-os-mcp, 仅内部/Agent 直接调用)
```

容器间通过 Docker 内置 DNS 使用服务名互相访问（如 `novel-os-mcp:8787`、`postgres:5432`）。