/**
 * Expectations Page
 * 读者期待管理 - 管理伏笔和悬念
 */
(function() {
  window.ExpectationsPage = {
    expectations: [],

    async init() {
      const contentArea = document.getElementById('content-area');
      contentArea.innerHTML = `
        <div class="flex items-center justify-between mb-6">
          <h1 class="text-2xl font-bold text-gray-800">${window.t('nav.expectations') || '读者期待'}</h1>
          <div class="flex gap-2">
            <button onclick="ExpectationsPage.showCreateModal()" class="px-4 py-2 bg-primary-600 text-white rounded-lg hover:bg-primary-700 text-sm">➕ 新建期待</button>
            <button onclick="ExpectationsPage.loadData()" class="px-4 py-2 bg-gray-100 text-gray-700 rounded-lg hover:bg-gray-200 text-sm">🔄 刷新</button>
          </div>
        </div>
        <div class="flex gap-4 mb-4">
          <select id="type-filter" class="px-4 py-2 border border-gray-300 rounded-lg" onchange="ExpectationsPage.filterExpectations()">
            <option value="">全部类型</option>
            <option value="foreshadowing">伏笔</option>
            <option value="mystery">悬念</option>
            <option value="promise">承诺</option>
            <option value="callback"> callback</option>
          </select>
          <select id="status-filter" class="px-4 py-2 border border-gray-300 rounded-lg" onchange="ExpectationsPage.filterExpectations()">
            <option value="">全部状态</option>
            <option value="pending">待兑现</option>
            <option value="fulfilled">已兑现</option>
          </select>
        </div>
        <div id="expectations-content" class="bg-white rounded-lg shadow">
          <div class="p-8 text-center text-gray-500">加载中...</div>
        </div>
      `;
      await this.loadData();
      return true;
    },

    async loadData() {
      const container = document.getElementById('expectations-content');
      try {
        const workspace = window.AppState.currentWorkspace || '';
        const project = window.AppState.currentProject || '';
        const result = await window.ApiClient.callTool('expectation.list', { workspace, project }).catch(() => []);
        this.expectations = Array.isArray(result) ? result : (result?.expectations || result?.result || []);
        this.renderExpectations();
      } catch (e) {
        container.innerHTML = `<div class="p-8 text-center text-red-500">加载失败: ${e.message}</div>`;
      }
    },

    renderExpectations() {
      const container = document.getElementById('expectations-content');
      const typeFilter = document.getElementById('type-filter')?.value || '';
      const statusFilter = document.getElementById('status-filter')?.value || '';

      let filtered = this.expectations;
      if (typeFilter) {
        filtered = filtered.filter(e => e.expectation_type === typeFilter);
      }
      if (statusFilter) {
        filtered = filtered.filter(e => e.status === statusFilter);
      }

      if (!filtered || filtered.length === 0) {
        container.innerHTML = `<div class="p-8 text-center text-gray-500">暂无读者期待</div>`;
        return;
      }

      container.innerHTML = `
        <div class="overflow-x-auto">
          <table class="w-full text-sm">
            <thead class="bg-gray-50">
              <tr>
                <th class="px-4 py-3 text-left font-medium text-gray-600">标题</th>
                <th class="px-4 py-3 text-left font-medium text-gray-600">类型</th>
                <th class="px-4 py-3 text-left font-medium text-gray-600">状态</th>
                <th class="px-4 py-3 text-left font-medium text-gray-600">埋设章节</th>
                <th class="px-4 py-3 text-left font-medium text-gray-600">兑现章节</th>
                <th class="px-4 py-3 text-left font-medium text-gray-600">操作</th>
              </tr>
            </thead>
            <tbody class="divide-y divide-gray-100">
              ${filtered.map(e => `
                <tr class="hover:bg-gray-50 ${e.status === 'fulfilled' ? 'bg-green-50' : ''}">
                  <td class="px-4 py-3">
                    <div class="font-medium text-gray-800">${e.title}</div>
                    ${e.description ? `<div class="text-xs text-gray-500 mt-1">${e.description}</div>` : ''}
                  </td>
                  <td class="px-4 py-3">
                    <span class="px-2 py-1 text-xs rounded ${this.getTypeColor(e.expectation_type)}">${this.getTypeLabel(e.expectation_type)}</span>
                  </td>
                  <td class="px-4 py-3">
                    <span class="px-2 py-1 text-xs rounded ${e.status === 'fulfilled' ? 'bg-green-100 text-green-700' : 'bg-yellow-100 text-yellow-700'}">
                      ${e.status === 'fulfilled' ? '已兑现' : '待兑现'}
                    </span>
                  </td>
                  <td class="px-4 py-3 text-gray-600">${e.chapter_no ? `第${e.chapter_no}章` : '-'}</td>
                  <td class="px-4 py-3 text-gray-600">${e.payoff_chapter_no ? `第${e.payoff_chapter_no}章` : '-'}</td>
                  <td class="px-4 py-3">
                    <div class="flex gap-1">
                      ${e.status !== 'fulfilled' ? `
                        <button onclick="ExpectationsPage.showFulfillModal('${e.expectation_key}')" class="px-2 py-1 text-xs text-green-600 hover:bg-green-50 rounded">兑现</button>
                      ` : ''}
                    </div>
                  </td>
                </tr>
              `).join('')}
            </tbody>
          </table>
        </div>
      `;
    },

    getTypeColor(type) {
      const colors = {
        'foreshadowing': 'bg-purple-100 text-purple-700',
        'mystery': 'bg-blue-100 text-blue-700',
        'promise': 'bg-orange-100 text-orange-700',
        'callback': 'bg-pink-100 text-pink-700'
      };
      return colors[type] || 'bg-gray-100 text-gray-700';
    },

    getTypeLabel(type) {
      const labels = {
        'foreshadowing': '伏笔',
        'mystery': '悬念',
        'promise': '承诺',
        'callback': 'callback'
      };
      return labels[type] || type;
    },

    filterExpectations() {
      this.renderExpectations();
    },

    showCreateModal() {
      ModalDialog.show({
        title: '新建读者期待',
        content: `
          <div class="space-y-4">
            <div>
              <label class="block text-sm font-medium mb-1">标识 <span class="text-red-500">*</span></label>
              <input id="new-key" class="w-full border rounded px-3 py-2" placeholder="英文+数字+下划线" />
            </div>
            <div>
              <label class="block text-sm font-medium mb-1">标题 <span class="text-red-500">*</span></label>
              <input id="new-title" class="w-full border rounded px-3 py-2" />
            </div>
            <div>
              <label class="block text-sm font-medium mb-1">类型 <span class="text-red-500">*</span></label>
              <select id="new-type" class="w-full border rounded px-3 py-2">
                <option value="foreshadowing">伏笔</option>
                <option value="mystery">悬念</option>
                <option value="promise">承诺</option>
                <option value="callback">callback</option>
              </select>
            </div>
            <div>
              <label class="block text-sm font-medium mb-1">埋设章节</label>
              <input type="number" id="new-chapter" class="w-full border rounded px-3 py-2" placeholder="章节号" />
            </div>
            <div>
              <label class="block text-sm font-medium mb-1">描述</label>
              <textarea id="new-desc" class="w-full border rounded px-3 py-2" rows="3" placeholder="详细描述这个期待..."></textarea>
            </div>
          </div>`,
        onConfirm: async () => {
          const expectation_key = document.getElementById('new-key').value.trim();
          const title = document.getElementById('new-title').value.trim();
          const expectation_type = document.getElementById('new-type').value;
          const chapter_no = parseInt(document.getElementById('new-chapter').value) || undefined;
          const description = document.getElementById('new-desc').value.trim();
          
          if (!expectation_key || !title) { alert('标识和标题不能为空'); return; }
          
          try {
            const workspace = window.AppState.currentWorkspace || '';
            const project = window.AppState.currentProject || '';
            await window.ApiClient.callTool('expectation.upsert', {
              workspace, project, expectation_key, title, expectation_type,
              chapter_no, description: description || undefined
            });
            ModalDialog.close();
            await ExpectationsPage.loadData();
          } catch (e) { alert('创建失败: ' + e.message); }
        }
      });
    },

    showFulfillModal(key) {
      ModalDialog.show({
        title: '兑现期待',
        content: `
          <div class="space-y-4">
            <div>
              <label class="block text-sm font-medium mb-1">兑现章节 <span class="text-red-500">*</span></label>
              <input type="number" id="payoff-chapter" class="w-full border rounded px-3 py-2" placeholder="章节号" />
            </div>
          </div>`,
        onConfirm: async () => {
          const payoff_chapter_no = parseInt(document.getElementById('payoff-chapter').value);
          if (!payoff_chapter_no) { alert('请输入章节号'); return; }
          
          try {
            const workspace = window.AppState.currentWorkspace || '';
            const project = window.AppState.currentProject || '';
            await window.ApiClient.callTool('expectation.fulfill', {
              workspace, project, expectation_key: key, payoff_chapter_no
            });
            ModalDialog.close();
            await ExpectationsPage.loadData();
          } catch (e) { alert('兑现失败: ' + e.message); }
        }
      });
    },

  };
})();
