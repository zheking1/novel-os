/**
 * Knowledge Graph Viewer
 * Visualizes entity relationships
 */
(function() {
  window.KnowledgeGraphPage = {
    async init() {
      const contentArea = document.getElementById('content-area');
      contentArea.innerHTML = `
        <div class="flex items-center justify-between mb-6">
          <h1 class="text-2xl font-bold text-gray-800">${window.t('nav.knowledgeGraph') || '知识图谱'}</h1>
          <div class="flex gap-2">
            <select id="graph-entity-type" class="border rounded px-3 py-2 text-sm">
              <option value="">全部类型</option>
              <option value="person">人物</option>
              <option value="location">地点</option>
              <option value="event">事件</option>
              <option value="faction">势力</option>
              <option value="concept">概念</option>
            </select>
            <button onclick="KnowledgeGraphPage.loadData()" class="px-4 py-2 bg-gray-100 text-gray-700 rounded-lg hover:bg-gray-200 text-sm">🔄 刷新</button>
          </div>
        </div>
        <div class="grid grid-cols-1 lg:grid-cols-4 gap-6">
          <div class="lg:col-span-3 bg-white rounded-lg shadow p-6">
            <div id="graph-canvas" class="w-full h-96 bg-gray-50 rounded border flex items-center justify-center text-gray-400">
              图谱可视化区域
            </div>
          </div>
          <div class="bg-white rounded-lg shadow p-4">
            <h3 class="font-semibold text-gray-700 mb-3">实体列表</h3>
            <div id="graph-entities" class="space-y-2 max-h-96 overflow-y-auto text-sm"></div>
          </div>
        </div>
      `;
      await this.loadData();
    },

    async loadData() {
      const container = document.getElementById('graph-entities');
      try {
        const workspace = window.AppState.currentWorkspace;
        const project = window.AppState.currentProject;
        if (!workspace || !project) {
          container.innerHTML = '<div class="text-gray-500">请先选择工作空间和项目</div>';
          return;
        }
        const data = await window.ApiClient.graph.getData({ depth: 2 });
        if (!data || !data.nodes) {
          container.innerHTML = '<div class="text-gray-500">暂无图谱数据</div>';
          return;
        }
        container.innerHTML = data.nodes.map(n => `
          <div class="flex items-center gap-2 p-2 rounded hover:bg-gray-50 cursor-pointer" onclick="KnowledgeGraphPage.showEntity('${n.id}')">
            <span class="w-2 h-2 rounded-full bg-primary-500"></span>
            <span class="text-gray-700">${n.label || n.name}</span>
            <span class="text-xs text-gray-400 ml-auto">${n.type || ''}</span>
          </div>
        `).join('');
        
        // Simple text-based graph display
        const canvas = document.getElementById('graph-canvas');
        if (data.edges && data.edges.length > 0) {
          canvas.innerHTML = `<pre class="text-xs text-left overflow-auto p-4">${JSON.stringify(data.edges.slice(0, 20), null, 1)}</pre>`;
        }
      } catch (e) {
        container.innerHTML = `<div class="text-red-500">加载失败: ${e.message}</div>`;
      }
    },

    async showEntity(id) {
      try {
        const entity = await window.ApiClient.request(`/api/kb/entities/${id}`);
        window.ModalDialog.show({
          title: entity.name || '实体详情',
          content: `<pre class="text-sm bg-gray-50 p-4 rounded overflow-auto max-h-96">${JSON.stringify(entity, null, 2)}</pre>`,
          showCancel: false,
          confirmText: '关闭'
        });
      } catch (e) {
        alert('加载失败: ' + e.message);
      }
    }
  };
})();
