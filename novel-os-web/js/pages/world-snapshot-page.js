/**
 * World Snapshot Page
 * 世界观快照 - 查看和管理世界状态快照
 */
(function() {
  window.WorldSnapshotPage = {
    async init() {
      const contentArea = document.getElementById('content-area');
      contentArea.innerHTML = `
        <div class="flex items-center justify-between mb-6">
          <h1 class="text-2xl font-bold text-gray-800">${window.t('nav.worldSnapshot') || '世界观快照'}</h1>
          <button onclick="WorldSnapshotPage.loadData()" class="px-4 py-2 bg-gray-100 text-gray-700 rounded-lg hover:bg-gray-200 text-sm">🔄 刷新</button>
        </div>
        <div id="snapshot-content" class="bg-white rounded-lg shadow">
          <div class="p-8 text-center text-gray-500">加载中...</div>
        </div>`;
      await this.loadData();
      return true;
    },

    async loadData() {
      const container = document.getElementById('snapshot-content');
      try {
        const pid = window.AppState.currentProjectId || window.AppState.currentProject;
        if (!pid) { container.innerHTML = '<div class="p-8 text-center text-gray-500">请先选择项目</div>'; return; }
        
        const [worldList, entities] = await Promise.all([
          window.ApiClient.callTool('kb.world.list', { workspace: window.AppState.currentWorkspace, project: window.AppState.currentProject }).catch(() => []),
          window.ApiClient.callTool('state.entity.list', { workspace: window.AppState.currentWorkspace || '', project: window.AppState.currentProject || '', limit: 50 }).catch(() => [])
        ]);

        const snapshots = worldList && worldList.data ? worldList.data : (Array.isArray(worldList) ? worldList : (worldList?.result || []));
        const entityList = Array.isArray(entities) ? entities : (entities?.result || []);

        container.innerHTML = snapshots.length === 0 ? '<div class="p-8 text-center text-gray-500">暂无世界状态快照</div>' : `
          <div class="p-4 space-y-4">
            ${snapshots.map(s => `
              <div class="border rounded-lg p-4">
                <div class="flex justify-between items-start mb-2">
                  <h3 class="font-semibold">第${s.chapter_no}章快照</h3>
                  <span class="text-xs text-gray-500">${s.story_time || '-'}</span>
                </div>
                <div class="grid grid-cols-2 md:grid-cols-4 gap-3 text-sm">
                  <div class="bg-gray-50 p-2 rounded"><span class="text-gray-500">时代:</span> ${s.story_era || '-'}</div>
                  <div class="bg-gray-50 p-2 rounded"><span class="text-gray-500">年份:</span> ${s.story_year || '-'}</div>
                  <div class="bg-gray-50 p-2 rounded"><span class="text-gray-500">角色数:</span> ${s.character_count || '-'}</div>
                  <div class="bg-gray-50 p-2 rounded"><span class="text-gray-500">进度:</span> ${s.story_progress ? (s.story_progress*100).toFixed(0)+'%' : '-'}</div>
                </div>
                ${s.active_threads ? `<div class="mt-2 flex flex-wrap gap-1">${s.active_threads.map(t => `<span class="px-2 py-0.5 bg-blue-100 text-blue-700 rounded text-xs">${t}</span>`).join('')}</div>` : ''}
              </div>`).join('')}
          </div>`;

        container.innerHTML += `<div class="p-4 border-t"><h3 class="font-semibold mb-2">活跃实体 (${entityList.length})</h3>
          <div class="flex flex-wrap gap-2">${entityList.map(e => `<span class="px-2 py-1 bg-gray-100 rounded text-xs">${e.name} <span class="text-gray-400">${e.entity_type}</span></span>`).join('')}</div></div>`;
      } catch(e) {
        container.innerHTML = `<div class="p-8 text-center text-red-500">${e.message}</div>`;
      }
    },

  };
})();