/**
 * Users Page
 * User management
 */
(function() {
  window.UsersPage = {
    async init() {
      const contentArea = document.getElementById('content-area');
      contentArea.innerHTML = `
        <div class="flex items-center justify-between mb-6">
          <h1 class="text-2xl font-bold text-gray-800">${window.t('nav.users') || '用户管理'}</h1>
          <button onclick="UsersPage.showCreateModal()" class="px-4 py-2 bg-primary-600 text-white rounded-lg hover:bg-primary-700 text-sm">➕ 创建用户</button>
        </div>
        <div id="users-content" class="bg-white rounded-lg shadow">
          <div class="p-8 text-center text-gray-500">加载中...</div>
        </div>
      `;
      await this.loadData();
    },

    async loadData() {
      const container = document.getElementById('users-content');
      try {
        const users = await window.ApiClient.request('GET', '/users').catch(() => []);
        if (!users || users.length === 0) {
          container.innerHTML = `<div class="p-8 text-center text-gray-500">暂无用户</div>`;
          return;
        }
        container.innerHTML = `
          <div class="overflow-x-auto">
            <table class="w-full text-sm">
              <thead class="bg-gray-50">
                <tr>
                  <th class="px-4 py-3 text-left font-medium text-gray-600">用户名</th>
                  <th class="px-4 py-3 text-left font-medium text-gray-600">显示名</th>
                  <th class="px-4 py-3 text-left font-medium text-gray-600">状态</th>
                  <th class="px-4 py-3 text-left font-medium text-gray-600">操作</th>
                </tr>
              </thead>
              <tbody class="divide-y divide-gray-100">
                ${users.map(u => `
                  <tr class="hover:bg-gray-50">
                    <td class="px-4 py-3 font-medium text-gray-800">${u.username}</td>
                    <td class="px-4 py-3 text-gray-600">${u.display_name || '-'}</td>
                    <td class="px-4 py-3"><span class="px-2 py-1 text-xs rounded ${u.status === 'active' ? 'bg-green-100 text-green-700' : 'bg-gray-100 text-gray-500'}">${u.status || 'active'}</span></td>
                    <td class="px-4 py-3 text-gray-500">${u.username === window.AppState.username ? '当前用户' : ''}</td>
                  </tr>
                `).join('')}
              </tbody>
            </table>
          </div>`;
      } catch (e) {
        container.innerHTML = `<div class="p-8 text-center text-red-500">加载失败: ${e.message}</div>`;
      }
    },

    showCreateModal() {
      window.ModalDialog.show({
        title: '创建用户',
        content: `
          <div class="space-y-4">
            <div><label class="block text-sm font-medium mb-1">用户名</label><input id="new-username" class="w-full border rounded px-3 py-2" /></div>
            <div><label class="block text-sm font-medium mb-1">显示名</label><input id="new-displayname" class="w-full border rounded px-3 py-2" /></div>
            <div><label class="block text-sm font-medium mb-1">密码</label><input id="new-password" type="password" class="w-full border rounded px-3 py-2" value="123456" /></div>
          </div>`,
        onConfirm: async () => {
          const username = document.getElementById('new-username').value;
          const display_name = document.getElementById('new-displayname').value;
          const password = document.getElementById('new-password').value;
          if (!username) { alert('用户名不能为空'); return false; }
          await window.ApiClient.request('POST', '/users', { username, display_name, password });
          await this.loadData();
        }
      });
    }
  };
})();
