/**
 * Compliance Page
 * 合规检查页面 - 检测内容合规性
 * 
 * 开发任务 3.1-3.8: 合规检查完整实现
 */
(function() {
  'use strict';

  window.CompliancePage = {
    state: {
      issues: [],
      rules: [],
      loading: false,
      selectedIssue: null,
      filters: {
        severity: [],
        category: []
      },
      ignoredIssues: new Set(),
      batchMode: false,
      selectedIssues: new Set(),
      editingRuleKey: null
    },

    async init() {
      this.render();
      await this.loadRules();
      return true;
    },

    render() {
      const contentArea = document.getElementById('content-area');
      contentArea.innerHTML = `
        <div class="h-full flex flex-col">
          <!-- 标题栏 -->
          <div class="flex items-center justify-between px-6 py-4 bg-white border-b border-gray-200">
            <div>
              <h1 class="text-2xl font-bold text-gray-800">合规检查</h1>
              <p class="text-sm text-gray-500 mt-1">检测敏感词、设定冲突等合规问题</p>
            </div>
            <div class="flex gap-3">
              <select id="compliance-scope" class="px-4 py-2 border border-gray-300 rounded-lg text-sm">
                <option value="full">全文检查</option>
                <option value="chapter">当前章节</option>
                <option value="volume">当前卷</option>
              </select>
              <button onclick="CompliancePage.toggleBatchMode()" 
                      id="batch-mode-btn"
                      class="px-4 py-2 bg-gray-100 text-gray-700 rounded-lg hover:bg-gray-200 transition-colors text-sm">
                <span>☑️</span> 批量模式
              </button>
              <button onclick="CompliancePage.showAddRuleModal()" 
                      class="px-4 py-2 bg-gray-100 text-gray-700 rounded-lg hover:bg-gray-200 transition-colors text-sm">
                <span>➕</span> 添加规则
              </button>
              <button onclick="CompliancePage.showReport()" 
                      class="px-4 py-2 bg-gray-100 text-gray-700 rounded-lg hover:bg-gray-200 transition-colors text-sm">
                <span>📊</span> 报告
              </button>
              <button onclick="CompliancePage.startCheck()" 
                      class="px-4 py-2 bg-primary-600 text-white rounded-lg hover:bg-primary-700 transition-colors text-sm flex items-center gap-2">
                <span>🔍</span> 开始检查
              </button>
            </div>
          </div>

          <!-- 主内容区 -->
          <div class="flex-1 flex overflow-hidden">
            <!-- 左侧规则列表 -->
            <div class="w-72 bg-white border-r border-gray-200 flex flex-col">
              <div class="p-3 border-b border-gray-200">
                <h3 class="font-medium text-gray-700">检查规则</h3>
              </div>
              <div id="compliance-rules" class="flex-1 overflow-y-auto p-3">
                <div class="text-center text-gray-400 py-8">加载中...</div>
              </div>
            </div>

            <!-- 中间问题列表 -->
            <div class="flex-1 flex flex-col min-w-0 bg-gray-50">
              <div class="px-4 py-2 bg-white border-b border-gray-200 flex items-center justify-between">
                <div class="flex items-center gap-2">
                  <span class="text-sm text-gray-600">检查结果</span>
                  <span id="compliance-score" class="text-2xl font-bold text-green-600">--</span>
                  <span class="text-xs text-gray-400">分</span>
                </div>
                <div class="flex items-center gap-2 text-sm">
                  <span class="px-2 py-1 bg-red-100 text-red-700 rounded cursor-pointer hover:bg-red-200" onclick="CompliancePage.filterBySeverity('critical')">致命: <span id="count-critical">0</span></span>
                  <span class="px-2 py-1 bg-orange-100 text-orange-700 rounded cursor-pointer hover:bg-orange-200" onclick="CompliancePage.filterBySeverity('serious')">严重: <span id="count-serious">0</span></span>
                  <span class="px-2 py-1 bg-yellow-100 text-yellow-700 rounded cursor-pointer hover:bg-yellow-200" onclick="CompliancePage.filterBySeverity('warning')">警告: <span id="count-warning">0</span></span>
                  <span class="px-2 py-1 bg-blue-100 text-blue-700 rounded cursor-pointer hover:bg-blue-200" onclick="CompliancePage.filterBySeverity('info')">提示: <span id="count-info">0</span></span>
                </div>
              </div>

              <div id="compliance-issues" class="flex-1 overflow-y-auto p-4">
                <div class="text-center text-gray-400 py-12">
                  <div class="text-4xl mb-4">🔍</div>
                  <p>点击"开始检查"进行检测</p>
                </div>
              </div>
            </div>

            <!-- 右侧详情 -->
            <div id="compliance-detail" class="w-96 bg-white border-l border-gray-200 flex flex-col">
              <div class="p-4 border-b border-gray-200 flex items-center justify-between">
                <h3 class="font-medium text-gray-700">问题详情</h3>
                <button onclick="CompliancePage.closeDetail()" class="text-gray-400 hover:text-gray-600">
                  <svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12"></path></svg>
                </button>
              </div>
              <div id="compliance-detail-content" class="flex-1 overflow-y-auto p-4">
                <p class="text-gray-400 text-center py-8">选择问题查看详情</p>
              </div>
            </div>
          </div>
        </div>

        <!-- 添加规则模态框 -->
        <div id="add-rule-modal" class="fixed inset-0 bg-black bg-opacity-50 hidden items-center justify-center z-50">
          <div class="bg-white rounded-lg shadow-xl w-[500px] max-h-[80vh] flex flex-col">
            <div class="flex items-center justify-between p-4 border-b border-gray-200">
              <h3 id="add-rule-modal-title" class="text-lg font-semibold">添加检查规则</h3>
              <button onclick="CompliancePage.closeAddRuleModal()" class="text-gray-400 hover:text-gray-600">
                <svg class="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12"></path></svg>
              </button>
            </div>
            <div class="p-6 overflow-y-auto space-y-4">
              <div>
                <label class="block text-sm font-medium text-gray-700 mb-1">规则名称</label>
                <input type="text" id="rule-name" class="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-primary-500">
              </div>
              <div>
                <label class="block text-sm font-medium text-gray-700 mb-1">规则类型</label>
                <select id="rule-type" class="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-primary-500">
                  <option value="keyword">关键词匹配</option>
                  <option value="regex">正则表达式</option>
                  <option value="pattern">模式匹配</option>
                </select>
              </div>
              <div>
                <label class="block text-sm font-medium text-gray-700 mb-1">匹配内容</label>
                <input type="text" id="rule-pattern" placeholder="关键词或正则表达式" class="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-primary-500">
              </div>
              <div>
                <label class="block text-sm font-medium text-gray-700 mb-1">严重程度</label>
                <select id="rule-severity" class="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-primary-500">
                  <option value="critical">致命</option>
                  <option value="serious">严重</option>
                  <option value="warning" selected>警告</option>
                  <option value="info">提示</option>
                </select>
              </div>
              <div>
                <label class="block text-sm font-medium text-gray-700 mb-1">提示信息</label>
                <input type="text" id="rule-message" placeholder="发现问题时显示的提示" class="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-primary-500">
              </div>
            </div>
            <div class="flex justify-end gap-3 p-4 border-t border-gray-200">
              <button onclick="CompliancePage.closeAddRuleModal()" class="px-4 py-2 text-gray-600 hover:text-gray-800">取消</button>
              <button id="add-rule-confirm-btn" onclick="CompliancePage.confirmAddRule()" class="px-4 py-2 bg-primary-600 text-white rounded-lg hover:bg-primary-700">添加</button>
            </div>
          </div>
        </div>
      `;
    },

    async loadRules() {
      const container = document.getElementById('compliance-rules');
      if (!container) return;

      try {
        const workspace = window.AppState.currentWorkspace;
        const project = window.AppState.currentProject;
        const result = await window.ApiClient.callTool('compliance.rule.list', { workspace, project });
        this.state.rules = Array.isArray(result) ? result.filter(r => r.status !== 'deleted') : (result?.rules?.filter(r => r.status !== 'deleted') || []);
        
        this.renderRules();
      } catch (error) {
        console.error('[Compliance] Failed to load rules:', error);
        container.innerHTML = '<p class="text-sm text-red-400">加载失败</p>';
      }
    },

    renderRules() {
      const container = document.getElementById('compliance-rules');
      if (!this.state.rules.length) {
        container.innerHTML = '<p class="text-sm text-gray-400">暂无规则</p>';
        return;
      }

      const categoryIcons = {
        'sensitive': '🚫',
        'consistency': '🔄',
        'style': '✍️',
        'format': '📄',
        'custom': '⚙️'
      };

      container.innerHTML = this.state.rules.map(rule => `
        <div class="flex items-start gap-2 py-2 border-b border-gray-100 last:border-0">
          <input type="checkbox" checked class="mt-1 rounded" data-rule="${rule.rule_key || rule.key}">
          <div class="flex-1 min-w-0">
            <div class="flex items-center gap-1">
              <span class="text-xs">${categoryIcons[rule.category] || '📋'}</span>
              <span class="text-sm truncate">${rule.title || rule.name}</span>
            </div>
            <div class="flex items-center gap-2 mt-1">
              <span class="text-xs px-1.5 rounded ${this.getSeverityClass(rule.severity)}">${rule.severity}</span>
              <span class="text-xs text-gray-400">${rule.match_type || 'keyword'}</span>
            </div>
          </div>
          <div class="flex items-center gap-1 ml-2">
            <button onclick="CompliancePage.editRule('${rule.rule_key || rule.key}')"
                    class="p-1 text-gray-400 hover:text-primary-600 hover:bg-primary-50 rounded transition-colors"
                    title="编辑">
              <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M11 5H6a2 2 0 00-2 2v11a2 2 0 002 2h11a2 2 0 002-2v-5m-1.414-9.414a2 2 0 112.828 2.828L11.828 15H9v-2.828l8.586-8.586z"/>
              </svg>
            </button>
            <button onclick="CompliancePage.deleteRule('${rule.rule_key || rule.key}', '${(rule.title || rule.name || '').replace(/'/g, "\\'")}')"
                    class="p-1 text-gray-400 hover:text-red-600 hover:bg-red-50 rounded transition-colors"
                    title="删除">
              <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16"/>
              </svg>
            </button>
          </div>
        </div>
      `).join('');
    },

    getSeverityClass(severity) {
      const classes = {
        'critical': 'bg-red-100 text-red-700',
        'serious': 'bg-orange-100 text-orange-700',
        'warning': 'bg-yellow-100 text-yellow-700',
        'info': 'bg-blue-100 text-blue-700'
      };
      return classes[severity] || 'bg-gray-100 text-gray-700';
    },

    async startCheck() {
      const container = document.getElementById('compliance-issues');
      container.innerHTML = `
        <div class="text-center py-12">
          <div class="w-8 h-8 border-3 border-primary-600 border-t-transparent rounded-full animate-spin mx-auto"></div>
          <p class="text-sm text-gray-500 mt-3">检查中...</p>
        </div>
      `;

      try {
        const workspace = window.AppState.currentWorkspace;
        const project = window.AppState.currentProject;
        const scope = document.getElementById('compliance-scope')?.value || 'full';

        const result = await window.ApiClient.callTool('compliance.check', {
          workspace,
          project,
          scope
        });

        this.state.issues = result.issues || result.violations || [];
        this.renderIssues();
        this.updateStats(result.summary || result.stats);
      } catch (error) {
        console.error('[Compliance] Check failed:', error);
        container.innerHTML = `<div class="text-center text-red-400 py-12">检查失败: ${error.message || '未知错误'}</div>`;
      }
    },

    renderIssues() {
      const container = document.getElementById('compliance-issues');
      let issues = this.state.issues.filter(i => !this.state.ignoredIssues.has(i.id || i.issue_id));

      // 应用过滤器
      if (this.state.filters.severity.length) {
        issues = issues.filter(i => this.state.filters.severity.includes(i.severity));
      }

      if (!issues.length) {
        container.innerHTML = `
          <div class="text-center text-green-600 py-12">
            <div class="text-4xl mb-4">✓</div>
            <p>${this.state.issues.length ? '所有问题已处理' : '未发现合规问题'}</p>
          </div>
        `;
        return;
      }

      const severityColors = {
        'critical': 'border-red-500 bg-red-50',
        'serious': 'border-orange-500 bg-orange-50',
        'warning': 'border-yellow-500 bg-yellow-50',
        'info': 'border-blue-500 bg-blue-50'
      };

      const severityLabels = {
        'critical': '致命',
        'serious': '严重',
        'warning': '警告',
        'info': '提示'
      };

      container.innerHTML = issues.map((issue, idx) => {
        const issueId = issue.id || issue.issue_id;
        const isSelected = this.state.selectedIssues.has(issueId);
        
        return `
        <div class="mb-3 p-4 rounded-lg border-l-4 ${severityColors[issue.severity] || 'border-gray-300 bg-white'} ${isSelected ? 'ring-2 ring-primary-500' : ''} cursor-pointer hover:shadow-md transition-shadow"
             onclick="${this.state.batchMode ? '' : `CompliancePage.showIssueDetail(${idx})`}">
          <div class="flex items-start justify-between">
            ${this.state.batchMode ? `
              <input type="checkbox" class="mt-1 mr-3 rounded" ${isSelected ? 'checked' : ''}
                     onclick="CompliancePage.toggleIssueSelection('${issueId}', event)">
            ` : ''}
            <div class="flex-1 min-w-0" ${this.state.batchMode ? `onclick="CompliancePage.showIssueDetail(${idx})"` : ''}>
              <div class="flex items-center gap-2">
                <span class="text-xs px-2 py-0.5 rounded ${this.getSeverityClass(issue.severity)}">${severityLabels[issue.severity] || issue.severity}</span>
                <span class="font-medium text-sm truncate">${issue.rule?.title || issue.rule_name || '未知规则'}</span>
              </div>
              <p class="text-sm text-gray-600 mt-1 line-clamp-2">${issue.message}</p>
              ${issue.location ? `<p class="text-xs text-gray-400 mt-1">位置: ${this.formatLocation(issue.location)}</p>` : ''}
            </div>
          </div>
        </div>
      `;
      }).join('');
    },

    formatLocation(location) {
      if (!location) return '未知位置';
      const parts = [];
      if (location.chapter_no) parts.push(`第${location.chapter_no}章`);
      if (location.paragraph_no) parts.push(`第${location.paragraph_no}段`);
      if (location.line_no) parts.push(`第${location.line_no}行`);
      return parts.join(' ') || '未知位置';
    },

    updateStats(summary) {
      summary = summary || {};
      document.getElementById('compliance-score').textContent = summary.score ?? (this.state.issues.length ? Math.max(0, 100 - this.state.issues.length * 5) : 100);
      document.getElementById('count-critical').textContent = summary.critical_count || this.countBySeverity('critical');
      document.getElementById('count-serious').textContent = summary.serious_count || this.countBySeverity('serious');
      document.getElementById('count-warning').textContent = summary.warning_count || this.countBySeverity('warning');
      document.getElementById('count-info').textContent = summary.info_count || this.countBySeverity('info');
    },

    countBySeverity(severity) {
      return this.state.issues.filter(i => i.severity === severity).length;
    },

    filterBySeverity(severity) {
      if (this.state.filters.severity.includes(severity)) {
        this.state.filters.severity = this.state.filters.severity.filter(s => s !== severity);
      } else {
        this.state.filters.severity.push(severity);
      }
      this.renderIssues();
    },

    showIssueDetail(idx) {
      const issues = this.state.issues.filter(i => !this.state.ignoredIssues.has(i.id || i.issue_id));
      const issue = issues[idx];
      if (!issue) return;

      this.state.selectedIssue = issue;
      const content = document.getElementById('compliance-detail-content');

      content.innerHTML = `
        <div class="space-y-4">
          <div>
            <label class="text-xs text-gray-500">规则</label>
            <p class="font-medium">${issue.rule?.title || issue.rule_name || '未知规则'}</p>
          </div>
          <div>
            <label class="text-xs text-gray-500">问题描述</label>
            <p class="text-sm">${issue.message}</p>
          </div>
          <div>
            <label class="text-xs text-gray-500">严重程度</label>
            <p class="text-sm"><span class="px-2 py-0.5 rounded ${this.getSeverityClass(issue.severity)}">${issue.severity}</span></p>
          </div>
          ${issue.location ? `
            <div>
              <label class="text-xs text-gray-500">位置</label>
              <p class="text-sm">${this.formatLocation(issue.location)}</p>
            </div>
          ` : ''}
          ${issue.content ? `
            <div>
              <label class="text-xs text-gray-500">原文</label>
              <div class="mt-1 p-3 bg-gray-50 rounded text-sm font-mono">${issue.content.text || issue.content}</div>
            </div>
          ` : ''}
          ${issue.suggestion ? `
            <div>
              <label class="text-xs text-gray-500">建议修改</label>
              <div class="mt-1 p-3 bg-green-50 rounded text-sm">${issue.suggestion}</div>
            </div>
          ` : ''}
          <div class="pt-4 flex gap-2">
            <button onclick="CompliancePage.fixIssue()" class="flex-1 px-4 py-2 bg-primary-600 text-white rounded-lg text-sm hover:bg-primary-700">一键修复</button>
            <button onclick="CompliancePage.ignoreIssue()" class="px-4 py-2 bg-gray-100 text-gray-700 rounded-lg text-sm hover:bg-gray-200">忽略</button>
          </div>
        </div>
      `;
    },

    closeDetail() {
      this.state.selectedIssue = null;
      document.getElementById('compliance-detail-content').innerHTML = '<p class="text-gray-400 text-center py-8">选择问题查看详情</p>';
    },

    async fixIssue() {
      if (!this.state.selectedIssue) return;
      window.showToast && window.showToast('info', '修复功能需要在编辑器中实现');
    },

    async ignoreIssue() {
      if (!this.state.selectedIssue) return;
      this.state.ignoredIssues.add(this.state.selectedIssue.id || this.state.selectedIssue.issue_id);
      this.closeDetail();
      this.renderIssues();
      window.showToast && window.showToast('success', '已忽略该问题');
    },

    showAddRuleModal() {
      document.getElementById('add-rule-modal').classList.remove('hidden');
      document.getElementById('add-rule-modal').classList.add('flex');
    },

    closeAddRuleModal() {
      this.state.editingRuleKey = null;
      document.getElementById('add-rule-modal-title').textContent = '添加检查规则';
      document.getElementById('add-rule-confirm-btn').textContent = '添加';
      document.getElementById('add-rule-modal').classList.add('hidden');
      document.getElementById('add-rule-modal').classList.remove('flex');
    },

    async editRule(ruleKey) {
      const rule = this.state.rules.find(r => (r.rule_key || r.key) === ruleKey);
      if (!rule) { window.showToast && window.showToast('error', '规则不存在'); return; }
      
      this.state.editingRuleKey = ruleKey;
      document.getElementById('add-rule-modal-title').textContent = '编辑检查规则';
      document.getElementById('add-rule-confirm-btn').textContent = '保存';
      document.getElementById('rule-name').value = rule.title || rule.name || '';
      document.getElementById('rule-type').value = rule.match_type || 'keyword';
      document.getElementById('rule-pattern').value = rule.content || rule.pattern || '';
      document.getElementById('rule-severity').value = rule.severity || 'warning';
      document.getElementById('rule-message').value = rule.hint || '';
      document.getElementById('add-rule-modal').classList.remove('hidden');
      document.getElementById('add-rule-modal').classList.add('flex');
    },

    async deleteRule(ruleKey, title) {
      if (!confirm(`确定删除规则 "${title}" 吗？`)) return;
      
      try {
        const workspace = window.AppState.currentWorkspace;
        const project = window.AppState.currentProject;
        await window.ApiClient.callTool('compliance.rule.delete', {
          workspace, project, rule_key: ruleKey
        });
        window.showToast && window.showToast('success', '规则已删除');
        await CompliancePage.loadRules();
      } catch (error) {
        window.showToast && window.showToast('error', '删除失败: ' + (error.message || ''));
      }
    },

    /**
     * 切换批量模式
     */
    toggleBatchMode() {
      this.state.batchMode = !this.state.batchMode;
      const btn = document.getElementById('batch-mode-btn');
      
      if (this.state.batchMode) {
        btn.classList.remove('bg-gray-100', 'text-gray-700');
        btn.classList.add('bg-primary-100', 'text-primary-700');
        this.showBatchToolbar();
      } else {
        btn.classList.add('bg-gray-100', 'text-gray-700');
        btn.classList.remove('bg-primary-100', 'text-primary-700');
        this.hideBatchToolbar();
        this.state.selectedIssues.clear();
        this.renderIssues();
      }
    },

    /**
     * 显示批量操作工具栏
     */
    showBatchToolbar() {
      let toolbar = document.getElementById('batch-toolbar');
      if (!toolbar) {
        toolbar = document.createElement('div');
        toolbar.id = 'batch-toolbar';
        toolbar.className = 'px-4 py-2 bg-primary-50 border-b border-primary-200 flex items-center justify-between';
        
        const container = document.querySelector('#compliance-issues').parentNode;
        container.insertBefore(toolbar, container.firstChild);
      }
      
      this.updateBatchToolbar();
    },

    /**
     * 隐藏批量操作工具栏
     */
    hideBatchToolbar() {
      const toolbar = document.getElementById('batch-toolbar');
      if (toolbar) toolbar.remove();
    },

    /**
     * 更新批量操作工具栏
     */
    updateBatchToolbar() {
      const toolbar = document.getElementById('batch-toolbar');
      if (!toolbar) return;
      
      const count = this.state.selectedIssues.size;
      toolbar.innerHTML = `
        <div class="flex items-center gap-4">
          <input type="checkbox" id="select-all-issues" ${count === this.state.issues.length ? 'checked' : ''} 
                 onchange="CompliancePage.toggleSelectAll()">
          <span class="text-sm text-gray-700">已选择 ${count} 个问题</span>
        </div>
        <div class="flex items-center gap-2">
          <button onclick="CompliancePage.batchIgnore()" ${count === 0 ? 'disabled' : ''} 
                  class="px-3 py-1.5 bg-gray-100 text-gray-700 rounded text-sm ${count === 0 ? 'opacity-50 cursor-not-allowed' : 'hover:bg-gray-200'}">
            批量忽略
          </button>
          <button onclick="CompliancePage.batchFix()" ${count === 0 ? 'disabled' : ''} 
                  class="px-3 py-1.5 bg-primary-600 text-white rounded text-sm ${count === 0 ? 'opacity-50 cursor-not-allowed' : 'hover:bg-primary-700'}">
            批量修复
          </button>
        </div>
      `;
    },

    /**
     * 全选/取消全选
     */
    toggleSelectAll() {
      const checkbox = document.getElementById('select-all-issues');
      if (checkbox.checked) {
        this.state.issues.forEach(issue => {
          this.state.selectedIssues.add(issue.id || issue.issue_id);
        });
      } else {
        this.state.selectedIssues.clear();
      }
      this.updateBatchToolbar();
      this.renderIssues();
    },

    /**
     * 切换单个问题选中状态
     */
    toggleIssueSelection(issueId, event) {
      event.stopPropagation();
      if (this.state.selectedIssues.has(issueId)) {
        this.state.selectedIssues.delete(issueId);
      } else {
        this.state.selectedIssues.add(issueId);
      }
      this.updateBatchToolbar();
      this.renderIssues();
    },

    /**
     * 批量忽略
     */
    async batchIgnore() {
      const count = this.state.selectedIssues.size;
      if (!count) return;
      
      if (!confirm(`确定要忽略选中的 ${count} 个问题吗？`)) return;
      
      this.state.selectedIssues.forEach(id => {
        this.state.ignoredIssues.add(id);
      });
      
      this.state.selectedIssues.clear();
      this.updateBatchToolbar();
      this.renderIssues();
      
      window.showToast && window.showToast('success', `已忽略 ${count} 个问题`);
    },

    /**
     * 批量修复
     */
    async batchFix() {
      const count = this.state.selectedIssues.size;
      if (!count) return;
      
      window.showToast && window.showToast('info', `批量修复功能需要在编辑器中实现\n选中问题数: ${count}`);
    },

    /**
     * 显示统计报告
     */
    showReport() {
      if (!this.state.issues.length) {
        window.showToast && window.showToast('warning', '请先执行检查');
        return;
      }

      const workspace = window.AppState.currentWorkspace;
      const project = window.AppState.currentProject;
      const timestamp = new Date().toLocaleString();
      
      // 统计各类问题数量
      const stats = {
        critical: this.state.issues.filter(i => i.severity === 'critical').length,
        serious: this.state.issues.filter(i => i.severity === 'serious').length,
        warning: this.state.issues.filter(i => i.severity === 'warning').length,
        info: this.state.issues.filter(i => i.severity === 'info').length
      };

      // 按规则统计
      const ruleStats = {};
      this.state.issues.forEach(issue => {
        const ruleName = issue.rule?.title || issue.rule_name || '未知规则';
        if (!ruleStats[ruleName]) {
          ruleStats[ruleName] = { count: 0, severity: issue.severity };
        }
        ruleStats[ruleName].count++;
      });

      const modal = document.createElement('div');
      modal.className = 'fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50';
      modal.id = 'compliance-report-modal';
      modal.innerHTML = `
        <div class="bg-white rounded-lg shadow-xl w-[600px] max-h-[80vh] flex flex-col">
          <div class="flex items-center justify-between p-4 border-b border-gray-200">
            <h3 class="text-lg font-semibold">合规检查报告</h3>
            <button onclick="document.getElementById('compliance-report-modal').remove()" class="text-gray-400 hover:text-gray-600">✕</button>
          </div>
          <div class="p-6 overflow-y-auto">
            <div class="mb-6">
              <div class="text-sm text-gray-500 mb-1">检查时间: ${timestamp}</div>
              <div class="text-sm text-gray-500">项目: ${workspace}/${project}</div>
            </div>
            
            <div class="grid grid-cols-4 gap-4 mb-6">
              <div class="text-center p-3 bg-red-50 rounded-lg">
                <div class="text-2xl font-bold text-red-600">${stats.critical}</div>
                <div class="text-xs text-red-600">致命</div>
              </div>
              <div class="text-center p-3 bg-orange-50 rounded-lg">
                <div class="text-2xl font-bold text-orange-600">${stats.serious}</div>
                <div class="text-xs text-orange-600">严重</div>
              </div>
              <div class="text-center p-3 bg-yellow-50 rounded-lg">
                <div class="text-2xl font-bold text-yellow-600">${stats.warning}</div>
                <div class="text-xs text-yellow-600">警告</div>
              </div>
              <div class="text-center p-3 bg-blue-50 rounded-lg">
                <div class="text-2xl font-bold text-blue-600">${stats.info}</div>
                <div class="text-xs text-blue-600">提示</div>
              </div>
            </div>

            <div class="mb-4">
              <h4 class="font-medium mb-2">问题分布</h4>
              <div class="space-y-2">
                ${Object.entries(ruleStats).sort((a, b) => b[1].count - a[1].count).map(([rule, data]) => `
                  <div class="flex items-center justify-between p-2 bg-gray-50 rounded">
                    <span class="text-sm">${rule}</span>
                    <div class="flex items-center gap-2">
                      <span class="text-xs px-2 py-0.5 rounded ${this.getSeverityClass(data.severity)}">${data.severity}</span>
                      <span class="text-sm font-medium">${data.count}</span>
                    </div>
                  </div>
                `).join('')}
              </div>
            </div>
          </div>
          <div class="flex justify-end gap-3 p-4 border-t border-gray-200">
            <button onclick="CompliancePage.exportReport()" class="px-4 py-2 bg-primary-600 text-white rounded-lg hover:bg-primary-700">导出报告</button>
            <button onclick="document.getElementById('compliance-report-modal').remove()" class="px-4 py-2 text-gray-600 hover:text-gray-800">关闭</button>
          </div>
        </div>
      `;
      document.body.appendChild(modal);
    },

    /**
     * 导出报告
     */
    exportReport() {
      const workspace = window.AppState.currentWorkspace;
      const project = window.AppState.currentProject;
      const timestamp = new Date().toLocaleString();
      
      const report = {
        title: '合规检查报告',
        timestamp,
        workspace,
        project,
        summary: {
          total: this.state.issues.length,
          critical: this.state.issues.filter(i => i.severity === 'critical').length,
          serious: this.state.issues.filter(i => i.severity === 'serious').length,
          warning: this.state.issues.filter(i => i.severity === 'warning').length,
          info: this.state.issues.filter(i => i.severity === 'info').length
        },
        issues: this.state.issues.map(i => ({
          severity: i.severity,
          rule: i.rule?.title || i.rule_name,
          message: i.message,
          location: i.location
        }))
      };

      // 导出为JSON
      const blob = new Blob([JSON.stringify(report, null, 2)], { type: 'application/json' });
      const url = URL.createObjectURL(blob);
      const link = document.createElement('a');
      link.href = url;
      link.download = `compliance-report-${Date.now()}.json`;
      link.click();
      URL.revokeObjectURL(url);
      
      window.showToast && window.showToast('success', '报告已导出');
    },

    async confirmAddRule() {
      const name = document.getElementById('rule-name').value.trim();
      const type = document.getElementById('rule-type').value;
      const pattern = document.getElementById('rule-pattern').value.trim();
      const severity = document.getElementById('rule-severity').value;
      const message = document.getElementById('rule-message').value.trim();

      if (!name || !pattern) {
        window.showToast && window.showToast('warning', '请填写完整信息');
        return;
      }

      try {
        const workspace = window.AppState.currentWorkspace;
        const project = window.AppState.currentProject;
        
        await window.ApiClient.callTool('compliance.rule.upsert', {
          workspace,
          project,
          rule_key: this.state.editingRuleKey || 'custom_' + Date.now(),
          title: name,
          content: pattern,
          match_type: type,
          severity,
          hint: message,
          category: 'custom'
        });

        const action = this.state.editingRuleKey ? '更新' : '添加';
        window.showToast && window.showToast('success', `规则${action}成功`);
        this.state.editingRuleKey = null;
        CompliancePage.closeAddRuleModal();
        await CompliancePage.loadRules();
      } catch (error) {
        window.showToast && window.showToast('error', '添加失败: ' + (error.message || '未知错误'));
      }
    }
  };
})();
