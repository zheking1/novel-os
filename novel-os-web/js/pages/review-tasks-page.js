/**
 * Novel OS - Review Tasks Page
 * 审核任务页面
 */
(function() {
  'use strict';

  window.ReviewTasksPage = {
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
              <h1 class="text-2xl font-bold text-gray-800">${t('nav.reviewTasks')}</h1>
              <p class="text-gray-500 mt-1">管理章节审核任务</p>
            </div>
            <div class="flex gap-2">
              <button onclick="ReviewTasksPage.showStartModal()" 
                      class="px-4 py-2 bg-primary-600 text-white rounded-lg hover:bg-primary-700 transition-colors">
                ${t('common.new')} 审核任务
              </button>
            </div>
          </div>

          <div class="flex gap-4 items-center">
            <select id="review-status-filter" onchange="ReviewTasksPage.loadData()" 
                    class="px-4 py-2 border border-gray-300 rounded-lg">
              <option value="">全部状态</option>
              <option value="pending">待审核</option>
              <option value="running">审核中</option>
              <option value="completed">已完成</option>
              <option value="failed">失败</option>
            </select>
          </div>

          <div id="review-list-container" class="bg-white rounded-lg shadow">
            <div class="p-8 text-center text-gray-500">
              <div class="spinner w-8 h-8 border-4 border-primary-600 border-t-transparent rounded-full animate-spin mx-auto"></div>
              <p class="mt-2">${t('common.loading')}</p>
            </div>
          </div>
        </div>

        <!-- 创建审核任务模态框 -->
        <div id="review-start-modal" class="fixed inset-0 bg-black/50 z-50 hidden flex items-center justify-center">
          <div class="bg-white rounded-lg shadow-xl w-full max-w-md mx-4">
            <div class="px-6 py-4 border-b border-gray-200 flex items-center justify-between">
              <h3 class="text-lg font-semibold">新建审核任务</h3>
              <button onclick="ReviewTasksPage.hideStartModal()" class="text-gray-400 hover:text-gray-600">
                <svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12"/>
                </svg>
              </button>
            </div>
            <div class="p-6">
              <div class="space-y-4">
                <div>
                  <label class="block text-sm font-medium text-gray-700 mb-1">章节号 <span class="text-red-500">*</span></label>
                  <input type="number" id="review-chapter-no" required min="1"
                         class="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary-500">
                </div>
                <div>
                  <label class="block text-sm font-medium text-gray-700 mb-1">审核维度</label>
                  <div class="space-y-2">
                    <label class="flex items-center">
                      <input type="checkbox" value="consistency" checked class="mr-2"> 一致性
                    </label>
                    <label class="flex items-center">
                      <input type="checkbox" value="quality" checked class="mr-2"> 质量
                    </label>
                    <label class="flex items-center">
                      <input type="checkbox" value="pacing" class="mr-2"> 节奏
                    </label>
                    <label class="flex items-center">
                      <input type="checkbox" value="character" class="mr-2"> 角色
                    </label>
                  </div>
                </div>
              </div>
              <div class="mt-6 flex justify-end gap-3">
                <button type="button" onclick="ReviewTasksPage.hideStartModal()" 
                        class="px-4 py-2 border border-gray-300 rounded-lg hover:bg-gray-50">
                  ${t('common.cancel')}
                </button>
                <button onclick="ReviewTasksPage.startReview()" 
                        class="px-4 py-2 bg-primary-600 text-white rounded-lg hover:bg-primary-700">
                  开始审核
                </button>
              </div>
            </div>
          </div>
        </div>
      `;
    },

    async loadData() {
      const container = document.getElementById('review-list-container');
      try {
        const workspace = window.AppState.currentWorkspace;
        const project = window.AppState.currentProject;
        
        if (!workspace || !project) {
          container.innerHTML = `<div class="p-8 text-center text-gray-500">请先选择工作区和项目</div>`;
          return;
        }

        // 获取审核任务列表
        const result = await window.ApiClient.review.listJobs(workspace, project);
        this.renderList(result || []);
      } catch (error) {
        console.error('[ReviewTasks] Load error:', error);
        container.innerHTML = `<div class="p-8 text-center text-red-500">加载失败: ${error.message}</div>`;
      }
    },

    renderList(tasks) {
      const container = document.getElementById('review-list-container');
      
      if (!tasks || tasks.length === 0) {
        container.innerHTML = `
          <div class="p-8 text-center text-gray-500">
            <div class="text-4xl mb-2">🔍</div>
            <p>暂无审核任务</p>
            <p class="text-sm mt-2">点击右上角按钮创建审核任务</p>
          </div>
        `;
        return;
      }

      container.innerHTML = `
        <div class="divide-y divide-gray-200">
          ${tasks.map(task => `
            <div class="p-4 hover:bg-gray-50 transition-colors">
              <div class="flex items-start justify-between">
                <div class="flex-1 min-w-0">
                  <div class="flex items-center gap-2">
                    <span class="px-2 py-0.5 text-xs rounded-full ${this.getStatusClass(task.status)}">
                      ${task.status}
                    </span>
                    <h3 class="font-medium text-gray-800">第${task.chapter_no}章审核</h3>
                    ${task.score ? `<span class="text-sm text-gray-500">评分: ${task.score}</span>` : ''}
                  </div>
                  ${task.summary ? `<p class="text-sm text-gray-500 mt-1 line-clamp-2">${task.summary}</p>` : ''}
                  <div class="flex items-center gap-4 mt-2 text-xs text-gray-400">
                    <span>ID: ${task.id?.substring(0, 8) || '-'}</span>
                    <span>创建: ${task.created_at ? new Date(task.created_at).toLocaleString() : '-'}</span>
                  </div>
                </div>
                <div class="flex items-center gap-2 ml-4">
                  ${task.status === 'completed' ? `
                    <button onclick="ReviewTasksPage.aggregate('${task.id}')" 
                            class="p-2 text-gray-400 hover:text-primary-600 hover:bg-primary-50 rounded transition-colors"
                            title="汇总结果">
                      <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 19v-6a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2a2 2 0 002-2zm0 0V9a2 2 0 012-2h2a2 2 0 012 2v10m-6 0a2 2 0 002 2h2a2 2 0 002-2m0 0V5a2 2 0 012-2h2a2 2 0 012 2v14a2 2 0 01-2 2h-2a2 2 0 01-2-2z"/>
                      </svg>
                    </button>
                  ` : ''}
                </div>
              </div>
            </div>
          `).join('')}
        </div>
      `;
    },

    showStartModal() {
      document.getElementById('review-chapter-no').value = '';
      document.getElementById('review-start-modal').classList.remove('hidden');
    },

    hideStartModal() {
      document.getElementById('review-start-modal').classList.add('hidden');
    },

    async startReview() {
      const chapterNo = document.getElementById('review-chapter-no').value;
      if (!chapterNo) {
        alert('请输入章节号');
        return;
      }

      const dimensions = [];
      document.querySelectorAll('#review-start-modal input[type="checkbox"]:checked').forEach(cb => {
        dimensions.push(cb.value);
      });

      try {
        const workspace = window.AppState.currentWorkspace;
        const project = window.AppState.currentProject;

        await window.ApiClient.review.startJob(workspace, project, parseInt(chapterNo), dimensions);
        this.hideStartModal();
        this.loadData();
      } catch (error) {
        alert('创建审核任务失败: ' + error.message);
      }
    },

    async aggregate(jobId) {
      try {
        await window.ApiClient.review.aggregate(window.AppState.currentWorkspace, window.AppState.currentProject, jobId);
        alert('汇总完成');
        this.loadData();
      } catch (error) {
        alert('汇总失败: ' + error.message);
      }
    },

    getStatusClass(status) {
      const classes = {
        pending: 'bg-yellow-100 text-yellow-700',
        running: 'bg-blue-100 text-blue-700',
        completed: 'bg-green-100 text-green-700',
        failed: 'bg-red-100 text-red-700'
      };
      return classes[status] || 'bg-gray-100 text-gray-600';
    }
  };
})();
