/**
 * Model Routes Page
 * 模型路由规则 - 配置不同任务类型的模型路由
 */
(function() {
  window.ModelRoutesPage = {
    rules: [],
    profiles: [],

    async init() {
      const contentArea = document.getElementById('content-area');
      contentArea.innerHTML = `
        <div class="flex items-center justify-between mb-6">
          <h1 class="text-2xl font-bold text-gray-800">${window.t('nav.modelRoutes') || '模型路由规则'}</h1>
          <div class="flex gap-2">
            <button onclick="ModelRoutesPage.showCreateModal()" class="px-4 py-2 bg-primary-600 text-white rounded-lg hover:bg-primary-700 text-sm">➕ 新建规则</button>
            <button onclick="ModelRoutesPage.loadData()" class="px-4 py-2 bg-gray-100 text-gray-700 rounded-lg hover:bg-gray-200 text-sm">🔄 刷新</button>
          </div>
        </div>
        <div id="routes-content" class="bg-white rounded-lg shadow">
          <div class="p-8 text-center text-gray-500">加载中...</div>
        </div>
      `;
      await this.loadData();
      return true;
    },

    async loadData() {
      const container = document.getElementById('routes-content');
      try {
        const workspace = window.AppState.currentWorkspace || '';
        const project = window.AppState.currentProject || '';
        
        // Load both rules and profiles
        const [rulesResult, profilesResult] = await Promise.all([
          window.ApiClient.callTool('model.route_rule.list', { workspace, project }).catch(() => []),
          window.ApiClient.callTool('model.profile.list').catch(() => [])
        ]);
        
        this.rules = Array.isArray(rulesResult) ? rulesResult : (rulesResult?.rules || rulesResult?.result || []);
        this.profiles = Array.isArray(profilesResult) ? profilesResult : (profilesResult?.profiles || profilesResult?.result || []);
        
        this.renderRules();
      } catch (e) {
        container.innerHTML = `<div class="p-8 text-center text-red-500">加载失败: ${e.message}</div>`;
      }
    },

    renderRules() {
      const container = document.getElementById('routes-content');
      
      if (!this.rules || this.rules.length === 0) {
        container.innerHTML = `<div class="p-8 text-center text-gray-500">暂无路由规则</div>`;
        return;
      }

      // Sort by priority (higher first)
      const sortedRules = [...this.rules].sort((a, b) => (b.priority || 0) - (a.priority || 0));

      container.innerHTML = `
        <div class="overflow-x-auto">
          <table class="w-full text-sm">
            <thead class="bg-gray-50">
              <tr>
                <th class="px-4 py-3 text-left font-medium text-gray-600">优先级</th>
                <th class="px-4 py-3 text-left font-medium text-gray-600">任务类型</th>
                <th class="px-4 py-3 text-left font-medium text-gray-600">模型配置</th>
                <th class="px-4 py-3 text-left font-medium text-gray-600">条件</th>
                <th class="px-4 py-3 text-left font-medium text-gray-600">状态</th>
              </tr>
            </thead>
            <tbody class="divide-y divide-gray-100">
              ${sortedRules.map(r => {
                const profile = this.profiles.find(p => p.profile_key === r.profile_key);
                return `
                  <tr class="hover:bg-gray-50">
                    <td class="px-4 py-3 font-medium">${r.priority || 100}</td>
                    <td class="px-4 py-3">
                      <span class="px-2 py-1 bg-blue-100 text-blue-700 rounded text-xs">${r.task_type}</span>
                    </td>
                    <td class="px-4 py-3">
                      <div class="font-medium">${r.profile_key}</div>
                      ${profile ? `<div class="text-xs text-gray-500">${profile.display_name || ''}</div>` : ''}
                    </td>
                    <td class="px-4 py-3 text-gray-600">
                      ${r.conditions && Object.keys(r.conditions).length > 0 
                        ? `<pre class="text-xs bg-gray-50 p-1 rounded">${JSON.stringify(r.conditions, null, 2)}</pre>`
                        : '-'}
                    </td>
                    <td class="px-4 py-3">
                      <span class="px-2 py-1 text-xs rounded ${r.status === 'active' ? 'bg-green-100 text-green-700' : 'bg-gray-100 text-gray-500'}">
                        ${r.status === 'active' ? '启用' : '禁用'}
                      </span>
                    </td>
                  </tr>
                `;
              }).join('')}
            </tbody>
          </table>
        </div>
      `;
    },

    showCreateModal() {
      if (this.profiles.length === 0) {
        alert('请先创建模型配置');
        return;
      }

      ModalDialog.show({
        title: '新建路由规则',
        content: `
          <div class="space-y-4">
            <div>
              <label class="block text-sm font-medium mb-1">任务类型 <span class="text-red-500">*</span></label>
              <select id="route-task-type" class="w-full border rounded px-3 py-2">
                <option value="outline">大纲生成</option>
                <option value="draft">初稿生成</option>
                <option value="polish">润色</option>
                <option value="review">审核</option>
                <option value="embedding">Embedding</option>
                <option value="rerank">Rerank</option>
              </select>
            </div>
            <div>
              <label class="block text-sm font-medium mb-1">模型配置 <span class="text-red-500">*</span></label>
              <select id="route-profile" class="w-full border rounded px-3 py-2">
                ${this.profiles.map(p => `<option value="${p.profile_key}">${p.display_name || p.profile_key}</option>`).join('')}
              </select>
            </div>
            <div>
              <label class="block text-sm font-medium mb-1">优先级 (1-999)</label>
              <input type="number" id="route-priority" class="w-full border rounded px-3 py-2" value="100" min="1" max="999" />
              <p class="text-xs text-gray-500 mt-1">数值越大优先级越高</p>
            </div>
          </div>`,
        onConfirm: async () => {
          const task_type = document.getElementById('route-task-type').value;
          const profile_key = document.getElementById('route-profile').value;
          const priority = parseInt(document.getElementById('route-priority').value) || 100;
          
          if (!task_type || !profile_key) { alert('请填写所有必填项'); return; }
          
          try {
            const workspace = window.AppState.currentWorkspace || '';
            const project = window.AppState.currentProject || '';
            await window.ApiClient.callTool('model.route_rule.upsert', {
              workspace, project, task_type, profile_key, priority
            });
            ModalDialog.close();
            await ModelRoutesPage.loadData();
          } catch (e) { alert('创建失败: ' + e.message); }
        }
      });
    },

    };
})();
