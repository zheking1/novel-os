/**
 * Novel OS - Project Factions Page
 * 项目势力管理页面
 */
(function() {
  'use strict';

  window.ProjectFactionsPage = {
    init() {
      this.render();
      this.loadData();
    },

    render() {
      const contentArea = document.getElementById('content-area');
      contentArea.innerHTML = `
        <div class="space-y-4">
          <div class="flex items-center justify-between">
            <div>
              <h1 class="text-2xl font-bold text-gray-800">${t('nav.factions')}</h1>
              <p class="text-gray-500 mt-1">管理项目中的势力组织</p>
            </div>
            <button onclick="ProjectFactionsPage.showCreateModal()" 
                    class="px-4 py-2 bg-primary-600 text-white rounded-lg hover:bg-primary-700 transition-colors">
              ${t('common.new')} 势力
            </button>
          </div>

          <div id="factions-container" class="bg-white rounded-lg shadow">
            <div class="p-8 text-center text-gray-500">
              <div class="spinner w-8 h-8 border-4 border-primary-600 border-t-transparent rounded-full animate-spin mx-auto"></div>
              <p class="mt-2">${t('common.loading')}</p>
            </div>
          </div>
        </div>

        <!-- 模态框 -->
        <div id="faction-modal" class="fixed inset-0 bg-black/50 z-50 hidden flex items-center justify-center">
          <div class="bg-white rounded-lg shadow-xl w-full max-w-2xl mx-4 max-h-[90vh] overflow-hidden">
            <div class="px-6 py-4 border-b border-gray-200 flex items-center justify-between">
              <h3 id="faction-modal-title" class="text-lg font-semibold">新建势力</h3>
              <button onclick="ProjectFactionsPage.hideModal()" class="text-gray-400 hover:text-gray-600">
                <svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12"/>
                </svg>
              </button>
            </div>
            <div class="p-6 overflow-y-auto max-h-[60vh]">
              <form onsubmit="ProjectFactionsPage.saveFaction(event)">
                <input type="hidden" id="faction-id">
                <div class="space-y-4">
                  <div>
                    <label class="block text-sm font-medium text-gray-700 mb-1">势力名称 <span class="text-red-500">*</span></label>
                    <input type="text" id="faction-name" required
                           class="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary-500">
                  </div>
                  <div>
                    <label class="block text-sm font-medium text-gray-700 mb-1">描述</label>
                    <textarea id="faction-summary" rows="3"
                              class="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary-500"></textarea>
                  </div>
                  <div>
                    <label class="block text-sm font-medium text-gray-700 mb-1">详细资料 (JSON)</label>
                    <textarea id="faction-profile" rows="6" placeholder='{"leader": "", "territory": "", "power": ""}'
                              class="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary-500 font-mono text-sm"></textarea>
                  </div>
                </div>
                <div class="mt-6 flex justify-end gap-3">
                  <button type="button" onclick="ProjectFactionsPage.hideModal()" 
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
      const container = document.getElementById('factions-container');
      try {
        const workspace = window.AppState.currentWorkspace;
        const project = window.AppState.currentProject;
        
        if (!workspace || !project) {
          container.innerHTML = `<div class="p-8 text-center text-gray-500">请先选择工作区和项目</div>`;
          return;
        }

        const result = await window.ApiClient.kb.pk.list(project, 'faction');
        this.renderList(result || []);
      } catch (error) {
        console.error('[Factions] Load error:', error);
        container.innerHTML = `<div class="p-8 text-center text-red-500">加载失败: ${error.message}</div>`;
      }
    },

    renderList(factions) {
      const container = document.getElementById('factions-container');
      
      if (!factions || factions.length === 0) {
        container.innerHTML = `
          <div class="p-8 text-center text-gray-500">
            <div class="text-4xl mb-2">🏴</div>
            <p>暂无势力</p>
            <p class="text-sm mt-2">点击右上角按钮添加势力</p>
          </div>
        `;
        return;
      }

      container.innerHTML = `
        <div class="divide-y divide-gray-200">
          ${factions.map(faction => `
            <div class="p-4 hover:bg-gray-50 transition-colors">
              <div class="flex items-start justify-between">
                <div class="flex-1 min-w-0">
                  <div class="flex items-center gap-2">
                    <span class="text-lg">🏴</span>
                    <h3 class="font-medium text-gray-800">${faction.key || faction.title || '未命名'}</h3>
                  </div>
                  <p class="text-sm text-gray-500 mt-1 line-clamp-2">${faction.value?.summary || faction.description || '暂无描述'}</p>
                </div>
                <div class="flex items-center gap-2 ml-4">
                  <button onclick="ProjectFactionsPage.editFaction('${faction.id}', '${faction.key}')" 
                          class="p-2 text-gray-400 hover:text-primary-600 hover:bg-primary-50 rounded transition-colors">
                    <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M11 5H6a2 2 0 00-2 2v11a2 2 0 002 2h11a2 2 0 002-2v-5m-1.414-9.414a2 2 0 112.828 2.828L11.828 15H9v-2.828l8.586-8.586z"/>
                    </svg>
                  </button>
                  <button onclick="ProjectFactionsPage.deleteFaction('${faction.id}', '${faction.key}')" 
                          class="p-2 text-gray-400 hover:text-red-600 hover:bg-red-50 rounded transition-colors">
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

    showCreateModal() {
      document.getElementById('faction-modal-title').textContent = '新建势力';
      document.getElementById('faction-id').value = '';
      document.getElementById('faction-name').value = '';
      document.getElementById('faction-summary').value = '';
      document.getElementById('faction-profile').value = '';
      document.getElementById('faction-modal').classList.remove('hidden');
    },

    hideModal() {
      document.getElementById('faction-modal').classList.add('hidden');
    },

    async editFaction(id, key) {
      try {
        const project = window.AppState.currentProject;
        const faction = await window.ApiClient.kb.pk.get(project, 'faction', key);
        
        document.getElementById('faction-modal-title').textContent = '编辑势力';
        document.getElementById('faction-id').value = id;
        document.getElementById('faction-name').value = key;
        document.getElementById('faction-summary').value = faction?.value?.summary || '';
        document.getElementById('faction-profile').value = faction?.value?.profile ? JSON.stringify(faction.value.profile, null, 2) : '';
        document.getElementById('faction-modal').classList.remove('hidden');
      } catch (error) {
        alert('加载势力失败: ' + error.message);
      }
    },

    async saveFaction(e) {
      e.preventDefault();
      const project = window.AppState.currentProject;
      
      const key = document.getElementById('faction-name').value;
      
      let profile = null;
      const profileStr = document.getElementById('faction-profile').value;
      if (profileStr) {
        try { profile = JSON.parse(profileStr); } catch (e) { alert('JSON格式错误'); return; }
      }

      const value = {
        summary: document.getElementById('faction-summary').value,
        profile
      };

      try {
        await window.ApiClient.kb.pk.upsert(project, 'faction', key, value);
        this.hideModal();
        this.loadData();
      } catch (error) {
        alert('保存失败: ' + error.message);
      }
    },

    async deleteFaction(id, key) {
      if (!confirm(`确定删除势力 "${key}" 吗？`)) return;
      
      try {
        await window.ApiClient.kb.pk.delete(window.AppState.currentProject, 'faction', key);
        this.loadData();
      } catch (error) {
        alert('删除失败: ' + error.message);
      }
    }
  };
})();
