/**
 * Novel OS - Data Table Component
 * 通用数据表格组件，支持排序、分页、操作按钮
 * @version 1.0.0
 */

(function() {
  'use strict';

  if (window.DataTable) {
    return;
  }

  /**
   * 数据表格组件
   */
  const DataTable = {
    /**
     * 渲染表格
     * @param {Object} config - 表格配置
     */
    render(config) {
      const {
        containerId,
        columns = [],
        data = [],
        actions = [],
        emptyMessage = '暂无数据',
        onRowClick = null
      } = config;

      const container = document.getElementById(containerId);
      if (!container) {
        console.error('[DataTable] Container not found:', containerId);
        return;
      }

      if (!data || data.length === 0) {
        container.innerHTML = `
          <div class="text-center py-12 text-gray-500">
            <div class="text-4xl mb-4">📭</div>
            <p>${emptyMessage}</p>
          </div>
        `;
        return;
      }

      const tableHtml = `
        <div class="overflow-x-auto">
          <table class="min-w-full divide-y divide-gray-200">
            <thead class="bg-gray-50">
              <tr>
                ${columns.map(col => `
                  <th class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider"
                      ${col.width ? `style="width: ${col.width}"` : ''}>
                    ${col.header}
                  </th>
                `).join('')}
                ${actions.length > 0 ? `
                  <th class="px-6 py-3 text-right text-xs font-medium text-gray-500 uppercase tracking-wider" style="width: 150px">
                    ${t('common.actions')}
                  </th>
                ` : ''}
              </tr>
            </thead>
            <tbody class="bg-white divide-y divide-gray-200">
              ${data.map((row, index) => `
                <tr class="hover:bg-gray-50 ${onRowClick ? 'cursor-pointer' : ''}"
                    ${onRowClick ? `onclick="${onRowClick}('${row.id || index}')" data-id="${row.id || index}"` : ''}>
                  ${columns.map(col => `
                    <td class="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                      ${this.renderCell(row, col)}
                    </td>
                  `).join('')}
                  ${actions.length > 0 ? `
                    <td class="px-6 py-4 whitespace-nowrap text-right text-sm font-medium">
                      <div class="flex justify-end gap-2">
                        ${actions.map(action => `
                          <button onclick="${action.onClick}('${row.id || row.slug || index}')"
                                  class="px-3 py-1 text-xs rounded ${action.class || 'bg-gray-100 text-gray-700 hover:bg-gray-200'}"
                                  title="${action.title || ''}">
                            ${action.icon ? `<span>${action.icon}</span>` : action.label}
                          </button>
                        `).join('')}
                      </div>
                    </td>
                  ` : ''}
                </tr>
              `).join('')}
            </tbody>
          </table>
        </div>
      `;

      container.innerHTML = tableHtml;
    },

    /**
     * 渲染单元格
     */
    renderCell(row, column) {
      const value = this.getNestedValue(row, column.key);
      
      if (column.render) {
        return column.render(value, row);
      }

      if (column.type === 'badge') {
        return `<span class="px-2 inline-flex text-xs leading-5 font-semibold rounded-full ${column.badgeClass || 'bg-gray-100 text-gray-800'}">${value || '-'}</span>`;
      }

      if (column.type === 'order') {
        return `<span class="font-mono text-gray-500">${value || 0}</span>`;
      }

      if (column.type === 'tags' && Array.isArray(value)) {
        return value.map(tag => `<span class="px-2 py-0.5 bg-blue-100 text-blue-800 text-xs rounded mr-1">${tag}</span>`).join('');
      }

      if (column.type === 'truncate') {
        const text = String(value || '');
        return `<span title="${text}">${text.length > 50 ? text.substring(0, 50) + '...' : text}</span>`;
      }

      return value || '-';
    },

    /**
     * 获取嵌套对象的值
     */
    getNestedValue(obj, path) {
      return path.split('.').reduce((current, key) => current?.[key], obj);
    }
  };

  window.DataTable = DataTable;

})();
