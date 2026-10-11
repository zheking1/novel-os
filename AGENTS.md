# Novel OS Project - Agent Instructions

## Mandatory: Read Docs Before Starting

**At the start of EVERY session, read the project documentation before making any changes:**

1. Read `novel-os-web/docs/development-guide.md` — Architecture, deployment, page patterns
2. Read `novel-os-web/docs/api-conventions.md` — MCP tool naming, API patterns, server architecture
3. Read `novel-os-web/docs/troubleshooting.md` — Known issues and fixes

These files contain project-specific rules that MUST be followed. Do not guess conventions — check the docs first.

## Session Rules (Mandatory)

1. **Confirm before execution** — Before making ANY code changes, wait for the user to explicitly say "开始" or "执行" or equivalent confirmation. Do not start editing files until confirmed.
2. **Design docs first** — Any non-trivial feature (est. >30 min work) requires writing design/requirements/development documents in the `docs/` directory BEFORE writing any code. Present the documents to the user for review and wait for confirmation.

## Key Rules (Summary)

### API Calls
- **ALL feature API calls use `ApiClient.callTool('tool.name', args)`** — there are NO REST endpoints like `/api/users`, `/api/backups`, etc.
- `ApiClient.request()` signature is `request(method, endpoint, data, options)` — NOT `request(endpoint, options)`
- `ApiClient.baseUrl` is `/api`, so endpoints must NOT include `/api` prefix

### MCP Tools
- Tool names use **dots** not underscores: `user.create` not `user_create`
- MCP source files live on NAS host at `/opt/novel-os/novel-os-mcp/src/` — do NOT edit inside containers
- After editing MCP files, rebuild: `docker build --no-cache -t novel-os-mcp:latest`
- `@validate_call` decorator does NOT exist — do not use it
- Delete tools MUST return dict, not bool: `return {"ok": deleted, "key": key}`
- Always add `ON DELETE CASCADE` or `ON DELETE SET NULL` to FK constraints on `users` table
- **Key tools return `workflow_guide`** — AI tools read this to know what to call next. Never remove or break this field.

### Frontend
- All page `init()` methods must return `true` to prevent placeholder fallback
- `ModalDialog.show()` does NOT return a boolean — use `onConfirm` callback pattern, call `ModalDialog.close()` inside callback
- Use business keys (e.g., `template_key`) not UUIDs for API calls

### Deployment
- Upload files to NAS source directory FIRST, then rebuild container
- Use `docker compose` (v2 syntax), not `docker-compose`
- JS changes require web container rebuild; MCP changes require MCP container rebuild
- Container restart loses non-persistent files

### Deployment
- Upload files to NAS source directory FIRST, then rebuild container
- Use `docker compose` (v2 syntax), not `docker-compose`
- JS changes require web container rebuild; MCP changes require MCP container rebuild
- Container restart loses non-persistent files

### Database
- User: `novel_os`, Password: `${POSTGRES_PASSWORD}`, DB: `novel_os`
- Run SQL via file upload (PowerShell quoting breaks inline SQL):
  ```bash
  echo "SQL;" > query.sql
  pscp -pw "${NAS_SSH_PASSWORD}" query.sql root@${NAS_HOST}:/tmp/query.sql
  plink -batch -pw "${NAS_SSH_PASSWORD}" root@${NAS_HOST} docker exec -i novel-postgres psql -U novel_os -d novel_os -f /tmp/query.sql
  ```

## Deployment Commands

### Deploy JS Changes
```bash
pscp -pw "${NAS_SSH_PASSWORD}" <file> root@${NAS_HOST}:/opt/novel-os/novel-os-web/<path>
plink -batch -pw "${NAS_SSH_PASSWORD}" root@${NAS_HOST} "cd /opt/novel-os && docker compose -f docker-compose.yml -f docker-compose.app.example.yml up -d --build novel-os-web"
```

### Deploy MCP Changes
```bash
pscp -pw "${NAS_SSH_PASSWORD}" <file> root@${NAS_HOST}:/opt/novel-os/novel-os-mcp/src/novel_os_mcp/<path>
plink -batch -pw "${NAS_SSH_PASSWORD}" root@${NAS_HOST} "cd /opt/novel-os && docker build --no-cache -t novel-os-mcp:latest -f novel-os-mcp/Dockerfile novel-os-mcp/ && docker compose -f docker-compose.yml -f docker-compose.app.example.yml up -d novel-os-mcp"
```

## Available MCP Tools

### User Management
- `user.create(username, display_name?, email?, remark?, status?, password?)`
- `user.list(status?, limit?)`
- 注：`user.update` 尚未实现，当前仅有 create / list / delete
- `user.delete(username)`

### Auth
- `auth.whoami()`, `auth.login(username, password)`, `auth.change_password(username, old_password, new_password)`

### Knowledge Base
- `kb.entity.create/search/update/get`, `kb.pk.upsert/list/get/delete`
- `kb.uk.search/create/update/delete`, `kb.world.get/update/list`
- `kb.category.list/tree/create/update/delete`
- `kb.auto.search/create_job/store/search_and_store` — 联网搜索知识并存入 UK
- `kb.genre.list/get/keywords/preheat` — 题材知识策略
- `kb.gap.create/list/resolve/detect` — 知识缺口管理
- `kb.pack.create/get/update/categories/custom.*` — 项目知识包

### Entity (Story Runtime)
- `state.entity.upsert(workspace, project, entity_type, name, summary?, description?, profile?, aliases?, tags?, importance?, lifecycle_status?, first_seen_chapter_no?, last_seen_chapter_no?)` — 创建/更新故事实体（角色/location/faction等），**character/faction 请用此工具而非 kb.pk.upsert**
- `state.entity.list(workspace, project, entity_type?, lifecycle_status?, query?, tags?)` — 列出实体
- `state.entity.get(workspace, project, entity_id? | entity_type+name)` — 获取单个实体详情
- `state.snapshot.upsert/list` — 实体状态快照管理
- `state.relationship.upsert/list` — 实体关系管理

### Settings
- `setting.category.list/get/upsert/delete`, `setting.item.list/upsert/delete`
- `setting.genre.list/resolve/delete`

### Prompt Templates
- `prompt.template.list/get/upsert/delete/render`

### Model Profiles
- `model.profile.list/upsert`

### System
- `system.health`, `cache.health/get_stats/warm/invalidate`
- `backup.create/list`, `restore.list`

### Graph
- `graph.get_data/get_subgraph/get_timeline`

### Skills
- `skill.list/get/create/update/delete`, `skill.step.list/add/update/delete`

### Plot (Story Planning)
- `plot.upsert_foreshadowing(workspace, project, key, title, layer?, importance?, status?, must_payoff?, payoff_deadline_chapter?, payoff_deadline_volume?, overdue_policy?)` — 创建/更新伏笔（推荐）
- `plot.list_foreshadowing` / `foreshadowing.payoff` / `foreshadowing.link` / `foreshadowing.check_overdue` — 伏笔管理
- `plot.thread.upsert/list/advance/check_stalled/delete` — 情节线管理
- `plot.create_chapter_plan/list_chapter_plans` — 章节大纲
- `volume.upsert/get/list` — 卷管理
- ~~`expectation.*`~~ **已废弃**，请使用 `plot.upsert_foreshadowing` 代替

### Workspace/Project
- `workspace.list/create/add_member`, `project.list/create/add_member`

## Credentials

> **本仓库不含任何真实凭证。** 所有敏感值一律用 `${...}` 占位符表示，真实值保存在仓库之外。

- 部署变量见 [`deploy/nas/.env.example`](deploy/nas/.env.example)；复制为 `.env` 后填写（已被 `.gitignore` 忽略）
- 文档命令中的 `${NAS_HOST}` / `${NAS_SSH_PASSWORD}` 等，请在本地导出后使用：
  ```bash
  set -a; . ~/.novel-os.env; set +a
  ```
- 种子管理员初始口令为 `123456`，**首次登录后必须立即修改**
- 口令哈希格式：bcrypt（`$2b$...`），兼容旧版 pbkdf2_sha256
