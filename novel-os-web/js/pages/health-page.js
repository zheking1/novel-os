/**
 * Novel OS - Health Page
 * 系统健康状态页面
 * @version 1.0.0
 */

(function() {
  'use strict';

  if (window.HealthPage) {
    return;
  }

  const HealthPage = {
    // 健康数据
    healthData: null,

    /**
     * 初始化
     */
    async init() {
      console.log('[HealthPage] Initializing...');
      
      this.showLoading();

      try {
        await this.loadHealth();
        this.render();
      } catch (error) {
        console.error('[HealthPage] Initialization failed:', error);
        this.showError(error.message);
      }
      return true;
    },

    /**
     * 加载健康数据
     */
    async loadHealth() {
      try {
        const result = await window.ApiClient.callTool('admin.health');
        this.healthData = result;
        console.log('[HealthPage] Health data loaded:', this.healthData);
      } catch (error) {
        console.error('[HealthPage] Failed to load health:', error);
        throw new Error(t('error.loadFailed') + ': ' + error.message);
      }
    },

    /**
     * 渲染页面
     */
    render() {
      const container = document.getElementById('content-area');
      if (!container) return;

      const status = this.healthData?.status || 'unknown';
      const statusColor = status === 'ok' ? 'green' : 'red';
      const statusText = status === 'ok' ? '✓ 正常' : '✗ 异常';

      const html = `
        <div class="space-y-6">
          <!-- 页面头部 -->
          <div>
            <h1 class="text-2xl font-bold text-gray-900">${t('system.health.title')}</h1>
            <p class="mt-1 text-sm text-gray-500">${t('system.health.description')}</p>
          </div>

          <!-- 状态卡片 -->
          <div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
            <!-- 系统状态 -->
            <div class="bg-white shadow rounded-lg p-6">
              <div class="flex items-center justify-between">
                <h3 class="text-lg font-medium text-gray-900">系统状态</h3>
                <span class="px-3 py-1 text-sm font-medium rounded-full bg-${statusColor}-100 text-${statusColor}-800">
                  ${statusText}
                </span>
              </div>
              <div class="mt-4 space-y-2">
                <div class="flex justify-between text-sm">
                  <span class="text-gray-500">MCP服务器</span>
                  <span class="font-medium">${this.healthData?.default_mcp_url ? '已配置' : '未配置'}</span>
                </div>
              </div>
            </div>

            <!-- 工作区信息 -->
            <div class="bg-white shadow rounded-lg p-6">
              <h3 class="text-lg font-medium text-gray-900">工作区</h3>
              <div class="mt-4 space-y-2">
                <div class="flex justify-between text-sm">
                  <span class="text-gray-500">当前工作区</span>
                  <span class="font-medium">${window.AppState?.currentWorkspace || '未选择'}</span>
                </div>
              </div>
            </div>

            <!-- 快捷操作 -->
            <div class="bg-white shadow rounded-lg p-6">
              <h3 class="text-lg font-medium text-gray-900">快捷操作</h3>
              <div class="mt-4 space-y-3">
                <button onclick="HealthPage.refresh()" 
                        class="w-full px-4 py-2 bg-primary-600 text-white rounded-lg hover:bg-primary-700">
                  ${t('common.refresh')}
                </button>
                <button onclick="HealthPage.testApi()" 
                        class="w-full px-4 py-2 bg-gray-200 text-gray-700 rounded-lg hover:bg-gray-300">
                  测试API连接
                </button>
              </div>
            </div>
          </div>

          <!-- 详细信息 -->
          <div class="bg-white shadow rounded-lg p-6">
            <h3 class="text-lg font-medium text-gray-900 mb-4">详细信息</h3>
            <pre class="bg-gray-50 p-4 rounded-lg overflow-x-auto text-sm text-gray-800">${JSON.stringify(this.healthData, null, 2)}</pre>
          </div>
        </div>
      `;

      container.innerHTML = html;
    },

    /**
     * 刷新数据
     */
    async refresh() {
      this.showLoading();
      await this.loadHealth();
      this.render();
    },

    /**
     * 测试API连接
     */
    async testApi() {
      try {
        const startTime = Date.now();
        await window.ApiClient.callTool('workspace.list', {});
        const duration = Date.now() - startTime;
        
        window.ModalDialog.alert(`API连接成功！响应时间: ${duration}ms`, 'success');
      } catch (error) {
        window.ModalDialog.alert('API连接失败: ' + error.message, 'error');
      }
    },

    /**
     * 显示加载状态
     */
    showLoading() {
      const container = document.getElementById('content-area');
      if (container) {
        container.innerHTML = `
          <div class="flex items-center justify-center py-12">
            <div class="spinner w-8 h-8 border-4 border-primary-600 border-t-transparent rounded-full animate-spin"></div>
            <span class="ml-3 text-gray-600">${t('common.loading')}</span>
          </div>
        `;
      }
    },

    /**
     * 显示错误
     */
    showError(message) {
      const container = document.getElementById('content-area');
      if (container) {
        container.innerHTML = `
          <div class="bg-red-50 border border-red-200 rounded-lg p-8 text-center">
            <h2 class="text-xl font-bold text-red-600 mb-2">${t('common.error')}</h2>
            <p class="text-red-500">${message}</p>
            <button onclick="location.reload()" class="mt-4 px-4 py-2 bg-red-600 text-white rounded hover:bg-red-700">
              ${t('common.refresh')}
            </button>
          </div>
        `;
      }
    }
  };

  window.HealthPage = HealthPage;

})();
