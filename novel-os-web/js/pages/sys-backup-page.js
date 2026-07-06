/**
 * System Backup Page
 * Shows backup status and management
 */
(function() {
  window.SysBackupPage = {
    async init() {
      const contentArea = document.getElementById('content-area');
      contentArea.innerHTML = `
        <div class="flex items-center justify-between mb-6">
          <h1 class="text-2xl font-bold text-gray-800">${window.t('nav.sysBackup') || '备份管理'}</h1>
          <div class="flex gap-2">
            <button onclick="SysBackupPage.createBackup()" class="px-4 py-2 bg-primary-600 text-white rounded-lg hover:bg-primary-700 text-sm">💾 立即备份</button>
            <button onclick="SysBackupPage.loadData()" class="px-4 py-2 bg-gray-100 text-gray-700 rounded-lg hover:bg-gray-200 text-sm">🔄 刷新</button>
          </div>
        </div>
        <div id="backup-content" class="space-y-6"></div>
      `;
      await this.loadData();
    },

    async loadData() {
      const container = document.getElementById('backup-content');
      try {
        const [backups, schedules] = await Promise.all([
          window.ApiClient.request('GET', '/backups').catch(() => []),
          window.ApiClient.request('GET', '/backups/schedules').catch(() => [])
        ]);
        container.innerHTML = `
          <div class="bg-white rounded-lg shadow p-6">
            <h3 class="font-semibold text-gray-700 mb-4">备份记录</h3>
            ${(!backups || backups.length === 0) ? '<div class="text-gray-500 text-sm">暂无备份</div>' : `
              <div class="overflow-x-auto">
                <table class="w-full text-sm">
                  <thead class="bg-gray-50">
                    <tr>
                      <th class="px-4 py-3 text-left font-medium text-gray-600">时间</th>
                      <th class="px-4 py-3 text-left font-medium text-gray-600">类型</th>
                      <th class="px-4 py-3 text-left font-medium text-gray-600">大小</th>
                      <th class="px-4 py-3 text-left font-medium text-gray-600">状态</th>
                    </tr>
                  </thead>
                  <tbody class="divide-y divide-gray-100">
                    ${(backups || []).map(b => `
                      <tr class="hover:bg-gray-50">
                        <td class="px-4 py-3 text-gray-500">${b.created_at || '-'}</td>
                        <td class="px-4 py-3 text-gray-600">${b.backup_type || 'incremental'}</td>
                        <td class="px-4 py-3 text-gray-600">${b.size || '-'}</td>
                        <td class="px-4 py-3"><span class="px-2 py-1 text-xs rounded ${b.status === 'completed' ? 'bg-green-100 text-green-700' : 'bg-yellow-100 text-yellow-700'}">${b.status || 'pending'}</span></td>
                      </tr>
                    `).join('')}
                  </tbody>
                </table>
              </div>
            `}
          </div>
          <div class="bg-white rounded-lg shadow p-6">
            <h3 class="font-semibold text-gray-700 mb-4">备份计划</h3>
            ${(!schedules || schedules.length === 0) ? '<div class="text-gray-500 text-sm">暂无备份计划</div>' : `
              <div class="space-y-3">
                ${(schedules || []).map(s => `
                  <div class="flex items-center justify-between p-3 bg-gray-50 rounded">
                    <div>
                      <div class="font-medium text-gray-800">${s.schedule_name || '默认计划'}</div>
                      <div class="text-sm text-gray-500">${s.schedule_type || 'daily'} | 保留: ${s.retention_count || 7} 份</div>
                    </div>
                    <span class="px-2 py-1 text-xs rounded ${s.enabled ? 'bg-green-100 text-green-700' : 'bg-gray-100 text-gray-500'}">${s.enabled ? '启用' : '禁用'}</span>
                  </div>
                `).join('')}
              </div>
            `}
          </div>`;
      } catch (e) {
        container.innerHTML = `<div class="bg-white rounded-lg shadow p-8 text-center text-red-500">加载失败: ${e.message}</div>`;
      }
    },

    async createBackup() {
      if (!confirm('确定创建备份？')) return;
      try {
        await window.ApiClient.request('POST', '/backups', { backup_type: 'manual' });
        alert('备份已创建');
        await this.loadData();
      } catch (e) { alert('创建失败: ' + e.message); }
    }
  };
})();
