/**
 * Novel OS - DataTable Component
 * Reusable data table with sorting, pagination, and filtering
 * @version 1.0.0
 */

(function() {
  'use strict';

  document.addEventListener('alpine:init', () => {

    /**
     * DataTable组件
     * @param {Object} config - 配置
     */
    Alpine.data('dataTable', (config = {}) => ({
      // 数据
      items: [],
      filteredItems: [],
      displayItems: [],

      // 配置
      columns: config.columns || [],
      pageSize: config.pageSize || 10,
      pageSizeOptions: config.pageSizeOptions || [10, 20, 50, 100],

      // 状态
      loading: false,
      error: null,
      selectedItems: [],

      // 分页
      pagination: {
        currentPage: 1,
        totalPages: 1,
        totalItems: 0,
        startIndex: 0,
        endIndex: 0
      },

      // 排序
      sorting: {
        field: null,
        direction: 'asc' // 'asc' | 'desc'
      },

      // 过滤
      filters: {
        search: '',
        columnFilters: {}
      },

      // 回调函数
      onLoad: config.onLoad || null,
      onSelect: config.onSelect || null,
      onAction: config.onAction || null,

      /**
       * 初始化
       */
      async init() {
        if (config.autoLoad !== false) {
          await this.load();
        }
      },

      /**
       * 加载数据
       */
      async load() {
        this.loading = true;
        this.error = null;

        try {
          let items;

          if (typeof this.onLoad === 'function') {
            // 使用自定义加载函数
            items = await this.onLoad({
              page: this.pagination.currentPage,
              pageSize: this.pageSize,
              sort: this.sorting,
              filters: this.filters
            });
          } else if (config.items) {
            // 使用静态数据
            items = config.items;
          } else {
            items = [];
          }

          this.items = Array.isArray(items) ? items : [];
          this.applyFilters();
          this.applySorting();
          this.applyPagination();

        } catch (err) {
          this.error = err.message || '加载失败';
          console.error('DataTable load error:', err);
        } finally {
          this.loading = false;
        }
      },

      /**
       * 刷新数据
       */
      async refresh() {
        this.pagination.currentPage = 1;
        await this.load();
      },

      /**
       * 应用过滤器
       */
      applyFilters() {
        let result = [...this.items];

        // 全局搜索
        if (this.filters.search) {
          const searchLower = this.filters.search.toLowerCase();
          result = result.filter(item => {
            return this.columns.some(col => {
              if (!col.searchable !== false) {
                const value = this.getColumnValue(item, col.field);
                return String(value).toLowerCase().includes(searchLower);
              }
              return false;
            });
          });
        }

        // 列过滤器
        Object.entries(this.filters.columnFilters).forEach(([field, filterValue]) => {
          if (filterValue) {
            result = result.filter(item => {
              const value = this.getColumnValue(item, field);
              return String(value).toLowerCase().includes(String(filterValue).toLowerCase());
            });
          }
        });

        this.filteredItems = result;
        this.pagination.totalItems = result.length;
      },

      /**
       * 应用排序
       */
      applySorting() {
        if (!this.sorting.field) {
          this.displayItems = [...this.filteredItems];
          return;
        }

        const { field, direction } = this.sorting;
        const multiplier = direction === 'asc' ? 1 : -1;

        this.filteredItems.sort((a, b) => {
          const valA = this.getColumnValue(a, field);
          const valB = this.getColumnValue(b, field);

          // 处理null/undefined
          if (valA == null && valB == null) return 0;
          if (valA == null) return 1 * multiplier;
          if (valB == null) return -1 * multiplier;

          // 根据类型排序
          if (typeof valA === 'number' && typeof valB === 'number') {
            return (valA - valB) * multiplier;
          }

          return String(valA).localeCompare(String(valB)) * multiplier;
        });
      },

      /**
       * 应用分页
       */
      applyPagination() {
        const totalPages = Math.ceil(this.filteredItems.length / this.pageSize) || 1;
        this.pagination.totalPages = totalPages;

        // 确保当前页在有效范围内
        if (this.pagination.currentPage > totalPages) {
          this.pagination.currentPage = totalPages;
        }
        if (this.pagination.currentPage < 1) {
          this.pagination.currentPage = 1;
        }

        const start = (this.pagination.currentPage - 1) * this.pageSize;
        const end = start + this.pageSize;

        this.displayItems = this.filteredItems.slice(start, end);
        this.pagination.startIndex = this.filteredItems.length > 0 ? start + 1 : 0;
        this.pagination.endIndex = Math.min(end, this.filteredItems.length);
      },

      /**
       * 获取列值
       * @param {Object} item - 数据项
       * @param {string} field - 字段路径（支持点号）
       */
      getColumnValue(item, field) {
        if (!field) return '';

        const keys = field.split('.');
        let value = item;

        for (const key of keys) {
          if (value && typeof value === 'object') {
            value = value[key];
          } else {
            return '';
          }
        }

        return value;
      },

      /**
       * 渲染单元格
       * @param {Object} item - 数据项
       * @param {Object} column - 列配置
       */
      renderCell(item, column) {
        const value = this.getColumnValue(item, column.field);

        // 使用自定义渲染函数
        if (typeof column.render === 'function') {
          return column.render(value, item);
        }

        // 格式化值
        if (typeof column.format === 'function') {
          return column.format(value);
        }

        return value;
      },

      /**
       * 排序
       * @param {string} field - 字段名
       */
      sort(field) {
        if (this.sorting.field === field) {
          // 切换方向
          this.sorting.direction = this.sorting.direction === 'asc' ? 'desc' : 'asc';
        } else {
          // 新字段，默认升序
          this.sorting.field = field;
          this.sorting.direction = 'asc';
        }

        this.applySorting();
        this.applyPagination();
      },

      /**
       * 获取排序图标
       * @param {string} field - 字段名
       */
      getSortIcon(field) {
        if (this.sorting.field !== field) {
          return '⇅';
        }
        return this.sorting.direction === 'asc' ? '↑' : '↓';
      },

      /**
       * 跳转到指定页
       * @param {number} page - 页码
       */
      goToPage(page) {
        if (page < 1 || page > this.pagination.totalPages) return;
        this.pagination.currentPage = page;
        this.applyPagination();
      },

      /**
       * 上一页
       */
      prevPage() {
        this.goToPage(this.pagination.currentPage - 1);
      },

      /**
       * 下一页
       */
      nextPage() {
        this.goToPage(this.pagination.currentPage + 1);
      },

      /**
       * 设置页大小
       * @param {number} size - 页大小
       */
      setPageSize(size) {
        this.pageSize = size;
        this.pagination.currentPage = 1;
        this.applyPagination();
      },

      /**
       * 搜索
       * @param {string} value - 搜索值
       */
      search(value) {
        this.filters.search = value;
        this.pagination.currentPage = 1;
        this.applyFilters();
        this.applySorting();
        this.applyPagination();
      },

      /**
       * 设置列过滤器
       * @param {string} field - 字段名
       * @param {string} value - 过滤值
       */
      setColumnFilter(field, value) {
        this.filters.columnFilters[field] = value;
        this.pagination.currentPage = 1;
        this.applyFilters();
        this.applySorting();
        this.applyPagination();
      },

      /**
       * 选择/取消选择行
       * @param {Object} item - 数据项
       */
      toggleSelect(item) {
        const index = this.selectedItems.indexOf(item);
        if (index > -1) {
          this.selectedItems.splice(index, 1);
        } else {
          this.selectedItems.push(item);
        }

        if (typeof this.onSelect === 'function') {
          this.onSelect(this.selectedItems);
        }
      },

      /**
       * 是否选中
       * @param {Object} item - 数据项
       */
      isSelected(item) {
        return this.selectedItems.includes(item);
      },

      /**
       * 全选/取消全选
       */
      toggleSelectAll() {
        if (this.selectedItems.length === this.displayItems.length) {
          this.selectedItems = [];
        } else {
          this.selectedItems = [...this.displayItems];
        }

        if (typeof this.onSelect === 'function') {
          this.onSelect(this.selectedItems);
        }
      },

      /**
       * 是否全选
       */
      isAllSelected() {
        return this.displayItems.length > 0 && this.selectedItems.length === this.displayItems.length;
      },

      /**
       * 执行操作
       * @param {string} action - 操作名
       * @param {Object} item - 数据项
       */
      doAction(action, item) {
        if (typeof this.onAction === 'function') {
          this.onAction(action, item);
        }
      },

      /**
       * 获取页码列表（用于分页器）
       * @param {number} maxVisible - 最大可见页码数
       */
      getPageNumbers(maxVisible = 5) {
        const pages = [];
        const total = this.pagination.totalPages;
        const current = this.pagination.currentPage;

        if (total <= maxVisible) {
          for (let i = 1; i <= total; i++) {
            pages.push(i);
          }
        } else {
          // 计算显示范围
          let start = Math.max(1, current - Math.floor(maxVisible / 2));
          let end = Math.min(total, start + maxVisible - 1);

          if (end - start < maxVisible - 1) {
            start = Math.max(1, end - maxVisible + 1);
          }

          for (let i = start; i <= end; i++) {
            pages.push(i);
          }
        }

        return pages;
      }
    }));

  });

})();
