/**
 * Novel OS - Project World Rules Page
 * 项目世界规则管理页面（直接使用 canon_rules）
 */
(function() {
  'use strict';

  window.ProjectWorldRulesPage = {
    init() {
      this.render();
      this.loadData();
      return true;
    },

    render() {
      const contentArea = document.getElementById('content-area');
      contentArea.innerHTML = `
        <div class="max-w-5xl mx-auto space-y-4">
          <div class="flex items-center justify-between">
            <div>
              <h1 class="text-2xl font-bold text-gray-800">${t('nav.worldRules')}</h1>
              <p class="text-gray-500 mt-1">管理项目的世界规则设定（自动参与上下文）</p>
            </div>
            <button onclick="ProjectWorldRulesPage.showCreateModal()" 
                    class="px-4 py-2 bg-primary-600 text-white rounded-lg hover:bg-primary-700 transition-colors">
              ${t('common.new')} 规则
            </button>
          </div>

          <div id="world-rules-container" class="bg-white rounded-lg shadow">
            <div class="p-8 text-center text-gray-500">
              <div class="spinner w-8 h-8 border-4 border-primary-600 border-t-transparent rounded-full animate-spin mx-auto"></div>
              <p class="mt-2">${t('common.loading')}</p>
            </div>
          </div>
        </div>

        <!-- 模态框 -->
        <div id="world-rule-modal" class="fixed inset-0 bg-black/50 z-50 hidden flex items-center justify-center">
          <div class="bg-white rounded-lg shadow-xl w-full max-w-2xl mx-4 max-h-[90vh] overflow-hidden">
            <div class="px-6 py-4 border-b border-gray-200 flex items-center justify-between">
              <h3 id="world-rule-modal-title" class="text-lg font-semibold">新建世界规则</h3>
              <button onclick="ProjectWorldRulesPage.hideModal()" class="text-gray-400 hover:text-gray-600">
                <svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12"/>
                </svg>
              </button>
            </div>
            <div class="p-6 overflow-y-auto max-h-[60vh]">
              <form onsubmit="ProjectWorldRulesPage.saveRule(event)">
                <input type="hidden" id="world-rule-key">
                <div class="space-y-4">
                  <div>
                    <label class="block text-sm font-medium text-gray-700 mb-1">规则名称 <span class="text-red-500">*</span></label>
                    <input type="text" id="world-rule-name" required
                           class="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary-500">
                  </div>
                  <div>
                    <label class="block text-sm font-medium text-gray-700 mb-1">规则内容 <span class="text-red-500">*</span></label>
                    <textarea id="world-rule-content" required rows="6"
                              class="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary-500"></textarea>
                  </div>
                  <div class="grid grid-cols-2 gap-4">
                    <div>
                      <label class="block text-sm font-medium text-gray-700 mb-1">严重程度</label>
                      <select id="world-rule-severity"
                              class="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary-500">
                        <option value="info">信息</option>
                        <option value="warning" selected>警告</option>
                        <option value="critical">严重</option>
                      </select>
                    </div>
                    <div>
                      <label class="block text-sm font-medium text-gray-700 mb-1">类型</label>
                      <select id="world-rule-type"
                              class="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary-500">
                        <option value="canon" selected>正典</option>
                        <option value="character">角色</option>
                        <option value="plot">情节</option>
                        <option value="style">风格</option>
                        <option value="forbidden">禁止</option>
                      </select>
                    </div>
                  </div>
                </div>
                <div class="mt-6 flex justify-end gap-3">
                  <button type="button" onclick="ProjectWorldRulesPage.hideModal()" 
                          class="px-4 py-2 border border-gray-300 rounded-lg hover:bg-gray-50">
                    ${t('common.cancel')}
                  </button>
                  <button type="submit" class="px-4 py-2 bg-primary-600 text-white rounded-lg hover:bg-primary-700">
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
      const container = document.getElementById('world-rules-container');
      try {
        const workspace = window.AppState.currentWorkspace;
        const project = window.AppState.currentProject;
        
        if (!workspace || !project) {
          container.innerHTML = `<div class="p-8 text-center text-gray-500">请先选择工作区和项目</div>`;
          return;
        }

        const result = await window.ApiClient.callTool('rules.list', { workspace, project, rule_types: ['canon'], status: null });
        const rules = Array.isArray(result) ? result : (result?.rules || []);
        this.renderList(rules);
      } catch (error) {
        console.error('[WorldRules] Load error:', error);
        container.innerHTML = `<div class="p-8 text-center text-red-500">加载失败: ${error.message}</div>`;
      }
    },

    renderList(rules) {
      const container = document.getElementById('world-rules-container');
      
      if (!rules || rules.length === 0) {
        container.innerHTML = `
          <div class="p-8 text-center text-gray-500">
            <div class="text-4xl mb-2">🌍</div>
            <p>暂无世界规则</p>
            <p class="text-sm mt-2">点击右上角按钮添加规则（自动参与章节上下文）</p>
          </div>
        `;
        return;
      }

      container.innerHTML = `
        <div class="divide-y divide-gray-200">
          ${rules.map(rule => `
            <div class="p-4 hover:bg-gray-50 transition-colors">
              <div class="flex items-start justify-between">
                <div class="flex-1 min-w-0">
                  <div class="flex items-center gap-2">
                    <h3 class="font-medium text-gray-800">${rule.title || rule.rule_key || '未命名'}</h3>
                    <span class="px-2 py-0.5 text-xs rounded-full ${this.getSeverityClass(rule.severity)}">${rule.severity || 'warning'}</span>
                    ${rule.status === 'active' ? '' : `<span class="px-2 py-0.5 text-xs rounded-full bg-gray-100 text-gray-600">${rule.status}</span>`}
                  </div>
                  <p class="text-sm text-gray-500 mt-1 line-clamp-3">${rule.content || '暂无内容'}</p>
                </div>
                <div class="flex items-center gap-2 ml-4">
                  <button onclick="ProjectWorldRulesPage.editRule('${rule.rule_key}')" 
                          class="p-2 text-gray-400 hover:text-primary-600 hover:bg-primary-50 rounded transition-colors" title="编辑">
                    <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M11 5H6a2 2 0 00-2 2v11a2 2 0 002 2h11a2 2 0 002-2v-5m-1.414-9.414a2 2 0 112.828 2.828L11.828 15H9v-2.828l8.586-8.586z"/>
                    </svg>
                  </button>
                  <button onclick="ProjectWorldRulesPage.deleteRule('${rule.rule_key}')" 
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

    getSeverityClass(severity) {
      const classes = { info: 'bg-blue-100 text-blue-600', warning: 'bg-yellow-100 text-yellow-700', critical: 'bg-red-100 text-red-700' };
      return classes[severity] || 'bg-gray-100 text-gray-600';
    },

    showCreateModal() {
      document.getElementById('world-rule-modal-title').textContent = '新建世界规则';
      document.getElementById('world-rule-key').value = '';
      document.getElementById('world-rule-name').value = '';
      document.getElementById('world-rule-content').value = '';
      document.getElementById('world-rule-severity').value = 'warning';
      document.getElementById('world-rule-type').value = 'canon';
      document.getElementById('world-rule-modal').classList.remove('hidden');
    },

    hideModal() {
      document.getElementById('world-rule-modal').classList.add('hidden');
    },

    async editRule(key) {
      try {
        const workspace = window.AppState.currentWorkspace;
        const project = window.AppState.currentProject;
        const result = await window.ApiClient.callTool('rules.list', { workspace, project, rule_types: ['canon'], status: null });
        const rules = Array.isArray(result) ? result : (result?.rules || []);
        const rule = rules.find(r => r.rule_key === key);
        if (!rule) { alert('规则未找到'); return; }
        
        document.getElementById('world-rule-modal-title').textContent = '编辑世界规则';
        document.getElementById('world-rule-key').value = rule.rule_key;
        document.getElementById('world-rule-name').value = rule.title || rule.rule_key;
        document.getElementById('world-rule-content').value = rule.content || '';
        document.getElementById('world-rule-severity').value = rule.severity || 'warning';
        document.getElementById('world-rule-type').value = rule.rule_type || 'canon';
        document.getElementById('world-rule-modal').classList.remove('hidden');
      } catch (error) {
        alert('加载规则失败: ' + error.message);
      }
    },

    async saveRule(e) {
      e.preventDefault();
      const workspace = window.AppState.currentWorkspace;
      const project = window.AppState.currentProject;
      const key = document.getElementById('world-rule-key').value;
      const name = document.getElementById('world-rule-name').value;

      try {
        await window.ApiClient.callTool('rules.upsert', {
          workspace, project,
          rule_key: key || `world_${name.replace(/\s+/g, '_')}`,
          rule_type: document.getElementById('world-rule-type').value,
          title: name,
          content: document.getElementById('world-rule-content').value,
          severity: document.getElementById('world-rule-severity').value,
        });
        this.hideModal();
        this.loadData();
      } catch (error) {
        alert('保存失败: ' + error.message);
      }
    },

    async deleteRule(key) {
      if (!confirm(`确定删除规则 "${key}" 吗？`)) return;
      
      try {
        await window.ApiClient.callTool('rules.delete', { workspace: window.AppState.currentWorkspace, project: window.AppState.currentProject, rule_key: key });
        this.loadData();
      } catch (error) {
        alert('删除失败: ' + error.message);
      }
    }
  };
})();
