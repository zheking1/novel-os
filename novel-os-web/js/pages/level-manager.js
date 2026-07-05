/**
 * Novel OS - Level Manager Page
 * 等级管理页面（物品/人物/技能/科技等级通用）
 * @version 1.0.0
 */

(function() {
  'use strict';

  if (window.LevelManager) {
    return;
  }

  /**
   * 等级管理器
   */
  const LevelManager = {
    // 当前配置
    config: null,

    // 数据
    items: [],
    category: null,

    /**
     * 初始化等级管理页面
     * @param {Object} config - 配置
     */
    async init(config) {
      console.log('[LevelManager] Initializing with config:', config);
      
      this.config = {
        type: config.type, // item, character, skill, tech
        title: config.title,
        description: config.description,
        containerId: config.containerId || 'content-area'
      };

      // 显示加载状态
      this.showLoading();

      try {
        // 获取工作区
        const workspace = window.AppState?.currentWorkspace;
        if (!workspace) {
          this.showError(t('workspace.select') + '...');
          return;
        }

        // 获取分类
        await this.loadCategory(workspace);

        // 加载数据
        await this.loadItems(workspace);

        // 渲染页面
        this.render();
      } catch (error) {
        console.error('[LevelManager] Initialization failed:', error);
        this.showError(error.message);
      }
    },

    /**
     * 加载分类信息
     */
    async loadCategory(workspace) {
      try {
        const result = await window.ApiClient.setting.get(workspace, this.config.type);
        this.category = result;
        console.log('[LevelManager] Category loaded:', this.category);
      } catch (error) {
        console.error('[LevelManager] Failed to load category:', error);
        throw new Error(t('error.loadFailed') + ': ' + error.message);
      }
    },

    /**
     * 加载等级数据
     */
    async loadItems(workspace) {
      try {
        if (!this.category?.id) {
          this.items = [];
          return;
        }

        const result = await window.ApiClient.item.list(workspace, this.category.id);
        this.items = result || [];
        
        // 按order排序
        this.items.sort((a, b) => (a.data?.order || 0) - (b.data?.order || 0));
        
        console.log('[LevelManager] Items loaded:', this.items.length);
      } catch (error) {
        console.error('[LevelManager] Failed to load items:', error);
        throw new Error(t('error.loadFailed') + ': ' + error.message);
      }
    },

    /**
     * 渲染页面
     */
    render() {
      const container = document.getElementById(this.config.containerId);
      if (!container) return;

      const html = `
        <div class="space-y-6">
          <!-- 页面头部 -->
          <div class="flex items-center justify-between">
            <div>
              <h1 class="text-2xl font-bold text-gray-900">${this.config.title}</h1>
              <p class="mt-1 text-sm text-gray-500">${this.config.description}</p>
            </div>
            <button onclick="LevelManager.showAddModal()"
                    class="px-4 py-2 bg-primary-600 text-white rounded-lg hover:bg-primary-700 flex items-center gap-2">
              <span>+</span>
              <span>${t('level.new')}</span>
            </button>
          </div>

          <!-- 数据表格 -->
          <div class="bg-white shadow rounded-lg overflow-hidden">
            <div id="level-table"></div>
          </div>
        </div>
      `;

      container.innerHTML = html;

      // 渲染表格
      this.renderTable();
    },

    /**
     * 渲染数据表格
     */
    renderTable() {
      window.DataTable.render({
        containerId: 'level-table',
        columns: [
          { key: 'data.order', header: t('level.order'), type: 'order', width: '80px' },
          { key: 'name', header: t('level.name') },
          { key: 'description', header: t('level.desc'), type: 'truncate' },
          { key: 'data.range', header: t('level.range'), render: (val) => val || '-' }
        ],
        data: this.items,
        actions: [
          {
            label: t('common.edit'),
            icon: '✏️',
            class: 'bg-blue-100 text-blue-700 hover:bg-blue-200',
            onClick: (id) => this.showEditModal(id)
          },
          {
            label: t('common.delete'),
            icon: '🗑️',
            class: 'bg-red-100 text-red-700 hover:bg-red-200',
            onClick: (id) => this.handleDelete(id)
          }
        ],
        emptyMessage: t('level.empty')
      });
    },

    /**
     * 显示添加模态框
     */
    showAddModal() {
      const formHtml = this.getFormHtml();

      window.ModalDialog.show({
        title: t('level.new'),
        content: formHtml,
        size: 'md',
        confirmText: t('level.save'),
        onConfirm: async (modalId) => {
          await this.handleSave(modalId);
        }
      });
    },

    /**
     * 显示编辑模态框
     * @param {string} itemId - 项目ID
     */
    showEditModal(itemId) {
      const item = this.items.find(i => i.id === itemId);
      if (!item) return;

      const formHtml = this.getFormHtml(item);

      window.ModalDialog.show({
        title: t('level.edit'),
        content: formHtml,
        size: 'md',
        confirmText: t('level.save'),
        onConfirm: async (modalId) => {
          await this.handleSave(modalId, itemId);
        }
      });
    },

    /**
     * 获取表单HTML
     */
    getFormHtml(item = null) {
      return `
        <form id="level-form" class="space-y-4">
          <div>
            <label class="block text-sm font-medium text-gray-700 mb-1">${t('level.name')} *</label>
            <input type="text" id="form-name" value="${item?.name || ''}"
                   class="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary-500 focus:border-primary-500"
                   required>
          </div>
          
          <div>
            <label class="block text-sm font-medium text-gray-700 mb-1">${t('level.desc')}</label>
            <textarea id="form-description" rows="3"
                      class="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary-500 focus:border-primary-500">${item?.description || ''}</textarea>
          </div>
          
          <div class="grid grid-cols-2 gap-4">
            <div>
              <label class="block text-sm font-medium text-gray-700 mb-1">${t('level.order')}</label>
              <input type="number" id="form-order" value="${item?.data?.order || 0}"
                     class="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary-500 focus:border-primary-500">
            </div>
            
            <div>
              <label class="block text-sm font-medium text-gray-700 mb-1">${t('level.range')}</label>
              <input type="text" id="form-range" value="${item?.data?.range || ''}"
                     placeholder="如: 1-10, 1-100"
                     class="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary-500 focus:border-primary-500">
            </div>
          </div>
        </form>
      `;
    },

    /**
     * 处理保存
     */
    async handleSave(modalId, itemId = null) {
      const name = document.getElementById('form-name')?.value?.trim();
      const description = document.getElementById('form-description')?.value?.trim();
      const order = parseInt(document.getElementById('form-order')?.value) || 0;
      const range = document.getElementById('form-range')?.value?.trim();

      // 验证
      if (!name) {
        window.ModalDialog.alert(t('validation.required'), 'warning');
        return;
      }

      try {
        const workspace = window.AppState?.currentWorkspace;
        
        const data = {
          name,
          description,
          category_id: this.category.id,
          data: {
            order,
            range: range || null
          }
        };

        if (itemId) {
          data.item_id = itemId;
        }

        await window.ApiClient.item.upsert(workspace, data);

        // 关闭模态框
        window.ModalDialog.close();

        // 重新加载数据
        await this.loadItems(workspace);
        this.renderTable();

        // 显示成功提示
        window.AppCore.toast(t('common.success'), 'success');
      } catch (error) {
        console.error('[LevelManager] Save failed:', error);
        window.ModalDialog.alert(t('common.error') + ': ' + error.message, 'error');
      }
    },

    /**
     * 处理删除
     */
    async handleDelete(itemId) {
      const item = this.items.find(i => i.id === itemId);
      if (!item) return;

      window.ModalDialog.confirm(
        t('level.confirmDelete'),
        async () => {
          try {
            const workspace = window.AppState?.currentWorkspace;
            await window.ApiClient.item.delete(workspace, itemId);

            // 重新加载数据
            await this.loadItems(workspace);
            this.renderTable();

            window.AppCore.toast(t('common.success'), 'success');
          } catch (error) {
            console.error('[LevelManager] Delete failed:', error);
            window.ModalDialog.alert(t('common.error') + ': ' + error.message, 'error');
          }
        }
      );
    },

    /**
     * 显示加载状态
     */
    showLoading() {
      const container = document.getElementById(this.config.containerId);
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
      const container = document.getElementById(this.config.containerId);
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

  window.LevelManager = LevelManager;

})();
