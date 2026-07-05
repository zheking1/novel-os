/**
 * 项目知识管理页面 - CRUD for project knowledge entries
 */
(function() {
  'use strict';

  const PAGE_CONFIG = {
    pageId: 'kb-pk',
    pageName: '项目知识',
    apiNamespace: 'kb.pk',
    requiredProject: true,
    emptyIcon: '📚',
    emptyText: '暂无知识条目',
    emptyHint: '点击右上角按钮创建第一个知识条目',
    columns: [
      { key: 'key', header: '标识', width: '150px', mono: true },
      { key: 'category', header: '分类', type: 'badge', width: '120px' },
      { key: 'description', header: '描述', type: 'truncate' },
      { key: 'chapter_no', header: '章节', width: '80px' },
      { key: 'updated_at', header: '更新时间', type: 'date', width: '150px' }
    ],
    filters: [
      { key: 'category', label: '分类', options: [
        { value: '', label: '全部' },
        { value: 'world_rule', label: '世界规则' },
        { value: 'character', label: '角色' },
        { value: 'faction', label: '势力' },
        { value: 'plot', label: '情节' },
        { value: 'world_state', label: '世界状态' },
        { value: 'timeline', label: '时间线' }
      ]}
    ],
    formFields: [
      { key: 'category', label: '分类', type: 'select', required: true, options: [
        { value: 'world_rule', label: '世界规则' },
        { value: 'character', label: '角色' },
        { value: 'faction', label: '势力' },
        { value: 'plot', label: '情节' },
        { value: 'world_state', label: '世界状态' },
        { value: 'timeline', label: '时间线' }
      ]},
      { key: 'key', label: '标识', type: 'text', required: true, placeholder: '如: magic_system' },
      { key: 'description', label: '描述', type: 'text', required: true },
      { key: 'value', label: '内容 (JSON)', type: 'textarea', rows: 8, monospace: true, required: true, placeholder: '{"name": "...", "detail": "..."}' },
      { key: 'chapter_no', label: '首次出现章节', type: 'number' },
      { key: 'tags', label: '标签 (逗号分隔)', type: 'text', placeholder: 'magic, power, system' }
    ]
  };

  const PAGE_ID = PAGE_CONFIG.pageId;

  window.KbPkListPage = {
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
              <p class="text-gray-500 mt-1">管理项目知识条目 (角色/势力/世界规则等)</p>
            </div>
            <button onclick="KbPkListPage.showCreateModal()" 
                    class="px-4 py-2 bg-primary-600 text-white rounded-lg hover:bg-primary-700 transition-colors">
              ${t('common.new')} ${cfg.pageName}
            </button>
          </div>
          <div class="flex gap-4 items-center">
            <input type="text" id="${PAGE_ID}-search" 
                   placeholder="${t('common.search')}..." 
                   oninput="KbPkListPage.handleSearch(this.value)"
                   class="flex-1 px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary-500">
            ${cfg.filters.map(filter => `
              <select id="${PAGE_ID}-filter-${filter.key}" 
                      onchange="KbPkListPage.handleFilter('${filter.key}', this.value)"
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
              <button onclick="KbPkListPage.hideModal()" class="text-gray-400 hover:text-gray-600">
                <svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12"/>
                </svg>
              </button>
            </div>
            <div class="p-6 overflow-y-auto max-h-[60vh]">
              <form id="${PAGE_ID}-form" onsubmit="KbPkListPage.handleSave(event)">
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
                  <button type="button" onclick="KbPkListPage.hideModal()" 
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
        const project = window.AppState.currentProject;
        if (!workspace || !project) {
          container.innerHTML = `<div class="p-8 text-center text-gray-500">请先选择工作区和项目</div>`;
          return;
        }
        const result = await window.ApiClient.callTool('kb.pk.list', { workspace, project, category: this.currentFilters.category || undefined });
        let items = [];
        if (Array.isArray(result)) {
          items = result;
        } else if (result?.items) {
          items = result.items;
        } else if (result?.data) {
          items = result.data;
        }
        this.currentData = items;
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
            <div class="p-4 hover:bg-gray-50 transition-colors" data-id="${item.key}">
              <div class="flex items-start justify-between">
                <div class="flex-1 min-w-0">
                  <div class="flex items-center gap-2">
                    <code class="text-sm font-mono text-gray-800">${item.key}</code>
                    ${this.renderBadge(item.category)}
                    ${item.chapter_no ? `<span class="text-xs text-gray-400">Ch.${item.chapter_no}</span>` : ''}
                  </div>
                  <p class="text-sm text-gray-600 mt-1">${item.description || ''}</p>
                </div>
                <div class="flex items-center gap-2 ml-4">
                  <button onclick="KbPkListPage.handleEdit('${item.key}')" 
                          class="p-2 text-gray-400 hover:text-primary-600 hover:bg-primary-50 rounded transition-colors" title="编辑">
                    <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M11 5H6a2 2 0 00-2 2v11a2 2 0 002 2h11a2 2 0 002-2v-5m-1.414-9.414a2 2 0 112.828 2.828L11.828 15H9v-2.828l8.586-8.586z"/>
                    </svg>
                  </button>
                  <button onclick="KbPkListPage.handleDelete('${item.key}', '${(item.key).replace(/'/g, "\\'")}')"
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
      KbPkListPage.currentFilters.search = value;
      KbPkListPage.loadData();
    }, 300),

    handleFilter(key, value) {
      this.currentFilters[key] = value;
      this.loadData();
    },

    showCreateModal() {
      document.getElementById(`${PAGE_ID}-modal-title`).textContent = `新建${PAGE_CONFIG.pageName}`;
      PAGE_CONFIG.formFields.forEach(field => {
        const el = document.getElementById(`${PAGE_ID}-${field.key}`);
        if (el) el.value = field.type === 'select' ? (field.options?.[0]?.value || '') : '';
      });
      document.getElementById(`${PAGE_ID}-modal`).classList.remove('hidden');
    },

    hideModal() {
      document.getElementById(`${PAGE_ID}-modal`).classList.add('hidden');
    },

    async handleEdit(key) {
      try {
        const workspace = window.AppState.currentWorkspace;
        const project = window.AppState.currentProject;
        const item = await window.ApiClient.callTool('kb.pk.get', { workspace, project, category: this.currentFilters.category || 'world_rule', key });
        document.getElementById(`${PAGE_ID}-modal-title`).textContent = `编辑${PAGE_CONFIG.pageName}`;
        PAGE_CONFIG.formFields.forEach(field => {
          const el = document.getElementById(`${PAGE_ID}-${field.key}`);
          if (el) {
            if (field.key === 'value') {
              el.value = JSON.stringify(item[field.key] || item.value || {}, null, 2);
            } else if (field.key === 'tags') {
              el.value = (item[field.key] || []).join(', ');
            } else {
              el.value = item[field.key] || '';
            }
          }
        });
        document.getElementById(`${PAGE_ID}-modal`).classList.remove('hidden');
      } catch (error) {
        ModalDialog.alert('加载失败: ' + error.message, 'error');
      }
    },

    async handleSave(e) {
      e.preventDefault();
      const workspace = window.AppState.currentWorkspace;
      const project = window.AppState.currentProject;
      const category = document.getElementById(`${PAGE_ID}-category`).value;
      const key = document.getElementById(`${PAGE_ID}-key`).value;
      const description = document.getElementById(`${PAGE_ID}-description`).value;
      const valueStr = document.getElementById(`${PAGE_ID}-value`).value;
      const chapterNo = document.getElementById(`${PAGE_ID}-chapter_no`).value;
      const tagsStr = document.getElementById(`${PAGE_ID}-tags`).value;

      let value;
      try {
        value = JSON.parse(valueStr);
      } catch (err) {
        ModalDialog.alert('JSON 格式错误: ' + err.message, 'error');
        return;
      }

      const data = {
        category,
        key,
        description,
        value,
        chapter_no: chapterNo ? parseInt(chapterNo) : undefined,
        tags: tagsStr ? tagsStr.split(',').map(t => t.trim()).filter(Boolean) : undefined
      };

      try {
        await window.ApiClient.callTool('kb.pk.upsert', { workspace, project, ...data });
        this.hideModal();
        this.loadData();
        ModalDialog.alert('保存成功', 'success');
      } catch (error) {
        ModalDialog.alert('保存失败: ' + error.message, 'error');
      }
    },

    async handleDelete(key, name) {
      ModalDialog.confirm(`确定删除 "${name}" 吗？`, async () => {
        try {
          const workspace = window.AppState.currentWorkspace;
          const project = window.AppState.currentProject;
          await window.ApiClient.callTool('kb.pk.delete', { workspace, project, category: this.currentFilters.category || 'world_rule', key });
          this.loadData();
          ModalDialog.alert('删除成功', 'success');
        } catch (error) {
          ModalDialog.alert('删除失败: ' + error.message, 'error');
        }
      });
    },

    renderBadge(category) {
      const classes = {
        world_rule: 'bg-blue-100 text-blue-700',
        character: 'bg-green-100 text-green-700',
        faction: 'bg-purple-100 text-purple-700',
        plot: 'bg-yellow-100 text-yellow-700',
        world_state: 'bg-red-100 text-red-700',
        timeline: 'bg-indigo-100 text-indigo-700'
      };
      const labels = {
        world_rule: '世界规则',
        character: '角色',
        faction: '势力',
        plot: '情节',
        world_state: '世界状态',
        timeline: '时间线'
      };
      return `<span class="px-2 py-0.5 text-xs rounded-full ${classes[category] || 'bg-gray-100 text-gray-500'}">${labels[category] || category}</span>`;
    }
  };

  function debounce(fn, delay) {
    let timer;
    return function(...args) {
      clearTimeout(timer);
      timer = setTimeout(() => fn.apply(this, args), delay);
    };
  }
})();
