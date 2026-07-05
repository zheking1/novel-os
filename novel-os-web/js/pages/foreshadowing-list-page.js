/**
 * Novel OS - Foreshadowing List Page
 * 伏笔管理页面
 */
(function() {
  'use strict';

  window.ForeshadowingListPage = {
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
              <h1 class="text-2xl font-bold text-gray-800">${t('nav.foreshadowList')}</h1>
              <p class="text-gray-500 mt-1">管理伏笔的埋设和回收</p>
            </div>
            <button onclick="ForeshadowingListPage.showCreateModal()" 
                    class="px-4 py-2 bg-primary-600 text-white rounded-lg hover:bg-primary-700 transition-colors">
              ${t('common.new')} 伏笔
            </button>
          </div>

          <div class="flex gap-4 items-center">
            <select id="foreshadow-status-filter" onchange="ForeshadowingListPage.loadData()" 
                    class="px-4 py-2 border border-gray-300 rounded-lg">
              <option value="">全部状态</option>
              <option value="planted">已埋设</option>
              <option value="paid_off">已回收</option>
              <option value="expired">已过期</option>
              <option value="abandoned">已废弃</option>
            </select>
            <select id="foreshadow-layer-filter" onchange="ForeshadowingListPage.loadData()" 
                    class="px-4 py-2 border border-gray-300 rounded-lg">
              <option value="">全部层级</option>
              <option value="visible">显性</option>
              <option value="subtle">隐性</option>
              <option value="deep">深层</option>
            </select>
          </div>

          <div id="foreshadow-list-container" class="bg-white rounded-lg shadow">
            <div class="p-8 text-center text-gray-500">
              <div class="spinner w-8 h-8 border-4 border-primary-600 border-t-transparent rounded-full animate-spin mx-auto"></div>
              <p class="mt-2">${t('common.loading')}</p>
            </div>
          </div>
        </div>

        <!-- 创建/编辑模态框 -->
        <div id="foreshadow-modal" class="fixed inset-0 bg-black/50 z-50 hidden flex items-center justify-center">
          <div class="bg-white rounded-lg shadow-xl w-full max-w-2xl mx-4 max-h-[90vh] overflow-hidden">
            <div class="px-6 py-4 border-b border-gray-200 flex items-center justify-between">
              <h3 id="foreshadow-modal-title" class="text-lg font-semibold">新建伏笔</h3>
              <button onclick="ForeshadowingListPage.hideModal()" class="text-gray-400 hover:text-gray-600">
                <svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12"/>
                </svg>
              </button>
            </div>
            <div class="p-6 overflow-y-auto max-h-[60vh]">
              <form id="foreshadow-form" onsubmit="ForeshadowingListPage.saveForeshadow(event)">
                <input type="hidden" id="foreshadow-id">
                <div class="space-y-4">
                  <div>
                    <label class="block text-sm font-medium text-gray-700 mb-1">标题 <span class="text-red-500">*</span></label>
                    <input type="text" id="foreshadow-title" required
                           class="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary-500">
                  </div>
                  <div>
                    <label class="block text-sm font-medium text-gray-700 mb-1">键名 <span class="text-red-500">*</span></label>
                    <input type="text" id="foreshadow-key" required placeholder="如: mysterious_sword"
                           class="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary-500 font-mono">
                  </div>
                  <div class="grid grid-cols-2 gap-4">
                    <div>
                      <label class="block text-sm font-medium text-gray-700 mb-1">层级</label>
                      <select id="foreshadow-layer" 
                              class="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary-500">
                        <option value="visible">显性</option>
                        <option value="subtle">隐性</option>
                        <option value="deep">深层</option>
                      </select>
                    </div>
                    <div>
                      <label class="block text-sm font-medium text-gray-700 mb-1">重要程度</label>
                      <select id="foreshadow-importance" 
                              class="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary-500">
                        <option value="low">低</option>
                        <option value="medium" selected>中</option>
                        <option value="high">高</option>
                        <option value="critical">关键</option>
                      </select>
                    </div>
                  </div>
                  <div>
                    <label class="block text-sm font-medium text-gray-700 mb-1">描述</label>
                    <textarea id="foreshadow-description" rows="3"
                              class="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary-500"></textarea>
                  </div>
                  <div class="grid grid-cols-2 gap-4">
                    <div>
                      <label class="block text-sm font-medium text-gray-700 mb-1">埋设章节</label>
                      <input type="number" id="foreshadow-planted-chapter" min="1"
                             class="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary-500">
                    </div>
                    <div>
                      <label class="block text-sm font-medium text-gray-700 mb-1">期望回收章节</label>
                      <input type="number" id="foreshadow-deadline" min="1"
                             class="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary-500">
                    </div>
                  </div>
                  <div>
                    <label class="block text-sm font-medium text-gray-700 mb-1">状态</label>
                    <select id="foreshadow-status" 
                            class="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary-500">
                      <option value="planted">已埋设</option>
                      <option value="paid_off">已回收</option>
                      <option value="expired">已过期</option>
                      <option value="abandoned">已废弃</option>
                    </select>
                  </div>
                </div>
                <div class="mt-6 flex justify-end gap-3">
                  <button type="button" onclick="ForeshadowingListPage.hideModal()" 
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
      const container = document.getElementById('foreshadow-list-container');
      try {
        const workspace = window.AppState.currentWorkspace;
        const project = window.AppState.currentProject;
        
        if (!workspace || !project) {
          container.innerHTML = `<div class="p-8 text-center text-gray-500">请先选择工作区和项目</div>`;
          return;
        }

        const result = await window.ApiClient.foreshadowing.list(workspace, project);
        this.renderList(result || []);
      } catch (error) {
        console.error('[ForeshadowingList] Load error:', error);
        container.innerHTML = `<div class="p-8 text-center text-red-500">加载失败: ${error.message}</div>`;
      }
    },

    renderList(foreshadows) {
      const container = document.getElementById('foreshadow-list-container');
      
      if (!foreshadows || foreshadows.length === 0) {
        container.innerHTML = `
          <div class="p-8 text-center text-gray-500">
            <div class="text-4xl mb-2">🔮</div>
            <p>暂无伏笔</p>
            <p class="text-sm mt-2">点击右上角按钮创建第一个伏笔</p>
          </div>
        `;
        return;
      }

      container.innerHTML = `
        <div class="divide-y divide-gray-200">
          ${foreshadows.map(fs => `
            <div class="p-4 hover:bg-gray-50 transition-colors">
              <div class="flex items-start justify-between">
                <div class="flex-1 min-w-0">
                  <div class="flex items-center gap-2">
                    <span class="px-2 py-0.5 text-xs rounded-full ${this.getLayerClass(fs.layer)}">
                      ${fs.layer || 'visible'}
                    </span>
                    <h3 class="font-medium text-gray-800 truncate">${fs.title}</h3>
                    <span class="px-2 py-0.5 text-xs rounded-full ${this.getStatusClass(fs.status)}">
                      ${this.getStatusLabel(fs.status)}
                    </span>
                    <span class="px-2 py-0.5 text-xs rounded-full ${this.getImportanceClass(fs.importance)}">
                      ${fs.importance || 'medium'}
                    </span>
                  </div>
                  ${fs.description ? `<p class="text-sm text-gray-500 mt-1 line-clamp-2">${fs.description}</p>` : ''}
                  <div class="flex items-center gap-4 mt-2 text-xs text-gray-400">
                    <span>键名: ${fs.key}</span>
                    ${fs.planted_chapter_no ? `<span>埋设: 第${fs.planted_chapter_no}章</span>` : ''}
                    ${fs.payoff_deadline_chapter ? `<span>期望回收: 第${fs.payoff_deadline_chapter}章</span>` : ''}
                    ${fs.payoff_chapter_no ? `<span>回收: 第${fs.payoff_chapter_no}章</span>` : ''}
                  </div>
                </div>
                <div class="flex items-center gap-2 ml-4">
                  ${fs.status === 'planted' ? `
                    <button onclick="ForeshadowingListPage.payoffForeshadow('${fs.id}')" 
                            class="p-2 text-gray-400 hover:text-green-600 hover:bg-green-50 rounded transition-colors"
                            title="回收">
                      <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M5 13l4 4L19 7"/>
                      </svg>
                    </button>
                  ` : ''}
                  <button onclick="ForeshadowingListPage.editForeshadow('${fs.id}')" 
                          class="p-2 text-gray-400 hover:text-primary-600 hover:bg-primary-50 rounded transition-colors"
                          title="编辑">
                    <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M11 5H6a2 2 0 00-2 2v11a2 2 0 002 2h11a2 2 0 002-2v-5m-1.414-9.414a2 2 0 112.828 2.828L11.828 15H9v-2.828l8.586-8.586z"/>
                    </svg>
                  </button>
                  <button onclick="ForeshadowingListPage.deleteForeshadow('${fs.id}', '${fs.title}')" 
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

    showCreateModal() {
      document.getElementById('foreshadow-modal-title').textContent = '新建伏笔';
      document.getElementById('foreshadow-id').value = '';
      document.getElementById('foreshadow-title').value = '';
      document.getElementById('foreshadow-key').value = '';
      document.getElementById('foreshadow-layer').value = 'visible';
      document.getElementById('foreshadow-importance').value = 'medium';
      document.getElementById('foreshadow-description').value = '';
      document.getElementById('foreshadow-planted-chapter').value = '';
      document.getElementById('foreshadow-deadline').value = '';
      document.getElementById('foreshadow-status').value = 'planted';
      document.getElementById('foreshadow-modal').classList.remove('hidden');
    },

    hideModal() {
      document.getElementById('foreshadow-modal').classList.add('hidden');
    },

    async editForeshadow(id) {
      try {
        const workspace = window.AppState.currentWorkspace;
        const project = window.AppState.currentProject;
        const fs = await window.ApiClient.foreshadowing.get(workspace, project, id);
        
        document.getElementById('foreshadow-modal-title').textContent = '编辑伏笔';
        document.getElementById('foreshadow-id').value = fs.id;
        document.getElementById('foreshadow-title').value = fs.title;
        document.getElementById('foreshadow-key').value = fs.key;
        document.getElementById('foreshadow-layer').value = fs.layer || 'visible';
        document.getElementById('foreshadow-importance').value = fs.importance || 'medium';
        document.getElementById('foreshadow-description').value = fs.description || '';
        document.getElementById('foreshadow-planted-chapter').value = fs.planted_chapter_no || '';
        document.getElementById('foreshadow-deadline').value = fs.payoff_deadline_chapter || '';
        document.getElementById('foreshadow-status').value = fs.status || 'planted';
        document.getElementById('foreshadow-modal').classList.remove('hidden');
      } catch (error) {
        alert('加载伏笔失败: ' + error.message);
      }
    },

    async saveForeshadow(e) {
      e.preventDefault();
      const workspace = window.AppState.currentWorkspace;
      const project = window.AppState.currentProject;
      const id = document.getElementById('foreshadow-id').value;
      
      const data = {
        title: document.getElementById('foreshadow-title').value,
        key: document.getElementById('foreshadow-key').value,
        layer: document.getElementById('foreshadow-layer').value,
        importance: document.getElementById('foreshadow-importance').value,
        description: document.getElementById('foreshadow-description').value || undefined,
        planted_chapter_no: document.getElementById('foreshadow-planted-chapter').value ? parseInt(document.getElementById('foreshadow-planted-chapter').value) : undefined,
        payoff_deadline_chapter: document.getElementById('foreshadow-deadline').value ? parseInt(document.getElementById('foreshadow-deadline').value) : undefined,
        status: document.getElementById('foreshadow-status').value
      };

      try {
        if (id) {
          await window.ApiClient.foreshadowing.update(workspace, project, id, data);
        } else {
          await window.ApiClient.foreshadowing.create(workspace, project, data);
        }
        this.hideModal();
        this.loadData();
      } catch (error) {
        alert('保存失败: ' + error.message);
      }
    },

    async deleteForeshadow(id, title) {
      if (!confirm(`确定删除伏笔 "${title}" 吗？此操作不可恢复。`)) return;
      
      try {
        await window.ApiClient.foreshadowing.delete(window.AppState.currentWorkspace, window.AppState.currentProject, id);
        this.loadData();
      } catch (error) {
        alert('删除失败: ' + error.message);
      }
    },

    async payoffForeshadow(id) {
      const chapter = prompt('请输入回收章节号:');
      if (!chapter) return;
      
      try {
        await window.ApiClient.foreshadowing.payoff(window.AppState.currentWorkspace, window.AppState.currentProject, id, parseInt(chapter));
        this.loadData();
      } catch (error) {
        alert('回收失败: ' + error.message);
      }
    },

    getLayerClass(layer) {
      const classes = { visible: 'bg-blue-100 text-blue-700', subtle: 'bg-purple-100 text-purple-700', deep: 'bg-indigo-100 text-indigo-700' };
      return classes[layer] || 'bg-gray-100 text-gray-600';
    },

    getStatusClass(status) {
      const classes = { planted: 'bg-yellow-100 text-yellow-700', paid_off: 'bg-green-100 text-green-700', expired: 'bg-gray-100 text-gray-500', abandoned: 'bg-red-100 text-red-500' };
      return classes[status] || 'bg-gray-100 text-gray-600';
    },

    getStatusLabel(status) {
      const labels = { planted: '已埋设', paid_off: '已回收', expired: '已过期', abandoned: '已废弃' };
      return labels[status] || status;
    },

    getImportanceClass(importance) {
      const classes = { low: 'bg-gray-100 text-gray-600', medium: 'bg-blue-100 text-blue-700', high: 'bg-orange-100 text-orange-700', critical: 'bg-red-100 text-red-700' };
      return classes[importance] || 'bg-blue-100 text-blue-700';
    }
  };
})();
