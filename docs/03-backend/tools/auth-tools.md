# Auth & User/Workspace/Project Tools

> Source: `novel-os-mcp/src/novel_os_mcp/tools/auth.py`
> Dependencies: `db`, `auth`, `workspace_service`, `get_principal`, `validate_required`

---

## auth.whoami

```python
@mcp.tool(name="auth.whoami")
async def auth_whoami() -> dict[str, Any]
```

**Purpose:** Get current user identity, scopes, and auth mode.

**Parameters:** None

**Returns:** `{username, workspace, project_id, scopes: [...], auth_mode}`

**Logic:** Calls `get_principal(None)` — no scope requirement.

---

## auth.login

```python
@mcp.tool(name="auth.login")
async def auth_login(username: str, password: str) -> dict[str, Any]
```

**Purpose:** Verify user credentials and update `last_login_at`.

**Parameters:**
- `username: str` — Username
- `password: str` — Plaintext password

**Returns:** `{id, username, display_name, email, status, created_at, updated_at}` (excludes `password_hash`)

**DB Tables:** `users`

**Logic:**
1. Fetch user row from `users` WHERE `username = $1`
2. Verify password via `bcrypt.checkpw()`
3. Update `last_login_at = now()`
4. Return user info (no hash)

---

## auth.change_password

```python
@mcp.tool(name="auth.change_password")
async def auth_change_password(username: str, old_password: str, new_password: str) -> dict[str, Any]
```

**Purpose:** Change a user password. User can change their own; admin can change anyone.

**Parameters:**
- `username: str`
- `old_password: str` — Current password for verification
- `new_password: str` — New password

**Returns:** `{ok: True, username, message}`

**Logic:**
1. Verify caller is `username` OR admin
2. If self: verify `old_password` matches stored hash
3. Hash `new_password` via bcrypt (rounds=10)
4. Update `users.password_hash`

---

## auth.create_api_token

```python
@mcp.tool(name="auth.create_api_token")
async def auth_create_api_token(
    name: str, scopes: list[str],
    username: str | None = None, workspace: str | None = None,
    project: str | None = None, expires_at: str | None = None,
) -> dict[str, Any]
```

**Purpose:** Create API token with specified scopes. Regular users create for self; admins can create for anyone.

**Parameters:**
- `name: str` — Token name
- `scopes: list[str]` — Permission scopes
- `username: str?` — Target user (admin only)
- `workspace: str?` — Scope to specific workspace
- `project: str?` — Scope to specific project
- `expires_at: str?` — Expiry timestamp

**Logic:** Ensures target user exists via `ensure_user_exists()`, then calls `workspace_service.create_api_token()`.

---

## auth.list_api_tokens

```python
@mcp.tool(name="auth.list_api_tokens")
async def auth_list_api_tokens(
    workspace: str | None = None, project: str | None = None,
    include_revoked: bool = False,
) -> list[dict[str, Any]]
```

**Purpose:** List API tokens. Admin sees all; regular users see own only.

**Parameters:**
- `workspace: str?` — Filter by workspace
- `project: str?` — Filter by project
- `include_revoked: bool` — Include revoked tokens

---

## auth.revoke_api_token

```python
@mcp.tool(name="auth.revoke_api_token")
async def auth_revoke_api_token(token_id: str) -> dict[str, Any]
```

**Purpose:** Revoke an API token. Admin only. Token becomes immediately invalid and cannot be recovered.

---

## user.create

```python
@mcp.tool(name="user.create")
async def user_create(
    username: str, display_name: str | None = None,
    email: str | None = None, status: str = "active",
    password: str | None = None,
) -> dict[str, Any]
```

**Purpose:** Create new user (admin only).

**Parameters:**
- `username: str` — Unique identifier
- `display_name: str?`
- `email: str?`
- `status: str` — Default "active"
- `password: str?` — If empty, defaults to `123456`

**Logic:** Hash password via bcrypt, call `workspace_service.create_user()`.

---

## user.list

```python
@mcp.tool(name="user.list")
async def user_list(status: str | None = None, limit: int = 100) -> list[dict[str, Any]]
```

**Purpose:** List users (admin only). Can filter by status.

---

## user.delete

```python
@mcp.tool(name="user.delete")
async def user_delete(username: str) -> dict[str, Any]
```

**Purpose:** Delete user (admin only).

---

## workspace.create

```python
@mcp.tool(name="workspace.create")
async def workspace_create(slug: str, name: str) -> dict[str, Any]
```

**Purpose:** Create new workspace. `slug` = unique ID, `name` = display name.

**Scope:** `write`

---

## workspace.list

```python
@mcp.tool(name="workspace.list")
async def workspace_list(username: str | None = None) -> list[dict[str, Any]]
```

**Purpose:** List workspaces. Non-admin users only see their own workspaces (username auto-restricted).

---

## workspace.add_member

```python
@mcp.tool(name="workspace.add_member")
async def workspace_add_member(workspace: str, username: str, role: str = "writer") -> dict[str, Any]
```

**Purpose:** Add member to workspace. `role`: admin / writer / reader (default writer).

---

## workspace.remove_member

```python
@mcp.tool(name="workspace.remove_member")
async def workspace_remove_member(workspace: str, username: str) -> dict[str, Any]
```

**Purpose:** Remove member from workspace. Scope: `write`.

---

## workspace.delete

```python
@mcp.tool(name="workspace.delete")
async def workspace_delete(slug: str) -> dict[str, Any]
```

**Purpose:** Delete workspace. Requires write access to the workspace.

---

## project.create

```python
@mcp.tool(name="project.create")
async def project_create(workspace: str, slug: str, title: str, description: str | None = None) -> dict[str, Any]
```

**Purpose:** Create project in workspace. Requires write + workspace access.

---

## project.list

```python
@mcp.tool(name="project.list")
async def project_list(workspace: str, username: str | None = None) -> list[dict[str, Any]]
```

**Purpose:** List projects in workspace. Non-admin restricted to own projects.

---

## project.delete

```python
@mcp.tool(name="project.delete")
async def project_delete(workspace: str, slug: str) -> dict[str, Any]
```

**Purpose:** Delete project. Requires write + workspace access.

---

## project.add_member

```python
@mcp.tool(name="project.add_member")
async def project_add_member(workspace: str, project: str, username: str, role: str = "writer") -> dict[str, Any]
```

**Purpose:** Add project member (admin only). Overrides workspace-level permissions.

---

## project.list_members

```python
@mcp.tool(name="project.list_members")
async def project_list_members(workspace: str, project: str) -> list[dict[str, Any]]
```

**Purpose:** List project members (admin only).

---

## project.register_local_binding

```python
@mcp.tool(name="project.register_local_binding")
async def project_register_local_binding(
    workspace: str, project: str, client_id: str,
    local_root_hint: str | None = None,
    manifest: dict[str, Any] | None = None,
) -> dict[str, Any]
```

**Purpose:** Register local client with project for file sync. Scope: `write`.

---

## Password Hashing

```python
def hash_password(password: str) -> str:
    return bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt(rounds=10)).decode("ascii")

def verify_password(password: str, hashed: str) -> bool:
    return bcrypt.checkpw(password.encode("utf-8"), hashed.encode("ascii"))
```

Default password: `123456`. Hash format: bcrypt (`$2b$...`).
