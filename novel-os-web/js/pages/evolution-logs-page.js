/**
 * Evolution Logs Page
 * 进化日志管理
 */
(function() {
  window.EvolutionLogsPage = {
    logs: [], filterSource: '', filterRisk: '',

    async init() {
      const ca = document.getElementById('content-area');
      ca.innerHTML = `
        <div class="space-y-4">
          <div class="flex items-center justify-between">
            <h1 class="text-2xl font-bold text-gray-800">进化日志</h1>
            <button onclick="EvolutionLogsPage.loadData()" class="px-4 py-2 bg-gray-100 text-gray-700 rounded-lg hover:bg-gray-200 text-sm">🔄 刷新</button>
          </div>
          <div class="flex gap-2">
            <select id="ev-source" onchange="EvolutionLogsPage.filterSource=this.value;EvolutionLogsPage.loadData()" class="px-3 py-1.5 border rounded text-sm">
              <option value="">全部来源</option><option value="discussion_room">讨论室</option><option value="agent">Agent</option><option value="user">用户</option>
            </select>
            <select id="ev-risk" onchange="EvolutionLogsPage.filterRisk=this.value;EvolutionLogsPage.loadData()" class="px-3 py-1.5 border rounded text-sm">
              <option value="">全部风险</option><option value="low">低风险</option><option value="medium">中风险</option><option value="high">高风险</option>
            </select>
          </div>
          <div id="ev-table" class="bg-white rounded-lg shadow overflow-hidden">
            <div class="p-8 text-center text-gray-500">加载中...</div>
          </div>
        </div>
      `;
      await this.loadData();
      return true;
    },

    async loadData() {
      try {
        const args = { limit: 100 };
        if (this.filterSource) args.source_type = this.filterSource;
        if (this.filterRisk) args.risk_level = this.filterRisk;
        this.logs = await window.ApiClient.callTool('evolution.logs', args).catch(() => []);
        this.renderTable();
      } catch (e) {
        document.getElementById('ev-table').innerHTML = '<div class="p-8 text-center text-red-500">加载失败: ' + e.message + '</div>';
      }
    },

    renderTable() {
      const t = document.getElementById('ev-table');
      if (!this.logs.length) { t.innerHTML = '<div class="p-8 text-center text-gray-500">暂无进化日志</div>'; return; }
      const riskColor = { low: 'bg-green-100 text-green-700', medium: 'bg-yellow-100 text-yellow-700', high: 'bg-red-100 text-red-700' };
      const sourceLabel = { discussion_room: '讨论室', agent: 'Agent', user: '用户' };
      t.innerHTML = `
        <table class="min-w-full divide-y divide-gray-200">
          <thead class="bg-gray-50"><tr>
            <th class="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">来源</th>
            <th class="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">目标表</th>
            <th class="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">操作</th>
            <th class="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">风险</th>
            <th class="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">自动?</th>
            <th class="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">时间</th>
            <th class="px-4 py-3 text-right text-xs font-medium text-gray-500 uppercase">操作</th>
          </tr></thead>
          <tbody class="divide-y divide-gray-100">
            ${this.logs.map(l => `
              <tr class="hover:bg-gray-50">
                <td class="px-4 py-3 text-sm">${sourceLabel[l.source_type]||l.source_type}</td>
                <td class="px-4 py-3 text-sm text-gray-600">${l.target_table}</td>
                <td class="px-4 py-3 text-sm">${l.action}</td>
                <td class="px-4 py-3"><span class="px-2 py-0.5 rounded text-xs ${riskColor[l.risk_level]||'bg-gray-100 text-gray-600'}">${l.risk_level||'?'}</span></td>
                <td class="px-4 py-3 text-sm">${l.auto_applied?'✅':'❌'}</td>
                <td class="px-4 py-3 text-xs text-gray-400">${new Date(l.created_at).toLocaleString()}</td>
                <td class="px-4 py-3 text-right">
                  <button onclick="EvolutionLogsPage.showDetail('${l.id}')" class="text-blue-600 hover:underline text-xs mr-2">详情</button>
                  ${window.AppState?.isAdmin ? `<button onclick="EvolutionLogsPage.rollback('${l.id}')" class="text-red-600 hover:underline text-xs">回滚</button>` : ''}
                </td>
              </tr>
            `).join('')}
          </tbody>
        </table>`;
    },

    showDetail(id) {
      const log = this.logs.find(l => l.id === id);
      if (!log) return;
      ModalDialog.show({
        title: '进化详情',
        size: 'lg',
        content: `<div class="space-y-3 text-sm">
          <div><span class="font-medium">来源:</span> ${log.source_type} / ${log.source_id||''}</div>
          <div><span class="font-medium">目标:</span> ${log.target_table} / ${log.action}</div>
          <div><span class="font-medium">风险:</span> ${log.risk_level} — ${log.risk_reason||''}</div>
          <div class="bg-gray-50 p-3 rounded text-xs font-mono max-h-48 overflow-y-auto"><pre>${JSON.stringify(log.new_value||{}, null, 2)}</pre></div>
        </div>`,
        showFooter: false,
      });
    },

    async rollback(id) {
      ModalDialog.confirm('确定回滚此进化记录？旧值将被恢复。', async () => {
        try {
          await window.ApiClient.callTool('evolution.rollback', { log_id: id });
          ModalDialog.close();
          await this.loadData();
          window.AppCore?.toast('已回滚', 'success');
        } catch (e) { alert('回滚失败: ' + e.message); }
      });
    }
  };
})();