# 开发规则总汇

## 会话规则（强制）

1. **执行前确认** — 任何代码修改前等待用户说 "开始"、"执行" 或等同意确认。未确认前不编辑文件。
2. **先写设计文档** — 非平凡功能（预计 >30 分钟）需先写设计文档，展示给用户审核后再编码。
3. **每会话必读文档** — 开工前读 `development-guide.md`、`api-conventions.md`、`troubleshooting.md`。

## API 调用规则

1. **所有功能 API 使用 `ApiClient.callTool('tool.name', args)`** — 没有 REST 端点
2. `ApiClient.request()` 签名: `request(method, endpoint, data, options)` — **method 在前，不是 `request(endpoint, options)`**
3. `ApiClient.baseUrl` 是 `/api`，端点**不能**包含 `/api` 前缀
4. **项目参数自动注入** — `api-client.js` 从 `AppState.currentProject` 自动注入

## MCP 工具规则

| 规则 | 说明 |
|------|------|
| 工具名用点 | `user.create` 而非 `user_create` |
| MCP 源文件位置 | NAS 的 `/opt/novel-os/novel-os-mcp/src/`，不能在容器内编辑 |
| 重建 MCP | `docker build --no-cache -t novel-os-mcp:latest` |
| 无 `@validate_call` | 该装饰器不存在，不要使用 |
| Delete 返回 dict | `return {"ok": deleted, "key": key}` 而非 `return bool` |
| 用户 FK 级联 | 始终使用 `ON DELETE CASCADE` 或 `ON DELETE SET NULL` |
| workflow_guide | 核心工具返回 `workflow_guide`，AI 据此知道下一步 |

## 前端规则

1. `init()` 必须返回 `true` — 否则触发 `placeholder` 后备
2. `ModalDialog.show()` 不返回 boolean — 使用 `onConfirm` 回调模式，回调内调用 `ModalDialog.close()`
3. 使用业务键 (`template_key`) 而非 UUID 进行 API 调用
4. Workspace/Project 持久化到 localStorage（key: `novel-workspace`、`novel-project`）

## 部署规则

1. 先上传到源目录，再重建容器
2. 使用 `docker compose`（v2），非 `docker-compose`
3. JS 变更 → Web 容器重建；Python 变更 → MCP 容器重建
4. 容器重启丢失非持久化文件

## 数据库

- 用户: `novel_os`，密码: `${POSTGRES_PASSWORD}`，数据库: `novel_os`
- SQL 查询通过文件上传（PowerShell 引号有问题）