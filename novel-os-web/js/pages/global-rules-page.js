/**
 * Global Rules Page
 * 全局规则管理
 */
(function() {
  window.GlobalRulesPage = {
    rules: [], filterType: '',

    async init() {
      const ca = document.getElementById('content-area');
      ca.innerHTML = `
        <div class="space-y-4">
          <div class="flex items-center justify-between">
            <div>
              <h1 class="text-2xl font-bold text-gray-800">全局规则</h1>
              <p class="text-gray-500 mt-1">跨项目共享的创作规则和审查规则</p>
            </div>
            ${window.AppState?.isAdmin ? `
            <button onclick="GlobalRulesPage.showCreateModal()" class="px-4 py-2 bg-primary-600 text-white rounded-lg hover:bg-primary-700 flex items-center gap-2">
              <span>+</span> 新建规则
            </button>` : ''}
          </div>
          <div class="flex gap-2 mb-2" id="global-rules-filter">
            <button onclick="GlobalRulesPage.filterType='';GlobalRulesPage.loadData()" class="px-3 py-1.5 rounded text-sm font-medium transition ${this.filterType?'bg-gray-100 text-gray-600 border border-gray-200':'bg-primary-600 text-white'}">全部</button>
            <button onclick="GlobalRulesPage.filterType='creative';GlobalRulesPage.loadData()" class="px-3 py-1.5 rounded text-sm font-medium transition ${this.filterType==='creative'?'bg-blue-600 text-white':'bg-gray-100 text-gray-600 border border-gray-200'}">1. 创作规则</button>
            <button onclick="GlobalRulesPage.filterType='compliance';GlobalRulesPage.loadData()" class="px-3 py-1.5 rounded text-sm font-medium transition ${this.filterType==='compliance'?'bg-red-600 text-white':'bg-gray-100 text-gray-600 border border-gray-200'}">2. 审查规则</button>
            <button onclick="GlobalRulesPage.filterType='polish';GlobalRulesPage.loadData()" class="px-3 py-1.5 rounded text-sm font-medium transition ${this.filterType==='polish'?'bg-purple-600 text-white':'bg-gray-100 text-gray-600 border border-gray-200'}">3. 润色规则</button>
          </div>
          <div id="global-rules-table" class="bg-white rounded-lg shadow overflow-hidden">
            <div class="p-8 text-center text-gray-500">加载中...</div>
          </div>
        </div>
      `;
      await this.loadData();
      return true;
    },

    async loadData() {
      try {
        const args = { status: 'active' };
        if (this.filterType) args.rule_type = this.filterType;
        this.rules = await window.ApiClient.callTool('global_rules.list', args).catch(() => []);
        this.renderTable();
        this.updateFilterButtons();
      } catch (e) {
        document.getElementById('global-rules-table').innerHTML = `<div class="p-8 text-center text-red-500">加载失败: ${e.message}</div>`;
      }
    },

    updateFilterButtons() {
      const btns = document.querySelectorAll('#global-rules-filter button');
      if (!btns.length) return;
      btns[0].className = 'px-3 py-1.5 rounded text-sm font-medium transition ' +
        (this.filterType ? 'bg-gray-100 text-gray-600 border border-gray-200' : 'bg-primary-600 text-white');
      [['creative','bg-blue-600 text-white','bg-gray-100 text-gray-600 border border-gray-200'],
       ['compliance','bg-red-600 text-white','bg-gray-100 text-gray-600 border border-gray-200'],
       ['polish','bg-purple-600 text-white','bg-gray-100 text-gray-600 border border-gray-200']]
      .forEach(function(arr, i) {
        if (btns[i+1]) btns[i+1].className = 'px-3 py-1.5 rounded text-sm font-medium transition ' +
          (this.filterType === arr[0] ? arr[1] : arr[2]);
      }, this);
    },

    renderTable() {
      const t = document.getElementById('global-rules-table');
      if (!this.rules.length) {
        t.innerHTML = `<div class="p-8 text-center text-gray-500">暂无全局规则</div>`;
        return;
      }
      const typeLabel = { creative: '创作', compliance: '审查', polish: '润色' };
      const typeColor = { creative: 'bg-blue-100 text-blue-700', compliance: 'bg-red-100 text-red-700', polish: 'bg-purple-100 text-purple-700' };
      t.innerHTML = `
        <table class="min-w-full divide-y divide-gray-200">
          <thead class="bg-gray-50"><tr>
            <th class="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">规则Key</th>
            <th class="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">标题</th>
            <th class="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">类型</th>
            <th class="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">严重度</th>
            <th class="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">来源</th>
            <th class="px-4 py-3 text-right text-xs font-medium text-gray-500 uppercase">操作</th>
          </tr></thead>
          <tbody class="divide-y divide-gray-100">
            ${this.rules.map(r => `
              <tr class="hover:bg-gray-50">
                <td class="px-4 py-3 text-sm font-mono text-gray-600">${r.rule_key}</td>
                <td class="px-4 py-3 text-sm text-gray-800">${r.title}</td>
                <td class="px-4 py-3"><span class="px-2 py-0.5 rounded text-xs ${typeColor[r.rule_type]||'bg-gray-100 text-gray-700'}">${typeLabel[r.rule_type]||r.rule_type}</span></td>
                <td class="px-4 py-3 text-xs text-gray-500">${r.severity}</td>
                <td class="px-4 py-3 text-xs text-gray-400">${r.source_project_id?'来自项目':'手动创建'}</td>
                <td class="px-4 py-3 text-right">
                  <button onclick="GlobalRulesPage.showEditModal('${r.rule_key}')" class="text-blue-600 hover:underline text-xs mr-2">编辑</button>
                  <button onclick="GlobalRulesPage.handleDelete('${r.rule_key}')" class="text-red-600 hover:underline text-xs">删除</button>
                </td>
              </tr>
            `).join('')}
          </tbody>
        </table>`;
    },

    showCreateModal() {
      if (!window.AppState?.isAdmin) { alert('仅管理员可创建全局规则'); return; }
      ModalDialog.show({
        title: '新建全局规则',
        size: 'lg',
        content: this._formHtml(),
        confirmText: '创建',
        onConfirm: async () => { await this._handleSave(); }
      });
    },

    showEditModal(ruleKey) {
      if (!window.AppState?.isAdmin) { alert('仅管理员可编辑全局规则'); return; }
      const rule = this.rules.find(r => r.rule_key === ruleKey);
      if (!rule) return;
      ModalDialog.show({
        title: '编辑全局规则',
        size: 'lg',
        content: this._formHtml(rule),
        confirmText: '保存',
        onConfirm: async () => { await this._handleSave(ruleKey); }
      });
    },

    _formHtml(rule) {
      const d = rule || {};
      return `
        <div class="space-y-4">
          <div class="grid grid-cols-2 gap-4">
            <div>
              <label class="block text-sm font-medium text-gray-700 mb-1">Rule Key *</label>
              <input type="text" id="gr-key" value="${d.rule_key||''}" ${rule?'readonly':''} class="w-full px-3 py-2 border border-gray-300 rounded-lg text-sm" required>
            </div>
            <div>
              <label class="block text-sm font-medium text-gray-700 mb-1">类型 *</label>
              <select id="gr-type" class="w-full px-3 py-2 border border-gray-300 rounded-lg text-sm">
                <option value="creative" ${d.rule_type==='creative'?'selected':''}>创作规则</option>
                <option value="compliance" ${d.rule_type==='compliance'?'selected':''}>审查规则</option>
                <option value="polish" ${d.rule_type==='polish'?'selected':''}>润色规则</option>
              </select>
            </div>
          </div>
          <div>
            <label class="block text-sm font-medium text-gray-700 mb-1">标题 *</label>
            <input type="text" id="gr-title" value="${d.title||''}" class="w-full px-3 py-2 border border-gray-300 rounded-lg text-sm" required>
          </div>
          <div>
            <label class="block text-sm font-medium text-gray-700 mb-1">内容 *</label>
            <textarea id="gr-content" rows="4" class="w-full px-3 py-2 border border-gray-300 rounded-lg text-sm">${d.content||''}</textarea>
          </div>
          <div class="grid grid-cols-2 gap-4">
            <div>
              <label class="block text-sm font-medium text-gray-700 mb-1">严重度</label>
              <select id="gr-severity" class="w-full px-3 py-2 border border-gray-300 rounded-lg text-sm">
                ${['critical','serious','warning','info'].map(s => `<option value="${s}" ${d.severity===s?'selected':''}>${s}</option>`).join('')}
              </select>
            </div>
            <div>
              <label class="block text-sm font-medium text-gray-700 mb-1">状态</label>
              <select id="gr-status" class="w-full px-3 py-2 border border-gray-300 rounded-lg text-sm">
                <option value="active" ${d.status==='active'?'selected':''}>启用</option>
                <option value="inactive" ${d.status==='inactive'?'selected':''}>禁用</option>
              </select>
            </div>
          </div>
        </div>`;
    },

    async _handleSave(editKey) {
      const key = document.getElementById('gr-key')?.value?.trim();
      const type = document.getElementById('gr-type')?.value;
      const title = document.getElementById('gr-title')?.value?.trim();
      const content = document.getElementById('gr-content')?.value?.trim();
      const severity = document.getElementById('gr-severity')?.value;
      const status = document.getElementById('gr-status')?.value;
      if (!key || !title || !content) { alert('Key、标题和内容为必填'); return; }
      try {
        await window.ApiClient.callTool('global_rules.upsert', { rule_key: key, rule_type: type, title, content, severity, status });
        ModalDialog.close();
        await this.loadData();
        window.AppCore?.toast('已保存', 'success');
      } catch (e) { alert('保存失败: ' + e.message); }
    },

    async handleDelete(ruleKey) {
      if (!window.AppState?.isAdmin) { alert('仅管理员可删除全局规则'); return; }
      ModalDialog.confirm(`确定删除全局规则「${ruleKey}」？`, async () => {
        await window.ApiClient.callTool('global_rules.delete', { rule_key: ruleKey });
        ModalDialog.close();
        await this.loadData();
        window.AppCore?.toast('已删除', 'success');
      });
    }
  };
})();