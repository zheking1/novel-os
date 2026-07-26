/**
 * KB Auto Search Page
 * 知识自动搜索 - 自动搜索并组织知识
 */
(function() {
  window.KbAutoSearchPage = {
    jobs: [],

    async init() {
      const contentArea = document.getElementById('content-area');
      contentArea.innerHTML = `
        <div class="flex items-center justify-between mb-6">
          <h1 class="text-2xl font-bold text-gray-800">${window.t('nav.autoSearch') || '知识自动搜索'}</h1>
          <div class="flex gap-2">
            <button onclick="KbAutoSearchPage.showCreateModal()" class="px-4 py-2 bg-primary-600 text-white rounded-lg hover:bg-primary-700 text-sm">🔍 新建搜索任务</button>
            <button onclick="KbAutoSearchPage.loadData()" class="px-4 py-2 bg-gray-100 text-gray-700 rounded-lg hover:bg-gray-200 text-sm">🔄 刷新</button>
          </div>
        </div>
        <div id="auto-search-content" class="bg-white rounded-lg shadow">
          <div class="p-8 text-center text-gray-500">加载中...</div>
        </div>
      `;
      await this.loadData();
      return true;
    },

    async loadData() {
      const container = document.getElementById('auto-search-content');
      try {
        // List search jobs
        const result = await window.ApiClient.callTool('kb.gap.list').catch(() => []);
        this.jobs = Array.isArray(result) ? result : (result?.gaps || result?.result || []);
        this.renderJobs();
      } catch (e) {
        container.innerHTML = `<div class="p-8 text-center text-red-500">加载失败: ${e.message}</div>`;
      }
    },

    renderJobs() {
      const container = document.getElementById('auto-search-content');
      
      if (!this.jobs || this.jobs.length === 0) {
        container.innerHTML = `<div class="p-8 text-center text-gray-500">暂无搜索任务</div>`;
        return;
      }

      container.innerHTML = `
        <div class="overflow-x-auto">
          <table class="w-full text-sm">
            <thead class="bg-gray-50">
              <tr>
                <th class="px-4 py-3 text-left font-medium text-gray-600">查询内容</th>
                <th class="px-4 py-3 text-left font-medium text-gray-600">类型</th>
                <th class="px-4 py-3 text-left font-medium text-gray-600">状态</th>
                <th class="px-4 py-3 text-left font-medium text-gray-600">操作</th>
              </tr>
            </thead>
            <tbody class="divide-y divide-gray-100">
              ${this.jobs.map(job => `
                <tr class="hover:bg-gray-50">
                  <td class="px-4 py-3">
                    <div class="font-medium text-gray-800">${job.description || job.query || '未命名'}</div>
                    ${job.entity_name ? `<div class="text-xs text-gray-500">实体: ${job.entity_name}</div>` : ''}
                  </td>
                  <td class="px-4 py-3">
                    <span class="px-2 py-1 text-xs rounded bg-blue-100 text-blue-700">${job.gap_type || 'search'}</span>
                  </td>
                  <td class="px-4 py-3">
                    <span class="px-2 py-1 text-xs rounded ${job.resolved ? 'bg-green-100 text-green-700' : 'bg-yellow-100 text-yellow-700'}">
                      ${job.resolved ? '已完成' : '待处理'}
                    </span>
                  </td>
                  <td class="px-4 py-3">
                    <div class="flex gap-1">
                      ${!job.resolved ? `
                        <button onclick="KbAutoSearchPage.executeSearch('${job.gap_id || job.id}')" class="px-2 py-1 text-xs text-green-600 hover:bg-green-50 rounded">执行搜索</button>
                      ` : ''}
                    </div>
                  </td>
                </tr>
              `).join('')}
            </tbody>
          </table>
        </div>
      `;
    },

    showCreateModal() {
      ModalDialog.show({
        title: '新建自动搜索任务',
        content: `
          <div class="space-y-4">
            <div>
              <label class="block text-sm font-medium mb-1">搜索查询 <span class="text-red-500">*</span></label>
              <input id="search-query" class="w-full border rounded px-3 py-2" placeholder="输入搜索关键词..." />
            </div>
            <div>
              <label class="block text-sm font-medium mb-1">分类</label>
              <input id="search-category" class="w-full border rounded px-3 py-2" placeholder="知识分类（可选）" />
            </div>
            <div>
              <label class="block text-sm font-medium mb-1">相关章节</label>
              <input type="number" id="search-chapter" class="w-full border rounded px-3 py-2" placeholder="章节号（可选）" />
            </div>
          </div>`,
        onConfirm: async () => {
          const query = document.getElementById('search-query').value.trim();
          const category_slug = document.getElementById('search-category').value.trim() || undefined;
          const chapter_no = parseInt(document.getElementById('search-chapter').value) || undefined;
          
          if (!query) { alert('请输入搜索查询'); return; }
          
          try {
            const projectId = window.AppState.currentProjectId || window.AppState.currentProject || '';
            await window.ApiClient.callTool('kb.auto.search', {
              query,
              category_slug,
              chapter_no,
              workspace: window.AppState.currentWorkspace, project: window.AppState.currentProject
            });
            ModalDialog.close();
            alert('搜索任务已创建，系统会自动搜索并整理结果');
            await KbAutoSearchPage.loadData();
          } catch (e) { alert('创建失败: ' + e.message); }
        }
      });
    },

    async executeSearch(gapId) {
      try {
        // This would trigger the actual web search and store results
        alert('执行搜索功能需要配置外部搜索API');
      } catch (e) {
        alert('执行失败: ' + e.message);
      }
    },

    loadData() {
      this.loadData();
    }
  };
})();
