/**
 * System Cache Page
 * Shows cache statistics and management
 */
(function() {
  window.SysCachePage = {
    async init() {
      const contentArea = document.getElementById('content-area');
      contentArea.innerHTML = `
        <div class="flex items-center justify-between mb-6">
          <h1 class="text-2xl font-bold text-gray-800">${window.t('nav.sysCache') || '缓存管理'}</h1>
          <div class="flex gap-2">
            <button onclick="SysCachePage.warmCache()" class="px-4 py-2 bg-primary-600 text-white rounded-lg hover:bg-primary-700 text-sm">🔥 预热缓存</button>
            <button onclick="SysCachePage.loadData()" class="px-4 py-2 bg-gray-100 text-gray-700 rounded-lg hover:bg-gray-200 text-sm">🔄 刷新</button>
          </div>
        </div>
        <div id="cache-content" class="space-y-6"></div>
      `;
      await this.loadData();
    },

    async loadData() {
      const container = document.getElementById('cache-content');
      try {
        const [health, stats] = await Promise.all([
          window.ApiClient.request('GET', '/api/cache/health').catch(() => ({})),
          window.ApiClient.request('GET', '/api/cache/stats').catch(() => ({}))
        ]);
        container.innerHTML = `
          <div class="grid grid-cols-1 md:grid-cols-2 gap-6">
            <div class="bg-white rounded-lg shadow p-6">
              <h3 class="font-semibold text-gray-700 mb-4">Redis 状态</h3>
              <div class="flex items-center gap-2">
                <span class="w-3 h-3 rounded-full ${health.status === 'healthy' ? 'bg-green-500' : 'bg-red-500'}"></span>
                <span class="font-medium">${health.status === 'healthy' ? '健康' : '异常'}</span>
              </div>
              <div class="text-sm text-gray-500 mt-2">连接数: ${health.connections || 0}</div>
              <div class="text-sm text-gray-500 mt-1">内存: ${health.memory || '未知'}</div>
            </div>
            <div class="bg-white rounded-lg shadow p-6">
              <h3 class="font-semibold text-gray-700 mb-4">缓存统计</h3>
              <div class="text-sm text-gray-600">命中率: ${stats.hit_rate || '0%'}</div>
              <div class="text-sm text-gray-600 mt-2">键总数: ${stats.total_keys || 0}</div>
              <div class="text-sm text-gray-600 mt-2">内存使用: ${stats.memory_used || '未知'}</div>
            </div>
          </div>`;
      } catch (e) {
        container.innerHTML = `<div class="bg-white rounded-lg shadow p-8 text-center text-red-500">加载失败: ${e.message}</div>`;
      }
    },

    async warmCache() {
      try {
        await window.ApiClient.request('POST', '/api/cache/warm');
        alert('缓存预热已启动');
      } catch (e) { alert('操作失败: ' + e.message); }
    }
  };
})();
