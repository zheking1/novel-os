# User & Workspace 表详细设计

> 域：User & Workspace / 子域：用户账户、工作区、成员、API 令牌、本地绑定
>
> 共 6 张表。

---

## 1. users

**用途**：用户账户 — 用户名、密码散列、显示名、邮箱、角色、状态。

| 列名 | 类型 | 约束 | 描述 |
|------|------|------|------|
| `id` | `UUID` | **PK**, DEFAULT `gen_random_uuid()` | 主键 |
| `username` | `VARCHAR(100)` | NOT NULL, **UNIQUE** | 用户名（登录用） |
| `password_hash` | `VARCHAR(255)` | NOT NULL | 密码散列（bcrypt 或 pbkdf2_sha256） |
| `display_name` | `VARCHAR(255)` | 可空 | 显示名称 |
| `email` | `VARCHAR(255)` | 可空, **UNIQUE** | 邮箱地址 |
| `role` | `VARCHAR(50)` | DEFAULT `use` | 角色：admin / user / viewer |
| `status` | `VARCHAR(50)` | DEFAULT `activ` | 状态：active / disabled / locked |
| `remark` | `TEXT` | 可空 | 备注 |
| `avatar_url` | `TEXT` | 可空 | 头像 URL |
| `last_login_at` | `TIMESTAMPTZ` | 可空 | 最后登录时间 |
| `created_at` | `TIMESTAMPTZ` | DEFAULT `now()` | 创建时间 |
| `updated_at` | `TIMESTAMPTZ` | DEFAULT `now()` | 更新时间 |

**索引**：
- `idx_users_username` ON (`username`)
- `idx_users_status` ON (`status`)

---

## 2. workspaces

**用途**：工作区 — 名称、描述、所有者、可见性设置。

| 列名 | 类型 | 约束 | 描述 |
|------|------|------|------|
| `id` | `UUID` | **PK**, DEFAULT `gen_random_uuid()` | 主键 |
| `name` | `VARCHAR(255)` | NOT NULL, **UNIQUE** | 工作区名称 |
| `description` | `TEXT` | 可空 | 工作区描述 |
| `owner_id` | `UUID` | **FK** → `users(id)`, NOT NULL | 所有者 |
| `visibility` | `VARCHAR(50)` | DEFAULT `privat` | 可见性：private / team / public |
| `settings` | `JSONB` | DEFAULT `{}` | 工作区设置（JSON） |
| `created_at` | `TIMESTAMPTZ` | DEFAULT `now()` | 创建时间 |
| `updated_at` | `TIMESTAMPTZ` | DEFAULT `now()` | 更新时间 |

**索引**：`idx_workspaces_owner` ON (`owner_id`)

---

## 3. workspace_members

**用途**：工作区成员 — 用户-工作区关联、角色。

| 列名 | 类型 | 约束 | 描述 |
|------|------|------|------|
| `id` | `UUID` | **PK**, DEFAULT `gen_random_uuid()` | 主键 |
| `workspace_id` | `UUID` | **FK** → `workspaces(id)` ON DELETE CASCADE, NOT NULL | 关联工作区 |
| `user_id` | `UUID` | **FK** → `users(id)` ON DELETE CASCADE, NOT NULL | 关联用户 |
| `role` | `VARCHAR(50)` | DEFAULT `member`, NOT NULL | 角色：owner / admin / member / viewer |
| `joined_at` | `TIMESTAMPTZ` | DEFAULT `now()` | 加入时间 |
| `invited_by` | `UUID` | 可空，**FK** → `users(id)` | 邀请人 |

**唯一约束**：`uq_workspace_members` UNIQUE (`workspace_id`, `user_id`)

**索引**：
- `idx_workspace_members_workspace` ON (`workspace_id`)
- `idx_workspace_members_user` ON (`user_id`)

---

## 4. project_members

**用途**：项目成员 — 用户-项目关联、角色。

| 列名 | 类型 | 约束 | 描述 |
|------|------|------|------|
| `id` | `UUID` | **PK**, DEFAULT `gen_random_uuid()` | 主键 |
| `project_id` | `UUID` | **FK** → `projects(id)` ON DELETE CASCADE, NOT NULL | 关联项目 |
| `user_id` | `UUID` | **FK** → `users(id)` ON DELETE CASCADE, NOT NULL | 关联用户 |
| `role` | `VARCHAR(50)` | DEFAULT `editor`, NOT NULL | 角色：owner / editor / viewer |
| `permissions` | `JSONB` | DEFAULT `{}` | 细粒度权限（JSON） |
| `joined_at` | `TIMESTAMPTZ` | DEFAULT `now()` | 加入时间 |
| `invited_by` | `UUID` | 可空，**FK** → `users(id)` | 邀请人 |

**唯一约束**：`uq_project_members` UNIQUE (`project_id`, `user_id`)

**索引**：
- `idx_project_members_project` ON (`project_id`)
- `idx_project_members_user` ON (`user_id`)

---

## 5. api_tokens

**用途**：用户 API 令牌 — 令牌散列、名称、权限范围、过期时间。

| 列名 | 类型 | 约束 | 描述 |
|------|------|------|------|
| `id` | `UUID` | **PK**, DEFAULT `gen_random_uuid()` | 主键 |
| `user_id` | `UUID` | **FK** → `users(id)` ON DELETE CASCADE, NOT NULL | 关联用户 |
| `name` | `VARCHAR(255)` | NOT NULL | 令牌名称 |
| `token_hash` | `VARCHAR(255)` | NOT NULL, **UNIQUE** | 令牌散列值 |
| `prefix` | `VARCHAR(20)` | 可空 | 令牌前缀（用于 UI 显示） |
| `scopes` | `TEXT[]` | DEFAULT `{}` | 权限范围列表 |
| `expires_at` | `TIMESTAMPTZ` | 可空 | 过期时间（空 = 永不过期） |
| `last_used_at` | `TIMESTAMPTZ` | 可空 | 最后使用时间 |
| `created_at` | `TIMESTAMPTZ` | DEFAULT `now()` | 创建时间 |
| `revoked_at` | `TIMESTAMPTZ` | 可空 | 吊销时间 |

**索引**：
- `idx_api_tokens_user` ON (`user_id`)
- `idx_api_tokens_hash` ON (`token_hash`)

---

## 6. local_project_bindings

**用途**：本地项目绑定 — 本地项目 ID 与服务器项目 ID 的映射关系。

| 列名 | 类型 | 约束 | 描述 |
|------|------|------|------|
| `id` | `UUID` | **PK**, DEFAULT `gen_random_uuid()` | 主键 |
| `user_id` | `UUID` | **FK** → `users(id)` ON DELETE CASCADE, NOT NULL | 关联用户 |
| `local_project_id` | `VARCHAR(255)` | NOT NULL | 本地项目唯一标识 |
| `local_project_path` | `TEXT` | 可空 | 本地项目路径 |
| `server_project_id` | `UUID` | 可空，**FK** → `projects(id)` ON DELETE SET NULL | 服务器项目 ID |
| `sync_status` | `VARCHAR(50)` | DEFAULT `pending` | 同步状态：pending / syncing / synced / conflict |
| `last_synced_at` | `TIMESTAMPTZ` | 可空 | 最后同步时间 |
| `conflict_info` | `JSONB` | DEFAULT `{}` | 冲突信息 |
| `created_at` | `TIMESTAMPTZ` | DEFAULT `now()` | 创建时间 |
| `updated_at` | `TIMESTAMPTZ` | DEFAULT `now()` | 更新时间 |

**唯一约束**：`uq_local_binding` UNIQUE (`user_id`, `local_project_id`)

**索引**：`idx_local_bindings_server` ON (`server_project_id`)

---

> **最后更新**: 2026-07-28
