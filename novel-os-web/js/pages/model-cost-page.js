/**
 * Novel OS - Model Cost Page
 * 费用报告页面（/system/cost）
 *
 * 数据源：MCP 工具 cost.report（services/model_cost.py）
 * - 按时间分组：group_by = day / week / month
 * - 按模型拆分：cost.report 的 profile_keys 实际按 model_name 过滤，故逐模型再查一次
 */
(function () {
  'use strict';

  function t(key, fallback) {
    return (window.t && window.t(key)) || fallback;
  }

  window.ModelCostPage = {
    report: null,

    init() {
      this.render();
      this.loadData();
      return true;
    },

    render() {
      const contentArea = document.getElementById('content-area');
      if (!contentArea) return;

      const today = new Date().toISOString().split('T')[0];
      const from30 = new Date(Date.now() - 30 * 24 * 60 * 60 * 1000).toISOString().split('T')[0];

      contentArea.innerHTML = `
        <div class="space-y-4">
          <div class="flex items-center justify-between">
            <div>
              <h1 class="text-2xl font-bold text-gray-800">${t('nav.costReport', '费用报告')}</h1>
              <p class="text-gray-500 mt-1">按时间 / 模型统计 Token 用量与成本</p>
            </div>
            <button onclick="ModelCostPage.loadData()"
                    class="px-4 py-2 bg-gray-100 text-gray-700 rounded-lg hover:bg-gray-200 text-sm">刷新</button>
          </div>

          <div class="bg-white rounded-lg shadow p-4 flex flex-wrap items-end gap-3">
            <div>
              <label class="block text-xs font-medium text-gray-600 mb-1">粒度</label>
              <select id="cost-group-by" class="px-3 py-2 border border-gray-300 rounded-lg text-sm">
                <option value="day">按天</option>
                <option value="week">按周</option>
                <option value="month">按月</option>
              </select>
            </div>
            <div>
              <label class="block text-xs font-medium text-gray-600 mb-1">开始日期</label>
              <input type="date" id="cost-from-date" value="${from30}"
                     class="px-3 py-2 border border-gray-300 rounded-lg text-sm">
            </div>
            <div>
              <label class="block text-xs font-medium text-gray-600 mb-1">结束日期</label>
              <input type="date" id="cost-to-date" value="${today}"
                     class="px-3 py-2 border border-gray-300 rounded-lg text-sm">
            </div>
            <button onclick="ModelCostPage.loadData()"
                    class="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 text-sm">查询</button>
          </div>

          <div id="cost-summary" class="grid grid-cols-2 md:grid-cols-4 gap-4"></div>

          <div id="cost-container" class="bg-white rounded-lg shadow">
            <div class="p-8 text-center text-gray-500">${t('common.loading', '加载中...')}</div>
          </div>

          <div id="cost-model-container" class="bg-white rounded-lg shadow"></div>
        </div>
      `;
    },

    async loadData() {
      const container = document.getElementById('cost-container');
      const workspace = window.AppState && window.AppState.currentWorkspace;
      const project = window.AppState && window.AppState.currentProject;

      if (!workspace || !project) {
        container.innerHTML = '<div class="p-8 text-center text-gray-500">请先选择工作区与项目</div>';
        return;
      }

      const groupBy = (document.getElementById('cost-group-by') || {}).value || 'day';
      const fromDate = (document.getElementById('cost-from-date') || {}).value || undefined;
      const toDate = (document.getElementById('cost-to-date') || {}).value || undefined;

      try {
        this.report = await window.ApiClient.callTool('cost.report', {
          workspace: workspace,
          project: project,
          group_by: groupBy,
          from_date: fromDate,
          to_date: toDate
        });
        this.renderSummary(this.report);
        this.renderTable(this.report);
        await this.loadModelBreakdown(workspace, project, fromDate, toDate);
      } catch (error) {
        console.error('[ModelCost] load error:', error);
        container.innerHTML = '<div class="p-8 text-center text-red-500">加载失败: ' + (error && error.message) + '</div>';
      }
    },

    renderSummary(r) {
      const el = document.getElementById('cost-summary');
      if (!el) return;
      const usd = Number(r && r.total_cost_usd) || 0;
      const cards = [
        { label: '总花费 (USD)', value: '$' + usd.toFixed(4) },
        { label: '总请求数', value: this._fmtInt(r && r.total_requests) },
        { label: '输入 Tokens', value: this._fmtInt(r && r.total_input_tokens) },
        { label: '输出 Tokens', value: this._fmtInt(r && r.total_output_tokens) }
      ];
      el.innerHTML = cards.map(function (c) {
        return '<div class="bg-white rounded-lg shadow p-4">' +
          '<div class="text-xs text-gray-500">' + c.label + '</div>' +
          '<div class="text-xl font-semibold mt-1 text-gray-800">' + c.value + '</div>' +
          '</div>';
      }).join('');
    },

    renderTable(r) {
      const container = document.getElementById('cost-container');
      if (!container) return;
      const groups = (r && Array.isArray(r.groups)) ? r.groups : [];

      if (groups.length === 0) {
        container.innerHTML = '<div class="p-8 text-center text-gray-500">所选区间内暂无用量记录</div>';
        return;
      }

      const self = this;
      container.innerHTML =
        '<div class="px-4 py-3 border-b border-gray-200 font-medium text-gray-700">按时间分组</div>' +
        '<div class="overflow-x-auto"><table class="w-full text-sm">' +
        '<thead class="bg-gray-50"><tr>' +
        '<th class="px-4 py-3 text-left font-medium text-gray-600">周期</th>' +
        '<th class="px-4 py-3 text-left font-medium text-gray-600">请求数</th>' +
        '<th class="px-4 py-3 text-left font-medium text-gray-600">输入 Tokens</th>' +
        '<th class="px-4 py-3 text-left font-medium text-gray-600">输出 Tokens</th>' +
        '<th class="px-4 py-3 text-left font-medium text-gray-600">花费 (USD)</th>' +
        '</tr></thead><tbody class="divide-y divide-gray-100">' +
        groups.map(function (g) {
          return '<tr class="hover:bg-gray-50">' +
            '<td class="px-4 py-3 text-gray-800">' + self._fmtKey(g.key) + '</td>' +
            '<td class="px-4 py-3 text-gray-600">' + self._fmtInt(g.request_count) + '</td>' +
            '<td class="px-4 py-3 text-gray-600">' + self._fmtInt(g.input_tokens) + '</td>' +
            '<td class="px-4 py-3 text-gray-600">' + self._fmtInt(g.output_tokens) + '</td>' +
            '<td class="px-4 py-3 font-medium text-gray-800">$' + (Number(g.cost) || 0).toFixed(4) + '</td>' +
            '</tr>';
        }).join('') +
        '</tbody></table></div>';
    },

    // cost.report 只按时间分组；按模型拆分需逐模型再查一次汇总
    async loadModelBreakdown(workspace, project, fromDate, toDate) {
      const el = document.getElementById('cost-model-container');
      if (!el) return;

      let profiles = [];
      try {
        profiles = await window.ApiClient.callTool('model.profile.list') || [];
      } catch (e) {
        el.innerHTML = '';
        return;
      }
      if (!Array.isArray(profiles)) profiles = [];

      const names = [];
      profiles.forEach(function (p) {
        if (p && p.model_name && names.indexOf(p.model_name) === -1) names.push(p.model_name);
      });
      if (names.length === 0) {
        el.innerHTML = '';
        return;
      }

      const rows = [];
      for (let i = 0; i < Math.min(names.length, 12); i++) {
        try {
          const r = await window.ApiClient.callTool('cost.report', {
            workspace: workspace,
            project: project,
            group_by: 'month',
            profile_keys: [names[i]],
            from_date: fromDate,
            to_date: toDate
          });
          rows.push({
            model_name: names[i],
            cost: Number(r && r.total_cost_usd) || 0,
            requests: Number(r && r.total_requests) || 0
          });
        } catch (e) {
          // 单模型查询失败不影响整体
        }
      }
      rows.sort(function (a, b) { return b.cost - a.cost; });

      el.innerHTML =
        '<div class="px-4 py-3 border-b border-gray-200 font-medium text-gray-700">按模型拆分</div>' +
        '<div class="overflow-x-auto"><table class="w-full text-sm">' +
        '<thead class="bg-gray-50"><tr>' +
        '<th class="px-4 py-3 text-left font-medium text-gray-600">模型</th>' +
        '<th class="px-4 py-3 text-left font-medium text-gray-600">请求数</th>' +
        '<th class="px-4 py-3 text-left font-medium text-gray-600">花费 (USD)</th>' +
        '</tr></thead><tbody class="divide-y divide-gray-100">' +
        rows.map(function (r) {
          return '<tr class="hover:bg-gray-50">' +
            '<td class="px-4 py-3 font-mono text-xs text-gray-800">' + r.model_name + '</td>' +
            '<td class="px-4 py-3 text-gray-600">' + r.requests + '</td>' +
            '<td class="px-4 py-3 font-medium text-gray-800">$' + r.cost.toFixed(4) + '</td>' +
            '</tr>';
        }).join('') +
        '</tbody></table></div>';
    },

    _fmtInt(v) {
      return (Number(v) || 0).toLocaleString('en-US');
    },

    _fmtKey(k) {
      if (!k) return '-';
      return String(k).slice(0, 10);
    }
  };
})();
