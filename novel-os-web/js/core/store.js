/**
 * Novel OS - Global State Store
 * Alpine.js Global Store for application state management
 * @version 1.0.0
 */

(function() {
  'use strict';

  // 等待Alpine初始化
document.addEventListener('alpine:init', () => {

    /**
     * 全局应用Store
     */
    Alpine.store('app', {
      // ============ 核心状态 ============
      currentPage: 'level-item',
      currentGroup: 'worldbuilding',
      currentLang: 'zh',
      loading: false,
      sidebarCollapsed: false,

      // ============ 工作区/项目 ============
      workspace: 'default',
      project: '',
      workspaces: [],
      projects: [],

      // ============ UI状态 ============
      breadcrumbs: [],
      toasts: [],
      modal: {
        isOpen: false,
        title: '',
        component: null,
        data: null
      },

      // ============ 缓存状态 ============
      categoryCache: new Map(),

      // ============ Actions ============

      /**
       * 设置当前页面
       * @param {string} page - 页面ID
       * @param {string} group - 组ID
       */
      setPage(page, group = null) {
        this.currentPage = page;
        if (group) {
          this.currentGroup = group;
        }
        this.updateBreadcrumbs(page);
      },

      /**
       * 切换语言
       */
      toggleLang() {
        this.currentLang = this.currentLang === 'zh' ? 'en' : 'zh';
        // 触发i18n更新事件
        window.dispatchEvent(new CustomEvent('i18n:changed', {
          detail: { lang: this.currentLang }
        }));
      },

      /**
       * 设置loading状态
       * @param {boolean} value - 状态值
       */
      setLoading(value) {
        this.loading = value;
      },

      /**
       * 切换侧边栏
       */
      toggleSidebar() {
        this.sidebarCollapsed = !this.sidebarCollapsed;
      },

      /**
       * 添加Toast通知
       * @param {string} type - 类型: success, error, warning, info
       * @param {string} title - 标题
       * @param {string} message - 消息
       * @param {number} duration - 持续时间(ms)
       */
      addToast(type, title, message = '', duration = 3000) {
        const toast = {
          id: Date.now(),
          type,
          title,
          message,
          duration
        };
        this.toasts.push(toast);

        // 自动移除
        setTimeout(() => {
          this.removeToast(toast.id);
        }, duration);
      },

      /**
       * 移除Toast
       * @param {number} id - Toast ID
       */
      removeToast(id) {
        const index = this.toasts.findIndex(t => t.id === id);
        if (index > -1) {
          this.toasts.splice(index, 1);
        }
      },

      /**
       * 打开模态框
       * @param {string} title - 标题
       * @param {string} component - 组件名
       * @param {Object} data - 数据
       */
      openModal(title, component = null, data = null) {
        this.modal.title = title;
        this.modal.component = component;
        this.modal.data = data;
        this.modal.isOpen = true;
      },

      /**
       * 关闭模态框
       */
      closeModal() {
        this.modal.isOpen = false;
        setTimeout(() => {
          this.modal.title = '';
          this.modal.component = null;
          this.modal.data = null;
        }, 300);
      },

      /**
       * 更新面包屑
       * @param {string} page - 页面ID
       */
      updateBreadcrumbs(page) {
        const route = window.router?.getRoute?.(page);
        if (route) {
          this.breadcrumbs = [
            { label: 'Home', page: 'dashboard' },
            { label: route.groupLabel, page: null },
            { label: route.title, page: page }
          ];
        }
      },

      /**
       * 设置工作区
       * @param {string} workspace - 工作区slug
       */
      async setWorkspace(workspace) {
        this.workspace = workspace;
        this.categoryCache.clear();

        // 加载项目列表
        try {
          const projects = await window.apiClient.project.list(workspace);
          this.projects = projects || [];
          if (this.projects.length > 0 && !this.project) {
            this.project = this.projects[0].slug;
          }
        } catch (error) {
          console.error('Failed to load projects:', error);
        }

        // 触发工作区变更事件
        window.dispatchEvent(new CustomEvent('workspace:changed', {
          detail: { workspace }
        }));
      },

      /**
       * 设置项目
       * @param {string} project - 项目slug
       */
      setProject(project) {
        this.project = project;
        window.dispatchEvent(new CustomEvent('project:changed', {
          detail: { project }
        }));
      },

      /**
       * 获取分类ID（带缓存）
       * @param {string} slug - 分类slug
       */
      async getCategoryId(slug) {
        if (this.categoryCache.has(slug)) {
          return this.categoryCache.get(slug);
        }

        try {
          const cat = await window.apiClient.setting.get(this.workspace, slug, {
            showLoading: false,
            showError: false
          });
          if (cat?.id || cat?.result?.id) {
            const id = cat.id || cat.result.id;
            this.categoryCache.set(slug, id);
            return id;
          }
        } catch (error) {
          console.warn(`Category not found: ${slug}`);
        }
        return null;
      },

      /**
       * 清除分类缓存
       */
      clearCategoryCache() {
        this.categoryCache.clear();
      }
    });

    /**
     * 用户Store
     */
    Alpine.store('user', {
      username: '',
      isLoggedIn: false,
      permissions: [],

      /**
       * 设置用户信息
       * @param {Object} user - 用户数据
       */
      setUser(user) {
        this.username = user.username || '';
        this.isLoggedIn = true;
        this.permissions = user.permissions || [];
      },

      /**
       * 检查权限
       * @param {string} permission - 权限名称
       */
      hasPermission(permission) {
        return this.permissions.includes(permission) || this.permissions.includes('admin');
      },

      /**
       * 登出
       */
      logout() {
        this.username = '';
        this.isLoggedIn = false;
        this.permissions = [];
      }
    });

  });

})();
