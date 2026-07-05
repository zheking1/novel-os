/**
 * Novel OS - Plot Threads Page
 * 情节线管理页面
 */
(function() {
  'use strict';

  window.PlotThreadsPage = {
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
              <h1 class="text-2xl font-bold text-gray-800">${t('nav.threads')}</h1>
              <p class="text-gray-500 mt-1">管理情节线索和进度</p>
            </div>
            <button onclick="PlotThreadsPage.showCreateModal()" 
                    class="px-4 py-2 bg-primary-600 text-white rounded-lg hover:bg-primary-700 transition-colors">
              ${t('common.new')} 情节线
            </button>
          </div>

          <div class="flex gap-4 items-center">
            <select id="thread-status-filter" onchange="PlotThreadsPage.loadData()" 
                    class="px-4 py-2 border border-gray-300 rounded-lg">
              <option value="">全部状态</option>
              <option value="open">进行中</option>
              <option value="resolved">已解决</option>
              <option value="abandoned">已废弃</option>
            </select>
            <select id="thread-type-filter" onchange="PlotThreadsPage.loadData()" 
                    class="px-4 py-2 border border-gray-300 rounded-lg">
              <option value="">全部类型</option>
              <option value="main">主线</option>
              <option value="sub">支线</option>
              <option value="arc">弧线</option>
            </select>
          </div>

          <div id="threads-list-container" class="bg-white rounded-lg shadow">
            <div class="p-8 text-center text-gray-500">
              <div class="spinner w-8 h-8 border-4 border-primary-600 border-t-transparent rounded-full animate-spin mx-auto"></div>
              <p class="mt-2">${t('common.loading')}</p>
            </div>
          </div>
        </div>

        <!-- 创建/编辑模态框 -->
        <div id="thread-modal" class="fixed inset-0 bg-black/50 z-50 hidden flex items-center justify-center">
          <div class="bg-white rounded-lg shadow-xl w-full max-w-2xl mx-4 max-h-[90vh] overflow-hidden">
            <div class="px-6 py-4 border-b border-gray-200 flex items-center justify-between">
              <h3 id="thread-modal-title" class="text-lg font-semibold">新建情节线</h3>
              <button onclick="PlotThreadsPage.hideModal()" class="text-gray-400 hover:text-gray-600">
                <svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12"/>
                </svg>
              </button>
            </div>
            <div class="p-6 overflow-y-auto max-h-[60vh]">
              <form id="thread-form" onsubmit="PlotThreadsPage.saveThread(event)">
                <input type="hidden" id="thread-id">
                <div class="space-y-4">
                  <div>
                    <label class="block text-sm font-medium text-gray-700 mb-1">标题 <span class="text-red-500">*</span></label>
                    <input type="text" id="thread-title" required
                           class="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary-500">
                  </div>
                  <div>
                    <label class="block text-sm font-medium text-gray-700 mb-1">键名 <span class="text-red-500">*</span></label>
                    <input type="text" id="thread-key" required placeholder="如: protagonist_journey"
                           class="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary-500 font-mono">
                  </div>
                  <div class="grid grid-cols-2 gap-4">
                    <div>
                      <label class="block text-sm font-medium text-gray-700 mb-1">类型</label>
                      <select id="thread-type" 
                              class="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary-500">
                        <option value="main">主线</option>
                        <option value="sub">支线</option>
                        <option value="arc">弧线</option>
                      </select>
                    </div>
                    <div>
                      <label class="block text-sm font-medium text-gray-700 mb-1">重要程度</label>
                      <select id="thread-importance" 
                              class="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary-500">
                        <option value="low">低</option>
                        <option value="medium" selected>中</option>
                        <option value="high">高</option>
                        <option value="critical">关键</option>
                      </select>
                    </div>
                  </div>
                  <div class="grid grid-cols-2 gap-4">
                    <div>
                      <label class="block text-sm font-medium text-gray-700 mb-1">当前章节</label>
                      <input type="number" id="thread-current-chapter" min="1"
                             class="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary-500">
                    </div>
                    <div>
                      <label class="block text-sm font-medium text-gray-700 mb-1">期望下一章</label>
                      <input type="number" id="thread-expected-next" min="1"
                             class="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary-500">
                    </div>
                  </div>
                  <div>
                    <label class="block text-sm font-medium text-gray-700 mb-1">进度备注</label>
                    <textarea id="thread-progress-note" rows="3"
                              class="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary-500"></textarea>
                  </div>
                </div>
                <div class="mt-6 flex justify-end gap-3">
                  <button type="button" onclick="PlotThreadsPage.hideModal()" 
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
      const container = document.getElementById('threads-list-container');
      try {
        const workspace = window.AppState.currentWorkspace;
        const project = window.AppState.currentProject;
        
        if (!workspace || !project) {
          container.innerHTML = `<div class="p-8 text-center text-gray-500">请先选择工作区和项目</div>`;
          return;
        }

        const result = await window.ApiClient.plotThread.list(workspace, project);
        this.renderList(result || []);
      } catch (error) {
        console.error('[PlotThreads] Load error:', error);
        container.innerHTML = `<div class="p-8 text-center text-red-500">加载失败: ${error.message}</div>`;
      }
    },

    renderList(threads) {
      const container = document.getElementById('threads-list-container');
      
      if (!threads || threads.length === 0) {
        container.innerHTML = `
          <div class="p-8 text-center text-gray-500">
            <div class="text-4xl mb-2">🧵</div>
            <p>暂无情节线</p>
            <p class="text-sm mt-2">点击右上角按钮创建第一个情节线</p>
          </div>
        `;
        return;
      }

      container.innerHTML = `
        <div class="divide-y divide-gray-200">
          ${threads.map(thread => `
            <div class="p-4 hover:bg-gray-50 transition-colors">
              <div class="flex items-start justify-between">
                <div class="flex-1 min-w-0">
                  <div class="flex items-center gap-2">
                    <span class="px-2 py-0.5 text-xs rounded-full ${this.getTypeClass(thread.thread_type)}">
                      ${thread.thread_type || 'sub'}
                    </span>
                    <h3 class="font-medium text-gray-800 truncate">${thread.title}</h3>
                    <span class="px-2 py-0.5 text-xs rounded-full ${this.getStatusClass(thread.status)}">
                      ${this.getStatusLabel(thread.status)}
                    </span>
                    <span class="px-2 py-0.5 text-xs rounded-full ${this.getImportanceClass(thread.importance)}">
                      ${thread.importance || 'medium'}
                    </span>
                  </div>
                  ${thread.progress_note ? `<p class="text-sm text-gray-500 mt-1">${thread.progress_note}</p>` : ''}
                  <div class="flex items-center gap-4 mt-2 text-xs text-gray-400">
                    <span>键名: ${thread.key}</span>
                    ${thread.current_chapter_no ? `<span>当前: 第${thread.current_chapter_no}章</span>` : ''}
                    ${thread.expected_next_chapter_no ? `<span>期望: 第${thread.expected_next_chapter_no}章</span>` : ''}
                    ${thread.stalled ? '<span class="text-orange-500">已停滞</span>' : ''}
                  </div>
                </div>
                <div class="flex items-center gap-2 ml-4">
                  <button onclick="PlotThreadsPage.advanceThread('${thread.id}')" 
                          class="p-2 text-gray-400 hover:text-green-600 hover:bg-green-50 rounded transition-colors"
                          title="推进">
                    <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M14.752 11.168l-3.197-2.132A1 1 0 0010 9.87v4.263a1 1 0 001.555.832l3.197-2.132a1 1 0 000-1.664z"/>
                      <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M21 12a9 9 0 11-18 0 9 9 0 0118 0z"/>
                    </svg>
                  </button>
                  <button onclick="PlotThreadsPage.editThread('${thread.id}')" 
                          class="p-2 text-gray-400 hover:text-primary-600 hover:bg-primary-50 rounded transition-colors"
                          title="编辑">
                    <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M11 5H6a2 2 0 00-2 2v11a2 2 0 002 2h11a2 2 0 002-2v-5m-1.414-9.414a2 2 0 112.828 2.828L11.828 15H9v-2.828l8.586-8.586z"/>
                    </svg>
                  </button>
                  <button onclick="PlotThreadsPage.deleteThread('${thread.id}', '${thread.title}')" 
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
      document.getElementById('thread-modal-title').textContent = '新建情节线';
      document.getElementById('thread-id').value = '';
      document.getElementById('thread-title').value = '';
      document.getElementById('thread-key').value = '';
      document.getElementById('thread-type').value = 'main';
      document.getElementById('thread-importance').value = 'medium';
      document.getElementById('thread-current-chapter').value = '';
      document.getElementById('thread-expected-next').value = '';
      document.getElementById('thread-progress-note').value = '';
      document.getElementById('thread-modal').classList.remove('hidden');
    },

    hideModal() {
      document.getElementById('thread-modal').classList.add('hidden');
    },

    async editThread(id) {
      try {
        const workspace = window.AppState.currentWorkspace;
        const project = window.AppState.currentProject;
        const thread = await window.ApiClient.plotThread.get(workspace, project, id);
        
        document.getElementById('thread-modal-title').textContent = '编辑情节线';
        document.getElementById('thread-id').value = thread.id;
        document.getElementById('thread-title').value = thread.title;
        document.getElementById('thread-key').value = thread.key;
        document.getElementById('thread-type').value = thread.thread_type || 'main';
        document.getElementById('thread-importance').value = thread.importance || 'medium';
        document.getElementById('thread-current-chapter').value = thread.current_chapter_no || '';
        document.getElementById('thread-expected-next').value = thread.expected_next_chapter_no || '';
        document.getElementById('thread-progress-note').value = thread.progress_note || '';
        document.getElementById('thread-modal').classList.remove('hidden');
      } catch (error) {
        alert('加载情节线失败: ' + error.message);
      }
    },

    async saveThread(e) {
      e.preventDefault();
      const workspace = window.AppState.currentWorkspace;
      const project = window.AppState.currentProject;
      const id = document.getElementById('thread-id').value;
      
      const data = {
        title: document.getElementById('thread-title').value,
        key: document.getElementById('thread-key').value,
        thread_type: document.getElementById('thread-type').value,
        importance: document.getElementById('thread-importance').value,
        current_chapter_no: document.getElementById('thread-current-chapter').value ? parseInt(document.getElementById('thread-current-chapter').value) : undefined,
        expected_next_chapter_no: document.getElementById('thread-expected-next').value ? parseInt(document.getElementById('thread-expected-next').value) : undefined,
        progress_note: document.getElementById('thread-progress-note').value || undefined
      };

      try {
        if (id) {
          await window.ApiClient.plotThread.update(workspace, project, id, data);
        } else {
          await window.ApiClient.plotThread.create(workspace, project, data);
        }
        this.hideModal();
        this.loadData();
      } catch (error) {
        alert('保存失败: ' + error.message);
      }
    },

    async deleteThread(id, title) {
      if (!confirm(`确定删除情节线 "${title}" 吗？此操作不可恢复。`)) return;
      
      try {
        await window.ApiClient.plotThread.delete(window.AppState.currentWorkspace, window.AppState.currentProject, id);
        this.loadData();
      } catch (error) {
        alert('删除失败: ' + error.message);
      }
    },

    async advanceThread(id) {
      const chapter = prompt('请输入推进到的章节号:');
      if (!chapter) return;
      
      try {
        await window.ApiClient.plotThread.advance(window.AppState.currentWorkspace, window.AppState.currentProject, id, parseInt(chapter));
        this.loadData();
      } catch (error) {
        alert('推进失败: ' + error.message);
      }
    },

    getTypeClass(type) {
      const classes = { main: 'bg-blue-100 text-blue-700', sub: 'bg-purple-100 text-purple-700', arc: 'bg-green-100 text-green-700' };
      return classes[type] || 'bg-gray-100 text-gray-600';
    },

    getStatusClass(status) {
      const classes = { open: 'bg-yellow-100 text-yellow-700', resolved: 'bg-green-100 text-green-700', abandoned: 'bg-gray-100 text-gray-500' };
      return classes[status] || 'bg-gray-100 text-gray-600';
    },

    getStatusLabel(status) {
      const labels = { open: '进行中', resolved: '已解决', abandoned: '已废弃' };
      return labels[status] || status;
    },

    getImportanceClass(importance) {
      const classes = { low: 'bg-gray-100 text-gray-600', medium: 'bg-blue-100 text-blue-700', high: 'bg-orange-100 text-orange-700', critical: 'bg-red-100 text-red-700' };
      return classes[importance] || 'bg-blue-100 text-blue-700';
    }
  };
})();
