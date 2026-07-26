/**
 * System Notifications Page - 站内通知中心
 * 
 * 显示系统消息和进化提案通知
 */
(function() {
  'use strict';
  console.log('[SystemNotificationsPage] Script loading...');

  // ==================== 页面配置 ====================
  const PAGE_CONFIG = {
    pageId: 'system-notifications',
    pageName: '通知中心',
    apiNamespace: 'systemNotification',
    requiredProject: false,
    emptyIcon: '🔔',
    emptyText: '暂无通知',
    emptyHint: '系统消息和进化提案通知将显示在这里'
  };

  const PAGE_ID = PAGE_CONFIG.pageId;

  // ==================== 页面逻辑 ====================
  window.SystemNotificationsPage = {
    notifications: [],
    unreadCount: 0,

    init() {
      console.log('[SystemNotificationsPage] init() called');
      this.render();
      this.loadData();
      return true;
    },

    render() {
      console.log('[SystemNotificationsPage] render() called');
      const contentArea = document.getElementById('content-area');
      if (!contentArea) {
        console.error('[SystemNotificationsPage] content-area not found!');
        return;
      }
      
      contentArea.innerHTML = `
        <div class="max-w-4xl mx-auto space-y-4">
          <!-- 页面标题 -->
          <div class="flex items-center justify-between">
            <div>
              <h1 class="text-2xl font-bold text-gray-800">${PAGE_CONFIG.pageName}</h1>
              <p class="text-gray-500 mt-1">系统消息和进化提案通知</p>
            </div>
            <button onclick="SystemNotificationsPage.markAllRead()" 
                    class="px-4 py-2 text-primary-600 hover:text-primary-800 transition-colors">
              全部标记为已读
            </button>
          </div>

          <!-- 筛选标签 -->
          <div class="flex gap-2 border-b border-gray-200">
            <button onclick="SystemNotificationsPage.filterByType('')" 
                    class="px-4 py-2 text-sm font-medium text-primary-600 border-b-2 border-primary-600" 
                    id="${PAGE_ID}-tab-all">
              全部
            </button>
            <button onclick="SystemNotificationsPage.filterByType('unread')" 
                    class="px-4 py-2 text-sm font-medium text-gray-500 hover:text-gray-700" 
                    id="${PAGE_ID}-tab-unread">
              未读
            </button>
            <button onclick="SystemNotificationsPage.filterByType('proposal')" 
                    class="px-4 py-2 text-sm font-medium text-gray-500 hover:text-gray-700" 
                    id="${PAGE_ID}-tab-proposal">
              提案
            </button>
            <button onclick="SystemNotificationsPage.filterByType('system')" 
                    class="px-4 py-2 text-sm font-medium text-gray-500 hover:text-gray-700" 
                    id="${PAGE_ID}-tab-system">
              系统
            </button>
          </div>

          <!-- 通知列表 -->
          <div id="${PAGE_ID}-container" class="space-y-3">
            <div class="p-8 text-center text-gray-500">
              <div class="spinner w-8 h-8 border-4 border-primary-600 border-t-transparent rounded-full animate-spin mx-auto"></div>
              <p class="mt-2">加载中...</p>
            </div>
          </div>
        </div>
      `;
    },

    async loadData() {
      console.log('[SystemNotificationsPage] loadData() called');
      const container = document.getElementById(`${PAGE_ID}-container`);
      if (!container) return;
      
      try {
        const workspace = window.AppState?.currentWorkspace;
        if (!workspace) {
          container.innerHTML = `<div class="p-8 text-center text-gray-500">请先选择工作区</div>`;
          return;
        }

        const result = await window.ApiClient.callTool('system.notification.list', { 
          workspace, 
          limit: 50 
        });

        console.log('[SystemNotificationsPage] API result:', result);

        if (result?.notifications) {
          this.notifications = result.notifications;
        } else if (Array.isArray(result)) {
          this.notifications = result;
        } else {
          this.notifications = [];
        }

        this.unreadCount = result?.unread_count || 0;
        this.renderList();
      } catch (error) {
        console.error(`[${PAGE_ID}] Load error:`, error);
        container.innerHTML = `<div class="p-8 text-center text-red-500">加载失败: ${error.message}</div>`;
      }
    },

    renderList() {
      const container = document.getElementById(`${PAGE_ID}-container`);
      if (!container) return;
      
      const data = this.notifications;
      if (!data || data.length === 0) {
        container.innerHTML = `
          <div class="p-8 text-center text-gray-500 bg-white rounded-lg shadow">
            <div class="text-4xl mb-2">${PAGE_CONFIG.emptyIcon}</div>
            <p>${PAGE_CONFIG.emptyText}</p>
            <p class="text-sm mt-2">${PAGE_CONFIG.emptyHint}</p>
          </div>
        `;
        return;
      }

      container.innerHTML = `
        <div class="space-y-3">
          ${data.map(n => `
            <div class="bg-white rounded-lg shadow p-4 ${n.is_read ? 'opacity-75' : 'border-l-4 border-primary-500'}" data-id="${n.id}">
              <div class="flex items-start justify-between">
                <div class="flex-1 min-w-0">
                  <div class="flex items-center gap-2">
                    <span class="text-xl">${this.getTypeIcon(n.notification_type)}</span>
                    <h3 class="font-medium text-gray-800">${n.title || '无标题'}</h3>
                    ${!n.is_read ? '<span class="px-2 py-0.5 text-xs rounded-full bg-red-100 text-red-600">未读</span>' : ''}
                  </div>
                  <p class="text-sm text-gray-600 mt-1">${n.content || ''}</p>
                  <div class="flex items-center gap-4 mt-2 text-xs text-gray-400">
                    <span>${n.created_at ? new Date(n.created_at).toLocaleString() : '-'}</span>
                    ${n.proposal_id ? `<span>相关提案: ${n.proposal_id}</span>` : ''}
                  </div>
                </div>
                <div class="flex items-center gap-2 ml-4">
                  ${!n.is_read ? `
                    <button onclick="SystemNotificationsPage.markRead('${n.id}')"
                            class="p-2 text-gray-400 hover:text-primary-600 hover:bg-primary-50 rounded transition-colors" title="标记为已读">
                      <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M5 13l4 4L19 7"/>
                      </svg>
                    </button>
                  ` : ''}
                  <button onclick="SystemNotificationsPage.delete('${n.id}')"
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

    getTypeIcon(type) {
      const icons = {
        proposal_created: '📝',
        proposal_approved: '✅',
        proposal_rejected: '❌',
        proposal_applied: '🚀',
        system_update: '🔧',
        system_alert: '⚠️',
        welcome: '👋'
      };
      return icons[type] || '📌';
    },

    filterByType(type) {
      // 更新标签样式
      ['all', 'unread', 'proposal', 'system'].forEach(t => {
        const tab = document.getElementById(`${PAGE_ID}-tab-${t}`);
        if (tab) {
          if ((type === '' && t === 'all') || t === type) {
            tab.className = 'px-4 py-2 text-sm font-medium text-primary-600 border-b-2 border-primary-600';
          } else {
            tab.className = 'px-4 py-2 text-sm font-medium text-gray-500 hover:text-gray-700';
          }
        }
      });

      // 过滤数据
      let filtered = this.notifications;
      if (type === 'unread') {
        filtered = this.notifications.filter(n => !n.is_read);
      } else if (type === 'proposal') {
        filtered = this.notifications.filter(n => 
          ['proposal_created', 'proposal_approved', 'proposal_rejected', 'proposal_applied'].includes(n.notification_type)
        );
      } else if (type === 'system') {
        filtered = this.notifications.filter(n => 
          ['system_update', 'system_alert', 'welcome'].includes(n.notification_type)
        );
      }
      
      // 临时替换数据并渲染
      const originalData = this.notifications;
      this.notifications = filtered;
      this.renderList();
      this.notifications = originalData;
    },

    async markRead(id) {
      try {
        const workspace = window.AppState?.currentWorkspace;
        await window.ApiClient.callTool('system.notification.mark_read', { 
          workspace, 
          notification_id: id 
        });
        this.loadData();
      } catch (error) {
        console.error('标记已读失败:', error);
      }
    },

    async markAllRead() {
      try {
        const workspace = window.AppState?.currentWorkspace;
        await window.ApiClient.callTool('system.notification.mark_all_read', { 
          workspace 
        });
        this.loadData();
        ModalDialog.alert('全部标记为已读', 'success');
      } catch (error) {
        ModalDialog.alert('操作失败: ' + error.message, 'error');
      }
    },

    async delete(id) {
      ModalDialog.confirm('确定删除这条通知吗？', async () => {
        try {
          const workspace = window.AppState?.currentWorkspace;
          await window.ApiClient.callTool('system.notification.delete', { 
            workspace, 
            notification_id: id 
          });
          this.loadData();
        } catch (error) {
          ModalDialog.alert('删除失败: ' + error.message, 'error');
        }
      });
    }
  };

  console.log('[SystemNotificationsPage] Script loaded, window.SystemNotificationsPage:', !!window.SystemNotificationsPage);
})();
