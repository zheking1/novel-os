/**
 * Knowledge Stats Page
 * Shows knowledge base statistics
 */
(function() {
  window.KnowledgeStatsPage = {
    async init() {
      const contentArea = document.getElementById('content-area');
      contentArea.innerHTML = `
        <div class="flex items-center justify-between mb-6">
          <h1 class="text-2xl font-bold text-gray-800">${window.t('nav.knowledgeStats') || '知识统计'}</h1>
          <button onclick="KnowledgeStatsPage.loadData()" class="px-4 py-2 bg-gray-100 text-gray-700 rounded-lg hover:bg-gray-200 text-sm">🔄 刷新</button>
        </div>
        <div id="stats-content" class="space-y-6">
          <div class="text-center text-gray-500 py-8">加载中...</div>
        </div>
      `;
      await this.loadData();
    },

    async loadData() {
      const container = document.getElementById('stats-content');
      try {
        const [ukStats, catStats] = await Promise.all([
          window.ApiClient.kb.getUkStats().catch(() => null),
          window.ApiClient.kbCategories.list().catch(() => [])
        ]);

        let html = '<div class="grid grid-cols-1 md:grid-cols-3 gap-6">';
        
        // UK Stats
        if (ukStats) {
          html += `
            <div class="bg-white rounded-lg shadow p-6">
              <div class="text-3xl font-bold text-primary-600">${ukStats.total || 0}</div>
              <div class="text-gray-500 mt-1">通用知识条目</div>
            </div>`;
          if (ukStats.by_genre) {
            Object.entries(ukStats.by_genre).forEach(([genre, count]) => {
              html += `
                <div class="bg-white rounded-lg shadow p-6">
                  <div class="text-3xl font-bold text-green-600">${count}</div>
                  <div class="text-gray-500 mt-1">${genre}</div>
                </div>`;
            });
          }
        }

        // Category Stats
        if (catStats && catStats.length > 0) {
          html += `
            <div class="bg-white rounded-lg shadow p-6 md:col-span-3">
              <h3 class="font-semibold text-gray-700 mb-4">分类统计</h3>
              <div class="grid grid-cols-2 md:grid-cols-4 gap-4">
                ${catStats.map(c => `
                  <div class="text-center p-3 bg-gray-50 rounded">
                    <div class="text-xl font-bold text-gray-800">${c.item_count || 0}</div>
                    <div class="text-sm text-gray-500">${c.name}</div>
                  </div>
                `).join('')}
              </div>
            </div>`;
        }

        html += '</div>';
        container.innerHTML = html || '<div class="text-center text-gray-500 py-8">暂无统计数据</div>';
      } catch (e) {
        container.innerHTML = `<div class="text-center text-red-500 py-8">加载失败: ${e.message}</div>`;
      }
    }
  };
})();
