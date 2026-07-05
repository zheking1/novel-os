/**
 * Novel OS - Project Characters Page
 * 项目角色管理页面
 */
(function() {
  'use strict';

  window.ProjectCharactersPage = {
    init() {
      this.render();
      this.loadData();
      return true;
    },

    render() {
      const contentArea = document.getElementById('content-area');
      contentArea.innerHTML = `
        <div class="space-y-4">
          <div class="flex items-center justify-between">
            <div>
              <h1 class="text-2xl font-bold text-gray-800">${t('nav.characters')}</h1>
              <p class="text-gray-500 mt-1">管理项目中的角色</p>
            </div>
            <button onclick="ProjectCharactersPage.showCreateModal()" 
                    class="px-4 py-2 bg-primary-600 text-white rounded-lg hover:bg-primary-700 transition-colors">
              ${t('common.new')} 角色
            </button>
          </div>

          <div id="characters-container" class="bg-white rounded-lg shadow">
            <div class="p-8 text-center text-gray-500">
              <div class="spinner w-8 h-8 border-4 border-primary-600 border-t-transparent rounded-full animate-spin mx-auto"></div>
              <p class="mt-2">${t('common.loading')}</p>
            </div>
          </div>
        </div>

        <!-- 模态框 -->
        <div id="character-modal" class="fixed inset-0 bg-black/50 z-50 hidden flex items-center justify-center">
          <div class="bg-white rounded-lg shadow-xl w-full max-w-2xl mx-4 max-h-[90vh] overflow-hidden">
            <div class="px-6 py-4 border-b border-gray-200 flex items-center justify-between">
              <h3 id="character-modal-title" class="text-lg font-semibold">新建角色</h3>
              <button onclick="ProjectCharactersPage.hideModal()" class="text-gray-400 hover:text-gray-600">
                <svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12"/>
                </svg>
              </button>
            </div>
            <div class="p-6 overflow-y-auto max-h-[60vh]">
              <form onsubmit="ProjectCharactersPage.saveCharacter(event)">
                <input type="hidden" id="character-id">
                <div class="space-y-4">
                  <div>
                    <label class="block text-sm font-medium text-gray-700 mb-1">角色名称 <span class="text-red-500">*</span></label>
                    <input type="text" id="character-name" required
                           class="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary-500">
                  </div>
                  <div>
                    <label class="block text-sm font-medium text-gray-700 mb-1">别名</label>
                    <input type="text" id="character-aliases" placeholder="别名1, 别名2"
                           class="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary-500">
                  </div>
                  <div>
                    <label class="block text-sm font-medium text-gray-700 mb-1">描述</label>
                    <textarea id="character-summary" rows="3"
                              class="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary-500"></textarea>
                  </div>
                  <div>
                    <label class="block text-sm font-medium text-gray-700 mb-1">详细资料 (JSON)</label>
                    <textarea id="character-profile" rows="6" placeholder='{"appearance": "", "personality": "", "background": ""}'
                              class="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary-500 font-mono text-sm"></textarea>
                  </div>
                </div>
                <div class="mt-6 flex justify-end gap-3">
                  <button type="button" onclick="ProjectCharactersPage.hideModal()" 
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
      const container = document.getElementById('characters-container');
      try {
        const workspace = window.AppState.currentWorkspace;
        const project = window.AppState.currentProject;
        
        if (!workspace || !project) {
          container.innerHTML = `<div class="p-8 text-center text-gray-500">请先选择工作区和项目</div>`;
          return;
        }

        const result = await window.ApiClient.kb.pk.list(project, 'character');
        this.renderList(result || []);
      } catch (error) {
        console.error('[Characters] Load error:', error);
        container.innerHTML = `<div class="p-8 text-center text-red-500">加载失败: ${error.message}</div>`;
      }
    },

    renderList(characters) {
      const container = document.getElementById('characters-container');
      
      if (!characters || characters.length === 0) {
        container.innerHTML = `
          <div class="p-8 text-center text-gray-500">
            <div class="text-4xl mb-2">👤</div>
            <p>暂无角色</p>
            <p class="text-sm mt-2">点击右上角按钮添加角色</p>
          </div>
        `;
        return;
      }

      container.innerHTML = `
        <div class="divide-y divide-gray-200">
          ${characters.map(char => `
            <div class="p-4 hover:bg-gray-50 transition-colors">
              <div class="flex items-start justify-between">
                <div class="flex-1 min-w-0">
                  <div class="flex items-center gap-2">
                    <span class="text-lg">👤</span>
                    <h3 class="font-medium text-gray-800">${char.key || char.title || '未命名'}</h3>
                  </div>
                  <p class="text-sm text-gray-500 mt-1 line-clamp-2">${char.value?.summary || char.description || '暂无描述'}</p>
                </div>
                <div class="flex items-center gap-2 ml-4">
                  <button onclick="ProjectCharactersPage.editCharacter('${char.id}', '${char.key}')" 
                          class="p-2 text-gray-400 hover:text-primary-600 hover:bg-primary-50 rounded transition-colors">
                    <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M11 5H6a2 2 0 00-2 2v11a2 2 0 002 2h11a2 2 0 002-2v-5m-1.414-9.414a2 2 0 112.828 2.828L11.828 15H9v-2.828l8.586-8.586z"/>
                    </svg>
                  </button>
                  <button onclick="ProjectCharactersPage.deleteCharacter('${char.id}', '${char.key}')" 
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
      document.getElementById('character-modal-title').textContent = '新建角色';
      document.getElementById('character-id').value = '';
      document.getElementById('character-name').value = '';
      document.getElementById('character-aliases').value = '';
      document.getElementById('character-summary').value = '';
      document.getElementById('character-profile').value = '';
      document.getElementById('character-modal').classList.remove('hidden');
    },

    hideModal() {
      document.getElementById('character-modal').classList.add('hidden');
    },

    async editCharacter(id, key) {
      try {
        const project = window.AppState.currentProject;
        const char = await window.ApiClient.kb.pk.get(project, 'character', key);
        
        document.getElementById('character-modal-title').textContent = '编辑角色';
        document.getElementById('character-id').value = id;
        document.getElementById('character-name').value = key;
        document.getElementById('character-aliases').value = (char?.value?.aliases || []).join(', ');
        document.getElementById('character-summary').value = char?.value?.summary || '';
        document.getElementById('character-profile').value = char?.value?.profile ? JSON.stringify(char.value.profile, null, 2) : '';
        document.getElementById('character-modal').classList.remove('hidden');
      } catch (error) {
        alert('加载角色失败: ' + error.message);
      }
    },

    async saveCharacter(e) {
      e.preventDefault();
      const project = window.AppState.currentProject;
      
      const key = document.getElementById('character-name').value;
      const aliasesStr = document.getElementById('character-aliases').value;
      const aliases = aliasesStr ? aliasesStr.split(',').map(a => a.trim()).filter(Boolean) : [];
      
      let profile = null;
      const profileStr = document.getElementById('character-profile').value;
      if (profileStr) {
        try { profile = JSON.parse(profileStr); } catch (e) { alert('JSON格式错误'); return; }
      }

      const value = {
        summary: document.getElementById('character-summary').value,
        aliases,
        profile
      };

      try {
        await window.ApiClient.kb.pk.upsert(project, 'character', key, value);
        this.hideModal();
        this.loadData();
      } catch (error) {
        alert('保存失败: ' + error.message);
      }
    },

    async deleteCharacter(id, key) {
      if (!confirm(`确定删除角色 "${key}" 吗？`)) return;
      
      try {
        await window.ApiClient.kb.pk.delete(window.AppState.currentProject, 'character', key);
        this.loadData();
      } catch (error) {
        alert('删除失败: ' + error.message);
      }
    }
  };
})();
