/**
 * KB Genres Page
 * 题材策略管理 - 查看、新增、编辑和删除不同小说类型的知识策略
 */
(function() {
  window.KbGenresPage = {
    genres: [],
    categories: [],

    async init() {
      const contentArea = document.getElementById('content-area');
      contentArea.innerHTML = `
        <div class="flex items-center justify-between mb-6">
          <h1 class="text-2xl font-bold text-gray-800">${window.t('nav.kbGenres') || '题材策略'}</h1>
          <div class="flex gap-2">
            <button onclick="KbGenresPage.showCreateModal()" class="px-4 py-2 bg-primary-600 text-white rounded-lg hover:bg-primary-700 text-sm">+ 新增题材</button>
            <button onclick="KbGenresPage.loadData()" class="px-4 py-2 bg-gray-100 text-gray-700 rounded-lg hover:bg-gray-200 text-sm">🔄 刷新</button>
          </div>
        </div>
        <div id="genres-content">
          <div class="p-8 text-center text-gray-500 bg-white rounded-lg shadow">加载中...</div>
        </div>
      `;
      await this.loadData();
      return true;
    },

    async loadData() {
      const container = document.getElementById('genres-content');
      try {
        const result = await window.ApiClient.callTool('kb.genre.list').catch(() => []);
        this.genres = Array.isArray(result) ? result : (result?.genres || result?.result || []);

        if (!this.genres || this.genres.length === 0) {
          container.innerHTML = `<div class="p-8 text-center text-gray-500 bg-white rounded-lg shadow">暂无题材数据</div>`;
          return;
        }

        container.innerHTML = `
          <div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
            ${this.genres.map(g => {
              const incCount = (g.included_categories || []).length;
              const excCount = (g.excluded_categories || []).length;
              const incNames = g.included_names || g.included_categories || [];
              const statusBadge = incCount > 0
                ? '<span class="text-xs px-2 py-0.5 bg-green-100 text-green-700 rounded-full">已配置</span>'
                : '<span class="text-xs px-2 py-0.5 bg-yellow-100 text-yellow-700 rounded-full">待配置</span>';
              return `
              <div class="bg-white rounded-lg shadow p-4 hover:shadow-md transition-shadow cursor-pointer" onclick="KbGenresPage.showGenreDetail('${g.id || g.slug}')">
                <div class="flex items-center gap-3 mb-3">
                  <span class="text-2xl">${g.icon || '📚'}</span>
                  <div class="flex-1">
                    <div class="flex items-center justify-between">
                      <h3 class="font-semibold text-gray-800">${g.name || g.id}</h3>
                      ${statusBadge}
                    </div>
                    <span class="text-xs text-gray-500">${g.id || g.slug}</span>
                  </div>
                </div>
                <p class="text-sm text-gray-600 line-clamp-2">${g.description || '暂无描述'}</p>
                <div class="mt-3 flex items-center justify-between">
                  <span class="text-xs text-gray-400">${incCount} 个分类 / ${excCount} 排除</span>
                  <button class="text-xs text-primary-600 hover:underline">查看详情 →</button>
                </div>
              </div>
            `;}).join('')}
          </div>
        `;
      } catch (e) {
        container.innerHTML = `<div class="p-8 text-center text-red-500 bg-white rounded-lg shadow">加载失败: ${e.message}</div>`;
      }
    },

    showCreateModal() {
      window.ModalDialog.show({
        title: '新增题材',
        size: 'lg',
        content: `
          <div class="space-y-4">
            <div class="grid grid-cols-2 gap-4">
              <div>
                <label class="block text-sm font-medium text-gray-700 mb-1">Slug *</label>
                <input type="text" id="new-slug" placeholder="英文标识，如 xianxia"
                       class="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary-500 text-sm">
              </div>
              <div>
                <label class="block text-sm font-medium text-gray-700 mb-1">名称 *</label>
                <input type="text" id="new-name" placeholder="显示名称，如 仙侠"
                       class="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary-500 text-sm">
              </div>
            </div>
            <div>
              <label class="block text-sm font-medium text-gray-700 mb-1">描述</label>
              <textarea id="new-desc" rows="2" placeholder="题材特征描述..."
                        class="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary-500 text-sm"></textarea>
            </div>
            <div>
              <label class="block text-sm font-medium text-gray-700 mb-1">典型元素（一行一个）</label>
              <textarea id="new-elements" rows="3" placeholder="升级打怪&#10;异火神兽&#10;宗门争霸"
                        class="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary-500 text-sm"></textarea>
            </div>
            <div class="grid grid-cols-2 gap-4">
              <div>
                <label class="block text-sm font-medium text-gray-700 mb-1">目标受众</label>
                <select id="new-audience" class="w-full px-3 py-2 border border-gray-300 rounded-lg text-sm">
                  <option value="全年龄">全年龄</option>
                  <option value="男性">男性</option>
                  <option value="女性">女性</option>
                </select>
              </div>
              <div>
                <label class="block text-sm font-medium text-gray-700 mb-1">别名（逗号分隔）</label>
                <input type="text" id="new-aliases" placeholder="修仙, 修真, 古典仙侠"
                       class="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary-500 text-sm">
              </div>
            </div>
          </div>
        `,
        confirmText: '创建',
        onConfirm: async () => {
          await KbGenresPage.handleCreate();
        }
      });
    },

    async handleCreate() {
      const slug = document.getElementById('new-slug')?.value?.trim();
      const name = document.getElementById('new-name')?.value?.trim();
      if (!slug || !name) { alert('Slug 和名称为必填'); return; }

      const desc = document.getElementById('new-desc')?.value?.trim();
      const elementsRaw = document.getElementById('new-elements')?.value?.trim();
      const audience = document.getElementById('new-audience')?.value;
      const aliasesRaw = document.getElementById('new-aliases')?.value?.trim();

      try {
        await window.ApiClient.callTool('kb.genre.create', {
          slug, name,
          description: desc || null,
          typical_elements: elementsRaw ? elementsRaw.split('\n').map(s => s.trim()).filter(Boolean) : [],
          target_audience: audience || '全年龄',
          aliases: aliasesRaw ? aliasesRaw.split(',').map(s => s.trim()).filter(Boolean) : [],
          platform_tags: [name]
        });
        ModalDialog.close();
        await this.loadData();
        window.AppCore?.toast('题材已创建', 'success');
      } catch (e) {
        alert('创建失败: ' + e.message);
      }
    },

    async showGenreDetail(genreId) {
      try {
        const [genreDetail, keywords] = await Promise.all([
          window.ApiClient.callTool('kb.genre.get', { genre_id: genreId }).catch(() => null),
          window.ApiClient.callTool('kb.genre.keywords', { genre_id: genreId }).catch(() => null)
        ]);

        const genre = this.genres.find(g => (g.id || g.slug) === genreId) || {};
        const included = genreDetail?.included_categories || genreDetail?.active_categories || [];
        const excluded = genreDetail?.excluded_categories || [];
        const elements = genreDetail?.typical_elements || genre.typical_elements || [];

        window.ModalDialog.show({
          title: `题材: ${genre.name || genreId}`,
          size: 'lg',
          content: `
            <div class="space-y-6">
              <div class="border-b pb-4">
                <h4 class="font-medium mb-2">基本信息</h4>
                <p class="text-sm text-gray-600">${genre.description || genreDetail?.description || '暂无描述'}</p>
              </div>

              ${elements.length ? `
              <div>
                <h4 class="font-medium mb-2">典型元素</h4>
                <div class="flex flex-wrap gap-2">
                  ${elements.map(e => `<span class="px-2 py-1 bg-purple-100 text-purple-700 rounded text-xs">${e}</span>`).join('')}
                </div>
              </div>
              ` : ''}

              <div>
                <h4 class="font-medium mb-2">启用的知识分类 (${included.length})</h4>
                ${included.length ? `
                  <div class="flex flex-wrap gap-2">
                    ${included.map(cat => `<span class="px-2 py-1 bg-blue-100 text-blue-700 rounded text-xs">${cat}</span>`).join('')}
                  </div>
                ` : '<p class="text-sm text-gray-500">未配置</p>'}
              </div>

              ${excluded.length ? `
              <div>
                <h4 class="font-medium mb-2">排除的分类 (${excluded.length})</h4>
                <div class="flex flex-wrap gap-2">
                  ${excluded.map(cat => `<span class="px-2 py-1 bg-red-100 text-red-700 rounded text-xs">${cat}</span>`).join('')}
                </div>
              </div>
              ` : ''}

              <div>
                <h4 class="font-medium mb-2">推荐搜索关键词</h4>
                ${keywords?.keywords?.length ? `
                  <div class="flex flex-wrap gap-2">
                    ${keywords.keywords.map(kw => `<span class="px-2 py-1 bg-green-100 text-green-700 rounded text-xs">${kw}</span>`).join('')}
                  </div>
                ` : '<p class="text-sm text-gray-500">暂无关键词</p>'}
              </div>

              <div class="border-t pt-4 flex flex-wrap gap-2">
                <button onclick="KbGenresPage.showEditConfig('${genreId}')" class="px-4 py-2 bg-primary-600 text-white rounded-lg hover:bg-primary-700 text-sm">✏️ 编辑分类配置</button>
                ${window.AppState.currentProject ? `
                <button onclick="KbGenresPage.preheatGenre('${genreId}')" class="px-4 py-2 bg-orange-600 text-white rounded-lg hover:bg-orange-700 text-sm">🔥 预加载知识</button>
                ` : ''}
                <button onclick="KbGenresPage.handleDelete('${genreId}')" class="px-4 py-2 bg-red-100 text-red-700 rounded-lg hover:bg-red-200 text-sm">🗑️ 删除</button>
              </div>
            </div>
          `,
          showFooter: false
        });
      } catch (e) {
        alert('加载详情失败: ' + e.message);
      }
    },

    async showEditConfig(genreId) {
      const genre = this.genres.find(g => (g.id || g.slug) === genreId) || {};
      const detail = await window.ApiClient.callTool('kb.genre.get', { genre_id: genreId }).catch(() => ({}));
      const included = (detail?.included_categories || detail?.active_categories || []).join('\n');
      const excluded = (detail?.excluded_categories || []).join('\n');

      ModalDialog.close();

      if (!this.categories.length) {
        try {
          const cats = await window.ApiClient.callTool('kb.category.tree').catch(() => []);
          this.categories = Array.isArray(cats) ? cats : (cats?.result || cats?.categories || []);
        } catch (e) { this.categories = []; }
      }

      const catRefHtml = this.categories.length ? `
        <div class="mt-4 border rounded-lg p-3 bg-gray-50 max-h-48 overflow-y-auto">
          <h5 class="text-sm font-medium text-gray-600 mb-2">可用分类参考 (点击复制 slug):</h5>
          <div class="grid grid-cols-2 gap-1">
            ${this.categories.map(c => `
              <span class="text-xs text-gray-500 cursor-pointer hover:text-primary-600 hover:underline"
                    onclick="navigator.clipboard.writeText('${c.slug}')" title="点击复制: ${c.slug}">
                ${c.name || c.slug}
              </span>
            `).join('')}
          </div>
        </div>
      ` : '';

      window.ModalDialog.show({
        title: '编辑分类配置: ' + (genre.name || genreId),
        size: 'lg',
        content: `
          <div class="space-y-4">
            <p class="text-sm text-gray-500">配置该题材允许使用和排除的知识分类，一行一个 slug。</p>
            <div>
              <label class="block text-sm font-medium text-gray-700 mb-1">启用的分类 <span class="text-green-600">(included)</span></label>
              <textarea id="edit-included" rows="5"
                        class="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary-500 text-sm font-mono"
                        placeholder="例如:&#10;internal-energy&#10;bloodline&#10;world_building">${included}</textarea>
            </div>
            <div>
              <label class="block text-sm font-medium text-gray-700 mb-1">排除的分类 <span class="text-red-600">(excluded)</span></label>
              <textarea id="edit-excluded" rows="5"
                        class="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary-500 text-sm font-mono"
                        placeholder="例如:&#10;technology&#10;contract">${excluded}</textarea>
            </div>
            ${catRefHtml}
          </div>
        `,
        confirmText: '保存',
        onConfirm: async () => { await KbGenresPage.saveConfig(genreId); }
      });
    },

    async saveConfig(genreId) {
      const includedRaw = document.getElementById('edit-included')?.value?.trim() || '';
      const excludedRaw = document.getElementById('edit-excluded')?.value?.trim() || '';
      const included = includedRaw.split('\n').map(s => s.trim()).filter(Boolean);
      const excluded = excludedRaw.split('\n').map(s => s.trim()).filter(Boolean);

      try {
        await window.ApiClient.callTool('kb.genre.update', { genre: genreId, included_categories: included, excluded_categories: excluded });
        await this.loadData();
        ModalDialog.close();
        window.AppCore?.toast('配置已保存', 'success');
      } catch (e) {
        alert('保存失败: ' + e.message);
      }
    },

    async handleDelete(genreId) {
      const genre = this.genres.find(g => (g.id || g.slug) === genreId) || {};
      const name = genre.name || genreId;

      window.ModalDialog.confirm(`确认删除题材「${name}」？此操作不可恢复。`, async () => {
        try {
          await window.ApiClient.callTool('kb.genre.delete', { slug: genreId });
          ModalDialog.close();
          await this.loadData();
          window.AppCore?.toast('已删除', 'success');
        } catch (e) {
          alert('删除失败: ' + e.message);
        }
      });
    },

    async preheatGenre(genreId) {
      const projectId = window.AppState.currentProjectId || window.AppState.currentProject;
      if (!projectId) { alert('请先选择项目'); return; }
      try {
        await window.ApiClient.callTool('kb.genre.preheat', {
          workspace: window.AppState.currentWorkspace, project: window.AppState.currentProject,
          project_id: projectId, genre: genreId
        });
        alert('预加载成功！');
        ModalDialog.close();
      } catch (e) {
        alert('预加载失败: ' + e.message);
      }
    },

  };
})();
