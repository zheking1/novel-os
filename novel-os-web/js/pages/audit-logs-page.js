/**
 * Audit Logs Page
 * Shows system audit logs
 */
(function() {
  window.AuditLogsPage = {
    async init() {
      const contentArea = document.getElementById('content-area');
      contentArea.innerHTML = `
        <div class="flex items-center justify-between mb-6">
          <h1 class="text-2xl font-bold text-gray-800">${window.t('nav.auditLogs') || '审计日志'}</h1>
          <button onclick="AuditLogsPage.loadData()" class="px-4 py-2 bg-gray-100 text-gray-700 rounded-lg hover:bg-gray-200 text-sm">🔄 刷新</button>
        </div>
        <div id="audit-content" class="bg-white rounded-lg shadow">
          <div class="p-8 text-center text-gray-500">加载中...</div>
        </div>
      `;
      await this.loadData();
    },

    async loadData() {
      const container = document.getElementById('audit-content');
      try {
        const logs = await window.ApiClient.request('GET', '/api/workflow/audit-logs?limit=50').catch(() => []);
        if (!logs || logs.length === 0) {
          container.innerHTML = `<div class="p-8 text-center text-gray-500">暂无审计日志</div>`;
          return;
        }
        container.innerHTML = `
          <div class="overflow-x-auto">
            <table class="w-full text-sm">
              <thead class="bg-gray-50">
                <tr>
                  <th class="px-4 py-3 text-left font-medium text-gray-600">时间</th>
                  <th class="px-4 py-3 text-left font-medium text-gray-600">操作</th>
                  <th class="px-4 py-3 text-left font-medium text-gray-600">资源</th>
                  <th class="px-4 py-3 text-left font-medium text-gray-600">用户</th>
                </tr>
              </thead>
              <tbody class="divide-y divide-gray-100">
                ${logs.map(l => `
                  <tr class="hover:bg-gray-50">
                    <td class="px-4 py-3 text-gray-500 text-xs">${l.created_at || l.timestamp || '-'}</td>
                    <td class="px-4 py-3 text-gray-800">${l.action || '-'}</td>
                    <td class="px-4 py-3 text-gray-600">${l.resource_type || ''} ${l.resource_id || ''}</td>
                    <td class="px-4 py-3 text-gray-500">${l.user_id || l.username || '-'}</td>
                  </tr>
                `).join('')}
              </tbody>
            </table>
          </div>`;
      } catch (e) {
        container.innerHTML = `<div class="p-8 text-center text-red-500">加载失败: ${e.message}</div>`;
      }
    }
  };
})();
