/**
 * Novel OS - Pipeline Page
 * 流水线管理页面
 */
(function() {
  'use strict';

  window.PipelinePage = {
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
              <h1 class="text-2xl font-bold text-gray-800">${t('nav.pipeline')}</h1>
              <p class="text-gray-500 mt-1">管理章节生成流水线</p>
            </div>
            <div class="flex gap-2">
              <button onclick="PipelinePage.showRunModal()" 
                      class="px-4 py-2 bg-primary-600 text-white rounded-lg hover:bg-primary-700 transition-colors">
                运行流水线
              </button>
            </div>
          </div>

          <div class="bg-white rounded-lg shadow p-4">
            <h3 class="font-medium text-gray-700 mb-4">流水线阶段</h3>
            <div class="flex items-center justify-between">
              <div class="flex items-center gap-2">
                <div class="w-12 h-12 rounded-full bg-blue-100 flex items-center justify-center text-blue-600 font-bold">1</div>
                <div>
                  <div class="font-medium text-sm">大纲</div>
                  <div class="text-xs text-gray-500">生成章节大纲</div>
                </div>
              </div>
              <div class="flex-1 h-1 bg-gray-200 mx-4"><div class="h-full bg-blue-500" style="width: 100%"></div></div>
              
              <div class="flex items-center gap-2">
                <div class="w-12 h-12 rounded-full bg-green-100 flex items-center justify-center text-green-600 font-bold">2</div>
                <div>
                  <div class="font-medium text-sm">初稿</div>
                  <div class="text-xs text-gray-500">生成章节内容</div>
                </div>
              </div>
              <div class="flex-1 h-1 bg-gray-200 mx-4"><div class="h-full bg-green-500" style="width: 100%"></div></div>
              
              <div class="flex items-center gap-2">
                <div class="w-12 h-12 rounded-full bg-purple-100 flex items-center justify-center text-purple-600 font-bold">3</div>
                <div>
                  <div class="font-medium text-sm">润色</div>
                  <div class="text-xs text-gray-500">优化文本质量</div>
                </div>
              </div>
              <div class="flex-1 h-1 bg-gray-200 mx-4"><div class="h-full bg-purple-500" style="width: 100%"></div></div>
              
              <div class="flex items-center gap-2">
                <div class="w-12 h-12 rounded-full bg-orange-100 flex items-center justify-center text-orange-600 font-bold">4</div>
                <div>
                  <div class="font-medium text-sm">验证</div>
                  <div class="text-xs text-gray-500">校验内容一致性</div>
                </div>
              </div>
            </div>
          </div>

          <div id="pipeline-list-container" class="bg-white rounded-lg shadow">
            <div class="p-8 text-center text-gray-500">
              <p>选择章节查看流水线状态</p>
            </div>
          </div>
        </div>

        <!-- 运行流水线模态框 -->
        <div id="pipeline-run-modal" class="fixed inset-0 bg-black/50 z-50 hidden flex items-center justify-center">
          <div class="bg-white rounded-lg shadow-xl w-full max-w-md mx-4">
            <div class="px-6 py-4 border-b border-gray-200 flex items-center justify-between">
              <h3 class="text-lg font-semibold">运行流水线</h3>
              <button onclick="PipelinePage.hideRunModal()" class="text-gray-400 hover:text-gray-600">
                <svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12"/>
                </svg>
              </button>
            </div>
            <div class="p-6">
              <div class="space-y-4">
                <div>
                  <label class="block text-sm font-medium text-gray-700 mb-1">章节号 <span class="text-red-500">*</span></label>
                  <input type="number" id="pipeline-chapter-no" required min="1"
                         class="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary-500">
                </div>
                <div>
                  <label class="block text-sm font-medium text-gray-700 mb-1">运行阶段</label>
                  <select id="pipeline-pass" class="w-full px-3 py-2 border border-gray-300 rounded-lg">
                    <option value="full">完整流水线（4轮）</option>
                    <option value="1">仅大纲</option>
                    <option value="2">仅初稿</option>
                    <option value="3">仅润色</option>
                    <option value="4">仅验证</option>
                  </select>
                </div>
              </div>
              <div class="mt-6 flex justify-end gap-3">
                <button type="button" onclick="PipelinePage.hideRunModal()" 
                        class="px-4 py-2 border border-gray-300 rounded-lg hover:bg-gray-50">
                  ${t('common.cancel')}
                </button>
                <button onclick="PipelinePage.runPipeline()" 
                        class="px-4 py-2 bg-primary-600 text-white rounded-lg hover:bg-primary-700">
                  运行
                </button>
              </div>
            </div>
          </div>
        </div>
      `;
    },

    async loadData() {
      try {
        const workspace = window.AppState.currentWorkspace;
        const project = window.AppState.currentProject;
        
        if (!workspace || !project) return;

        const chapters = await window.ApiClient.localChapter.list(project);
        this.renderChapterList(chapters || []);
      } catch (error) {
        console.error('[Pipeline] Load error:', error);
      }
    },

    renderChapterList(chapters) {
      const container = document.getElementById('pipeline-list-container');
      
      if (!chapters || chapters.length === 0) {
        container.innerHTML = `<div class="p-8 text-center text-gray-500">暂无章节数据</div>`;
        return;
      }

      container.innerHTML = `
        <div class="divide-y divide-gray-200">
          ${chapters.slice(0, 20).map(ch => `
            <div class="p-4 hover:bg-gray-50 transition-colors cursor-pointer" onclick="PipelinePage.viewPasses(${ch.chapter_no})">
              <div class="flex items-center justify-between">
                <div class="flex items-center gap-3">
                  <span class="font-medium text-gray-800">第${ch.chapter_no}章</span>
                  <span class="text-sm text-gray-500">${ch.title || '未命名'}</span>
                </div>
                <div class="flex items-center gap-2">
                  <span class="px-2 py-0.5 text-xs rounded-full ${this.getStatusClass(ch.status)}">
                    ${ch.status}
                  </span>
                  <span class="text-xs text-gray-400">${ch.word_count || 0}字</span>
                </div>
              </div>
            </div>
          `).join('')}
        </div>
      `;
    },

    async viewPasses(chapterNo) {
      try {
        const project = window.AppState.currentProject;
        const passes = await window.ApiClient.pipeline.getPasses(project, chapterNo);
        
        const container = document.getElementById('pipeline-list-container');
        container.innerHTML = `
          <div class="p-4 border-b border-gray-200">
            <div class="flex items-center justify-between">
              <h3 class="font-medium text-gray-800">第${chapterNo}章 - 生成轮次</h3>
              <button onclick="PipelinePage.loadData()" class="text-sm text-primary-600 hover:underline">返回列表</button>
            </div>
          </div>
          <div class="p-4">
            ${(!passes || passes.length === 0) ? '<p class="text-gray-500">暂无生成记录</p>' : 
              passes.map(p => `
                <div class="mb-4 p-3 bg-gray-50 rounded-lg">
                  <div class="flex items-center gap-2 mb-2">
                    <span class="px-2 py-0.5 text-xs rounded-full bg-blue-100 text-blue-700">第${p.pass_number}轮</span>
                    <span class="text-sm font-medium">${p.pass_type}</span>
                    <span class="text-xs text-gray-400">${p.created_at ? new Date(p.created_at).toLocaleString() : ''}</span>
                  </div>
                  <div class="text-sm text-gray-600 max-h-40 overflow-y-auto">${p.content ? p.content.substring(0, 500) + '...' : '暂无内容'}</div>
                </div>
              `).join('')}
          </div>
        `;
      } catch (error) {
        alert('加载失败: ' + error.message);
      }
    },

    showRunModal() {
      document.getElementById('pipeline-chapter-no').value = '';
      document.getElementById('pipeline-pass').value = 'full';
      document.getElementById('pipeline-run-modal').classList.remove('hidden');
    },

    hideRunModal() {
      document.getElementById('pipeline-run-modal').classList.add('hidden');
    },

    async runPipeline() {
      const chapterNo = document.getElementById('pipeline-chapter-no').value;
      if (!chapterNo) {
        alert('请输入章节号');
        return;
      }

      try {
        const project = window.AppState.currentProject;
        alert('流水线任务已提交（功能开发中）');
        this.hideRunModal();
      } catch (error) {
        alert('运行失败: ' + error.message);
      }
    },

    getStatusClass(status) {
      const classes = {
        draft: 'bg-yellow-100 text-yellow-700',
        final: 'bg-green-100 text-green-700',
        published: 'bg-purple-100 text-purple-700'
      };
      return classes[status] || 'bg-gray-100 text-gray-600';
    }
  };
})();
