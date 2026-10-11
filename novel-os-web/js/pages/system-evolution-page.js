/**
 * System Evolution Page - 系统进化管理页面
 * 
 * 管理系统级数据的进化提案，AI自动初审 + 管理员终审
 */
(function() {
  'use strict';
  console.log('[SystemEvolutionPage] Script loading...');

  // ==================== 页面配置 ====================
  const PAGE_CONFIG = {
    pageId: 'system-evolution',
    pageName: '系统进化管理',
    apiNamespace: 'systemEvolution',
    requiredProject: false,
    emptyIcon: '📊',
    emptyText: '暂无进化提案',
    emptyHint: '点击右上角按钮提交第一个提案',
    columns: [
      { key: 'title', header: '提案标题', width: '250px' },
      { key: 'proposal_type', header: '类型', type: 'badge', width: '80px' },
      { key: 'target_entity_type', header: '目标类型', type: 'badge', width: '100px' },
      { key: 'status', header: '状态', type: 'badge', width: '100px' },
      { key: 'ai_score', header: 'AI评分', width: '80px' },
      { key: 'created_at', header: '创建时间', type: 'date', width: '150px' }
    ],
    filters: [
      { key: 'status', label: '状态', options: [
        { value: '', label: '全部状态' },
        { value: 'draft', label: '草稿' },
        { value: 'ai_reviewing', label: 'AI初审中' },
        { value: 'ai_reviewed', label: 'AI初审完成' },
        { value: 'pending_admin', label: '待管理员审核' },
        { value: 'admin_approved', label: '已批准' },
        { value: 'admin_rejected', label: '已拒绝' },
        { value: 'applied', label: '已应用' }
      ]},
      { key: 'target_entity_type', label: '目标类型', options: [
        { value: '', label: '全部类型' },
        { value: 'style_profile', label: '文风档案' },
        { value: 'prompt_template', label: '提示词模板' },
        { value: 'model_profile', label: '模型配置' },
        { value: 'knowledge_item', label: '知识条目' },
        { value: 'setting_item', label: '设置项' },
        { value: 'genre_config', label: '题材配置' }
      ]}
    ],
    formFields: [
      { key: 'title', label: '提案标题', type: 'text', required: true },
      { key: 'proposal_type', label: '提案类型', type: 'select', required: true, options: [
        { value: 'create', label: '创建' },
        { value: 'update', label: '更新' },
        { value: 'delete', label: '删除' },
        { value: 'merge', label: '合并' }
      ]},
      { key: 'target_entity_type', label: '目标实体类型', type: 'select', required: true, options: [
        { value: 'style_profile', label: '文风档案' },
        { value: 'prompt_template', label: '提示词模板' },
        { value: 'model_profile', label: '模型配置' },
        { value: 'knowledge_item', label: '知识条目' },
        { value: 'setting_item', label: '设置项' },
        { value: 'genre_config', label: '题材配置' }
      ]},
      { key: 'target_entity_key', label: '目标实体键', type: 'text', placeholder: '如: xianxia_style（更新/删除时必填）' },
      { key: 'description', label: '提案描述', type: 'textarea', rows: 3, required: true },
      { key: 'evolution_reason', label: '进化原因', type: 'textarea', rows: 3, required: true },
      { key: 'proposed_content', label: '提案内容(JSON)', type: 'textarea', rows: 5, monospace: true, placeholder: '{"key": "value"}' }
    ]
  };

  const PAGE_ID = PAGE_CONFIG.pageId;

  // ==================== 页面逻辑 ====================
  window.SystemEvolutionPage = {
    currentData: [],
    currentFilters: {},

    init() {
      console.log('[SystemEvolutionPage] init() called');
      this.render();
      this.loadData();
      return true;
    },

    render() {
      console.log('[SystemEvolutionPage] render() called');
      const contentArea = document.getElementById('content-area');
      if (!contentArea) {
        console.error('[SystemEvolutionPage] content-area not found!');
        return;
      }
      
      const cfg = PAGE_CONFIG;
      
      contentArea.innerHTML = `
        <div class="space-y-4">
          <!-- 页面标题 -->
          <div class="flex items-center justify-between">
            <div>
              <h1 class="text-2xl font-bold text-gray-800">${cfg.pageName}</h1>
              <p class="text-gray-500 mt-1">管理系统级数据的进化提案，AI自动初审 + 管理员终审</p>
            </div>
            <button onclick="SystemEvolutionPage.showCreateModal()" 
                    class="px-4 py-2 bg-primary-600 text-white rounded-lg hover:bg-primary-700 transition-colors flex items-center gap-2">
              <span>+</span>
              <span>提交新提案</span>
            </button>
          </div>

          <!-- 统计卡片 -->
          <div class="grid grid-cols-4 gap-4">
            <div class="bg-white rounded-xl p-4 shadow-sm border border-gray-100">
              <div class="text-sm text-gray-500">待AI初审</div>
              <div class="text-2xl font-bold text-blue-600 mt-1" id="stat-ai-reviewing">-</div>
            </div>
            <div class="bg-white rounded-xl p-4 shadow-sm border border-gray-100">
              <div class="text-sm text-gray-500">待管理员审核</div>
              <div class="text-2xl font-bold text-yellow-600 mt-1" id="stat-pending-admin">-</div>
            </div>
            <div class="bg-white rounded-xl p-4 shadow-sm border border-gray-100">
              <div class="text-sm text-gray-500">本月已通过</div>
              <div class="text-2xl font-bold text-green-600 mt-1" id="stat-approved">-</div>
            </div>
            <div class="bg-white rounded-xl p-4 shadow-sm border border-gray-100">
              <div class="text-sm text-gray-500">累计进化</div>
              <div class="text-2xl font-bold text-gray-800 mt-1" id="stat-total">-</div>
            </div>
          </div>

          <!-- 筛选栏 -->
          <div class="flex gap-4 items-center">
            <input type="text" id="${PAGE_ID}-search" 
                   placeholder="搜索提案..." 
                   oninput="SystemEvolutionPage.handleSearch(this.value)"
                   class="flex-1 px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary-500">
            ${cfg.filters.map(filter => `
              <select id="${PAGE_ID}-filter-${filter.key}" 
                      onchange="SystemEvolutionPage.handleFilter('${filter.key}', this.value)"
                      class="px-4 py-2 border border-gray-300 rounded-lg">
                ${filter.options.map(opt => `<option value="${opt.value}">${opt.label}</option>`).join('')}
              </select>
            `).join('')}
          </div>

          <!-- 列表容器 -->
          <div id="${PAGE_ID}-container" class="bg-white rounded-lg shadow">
            <div class="p-8 text-center text-gray-500">
              <div class="spinner w-8 h-8 border-4 border-primary-600 border-t-transparent rounded-full animate-spin mx-auto"></div>
              <p class="mt-2">加载中...</p>
            </div>
          </div>
        </div>

        <!-- 模态框 -->
        <div id="${PAGE_ID}-modal" class="fixed inset-0 bg-black/50 z-50 hidden flex items-center justify-center">
          <div class="bg-white rounded-lg shadow-xl w-full max-w-2xl mx-4 max-h-[90vh] overflow-hidden">
            <div class="px-6 py-4 border-b border-gray-200 flex items-center justify-between">
              <h3 id="${PAGE_ID}-modal-title" class="text-lg font-semibold">新建提案</h3>
              <button onclick="SystemEvolutionPage.hideModal()" class="text-gray-400 hover:text-gray-600">
                <svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12"/>
                </svg>
              </button>
            </div>
            <div class="p-6 overflow-y-auto max-h-[60vh]">
              <form id="${PAGE_ID}-form" onsubmit="SystemEvolutionPage.handleSave(event)">
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
                  <button type="button" onclick="SystemEvolutionPage.hideModal()" 
                          class="px-4 py-2 border border-gray-300 rounded-lg hover:bg-gray-50">
                    取消
                  </button>
                  <button type="submit" id="system-evolution-save-btn" class="px-4 py-2 bg-primary-600 text-white rounded-lg hover:bg-primary-700">
                    保存
                  </button>
                </div>
              </form>
            </div>
          </div>
        </div>
      `;
    },

    async loadData() {
      console.log('[SystemEvolutionPage] loadData() called');
      const container = document.getElementById(`${PAGE_ID}-container`);
      if (!container) return;
      
      try {
        const workspace = window.AppState?.currentWorkspace;
        if (!workspace) {
          container.innerHTML = `<div class="p-8 text-center text-gray-500">请先选择工作区</div>`;
          return;
        }

        const result = await window.ApiClient.callTool('system.evolution.list', { 
          workspace, 
          project: window.AppState?.currentProject,
          limit: 50,
          ...this.currentFilters 
        });

        console.log('[SystemEvolutionPage] API result:', result);

        if (Array.isArray(result)) {
          this.currentData = result;
        } else if (result?.proposals) {
          this.currentData = result.proposals;
        } else if (result?.items) {
          this.currentData = result.items;
        } else if (result?.data) {
          this.currentData = result.data;
        } else {
          this.currentData = [];
        }

        // 更新统计
        this.updateStats(result?.total || this.currentData.length);
        this.renderList();
      } catch (error) {
        console.error(`[${PAGE_ID}] Load error:`, error);
        container.innerHTML = `<div class="p-8 text-center text-red-500">加载失败: ${error.message}</div>`;
      }
    },

    updateStats(total) {
      const statTotal = document.getElementById('stat-total');
      if (statTotal) statTotal.textContent = total || 0;
      
      // 简化显示，实际应该分别查询各状态数量
      const statAiReviewing = document.getElementById('stat-ai-reviewing');
      const statPendingAdmin = document.getElementById('stat-pending-admin');
      const statApproved = document.getElementById('stat-approved');
      
      if (statAiReviewing) statAiReviewing.textContent = '-';
      if (statPendingAdmin) statPendingAdmin.textContent = '-';
      if (statApproved) statApproved.textContent = '-';
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
            <div class="p-4 hover:bg-gray-50 transition-colors" data-id="${item.id}">
              <div class="flex items-start justify-between">
                <div class="flex-1 min-w-0">
                  <div class="flex items-center gap-2">
                    <h3 class="font-medium text-gray-800 truncate">${item.title || '无标题'}</h3>
                    ${this.renderBadge(item)}
                  </div>
                  ${item.description ? `<p class="text-sm text-gray-500 mt-1 line-clamp-2">${item.description}</p>` : ''}
                  <div class="flex items-center gap-4 mt-2 text-xs text-gray-400">
                    <span>类型: ${item.proposal_type || '-'}</span>
                    <span>目标: ${item.target_entity_type || '-'}</span>
                    ${item.ai_score != null ? `<span>AI评分: ${item.ai_score}</span>` : '<span class="text-gray-400">AI评分: 未评分</span>'}
                    <span>${item.created_at ? new Date(item.created_at).toLocaleString() : '-'}</span>
                  </div>
                </div>
                <div class="flex items-center gap-2 ml-4">
                  <button onclick="SystemEvolutionPage.viewDetail('${item.id}')"
                          class="p-2 text-gray-400 hover:text-primary-600 hover:bg-primary-50 rounded transition-colors" title="查看">
                    <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M15 12a3 3 0 11-6 0 3 3 0 016 0z"/>
                      <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M2.458 12C3.732 7.943 7.523 5 12 5c4.478 0 8.268 2.943 9.542 7-1.274 4.057-5.064 7-9.542 7-4.477 0-8.268-2.943-9.542-7z"/>
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
      SystemEvolutionPage.currentFilters.search = value;
      SystemEvolutionPage.loadData();
    }, 300),

    handleFilter(key, value) {
      this.currentFilters[key] = value;
      this.loadData();
    },

    showCreateModal() {
      document.getElementById(`${PAGE_ID}-modal-title`).textContent = '新建提案';
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

    async viewDetail(id) {
      try {
        const workspace = window.AppState?.currentWorkspace;
        const result = await window.ApiClient.callTool('system.evolution.get', { 
          workspace, 
          proposal_id: id 
        });
        
        if (result) {
          ModalDialog.alert(`
            <div class="text-left">
              <h3 class="font-bold text-lg mb-2">${result.title || '无标题'}</h3>
              <p class="text-gray-600 mb-4">${result.description || ''}</p>
              <div class="text-sm text-gray-500 space-y-1">
                <p><span class="font-medium">状态:</span> ${result.status || '-'}</p>
                <p><span class="font-medium">类型:</span> ${result.proposal_type || '-'}</p>
                <p><span class="font-medium">目标:</span> ${result.target_entity_type || '-'}</p>
                ${result.ai_score != null ? `<p><span class="font-medium">AI评分:</span> ${result.ai_score}</p>` : '<p><span class="font-medium">AI评分:</span> <span class="text-gray-400">未评分</span></p>'}
                ${result.ai_review_comment ? `<p><span class="font-medium">AI评语:</span> ${result.ai_review_comment}</p>` : ''}
              </div>
            </div>
          `, 'info');
        }
      } catch (error) {
        ModalDialog.alert('加载失败: ' + error.message, 'error');
      }
    },

    async handleSave(e) {
      e.preventDefault();
      const workspace = window.AppState?.currentWorkspace;
      if (!workspace) {
        ModalDialog.alert('请先选择工作区', 'error');
        return;
      }

      const data = {};
      PAGE_CONFIG.formFields.forEach(field => {
        const el = document.getElementById(`${PAGE_ID}-${field.key}`);
        if (el) {
          if (field.key === 'proposed_content' && el.value) {
            try {
              data[field.key] = JSON.parse(el.value);
            } catch {
              data[field.key] = { content: el.value };
            }
          } else {
            data[field.key] = el.value || undefined;
          }
        }
      });

      try {
        await window.ApiClient.callTool('system.evolution.propose', { 
          workspace, 
          project: window.AppState?.currentProject,
          ...data 
        });
        this.hideModal();
        this.loadData();
        ModalDialog.alert('提案提交成功', 'success');
      } catch (error) {
        ModalDialog.alert('提交失败: ' + error.message, 'error');
      }
    },

    renderBadge(item) {
      const status = item.status || 'draft';
      const type = item.proposal_type || '';
      
      const statusClasses = {
        draft: 'bg-gray-100 text-gray-600',
        ai_reviewing: 'bg-blue-100 text-blue-700',
        ai_reviewed: 'bg-purple-100 text-purple-700',
        pending_admin: 'bg-yellow-100 text-yellow-700',
        admin_approved: 'bg-green-100 text-green-700',
        admin_rejected: 'bg-red-100 text-red-700',
        applied: 'bg-green-200 text-green-800'
      };
      
      const typeClasses = {
        create: 'bg-blue-100 text-blue-700',
        update: 'bg-yellow-100 text-yellow-700',
        delete: 'bg-red-100 text-red-700',
        merge: 'bg-purple-100 text-purple-700'
      };
      
      let badges = '';
      if (status) {
        badges += `<span class="px-2 py-0.5 text-xs rounded-full ${statusClasses[status] || 'bg-gray-100 text-gray-500'}">${status}</span>`;
      }
      if (type) {
        badges += ` <span class="px-2 py-0.5 text-xs rounded-full ${typeClasses[type] || 'bg-gray-100 text-gray-500'}">${type}</span>`;
      }
      
      return badges;
    }
  };

  function debounce(fn, delay) {
    let timer;
    return function(...args) {
      clearTimeout(timer);
      timer = setTimeout(() => fn.apply(this, args), delay);
    };
  }

  console.log('[SystemEvolutionPage] Script loaded, window.SystemEvolutionPage:', !!window.SystemEvolutionPage);
})();
