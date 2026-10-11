# server.py 详细分析

> 文件: `novel-os-web/server.py` (736行)

## HTTP 服务器架构

- **类型**: `ThreadingHTTPServer` — 多线程 HTTP 服务器
- **监听地址**: `0.0.0.0:8790`（环境变量 `NOVEL_OS_WEB_HOST` / `NOVEL_OS_WEB_PORT`）
- **默认超时**: 30 秒
- **Server 版本头**: `NovelOSWeb/0.2`

## 完整路由表

### POST 路由

| 路径 | 处理函数 | 需要认证 | 说明 |
|---|---|---|---|
| `/api/setup` | `handle_setup()` | 否 | 首次初始化，创建管理员用户 |
| `/api/login` | `handle_login()` | 否 | 登录 → 签发 session cookie |
| `/api/logout` | 内联 | 否 | 清除 cookie（Max-Age=0） |
| `/api/account` | `handle_account()` | 是 | 修改密码 |
| `/api/tool` | `handle_tool()` | 是 | MCP 工具代理（核心 API） |
| `/api/captcha` | `handle_captcha()` | 否 | 生成数学验证码 |
| `/api/register` | `handle_register()` | 否 | 注册新用户（需验证码） |
| `/api/admin/setting` | `handle_admin_setting()` | 是(admin) | 管理系统设置键值 |

### GET 路由

| 路径 | 处理函数 | 说明 |
|---|---|---|
| `/api/me` | 内联 | 返回当前登录用户信息 + 认证状态 |
| `/api/admin/setting?key=` | `handle_admin_setting_get()` | 读取系统设置（仅 admin） |
| `/health` | 内联 | 健康检查，返回 `{status:"ok"}` |
| `/js/*`, `/css/*`, `/i18n/*`, `*.md` | `serve_static()` | 静态文件（应用缓存控制头: no-cache） |
| `/spa` | 内联 | 读取 `spa.html` |
| `/index-simple.html` | 内联 | 读取简化版 HTML |
| 所有其他 `GET` | 内联 | **SPA fallback** — 返回 `index.html` |

## 认证流程

### 登录流程 (`handle_login`)

1. 接收 `{username, password}`
2. 从 PostgreSQL `users` 表查询用户（`status='active'`）
3. 密码验证：支持两种格式
   - `pbkdf2_sha256$200000$salt$digest` — 旧版格式（纯 Python）
   - `$2b$...` — bcrypt 格式（需安装 `bcrypt` 库）
4. 自动创建缺失用户（兼容迁移）：如果用户不存在，用默认密码 `123456` 自动创建
5. **自动创建 MCP API Token**: 通过 `McpClient` 调用 `auth.create_api_token`
   - admin 用户（管理员名单内）获得 `["admin", "read", "write"]` 权限
   - 普通用户获得 `["read", "write"]` 权限
6. **自动创建个人工作区**: 调用 `workspace.create(slug=username)`
7. 签发 Session Cookie

### Session 管理

- **Cookie 名称**: `novel_os_web_session`
- **属性**: `Path=/; HttpOnly; SameSite=Lax; Max-Age=604800`（7 天）
- **签名算法**: HMAC-SHA256
- **载荷格式**: `base64url({"username":"...","exp":1234567890}).hexdigest`
- **密钥存储**: `/app/data/session.secret`（32 字节随机数，自动生成）
- **过期验证**: 解析后比对 `exp` 与当前时间戳

### 注册流程 (`handle_register`)

1. 检查 `auth.allow_registration` 系统设置是否为 `"true"`
2. 验证数学题验证码（`captcha_id` + `captcha_answer`）
3. 验证码 5 分钟过期
4. 检查用户名是否已存在
5. 在 `users` 表创建用户（状态 `active`）

## MCP 代理机制

### `McpClient` 类 (第155-241行)

```
McpClient(url, token)
  ├── initialize()     → JSON-RPC initialize 握手
  ├── call_tool()      → JSON-RPC tools/call
  ├── post()           → HTTP POST + session 管理
  └── 自动维护 mcp-session-id 头
```

- **JSON-RPC 2.0** 协议到 `http://novel-os-mcp:8787/mcp`
- Token 通过 `apiKey` 头传递
- 自动处理 `mcp-session-id` 头（跨请求保持）
- 响应解析：支持标准 JSON 和 SSE 格式（`data:` 行）
- 工具返回的 `content` 数组自动 `json.loads` 解析

### `/api/tool` 代理流程

1. 验证 session（读取 cookie）
2. 获取用户个人 MCP token（从 `system_settings` 表）
3. 创建临时 `McpClient` 实例，携带用户 token
4. 调用工具并返回结果

## 用户 Token 管理

### 存储位置

| 操作 | 方法 |
|---|---|
| 读取 token | `get_user_mcp_token(username)` → 查 `system_settings` 表 `mcp_token:xx` 键 |
| 写入 token | `set_user_mcp_token(username, token)` → 写入 `system_settings` 表 |
| 自动创建 | 登录时无 token 则调用 `auth.create_api_token` |

### Token 生命周期

- 登录时自动检查 → 无则创建 → 存入 `system_settings` 表
- 每个用户有独立的 MCP token（不是共享的）
- admin 用户（命中管理员名单）token 含 admin scope

## 数据库操作

### 连接信息

```python
DB_HOST = "postgres"  # Docker 服务名
DB_DB   = "novel_os"
DB_USER = "novel_os"
```

### 使用模式

```python
conn = get_db_connection()    # psycopg2.connect(...)
cur = conn.cursor()            # 或 RealDictCursor
cur.execute(sql, params)
conn.commit()
conn.close()
```

### 涉及的表

- `users` — 用户认证信息（username, display_name, password_hash, status, email, created_at）
- `system_settings` — 键值存储（key, value, description, updated_at），存放 token 和配置

## 静态文件服务

- 路径安全：`resolve()` 后检查是否在 web 根目录内
- MIME 类型：`.js` → `application/javascript`, `.css` → `text/css`, `.md` → `text/markdown`
- 缓存控制：全部 `Cache-Control: no-cache, no-store, must-revalidate`
- 支持查询字符串（自动去除 `?v=42` 等）

## 系统设置管理 (`/api/admin/setting`)

- 仅 admin 可读写（管理员名单内）
- GET: 通过 `?key=xxx` 查询参数读取
- POST: 通过 JSON body `{key, value}` 写入（`ON CONFLICT ... DO UPDATE`）
- 当前已知键：`mcp_token:xxx`（用户 token）、`auth.allow_registration`（注册开关）

## 首次初始化 (`/api/setup`)

1. 检查 `check_users_exist()` — 如果已有用户，拒绝
2. 接收 `{username, password, token}`
3. 创建用户（`create_user_in_db`）
4. 保存 MCP token
5. 调用 `send_login` 签发 session → 直接登录