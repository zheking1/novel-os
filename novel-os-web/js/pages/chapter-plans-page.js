/**
 * Novel OS - Chapter Plans Page
 * 章节大纲计划查看页面
 */
(function() {
  'use strict';

  window.ChapterPlansPage = {
    init() {
      this.render();
      this.loadData();
      return true;
    },

    render() {
      const contentArea = document.getElementById('content-area');
      contentArea.innerHTML = `
        <div class="max-w-5xl mx-auto space-y-4">
          <div class="flex items-center justify-between">
            <div>
              <h1 class="text-2xl font-bold text-gray-800">章节大纲</h1>
              <p class="text-gray-500 mt-1">查看各章节的生成计划</p>
            </div>
            <button onclick="ChapterPlansPage.loadData()" 
                    class="px-4 py-2 bg-primary-600 text-white rounded-lg hover:bg-primary-700 transition-colors">
              ${t('common.refresh')}
            </button>
          </div>

          <div id="plans-container" class="space-y-4">
            <div class="bg-white rounded-lg shadow p-8 text-center">
              <div class="spinner w-8 h-8 border-4 border-primary-600 border-t-transparent rounded-full animate-spin mx-auto"></div>
              <p class="mt-2 text-gray-500">加载中...</p>
            </div>
          </div>
        </div>
      `;
    },

    async loadData() {
      const container = document.getElementById('plans-container');
      try {
        const workspace = window.AppState.currentWorkspace;
        const project = window.AppState.currentProject;
        if (!workspace || !project) {
          container.innerHTML = '<div class="bg-white rounded-lg shadow p-8 text-center text-gray-500">请先选择工作区和项目</div>';
          return;
        }

        const plans = await window.ApiClient.callTool('plot.list_chapter_plans', { workspace, project });
        if (!plans || plans.length === 0) {
          container.innerHTML = '<div class="bg-white rounded-lg shadow p-8 text-center text-gray-500">暂无章节大纲（生成章节时会自动创建）</div>';
          return;
        }

        container.innerHTML = plans.map(p => `
          <div class="bg-white rounded-lg shadow overflow-hidden">
            <div class="px-4 py-3 bg-gray-50 border-b border-gray-200 flex items-center justify-between">
              <div class="flex items-center gap-2">
                <span class="px-2 py-0.5 text-xs rounded-full bg-primary-100 text-primary-700 font-medium">第${p.chapter_no}章</span>
                <span class="px-2 py-0.5 text-xs rounded-full ${p.status === 'active' ? 'bg-green-100 text-green-700' : 'bg-gray-100 text-gray-600'}">${p.status}</span>
                <span class="text-xs text-gray-400">${p.created_at ? new Date(p.created_at).toLocaleString() : ''}</span>
              </div>
            </div>
            <div class="p-4">
              <pre class="text-sm text-gray-700 whitespace-pre-wrap font-sans">${this.formatPlan(p.plan)}</pre>
            </div>
          </div>
        `).join('');
      } catch (error) {
        console.error('[ChapterPlans] Load error:', error);
        container.innerHTML = `<div class="bg-white rounded-lg shadow p-8 text-center text-red-500">加载失败: ${error.message}</div>`;
      }
    },

    formatPlan(plan) {
      if (!plan) return '暂无内容';
      if (typeof plan === 'string') return plan;
      const lines = [];
      for (const [key, val] of Object.entries(plan)) {
        if (Array.isArray(val)) {
          lines.push(`【${key}】`);
          val.forEach((v, i) => lines.push(`  ${i + 1}. ${typeof v === 'object' ? JSON.stringify(v) : v}`));
        } else if (typeof val === 'object' && val !== null) {
          lines.push(`【${key}】`);
          lines.push(`  ${JSON.stringify(val, null, 2).replace(/\n/g, '\n  ')}`);
        } else {
          lines.push(`【${key}】 ${val}`);
        }
      }
      return lines.join('\n');
    }
  };
})();