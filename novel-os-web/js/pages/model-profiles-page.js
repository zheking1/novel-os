/**
 * Novel OS - Model Profiles Page
 * 模型配置管理页面
 */
(function() {
  'use strict';

  window.ModelProfilesPage = {
    init() {
      this.render();
      this.loadData();
      return true;
    },

    render() {
      const contentArea = document.getElementById('content-area');
      contentArea.innerHTML = `
        <div class="space-y-4">
          <div class="flex items-center justify-between">
            <div>
              <h1 class="text-2xl font-bold text-gray-800">${t('nav.modelProfiles')}</h1>
              <p class="text-gray-500 mt-1">配置AI模型和路由</p>
            </div>
            <button onclick="ModelProfilesPage.showCreateModal()" 
                    class="px-4 py-2 bg-primary-600 text-white rounded-lg hover:bg-primary-700 transition-colors">
              ${t('common.new')} 模型配置
            </button>
          </div>

          <div id="models-container" class="bg-white rounded-lg shadow">
            <div class="p-8 text-center text-gray-500">
              <div class="spinner w-8 h-8 border-4 border-primary-600 border-t-transparent rounded-full animate-spin mx-auto"></div>
              <p class="mt-2">${t('common.loading')}</p>
            </div>
          </div>
        </div>

        <!-- 模态框 -->
        <div id="model-modal" class="fixed inset-0 bg-black/50 z-50 hidden flex items-center justify-center">
          <div class="bg-white rounded-lg shadow-xl w-full max-w-2xl mx-4 max-h-[90vh] overflow-hidden">
            <div class="px-6 py-4 border-b border-gray-200 flex items-center justify-between">
              <h3 id="model-modal-title" class="text-lg font-semibold">新建模型配置</h3>
              <button onclick="ModelProfilesPage.hideModal()" class="text-gray-400 hover:text-gray-600">
                <svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12"/>
                </svg>
              </button>
            </div>
            <div class="p-6 overflow-y-auto max-h-[60vh]">
              <form onsubmit="ModelProfilesPage.saveProfile(event)">
                <input type="hidden" id="model-id">
                <div class="space-y-4">
                  <div class="grid grid-cols-2 gap-4">
                    <div>
                      <label class="block text-sm font-medium text-gray-700 mb-1">配置键名 <span class="text-red-500">*</span></label>
                      <input type="text" id="model-key" required placeholder="如: siliconflow-qwen"
                             class="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary-500 font-mono">
                    </div>
                    <div>
                      <label class="block text-sm font-medium text-gray-700 mb-1">显示名称 <span class="text-red-500">*</span></label>
                      <input type="text" id="model-display-name" required placeholder="硅基流动 Qwen2.5"
                             class="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary-500">
                    </div>
                  </div>
                  <div class="grid grid-cols-2 gap-4">
                    <div>
                      <label class="block text-sm font-medium text-gray-700 mb-1">Provider <span class="text-red-500">*</span></label>
                      <select id="model-provider" required
                              class="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary-500">
                        <option value="openai">OpenAI</option>
                        <option value="anthropic">Anthropic</option>
                        <option value="google">Google</option>
                        <option value="siliconflow">硅基流动 (SiliconFlow)</option>
                        <option value="alibaba">阿里云百炼</option>
                        <option value="deepseek">DeepSeek</option>
                        <option value="zhipu">智谱AI (GLM)</option>
                        <option value="moonshot">月之暗面 (Kimi)</option>
                        <option value="azure">Azure</option>
                        <option value="custom">自定义</option>
                      </select>
                    </div>
                    <div>
                      <label class="block text-sm font-medium text-gray-700 mb-1">模型名称 <span class="text-red-500">*</span></label>
                      <input type="text" id="model-name" required placeholder="如: Qwen/Qwen2.5-7B-Instruct"
                             class="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary-500 font-mono">
                    </div>
                  </div>
                  <div>
                    <label class="block text-sm font-medium text-gray-700 mb-1">API Base URL</label>
                    <input type="text" id="model-api-url" placeholder="如: https://api.siliconflow.cn"
                           class="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary-500 font-mono text-sm">
                  </div>
                  <div>
                    <label class="block text-sm font-medium text-gray-700 mb-1">API Key</label>
                    <input type="password" id="model-api-key" placeholder="sk-xxxxxxxx"
                           class="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary-500 font-mono text-sm">
                  </div>
                  <div>
                    <label class="block text-sm font-medium text-gray-700 mb-2">任务类型 (可多选)</label>
                    <div id="model-task-types" class="flex flex-wrap gap-2">
                      ${[
                        {v:'embedding',l:'Embedding 向量化'},
                        {v:'rerank',l:'Rerank 重排序'},
                        {v:'outline',l:'大纲生成'},
                        {v:'draft',l:'初稿生成'},
                        {v:'polish',l:'润色优化'},
                        {v:'review',l:'审核/审查'},
                        {v:'analysis',l:'深度分析'},
                        {v:'context',l:'上下文压缩'}
                      ].map(t => `<label class="px-2 py-1 text-xs rounded border cursor-pointer hover:bg-gray-50">
                        <input type="checkbox" value="${t.v}" class="task-type-check"> ${t.l}</label>`).join('')}
                    </div>
                  </div>
                  <div id="task-temperatures-section" class="hidden">
                    <label class="block text-sm font-medium text-gray-700 mb-2">任务温度 (按任务类型分别设置)</label>
                    <div id="task-temperatures" class="space-y-2">
                      ${['outline','draft','polish','review','analysis','context','embedding','rerank'].map(t => {
                        const labels = {outline:'大纲生成',draft:'初稿生成',polish:'润色优化',review:'审核审查',analysis:'深度分析',context:'上下文压缩',embedding:'向量化',rerank:'重排序'};
                        return '<div class="task-temp-row flex items-center gap-2 hidden" data-task="'+t+'"><span class="text-xs text-gray-500 w-16 text-right">'+labels[t].substring(0,4)+'</span><input type="range" min="0" max="2" step="0.1" value="0.7" class="task-temp-slider flex-1" oninput="this.nextElementSibling.textContent=this.value"><span class="task-temp-value text-xs text-gray-600 w-8">0.7</span></div>';
                      }).join('')}
                    </div>
                  </div>
                  <div class="grid grid-cols-2 gap-4">
                    <div>
                      <label class="block text-sm font-medium text-gray-700 mb-1">层级</label>
                      <select id="model-tier" 
                              class="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary-500">
                        <option value="standard">标准</option>
                        <option value="premium">高级</option>
                        <option value="budget">经济</option>
                      </select>
                    </div>
                    <div>
                      <label class="block text-sm font-medium text-gray-700 mb-1">默认</label>
                      <select id="model-is-default" 
                              class="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary-500">
                        <option value="false">否</option>
                        <option value="true">是</option>
                      </select>
                    </div>
                  </div>
                </div>
                <div class="mt-6 flex justify-end gap-3">
                  <button type="button" onclick="ModelProfilesPage.hideModal()" 
                          class="px-4 py-2 border border-gray-300 rounded-lg hover:bg-gray-50">
                    ${t('common.cancel')}
                  </button>
                  <button type="submit" id="model-profiles-save-btn" class="px-4 py-2 bg-primary-600 text-white rounded-lg hover:bg-primary-700">
                    ${t('common.save')}
                  </button>
                </div>
              </form>
            </div>
          </div>
        </div>
      `;
      this._bindEvents();
    },

    _bindEvents() {
      setTimeout(() => {
        document.querySelectorAll('.task-type-check').forEach(cb => {
          cb.addEventListener('change', function() {
            const row = document.querySelector('.task-temp-row[data-task="' + this.value + '"]');
            const section = document.getElementById('task-temperatures-section');
            if (row) {
              row.classList.toggle('hidden', !this.checked);
              const any = document.querySelectorAll('.task-type-check:checked').length > 0;
              section.classList.toggle('hidden', !any);
            }
          });
        });
      }, 100);
    },

    async loadData() {
      const container = document.getElementById('models-container');
      try {
        const workspace = window.AppState.currentWorkspace || 'default';
        const result = await window.ApiClient.callTool('model.profile.list');
        this.renderList(result || []);
      } catch (error) {
        console.error('[ModelProfiles] Load error:', error);
        container.innerHTML = `<div class="p-8 text-center text-red-500">加载失败: ${error.message}</div>`;
      }
    },

    renderList(profiles) {
      const container = document.getElementById('models-container');
      
      if (!profiles || profiles.length === 0) {
        container.innerHTML = `
          <div class="p-8 text-center text-gray-500">
            <div class="text-4xl mb-2">🤖</div>
            <p>暂无模型配置</p>
            <p class="text-sm mt-2">点击右上角按钮添加模型</p>
          </div>
        `;
        return;
      }

      container.innerHTML = `
        <div class="divide-y divide-gray-200">
          ${profiles.map(profile => {
            const types = Array.isArray(profile.task_types) ? profile.task_types : [];
            const params = typeof profile.default_params === 'string'
              ? JSON.parse(profile.default_params) : (profile.default_params || {});
            const typeLabels = { embedding: '向量化', rerank: '重排序', outline: '大纲', draft: '初稿', polish: '润色', review: '审核', analysis: '分析', context: '压缩' };
            const temps = params.task_temperatures || {};
            return `
            <div class="p-4 hover:bg-gray-50 transition-colors">
              <div class="flex items-start justify-between">
                <div class="flex-1 min-w-0">
                  <div class="flex items-center gap-2">
                    <span class="text-lg">🤖</span>
                    <h3 class="font-medium text-gray-800">${profile.display_name || profile.profile_key}</h3>
                    <span class="px-2 py-0.5 text-xs rounded-full bg-blue-100 text-blue-700">${profile.provider}</span>
                    <span class="text-xs text-gray-400 font-mono">${profile.model_name}</span>
                    ${profile.is_default ? '<span class="px-2 py-0.5 text-xs rounded-full bg-green-100 text-green-700">默认</span>' : ''}
                  </div>
                  <div class="flex items-center gap-2 mt-2 flex-wrap">
                    ${types.map(t => {
                      const tlabel = typeLabels[t] || t;
                      const temp = temps[t];
                      return '<span class="px-1.5 py-0.5 text-xs rounded bg-gray-100 text-gray-600">' + tlabel + (temp != null ? ' t=' + temp : '') + '</span>';
                    }).join('')}
                  </div>
                  <div class="flex items-center gap-4 mt-1 text-xs text-gray-400">
                    <span>键名: ${profile.profile_key}</span>
                    <span>层级: ${profile.tier || 'standard'}</span>
                    <span>状态: ${profile.status}</span>
                    ${params.api_url ? `<span>端点: ${params.api_url}</span>` : ''}
                  </div>
                </div>
                <div class="flex items-center gap-2 ml-4">
                  <button onclick="ModelProfilesPage.editProfile('${profile.id}')" 
                          class="p-2 text-gray-400 hover:text-primary-600 hover:bg-primary-50 rounded transition-colors">
                    <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M11 5H6a2 2 0 00-2 2v11a2 2 0 002 2h11a2 2 0 002-2v-5m-1.414-9.414a2 2 0 112.828 2.828L11.828 15H9v-2.828l8.586-8.586z"/>
                    </svg>
                  </button>
                  <button onclick="ModelProfilesPage.deleteProfile('${profile.id}', '${profile.profile_key}')" 
                          class="p-2 text-gray-400 hover:text-red-600 hover:bg-red-50 rounded transition-colors" title="删除">
                    <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16"/>
                    </svg>
                  </button>
                </div>
              </div>
            </div>
          `; }).join('')}
        </div>
      `;
    },

    showCreateModal() {
      document.getElementById('model-modal-title').textContent = '新建模型配置';
      document.getElementById('model-id').value = '';
      document.getElementById('model-key').value = '';
      document.getElementById('model-display-name').value = '';
      document.getElementById('model-provider').value = 'openai';
      document.getElementById('model-name').value = '';
      document.getElementById('model-api-url').value = '';
      document.getElementById('model-api-key').value = '';
      document.querySelectorAll('.task-type-check').forEach(c => c.checked = false);
      document.querySelectorAll('.task-temp-row').forEach(r => r.classList.add('hidden'));
      document.getElementById('task-temperatures-section').classList.add('hidden');
      document.getElementById('model-tier').value = 'standard';
      document.getElementById('model-is-default').value = 'false';
      document.getElementById('model-modal').classList.remove('hidden');
    },

    hideModal() {
      document.getElementById('model-modal').classList.add('hidden');
    },

    async editProfile(id) {
      try {
        const workspace = window.AppState.currentWorkspace || 'default';
        const profiles = await window.ApiClient.callTool('model.profile.list');
        const profile = profiles.find(p => p.id === id);
        
        if (!profile) throw new Error('Profile not found');
        
        document.getElementById('model-modal-title').textContent = '编辑模型配置';
        document.getElementById('model-id').value = profile.id;
        document.getElementById('model-key').value = profile.profile_key;
        document.getElementById('model-display-name').value = profile.display_name;
        document.getElementById('model-provider').value = profile.provider;
        document.getElementById('model-name').value = profile.model_name;

        const params = typeof profile.default_params === 'string'
          ? JSON.parse(profile.default_params) : (profile.default_params || {});
        document.getElementById('model-api-url').value = params.api_url || '';
        document.getElementById('model-api-key').value = params.api_key || '';

        document.querySelectorAll('.task-type-check').forEach(c => c.checked = false);
        const types = Array.isArray(profile.task_types) ? profile.task_types : [];
        types.forEach(t => {
          const cb = document.querySelector('.task-type-check[value="' + t + '"]');
          if (cb) cb.checked = true;
        });

        // Restore per-task temperatures
        const temps = params.task_temperatures || {};
        document.querySelectorAll('.task-temp-row').forEach(r => {
          const task = r.getAttribute('data-task');
          if (temps[task] != null) {
            const slider = r.querySelector('.task-temp-slider');
            const label = r.querySelector('.task-temp-value');
            if (slider) slider.value = temps[task];
            if (label) label.textContent = temps[task];
          }
          r.classList.toggle('hidden', !types.includes(task));
        });
        document.getElementById('task-temperatures-section').classList.toggle('hidden', types.length === 0);

        document.getElementById('model-tier').value = profile.tier || 'standard';
        document.getElementById('model-is-default').value = profile.is_default ? 'true' : 'false';
        document.getElementById('model-modal').classList.remove('hidden');
      } catch (error) {
        alert('加载配置失败: ' + error.message);
      }
    },

    async saveProfile(e) {
      e.preventDefault();
      const workspace = window.AppState.currentWorkspace;
      const project = window.AppState.currentProject;

      const task_types = [];
      document.querySelectorAll('.task-type-check:checked').forEach(c => task_types.push(c.value));

      const api_url = document.getElementById('model-api-url').value.trim();
      const api_key = document.getElementById('model-api-key').value.trim();
      const default_params = {};
      if (api_url) default_params.api_url = api_url;
      if (api_key) default_params.api_key = api_key;

      // Collect per-task temperatures
      const temps = {};
      document.querySelectorAll('.task-temp-row:not(.hidden)').forEach(r => {
        const task = r.getAttribute('data-task');
        temps[task] = parseFloat(r.querySelector('.task-temp-slider').value);
      });
      if (Object.keys(temps).length > 0) {
        default_params.task_temperatures = temps;
      }

      const data = {
        profile_key: document.getElementById('model-key').value,
        display_name: document.getElementById('model-display-name').value,
        provider: document.getElementById('model-provider').value,
        model_name: document.getElementById('model-name').value,
        task_types: task_types,
        default_params: default_params,
        tier: document.getElementById('model-tier').value,
        is_default: document.getElementById('model-is-default').value === 'true'
      };

      try {
        await window.ApiClient.callTool('model.profile.upsert', data);
        window.showToast && window.showToast('success', '模型配置已保存');
        this.hideModal();
        this.loadData();
      } catch (error) {
        alert('保存失败: ' + error.message);
      }
    },

    async deleteProfile(id, key) {
      if (!confirm('确定删除模型配置 "' + key + '" 吗？')) return;
      
      try {
        const workspace = window.AppState.currentWorkspace;
        const project = window.AppState.currentProject;
        
        await window.ApiClient.callTool('model.profile.upsert', {
          workspace, project,
          profile_key: key,
          status: 'inactive'
        });
        
        this.loadData();
        
        if (window.showToast) {
          window.showToast('success', '已删除模型配置: ' + key);
        }
      } catch (error) {
        console.error('[ModelProfiles] Delete error:', error);
        alert('删除失败: ' + (error.message || '未知错误'));
      }
    }
  };
})();