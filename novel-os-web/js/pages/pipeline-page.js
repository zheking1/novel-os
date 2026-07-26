/**
 * Novel OS - Pipeline Page
 * 可配置的小说生成流水线：定义 → 运行 → 查看结果
 */
(function() {
  'use strict';

  window.PipelinePage = {
    state: {
      selectedChapter: null,
      passes: [],
      stageConfigs: []  // 用户可编辑的环节配置
    },

    // 默认环节定义（可修改）
    defaultStages: [
      { section: '上游准备', icon: '📋', stages: [
        { id: 'world-inject', step: 'A1', name: '世界设定注入', color: 'blue',
          desc: '将世界观、物理规则、社会结构等设定信息注入生成上下文',
          config: { prompt: '请根据以下世界设定生成章节上下文：\n{world_settings}\n重点关注与本章节相关的设定', model: 'default', temperature: 0.3, enabled: true } },
        { id: 'char-inject', step: 'A2', name: '角色设定注入', color: 'indigo',
          desc: '加载角色档案和当前状态，保持角色行为一致性',
          config: { prompt: '当前角色状态：\n{character_states}\n请确保角色言行符合其性格设定', model: 'default', temperature: 0.4, enabled: true } },
        { id: 'chapter-plan', step: 'A3', name: '章节规划', color: 'cyan',
          desc: '确定本章剧情位置、情节推进、POV视角，生成章节概要',
          config: { prompt: '请生成第{chapter_no}章的详细大纲，包括：\n1. 核心事件\n2. 情感节奏\n3. 预计字数：{word_count}', model: 'default', temperature: 0.6, enabled: true } }
      ]},
      { section: '核心流水线', icon: '⚙️', stages: [
        { id: 'outline', step: 'B1', name: '大纲生成', color: 'emerald',
          desc: '根据章节规划生成详细大纲，包含场景划分和情节转折',
          config: { prompt: '请根据以下概要生成详细大纲：\n{chapter_plan}\n输出格式：场景列表 + 关键事件', model: 'default', temperature: 0.7, enabled: true } },
        { id: 'draft', step: 'B2', name: '初稿生成', color: 'green',
          desc: '基于大纲逐场景生成正文，含对话、环境描写、动作',
          config: { prompt: '请根据以下大纲生成初稿：\n{outline}\n风格要求：{style_guide}', model: 'default', temperature: 0.8, enabled: true } },
        { id: 'polish', step: 'B3', name: '润色优化', color: 'teal',
          desc: '优化语言表达，修正语病，丰富修辞，统一文风',
          config: { prompt: '请润色以下文本：\n{draft}\n关注：句式多样性、修辞手法、节奏感', model: 'default', temperature: 0.5, enabled: true } },
        { id: 'verify', step: 'B4', name: '验证校对', color: 'cyan',
          desc: '校验逻辑漏洞、时间线冲突、设定违背、错别字',
          config: { prompt: '请校验以下文本的问题：\n{polished}\n检查：逻辑、时间线、设定一致性、错别字', model: 'default', temperature: 0.2, enabled: true } }
      ]},
      { section: '下游质控', icon: '✅', stages: [
        { id: 'continuity', step: 'C1', name: '一致性检查', color: 'purple',
          desc: '全局上下文检查：与前文连贯性、角色状态连续性',
          config: { prompt: '请检查以下内容与前文的连贯性：\n{content}\n前文摘要：{previous_summaries}', model: 'default', temperature: 0.2, enabled: true } },
        { id: 'multi-review', step: 'C2', name: '多模型审查', color: 'violet',
          desc: '多模型并行审查：配置多个模型分别从不同维度审查章节内容',
          config: { reviewers: [
            { model: '', focus: 'consistency', name: '一致性审查', prompt: '检查角色、设定与前文的一致性', weight: 1 },
            { model: '', focus: 'logic', name: '逻辑审查', prompt: '检查情节逻辑漏洞和时间线冲突', weight: 1 },
            { model: '', focus: 'compliance', name: '合规审查', prompt: '检查是否违反创作规则', weight: 1 }
          ], enabled: true } },
        { id: 'compliance', step: 'C3', name: '合规检查', color: 'fuchsia',
          desc: '运行自定义合规规则检查',
          config: { prompt: '合规规则列表：\n{rules}\n请检查文本是否违反以上规则', model: 'default', temperature: 0.1, enabled: true } },
        { id: 'review', step: 'C4', name: '人工审阅', color: 'pink',
          desc: '作者最终审阅，批准发布或退回修改',
          config: { prompt: '', model: 'manual', temperature: 0, enabled: true } }
      ]}
    ],

    init() {
      // 初始化环节配置（从 localStorage 读取，或使用默认）
      const saved = localStorage.getItem('pipeline_stage_configs');
      if (saved) {
        try { this.state.stageConfigs = JSON.parse(saved); } catch(e) { this.state.stageConfigs = []; }
      }
      this.render();
      this.loadData();
      return true;
    },

    getConfig(stageId) {
      const saved = this.state.stageConfigs.find(c => c.id === stageId);
      if (saved) return saved;
      // 从默认找
      for (const section of this.defaultStages) {
        const found = section.stages.find(s => s.id === stageId);
        if (found) return { ...found.config };
      }
      return { prompt: '', model: 'default', temperature: 0.5, enabled: true };
    },

    saveConfig(stageId, config) {
      const idx = this.state.stageConfigs.findIndex(c => c.id === stageId);
      if (idx >= 0) this.state.stageConfigs[idx] = { id: stageId, ...config };
      else this.state.stageConfigs.push({ id: stageId, ...config });
      localStorage.setItem('pipeline_stage_configs', JSON.stringify(this.state.stageConfigs));
    },

    render() {
      const contentArea = document.getElementById('content-area');
      contentArea.innerHTML = `
        <div class="space-y-6">
          <!-- 头部 -->
          <div class="flex items-center justify-between">
            <div>
              <h1 class="text-2xl font-bold text-gray-800">章节生成流水线</h1>
              <p class="text-gray-500 mt-1">定义流水线各环节配置 → 选择章节运行 → 查看生成结果</p>
            </div>
            <div class="flex items-center gap-3">
              <select id="pipeline-chapter-select" class="px-3 py-2 border border-gray-300 rounded-lg text-sm" onchange="PipelinePage.onChapterChange(this.value)">
                <option value="">选择章节运行...</option>
              </select>
              <button onclick="PipelinePage.runFullPipeline()" id="pipeline-run-btn" disabled
                      class="px-4 py-2 bg-primary-600 text-white rounded-lg hover:bg-primary-700 transition-colors text-sm flex items-center gap-1">
                ▶ 运行完整流水线
              </button>
            </div>
          </div>

          <!-- 流水线定义（可编辑配置） -->
          <div class="space-y-4" id="pipeline-stages">
            ${this.renderStageSections()}
          </div>

          <!-- 生成结果 -->
          <div id="pipeline-output" class="bg-white rounded-lg shadow">
            <div class="p-8 text-center text-gray-400">
              <p class="text-lg mb-2">📝 选择章节查看生成结果</p>
              <p class="text-sm">选择章节后，运行流水线的生成内容会显示在这里</p>
            </div>
          </div>
        </div>

        <!-- 环节配置编辑弹窗 -->
        <div id="pipeline-config-modal" class="fixed inset-0 bg-black/50 z-50 hidden flex items-center justify-center">
          <div class="bg-white rounded-lg shadow-xl w-full max-w-2xl mx-4 max-h-[85vh] flex flex-col">
            <div class="px-6 py-4 border-b border-gray-200 flex items-center justify-between">
              <h3 id="pipeline-config-title" class="text-lg font-semibold">编辑环节配置</h3>
              <button onclick="PipelinePage.closeConfigModal()" class="text-gray-400 hover:text-gray-600">
                <svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12"/></svg>
              </button>
            </div>
            <div class="p-6 overflow-y-auto flex-1 space-y-4">
              <!-- 标准环节配置 -->
              <div id="cfg-standard-fields" class="space-y-4">
                <div>
                  <label class="block text-sm font-medium text-gray-700 mb-1">提示词模板</label>
                  <textarea id="cfg-prompt" class="w-full h-40 border border-gray-300 rounded-lg p-3 text-sm font-mono" placeholder="使用 {变量名} 引用上下文"></textarea>
                  <p class="text-xs text-gray-400 mt-1">可用变量：{world_settings} {character_states} {chapter_plan} {outline} {draft} {polished} {content} {previous_summaries} {rules} {chapter_no} {word_count} {style_guide}</p>
                </div>
                <div class="grid grid-cols-2 gap-4">
                  <div>
                    <label class="block text-sm font-medium text-gray-700 mb-1">模型</label>
                    <select id="cfg-model" class="w-full border border-gray-300 rounded-lg px-3 py-2 text-sm">
                      <option value="default">默认模型</option>
                      <option value="fast">快速模型</option>
                      <option value="precise">精确模型</option>
                      <option value="manual">人工操作</option>
                    </select>
                  </div>
                  <div>
                    <label class="block text-sm font-medium text-gray-700 mb-1">温度 (0-2)</label>
                    <input type="number" id="cfg-temperature" min="0" max="2" step="0.1" value="0.7" class="w-full border border-gray-300 rounded-lg px-3 py-2 text-sm">
                  </div>
                </div>
              </div>
              <!-- 多模型审查员配置 -->
              <div id="cfg-reviewer-fields" class="hidden space-y-3">
                <label class="block text-sm font-medium text-gray-700">审查员列表（选择已配置的模型）</label>
                <div id="cfg-reviewer-list" class="space-y-2"></div>
                <button onclick="PipelinePage.addReviewer()" class="text-sm px-3 py-1.5 border border-dashed border-gray-300 rounded-lg hover:bg-gray-50 text-gray-500 w-full">
                  + 添加审查员
                </button>
              </div>
              </div>
              <div class="flex items-center gap-2">
                <input type="checkbox" id="cfg-enabled" checked class="rounded">
                <label for="cfg-enabled" class="text-sm text-gray-700">启用此环节</label>
              </div>
            </div>
            <div class="px-6 py-4 border-t border-gray-200 flex justify-end gap-3">
              <button onclick="PipelinePage.closeConfigModal()" class="px-4 py-2 border border-gray-300 rounded-lg hover:bg-gray-50">取消</button>
              <button onclick="PipelinePage.saveStageConfig()" class="px-4 py-2 bg-primary-600 text-white rounded-lg hover:bg-primary-700">保存配置</button>
            </div>
          </div>
        </div>
      `;
    },

    renderStageSections() {
      return this.defaultStages.map(section => `
        <div class="bg-white rounded-lg shadow overflow-hidden">
          <div class="px-4 py-3 bg-gray-50 border-b border-gray-200 flex items-center gap-2">
            <span>${section.icon}</span>
            <span class="font-semibold text-gray-700">${section.section}</span>
            <span class="text-xs text-gray-400">（${section.stages.length} 个环节）</span>
          </div>
          <div class="p-4 grid grid-cols-1 md:grid-cols-${Math.min(section.stages.length, 4)} gap-4">
            ${section.stages.map(stage => this.renderStageCard(stage)).join('')}
          </div>
        </div>
      `).join('');
    },

    renderStageCard(stage) {
      const colors = {
        blue: { bg: 'bg-blue-50', border: 'border-blue-200', badge: 'bg-blue-100 text-blue-700' },
        indigo: { bg: 'bg-indigo-50', border: 'border-indigo-200', badge: 'bg-indigo-100 text-indigo-700' },
        cyan: { bg: 'bg-cyan-50', border: 'border-cyan-200', badge: 'bg-cyan-100 text-cyan-700' },
        emerald: { bg: 'bg-emerald-50', border: 'border-emerald-200', badge: 'bg-emerald-100 text-emerald-700' },
        green: { bg: 'bg-green-50', border: 'border-green-200', badge: 'bg-green-100 text-green-700' },
        teal: { bg: 'bg-teal-50', border: 'border-teal-200', badge: 'bg-teal-100 text-teal-700' },
        purple: { bg: 'bg-purple-50', border: 'border-purple-200', badge: 'bg-purple-100 text-purple-700' },
        violet: { bg: 'bg-violet-50', border: 'border-violet-200', badge: 'bg-violet-100 text-violet-700' },
        fuchsia: { bg: 'bg-fuchsia-50', border: 'border-fuchsia-200', badge: 'bg-fuchsia-100 text-fuchsia-700' },
        pink: { bg: 'bg-pink-50', border: 'border-pink-200', badge: 'bg-pink-100 text-pink-700' }
      };
      const c = colors[stage.color] || colors.blue;
      const cfg = this.getConfig(stage.id);
      const statusText = cfg.enabled ? '' : ' ⏸ 已禁用';
      const reviewInfo = stage.id === 'multi-review' && cfg.reviewers
        ? ` ${cfg.reviewers.filter(r => r.model).length}个审查员`
        : (cfg.model ? ` ${cfg.model}` : '');
      return `
        <div class="${c.bg} border ${c.border} rounded-lg p-3 relative">
          <div class="flex items-start justify-between mb-2">
            <span class="${c.badge} text-xs font-medium px-2 py-0.5 rounded">${stage.step}</span>
            <span class="text-xs text-gray-400">${reviewInfo}${statusText}</span>
          </div>
          <h4 class="font-medium text-sm text-gray-800 mb-1">${stage.name}</h4>
          <p class="text-xs text-gray-500 leading-relaxed mb-3">${stage.desc}</p>
          <button onclick="PipelinePage.openConfigModal('${stage.id}')" class="text-xs px-2 py-1 rounded border border-gray-300 hover:bg-white text-gray-600 flex items-center gap-1">
            ⚙️ 配置
          </button>
        </div>
      `;
    },

    async loadData() {
      try {
        const workspace = window.AppState.currentWorkspace;
        const project = window.AppState.currentProject;
        if (!workspace || !project) return;
        const chapters = await window.ApiClient.callTool('local.chapter.list', { workspace, project });
        const list = Array.isArray(chapters) ? chapters : (chapters?.items || chapters?.chapters || []);
        document.getElementById('pipeline-chapter-select').innerHTML =
          '<option value="">选择章节运行...</option>' +
          list.map(ch => `<option value="${ch.chapter_no}">第${ch.chapter_no}章 ${ch.title || ''}</option>`).join('');
      } catch (e) { console.error('[Pipeline] Load error:', e); }
    },

    onChapterChange(chapterNo) {
      PipelinePage.state.selectedChapter = chapterNo;
      document.getElementById('pipeline-run-btn').disabled = !chapterNo;
      if (chapterNo) PipelinePage.loadChapterPasses(parseInt(chapterNo));
    },

    async loadChapterPasses(chapterNo) {
      try {
        const project = window.AppState.currentProject;
        const passes = await window.ApiClient.callTool('pipeline.get_passes', {
          workspace: window.AppState.currentWorkspace, project, chapter_no: chapterNo
        });
        PipelinePage.state.passes = Array.isArray(passes) ? passes : [];
        PipelinePage.renderOutput();
      } catch (e) {
        PipelinePage.state.passes = [];
        PipelinePage.renderOutput();
      }
    },

    renderOutput() {
      const container = document.getElementById('pipeline-output');
      if (!PipelinePage.state.selectedChapter) {
        container.innerHTML = `<div class="p-8 text-center text-gray-400"><p>选择章节查看生成结果</p></div>`;
        return;
      }
      if (!PipelinePage.state.passes.length) {
        container.innerHTML = `<div class="p-8 text-center text-gray-400"><p>第${PipelinePage.state.selectedChapter}章暂无生成记录，点击"运行完整流水线"开始生成</p></div>`;
        return;
      }
      container.innerHTML = `
        <div class="p-4 border-b border-gray-200">
          <h3 class="font-medium text-gray-800">📄 第${PipelinePage.state.selectedChapter}章 - 生成结果</h3>
        </div>
        <div class="divide-y divide-gray-100">
          ${PipelinePage.state.passes.map((p, i) => `
            <div class="p-4 hover:bg-gray-50">
              <div class="flex items-center gap-2 mb-2">
                <span class="px-2 py-0.5 text-xs font-medium rounded-full bg-blue-100 text-blue-700">第${p.pass_number || i+1}轮</span>
                <span class="text-sm font-medium">${p.pass_type || '未知'}</span>
                <span class="text-xs text-gray-400">${p.created_at ? new Date(p.created_at).toLocaleString('zh-CN') : ''}</span>
              </div>
              <div class="text-sm text-gray-600 max-h-48 overflow-y-auto bg-gray-50 rounded p-3">${PipelinePage.renderContent(p.content)}</div>
            </div>
          `).join('')}
        </div>
      `;
    },

    renderContent(content) {
      if (!content) return '<span class="text-gray-400 italic">暂无内容</span>';
      return content.length > 800 ? content.substring(0, 800) + '...' : content;
    },

    async runFullPipeline() {
      if (!PipelinePage.state.selectedChapter) return;
      const chapterNo = parseInt(PipelinePage.state.selectedChapter);
      try {
        const workspace = window.AppState.currentWorkspace;
        const project = window.AppState.currentProject;
        await window.ApiClient.callTool('pipeline.run_full', {
          workspace, project, chapter_no: chapterNo,
          plan: {}, draft_content: ''
        });
        if (window.showToast) window.showToast('success', `流水线已启动: 第${chapterNo}章`);
        PipelinePage.pollPipelineStatus(chapterNo);
      } catch (e) {
        if (window.showToast) window.showToast('error', '运行失败: ' + (e.message || ''));
      }
    },

    async pollPipelineStatus(chapterNo) {
      const check = async () => {
        try {
          const ws = window.AppState.currentWorkspace, proj = window.AppState.currentProject;
          const result = await window.ApiClient.callTool('pipeline.status', { workspace: ws, project: proj, chapter_no: chapterNo });
          if (result.status === 'running') setTimeout(check, 3000);
          else if (result.status === 'completed') {
            if (window.showToast) window.showToast('success', `第${chapterNo}章完成！`);
            PipelinePage.loadChapterPasses(chapterNo);
          }
        } catch (e) { console.error(e); }
      };
      check();
    },

    // --- 配置编辑 ---
    openConfigModal(stageId) {
      PipelinePage._editingStageId = stageId;
      const cfg = PipelinePage.getConfig(stageId);
      const name = PipelinePage.getStageName(stageId) || stageId;
      const isMultiReview = stageId === 'multi-review';
      document.getElementById('pipeline-config-title').textContent = '配置 - ' + name;

      if (isMultiReview) {
        document.getElementById('cfg-standard-fields').classList.add('hidden');
        document.getElementById('cfg-reviewer-fields').classList.remove('hidden');
        PipelinePage.renderReviewers(cfg.reviewers || []);
      } else {
        document.getElementById('cfg-reviewer-fields').classList.add('hidden');
        document.getElementById('cfg-standard-fields').classList.remove('hidden');
        document.getElementById('cfg-prompt').value = cfg.prompt || '';
        document.getElementById('cfg-model').value = cfg.model || 'default';
        document.getElementById('cfg-temperature').value = cfg.temperature ?? 0.7;
      }
      document.getElementById('cfg-enabled').checked = cfg.enabled !== false;
      document.getElementById('pipeline-config-modal').classList.remove('hidden');
      document.getElementById('pipeline-config-modal').classList.add('flex');
    },

    async renderReviewers(reviewers) {
      const list = document.getElementById('cfg-reviewer-list');
      // Load model profiles for selection
      let profiles = [];
      try {
        const ws = window.AppState.currentWorkspace, pr = window.AppState.currentProject;
        if (ws && pr) {
          const result = await window.ApiClient.callTool('model.profile.list');
          profiles = Array.isArray(result) ? result : (result?.profiles || result?.result || []);
        }
      } catch(e) { /* ignore */ }

      const modelOpts = profiles.map(p =>
        `<option value="${p.profile_key}">${p.display_name || p.profile_key} (${p.provider})</option>`
      ).join('');

      list.innerHTML = reviewers.map((r, i) => `
        <div class="p-3 border border-gray-200 rounded-lg space-y-2" data-reviewer-idx="${i}">
          <div class="flex items-center justify-between">
            <input class="text-sm font-medium border-0 bg-transparent w-40" value="${r.name}" placeholder="审查员名称"
                   onchange="PipelinePage._updateReviewer(${i}, 'name', this.value)">
            <button onclick="PipelinePage._removeReviewer(${i})" class="text-red-500 text-xs hover:text-red-700">删除</button>
          </div>
          <div class="grid grid-cols-2 gap-2">
            <select class="text-sm border rounded px-2 py-1" onchange="PipelinePage._updateReviewer(${i}, 'model', this.value)">
              <option value="">选择模型...</option>
              ${profiles.map(p =>
                `<option value="${p.profile_key}" ${p.profile_key === r.model ? 'selected' : ''}>${p.display_name || p.profile_key}</option>`
              ).join('')}
            </select>
            <select class="text-sm border rounded px-2 py-1" onchange="PipelinePage._updateReviewer(${i}, 'focus', this.value)">
              <option value="consistency" ${r.focus === 'consistency' ? 'selected' : ''}>一致性</option>
              <option value="logic" ${r.focus === 'logic' ? 'selected' : ''}>逻辑</option>
              <option value="style" ${r.focus === 'style' ? 'selected' : ''}>文风</option>
              <option value="character" ${r.focus === 'character' ? 'selected' : ''}>角色</option>
              <option value="compliance" ${r.focus === 'compliance' ? 'selected' : ''}>合规</option>
              <option value="pacing" ${r.focus === 'pacing' ? 'selected' : ''}>节奏</option>
              <option value="full" ${r.focus === 'full' ? 'selected' : ''}>全面</option>
            </select>
          </div>
          <input class="text-xs text-gray-500 border-0 bg-transparent w-full" value="${r.prompt}" placeholder="审查重点提示（可选）"
                 onchange="PipelinePage._updateReviewer(${i}, 'prompt', this.value)">
        </div>
      `).join('');
    },

    _updateReviewer(idx, field, value) {
      if (!PipelinePage._tempReviewers) PipelinePage._tempReviewers = [];
      if (!PipelinePage._tempReviewers[idx]) PipelinePage._tempReviewers[idx] = {};
      PipelinePage._tempReviewers[idx][field] = value;
    },

    _removeReviewer(idx) {
      const list = document.getElementById('cfg-reviewer-list');
      const el = list.querySelector(`[data-reviewer-idx="${idx}"]`);
      if (el) el.remove();
    },

    addReviewer() {
      const list = document.getElementById('cfg-reviewer-list');
      const idx = list.children.length;
      const div = document.createElement('div');
      div.className = 'p-3 border border-gray-200 rounded-lg space-y-2';
      div.dataset.reviewerIdx = idx;
      div.innerHTML = `
        <div class="flex items-center justify-between">
          <input class="text-sm font-medium border-0 bg-transparent w-40" placeholder="审查员名称"
                 onchange="PipelinePage._updateReviewer(${idx}, 'name', this.value)">
          <button onclick="PipelinePage._removeReviewer(${idx})" class="text-red-500 text-xs hover:text-red-700">删除</button>
        </div>
        <div class="grid grid-cols-2 gap-2">
          <select class="text-sm border rounded px-2 py-1" onchange="PipelinePage._updateReviewer(${idx}, 'model', this.value)">
            <option value="">选择模型...</option>
            ${document.querySelector('#cfg-reviewer-list select')?.innerHTML.replace('<option value="">选择模型...</option>', '') || ''}
          </select>
          <select class="text-sm border rounded px-2 py-1" onchange="PipelinePage._updateReviewer(${idx}, 'focus', this.value)">
            <option value="consistency">一致性</option>
            <option value="logic">逻辑</option>
            <option value="style">文风</option>
            <option value="character">角色</option>
            <option value="compliance">合规</option>
            <option value="pacing">节奏</option>
            <option value="full">全面</option>
          </select>
        </div>
        <input class="text-xs text-gray-500 border-0 bg-transparent w-full" placeholder="审查重点提示（可选）"
               onchange="PipelinePage._updateReviewer(${idx}, 'prompt', this.value)">
      `;
      list.appendChild(div);
    },

    closeConfigModal() {
      PipelinePage._editingStageId = null;
      PipelinePage._tempReviewers = null;
      document.getElementById('pipeline-config-modal').classList.add('hidden');
      document.getElementById('pipeline-config-modal').classList.remove('flex');
    },

    saveStageConfig() {
      const id = PipelinePage._editingStageId;
      if (!id) return;
      const isMultiReview = id === 'multi-review';
      let config;
      if (isMultiReview) {
        const reviewers = [];
        document.querySelectorAll('#cfg-reviewer-list > div').forEach((el, i) => {
          const name = el.querySelector('input:first-child')?.value || `审查员${i + 1}`;
          const model = el.querySelector('select')?.value || '';
          const focus = el.querySelectorAll('select')[1]?.value || 'consistency';
          const prompt = el.querySelector('input:last-child')?.value || '';
          if (model) reviewers.push({ model, focus, name, prompt, weight: 1 });
        });
        config = { reviewers, enabled: document.getElementById('cfg-enabled').checked };
      } else {
        config = {
          prompt: document.getElementById('cfg-prompt').value,
          model: document.getElementById('cfg-model').value,
          temperature: parseFloat(document.getElementById('cfg-temperature').value) || 0.7,
          enabled: document.getElementById('cfg-enabled').checked
        };
      }
      PipelinePage.saveConfig(id, config);
      if (window.showToast) window.showToast('success', '配置已保存');
      PipelinePage.closeConfigModal();
      PipelinePage.render();
      PipelinePage.loadData();
    },

    getStageName(stageId) {
      for (const section of PipelinePage.defaultStages) {
        const found = section.stages.find(s => s.id === stageId);
        if (found) return found.name;
      }
      return null;
    }
  };
})();