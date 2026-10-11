# MCP 后端架构

## 概述

Novel OS MCP 后端基于 FastMCP 框架构建，以 HTTP/SSE 协议对外暴露工具调用。整个服务通过 `main.py` 启动，核心流程为：FastMCP 服务器创建 → Redis 会话持久化 → 工具模块注册 → 工具白名单过滤 → 资源注册 → 启动 HTTP 传输。

---

## 主入口 (main.py)

### FastMCP 服务器

`mcp_core.py` 创建全局单例 FastMCP 实例：

```python
mcp = FastMCP("novel-os-mcp", mask_error_details=False, instructions="...")
```

FastMCP 是一个基于 Starlette 的 MCP（Model Context Protocol）服务器框架，以 HTTP 传输模式运行（`mcp.run(transport="http", ...)`），支持 SSE（Server-Sent Events）和 Streamable HTTP 两种传输方式。每个 `@mcp.tool()` 装饰的函数自动注册为可调用的 MCP 工具。

### SSE 会话持久化 (Redis)

为应对容器重启导致客户端会话丢失的问题，`main.py` 使用两套 Redis 数据库实现会话持久化：

1. **Redis db=1 — 状态存储**：使用 `key_value` 库的 `RedisStore` + `PydanticAdapter` 替换 FastMCP 默认的内存状态存储（`mcp._state_storage` 和 `mcp._state_store`），使 FastMCP 内部状态在重启后仍可恢复。

2. **Redis db=2 — Streamable HTTP 会话跟踪**：通过 monkey-patch `StreamableHTTPSessionManager` 的两个核心方法：
   - `create_transport`：创建 transport 后在 Redis 中记录 `mcp_sess:{session_id}` 键（TTL 86400 秒）
   - `handle_request`：处理请求时，若内存中未找到会话但 Redis 中会话键仍存在（说明容器重启但会话未过期），返回 JSON-RPC 错误提示客户端重新 `initialize()`

所有 Redis 相关代码均包裹在 try/except 中，初始化失败时回退到内存模式。

### 工具白名单过滤

环境变量 `NOVEL_OS_MCP_TOOL_WHITELIST` 支持逗号分隔的工具前缀列表。`apply_tool_filter()` 在工具注册完成后遍历 `mcp._tool_manager._tools`，移除不匹配任何前缀的工具。未设置该环境变量时不过滤。

### 启动流程

1. `config.py` 加载所有环境变量配置
2. `mcp_core.py` 创建 FastMCP 实例 → 注册 `instructions`
3. Redis 会话/状态存储初始化（db=1, db=2）
4. `tools/__init__.py` 导入全部工具模块 → 触发 `@mcp.tool()` 装饰器注册
5. `apply_tool_filter()` 执行白名单过滤
6. `resources` 导入 → `@mcp.resource()` 注册
7. `mcp.run(transport="http", host=..., port=...)` 启动 Starlette HTTP 服务

---

## 配置 (config.py)

`Settings` 类基于 `pydantic_settings.BaseSettings`，支持 `.env` 文件和环境变量，所有配置项及默认值：

| 配置项 | 环境变量 | 默认值 | 说明 |
|---|---|---|---|
| `database_url` | `DATABASE_URL` | —（必填） | PostgreSQL 连接串 |
| `qdrant_url` | `QDRANT_URL` | `http://localhost:6333` | Qdrant 向量库地址 |
| `qdrant_api_key` | `QDRANT_API_KEY` | `None` | Qdrant API 密钥 |
| `qdrant_memory_collection` | `QDRANT_MEMORY_COLLECTION` | `novel_memory_chunks` | 记忆分块集合名 |
| `qdrant_reference_collection` | `QDRANT_REFERENCE_COLLECTION` | `novel_reference_chunks` | 参考材料分块集合名 |
| `redis_host` | `REDIS_HOST` | `127.0.0.1` | Redis 主机 |
| `redis_port` | `REDIS_PORT` | `6379` | Redis 端口 |
| `redis_db` | `REDIS_DB` | `0` | Redis 数据库编号 |
| `redis_password` | `REDIS_PASSWORD` | `None` | Redis 密码 |
| `auth_mode` | `NOVEL_OS_AUTH_MODE` | `dev` | 认证模式：`dev` / `token` |
| `dev_user` | `NOVEL_OS_DEV_USER` | `admin` | 开发模式默认用户名 |
| `dev_workspace` | `NOVEL_OS_DEV_WORKSPACE` | `default` | 开发模式默认工作区 |
| `dev_scopes` | `NOVEL_OS_DEV_SCOPES` | `admin,read,write` | 开发模式权限范围 |
| `host` | `NOVEL_OS_HOST` | `0.0.0.0` | 服务监听地址 |
| `port` | `NOVEL_OS_PORT` | `8787` | 服务端口 |
| `log_level` | `LOG_LEVEL` | `INFO` | 日志级别 |

额外属性：
- `redis_url`：拼接 Redis 连接字符串（含认证信息）
- `dev_scope_set`：解析 `dev_scopes` 为 `set[str]`

使用 `@lru_cache(maxsize=1)` 缓存 `get_settings()` 返回的单例配置。

---

## 数据库 (db.py)

`Database` 类封装 asyncpg 连接池：

- **连接池**：`asyncpg.create_pool(dsn, min_size=1, max_size=10)`
- **核心方法**（均自动 acquire/release 连接）：
  - `fetchrow(query, *args)` — 获取单行
  - `fetch(query, *args)` — 获取多行
  - `fetchval(query, *args)` — 获取标量值
  - `execute(query, *args)` — 执行写操作，返回命令状态字符串
- `acquire()` — 返回 `async with` 上下文管理器，供需要事务的场景使用

连接信息来自 `DATABASE_URL` 配置项。池未初始化时访问 `pool` 属性抛出 `RuntimeError`。

---

## 依赖注入 (deps.py)

`deps.py` 作为集中式的依赖注入模块，按依赖顺序实例化所有服务。所有服务实例均为模块级单例，供 `tools/` 模块直接 `from .deps import xxx` 引用。

### 完整服务实例化顺序（44+ 服务）

```
settings → db → auth
├── workspace_service = WorkspaceService(db)
├── canon_service = CanonService(db)
├── rules_service = RulesService(db)
├── compliance_service = ComplianceService(db, rules_service)
├── plot_service = PlotService(db)
├── vector_index = VectorIndex(settings)
├── embedding_service = EmbeddingService(db)
├── rerank_service = RerankService(db)
├── memory_service = MemoryService(db, embedding_service, vector_index)
├── character_arc_service = CharacterArcService(db)
├── causality_service = CausalityService(db)
├── pacing_service = PacingService(db)
├── style_fingerprint_service = StyleFingerprintService(db)
├── context_service = ContextService(db, memory, rules, plot,
│       embedding_service, rerank_service, character_arc_service,
│       causality_service, pacing_service, style_fingerprint_service)
├── review_service = ReviewService(db)
├── workflow_service = WorkflowService(db)
├── reference_service = ReferenceService(db)
├── sync_service = SyncService(db)
├── model_cost_service = ModelCostService(db)
├── global_settings_service = GlobalSettingsService(db)
├── vector_index_service = VectorIndexService(db)
├── cache_service = CacheService(settings)
├── archive_service = ArchiveService(db)
├── backup_service = BackupService(db)
├── kb_service = KBService(db)
├── prompt_template_service = PromptTemplateService(db)
├── context_weight_service = ContextWeightService(db)
├── reference_material_service = ReferenceMaterialService(db)
├── reader_expectation_service = ReaderExpectationService(db)
├── chapter_annotation_service = ChapterAnnotationService(db)
├── proper_noun_service = ProperNounService(db)
├── fulltext_search_service = FulltextSearchService(db)
├── llm_client = LLMClient(db)
├── context_compression_service = ContextCompressionService(db, llm_client)
├── multipass_service = MultiPassService(db)
├── novelty_service = NoveltyService(db, vector_index)
├── graph_service = RelationshipGraphService(db)
├── local_service = LocalService(db)
├── skill_service = SkillService(db)
├── knowledge_audit_service = KnowledgeAuditService(db, llm_client)
├── knowledge_council_service = KnowledgeCouncilService(db, llm_client)
├── gatekeeper_service = GatekeeperService(db)
├── init_ai_reviewer(llm_client)  -- 初始化AI审阅器
└── _health_service = DependencyHealthService(settings)
└── _degradation_service = DegradationModeService(settings)
```

关键依赖链：
- `EmbeddingService(db)` / `RerankService(db)` → `MemoryService` → `ContextService`
- `LLMClient(db)` → `ContextCompressionService`、`KnowledgeAuditService`、`KnowledgeCouncilService`
- `RulesService(db)` → `ComplianceService`、`ContextService`
- `VectorIndex(settings)` → `NoveltyService`、`MemoryService`

---

## 工具注册 (tools/)

`tools/__init__.py` 一次性导入全部 30 个工具模块：

```python
from . import admin, auth, canon, plot, memory, context
from . import review, kb, setting, model, vector, system
from . import prompt, novel_gen, archive, sync, reference, graph, local, knowledge_pack, skill, novel_wizard
from . import system_evolution, system_assets, system_notifications, discussion_room, global_rules, evolution
```

每个工具模块内部使用 `from ..mcp_core import mcp` 获取 FastMCP 实例，然后通过 `@mcp.tool()` 装饰器注册工具。FastMCP 的 `@mcp.tool()` 自动将函数签名转换为 JSON Schema 输入参数，返回值序列化为 JSON 输出。

---

## 请求流程

完整的请求流程（从前端 Web UI 到工具执行）：

```
┌──────────────────┐
│   Web UI 前端    │  ApiClient.callTool("tool.name", args)
└────────┬─────────┘
         │ POST /api (JSON-RPC via SSE/Streamable HTTP)
         ▼
┌──────────────────┐
│  novel-os-web     │  Nginx 反向代理 → Starlette 路由
│  (前端容器)       │  /mcp → MCP HTTP handler
└────────┬─────────┘
         │ HTTP POST (JSON-RPC 2.0)
         ▼
┌──────────────────────────────────────────────┐
│  FastMCP Server (novel-os-mcp)               │
│                                               │
│  1. StreamableHTTPSessionManager             │
│     ├─ 检查 Redis db=2 会话有效性             │
│     └─ 创建/恢复 transport                    │
│                                               │
│  2. FastMCP 路由 → tool_name 匹配            │
│     ├─ 参数解析 (JSON → Python)              │
│     └─ 调用被 @mcp.tool() 装饰的函数          │
│                                               │
│  3. Tool 函数内部：                           │
│     ├─ get_principal(permission)              │
│     │   ├─ db.connect()                        │
│     │   ├─ auth.current_principal()            │
│     │   │   ├─ mode=="dev" → Principal(...)   │
│     │   │   └─ mode=="token" → 读 header 验证 │
│     │   └─ principal.require(permission)       │
│     ├─ 业务逻辑 (调用 deps 中的 service)      │
│     └─ 返回 dict (含 workflow_guide)          │
│                                               │
│  4. 响应序列化 → JSON-RPC Result              │
└──────────────────────────────────────────────┘
```

### 关键特性

- **workflow_guide**：每个工具返回值包含 `workflow_guide.steps`，指导 AI 客户端按步骤调用后续工具
- **错误透传**：`mask_error_details=False`，异常信息完整返回给客户端
- **无状态工具**：工具函数每次调用都独立连接 DB、验证认证、执行业务逻辑