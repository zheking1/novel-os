/**
 * Member Manage Page
 * 成员管理 - 管理工作区成员
 */
(function() {
  window.MemberManagePage = {
    currentWorkspace: null,

    async init() {
      const contentArea = document.getElementById('content-area');
      contentArea.innerHTML = `
        <div class="flex items-center justify-between mb-6">
          <h1 class="text-2xl font-bold text-gray-800">${window.t('nav.memberManage') || '成员管理'}</h1>
          <div class="flex gap-2">
            <select id="workspace-selector" class="border rounded px-3 py-2 text-sm" onchange="MemberManagePage.onWorkspaceChange(this.value)">
              <option value="">选择工作区...</option>
            </select>
            <button onclick="MemberManagePage.loadData()" class="px-4 py-2 bg-gray-100 text-gray-700 rounded-lg hover:bg-gray-200 text-sm">🔄 刷新</button>
          </div>
        </div>
        <div id="member-content" class="bg-white rounded-lg shadow">
          <div class="p-8 text-center text-gray-500">请先选择工作区</div>
        </div>
      `;
      await this.loadWorkspaces();
      return true;
    },

    async loadWorkspaces() {
      try {
        const result = await window.ApiClient.callTool('workspace.list').catch(() => []);
        const workspaces = Array.isArray(result) ? result : (result?.workspaces || result?.result || []);
        const selector = document.getElementById('workspace-selector');
        if (selector && workspaces.length > 0) {
          selector.innerHTML = '<option value="">选择工作区...</option>' +
            workspaces.map(w => `<option value="${w.slug}">${w.name || w.slug}</option>`).join('');
        }
      } catch (e) {
        console.error('加载工作区失败:', e);
      }
    },

    async onWorkspaceChange(workspaceSlug) {
      this.currentWorkspace = workspaceSlug;
      if (workspaceSlug) {
        await this.loadMembers();
      } else {
        document.getElementById('member-content').innerHTML = '<div class="p-8 text-center text-gray-500">请先选择工作区</div>';
      }
    },

    async loadMembers() {
      const container = document.getElementById('member-content');
      if (!this.currentWorkspace) {
        container.innerHTML = '<div class="p-8 text-center text-gray-500">请先选择工作区</div>';
        return;
      }

      container.innerHTML = '<div class="p-8 text-center text-gray-500">加载中...</div>';

      try {
        // Get projects in this workspace to find members
        const projectsResult = await window.ApiClient.callTool('project.list', { workspace: this.currentWorkspace }).catch(() => []);
        const projects = Array.isArray(projectsResult) ? projectsResult : (projectsResult?.projects || projectsResult?.result || []);

        if (projects.length === 0) {
          container.innerHTML = `<div class="p-8 text-center text-gray-500">该工作区暂无项目，无法获取成员列表</div>`;
          return;
        }

        // Try to get members from first project
        const project = projects[0];
        let members = [];
        try {
          const membersResult = await window.ApiClient.callTool('project.list_members', { workspace: this.currentWorkspace, project: project.slug }).catch(() => []);
          members = Array.isArray(membersResult) ? membersResult : (membersResult?.members || membersResult?.result || []);
        } catch (e) {
          // Fallback: show projects with their member_role
          members = projects.map(p => ({
            username: p.member_role ? '当前用户' : '-',
            role: p.member_role || 'unknown',
            project: p.slug
          }));
        }

        if (!members || members.length === 0) {
          container.innerHTML = `<div class="p-8 text-center text-gray-500">暂无成员数据</div>`;
          return;
        }

        container.innerHTML = `
          <div class="overflow-x-auto">
            <table class="w-full text-sm">
              <thead class="bg-gray-50">
                <tr>
                  <th class="px-4 py-3 text-left font-medium text-gray-600">用户名</th>
                  <th class="px-4 py-3 text-left font-medium text-gray-600">角色</th>
                  <th class="px-4 py-3 text-left font-medium text-gray-600">项目</th>
                  <th class="px-4 py-3 text-left font-medium text-gray-600">操作</th>
                </tr>
              </thead>
              <tbody class="divide-y divide-gray-100">
                ${members.map(m => `
                  <tr class="hover:bg-gray-50">
                    <td class="px-4 py-3 font-medium text-gray-800">${m.username || m.user || '-'}</td>
                    <td class="px-4 py-3"><span class="px-2 py-1 text-xs rounded bg-blue-100 text-blue-700">${m.role || 'member'}</span></td>
                    <td class="px-4 py-3 text-gray-500">${m.project || '-'}</td>
                    <td class="px-4 py-3">
                      <div class="flex gap-1">
                        <button onclick="MemberManagePage.showChangeRoleModal('${m.username || m.user}', '${m.role}')" class="px-2 py-1 text-xs text-blue-600 hover:bg-blue-50 rounded">修改角色</button>
                      </div>
                    </td>
                  </tr>
                `).join('')}
              </tbody>
            </table>
          </div>`;
      } catch (e) {
        container.innerHTML = `<div class="p-8 text-center text-red-500">加载失败: ${e.message}</div>`;
      }
    },

    showChangeRoleModal(username, currentRole) {
      ModalDialog.show({
        title: `修改成员角色: ${username}`,
        content: `
          <div class="space-y-4">
            <div>
              <label class="block text-sm font-medium mb-1">新角色 <span class="text-red-500">*</span></label>
              <select id="new-role" class="w-full border rounded px-3 py-2">
                <option value="reader" ${currentRole === 'reader' ? 'selected' : ''}>reader - 读者</option>
                <option value="writer" ${currentRole === 'writer' ? 'selected' : ''}>writer - 作者</option>
                <option value="admin" ${currentRole === 'admin' ? 'selected' : ''}>admin - 管理员</option>
              </select>
            </div>
          </div>`,
        onConfirm: async () => {
          const newRole = document.getElementById('new-role').value;
          if (!newRole) { alert('请选择角色'); return; }
          try {
            // Note: This may not be supported by backend yet
            await window.ApiClient.callTool('project.add_member', { workspace: this.currentWorkspace, username, role: newRole });
            ModalDialog.close();
            await MemberManagePage.loadMembers();
          } catch (e) { alert('修改失败: ' + e.message); }
        }
      });
    },

    loadData() {
      this.loadMembers();
    }
  };
})();
