(function() {
  'use strict';
  window.HomePage = {
    tab: 'dashboard',

    init() {
      this.render();
      this.loadData();
      return true;
    },

    render() {
      document.getElementById('content-area').innerHTML = `
        <div class="max-w-5xl mx-auto space-y-4">
          <div class="flex items-center gap-4 border-b border-gray-200 pb-2">
            <button onclick="HomePage.switchTab('dashboard')" class="px-4 py-2 text-sm font-medium rounded-t ${this.tab === 'dashboard' ? 'text-primary-600 border-b-2 border-primary-600' : 'text-gray-500 hover:text-gray-700'}">📊 工作台</button>
            <button onclick="HomePage.switchTab('tutorial')" class="px-4 py-2 text-sm font-medium rounded-t ${this.tab === 'tutorial' ? 'text-primary-600 border-b-2 border-primary-600' : 'text-gray-500 hover:text-gray-700'}">📖 使用教程</button>
          </div>
          <div id="home-content"></div>
        </div>`;
      this.loadData();
    },

    switchTab(tab) {
      this.tab = tab;
      this.render();
    },

    async loadData() {
      const el = document.getElementById('home-content');
      if (!el) return;
      if (this.tab === 'dashboard') {
        await this.loadDashboard(el);
      } else {
        this.renderTutorial(el);
      }
    },

    async loadDashboard(el) {
      el.innerHTML = '<div class="text-center py-8 text-gray-500"><div class="spinner w-8 h-8 border-4 border-primary-600 border-t-transparent rounded-full animate-spin mx-auto"></div><p class="mt-2">加载中...</p></div>';
      const ws = window.AppState?.currentWorkspace || '';
      const prj = window.AppState?.currentProject || '';

      let models = [], workspaces = [], reviews = [], entities = [];
      try { workspaces = await window.ApiClient.callTool('workspace.list', {}) || []; } catch(_) {}
      if (ws) try { models = await window.ApiClient.callTool('model.profile.list') || []; } catch(_) {}

      // Count by task_type
      const reviewModels = models.filter(m => m.task_types?.includes('review') && m.status === 'active');
      const embedModels = models.filter(m => m.task_types?.includes('embedding') && m.status === 'active');
      const analysisModels = models.filter(m => m.task_types?.includes('analysis') && m.status === 'active');
      const contextModels = models.filter(m => m.task_types?.includes('context') && m.status === 'active');
      const rerankModels = models.filter(m => m.task_types?.includes('rerank') && m.status === 'active');
      const polishModels = models.filter(m => m.task_types?.includes('polish') && m.status === 'active');
      const allActive = reviewModels.length + embedModels.length + analysisModels.length + contextModels.length + rerankModels.length + polishModels.length;

      // Get projects with details
      let projectCards = '';
      for (const w of workspaces.slice(0, 3)) {
        try {
          const projects = await window.ApiClient.callTool('project.list', { workspace: w.slug }) || [];
          for (const p of projects.slice(0, 5)) {
            let chapters = [], vols = [], jobCount = 0, lastActivity = '';
            try {
              const chRes = await window.ApiClient.callTool('local.chapter.list', { workspace: w.slug, project: p.slug, limit: 200 });
              chapters = chRes?.chapters || chRes || [];
            } catch(_) {}
            try { vols = await window.ApiClient.callTool('volume.list', { workspace: w.slug, project: p.slug }) || []; } catch(_) {}
            try {
              const jRes = await window.ApiClient.callTool('review.list_revision_tasks', { workspace: w.slug, project: p.slug, status: 'pending' });
              jobCount = (Array.isArray(jRes) ? jRes : []).length;
            } catch(_) {}
            // Find last activity
            try {
              const jDone = await window.ApiClient.callTool('review.list_revision_tasks', { workspace: w.slug, project: p.slug, limit: 1 });
              const done = Array.isArray(jDone) ? jDone : [];
              if (done.length) lastActivity = `第${done[0].chapter_no}章审核完成`;
            } catch(_) {}

            const done = chapters.filter(c => c.status === 'final' || c.status === 'published').length;
            const total = chapters.length;
            const pct = total > 0 ? Math.round(done / total * 100) : 0;
            const barColor = pct >= 100 ? 'bg-green-500' : 'bg-primary-500';

            projectCards += `
              <div class="bg-white rounded-lg shadow p-4 hover:shadow-md transition-shadow">
                <div class="flex items-center justify-between">
                  <div class="flex items-center gap-2">
                    <span class="text-lg">📚</span>
                    <h3 class="font-medium text-gray-800">${p.title || p.slug}</h3>
                    <span class="px-2 py-0.5 text-xs rounded-full ${pct >= 100 ? 'bg-green-100 text-green-700' : 'bg-blue-100 text-blue-700'}">${pct >= 100 ? '已完成' : '进行中'}</span>
                  </div>
                </div>
                <div class="mt-2 text-xs text-gray-500 flex gap-4">
                  <span>章节: ${total}</span>
                  ${jobCount > 0 ? `<span class="text-orange-600">待审核: ${jobCount}</span>` : ''}
                </div>
                <div class="mt-2 flex items-center gap-2 text-xs">
                  <div class="flex-1 h-2 bg-gray-200 rounded-full"><div class="h-2 rounded-full ${barColor}" style="width:${pct}%"></div></div>
                  <span class="text-gray-500">${pct}%</span>
                </div>
                ${lastActivity ? `<div class="mt-1 text-xs text-gray-400">📌 ${lastActivity}</div>` : ''}
              </div>`;
          }
        } catch(_) {}
      }

      // Recent activity
      let recentHtml = '<p class="text-gray-400 text-sm">暂无动态</p>';
      try {
        const allReviews = await window.ApiClient.callTool('review.list_revision_tasks', { workspace: ws, project: prj, limit: 5, status: null }) || [];
        const list = Array.isArray(allReviews) ? allReviews : [];
        if (list.length) {
          recentHtml = list.map(r => {
            const time = r.created_at ? new Date(r.created_at).toLocaleString() : '';
            const name = prj || '项目';
            return `<div class="flex items-center gap-2 text-sm py-1 border-b border-gray-100 last:border-0"><span class="text-gray-400">·</span><span class="text-gray-600">${name} - 第${r.chapter_no}章 ${r.status === 'aggregated' ? '审核完成' : '待审核'}</span><span class="text-xs text-gray-400 ml-auto">${time}</span></div>`;
          }).join('');
        }
      } catch(_) {}

      el.innerHTML = `
        <!-- 系统状态 -->
        <div class="grid grid-cols-6 gap-4">
          <div class="bg-white rounded-lg shadow p-4 text-center">
            <div class="text-lg ${reviewModels.length > 0 ? 'text-green-500' : 'text-red-500'}">${reviewModels.length > 0 ? '✅' : '❌'}</div>
            <div class="text-sm font-medium mt-1">审核</div>
            <div class="text-xs text-gray-400">${reviewModels.length} 模型</div>
            <div class="text-xs text-gray-300 mt-1">多模型并行审核章节质量</div>
          </div>
          <div class="bg-white rounded-lg shadow p-4 text-center">
            <div class="text-lg ${polishModels.length > 0 ? 'text-green-500' : 'text-red-500'}">${polishModels.length > 0 ? '✅' : '❌'}</div>
            <div class="text-sm font-medium mt-1">润色</div>
            <div class="text-xs text-gray-400">${polishModels.length} 模型</div>
            <div class="text-xs text-gray-300 mt-1">文笔润色和修辞优化</div>
          </div>
          <div class="bg-white rounded-lg shadow p-4 text-center">
            <div class="text-lg ${embedModels.length > 0 ? 'text-green-500' : 'text-red-500'}">${embedModels.length > 0 ? '✅' : '❌'}</div>
            <div class="text-sm font-medium mt-1">向量</div>
            <div class="text-xs text-gray-400">${embedModels.length} 模型</div>
            <div class="text-xs text-gray-300 mt-1">语义搜索和记忆检索</div>
          </div>
          <div class="bg-white rounded-lg shadow p-4 text-center">
            <div class="text-lg ${analysisModels.length > 0 ? 'text-green-500' : 'text-red-500'}">${analysisModels.length > 0 ? '✅' : '❌'}</div>
            <div class="text-sm font-medium mt-1">分析</div>
            <div class="text-xs text-gray-400">${analysisModels.length} 模型</div>
            <div class="text-xs text-gray-300 mt-1">文风分析/弧光追踪/节奏分析</div>
          </div>
          <div class="bg-white rounded-lg shadow p-4 text-center">
            <div class="text-lg ${contextModels.length > 0 ? 'text-green-500' : 'text-red-500'}">${contextModels.length > 0 ? '✅' : '❌'}</div>
            <div class="text-sm font-medium mt-1">上下文</div>
            <div class="text-xs text-gray-400">${contextModels.length} 模型</div>
            <div class="text-xs text-gray-300 mt-1">上下文压缩和摘要生成</div>
          </div>
          <div class="bg-white rounded-lg shadow p-4 text-center">
            <div class="text-lg ${rerankModels.length > 0 ? 'text-green-500' : 'text-red-500'}">${rerankModels.length > 0 ? '✅' : '❌'}</div>
            <div class="text-sm font-medium mt-1">重排序</div>
            <div class="text-xs text-gray-400">${rerankModels.length} 模型</div>
            <div class="text-xs text-gray-300 mt-1">知识检索结果精排</div>
          </div>
        </div>

        <!-- 配置缺失提醒 -->
        ${reviewModels.length === 0 || embedModels.length === 0 || analysisModels.length === 0 || polishModels.length === 0 ? `
          <div class="bg-yellow-50 border border-yellow-200 rounded-lg p-3 text-sm text-yellow-700">
            ⚠️ 部分模型未配置，请先到「系统管理 → 模型配置」中激活所需模型
            <a href="#/system/model-profiles" class="text-blue-600 hover:underline ml-2">去配置 →</a>
          </div>
        ` : ''}

        <!-- 项目列表 -->
        <h2 class="font-medium text-gray-700">📊 项目列表</h2>
        <div class="space-y-3">
          ${projectCards || '<div class="bg-white rounded-lg shadow p-6 text-center text-gray-500"><p>暂无项目</p><p class="text-sm mt-1">通过 AI 工具对话创建你的第一个小说项目</p></div>'}
        </div>

        <!-- 最近动态 -->
        <h2 class="font-medium text-gray-700">📜 最近动态</h2>
        <div class="bg-white rounded-lg shadow p-4">
          ${recentHtml}
        </div>
      `;
    },

    renderTutorial(el) {
      el.innerHTML = `
        <div class="space-y-4">

          <div class="bg-white rounded-lg shadow p-6">
            <h2 class="text-lg font-semibold mb-4">┌─ 第1步：系统配置 ───────────────┐</h2>
            <div class="space-y-3 text-sm text-gray-600">
              <div>
                <span class="font-medium text-gray-800">a. 配置模型</span>
                <p>菜单 → 系统管理 → 模型配置。确保审核/向量/分析模型都是 active 状态。</p>
              </div>
              <div>
                <span class="font-medium text-gray-800">b. 配置 API Key</span>
                <p>菜单 → 系统管理 → API Key管理 → 创建。复制生成的 Key 到 AI 工具的 MCP 设置中。</p>
              </div>
<div>
                <span class="font-medium text-gray-800">c. 配置 AI 工具提示词</span>
                <p>点击 <button onclick="HomePage.showAgentsMd()" class="text-blue-600 hover:underline font-medium">📄 AGENTS.md</button> 查看并复制到 AI 工具的自定义指令中。</p>
              </div>
              <div>
                <span class="font-medium text-gray-800">d. 配置 MCP 连接</span>
              <p class="text-xs text-gray-400 mb-2">将以下 JSON 添加到 AI 工具的 MCP 配置文件（如 opencode.json）中。</p>
              <div class="bg-gray-900 text-green-400 p-4 rounded-lg text-xs font-mono overflow-x-auto relative">
                <button onclick="navigator.clipboard.writeText(this.nextElementSibling.textContent); this.textContent='\u2714\ufe0f'; setTimeout(()=>{this.textContent='\ud83d\udccb'}, 2000)" class="absolute top-2 right-2 px-2 py-1 bg-gray-700 hover:bg-gray-600 text-white rounded text-xs">📋</button>
                <pre>{
  "mcpServers": {
    "novel-os": {
      "url": "https://novel.example.com/mcp",
      "headers": {
        "apiKey": "替换为你的 API Key"
      }
    }
  }
}</pre>
              </div>
              <p class="text-xs text-gray-400 mt-2">API Key 在 Web UI → 系统管理 → API Key 管理 中创建。配置完成后即可用 AI 工具直接对话操作。</p>
            </div>
            </div>
          </div>

          <div class="bg-white rounded-lg shadow p-6">
            <h2 class="text-lg font-semibold mb-4">┌─ 第2步：创建小说 ───────────────┐</h2>
            <div class="space-y-3 text-sm text-gray-600">
              <p>直接和 AI 工具对话，告诉它：</p>
              <div class="bg-gray-50 p-3 rounded text-gray-700 font-medium">"我想写一本小说"</div>
              <p>AI 工具会引导你完成：确定类型 → 创建项目 → 深化设定。整个过程是对话式的，你只需要回答问题。</p>
            </div>
          </div>

          <div class="bg-white rounded-lg shadow p-6">
            <h2 class="text-lg font-semibold mb-4">┌─ 第3步：生成章节 ───────────────┐</h2>
            <div class="space-y-3 text-sm text-gray-600">
              <p>设定完成后，告诉 AI 工具：</p>
              <div class="bg-gray-50 p-3 rounded text-gray-700 font-medium">"开始写第一章吧"</div>
              <p>系统会自动完成上下文获取 → 正文生成 → 多模型审核 → 保存到本地 → 更新角色弧光和剧情进度。</p>
              <p class="mt-2">每章完成后，继续告诉 AI 工具：</p>
              <div class="bg-gray-50 p-3 rounded text-gray-700 font-medium">"继续写第二章"</div>
            </div>
          </div>

          <div class="bg-blue-50 border border-blue-200 rounded-lg p-4 text-sm text-blue-700">
            💡 提示：所有复杂操作都由 AI 工具自动完成，你只需要用自然语言和它对话即可。详细的 MCP 工具参考请点击 <button onclick="HomePage.showAgentsMd()" class="text-blue-600 hover:underline font-medium">📄 AGENTS.md</button> 查看。
          </div>

        </div>
      `;
    },

    async showAgentsMd() {
      let content = '加载中...';
      try {
        const resp = await fetch('/AGENTS.md');
        content = await resp.text();
      } catch (e) {
        content = '加载失败: ' + e.message;
      }
      const modal = document.createElement('div');
      modal.className = 'fixed inset-0 bg-black/50 z-50 flex items-center justify-center';
      modal.innerHTML = `
        <div class="bg-white rounded-lg shadow-xl w-full max-w-3xl mx-4 max-h-[85vh] flex flex-col">
          <div class="px-6 py-4 border-b border-gray-200 flex items-center justify-between">
            <h3 class="text-lg font-semibold">📄 AGENTS.md</h3>
            <div class="flex gap-2">
              <button onclick="HomePage.copyAgents(this)" class="px-3 py-1.5 text-sm bg-primary-600 text-white rounded hover:bg-primary-700">
                📋 一键复制
              </button>
              <button onclick="this.closest('#agents-modal').remove()" class="text-gray-400 hover:text-gray-600">
                <svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12"/>
                </svg>
              </button>
            </div>
          </div>
          <div class="p-6 overflow-y-auto">
            <pre id="agents-content" class="text-sm text-gray-700 whitespace-pre-wrap font-sans leading-relaxed">${content}</pre>
          </div>
        </div>`;
      modal.id = 'agents-modal';
      document.body.appendChild(modal);
    },

    async copyAgents(btn) {
      const text = document.getElementById('agents-content')?.textContent;
      if (!text) return;
      try {
        if (navigator.clipboard) {
          await navigator.clipboard.writeText(text);
        } else {
          const ta = document.createElement('textarea');
          ta.value = text; ta.style.position = 'fixed'; ta.style.opacity = '0';
          document.body.appendChild(ta); ta.select();
          document.execCommand('copy'); document.body.removeChild(ta);
        }
        btn.textContent = '✅ 已复制';
        setTimeout(() => { btn.textContent = '📋 一键复制'; }, 2000);
      } catch (e) {
        alert('复制失败: ' + e.message);
      }
    }
  };
})();