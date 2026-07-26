/**
 * KB Search Page
 * 全文检索 - 搜索知识库内容
 */
(function() {
  window.KbSearchPage = {
    results: [],

    async init() {
      const contentArea = document.getElementById('content-area');
      contentArea.innerHTML = `
        <div class="flex items-center justify-between mb-6">
          <h1 class="text-2xl font-bold text-gray-800">${window.t('nav.kbSearch') || '全文检索'}</h1>
        </div>
        <div class="bg-white rounded-lg shadow p-6 mb-6">
          <div class="flex gap-4">
            <input type="text" id="search-input" 
                   class="flex-1 px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary-500 text-lg"
                   placeholder="输入关键词搜索知识库..."
                   onkeypress="if(event.key==='Enter')KbSearchPage.performSearch()">
            <button onclick="KbSearchPage.performSearch()" class="px-6 py-3 bg-primary-600 text-white rounded-lg hover:bg-primary-700">
              🔍 搜索
            </button>
          </div>
          <div class="flex gap-4 mt-4">
            <select id="search-type" class="px-3 py-2 border border-gray-300 rounded-lg">
              <option value="">全部类型</option>
              <option value="entity">实体</option>
              <option value="uk">通用知识</option>
              <option value="pk">项目知识</option>
            </select>
            <select id="search-category" class="px-3 py-2 border border-gray-300 rounded-lg">
              <option value="">全部分类</option>
            </select>
          </div>
        </div>
        <div id="search-results">
          <div class="p-8 text-center text-gray-500 bg-white rounded-lg shadow">输入关键词开始搜索</div>
        </div>
      `;
      await this.loadCategories();
      return true;
    },

    async loadCategories() {
      try {
        const result = await window.ApiClient.callTool('kb.category.list').catch(() => []);
        const categories = Array.isArray(result) ? result : (result?.categories || result?.result || []);
        const select = document.getElementById('search-category');
        if (select && categories.length > 0) {
          select.innerHTML = '<option value="">全部分类</option>' +
            categories.map(c => `<option value="${c.slug}">${c.name}</option>`).join('');
        }
      } catch (e) {
        console.error('加载分类失败:', e);
      }
    },

    async performSearch() {
      const query = document.getElementById('search-input').value.trim();
      if (!query) {
        alert('请输入搜索关键词');
        return;
      }

      const container = document.getElementById('search-results');
      container.innerHTML = '<div class="p-8 text-center text-gray-500 bg-white rounded-lg shadow">搜索中...</div>';

      try {
        const type = document.getElementById('search-type').value;
        const category = document.getElementById('search-category').value;
        const projectId = window.AppState.currentProjectId || window.AppState.currentProject || '';

        let results = [];

        // Search based on type
        if (!type || type === 'entity') {
          const entityResult = await window.ApiClient.callTool('kb.entity.search', {
            query,
            limit: 10
          }).catch(() => []);
          const entities = Array.isArray(entityResult) ? entityResult : (entityResult?.entities || entityResult?.result || []);
          results = results.concat(entities.map(e => ({ ...e, _type: 'entity' })));
        }

        if (!type || type === 'uk') {
          const ukResult = await window.ApiClient.callTool('kb.uk.search', {
            query,
            category_slug: category || undefined,
            limit: 10
          }).catch(() => []);
          const ukItems = Array.isArray(ukResult) ? ukResult : (ukResult?.entries || ukResult?.result || []);
          results = results.concat(ukItems.map(u => ({ ...u, _type: 'uk' })));
        }

        if ((!type || type === 'pk') && window.AppState.currentProject) {
          const pkResult = await window.ApiClient.callTool('kb.pk.list', {
            workspace: window.AppState.currentWorkspace,
            project: window.AppState.currentProject
          }).catch(() => []);
          const pkItems = Array.isArray(pkResult) ? pkResult : (pkResult?.entries || pkResult?.result || []);
          // Filter PK items by query
          const filteredPk = pkItems.filter(p => 
            JSON.stringify(p).toLowerCase().includes(query.toLowerCase())
          );
          results = results.concat(filteredPk.map(p => ({ ...p, _type: 'pk' })));
        }

        this.results = results;
        this.renderResults(query);
      } catch (e) {
        document.getElementById('search-results').innerHTML = 
          `<div class="p-8 text-center text-red-500 bg-white rounded-lg shadow">搜索失败: ${e.message}</div>`;
      }
    },

    renderResults(query) {
      const container = document.getElementById('search-results');

      if (!this.results || this.results.length === 0) {
        container.innerHTML = `<div class="p-8 text-center text-gray-500 bg-white rounded-lg shadow">未找到包含 "${query}" 的内容</div>`;
        return;
      }

      container.innerHTML = `
        <div class="mb-4 text-gray-600">找到 ${this.results.length} 个结果</div>
        <div class="space-y-3">
          ${this.results.map(r => this.renderResultItem(r, query)).join('')}
        </div>
      `;
    },

    renderResultItem(result, query) {
      const type = result._type;
      const typeLabel = type === 'entity' ? '实体' : type === 'uk' ? '通用知识' : '项目知识';
      const typeColor = type === 'entity' ? 'bg-purple-100 text-purple-700' : type === 'uk' ? 'bg-blue-100 text-blue-700' : 'bg-green-100 text-green-700';

      let title = result.name || result.title || result.topic || '未命名';
      let content = result.content || result.summary || result.description || '';

      // Highlight query in content
      const regex = new RegExp(`(${query})`, 'gi');
      content = content.replace(regex, '<mark class="bg-yellow-200">$1</mark>');

      return `
        <div class="bg-white rounded-lg shadow p-4 hover:shadow-md transition-shadow cursor-pointer" onclick="KbSearchPage.showDetail('${result.id || result.entry_id}', '${type}')">
          <div class="flex items-center gap-2 mb-2">
            <span class="px-2 py-0.5 text-xs rounded ${typeColor}">${typeLabel}</span>
            <span class="text-xs text-gray-400">${result.category || result.entity_type || '-'}</span>
          </div>
          <h3 class="font-semibold text-gray-800 mb-2">${title}</h3>
          <p class="text-sm text-gray-600 line-clamp-3">${content.substring(0, 200)}${content.length > 200 ? '...' : ''}</p>
        </div>
      `;
    },

    async showDetail(id, type) {
      try {
        let result;
        if (type === 'entity') {
          result = await window.ApiClient.callTool('kb.entity.get', { entity_id: id }).catch(() => null);
        } else if (type === 'uk') {
          result = await window.ApiClient.callTool('kb.uk.get', { entry_id: id }).catch(() => null);
        } else {
          const projectId = window.AppState.currentProjectId || window.AppState.currentProject || '';
          result = await window.ApiClient.callTool('kb.pk.get', { workspace: window.AppState.currentWorkspace, project: window.AppState.currentProject, key: id }).catch(() => null);
        }

        if (!result) {
          alert('无法加载详情');
          return;
        }

        ModalDialog.show({
          title: result.name || result.title || result.topic || '详情',
          size: 'lg',
          content: `
            <div class="space-y-4">
              <div class="flex items-center gap-2">
                <span class="px-2 py-1 bg-gray-100 rounded text-xs">${type === 'entity' ? '实体' : type === 'uk' ? '通用知识' : '项目知识'}</span>
                ${result.category ? `<span class="px-2 py-1 bg-gray-100 rounded text-xs">${result.category}</span>` : ''}
              </div>
              ${result.content ? `
                <div class="bg-gray-50 p-4 rounded">
                  <pre class="text-sm text-gray-700 whitespace-pre-wrap">${result.content}</pre>
                </div>
              ` : ''}
              ${result.summary ? `
                <div>
                  <h4 class="font-medium mb-1">摘要</h4>
                  <p class="text-sm text-gray-600">${result.summary}</p>
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

    loadData() {
      // Reset search
      document.getElementById('search-input').value = '';
      document.getElementById('search-results').innerHTML = 
        '<div class="p-8 text-center text-gray-500 bg-white rounded-lg shadow">输入关键词开始搜索</div>';
    }
  };
})();
