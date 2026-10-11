# 菜单系统

> 文件: `novel-os-web/js/core/menu-manager.js` (580行)

## 三层结构

```
MenuManager
  +-- menuDefinition: { home, project, knowledge, system }
      每个 Section 包含多个 Group (二级)
      每个 Group 包含多个 Item (三级，对应一个页面路由)
```

## 状态管理

`window.MenuManager.state`:
- `currentPage` — 当前激活的页面 ID
- `expandedSections` — 展开的 Section ID 集合(默认: project, knowledge, system)
- `expandedGroups` — 展开的 Group ID 集合(默认: project-settings, knowledge-mgmt, sys-monitor)
- `favorites` — 收藏的页面 ID 集合

状态持久化到 `localStorage['novel-os-menu-state']`。

---

## 完整菜单树

### home (首页) — order: 0

| Group | Item | Page ID | Route |
|---|---|---|---|
| home | 首页 | `home` | `/home` |

### project (项目管理) — order: 1

| Group | Item | Page ID | Route | 需项目 |
|---|---|---|---|---|
| project-settings 设定管理 | Canon 列表 | `canon-list` | `/project/canon` | Yes |
| | 实体列表 | `entities-list` | `/project/entities` | Yes |
| | 规则列表 | `rules-list` | `/project/rules` | Yes |
| | 关系图谱 | `graph-view` | `/project/graph` | Yes |
| project-plot 剧情管理 | 卷管理 | `plot-volumes` | `/project/volumes` | Yes |
| | 情节线 | `plot-threads` | `/project/threads` | Yes |
| | 伏笔管理 | `foreshadowing-list` | `/project/foreshadowing` | Yes |
| | 章节大纲 | `chapter-plans` | `/project/chapter-plans` | Yes |
| project-generation 生成与审查 | 上下文预览 | `context-preview` | `/project/context` | Yes |
| | 审核任务 | `review-tasks` | `/project/review` | Yes |
| | 合规检查 | `compliance` | `/project/compliance` | Yes |
| | Pipeline | `pipeline` | `/project/pipeline` | Yes |
| | 章节列表 | `chapters` | `/project/chapters` | Yes |
| project-knowledge 项目知识 | 世界观规则 | `project-world-rules` | `/project/world-rules` | Yes |
| | 角色列表 | `project-characters` | `/project/characters` | Yes |
| | 势力列表 | `project-factions` | `/project/factions` | Yes |
| | 世界状态 | `project-world-state` | `/project/world-state` | Yes |
| project-local 本地项目 | 本地项目 | `local-projects` | `/project/local-projects` | Yes |
| project-analysis 分析 | 角色弧光 | `arc-characters` | `/project/arc` | Yes |
| | 节奏分析 | `pacing-analysis` | `/project/pacing` | Yes |
| | 弧光追踪 | `arc-tracking` | `/project/arc-tracking` | Yes |
| | 世界快照 | `world-snapshot` | `/project/world-snapshot` | Yes |

### knowledge (知识库) — order: 2

| Group | Item | Page ID | Route | 需Admin |
|---|---|---|---|---|
| knowledge-mgmt 知识管理 | 通用知识管理 | `uk-manage` | `/knowledge/uk-manage` | |
| | 题材策略 | `kb-genres` | `/knowledge/genres` | |
| | 全局规则 | `global-rules` | `/knowledge/global-rules` | Yes |
| | 知识关系 | `kb-relations` | `/knowledge/relations` | |
| | 知识初始化 | `kb-init` | `/knowledge/init` | |
| | 素材库 | `materials` | `/knowledge/materials` | |
| | 自动搜索 | `auto-search` | `/knowledge/auto-search` | |
| | 知识图谱 | `knowledge-graph` | `/knowledge/graph` | |
| | 知识统计 | `knowledge-stats` | `/knowledge/stats` | |
| | 风格配置 | `style-profiles` | `/knowledge/style-profiles` | |
| | 语气管理 | `tone-management` | `/knowledge/tone-management` | |
| | 风格分析 | `style-analysis` | `/knowledge/style-analysis` | |
| | 风格偏移 | `style-drift` | `/knowledge/style-drift` | |
| | 分类管理 | `category-manage` | `/knowledge/category` | |
| knowledge-review 知识审查 | 知识审核 | `knowledge-review` | `/knowledge/review` | |
| | 知识过期 | `knowledge-expiry` | `/knowledge/expiry` | |
| | 预期管理 | `expectations` | `/knowledge/expectations` | |
| knowledge-search 知识搜索 | 搜索 | `kb-search` | `/knowledge/search` | |
| knowledge-evolution 进化 | 讨论室 | `discussion-room` | `/knowledge/discussion` | |
| | 系统进化 | `system-evolution` | `/knowledge/evolution` | Yes |
| | 进化日志 | `evolution-logs` | `/knowledge/evolution-logs` | Yes |
| | 系统通知 | `system-notifications` | `/knowledge/notifications` | |

### system (系统管理) — order: 3

| Group | Item | Page ID | Route | 需Admin |
|---|---|---|---|---|
| sys-project-mgmt 项目管理 | 项目管理 | `project-manage` | `/projects` | |
| | 工作区管理 | `workspace-manage` | `/system/workspaces` | |
| | 成员管理 | `member-manage` | `/system/members` | |
| sys-model 模型配置 | 模型配置 | `model-profiles` | `/system/model-profiles` | |
| | 模型路由 | `model-routes` | `/system/model-routes` | |
| | 速率限制 | `model-rate-limits` | `/system/model-rate-limits` | |
| | 费用报告 | `model-cost` | `/system/cost` | |
| sys-template 模板管理 | 模板列表 | `template-list` | `/system/templates` | |
| | 市场浏览 | `market-browse` | `/system/market` | |
| sys-skill | Skill管理 | `skill-manage` | `/system/skills` | |
| sys-data 数据管理 | 同步状态 | `sync-status` | `/system/sync` | |
| | 同步冲突 | `sync-conflicts` | `/system/conflicts` | |
| | 审计日志 | `audit-logs` | `/system/audit` | |
| | 离线状态 | `offline-status` | `/system/offline` | |
| sys-monitor 系统监控 | 系统健康 | `sys-health` | `/system/health` | |
| | 缓存管理 | `sys-cache` | `/system/cache` | |
| | 备份管理 | `sys-backup` | `/system/backup` | |
| sys-system 系统信息 | 连接状态 | `system-connection` | `/system/connection` | |
| | API Key | `api-keys` | `/system/api-keys` | |
| | 审核委员会 | `review-council` | `/system/review-council` | |
| | 账户设置 | `system-account` | `/system/account` | |
| | 用户管理 | `system-users` | `/system/users` | Yes |
| | 调试面板 | `system-debug` | `/system/debug` | |

---

## requiresProject 行为

- Section 级别: `requiresProject = true` 且未选项目时整个 Section 隐藏
- Group 级别: `requiresProject !== false` 且未选项目时整个 Group 隐藏
- `knowledge` 和 `system` Section 设置了 `requiresProject: false`，始终可见

## requiresAdmin 行为

- 管理员: username 命中 `server.py` 中定义的管理员名单（默认 `admin`，可用环境变量覆盖）
- Item 的 `requiresAdmin: true` 时仅管理员可见

## 菜单渲染

```javascript
// index.html 中的 renderMenu()
MenuManager.getMenu({ project, t, isAdmin })
// 返回: [{ id, label, icon, order, isExpanded, groups: [...] }]
// 每个 group 含 items: [{ id, label, path, isActive, isFavorite }]
```

### 交互 API

```javascript
MenuManager.toggleSection('project')     // 折叠/展开
MenuManager.toggleGroup('sys-model')     // 折叠/展开
MenuManager.setCurrentPage('template-list')  // 设置当前页(自动展开父级)
MenuManager.getPageInfo('template-list') // 获取页面所属 section/group
MenuManager.getBreadcrumbs('template-list', t) // 面包屑数组
MenuManager.toggleFavorite('template-list')   // 添加/移除收藏
```

## 全部 60+ 页面路由 → Page ID 映射

(详见各 Section 上方的表格)