# Novel OS Web Client - Development Guide

## Architecture Overview

```
novel-os-web/
├── index.html              # Main entry, SPA routing, login, workspace/project persistence
├── server.py               # Web server with auth proxy
├── js/
│   ├── core/               # Core modules
│   │   ├── api-client.js   # Unified API client (callTool wrapper)
│   │   ├── app-core.js     # App utilities (AppState, auth check)
│   │   ├── menu-manager.js # 3-level menu structure
│   │   ├── router.js       # Hash-based SPA router
│   │   └── i18n.js         # Internationalization
│   ├── components/         # Reusable components
│   │   ├── data-table.js   # Generic data table
│   │   └── modal-dialog.js # Modal dialog (confirm, alert)
│   └── pages/              # Page components (one per menu item)
│       ├── template-list-page.js  # Standardized CRUD template
│       └── ...
├── i18n/
│   ├── zh.json             # Chinese translations
│   └── en.json             # English translations
└── docs/                   # This documentation
```

## Deployment Workflow

### NAS Server
- **Host**: ${NAS_HOST}
- **SSH**: `plink -batch -pw "${NAS_SSH_PASSWORD}" root@${NAS_HOST}`
- **Upload**: `pscp -pw "${NAS_SSH_PASSWORD}" <file> root@${NAS_HOST}:<remote_path>`

### Deploy Steps

1. **Upload changed files** to NAS source directory:
   ```bash
   pscp -pw "${NAS_SSH_PASSWORD}" js/pages/my-page.js root@${NAS_HOST}:/opt/novel-os/novel-os-web/js/pages/my-page.js
   ```

2. **Rebuild container** (only the affected service):
   ```bash
   plink -batch -pw "${NAS_SSH_PASSWORD}" root@${NAS_HOST} "cd /opt/novel-os && docker compose -f docker-compose.yml -f docker-compose.app.example.yml up -d --build novel-os-web"
   ```

3. **For MCP tool changes**, rebuild MCP container:
   ```bash
   plink -batch -pw "${NAS_SSH_PASSWORD}" root@${NAS_HOST} "cd /opt/novel-os && docker compose -f docker-compose.yml -f docker-compose.app.example.yml up -d --build novel-os-mcp"
   ```

### Important Notes
- **Container restart loses non-persistent files**: Always upload to the source directory first, then rebuild
- **Use `docker compose`** not `docker-compose` (v2 syntax)
- **MCP tools are registered at startup**: Changes to tool definitions require MCP container rebuild

## Page Component Pattern

### Standardized CRUD Template (`template-list-page.js`)

Every CRUD page follows this pattern:

```javascript
(function() {
  'use strict';

  // Page config at top level
  const PAGE_CONFIG = {
    pageId: 'my-page',
    pageName: 'My Page',
    apiNamespace: 'myApi',           // Maps to ApiClient.myApi
    requiredProject: false,           // true = needs project selected
    emptyIcon: '📋',
    emptyText: 'No items',
    emptyHint: 'Click button to create',
    columns: [...],                   // Table columns
    filters: [...],                   // Filter dropdowns
    formFields: [...]                 // Create/edit form fields
  };

  const PAGE_ID = PAGE_CONFIG.pageId;

  window.MyPage = {
    currentData: [],
    currentFilters: {},

    init() {
      this.render();
      this.loadData();
      return true;  // CRITICAL: must return true to prevent placeholder fallback
    },

    render() { /* ... */ },
    async loadData() { /* ... */ },
    renderList() { /* ... */ },
    handleSearch: debounce(function(value) { /* ... */ }, 300),
    handleFilter(key, value) { /* ... */ },
    showCreateModal() { /* ... */ },
    hideModal() { /* ... */ },
    async handleEdit(id) { /* ... */ },
    async handleSave(e) { /* ... */ },
    async handleDelete(id, name) { /* ... */ },
    renderBadge(item) { /* ... */ }
  };

  function debounce(fn, delay) { /* ... */ }
})();
```

### Critical: `init()` Must Return `true`

All page `init()` methods must return `true`. The routing pattern uses:
```javascript
window.XxxPage?.init() || showPlaceholder()
```
If `init()` returns `undefined` (default), the `||` operator triggers the placeholder fallback.

### API Response Format Handling

`loadData()` should handle multiple response formats:
```javascript
const result = await window.ApiClient[PAGE_CONFIG.apiNamespace].list(workspace, this.currentFilters);
if (Array.isArray(result)) {
  this.currentData = result;
} else if (result?.templates) {
  this.currentData = result.templates;
} else if (result?.items) {
  this.currentData = result.items;
} else if (result?.data) {
  this.currentData = result.data;
} else {
  this.currentData = [];
}
```

## API Client Conventions

### Tool Naming
- MCP tools use **dots** not underscores: `prompt.template.upsert` (not `prompt_template_upsert`)
- API client methods use **camelCase**: `promptTemplate.create()`

### Project Parameter
Most tools require `workspace` and `project`. The `api-client.js` auto-injects project:
```javascript
promptTemplate: {
  async list(workspace, filters = {}, options = {}) {
    const project = window.AppState?.currentProject;
    return ApiClient.callTool('prompt.template.list', { workspace, project, ...filters }, options);
  }
}
```

### Delete Tool Pattern
Delete tools must return a dict, not a bool (FastMCP constraint):
```python
# WRONG - returns bool, causes "structured_content must be a dict or None" error
return await service.delete(project_id, key)

# CORRECT - wraps in dict
deleted = await service.delete(project_id, key)
return {"ok": deleted, "key": key}
```

## Menu Structure

### 3-Level Menu: Section > Group > Item
- **Section**: Top-level (Project, Knowledge, System)
- **Group**: Collapsible, can require project selection
- **Item**: Navigable page

### `requiresProject` Flag
- Groups with `requiresProject: true` are hidden when no project is selected
- All System and Knowledge groups have `requiresProject: false`
- Project section groups require a project

## State Management

### `AppState` (global)
```javascript
window.AppState = {
  initialized: false,
  currentLang: 'zh',
  currentWorkspace: null,
  currentProject: null,
  username: null
};
```

### Persistence
- Workspace and project selections are saved to `localStorage`
- Keys: `novel-workspace`, `novel-project`
- On page load, selections are restored from localStorage

## Login Flow

1. On load, SPA calls `/api/me` to check auth status
2. If unauthenticated, shows login screen
3. After login, hides login screen, renders menu and content
4. Auth state is server-side (session-based)

## Adding a New Page

1. Create `js/pages/my-page.js` following the CRUD template
2. Add route in `index.html`:
   ```javascript
   case 'my-page':
     window.MyPage?.init() || showPlaceholder();
     break;
   ```
3. Add script tag in `index.html`:
   ```html
   <script src="js/pages/my-page.js"></script>
   ```
4. Add menu item in `js/core/menu-manager.js`
5. Add translation keys in `i18n/zh.json` and `i18n/en.json`

## Commit Convention

Each feature should be committed separately:
```
feat(component): description

Examples:
feat(template-page): restore delete button, add prompt.template.delete MCP tool
fix(modal): center modal dialogs correctly
feat(api-client): add promptTemplate.delete method
```
