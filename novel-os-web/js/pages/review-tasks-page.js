/**
 * Novel OS - Review Tasks Page
 * 审核任务页面
 */
(function() {
  'use strict';

  window.ReviewTasksPage = {
    page: 0,
    pageSize: 10,
    totalTasks: 0,

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
                    <label class="flex items-center">
                      <input type="checkbox" value="ai_detection" checked class="mr-2 text-purple-600"> AI痕迹检测
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
      const statusFilter = document.getElementById('review-status-filter')?.value || '';
      
      try {
        const workspace = window.AppState.currentWorkspace;
        const project = window.AppState.currentProject;
        
        if (!workspace || !project) {
          container.innerHTML = `<div class="p-8 text-center text-gray-500">请先选择工作区和项目</div>`;
          return;
        }

        // 显示加载状态
        container.innerHTML = `
          <div class="p-8 text-center text-gray-500">
            <div class="spinner w-8 h-8 border-4 border-primary-600 border-t-transparent rounded-full animate-spin mx-auto"></div>
            <p class="mt-2">加载中...</p>
          </div>
        `;

        // 获取审核任务列表
        const result = await window.ApiClient.callTool('review.list_revision_tasks', { 
          workspace, 
          project,
          status: statusFilter || undefined,
          limit: this.pageSize,
        });
        
        const tasks = Array.isArray(result) ? result : (result?.items || result?.tasks || []);
        this.totalTasks = tasks.length < this.pageSize ? this.page * this.pageSize + tasks.length : (this.page + 1) * this.pageSize + this.pageSize;
        this.renderList(tasks);
      } catch (error) {
        console.error('[ReviewTasks] Load error:', error);
        this.renderList([]);
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

      const totalPages = Math.ceil(this.totalTasks / this.pageSize) || 1;

      container.innerHTML = `
        <div class="divide-y divide-gray-200">
          ${tasks.map(task => {
            const dims = task.dimensions ? task.dimensions.replace(/[\[\]\"]/g, '').split(',').map(s => s.trim()).filter(Boolean) : [];
            const modelList = task.models ? task.models.split(', ').filter(Boolean) : [];
            return `
            <div class="p-4 hover:bg-gray-50 transition-colors cursor-pointer" onclick="ReviewTasksPage.viewDetail('${task.id}')">
              <div class="flex items-start justify-between">
                <div class="flex-1 min-w-0">
                  <div class="flex items-center gap-2 flex-wrap">
                    <span class="px-2 py-0.5 text-xs rounded-full ${this.getStatusClass(task.status)}">
                      ${this.getStatusLabel(task.status)}
                    </span>
                    <h3 class="font-medium text-gray-800">第${task.chapter_no}章</h3>
                    ${task.avg_score ? `<span class="text-sm font-medium ${this.getScoreClass(task.avg_score)}">评分: ${task.avg_score}</span>` : ''}
                    <span class="text-xs text-gray-400">${task.report_count || 0} 份报告</span>
                  </div>
                  ${task.summary ? `<p class="text-sm text-gray-500 mt-1 line-clamp-2">${task.summary}</p>` : ''}
                  <div class="flex items-center gap-3 mt-2 text-xs text-gray-400 flex-wrap">
                    ${dims.length ? `<span>维度: ${dims.join(', ')}</span>` : ''}
                    ${modelList.length ? `<span>模型: ${modelList.join(', ')}</span>` : ''}
                    <span>${task.created_at ? new Date(task.created_at).toLocaleString() : '-'}</span>
                  </div>
                </div>
                <div class="flex items-center gap-2 ml-4">
                  ${task.status === 'aggregated' ? `
                    <button onclick="event.stopPropagation(); ReviewTasksPage.viewDetail('${task.id}')" 
                            class="px-3 py-1 text-sm bg-primary-100 text-primary-700 rounded hover:bg-primary-200 transition-colors">
                      查看报告
                    </button>
                  ` : ''}
                  ${task.status === 'pending' ? `
                    <button onclick="event.stopPropagation(); ReviewTasksPage.aggregate('${task.id}')" 
                            class="px-3 py-1 text-sm bg-green-100 text-green-700 rounded hover:bg-green-200 transition-colors">
                      汇总
                    </button>
                    <button onclick="event.stopPropagation(); ReviewTasksPage.deleteTask('${task.id}')" 
                            class="p-2 text-gray-400 hover:text-red-600 hover:bg-red-50 rounded transition-colors" title="删除">
                      <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16"/>
                      </svg>
                    </button>
                  ` : ''}
                </div>
              </div>
            </div>`;
          }).join('')}
        </div>
        ${totalPages > 1 ? `
          <div class="flex items-center justify-between px-4 py-3 border-t border-gray-200">
            <button onclick="ReviewTasksPage.goPage(0)" class="px-3 py-1 text-sm border rounded hover:bg-gray-50 ${this.page === 0 ? 'opacity-50 cursor-not-allowed' : ''}" ${this.page === 0 ? 'disabled' : ''}>首页</button>
            <button onclick="ReviewTasksPage.goPage(${this.page - 1})" class="px-3 py-1 text-sm border rounded hover:bg-gray-50 ${this.page === 0 ? 'opacity-50 cursor-not-allowed' : ''}" ${this.page === 0 ? 'disabled' : ''}>上一页</button>
            <span class="text-sm text-gray-500">第 ${this.page + 1} / ${totalPages} 页（共 ${this.totalTasks} 条）</span>
            <button onclick="ReviewTasksPage.goPage(${this.page + 1})" class="px-3 py-1 text-sm border rounded hover:bg-gray-50 ${this.page >= totalPages - 1 ? 'opacity-50 cursor-not-allowed' : ''}" ${this.page >= totalPages - 1 ? 'disabled' : ''}>下一页</button>
            <button onclick="ReviewTasksPage.goPage(${totalPages - 1})" class="px-3 py-1 text-sm border rounded hover:bg-gray-50 ${this.page >= totalPages - 1 ? 'opacity-50 cursor-not-allowed' : ''}" ${this.page >= totalPages - 1 ? 'disabled' : ''}>末页</button>
          </div>
        ` : ''}
      `;
    },

    goPage(p) {
      this.page = p;
      this.loadData();
    },

    getScoreClass(score) {
      if (!score) return 'text-gray-500';
      const s = parseFloat(score);
      if (s >= 80) return 'text-green-600';
      if (s >= 60) return 'text-orange-600';
      return 'text-red-600';
    },

    getStatusLabel(status) {
      const labels = { pending: '待汇总', aggregated: '已完成', running: '审核中', failed: '失败' };
      return labels[status] || status;
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

        await window.ApiClient.callTool('review.start_job', { workspace, project, chapter_no: parseInt(chapterNo), dimensions });
        this.hideStartModal();
        this.loadData();
      } catch (error) {
        alert('创建审核任务失败: ' + error.message);
      }
    },

    async aggregate(jobId) {
      try {
        await window.ApiClient.callTool('review.aggregate', { workspace: window.AppState.currentWorkspace, project: window.AppState.currentProject, review_job_id: jobId });
        alert('汇总完成');
        this.loadData();
      } catch (error) {
        alert('汇总失败: ' + error.message);
      }
    },

    getStatusClass(status) {
      const classes = {
        pending: 'bg-yellow-100 text-yellow-700',
        aggregated: 'bg-green-100 text-green-700',
        running: 'bg-blue-100 text-blue-700',
        failed: 'bg-red-100 text-red-700'
      };
      return classes[status] || 'bg-gray-100 text-gray-600';
    },

    getScoreClass(score) {
      if (score >= 90) return 'text-green-600';
      if (score >= 70) return 'text-yellow-600';
      return 'text-red-600';
    },

    async viewDetail(jobId) {
      try {
        const workspace = window.AppState.currentWorkspace;
        const project = window.AppState.currentProject;
        
        const result = await window.ApiClient.callTool('review.list_revision_tasks', { 
          workspace, project, task_id: jobId
        });
        
        const task = Array.isArray(result) ? result[0] : result;
        if (!task) { alert('未找到审核任务详情'); return; }

        // 解析 reports JSON 字符串
        let reports = [];
        if (task.reports) {
          try {
            reports = typeof task.reports === 'string' ? JSON.parse(task.reports) : task.reports;
          } catch (_) {}
        }
        this.showDetailModal(task, reports);
      } catch (error) {
        console.error('[ReviewTasks] View detail error:', error);
        alert('加载详情失败: ' + error.message);
      }
    },

    showDetailModal(task, reports) {
      const dims = task.dimensions ? task.dimensions.replace(/[\[\]\"]/g, '').split(',').map(s => s.trim()).filter(Boolean) : [];
      const modelList = task.models ? task.models.split(', ').filter(Boolean) : [];
      const statusLabels = { pending: '待汇总', aggregated: '已完成' };
      
      const modal = document.createElement('div');
      modal.className = 'fixed inset-0 bg-black/50 z-50 flex items-center justify-center';
      modal.id = 'review-detail-modal';
      modal.innerHTML = `
        <div class="bg-white rounded-lg shadow-xl w-full max-w-3xl mx-4 max-h-[85vh] flex flex-col">
          <div class="px-6 py-4 border-b border-gray-200 flex items-center justify-between">
            <div class="flex items-center gap-2">
              <h3 class="text-lg font-semibold">审核详情 - 第${task.chapter_no}章</h3>
              <span class="px-2 py-0.5 text-xs rounded-full ${this.getStatusClass(task.status)}">
                ${statusLabels[task.status] || task.status}
              </span>
            </div>
            <button onclick="document.getElementById('review-detail-modal').remove()" class="text-gray-400 hover:text-gray-600">
              <svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12"/>
              </svg>
            </button>
          </div>
          <div class="p-6 overflow-y-auto">
            <div class="space-y-4">
              <!-- 概览 -->
              <div class="grid grid-cols-2 gap-4">
                <div>
                  <label class="text-sm text-gray-500">章节</label>
                  <p class="font-medium">第${task.chapter_no}章</p>
                </div>
                <div>
                  <label class="text-sm text-gray-500">状态</label>
                  <p class="font-medium">${statusLabels[task.status] || task.status}</p>
                </div>
                ${task.avg_score ? `<div>
                  <label class="text-sm text-gray-500">综合评分</label>
                  <p class="font-medium text-lg ${this.getScoreClass(task.avg_score)}">${task.avg_score}</p>
                </div>` : ''}
                <div>
                  <label class="text-sm text-gray-500">报告数</label>
                  <p class="font-medium">${reports.length || task.report_count || 0}</p>
                </div>
              </div>
              
              ${dims.length ? `<div>
                <label class="text-sm text-gray-500">审核维度</label>
                <div class="flex flex-wrap gap-1 mt-1">${dims.map(d => `<span class="px-2 py-0.5 text-xs bg-blue-100 text-blue-700 rounded">${d}</span>`).join('')}</div>
              </div>` : ''}
              
              ${modelList.length ? `<div>
                <label class="text-sm text-gray-500">参与模型</label>
                <div class="flex flex-wrap gap-1 mt-1">${modelList.map(m => `<span class="px-2 py-0.5 text-xs bg-gray-100 text-gray-600 rounded">${m}</span>`).join('')}</div>
              </div>` : ''}
              
              <hr class="border-gray-200">
              
              <!-- 各模型详情 -->
              <h4 class="font-medium text-gray-700">📋 各模型审核报告</h4>
              ${reports && reports.length > 0 ? reports.map(r => this.renderReportCard(r)).join('') : '<p class="text-sm text-gray-400">暂无详细报告数据</p>'}
              
              <div class="text-xs text-gray-400 pt-2">
                <p>任务ID: ${task.id}</p>
                <p>创建时间: ${task.created_at ? new Date(task.created_at).toLocaleString() : '-'}</p>
              </div>
            </div>
          </div>
          <div class="px-6 py-4 border-t border-gray-200 flex justify-end gap-3">
            <button onclick="document.getElementById('review-detail-modal').remove()" 
                    class="px-4 py-2 border border-gray-300 rounded-lg hover:bg-gray-50">
              关闭
            </button>
          </div>
        </div>
      `;
      document.body.appendChild(modal);
    },

    renderReportCard(r) {
      const hasScore = r.score !== null && r.score !== undefined && r.score !== '';
      const score = parseFloat(r.score);
      const isFailed = !hasScore && !r.summary;
      let findings = [];
      try {
        findings = typeof r.findings === 'string' ? JSON.parse(r.findings) : (r.findings || []);
      } catch (_) {
        findings = [];
      }
      const failMsg = (typeof r.findings === 'string' && r.findings !== '[]') ? r.findings : '';
      return `
        <div class="border border-gray-200 rounded-lg p-4 mb-3">
          <div class="flex items-center justify-between mb-2">
            <div class="flex items-center gap-2">
              <span class="font-medium text-sm">${r.model_id || '未知模型'}</span>
              <span class="text-xs text-gray-400">${r.report_type || '审核'}</span>
            </div>
            ${isFailed ? '<span class="text-sm font-bold text-red-500">❌ 审核失败</span>' : (hasScore ? `<span class="text-sm font-bold ${this.getScoreClass(score)}">${score}分</span>` : '')}
          </div>
          ${isFailed ? `<div class="text-sm text-red-500 bg-red-50 p-2 rounded">该模型审核未返回有效结果${failMsg ? '：' + failMsg : ''}</div>` : ''}
          ${!isFailed && r.summary ? `<p class="text-sm text-gray-600 mb-2">${r.summary}</p>` : ''}
          ${!isFailed && findings.length > 0 ? `<div class="space-y-1">${findings.map(f => `
            <div class="flex items-start gap-2 text-xs p-1.5 rounded ${f.severity === 'warning' ? 'bg-yellow-50' : f.severity === 'error' || f.severity === 'critical' ? 'bg-red-50' : 'bg-gray-50'}">
              <span class="px-1.5 py-0.5 rounded text-xs font-medium ${f.severity === 'warning' ? 'bg-yellow-100 text-yellow-700' : f.severity === 'error' || f.severity === 'critical' ? 'bg-red-100 text-red-700' : 'bg-blue-100 text-blue-600'}">${f.severity || 'info'}</span>
              <span class="text-gray-600">${f.description || f.category}${f.location ? ` <span class="text-gray-400">(${f.location})</span>` : ''}</span>
            </div>
          `).join('')}</div>` : ''}
        </div>`;
    },

    async deleteTask(jobId) {
      if (!confirm('确定要删除这个审核任务吗？此操作不可恢复。')) return;
      
      try {
        const workspace = window.AppState.currentWorkspace;
        const project = window.AppState.currentProject;
        
        await window.ApiClient.callTool('review.update_revision_task', { 
          workspace, 
          project,
          task_id: jobId,
          status: 'cancelled'
        });
        
        this.loadData();
      } catch (error) {
        console.error('[ReviewTasks] Delete error:', error);
        alert('删除失败: ' + error.message);
      }
    },

  };
})();
