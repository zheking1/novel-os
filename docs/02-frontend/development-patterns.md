# 页面开发规范

## 标准 CRUD 模板 (PAGE_CONFIG 模式)

### 基本结构

每个标准 CRUD 页面遵循统一模板 (参考 `template-list-page.js`):

```javascript
(function() {
  'use strict';

  const PAGE_CONFIG = {
    pageId: 'my-page',           // 页面唯一标识
    pageName: '页面名称',
    apiNamespace: 'myNamespace', // ApiClient 命名空间
    requiredProject: false,      // 是否需要选择项目
    emptyIcon: '图标',
    emptyText: '暂无数据',
    emptyHint: '提示文字',
    columns: [                   // DataTable 列定义
      { key: 'name', header: '名称', width: '200px' },
      { key: 'status', header: '状态', type: 'badge' },
      { key: 'description', header: '描述', type: 'truncate' },
      { key: 'updated_at', header: '更新时间', type: 'date' }
    ],
    filters: [                   // 筛选下拉框
      { key: 'status', label: '状态', options: [
        { value: '', label: '全部' },
        { value: 'active', label: '激活' }
      ]}
    ],
    formFields: [                // 表单字段定义
      { key: 'name', label: '名称', type: 'text', required: true },
      { key: 'description', label: '描述', type: 'textarea', rows: 3 },
      { key: 'type', label: '类型', type: 'select', options: [...] }
    ]
  };

  window.MyPage = {
    currentData: [],
    currentFilters: {},

    init() {
      this.render();
      this.loadData();
      return true;  // 必须返回 true
    },

    render() { /* 渲染页面 HTML */ },
    async loadData() { /* 加载数据 */ },
    renderList() { /* 渲染列表 */ },
    handleSearch: debounce(function(value) { ... }, 300),
    handleFilter(key, value) { ... },
    showCreateModal() { ... },
    hideModal() { ... },
    async handleEdit(id) { ... },
    async handleSave(e) { ... },
    async handleDelete(id, name) { ... },
    renderBadge(item) { ... }
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

---

## init() 必须返回 true

所有页面 `init()` 方法**必须返回 `true`**。这是因为路由 `navigateToPage()` 中使用了短路求值:

```javascript
case 'template-list':
  window.TemplateListPage?.init() || showPlaceholder(t('nav.templateList'));
  break;
```

如果 `init()` 不返回 `true`，即使页面初始化了，也会触发占位符渲染。

---

## loadData() 响应格式处理

API 返回格式不统一，需要做兼容处理:

```javascript
async loadData() {
  const result = await window.ApiClient.callTool('tool.name', params);

  // 多种可能的响应格式
  if (Array.isArray(result)) {
    this.currentData = result;
  } else if (result?.templates) {
    this.currentData = result.templates;  // prompt.template.list
  } else if (result?.items) {
    this.currentData = result.items;      // setting.item.list
  } else if (result?.data) {
    this.currentData = result.data;       // 通用 fallback
  } else if (result?.chapters) {
    this.currentData = result.chapters;   // local.chapter.list
  } else if (result?.projects) {
    this.currentData = result.projects;   // project.list
  } else {
    this.currentData = [];
  }
}
```

---

## ModalDialog 回调模式

**不使用** `show()` 返回值判断，**必须**使用 `onConfirm` 回调:

```javascript
// 正确 ✅
ModalDialog.show({
  title: '确认删除',
  content: '<p>确定吗？</p>',
  onConfirm: async () => {
    await deleteItem();
    ModalDialog.close();  // 显式关闭
  }
});

// 错误 ❌
const result = ModalDialog.show({...});
if (result) { ... }
```

### 快捷用法

```javascript
// 确认框
ModalDialog.confirm('确定删除吗？', async () => {
  await ApiClient.callTool('tool.delete', {...});
  await this.loadData();
});

// 提示框
ModalDialog.alert('操作成功', 'success');
ModalDialog.alert('加载失败: ' + error.message, 'error');
```

---

## 业务键 vs UUID

**优先使用业务键 (business key)** 而非数据库 UUID:

```javascript
// 正确 ✅ — 使用 template_key 业务键
await ApiClient.callTool('prompt.template.get', { workspace, template_key: 'chapter_outline' });
await ApiClient.callTool('prompt.template.delete', { workspace, template_key: 'chapter_outline' });

// 正确 ✅ — 使用 slug
await ApiClient.callTool('project.delete', { workspace, slug: 'my-project' });
await ApiClient.callTool('workspace.create', { slug: 'my-ws', name: 'My WS' });

// 错误 ❌ — 不要传 UUID 给工具
await ApiClient.callTool('prompt.template.delete', { id: 'uuid-xxx' });
```

---

## 搜索防抖模式

```javascript
// 模板中定义的本地 debounce
function debounce(fn, delay) {
  let timer;
  return function(...args) {
    clearTimeout(timer);
    timer = setTimeout(() => fn.apply(this, args), delay);
  };
}

// 使用
handleSearch: debounce(function(value) {
  TemplateListPage.currentFilters.search = value;
  TemplateListPage.loadData();
}, 300),
```

---

## 过滤处理模式

```javascript
handleFilter(key, value) {
  this.currentFilters[key] = value;
  this.loadData();  // 带上所有 currentFilters 重新请求
}

// 在 loadData 中使用
async loadData() {
  const params = { workspace, limit: 100 };
  if (this.currentFilters.category_slug) params.category_slug = this.currentFilters.category_slug;
  if (this.currentFilters.search) params.query = this.currentFilters.search;
  const result = await ApiClient.callTool('tool', params);
}
```

---

## Badge 渲染模式

```javascript
renderBadge(item) {
  const type = item.template_type || item.status;
  if (!type) return '';
  const classes = {
    system: 'bg-blue-100 text-blue-700',
    user: 'bg-green-100 text-green-700',
    active: 'bg-green-100 text-green-700',
    draft: 'bg-yellow-100 text-yellow-700',
    inactive: 'bg-gray-100 text-gray-500'
  };
  return `<span class="px-2 py-0.5 text-xs rounded-full ${classes[type] || 'bg-gray-100 text-gray-500'}">${type}</span>`;
}
```

---

## Workspace/Project 状态读取

```javascript
// 标准模式
const workspace = window.AppState?.currentWorkspace;
const project = window.AppState?.currentProject;

if (!workspace) {
  container.innerHTML = '<div>请先选择工作区</div>';
  return;
}

// ApiClient 命名空间方法会自动注入 project
const result = await ApiClient.promptTemplate.list(workspace, { template_type: 'system' });
// 内部: callTool('prompt.template.list', { workspace, project: AppState.currentProject, ...filters })
```

---

## 错误处理模式

```javascript
// try-catch 模式
try {
  const result = await ApiClient.callTool('tool.name', params);
  this.currentData = result;
  this.renderList();
} catch (error) {
  console.error('[PageName] Load error:', error);
  container.innerHTML = `<div class="p-8 text-center text-red-500">
    加载失败: ${error.message}
    <button onclick="PageName.loadData()">重试</button>
  </div>`;
}

// ModalDialog 错误提示
catch (error) {
  ModalDialog.alert('操作失败: ' + error.message, 'error');
}
```

---

## 表单提交模式

```javascript
async handleSave(e) {
  e.preventDefault();
  const workspace = window.AppState.currentWorkspace;
  const id = document.getElementById('page-id').value;
  const data = {};
  PAGE_CONFIG.formFields.forEach(field => {
    const el = document.getElementById('page-' + field.key);
    if (el) data[field.key] = el.value || undefined;
  });

  try {
    if (id) {
      await ApiClient.callTool('tool.update', { workspace, key: id, ...data });
    } else {
      await ApiClient.callTool('tool.create', { workspace, ...data });
    }
    this.hideModal();
    this.loadData();
    ModalDialog.alert('保存成功', 'success');
  } catch (error) {
    ModalDialog.alert('保存失败: ' + error.message, 'error');
  }
}
```

---

## 页面注册清单

创建新页面需完成以下步骤:
1. 创建 `js/pages/xxx-page.js` 文件 — 遵循标准 CRUD 模板
2. 在 `index.html` 中:
   a. 添加 `<script>` 标签加载页面 JS
   b. 在 `navigateToPage()` switch 中添加 `case`
3. 在 `menu-manager.js` 中添加菜单项（Group → Item）
4. 如需国际化，在 `js/core/i18n.js` 添加翻译键