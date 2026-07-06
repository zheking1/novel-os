/**
 * Knowledge Categories Manager
 * Lists all knowledge categories (tree structure)
 */
(function() {
  const PAGE_ID = 'kb-categories';
  
  window.KbCategoriesPage = {
    async init() {
      const contentArea = document.getElementById('content-area');
      contentArea.innerHTML = `
        <div class="flex items-center justify-between mb-6">
          <h1 class="text-2xl font-bold text-gray-800">${window.t('nav.knowledgeCategories') || '知识分类'}</h1>
          <div class="flex gap-2">
            <button onclick="KbCategoriesPage.refresh()" class="px-4 py-2 bg-gray-100 text-gray-700 rounded-lg hover:bg-gray-200 transition-colors text-sm">
              🔄 ${window.t('common.refresh') || '刷新'}
            </button>
            <button onclick="KbCategoriesPage.showCreateModal()" class="px-4 py-2 bg-primary-600 text-white rounded-lg hover:bg-primary-700 transition-colors text-sm">
              ➕ ${window.t('common.create') || '创建'}
            </button>
          </div>
        </div>
        <div id="kb-categories-content" class="bg-white rounded-lg shadow">
          <div class="p-8 text-center text-gray-500">${window.t('common.loading') || '加载中...'}</div>
        </div>
      `;
      await this.loadData();
    },

    async loadData() {
      const container = document.getElementById('kb-categories-content');
      try {
        const categories = await window.ApiClient.kbCategories.list();
        if (!categories || categories.length === 0) {
          container.innerHTML = `<div class="p-8 text-center text-gray-500">暂无分类数据</div>`;
          return;
        }
        container.innerHTML = this.renderTree(categories);
      } catch (e) {
        container.innerHTML = `<div class="p-8 text-center text-red-500">加载失败: ${e.message}</div>`;
      }
    },

    renderTree(categories) {
      const roots = categories.filter(c => !c.parent_id);
      const children = {};
      categories.forEach(c => {
        if (c.parent_id) {
          if (!children[c.parent_id]) children[c.parent_id] = [];
          children[c.parent_id].push(c);
        }
      });

      const renderNode = (cat, depth = 0) => {
        const kids = children[cat.id] || [];
        const hasKids = kids.length > 0;
        return `
          <div class="border-b border-gray-100 last:border-0" style="padding-left: ${depth * 24}px">
            <div class="flex items-center justify-between px-4 py-3 hover:bg-gray-50">
              <div class="flex items-center gap-2">
                <span class="text-gray-400">${hasKids ? '📂' : '📄'}</span>
                <span class="font-medium text-gray-800">${cat.name || cat.slug}</span>
                <span class="text-xs text-gray-400 ml-2">${cat.slug || ''}</span>
              </div>
              <div class="flex gap-1">
                <button onclick="KbCategoriesPage.showEditModal('${cat.id}')" class="px-2 py-1 text-xs text-gray-500 hover:bg-gray-200 rounded">编辑</button>
                <button onclick="KbCategoriesPage.deleteCategory('${cat.id}')" class="px-2 py-1 text-xs text-red-500 hover:bg-red-50 rounded">删除</button>
              </div>
            </div>
            ${kids.map(k => renderNode(k, depth + 1)).join('')}
          </div>`;
      };

      return `<div class="divide-y divide-gray-100">${roots.map(r => renderNode(r)).join('')}</div>`;
    },

    async deleteCategory(id) {
      if (!confirm('确定删除此分类？')) return;
      try {
        await window.ApiClient.request(`/api/kb/categories/${id}`, { method: 'DELETE' });
        await this.loadData();
      } catch (e) {
        alert('删除失败: ' + e.message);
      }
    },

    showCreateModal() {
      window.ModalDialog.show({
        title: '创建分类',
        content: `
          <div class="space-y-4">
            <div><label class="block text-sm font-medium mb-1">名称</label><input id="cat-name" class="w-full border rounded px-3 py-2" /></div>
            <div><label class="block text-sm font-medium mb-1">Slug</label><input id="cat-slug" class="w-full border rounded px-3 py-2" /></div>
            <div><label class="block text-sm font-medium mb-1">描述</label><textarea id="cat-desc" class="w-full border rounded px-3 py-2" rows="3"></textarea></div>
          </div>`,
        onConfirm: async () => {
          const name = document.getElementById('cat-name').value;
          const slug = document.getElementById('cat-slug').value;
          const description = document.getElementById('cat-desc').value;
          if (!name) { alert('名称不能为空'); return false; }
          await window.ApiClient.request('/api/kb/categories', { method: 'POST', body: { name, slug, description } });
          await this.loadData();
        }
      });
    },

    showEditModal(id) {
      window.ModalDialog.show({
        title: '编辑分类',
        content: `<div><label class="block text-sm font-medium mb-1">名称</label><input id="cat-name-edit" class="w-full border rounded px-3 py-2" /></div>`,
        onConfirm: async () => {
          const name = document.getElementById('cat-name-edit').value;
          await window.ApiClient.request(`/api/kb/categories/${id}`, { method: 'PUT', body: { name } });
          await this.loadData();
        }
      });
    },

    async refresh() { await this.loadData(); }
  };
})();
