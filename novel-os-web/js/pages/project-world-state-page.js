/**
 * Novel OS - Project World State Page
 * 项目世界状态页面（结构化展示）
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
        <div class="max-w-5xl mx-auto space-y-4">
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

          <div id="world-state-content">
            <div id="world-state-meta" class="bg-white rounded-lg shadow p-4">
              <div class="animate-pulse h-4 bg-gray-200 rounded w-1/2"></div>
            </div>
            <div id="world-state-cards" class="grid grid-cols-2 gap-4 mt-4">
              <div class="animate-pulse h-24 bg-gray-200 rounded"></div>
              <div class="animate-pulse h-24 bg-gray-200 rounded"></div>
            </div>
          </div>
        </div>
      `;
    },

    async loadData() {
      try {
        const workspace = window.AppState.currentWorkspace;
        const project = window.AppState.currentProject;
        
        if (!workspace || !project) {
          document.getElementById('world-state-content').innerHTML = `<div class="p-8 text-center text-gray-500">请先选择工作区和项目</div>`;
          return;
        }
        
        const result = await window.ApiClient.callTool('kb.world.get', { workspace, project });
        
        if (!result) {
          document.getElementById('world-state-content').innerHTML = `<div class="p-8 text-center text-gray-500">暂无世界状态数据</div>`;
          return;
        }

        const ws = result.world_state || {};
        const ch = result.chapter_no || 'N/A';
        const time = result.updated_at ? new Date(result.updated_at).toLocaleString() : 'N/A';

        // Meta bar
        document.getElementById('world-state-meta').innerHTML = `
          <div class="flex items-center justify-between">
            <div>
              <h3 class="font-medium text-gray-800">世界状态快照</h3>
              <p class="text-sm text-gray-500 mt-1">章节: ${ch} | 更新时间: ${time} ${result.story_era ? '| 纪元: ' + result.story_era : ''} ${result.story_year ? '| 年份: ' + result.story_year : ''}</p>
            </div>
          </div>
        `;

        // Build structured cards from known fields
        const cards = [];

        if (ws.summary) cards.push({ icon: '📝', title: '世界概述', content: ws.summary, full: true });
        if (ws.active_locations?.length) cards.push({ icon: '📍', title: '活跃地点', content: ws.active_locations.join('、') });
        if (ws.faction_power) cards.push({ icon: '🏴', title: '势力格局', content: Object.entries(ws.faction_power).map(([k, v]) => `${k}: ${v}`).join('<br>') });
        if (ws.key_events?.length) cards.push({ icon: '📅', title: '关键事件', content: ws.key_events.join('<br>') });
        if (ws.story_time) cards.push({ icon: '⏰', title: '故事时间', content: ws.story_time });
        if (ws.political_climate) cards.push({ icon: '⚖️', title: '政治态势', content: ws.political_climate });
        if (ws.character_relationships) cards.push({ icon: '🔗', title: '角色关系', content: Object.entries(ws.character_relationships).map(([k, v]) => `${k}: ${v}`).join('<br>') });

        // If no structured fields, show raw JSON as fallback
        if (cards.length === 0) {
          document.getElementById('world-state-cards').innerHTML = `
            <div class="col-span-2 bg-white rounded-lg shadow p-4">
              <h3 class="font-medium text-gray-700 mb-2">原始数据</h3>
              <pre class="text-sm text-gray-600 bg-gray-50 p-3 rounded max-h-96 overflow-auto">${JSON.stringify(ws, null, 2)}</pre>
            </div>`;
          return;
        }

        document.getElementById('world-state-cards').innerHTML = cards.map(c => `
          <div class="${c.full ? 'col-span-2' : ''} bg-white rounded-lg shadow p-4">
            <h3 class="font-medium text-gray-700 mb-2">${c.icon} ${c.title}</h3>
            <div class="text-sm text-gray-600">${c.content}</div>
          </div>
        `).join('');
      } catch (error) {
        console.error('[WorldState] Load error:', error);
        document.getElementById('world-state-content').innerHTML = `<div class="p-8 text-center text-red-500">加载失败: ${error.message}</div>`;
      }
    }
  };
})();
