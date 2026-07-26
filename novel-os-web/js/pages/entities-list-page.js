/**
 * Novel OS - Entities List Page
 * 实体管理页面（角色、地点、势力、物品等）
 */
(function() {
  'use strict';

  window.EntitiesListPage = {
    entityType: null,

    init() {
      this.render();
      this.loadData();
      return true;
    },

    render() {
      const contentArea = document.getElementById('content-area');
      contentArea.innerHTML = `
        <div class="max-w-6xl mx-auto space-y-4">
          <div class="flex items-center justify-between">
            <div>
              <h1 class="text-2xl font-bold text-gray-800">${t('nav.entityList')}</h1>
              <p class="text-gray-500 mt-1">管理角色、地点、势力等实体</p>
            </div>
            <button onclick="EntitiesListPage.showCreateModal()" 
                    class="px-4 py-2 bg-primary-600 text-white rounded-lg hover:bg-primary-700 transition-colors">
              ${t('common.new')} 实体
            </button>
          </div>

          <div class="flex gap-4 items-center">
            <input type="text" id="entity-search" placeholder="${t('common.search')}..." 
                   oninput="EntitiesListPage.loadData()"
                   class="flex-1 px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary-500">
            <select id="entity-type-filter" onchange="EntitiesListPage.loadData()" 
                    class="px-4 py-2 border border-gray-300 rounded-lg">
              <option value="">全部类型</option>
              <option value="character">角色</option>
              <option value="location">地点</option>
              <option value="faction">势力</option>
              <option value="item">物品</option>
              <option value="creature">生物</option>
              <option value="concept">概念</option>
              <option value="event">事件</option>
              <option value="organization">组织</option>
            </select>
            <select id="entity-status-filter" onchange="EntitiesListPage.loadData()" 
                    class="px-4 py-2 border border-gray-300 rounded-lg">
              <option value="">全部状态</option>
              <option value="active">活跃</option>
              <option value="inactive">非活跃</option>
              <option value="deceased">已故</option>
            </select>
          </div>

          <div id="entity-list-container" class="bg-white rounded-lg shadow">
            <div class="p-8 text-center text-gray-500">
              <div class="spinner w-8 h-8 border-4 border-primary-600 border-t-transparent rounded-full animate-spin mx-auto"></div>
              <p class="mt-2">${t('common.loading')}</p>
            </div>
          </div>
        </div>

        <!-- 创建/编辑模态框 -->
        <div id="entity-modal" class="fixed inset-0 bg-black/50 z-50 hidden flex items-center justify-center">
          <div class="bg-white rounded-lg shadow-xl w-full max-w-3xl mx-4 max-h-[90vh] overflow-hidden">
            <div class="px-6 py-4 border-b border-gray-200 flex items-center justify-between">
              <h3 id="entity-modal-title" class="text-lg font-semibold">新建实体</h3>
              <button onclick="EntitiesListPage.hideModal()" class="text-gray-400 hover:text-gray-600">
                <svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12"/>
                </svg>
              </button>
            </div>
            <div class="p-6 overflow-y-auto max-h-[60vh]">
              <form id="entity-form" onsubmit="EntitiesListPage.saveEntity(event)">
                <div class="grid grid-cols-2 gap-4">
                  <div>
                    <label class="block text-sm font-medium text-gray-700 mb-1">名称 <span class="text-red-500">*</span></label>
                    <input type="text" id="entity-name" required
                           class="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary-500">
                  </div>
                  <div>
                    <label class="block text-sm font-medium text-gray-700 mb-1">类型 <span class="text-red-500">*</span></label>
                    <select id="entity-type" required
                            class="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary-500">
                      <option value="character">角色</option>
                      <option value="location">地点</option>
                      <option value="faction">势力</option>
                      <option value="item">物品</option>
                      <option value="creature">生物</option>
                      <option value="concept">概念</option>
                      <option value="event">事件</option>
                      <option value="organization">组织</option>
                    </select>
                  </div>
                  <div class="col-span-2">
                    <label class="block text-sm font-medium text-gray-700 mb-1">别名（逗号分隔）</label>
                    <input type="text" id="entity-aliases" placeholder="别名1, 别名2"
                           class="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary-500">
                  </div>
                  <div>
                    <label class="block text-sm font-medium text-gray-700 mb-1">重要程度</label>
                    <select id="entity-importance" 
                            class="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary-500">
                      <option value="low">低</option>
                      <option value="medium" selected>中</option>
                      <option value="high">高</option>
                      <option value="critical">关键</option>
                    </select>
                  </div>
                  <div>
                    <label class="block text-sm font-medium text-gray-700 mb-1">状态</label>
                    <select id="entity-lifecycle-status" 
                            class="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary-500">
                      <option value="active">活跃</option>
                      <option value="inactive">非活跃</option>
                      <option value="deceased">已故</option>
                    </select>
                  </div>
                  <div class="col-span-2">
                    <label class="block text-sm font-medium text-gray-700 mb-1">摘要</label>
                    <textarea id="entity-summary" rows="2"
                              class="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary-500"></textarea>
                  </div>
                  <div class="col-span-2">
                    <label class="block text-sm font-medium text-gray-700 mb-1">详细描述</label>
                    <textarea id="entity-description" rows="3"
                              class="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary-500"></textarea>
                  </div>
                  <div>
                    <label class="block text-sm font-medium text-gray-700 mb-1">标签（逗号分隔）</label>
                    <input type="text" id="entity-tags" placeholder="战士, 法师, 主角"
                           class="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary-500">
                  </div>
                  <div>
                    <label class="block text-sm font-medium text-gray-700 mb-1">首次出现章节</label>
                    <input type="number" id="entity-first-chapter" min="1"
                           class="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary-500">
                  </div>
                  <div>
                    <label class="block text-sm font-medium text-gray-700 mb-1">最近出现章节</label>
                    <input type="number" id="entity-last-chapter" min="1"
                           class="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary-500">
                  </div>
                  <div class="col-span-2">
                    <label class="block text-sm font-medium text-gray-700 mb-1">详细资料 (JSON)</label>
                    <textarea id="entity-profile" rows="4" placeholder='{"appearance": "", "personality": "", "background": ""}'
                              class="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary-500 font-mono text-sm"></textarea>
                  </div>
                </div>
                <div class="mt-6 flex justify-end gap-3">
                  <button type="button" onclick="EntitiesListPage.hideModal()" 
                          class="px-4 py-2 border border-gray-300 rounded-lg hover:bg-gray-50">
                    ${t('common.cancel')}
                  </button>
                  <button type="submit" 
                          class="px-4 py-2 bg-primary-600 text-white rounded-lg hover:bg-primary-700">
                    ${t('common.save')}
                  </button>
                </div>
              </form>
            </div>
          </div>
        </div>
      `;
    },

    async loadData() {
      const container = document.getElementById('entity-list-container');
      try {
        const workspace = window.AppState.currentWorkspace;
        const project = window.AppState.currentProject;
        
        if (!workspace || !project) {
          container.innerHTML = `<div class="p-8 text-center text-gray-500">请先选择工作区和项目</div>`;
          return;
        }

        const typeFilter = document.getElementById('entity-type-filter')?.value;
        const statusFilter = document.getElementById('entity-status-filter')?.value;
        const searchQuery = document.getElementById('entity-search')?.value;
        const params = {};
        if (typeFilter) params.entity_type = typeFilter;
        if (statusFilter) params.lifecycle_status = statusFilter;
        if (searchQuery) params.query = searchQuery;

        const result = await window.ApiClient.callTool('state.entity.list', { workspace, project, ...params });
        this.renderList((result || []).filter(entity => entity.lifecycle_status !== 'deleted'));
      } catch (error) {
        console.error('[EntitiesList] Load error:', error);
        container.innerHTML = `<div class="p-8 text-center text-red-500">加载失败: ${error.message}</div>`;
      }
    },

    renderList(entities) {
      const container = document.getElementById('entity-list-container');
      
      if (!entities || entities.length === 0) {
        container.innerHTML = `
          <div class="p-8 text-center text-gray-500">
            <div class="text-4xl mb-2">👥</div>
            <p>暂无实体</p>
            <p class="text-sm mt-2">点击右上角按钮创建第一个实体</p>
          </div>
        `;
        return;
      }

      container.innerHTML = `
        <div class="divide-y divide-gray-200">
          ${entities.map(entity => `
            <div class="p-4 hover:bg-gray-50 transition-colors">
              <div class="flex items-start justify-between">
                <div class="flex-1 min-w-0">
                  <div class="flex items-center gap-2">
                    <span class="text-lg">${this.getTypeIcon(entity.entity_type)}</span>
                    <h3 class="font-medium text-gray-800 truncate">${entity.name}</h3>
                    <span class="px-2 py-0.5 text-xs rounded-full ${this.getImportanceClass(entity.importance)}">
                      ${entity.importance || 'medium'}
                    </span>
                    ${entity.lifecycle_status && entity.lifecycle_status !== 'active' ? 
                      `<span class="px-2 py-0.5 text-xs rounded-full bg-gray-100 text-gray-600">${entity.lifecycle_status}</span>` : ''}
                  </div>
                  <p class="text-sm text-gray-500 mt-1 line-clamp-2">${entity.summary || '暂无描述'}</p>
                  ${entity.tags && entity.tags.length ? `<div class="flex gap-1 mt-1">${entity.tags.slice(0, 5).map(t => `<span class="text-xs bg-blue-50 text-blue-600 px-1.5 py-0.5 rounded">${t}</span>`).join('')}</div>` : ''}
                  <div class="flex items-center gap-3 mt-1 text-xs text-gray-400">
                    ${entity.first_seen_chapter_no ? `<span>首次: 第${entity.first_seen_chapter_no}章</span>` : ''}
                    ${entity.last_seen_chapter_no ? `<span>最近: 第${entity.last_seen_chapter_no}章</span>` : ''}
                  </div>
                </div>
                <div class="flex items-center gap-2 ml-4">
                  <button onclick="EntitiesListPage.editEntity('${entity.id}')" 
                          class="p-2 text-gray-400 hover:text-primary-600 hover:bg-primary-50 rounded transition-colors" title="编辑">
                    <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M11 5H6a2 2 0 00-2 2v11a2 2 0 002 2h11a2 2 0 002-2v-5m-1.414-9.414a2 2 0 112.828 2.828L11.828 15H9v-2.828l8.586-8.586z"/>
                    </svg>
                  </button>
                  <button onclick="EntitiesListPage.viewDetail('${entity.id}')" 
                          class="p-2 text-gray-400 hover:text-green-600 hover:bg-green-50 rounded transition-colors" title="查看详情">
                    <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M15 12a3 3 0 11-6 0 3 3 0 016 0z"/>
                      <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M2.458 12C3.732 7.943 7.523 5 12 5c4.478 0 8.268 2.943 9.542 7-1.274 4.057-5.064 7-9.542 7-4.477 0-8.268-2.943-9.542-7z"/>
                    </svg>
                  </button>
                  <button onclick="EntitiesListPage.deleteEntity('${entity.entity_type}', '${entity.name}')" 
                          class="p-2 text-gray-400 hover:text-red-600 hover:bg-red-50 rounded transition-colors" title="删除">
                    <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16"/>
                    </svg>
                  </button>
                </div>
              </div>
            </div>
          `).join('')}
        </div>
      `;
    },

    showCreateModal() {
      document.getElementById('entity-modal-title').textContent = '新建实体';
      document.getElementById('entity-name').value = '';
      document.getElementById('entity-type').value = 'character';
      document.getElementById('entity-aliases').value = '';
      document.getElementById('entity-importance').value = 'medium';
      document.getElementById('entity-lifecycle-status').value = 'active';
      document.getElementById('entity-summary').value = '';
      document.getElementById('entity-description').value = '';
      document.getElementById('entity-tags').value = '';
      document.getElementById('entity-first-chapter').value = '';
      document.getElementById('entity-last-chapter').value = '';
      document.getElementById('entity-profile').value = '';
      document.getElementById('entity-modal').classList.remove('hidden');
    },

    hideModal() {
      document.getElementById('entity-modal').classList.add('hidden');
    },

    async editEntity(id) {
      try {
        const workspace = window.AppState.currentWorkspace;
        const project = window.AppState.currentProject;
        const entity = await window.ApiClient.callTool('state.entity.get', { workspace, project, entity_id: id });
        
        document.getElementById('entity-modal-title').textContent = '编辑实体';
        document.getElementById('entity-name').value = entity.name;
        document.getElementById('entity-type').value = entity.entity_type;
        document.getElementById('entity-aliases').value = (entity.aliases || []).join(', ');
        document.getElementById('entity-importance').value = entity.importance || 'medium';
        document.getElementById('entity-lifecycle-status').value = entity.lifecycle_status || 'active';
        document.getElementById('entity-summary').value = entity.summary || '';
        document.getElementById('entity-description').value = entity.description || '';
        document.getElementById('entity-tags').value = (entity.tags || []).join(', ');
        document.getElementById('entity-first-chapter').value = entity.first_seen_chapter_no || '';
        document.getElementById('entity-last-chapter').value = entity.last_seen_chapter_no || '';
        document.getElementById('entity-profile').value = entity.profile ? JSON.stringify(entity.profile, null, 2) : '';
        document.getElementById('entity-modal').classList.remove('hidden');
      } catch (error) {
        alert('加载实体失败: ' + error.message);
      }
    },

    async saveEntity(e) {
      e.preventDefault();
      const workspace = window.AppState.currentWorkspace;
      const project = window.AppState.currentProject;
      
      const aliasesStr = document.getElementById('entity-aliases').value;
      const aliases = aliasesStr ? aliasesStr.split(',').map(a => a.trim()).filter(Boolean) : [];
      const tagsStr = document.getElementById('entity-tags').value;
      const tags = tagsStr ? tagsStr.split(',').map(t => t.trim()).filter(Boolean) : [];
      
      let profile = null;
      const profileStr = document.getElementById('entity-profile').value;
      if (profileStr) {
        try {
          profile = JSON.parse(profileStr);
        } catch (e) {
          alert('JSON 格式错误: ' + e.message);
          return;
        }
      }

      const data = {
        name: document.getElementById('entity-name').value,
        entity_type: document.getElementById('entity-type').value,
        aliases,
        tags,
        importance: document.getElementById('entity-importance').value,
        lifecycle_status: document.getElementById('entity-lifecycle-status').value,
        summary: document.getElementById('entity-summary').value || undefined,
        description: document.getElementById('entity-description').value || undefined,
        first_seen_chapter_no: document.getElementById('entity-first-chapter').value ? parseInt(document.getElementById('entity-first-chapter').value) : undefined,
        last_seen_chapter_no: document.getElementById('entity-last-chapter').value ? parseInt(document.getElementById('entity-last-chapter').value) : undefined,
        profile
      };

      try {
        await window.ApiClient.callTool('state.entity.upsert', { workspace, project, ...data });
        this.hideModal();
        this.loadData();
      } catch (error) {
        alert('保存失败: ' + error.message);
      }
    },

    async deleteEntity(entityType, name) {
      if (!confirm(`确定删除实体 "${name}" 吗？`)) return;
      
      try {
        await window.ApiClient.callTool('state.entity.upsert', { 
          workspace: window.AppState.currentWorkspace, 
          project: window.AppState.currentProject,
          entity_type: entityType,
          name: name,
          lifecycle_status: 'deleted'
        });
        this.loadData();
      } catch (error) {
        alert('删除失败: ' + error.message);
      }
    },

    viewDetail(id) {
      window.location.hash = `/entity/detail?id=${id}`;
    },

    getTypeIcon(type) {
      const icons = {
        character: '👤', location: '📍', faction: '🏴', item: '🎒',
        creature: '🐉', concept: '💡', event: '📅', organization: '🏛️'
      };
      return icons[type] || '📦';
    },

    getImportanceClass(importance) {
      const classes = {
        low: 'bg-gray-100 text-gray-600',
        medium: 'bg-blue-100 text-blue-700',
        high: 'bg-orange-100 text-orange-700',
        critical: 'bg-red-100 text-red-700'
      };
      return classes[importance] || 'bg-blue-100 text-blue-700';
    }
  };
})();
