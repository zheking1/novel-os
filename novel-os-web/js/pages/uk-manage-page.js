/**
 * UK Manage Page
 * 通用知识管理页面 - 管理通用知识库(Universal Knowledge)条目
 * 
 * 开发任务 1.1: 页面基础框架
 * - 基础布局和路由
 * - 三栏布局：左侧分类树、中间条目列表、右侧详情/编辑
 */
(function() {
  'use strict';

  window.UkManagePage = {
    // 页面状态
    state: {
      categories: [],
      entries: [],
      selectedCategory: null,
      selectedEntry: null,
      currentPage: 1,
      pageSize: 20,
      totalEntries: 0,
      loading: false,
      searchQuery: '',
      expandedCategoryIds: new Set(),  // 存储展开的分类 ID
      filters: {
        genre: '',
        era: '',
        reliability: null,
        status: ''
      }
    },

    /**
     * 初始化页面
     * @returns {boolean} 初始化成功返回true
     */
    async init() {
      console.log('[UKManage] Initializing page...');
      this.render();
      
      // 加载初始数据
      await Promise.all([
        this.loadCategories(),
        this.loadEntries()
      ]);
      
      return true;
    },

    /**
     * 渲染页面基础布局
     */
    render() {
      const contentArea = document.getElementById('content-area');
      if (!contentArea) {
        console.error('[UKManage] Content area not found');
        return;
      }

      contentArea.innerHTML = `
        <div class="h-full flex flex-col">
          <!-- 顶部标题栏 -->
          <div class="flex items-center justify-between px-6 py-4 bg-white border-b border-gray-200">
            <div>
              <h1 class="text-2xl font-bold text-gray-800">${window.t('nav.ukManage') || 'UK管理'}</h1>
              <p class="text-sm text-gray-500 mt-1">管理通用知识库条目</p>
            </div>
            <div class="flex gap-3">
              <button onclick="UkManagePage.showImportModal()" 
                      class="px-4 py-2 bg-gray-100 text-gray-700 rounded-lg hover:bg-gray-200 transition-colors text-sm flex items-center gap-2">
                <span>📥</span> 导入
              </button>
              <button onclick="UkManagePage.showExportModal()" 
                      class="px-4 py-2 bg-gray-100 text-gray-700 rounded-lg hover:bg-gray-200 transition-colors text-sm flex items-center gap-2">
                <span>📤</span> 导出
              </button>
              <button onclick="UkManagePage.showStats()" 
                      class="px-4 py-2 bg-gray-100 text-gray-700 rounded-lg hover:bg-gray-200 transition-colors text-sm flex items-center gap-2">
                <span>📊</span> 统计
              </button>
              <button onclick="UkManagePage.showCreateModal()" 
                      class="px-4 py-2 bg-primary-600 text-white rounded-lg hover:bg-primary-700 transition-colors text-sm flex items-center gap-2">
                <span>+</span> 新建条目
              </button>
            </div>
          </div>

          <!-- 搜索栏 -->
          <div class="px-6 py-3 bg-gray-50 border-b border-gray-200">
            <div class="flex gap-3">
              <div class="flex-1 relative">
                <input type="text" 
                       id="uk-search-input"
                       placeholder="搜索知识条目..." 
                       class="w-full px-4 py-2 pl-10 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-primary-500 focus:border-transparent"
                       onkeyup="UkManagePage.handleSearch(event)">
                <span class="absolute left-3 top-2.5 text-gray-400">🔍</span>
              </div>
              <button onclick="UkManagePage.toggleAdvancedSearch()" 
                      class="px-4 py-2 bg-white border border-gray-300 rounded-lg hover:bg-gray-50 transition-colors text-sm">
                高级筛选 ▼
              </button>
            </div>
            
            <!-- 高级筛选面板 (默认隐藏) -->
            <div id="uk-advanced-filters" class="hidden mt-3 p-4 bg-white rounded-lg border border-gray-200">
              <div class="grid grid-cols-4 gap-3">
                <div>
                  <label class="block text-xs text-gray-500 mb-1">题材</label>
                  <select id="uk-filter-genre" class="w-full px-3 py-2 border border-gray-300 rounded-lg text-sm" onchange="UkManagePage.applyFilters()">
                    <option value="">全部题材</option>
                  </select>
                </div>
                <div>
                  <label class="block text-xs text-gray-500 mb-1">年代</label>
                  <select id="uk-filter-era" class="w-full px-3 py-2 border border-gray-300 rounded-lg text-sm" onchange="UkManagePage.applyFilters()">
                    <option value="">全部年代</option>
                  </select>
                </div>
                <div>
                  <label class="block text-xs text-gray-500 mb-1">可靠性</label>
                  <select id="uk-filter-reliability" class="w-full px-3 py-2 border border-gray-300 rounded-lg text-sm" onchange="UkManagePage.applyFilters()">
                    <option value="">全部</option>
                    <option value="5">⭐⭐⭐⭐⭐ (5星)</option>
                    <option value="4">⭐⭐⭐⭐☆ (4星+)</option>
                    <option value="3">⭐⭐⭐☆☆ (3星+)</option>
                  </select>
                </div>
                <div>
                  <label class="block text-xs text-gray-500 mb-1">状态</label>
                  <select id="uk-filter-status" class="w-full px-3 py-2 border border-gray-300 rounded-lg text-sm" onchange="UkManagePage.applyFilters()">
                    <option value="">全部状态</option>
                    <option value="approved">已审核</option>
                    <option value="pending_review">待审核</option>
                    <option value="draft">草稿</option>
                  </select>
                </div>
              </div>
            </div>
          </div>

          <!-- 主内容区：三栏布局 -->
          <div class="flex-1 flex overflow-hidden">
            <!-- 左侧：分类树 -->
            <div class="w-64 bg-white border-r border-gray-200 flex flex-col">
              <div class="p-3 border-b border-gray-200">
                <div class="flex items-center justify-between">
                  <h3 class="font-medium text-gray-700">分类</h3>
                  <button onclick="UkManagePage.loadCategories()" class="text-gray-400 hover:text-gray-600" title="刷新">
                    🔄
                  </button>
                </div>
              </div>
              <div id="uk-category-tree" class="flex-1 overflow-y-auto p-3">
                <div class="text-center text-gray-400 py-8">
                  <div class="spinner w-6 h-6 border-2 border-primary-600 border-t-transparent rounded-full animate-spin mx-auto"></div>
                  <p class="text-sm mt-2">加载分类...</p>
                </div>
              </div>
              <div class="p-3 border-t border-gray-200">
                <button onclick="UkManagePage.showCreateCategoryModal()" 
                        class="w-full px-3 py-2 text-sm text-gray-600 hover:text-primary-600 hover:bg-gray-50 rounded-lg transition-colors">
                  + 新建分类
                </button>
              </div>
            </div>

            <!-- 中间：条目列表 -->
            <div class="flex-1 flex flex-col min-w-0 bg-gray-50">
              <!-- 工具栏 -->
              <div class="px-4 py-2 bg-white border-b border-gray-200 flex items-center justify-between">
                <div class="flex items-center gap-3">
                  <label class="flex items-center gap-2 text-sm text-gray-600">
                    <input type="checkbox" id="uk-select-all" onchange="UkManagePage.toggleSelectAll()">
                    全选
                  </label>
                  <span id="uk-selected-count" class="text-sm text-gray-500 hidden">已选择 <span class="font-medium">0</span> 项</span>
                </div>
                <div class="flex items-center gap-2">
                  <select id="uk-sort-by" class="px-3 py-1.5 border border-gray-300 rounded-lg text-sm" onchange="UkManagePage.loadEntries()">
                    <option value="updated_at">更新时间</option>
                    <option value="created_at">创建时间</option>
                    <option value="reliability">可靠性</option>
                    <option value="view_count">查看次数</option>
                  </select>
                  <button onclick="UkManagePage.toggleSortOrder()" class="px-2 py-1.5 border border-gray-300 rounded-lg hover:bg-gray-50" title="切换排序方向">
                    ↕️
                  </button>
                  <div class="h-4 w-px bg-gray-300 mx-1"></div>
                  <button onclick="UkManagePage.setViewMode('card')" class="p-1.5 rounded hover:bg-gray-100" title="卡片视图">
                    🎴
                  </button>
                  <button onclick="UkManagePage.setViewMode('list')" class="p-1.5 rounded hover:bg-gray-100" title="列表视图">
                    ☰
                  </button>
                </div>
              </div>

              <!-- 列表内容 -->
              <div id="uk-entries-container" class="flex-1 overflow-y-auto p-4">
                <div class="text-center text-gray-400 py-12">
                  <div class="spinner w-8 h-8 border-3 border-primary-600 border-t-transparent rounded-full animate-spin mx-auto"></div>
                  <p class="text-sm mt-3">加载知识条目...</p>
                </div>
              </div>

              <!-- 分页 -->
              <div id="uk-pagination" class="px-4 py-3 bg-white border-t border-gray-200 hidden">
                <!-- 分页组件 -->
              </div>
            </div>

            <!-- 右侧：详情面板 (默认隐藏，选中后显示) -->
            <div id="uk-detail-panel" class="hidden w-96 bg-white border-l border-gray-200 flex flex-col">
              <div class="p-4 border-b border-gray-200">
                <h3 class="font-medium text-gray-700">详情</h3>
              </div>
              <div class="flex-1 overflow-y-auto p-4">
                <p class="text-gray-400 text-center py-8">选择一个条目查看详情</p>
              </div>
            </div>
          </div>
        </div>
      `;

      console.log('[UKManage] Page rendered successfully');
    },

    /**
     * 加载分类树数据
     */
    async loadCategories() {
      console.log('[UKManage] Loading categories...');
      const container = document.getElementById('uk-category-tree');
      if (!container) return;

      try {
        const result = await window.ApiClient.callTool('kb.category.tree', {});
        console.log('[UKManage] Categories loaded:', result);
        
        // 处理返回数据
        const categories = Array.isArray(result) ? result : (result?.categories || []);
        this.state.categories = categories;
        
        if (categories.length === 0) {
          container.innerHTML = `
            <div class="text-center text-gray-400 py-8">
              <p class="text-sm">暂无分类数据</p>
              <p class="text-xs mt-1">请创建分类</p>
            </div>
          `;
          return;
        }
        
        // 将扁平列表转换为树形结构
        const tree = this.buildCategoryTree(categories);
        
        // 初始化展开状态：一级（无 parent_id）和二级（parent_id 指向一级）默认展开
        const parentIds = new Set(categories.filter(c => !c.parent_id).map(c => c.id));
        const level1Ids = new Set(categories.filter(c => c.parent_id && parentIds.has(c.parent_id)).map(c => c.id));
        this.state.expandedCategoryIds = new Set([...parentIds, ...level1Ids]);
        
        // 渲染树（包含"全部"选项）
        let html = `
          <div class="category-item flex items-center py-1.5 px-2 rounded-lg cursor-pointer transition-colors ${!this.state.selectedCategory ? 'bg-primary-50 text-primary-700' : 'hover:bg-gray-50'}"
               onclick="UkManagePage.selectCategory(null, event)">
            <span class="w-6"></span>
            <span class="text-sm font-medium">全部</span>
            <span class="text-xs text-gray-400 ml-auto">(${this.state.totalEntries || 0})</span>
          </div>
        `;
        html += this.renderCategoryTree(tree);
        container.innerHTML = html;
        
      } catch (error) {
        console.error('[UKManage] Failed to load categories:', error);
        container.innerHTML = `
          <div class="text-center text-red-400 py-8">
            <p class="text-sm">加载失败: ${error.message}</p>
            <button onclick="UkManagePage.loadCategories()" class="text-xs mt-2 text-primary-600 hover:underline">
              重试
            </button>
          </div>
        `;
      }
    },

    /**
     * 构建分类树结构
     */
    buildCategoryTree(categories) {
      const categoryMap = {};
      const tree = [];
      
      // 首先创建映射
      categories.forEach(cat => {
        categoryMap[cat.id] = {
          ...cat,
          children: []
        };
      });
      
      // 构建树形结构
      categories.forEach(cat => {
        const node = categoryMap[cat.id];
        if (cat.parent_id && categoryMap[cat.parent_id]) {
          // 有父节点，添加到父节点的children中
          categoryMap[cat.parent_id].children.push(node);
        } else {
          // 没有父节点，是顶级节点
          tree.push(node);
        }
      });
      
      // 按sort_order排序
      const sortByOrder = (nodes) => {
        nodes.sort((a, b) => (a.sort_order || 0) - (b.sort_order || 0));
        nodes.forEach(node => {
          if (node.children.length > 0) {
            sortByOrder(node.children);
          }
        });
      };
      sortByOrder(tree);
      
      return tree;
    },

    /**
     * 渲染分类树
     */
renderCategoryTree(tree, level = 0) {
      if (!tree || tree.length === 0) {
        return '';
      }
      
      return tree.map(node => {
        const hasChildren = node.children && node.children.length > 0;
        const isSelected = this.state.selectedCategory === node.id;
        const paddingLeft = level * 16 + 8;
        const isExpanded = this.state.expandedCategoryIds.has(node.id);
        
        return `
          <div class="category-node" data-id="${node.id}">
            <div class="category-item flex items-center py-1.5 px-2 rounded-lg cursor-pointer transition-colors ${isSelected ? 'bg-primary-50 text-primary-700' : 'hover:bg-gray-50'}"
                 style="padding-left: ${paddingLeft}px"
                 onclick="UkManagePage.selectCategory('${node.id}', event)">
              
              ${hasChildren ? `
                <button class="expand-btn w-5 h-5 flex items-center justify-center mr-1 rounded hover:bg-gray-200 transition-colors"
                        onclick="UkManagePage.toggleCategoryExpand('${node.id}', event)">
                  <span class="transform transition-transform ${isExpanded ? 'rotate-90' : ''}" id="expand-icon-${node.id}">▶</span>
                </button>
              ` : '<span class="w-6"></span>'}
              
              <span class="text-sm truncate flex-1" title="${node.name}">${node.name}</span>
              
              ${node.entry_count ? `
                <span class="text-xs text-gray-400 ml-1">${node.entry_count}</span>
              ` : node.child_count ? `
                <span class="text-xs text-gray-400 ml-1">${node.child_count}子</span>
              ` : ''}
            </div>
            
            ${hasChildren && isExpanded ? `
              <div class="category-children" id="children-${node.id}">
                ${this.renderCategoryTree(node.children, level + 1)}
              </div>
            ` : ''}
          </div>
        `;
      }).join('');
    },

    /**
     * 切换分类展开/折叠
     */
    toggleCategoryExpand(categoryId, event) {
      event.stopPropagation();
      
      // 从扁平数据中找节点，用 child_count 判断是否有子节点
      const node = this.state.categories.find(c => c.id === categoryId);
      if (!node || !node.child_count || node.child_count === 0) return;
      
      if (this.state.expandedCategoryIds.has(categoryId)) {
        this.state.expandedCategoryIds.delete(categoryId);
      } else {
        this.state.expandedCategoryIds.add(categoryId);
      }
      
      const tree = this.buildCategoryTree(this.state.categories);
      const container = document.getElementById('uk-category-tree');
      container.innerHTML = this.renderCategoryTree(tree);
    },

    /**
     * 查找分类节点
     */
    findCategoryNode(categories, id) {
      for (const cat of categories) {
        if (cat.id === id) return cat;
        if (cat.children && cat.children.length > 0) {
          const found = this.findCategoryNode(cat.children, id);
          if (found) return found;
        }
      }
      return null;
    },

    /**
     * 选择分类
     */
    selectCategory(categoryId, event) {
      event.preventDefault();
      
      console.log('[UKManage] Category selected:', categoryId);
      this.state.selectedCategory = categoryId;
      
      // 重新渲染以更新选中状态
      const tree = this.buildCategoryTree(this.state.categories);
      const container = document.getElementById('uk-category-tree');
      container.innerHTML = this.renderCategoryTree(tree);
      
      // 触发条目筛选
      this.state.currentPage = 1;
      this.loadEntries();
    },

    /**
     * 加载条目列表数据
     */
    async loadEntries() {
      console.log('[UKManage] Loading entries...');
      const container = document.getElementById('uk-entries-container');
      if (!container) return;

      // 显示加载状态
      container.innerHTML = `
        <div class="text-center text-gray-400 py-12">
          <div class="spinner w-8 h-8 border-3 border-primary-600 border-t-transparent rounded-full animate-spin mx-auto"></div>
          <p class="text-sm mt-3">加载知识条目...</p>
        </div>
      `;

      try {
        // 构建请求参数
        const params = {
          limit: this.state.pageSize
        };

        // 只在有搜索词时才传 query（空 query 会导致全文搜索无结果）
        if (this.state.searchQuery) {
          params.query = this.state.searchQuery;
        }
        
        // 添加分类筛选
        if (this.state.selectedCategory) {
          const selectedNode = this.findCategoryNode(this.state.categories, this.state.selectedCategory);
          if (selectedNode) {
            params.category_slug = selectedNode.slug;
          }
        }
        
        // 添加其他筛选（仅 MCP 支持的参数）
        if (this.state.filters.genre) {
          params.genre = this.state.filters.genre;
        }
        if (this.state.filters.era) {
          params.era = this.state.filters.era;
        }
        
        console.log('[UKManage] Search params:', params);
        
        const result = await window.ApiClient.callTool('kb.uk.search', params);
        console.log('[UKManage] Entries loaded:', result);
        
        const entries = Array.isArray(result) ? result : (result?.entries || []);
        const total = Array.isArray(result) ? entries.length : (result?.total || 0);
        
        this.state.entries = entries;
        this.state.totalEntries = total;
        
        if (entries.length === 0) {
          container.innerHTML = `
            <div class="text-center text-gray-400 py-12">
              <div class="text-4xl mb-4">📚</div>
              <p class="text-sm">暂无知识条目</p>
              <p class="text-xs mt-2">${this.state.selectedCategory ? '当前分类下没有条目，尝试选择其他分类' : '点击"新建条目"开始创建'}</p>
            </div>
          `;
          this.renderPagination(0);
          return;
        }
        
        // 渲染条目列表
        container.innerHTML = this.renderEntries(entries);
        
        // 渲染分页
        this.renderPagination(total);
        
      } catch (error) {
        console.error('[UKManage] Failed to load entries:', error);
        container.innerHTML = `
          <div class="text-center text-red-400 py-12">
            <p class="text-sm">加载失败: ${error.message}</p>
            <button onclick="UkManagePage.loadEntries()" class="text-xs mt-3 px-3 py-1 bg-primary-600 text-white rounded hover:bg-primary-700">
              重试
            </button>
          </div>
        `;
      }
    },

    /**
     * 渲染条目列表
     */
    renderEntries(entries) {
      return `
        <div class="grid grid-cols-1 gap-3">
          ${entries.map(entry => this.renderEntryCard(entry)).join('')}
        </div>
      `;
    },

    /**
     * 渲染单个条目卡片
     */
    renderEntryCard(entry) {
      const reliabilityStars = '⭐'.repeat(entry.reliability || 0) + '☆'.repeat(5 - (entry.reliability || 0));
      const statusLabels = {
        'approved': { text: '已审核', class: 'bg-green-100 text-green-700' },
        'pending_review': { text: '待审核', class: 'bg-yellow-100 text-yellow-700' },
        'draft': { text: '草稿', class: 'bg-gray-100 text-gray-700' },
        'rejected': { text: '已拒绝', class: 'bg-red-100 text-red-700' }
      };
      const status = statusLabels[entry.status] || statusLabels['draft'];
      
      return `
        <div class="bg-white rounded-lg shadow p-4 hover:shadow-md transition-shadow cursor-pointer ${this.state.selectedEntry?.id === entry.id ? 'ring-2 ring-primary-500' : ''}"
             onclick="UkManagePage.selectEntry('${entry.id}')">
          <div class="flex items-start justify-between">
            <div class="flex-1 min-w-0">
              <div class="flex items-center gap-2">
                <h3 class="font-semibold text-gray-800 truncate">${entry.topic || '未命名'}</h3>
                <span class="text-xs px-2 py-0.5 rounded ${status.class}">${status.text}</span>
              </div>
              <p class="text-sm text-gray-500 mt-1 line-clamp-2">${entry.summary || entry.content?.substring(0, 100) || '暂无描述'}...</p>
              <div class="flex items-center gap-3 mt-2 text-xs text-gray-400">
                <span>${entry.category?.name || '未分类'}</span>
                <span>可靠性: ${reliabilityStars}</span>
                <span>更新: ${new Date(entry.updated_at).toLocaleDateString()}</span>
              </div>
            </div>
            <div class="flex items-center gap-1 ml-2">
              <button onclick="UkManagePage.showEditModal('${entry.id}', event)" 
                      class="p-1.5 text-gray-400 hover:text-primary-600 hover:bg-gray-50 rounded"
                      title="编辑">
                ✏️
              </button>
              <button onclick="UkManagePage.deleteEntry('${entry.id}', event)" 
                      class="p-1.5 text-gray-400 hover:text-red-600 hover:bg-gray-50 rounded"
                      title="删除">
                🗑️
              </button>
            </div>
          </div>
        </div>
      `;
    },

    /**
     * 渲染分页
     */
    renderPagination(total) {
      const paginationEl = document.getElementById('uk-pagination');
      if (!paginationEl) return;
      
      const totalPages = Math.ceil(total / this.state.pageSize);
      
      if (totalPages <= 1) {
        paginationEl.classList.add('hidden');
        return;
      }
      
      paginationEl.classList.remove('hidden');
      
      let html = `
        <div class="flex items-center justify-between">
          <span class="text-sm text-gray-500">
            共 ${total} 条，第 ${this.state.currentPage}/${totalPages} 页
          </span>
          <div class="flex items-center gap-1">
      `;
      
      // 上一页
      html += `
        <button onclick="UkManagePage.goToPage(${this.state.currentPage - 1})" 
                class="px-3 py-1.5 border border-gray-300 rounded-lg text-sm ${this.state.currentPage <= 1 ? 'opacity-50 cursor-not-allowed' : 'hover:bg-gray-50'}"
                ${this.state.currentPage <= 1 ? 'disabled' : ''}>
          上一页
        </button>
      `;
      
      // 页码
      const maxButtons = 5;
      let startPage = Math.max(1, this.state.currentPage - Math.floor(maxButtons / 2));
      let endPage = Math.min(totalPages, startPage + maxButtons - 1);
      
      if (endPage - startPage < maxButtons - 1) {
        startPage = Math.max(1, endPage - maxButtons + 1);
      }
      
      if (startPage > 1) {
        html += `<button onclick="UkManagePage.goToPage(1)" class="px-3 py-1.5 border border-gray-300 rounded-lg text-sm hover:bg-gray-50">1</button>`;
        if (startPage > 2) html += `<span class="px-2">...</span>`;
      }
      
      for (let i = startPage; i <= endPage; i++) {
        html += `
          <button onclick="UkManagePage.goToPage(${i})" 
                  class="px-3 py-1.5 border rounded-lg text-sm ${i === this.state.currentPage ? 'bg-primary-600 text-white border-primary-600' : 'border-gray-300 hover:bg-gray-50'}">
            ${i}
          </button>
        `;
      }
      
      if (endPage < totalPages) {
        if (endPage < totalPages - 1) html += `<span class="px-2">...</span>`;
        html += `<button onclick="UkManagePage.goToPage(${totalPages})" class="px-3 py-1.5 border border-gray-300 rounded-lg text-sm hover:bg-gray-50">${totalPages}</button>`;
      }
      
      // 下一页
      html += `
        <button onclick="UkManagePage.goToPage(${this.state.currentPage + 1})" 
                class="px-3 py-1.5 border border-gray-300 rounded-lg text-sm ${this.state.currentPage >= totalPages ? 'opacity-50 cursor-not-allowed' : 'hover:bg-gray-50'}"
                ${this.state.currentPage >= totalPages ? 'disabled' : ''}>
          下一页
        </button>
      `;
      
      html += '</div></div>';
      paginationEl.innerHTML = html;
    },

    /**
     * 跳转到指定页
     */
    goToPage(page) {
      if (page < 1) return;
      this.state.currentPage = page;
      this.loadEntries();
    },

    /**
     * 选择条目
     */
    selectEntry(entryId) {
      const entry = this.state.entries.find(e => e.id === entryId);
      if (!entry) return;
      
      this.state.selectedEntry = entry;
      
      // 重新渲染列表以更新选中状态
      const container = document.getElementById('uk-entries-container');
      container.innerHTML = this.renderEntries(this.state.entries);
      
      // 显示详情面板
      this.showEntryDetail(entry);
    },

    /**
     * 显示条目详情
     */
    showEntryDetail(entry) {
      const panel = document.getElementById('uk-detail-panel');
      if (!panel) return;
      
      panel.classList.remove('hidden');
      
      const reliabilityStars = '⭐'.repeat(entry.reliability || 0);
      const statusLabels = {
        'approved': { text: '已审核', color: 'green' },
        'pending_review': { text: '待审核', color: 'yellow' },
        'draft': { text: '草稿', color: 'gray' },
        'rejected': { text: '已拒绝', color: 'red' }
      };
      const status = statusLabels[entry.status] || statusLabels['draft'];
      
      panel.innerHTML = `
        <div class="p-4 border-b border-gray-200 flex items-center justify-between">
          <h3 class="font-medium text-gray-700">条目详情</h3>
          <button onclick="UkManagePage.closeDetailPanel()" class="text-gray-400 hover:text-gray-600">
            ✕
          </button>
        </div>
        <div class="flex-1 overflow-y-auto p-4">
          <h2 class="text-lg font-semibold text-gray-800 mb-2">${entry.topic}</h2>
          <div class="flex items-center gap-2 mb-4">
            <span class="text-xs px-2 py-0.5 rounded bg-${status.color}-100 text-${status.color}-700">${status.text}</span>
            <span class="text-xs text-gray-500">可靠性: ${reliabilityStars}</span>
          </div>
          
          <div class="space-y-4">
            <div>
              <label class="text-xs text-gray-500">分类</label>
              <p class="text-sm">${entry.category?.name || '未分类'}</p>
            </div>
            
            <div>
              <label class="text-xs text-gray-500">摘要</label>
              <p class="text-sm text-gray-700">${entry.summary || '无摘要'}</p>
            </div>
            
            <div>
              <label class="text-xs text-gray-500">标签</label>
              <div class="flex flex-wrap gap-1 mt-1">
                ${entry.tags?.map(tag => `<span class="text-xs px-2 py-0.5 bg-gray-100 rounded">#${tag}</span>`).join('') || '<span class="text-xs text-gray-400">无标签</span>'}
              </div>
            </div>
            
            <div>
              <label class="text-xs text-gray-500">来源</label>
              <p class="text-sm">${entry.source || '未知'}</p>
            </div>
            
            <div class="pt-4 border-t border-gray-200">
              <button onclick="UkManagePage.showEditModal('${entry.id}')" 
                      class="w-full px-4 py-2 bg-primary-600 text-white rounded-lg hover:bg-primary-700 text-sm">
                编辑条目
              </button>
            </div>
          </div>
        </div>
      `;
    },

    /**
     * 关闭详情面板
     */
    closeDetailPanel() {
      const panel = document.getElementById('uk-detail-panel');
      if (panel) {
        panel.classList.add('hidden');
      }
      this.state.selectedEntry = null;
      
      // 重新渲染列表以移除选中状态
      if (this.state.entries.length > 0) {
        const container = document.getElementById('uk-entries-container');
        container.innerHTML = this.renderEntries(this.state.entries);
      }
    },

    /**
     * 删除条目
     */
    async deleteEntry(entryId, event) {
      if (event) event.stopPropagation();
      
      if (!confirm('确定要删除这个条目吗？此操作不可恢复。')) {
        return;
      }
      
      try {
        await window.ApiClient.callTool('kb.uk.delete', { entry_id: entryId });
        
        // 从列表中移除
        this.state.entries = this.state.entries.filter(e => e.id !== entryId);
        
        // 如果删除的是当前选中的，关闭详情面板
        if (this.state.selectedEntry?.id === entryId) {
          this.closeDetailPanel();
        }
        
        // 重新渲染
        const container = document.getElementById('uk-entries-container');
        if (this.state.entries.length === 0) {
          container.innerHTML = `
            <div class="text-center text-gray-400 py-12">
              <div class="text-4xl mb-4">📚</div>
              <p class="text-sm">暂无知识条目</p>
            </div>
          `;
        } else {
          container.innerHTML = this.renderEntries(this.state.entries);
        }
        
        alert('删除成功！');
      } catch (error) {
        console.error('[UKManage] Failed to delete entry:', error);
        alert('删除失败: ' + error.message);
      }
    },

    // ========== 事件处理方法 ==========

    handleSearch(event) {
      if (event.key === 'Enter') {
        const query = event.target.value.trim();
        this.state.searchQuery = query;
        this.state.currentPage = 1;
        this.loadEntries();
      }
    },

    toggleAdvancedSearch() {
      const panel = document.getElementById('uk-advanced-filters');
      if (panel) {
        panel.classList.toggle('hidden');
      }
    },

    applyFilters() {
      // 收集筛选条件
      const genreSelect = document.getElementById('uk-filter-genre');
      const eraSelect = document.getElementById('uk-filter-era');
      const reliabilitySelect = document.getElementById('uk-filter-reliability');
      const statusSelect = document.getElementById('uk-filter-status');
      
      this.state.filters = {
        genre: genreSelect?.value || '',
        era: eraSelect?.value || '',
        reliability: reliabilitySelect?.value || null,
        status: statusSelect?.value || ''
      };
      
      this.state.currentPage = 1;
      this.loadEntries();
    },

    toggleSelectAll() {
      const checkboxes = document.querySelectorAll('.uk-entry-checkbox');
      const allChecked = Array.from(checkboxes).every(cb => cb.checked);
      
      checkboxes.forEach(cb => {
        cb.checked = !allChecked;
        const entryId = cb.dataset.entryId;
        if (!allChecked) {
          this.state.selectedEntries.add(entryId);
        } else {
          this.state.selectedEntries.delete(entryId);
        }
      });
      
      this.updateBatchToolbar();
    },

    toggleSortOrder() {
      // 切换排序方向
      this.state.sortOrder = this.state.sortOrder === 'asc' ? 'desc' : 'asc';
      this.state.currentPage = 1;
      this.loadEntries();
      
      // 更新排序按钮图标
      const sortBtn = document.getElementById('uk-sort-order-btn');
      if (sortBtn) {
        sortBtn.textContent = this.state.sortOrder === 'asc' ? '↑' : '↓';
      }
    },

    setViewMode(mode) {
      this.state.viewMode = mode;
      this.renderEntries();
      
      // 更新按钮状态
      const listBtn = document.getElementById('uk-view-list');
      const gridBtn = document.getElementById('uk-view-grid');
      
      if (listBtn && gridBtn) {
        if (mode === 'list') {
          listBtn.classList.add('bg-primary-100', 'text-primary-700');
          gridBtn.classList.remove('bg-primary-100', 'text-primary-700');
        } else {
          gridBtn.classList.add('bg-primary-100', 'text-primary-700');
          listBtn.classList.remove('bg-primary-100', 'text-primary-700');
        }
      }
    },

    // ========== 模态框方法 (待实现) ==========

    showCreateModal() {
      const modal = document.createElement('div');
      modal.className = 'fixed inset-0 bg-black/50 z-50 flex items-center justify-center';
      modal.id = 'uk-create-modal';
      modal.innerHTML = `
        <div class="bg-white rounded-lg shadow-xl w-full max-w-lg mx-4 max-h-[90vh] flex flex-col">
          <div class="px-6 py-4 border-b border-gray-200 flex items-center justify-between">
            <h3 class="text-lg font-semibold">新建知识条目</h3>
            <button onclick="document.getElementById('uk-create-modal').remove()" class="text-gray-400 hover:text-gray-600">
              <svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12"/>
              </svg>
            </button>
          </div>
          <div class="p-6 overflow-y-auto">
            <div class="space-y-4">
              <div>
                <label class="block text-sm font-medium text-gray-700 mb-1">主题 <span class="text-red-500">*</span></label>
                <input type="text" id="uk-create-topic" class="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary-500" placeholder="输入条目主题">
              </div>
              <div>
                <label class="block text-sm font-medium text-gray-700 mb-1">分类</label>
                <select id="uk-create-category" class="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary-500">
                  <option value="">选择分类...</option>
                  ${this.state.categories.map(c => `<option value="${c.slug}">${c.name}</option>`).join('')}
                </select>
              </div>
              <div>
                <label class="block text-sm font-medium text-gray-700 mb-1">内容</label>
                <textarea id="uk-create-content" rows="6" class="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary-500" placeholder="输入知识内容"></textarea>
              </div>
              <div class="grid grid-cols-2 gap-4">
                <div>
                  <label class="block text-sm font-medium text-gray-700 mb-1">年代</label>
                  <input type="text" id="uk-create-era" class="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary-500" placeholder="如：唐朝">
                </div>
                <div>
                  <label class="block text-sm font-medium text-gray-700 mb-1">可信度 (0-1)</label>
                  <input type="number" id="uk-create-reliability" min="0" max="1" step="0.1" value="0.8" class="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary-500">
                </div>
              </div>
            </div>
          </div>
          <div class="px-6 py-4 border-t border-gray-200 flex justify-end gap-3">
            <button onclick="document.getElementById('uk-create-modal').remove()" class="px-4 py-2 border border-gray-300 rounded-lg hover:bg-gray-50">取消</button>
            <button onclick="UkManagePage.confirmCreate()" class="px-4 py-2 bg-primary-600 text-white rounded-lg hover:bg-primary-700">创建</button>
          </div>
        </div>
      `;
      document.body.appendChild(modal);
    },

    async confirmCreate() {
      const topic = document.getElementById('uk-create-topic').value.trim();
      const category = document.getElementById('uk-create-category').value;
      const content = document.getElementById('uk-create-content').value.trim();
      const era = document.getElementById('uk-create-era').value.trim();
      const reliability = parseFloat(document.getElementById('uk-create-reliability').value);

      if (!topic) {
        alert('请输入主题');
        return;
      }

      try {
        await window.ApiClient.callTool('kb.uk.create', {
          topic,
          category_slug: category || undefined,
          content: content || undefined,
          era: era || undefined,
          reliability: isNaN(reliability) ? 0.8 : reliability
        });

        if (window.showToast) {
          window.showToast('success', '条目创建成功');
        }

        document.getElementById('uk-create-modal').remove();
        this.loadEntries();
      } catch (error) {
        console.error('[UKManage] Create error:', error);
        alert('创建失败: ' + (error.message || '未知错误'));
      }
    },

    showImportModal() {
      const modal = document.createElement('div');
      modal.className = 'fixed inset-0 bg-black/50 z-50 flex items-center justify-center';
      modal.id = 'uk-import-modal';
      modal.innerHTML = `
        <div class="bg-white rounded-lg shadow-xl w-full max-w-lg mx-4">
          <div class="px-6 py-4 border-b border-gray-200 flex items-center justify-between">
            <h3 class="text-lg font-semibold">导入知识条目</h3>
            <button onclick="document.getElementById('uk-import-modal').remove()" class="text-gray-400 hover:text-gray-600">
              <svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12"/>
              </svg>
            </button>
          </div>
          <div class="p-6">
            <div class="space-y-4">
              <div>
                <label class="block text-sm font-medium text-gray-700 mb-1">选择文件</label>
                <input type="file" id="uk-import-file" accept=".json,.csv" class="w-full px-3 py-2 border border-gray-300 rounded-lg">
                <p class="text-xs text-gray-500 mt-1">支持 JSON 或 CSV 格式</p>
              </div>
              <div>
                <label class="block text-sm font-medium text-gray-700 mb-1">目标分类</label>
                <select id="uk-import-category" class="w-full px-3 py-2 border border-gray-300 rounded-lg">
                  <option value="">不指定分类</option>
                  ${this.state.categories.map(c => `<option value="${c.slug}">${c.name}</option>`).join('')}
                </select>
              </div>
            </div>
          </div>
          <div class="px-6 py-4 border-t border-gray-200 flex justify-end gap-3">
            <button onclick="document.getElementById('uk-import-modal').remove()" class="px-4 py-2 border border-gray-300 rounded-lg hover:bg-gray-50">取消</button>
            <button onclick="UkManagePage.confirmImport()" class="px-4 py-2 bg-primary-600 text-white rounded-lg hover:bg-primary-700">导入</button>
          </div>
        </div>
      `;
      document.body.appendChild(modal);
    },

    async confirmImport() {
      const fileInput = document.getElementById('uk-import-file');
      const category = document.getElementById('uk-import-category').value;

      if (!fileInput.files || fileInput.files.length === 0) {
        alert('请选择文件');
        return;
      }

      const file = fileInput.files[0];
      const reader = new FileReader();

      reader.onload = async (e) => {
        try {
          let data;
          if (file.name.endsWith('.json')) {
            data = JSON.parse(e.target.result);
          } else {
            // 简单CSV解析
            const lines = e.target.result.split('\n');
            const headers = lines[0].split(',').map(h => h.trim());
            data = lines.slice(1).filter(l => l.trim()).map(line => {
              const values = line.split(',');
              const obj = {};
              headers.forEach((h, i) => {
                obj[h] = values[i]?.trim() || '';
              });
              return obj;
            });
          }

          // 批量创建条目
          const entries = Array.isArray(data) ? data : [data];
          let successCount = 0;

          for (const entry of entries) {
            try {
              await window.ApiClient.callTool('kb.uk.create', {
                topic: entry.topic || entry.title || entry.name || '未命名',
                content: entry.content || entry.description || entry.body || '',
                category_slug: category || entry.category || undefined,
                era: entry.era || entry.period || undefined,
                reliability: parseFloat(entry.reliability) || 0.8
              });
              successCount++;
            } catch (err) {
              console.error('[UKManage] Import entry error:', err);
            }
          }

          if (window.showToast) {
            window.showToast('success', `成功导入 ${successCount}/${entries.length} 条记录`);
          }

          document.getElementById('uk-import-modal').remove();
          this.loadEntries();
        } catch (error) {
          console.error('[UKManage] Import error:', error);
          alert('导入失败: ' + error.message);
        }
      };

      reader.readAsText(file);
    },

    showExportModal() {
      const selectedCount = this.state.selectedEntries.size;
      
      const modal = document.createElement('div');
      modal.className = 'fixed inset-0 bg-black/50 z-50 flex items-center justify-center';
      modal.id = 'uk-export-modal';
      modal.innerHTML = `
        <div class="bg-white rounded-lg shadow-xl w-full max-w-lg mx-4">
          <div class="px-6 py-4 border-b border-gray-200 flex items-center justify-between">
            <h3 class="text-lg font-semibold">导出知识条目</h3>
            <button onclick="document.getElementById('uk-export-modal').remove()" class="text-gray-400 hover:text-gray-600">
              <svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12"/>
              </svg>
            </button>
          </div>
          <div class="p-6">
            <div class="space-y-4">
              <div>
                <label class="block text-sm font-medium text-gray-700 mb-2">导出范围</label>
                <div class="space-y-2">
                  <label class="flex items-center">
                    <input type="radio" name="export-scope" value="all" checked class="mr-2"> 全部条目 (${this.state.pagination.total}条)
                  </label>
                  ${selectedCount > 0 ? `
                    <label class="flex items-center">
                      <input type="radio" name="export-scope" value="selected" class="mr-2"> 选中条目 (${selectedCount}条)
                    </label>
                  ` : ''}
                  <label class="flex items-center">
                    <input type="radio" name="export-scope" value="filtered" class="mr-2"> 当前筛选结果
                  </label>
                </div>
              </div>
              <div>
                <label class="block text-sm font-medium text-gray-700 mb-2">导出格式</label>
                <div class="space-y-2">
                  <label class="flex items-center">
                    <input type="radio" name="export-format" value="json" checked class="mr-2"> JSON
                  </label>
                  <label class="flex items-center">
                    <input type="radio" name="export-format" value="csv" class="mr-2"> CSV
                  </label>
                </div>
              </div>
            </div>
          </div>
          <div class="px-6 py-4 border-t border-gray-200 flex justify-end gap-3">
            <button onclick="document.getElementById('uk-export-modal').remove()" class="px-4 py-2 border border-gray-300 rounded-lg hover:bg-gray-50">取消</button>
            <button onclick="UkManagePage.confirmExport()" class="px-4 py-2 bg-primary-600 text-white rounded-lg hover:bg-primary-700">导出</button>
          </div>
        </div>
      `;
      document.body.appendChild(modal);
    },

    async confirmExport() {
      const scope = document.querySelector('input[name="export-scope"]:checked')?.value || 'all';
      const format = document.querySelector('input[name="export-format"]:checked')?.value || 'json';

      try {
        let entriesToExport = [];

        if (scope === 'selected' && this.state.selectedEntries.size > 0) {
          entriesToExport = this.state.entries.filter(e => this.state.selectedEntries.has(e.id));
        } else if (scope === 'filtered') {
          entriesToExport = this.state.entries;
        } else {
          // 导出全部需要重新加载所有数据
          entriesToExport = this.state.entries;
        }

        if (entriesToExport.length === 0) {
          alert('没有可导出的数据');
          return;
        }

        let content, filename, mimeType;

        if (format === 'json') {
          content = JSON.stringify(entriesToExport, null, 2);
          filename = `uk-export-${Date.now()}.json`;
          mimeType = 'application/json';
        } else {
          // CSV格式
          const headers = ['topic', 'content', 'category', 'era', 'reliability', 'tags'];
          const rows = entriesToExport.map(e => [
            e.topic,
            (e.content || '').replace(/"/g, '""'),
            e.category_slug || '',
            e.era || '',
            e.reliability || 0.8,
            (e.tags || []).join(';')
          ].map(v => `"${v}"`).join(','));
          content = [headers.join(','), ...rows].join('\n');
          filename = `uk-export-${Date.now()}.csv`;
          mimeType = 'text/csv';
        }

        // 下载文件
        const blob = new Blob([content], { type: mimeType });
        const url = URL.createObjectURL(blob);
        const link = document.createElement('a');
        link.href = url;
        link.download = filename;
        link.click();
        URL.revokeObjectURL(url);

        if (window.showToast) {
          window.showToast('success', `已导出 ${entriesToExport.length} 条记录`);
        }

        document.getElementById('uk-export-modal').remove();
      } catch (error) {
        console.error('[UKManage] Export error:', error);
        alert('导出失败: ' + error.message);
      }
    },

    showStats() {
      const stats = {
        total: this.state.pagination.total || 0,
        categories: this.state.categories.length,
        byCategory: {}
      };

      // 统计各分类数量
      this.state.entries.forEach(e => {
        const cat = e.category_slug || '未分类';
        stats.byCategory[cat] = (stats.byCategory[cat] || 0) + 1;
      });

      const modal = document.createElement('div');
      modal.className = 'fixed inset-0 bg-black/50 z-50 flex items-center justify-center';
      modal.id = 'uk-stats-modal';
      modal.innerHTML = `
        <div class="bg-white rounded-lg shadow-xl w-full max-w-lg mx-4">
          <div class="px-6 py-4 border-b border-gray-200 flex items-center justify-between">
            <h3 class="text-lg font-semibold">知识库统计</h3>
            <button onclick="document.getElementById('uk-stats-modal').remove()" class="text-gray-400 hover:text-gray-600">
              <svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12"/>
              </svg>
            </button>
          </div>
          <div class="p-6">
            <div class="grid grid-cols-2 gap-4 mb-6">
              <div class="p-4 bg-blue-50 rounded-lg text-center">
                <div class="text-3xl font-bold text-blue-600">${stats.total}</div>
                <div class="text-sm text-blue-700">总条目数</div>
              </div>
              <div class="p-4 bg-green-50 rounded-lg text-center">
                <div class="text-3xl font-bold text-green-600">${stats.categories}</div>
                <div class="text-sm text-green-700">分类数</div>
              </div>
            </div>
            <div>
              <h4 class="font-medium text-gray-700 mb-3">分类分布</h4>
              <div class="space-y-2">
                ${Object.entries(stats.byCategory).map(([cat, count]) => `
                  <div class="flex items-center justify-between p-2 bg-gray-50 rounded">
                    <span class="text-sm">${cat}</span>
                    <span class="text-sm font-medium">${count}</span>
                  </div>
                `).join('')}
              </div>
            </div>
          </div>
          <div class="px-6 py-4 border-t border-gray-200 flex justify-end">
            <button onclick="document.getElementById('uk-stats-modal').remove()" class="px-4 py-2 border border-gray-300 rounded-lg hover:bg-gray-50">关闭</button>
          </div>
        </div>
      `;
      document.body.appendChild(modal);
    },

    showCreateCategoryModal() {
      const modal = document.createElement('div');
      modal.className = 'fixed inset-0 bg-black/50 z-50 flex items-center justify-center';
      modal.id = 'uk-create-category-modal';
      modal.innerHTML = `
        <div class="bg-white rounded-lg shadow-xl w-full max-w-md mx-4">
          <div class="px-6 py-4 border-b border-gray-200 flex items-center justify-between">
            <h3 class="text-lg font-semibold">新建分类</h3>
            <button onclick="document.getElementById('uk-create-category-modal').remove()" class="text-gray-400 hover:text-gray-600">
              <svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12"/>
              </svg>
            </button>
          </div>
          <div class="p-6">
            <div class="space-y-4">
              <div>
                <label class="block text-sm font-medium text-gray-700 mb-1">分类名称 <span class="text-red-500">*</span></label>
                <input type="text" id="uk-new-category-name" class="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary-500" placeholder="如：历史人物">
              </div>
              <div>
                <label class="block text-sm font-medium text-gray-700 mb-1">标识符 (slug)</label>
                <input type="text" id="uk-new-category-slug" class="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary-500" placeholder="如：historical-figures">
                <p class="text-xs text-gray-500 mt-1">留空将自动生成</p>
              </div>
              <div>
                <label class="block text-sm font-medium text-gray-700 mb-1">描述</label>
                <textarea id="uk-new-category-desc" rows="3" class="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary-500" placeholder="分类描述（可选）"></textarea>
              </div>
            </div>
          </div>
          <div class="px-6 py-4 border-t border-gray-200 flex justify-end gap-3">
            <button onclick="document.getElementById('uk-create-category-modal').remove()" class="px-4 py-2 border border-gray-300 rounded-lg hover:bg-gray-50">取消</button>
            <button onclick="UkManagePage.confirmCreateCategory()" class="px-4 py-2 bg-primary-600 text-white rounded-lg hover:bg-primary-700">创建</button>
          </div>
        </div>
      `;
      document.body.appendChild(modal);
    },

    async confirmCreateCategory() {
      const name = document.getElementById('uk-new-category-name').value.trim();
      let slug = document.getElementById('uk-new-category-slug').value.trim();
      const description = document.getElementById('uk-new-category-desc').value.trim();

      if (!name) {
        alert('请输入分类名称');
        return;
      }

      // 自动生成slug
      if (!slug) {
        slug = name.toLowerCase().replace(/\s+/g, '-').replace(/[^a-z0-9-]/g, '');
      }

      try {
        await window.ApiClient.callTool('kb.category.create', {
          name,
          slug,
          description: description || undefined
        });

        if (window.showToast) {
          window.showToast('success', '分类创建成功');
        }

        document.getElementById('uk-create-category-modal').remove();
        this.loadCategories(); // 刷新分类列表
      } catch (error) {
        console.error('[UKManage] Create category error:', error);
        alert('创建失败: ' + (error.message || '未知错误'));
      }
    },

    /**
     * 显示编辑弹窗
     */
    showEditModal(entryId, event) {
      if (event) event.stopPropagation();
      
      const entry = this.state.entries.find(e => e.id === entryId);
      if (!entry) {
        alert('条目不存在');
        return;
      }
      
      const modal = document.createElement('div');
      modal.className = 'fixed inset-0 bg-black/50 z-50 flex items-center justify-center';
      modal.id = 'uk-edit-modal';
      modal.innerHTML = `
        <div class="bg-white rounded-lg shadow-xl w-full max-w-lg mx-4 max-h-[90vh] flex flex-col">
          <div class="px-6 py-4 border-b border-gray-200 flex items-center justify-between">
            <h3 class="text-lg font-semibold">编辑知识条目</h3>
            <button onclick="document.getElementById('uk-edit-modal').remove()" class="text-gray-400 hover:text-gray-600">
              <svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12"/>
              </svg>
            </button>
          </div>
          <div class="p-6 overflow-y-auto">
            <div class="space-y-4">
              <div>
                <label class="block text-sm font-medium text-gray-700 mb-1">主题 <span class="text-red-500">*</span></label>
                <input type="text" id="uk-edit-topic" value="${entry.topic}" class="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary-500">
              </div>
              <div>
                <label class="block text-sm font-medium text-gray-700 mb-1">分类</label>
                <select id="uk-edit-category" class="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary-500">
                  <option value="">无分类</option>
                  ${this.state.categories.map(c => `
                    <option value="${c.slug}" ${c.slug === entry.category_slug ? 'selected' : ''}>${c.name}</option>
                  `).join('')}
                </select>
              </div>
              <div>
                <label class="block text-sm font-medium text-gray-700 mb-1">内容</label>
                <textarea id="uk-edit-content" rows="6" class="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary-500">${entry.content || ''}</textarea>
              </div>
              <div class="grid grid-cols-2 gap-4">
                <div>
                  <label class="block text-sm font-medium text-gray-700 mb-1">年代</label>
                  <input type="text" id="uk-edit-era" value="${entry.era || ''}" class="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary-500">
                </div>
                <div>
                  <label class="block text-sm font-medium text-gray-700 mb-1">可信度 (0-1)</label>
                  <input type="number" id="uk-edit-reliability" min="0" max="1" step="0.1" value="${entry.reliability || 0.8}" class="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary-500">
                </div>
              </div>
              <div>
                <label class="block text-sm font-medium text-gray-700 mb-1">标签 (用逗号分隔)</label>
                <input type="text" id="uk-edit-tags" value="${(entry.tags || []).join(', ')}" class="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary-500" placeholder="如：历史,人物,唐朝">
              </div>
            </div>
          </div>
          <div class="px-6 py-4 border-t border-gray-200 flex justify-end gap-3">
            <button onclick="document.getElementById('uk-edit-modal').remove()" class="px-4 py-2 border border-gray-300 rounded-lg hover:bg-gray-50">取消</button>
            <button onclick="UkManagePage.confirmEdit('${entryId}')" class="px-4 py-2 bg-primary-600 text-white rounded-lg hover:bg-primary-700">保存</button>
          </div>
        </div>
      `;
      document.body.appendChild(modal);
    },

    async confirmEdit(entryId) {
      const topic = document.getElementById('uk-edit-topic').value.trim();
      const category = document.getElementById('uk-edit-category').value;
      const content = document.getElementById('uk-edit-content').value.trim();
      const era = document.getElementById('uk-edit-era').value.trim();
      const reliability = parseFloat(document.getElementById('uk-edit-reliability').value);
      const tagsStr = document.getElementById('uk-edit-tags').value;
      const tags = tagsStr.split(',').map(t => t.trim()).filter(t => t);

      if (!topic) {
        alert('请输入主题');
        return;
      }

      try {
        await window.ApiClient.callTool('kb.uk.update', {
          entry_id: entryId,
          topic,
          category_slug: category || undefined,
          content: content || undefined,
          era: era || undefined,
          reliability: isNaN(reliability) ? 0.8 : reliability,
          tags: tags.length > 0 ? tags : undefined
        });

        if (window.showToast) {
          window.showToast('success', '条目更新成功');
        }

        document.getElementById('uk-edit-modal').remove();
        this.loadEntries();
      } catch (error) {
        console.error('[UKManage] Edit error:', error);
        alert('更新失败: ' + (error.message || '未知错误'));
      }
    },

    /**
     * 应用筛选条件
     */
    applyFilters() {
      const genreSelect = document.getElementById('uk-filter-genre');
      const eraSelect = document.getElementById('uk-filter-era');
      const reliabilitySelect = document.getElementById('uk-filter-reliability');
      const statusSelect = document.getElementById('uk-filter-status');
      
      this.state.filters = {
        genre: genreSelect?.value || '',
        era: eraSelect?.value || '',
        reliability: reliabilitySelect?.value || null,
        status: statusSelect?.value || ''
      };
      
      this.state.currentPage = 1;
      this.loadEntries();
    }
  };

  console.log('[UKManage] Page module loaded');
})();
