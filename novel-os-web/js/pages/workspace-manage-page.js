/**
 * Novel OS - Workspace Manage Page
 * 工作区管理页面 - CRUD + 成员管理
 * @version 2.0.0
 */
(function() {
  'use strict';

  if (window.WorkspaceManagePage) {
    return;
  }

  window.WorkspaceManagePage = {
    workspaces: [],
    currentFilters: {},

    async init() {
      console.log('[WorkspaceManagePage] Initializing...');
      this.render();
      await this.loadData();
      return true;
    },

    render() {
      const contentArea = document.getElementById('content-area');
      if (!contentArea) return;

      contentArea.innerHTML = `
        <div class="space-y-4">
          <!-- 页面标题 -->
          <div class="flex items-center justify-between">
            <div>
              <h1 class="text-2xl font-bold text-gray-800">${window.t('nav.workspaceManage') || '工作区管理'}</h1>
              <p class="text-gray-500 mt-1">管理工作空间和成员</p>
            </div>
            <div class="flex gap-2">
              <button onclick="WorkspaceManagePage.showCreateModal()" 
                      class="px-4 py-2 bg-primary-600 text-white rounded-lg hover:bg-primary-700 transition-colors flex items-center gap-2">
                <span>➕</span> 创建工作区
              </button>
              <button onclick="WorkspaceManagePage.loadData()" 
                      class="px-4 py-2 bg-gray-100 text-gray-700 rounded-lg hover:bg-gray-200 transition-colors">
                🔄 刷新
              </button>
            </div>
          </div>

          <!-- 搜索栏 -->
          <div class="flex gap-4 items-center">
            <div class="flex-1 relative">
              <input type="text" 
                     id="workspace-search" 
                     placeholder="搜索工作区标识或名称..." 
                     oninput="WorkspaceManagePage.handleSearch(this.value)"
                     class="w-full px-4 py-2 pl-10 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary-500 focus:border-transparent">
              <span class="absolute left-3 top-2.5 text-gray-400">🔍</span>
            </div>
          </div>

          <!-- 工作区列表 -->
          <div id="workspace-list-container" class="bg-white rounded-lg shadow">
            <div class="p-8 text-center text-gray-500">
              <div class="spinner w-8 h-8 border-4 border-primary-600 border-t-transparent rounded-full animate-spin mx-auto"></div>
              <p class="mt-2">加载中...</p>
            </div>
          </div>
        </div>

        <!-- 创建/编辑模态框 -->
        <div id="workspace-modal" class="fixed inset-0 bg-black/50 z-50 hidden flex items-center justify-center">
          <div class="bg-white rounded-lg shadow-xl w-full max-w-md mx-4">
            <div class="px-6 py-4 border-b border-gray-200 flex items-center justify-between">
              <h3 id="workspace-modal-title" class="text-lg font-semibold">创建工作区</h3>
              <button onclick="WorkspaceManagePage.hideModal()" class="text-gray-400 hover:text-gray-600">
                <svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12"/>
                </svg>
              </button>
            </div>
            <div class="p-6">
              <form id="workspace-form">
                <input type="hidden" id="workspace-slug-original">
                <div class="space-y-4">
                  <div>
                    <label class="block text-sm font-medium text-gray-700 mb-1">标识(slug) <span class="text-red-500">*</span></label>
                    <input type="text" 
                           id="workspace-slug" 
required
                            placeholder="例如: my-team"
                           class="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary-500 focus:border-transparent font-mono text-sm">
                    <p class="text-xs text-gray-500 mt-1">只允许小写字母、数字和横线</p>
                  </div>
                  <div>
                    <label class="block text-sm font-medium text-gray-700 mb-1">名称 <span class="text-red-500">*</span></label>
                    <input type="text" 
                           id="workspace-name" 
                           required
                           placeholder="例如: 我的团队"
                           class="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary-500 focus:border-transparent">
                  </div>
                  <div>
                    <label class="block text-sm font-medium text-gray-700 mb-1">描述</label>
                    <textarea id="workspace-description" 
                              rows="3"
                              placeholder="工作区简介（可选）"
                              class="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary-500 focus:border-transparent resize-y"></textarea>
                  </div>
                </div>
                <div class="mt-6 flex justify-end gap-3">
                  <button type="button" onclick="WorkspaceManagePage.hideModal()" 
                          class="px-4 py-2 border border-gray-300 rounded-lg hover:bg-gray-50 transition-colors">
                    取消
                  </button>
                  <button type="button" id="workspace-save-btn" onclick="WorkspaceManagePage.saveWorkspace()" class="px-4 py-2 bg-primary-600 text-white rounded-lg hover:bg-primary-700 transition-colors">
                    保存
                  </button>
                </div>
              </form>
            </div>
          </div>
        </div>

        <!-- 成员管理模态框 -->
        <div id="workspace-members-modal" class="fixed inset-0 bg-black/50 z-50 hidden flex items-center justify-center">
          <div class="bg-white rounded-lg shadow-xl w-full max-w-lg mx-4 max-h-[80vh] flex flex-col">
            <div class="px-6 py-4 border-b border-gray-200 flex items-center justify-between">
              <h3 id="workspace-members-title" class="text-lg font-semibold">工作区成员</h3>
              <button onclick="WorkspaceManagePage.hideMembersModal()" class="text-gray-400 hover:text-gray-600">
                <svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12"/>
                </svg>
              </button>
            </div>
            <div id="workspace-members-content" class="p-6 overflow-y-auto flex-1">
              <div class="text-center text-gray-500">加载中...</div>
            </div>
          </div>
        </div>
      `;
    },

    async loadData() {
      const container = document.getElementById('workspace-list-container');

      try {
        const result = await window.ApiClient.callTool('workspace.list');
        this.workspaces = Array.isArray(result) ? result : (result?.workspaces || result?.result || []);
        this.renderList(this.workspaces);
      } catch (error) {
        console.error('[WorkspaceManagePage] Load error:', error);
        container.innerHTML = `
          <div class="p-8 text-center text-red-500">
            <p>加载失败: ${error.message}</p>
            <button onclick="WorkspaceManagePage.loadData()" class="mt-4 px-4 py-2 bg-gray-100 rounded hover:bg-gray-200">
              重试
            </button>
          </div>
        `;
        if (window.showToast) {
          window.showToast('error', '加载工作区列表失败');
        }
      }
    },

    renderList(workspaces) {
      const container = document.getElementById('workspace-list-container');

      // 应用搜索筛选
      const searchTerm = (document.getElementById('workspace-search')?.value || '').toLowerCase();
      if (searchTerm) {
        workspaces = workspaces.filter(w =>
          (w.slug || '').toLowerCase().includes(searchTerm) ||
          (w.name || '').toLowerCase().includes(searchTerm) ||
          (w.description || '').toLowerCase().includes(searchTerm)
        );
      }

      if (!workspaces || workspaces.length === 0) {
        container.innerHTML = `
          <div class="p-8 text-center text-gray-500">
            <div class="text-4xl mb-4">🏢</div>
            <p>暂无工作区</p>
            <p class="text-sm mt-2">点击右上角按钮创建第一个工作区</p>
          </div>
        `;
        return;
      }

      container.innerHTML = `
        <div class="overflow-x-auto">
          <table class="w-full text-sm">
            <thead class="bg-gray-50">
              <tr>
                <th class="px-4 py-3 text-left font-medium text-gray-600">标识</th>
                <th class="px-4 py-3 text-left font-medium text-gray-600">名称</th>
                <th class="px-4 py-3 text-left font-medium text-gray-600">描述</th>
                <th class="px-4 py-3 text-left font-medium text-gray-600">我的角色</th>
                <th class="px-4 py-3 text-left font-medium text-gray-600">操作</th>
              </tr>
            </thead>
            <tbody class="divide-y divide-gray-100">
              ${workspaces.map(w => `
                <tr class="hover:bg-gray-50">
                  <td class="px-4 py-3 font-medium text-gray-800 font-mono">${w.slug || '-'}</td>
                  <td class="px-4 py-3 text-gray-600">${w.name || '-'}</td>
                  <td class="px-4 py-3 text-gray-500 max-w-[300px] truncate" title="${(w.description || '').replace(/"/g, '&quot;')}">${w.description || '-'}</td>
                  <td class="px-4 py-3">
                    <span class="px-2 py-1 text-xs rounded bg-blue-100 text-blue-700">${w.member_role || 'member'}</span>
                  </td>
                  <td class="px-4 py-3">
                    <div class="flex gap-1">
                      <button onclick="WorkspaceManagePage.editWorkspace('${w.slug}')" 
                              class="px-2 py-1 text-xs text-blue-600 hover:bg-blue-50 rounded transition-colors">编辑</button>
                      <button onclick="WorkspaceManagePage.showMembersModal('${w.slug}')" 
                              class="px-2 py-1 text-xs text-green-600 hover:bg-green-50 rounded transition-colors">成员</button>
                      ${w.member_role === 'owner' || w.member_role === 'admin' ? `
                        <button onclick="WorkspaceManagePage.deleteWorkspace('${w.slug}', '${w.name}')" 
                                class="px-2 py-1 text-xs text-red-600 hover:bg-red-50 rounded transition-colors">删除</button>
                      ` : ''}
                    </div>
                  </td>
                </tr>
              `).join('')}
            </tbody>
          </table>
        </div>
      `;
    },

    handleSearch(value) {
      this.renderList(this.workspaces);
    },

    showCreateModal() {
      ModalDialog.show({
        title: '创建工作区',
        content: this._formContent(),
        confirmText: '创建',
        onConfirm: async () => { await this._handleSave(); }
      });
    },

    _formContent(ws) {
      var d = ws || {};
      return '<div class="space-y-4">'
        + '<div><label class="block text-sm font-medium mb-1">标识(slug) *</label>'
        + '<input id="ws-slug" class="w-full border rounded px-3 py-2" value="' + (d.slug||'') + '" ' + (ws?'readonly':'') + '></div>'
        + '<div><label class="block text-sm font-medium mb-1">名称 *</label>'
        + '<input id="ws-name" class="w-full border rounded px-3 py-2" value="' + (d.name||'') + '"></div>'
        + '<input type="hidden" id="ws-original" value="' + (d.slug||'') + '">'
        + '</div>';
    },

async _handleSave() {
      var slug = document.getElementById('ws-slug').value.trim();
      var name = document.getElementById('ws-name').value.trim();
      if (!slug || !name) { alert('标识和名称为必填'); return; }
      try {
        var original = document.getElementById('ws-original').value;
        if (original) { alert('工作区暂不支持编辑，请删除后重新创建'); return; }
        await window.ApiClient.callTool('workspace.create', { slug, name });
        ModalDialog.close();
        await this.loadData();
        window.AppCore?.toast?.('创建成功', 'success');
      } catch(e) { alert('保存失败: ' + e.message); }
    },

    async editWorkspace(slug) {
      var ws = this.workspaces.find(function(w) { return w.slug === slug; });
      if (!ws) return;
      ModalDialog.show({
        title: '编辑工作区',
        content: this._formContent(ws),
        confirmText: '保存',
        onConfirm: async () => { await this._handleSave(); }
      });
    },

    async deleteWorkspace(slug, name) {
      if (!confirm(`确定删除工作区 "${name || slug}" 吗？此操作不可恢复。`)) return;

      try {
        await window.ApiClient.callTool('workspace.delete', { slug });
        if (window.showToast) window.showToast('success', '工作区已删除');
        await this.loadData();
      } catch (error) {
        console.error('[WorkspaceManagePage] Delete error:', error);
        if (window.showToast) {
          window.showToast('error', '删除失败: ' + error.message);
        } else {
          alert('删除失败: ' + error.message);
        }
      }
    },

    async showMembersModal(workspaceSlug) {
      const modal = document.getElementById('workspace-members-modal');
      const content = document.getElementById('workspace-members-content');
      const title = document.getElementById('workspace-members-title');

      title.textContent = `工作区成员: ${workspaceSlug}`;
      content.innerHTML = '<div class="text-center text-gray-500"><div class="spinner w-6 h-6 border-2 border-primary-600 border-t-transparent rounded-full animate-spin mx-auto"></div><p class="mt-2">加载中...</p></div>';
      modal.classList.remove('hidden');

      try {
        // 加载所有用户和当前成员
        const [usersResult, projectsResult] = await Promise.all([
          window.ApiClient.callTool('user.list').catch(() => []),
          window.ApiClient.callTool('project.list', { workspace: workspaceSlug }).catch(() => [])
        ]);

        const allUsers = Array.isArray(usersResult) ? usersResult : (usersResult?.users || []);
        const projects = Array.isArray(projectsResult) ? projectsResult : (projectsResult?.projects || []);

        // 获取成员列表
        let members = [];
        if (projects.length > 0) {
          try {
            const membersResult = await window.ApiClient.callTool('project.list_members', {
              workspace: workspaceSlug,
              project: projects[0].slug
            }).catch(() => []);
            members = Array.isArray(membersResult) ? membersResult : (membersResult?.members || []);
          } catch (e) {
            console.log('Failed to load members:', e);
          }
        }

        const memberUsernames = members.map(m => m.username || m.user);
        const nonMembers = allUsers.filter(u => !memberUsernames.includes(u.username));

        content.innerHTML = `
          <div class="space-y-6">
            <!-- 添加新成员 -->
            <div class="border-b pb-4">
              <h4 class="font-medium mb-3">添加成员</h4>
              <div class="flex gap-2">
                <select id="new-member-user" class="flex-1 border rounded px-3 py-2 text-sm">
                  <option value="">选择用户...</option>
                  ${nonMembers.map(u => `<option value="${u.username}">${u.username} ${u.display_name ? '(' + u.display_name + ')' : ''}</option>`).join('')}
                </select>
                <select id="new-member-role" class="border rounded px-3 py-2 text-sm">
                  <option value="writer">writer</option>
                  <option value="reader">reader</option>
                  <option value="admin">admin</option>
                </select>
                <button onclick="WorkspaceManagePage.addMember('${workspaceSlug}')" 
                        class="px-4 py-2 bg-primary-600 text-white rounded text-sm hover:bg-primary-700 transition-colors">添加</button>
              </div>
            </div>

            <!-- 当前成员列表 -->
            <div>
              <h4 class="font-medium mb-3">当前成员 (${members.length})</h4>
              ${members.length === 0 ?
                '<p class="text-gray-500 text-sm">暂无成员</p>' :
                `<div class="space-y-2">
                  ${members.map(m => `
                    <div class="flex items-center justify-between p-3 bg-gray-50 rounded">
                      <div>
                        <span class="font-medium">${m.username || m.user}</span>
                        <span class="ml-2 text-xs px-2 py-0.5 bg-blue-100 text-blue-700 rounded">${m.role || 'member'}</span>
                      </div>
                      <button onclick="WorkspaceManagePage.removeMember('${workspaceSlug}', '${m.username || m.user}')" 
                              class="text-xs text-red-600 hover:underline">移除</button>
                    </div>
                  `).join('')}
                </div>`
              }
            </div>
          </div>
        `;
      } catch (error) {
        console.error('[WorkspaceManagePage] Load members error:', error);
        content.innerHTML = `<div class="text-center text-red-500">加载成员失败: ${error.message}</div>`;
        if (window.showToast) window.showToast('error', '加载成员失败');
      }
    },

    hideMembersModal() {
      document.getElementById('workspace-members-modal').classList.add('hidden');
    },

    async addMember(workspaceSlug) {
      const username = document.getElementById('new-member-user')?.value;
      const role = document.getElementById('new-member-role')?.value;

      if (!username) {
        if (window.showToast) window.showToast('warning', '请选择用户');
        return;
      }

      try {
        await window.ApiClient.callTool('workspace.add_member', { workspace: workspaceSlug, username, role });
        if (window.showToast) window.showToast('success', '成员添加成功');
        // 刷新成员列表
        await this.showMembersModal(workspaceSlug);
      } catch (error) {
        console.error('[WorkspaceManagePage] Add member error:', error);
        if (window.showToast) {
          window.showToast('error', '添加失败: ' + error.message);
        } else {
          alert('添加失败: ' + error.message);
        }
      }
    },

    async removeMember(workspaceSlug, username) {
      if (!confirm(`确定从工作区移除成员 "${username}" 吗？`)) return;

      try {
        await window.ApiClient.callTool('workspace.remove_member', { workspace: workspaceSlug, username });
        if (window.showToast) window.showToast('success', '成员已移除');
        // 刷新成员列表
        await this.showMembersModal(workspaceSlug);
      } catch (error) {
        console.error('[WorkspaceManagePage] Remove member error:', error);
        if (window.showToast) {
          window.showToast('error', '移除失败: ' + error.message);
        } else {
          alert('移除失败: ' + error.message);
        }
      }
    }
  };
})();
