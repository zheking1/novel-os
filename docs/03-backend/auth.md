# 认证系统

## 概述

Novel OS 支持两种认证模式，通过环境变量 `NOVEL_OS_AUTH_MODE` 切换：

- **`dev` 模式**：开发调试用，读取 `NOVEL_OS_DEV_USER` / `NOVEL_OS_DEV_WORKSPACE` / `NOVEL_OS_DEV_SCOPES` 直接构造 Principal，跳过所有 Token 验证
- **`token` 模式**：生产模式，从 HTTP 请求头读取 API Key，SHA256 哈希后查库验证

---

## Principal 数据结构

```python
@dataclass(frozen=True)
class Principal:
    username: str         # 用户名
    workspace: str | None # 工作区 slug（Token 绑定的工作区，可为 None）
    project_id: str | None# 项目 UUID（Token 绑定的项目，可为 None）
    scopes: set[str]      # 权限集合：{"admin", "read", "write"}

    def require(self, scope: str) -> None:
        if "admin" not in self.scopes and scope not in self.scopes:
            raise PermissionError(f"Missing required scope: {scope}")
```

- `admin` scope 是超级权限，拥有 `admin` 则绕过所有读写检查
- `require()` 方法在工具函数入口处调用，确保调用者有足够权限

---

## Token 认证流程

### 1. 读取请求头

`_bearer_token()` 从 FastMCP 提供的 `get_http_headers(include={"apikey"})` 中读取：

```python
token = headers.get("apikey") or headers.get("apiKey") or headers.get("ApiKey") or ""
```

兼容大小写不敏感的 `apikey` / `apiKey` / `ApiKey` 请求头（兼顾不同 MCP 客户端的头部传递习惯）。未提供时报错提示用户在 Web UI 的「API Key 管理」中创建 Key。

### 2. 令牌验证

`_token_principal()` 执行：

1. 对原始 Token 做 SHA256 哈希：`sha256(token.encode("utf-8")).hexdigest()`
2. 查询数据库，JOIN 三表：

```sql
SELECT t.id AS token_id, t.scopes, t.project_id::text AS project_id,
       u.username, u.status AS user_status,
       w.slug AS workspace_slug
FROM api_tokens t
JOIN users u ON u.id = t.user_id
LEFT JOIN workspaces w ON w.id = t.workspace_id
WHERE t.token_hash = $1
  AND t.revoked_at IS NULL
  AND (t.expires_at IS NULL OR t.expires_at > now())
```

3. 验证条件：
   - `token_hash` 匹配
   - 未被撤销（`revoked_at IS NULL`）
   - 未过期（`expires_at IS NULL` 或 > 当前时间）
   - 用户状态为 `active`（`user_status == "active"`）

4. 成功时更新 `last_used_at`：`UPDATE api_tokens SET last_used_at = now() WHERE id = $1`

5. 从查询结果构造 `Principal(username, workspace, project_id, scopes)`

### 3. API Token Scopes

| Scope | 权限 |
|---|---|
| `admin` | 超级管理员，绕过所有 workspace/project 权限检查 |
| `read` | 只读访问 |
| `write` | 读写访问 |

Token 可绑定到特定 workspace（`workspace_id`）和 project（`project_id`），在权限检查时进一步限制范围。

---

## 权限检查

### require_workspace_access(principal, workspace_slug, access="read")

检查用户是否有权访问指定工作区：

1. `admin` scope → 直接通过
2. Token 绑定了特定 workspace 但请求不同的 workspace → 拒绝（"Token is scoped to workspace: xxx"）
3. 查 `workspace_members` 表，JOIN `users`，验证用户名匹配且状态为 `active`
4. `_role_allows(role, access)` 检查角色权限：

```python
def _role_allows(role, access):
    if access == "read":  return role in {"owner", "writer", "reader"}
    if access == "write": return role in {"owner", "writer"}
    return False
```

5. 失败时提供友好提示：列出用户有权限的所有 workspace

### require_project_access(principal, project_id, access="read")

检查用户是否有权访问指定项目：

1. `admin` scope → 直接通过
2. Token 绑定了特定 project 但请求不同的 project → 拒绝
3. 查 `project_members` 表，JOIN `users`，验证用户名 + `active` 状态
4. `_role_allows(role, access)` 检查角色

### resolve_project_id(workspace_slug, project_slug, principal, access)

综合权限检查和项目 ID 解析：

1. `require_workspace_access(principal, workspace_slug)`
2. 查 `projects JOIN workspaces` 通过 slug 找到 `project_id`
3. `require_project_access(principal, project_id, access)`

### resolve_workspace_id(principal, workspace_slug, access)

权限检查 + workspace ID 解析：
1. `require_workspace_access(principal, workspace_slug, access)`
2. 查 `workspaces` 返回 `id::text`

---

## Dev 模式

`current_principal()` 中当 `auth_mode == "dev"` 时：

```python
Principal(
    username=self._settings.dev_user,      # 默认 "admin"
    workspace=self._settings.dev_workspace, # 默认 "default"
    project_id=None,
    scopes=self._settings.dev_scope_set,    # 默认 {"admin", "read", "write"}
)
```

- 不读取任何 HTTP 请求头
- 不查询数据库
- project_id 始终为 None
- 建议仅开发和调试环境使用

---

## 工具认证辅助 (tool_auth.py)

为减少工具模块中的样板代码，提供两个辅助函数：

### get_principal(permission="read")

```python
async def get_principal(permission="read"):
    await db.connect()
    principal = await auth.current_principal()
    if permission:
        principal.require(permission)
    return principal
```

标准工具入口调用模式：
```python
principal = await get_principal("write")
workspace_id = await auth.resolve_workspace_id(principal, workspace, "write")
```

### validate_required(data, *fields)

```python
validate_required(data, "name", "description")
# 若 name 或 description 缺失/为空，抛出 ValueError
```

### validate_length(data, limits)

```python
validate_length(data, {"name": 100, "description": 500})
# 若字段超出 max_len，抛出 ValueError
```

---

## 密码系统

### 哈希方式

- **当前**：bcrypt（`$2b$...` 前缀）
- **Legacy 支持**：pbkdf2_sha256

### 默认密码

`123456` — 所有默认用户的初始密码，首次登录后建议修改。

### 用户认证

用户认证（`auth.login`、`auth.change_password`）在 `tools/auth.py` 中实现，读取 `users` 表的 `password_hash` 字段，根据前缀判断哈希算法进行验证。

---

## 安全设计要点

- Token 以 SHA256 哈希存储于 `api_tokens.token_hash`，数据库中不存原文
- Token 支持过期时间和撤销机制（`expires_at` / `revoked_at`）
- 每次使用更新 `last_used_at`，可用于审计和自动过期未活跃 Token
- 拒绝已禁用用户（`user_status != 'active'`）的 Token
- dev 模式和 token 模式严格隔离，不可同时生效