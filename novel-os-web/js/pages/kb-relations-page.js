/**
 * KB Relations Page
 * 实体关系管理 - 查看和管理知识库实体之间的关系
 */
(function() {
  window.KbRelationsPage = {

    async init() {
      const contentArea = document.getElementById('content-area');
      contentArea.innerHTML = `
        <div class="flex items-center justify-between mb-6">
          <h1 class="text-2xl font-bold text-gray-800">${window.t('nav.kbRelations') || '实体关系'}</h1>
          <div class="flex gap-2">
            <button onclick="KbRelationsPage.showCreateModal()" class="px-4 py-2 bg-primary-600 text-white rounded-lg hover:bg-primary-700 text-sm">➕ 新建关系</button>
            <button onclick="KbRelationsPage.loadData()" class="px-4 py-2 bg-gray-100 text-gray-700 rounded-lg hover:bg-gray-200 text-sm">🔄 刷新</button>
          </div>
        </div>
        <div class="bg-white rounded-lg shadow p-4 mb-4">
          <div class="flex gap-4">
            <input type="text" id="relation-search" placeholder="搜索实体名称..."
                   class="flex-1 px-4 py-2 border border-gray-300 rounded-lg"
                   onkeypress="if(event.key==='Enter')KbRelationsPage.searchEntity()">
            <button onclick="KbRelationsPage.searchEntity()" class="px-4 py-2 bg-primary-600 text-white rounded-lg">🔍 查找</button>
          </div>
        </div>
        <div id="relations-content" class="bg-white rounded-lg shadow">
          <div class="p-8 text-center text-gray-500">搜索实体以查看其关系</div>
        </div>
      `;
      return true;
    },

    async searchEntity() {
      const query = document.getElementById('relation-search').value.trim();
      if (!query) return;

      const container = document.getElementById('relations-content');
      container.innerHTML = '<div class="p-8 text-center text-gray-500">搜索中...</div>';

      try {
        // Search for entities matching query
        const entities = await window.ApiClient.callTool('kb.entity.search', { query, limit: 10 });
        const list = Array.isArray(entities) ? entities : (entities?.result || []);

        if (!list.length) {
          container.innerHTML = '<div class="p-8 text-center text-gray-500">未找到匹配实体</div>';
          return;
        }

        // Load relations for first entity
        const entity = list[0];
        const rels = await window.ApiClient.callTool('kb.entity.list_relations', { entity_id: entity.id });
        const relations = Array.isArray(rels) ? rels : (rels?.result || []);

        container.innerHTML = `
          <div class="p-4">
            <div class="mb-4">
              <h3 class="font-semibold">${entity.name}</h3>
              <span class="text-xs text-gray-500">${entity.entity_type || 'entity'}</span>
            </div>
            ${relations.length === 0 ? '<p class="text-gray-500">暂无关系</p>' : `
            <div class="space-y-2">
              ${relations.map(r => `
                <div class="flex items-center gap-3 p-3 bg-gray-50 rounded">
                  <span class="text-sm">${entity.name}</span>
                  <span class="px-2 py-0.5 bg-blue-100 text-blue-700 rounded text-xs">${r.relation_type || '-'}</span>
                  <span class="text-gray-400">→</span>
                  <span class="text-sm font-medium">${r.to_entity_name || r.to_entity_id || '-'}</span>
                  ${r.detail ? `<span class="text-xs text-gray-500">(${r.detail})</span>` : ''}
                </div>
              `).join('')}
            </div>`}
            ${list.length > 1 ? `<div class="mt-4 text-sm text-gray-500">其他匹配: ${list.slice(1).map(e => e.name).join(', ')}</div>` : ''}
          </div>`;
      } catch (e) {
        container.innerHTML = `<div class="p-8 text-center text-red-500">${e.message}</div>`;
      }
    },

    showCreateModal() {
      ModalDialog.show({
        title: '新建实体关系',
        content: `
          <div class="space-y-4">
            <div><label class="block text-sm font-medium mb-1">源实体ID <span class="text-red-500">*</span></label><input id="from-id" class="w-full border rounded px-3 py-2" /></div>
            <div><label class="block text-sm font-medium mb-1">目标实体ID <span class="text-red-500">*</span></label><input id="to-id" class="w-full border rounded px-3 py-2" /></div>
            <div><label class="block text-sm font-medium mb-1">关系类型 <span class="text-red-500">*</span></label><select id="rel-type" class="w-full border rounded px-3 py-2">
              <option value="related_to">相关于</option><option value="participated_in">参与</option><option value="located_at">位于</option><option value="belongs_to">属于</option><option value="caused_by">因</option><option value="same_as">等同于</option><option value="influenced_by">受影响</option>
            </select></div>
            <div><label class="block text-sm font-medium mb-1">详情</label><input id="rel-detail" class="w-full border rounded px-3 py-2" /></div>
          </div>`,
        onConfirm: async () => {
          const from_entity_id = document.getElementById('from-id').value.trim();
          const to_entity_id = document.getElementById('to-id').value.trim();
          const relation_type = document.getElementById('rel-type').value;
          const detail = document.getElementById('rel-detail').value.trim();
          if (!from_entity_id || !to_entity_id) { ModalDialog.alert('请填写实体ID'); return; }
          try {
            await window.ApiClient.callTool('kb.relation.create', { from_entity_id, to_entity_id, relation_type, detail: detail || undefined });
            ModalDialog.close();
          } catch (e) { ModalDialog.alert('创建失败: ' + e.message); }
        }
      });
    },

    loadData() {}
  };
})();