/**
 * Novel OS - Project Manage Page
 * 项目管理页面 - 列出工作空间内的项目，支持创建和选择项目
 * @version 2.0.0
 */
(function() {
  'use strict';

  if (window.ProjectManagePage) {
    return;
  }

  window.ProjectManagePage = {
    projects: [],
    currentFilters: {},

    async init() {
      console.log('[ProjectManage] Initializing...');
      this.render();
      await this.loadData();
      return true;
    },

    render() {
      const contentArea = document.getElementById('content-area');
      if (!contentArea) return;

      contentArea.innerHTML = `
        <div class="space-y-4">
          <!-- 页面标题 -->
          <div class="flex items-center justify-between">
            <div>
              <h1 class="text-2xl font-bold text-gray-800">项目管理</h1>
              <p class="text-gray-500 mt-1">管理工作空间内的所有项目</p>
            </div>
            <button onclick="ProjectManagePage.showCreateModal()" 
                    class="px-4 py-2 bg-primary-600 text-white rounded-lg hover:bg-primary-700 transition-colors flex items-center gap-2">
              <span>➕</span> 新建项目
            </button>
          </div>

          <!-- 搜索和筛选 -->
          <div class="flex gap-4 items-center">
            <div class="flex-1 relative">
              <input type="text" 
                     id="project-search" 
                     placeholder="搜索项目名称或标识..." 
                     oninput="ProjectManagePage.handleSearch(this.value)"
                     class="w-full px-4 py-2 pl-10 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary-500 focus:border-transparent">
              <span class="absolute left-3 top-2.5 text-gray-400">🔍</span>
            </div>
            <button onclick="ProjectManagePage.loadData()" 
                    class="px-4 py-2 bg-gray-100 text-gray-700 rounded-lg hover:bg-gray-200 transition-colors">
              🔄 刷新
            </button>
          </div>

          <!-- 项目列表 -->
          <div id="project-list-container" class="bg-white rounded-lg shadow">
            <div class="p-8 text-center text-gray-500">
              <div class="spinner w-8 h-8 border-4 border-primary-600 border-t-transparent rounded-full animate-spin mx-auto"></div>
              <p class="mt-2">加载中...</p>
            </div>
          </div>
        </div>

        <!-- 创建/编辑模态框 -->
        <div id="project-modal" class="fixed inset-0 bg-black/50 z-50 hidden flex items-center justify-center">
          <div class="bg-white rounded-lg shadow-xl w-full max-w-md mx-4">
            <div class="px-6 py-4 border-b border-gray-200 flex items-center justify-between">
              <h3 id="project-modal-title" class="text-lg font-semibold">新建项目</h3>
              <button onclick="ProjectManagePage.hideModal()" class="text-gray-400 hover:text-gray-600">
                <svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12"/>
                </svg>
              </button>
            </div>
            <div class="p-6">
              <form id="project-form" onsubmit="ProjectManagePage.saveProject(event)">
                <input type="hidden" id="project-slug-original">
                <div class="space-y-4">
                  <div>
                    <label class="block text-sm font-medium text-gray-700 mb-1">项目标识 (slug) <span class="text-red-500">*</span></label>
                    <input type="text" 
                           id="project-slug" 
                           required
                           placeholder="例如: xianni"
                           class="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary-500 focus:border-transparent font-mono text-sm">
                    <p class="text-xs text-gray-500 mt-1">只允许小写字母、数字和横线</p>
                  </div>
                  <div>
                    <label class="block text-sm font-medium text-gray-700 mb-1">项目标题 <span class="text-red-500">*</span></label>
                    <input type="text" 
                           id="project-title" 
                           required
                           placeholder="例如: 仙逆"
                           class="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary-500 focus:border-transparent">
                  </div>
                  <div>
                    <label class="block text-sm font-medium text-gray-700 mb-1">描述</label>
                    <textarea id="project-description" 
                              rows="3"
                              placeholder="项目简介（可选）"
                              class="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary-500 focus:border-transparent resize-y"></textarea>
                  </div>
                </div>
                <div class="mt-6 flex justify-end gap-3">
                  <button type="button" onclick="ProjectManagePage.hideModal()" 
                          class="px-4 py-2 border border-gray-300 rounded-lg hover:bg-gray-50 transition-colors">
                    取消
                  </button>
                  <button type="submit" id="project-manage-save-btn" class="px-4 py-2 bg-primary-600 text-white rounded-lg hover:bg-primary-700 transition-colors">
                    保存
                  </button>
                </div>
              </form>
            </div>
          </div>
        </div>
      `;
    },

    async loadData() {
      const container = document.getElementById('project-list-container');
      const workspace = window.AppState?.currentWorkspace;
      
      if (!workspace) {
        container.innerHTML = `
          <div class="p-8 text-center text-gray-500">
            <div class="text-4xl mb-4">📂</div>
            <p>请先选择工作空间</p>
          </div>
        `;
        return;
      }

      try {
        const result = await window.ApiClient.callTool('project.list', { workspace });
        this.projects = result.projects || [];
        this.renderList(this.projects);
      } catch (error) {
        console.error('[ProjectManage] Load error:', error);
        container.innerHTML = `
          <div class="p-8 text-center text-red-500">
            <p>加载失败: ${error.message}</p>
            <button onclick="ProjectManagePage.loadData()" class="mt-4 px-4 py-2 bg-gray-100 rounded hover:bg-gray-200">
              重试
            </button>
          </div>
        `;
      }
    },

    renderList(projects) {
      const container = document.getElementById('project-list-container');
      const currentProject = window.AppState?.currentProject;
      
      // 应用搜索筛选
      const searchTerm = (document.getElementById('project-search')?.value || '').toLowerCase();
      if (searchTerm) {
        projects = projects.filter(p => 
          (p.title || '').toLowerCase().includes(searchTerm) ||
          (p.slug || '').toLowerCase().includes(searchTerm) ||
          (p.description || '').toLowerCase().includes(searchTerm)
        );
      }

      if (!projects || projects.length === 0) {
        container.innerHTML = `
          <div class="p-8 text-center text-gray-500">
            <div class="text-4xl mb-4">📚</div>
            <p>暂无项目</p>
            <p class="text-sm mt-2">点击右上角按钮创建第一个项目</p>
          </div>
        `;
        return;
      }

      container.innerHTML = `
        <div class="divide-y divide-gray-200">
          ${projects.map(p => `
            <div class="p-4 hover:bg-gray-50 transition-colors ${p.slug === currentProject ? 'bg-primary-50 border-l-4 border-primary-500' : ''}">
              <div class="flex items-start justify-between">
                <div class="flex-1 min-w-0">
                  <div class="flex items-center gap-2">
                    <span class="text-2xl">📚</span>
                    <h3 class="font-medium text-gray-800 truncate">${p.title || p.slug}</h3>
                    ${p.slug === currentProject ? '<span class="px-2 py-0.5 text-xs bg-primary-100 text-primary-700 rounded">当前</span>' : ''}
                  </div>
                  <p class="text-sm text-gray-500 mt-1 font-mono">${p.slug}</p>
                  ${p.description ? `<p class="text-sm text-gray-600 mt-1 line-clamp-2">${p.description}</p>` : ''}
                </div>
                <div class="flex items-center gap-2 ml-4">
                  ${p.slug !== currentProject ? `
                    <button onclick="ProjectManagePage.selectProject('${p.slug}')" 
                            class="px-3 py-1.5 bg-primary-600 text-white text-sm rounded hover:bg-primary-700 transition-colors">
                      选择
                    </button>
                  ` : ''}
                  <button onclick="ProjectManagePage.editProject('${p.slug}')" 
                          class="p-2 text-gray-400 hover:text-primary-600 hover:bg-primary-50 rounded transition-colors"
                          title="编辑">
                    <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M11 5H6a2 2 0 00-2 2v11a2 2 0 002 2h11a2 2 0 002-2v-5m-1.414-9.414a2 2 0 112.828 2.828L11.828 15H9v-2.828l8.586-8.586z"/>
                    </svg>
                  </button>
                  <button onclick="ProjectManagePage.deleteProject('${p.slug}', '${p.title || p.slug}')" 
                          class="p-2 text-gray-400 hover:text-red-600 hover:bg-red-50 rounded transition-colors"
                          title="删除">
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

    handleSearch(value) {
      this.renderList(this.projects);
    },

    async selectProject(slug) {
      try {
        window.AppState.currentProject = slug;
        localStorage.setItem('novel-project', slug);
        
        // 更新项目选择器
        const projectSelect = document.getElementById('project-select');
        if (projectSelect) {
          projectSelect.value = slug;
        }
        
        // 刷新菜单
        if (window.MenuManager?.updateMenuVisibility) {
          window.MenuManager.updateMenuVisibility();
        }
        
        // 刷新列表
        await this.loadData();
        
        // 显示成功提示
        if (window.showToast) {
          window.showToast('success', `已切换到项目: ${slug}`);
        }
      } catch (error) {
        console.error('[ProjectManage] Select error:', error);
        alert('切换项目失败: ' + error.message);
      }
    },

    showCreateModal() {
      document.getElementById('project-modal-title').textContent = '新建项目';
      document.getElementById('project-slug-original').value = '';
      document.getElementById('project-slug').value = '';
      document.getElementById('project-title').value = '';
      document.getElementById('project-description').value = '';
      document.getElementById('project-slug').disabled = false;
      document.getElementById('project-modal').classList.remove('hidden');
    },

    hideModal() {
      document.getElementById('project-modal').classList.add('hidden');
    },

    async editProject(slug) {
      const project = this.projects.find(p => p.slug === slug);
      if (!project) {
        alert('项目不存在');
        return;
      }

      document.getElementById('project-modal-title').textContent = '编辑项目';
      document.getElementById('project-slug-original').value = project.slug;
      document.getElementById('project-slug').value = project.slug;
      document.getElementById('project-slug').disabled = true; // slug 不可修改
      document.getElementById('project-title').value = project.title || '';
      document.getElementById('project-description').value = project.description || '';
      document.getElementById('project-modal').classList.remove('hidden');
    },

    async saveProject(e) {
      e.preventDefault();
      
      const workspace = window.AppState?.currentWorkspace;
      if (!workspace) {
        alert('请先选择工作空间');
        return;
      }

      const originalSlug = document.getElementById('project-slug-original').value;
      const slug = document.getElementById('project-slug').value.trim();
      const title = document.getElementById('project-title').value.trim();
      const description = document.getElementById('project-description').value.trim();

      // 表单验证
      if (!slug || !title) {
        alert('请填写必填项');
        return;
      }

      // slug 格式验证
      if (!/^[a-z0-9-]+$/.test(slug)) {
        alert('项目标识只能包含小写字母、数字和横线');
        return;
      }

      try {
        if (originalSlug) {
          // 编辑模式
          await window.ApiClient.callTool('project.update', { 
            workspace, 
            slug: originalSlug, 
            title, 
            description: description || undefined 
          });
        } else {
          // 创建模式
          await window.ApiClient.callTool('project.create', { 
            workspace, 
            slug, 
            title, 
            description: description || undefined 
          });
        }
        
        this.hideModal();
        await this.loadData();
        
        if (window.showToast) {
          window.showToast('success', originalSlug ? '项目已更新' : '项目创建成功');
        }
      } catch (error) {
        console.error('[ProjectManage] Save error:', error);
        alert('保存失败: ' + error.message);
      }
    },

    async deleteProject(slug, name) {
      if (!confirm(`确定删除项目 "${name}" 吗？此操作不可恢复。`)) {
        return;
      }

      const workspace = window.AppState?.currentWorkspace;
      if (!workspace) {
        alert('请先选择工作空间');
        return;
      }

      try {
        await window.ApiClient.callTool('project.delete', { workspace, slug });
        
        // 如果删除的是当前选中的项目，清除选择
        if (window.AppState.currentProject === slug) {
          window.AppState.currentProject = null;
          localStorage.removeItem('novel-project');
          
          if (window.MenuManager?.updateMenuVisibility) {
            window.MenuManager.updateMenuVisibility();
          }
        }
        
        await this.loadData();
        
        if (window.showToast) {
          window.showToast('success', '项目已删除');
        }
      } catch (error) {
        console.error('[ProjectManage] Delete error:', error);
        alert('删除失败: ' + error.message);
      }
    }
  };
})();
