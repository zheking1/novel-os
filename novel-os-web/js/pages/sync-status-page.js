/**
 * Sync Status Page
 * Shows synchronization status
 */
(function() {
  window.SyncStatusPage = {
    async init() {
      const contentArea = document.getElementById('content-area');
      contentArea.innerHTML = `
        <div class="flex items-center justify-between mb-6">
          <h1 class="text-2xl font-bold text-gray-800">${window.t('nav.syncStatus') || '同步状态'}</h1>
          <button onclick="SyncStatusPage.loadData()" class="px-4 py-2 bg-gray-100 text-gray-700 rounded-lg hover:bg-gray-200 text-sm">🔄 刷新</button>
        </div>
        <div id="sync-content" class="space-y-6"></div>
      `;
      await this.loadData();
      return true;
    },

    async loadData() {
      const container = document.getElementById('sync-content');
      try {
        const [conflicts, queueStats] = await Promise.all([
          window.ApiClient.callTool('sync.list_conflicts').catch(() => []),
          window.ApiClient.callTool('vector_index.queue_stats').catch(() => ({}))
        ]);
        const conflictList = Array.isArray(conflicts) ? conflicts : [];
        container.innerHTML = `
          <div class="grid grid-cols-1 md:grid-cols-2 gap-6">
            <div class="bg-white rounded-lg shadow p-6">
              <h3 class="font-semibold text-gray-700 mb-4">同步冲突</h3>
              <div class="text-sm text-gray-600">待解决冲突: <span class="font-medium ${conflictList.length > 0 ? 'text-orange-600' : 'text-green-600'}">${conflictList.length}</span></div>
            </div>
            <div class="bg-white rounded-lg shadow p-6">
              <h3 class="font-semibold text-gray-700 mb-4">向量索引队列</h3>
              <div class="text-sm text-gray-600">待处理: <span class="font-medium">${queueStats.pending || 0}</span></div>
              <div class="text-sm text-gray-600 mt-1">处理中: <span class="font-medium">${queueStats.processing || 0}</span></div>
            </div>
          </div>`;
      } catch (e) {
        container.innerHTML = `<div class="bg-white rounded-lg shadow p-8 text-center text-red-500">加载失败: ${e.message}</div>`;
      }
    }
  };
})();
