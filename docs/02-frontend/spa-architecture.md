# SPA 架构

> 入口文件: `novel-os-web/index.html` (1045行)
> 纯 vanilla JS SPA，无框架依赖（Alpine.js 仅用于组件）

## 入口加载流程

```
DOMContentLoaded
  ├── waitForModules()          # 轮询等待所有模块就绪（最多 50 次 × 50ms）
  │   ├── window.i18n
  │   ├── window.AppCore
  │   ├── window.ApiClient
  │   ├── window.MenuManager
  │   └── window.NovelRouter
  ├── fetch('/api/me')          # 检查登录状态
  ├── me.authenticated?
  │   ├── Yes → showApp() → initApp()
  │   └── No  → showLogin()
  └── 监听事件: app:loading, popstate, menu:changed, i18n:changed
```

## Script 加载顺序

```
1. js/core/i18n.js          # 国际化引擎
2. js/core/app-core.js      # 应用核心（toast/loading 事件系统）
3. js/core/api-client.js    # API 客户端（MCP 代理 + 缓存）
4. js/core/menu-manager.js  # 三级菜单引擎
5. ~~js/core/router.js~~       # 已移除：routes 恒为空且无人注册，路由现由 index.html 的 navigateToPage switch 承担
6. js/utils/error-handler.js
7. js/utils/form-validator.js
8. js/components/data-table.js
9. js/components/modal-dialog.js
10. js/pages/*.js            # 所有业务页面（60+）
```

## 全局状态: `window.AppState`

```javascript
window.AppState = {
  initialized: false,                                  // 应用是否已完成初始化
  currentLang: null,                                   // 当前语言 'zh'/'en'
  currentWorkspace: null,                              // 当前工作区 slug
  currentProject: null,                                // 当前项目 slug
  currentProjectId: null,                              // 当前项目数据库 ID
  username: null,                                      // 登录用户名
  isAdmin: false,                                      // 是否管理员（命中 server.py 中的管理员名单）
  projectsList: []                                     // 当前工作区下的项目列表（用于 ID 查找）
}
```

**这是真正的全局状态**。Alpine.js 的 store 几乎没有被积极使用来做页面级状态管理。

## localStorage 持久化

| 键 | 值 | 说明 |
|---|---|---|
| `novel-workspace` | 工作区 slug | 登录和选择时写入，登出时清除 |
| `novel-project` | 项目 slug | 选择项目时写入，登出/切工作区时清除 |
| `novel-os-menu-state` | JSON `{expandedSections, expandedGroups, favorites}` | 菜单展开/折叠状态 |
| `novel-os-config` | JSON `{apiBaseUrl, defaultWorkspace, ...}` | AppCore 配置 |

## 路由系统

### Hash-based 导航

- 所有页面路由使用 URL hash：`#/project/entities`
- `navigateToPage(pageId)` — 巨型 `switch` 语句，60+ 分支
- `pathToPageId(path)` — 反向映射：遍历完整菜单树找匹配的 `item.path`
- `handleMenuClick(pageId, path)` — 点击菜单项时：
  1. `MenuManager.setCurrentPage(pageId)` — 设置当前页面，展开对应菜单
  2. `updateBreadcrumb()` — 更新面包屑
  3. `history.pushState(null, '', '#' + path)` — 更新 URL（不触发 hashchange）
  4. `navigateToPage(pageId)` — 执行路由

### 浏览器前进/后退

```javascript
window.addEventListener('popstate', () => {
  const hash = window.location.hash.slice(1);
  const pageId = pathToPageId(hash);
  if (pageId) {
    MenuManager.setCurrentPage(pageId);
    navigateToPage(pageId);
    updateBreadcrumb();
  }
});
```

## 工作区/项目选择

### 工作区选择器

- `<select id="workspace-select">` 在顶部栏
- 初始化: `updateWorkspaceSelector(workspaces)` 填充选项
- 恢复之前选择：从 `localStorage['novel-workspace']` 读取
- `handleWorkspaceChange(slug)`:
  1. 更新 `AppState.currentWorkspace`
  2. 清除 `AppState.currentProject` 和 `localStorage['novel-project']`
  3. 重新加载项目列表
  4. 存储 `AppState.projectsList`
  5. 调用 `renderMenu()` 更新菜单

### 项目选择器

- `<select id="project-select">` 在顶部栏
- `handleProjectChange(slug)`:
  1. 从 `AppState.projectsList` 查找项目 ID
  2. 写入 `localStorage['novel-project']`
  3. 调用 `renderMenu()` 更新菜单
  4. 如果当前有打开页面，重新加载该页面

## 加载/Toast 事件系统

### Loading 事件

```javascript
// 发送
window.AppCore.setLoading(true, '加载中...')
window.AppCore.setLoading(false)

// 监听 (index.html:992)
window.addEventListener('app:loading', (e) => {
  if (e.detail.loading) {
    document.getElementById('loading-mask').classList.remove('hidden');
  } else {
    document.getElementById('loading-mask').classList.add('hidden');
  }
});
```

### Toast 事件

```javascript
// 发送
window.AppCore.toast('success', '标题', '消息内容')

// 监听
window.addEventListener('app:toast', (e) => {
  // Toast 容器组件处理
});

// 快捷方式
window.showToast(type, title, message, duration)
```

## 菜单变更事件

```javascript
window.addEventListener('menu:changed', () => {
  renderMenu();  // 重新渲染侧边栏菜单
});
```

## 登录/登出流程

### 登录

1. `handleLogin(e)` → `POST /api/login`
2. 成功后设置 `AppState.username` 和 `AppState.isAdmin`
3. `showApp()` → `initApp()`

### 登出

1. `handleLogout()` → `confirm()` → `POST /api/logout`
2. 清除 `AppState.username`、`isAdmin`
3. 清除 `localStorage['novel-workspace']`、`['novel-project']`
4. `showLogin()` — 返回登录界面

### 语言切换

1. `toggleLanguage()` → `i18n.setLang()`
2. 更新 `AppState.currentLang`
3. 重新渲染菜单、面包屑、语言按钮

## 缓存系统

见 `CacheManager` (js/utils/cache-manager.js, 109行)：

- **TTL 分级**: workspace 5min, genre 10min, user 1min, project 1min, default 30s
- **请求去重**: 同一个 key 的并发请求共享同一个 promise
- **前缀失效**: `invalidatePrefix('prompt')` 清除所有 `prompt.*` 缓存
- **ApiClient 自动集成**: 只读操作（list/get/search/whoami/health/stats/tree）自动缓存，写操作（create/update/delete/upsert/record/fulfill）自动按前缀失效