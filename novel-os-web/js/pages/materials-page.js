/**
 * Materials Page
 * 参考素材管理 - 管理参考文本、图片链接等
 */
(function() {
  window.MaterialsPage = {
    materials: [],

    async init() {
      const contentArea = document.getElementById('content-area');
      contentArea.innerHTML = `
        <div class="flex items-center justify-between mb-6">
          <h1 class="text-2xl font-bold text-gray-800">${window.t('nav.materials') || '参考素材'}</h1>
          <div class="flex gap-2">
            <button onclick="MaterialsPage.showCreateModal()" class="px-4 py-2 bg-primary-600 text-white rounded-lg hover:bg-primary-700 text-sm">➕ 添加素材</button>
            <button onclick="MaterialsPage.loadData()" class="px-4 py-2 bg-gray-100 text-gray-700 rounded-lg hover:bg-gray-200 text-sm">🔄 刷新</button>
          </div>
        </div>
        <div class="flex gap-4 mb-4">
          <input type="text" id="material-search" placeholder="搜索素材..." 
                 class="flex-1 px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary-500"
                 oninput="MaterialsPage.filterMaterials()">
          <select id="material-type-filter" class="px-4 py-2 border border-gray-300 rounded-lg" onchange="MaterialsPage.filterMaterials()">
            <option value="">全部类型</option>
            <option value="text">文本</option>
            <option value="image">图片</option>
            <option value="url">链接</option>
            <option value="document">文档</option>
          </select>
        </div>
        <div id="materials-content" class="bg-white rounded-lg shadow">
          <div class="p-8 text-center text-gray-500">加载中...</div>
        </div>
      `;
      await this.loadData();
      return true;
    },

    async loadData() {
      const container = document.getElementById('materials-content');
      try {
        const workspace = window.AppState.currentWorkspace || '';
        const project = window.AppState.currentProject || '';
        const result = await window.ApiClient.callTool('material.list', { workspace, project }).catch(() => []);
        this.materials = Array.isArray(result) ? result : (result?.materials || result?.result || []);
        this.renderMaterials();
      } catch (e) {
        container.innerHTML = `<div class="p-8 text-center text-red-500">加载失败: ${e.message}</div>`;
      }
    },

    renderMaterials() {
      const container = document.getElementById('materials-content');
      const searchTerm = document.getElementById('material-search')?.value?.toLowerCase() || '';
      const typeFilter = document.getElementById('material-type-filter')?.value || '';

      let filtered = this.materials;
      if (searchTerm) {
        filtered = filtered.filter(m => 
          (m.title || '').toLowerCase().includes(searchTerm) ||
          (m.material_key || '').toLowerCase().includes(searchTerm) ||
          (m.content || '').toLowerCase().includes(searchTerm)
        );
      }
      if (typeFilter) {
        filtered = filtered.filter(m => m.material_type === typeFilter);
      }

      if (!filtered || filtered.length === 0) {
        container.innerHTML = `<div class="p-8 text-center text-gray-500">暂无素材</div>`;
        return;
      }

      container.innerHTML = `
        <div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4 p-4">
          ${filtered.map(m => `
            <div class="border rounded-lg p-4 hover:shadow-md transition-shadow ${m.favorite ? 'bg-yellow-50 border-yellow-200' : 'bg-white'}">
              <div class="flex items-start justify-between mb-2">
                <div class="flex items-center gap-2">
                  <span class="text-lg">${this.getTypeIcon(m.material_type)}</span>
                  <span class="text-xs px-2 py-0.5 bg-gray-100 rounded">${m.material_type || 'text'}</span>
                </div>
                <button onclick="MaterialsPage.toggleFavorite('${m.material_key}')" 
                        class="text-lg ${m.favorite ? 'text-yellow-500' : 'text-gray-300'} hover:text-yellow-500">
                  ★
                </button>
              </div>
              <h3 class="font-semibold text-gray-800 mb-1">${m.title || '未命名'}</h3>
              <p class="text-xs text-gray-400 mb-2">${m.material_key}</p>
              <p class="text-sm text-gray-600 line-clamp-3 mb-3">${m.content || m.source_url || '无内容'}</p>
              <div class="flex gap-2">
                <button onclick="MaterialsPage.showEditModal('${m.material_key}')" class="px-3 py-1 text-xs bg-blue-100 text-blue-700 rounded hover:bg-blue-200">编辑</button>
                <button onclick="MaterialsPage.showDetailModal('${m.material_key}')" class="px-3 py-1 text-xs bg-gray-100 text-gray-700 rounded hover:bg-gray-200">详情</button>
              </div>
            </div>
          `).join('')}
        </div>
      `;
    },

    getTypeIcon(type) {
      const icons = {
        'text': '📝',
        'image': '🖼️',
        'url': '🔗',
        'document': '📄',
        'reference': '📚'
      };
      return icons[type] || '📄';
    },

    filterMaterials() {
      this.renderMaterials();
    },

    showCreateModal() {
      ModalDialog.show({
        title: '添加参考素材',
        size: 'lg',
        content: `
          <div class="space-y-4">
            <div>
              <label class="block text-sm font-medium mb-1">素材标识 <span class="text-red-500">*</span></label>
              <input id="new-mkey" class="w-full border rounded px-3 py-2" placeholder="英文+数字+下划线" />
            </div>
            <div>
              <label class="block text-sm font-medium mb-1">标题 <span class="text-red-500">*</span></label>
              <input id="new-title" class="w-full border rounded px-3 py-2" />
            </div>
            <div>
              <label class="block text-sm font-medium mb-1">类型 <span class="text-red-500">*</span></label>
              <select id="new-type" class="w-full border rounded px-3 py-2">
                <option value="text">文本</option>
                <option value="image">图片</option>
                <option value="url">链接</option>
                <option value="document">文档</option>
              </select>
            </div>
            <div>
              <label class="block text-sm font-medium mb-1">内容/URL</label>
              <textarea id="new-content" class="w-full border rounded px-3 py-2" rows="4" placeholder="素材内容或描述"></textarea>
            </div>
            <div>
              <label class="block text-sm font-medium mb-1">来源链接</label>
              <input id="new-url" class="w-full border rounded px-3 py-2" placeholder="https://..." />
            </div>
          </div>`,
        onConfirm: async () => {
          const material_key = document.getElementById('new-mkey').value.trim();
          const title = document.getElementById('new-title').value.trim();
          const material_type = document.getElementById('new-type').value;
          const content = document.getElementById('new-content').value.trim();
          const source_url = document.getElementById('new-url').value.trim();
          
          if (!material_key || !title) { alert('标识和标题不能为空'); return; }
          
          try {
            const workspace = window.AppState.currentWorkspace || '';
            const project = window.AppState.currentProject || '';
            await window.ApiClient.callTool('material.upsert', {
              workspace, project, material_key, title, material_type,
              content: content || undefined, source_url: source_url || undefined
            });
            ModalDialog.close();
            await MaterialsPage.loadData();
          } catch (e) { alert('添加失败: ' + e.message); }
        }
      });
    },

    async showEditModal(materialKey) {
      const material = this.materials.find(m => m.material_key === materialKey);
      if (!material) { alert('素材不存在'); return; }

      ModalDialog.show({
        title: `编辑素材: ${material.title}`,
        size: 'lg',
        content: `
          <div class="space-y-4">
            <div>
              <label class="block text-sm font-medium mb-1">标题 <span class="text-red-500">*</span></label>
              <input id="edit-title" class="w-full border rounded px-3 py-2" value="${material.title || ''}" />
            </div>
            <div>
              <label class="block text-sm font-medium mb-1">类型</label>
              <select id="edit-type" class="w-full border rounded px-3 py-2">
                <option value="text" ${material.material_type === 'text' ? 'selected' : ''}>文本</option>
                <option value="image" ${material.material_type === 'image' ? 'selected' : ''}>图片</option>
                <option value="url" ${material.material_type === 'url' ? 'selected' : ''}>链接</option>
                <option value="document" ${material.material_type === 'document' ? 'selected' : ''}>文档</option>
              </select>
            </div>
            <div>
              <label class="block text-sm font-medium mb-1">内容/URL</label>
              <textarea id="edit-content" class="w-full border rounded px-3 py-2" rows="4">${material.content || ''}</textarea>
            </div>
            <div>
              <label class="block text-sm font-medium mb-1">来源链接</label>
              <input id="edit-url" class="w-full border rounded px-3 py-2" value="${material.source_url || ''}" />
            </div>
          </div>`,
        onConfirm: async () => {
          const title = document.getElementById('edit-title').value.trim();
          const material_type = document.getElementById('edit-type').value;
          const content = document.getElementById('edit-content').value.trim();
          const source_url = document.getElementById('edit-url').value.trim();
          
          if (!title) { alert('标题不能为空'); return; }
          
          try {
            const workspace = window.AppState.currentWorkspace || '';
            const project = window.AppState.currentProject || '';
            await window.ApiClient.callTool('material.upsert', {
              workspace, project, material_key: materialKey, title, material_type,
              content: content || undefined, source_url: source_url || undefined
            });
            ModalDialog.close();
            await MaterialsPage.loadData();
          } catch (e) { alert('更新失败: ' + e.message); }
        }
      });
    },

    async showDetailModal(materialKey) {
      try {
        const workspace = window.AppState.currentWorkspace || '';
        const project = window.AppState.currentProject || '';
        const result = await window.ApiClient.callTool('material.get', {
          workspace, project, material_key: materialKey
        }).catch(() => null);
        
        const material = result || this.materials.find(m => m.material_key === materialKey);
        if (!material) { alert('素材不存在'); return; }

        ModalDialog.show({
          title: material.title || '素材详情',
          size: 'lg',
          content: `
            <div class="space-y-4">
              <div class="flex items-center gap-2">
                <span class="text-2xl">${this.getTypeIcon(material.material_type)}</span>
                <span class="px-2 py-1 bg-gray-100 rounded text-sm">${material.material_type || 'text'}</span>
                ${material.favorite ? '<span class="px-2 py-1 bg-yellow-100 text-yellow-700 rounded text-sm">⭐ 收藏</span>' : ''}
              </div>
              <div class="text-sm text-gray-500">标识: ${material.material_key}</div>
              ${material.content ? `
                <div class="bg-gray-50 p-4 rounded">
                  <h4 class="text-sm font-medium mb-2">内容</h4>
                  <pre class="text-sm text-gray-700 whitespace-pre-wrap">${material.content}</pre>
                </div>
              ` : ''}
              ${material.source_url ? `
                <div>
                  <h4 class="text-sm font-medium mb-1">来源链接</h4>
                  <a href="${material.source_url}" target="_blank" class="text-sm text-blue-600 hover:underline break-all">${material.source_url}</a>
                </div>
              ` : ''}
            </div>
          `,
          showFooter: false
        });
      } catch (e) {
        alert('加载详情失败: ' + e.message);
      }
    },

    async toggleFavorite(materialKey) {
      try {
        const workspace = window.AppState.currentWorkspace || '';
        const project = window.AppState.currentProject || '';
        await window.ApiClient.callTool('material.favorite', { workspace, project, material_key: materialKey });
        await MaterialsPage.loadData();
      } catch (e) {
        alert('操作失败: ' + e.message);
      }
    },

  };
})();
