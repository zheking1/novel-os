/**
 * Knowledge Expiry Page
 * Shows expiring knowledge items
 */
(function() {
  window.KnowledgeExpiryPage = {
    async init() {
      const contentArea = document.getElementById('content-area');
      contentArea.innerHTML = `
        <div class="flex items-center justify-between mb-6">
          <h1 class="text-2xl font-bold text-gray-800">${window.t('nav.knowledgeExpiry') || '知识过期'}</h1>
          <button onclick="KnowledgeExpiryPage.loadData()" class="px-4 py-2 bg-gray-100 text-gray-700 rounded-lg hover:bg-gray-200 text-sm">🔄 刷新</button>
        </div>
        <div id="expiry-content" class="bg-white rounded-lg shadow">
          <div class="p-8 text-center text-gray-500">加载中...</div>
        </div>
      `;
      await this.loadData();
    },

    async loadData() {
      const container = document.getElementById('expiry-content');
      try {
        const items = await window.ApiClient.request('GET', '/api/kb/expiring').catch(() => []);
        if (!items || items.length === 0) {
          container.innerHTML = `<div class="p-8 text-center text-gray-500">暂无即将过期的知识条目</div>`;
          return;
        }
        container.innerHTML = `
          <div class="overflow-x-auto">
            <table class="w-full text-sm">
              <thead class="bg-gray-50">
                <tr>
                  <th class="px-4 py-3 text-left font-medium text-gray-600">主题</th>
                  <th class="px-4 py-3 text-left font-medium text-gray-600">类型</th>
                  <th class="px-4 py-3 text-left font-medium text-gray-600">过期时间</th>
                  <th class="px-4 py-3 text-left font-medium text-gray-600">操作</th>
                </tr>
              </thead>
              <tbody class="divide-y divide-gray-100">
                ${items.map(item => `
                  <tr class="hover:bg-gray-50">
                    <td class="px-4 py-3 text-gray-800">${item.topic || item.title}</td>
                    <td class="px-4 py-3 text-gray-500">${item.type || '-'}</td>
                    <td class="px-4 py-3 text-orange-600">${item.expires_at || '-'}</td>
                    <td class="px-4 py-3">
                      <button onclick="KnowledgeExpiryPage.renew('${item.id}')" class="px-3 py-1 bg-primary-100 text-primary-700 rounded text-xs hover:bg-primary-200">续期</button>
                    </td>
                  </tr>
                `).join('')}
              </tbody>
            </table>
          </div>`;
      } catch (e) {
        container.innerHTML = `<div class="p-8 text-center text-red-500">加载失败: ${e.message}</div>`;
      }
    },

    async renew(id) {
      try {
        await window.ApiClient.request('POST', `/api/kb/items/${id}/renew`);
        await this.loadData();
      } catch (e) { alert('续期失败: ' + e.message); }
    }
  };
})();
