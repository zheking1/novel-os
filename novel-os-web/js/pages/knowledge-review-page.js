/**
 * Knowledge Review Page
 * Shows pending knowledge reviews
 */
(function() {
  window.KnowledgeReviewPage = {
    async init() {
      const contentArea = document.getElementById('content-area');
      contentArea.innerHTML = `
        <div class="flex items-center justify-between mb-6">
          <h1 class="text-2xl font-bold text-gray-800">${window.t('nav.knowledgeReview') || '知识审核'}</h1>
          <button onclick="KnowledgeReviewPage.loadData()" class="px-4 py-2 bg-gray-100 text-gray-700 rounded-lg hover:bg-gray-200 text-sm">🔄 刷新</button>
        </div>
        <div id="review-content" class="bg-white rounded-lg shadow">
          <div class="p-8 text-center text-gray-500">加载中...</div>
        </div>
      `;
      await this.loadData();
    },

    async loadData() {
      const container = document.getElementById('review-content');
      try {
        const reviews = await window.ApiClient.request('GET', '/api/kb/reviews').catch(() => []);
        if (!reviews || reviews.length === 0) {
          container.innerHTML = `<div class="p-8 text-center text-gray-500">暂无待审核内容</div>`;
          return;
        }
        container.innerHTML = `
          <div class="divide-y divide-gray-100">
            ${reviews.map(r => `
              <div class="p-4 hover:bg-gray-50">
                <div class="flex items-center justify-between">
                  <div>
                    <div class="font-medium text-gray-800">${r.title || r.topic}</div>
                    <div class="text-sm text-gray-500 mt-1">${r.summary || r.description || ''}</div>
                    <div class="text-xs text-gray-400 mt-1">提交人: ${r.submitter || '未知'} | 状态: ${r.status || 'pending'}</div>
                  </div>
                  <div class="flex gap-2">
                    <button onclick="KnowledgeReviewPage.approve('${r.id}')" class="px-3 py-1 bg-green-100 text-green-700 rounded text-sm hover:bg-green-200">通过</button>
                    <button onclick="KnowledgeReviewPage.reject('${r.id}')" class="px-3 py-1 bg-red-100 text-red-700 rounded text-sm hover:bg-red-200">拒绝</button>
                  </div>
                </div>
              </div>
            `).join('')}
          </div>`;
      } catch (e) {
        container.innerHTML = `<div class="p-8 text-center text-red-500">加载失败: ${e.message}</div>`;
      }
    },

    async approve(id) {
      try {
        await window.ApiClient.request('POST', `/api/kb/reviews/${id}/approve`);
        await this.loadData();
      } catch (e) { alert('操作失败: ' + e.message); }
    },

    async reject(id) {
      const comment = prompt('拒绝原因:');
      if (comment === null) return;
      try {
        await window.ApiClient.request('POST', `/api/kb/reviews/${id}/reject`, { comment });
        await this.loadData();
      } catch (e) { alert('操作失败: ' + e.message); }
    }
  };
})();
