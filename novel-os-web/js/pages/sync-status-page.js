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
    },

    async loadData() {
      const container = document.getElementById('sync-content');
      try {
        const status = await window.ApiClient.request('GET', '/sync/status').catch(() => ({}));
        container.innerHTML = `
          <div class="grid grid-cols-1 md:grid-cols-2 gap-6">
            <div class="bg-white rounded-lg shadow p-6">
              <h3 class="font-semibold text-gray-700 mb-4">客户端绑定</h3>
              <div class="text-sm text-gray-600">状态: <span class="font-medium ${status.bound ? 'text-green-600' : 'text-orange-600'}">${status.bound ? '已绑定' : '未绑定'}</span></div>
              <div class="text-sm text-gray-600 mt-2">客户端ID: ${status.client_id || '未知'}</div>
              <div class="text-sm text-gray-600 mt-2">最后同步: ${status.last_sync || '从未'}</div>
            </div>
            <div class="bg-white rounded-lg shadow p-6">
              <h3 class="font-semibold text-gray-700 mb-4">同步统计</h3>
              <div class="text-sm text-gray-600">待同步文件: ${status.pending_files || 0}</div>
              <div class="text-sm text-gray-600 mt-2">冲突数: ${status.conflicts || 0}</div>
              <div class="text-sm text-gray-600 mt-2">同步方向: ${status.direction || '双向'}</div>
            </div>
          </div>`;
      } catch (e) {
        container.innerHTML = `<div class="bg-white rounded-lg shadow p-8 text-center text-red-500">加载失败: ${e.message}</div>`;
      }
    }
  };
})();
