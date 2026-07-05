/**
 * Novel OS - Project World State Page
 * 项目世界状态页面
 */
(function() {
  'use strict';

  window.ProjectWorldStatePage = {
    init() {
      this.render();
      this.loadData();
      return true;
    },

    render() {
      const contentArea = document.getElementById('content-area');
      contentArea.innerHTML = `
        <div class="space-y-4">
          <div class="flex items-center justify-between">
            <div>
              <h1 class="text-2xl font-bold text-gray-800">${t('nav.worldState')}</h1>
              <p class="text-gray-500 mt-1">查看项目世界状态快照</p>
            </div>
            <button onclick="ProjectWorldStatePage.loadData()" 
                    class="px-4 py-2 bg-primary-600 text-white rounded-lg hover:bg-primary-700 transition-colors">
              ${t('common.refresh')}
            </button>
          </div>

          <div id="world-state-container" class="bg-white rounded-lg shadow">
            <div class="p-8 text-center text-gray-500">
              <div class="spinner w-8 h-8 border-4 border-primary-600 border-t-transparent rounded-full animate-spin mx-auto"></div>
              <p class="mt-2">${t('common.loading')}</p>
            </div>
          </div>
        </div>
      `;
    },

    async loadData() {
      const container = document.getElementById('world-state-container');
      try {
        const workspace = window.AppState.currentWorkspace;
        const project = window.AppState.currentProject;
        
        if (!workspace || !project) {
          container.innerHTML = `<div class="p-8 text-center text-gray-500">请先选择工作区和项目</div>`;
          return;
        }

        const result = await window.ApiClient.kb.world.get(project);
        
        if (!result) {
          container.innerHTML = `<div class="p-8 text-center text-gray-500">暂无世界状态数据</div>`;
          return;
        }

        container.innerHTML = `
          <div class="p-4 border-b border-gray-200">
            <h3 class="font-medium text-gray-800">世界状态快照</h3>
            <p class="text-sm text-gray-500 mt-1">章节: ${result.chapter_no || 'N/A'} | 更新时间: ${result.updated_at ? new Date(result.updated_at).toLocaleString() : 'N/A'}</p>
          </div>
          <div class="p-4">
            <pre class="text-sm text-gray-700 bg-gray-50 p-4 rounded-lg overflow-auto max-h-96">${JSON.stringify(result.world_state || result, null, 2)}</pre>
          </div>
        `;
      } catch (error) {
        console.error('[WorldState] Load error:', error);
        container.innerHTML = `<div class="p-8 text-center text-red-500">加载失败: ${error.message}</div>`;
      }
    }
  };
})();
