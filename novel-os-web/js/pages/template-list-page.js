/**
 * 模板管理页面 - 标准化 CRUD 页面模板
 * 
 * 功能：列表展示、搜索过滤、新增、编辑、删除
 * 
 * 使用方式：
 * 1. 复制此文件，修改 PAGE_CONFIG 配置
 * 2. 在 index.html 添加路由和 script 标签
 * 3. 在 i18n 文件添加翻译键
 */
(function() {
  'use strict';
  console.log('[TemplateListPage] Script loading...');

  // ==================== 页面配置 ====================
  const PAGE_CONFIG = {
    pageId: 'template-list',
    pageName: '模板管理',
    apiNamespace: 'promptTemplate',
    requiredProject: false,
    emptyIcon: '📋',
    emptyText: '暂无模板',
    emptyHint: '点击右上角按钮创建第一个模板',
    columns: [
      { key: 'name', header: '模板名称', width: '200px' },
      { key: 'template_type', header: '类型', type: 'badge', width: '100px' },
      { key: 'description', header: '描述', type: 'truncate' },
      { key: 'updated_at', header: '更新时间', type: 'date', width: '150px' }
    ],
    filters: [
      { key: 'template_type', label: '类型', options: [
        { value: '', label: '全部' },
        { value: 'system', label: '系统' },
        { value: 'user', label: '用户' }
      ]}
    ],
    formFields: [
      { key: 'name', label: '模板名称', type: 'text', required: true },
      { key: 'template_key', label: '模板标识', type: 'text', required: true, placeholder: '如: chapter_outline' },
      { key: 'template_type', label: '类型', type: 'select', required: true, options: [
        { value: 'system', label: '系统' },
        { value: 'user', label: '用户' }
      ]},
      { key: 'description', label: '描述', type: 'textarea', rows: 2 },
      { key: 'template_content', label: '模板内容', type: 'textarea', rows: 10, required: true, monospace: true }
    ]
  };

  const PAGE_ID = PAGE_CONFIG.pageId;

  // ==================== 页面逻辑 ====================
  window.TemplateListPage = {
    currentData: [],
    currentFilters: {},

    init() {
      this.render();
      this.loadData();
      return true;
    },

    render() {
      const contentArea = document.getElementById('content-area');
      if (!contentArea) return;
      
      const cfg = PAGE_CONFIG;
      
      contentArea.innerHTML = `
        <div class="space-y-4">
          <div class="flex items-center justify-between">
            <div>
              <h1 class="text-2xl font-bold text-gray-800">${cfg.pageName}</h1>
              <p class="text-gray-500 mt-1">管理${cfg.pageName}条目</p>
            </div>
            <button onclick="TemplateListPage.showCreateModal()" 
                    class="px-4 py-2 bg-primary-600 text-white rounded-lg hover:bg-primary-700 transition-colors">
              ${t('common.new')} ${cfg.pageName}
            </button>
          </div>
          <div class="flex gap-4 items-center">
            <input type="text" id="${PAGE_ID}-search" 
                   placeholder="${t('common.search')}..." 
                   oninput="TemplateListPage.handleSearch(this.value)"
                   class="flex-1 px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary-500">
            ${cfg.filters.map(filter => `
              <select id="${PAGE_ID}-filter-${filter.key}" 
                      onchange="TemplateListPage.handleFilter('${filter.key}', this.value)"
                      class="px-4 py-2 border border-gray-300 rounded-lg">
                ${filter.options.map(opt => `<option value="${opt.value}">${opt.label}</option>`).join('')}
              </select>
            `).join('')}
          </div>
          <div id="${PAGE_ID}-container" class="bg-white rounded-lg shadow">
            <div class="p-8 text-center text-gray-500">
              <div class="spinner w-8 h-8 border-4 border-primary-600 border-t-transparent rounded-full animate-spin mx-auto"></div>
              <p class="mt-2">${t('common.loading')}</p>
            </div>
          </div>
        </div>
        <div id="${PAGE_ID}-modal" class="fixed inset-0 bg-black/50 z-50 hidden flex items-center justify-center">
          <div class="bg-white rounded-lg shadow-xl w-full max-w-2xl mx-4 max-h-[90vh] overflow-hidden">
            <div class="px-6 py-4 border-b border-gray-200 flex items-center justify-between">
              <h3 id="${PAGE_ID}-modal-title" class="text-lg font-semibold">新建${cfg.pageName}</h3>
              <button onclick="TemplateListPage.hideModal()" class="text-gray-400 hover:text-gray-600">
                <svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12"/>
                </svg>
              </button>
            </div>
            <div class="p-6 overflow-y-auto max-h-[60vh]">
              <form id="${PAGE_ID}-form" onsubmit="TemplateListPage.handleSave(event)">
                <input type="hidden" id="${PAGE_ID}-id">
                <div class="space-y-4">
                  ${cfg.formFields.map(field => `
                    <div>
                      <label class="block text-sm font-medium text-gray-700 mb-1">
                        ${field.label} ${field.required ? '<span class="text-red-500">*</span>' : ''}
                      </label>
                      ${field.type === 'textarea' ? `
                        <textarea id="${PAGE_ID}-${field.key}" 
                                  ${field.required ? 'required' : ''}
                                  rows="${field.rows || 3}"
                                  placeholder="${field.placeholder || ''}"
                                  class="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary-500 ${field.monospace ? 'font-mono text-sm' : ''}"></textarea>
                      ` : field.type === 'select' ? `
                        <select id="${PAGE_ID}-${field.key}" 
                                ${field.required ? 'required' : ''}
                                class="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary-500">
                          ${field.options.map(opt => `<option value="${opt.value}">${opt.label}</option>`).join('')}
                        </select>
                      ` : `
                        <input type="${field.type || 'text'}" 
                               id="${PAGE_ID}-${field.key}" 
                               ${field.required ? 'required' : ''}
                               placeholder="${field.placeholder || ''}"
                               class="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary-500">
                      `}
                    </div>
                  `).join('')}
                </div>
                <div class="mt-6 flex justify-end gap-3">
                  <button type="button" onclick="TemplateListPage.hideModal()" 
                          class="px-4 py-2 border border-gray-300 rounded-lg hover:bg-gray-50">
                    ${t('common.cancel')}
                  </button>
                  <button type="submit" 
                          class="px-4 py-2 bg-primary-600 text-white rounded-lg hover:bg-primary-700">
                    ${t('common.save')}
                  </button>
                </div>
              </form>
            </div>
          </div>
        </div>
      `;
    },

    async loadData() {
      const container = document.getElementById(`${PAGE_ID}-container`);
      if (!container) return;
      
      try {
        const workspace = window.AppState.currentWorkspace;
        if (!workspace) {
          container.innerHTML = `<div class="p-8 text-center text-gray-500">请先选择工作区</div>`;
          return;
        }
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
        this.renderList();
      } catch (error) {
        console.error(`[${PAGE_ID}] Load error:`, error);
        container.innerHTML = `<div class="p-8 text-center text-red-500">加载失败: ${error.message}</div>`;
      }
    },

    renderList() {
      const container = document.getElementById(`${PAGE_ID}-container`);
      if (!container) return;
      
      const data = this.currentData;
      if (!data || data.length === 0) {
        container.innerHTML = `
          <div class="p-8 text-center text-gray-500">
            <div class="text-4xl mb-2">${PAGE_CONFIG.emptyIcon}</div>
            <p>${PAGE_CONFIG.emptyText}</p>
            <p class="text-sm mt-2">${PAGE_CONFIG.emptyHint}</p>
          </div>
        `;
        return;
      }

      container.innerHTML = `
        <div class="divide-y divide-gray-200">
          ${data.map(item => `
            <div class="p-4 hover:bg-gray-50 transition-colors" data-id="${item.template_key}">
              <div class="flex items-start justify-between">
                <div class="flex-1 min-w-0">
                  <div class="flex items-center gap-2">
                    <h3 class="font-medium text-gray-800 truncate">${item.name || item.template_key}</h3>
                    ${this.renderBadge(item)}
                  </div>
                  ${item.description ? `<p class="text-sm text-gray-500 mt-1 line-clamp-2">${item.description}</p>` : ''}
                </div>
                <div class="flex items-center gap-2 ml-4">
                  <button onclick="TemplateListPage.handleEdit('${item.template_key}')"
                          class="p-2 text-gray-400 hover:text-primary-600 hover:bg-primary-50 rounded transition-colors" title="编辑">
                    <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M11 5H6a2 2 0 00-2 2v11a2 2 0 002 2h11a2 2 0 002-2v-5m-1.414-9.414a2 2 0 112.828 2.828L11.828 15H9v-2.828l8.586-8.586z"/>
                    </svg>
                  </button>
                  <button onclick="TemplateListPage.handleDelete('${item.template_key}', '${(item.name || item.template_key).replace(/'/g, "\\'")}')"
                          class="p-2 text-gray-400 hover:text-red-600 hover:bg-red-50 rounded transition-colors" title="删除">
                    <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16"/>
                    </svg>
                  </button>
                </div>
              </div>
            </div>
          `).join('')}
        </div>
      `;
    },

    handleSearch: debounce(function(value) {
      TemplateListPage.currentFilters.search = value;
      TemplateListPage.loadData();
    }, 300),

    handleFilter(key, value) {
      this.currentFilters[key] = value;
      this.loadData();
    },

    showCreateModal() {
      document.getElementById(`${PAGE_ID}-modal-title`).textContent = `新建${PAGE_CONFIG.pageName}`;
      document.getElementById(`${PAGE_ID}-id`).value = '';
      PAGE_CONFIG.formFields.forEach(field => {
        const el = document.getElementById(`${PAGE_ID}-${field.key}`);
        if (el) el.value = field.type === 'select' ? (field.options?.[0]?.value || '') : '';
      });
      document.getElementById(`${PAGE_ID}-modal`).classList.remove('hidden');
    },

    hideModal() {
      document.getElementById(`${PAGE_ID}-modal`).classList.add('hidden');
    },

    async handleEdit(id) {
      try {
        const workspace = window.AppState.currentWorkspace;
        const item = await window.ApiClient[PAGE_CONFIG.apiNamespace].get(workspace, id);
        document.getElementById(`${PAGE_ID}-modal-title`).textContent = `编辑${PAGE_CONFIG.pageName}`;
        document.getElementById(`${PAGE_ID}-id`).value = id;
        PAGE_CONFIG.formFields.forEach(field => {
          const el = document.getElementById(`${PAGE_ID}-${field.key}`);
          if (el) el.value = item[field.key] || '';
        });
        document.getElementById(`${PAGE_ID}-modal`).classList.remove('hidden');
      } catch (error) {
        ModalDialog.alert('加载失败: ' + error.message, 'error');
      }
    },

    async handleSave(e) {
      e.preventDefault();
      const workspace = window.AppState.currentWorkspace;
      const id = document.getElementById(`${PAGE_ID}-id`).value;
      const data = {};
      PAGE_CONFIG.formFields.forEach(field => {
        const el = document.getElementById(`${PAGE_ID}-${field.key}`);
        if (el) data[field.key] = el.value || undefined;
      });
      try {
        if (id) {
          await window.ApiClient[PAGE_CONFIG.apiNamespace].update(workspace, id, data);
        } else {
          await window.ApiClient[PAGE_CONFIG.apiNamespace].create(workspace, data);
        }
        this.hideModal();
        this.loadData();
        ModalDialog.alert(id ? '更新成功' : '创建成功', 'success');
      } catch (error) {
        ModalDialog.alert('保存失败: ' + error.message, 'error');
      }
    },

    async handleDelete(id, name) {
      ModalDialog.confirm(`确定删除 "${name}" 吗？`, async () => {
        try {
          await window.ApiClient[PAGE_CONFIG.apiNamespace].delete(window.AppState.currentWorkspace, id);
          this.loadData();
          ModalDialog.alert('删除成功', 'success');
        } catch (error) {
          ModalDialog.alert('删除失败: ' + error.message, 'error');
        }
      });
    },

    renderBadge(item) {
      const type = item.template_type || item.status;
      if (!type) return '';
      const classes = { system: 'bg-blue-100 text-blue-700', user: 'bg-green-100 text-green-700', active: 'bg-green-100 text-green-700', draft: 'bg-yellow-100 text-yellow-700' };
      return `<span class="px-2 py-0.5 text-xs rounded-full ${classes[type] || 'bg-gray-100 text-gray-500'}">${type}</span>`;
    }
  };

  function debounce(fn, delay) {
    let timer;
    return function(...args) {
      clearTimeout(timer);
      timer = setTimeout(() => fn.apply(this, args), delay);
    };
  }

  console.log('[TemplateListPage] Script loaded, window.TemplateListPage:', !!window.TemplateListPage);
})();
