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
          <div class="flex items-center gap-3">
            <div class="flex items-center gap-2">
              <span class="text-sm text-gray-500">开放注册</span>
              <button id="reg-toggle" onclick="UsersPage.toggleRegistration()" class="relative inline-flex h-6 w-11 items-center rounded-full transition-colors bg-gray-300">
                <span class="inline-block h-4 w-4 transform rounded-full bg-white transition-transform translate-x-1"></span>
              </button>
            </div>
            <button onclick="UsersPage.showCreateModal()" class="px-4 py-2 bg-primary-600 text-white rounded-lg hover:bg-primary-700 text-sm">+ 创建用户</button>
          </div>
        </div>
        <div id="users-content" class="bg-white rounded-lg shadow">
          <div class="p-8 text-center text-gray-500">加载中...</div>
        </div>
      `;
      await this.loadData();
      // 初始化开关：先调 GET 取状态，失败则默认关
      try {
        var r = await fetch('/api/admin/setting?key=auth.allow_registration', { credentials: 'same-origin' });
        var j = await r.json();
        if (j.ok && j.value === true) {
          var btn = document.getElementById('reg-toggle');
          if (btn) btn.className = 'relative inline-flex h-6 w-11 items-center rounded-full transition-colors bg-green-500';
          var span = btn?.querySelector('span');
          if (span) span.className = 'inline-block h-4 w-4 transform rounded-full bg-white transition-transform translate-x-6';
        }
      } catch(e) { console.log('reg status init failed:', e.message); }
    },

    async loadData() {
      const container = document.getElementById('users-content');
      try {
        const result = await window.ApiClient.callTool('user.list', { status: null }).catch(function(e) {
          console.error('user.list failed:', e);
          return [];
        });
        const users = Array.isArray(result) ? result : [];
        if (users.length === 0) {
          container.innerHTML = '<div class="p-8 text-center text-gray-500">暂无用户</div>';
          return;
        }
        container.innerHTML = `
          <div class="overflow-x-auto">
            <table class="w-full text-sm">
              <thead class="bg-gray-50"><tr>
                <th class="px-4 py-3 text-left font-medium text-gray-600">用户名</th>
                <th class="px-4 py-3 text-left font-medium text-gray-600">显示名</th>
                <th class="px-4 py-3 text-left font-medium text-gray-600">角色</th>
                <th class="px-4 py-3 text-left font-medium text-gray-600">状态</th>
              </tr></thead>
              <tbody class="divide-y divide-gray-100">
                ${users.map(function(u) { var isAdmin = ((window.AppState && window.AppState.adminUsers) || ['admin']).indexOf(u.username) >= 0; return '<tr class="hover:bg-gray-50"><td class="px-4 py-3 font-medium text-gray-800">' + escapeHtml(u.username) + '</td><td class="px-4 py-3 text-gray-600">' + (u.display_name || '-') + '</td><td class="px-4 py-3"><span class="px-2 py-1 text-xs rounded ' + (isAdmin ? 'bg-red-100 text-red-700' : 'bg-blue-100 text-blue-700') + '">' + (isAdmin ? '管理员' : '用户') + '</span></td><td class="px-4 py-3"><span class="px-2 py-1 text-xs rounded ' + (u.status === 'active' ? 'bg-green-100 text-green-700' : 'bg-gray-100 text-gray-500') + '">' + (u.status || 'active') + '</span></td></tr>'; }).join('')}
              </tbody>
            </table>
          </div>`;
      } catch (e) {
        container.innerHTML = '<div class="p-8 text-center text-red-500">加载失败: ' + e.message + '</div>';
      }
    },

    showCreateModal() {
      ModalDialog.show({
        title: '创建用户',
        content: '<div class="space-y-4"><div><label class="block text-sm font-medium mb-1">用户名</label><input id="new-username" class="w-full border rounded px-3 py-2"></div><div><label class="block text-sm font-medium mb-1">显示名</label><input id="new-displayname" class="w-full border rounded px-3 py-2"></div><div><label class="block text-sm font-medium mb-1">密码</label><input id="new-password" type="password" class="w-full border rounded px-3 py-2" value="123456"></div></div>',
        onConfirm: async function() {
          var u = document.getElementById('new-username').value;
          var d = document.getElementById('new-displayname').value;
          var p = document.getElementById('new-password').value;
          if (!u) { alert('用户名不能为空'); return; }
          await window.ApiClient.callTool('user.create', { username: u, display_name: d, password: p });
          await UsersPage.loadData();
        }
      });
    },

    async toggleRegistration() {
      var btn = document.getElementById('reg-toggle');
      if (!btn) return alert('toggle not found');
      var isOn = btn.className.indexOf('bg-green') > -1;
      var val = isOn ? 'false' : 'true';
      try {
        var r = await fetch('/api/admin/setting', { method: 'POST', credentials: 'same-origin', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ key: 'auth.allow_registration', value: val }) });
        var j = await r.json();
        if (j.ok) {
          btn.className = 'relative inline-flex h-6 w-11 items-center rounded-full transition-colors ' + (val === 'true' ? 'bg-green-500' : 'bg-gray-300');
          var span = btn.querySelector('span');
          if (span) span.className = 'inline-block h-4 w-4 transform rounded-full bg-white transition-transform ' + (val === 'true' ? 'translate-x-6' : 'translate-x-1');
        }
        else { alert('失败: ' + (j.error || '未知')); }
      } catch(e) { alert('操作失败: ' + e.message); }
    },

  };
  function escapeHtml(s) { return (s||'').replace(/&/g,'&amp;').replace(/</g,'&lt;').replace(/>/g,'&gt;'); }
})();