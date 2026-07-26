/**
 * Sync Conflicts Page
 * Shows and resolves sync conflicts
 */
(function() {
  window.SyncConflictsPage = {
    async init() {
      const contentArea = document.getElementById('content-area');
      contentArea.innerHTML = `
        <div class="flex items-center justify-between mb-6">
          <h1 class="text-2xl font-bold text-gray-800">${window.t('nav.syncConflicts') || '同步冲突'}</h1>
          <button onclick="SyncConflictsPage.loadData()" class="px-4 py-2 bg-gray-100 text-gray-700 rounded-lg hover:bg-gray-200 text-sm">🔄 刷新</button>
        </div>
        <div id="conflicts-content" class="bg-white rounded-lg shadow">
          <div class="p-8 text-center text-gray-500">加载中...</div>
        </div>
      `;
      await this.loadData();
      return true;
    },

    async loadData() {
      const container = document.getElementById('conflicts-content');
      try {
        const ws = window.AppState.currentWorkspace;
        const proj = window.AppState.currentProject;
        const args = {};
        if (ws) args.workspace = ws;
        if (proj) args.project = proj;
        const result = await window.ApiClient.callTool('sync.list_conflicts', args).catch(() => []);
        const conflicts = Array.isArray(result) ? result : (result?.conflicts || []);
        if (!conflicts || conflicts.length === 0) {
          container.innerHTML = `<div class="p-8 text-center text-gray-500">暂无冲突 🎉</div>`;
          return;
        }
        container.innerHTML = `
          <div class="divide-y divide-gray-100">
            ${conflicts.map(c => `
              <div class="p-4">
                <div class="flex items-center justify-between">
                  <div>
                    <div class="font-medium text-gray-800">${c.file_path || c.file}</div>
                    <div class="text-sm text-gray-500 mt-1">冲突类型: ${c.conflict_type || '未知'}</div>
                    <div class="text-xs text-gray-400 mt-1">修改时间: ${c.modified_at || '-'}</div>
                  </div>
                  <div class="flex gap-2">
                    <button onclick="SyncConflictsPage.resolve('${c.id}', 'client')" class="px-3 py-1 bg-blue-100 text-blue-700 rounded text-xs">保留本地</button>
                    <button onclick="SyncConflictsPage.resolve('${c.id}', 'server')" class="px-3 py-1 bg-green-100 text-green-700 rounded text-xs">保留远程</button>
                  </div>
                </div>
              </div>
            `).join('')}
          </div>`;
      } catch (e) {
        container.innerHTML = `<div class="p-8 text-center text-red-500">加载失败: ${e.message}</div>`;
      }
    },

    async resolve(id, action) {
      try {
        const ws = window.AppState.currentWorkspace;
        const proj = window.AppState.currentProject;
        const args = { conflict: { id }, action };
        if (ws) args.workspace = ws;
        if (proj) args.project = proj;
        await window.ApiClient.callTool('sync.resolve_conflict', args);
        await this.loadData();
      } catch (e) { alert('解决失败: ' + e.message); }
    }
  };
})();
