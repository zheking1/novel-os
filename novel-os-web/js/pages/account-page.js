/**
 * Account Page
 * Shows current user account info
 */
(function() {
  window.AccountPage = {
    async init() {
      const contentArea = document.getElementById('content-area');
      contentArea.innerHTML = `
        <div class="flex items-center justify-between mb-6">
          <h1 class="text-2xl font-bold text-gray-800">${window.t('nav.account') || '账户信息'}</h1>
        </div>
        <div class="bg-white rounded-lg shadow p-6 max-w-lg">
          <div class="flex items-center gap-4 mb-6">
            <div class="w-16 h-16 bg-primary-100 rounded-full flex items-center justify-center">
              <span class="text-2xl font-bold text-primary-600">${(window.AppState.username || 'U')[0].toUpperCase()}</span>
            </div>
            <div>
              <div class="text-xl font-bold text-gray-800">${window.AppState.username || '未登录'}</div>
              <div class="text-gray-500">${window.AppState.isAdmin ? '管理员' : '用户'}</div>
            </div>
          </div>
          <div class="space-y-4">
            <div class="p-4 bg-gray-50 rounded-lg">
              <div class="text-sm text-gray-500">用户名</div>
              <div class="font-medium text-gray-800">${window.AppState.username || '-'}</div>
            </div>
            <div class="p-4 bg-gray-50 rounded-lg">
              <div class="text-sm text-gray-500">当前工作空间</div>
              <div class="font-medium text-gray-800">${window.AppState.currentWorkspace || '未选择'}</div>
            </div>
            <div class="p-4 bg-gray-50 rounded-lg">
              <div class="text-sm text-gray-500">当前项目</div>
              <div class="font-medium text-gray-800">${window.AppState.currentProject || '未选择'}</div>
            </div>
          </div>
          <button onclick="AccountPage.logout()" class="mt-6 w-full px-4 py-2 bg-red-600 text-white rounded-lg hover:bg-red-700">退出登录</button>
        </div>
      `;
      return true;
    },

    logout() {
      if (!confirm('确定退出登录？')) return;
      document.cookie = 'session=; expires=Thu, 01 Jan 1970 00:00:00 UTC; path=/;';
      window.AppState.username = null;
      window.location.reload();
    }
  };
})();
