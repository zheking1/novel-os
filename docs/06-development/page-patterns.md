# 页面开发模式

## 标准 CRUD 模板

```javascript
(function() {
  'use strict';

  const PAGE_CONFIG = {
    pageId: 'my-page',
    pageName: 'My Page',
    apiNamespace: 'myApi',
    requiredProject: false,
    emptyIcon: '📋',
    emptyText: 'No items',
    emptyHint: 'Click button to create',
    columns: [
      { key: 'name', label: 'Name' },
      { key: 'status', label: 'Status', type: 'badge' }
    ],
    filters: [
      { key: 'status', label: 'Status', options: [{value:'',label:'All'},{value:'active',label:'Active'}] }
    ],
    formFields: [
      { key: 'name', label: 'Name', type: 'text', required: true },
      { key: 'content', label: 'Content', type: 'textarea' }
    ]
  };

  const PAGE_ID = PAGE_CONFIG.pageId;

  window.PageName = {
    currentData: [],
    currentFilters: {},

    init() {
      this.render();
      this.loadData();
      return true;  // 必须返回 true
    },

    render() {
      const area = document.getElementById('content-area');
      if (!area) return;
      area.innerHTML = `...`;
    },

    async loadData() {
      const ws = window.AppState?.currentWorkspace;
      const result = await window.ApiClient[PAGE_CONFIG.apiNamespace].list(ws, this.currentFilters);
      // 处理多种响应格式
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
      this.renderList();
    },

    renderList() { /* 渲染表格 */ },
    showCreateModal() { /* 显示创建弹窗 */ },
    async handleSave(e) { /* 保存 */ },
    async handleDelete(id, name) { /* 删除 */ }
  };

  function debounce(fn, delay) {
    let timer;
    return function(...args) {
      clearTimeout(timer);
      timer = setTimeout(() => fn.apply(this, args), delay);
    };
  }
})();
```

## 关键模式

### init() 必须返回 true
```javascript
init() {
  this.render();
  this.loadData();
  return true;  // 不返回 true 会触发 showPlaceholder()
}
```

### ModalDialog 回调模式
```javascript
showCreateModal() {
  ModalDialog.show({
    title: 'Create',
    content: formHTML,
    onConfirm: async () => {
      await this.handleSave();
      ModalDialog.close();  // 回调内必须调用 close()
    }
  });
  // 不要依赖 show() 的返回值！
}
```

### 业务键而非 UUID
```javascript
// 错误 — 发送 UUID
onclick="handleDelete('${item.id}')"

// 正确 — 发送业务键
onclick="handleDelete('${item.template_key}')"
```

### 搜索防抖
```javascript
handleSearch: debounce(function(value) {
  this.currentFilters.search = value;
  this.loadData();
}, 300)
```

### 筛选处理
```javascript
handleFilter(key, value) {
  this.currentFilters[key] = value;
  this.loadData();
}
```

### 读取工作区/项目状态
```javascript
async loadData() {
  const workspace = window.AppState?.currentWorkspace;
  const project = window.AppState?.currentProject;
  if (!workspace) return;
  const result = await ApiClient.xxx.list(workspace, project, filters);
}
```

## 添加新页面步骤

1. 创建 `js/pages/my-page.js`（按 CRUD 模板）
2. 在 `index.html` 添加路由 case:
   ```javascript
   case 'my-page':
     window.MyPage?.init() || showPlaceholder();
     break;
   ```
3. 添加 `<script>` 标签 `<script src="js/pages/my-page.js"></script>`
4. 在 `menu-manager.js` 添加菜单项
5. 在 `i18n/zh.json` 和 `i18n/en.json` 添加翻译