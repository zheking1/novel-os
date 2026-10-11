/**
 * Knowledge Expiry Page
 * Shows expiring knowledge items (uses gap detection)
 */
(function() {
  window.KnowledgeExpiryPage = {
    async init() {
      const contentArea = document.getElementById('content-area');
      contentArea.innerHTML = `
        <div class="flex items-center justify-between mb-6">
          <h1 class="text-2xl font-bold text-gray-800">${window.t('nav.knowledgeExpiry') || '知识缺口'}</h1>
          <button onclick="KnowledgeExpiryPage.loadData()" class="px-4 py-2 bg-gray-100 text-gray-700 rounded-lg hover:bg-gray-200 text-sm">🔄 刷新</button>
        </div>
        <div id="expiry-content" class="bg-white rounded-lg shadow">
          <div class="p-8 text-center text-gray-500">加载中...</div>
        </div>
      `;
      await this.loadData();
      return true;
    },

    async loadData() {
      const container = document.getElementById('expiry-content');
      try {
        // kb.gap.list 的 workspace / project 是必填参数
        const ws = window.AppState && window.AppState.currentWorkspace;
        const prj = window.AppState && window.AppState.currentProject;
        const gaps = await window.ApiClient.callTool('kb.gap.list', { workspace: ws, project: prj }).catch(() => []);
        const list = Array.isArray(gaps) ? gaps : (gaps?.gaps || []);
        if (!list || list.length === 0) {
          container.innerHTML = `<div class="p-8 text-center text-gray-500">暂无知识缺口 🎉</div>`;
          return;
        }
        container.innerHTML = `
          <div class="overflow-x-auto">
            <table class="w-full text-sm">
              <thead class="bg-gray-50">
                <tr>
                  <th class="px-4 py-3 text-left font-medium text-gray-600">描述</th>
                  <th class="px-4 py-3 text-left font-medium text-gray-600">类型</th>
                  <th class="px-4 py-3 text-left font-medium text-gray-600">实体</th>
                  <th class="px-4 py-3 text-left font-medium text-gray-600">状态</th>
                </tr>
              </thead>
              <tbody class="divide-y divide-gray-100">
                ${list.map(item => `
                  <tr class="hover:bg-gray-50">
                    <td class="px-4 py-3 text-gray-800">${item.description || '-'}</td>
                    <td class="px-4 py-3 text-gray-500">${item.gap_type || '-'}</td>
                    <td class="px-4 py-3 text-gray-600">${item.entity_name || '-'}</td>
                    <td class="px-4 py-3"><span class="px-2 py-1 text-xs rounded ${item.resolved ? 'bg-green-100 text-green-700' : 'bg-orange-100 text-orange-700'}">${item.resolved ? '已解决' : '待解决'}</span></td>
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
