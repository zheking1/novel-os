# Novel OS Web Client — 完整需求与技术规格文档

> 版本：v3.0 | 日期：2026-07-04 | 基于 129 个有效函数 + 全量文档分析

---

# 第一部分：系统概述

## 1.1 项目定位

Novel OS Web Client 是一个**AI 辅助小说创作管理平台**的 Web 前端。它提供可视化界面来管理小说的世界观、角色、规则、知识库、类型配置等创作要素。

## 1.2 架构关系

```
┌──────────────┐    HTTP/JSON    ┌──────────────┐    MCP协议    ┌──────────────┐
│  Web Client  │ ──────────────▶ │  server.py   │ ────────────▶ │  MCP Server  │
│  (index.html +│                │  (Python反向  │               │  (novel-os-  │
│   js/ modules)│ ◀────────────── │   代理)      │ ◀──────────── │   mcp)       │
└──────────────┘                └──────┬───────┘               └──────┬───────┘
                                       │                              │
                                       │ SQL                          │ SQL
                                       ▼                              ▼
                               ┌──────────────┐              ┌──────────────┐
                               │  PostgreSQL  │              │  PostgreSQL  │
                               │  + pgvector  │              │              │
                               └──────────────┘              └──────────────┘
```

- **Web Client** → 调用 `server.py` 的 `/api/tool` 接口
- **server.py** → 反向代理到 MCP Server
- **MCP Server** → 操作 PostgreSQL 数据库
- 所有业务数据在 PostgreSQL 中，Web Client 不直接访问数据库

## 1.3 部署信息

| 项目 | 值 |
|------|-----|
| NAS IP | ${NAS_HOST} |
| Web 端口 | 8790 |
| MCP 端口 | 8787 |
| 部署目录 | /opt/novel-os |
| 容器名 | novel-os-web, novel-os-mcp |
| 数据库 | PostgreSQL 16 + pgvector (novel_os) |

---

# 第二部分：Web 客户端功能需求

## 2.1 认证系统

### 2.1.1 登录/注册

- **登录页面**：用户名 + 密码登录，Session Cookie 保持 7 天
- **初始设置**：首次访问可创建管理员账号 + MCP Token
- **Token 管理**：用户可配置自己的 MCP Token

### 2.1.2 工作区 / 项目选择

- 登录后自动加载用户所属的工作区列表
- 选择工作区后自动加载该工作区下的项目列表
- 工作区切换联动项目列表更新

## 2.2 菜单结构

### 2.2.1 当前菜单树（v3.0 版本）

```
Project（项目内容）
├── Canon Docs（世界设定文档）
├── Entities（角色/势力实体）
├── Template（模板管理）
│
Knowledge（知识管理） [v3.0 新增]
├── 小说类型管理     [新增]
├── 分类管理         [新增]
├── 类型与分类绑定   [新增]
├── 知识包           [从 Local Project 移来]
├── UK知识管理
├── 自动搜索
├── 知识统计
├── 知识维护
└── 知识审核
│
System（系统管理）
├── Model Profiles
├── Model Cost
├── API Tokens
├── Backup
├── Skills
├── System Health
└── Prompt Templates

已删除：
- Project Knowledge 子菜单组 (World Rules/Characters/Factions) — 与 Settings 重复
- Local Project 整个菜单组 — MCP 不需要本地文件绑定
```

## 2.3 页面功能详解

### 2.3.1 Canon Docs（世界设定文档）

**功能**：管理小说世界观设定文档，支持版本历史和恢复

**MCP 工具**：
- `canon.doc.list` — 列表查询（按 doc_type 过滤）
- `canon.doc.get` — 获取单个文档
- `canon.doc.upsert` — 创建/更新
- `canon.doc.history` — 版本历史
- `canon.doc.restore` — 恢复到指定版本
- `canon.doc.archive` — 归档

**数据库表**：`canon_documents`, `canon_document_versions`

**关键函数**：`loadCanonDoc()`, `renderCanonList()`

### 2.3.2 Entities（实体管理）

**功能**：管理故事实体（角色 character、势力 faction、地点 location 等），支持快照和关系

**MCP 工具**：
- `state.entity.list` — 列表（按 entity_type 过滤）
- `state.entity.get` — 获取单个
- `state.entity.upsert` — 创建/更新
- `state.snapshot.list` — 实体快照列表
- `state.snapshot.upsert` — 创建快照
- `state.relationship.list` — 关系列表
- `state.relationship.upsert` — 创建关系

**数据库表**：`state_entities`, `state_snapshots`, `state_relationships`

**关键函数**：`loadEntityDetails()`, `renderEntityList()`, `loadState()`, `saveState()`

### 2.3.3 知识管理

#### UK 知识管理

**功能**：通用知识库（Universal Knowledge），树形分类管理

**MCP 工具**：
- `kb.category.list` / `tree` — 分类树
- `kb.category.create` / `update` / `delete`
- `kb.uk.search` — 搜索知识
- `kb.uk.create` / `update` / `delete`
- `kb.uk.stats` — 统计

**数据库表**：`ref_categories`, `universal_knowledge`

**关键函数**：`initUkManage()`, `loadUkStats()`, `loadUkTree()`, `loadUkItems()`, `renderUkTree()`

#### 知识库维护（Knowledge Items）

**功能**：创作知识条目的 CRUD，含审核流程

**MCP 工具**：
- `knowledge.category.list` / `item.list` / `item.get`
- `knowledge.item.upsert` / `delete`
- `knowledge.review.list` / `approve` / `reject` / `stats`
- `knowledge.user.list` / `upsert` / `submit_review`

**数据库表**：`knowledge_items`, `knowledge_categories`, `knowledge_review`

**关键函数**：`loadKnowledgeMaintain()`, `renderCategoryTree()`, `loadKnowledgeItems()`, `renderKnowledgeItemList()`

#### 自动搜索

**功能**：创建知识自动搜索任务，填充知识库

**MCP 工具**：`kb.auto.search`, `kb.auto.store`

**关键函数**：`init_auto_search()`

### 2.3.4 系统管理

#### Model Profiles

**功能**：管理 LLM 模型配置（provider, model, cost, rate limits）

**MCP 工具**：
- `model.profile.list` / `upsert` / `route`
- `model.route.rule.list` / `upsert`

**关键函数**：`init_model_profiles_fn()`, `renderModelProfiles()`

#### Skills

**功能**：管理创作技能（提示词模板）及其步骤

**MCP 工具**：
- `skill.list` / `get` / `create` / `update` / `delete`
- `skill.step.list` / `add` / `update` / `delete`
- `skill.match` — 按意图匹配技能

**关键函数**：`init_skill_manage_fn()`, `loadSkillList()`, `saveSkill()`

#### API Tokens

**功能**：管理用户的 API 令牌

**MCP 工具**：`auth.list_api_tokens`, `auth.create_api_token`, `auth.revoke_api_token`

**关键函数**：`loadApiTokens()`

#### Backup

**功能**：备份管理（创建备份、查看列表、备份计划）

**MCP 工具**：`backup.create`, `backup.list`, `backup.schedule.upsert`

**关键函数**：`loadBackupList()`, `saveBackupSchedule()`, `createBackup()`

### 2.3.5 新增功能（v3.0）

#### 小说类型管理

**功能**：管理小说类型（genre），支持增删改查

**MCP 工具**：`setting.genre.list`, `setting.genre.upsert`, `setting.genre.delete`

**数据库表**：`genre_canonical`

**实现文件**：`js/pages/genre.js`

#### 分类管理

**功能**：管理自定义分类，支持类型描述（说明存储什么数据）

**MCP 工具**：`setting.category.list`, `setting.category.upsert`, `setting.category.delete`

**数据库表**：`setting_categories`

**实现文件**：`js/pages/category.js`

#### 类型与分类绑定

**功能**：矩阵式勾选，定义每种小说类型需要哪些分类

**MCP 工具**：`genre.binding.matrix`, `genre.binding.bulk_upsert`

**数据库表**：`genre_category_bindings`

**实现文件**：`js/pages/binding.js`

---

# 第三部分：技术架构

## 3.1 文件结构

```
novel-os-web/
├── server.py                    # Python HTTP 服务器 + 反向代理
├── index.html                   # 主入口（HTML骨架 + 内联JS主逻辑）
├── Dockerfile                   # Docker 构建配置
├── js/
│   ├── app.js                   # 通用工具（api, showToast, setStatus, escapeHtml, $）
│   ├── auth.js                  # 认证 + 工作区/项目加载
│   └── pages/
│       ├── genre.js             # [新增] 小说类型管理
│       ├── category.js          # [新增] 分类管理
│       └── binding.js           # [新增] 类型-分类绑定
├── css/
│   └── style.css                # 样式表（从 HTML 提取）
├── docs/
│   └── functions-analysis.md    # 129 函数分析文档
└── index.html.backup_*          # 备份文件
```

## 3.2 后端 API 设计

### 3.2.1 server.py 路由

| 路径 | 方法 | 处理函数 | 说明 |
|------|------|----------|------|
| `/health` | GET | `do_GET` | 健康检查 |
| `/api/me` | GET | `do_GET` | 获取当前用户状态 |
| `/api/login` | POST | `handle_login` | 登录 |
| `/api/logout` | POST | `do_POST` | 登出 |
| `/api/setup` | POST | `handle_setup` | 初始设置 |
| `/api/account` | POST | `handle_account` | 账号管理（改密码、MCP配置） |
| `/api/tool` | POST | `handle_tool` | **核心**：调用 MCP 工具 |
| `/js/*`, `/css/*` | GET | `serve_static` | 静态文件 |
| 其他 | GET | `do_GET` | 返回 index.html |

### 3.2.2 /api/tool 请求格式

```json
{
  "tool": "workspace.list",
  "arguments": {
    "key": "value"
  },
  "mcp_url": "http://novel-os-mcp:8787/mcp"
}
```

### 3.2.3 /api/tool 响应格式

```json
{
  "ok": true,
  "result": { ... }
}
```

### 3.2.4 认证方式

- Session Cookie: `novel_os_web_session`
- MCP Tool Call: 使用 `Bearer <token>` 或 `ApiKey <key>`
- Service Token: 存储在 `NOVEL_OS_MCP_SERVICE_TOKEN` 环境变量

## 3.3 Dockerfile

```dockerfile
FROM python:3.12-slim
RUN apt-get update && apt-get install -y libpq-dev gcc && \
    pip install psycopg2-binary bcrypt && \
    apt-get remove -y gcc && apt-get autoremove -y && rm -rf /var/lib/apt/lists/*
COPY server.py index.html /app/
COPY js/ /app/js/
COPY css/ /app/css/
ENV NOVEL_OS_WEB_HOST=0.0.0.0
ENV NOVEL_OS_WEB_PORT=8790
ENV NOVEL_OS_WEB_ROOT=/app
EXPOSE 8790
CMD ["python", "server.py"]
```

## 3.4 构建与部署

```bash
# NAS 上执行
cd /opt/novel-os
docker compose -f docker-compose.yml -f docker-compose.app.example.yml up -d --build novel-os-web
```

---

# 第四部分：前端模块规范

## 4.1 全局 API 调用

### api()

```javascript
// 签名
async function api(path, body) 

// 用法
var result = await api('/api/tool', {
  tool: 'workspace.list',
  arguments: {}
});
// result = { ok: true, result: [...] } 
// 或 { error: 'message' }
```

**特性**：
- 自动处理 HTTP 错误（status 4xx/5xx）
- 自动显示网络错误 Toast
- 自动显示 API 错误 Toast
- 支持 GET（无 body）和 POST（有 body）

## 4.2 全局 UI 工具

| 函数 | 签名 | 用途 |
|------|------|------|
| `$()` | `(id) => document.getElementById(id)` | DOM 查询 |
| `escapeHtml()` | `(str) => escaped_string` | 安全转义 |
| `showToast()` | `(type, title, msg, duration)` | 提示消息 |
| `setStatus()` | `(text)` | 状态栏更新 |
| `t()` | `(key) => translated_string` | 国际化 |
| `closeModal()` | `()` | 关闭弹窗 |

## 4.3 页面模块开发规范

每个页面模块遵循标准模板：

```javascript
;(function(window) {
  'use strict';

  // ===== 私有状态 =====
  var localState = [];

  // ===== 页面加载函数 =====
  window.loadPageName = async function() {
    setStatus('loading...');
    var result = await api('/api/tool', {
      tool: 'mcp.tool.name',
      arguments: {}
    });
    if (result.ok) {
      localState = result.result || [];
      render();
      setStatus('');
    }
  };

  // ===== 渲染函数 =====
  function render() {
    var el = $('containerId');
    el.innerHTML = localState.map(function(item) {
      return '<div>' + escapeHtml(item.name) + '</div>';
    }).join('');
  }

  // ===== CRUD 函数 =====
  window.createItem = async function() { ... };
  window.updateItem = async function() { ... };
  window.deleteItem = async function() { ... };

})(window);
```

### 规范要求

1. **IIFE 包裹**：防止全局污染
2. **window 挂载**：需要从 HTML onclick 调用的函数挂到 window
3. **异步加载**：使用 async/await
4. **错误处理**：所有 API 调用包裹 try/catch
5. **状态管理**：本地变量存储列表数据
6. **escapeHtml**：所有用户数据渲染前必须转义
7. **独立可测**：每个模块不依赖其他模块（只依赖 app.js 的工具函数）

## 4.4 全局路由

### goToPage()

```javascript
function goToPage(pageName) {
  currentPage = pageName;
  document.querySelectorAll('.page').forEach(p => p.classList.add('hidden'));
  var target = document.getElementById('page-' + pageName);
  if (target) target.classList.remove('hidden');
}
```

**页面 ID 命名规范**：`id="page-{pagename}" class="page hidden"`

**菜单点击**：使用 `data-page` 属性 + `setupMenuGroups()` 事件委托

---

# 第五部分：CSS 规范

## 5.1 CSS 类名体系

| 类名 | 用途 |
|------|------|
| `.page` | 页面容器 |
| `.page.hidden` | 隐藏页面 |
| `.page-header` | 页面标题区 |
| `.list-container` | 列表容器 |
| `.list-item` | 列表项 |
| `.list-item-header` | 列表项标题 |
| `.list-item-meta` | 列表项元数据 |
| `.badge` | 标签 |
| `.badge-success` | 成功标签 |
| `.btn` | 按钮 |
| `.btn-sm` | 小按钮 |
| `.btn-danger` | 危险操作按钮 |
| `.form-group` | 表单组 |
| `.form-input` | 表单输入 |
| `.modal-content` | 弹窗内容 |
| `.modal-actions` | 弹窗操作区 |
| `.toast` | 提示消息 |
| `.empty-state` | 空数据状态 |
| `.data-table` | 数据表格 |
| `.menu-section` | 菜单分区 |
| `.menu-title` | 菜单标题 |
| `.menu-item` / `.submenu-item` | 菜单项 |
| `.workspace-selector` / `.project-selector` | 选择器 |

## 5.2 颜色变量

```css
--accent       /* 主色调 */
--muted        /* 灰色文字 */
--danger       /* 红色/危险 */
--success      /* 绿色/成功 */
--warning      /* 黄色/警告 */
--bg           /* 背景色 */
```

---

# 第六部分：MCP 工具索引

## 6.1 工具完整列表

### 认证与工作区
| 工具名 | 说明 |
|--------|------|
| `workspace.list` | 列出工作空间 |
| `workspace.create` | 创建工作空间 |
| `workspace.add_member` | 添加成员 |
| `auth.whoami` | 当前用户身份 |
| `auth.list_api_tokens` | API令牌列表 |
| `auth.create_api_token` | 创建API令牌 |
| `auth.revoke_api_token` | 吊销API令牌 |
| `project.list` | 列出项目 |
| `project.create` | 创建项目 |
| `project.list_members` | 项目成员 |

### 设定管理
| 工具名 | 说明 |
|--------|------|
| `canon.doc.list` | 列出设定文档 |
| `canon.doc.get` | 获取设定文档 |
| `canon.doc.upsert` | 创建/更新设定 |
| `canon.doc.history` | 版本历史 |
| `canon.doc.restore` | 恢复版本 |
| `state.entity.list` | 列出实体 |
| `state.entity.upsert` | 创建/更新实体 |
| `state.snapshot.list` | 实体快照 |
| `state.snapshot.upsert` | 创建快照 |
| `state.relationship.list` | 关系列表 |
| `state.relationship.upsert` | 创建关系 |
| `rules.list` | 列出规则 |
| `rules.upsert` | 创建/更新规则 |
| `rules.list_effective` | 当前生效规则 |
| `rules.check_conflict` | 检查规则冲突 |

### 情节管理
| 工具名 | 说明 |
|--------|------|
| `plot.thread.upsert` | 创建/更新情节线 |
| `plot.thread.list` | 情节线列表 |
| `plot.thread.advance` | 推进情节线 |
| `plot.upsert_foreshadowing` | 伏笔管理 |
| `plot.list_foreshadowing` | 伏笔列表 |
| `volume.upsert` | 卷管理 |
| `volume.list` | 卷列表 |

### 知识库
| 工具名 | 说明 |
|--------|------|
| `kb.category.list` | 分类列表 |
| `kb.category.tree` | 分类树 |
| `kb.category.create/update/delete` | 分类 CRUD |
| `kb.uk.search` | 搜索UK知识 |
| `kb.uk.create/update/delete` | UK知识 CRUD |
| `kb.auto.search` | 自动搜索 |
| `kb.auto.store` | 存储搜索结果 |
| `kb.pack.get` | 获取知识包 |
| `kb.pack.create` | 创建知识包 |
| `kb.pack.update` | 更新知识包 |
| `kb.pack.custom.add/remove` | 自定义分类 |
| `knowledge.category.list` | 知识分类 |
| `knowledge.item.list/get` | 知识条目 |
| `knowledge.item.upsert/delete` | 条目 CRUD |
| `knowledge.review.*` | 审核管理 |

### 全局设定 [v3.0 新增]
| 工具名 | 说明 |
|--------|------|
| `setting.category.list` | 列出设定分类 |
| `setting.category.get` | 获取分类 |
| `setting.category.upsert` | 创建/更新分类 |
| `setting.category.delete` | 删除分类 |
| `setting.item.list/get` | 设定条目 |
| `setting.item.upsert/delete` | 条目 CRUD |
| `setting.search` | 全文搜索 |
| `setting.genre.list` | 小说类型列表 |
| `setting.genre.upsert` | 创建/更新类型 |
| `setting.genre.delete` | 删除类型 |
| `genre.binding.list` | 绑定列表 |
| `genre.binding.bulk_upsert` | 批量绑定 |
| `genre.binding.matrix` | 绑定矩阵 |

### 系统管理
| 工具名 | 说明 |
|--------|------|
| `model.profile.list/upsert` | 模型配置 |
| `model.route.rule.list/upsert` | 路由规则 |
| `model.route` | 模型路由 |
| `skill.list/get/create/update/delete` | 技能管理 |
| `skill.step.*` | 技能步骤 |
| `backup.create/list` | 备份管理 |
| `system.health` | 系统健康 |
| `prompt.template.*` | Prompt 模板 |
| `cache.get/stats/clear/warm` | 缓存管理 |

---

# 第七部分：数据库核心表

## 7.1 用户与权限

```sql
users(id, username, display_name, password_hash, status, role)
api_tokens(id, user_id, workspace_id, name, token_hash, scopes)
workspaces(id, slug, name, owner_user_id, settings)
workspace_members(workspace_id, user_id, role)
projects(id, workspace_id, slug, title, description, status, settings)
project_members(project_id, user_id, role)
```

## 7.2 设定与实体

```sql
canon_documents(id, project_id, doc_type, key, title, content, status, version)
canon_document_versions(id, document_id, version, content, change_reason)
state_entities(id, project_id, entity_type, name, profile, importance)
state_snapshots(id, entity_id, chapter_no, state, is_current)
state_relationships(id, source_entity_id, target_entity_id, relation_type)
```

## 7.3 知识库

```sql
ref_categories(id, slug, name, parent_id, is_system)
universal_knowledge(id, topic, content, category_id, era, genre_tags, source)
project_knowledge_pack(project_id, genre, active_categories, custom_categories)
knowledge_items(id, category_id, title, content, level, status)
knowledge_categories(id, slug, name, parent_id)
genre_canonical(canonical_genre, slug, name, description, aliases, typical_elements)
```

## 7.4 全局设定 [v3.0]

```sql
setting_categories(id, workspace_id, slug, name, description, type_description, icon, is_standard)
setting_items(id, category_id, workspace_id, item_code, data, tags, is_global)
genre_category_bindings(genre_slug, category_id, is_required, priority)
```

## 7.5 创作规则

```sql
rules(id, project_id, rule_key, rule_type, title, content, severity, status)
rule_proposals(id, project_id, proposal_type, title, content, status)
rule_versions(id, rule_id, version, content)
```

## 7.6 情节

```sql
plot_threads(id, project_id, key, title, thread_type, importance, status, current_chapter_no)
volumes(id, project_id, volume_no, title, outline, start_chapter_no, end_chapter_no, status)
foreshadowing(id, project_id, key, title, importance, status, payoff_deadline_chapter)
```

## 7.7 审查

```sql
review_council_configs(id, project_id, name, config, is_active)
review_jobs(id, project_id, chapter_id, status, config)
review_reports(id, review_job_id, model_id, score, findings, summary)
revision_tasks(id, project_id, chapter_id, title, severity, status)
```

---

# 第八部分：前端函数分类索引

## 8.1 核心工具函数（app.js）

| 函数 | 行数 | 用途 |
|------|------|------|
| `$` | 1 | `document.getElementById` 简写 |
| `escapeHtml` | 4 | HTML 实体转义 |
| `api` | 28 | 封装 fetch，自动错误处理和 Toast |
| `showToast` | 13 | Toast 消息弹窗 |
| `setStatus` | 4 | 状态栏消息更新 |
| `t` | 3 | i18n 翻译查找 |
| `applyLanguage` | 12 | 语言切换应用 |
| `parseJson` | 6 | 安全 JSON 解析 |
| `parseCsv` | 12 | CSV 文本解析 |
| `renderMarkdown` | 15 | 简易 Markdown 渲染 |
| `buildTree` | 15 | 扁平列表转树结构 |

## 8.2 认证（auth.js）

| 函数 | 用途 |
|------|------|
| `loadWorkspaces` | 加载工作区列表 + 填充选择器 |
| `loadProjects` | 加载项目列表 |
| `refreshAuth` | 检查认证状态 |
| `getActiveWorkspace` | 获取当前工作区 |
| `getActiveProjectArgs` | 获取项目参数 |
| `baseProjectArgs` | 基础项目参数（workspace, project） |
| `updateProjectDropdowns` | 更新所有项目下拉框 |

## 8.3 菜单路由

| 函数 | 用途 |
|------|------|
| `goToPage` | 页面导航（hidden class 切换） |
| `setupMenuGroups` | 菜单折叠组初始化 |
| `setupDropdown` | 下拉菜单行为 |
| `closeAllDropdowns` | 关闭所有打开的下拉 |
| `toggleSidebar` | 侧边栏折叠/展开 |
| `loadModule` | 动态加载模块页面 |

## 8.4 知识管理（48个函数 — 最大模块）

分为以下子域：
- UK 管理：`initUkManage`, `loadUkStats`, `loadUkTree`, `loadUkItems`, `renderUkTree`
- 知识维护：`loadKnowledgeMaintain`, `renderCategoryTree`, `loadKnowledgeItems`
- 知识列表：`loadKnowledgeList`, `renderKnowledgeList`, `renderKnowledgeListPagination`
- 知识编辑：`renderKnowledgeEditor`, `saveKnowledgeEditor`, `createNewKnowledgeItem`
- 审核：`loadReviewList`, `renderReviewList`, `approveReview`, `rejectReview`
- 缓存：`loadCacheStats`, `clearCache`, `warmCache`
- 知识包：`createKnowledgePack`, `saveKnowledgePack`, `toggleCategory`

## 8.5 系统管理（25个函数）

- 模型：`init_model_profiles_fn`, `renderModelProfiles`
- 成本：`init_model_cost_fn`
- 模板：`init_template_list_fn`, `loadMarketTemplates`, `renderTemplates`
- 技能：`init_skill_manage_fn`, `loadSkillList`, `saveSkill`, `openSkillEdit`
- 备份：`loadBackupList`, `saveBackupSchedule`, `createBackup`
- 令牌：`loadApiTokens`
- 健康：`loadSystemHealth`

---

# 第九部分：开发指南

## 9.1 添加新页面步骤

1. 创建 `js/pages/newpage.js`（按标准模板）
2. 在 `index.html` 的 `</body>` 前添加：
   ```html
   <div id="page-newpage" class="page hidden">...</div>
   <script src="js/pages/newpage.js"></script>
   ```
3. 在菜单中添加：
   ```html
   <div class="submenu-item" data-page="newpage">新页面</div>
   ```
4. 无需修改 `goToPage` — `data-page` 属性自动路由

## 9.2 编译部署流程

```bash
# 1. 本地修改 → 测试
# 2. 提交 Git
git add -A && git commit -m "描述" && git push origin main

# 3. NAS 部署
cd /opt/novel-os
docker compose -f docker-compose.yml -f docker-compose.app.example.yml up -d --build novel-os-web

# 4. 验证
curl http://${NAS_HOST}:8790/health
```

## 9.3 回滚

```bash
# Git 回滚
git log --oneline -5
git revert <commit_hash>

# Docker 回滚到上一个镜像
docker tag novel-os-web:latest novel-os-web:broken
docker tag novel-os-web:previous novel-os-web:latest
docker compose up -d novel-os-web
```

---

# 第十部分：已知限制与后续规划

## 10.1 当前限制

1. **index.html 内联 JS 庞大** — 仍有 443KB，包含 129 个函数在单文件 script 块中
2. **CSS inline 残留** — 部分样式仍在 HTML 的 style 属性中
3. **缺少状态管理** — 页面间状态通过全局变量共享
4. **无构建工具** — 纯手写 JS，无 lint/typecheck
5. **知识图谱扩展未完成** — 等级体系、物品、技能、地图等 UI 待开发

## 10.2 后续建议

| 任务 | 优先级 | 工作量 |
|------|--------|--------|
| 继续提取低风险工具函数到 app.js | P1 | 2h |
| 提取 Knowledge 模块到独立文件 | P1 | 4h |
| 提取 System 模块到独立文件 | P2 | 3h |
| 添加等级/物品/技能管理页面 | P2 | 1天 |
| 引入 ESLint/Prettier | P3 | 1h |
| 引入 JS 模块化 (ES modules) | P3 | 2天 |

---

*文档版本：v3.0*
*生成日期：2026-07-04*
*基于 145 函数分析 + 项目文档 + 实际代码*