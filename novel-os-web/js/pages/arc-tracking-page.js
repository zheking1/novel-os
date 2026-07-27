/**
 * Arc Tracking Page
 * 弧光追踪 - 多角色弧光汇总对比
 */
(function() {
  window.ArcTrackingPage = {
    async init() {
      const contentArea = document.getElementById('content-area');
      contentArea.innerHTML = `
        <div class="flex items-center justify-between mb-6">
          <h1 class="text-2xl font-bold text-gray-800">${window.t('nav.arcTracking') || '弧光追踪'}</h1>
          <button onclick="ArcTrackingPage.loadData()" class="px-4 py-2 bg-gray-100 text-gray-700 rounded-lg hover:bg-gray-200 text-sm">🔄 刷新</button>
        </div>
        <div id="arc-tracking-content" class="bg-white rounded-lg shadow">
          <div class="p-8 text-center text-gray-500">加载中...</div>
        </div>`;
      await this.loadData();
      return true;
    },

    async loadData() {
      const container = document.getElementById('arc-tracking-content');
      try {
        const pid = window.AppState.currentProjectId || window.AppState.currentProject;
        const ws = window.AppState.currentWorkspace || '';
        const proj = window.AppState.currentProject || '';

        if (!pid) {
          container.innerHTML = '<div class="p-8 text-center text-gray-500">请先选择项目</div>';
          return;
        }

        // Load all characters and their latest arc states
        const entities = await window.ApiClient.callTool('state.entity.list', { workspace: ws, project: proj, entity_type: 'character', limit: 20 });
        const chars = entities && entities.data ? entities.data : (entities?.result || (Array.isArray(entities) ? entities : []));

        if (!chars.length) {
          container.innerHTML = '<div class="p-8 text-center text-gray-500">无角色数据</div>';
          return;
        }

        // Load arc summaries for all chars
        const arcPromises = chars.map(c => 
          window.ApiClient.callTool('arc.get_summary_for_context', { workspace: window.AppState.currentWorkspace, project: window.AppState.currentProject, project_id: pid, character_name: c.name, current_chapter: 999, max_tokens: 100 }).catch(() => null)
        );
        const arcs = await Promise.all(arcPromises);

        container.innerHTML = `
          <div class="p-4 grid gap-4">
            ${chars.map((c, i) => {
              const arc = arcs[i];
              return `
              <div class="border rounded-lg p-4">
                <h3 class="font-semibold">${c.name}</h3>
                <p class="text-sm text-gray-600 mt-1">${arc?.summary || arc?.content || '暂无弧光数据'}</p>
                ${arc?.emotion ? `<span class="inline-block mt-2 px-2 py-0.5 bg-yellow-100 text-yellow-700 rounded text-xs">😊 ${arc.emotion}</span>` : ''}
                ${arc?.power_level ? `<span class="inline-block mt-2 px-2 py-0.5 bg-green-100 text-green-700 rounded text-xs">⚡ ${arc.power_level}</span>` : ''}
              </div>`;
            }).join('')}
          </div>`;
      } catch(e) {
        container.innerHTML = `<div class="p-8 text-center text-red-500">${e.message}</div>`;
      }
    },

  };
})();