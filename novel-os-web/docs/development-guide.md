# Novel OS Web Client - 开发文档

## 一、开发环境

### 1.1 技术栈
- **前端框架**: Alpine.js（轻量级响应式框架）
- **CSS**: Tailwind CSS（CDN版本）
- **构建工具**: 无需构建，直接部署
- **服务器**: Python HTTP Server

### 1.2 目录结构

```
novel-os-web/
├── index.html                    # 主入口文件
├── server.py                     # Python HTTP 服务器
├── Dockerfile                    # Docker 构建文件
├── i18n/                         # 国际化语言包
│   ├── zh.json
│   └── en.json
├── js/
│   ├── core/                     # 核心模块
│   │   ├── i18n.js               # 国际化模块
│   │   ├── api-client.js         # API 客户端
│   │   ├── app-core.js           # 应用核心工具
│   │   ├── menu-manager.js       # 菜单管理器
│   │   └── router.js             # 路由器
│   ├── components/               # 通用组件
│   │   ├── data-table.js         # 数据表格
│   │   ├── modal-dialog.js       # 模态框
│   │   ├── form-builder.js       # 表单构建器
│   │   ├── loading-overlay.js    # 加载遮罩
│   │   └── toast-container.js    # 消息提示
│   └── pages/                    # 页面组件
│       ├── level-manager.js      # 等级管理（已实现）
│       ├── genre-manager.js      # 类型管理（已实现）
│       ├── category-manager.js   # 分类管理（已实现）
│       ├── binding-matrix-manager.js  # 类型绑定（已实现）
│       ├── health-page.js        # 系统健康（已实现）
│       └── ...                   # 待实现的页面
└── docs/                         # 文档
    ├── menu-migration-plan.md    # 菜单迁移计划
    └── development-guide.md      # 开发指南（本文件）
```

---

## 二、核心模块 API

### 2.1 i18n 国际化模块

```javascript
// 获取翻译文本
window.t(key, params = {})
// 示例
window.t('nav.canonList')  // "Canon文档"
window.t('common.save')    // "保存"

// 切换语言
await window.i18n.setLang('en')

// 获取当前语言
window.i18n.getCurrentLang()  // 'zh' 或 'en'
```

### 2.2 ApiClient API 客户端

```javascript
// 工作区相关
await window.ApiClient.workspace.list()
await window.ApiClient.project.list(workspace)

// 设定相关
await window.ApiClient.setting.list(workspace)
await window.ApiClient.setting.get(workspace, slug)
await window.ApiClient.setting.upsert(workspace, data)
await window.ApiClient.setting.delete(workspace, categoryId)

// 项目相关
await window.ApiClient.item.list(workspace, categoryId)
await window.ApiClient.item.upsert(workspace, data)
await window.ApiClient.item.delete(workspace, itemId)

// 类型相关
await window.ApiClient.genre.list()
await window.ApiClient.genre.upsert(data)
await window.ApiClient.genre.delete(slug)

// MCP 工具调用
await window.ApiClient.callTool(toolName, args)
```

### 2.3 AppCore 应用核心

```javascript
// 显示加载状态
window.AppCore.setLoading(true/false)

// 显示消息提示
window.AppCore.toast(message, type)
// type: 'success' | 'error' | 'warning' | 'info'

// 防抖函数
window.AppCore.debounce(fn, delay)

// 节流函数
window.AppCore.throttle(fn, limit)
```

### 2.4 MenuManager 菜单管理器

```javascript
// 获取菜单数据
const menu = window.MenuManager.getMenu({ t: window.t, project: 'xxx' })

// 设置当前页面
window.MenuManager.setCurrentPage('canon-list')

// 获取页面信息
const pageInfo = window.MenuManager.getPageInfo('canon-list')

// 切换分组展开状态
window.MenuManager.toggleGroup('project-settings')
```

### 2.5 DataTable 数据表格

```javascript
window.DataTable.render({
  containerId: 'table-container',
  columns: [
    { key: 'name', header: '名称' },
    { key: 'slug', header: '标识', render: (val) => `<code>${val}</code>` },
    { key: 'status', header: '状态', type: 'badge' }
  ],
  data: items,
  actions: [
    { label: '编辑', icon: '✏️', onClick: (id) => edit(id) },
    { label: '删除', icon: '🗑️', onClick: (id) => delete(id) }
  ],
  emptyMessage: '暂无数据'
})
```

### 2.6 ModalDialog 模态框

```javascript
// 显示确认框
window.ModalDialog.confirm('确定删除吗？', async () => {
  // 执行删除操作
})

// 显示提示框
window.ModalDialog.alert('操作成功', 'success')

// 显示自定义模态框
window.ModalDialog.show({
  title: '编辑',
  content: '<form>...</form>',
  size: 'md',
  onConfirm: async (modalId) => {
    // 保存操作
  }
})

// 关闭模态框
window.ModalDialog.close()
```

---

## 三、页面组件开发规范

### 3.1 组件结构模板

```javascript
/**
 * Novel OS - [Page Name]
 * [页面描述]
 * @version 1.0.0
 */

(function() {
  'use strict';

  if (window.PageName) {
    return;
  }

  const PageName = {
    // 数据
    items: [],

    /**
     * 初始化
     */
    async init() {
      console.log('[PageName] Initializing...');
      this.showLoading();

      try {
        await this.loadData();
        this.render();
      } catch (error) {
        console.error('[PageName] Initialization failed:', error);
        this.showError(error.message);
      }
    },

    /**
     * 加载数据
     */
    async loadData() {
      const workspace = window.AppState?.currentWorkspace;
      const project = window.AppState?.currentProject;
      
      // 调用 API 获取数据
      const result = await window.ApiClient.callTool('tool.name', { workspace, project });
      this.items = result || [];
    },

    /**
     * 渲染页面
     */
    render() {
      const container = document.getElementById('content-area');
      if (!container) return;

      container.innerHTML = `
        <div class="space-y-6">
          <!-- 页面头部 -->
          <div class="flex items-center justify-between">
            <div>
              <h1 class="text-2xl font-bold text-gray-900">${t('page.title')}</h1>
              <p class="mt-1 text-sm text-gray-500">${t('page.description')}</p>
            </div>
            <button onclick="PageName.showAddModal()"
                    class="px-4 py-2 bg-primary-600 text-white rounded-lg hover:bg-primary-700">
              + ${t('common.new')}
            </button>
          </div>

          <!-- 数据表格 -->
          <div class="bg-white shadow rounded-lg overflow-hidden">
            <div id="data-table"></div>
          </div>
        </div>
      `;

      this.renderTable();
    },

    /**
     * 渲染表格
     */
    renderTable() {
      window.DataTable.render({
        containerId: 'data-table',
        columns: [
          // 定义列
        ],
        data: this.items,
        actions: [
          // 定义操作按钮
        ],
        emptyMessage: t('common.noData')
      });
    },

    /**
     * 显示加载状态
     */
    showLoading() {
      const container = document.getElementById('content-area');
      if (container) {
        container.innerHTML = `
          <div class="flex items-center justify-center py-12">
            <div class="spinner w-8 h-8 border-4 border-primary-600 border-t-transparent rounded-full animate-spin"></div>
            <span class="ml-3 text-gray-600">${t('common.loading')}</span>
          </div>
        `;
      }
    },

    /**
     * 显示错误
     */
    showError(message) {
      const container = document.getElementById('content-area');
      if (container) {
        container.innerHTML = `
          <div class="bg-red-50 border border-red-200 rounded-lg p-8 text-center">
            <h2 class="text-xl font-bold text-red-600 mb-2">${t('common.error')}</h2>
            <p class="text-red-500">${message}</p>
          </div>
        `;
      }
    }
  };

  window.PageName = PageName;

})();
```

### 3.2 开发步骤

1. **创建组件文件**: 在 `js/pages/` 目录下创建新的 JS 文件
2. **实现组件结构**: 按照模板实现 init, loadData, render 等方法
3. **更新 index.html**: 
   - 添加 `<script>` 标签加载组件
   - 在 `navigateToPage()` 中添加路由
4. **更新 i18n**: 添加翻译键
5. **部署测试**: 上传到 NAS 并测试

---

## 四、API 工具对照表

| 功能 | API 工具名 | 参数 |
|------|-----------|------|
| 列出工作区 | `workspace.list` | `{}` |
| 列出项目 | `project.list` | `{ workspace }` |
| 列出分类 | `setting.category.list` | `{ workspace }` |
| 获取分类 | `setting.category.get` | `{ workspace, slug }` |
| 创建/更新分类 | `setting.category.upsert` | `{ workspace, name, slug, ... }` |
| 删除分类 | `setting.category.delete` | `{ workspace, category_id }` |
| 列出设定项 | `setting.item.list` | `{ workspace, category_id }` |
| 创建/更新设定项 | `setting.item.upsert` | `{ workspace, name, category_id, ... }` |
| 删除设定项 | `setting.item.delete` | `{ workspace, item_id }` |
| 列出类型 | `setting.genre.list` | `{}` |
| 创建/更新类型 | `setting.genre.upsert` | `{ name, slug, ... }` |
| 删除类型 | `setting.genre.delete` | `{ slug }` |
| 获取类型绑定矩阵 | `genre.binding.matrix` | `{}` |
| 批量更新绑定 | `genre.binding.bulk_upsert` | `{ bindings: [...] }` |
| 列出 Canon 文档 | `canon_doc.list` | `{ workspace, project }` |
| 创建/更新 Canon 文档 | `canon_doc.upsert` | `{ workspace, project, key, title, content }` |
| 删除 Canon 文档 | `canon_doc.delete` | `{ workspace, project, document_id }` |
| 列出实体 | `state_entity.list` | `{ workspace, project }` |
| 创建/更新实体 | `state_entity.upsert` | `{ workspace, project, name, entity_type, ... }` |
| 删除实体 | `state_entity.delete` | `{ workspace, project, entity_id }` |
| 列出情节线 | `plot_thread.list` | `{ workspace, project }` |
| 创建/更新情节线 | `plot_thread.upsert` | `{ workspace, project, key, title, ... }` |
| 列出伏笔 | `foreshadowing.list` | `{ workspace, project }` |
| 创建/更新伏笔 | `foreshadowing.upsert` | `{ workspace, project, key, title, ... }` |
| 获取系统健康 | `health.check` | `{}` |

---

## 五、部署流程

### 5.1 本地开发

1. 修改本地文件
2. 使用 pscp 上传到 NAS:
```powershell
pscp -pw "${NAS_SSH_PASSWORD}" <本地文件> root@${NAS_HOST}:/opt/novel-os/novel-os-web/<目标路径>
```

### 5.2 重建镜像

```powershell
plink -batch -pw "${NAS_SSH_PASSWORD}" root@${NAS_HOST} "cd /opt/novel-os && docker compose -f docker-compose.yml -f docker-compose.app.example.yml up -d --build novel-os-web"
```

### 5.3 验证部署

```powershell
# 检查容器状态
plink -batch -pw "${NAS_SSH_PASSWORD}" root@${NAS_HOST} "docker ps | grep novel-os-web"

# 检查文件是否存在
plink -batch -pw "${NAS_SSH_PASSWORD}" root@${NAS_HOST} "docker exec novel-os-web ls /app/js/pages/"

# 测试 API
plink -batch -pw "${NAS_SSH_PASSWORD}" root@${NAS_HOST} "curl -s http://127.0.0.1:8790/health"
```

---

## 六、常见问题

### Q1: 页面刷新后 404
**原因**: 文件未上传到容器，或容器未重建  
**解决**: 
1. 确保文件已上传到 NAS 的 `/opt/novel-os/novel-os-web/` 目录
2. 执行 docker compose build 重建镜像

### Q2: API 调用失败
**原因**: 工作区或项目未选择  
**解决**: 确保 `window.AppState.currentWorkspace` 和 `window.AppState.currentProject` 已设置

### Q3: 菜单不显示
**原因**: i18n 翻译键缺失  
**解决**: 检查 `i18n/zh.json` 和 `i18n/en.json` 是否包含对应的翻译键

---

*文档版本：v1.0*
*创建时间：2026-07-05*
