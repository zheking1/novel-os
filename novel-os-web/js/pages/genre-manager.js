/**
 * Novel OS - Genre Manager Page
 * 小说类型管理页面
 * @version 1.0.0
 */

(function() {
  'use strict';

  if (window.GenreManager) {
    return;
  }

  const GenreManager = {
    // 数据
    genres: [],

    /**
     * 初始化
     */
    async init() {
      console.log('[GenreManager] Initializing...');
      
      this.showLoading();

      try {
        await this.loadGenres();
        this.render();
      } catch (error) {
        console.error('[GenreManager] Initialization failed:', error);
        this.showError(error.message);
      }
      return true;
    },

    /**
     * 加载类型数据
     */
    async loadGenres() {
      try {
        const result = await window.ApiClient.genre.list();
        this.genres = result || [];
        console.log('[GenreManager] Genres loaded:', this.genres.length);
      } catch (error) {
        console.error('[GenreManager] Failed to load genres:', error);
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
              <h1 class="text-2xl font-bold text-gray-900">${t('genre.title')}</h1>
              <p class="mt-1 text-sm text-gray-500">${t('genre.description')}</p>
            </div>
            <button onclick="GenreManager.showAddModal()"
                    class="px-4 py-2 bg-primary-600 text-white rounded-lg hover:bg-primary-700 flex items-center gap-2">
              <span>+</span>
              <span>${t('genre.new')}</span>
            </button>
          </div>

          <!-- 数据表格 -->
          <div class="bg-white shadow rounded-lg overflow-hidden">
            <div id="genre-table"></div>
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
        containerId: 'genre-table',
        columns: [
          { key: 'name', header: t('genre.name') },
          { key: 'slug', header: t('genre.slug'), render: (val) => `<code class="px-2 py-0.5 bg-gray-100 text-gray-800 text-xs rounded">${val}</code>` },
          { key: 'description', header: t('genre.desc'), type: 'truncate' },
          { key: 'aliases', header: t('genre.aliases'), type: 'tags' },
          { key: 'typical_elements', header: t('genre.elements'), type: 'tags' }
        ],
        data: this.genres,
        actions: [
          {
            label: t('common.edit'),
            icon: '✏️',
            class: 'bg-blue-100 text-blue-700 hover:bg-blue-200',
            onClick: (slug) => this.showEditModal(slug)
          },
          {
            label: t('common.delete'),
            icon: '🗑️',
            class: 'bg-red-100 text-red-700 hover:bg-red-200',
            onClick: (slug) => this.handleDelete(slug)
          }
        ],
        emptyMessage: t('genre.empty')
      });
    },

    /**
     * 显示添加模态框
     */
    showAddModal() {
      const formHtml = this.getFormHtml();

      window.ModalDialog.show({
        title: t('genre.new'),
        content: formHtml,
        size: 'lg',
        confirmText: t('common.save'),
        onConfirm: async (modalId) => {
          await this.handleSave(modalId);
        }
      });
    },

    /**
     * 显示编辑模态框
     */
    showEditModal(slug) {
      const genre = this.genres.find(g => g.slug === slug);
      if (!genre) return;

      const formHtml = this.getFormHtml(genre);

      window.ModalDialog.show({
        title: t('genre.edit'),
        content: formHtml,
        size: 'lg',
        confirmText: t('common.save'),
        onConfirm: async (modalId) => {
          await this.handleSave(modalId, slug);
        }
      });
    },

    /**
     * 获取表单HTML
     */
    getFormHtml(genre = null) {
      return `
        <form id="genre-form" class="space-y-4">
          <div class="grid grid-cols-2 gap-4">
            <div>
              <label class="block text-sm font-medium text-gray-700 mb-1">${t('genre.name')} *</label>
              <input type="text" id="form-name" value="${genre?.name || ''}"
                     class="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary-500 focus:border-primary-500"
                     required>
            </div>
            
            <div>
              <label class="block text-sm font-medium text-gray-700 mb-1">${t('genre.slug')} *</label>
              <input type="text" id="form-slug" value="${genre?.slug || ''}"
                     class="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary-500 focus:border-primary-500"
                     ${genre ? 'readonly disabled' : ''} required>
              <p class="mt-1 text-xs text-gray-500">唯一标识符，创建后不可修改</p>
            </div>
          </div>
          
          <div>
            <label class="block text-sm font-medium text-gray-700 mb-1">${t('genre.desc')}</label>
            <textarea id="form-description" rows="3"
                      class="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary-500 focus:border-primary-500">${genre?.description || ''}</textarea>
          </div>
          
          <div>
            <label class="block text-sm font-medium text-gray-700 mb-1">${t('genre.aliases')}</label>
            <input type="text" id="form-aliases" value="${(genre?.aliases || []).join(', ')}"
                   placeholder="用逗号分隔"
                   class="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary-500 focus:border-primary-500">
          </div>
          
          <div>
            <label class="block text-sm font-medium text-gray-700 mb-1">${t('genre.elements')}</label>
            <textarea id="form-elements" rows="3"
                      placeholder="每行一个典型元素"
                      class="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary-500 focus:border-primary-500">${(genre?.typical_elements || []).join('\n')}</textarea>
          </div>
        </form>
      `;
    },

    /**
     * 处理保存
     */
    async handleSave(modalId, editSlug = null) {
      const name = document.getElementById('form-name')?.value?.trim();
      const slug = document.getElementById('form-slug')?.value?.trim();
      const description = document.getElementById('form-description')?.value?.trim();
      const aliasesStr = document.getElementById('form-aliases')?.value?.trim();
      const elementsStr = document.getElementById('form-elements')?.value?.trim();

      // 验证
      if (!name) {
        window.ModalDialog.alert(t('validation.required'), 'warning');
        return;
      }

      if (!slug && !editSlug) {
        window.ModalDialog.alert(t('validation.required'), 'warning');
        return;
      }

      try {
        const data = {
          name,
          slug: editSlug || slug,
          description: description || null,
          aliases: aliasesStr ? aliasesStr.split(',').map(s => s.trim()).filter(Boolean) : [],
          typical_elements: elementsStr ? elementsStr.split('\n').map(s => s.trim()).filter(Boolean) : []
        };

        await window.ApiClient.genre.upsert(data);

        // 关闭模态框
        window.ModalDialog.close();

        // 重新加载数据
        await this.loadGenres();
        this.renderTable();

        window.AppCore.toast(t('common.success'), 'success');
      } catch (error) {
        console.error('[GenreManager] Save failed:', error);
        window.ModalDialog.alert(t('common.error') + ': ' + error.message, 'error');
      }
    },

    /**
     * 处理删除
     */
    async handleDelete(slug) {
      const genre = this.genres.find(g => g.slug === slug);
      if (!genre) return;

      window.ModalDialog.confirm(
        t('common.confirmDelete'),
        async () => {
          try {
            await window.ApiClient.genre.delete(slug);

            await this.loadGenres();
            this.renderTable();

            window.AppCore.toast(t('common.success'), 'success');
          } catch (error) {
            console.error('[GenreManager] Delete failed:', error);
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

  window.GenreManager = GenreManager;

})();
