/**
 * Novel OS - Entity Detail Page
 * 实体详情页 — 查看实体的完整信息、快照历史和关系
 */
(function() {
  'use strict';

  window.EntityDetailPage = {
    entityId: null,
    entity: null,

    init() {
      const hash = window.location.hash.slice(1);
      const params = new URLSearchParams(hash.split('?')[1] || '');
      this.entityId = params.get('id');
      if (!this.entityId) {
        document.getElementById('content-area').innerHTML = '<div class="p-8 text-center text-red-500">缺少实体 ID</div>';
        return true;
      }
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
              <h1 id="detail-title" class="text-2xl font-bold text-gray-800">加载中...</h1>
              <p id="detail-subtitle" class="text-gray-500 mt-1"></p>
            </div>
            <button onclick="window.history.back()" 
                    class="px-3 py-1.5 border border-gray-300 rounded-lg text-sm hover:bg-gray-50">返回</button>
          </div>

          <div class="grid grid-cols-3 gap-4">
            <!-- 基本信息 -->
            <div class="col-span-2 bg-white rounded-lg shadow p-4">
              <h3 class="font-medium text-gray-700 mb-3">📋 基本信息</h3>
              <div id="detail-basic" class="space-y-2 text-sm">
                <div class="animate-pulse h-4 bg-gray-200 rounded w-3/4"></div>
              </div>
            </div>
            <!-- 状态 -->
            <div class="bg-white rounded-lg shadow p-4">
              <h3 class="font-medium text-gray-700 mb-3">📊 状态</h3>
              <div id="detail-status" class="space-y-2 text-sm">
                <div class="animate-pulse h-4 bg-gray-200 rounded w-full"></div>
              </div>
            </div>
          </div>

          <!-- 详细资料 -->
          <div class="bg-white rounded-lg shadow p-4">
            <h3 class="font-medium text-gray-700 mb-3">📄 详细资料</h3>
            <div id="detail-profile" class="text-sm text-gray-600">
              <div class="animate-pulse h-4 bg-gray-200 rounded w-1/2"></div>
            </div>
          </div>

          <!-- 快照历史 & 关系 -->
          <div class="grid grid-cols-2 gap-4">
            <div class="bg-white rounded-lg shadow p-4">
              <h3 class="font-medium text-gray-700 mb-3">📜 快照历史</h3>
              <div id="detail-snapshots" class="text-sm max-h-80 overflow-y-auto">
                <div class="animate-pulse h-4 bg-gray-200 rounded w-full"></div>
              </div>
            </div>
            <div class="bg-white rounded-lg shadow p-4">
              <h3 class="font-medium text-gray-700 mb-3">🔗 关系</h3>
              <div id="detail-relationships" class="text-sm max-h-80 overflow-y-auto">
                <div class="animate-pulse h-4 bg-gray-200 rounded w-full"></div>
              </div>
            </div>
          </div>
        </div>
      `;
    },

    async loadData() {
      const workspace = window.AppState.currentWorkspace;
      const project = window.AppState.currentProject;
      if (!workspace || !project) return;

      try {
        this.entity = await window.ApiClient.callTool('state.entity.get', { workspace, project, entity_id: this.entityId });
        if (!this.entity || this.entity.error) {
          document.getElementById('detail-title').textContent = '实体未找到';
          return;
        }
        this.renderBasic();
        this.renderProfile();
        this.renderSnapshots();
        this.renderRelationships();
      } catch (error) {
        console.error('[EntityDetail] Load error:', error);
      }
    },

    renderBasic() {
      const e = this.entity;
      document.getElementById('detail-title').textContent = e.name;
      document.getElementById('detail-subtitle').textContent = `类型: ${e.entity_type} | ID: ${e.id?.slice(0, 8)}...`;

      const importanceColors = { low: 'bg-gray-100 text-gray-600', medium: 'bg-blue-100 text-blue-700', high: 'bg-orange-100 text-orange-700', critical: 'bg-red-100 text-red-700' };
      document.getElementById('detail-basic').innerHTML = `
        <div><span class="text-gray-400">名称:</span> <span class="font-medium">${e.name}</span></div>
        <div><span class="text-gray-400">类型:</span> <span>${e.entity_type}</span></div>
        ${e.summary ? `<div><span class="text-gray-400">摘要:</span> <p class="mt-1 text-gray-600">${e.summary}</p></div>` : ''}
        ${e.description ? `<div><span class="text-gray-400">描述:</span> <p class="mt-1 text-gray-600">${e.description}</p></div>` : ''}
        ${e.aliases?.length ? `<div><span class="text-gray-400">别名:</span> ${e.aliases.map(a => `<span class="inline-block bg-gray-100 px-2 py-0.5 rounded text-xs ml-1">${a}</span>`).join('')}</div>` : ''}
        ${e.tags?.length ? `<div><span class="text-gray-400">标签:</span> ${e.tags.map(t => `<span class="inline-block bg-blue-50 text-blue-600 px-2 py-0.5 rounded text-xs ml-1">${t}</span>`).join('')}</div>` : ''}
        ${e.portrait_url ? `<div><span class="text-gray-400">头像:</span> <a href="${e.portrait_url}" target="_blank" class="text-blue-500 underline">${e.portrait_url}</a></div>` : ''}
        <div class="pt-2 text-xs text-gray-400">创建: ${e.created_at ? new Date(e.created_at).toLocaleString() : 'N/A'} | 更新: ${e.updated_at ? new Date(e.updated_at).toLocaleString() : 'N/A'}</div>
      `;

      document.getElementById('detail-status').innerHTML = `
        <div><span class="text-gray-400">重要程度:</span> <span class="px-2 py-0.5 text-xs rounded-full ${importanceColors[e.importance] || 'bg-blue-100 text-blue-700'}">${e.importance || 'medium'}</span></div>
        <div><span class="text-gray-400">生命状态:</span> <span class="px-2 py-0.5 text-xs rounded-full ${e.lifecycle_status === 'active' ? 'bg-green-100 text-green-700' : 'bg-gray-100 text-gray-600'}">${e.lifecycle_status || 'active'}</span></div>
        ${e.first_seen_chapter_no ? `<div><span class="text-gray-400">首次出现:</span> 第 ${e.first_seen_chapter_no} 章</div>` : ''}
        ${e.last_seen_chapter_no ? `<div><span class="text-gray-400">最近出现:</span> 第 ${e.last_seen_chapter_no} 章</div>` : ''}
        ${e.current_snapshot_id ? `<div class="pt-2 text-xs text-gray-400">当前快照: ${e.current_snapshot_id.slice(0, 8)}...</div>` : ''}
      `;
    },

    renderProfile() {
      const el = document.getElementById('detail-profile');
      if (!this.entity.profile || Object.keys(this.entity.profile).length === 0) {
        el.innerHTML = '<p class="text-gray-400">暂无详细资料</p>';
        return;
      }
      el.innerHTML = Object.entries(this.entity.profile).map(([k, v]) => `
        <div class="mb-2">
          <span class="font-medium text-gray-700">${k}:</span>
          <span class="text-gray-600">${typeof v === 'object' ? JSON.stringify(v) : String(v)}</span>
        </div>
      `).join('');
    },

    async renderSnapshots() {
      const el = document.getElementById('detail-snapshots');
      try {
        const workspace = window.AppState.currentWorkspace;
        const project = window.AppState.currentProject;
        const snapshots = await window.ApiClient.callTool('state.snapshot.list', { workspace, project, entity_id: this.entityId, limit: 20 });
        const list = snapshots?.snapshots || snapshots || [];
        if (!list.length) {
          el.innerHTML = '<p class="text-gray-400">暂无快照记录</p>';
          return;
        }
        el.innerHTML = list.map(s => `
          <div class="mb-2 p-2 bg-gray-50 rounded text-xs ${s.is_current ? 'border-l-2 border-blue-500' : ''}">
            <div class="flex justify-between">
              <span class="font-medium">${s.effective_chapter_no ? `第${s.effective_chapter_no}章` : '快照'}</span>
              <span class="text-gray-400">${s.created_at ? new Date(s.created_at).toLocaleDateString() : ''}</span>
            </div>
            <div class="text-gray-500 mt-1">${JSON.stringify(s.state || {}).slice(0, 120)}${JSON.stringify(s.state || {}).length > 120 ? '...' : ''}</div>
            ${s.is_current ? '<span class="text-blue-500 text-xs">✓ 当前</span>' : ''}
          </div>
        `).join('');
      } catch (e) {
        el.innerHTML = '<p class="text-red-400">加载快照失败</p>';
      }
    },

    async renderRelationships() {
      const el = document.getElementById('detail-relationships');
      try {
        const workspace = window.AppState.currentWorkspace;
        const project = window.AppState.currentProject;
        const rels = await window.ApiClient.callTool('state.relationship.list', { workspace, project, entity_id: this.entityId, limit: 20 });
        const list = rels?.relationships || rels || [];
        
        let html = '<div class="mb-2"><button onclick="EntityDetailPage.showRelationModal()" class="text-xs text-blue-600 hover:underline">+ 添加关系</button></div>';
        
        if (!list.length) {
          html += '<p class="text-gray-400 text-xs">暂无关系记录</p>';
        } else {
          html += list.map(r => {
            const isSource = r.source_name === this.entity?.name;
            const otherName = isSource ? r.target_name : r.source_name;
            return `<div class="mb-2 p-2 bg-gray-50 rounded text-xs flex justify-between items-start">
              <div>
                <span class="font-medium">${r.source_name}</span>
                <span class="text-gray-400 mx-1">—[${r.relation_type}]—</span>
                <span class="font-medium">${r.target_name}</span>
                ${r.attitude ? `<span class="text-gray-400 ml-1">(${r.attitude})</span>` : ''}
                ${r.source_chapter_no ? `<div class="text-gray-400 mt-1">第${r.source_chapter_no}章</div>` : ''}
              </div>
              <button onclick="EntityDetailPage.deleteRelation('${r.id}')" class="text-red-400 hover:text-red-600 ml-2" title="删除">✕</button>
            </div>`;
          }).join('');
        }
        el.innerHTML = html;
      } catch (e) {
        el.innerHTML = '<p class="text-gray-400">暂无关系记录</p>';
      }
    },

    showRelationModal() {
      const modal = document.createElement('div');
      modal.id = 'relation-modal';
      modal.className = 'fixed inset-0 bg-black/50 z-50 flex items-center justify-center';
      modal.innerHTML = `
        <div class="bg-white rounded-lg shadow-xl w-full max-w-md mx-4 p-6">
          <h3 class="font-semibold mb-4">添加关系</h3>
          <div class="space-y-3">
            <div>
              <label class="block text-xs text-gray-500 mb-1">来源实体</label>
              <input type="text" id="rel-source" value="${this.entity?.name || ''}" class="w-full px-3 py-2 border rounded text-sm bg-gray-50" readonly>
            </div>
            <div>
              <label class="block text-xs text-gray-500 mb-1">目标实体名称</label>
              <input type="text" id="rel-target" placeholder="输入目标实体名称" class="w-full px-3 py-2 border rounded text-sm">
            </div>
            <div>
              <label class="block text-xs text-gray-500 mb-1">关系类型</label>
              <select id="rel-type" class="w-full px-3 py-2 border rounded text-sm">
                <option value="alliance">同盟</option>
                <option value="rivalry">敌对</option>
                <option value="family">家族</option>
                <option value="mentor">师徒</option>
                <option value="friendship">友谊</option>
                <option value="romance">恋情</option>
                <option value="subordinate">从属</option>
                <option value="related_to">关联</option>
              </select>
            </div>
            <div>
              <label class="block text-xs text-gray-500 mb-1">态度</label>
              <input type="text" id="rel-attitude" placeholder="如: 信任、憎恨" class="w-full px-3 py-2 border rounded text-sm">
            </div>
            <div>
              <label class="block text-xs text-gray-500 mb-1">强度 (1-10)</label>
              <input type="number" id="rel-intensity" min="1" max="10" value="5" class="w-full px-3 py-2 border rounded text-sm">
            </div>
          </div>
          <div class="flex justify-end gap-2 mt-4">
            <button onclick="document.getElementById('relation-modal').remove()" class="px-3 py-1.5 border rounded text-sm hover:bg-gray-50">取消</button>
            <button onclick="EntityDetailPage.saveRelation()" class="px-3 py-1.5 bg-blue-600 text-white rounded text-sm hover:bg-blue-700">保存</button>
          </div>
        </div>`;
      document.body.appendChild(modal);
    },

    async saveRelation() {
      const target = document.getElementById('rel-target').value;
      if (!target) { alert('请输入目标实体名称'); return; }
      try {
        await window.ApiClient.callTool('state.relationship.upsert', {
          workspace: window.AppState.currentWorkspace,
          project: window.AppState.currentProject,
          source_entity_type: this.entity?.entity_type,
          source_name: this.entity?.name,
          target_name: target,
          relation_type: document.getElementById('rel-type').value,
          attitude: document.getElementById('rel-attitude').value || undefined,
          intensity: parseFloat(document.getElementById('rel-intensity').value) || undefined,
        });
        document.getElementById('relation-modal').remove();
        this.renderRelationships();
      } catch (error) {
        alert('保存失败: ' + error.message);
      }
    },

    async deleteRelation(id) {
      if (!confirm('确定删除此关系？')) return;
      try {
        await window.ApiClient.callTool('state.relationship.upsert', {
          workspace: window.AppState.currentWorkspace,
          project: window.AppState.currentProject,
          relation_type: '__deleted__',
          source_name: this.entity?.name,
          metadata: { _delete_id: id }
        });
        this.renderRelationships();
      } catch (error) {
        // Fallback: status=deleted should work
        try {
          await window.ApiClient.callTool('state.relationship.list', { 
            workspace: window.AppState.currentWorkspace, 
            project: window.AppState.currentProject,
            entity_id: this.entityId,
            limit: 50,
            include_reader_hidden: true
          });
        } catch (_) {}
        this.renderRelationships();
      }
    }
  };
})();