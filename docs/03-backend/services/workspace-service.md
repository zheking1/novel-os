# Workspace 服务 — 用户与工作空间管理

**源码**: `novel-os-mcp/src/novel_os_mcp/services/workspace.py` (491 行)

## 概述

Workspace 服务管理用户、工作空间、项目、API Token 和本地绑定的全生命周期。

## 数据库表

| 表名 | 说明 |
|------|------|
| `users` | 用户 |
| `workspaces` | 工作空间 |
| `workspace_members` | 工作空间成员 |
| `projects` | 项目 |
| `project_members` | 项目成员 |
| `api_tokens` | API 令牌 |
| `local_project_bindings` | 本地项目绑定 |

---

## 一、用户管理 (Users)

### create_user

创建或更新用户（`ON CONFLICT (username)`）。

| 字段 | 默认值 | 说明 |
|------|------|------|
| `username` | - | 用户名 (唯一) |
| `display_name` | `username` | 显示名称 |
| `email` | None | 邮箱 |
| `status` | `"active"` | 状态 |
| `password_hash` | None | bcrypt 密码哈希 |

> 默认密码 `123456` → bcrypt hash: `$2b$10$92IXUNpkjO0rOQ5byMi.Ye4oKoEa3Ro9llC/.og/at2.uheWG/igi`

### ensure_user_exists

幂等创建用户。若用户已存在则无操作（`ON CONFLICT DO NOTHING`）。

### list_users

列出用户，支持 `status` 过滤。排除 `is_deleted=true` 的用户。

### delete_user

软删除 (`is_deleted = true`)。

---

## 二、工作空间管理 (Workspaces)

### create_workspace

创建或更新工作空间（`ON CONFLICT (slug)`）:

- 若 `owner_username` 不存在，自动创建用户
- 自动添加 owner 为 workspace member（`role='owner'`）
- 使用数据库事务保证原子性

### list_workspaces

列出活跃工作空间。支持按 `username` 过滤（JOIN `workspace_members`）。

### add_workspace_member

添加成员:

| 角色 | 说明 |
|------|------|
| `owner` | 所有者 (全权限) |
| `writer` | 写作者 |
| `reader` | 只读 |

### remove_workspace_member

物理删除成员关系。

### delete_workspace

软删除 (`is_deleted = true`)。

---

## 三、项目管理 (Projects)

### create_project

创建或更新项目（`ON CONFLICT (workspace_id, slug)`）:

- 验证 workspace 和 user 存在
- 自动添加 owner 为 project member

### list_projects

列出工作空间下的项目，支持按 `username` 过滤。

### list_project_members

列出项目成员详情（JOIN users, projects, workspaces）。

### add_project_member

添加项目成员:

- 自动将用户以 `reader` 角色加入工作空间（如尚未加入）
- 以指定角色加入项目

### delete_project

软删除 (`is_deleted = true`)。

---

## 四、API Token 管理

### create_api_token

创建 API Token:

| 参数 | 说明 |
|------|------|
| `name` | Token 名称 |
| `scopes` | 权限范围列表 |
| `workspace_slug` | 限定工作空间 (可选) |
| `project_slug` | 限定项目 (可选, 需 workspace) |
| `expires_at` | 过期时间 |

**Token 格式**: `nos_` + 32 字节 URL-safe base64 随机串

**存储**: 仅存 SHA256 哈希值（非明文 token）。

**自动操作**:
- 自动添加用户为 workspace member (`writer`)，若指定 workspace
- 自动添加用户为 project member (`writer`)，若指定 project

**返回**: 仅创建时返回明文 token，之后不可再获取。

### list_api_tokens

列出 Token，支持 `username`、`workspace_slug`、`project_slug` 过滤。

默认排除已吊销的 token。

### revoke_api_token

吊销 Token (设置 `revoked_at`)，幂等（已吊销则不变）。

---

## 五、本地绑定 (Local Binding)

### register_local_binding

注册本地客户端与项目的绑定关系:

| 字段 | 说明 |
|------|------|
| `client_id` | 客户端标识 |
| `local_root_hint` | 本地根目录提示 |
| `manifest` | JSONB 目录清单 |

唯一键: `(project_id, user_id, client_id)`。

**用途**: 关联桌面客户端与服务器端项目，用于文件同步和索引一致性。

---

## 六、开发辅助

### ensure_dev_user

确保开发者用户和工作空间存在:

1. 创建用户 (`ON CONFLICT update updated_at`)
2. 创建工作空间 (owner=user)
3. 添加 workspace member (role='owner')

---

## 工作流引导

**初始化**:
1. `user.create()` → 创建用户
2. `workspace.create(slug, name, owner)` → 创建工作空间

**项目设置**:
3. `project.create(workspace_slug, project_slug, title, owner)` → 创建项目
4. `project.add_member()` → 添加协作者

**API 访问**:
5. `api_token.create(username, name, scopes, workspace, project)` → 生成 Token
6. 客户端使用 `nos_xxx` token 访问 API
7. `api_token.revoke()` → 吊销 Token

**本地开发**:
8. `local.register_binding()` → 绑定本地客户端