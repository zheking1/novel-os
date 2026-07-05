/**
 * Novel OS - Canon List Page
 * Canon文档管理页面
 */
(function() {
  'use strict';

  window.CanonListPage = {
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
              <h1 class="text-2xl font-bold text-gray-800">${t('nav.canonList')}</h1>
              <p class="text-gray-500 mt-1">管理世界观设定文档</p>
            </div>
            <button onclick="CanonListPage.showCreateModal()" 
                    class="px-4 py-2 bg-primary-600 text-white rounded-lg hover:bg-primary-700 transition-colors">
              ${t('common.new')} Canon
            </button>
          </div>

          <div class="flex gap-4 items-center">
            <input type="text" id="canon-search" placeholder="${t('common.search')}..." 
                   oninput="CanonListPage.filterByType(this.value)"
                   class="flex-1 px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary-500">
            <select id="canon-type-filter" onchange="CanonListPage.filterByType(this.value)" 
                    class="px-4 py-2 border border-gray-300 rounded-lg">
              <option value="">全部类型</option>
              <option value="worldbuilding">世界设定</option>
              <option value="character">角色设定</option>
              <option value="plot">剧情设定</option>
              <option value="magic">魔法体系</option>
              <option value="technology">科技体系</option>
              <option value="culture">文化设定</option>
              <option value="history">历史设定</option>
              <option value="geography">地理设定</option>
              <option value="faction">势力设定</option>
              <option value="item">物品设定</option>
              <option value="creature">生物设定</option>
            </select>
          </div>

          <div id="canon-list-container" class="bg-white rounded-lg shadow">
            <div class="p-8 text-center text-gray-500">
              <div class="spinner w-8 h-8 border-4 border-primary-600 border-t-transparent rounded-full animate-spin mx-auto"></div>
              <p class="mt-2">${t('common.loading')}</p>
            </div>
          </div>
        </div>

        <!-- 创建/编辑模态框 -->
        <div id="canon-modal" class="fixed inset-0 bg-black/50 z-50 hidden flex items-center justify-center">
          <div class="bg-white rounded-lg shadow-xl w-full max-w-2xl mx-4 max-h-[90vh] overflow-hidden">
            <div class="px-6 py-4 border-b border-gray-200 flex items-center justify-between">
              <h3 id="canon-modal-title" class="text-lg font-semibold">新建 Canon 文档</h3>
              <button onclick="CanonListPage.hideModal()" class="text-gray-400 hover:text-gray-600">
                <svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12"/>
                </svg>
              </button>
            </div>
            <div class="p-6 overflow-y-auto max-h-[60vh]">
              <form id="canon-form" onsubmit="CanonListPage.saveCanon(event)">
                <input type="hidden" id="canon-id">
                <div class="space-y-4">
                  <div>
                    <label class="block text-sm font-medium text-gray-700 mb-1">标题 <span class="text-red-500">*</span></label>
                    <input type="text" id="canon-title" required
                           class="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary-500">
                  </div>
                  <div>
                    <label class="block text-sm font-medium text-gray-700 mb-1">类型 <span class="text-red-500">*</span></label>
                    <select id="canon-doc-type" required
                            class="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary-500">
                      <option value="worldbuilding">世界设定</option>
                      <option value="character">角色设定</option>
                      <option value="plot">剧情设定</option>
                      <option value="magic">魔法体系</option>
                      <option value="technology">科技体系</option>
                      <option value="culture">文化设定</option>
                      <option value="history">历史设定</option>
                      <option value="geography">地理设定</option>
                      <option value="faction">势力设定</option>
                      <option value="item">物品设定</option>
                      <option value="creature">生物设定</option>
                    </select>
                  </div>
                  <div>
                    <label class="block text-sm font-medium text-gray-700 mb-1">键名 (唯一标识)</label>
                    <input type="text" id="canon-key" placeholder="自动生成（如不填写）"
                           class="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary-500">
                  </div>
                  <div>
                    <label class="block text-sm font-medium text-gray-700 mb-1">内容 <span class="text-red-500">*</span></label>
                    <textarea id="canon-content" required rows="12"
                              class="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary-500 font-mono text-sm"></textarea>
                  </div>
                  <div>
                    <label class="block text-sm font-medium text-gray-700 mb-1">状态</label>
                    <select id="canon-status" class="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary-500">
                      <option value="active">生效</option>
                      <option value="draft">草稿</option>
                      <option value="archived">已归档</option>
                    </select>
                  </div>
                </div>
                <div class="mt-6 flex justify-end gap-3">
                  <button type="button" onclick="CanonListPage.hideModal()" 
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
      const container = document.getElementById('canon-list-container');
      try {
        const workspace = window.AppState.currentWorkspace;
        const project = window.AppState.currentProject;
        
        if (!workspace || !project) {
          container.innerHTML = `<div class="p-8 text-center text-gray-500">请先选择工作区和项目</div>`;
          return;
        }

        const result = await window.ApiClient.canonDoc.list(workspace, project);
        this.renderList(result || []);
      } catch (error) {
        console.error('[CanonList] Load error:', error);
        container.innerHTML = `<div class="p-8 text-center text-red-500">加载失败: ${error.message}</div>`;
      }
    },

    renderList(docs) {
      const container = document.getElementById('canon-list-container');
      
      if (!docs || docs.length === 0) {
        container.innerHTML = `
          <div class="p-8 text-center text-gray-500">
            <div class="text-4xl mb-2">📄</div>
            <p>暂无 Canon 文档</p>
            <p class="text-sm mt-2">点击右上角按钮创建第一个文档</p>
          </div>
        `;
        return;
      }

      container.innerHTML = `
        <div class="divide-y divide-gray-200">
          ${docs.map(doc => `
            <div class="p-4 hover:bg-gray-50 transition-colors" data-doc-id="${doc.id}">
              <div class="flex items-start justify-between">
                <div class="flex-1 min-w-0">
                  <div class="flex items-center gap-2">
                    <span class="text-lg">${this.getTypeIcon(doc.doc_type)}</span>
                    <h3 class="font-medium text-gray-800 truncate">${doc.title}</h3>
                    <span class="px-2 py-0.5 text-xs rounded-full ${this.getStatusClass(doc.status)}">
                      ${this.getStatusLabel(doc.status)}
                    </span>
                  </div>
                  <p class="text-sm text-gray-500 mt-1 line-clamp-2">${doc.content?.substring(0, 200) || '暂无内容'}</p>
                  <div class="flex items-center gap-4 mt-2 text-xs text-gray-400">
                    <span>类型: ${doc.doc_type}</span>
                    ${doc.key ? `<span>键名: ${doc.key}</span>` : ''}
                    <span>更新: ${doc.updated_at ? new Date(doc.updated_at).toLocaleDateString() : '-'}</span>
                  </div>
                </div>
                <div class="flex items-center gap-2 ml-4">
                  <button onclick="CanonListPage.editCanon('${doc.id}')" 
                          class="p-2 text-gray-400 hover:text-primary-600 hover:bg-primary-50 rounded transition-colors"
                          title="编辑">
                    <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M11 5H6a2 2 0 00-2 2v11a2 2 0 002 2h11a2 2 0 002-2v-5m-1.414-9.414a2 2 0 112.828 2.828L11.828 15H9v-2.828l8.586-8.586z"/>
                    </svg>
                  </button>
                  <button onclick="CanonListPage.deleteCanon('${doc.id}', '${doc.title}')" 
                          class="p-2 text-gray-400 hover:text-red-600 hover:bg-red-50 rounded transition-colors"
                          title="删除">
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

    filterByType() {
      // TODO: 实现过滤逻辑
      this.loadData();
    },

    showCreateModal() {
      document.getElementById('canon-modal-title').textContent = '新建 Canon 文档';
      document.getElementById('canon-id').value = '';
      document.getElementById('canon-title').value = '';
      document.getElementById('canon-doc-type').value = 'worldbuilding';
      document.getElementById('canon-key').value = '';
      document.getElementById('canon-content').value = '';
      document.getElementById('canon-status').value = 'active';
      document.getElementById('canon-modal').classList.remove('hidden');
    },

    hideModal() {
      document.getElementById('canon-modal').classList.add('hidden');
    },

    async editCanon(id) {
      try {
        const workspace = window.AppState.currentWorkspace;
        const project = window.AppState.currentProject;
        const doc = await window.ApiClient.canonDoc.get(workspace, project, { document_id: id });
        
        document.getElementById('canon-modal-title').textContent = '编辑 Canon 文档';
        document.getElementById('canon-id').value = doc.id;
        document.getElementById('canon-title').value = doc.title;
        document.getElementById('canon-doc-type').value = doc.doc_type;
        document.getElementById('canon-key').value = doc.key || '';
        document.getElementById('canon-content').value = doc.content;
        document.getElementById('canon-status').value = doc.status;
        document.getElementById('canon-modal').classList.remove('hidden');
      } catch (error) {
        alert('加载文档失败: ' + error.message);
      }
    },

    async saveCanon(e) {
      e.preventDefault();
      const workspace = window.AppState.currentWorkspace;
      const project = window.AppState.currentProject;
      const id = document.getElementById('canon-id').value;
      
      const data = {
        title: document.getElementById('canon-title').value,
        doc_type: document.getElementById('canon-doc-type').value,
        key: document.getElementById('canon-key').value || undefined,
        content: document.getElementById('canon-content').value,
        status: document.getElementById('canon-status').value
      };

      try {
        if (id) {
          await window.ApiClient.canonDoc.update(workspace, project, id, data);
        } else {
          await window.ApiClient.canonDoc.create(workspace, project, data);
        }
        this.hideModal();
        this.loadData();
      } catch (error) {
        alert('保存失败: ' + error.message);
      }
    },

    async deleteCanon(id, title) {
      if (!confirm(`确定删除文档 "${title}" 吗？此操作不可恢复。`)) return;
      
      try {
        await window.ApiClient.canonDoc.delete(window.AppState.currentWorkspace, window.AppState.currentProject, id);
        this.loadData();
      } catch (error) {
        alert('删除失败: ' + error.message);
      }
    },

    getTypeIcon(type) {
      const icons = {
        worldbuilding: '🌍', character: '👤', plot: '📖', magic: '✨',
        technology: '⚙️', culture: '🏛️', history: '📜', geography: '🗺️',
        faction: '🏴', item: '🎒', creature: '🐉'
      };
      return icons[type] || '📄';
    },

    getStatusClass(status) {
      const classes = {
        active: 'bg-green-100 text-green-700',
        draft: 'bg-yellow-100 text-yellow-700',
        archived: 'bg-gray-100 text-gray-500'
      };
      return classes[status] || 'bg-gray-100 text-gray-500';
    },

    getStatusLabel(status) {
      const labels = { active: '生效', draft: '草稿', archived: '归档' };
      return labels[status] || status;
    }
  };
})();
