/**
 * Novel OS - Plot Volumes Page
 * 卷管理页面
 */
(function() {
  'use strict';

  window.PlotVolumesPage = {
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
              <h1 class="text-2xl font-bold text-gray-800">${t('nav.volumes')}</h1>
              <p class="text-gray-500 mt-1">管理小说卷章结构</p>
            </div>
            <button onclick="PlotVolumesPage.showCreateModal()" 
                    class="px-4 py-2 bg-primary-600 text-white rounded-lg hover:bg-primary-700 transition-colors">
              ${t('common.new')} 卷
            </button>
          </div>

          <div id="volumes-list-container" class="bg-white rounded-lg shadow">
            <div class="p-8 text-center text-gray-500">
              <div class="spinner w-8 h-8 border-4 border-primary-600 border-t-transparent rounded-full animate-spin mx-auto"></div>
              <p class="mt-2">${t('common.loading')}</p>
            </div>
          </div>
        </div>

        <!-- 创建/编辑模态框 -->
        <div id="volume-modal" class="fixed inset-0 bg-black/50 z-50 hidden flex items-center justify-center">
          <div class="bg-white rounded-lg shadow-xl w-full max-w-2xl mx-4 max-h-[90vh] overflow-hidden">
            <div class="px-6 py-4 border-b border-gray-200 flex items-center justify-between">
              <h3 id="volume-modal-title" class="text-lg font-semibold">新建卷</h3>
              <button onclick="PlotVolumesPage.hideModal()" class="text-gray-400 hover:text-gray-600">
                <svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12"/>
                </svg>
              </button>
            </div>
            <div class="p-6 overflow-y-auto max-h-[60vh]">
              <form id="volume-form" onsubmit="PlotVolumesPage.saveVolume(event)">
                <input type="hidden" id="volume-id">
                <div class="space-y-4">
                  <div class="grid grid-cols-2 gap-4">
                    <div>
                      <label class="block text-sm font-medium text-gray-700 mb-1">卷号 <span class="text-red-500">*</span></label>
                      <input type="number" id="volume-number" required min="1"
                             class="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary-500">
                    </div>
                    <div>
                      <label class="block text-sm font-medium text-gray-700 mb-1">标题</label>
                      <input type="text" id="volume-title" placeholder="如: 初入江湖"
                             class="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary-500">
                    </div>
                  </div>
                  <div class="grid grid-cols-2 gap-4">
                    <div>
                      <label class="block text-sm font-medium text-gray-700 mb-1">起始章节</label>
                      <input type="number" id="volume-start-chapter" min="1"
                             class="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary-500">
                    </div>
                    <div>
                      <label class="block text-sm font-medium text-gray-700 mb-1">结束章节</label>
                      <input type="number" id="volume-end-chapter" min="1"
                             class="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary-500">
                    </div>
                  </div>
                  <div>
                    <label class="block text-sm font-medium text-gray-700 mb-1">状态</label>
                    <select id="volume-status" 
                            class="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary-500">
                      <option value="planned">计划中</option>
                      <option value="writing">写作中</option>
                      <option value="completed">已完成</option>
                      <option value="published">已发布</option>
                    </select>
                  </div>
                  <div>
                    <label class="block text-sm font-medium text-gray-700 mb-1">摘要</label>
                    <textarea id="volume-summary" rows="3"
                              class="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary-500"></textarea>
                  </div>
                  <div>
                    <label class="block text-sm font-medium text-gray-700 mb-1">大纲</label>
                    <textarea id="volume-outline" rows="6"
                              class="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary-500"></textarea>
                  </div>
                  <div>
                    <label class="block text-sm font-medium text-gray-700 mb-1">卷目标（每行一个）</label>
                    <textarea id="volume-goals" rows="3" placeholder="主角拜入师门&#10;结识重要伙伴&#10;揭示世界观设定"
                              class="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary-500"></textarea>
                  </div>
                </div>
                <div class="mt-6 flex justify-end gap-3">
                  <button type="button" onclick="PlotVolumesPage.hideModal()" 
                          class="px-4 py-2 border border-gray-300 rounded-lg hover:bg-gray-50">
                    ${t('common.cancel')}
                  </button>
                  <button type="submit" id="volume-save-btn"
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
      const container = document.getElementById('volumes-list-container');
      try {
        const workspace = window.AppState.currentWorkspace;
        const project = window.AppState.currentProject;
        
        if (!workspace || !project) {
          container.innerHTML = `<div class="p-8 text-center text-gray-500">请先选择工作区和项目</div>`;
          return;
        }

        const result = await window.ApiClient.callTool('volume.list', { workspace, project });
        this.renderList(Array.isArray(result) ? result.filter(v => v.status !== 'archived' && v.status !== 'deleted') : []);
      } catch (error) {
        console.error('[PlotVolumes] Load error:', error);
        container.innerHTML = `<div class="p-8 text-center text-red-500">加载失败: ${error.message}</div>`;
      }
    },

    renderList(volumes) {
      const container = document.getElementById('volumes-list-container');
      
      if (!volumes || volumes.length === 0) {
        container.innerHTML = `
          <div class="p-8 text-center text-gray-500">
            <div class="text-4xl mb-2">📚</div>
            <p>暂无卷数据</p>
            <p class="text-sm mt-2">点击右上角按钮创建第一卷</p>
          </div>
        `;
        return;
      }

      // 按卷号排序
      volumes.sort((a, b) => (a.volume_no || 0) - (b.volume_no || 0));

      container.innerHTML = `
        <div class="divide-y divide-gray-200">
          ${volumes.map(vol => `
            <div class="p-4 hover:bg-gray-50 transition-colors">
              <div class="flex items-start justify-between">
                <div class="flex-1 min-w-0">
                  <div class="flex items-center gap-2">
                    <span class="px-3 py-1 bg-primary-100 text-primary-700 rounded font-medium text-sm">第${vol.volume_no}卷</span>
                    <h3 class="font-medium text-gray-800 truncate">${vol.title || '未命名'}</h3>
                    <span class="px-2 py-0.5 text-xs rounded-full ${this.getStatusClass(vol.status)}">
                      ${this.getStatusLabel(vol.status)}
                    </span>
                  </div>
                  ${vol.summary ? `<p class="text-sm text-gray-500 mt-2 line-clamp-2">${vol.summary}</p>` : ''}
                  <div class="flex items-center gap-4 mt-2 text-xs text-gray-400">
                    ${vol.start_chapter_no ? `<span>章节: ${vol.start_chapter_no} - ${vol.end_chapter_no || '?'}</span>` : ''}
                    ${vol.goals && vol.goals.length ? `<span>目标: ${vol.goals.length}个</span>` : ''}
                  </div>
                  ${vol.goals && vol.goals.length ? `<div class="flex flex-wrap gap-1 mt-2">${vol.goals.slice(0, 5).map(g => `<span class="text-xs bg-gray-100 text-gray-600 px-2 py-0.5 rounded">${g}</span>`).join('')}${vol.goals.length > 5 ? `<span class="text-xs text-gray-400">+${vol.goals.length - 5}</span>` : ''}</div>` : ''}
                </div>
                <div class="flex items-center gap-2 ml-4">
                  <button onclick="PlotVolumesPage.editVolume('${vol.id}')" 
                          class="p-2 text-gray-400 hover:text-primary-600 hover:bg-primary-50 rounded transition-colors"
                          title="编辑">
                    <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M11 5H6a2 2 0 00-2 2v11a2 2 0 002 2h11a2 2 0 002-2v-5m-1.414-9.414a2 2 0 112.828 2.828L11.828 15H9v-2.828l8.586-8.586z"/>
                    </svg>
                  </button>
                  <button onclick="PlotVolumesPage.deleteVolume('${vol.id}', ${vol.volume_no})" 
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
      document.getElementById('volume-modal-title').textContent = '新建卷';
      document.getElementById('volume-id').value = '';
      document.getElementById('volume-number').value = '';
      document.getElementById('volume-title').value = '';
      document.getElementById('volume-start-chapter').value = '';
      document.getElementById('volume-end-chapter').value = '';
      document.getElementById('volume-status').value = 'planned';
      document.getElementById('volume-summary').value = '';
      document.getElementById('volume-outline').value = '';
      document.getElementById('volume-goals').value = '';
      document.getElementById('volume-modal').classList.remove('hidden');
    },

    hideModal() {
      document.getElementById('volume-modal').classList.add('hidden');
    },

    async editVolume(id) {
      try {
        const workspace = window.AppState.currentWorkspace;
        const project = window.AppState.currentProject;
        const list = await window.ApiClient.callTool('volume.list', { workspace, project });
        const vol = Array.isArray(list) ? list.find(v => v.id === id || v.volume_no.toString() === id) : null;
        if (!vol) throw new Error('卷不存在');
        
        document.getElementById('volume-modal-title').textContent = '编辑卷';
        document.getElementById('volume-id').value = vol.id;
        document.getElementById('volume-number').value = vol.volume_no;
        document.getElementById('volume-title').value = vol.title || '';
        document.getElementById('volume-start-chapter').value = vol.start_chapter_no || '';
        document.getElementById('volume-end-chapter').value = vol.end_chapter_no || '';
        document.getElementById('volume-status').value = vol.status || 'planned';
        document.getElementById('volume-summary').value = vol.summary || '';
        document.getElementById('volume-outline').value = vol.outline || '';
        document.getElementById('volume-goals').value = (vol.goals || []).join('\n');
        document.getElementById('volume-modal').classList.remove('hidden');
      } catch (error) {
        alert('加载卷失败: ' + error.message);
      }
    },

    async saveVolume(e) {
      e.preventDefault();
      const workspace = window.AppState.currentWorkspace;
      const project = window.AppState.currentProject;
      const id = document.getElementById('volume-id').value;
      
      const data = {
        volume_no: parseInt(document.getElementById('volume-number').value),
        title: document.getElementById('volume-title').value || undefined,
        start_chapter_no: document.getElementById('volume-start-chapter').value ? parseInt(document.getElementById('volume-start-chapter').value) : undefined,
        end_chapter_no: document.getElementById('volume-end-chapter').value ? parseInt(document.getElementById('volume-end-chapter').value) : undefined,
        status: document.getElementById('volume-status').value,
        summary: document.getElementById('volume-summary').value || undefined,
        outline: document.getElementById('volume-outline').value || undefined,
        goals: document.getElementById('volume-goals').value ? document.getElementById('volume-goals').value.split('\n').filter(Boolean) : undefined
      };

      try {
        await window.ApiClient.callTool('volume.upsert', { workspace, project, ...data });
        this.hideModal();
        this.loadData();
      } catch (error) {
        alert('保存失败: ' + error.message);
      }
    },

    async deleteVolume(id, volumeNo) {
      if (!confirm(`确定删除第${volumeNo}卷吗？将标记为已删除状态。`)) return;
      
      try {
        // 获取卷信息
        const vol = await window.ApiClient.callTool('volume.list', { 
          workspace: window.AppState.currentWorkspace, 
          project: window.AppState.currentProject 
        });
        const volume = vol.find(v => v.id === id);
        
        if (!volume) {
          alert('卷不存在');
          return;
        }
        
        // 使用 upsert 更新状态为 deleted
        await window.ApiClient.callTool('volume.upsert', { 
          workspace: window.AppState.currentWorkspace, 
          project: window.AppState.currentProject,
          volume_no: volume.volume_no,
          title: volume.title,
          status: 'deleted'
        });
        this.loadData();
      } catch (error) {
        alert('删除失败: ' + error.message);
      }
    },

    getStatusClass(status) {
      const classes = {
        planned: 'bg-gray-100 text-gray-600',
        writing: 'bg-blue-100 text-blue-700',
        completed: 'bg-green-100 text-green-700',
        published: 'bg-purple-100 text-purple-700'
      };
      return classes[status] || 'bg-gray-100 text-gray-600';
    },

    getStatusLabel(status) {
      const labels = { planned: '计划中', writing: '写作中', completed: '已完成', published: '已发布' };
      return labels[status] || status;
    }
  };
})();
