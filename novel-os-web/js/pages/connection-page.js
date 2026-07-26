/**
 * Connection Page
 * Shows server connection status
 */
(function() {
  window.ConnectionPage = {
    async init() {
      const contentArea = document.getElementById('content-area');
      contentArea.innerHTML = `
        <div class="flex items-center justify-between mb-6">
          <h1 class="text-2xl font-bold text-gray-800">${window.t('nav.connection') || '连接状态'}</h1>
          <button onclick="ConnectionPage.loadData()" class="px-4 py-2 bg-primary-600 text-white rounded-lg hover:bg-primary-700 text-sm">🔍 检测连接</button>
        </div>
        <div id="conn-content" class="space-y-6"></div>
      `;
      await this.loadData();
      return true;
    },

    async loadData() {
      const container = document.getElementById('conn-content');
      try {
        const health = await window.ApiClient.callTool('admin.health').catch(() => ({}));
        const dbOk = health.database === 'ok' || health.db_connected === true;
        const mcpOk = health.mcp === 'ok' || health.mcp_connected === true;
        container.innerHTML = `
          <div class="bg-white rounded-lg shadow p-6">
            <div class="flex items-center gap-4 mb-6">
              <div class="w-16 h-16 rounded-full flex items-center justify-center ${health.status === 'ok' || health.healthy ? 'bg-green-100' : 'bg-red-100'}">
                <span class="text-3xl">${health.status === 'ok' || health.healthy ? '✅' : '❌'}</span>
              </div>
              <div>
                <h2 class="text-xl font-bold text-gray-800">${health.status === 'ok' || health.healthy ? '连接正常' : '连接异常'}</h2>
                <p class="text-gray-500">服务器响应时间: ${health.latency != null ? health.latency : '-'}ms</p>
              </div>
            </div>
            <div class="grid grid-cols-1 md:grid-cols-3 gap-4">
              <div class="p-4 bg-gray-50 rounded-lg">
                <div class="text-sm text-gray-500">数据库</div>
                <div class="font-medium ${dbOk ? 'text-green-600' : 'text-red-600'}">${dbOk ? '正常' : '异常'}</div>
              </div>
              <div class="p-4 bg-gray-50 rounded-lg">
                <div class="text-sm text-gray-500">MCP 服务</div>
                <div class="font-medium ${mcpOk ? 'text-green-600' : 'text-red-600'}">${mcpOk ? '正常' : '异常'}</div>
              </div>
              <div class="p-4 bg-gray-50 rounded-lg">
                <div class="text-sm text-gray-500">向量数据库</div>
                <div class="font-medium ${health.qdrant === 'ok' ? 'text-green-600' : 'text-red-600'}">${health.qdrant === 'ok' ? '正常' : '异常'}</div>
              </div>
            </div>
          </div>`;
      } catch (e) {
        container.innerHTML = `<div class="bg-white rounded-lg shadow p-8 text-center text-red-500">连接失败: ${e.message}</div>`;
      }
    }
  };
})();
