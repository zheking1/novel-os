/**
 * Review Council Config Page
 * 审核委员会配置 - 模型选择、维度分配、并行/串行
 */
(function() {
  'use strict';

  window.ReviewCouncilPage = {
    config: {},
    reviewModels: [],

    init() { this.render(); this.loadData(); return true; },

    render() {
      document.getElementById('content-area').innerHTML = `
        <div class="space-y-6 max-w-3xl">
          <div class="flex items-center justify-between">
            <div>
              <h1 class="text-2xl font-bold text-gray-800">审核委员会</h1>
              <p class="text-gray-500 mt-1" id="council-scope">个人审核委员会配置</p>
            </div>
            <button id="council-save-btn" onclick="ReviewCouncilPage.save()" class="px-4 py-2 bg-primary-600 text-white rounded-lg hover:bg-primary-700 text-sm" disabled>保存配置</button>
          </div>

          <div id="council-content" class="bg-white rounded-lg shadow p-6">
            <div class="text-center text-gray-500 py-4">加载中...</div>
          </div>

          <div class="bg-blue-50 border border-blue-200 rounded-lg p-4 text-sm text-blue-700">
            <strong>说明</strong>：每个用户有自己的审核委员会配置，所有项目共用。<br>
            - <strong>AI 痕迹检测</strong>：每个模型审核时自动附带，无需单独分配<br>
            - <strong>并行</strong>：所有模型同时审核 | <strong>串行</strong>：逐模型依次审核（适合有 RPM 限制的 API）
          </div>
        </div>
      `;
    },

    async loadData() {
      const container = document.getElementById('council-content');
      try {
        const result = await window.ApiClient.callTool('review.list_council_configs') || [];
        const modelsRaw = await window.ApiClient.callTool('model.profile.list').catch(() => []);
        const models = Array.isArray(modelsRaw) ? modelsRaw : (modelsRaw?.profiles || modelsRaw?.items || modelsRaw?.results || []);
        this.reviewModels = models.filter(m => m.task_types && m.task_types.indexOf('review') >= 0);

        const existing = result.length > 0 && result[0];
        const cfg = existing && existing.config
          ? (typeof existing.config === 'string' ? JSON.parse(existing.config) : existing.config)
          : null;

        this.config = {
          model_count: cfg?.model_count || Math.min(3, this.reviewModels.length || 1),
          dimensions_per_model: cfg?.dimensions_per_model || 1,
          review_mode: cfg?.review_mode || 'serial',
          is_active: existing?.is_active ?? true,
          reviewers: cfg?.reviewers || [],
        };

        this.renderForm();
        document.getElementById('council-save-btn').disabled = false;
      } catch(e) {
        container.innerHTML = '<div class="p-6 text-center text-red-500">加载失败: ' + (e.message || '未知') + '</div>';
      }
    },

    renderForm() {
      const container = document.getElementById('council-content');
      const c = this.config;

      const modelRowsHtml = this.reviewModels.map((m, i) => {
        const assigned = (c.reviewers || []).find(r => r.model === m.profile_key);
        const checked = assigned ? 'checked' : '';
        const focus = assigned?.focus || '';
        const dims = ['设定一致性', '文笔质量', '节奏控制', '角色行为一致性'];
        const selectedDims = focus ? focus.split(',').map(s => s.trim()).filter(Boolean) : [];
        const dimTagsHtml = selectedDims.map((d, di) => `
          <span class="inline-flex items-center gap-1 px-2 py-0.5 bg-blue-100 text-blue-700 text-xs rounded">
            ${d}<button onclick="this.parentElement.remove()" class="text-blue-400 hover:text-blue-600">&times;</button>
          </span>`).join('');

        const dimOptionsHtml = dims.filter(d => !selectedDims.includes(d)).map(d => `
          <option value="${d}">${d}</option>`).join('');

        return `
          <div class="flex items-center gap-3 p-2 bg-gray-50 rounded">
            <input type="checkbox" value="${m.profile_key}" class="reviewer-checkbox" data-idx="${i}" ${checked}
                   onchange="ReviewCouncilPage.onModelToggle(this)">
            <span class="text-sm font-medium flex-1">${m.display_name || m.profile_key}</span>
            <span class="text-xs text-gray-400">${m.profile_key}</span>
            <div class="flex items-center gap-2 flex-1">
              <select class="reviewer-dim-select px-2 py-1 border border-gray-300 rounded text-sm"
                      onchange="ReviewCouncilPage.addDim(this, '${m.profile_key}')" ${checked ? '' : 'disabled'}>
                <option value="">+ 添加维度</option>
                ${dimOptionsHtml}
              </select>
              <div class="reviewer-dims flex flex-wrap gap-1" data-model="${m.profile_key}">${dimTagsHtml}</div>
            </div>
          </div>`;
      }).join('');

      container.innerHTML = `
        <div class="space-y-6">
          <div>
            <label class="block text-sm font-medium text-gray-700 mb-2">选择审核模型</label>
            <p class="text-xs text-gray-400 mb-2">勾选参与审核的模型，可选填审核维度（如"设定一致性"/"文笔质量"）</p>
            <div class="space-y-2 max-h-64 overflow-y-auto">
              ${modelRowsHtml}
            </div>
            <p class="text-xs text-gray-400 mt-1">可用 review 模型：${this.reviewModels.length} 个</p>
          </div>

          <div>
            <label class="block text-sm font-medium text-gray-700 mb-1">审核委员会模型数量 <span class="text-xs text-gray-400">(前N个模型被激活)</span></label>
            <div class="flex items-center gap-3">
              <input type="range" id="cfg-model-count" min="1" max="${this.reviewModels.length || 1}" value="${c.model_count}" class="flex-1" oninput="document.getElementById('cfg-model-count-val').textContent=this.value">
              <span id="cfg-model-count-val" class="text-sm font-medium text-gray-800 w-8">${c.model_count}</span>
            </div>
          </div>

          <div>
            <label class="block text-sm font-medium text-gray-700 mb-1">每个模型负责维度数（4个创作维度 + AI痕迹）</label>
            <div class="flex items-center gap-3">
              <input type="range" id="cfg-dims-per-model" min="1" max="4" value="${c.dimensions_per_model}" class="flex-1" oninput="document.getElementById('cfg-dims-per-model-val').textContent=this.value">
              <span id="cfg-dims-per-model-val" class="text-sm font-medium text-gray-800 w-8">${c.dimensions_per_model}</span>
            </div>
          </div>

          <div>
            <label class="block text-sm font-medium text-gray-700 mb-2">审核模式</label>
            <div class="flex gap-4">
              <label class="flex items-center gap-2 cursor-pointer">
                <input type="radio" name="review-mode" value="parallel" ${c.review_mode === 'parallel' ? 'checked' : ''} class="text-primary-600">
                <span class="text-sm">并行（所有模型同时审核）</span>
              </label>
              <label class="flex items-center gap-2 cursor-pointer">
                <input type="radio" name="review-mode" value="serial" ${c.review_mode === 'serial' ? 'checked' : ''} class="text-primary-600">
                <span class="text-sm">串行（逐模型依次审核）</span>
              </label>
            </div>
          </div>
        </div>
      `;
    },

    onModelToggle(checkbox) {
      const modelKey = checkbox.value;
      const dimSelect = document.querySelector(`.reviewer-dim-select[onchange*="${modelKey}"]`);
      if (checkbox.checked) {
        dimSelect && (dimSelect.disabled = false);
      } else {
        dimSelect && (dimSelect.disabled = true);
        const dimsContainer = document.querySelector(`.reviewer-dims[data-model="${modelKey}"]`);
        if (dimsContainer) dimsContainer.innerHTML = '';
      }
    },

    addDim(select, modelKey) {
      const dimValue = select.value;
      if (!dimValue) return;
      const dimsContainer = document.querySelector(`.reviewer-dims[data-model="${modelKey}"]`);
      if (!dimsContainer) return;

      const tag = document.createElement('span');
      tag.className = 'inline-flex items-center gap-1 px-2 py-0.5 bg-blue-100 text-blue-700 text-xs rounded';
      tag.innerHTML = dimValue + '<button onclick="this.parentElement.remove()" class="text-blue-400 hover:text-blue-600">&times;</button>';
      dimsContainer.appendChild(tag);

      const selectedDims = Array.from(dimsContainer.children).map(t => t.textContent.replace('×', '').trim());
      select.innerHTML = '<option value="">+ 添加维度</option>' +
        ['设定一致性', '文笔质量', '节奏控制', '角色行为一致性']
          .filter(d => !selectedDims.includes(d))
          .map(d => `<option value="${d}">${d}</option>`).join('');
      select.value = '';
    },

    async save() {
      try {
        const reviewers = [];
        document.querySelectorAll('.reviewer-checkbox:checked').forEach(cb => {
          const modelKey = cb.value;
          const dimsContainer = document.querySelector(`.reviewer-dims[data-model="${modelKey}"]`);
          const focus = dimsContainer
            ? Array.from(dimsContainer.children).map(t => t.textContent.replace('×', '').trim()).join(',')
            : '';
          reviewers.push({
            model: modelKey,
            focus: focus,
            weight: 1
          });
        });

        if (reviewers.length === 0) {
          alert('请至少勾选一个审核模型');
          return;
        }

        const config = {
          reviewers: reviewers,
          model_count: parseInt(document.getElementById('cfg-model-count').value),
          dimensions_per_model: parseInt(document.getElementById('cfg-dims-per-model').value),
          review_mode: document.querySelector('input[name="review-mode"]:checked').value,
          is_active: true
        };

        await window.ApiClient.callTool('review.upsert_council_config', {
          name: '默认审核委员会',
          config: config,
          is_active: true
        });
        window.showToast && window.showToast('success', '审核委员会配置已保存');
        this.loadData();
      } catch(e) {
        alert('保存失败: ' + (e.message || '未知错误'));
      }
    }
  };
})();