/**
 * Model Rate Limits Page
 * 模型速率限制 - 配置模型调用频率限制
 */
(function() {
  window.ModelRateLimitsPage = {
    profiles: [],

    async init() {
      const contentArea = document.getElementById('content-area');
      contentArea.innerHTML = `
        <div class="flex items-center justify-between mb-6">
          <h1 class="text-2xl font-bold text-gray-800">${window.t('nav.modelRateLimits') || '模型速率限制'}</h1>
          <div class="flex gap-2">
            <button onclick="ModelRateLimitsPage.loadData()" class="px-4 py-2 bg-gray-100 text-gray-700 rounded-lg hover:bg-gray-200 text-sm">🔄 刷新</button>
          </div>
        </div>
        <div id="rate-limits-content" class="bg-white rounded-lg shadow">
          <div class="p-8 text-center text-gray-500">加载中...</div>
        </div>
      `;
      await this.loadData();
      return true;
    },

    async loadData() {
      const container = document.getElementById('rate-limits-content');
      try {
        const workspace = window.AppState.currentWorkspace || '';
        const project = window.AppState.currentProject || '';
        const result = await window.ApiClient.callTool('model.profile.list').catch(() => []);
        this.profiles = Array.isArray(result) ? result : (result?.profiles || result?.result || []);
        this.renderRateLimits();
      } catch (e) {
        container.innerHTML = `<div class="p-8 text-center text-red-500">加载失败: ${e.message}</div>`;
      }
    },

    renderRateLimits() {
      const container = document.getElementById('rate-limits-content');
      
      if (!this.profiles || this.profiles.length === 0) {
        container.innerHTML = `<div class="p-8 text-center text-gray-500">暂无模型配置</div>`;
        return;
      }

      container.innerHTML = `
        <div class="space-y-4 p-4">
          ${this.profiles.map(p => {
            const rateLimit = p.rate_limit_config || {};
            return `
              <div class="border rounded-lg p-4 hover:shadow-md transition-shadow">
                <div class="flex items-center justify-between mb-3">
                  <div>
                    <h3 class="font-semibold text-gray-800">${p.display_name || p.profile_key}</h3>
                    <p class="text-xs text-gray-500">${p.provider} / ${p.model_name}</p>
                  </div>
                  <button onclick="ModelRateLimitsPage.showEditModal('${p.profile_key}')" class="px-3 py-1 text-xs bg-blue-100 text-blue-700 rounded hover:bg-blue-200">编辑限制</button>
                </div>
                <div class="grid grid-cols-3 gap-4 text-sm">
                  <div class="bg-gray-50 p-3 rounded">
                    <div class="text-gray-500 text-xs mb-1">每分钟请求</div>
                    <div class="font-medium">${rateLimit.requests_per_minute || '-'}</div>
                  </div>
                  <div class="bg-gray-50 p-3 rounded">
                    <div class="text-gray-500 text-xs mb-1">每分钟 Token</div>
                    <div class="font-medium">${rateLimit.tokens_per_minute ? this.formatNumber(rateLimit.tokens_per_minute) : '-'}</div>
                  </div>
                  <div class="bg-gray-50 p-3 rounded">
                    <div class="text-gray-500 text-xs mb-1">并发请求</div>
                    <div class="font-medium">${rateLimit.concurrent_requests || '-'}</div>
                  </div>
                </div>
              </div>
            `;
          }).join('')}
        </div>
      `;
    },

    formatNumber(num) {
      if (num >= 1000000) return (num / 1000000).toFixed(1) + 'M';
      if (num >= 1000) return (num / 1000).toFixed(1) + 'K';
      return num.toString();
    },

    showEditModal(profileKey) {
      const profile = this.profiles.find(p => p.profile_key === profileKey);
      if (!profile) { alert('配置不存在'); return; }

      const rateLimit = profile.rate_limit_config || {};

      ModalDialog.show({
        title: `编辑速率限制: ${profile.display_name || profileKey}`,
        content: `
          <div class="space-y-4">
            <div>
              <label class="block text-sm font-medium mb-1">每分钟请求数</label>
              <input type="number" id="limit-rpm" class="w-full border rounded px-3 py-2" value="${rateLimit.requests_per_minute || ''}" placeholder="例如: 60" />
            </div>
            <div>
              <label class="block text-sm font-medium mb-1">每分钟 Token 数</label>
              <input type="number" id="limit-tpm" class="w-full border rounded px-3 py-2" value="${rateLimit.tokens_per_minute || ''}" placeholder="例如: 100000" />
            </div>
            <div>
              <label class="block text-sm font-medium mb-1">并发请求数</label>
              <input type="number" id="limit-concurrent" class="w-full border rounded px-3 py-2" value="${rateLimit.concurrent_requests || ''}" placeholder="例如: 5" />
            </div>
          </div>`,
        onConfirm: async () => {
          const requests_per_minute = parseInt(document.getElementById('limit-rpm').value) || undefined;
          const tokens_per_minute = parseInt(document.getElementById('limit-tpm').value) || undefined;
          const concurrent_requests = parseInt(document.getElementById('limit-concurrent').value) || undefined;
          
          try {
            const workspace = window.AppState.currentWorkspace || '';
            const project = window.AppState.currentProject || '';
            
            // Update profile with new rate limit config
            await window.ApiClient.callTool('model.profile.upsert', {
              workspace, project,
              profile_key: profileKey,
              display_name: profile.display_name,
              provider: profile.provider,
              model_name: profile.model_name,
              rate_limit_config: {
                ...(requests_per_minute && { requests_per_minute }),
                ...(tokens_per_minute && { tokens_per_minute }),
                ...(concurrent_requests && { concurrent_requests })
              }
            });
            ModalDialog.close();
            await ModelRateLimitsPage.loadData();
          } catch (e) { alert('更新失败: ' + e.message); }
        }
      });
    },

    };
})();
