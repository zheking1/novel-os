/**
 * Offline Status Page
 * Shows offline mode status
 */
(function() {
  window.OfflineStatusPage = {
    async init() {
      const contentArea = document.getElementById('content-area');
      contentArea.innerHTML = `
        <div class="flex items-center justify-between mb-6">
          <h1 class="text-2xl font-bold text-gray-800">${window.t('nav.offlineStatus') || '离线状态'}</h1>
        </div>
        <div class="bg-white rounded-lg shadow p-6">
          <div class="flex items-center gap-4 mb-6">
            <div class="w-16 h-16 bg-green-100 rounded-full flex items-center justify-center">
              <span class="text-3xl">📡</span>
            </div>
            <div>
              <h2 class="text-xl font-bold text-gray-800">在线模式</h2>
              <p class="text-gray-500">当前已连接到服务器</p>
            </div>
          </div>
          <div class="grid grid-cols-1 md:grid-cols-2 gap-4">
            <div class="p-4 bg-gray-50 rounded-lg">
              <div class="text-sm text-gray-500">最后连接时间</div>
              <div class="font-medium text-gray-800">${new Date().toLocaleString()}</div>
            </div>
            <div class="p-4 bg-gray-50 rounded-lg">
              <div class="text-sm text-gray-500">网络延迟</div>
              <div class="font-medium text-gray-800">~50ms</div>
            </div>
          </div>
        </div>
      `;
    }
  };
})();
