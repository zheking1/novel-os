/**
 * Knowledge Graph Page
 * 关系图谱页面 - 可视化展示实体关系网络
 * 
 * 开发任务 2.1: 页面基础框架
 */
(function() {
  'use strict';

  // 检查 D3.js 是否加载

  window.KnowledgeGraphPage = {
    // 页面状态
    state: {
      nodes: [],
      edges: [],
      selectedNode: null,
      selectedEdge: null,
      zoom: 1,
      transform: { x: 0, y: 0 },
      simulation: null,
      svg: null,
      g: null,
      mode: 'project', // 'project' = 项目级, 'global' = 全局知识库
      filters: {
        entityTypes: [],
        relationTypes: [],
        minIntensity: 1
      }
    },

    /**
     * 初始化页面
     * @param {string} mode - 'project' 或 'global'
     */
    async init(mode = 'project') {
      this.state.mode = mode;
      this.render();
      
      if (typeof d3 !== 'undefined') {
        await this.loadData();
      } else {
        this.showD3Error();
      }
      
      return true;
    },

    /**
     * 渲染页面布局
     */
    render() {
      const contentArea = document.getElementById('content-area');
      if (!contentArea) return;

      const title = this.state.mode === 'global' ? '知识图谱' : '关系图谱';
      const scopeLabel = this.state.mode === 'global' ? '全局知识库' : '当前项目';
      
      contentArea.innerHTML = `
        <div class="h-full flex flex-col">
          <!-- 顶部工具栏 -->
          <div class="flex items-center justify-between px-4 py-3 bg-white border-b border-gray-200">
            <div class="flex items-center gap-4">
              <h1 class="text-xl font-bold text-gray-800">${title}</h1>
              <span class="text-xs px-2 py-1 bg-gray-100 text-gray-600 rounded">${scopeLabel}</span>
              <div class="flex items-center gap-2 text-sm text-gray-500">
                <span id="graph-node-count">0</span> 个实体
                <span class="mx-1">|</span>
                <span id="graph-edge-count">0</span> 条关系
              </div>
            </div>
            
            <div class="flex items-center gap-2">
              <!-- 筛选器 -->
              <select id="graph-entity-filter" class="px-3 py-1.5 border border-gray-300 rounded-lg text-sm" onchange="KnowledgeGraphPage.applyFilters()">
                <option value="">全部实体</option>
                <option value="character">角色</option>
                <option value="location">地点</option>
                <option value="faction">势力</option>
                <option value="item">物品</option>
                <option value="event">事件</option>
              </select>
              
              <select id="graph-layout" class="px-3 py-1.5 border border-gray-300 rounded-lg text-sm" onchange="KnowledgeGraphPage.changeLayout()">
                <option value="force">力导向布局</option>
                <option value="circular">圆形布局</option>
                <option value="hierarchical">层次布局</option>
              </select>
              
              <div class="h-6 w-px bg-gray-300 mx-1"></div>
              
              <button onclick="KnowledgeGraphPage.exportGraph()" class="p-2 hover:bg-gray-100 rounded-lg" title="导出图片">💾</button>
              <button onclick="KnowledgeGraphPage.zoomIn()" class="p-2 hover:bg-gray-100 rounded-lg" title="放大">🔍+</button>
              <button onclick="KnowledgeGraphPage.zoomOut()" class="p-2 hover:bg-gray-100 rounded-lg" title="缩小">🔍-</button>
              <button onclick="KnowledgeGraphPage.resetZoom()" class="p-2 hover:bg-gray-100 rounded-lg" title="重置视图">⌖</button>
              <button onclick="KnowledgeGraphPage.loadData()" class="p-2 hover:bg-gray-100 rounded-lg" title="刷新">🔄</button>
            </div>
          </div>

          <!-- 主内容区 -->
          <div class="flex-1 flex overflow-hidden">
            <!-- 左侧实体列表 -->
            <div class="w-64 bg-white border-r border-gray-200 flex flex-col">
              <div class="p-3 border-b border-gray-200">
                <div class="relative">
                  <input type="text" 
                         id="entity-search" 
                         placeholder="搜索实体..." 
                         class="w-full px-3 py-2 pl-9 border border-gray-300 rounded-lg text-sm"
                         onkeyup="KnowledgeGraphPage.searchEntities(event)">
                  <span class="absolute left-3 top-2.5 text-gray-400">🔍</span>
                </div>
                <div class="flex gap-2 mt-2">
                  <button onclick="KnowledgeGraphPage.clearFilters()" class="text-xs text-gray-500 hover:text-primary-600">清除筛选</button>
                </div>
              </div>
              <div id="graph-entity-list" class="flex-1 overflow-y-auto p-2">
                <div class="text-center text-gray-400 py-8">
                  <div class="spinner w-6 h-6 border-2 border-primary-600 border-t-transparent rounded-full animate-spin mx-auto"></div>
                  <p class="text-xs mt-2">加载实体...</p>
                </div>
              </div>
            </div>

            <!-- 中间图谱区域 -->
            <div class="flex-1 relative bg-gray-50 overflow-hidden">
              <div id="graph-canvas" class="w-full h-full"></div>
              
              <!-- 图例 -->
              <div class="absolute bottom-4 left-4 bg-white rounded-lg shadow p-3 text-xs">
                <div class="font-medium mb-2">图例 (点击筛选)</div>
                <div class="space-y-1">
                  <div class="flex items-center gap-2 cursor-pointer hover:bg-gray-50 p-1 rounded" onclick="KnowledgeGraphPage.filterByType('character')">
                    <span class="w-3 h-3 rounded-full bg-blue-500"></span> 角色
                  </div>
                  <div class="flex items-center gap-2 cursor-pointer hover:bg-gray-50 p-1 rounded" onclick="KnowledgeGraphPage.filterByType('location')">
                    <span class="w-3 h-3 rounded-full bg-green-500"></span> 地点
                  </div>
                  <div class="flex items-center gap-2 cursor-pointer hover:bg-gray-50 p-1 rounded" onclick="KnowledgeGraphPage.filterByType('faction')">
                    <span class="w-3 h-3 rounded-full bg-red-500"></span> 势力
                  </div>
                  <div class="flex items-center gap-2 cursor-pointer hover:bg-gray-50 p-1 rounded" onclick="KnowledgeGraphPage.filterByType('item')">
                    <span class="w-3 h-3 rounded-full bg-yellow-500"></span> 物品
                  </div>
                  <div class="flex items-center gap-2 cursor-pointer hover:bg-gray-50 p-1 rounded" onclick="KnowledgeGraphPage.filterByType('event')">
                    <span class="w-3 h-3 rounded-full bg-purple-500"></span> 事件
                  </div>
                </div>
              </div>
              
              <!-- 操作提示 -->
              <div class="absolute top-4 left-4 bg-white/90 rounded-lg shadow px-3 py-2 text-xs text-gray-500">
                滚轮缩放 · 拖拽移动 · 点击查看详情
              </div>
            </div>

            <!-- 右侧面板 -->
            <div id="graph-side-panel" class="hidden w-80 bg-white border-l border-gray-200 flex flex-col">
              <div class="p-4 border-b border-gray-200 flex items-center justify-between">
                <h3 class="font-medium text-gray-700" id="panel-title">详情</h3>
                <button onclick="KnowledgeGraphPage.closePanel()" class="text-gray-400 hover:text-gray-600">✕</button>
              </div>
              <div id="panel-content" class="flex-1 overflow-y-auto p-4">
                <p class="text-gray-400 text-center py-8">选择一个节点或连线查看详情</p>
              </div>
            </div>
          </div>
        </div>
      `;
    },

    /**
     * 显示 D3 未加载错误
     */
    showD3Error() {
      const canvas = document.getElementById('graph-canvas');
      if (canvas) {
        canvas.innerHTML = `
          <div class="flex items-center justify-center h-full">
            <div class="text-center text-gray-400">
              <div class="text-4xl mb-4">📊</div>
              <p class="text-lg font-medium">D3.js 未加载</p>
              <p class="text-sm mt-2">请检查网络连接或刷新页面重试</p>
              <button onclick="location.reload()" class="mt-4 px-4 py-2 bg-primary-600 text-white rounded-lg hover:bg-primary-700">
                刷新页面
              </button>
            </div>
          </div>
        `;
      }
    },

    /**
     * 加载图谱数据
     */
    async loadData() {
      const canvas = document.getElementById('graph-canvas');
      
      if (!canvas || typeof d3 === 'undefined') return;

      try {
        const workspace = window.AppState.currentWorkspace;
        const project = window.AppState.currentProject;
        
        // 项目模式需要选择项目
        if (this.state.mode === 'project' && (!workspace || !project)) {
          canvas.innerHTML = `
            <div class="flex items-center justify-center h-full">
              <div class="text-center text-gray-400">
                <p>请先选择工作区和项目</p>
              </div>
            </div>
          `;
          return;
        }

        // 显示加载状态
        canvas.innerHTML = `
          <div class="flex items-center justify-center h-full">
            <div class="text-center">
              <div class="spinner w-8 h-8 border-3 border-primary-600 border-t-transparent rounded-full animate-spin mx-auto"></div>
              <p class="text-sm text-gray-500 mt-3">加载图谱数据...</p>
            </div>
          </div>
        `;

        let result;
        
        if (this.state.mode === 'global') {
          // 全局知识库模式 - 加载所有实体
          result = await window.ApiClient.callTool('graph.get_data', {
            workspace: workspace || 'default',
            depth: 2
          });
        } else {
          // 项目模式 - 只加载当前项目实体
          result = await window.ApiClient.callTool('graph.get_data', {
            workspace,
            project,
            depth: 2
          });
        }

        this.state.nodes = result.nodes || [];
        this.state.edges = result.edges || [];

        // 更新计数
        document.getElementById('graph-node-count').textContent = this.state.nodes.length;
        document.getElementById('graph-edge-count').textContent = this.state.edges.length;

        // 渲染实体列表
        this.renderEntityList();

        // 渲染图谱
        this.renderGraph();

      } catch (error) {
        canvas.innerHTML = `
          <div class="flex items-center justify-center h-full">
            <div class="text-center text-red-400">
              <p>加载失败: ${error.message}</p>
              <button onclick="KnowledgeGraphPage.loadData()" class="mt-3 px-4 py-2 bg-primary-600 text-white rounded-lg">
                重试
              </button>
            </div>
          </div>
        `;
      }
    },

    /**
     * 渲染实体列表
     */
    renderEntityList() {
      const container = document.getElementById('graph-entity-list');
      if (!container) return;

      if (this.state.nodes.length === 0) {
        container.innerHTML = `
          <div class="text-center text-gray-400 py-8">
            <p class="text-sm">暂无实体数据</p>
          </div>
        `;
        return;
      }

      const typeIcons = {
        'character': '👤',
        'location': '📍',
        'faction': '🏴',
        'item': '📦',
        'event': '⚡',
        'concept': '💡'
      };

      container.innerHTML = this.state.nodes.map(node => {
        // 计算关系数
        const relationCount = this.state.edges.filter(e => 
          (e.source.id || e.source) === node.id || (e.target.id || e.target) === node.id
        ).length;
        
        return `
          <div class="flex items-center gap-2 p-2 rounded hover:bg-gray-50 cursor-pointer ${this.state.selectedNode?.id === node.id ? 'bg-primary-50' : ''}"
               onclick="KnowledgeGraphPage.focusNode('${node.id}')">
            <span class="text-lg">${typeIcons[node.type] || '●'}</span>
            <div class="flex-1 min-w-0">
              <span class="text-sm truncate block">${node.name}</span>
              <span class="text-xs text-gray-400">${relationCount} 关系</span>
            </div>
          </div>
        `;
      }).join('');
    },

    /**
     * 渲染 D3 图谱
     */
    renderGraph() {
      const container = document.getElementById('graph-canvas');
      if (!container || typeof d3 === 'undefined') return;

      container.innerHTML = '';

      const width = container.clientWidth;
      const height = container.clientHeight;

      // 创建 SVG
      const svg = d3.select('#graph-canvas')
        .append('svg')
        .attr('width', width)
        .attr('height', height)
        .attr('viewBox', [0, 0, width, height]);

      this.state.svg = svg;

      // 创建缩放行为
      const zoom = d3.zoom()
        .scaleExtent([0.1, 5])
        .on('zoom', (event) => {
          this.state.transform = event.transform;
          g.attr('transform', event.transform);
        });

      svg.call(zoom);

      // 创建主图形组
      const g = svg.append('g');
      this.state.g = g;

      // 颜色映射
      const colorMap = {
        'character': '#3b82f6',
        'location': '#22c55e',
        'faction': '#ef4444',
        'item': '#eab308',
        'event': '#a855f7',
        'concept': '#f97316'
      };

      // 创建力导向模拟
      const simulation = d3.forceSimulation(this.state.nodes)
        .force('link', d3.forceLink(this.state.edges).id(d => d.id).distance(100))
        .force('charge', d3.forceManyBody().strength(-300))
        .force('center', d3.forceCenter(width / 2, height / 2))
        .force('collision', d3.forceCollide().radius(40));

      this.state.simulation = simulation;

      // 绘制连线
      const link = g.append('g')
        .selectAll('line')
        .data(this.state.edges)
        .join('line')
        .attr('stroke', '#999')
        .attr('stroke-opacity', 0.6)
        .attr('stroke-width', d => Math.sqrt(d.intensity || 1))
        .on('click', (event, d) => this.selectEdge(d));

      // 绘制节点
      const node = g.append('g')
        .selectAll('g')
        .data(this.state.nodes)
        .join('g')
        .call(d3.drag()
          .on('start', (event, d) => {
            if (!event.active) simulation.alphaTarget(0.3).restart();
            d.fx = d.x;
            d.fy = d.y;
          })
          .on('drag', (event, d) => {
            d.fx = event.x;
            d.fy = event.y;
          })
          .on('end', (event, d) => {
            if (!event.active) simulation.alphaTarget(0);
            d.fx = null;
            d.fy = null;
          }))
        .on('click', (event, d) => {
          event.stopPropagation();
          this.selectNode(d);
        });

      // 节点圆形
      node.append('circle')
        .attr('r', 20)
        .attr('fill', d => colorMap[d.type] || '#999')
        .attr('stroke', '#fff')
        .attr('stroke-width', 2);

      // 节点标签
      node.append('text')
        .text(d => d.name)
        .attr('x', 25)
        .attr('y', 5)
        .attr('font-size', '12px')
        .attr('fill', '#333');

      // 更新位置
      simulation.on('tick', () => {
        link
          .attr('x1', d => d.source.x)
          .attr('y1', d => d.source.y)
          .attr('x2', d => d.target.x)
          .attr('y2', d => d.target.y);

        node.attr('transform', d => `translate(${d.x},${d.y})`);
      });
    },

    /**
     * 选中节点
     */
    selectNode(node) {
      this.state.selectedNode = node;
      this.state.selectedEdge = null;
      
      // 更新实体列表选中状态
      this.renderEntityList();
      
      // 显示详情面板
      this.showNodeDetails(node);
      
      // 高亮节点
      if (this.state.g) {
        this.state.g.selectAll('circle')
          .attr('stroke', d => d.id === node.id ? '#f59e0b' : '#fff')
          .attr('stroke-width', d => d.id === node.id ? 4 : 2);
      }
    },

    /**
     * 显示节点详情
     */
    showNodeDetails(node) {
      const panel = document.getElementById('graph-side-panel');
      const title = document.getElementById('panel-title');
      const content = document.getElementById('panel-content');
      
      if (!panel || !title || !content) return;
      
      panel.classList.remove('hidden');
      title.textContent = node.name || '实体详情';
      
      const typeNames = {
        'character': '角色',
        'location': '地点',
        'faction': '势力',
        'item': '物品',
        'event': '事件',
        'concept': '概念'
      };
      
      // 计算关系
      const relations = this.state.edges.filter(e => 
        (e.source.id || e.source) === node.id || (e.target.id || e.target) === node.id
      );
      
      content.innerHTML = `
        <div class="space-y-4">
          <div>
            <label class="text-xs text-gray-500">类型</label>
            <p class="text-sm font-medium">${typeNames[node.type] || node.type}</p>
          </div>
          <div>
            <label class="text-xs text-gray-500">关系数</label>
            <p class="text-sm font-medium">${relations.length} 条</p>
          </div>
          ${relations.length > 0 ? `
            <div>
              <label class="text-xs text-gray-500">关联实体</label>
              <div class="mt-1 space-y-1 max-h-32 overflow-y-auto">
                ${relations.slice(0, 5).map(r => {
                  const isSource = (r.source.id || r.source) === node.id;
                  const otherId = isSource ? (r.target.id || r.target) : (r.source.id || r.source);
                  const otherNode = this.state.nodes.find(n => n.id === otherId);
                  return otherNode ? `
                    <div class="text-sm p-2 bg-gray-50 rounded cursor-pointer hover:bg-gray-100" onclick="KnowledgeGraphPage.focusNode('${otherId}')">
                      ${isSource ? '→' : '←'} ${otherNode.name} <span class="text-gray-400">(${r.relation_type || '关联'})</span>
                    </div>
                  ` : '';
                }).join('')}
                ${relations.length > 5 ? `<div class="text-xs text-gray-400">还有 ${relations.length - 5} 个...</div>` : ''}
              </div>
            </div>
          ` : ''}
          ${node.profile ? `
            <div>
              <label class="text-xs text-gray-500">简介</label>
              <p class="text-sm text-gray-700">${typeof node.profile === 'string' ? node.profile.substring(0, 200) : JSON.stringify(node.profile).substring(0, 200)}...</p>
            </div>
          ` : ''}
          <div class="pt-4 border-t border-gray-200 space-y-2">
            <button onclick="KnowledgeGraphPage.showSubgraph('${node.id}')" 
                    class="w-full px-4 py-2 bg-primary-600 text-white rounded-lg hover:bg-primary-700 text-sm">
              🔍 查看子图
            </button>
            <button onclick="KnowledgeGraphPage.showEntityDetail('${node.id}')" 
                    class="w-full px-4 py-2 bg-gray-100 text-gray-700 rounded-lg hover:bg-gray-200 text-sm">
              📄 查看完整详情
            </button>
          </div>
        </div>
      `;
    },

    /**
     * 选中连线
     */
    selectEdge(edge) {
      this.state.selectedEdge = edge;
      this.state.selectedNode = null;
      
      // 显示连线详情
      const panel = document.getElementById('graph-side-panel');
      const title = document.getElementById('panel-title');
      const content = document.getElementById('panel-content');
      
      if (!panel || !title || !content) return;
      
      panel.classList.remove('hidden');
      title.textContent = '关系详情';
      
      const sourceNode = this.state.nodes.find(n => n.id === (edge.source.id || edge.source));
      const targetNode = this.state.nodes.find(n => n.id === (edge.target.id || edge.target));
      
      content.innerHTML = `
        <div class="space-y-4">
          <div class="flex items-center justify-center gap-4 py-4">
            <div class="text-center">
              <div class="text-lg font-medium">${sourceNode?.name || 'Unknown'}</div>
              <div class="text-xs text-gray-400">${sourceNode?.type || ''}</div>
            </div>
            <div class="text-2xl text-gray-400">→</div>
            <div class="text-center">
              <div class="text-lg font-medium">${targetNode?.name || 'Unknown'}</div>
              <div class="text-xs text-gray-400">${targetNode?.type || ''}</div>
            </div>
          </div>
          <div>
            <label class="text-xs text-gray-500">关系类型</label>
            <p class="text-sm font-medium">${edge.relation_type || '关联'}</p>
          </div>
          <div>
            <label class="text-xs text-gray-500">强度</label>
            <div class="flex items-center gap-2">
              <div class="flex-1 bg-gray-200 rounded-full h-2">
                <div class="bg-primary-600 h-2 rounded-full" style="width: ${Math.min((edge.intensity || 1) * 20, 100)}%"></div>
              </div>
              <span class="text-sm">${edge.intensity || 1}</span>
            </div>
          </div>
          ${edge.detail ? `
            <div>
              <label class="text-xs text-gray-500">描述</label>
              <p class="text-sm text-gray-700">${edge.detail}</p>
            </div>
          ` : ''}
        </div>
      `;
    },

    /**
     * 聚焦到指定节点
     */
    focusNode(nodeId) {
      const node = this.state.nodes.find(n => n.id === nodeId);
      if (!node || !this.state.svg) return;
      
      this.selectNode(node);
      
      // 缩放并移动到节点位置
      const width = this.state.svg.attr('width');
      const height = this.state.svg.attr('height');
      
      this.state.svg.transition()
        .duration(750)
        .call(
          d3.zoom().transform,
          d3.zoomIdentity
            .translate(width / 2, height / 2)
            .scale(1.5)
            .translate(-node.x, -node.y)
        );
    },

    /**
     * 关闭侧面板
     */
    closePanel() {
      const panel = document.getElementById('graph-side-panel');
      if (panel) panel.classList.add('hidden');
      
      this.state.selectedNode = null;
      this.state.selectedEdge = null;
      
      // 取消高亮
      if (this.state.g) {
        this.state.g.selectAll('circle')
          .attr('stroke', '#fff')
          .attr('stroke-width', 2);
      }
    },

    /**
     * 搜索实体
     */
    searchEntities(event) {
      const query = event.target.value.toLowerCase();
      const container = document.getElementById('graph-entity-list');
      if (!container) return;
      
      const items = container.querySelectorAll('.flex');
      items.forEach(item => {
        const text = item.textContent.toLowerCase();
        item.style.display = text.includes(query) ? '' : 'none';
      });
    },

    /**
     * 应用筛选
     */
    applyFilters() {
      const filterType = document.getElementById('graph-entity-filter')?.value || '';
      
      // 筛选节点
      if (filterType) {
        const filteredNodes = this.state.nodes.filter(n => n.type === filterType);
        const nodeIds = new Set(filteredNodes.map(n => n.id));
        const filteredEdges = this.state.edges.filter(e => 
          nodeIds.has(e.source.id || e.source) && nodeIds.has(e.target.id || e.target)
        );
        
        // 临时保存完整数据
        this._allNodes = this.state.nodes;
        this._allEdges = this.state.edges;
        this.state.nodes = filteredNodes;
        this.state.edges = filteredEdges;
      } else {
        // 恢复完整数据
        if (this._allNodes) {
          this.state.nodes = this._allNodes;
          this.state.edges = this._allEdges;
        }
      }

      // 更新计数
      document.getElementById('graph-node-count').textContent = this.state.nodes.length;
      document.getElementById('graph-edge-count').textContent = this.state.edges.length;

      // 重新渲染
      this.renderEntityList();
      this.renderGraph();
    },

    /**
     * 通过图例筛选
     */
    filterByType(type) {
      document.getElementById('graph-entity-filter').value = type;
      this.applyFilters();
    },

    /**
     * 清除筛选
     */
    clearFilters() {
      document.getElementById('graph-entity-filter').value = '';
      document.getElementById('entity-search').value = '';
      this.applyFilters();
    },

    /**
     * 切换布局
     */
    changeLayout() {
      const layout = document.getElementById('graph-layout')?.value || 'force';
      
      const container = document.getElementById('graph-canvas');
      const width = container.clientWidth;
      const height = container.clientHeight;
      
      if (layout === 'circular') {
        // 圆形布局
        const radius = Math.min(width, height) / 3;
        const centerX = width / 2;
        const centerY = height / 2;
        
        this.state.nodes.forEach((node, i) => {
          const angle = (2 * Math.PI * i) / this.state.nodes.length;
          node.x = centerX + radius * Math.cos(angle);
          node.y = centerY + radius * Math.sin(angle);
        });
      } else if (layout === 'hierarchical') {
        // 层次布局
        const levels = { 'faction': 0, 'location': 1, 'character': 2, 'item': 3, 'event': 4, 'concept': 5 };
        const levelHeight = height / 6;
        
        this.state.nodes.forEach(node => {
          const level = levels[node.type] || 3;
          node.y = level * levelHeight + levelHeight / 2;
        });
      }
      
      // 重新渲染
      this.renderGraph();
    },

    /**
     * 导出图谱图片
     */
    exportGraph() {
      const svg = document.querySelector('#graph-canvas svg');
      if (!svg) {
        window.showToast && window.showToast('warning', '图谱尚未加载');
        return;
      }
      
      // 创建Canvas
      const canvas = document.createElement('canvas');
      const ctx = canvas.getContext('2d');
      const svgData = new XMLSerializer().serializeToString(svg);
      
      const img = new Image();
      const svgBlob = new Blob([svgData], { type: 'image/svg+xml;charset=utf-8' });
      const url = URL.createObjectURL(svgBlob);
      
      img.onload = function() {
        canvas.width = img.width;
        canvas.height = img.height;
        ctx.drawImage(img, 0, 0);
        URL.revokeObjectURL(url);
        
        // 下载
        const link = document.createElement('a');
        link.download = 'knowledge-graph.png';
        link.href = canvas.toDataURL('image/png');
        link.click();
      };
      
      img.src = url;
    },

    /**
     * 显示添加关系模态框
     */
    showRelationModal() {
      // 填充实体下拉列表
      const options = this.state.nodes.map(n => 
        `<option value="${n.id}">${n.name} (${n.type})</option>`
      ).join('');

      const modal = document.createElement('div');
      modal.id = 'relation-modal';
      modal.className = 'fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50';
      modal.innerHTML = `
        <div class="bg-white rounded-lg shadow-xl w-[500px] max-h-[80vh] flex flex-col">
          <div class="flex items-center justify-between p-4 border-b border-gray-200">
            <h3 class="text-lg font-semibold">添加关系</h3>
            <button onclick="document.getElementById('relation-modal').remove()" class="text-gray-400 hover:text-gray-600">✕</button>
          </div>
          <div class="p-6 space-y-4 overflow-y-auto">
            <div>
              <label class="block text-sm font-medium text-gray-700 mb-1">源实体</label>
              <select id="relation-source" class="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-primary-500">
                <option value="">选择实体...</option>
                ${options}
              </select>
            </div>
            <div>
              <label class="block text-sm font-medium text-gray-700 mb-1">关系类型</label>
              <select id="relation-type" class="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-primary-500">
                <option value="related_to">相关联</option>
                <option value="belongs_to">属于</option>
                <option value="located_at">位于</option>
                <option value="participated_in">参与</option>
                <option value="caused_by">导致</option>
                <option value="owns">拥有</option>
                <option value="friend">朋友</option>
                <option value="enemy">敌人</option>
                <option value="family">家人</option>
                <option value="master">师徒</option>
              </select>
            </div>
            <div>
              <label class="block text-sm font-medium text-gray-700 mb-1">目标实体</label>
              <select id="relation-target" class="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-primary-500">
                <option value="">选择实体...</option>
                ${options}
              </select>
            </div>
            <div>
              <label class="block text-sm font-medium text-gray-700 mb-1">关系强度 (1-5)</label>
              <input type="range" id="relation-intensity" min="1" max="5" value="3" class="w-full" oninput="document.getElementById('intensity-value').textContent = this.value">
              <div class="text-center text-sm text-gray-600">强度: <span id="intensity-value">3</span></div>
            </div>
            <div>
              <label class="block text-sm font-medium text-gray-700 mb-1">关系描述</label>
              <textarea id="relation-detail" placeholder="可选描述" class="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-primary-500 h-20"></textarea>
            </div>
          </div>
          <div class="flex justify-end gap-3 p-4 border-t border-gray-200">
            <button onclick="document.getElementById('relation-modal').remove()" class="px-4 py-2 text-gray-600 hover:text-gray-800">取消</button>
            <button onclick="KnowledgeGraphPage.confirmAddRelation()" class="px-4 py-2 bg-primary-600 text-white rounded-lg hover:bg-primary-700">添加</button>
          </div>
        </div>
      `;
      document.body.appendChild(modal);
    },

    /**
     * 确认添加关系
     */
    async confirmAddRelation() {
      const sourceId = document.getElementById('relation-source').value;
      const targetId = document.getElementById('relation-target').value;
      const relationType = document.getElementById('relation-type').value;
      const intensity = parseInt(document.getElementById('relation-intensity').value);
      const detail = document.getElementById('relation-detail').value.trim();

      if (!sourceId || !targetId) {
        window.showToast && window.showToast('warning', '请选择源实体和目标实体');
        return;
      }

      if (sourceId === targetId) {
        window.showToast && window.showToast('warning', '不能将实体关联到自身');
        return;
      }

      try {
        const workspace = window.AppState.currentWorkspace;
        const project = window.AppState.currentProject;

        await window.ApiClient.callTool('kb.relation.create', {
          from_entity_id: sourceId,
          to_entity_id: targetId,
          relation_type: relationType,
          detail: detail || undefined,
          strength: intensity
        });

        window.showToast && window.showToast('success', '关系添加成功');
        document.getElementById('relation-modal').remove();
        
        // 刷新数据
        await this.loadData();
      } catch (error) {
        window.showToast && window.showToast('error', '添加失败: ' + (error.message || '未知错误'));
      }
    },

    /**
     * 删除关系
     */
    async deleteRelation(edge) {
      if (!confirm('确定要删除这条关系吗？')) return;

      try {
        // 这里需要后端支持删除关系的API
        window.showToast && window.showToast('info', '删除关系功能需要后端API支持');
      } catch (error) {
        window.showToast && window.showToast('error', '删除失败');
      }
    },

    /**
     * 查看子图 - 以选中节点为中心的辐射布局
     */
    showSubgraph(nodeId) {
      const centerNode = this.state.nodes.find(n => n.id === nodeId);
      if (!centerNode) return;

      // 找到所有与中心节点相关的边和节点
      const relatedEdges = this.state.edges.filter(e => 
        (e.source.id || e.source) === nodeId || (e.target.id || e.target) === nodeId
      );

      const relatedNodeIds = new Set([nodeId]);
      relatedEdges.forEach(e => {
        relatedNodeIds.add(e.source.id || e.source);
        relatedNodeIds.add(e.target.id || e.target);
      });

      // 筛选出子图数据
      const subgraphNodes = this.state.nodes.filter(n => relatedNodeIds.has(n.id));
      const subgraphEdges = relatedEdges;

      if (subgraphNodes.length <= 1) {
        window.showToast && window.showToast('warning', '该实体暂无关联实体');
        return;
      }

      // 创建子图弹窗
      const modal = document.createElement('div');
      modal.className = 'fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50';
      modal.id = 'subgraph-modal';
      modal.innerHTML = `
        <div class="bg-white rounded-lg shadow-xl w-[800px] h-[600px] flex flex-col">
          <div class="flex items-center justify-between p-4 border-b border-gray-200">
            <div>
              <h3 class="text-lg font-semibold">子图: ${centerNode.name}</h3>
              <p class="text-sm text-gray-500">${subgraphNodes.length} 个实体, ${subgraphEdges.length} 条关系</p>
            </div>
            <button onclick="document.getElementById('subgraph-modal').remove()" class="text-gray-400 hover:text-gray-600">✕</button>
          </div>
          <div class="flex-1 relative bg-gray-50" id="subgraph-canvas"></div>
          <div class="p-3 border-t border-gray-200 flex justify-end gap-2">
            <button onclick="KnowledgeGraphPage.exportSubgraph()" class="px-4 py-2 bg-gray-100 text-gray-700 rounded-lg text-sm">💾 导出</button>
            <button onclick="document.getElementById('subgraph-modal').remove()" class="px-4 py-2 bg-primary-600 text-white rounded-lg text-sm">关闭</button>
          </div>
        </div>
      `;
      document.body.appendChild(modal);

      // 渲染子图
      this.renderSubgraph(subgraphNodes, subgraphEdges, centerNode);
    },

    /**
     * 渲染子图 - 中心辐射布局
     */
    renderSubgraph(nodes, edges, centerNode) {
      const container = document.getElementById('subgraph-canvas');
      if (!container || typeof d3 === 'undefined') return;

      container.innerHTML = '';
      const width = container.clientWidth;
      const height = container.clientHeight;

      // 创建 SVG
      const svg = d3.select('#subgraph-canvas')
        .append('svg')
        .attr('width', width)
        .attr('height', height)
        .attr('viewBox', [0, 0, width, height]);

      // 创建缩放行为
      const zoom = d3.zoom()
        .scaleExtent([0.5, 3])
        .on('zoom', (event) => {
          g.attr('transform', event.transform);
        });
      svg.call(zoom);

      const g = svg.append('g');

      // 颜色映射
      const colorMap = {
        'character': '#3b82f6',
        'location': '#22c55e',
        'faction': '#ef4444',
        'item': '#eab308',
        'event': '#a855f7',
        'concept': '#f97316'
      };

      // 中心辐射布局计算
      const centerX = width / 2;
      const centerY = height / 2;
      const radius = Math.min(width, height) / 3;

      // 设置中心节点位置
      centerNode.x = centerX;
      centerNode.y = centerY;

      // 设置其他节点位置（围绕中心均匀分布）
      const otherNodes = nodes.filter(n => n.id !== centerNode.id);
      otherNodes.forEach((node, i) => {
        const angle = (2 * Math.PI * i) / otherNodes.length - Math.PI / 2;
        node.x = centerX + radius * Math.cos(angle);
        node.y = centerY + radius * Math.sin(angle);
      });

      // 绘制连线
      const link = g.append('g')
        .selectAll('line')
        .data(edges)
        .join('line')
        .attr('stroke', '#999')
        .attr('stroke-opacity', 0.6)
        .attr('stroke-width', d => Math.sqrt(d.intensity || 1) * 2)
        .attr('x1', d => d.source.x || nodes.find(n => n.id === (d.source.id || d.source))?.x || centerX)
        .attr('y1', d => d.source.y || nodes.find(n => n.id === (d.source.id || d.source))?.y || centerY)
        .attr('x2', d => d.target.x || nodes.find(n => n.id === (d.target.id || d.target))?.x || centerX)
        .attr('y2', d => d.target.y || nodes.find(n => n.id === (d.target.id || d.target))?.y || centerY);

      // 绘制节点组
      const node = g.append('g')
        .selectAll('g')
        .data(nodes)
        .join('g')
        .attr('transform', d => `translate(${d.x},${d.y})`)
        .on('click', (event, d) => {
          event.stopPropagation();
          if (d.id !== centerNode.id) {
            KnowledgeGraphPage.showSubgraph(d.id);
          }
        });

      // 节点圆形
      node.append('circle')
        .attr('r', d => d.id === centerNode.id ? 30 : 20)
        .attr('fill', d => colorMap[d.type] || '#999')
        .attr('stroke', d => d.id === centerNode.id ? '#f59e0b' : '#fff')
        .attr('stroke-width', d => d.id === centerNode.id ? 4 : 2);

      // 节点图标
      const typeIcons = { 'character': '👤', 'location': '📍', 'faction': '🏴', 'item': '📦', 'event': '⚡', 'concept': '💡' };
      node.append('text')
        .text(d => typeIcons[d.type] || '●')
        .attr('text-anchor', 'middle')
        .attr('dy', '0.35em')
        .attr('font-size', d => d.id === centerNode.id ? '18px' : '14px');

      // 节点标签
      node.append('text')
        .text(d => d.name)
        .attr('y', d => d.id === centerNode.id ? 45 : 32)
        .attr('text-anchor', 'middle')
        .attr('font-size', d => d.id === centerNode.id ? '14px' : '12px')
        .attr('font-weight', d => d.id === centerNode.id ? 'bold' : 'normal')
        .attr('fill', '#333');

      // 添加提示
      g.append('text')
        .attr('x', 10)
        .attr('y', height - 10)
        .attr('font-size', '11px')
        .attr('fill', '#999')
        .text('点击外围节点可切换中心');
    },

    /**
     * 导出子图
     */
    exportSubgraph() {
      const svg = document.querySelector('#subgraph-canvas svg');
      if (!svg) return;

      const canvas = document.createElement('canvas');
      const ctx = canvas.getContext('2d');
      const svgData = new XMLSerializer().serializeToString(svg);
      
      const img = new Image();
      const svgBlob = new Blob([svgData], { type: 'image/svg+xml;charset=utf-8' });
      const url = URL.createObjectURL(svgBlob);
      
      img.onload = function() {
        canvas.width = img.width;
        canvas.height = img.height;
        ctx.drawImage(img, 0, 0);
        URL.revokeObjectURL(url);
        
        const link = document.createElement('a');
        link.download = 'subgraph.png';
        link.href = canvas.toDataURL('image/png');
        link.click();
      };
      
      img.src = url;
    },

    /**
     * 缩放控制
     */
    zoomIn() {
      if (!this.state.svg) return;
      this.state.svg.transition().call(
        d3.zoom().scaleBy,
        1.3
      );
    },

    zoomOut() {
      if (!this.state.svg) return;
      this.state.svg.transition().call(
        d3.zoom().scaleBy,
        1 / 1.3
      );
    },

    resetZoom() {
      if (!this.state.svg) return;
      this.state.svg.transition().call(
        d3.zoom().transform,
        d3.zoomIdentity
      );
    },

    /**
     * 显示实体详情弹窗
     */
    showEntityDetail(nodeId) {
      const node = this.state.nodes.find(n => n.id === nodeId);
      if (!node) return;

      const typeNames = {
        'character': '角色',
        'location': '地点',
        'faction': '势力',
        'item': '物品',
        'event': '事件',
        'concept': '概念'
      };

      const typeIcons = {
        'character': '👤',
        'location': '📍',
        'faction': '🏴',
        'item': '📦',
        'event': '⚡',
        'concept': '💡'
      };

      // 计算关系
      const relations = this.state.edges.filter(e => 
        (e.source.id || e.source) === nodeId || (e.target.id || e.target) === nodeId
      );

      const modal = document.createElement('div');
      modal.className = 'fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50';
      modal.id = 'entity-detail-modal';
      modal.innerHTML = `
        <div class="bg-white rounded-lg shadow-xl w-[600px] max-h-[80vh] flex flex-col">
          <div class="flex items-center justify-between p-4 border-b border-gray-200">
            <div class="flex items-center gap-2">
              <span class="text-2xl">${typeIcons[node.type] || '●'}</span>
              <h3 class="text-lg font-semibold">${node.name}</h3>
            </div>
            <button onclick="document.getElementById('entity-detail-modal').remove()" class="text-gray-400 hover:text-gray-600">✕</button>
          </div>
          <div class="p-6 overflow-y-auto">
            <div class="space-y-4">
              <div class="grid grid-cols-2 gap-4">
                <div class="p-3 bg-gray-50 rounded-lg">
                  <div class="text-xs text-gray-500">类型</div>
                  <div class="font-medium">${typeNames[node.type] || node.type}</div>
                </div>
                <div class="p-3 bg-gray-50 rounded-lg">
                  <div class="text-xs text-gray-500">关系数</div>
                  <div class="font-medium">${relations.length} 条</div>
                </div>
              </div>
              
              ${node.profile ? `
                <div>
                  <label class="text-xs text-gray-500">简介</label>
                  <p class="text-sm text-gray-700 mt-1">${typeof node.profile === 'string' ? node.profile : JSON.stringify(node.profile)}</p>
                </div>
              ` : ''}
              
              ${relations.length > 0 ? `
                <div>
                  <label class="text-xs text-gray-500">关联实体</label>
                  <div class="mt-2 space-y-2">
                    ${relations.slice(0, 10).map(r => {
                      const isSource = (r.source.id || r.source) === nodeId;
                      const otherId = isSource ? (r.target.id || r.target) : (r.source.id || r.source);
                      const otherNode = this.state.nodes.find(n => n.id === otherId);
                      if (!otherNode) return '';
                      return `
                        <div class="flex items-center justify-between p-2 bg-gray-50 rounded">
                          <div class="flex items-center gap-2">
                            <span>${typeIcons[otherNode.type] || '●'}</span>
                            <span>${otherNode.name}</span>
                          </div>
                          <div class="flex items-center gap-2">
                            <span class="text-xs text-gray-400">${isSource ? '→' : '←'} ${r.relation_type || '关联'}</span>
                            <button onclick="KnowledgeGraphPage.showSubgraph('${otherNode.id}')" class="text-xs text-primary-600 hover:text-primary-700">查看子图</button>
                          </div>
                        </div>
                      `;
                    }).join('')}
                    ${relations.length > 10 ? `<div class="text-xs text-gray-400 text-center">还有 ${relations.length - 10} 个关联...</div>` : ''}
                  </div>
                </div>
              ` : ''}
            </div>
          </div>
          <div class="flex justify-end gap-3 p-4 border-t border-gray-200">
            <button onclick="KnowledgeGraphPage.showSubgraph('${nodeId}')" class="px-4 py-2 bg-primary-600 text-white rounded-lg hover:bg-primary-700">🔍 查看子图</button>
            <button onclick="document.getElementById('entity-detail-modal').remove()" class="px-4 py-2 text-gray-600 hover:text-gray-800">关闭</button>
          </div>
        </div>
      `;
      document.body.appendChild(modal);
    }
  };

})();
