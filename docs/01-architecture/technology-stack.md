# 技术栈详解

## 总览

```
┌─────────────────────────────────────────────────────────────┐
│ 层      │ 技术                          │ 选型原因           │
├─────────┼───────────────────────────────┼────────────────────┤
│ 前端    │ Python 3 stdlib ThreadingHTTPServer │ 零依赖，足够简单  │
│         │ Vanilla JavaScript (IIFE)     │ 无构建步骤         │
│         │ Tailwind CSS CDN              │ 即用即走，无需配置  │
│         │ D3.js CDN (图谱可视化)        │ 仅需数据可视化时加载 │
│         │ Alpine.js CDN                │ 少量交互增强        │
├─────────┼───────────────────────────────┼────────────────────┤
│ 后端    │ Python 3.12                   │ 稳定，async 支持好  │
│         │ FastMCP >= 2.0.0              │ MCP 协议标准实现    │
│         │ asyncpg >= 0.29.0             │ 高性能异步 PostgreSQL│
│         │ Qdrant Client >= 1.9.0        │ 官方 Python 客户端  │
│         │ Redis >= 5.0.0                │ 缓存与任务队列      │
│         │ bcrypt >= 4.0.0               │ 密码散列           │
│         │ pydantic-settings >= 2.2.0    │ 配置管理           │
│         │ pydantic >= 2.7.0             │ 数据校验           │
├─────────┼───────────────────────────────┼────────────────────┤
│ 数据库  │ PostgreSQL 16 + pgvector      │ 关系型 + 向量双引擎 │
│         │ pg_trgm 扩展                  │ 模糊搜索/拼音      │
├─────────┼───────────────────────────────┼────────────────────┤
│ 向量库  │ Qdrant (latest)               │ 专用向量检索引擎    │
├─────────┼───────────────────────────────┼────────────────────┤
│ 缓存    │ Redis (NAS 宿主机)            │ 减少 LLM 重复调用   │
├─────────┼───────────────────────────────┼────────────────────┤
│ 部署    │ Docker Compose v2             │ 多容器编排          │
│         │ Nginx (SSL 终端)              │ 反向代理 + HTTPS    │
└─────────────────────────────────────────────────────────────┘
```

---

## 前端技术栈

### 服务端：Python 3 stdlib — `ThreadingHTTPServer`

```python
# novel-os-web/server.py — 入口
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

httpd = ThreadingHTTPServer((HOST, PORT), Handler)
httpd.serve_forever()
```

| 特性 | 说明 |
|------|------|
| **依赖** | 零外部依赖，纯 Python 标准库 |
| **并发模型** | 多线程（每个请求一个线程） |
| **路由** | 手动 if/elif 判断 `self.path` |
| **静态文件** | 手动读取 + Content-Type 设置 |
| **会话** | 自实现 Cookie 会话（HMAC 签名，7 天有效期） |
| **密码** | pbkdf2_sha256（自实现）+ bcrypt 兼容 |

**选型原因**：项目部署在 NAS Docker 上，追求最小依赖。用 Python stdlib 写 HTTP 服务避免了引入 Flask/FastAPI 等框架及其依赖树，`server.py` 逻辑非常简单（仅 ~730 行），不需要框架级抽象。

### JavaScript SPA 前端

| 技术 | 加载方式 | 用途 |
|------|----------|------|
| **Vanilla JavaScript** | `<script>` 标签直接引用 | 所有业务逻辑 |
| **Tailwind CSS** | CDN `<script src="...tailwind...">` | 全局样式 |
| **D3.js v7** | CDN | 知识图谱可视化 |
| **Alpine.js** | CDN（已加载，极少使用） | 少量声明式交互 |

#### IIFE 模块模式

所有 JS 文件使用 IIFE（立即执行函数）模式，挂载到 `window` 全局对象：

```javascript
(function() {
  'use strict';
  window.MyPage = {
    init() {
      this.render();
      this.loadData();
      return true;
    },
    // ...
  };
})();
```

**选型原因**：
- **无打包器**：不需要 webpack/vite/esbuild，源码即部署文件
- **IIFE 模式**：简单明确的模块隔离，无循环依赖风险
- **`window.XxxPage`**：方便路由直接引用 `window.XxxPage?.init()`

#### 核心 JS 模块

```
js/
├── core/
│   ├── api-client.js   # 统一 API 调用（MCP callTool 封装）
│   ├── app-core.js     # 应用状态管理（AppState）
│   ├── menu-manager.js # 三级菜单系统
│   ├── ~~router.js~~   # 已移除：原 Hash-based SPA 路由从未被注册调用，现由 index.html 内联 switch 承担
│   └── i18n.js         # 国际化（zh/en）
├── components/
│   ├── data-table.js   # 通用数据表格
│   └── modal-dialog.js # 模态对话框
└── pages/
    ├── template-list-page.js  # 标准化 CRUD 模板
    └── *.js                   # 各功能页面
```

#### 路由机制

Hash-based 路由，无历史 API 依赖：

```javascript
// 监听 hashchange
window.addEventListener('hashchange', handleRoute);

function handleRoute() {
  const hash = window.location.hash.slice(1) || 'home';
  switch (hash) {
    case 'template-list':
      window.TemplateListPage?.init() || showPlaceholder();
      break;
    // ...
  }
}
```

**关键规则**：所有页面 `init()` 必须返回 `true`，否则 `||` 短路会触发占位符回退。

#### Tailwind CSS

通过 CDN 引入，无需本地构建。使用 Tailwind 的 utility-first 类名直接在 HTML 模板字符串中写样式。

#### 国际化

```
i18n/
├── zh.json  # 中文翻译
└── en.json  # 英文翻译
```

通过 `window.I18n.t('menu.project')` 调用，当前语言保存在 `AppState.currentLang`。

---

## 后端技术栈

### Python 3.12

> `novel-os-mcp/pyproject.toml` 声明 `requires-python = ">=3.11"`

生产环境在 Docker 容器中运行 Python 3.12，利用其改进的 asyncio 性能和新语法特性。

### FastMCP >= 2.0.0

```python
from fastmcp import FastMCP

mcp = FastMCP("novel-os-mcp")

@mcp.tool(name="kb.entity.create")
async def kb_entity_create(workspace: str, project: str, ...):
    """创建知识库实体"""
    return await kb_service.create_entity(...)
```

FastMCP 是 MCP 协议的 Python 实现，提供：
- **SSE 传输**：Server-Sent Events，用于 `server.py` 到 MCP 的 JSON-RPC 通信
- **工具注册**：`@mcp.tool(name="xxx.yyy")` 声明式注册
- **参数校验**：基于 Pydantic 的自动类型验证和文档生成
- **认证**：自实现 API Key 中间件 (`tool_auth.py`)

### 核心依赖（from pyproject.toml）

| 包 | 版本 | 用途 |
|----|------|------|
| `fastmcp` | >= 2.0.0 | MCP 协议服务器框架 |
| `pydantic` | >= 2.7.0 | 数据模型与输入校验 |
| `pydantic-settings` | >= 2.2.0 | 环境变量 → 配置对象 |
| `asyncpg` | >= 0.29.0 | 异步 PostgreSQL 驱动 |
| `qdrant-client` | >= 1.9.0 | Qdrant 向量数据库客户端 |
| `redis` | >= 5.0.0 | Redis 客户端（缓存/会话/队列） |
| `bcrypt` | >= 4.0.0 | 密码散列（MCP 端用户认证） |
| `python-dotenv` | >= 1.0.1 | `.env` 文件加载 |

---

## 数据库技术栈

### PostgreSQL 16 + pgvector

| 组件 | 版本 | 用途 |
|------|------|------|
| **PostgreSQL** | 16 | 主力关系型数据库 |
| **pgvector** | pg16 配套 | 向量存储与相似度检索（`<=>` 操作符） |
| **pg_trgm** | 内置扩展 | 三元组模糊匹配（`ILIKE`、`similarity()`） |

**为什么用 pgvector 而不是纯 Qdrant？**
- 部分向量检索需求（如按项目过滤 + 向量搜索）可以和关系查询在同一个查询中完成
- pg_trgm 提供的模糊文本搜索对小规模数据比专用搜索引擎更轻量
- Qdrant 用于大规模知识库语义检索，两者互补

### Qdrant

专用向量数据库，用于：
- 知识库（KB）的语义检索
- 实体相似度匹配
- 跨项目知识推荐

通过 `qdrant-client` Python 库访问，支持 HTTP (6333) 和 gRPC (6334) 两种协议。

### Redis

部署在 NAS 宿主机上，MCP 端通过 `redis` Python 客户端连接用于：
- API 调用结果缓存（减少重复 LLM 查询）
- 工作流中间状态存储
- Agent 会话上下文存储

---

## 基础设施

### Docker Compose v2

```bash
cd /opt/novel-os
docker compose -f docker-compose.yml -f docker-compose.app.example.yml up -d
```

| 特性 | 说明 |
|------|------|
| **语法** | Compose v2（`docker compose`，无连字符） |
| **文件分离** | `docker-compose.yml`（基础设施：postgres/qdrant）+ `docker-compose.app.example.yml`（应用：mcp/web） |
| **网络** | `novel_net` bridge，子网 `172.20.0.0/16` |
| **数据持久化** | volumes 映射到 `./data/` 目录 |
| **资源限制** | CPU 和内存 limits/reservations 已配置 |

### Nginx 反向代理

Nginx 部署在 NAS 上，负责：
- SSL/TLS 终端（HTTPS）
- 反向代理 `:8790`（novel-os-web）
- 静态资源缓存

### 部署流程

1. 本地修改源文件
2. 通过 `pscp` 上传到 NAS 源码目录
3. 通过 `plink` 远程执行 Docker 重建命令
4. 容器重启后生效

> 容器内直接修改的文件在重启后会丢失，必须上传到宿主机源码目录后重建。