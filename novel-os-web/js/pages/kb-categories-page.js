(function() {
  const PAGE_ID = 'kb-categories';

  window.KbCategoriesPage = {
    allCats: [],

    async init() {
      const contentArea = document.getElementById('content-area');
      contentArea.innerHTML = `
        <div class="flex items-center justify-between mb-6">
          <h1 class="text-2xl font-bold text-gray-800">知识分类</h1>
          <div class="flex gap-2">
            <button onclick="KbCategoriesPage.refresh()" class="px-4 py-2 bg-gray-100 text-gray-700 rounded-lg hover:bg-gray-200 text-sm">🔄 刷新</button>
            <button onclick="KbCategoriesPage.showCreateModal()" class="px-4 py-2 bg-primary-600 text-white rounded-lg hover:bg-primary-700 text-sm">➕ 创建</button>
          </div>
        </div>
        <div id="kb-categories-content" class="bg-white rounded-lg shadow">
          <div class="p-8 text-center text-gray-500">加载中...</div>
        </div>
      `;
      await this.loadData();
      return true;
    },

    async loadData() {
      const container = document.getElementById('kb-categories-content');
      try {
        const result = await window.ApiClient.callTool('kb.category.tree', {});
        this.allCats = Array.isArray(result) ? result : (result?.categories || []);
        if (!this.allCats.length) {
          container.innerHTML = '<div class="p-8 text-center text-gray-500">暂无分类数据</div>';
          return;
        }
        container.innerHTML = this.renderTree(this.allCats);
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
        const kids = children[cat.category_id || cat.id] || [];
        const hasKids = kids.length > 0;
        const entryCount = cat.entry_count || 0;
        const sid = cat.category_id || cat.id;
        return `
          <div style="padding-left: ${depth * 24}px" class="border-b border-gray-100 last:border-0">
            <div class="flex items-center justify-between px-4 py-3 hover:bg-gray-50">
              <div class="flex items-center gap-2 min-w-0">
                <span class="text-gray-400 shrink-0">${hasKids ? '📂' : '📄'}</span>
                <span class="font-medium text-gray-800 truncate">${this.esc(cat.name || cat.slug)}</span>
                <span class="text-xs text-gray-400 font-mono shrink-0">${this.esc(cat.slug || '')}</span>
                ${entryCount > 0 ? `<span class="text-xs bg-blue-100 text-blue-700 px-1.5 py-0.5 rounded-full shrink-0">${entryCount}</span>` : ''}
                ${cat.description ? `<span class="text-xs text-gray-400 truncate hidden lg:inline max-w-[200px]">— ${this.esc(cat.description)}</span>` : ''}
              </div>
              <div class="flex gap-1 shrink-0 ml-2">
                <button onclick="KbCategoriesPage.showEditModal('${sid}')" class="px-2 py-1 text-xs text-gray-500 hover:bg-gray-200 rounded" title="编辑">编辑</button>
                <button onclick="KbCategoriesPage.deleteCategory('${sid}')" class="px-2 py-1 text-xs text-red-500 hover:bg-red-50 rounded" title="删除">删除</button>
              </div>
            </div>
            ${kids.map(k => renderNode(k, depth + 1)).join('')}
          </div>`;
      };

      return `<div class="divide-y divide-gray-100">${roots.map(r => renderNode(r)).join('')}</div>`;
    },

    getParentOptions() {
      let html = '<option value="">— 顶级分类 —</option>';
      const addOpts = (cats, depth = 0) => {
        cats.forEach(c => {
          const indent = '  '.repeat(depth);
          html += `<option value="${c.category_id || c.id}">${indent}${this.esc(c.name || c.slug)}</option>`;
          const kids = this.allCats.filter(x => x.parent_id === (c.category_id || c.id));
          if (kids.length) addOpts(kids, depth + 1);
        });
      };
      addOpts(this.allCats.filter(c => !c.parent_id));
      return html;
    },

    showCreateModal() {
      window.ModalDialog.show({
        title: '创建分类',
        content: `
          <div class="space-y-4">
            <div><label class="block text-sm font-medium mb-1">名称 <span class="text-red-500">*</span></label><input id="cat-name" class="w-full border rounded px-3 py-2" /></div>
            <div><label class="block text-sm font-medium mb-1">标识符 (Slug)</label><input id="cat-slug" class="w-full border rounded px-3 py-2" placeholder="留空自动从名称生成" /></div>
            <div><label class="block text-sm font-medium mb-1">父分类</label><select id="cat-parent" class="w-full border rounded px-3 py-2">${this.getParentOptions()}</select></div>
            <div><label class="block text-sm font-medium mb-1">描述</label><textarea id="cat-desc" class="w-full border rounded px-3 py-2" rows="3" placeholder="说明此分类的用途和包含的内容"></textarea></div>
          </div>`,
        onConfirm: async () => {
          const name = document.getElementById('cat-name').value.trim();
          let slug = document.getElementById('cat-slug').value.trim();
          const parentId = document.getElementById('cat-parent').value;
          const description = document.getElementById('cat-desc').value.trim();
          if (!name) { alert('名称不能为空'); return false; }
          if (!slug) slug = name.toLowerCase().replace(/[^\w\u4e00-\u9fff]+/g, '_').replace(/^_|_$/g, '');
          await window.ApiClient.callTool('kb.category.create', { slug, name, description, parent_id: parentId || undefined });
          await this.loadData();
        }
      });
    },

    async showEditModal(id) {
      const cat = this.allCats.find(c => (c.category_id || c.id) === id);
      if (!cat) return;
      window.ModalDialog.show({
        title: '编辑分类',
        content: `
          <div class="space-y-4">
            <div><label class="block text-sm font-medium mb-1">名称</label><input id="cat-name-edit" class="w-full border rounded px-3 py-2" value="${this.esc(cat.name || '')}" /></div>
            <div><label class="block text-sm font-medium mb-1">标识符 (Slug)</label><input id="cat-slug-edit" class="w-full border rounded px-3 py-2" value="${this.esc(cat.slug || '')}" /></div>
            <div><label class="block text-sm font-medium mb-1">父分类</label><select id="cat-parent-edit" class="w-full border rounded px-3 py-2">${this.getParentOptions()}</select></div>
            <div><label class="block text-sm font-medium mb-1">描述</label><textarea id="cat-desc-edit" class="w-full border rounded px-3 py-2" rows="3">${this.esc(cat.description || '')}</textarea></div>
          </div>`,
        onConfirm: async () => {
          const name = document.getElementById('cat-name-edit').value.trim();
          const slug = document.getElementById('cat-slug-edit').value.trim();
          const parentId = document.getElementById('cat-parent-edit').value;
          const description = document.getElementById('cat-desc-edit').value.trim();
          const payload = {};
          if (name) payload.name = name;
          if (slug) payload.slug = slug;
          if (description !== undefined) payload.description = description;
          payload.parent_id = parentId || undefined;
          await window.ApiClient.callTool('kb.category.update', { category_id: id, ...payload });
          await this.loadData();
        }
      });
      // Set parent dropdown to current value
      setTimeout(() => {
        const sel = document.getElementById('cat-parent-edit');
        if (sel && cat.parent_id) sel.value = cat.parent_id;
      }, 100);
    },

    async deleteCategory(id) {
      if (!confirm('确定删除此分类？')) return;
      try {
        await window.ApiClient.callTool('kb.category.delete', { category_id: id });
        await this.loadData();
      } catch (e) {
        alert('删除失败: ' + e.message);
      }
    },

    async refresh() { await this.loadData(); },

    esc(s) { return String(s || '').replace(/&/g,'&amp;').replace(/</g,'&lt;').replace(/>/g,'&gt;').replace(/'/g,'&#39;').replace(/"/g,'&quot;'); }
  };
})();