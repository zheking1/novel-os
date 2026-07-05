/**
 * Novel OS - Binding Matrix Manager Page
 * 类型绑定矩阵管理页面
 * @version 1.0.0
 */

(function() {
  'use strict';

  if (window.BindingMatrixManager) {
    return;
  }

  const BindingMatrixManager = {
    // 数据
    genres: [],
    categories: [],
    bindings: {}, // { "genre_slug||category_id||all": true/false }

    /**
     * 初始化
     */
    async init() {
      console.log('[BindingMatrixManager] Initializing...');
      
      this.showLoading();

      try {
        await this.loadData();
        this.render();
      } catch (error) {
        console.error('[BindingMatrixManager] Initialization failed:', error);
        this.showError(error.message);
      }
    },

    /**
     * 加载数据
     */
    async loadData() {
      try {
        const workspace = window.AppState?.currentWorkspace;
        
        const [genresResult, categoriesResult, matrixResult] = await Promise.all([
          window.ApiClient.genre.list(),
          workspace ? window.ApiClient.setting.list(workspace) : Promise.resolve([]),
          window.ApiClient.callTool('genre.binding.matrix')
        ]);

        this.genres = genresResult || [];
        this.categories = categoriesResult || [];
        
        // 解析矩阵数据
        if (matrixResult?.matrix) {
          this.bindings = matrixResult.matrix;
        }

        console.log('[BindingMatrixManager] Data loaded:', {
          genres: this.genres.length,
          categories: this.categories.length,
          bindings: Object.keys(this.bindings).length
        });
      } catch (error) {
        console.error('[BindingMatrixManager] Failed to load data:', error);
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
              <h1 class="text-2xl font-bold text-gray-900">${t('binding.title')}</h1>
              <p class="mt-1 text-sm text-gray-500">${t('binding.description')}</p>
            </div>
            <button onclick="BindingMatrixManager.saveBindings()"
                    class="px-4 py-2 bg-primary-600 text-white rounded-lg hover:bg-primary-700 flex items-center gap-2">
              <span>💾</span>
              <span>${t('binding.save')}</span>
            </button>
          </div>

          <!-- 矩阵表格 -->
          <div class="bg-white shadow rounded-lg overflow-hidden">
            <div class="px-6 py-4 border-b border-gray-200">
              <h3 class="text-lg font-medium text-gray-900">${t('binding.matrix')}</h3>
              <p class="mt-1 text-sm text-gray-500">勾选表示该分类在此类型中可用</p>
            </div>
            <div class="overflow-x-auto">
              <table id="binding-matrix" class="min-w-full divide-y divide-gray-200">
                <thead class="bg-gray-50">
                  <tr id="matrix-header">
                    <th class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                      ${t('binding.category')}
                    </th>
                  </tr>
                </thead>
                <tbody class="bg-white divide-y divide-gray-200" id="matrix-body">
                </tbody>
              </table>
            </div>
          </div>

          <!-- 图例 -->
          <div class="bg-gray-50 rounded-lg p-4">
            <h4 class="text-sm font-medium text-gray-700 mb-2">说明</h4>
            <ul class="text-sm text-gray-600 space-y-1">
              <li>• <span class="font-medium">勾选</span>: 该分类在此小说类型中可用</li>
              <li>• <span class="font-medium">未勾选</span>: 该分类在此小说类型中不可用</li>
              <li>• 保存后立即生效</li>
            </ul>
          </div>
        </div>
      `;

      container.innerHTML = html;
      this.renderMatrix();
    },

    /**
     * 渲染矩阵表格
     */
    renderMatrix() {
      // 渲染表头
      const headerRow = document.getElementById('matrix-header');
      if (!headerRow) return;

      let headerHtml = `
        <th class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider sticky left-0 bg-gray-50 z-10">
          ${t('binding.category')}
        </th>
      `;

      this.genres.forEach(genre => {
        headerHtml += `
          <th class="px-4 py-3 text-center text-xs font-medium text-gray-500 uppercase tracking-wider" style="min-width: 100px;">
            ${genre.name || genre.slug}
          </th>
        `;
      });

      headerRow.innerHTML = headerHtml;

      // 渲染表体
      const tbody = document.getElementById('matrix-body');
      if (!tbody) return;

      let bodyHtml = '';

      this.categories.forEach(category => {
        bodyHtml += `
          <tr class="hover:bg-gray-50">
            <td class="px-6 py-4 whitespace-nowrap sticky left-0 bg-white z-10 border-r border-gray-200">
              <div class="flex items-center gap-2">
                <span class="text-lg">${category.metadata?.icon || '📂'}</span>
                <div>
                  <div class="font-medium text-gray-900">${category.name}</div>
                  <div class="text-xs text-gray-500">${category.slug}</div>
                </div>
              </div>
            </td>
        `;

        this.genres.forEach(genre => {
          const key = `${genre.slug}||${category.id}||all`;
          const isChecked = this.bindings[key] === true;

          bodyHtml += `
            <td class="px-4 py-4 text-center">
              <input type="checkbox" 
                     data-genre="${genre.slug}" 
                     data-cat="${category.id}"
                     ${isChecked ? 'checked' : ''}
                     onchange="BindingMatrixManager.toggleBinding(this)"
                     class="h-5 w-5 text-primary-600 focus:ring-primary-500 border-gray-300 rounded cursor-pointer">
            </td>
          `;
        });

        bodyHtml += '</tr>';
      });

      tbody.innerHTML = bodyHtml;
    },

    /**
     * 切换绑定状态
     */
    toggleBinding(checkbox) {
      const genre = checkbox.dataset.genre;
      const cat = checkbox.dataset.cat;
      const key = `${genre}||${cat}||all`;
      
      this.bindings[key] = checkbox.checked;
      console.log('[BindingMatrixManager] Toggle binding:', key, checkbox.checked);
    },

    /**
     * 保存绑定
     */
    async saveBindings() {
      try {
        // 收集所有绑定数据
        const bindings = [];
        
        document.querySelectorAll('#binding-matrix input[type="checkbox"]').forEach(checkbox => {
          bindings.push({
            genre: checkbox.dataset.genre,
            category: checkbox.dataset.cat,
            is_required: checkbox.checked
          });
        });

        if (bindings.length === 0) {
          window.ModalDialog.alert('没有可保存的数据', 'warning');
          return;
        }

        // 调用批量更新API
        await window.ApiClient.callTool('genre.binding.bulk_upsert', { bindings });

        window.AppCore.toast(t('common.success'), 'success');
        console.log('[BindingMatrixManager] Bindings saved:', bindings.length);
      } catch (error) {
        console.error('[BindingMatrixManager] Save failed:', error);
        window.ModalDialog.alert(t('common.error') + ': ' + error.message, 'error');
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

  window.BindingMatrixManager = BindingMatrixManager;

})();
