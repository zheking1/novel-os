/**
 * Debug Page
 * Shows debug information and system tools
 */
(function() {
  window.DebugPage = {
    async init() {
      const contentArea = document.getElementById('content-area');
      contentArea.innerHTML = `
        <div class="flex items-center justify-between mb-6">
          <h1 class="text-2xl font-bold text-gray-800">${window.t('nav.debug') || '调试工具'}</h1>
        </div>
        <div class="space-y-6">
          <div class="bg-white rounded-lg shadow p-6">
            <h3 class="font-semibold text-gray-700 mb-4">应用状态</h3>
            <pre class="text-sm bg-gray-50 p-4 rounded overflow-auto max-h-64">${JSON.stringify({
              initialized: window.AppState.initialized,
              lang: window.AppState.currentLang,
              workspace: window.AppState.currentWorkspace,
              project: window.AppState.currentProject,
              username: window.AppState.username,
              currentPage: window.MenuManager?.state?.currentPage
            }, null, 2)}</pre>
          </div>
          <div class="bg-white rounded-lg shadow p-6">
            <h3 class="font-semibold text-gray-700 mb-4">已注册页面</h3>
            <div class="grid grid-cols-2 md:grid-cols-4 gap-2 text-sm">
              ${['ProjectManagePage','TemplateListPage','LevelManager','GenreManager','CategoryManager','BindingMatrixManager','HealthPage','CanonListPage','EntitiesListPage','RulesListPage','PlotVolumesPage','PlotThreadsPage','ForeshadowingListPage','ContextPreviewPage','ReviewTasksPage','PipelinePage','ChaptersPage','ModelProfilesPage','KbPkListPage','KbUkListPage','KbCategoriesPage','KnowledgeGraphPage','KnowledgeStatsPage','KnowledgeReviewPage','KnowledgeExpiryPage','SkillManagePage','SyncStatusPage','SyncConflictsPage','AuditLogsPage','OfflineStatusPage','SysCachePage','SysBackupPage','ConnectionPage','AccountPage','UsersPage','DebugPage'].map(p => `
                <div class="p-2 bg-gray-50 rounded flex items-center gap-2">
                  <span class="w-2 h-2 rounded-full ${window[p] ? 'bg-green-500' : 'bg-red-500'}"></span>
                  <span>${p}</span>
                </div>
              `).join('')}
            </div>
          </div>
          <div class="bg-white rounded-lg shadow p-6">
            <h3 class="font-semibold text-gray-700 mb-4">快速操作</h3>
            <div class="flex flex-wrap gap-2">
              <button onclick="DebugPage.testApi()" class="px-4 py-2 bg-primary-100 text-primary-700 rounded hover:bg-primary-200 text-sm">测试 API</button>
              <button onclick="DebugPage.reloadModules()" class="px-4 py-2 bg-gray-100 text-gray-700 rounded hover:bg-gray-200 text-sm">重载模块</button>
              <button onclick="DebugPage.clearCache()" class="px-4 py-2 bg-orange-100 text-orange-700 rounded hover:bg-orange-200 text-sm">清除缓存</button>
              <button onclick="localStorage.clear();location.reload()" class="px-4 py-2 bg-red-100 text-red-700 rounded hover:bg-red-200 text-sm">清除本地存储</button>
            </div>
          </div>
        </div>
      `;
    },

    async testApi() {
      try {
        const result = await window.ApiClient.workspace.list({ showLoading: false });
        alert('API 正常!\n工作空间数量: ' + (result?.length || 0));
      } catch (e) {
        alert('API 错误: ' + e.message);
      }
    },

    reloadModules() {
      window.location.reload();
    },

    clearCache() {
      if ('caches' in window) {
        caches.keys().then(names => names.forEach(name => caches.delete(name)));
      }
      alert('浏览器缓存已清除');
    }
  };
})();
