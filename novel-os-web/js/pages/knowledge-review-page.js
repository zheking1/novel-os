/**
 * Knowledge Review Page
 * 知识审核 - 审计提案 / 委员会裁决 / 管理员终审
 *
 * 数据源：
 * - knowledge.audit_status  统计待审核数量
 * - knowledge.audit_all     触发审计（mode: 空=新增+优化 / add / optimize）
 * - knowledge.council_debate_all  对已有提案做委员会裁决
 * - system.evolution.list / get / admin_review  提案列表、详情、通过/驳回
 */
(function () {
  'use strict';

  function t(key, fallback) {
    return (window.t && window.t(key)) || fallback;
  }

  function esc(s) {
    return String(s == null ? '' : s)
      .replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;');
  }

  function state() {
    return {
      workspace: window.AppState && window.AppState.currentWorkspace,
      project: window.AppState && window.AppState.currentProject
    };
  }

  window.KnowledgeReviewPage = {
    proposals: [],

    async init() {
      const contentArea = document.getElementById('content-area');
      if (!contentArea) return true;

      contentArea.innerHTML = `
        <div class="flex items-center justify-between mb-6">
          <div>
            <h1 class="text-2xl font-bold text-gray-800">${t('nav.knowledgeReview', '知识审核')}</h1>
            <p class="text-gray-500 mt-1 text-sm">审计知识库产出改进提案，由委员会辩论后交管理员终审</p>
          </div>
          <div class="flex gap-2">
            <select id="kr-audit-mode" class="px-3 py-2 border border-gray-300 rounded-lg text-sm">
              <option value="">新增 + 优化</option>
              <option value="add">只新增</option>
              <option value="optimize">只优化</option>
            </select>
            <button onclick="KnowledgeReviewPage.runAudit()"
              class="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 text-sm">运行审计</button>
            <button onclick="KnowledgeReviewPage.runDebate()"
              class="px-4 py-2 bg-purple-600 text-white rounded-lg hover:bg-purple-700 text-sm">委员会裁决</button>
            <button onclick="KnowledgeReviewPage.loadData()"
              class="px-4 py-2 bg-gray-100 text-gray-700 rounded-lg hover:bg-gray-200 text-sm">刷新</button>
          </div>
        </div>
        <div id="kr-status" class="grid grid-cols-2 md:grid-cols-4 gap-4 mb-4"></div>
        <div id="kr-content" class="bg-white rounded-lg shadow">
          <div class="p-8 text-center text-gray-500">${t('common.loading', '加载中...')}</div>
        </div>
      `;

      await this.loadData();
      return true;
    },

    async loadData() {
      const el = document.getElementById('kr-content');
      const { workspace, project } = state();

      if (!workspace || !project) {
        el.innerHTML = '<div class="p-8 text-center text-gray-500">请先选择工作区与项目</div>';
        return;
      }

      try {
        const st = await window.ApiClient.callTool('knowledge.audit_status', { workspace, project }).catch(() => null);
        this.renderStatus(st);

        const list = await window.ApiClient.callTool('system.evolution.list', {
          workspace, project, status: 'pending_review', limit: 50
        }).catch(() => ({ proposals: [] }));

        this.proposals = (list && list.proposals) || [];
        this.renderList();
      } catch (e) {
        el.innerHTML = '<div class="p-8 text-center text-red-500">加载失败: ' + esc(e && e.message) + '</div>';
      }
    },

    renderStatus(st) {
      const el = document.getElementById('kr-status');
      if (!el) return;
      const cards = [
        { label: '提案总数', value: (st && st.total) || 0 },
        { label: '待审核', value: (st && st.pending_review) || 0 },
        { label: '已采纳', value: (st && st.applied) || 0 },
        { label: '已驳回', value: (st && st.rejected) || 0 }
      ];
      el.innerHTML = cards.map(function (c) {
        return '<div class="bg-white rounded-lg shadow p-4">' +
          '<div class="text-xs text-gray-500">' + c.label + '</div>' +
          '<div class="text-xl font-semibold mt-1 text-gray-800">' + c.value + '</div>' +
          '</div>';
      }).join('');
    },

    renderList() {
      const el = document.getElementById('kr-content');
      if (!el) return;

      if (!this.proposals.length) {
        el.innerHTML = '<div class="p-8 text-center text-gray-500">暂无待审核提案</div>';
        return;
      }

      const self = this;
      el.innerHTML =
        '<div class="px-4 py-3 border-b border-gray-200 font-medium text-gray-700">待审核提案</div>' +
        '<div class="overflow-x-auto"><table class="w-full text-sm">' +
        '<thead class="bg-gray-50"><tr>' +
        '<th class="px-4 py-3 text-left font-medium text-gray-600">标题</th>' +
        '<th class="px-4 py-3 text-left font-medium text-gray-600">类型</th>' +
        '<th class="px-4 py-3 text-left font-medium text-gray-600">目标</th>' +
        '<th class="px-4 py-3 text-left font-medium text-gray-600">AI 评分</th>' +
        '<th class="px-4 py-3 text-left font-medium text-gray-600">操作</th>' +
        '</tr></thead><tbody class="divide-y divide-gray-100">' +
        this.proposals.map(function (p) {
          const score = (p.ai_score == null) ? '<span class="text-gray-400">未评分</span>' : String(p.ai_score);
          return '<tr class="hover:bg-gray-50">' +
            '<td class="px-4 py-3 font-medium text-gray-800">' + esc(p.title) + '</td>' +
            '<td class="px-4 py-3 text-gray-600">' + esc(p.proposal_type) + '</td>' +
            '<td class="px-4 py-3 text-gray-600">' + esc(p.target_entity_key || p.target_entity_type) + '</td>' +
            '<td class="px-4 py-3 text-gray-600">' + score + '</td>' +
            '<td class="px-4 py-3">' +
              '<div class="flex gap-1">' +
                '<button onclick="KnowledgeReviewPage.showDetail(\'' + p.id + '\')" ' +
                  'class="px-2 py-1 text-xs text-gray-600 hover:bg-gray-100 rounded">详情</button>' +
                '<button onclick="KnowledgeReviewPage.review(\'' + p.id + '\',\'approve\')" ' +
                  'class="px-2 py-1 text-xs text-green-600 hover:bg-green-50 rounded">通过</button>' +
                '<button onclick="KnowledgeReviewPage.review(\'' + p.id + '\',\'reject\')" ' +
                  'class="px-2 py-1 text-xs text-red-600 hover:bg-red-50 rounded">驳回</button>' +
              '</div>' +
            '</td>' +
            '</tr>';
        }).join('') +
        '</tbody></table></div>';

      void self;
    },

    async showDetail(id) {
      const { workspace, project } = state();
      try {
        const r = await window.ApiClient.callTool('system.evolution.get', { workspace, project, proposal_id: id });
        const p = (r && r.proposal) ? r.proposal : r;
        ModalDialog.show({
          title: p.title || '提案详情',
          content:
            '<div class="space-y-3 text-sm">' +
            '<div><span class="text-gray-500">类型：</span>' + esc(p.proposal_type) + '</div>' +
            '<div><span class="text-gray-500">状态：</span>' + esc(p.status) + '</div>' +
            '<div><span class="text-gray-500">理由：</span>' + esc(p.evolution_reason) + '</div>' +
            '<div><span class="text-gray-500">描述：</span>' + esc(p.description) + '</div>' +
            '</div>'
        });
      } catch (e) {
        alert('加载详情失败: ' + (e && e.message));
      }
    },

    async review(id, decision) {
      const { workspace, project } = state();
      const reason = (decision === 'reject') ? (prompt('请输入驳回理由：') || '管理员驳回') : undefined;
      try {
        await window.ApiClient.callTool('system.evolution.admin_review', {
          workspace, project, proposal_id: id, decision, reason
        });
        alert(decision === 'approve' ? '已通过' : '已驳回');
        await this.loadData();
      } catch (e) {
        alert('操作失败: ' + (e && e.message));
      }
    },

    async runAudit() {
      const { workspace, project } = state();
      const mode = (document.getElementById('kr-audit-mode') || {}).value || undefined;
      try {
        const r = await window.ApiClient.callTool('knowledge.audit_all', { workspace, project, mode });
        const n = (r && r.total_proposals) || 0;
        alert('审计完成，产出 ' + n + ' 条提案');
        await this.loadData();
      } catch (e) {
        alert('审计失败: ' + (e && e.message));
      }
    },

    async runDebate() {
      const { workspace, project } = state();
      try {
        const r = await window.ApiClient.callTool('knowledge.council_debate_all', { workspace, project });
        alert('委员会裁决完成：通过 ' + ((r && r.approved) || 0) + ' 条，驳回 ' + ((r && r.rejected) || 0) + ' 条');
        await this.loadData();
      } catch (e) {
        alert('裁决失败: ' + (e && e.message));
      }
    }
  };
})();
