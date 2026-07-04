# Novel OS MCP 开发规范交接

更新时间：2026-06-27

## 基本开发原则

- 先读现有代码和文档，再改。
- 复用现有服务风格，不为小功能引入新框架。
- 数据库 schema、服务层、MCP tool、文档、冒烟脚本必须同步推进。
- 每个工具都必须验证权限和 project 隔离。
- 不把正文、大纲、细纲、草稿等可编辑全文写入 MCP。
- 审查和合规可以阻断、提案、建任务，但不能自动改正文或硬 Canon。
- 不修改 NAS `/opt/novel-os` 之外的目录，除非用户重新明确授权。
- 不把密码、API key、`.env` 内容写进仓库或文档。

## 推荐开发顺序

新功能按这个顺序做：

```text
1. 更新或新增 SQL 迁移
2. 实现 services.py 中的 service method
3. 在 main.py 注册 MCP tool
4. 更新 docs/novel-os-mcp/tool-schema.md
5. 更新 novel-os-mcp/docs/TOOLS.md
6. 更新 docs/novel-os-mcp/development-plan.md
7. 新增或更新 deploy/nas/scripts/verify-*.sh
8. 本地 compileall
9. 同步 NAS
10. docker compose rebuild
11. 单项冒烟
12. 组合冒烟
13. 更新 handoff 文档或当前进度
```

## Python 代码规范

当前代码风格：

- Python 3.12 容器运行。
- 使用 `asyncpg`。
- 数据访问集中在 `services.py`。
- MCP tool 注册在 `main.py`。
- JSON 字段通过 `json_dumps` 写入，读取后用 `ensure_json_value` 兼容字符串/对象。
- DB row 转 dict 使用 `row_to_dict`、`rows_to_dicts`。
- 不要把复杂 SQL 拼接成字符串；优先使用参数化查询。

新增 service 时：

- 构造函数接收 `Database`，必要时接收其他 service。
- 方法返回结构化 dict/list。
- 不返回不可 JSON 序列化对象。
- 错误用 `ValueError` 给可读信息。
- 大量写操作用 transaction。
- 多项目查询必须加 `project_id = $1`。

## MCP Tool 规范

每个 tool 形态应类似：

```python
@mcp.tool(name="domain.action")
async def domain_action(workspace: str, project: str, ...):
    await db.connect()
    principal = await auth.current_principal()
    principal.require("read" or "write" or "admin")
    project_id = await auth.resolve_project_id(workspace, project, principal, access="write")
    return await service.method(project_id=project_id, ...)
```

只读工具：

```text
principal.require("read")
auth.resolve_project_id(..., principal)
```

写工具：

```text
principal.require("write")
auth.resolve_project_id(..., principal, access="write")
```

管理工具：

```text
principal.require("admin")
```

## 数据库迁移规范

新增迁移文件命名：

```text
deploy/nas/postgres/init/150_xxx.sql
deploy/nas/postgres/init/160_xxx.sql
```

规则：

- 不要编辑已有线上已执行迁移的语义，除非是补 `IF NOT EXISTS` 兼容。
- 不要删除字段。
- 不要改已有字段类型，除非有清晰迁移策略。
- 新增字段必须有合理默认值或允许 NULL。
- 对列表页、筛选页、上下文检索使用的字段加索引。
- 所有表尽量有 `project_id`。
- 所有项目级数据必须能 `ON DELETE CASCADE` 或有清理策略。

## 文档规范

新增或变更 MCP 工具时必须更新：

- [tool-schema.md](./tool-schema.md)
- [../../novel-os-mcp/docs/TOOLS.md](../../novel-os-mcp/docs/TOOLS.md)
- [development-plan.md](./development-plan.md)

如果改变架构或部署，更新：

- [handoff-architecture.md](./handoff-architecture.md)
- [handoff-deployment-runbook.md](./handoff-deployment-runbook.md)

如果改变下一步计划，更新：

- [HANDOFF.md](./HANDOFF.md)
- [handoff-current-state.md](./handoff-current-state.md)
- [handoff-next-tasks.md](./handoff-next-tasks.md)

## 验证规范

本地 Python 编译：

```text
python -m compileall novel-os-mcp/src
```

NAS 单项冒烟：

```text
cd /opt/novel-os
sh scripts/verify-phase2-xxx-tools.sh
```

Phase 2 组合冒烟：

```text
cd /opt/novel-os
sh scripts/verify-phase2-state-tools.sh &&
sh scripts/verify-phase2-plot-tools.sh &&
sh scripts/verify-phase2-foreshadowing-tools.sh &&
sh scripts/verify-phase2-rules-tools.sh &&
sh scripts/verify-phase2-context-tools.sh &&
sh scripts/verify-phase2-sync-tools.sh &&
sh scripts/verify-phase2-review-learning-tools.sh &&
sh scripts/verify-phase2-compliance-tools.sh &&
docker compose -f docker-compose.yml -f docker-compose.app.example.yml ps novel-os-mcp
```

新增 Phase 2.10 后应补：

```text
sh scripts/verify-phase2-model-cost-tools.sh
```

并加入组合冒烟。

## NAS 部署规范

只允许操作：

```text
/opt/novel-os
```

部署步骤：

```text
1. 复制变更文件到 /opt/novel-os 对应路径
2. cd /opt/novel-os
3. docker compose -f docker-compose.yml -f docker-compose.app.example.yml up -d --build novel-os-mcp
4. 运行单项冒烟
5. 运行组合冒烟
6. 检查 docker compose ps novel-os-mcp
```

不要在文档中记录 SSH 密码、数据库密码、Redis 密码、Qdrant key。

## 冒烟脚本规范

脚本放在：

```text
deploy/nas/scripts/
```

命名：

```text
verify-phase2-xxx-tools.sh
verify-phase3-xxx-web.sh
```

脚本必须：

- `set -eu`
- `cd /opt/novel-os`
- 使用容器内 Python 直接调用 service，避免依赖外部网络。
- 创建临时 workspace/project。
- 验证核心行为。
- finally 清理临时 workspace。
- 打印明确成功行，例如 `phase2 xxx tools smoke ok`。

## Web 开发规范

当前 Web 是简单 Python server + HTML，不是现代前端工程。

Phase 3 如果重构 Web：

- 保留登录和 token 机制。
- 保留调试工具，但不要把调试工具作为主界面。
- 页面必须支持中英文切换。
- Web 只维护 MCP 数据，不做小说初始化。
- 常用维护操作不应要求手写 JSON。
- 项目选择器是基础入口。
- 所有写操作应有确认或清晰反馈。

## 本地 Skill 开发规范

本地 skill 的职责：

- 初始化本地目录。
- 和用户沟通生成基础设定。
- 把结构化设定导入 MCP。
- 拉取上下文包。
- 调用用户配置的模型生成大纲/细纲/正文/审查。
- 保存本地文件。
- 提交结构化 commit、hash、摘要、审查报告。

本地 skill 不应：

- 把正文全文默认上传 MCP。
- 使用 MCP 服务器保存用户 API key。
- 静默覆盖本地文件。

## 安全规范

- 不记录 secrets。
- 不把 `.env` 加入文档或提交。
- 不打印用户 API key。
- 导出工程包时后续需要做脱敏。
- 合规和审查的 blocking 结果必须可追溯，有 audit log。

## 常见坑

- asyncpg 有时需要显式 cast，比如 `$1::uuid`。
- `Database` 封装当前没有 `fetchval`，需要 `fetchrow("SELECT count(*) AS count ...")`。
- 远端 NAS 只允许在 `/opt/novel-os` 操作。
- Web 功能还不完整，不能把“Web 能调 MCP tool”等同于“Web 后台已完成”。
- 审查提取的状态/伏笔建议目前是结构化返回，还未有完整人工采纳 UI。
