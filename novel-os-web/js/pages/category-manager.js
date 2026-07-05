/**
 * Novel OS - Category Manager Page
 * 分类管理页面
 * @version 1.0.0
 */

(function() {
  'use strict';

  if (window.CategoryManager) {
    return;
  }

  const CategoryManager = {
    // 数据
    categories: [],

    /**
     * 初始化
     */
    async init() {
      console.log('[CategoryManager] Initializing...');
      
      this.showLoading();

      try {
        await this.loadCategories();
        this.render();
      } catch (error) {
        console.error('[CategoryManager] Initialization failed:', error);
        this.showError(error.message);
      }
      return true;
    },

    /**
     * 加载分类数据
     */
    async loadCategories() {
      try {
        const workspace = window.AppState?.currentWorkspace;
        if (!workspace) {
          throw new Error(t('workspace.select'));
        }

        const result = await window.ApiClient.setting.list(workspace);
        this.categories = result || [];
        console.log('[CategoryManager] Categories loaded:', this.categories.length);
      } catch (error) {
        console.error('[CategoryManager] Failed to load categories:', error);
        throw new Error(t('error.loadFailed') + ': ' + error.message);
      }
    },

    /**
     * 渲染页面
     */
    render() {
      const container = document.getElementById('content-area');
      if (!container) return;

      const html = `
        <div class="space-y-6">
          <!-- 页面头部 -->
          <div class="flex items-center justify-between">
            <div>
              <h1 class="text-2xl font-bold text-gray-900">${t('category.title')}</h1>
              <p class="mt-1 text-sm text-gray-500">${t('category.description')}</p>
            </div>
            <button onclick="CategoryManager.showAddModal()"
                    class="px-4 py-2 bg-primary-600 text-white rounded-lg hover:bg-primary-700 flex items-center gap-2">
              <span>+</span>
              <span>${t('category.new')}</span>
            </button>
          </div>

          <!-- 数据表格 -->
          <div class="bg-white shadow rounded-lg overflow-hidden">
            <div id="category-table"></div>
          </div>
        </div>
      `;

      container.innerHTML = html;
      this.renderTable();
    },

    /**
     * 渲染表格
     */
    renderTable() {
      window.DataTable.render({
        containerId: 'category-table',
        columns: [
          { key: 'name', header: t('category.name') },
          { key: 'slug', header: t('category.slug'), render: (val) => `<code class="px-2 py-0.5 bg-gray-100 text-gray-800 text-xs rounded">${val}</code>` },
          { key: 'description', header: t('category.desc'), type: 'truncate' },
          { key: 'is_system', header: t('category.isStandard'), type: 'badge', 
            badgeClass: (val) => val ? 'bg-blue-100 text-blue-800' : 'bg-gray-100 text-gray-800',
            render: (val) => val ? '✓' : '-' }
        ],
        data: this.categories,
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
        emptyMessage: t('category.empty')
      });
    },

    /**
     * 显示添加模态框
     */
    showAddModal() {
      const formHtml = this.getFormHtml();

      window.ModalDialog.show({
        title: t('category.new'),
        content: formHtml,
        size: 'md',
        confirmText: t('common.save'),
        onConfirm: async (modalId) => {
          await this.handleSave(modalId);
        }
      });
    },

    /**
     * 显示编辑模态框
     */
    showEditModal(categoryId) {
      const category = this.categories.find(c => c.id === categoryId);
      if (!category) return;

      const formHtml = this.getFormHtml(category);

      window.ModalDialog.show({
        title: t('category.edit'),
        content: formHtml,
        size: 'md',
        confirmText: t('common.save'),
        onConfirm: async (modalId) => {
          await this.handleSave(modalId, categoryId);
        }
      });
    },

    /**
     * 获取表单HTML
     */
    getFormHtml(category = null) {
      return `
        <form id="category-form" class="space-y-4">
          <div>
            <label class="block text-sm font-medium text-gray-700 mb-1">${t('category.name')} *</label>
            <input type="text" id="form-name" value="${category?.name || ''}"
                   class="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary-500 focus:border-primary-500"
                   required>
          </div>
          
          <div>
            <label class="block text-sm font-medium text-gray-700 mb-1">${t('category.slug')} *</label>
            <input type="text" id="form-slug" value="${category?.slug || ''}"
                   class="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary-500 focus:border-primary-500"
                   ${category ? 'readonly disabled' : ''} required>
            <p class="mt-1 text-xs text-gray-500">唯一标识符，创建后不可修改</p>
          </div>
          
          <div>
            <label class="block text-sm font-medium text-gray-700 mb-1">${t('category.desc')}</label>
            <textarea id="form-description" rows="3"
                      class="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary-500 focus:border-primary-500">${category?.description || ''}</textarea>
          </div>
          
          <div>
            <label class="block text-sm font-medium text-gray-700 mb-1">${t('category.icon')}</label>
            <input type="text" id="form-icon" value="${category?.metadata?.icon || ''}"
                   placeholder="如: 📖"
                   class="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary-500 focus:border-primary-500">
          </div>
          
          <div class="flex items-center">
            <input type="checkbox" id="form-is-system" ${category?.is_system ? 'checked disabled' : ''}
                   class="h-4 w-4 text-primary-600 focus:ring-primary-500 border-gray-300 rounded">
            <label for="form-is-system" class="ml-2 text-sm text-gray-700">${t('category.isStandard')}</label>
          </div>
        </form>
      `;
    },

    /**
     * 处理保存
     */
    async handleSave(modalId, categoryId = null) {
      const name = document.getElementById('form-name')?.value?.trim();
      const slug = document.getElementById('form-slug')?.value?.trim();
      const description = document.getElementById('form-description')?.value?.trim();
      const icon = document.getElementById('form-icon')?.value?.trim();

      // 验证
      if (!name) {
        window.ModalDialog.alert(t('validation.required'), 'warning');
        return;
      }

      if (!slug && !categoryId) {
        window.ModalDialog.alert(t('validation.required'), 'warning');
        return;
      }

      try {
        const workspace = window.AppState?.currentWorkspace;
        
        const data = {
          name,
          slug: categoryId ? undefined : slug,
          description: description || null,
          metadata: icon ? { icon } : null
        };

        if (categoryId) {
          data.category_id = categoryId;
        }

        await window.ApiClient.setting.upsert(workspace, data);

        // 关闭模态框
        window.ModalDialog.close();

        // 重新加载数据
        await this.loadCategories();
        this.renderTable();

        window.AppCore.toast(t('common.success'), 'success');
      } catch (error) {
        console.error('[CategoryManager] Save failed:', error);
        window.ModalDialog.alert(t('common.error') + ': ' + error.message, 'error');
      }
    },

    /**
     * 处理删除
     */
    async handleDelete(categoryId) {
      const category = this.categories.find(c => c.id === categoryId);
      if (!category) return;

      // 系统分类不能删除
      if (category.is_system) {
        window.ModalDialog.alert(t('category.cannotDeleteStandard'), 'warning');
        return;
      }

      window.ModalDialog.confirm(
        t('common.confirmDelete'),
        async () => {
          try {
            const workspace = window.AppState?.currentWorkspace;
            await window.ApiClient.setting.delete(workspace, categoryId);

            await this.loadCategories();
            this.renderTable();

            window.AppCore.toast(t('common.success'), 'success');
          } catch (error) {
            console.error('[CategoryManager] Delete failed:', error);
            window.ModalDialog.alert(t('common.error') + ': ' + error.message, 'error');
          }
        }
      );
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

  window.CategoryManager = CategoryManager;

})();
