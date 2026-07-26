/**
 * Novel OS - Rules List Page
 * 创作规则管理页面
 * @version 2.0.0
 */
(function() {
  'use strict';

  if (window.RulesListPage) {
    return;
  }

  window.RulesListPage = {
    rules: [],
    currentFilters: {},

    init() {
      console.log('[RulesListPage] Initializing...');
      this.render();
      this.loadData();
      return true;
    },

    render() {
      const contentArea = document.getElementById('content-area');
      if (!contentArea) return;

      contentArea.innerHTML = `
        <div class="space-y-4">
          <!-- 页面标题 -->
          <div class="flex items-center justify-between">
            <div>
              <h1 class="text-2xl font-bold text-gray-800">创作规则</h1>
              <p class="text-gray-500 mt-1">管理创作约束和规则</p>
            </div>
            <button onclick="RulesListPage.showCreateModal()" 
                    class="px-4 py-2 bg-primary-600 text-white rounded-lg hover:bg-primary-700 transition-colors flex items-center gap-2">
              <span>➕</span> 新建规则
            </button>
          </div>

          <!-- 搜索和筛选 -->
          <div class="flex gap-4 items-center">
            <div class="flex-1 relative">
              <input type="text" 
                     id="rule-search" 
                     placeholder="搜索规则标题或内容..." 
                     oninput="RulesListPage.handleSearch(this.value)"
                     class="w-full px-4 py-2 pl-10 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary-500 focus:border-transparent">
              <span class="absolute left-3 top-2.5 text-gray-400">🔍</span>
            </div>
            <select id="rule-type-filter" onchange="RulesListPage.handleFilter()" 
                    class="px-4 py-2 border border-gray-300 rounded-lg">
              <option value="">全部类型</option>
              <option value="character">角色规则</option>
              <option value="plot">剧情规则</option>
              <option value="world">世界规则</option>
              <option value="style">风格规则</option>
              <option value="compliance">合规规则</option>
            </select>
            <select id="rule-status-filter" onchange="RulesListPage.handleFilter()" 
                    class="px-4 py-2 border border-gray-300 rounded-lg">
              <option value="">全部状态</option>
              <option value="active">生效</option>
              <option value="draft">草稿</option>
              <option value="disabled">禁用</option>
            </select>
          </div>

          <!-- 规则列表 -->
          <div id="rules-list-container" class="bg-white rounded-lg shadow">
            <div class="p-8 text-center text-gray-500">
              <div class="spinner w-8 h-8 border-4 border-primary-600 border-t-transparent rounded-full animate-spin mx-auto"></div>
              <p class="mt-2">加载中...</p>
            </div>
          </div>
        </div>

        <!-- 创建/编辑模态框 -->
        <div id="rule-modal" class="fixed inset-0 bg-black/50 z-50 hidden flex items-center justify-center">
          <div class="bg-white rounded-lg shadow-xl w-full max-w-2xl mx-4 max-h-[90vh] overflow-hidden flex flex-col">
            <div class="px-6 py-4 border-b border-gray-200 flex items-center justify-between">
              <h3 id="rule-modal-title" class="text-lg font-semibold">新建规则</h3>
              <button onclick="RulesListPage.hideModal()" class="text-gray-400 hover:text-gray-600">
                <svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12"/>
                </svg>
              </button>
            </div>
            <div class="p-6 overflow-y-auto">
              <form id="rule-form" onsubmit="RulesListPage.saveRule(event)">
                <input type="hidden" id="rule-id">
                <div class="space-y-4">
                  <div>
                    <label class="block text-sm font-medium text-gray-700 mb-1">规则标题 <span class="text-red-500">*</span></label>
                    <input type="text" id="rule-title" required
                           class="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary-500 focus:border-transparent">
                  </div>
                  <div class="grid grid-cols-2 gap-4">
                    <div>
                      <label class="block text-sm font-medium text-gray-700 mb-1">类型 <span class="text-red-500">*</span></label>
                      <select id="rule-type" required
                              class="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary-500 focus:border-transparent">
                        <option value="character">角色规则</option>
                        <option value="plot">剧情规则</option>
                        <option value="world">世界规则</option>
                        <option value="style">风格规则</option>
                        <option value="compliance">合规规则</option>
                      </select>
                    </div>
                    <div>
                      <label class="block text-sm font-medium text-gray-700 mb-1">严重程度</label>
                      <select id="rule-severity" 
                              class="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary-500 focus:border-transparent">
                        <option value="info">提示</option>
                        <option value="warning" selected>警告</option>
                        <option value="error">错误</option>
                        <option value="critical">严重</option>
                      </select>
                    </div>
                  </div>
                  <div class="grid grid-cols-2 gap-4">
                    <div>
                      <label class="block text-sm font-medium text-gray-700 mb-1">作用域</label>
                      <select id="rule-scope" 
                              class="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary-500 focus:border-transparent">
                        <option value="global">全局</option>
                        <option value="volume">卷级</option>
                        <option value="chapter">章级</option>
                      </select>
                    </div>
                    <div>
                      <label class="block text-sm font-medium text-gray-700 mb-1">优先级</label>
                      <input type="number" id="rule-priority" value="100" min="0" max="1000"
                             class="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary-500 focus:border-transparent">
                    </div>
                  </div>
                  <div>
                    <label class="block text-sm font-medium text-gray-700 mb-1">规则键名 <span class="text-red-500">*</span></label>
                    <input type="text" id="rule-key" required placeholder="如: no_time_travel"
                           class="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary-500 focus:border-transparent font-mono text-sm">
                  </div>
                  <div>
                    <label class="block text-sm font-medium text-gray-700 mb-1">规则内容 <span class="text-red-500">*</span></label>
                    <textarea id="rule-content" required rows="4"
                              class="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary-500 focus:border-transparent resize-y"></textarea>
                  </div>
                  <div>
                    <label class="block text-sm font-medium text-gray-700 mb-1">状态</label>
                    <select id="rule-status" 
                            class="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary-500 focus:border-transparent">
                      <option value="active">生效</option>
                      <option value="draft">草稿</option>
                      <option value="disabled">禁用</option>
                    </select>
                  </div>
                </div>
                <div class="mt-6 flex justify-end gap-3">
                  <button type="button" onclick="RulesListPage.hideModal()" 
                          class="px-4 py-2 border border-gray-300 rounded-lg hover:bg-gray-50 transition-colors">
                    取消
                  </button>
                  <button type="submit" id="rule-save-btn"
                          class="px-4 py-2 bg-primary-600 text-white rounded-lg hover:bg-primary-700 transition-colors">
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
      const container = document.getElementById('rules-list-container');
      const workspace = window.AppState?.currentWorkspace;
      const project = window.AppState?.currentProject;
      
      if (!workspace || !project) {
        container.innerHTML = `
          <div class="p-8 text-center text-gray-500">
            <div class="text-4xl mb-4">📋</div>
            <p>请先选择工作区和项目</p>
          </div>
        `;
        return;
      }

      try {
        const result = await window.ApiClient.callTool('rules.list', { workspace, project, status: null });
        this.rules = Array.isArray(result) ? result : (result?.rules || result?.items || []);
        this.renderList(this.rules);
      } catch (error) {
        console.error('[RulesListPage] Load error:', error);
        container.innerHTML = `
          <div class="p-8 text-center text-red-500">
            <p>加载失败: ${error.message}</p>
            <button onclick="RulesListPage.loadData()" class="mt-4 px-4 py-2 bg-gray-100 rounded hover:bg-gray-200">
              重试
            </button>
          </div>
        `;
        if (window.showToast) window.showToast('error', '加载规则列表失败');
      }
    },

    renderList(rules) {
      const container = document.getElementById('rules-list-container');
      
      // 应用筛选
      const searchTerm = (document.getElementById('rule-search')?.value || '').toLowerCase();
      const typeFilter = document.getElementById('rule-type-filter')?.value;
      const statusFilter = document.getElementById('rule-status-filter')?.value;
      
      if (searchTerm) {
        rules = rules.filter(r => 
          (r.title || '').toLowerCase().includes(searchTerm) ||
          (r.content || '').toLowerCase().includes(searchTerm) ||
          (r.rule_key || '').toLowerCase().includes(searchTerm)
        );
      }
      
      if (typeFilter) {
        rules = rules.filter(r => r.rule_type === typeFilter);
      }
      
      if (statusFilter) {
        rules = rules.filter(r => r.status === statusFilter);
      }

      if (!rules || rules.length === 0) {
        container.innerHTML = `
          <div class="p-8 text-center text-gray-500">
            <div class="text-4xl mb-4">📋</div>
            <p>暂无创作规则</p>
            <p class="text-sm mt-2">点击右上角按钮创建第一个规则</p>
          </div>
        `;
        return;
      }

      // Group by scope: system > user > project
      const groups = { system: [], user: [], project: [], global: [] };
      rules.forEach(r => {
        const s = (r.scope || 'global').toLowerCase();
        if (groups[s]) groups[s].push(r);
        else groups.global.push(r);
      });
      const scopeLabels = { system: '🔒 系统规则（只读）', user: '👤 用户规则', project: '📁 项目规则', global: '🌐 全局规则' };

      container.innerHTML = ['system', 'user', 'project', 'global'].map(scope => {
        const items = groups[scope];
        if (!items || items.length === 0) return '';
        const isReadonly = scope === 'system';
        return `
          <div class="border-b border-gray-200 last:border-b-0">
            <div class="px-4 py-2 bg-gray-50 text-xs font-semibold text-gray-500 uppercase tracking-wider">${scopeLabels[scope] || scope} (${items.length})</div>
            ${items.map(rule => `
              <div class="p-4 hover:bg-gray-50 transition-colors border-t border-gray-100">
                <div class="flex items-start justify-between">
                  <div class="flex-1 min-w-0">
                    <div class="flex items-center gap-2 flex-wrap">
                      <span class="px-2 py-0.5 text-xs rounded-full ${this.getSeverityClass(rule.severity)}">
                        ${rule.severity || 'warning'}
                      </span>
                      <h3 class="font-medium text-gray-800">${rule.title}</h3>
                      <span class="text-xs text-gray-400 font-mono">${rule.rule_key}</span>
                      ${isReadonly ? '<span class="text-xs text-gray-400 border border-gray-300 rounded px-1">只读</span>' : ''}
                    </div>
                    <p class="text-sm text-gray-500 mt-1 line-clamp-2">${rule.content}</p>
                    <div class="flex items-center gap-4 mt-2 text-xs text-gray-400">
                      <span>类型: ${rule.rule_type}</span>
                      <span>作用域: ${rule.scope || 'global'}</span>
                      <span>优先级: ${rule.priority || 100}</span>
                      <span class="${rule.status === 'active' ? 'text-green-600' : 'text-gray-500'}">状态: ${rule.status}</span>
                    </div>
                  </div>
                  <div class="flex items-center gap-2 ml-4">
                    ${isReadonly ? '' : `
                    <button onclick="RulesListPage.toggleRuleStatus('${rule.id}', '${rule.status}')" 
                            class="p-2 ${rule.status === 'active' ? 'text-green-600 hover:bg-green-50' : 'text-gray-400 hover:bg-gray-100'} rounded transition-colors"
                            title="${rule.status === 'active' ? '禁用' : '启用'}">
                      <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="${rule.status === 'active' ? 'M18.364 18.364A9 9 0 005.636 5.636m12.728 12.728A9 9 0 015.636 5.636m12.728 12.728L5.636 5.636' : 'M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z'}"/>
                      </svg>
                    </button>
                    <button onclick="RulesListPage.editRule('${rule.id}')" 
                            class="p-2 text-gray-400 hover:text-primary-600 hover:bg-primary-50 rounded transition-colors"
                            title="编辑">
                      <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M11 5H6a2 2 0 00-2 2v11a2 2 0 002 2h11a2 2 0 002-2v-5m-1.414-9.414a2 2 0 112.828 2.828L11.828 15H9v-2.828l8.586-8.586z"/>
                      </svg>
                    </button>
                    <button onclick="RulesListPage.deleteRule('${rule.id}', '${rule.title}')" 
                            class="p-2 text-gray-400 hover:text-red-600 hover:bg-red-50 rounded transition-colors"
                            title="删除">
                      <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16"/>
                      </svg>
                    </button>
                    `}
                  </div>
                </div>
              </div>
            `).join('')}
          </div>
        `;
      }).join('');
    },

    handleSearch(value) {
      this.renderList(this.rules);
    },

    handleFilter() {
      this.renderList(this.rules);
    },

    showCreateModal() {
      document.getElementById('rule-modal-title').textContent = '新建规则';
      document.getElementById('rule-id').value = '';
      document.getElementById('rule-title').value = '';
      document.getElementById('rule-type').value = 'character';
      document.getElementById('rule-severity').value = 'warning';
      document.getElementById('rule-scope').value = 'global';
      document.getElementById('rule-priority').value = '100';
      document.getElementById('rule-key').value = '';
      document.getElementById('rule-content').value = '';
      document.getElementById('rule-status').value = 'active';
      document.getElementById('rule-modal').classList.remove('hidden');
    },

    hideModal() {
      document.getElementById('rule-modal').classList.add('hidden');
    },

    async editRule(id) {
      try {
        const rule = this.rules.find(r => r.id === id || r.rule_key === id);
        if (!rule) {
          if (window.showToast) window.showToast('error', '规则不存在');
          return;
        }
        
        document.getElementById('rule-modal-title').textContent = '编辑规则';
        document.getElementById('rule-id').value = rule.id;
        document.getElementById('rule-title').value = rule.title;
        document.getElementById('rule-type').value = rule.rule_type;
        document.getElementById('rule-severity').value = rule.severity || 'warning';
        document.getElementById('rule-scope').value = rule.scope || 'global';
        document.getElementById('rule-priority').value = rule.priority || 100;
        document.getElementById('rule-key').value = rule.rule_key;
        document.getElementById('rule-content').value = rule.content;
        document.getElementById('rule-status').value = rule.status;
        document.getElementById('rule-modal').classList.remove('hidden');
      } catch (error) {
        console.error('[RulesListPage] Edit error:', error);
        if (window.showToast) window.showToast('error', '加载规则失败: ' + error.message);
      }
    },

    async saveRule(e) {
      e.preventDefault();
      const workspace = window.AppState?.currentWorkspace;
      const project = window.AppState?.currentProject;
      const id = document.getElementById('rule-id').value;
      
      const data = {
        title: document.getElementById('rule-title').value.trim(),
        rule_type: document.getElementById('rule-type').value,
        severity: document.getElementById('rule-severity').value,
        scope: document.getElementById('rule-scope').value,
        priority: parseInt(document.getElementById('rule-priority').value) || 100,
        rule_key: document.getElementById('rule-key').value.trim(),
        content: document.getElementById('rule-content').value.trim(),
        status: document.getElementById('rule-status').value
      };

      // 验证
      if (!data.title || !data.rule_key || !data.content) {
        if (window.showToast) window.showToast('warning', '请填写必填项');
        return;
      }

      try {
        await window.ApiClient.callTool('rules.upsert', { workspace, project, ...data });
        if (window.showToast) window.showToast('success', id ? '规则已更新' : '规则创建成功');
        this.hideModal();
        this.loadData();
      } catch (error) {
        console.error('[RulesListPage] Save error:', error);
        if (window.showToast) window.showToast('error', '保存失败: ' + error.message);
      }
    },

    async deleteRule(id, title) {
      if (!confirm(`确定删除规则 "${title}" 吗？此操作不可恢复。`)) return;

      const workspace = window.AppState?.currentWorkspace;
      const project = window.AppState?.currentProject;
      
      try {
        await window.ApiClient.callTool('rules.delete', { 
          workspace, 
          project, 
          rule_id: id
        });
        if (window.showToast) window.showToast('success', '规则已删除');
        this.loadData();
      } catch (error) {
        console.error('[RulesListPage] Delete error:', error);
        if (window.showToast) window.showToast('error', '删除失败: ' + error.message);
      }
    },

    async toggleRuleStatus(id, currentStatus) {
      const newStatus = currentStatus === 'active' ? 'disabled' : 'active';
      const workspace = window.AppState?.currentWorkspace;
      const project = window.AppState?.currentProject;
      
      try {
        await window.ApiClient.callTool('rules.bulk_toggle', { 
          workspace, 
          project, 
          rule_ids: [id],
          status: newStatus,
          reason: currentStatus === 'active' ? '用户手动禁用' : '用户手动启用'
        });
        if (window.showToast) window.showToast('success', newStatus === 'active' ? '规则已启用' : '规则已禁用');
        this.loadData();
      } catch (error) {
        console.error('[RulesListPage] Toggle status error:', error);
        if (window.showToast) window.showToast('error', '更新状态失败: ' + error.message);
      }
    },

    getSeverityClass(severity) {
      const classes = {
        info: 'bg-blue-100 text-blue-700',
        warning: 'bg-yellow-100 text-yellow-700',
        error: 'bg-orange-100 text-orange-700',
        critical: 'bg-red-100 text-red-700'
      };
      return classes[severity] || 'bg-yellow-100 text-yellow-700';
    }
  };
})();
