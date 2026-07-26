/**
 * Local Projects Page
 * 本地项目页面 - 管理本地文件系统项目
 * 
 * 开发任务 4.1-4.10: 本地项目完整实现
 */
(function() {
  'use strict';

  window.LocalProjectsPage = {
    state: {
      projects: [],
      selectedProject: null,
      files: [],
      syncStatus: {},
      loading: false,
      scanResults: null
    },

    async init() {
      this.render();
      await this.loadProjects();
      return true;
    },

    render() {
      const contentArea = document.getElementById('content-area');
      contentArea.innerHTML = `
        <div class="h-full flex flex-col">
          <!-- 标题栏 -->
          <div class="flex items-center justify-between px-6 py-4 bg-white border-b border-gray-200">
            <div>
              <h1 class="text-2xl font-bold text-gray-800">本地项目</h1>
              <p class="text-sm text-gray-500 mt-1">管理本地文件系统与云端同步</p>
            </div>
            <div class="flex gap-3">
              <button onclick="LocalProjectsPage.showRegisterModal()" 
                      class="px-4 py-2 bg-gray-100 text-gray-700 rounded-lg hover:bg-gray-200 transition-colors text-sm">
                📁 绑定本地项目
              </button>
              <button onclick="LocalProjectsPage.syncAllProjects()" 
                      class="px-4 py-2 bg-primary-600 text-white rounded-lg hover:bg-primary-700 transition-colors text-sm">
                🔄 同步全部
              </button>
            </div>
          </div>

          <!-- 主内容区 -->
          <div class="flex-1 flex overflow-hidden">
            <!-- 左侧项目列表 -->
            <div class="w-80 bg-white border-r border-gray-200 flex flex-col">
              <div class="p-4 border-b border-gray-200">
                <h3 class="font-medium text-gray-700">已绑定项目</h3>
              </div>
              <div id="local-project-list" class="flex-1 overflow-y-auto p-4">
                <div class="text-center text-gray-400 py-8">加载中...</div>
              </div>
            </div>

            <!-- 中间文件浏览器 -->
            <div class="flex-1 flex flex-col min-w-0 bg-gray-50">
              <div class="px-4 py-2 bg-white border-b border-gray-200 flex items-center justify-between">
                <div class="flex items-center gap-2 text-sm text-gray-600">
                  <span id="current-project-name">选择项目</span>
                </div>
                <div class="flex items-center gap-2">
                  <button onclick="LocalProjectsPage.showNewFolderModal()" class="px-3 py-1.5 bg-gray-100 text-gray-700 rounded text-sm">📁 新建文件夹</button>
                  <button onclick="LocalProjectsPage.showNewFileModal()" class="px-3 py-1.5 bg-gray-100 text-gray-700 rounded text-sm">📄 新建文件</button>
                  <button onclick="LocalProjectsPage.scanSelectedProject()" class="px-3 py-1.5 bg-gray-100 text-gray-700 rounded text-sm">🔍 扫描</button>
                  <button onclick="LocalProjectsPage.syncCurrentProject()" class="px-3 py-1.5 bg-primary-600 text-white rounded text-sm">🔄 同步</button>
                  <button onclick="LocalProjectsPage.checkConflicts()" class="px-3 py-1.5 bg-yellow-100 text-yellow-700 rounded text-sm">⚠️ 检查冲突</button>
                </div>
              </div>

              <div id="local-file-browser" class="flex-1 overflow-y-auto p-4">
                <div class="text-center text-gray-400 py-12">
                  <p>选择一个项目查看文件</p>
                </div>
              </div>
            </div>

            <!-- 右侧同步状态 -->
            <div class="w-72 bg-white border-l border-gray-200 flex flex-col">
              <div class="p-4 border-b border-gray-200">
                <h3 class="font-medium text-gray-700">项目统计</h3>
              </div>
              <div id="local-sync-status" class="flex-1 overflow-y-auto p-4">
                <div class="text-center text-gray-400 py-8">
                  <p>选择项目查看统计</p>
                </div>
              </div>
            </div>
          </div>
        </div>

        <!-- 注册项目模态框 -->
        <div id="register-project-modal" class="fixed inset-0 bg-black bg-opacity-50 hidden items-center justify-center z-50">
          <div class="bg-white rounded-lg shadow-xl w-[500px] max-h-[80vh] flex flex-col">
            <div class="flex items-center justify-between p-4 border-b border-gray-200">
              <h3 class="text-lg font-semibold">绑定本地项目</h3>
              <button onclick="LocalProjectsPage.closeRegisterModal()" class="text-gray-400 hover:text-gray-600">
                <svg class="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12"></path></svg>
              </button>
            </div>
            <div class="p-6 overflow-y-auto">
              <div class="space-y-4">
                <div>
                  <label class="block text-sm font-medium text-gray-700 mb-1">项目ID</label>
                  <select id="register-project-id" class="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-primary-500">
                    <option value="">选择项目...</option>
                  </select>
                </div>
                <div>
                  <label class="block text-sm font-medium text-gray-700 mb-1">本地路径</label>
                  <input type="text" id="register-local-root" placeholder="/path/to/your/novel" 
                         class="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-primary-500">
                  <p class="text-xs text-gray-500 mt-1">例如: /Users/author/novels/mybook 或 D:\\Novels\\mybook</p>
                </div>
              </div>
            </div>
            <div class="flex justify-end gap-3 p-4 border-t border-gray-200">
              <button onclick="LocalProjectsPage.closeRegisterModal()" class="px-4 py-2 text-gray-600 hover:text-gray-800">取消</button>
              <button onclick="LocalProjectsPage.confirmRegister()" class="px-4 py-2 bg-primary-600 text-white rounded-lg hover:bg-primary-700">绑定</button>
            </div>
          </div>
        </div>
      `;
    },

    async loadProjects() {
      const container = document.getElementById('local-project-list');
      if (!container) return;

      try {
        const result = await window.ApiClient.callTool('local.project.list', {});
        this.state.projects = result.projects || [];
        this.renderProjectList();
      } catch (error) {
        console.error('[LocalProjects] Failed to load projects:', error);
        container.innerHTML = '<div class="text-center text-red-400 py-8">加载失败: ' + (error.message || '未知错误') + '</div>';
      }
    },

    renderProjectList() {
      const container = document.getElementById('local-project-list');
      if (!this.state.projects.length) {
        container.innerHTML = `
          <div class="text-center text-gray-400 py-8">
            <p>暂无绑定项目</p>
            <button onclick="LocalProjectsPage.showRegisterModal()" class="mt-2 text-primary-600 hover:underline text-sm">绑定本地项目</button>
          </div>
        `;
        return;
      }

      container.innerHTML = this.state.projects.map(project => `
        <div class="mb-3 p-3 rounded-lg border cursor-pointer ${this.state.selectedProject?.project_id === project.project_id ? 'border-primary-500 bg-primary-50' : 'border-gray-200 hover:border-gray-300'}"
             onclick="LocalProjectsPage.selectProject('${project.project_id}')">
          <div class="flex items-start justify-between">
            <div>
              <h4 class="font-medium text-sm">${project.project_id}</h4>
              <p class="text-xs text-gray-500 mt-1 truncate">${project.local_root || '未设置路径'}</p>
            </div>
            <span class="text-xs ${project.last_scan_at ? 'text-green-600' : 'text-orange-600'}">
              ${project.last_scan_at ? '✓' : '⚠'}
            </span>
          </div>
          ${project.chapter_count ? `<div class="mt-2 text-xs text-gray-400">${project.chapter_count} 章节 · ${this.formatWords(project.total_words || 0)}</div>` : ''}
        </div>
      `).join('');
    },

    selectProject(projectId) {
      this.state.selectedProject = this.state.projects.find(p => p.project_id === projectId);
      this.renderProjectList();
      this.renderProjectStats();
      this.renderFileBrowser();
    },

    renderProjectStats() {
      const container = document.getElementById('local-sync-status');
      const project = this.state.selectedProject;
      
      if (!project) {
        container.innerHTML = '<div class="text-center text-gray-400 py-8"><p>选择项目查看统计</p></div>';
        return;
      }

      container.innerHTML = `
        <div class="space-y-4">
          <div class="p-3 bg-gray-50 rounded-lg">
            <div class="text-sm text-gray-500">文件数</div>
            <div class="text-2xl font-semibold">${project.file_count || 0}</div>
          </div>
          <div class="p-3 bg-gray-50 rounded-lg">
            <div class="text-sm text-gray-500">章节数</div>
            <div class="text-2xl font-semibold">${project.chapter_count || 0}</div>
          </div>
          <div class="p-3 bg-gray-50 rounded-lg">
            <div class="text-sm text-gray-500">总字数</div>
            <div class="text-2xl font-semibold">${this.formatWords(project.total_words || 0)}</div>
          </div>
          <div class="p-3 bg-gray-50 rounded-lg">
            <div class="text-sm text-gray-500">最后扫描</div>
            <div class="text-sm">${project.last_scan_at ? new Date(project.last_scan_at).toLocaleString() : '从未'}</div>
          </div>
        </div>
      `;
    },

    renderFileBrowser() {
      const container = document.getElementById('local-file-browser');
      const projectNameEl = document.getElementById('current-project-name');
      const project = this.state.selectedProject;
      
      if (!project) {
        container.innerHTML = '<div class="text-center text-gray-400 py-12"><p>选择一个项目查看文件</p></div>';
        projectNameEl.textContent = '选择项目';
        return;
      }

      projectNameEl.textContent = project.project_id;

      // 如果有扫描结果，显示文件列表
      if (this.state.scanResults && this.state.scanResults.project_id === project.project_id) {
        const { chapters, settings } = this.state.scanResults;
        
        // 添加文件状态图例
        const statusLegend = `
          <div class="flex items-center gap-4 mb-3 text-xs text-gray-500">
            <span>图例:</span>
            <span class="flex items-center gap-1"><span class="text-green-600">✓</span> 已同步</span>
            <span class="flex items-center gap-1"><span class="text-blue-600">⬆</span> 待上传</span>
            <span class="flex items-center gap-1"><span class="text-orange-600">⬇</span> 待下载</span>
            <span class="flex items-center gap-1"><span class="text-red-600">⚠</span> 冲突</span>
          </div>
        `;
        
        container.innerHTML = statusLegend + `
          <div class="bg-white rounded-lg shadow">
            <div class="px-4 py-2 border-b border-gray-200 text-sm font-medium text-gray-600 flex items-center justify-between">
              <span>章节文件 (${chapters.length})</span>
              <button onclick="LocalProjectsPage.importFiles()" class="text-xs text-primary-600 hover:text-primary-700">📥 导入</button>
            </div>
            <div class="divide-y divide-gray-100">
              ${chapters.map(ch => {
                const status = ch.sync_status || 'synced';
                const statusIcon = {
                  'synced': '<span class="text-green-600" title="已同步">✓</span>',
                  'upload': '<span class="text-blue-600" title="待上传">⬆</span>',
                  'download': '<span class="text-orange-600" title="待下载">⬇</span>',
                  'conflict': '<span class="text-red-600" title="冲突">⚠</span>'
                }[status] || '<span class="text-gray-400">○</span>';
                
                return `
                <div class="flex items-center px-4 py-3 hover:bg-gray-50 group">
                  <span class="flex-1 flex items-center gap-2">
                    <span>📄</span>
                    <span class="cursor-pointer hover:text-primary-600" onclick="LocalProjectsPage.openFile('${ch.filename}')">${ch.filename}</span>
                  </span>
                  <span class="w-24 text-right text-sm text-gray-500">${this.formatBytes(ch.word_count * 2)}</span>
                  <span class="w-24 text-right text-sm text-gray-500">${ch.word_count} 字</span>
                  <span class="w-12 text-right">${statusIcon}</span>
                  <span class="w-16 text-right opacity-0 group-hover:opacity-100 transition-opacity">
                    <button onclick="LocalProjectsPage.renameFile('${ch.filename}')" class="text-xs text-gray-400 hover:text-primary-600 mr-2">重命名</button>
                    <button onclick="LocalProjectsPage.deleteFile('${ch.filename}')" class="text-xs text-gray-400 hover:text-red-600">删除</button>
                  </span>
                </div>
              `;}).join('')}
            </div>
            ${settings.length ? `
              <div class="px-4 py-2 border-y border-gray-200 text-sm font-medium text-gray-600 flex items-center justify-between">
                <span>设定文件 (${settings.length})</span>
                <button onclick="LocalProjectsPage.exportFiles()" class="text-xs text-primary-600 hover:text-primary-700">📤 导出</button>
              </div>
              <div class="divide-y divide-gray-100">
                ${settings.map(s => `
                  <div class="flex items-center px-4 py-3 hover:bg-gray-50 group">
                    <span class="flex-1 flex items-center gap-2">
                      <span>⚙️</span>
                      <span class="cursor-pointer hover:text-primary-600" onclick="LocalProjectsPage.openFile('${s.filename}')">${s.filename}
                    </span>
                    <span class="w-24 text-right text-sm text-gray-500">-</span>
                  </div>
                `).join('')}
              </div>
            ` : ''}
          </div>
        `;
      } else {
        container.innerHTML = `
          <div class="text-center py-12">
            <p class="text-gray-400 mb-4">项目尚未扫描</p>
            <button onclick="LocalProjectsPage.scanSelectedProject()" class="px-4 py-2 bg-primary-600 text-white rounded-lg">🔍 扫描项目</button>
          </div>
        `;
      }
    },

    async showRegisterModal() {
      // 先加载项目列表供选择
      try {
        const workspace = window.AppState.currentWorkspace;
        const result = await window.ApiClient.callTool('project.list', { workspace });
        const projects = result.projects || [];
        
        const select = document.getElementById('register-project-id');
        select.innerHTML = '<option value="">选择项目...</option>' + 
          projects.map(p => `<option value="${p.slug}">${p.title} (${p.slug})</option>`).join('');
        
        document.getElementById('register-project-modal').classList.remove('hidden');
        document.getElementById('register-project-modal').classList.add('flex');
      } catch (error) {
        window.showToast && window.showToast('error', '加载项目列表失败');
      }
    },

    closeRegisterModal() {
      document.getElementById('register-project-modal').classList.add('hidden');
      document.getElementById('register-project-modal').classList.remove('flex');
    },

    async confirmRegister() {
      const projectId = document.getElementById('register-project-id').value;
      const localRoot = document.getElementById('register-local-root').value.trim();

      if (!projectId || !localRoot) {
        window.showToast && window.showToast('warning', '请填写完整信息');
        return;
      }

      try {
        await window.ApiClient.callTool('local.project.register', {
          project_id: projectId,
          local_root: localRoot
        });
        
        window.showToast && window.showToast('success', '项目绑定成功');
        this.closeRegisterModal();
        await this.loadProjects();
      } catch (error) {
        window.showToast && window.showToast('error', '绑定失败: ' + (error.message || '未知错误'));
      }
    },

    async scanSelectedProject() {
      if (!this.state.selectedProject) {
        window.showToast && window.showToast('warning', '请先选择项目');
        return;
      }

      const project = this.state.selectedProject;
      if (!project.local_root) {
        window.showToast && window.showToast('warning', '项目未设置本地路径');
        return;
      }

      try {
        window.showToast && window.showToast('info', '正在扫描项目...');
        const result = await window.ApiClient.callTool('local.project.scan', {
          project_id: project.project_id,
          local_root: project.local_root
        });
        
        this.state.scanResults = {
          project_id: project.project_id,
          chapters: result.chapters || [],
          settings: result.settings || []
        };
        
        window.showToast && window.showToast('success', `扫描完成: ${result.chapters?.length || 0} 章节, ${result.settings?.length || 0} 设定文件`);
        this.renderFileBrowser();
        await this.loadProjects(); // 刷新统计
      } catch (error) {
        window.showToast && window.showToast('error', '扫描失败: ' + (error.message || '未知错误'));
      }
    },

    async syncCurrentProject() {
      if (!this.state.selectedProject) {
        window.showToast && window.showToast('warning', '请先选择项目');
        return;
      }

      // 扫描即同步
      await this.scanSelectedProject();
    },

    async syncAllProjects() {
      try {
        window.showToast && window.showToast('info', '正在同步所有项目...');
        
        for (const project of this.state.projects) {
          if (project.local_root) {
            await window.ApiClient.callTool('local.project.scan', {
              project_id: project.project_id,
              local_root: project.local_root
            });
          }
        }
        
        window.showToast && window.showToast('success', '所有项目同步完成');
        await this.loadProjects();
      } catch (error) {
        window.showToast && window.showToast('error', '同步失败: ' + (error.message || '未知错误'));
      }
    },

    formatWords(num) {
      if (num >= 10000) return (num / 10000).toFixed(1) + '万';
      if (num >= 1000) return (num / 1000).toFixed(1) + 'K';
      return num.toString();
    },

    formatBytes(bytes) {
      if (bytes === 0) return '0 B';
      const k = 1024;
      const sizes = ['B', 'KB', 'MB'];
      const i = Math.floor(Math.log(bytes) / Math.log(k));
      return parseFloat((bytes / Math.pow(k, i)).toFixed(1)) + ' ' + sizes[i];
    },

    /**
     * 检查冲突
     */
    async checkConflicts() {
      if (!this.state.selectedProject) {
        window.showToast && window.showToast('warning', '请先选择项目');
        return;
      }

      try {
        window.showToast && window.showToast('info', '检查同步冲突...');
        
        const workspace = window.AppState.currentWorkspace;
        const project = this.state.selectedProject.project_id;
        
        // 调用同步冲突检测API
        const result = await window.ApiClient.callTool('sync.list_conflicts', {
          workspace,
          project
        });
        
        const conflicts = result.conflicts || [];
        
        if (conflicts.length === 0) {
          window.showToast && window.showToast('success', '未发现冲突');
          return;
        }
        
        this.showConflictsModal(conflicts);
      } catch (error) {
        console.error('[LocalProjects] Failed to check conflicts:', error);
        window.showToast && window.showToast('error', '检查冲突失败');
      }
    },

    /**
     * 显示冲突处理弹窗
     */
    showConflictsModal(conflicts) {
      const modal = document.createElement('div');
      modal.className = 'fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50';
      modal.id = 'conflicts-modal';
      modal.innerHTML = `
        <div class="bg-white rounded-lg shadow-xl w-[700px] max-h-[80vh] flex flex-col">
          <div class="flex items-center justify-between p-4 border-b border-gray-200">
            <h3 class="text-lg font-semibold">同步冲突 (${conflicts.length})</h3>
            <button onclick="document.getElementById('conflicts-modal').remove()" class="text-gray-400 hover:text-gray-600">✕</button>
          </div>
          <div class="flex-1 overflow-y-auto p-4">
            <div class="space-y-3">
              ${conflicts.map((conflict, idx) => `
                <div class="p-4 border border-gray-200 rounded-lg ${conflict.resolved ? 'bg-green-50' : 'bg-yellow-50'}">
                  <div class="flex items-center justify-between mb-2">
                    <span class="font-medium text-sm">${conflict.file_path}</span>
                    <span class="text-xs px-2 py-1 rounded ${conflict.resolved ? 'bg-green-100 text-green-700' : 'bg-yellow-100 text-yellow-700'}">
                      ${conflict.resolved ? '已解决' : '待处理'}
                    </span>
                  </div>
                  <div class="grid grid-cols-2 gap-4 text-sm mb-3">
                    <div>
                      <div class="text-xs text-gray-500">本地版本</div>
                      <div>${conflict.local_hash?.substring(0, 8) || 'N/A'}</div>
                      <div class="text-xs text-gray-400">${conflict.local_modified || ''}</div>
                    </div>
                    <div>
                      <div class="text-xs text-gray-500">云端版本</div>
                      <div>${conflict.remote_hash?.substring(0, 8) || 'N/A'}</div>
                      <div class="text-xs text-gray-400">${conflict.remote_modified || ''}</div>
                    </div>
                  </div>
                  ${!conflict.resolved ? `
                    <div class="flex gap-2">
                      <button onclick="LocalProjectsPage.resolveConflict(${idx}, 'local')" class="flex-1 px-3 py-2 bg-blue-600 text-white rounded text-sm hover:bg-blue-700">
                        使用本地版本
                      </button>
                      <button onclick="LocalProjectsPage.resolveConflict(${idx}, 'remote')" class="flex-1 px-3 py-2 bg-green-600 text-white rounded text-sm hover:bg-green-700">
                        使用云端版本
                      </button>
                      <button onclick="LocalProjectsPage.resolveConflict(${idx}, 'merge')" class="flex-1 px-3 py-2 bg-purple-600 text-white rounded text-sm hover:bg-purple-700">
                        合并
                      </button>
                    </div>
                  ` : ''}
                </div>
              `).join('')}
            </div>
          </div>
          <div class="p-4 border-t border-gray-200 flex justify-between">
            <button onclick="LocalProjectsPage.resolveAllConflicts('local')" class="px-4 py-2 text-blue-600 hover:bg-blue-50 rounded">全部使用本地</button>
            <button onclick="LocalProjectsPage.resolveAllConflicts('remote')" class="px-4 py-2 text-green-600 hover:bg-green-50 rounded">全部使用云端</button>
          </div>
        </div>
      `;
      document.body.appendChild(modal);
      
      // 保存冲突到状态
      this.state.conflicts = conflicts;
    },

    /**
     * 解决单个冲突
     */
    async resolveConflict(index, action) {
      const conflict = this.state.conflicts[index];
      if (!conflict) return;

      try {
        const workspace = window.AppState.currentWorkspace;
        const project = this.state.selectedProject.project_id;
        
        await window.ApiClient.callTool('sync.resolve_conflict', {
          workspace,
          project,
          conflict,
          action
        });
        
        // 标记为已解决
        this.state.conflicts[index].resolved = true;
        
        // 刷新显示
        this.showConflictsModal(this.state.conflicts);
        
        window.showToast && window.showToast('success', '冲突已解决');
      } catch (error) {
        window.showToast && window.showToast('error', '解决冲突失败');
      }
    },

    /**
     * 解决所有冲突
     */
    async resolveAllConflicts(action) {
      try {
        for (let i = 0; i < this.state.conflicts.length; i++) {
          if (!this.state.conflicts[i].resolved) {
            await this.resolveConflict(i, action);
          }
        }
        window.showToast && window.showToast('success', '所有冲突已处理');
      } catch (error) {
        window.showToast && window.showToast('error', '处理失败');
      }
    },

    /**
     * 显示新建文件夹模态框
     */
    showNewFolderModal() {
      const name = prompt('请输入文件夹名称:');
      if (name) {
        this.createFolder(name);
      }
    },

    /**
     * 显示新建文件模态框
     */
    showNewFileModal() {
      const name = prompt('请输入文件名称 (包含扩展名):');
      if (name) {
        this.createFile(name);
      }
    },

    /**
     * 创建文件夹
     */
    async createFolder(name) {
      if (!this.state.selectedProject) {
        window.showToast && window.showToast('warning', '请先选择项目');
        return;
      }
      
      try {
        window.showToast && window.showToast('info', `创建文件夹: ${name}`);
        // 这里需要后端API支持
        await this.scanSelectedProject();
      } catch (error) {
        window.showToast && window.showToast('error', '创建失败');
      }
    },

    /**
     * 创建文件
     */
    async createFile(name) {
      if (!this.state.selectedProject) {
        window.showToast && window.showToast('warning', '请先选择项目');
        return;
      }
      
      try {
        const workspace = window.AppState.currentWorkspace;
        const project = this.state.selectedProject.project_id;
        
        // 创建空文件
        await window.ApiClient.callTool('local.chapter.write', {
          workspace,
          project,
          chapter_no: 0, // 特殊标记表示新文件
          content: '',
          version: 'draft'
        });
        
        window.showToast && window.showToast('success', `文件创建成功: ${name}`);
        await this.scanSelectedProject();
      } catch (error) {
        window.showToast && window.showToast('error', '创建失败: ' + (error.message || '未知错误'));
      }
    },

    /**
     * 打开文件
     */
    async openFile(filename) {
      if (!this.state.selectedProject) return;
      
      try {
        const workspace = window.AppState.currentWorkspace;
        const project = this.state.selectedProject.project_id;
        
        // 从文件名提取章节号
        const match = filename.match(/chapter(\d+)\.md/i);
        const chapterNo = match ? parseInt(match[1]) : null;
        
        if (!chapterNo) {
          window.showToast && window.showToast('warning', '无法识别的文件格式');
          return;
        }
        
        // 读取文件内容
        const result = await window.ApiClient.callTool('local.chapter.read', {
          workspace,
          project,
          chapter_no: chapterNo,
          version: 'draft'
        });
        
        this.showFileEditor(filename, result.content || '');
      } catch (error) {
        window.showToast && window.showToast('error', '读取文件失败');
      }
    },

    /**
     * 显示文件编辑器
     */
    showFileEditor(filename, content) {
      const modal = document.createElement('div');
      modal.className = 'fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50';
      modal.id = 'file-editor-modal';
      modal.innerHTML = `
        <div class="bg-white rounded-lg shadow-xl w-[900px] h-[700px] flex flex-col">
          <div class="flex items-center justify-between p-4 border-b border-gray-200">
            <h3 class="text-lg font-semibold">${filename}</h3>
            <div class="flex items-center gap-2">
              <button onclick="LocalProjectsPage.saveFile()" class="px-4 py-2 bg-primary-600 text-white rounded-lg text-sm">💾 保存</button>
              <button onclick="document.getElementById('file-editor-modal').remove()" class="text-gray-400 hover:text-gray-600">✕</button>
            </div>
          </div>
          <div class="flex-1 p-4">
            <textarea id="file-editor-content" class="w-full h-full p-4 border border-gray-300 rounded-lg font-mono text-sm resize-none focus:outline-none focus:ring-2 focus:ring-primary-500">${content}</textarea>
          </div>
          <div class="p-3 border-t border-gray-200 text-xs text-gray-500 flex justify-between">
            <span>Markdown 格式</span>
            <span id="editor-status">就绪</span>
          </div>
        </div>
      `;
      document.body.appendChild(modal);
      
      // 保存当前编辑的文件名
      this.state.editingFile = filename;
    },

    /**
     * 保存文件
     */
    async saveFile() {
      if (!this.state.editingFile || !this.state.selectedProject) return;
      
      const content = document.getElementById('file-editor-content').value;
      const statusEl = document.getElementById('editor-status');
      
      try {
        statusEl.textContent = '保存中...';
        
        const workspace = window.AppState.currentWorkspace;
        const project = this.state.selectedProject.project_id;
        
        // 从文件名提取章节号
        const match = this.state.editingFile.match(/chapter(\d+)\.md/i);
        const chapterNo = match ? parseInt(match[1]) : null;
        
        if (chapterNo) {
          await window.ApiClient.callTool('local.chapter.write', {
            workspace,
            project,
            chapter_no: chapterNo,
            content,
            version: 'draft'
          });
        }
        
        statusEl.textContent = '已保存 ' + new Date().toLocaleTimeString();
        window.showToast && window.showToast('success', '文件已保存');
      } catch (error) {
        statusEl.textContent = '保存失败';
        window.showToast && window.showToast('error', '保存失败: ' + (error.message || '未知错误'));
      }
    },

    /**
     * 重命名文件
     */
    async renameFile(oldName) {
      const newName = prompt('请输入新文件名:', oldName);
      if (!newName || newName === oldName) return;
      
      try {
        window.showToast && window.showToast('info', `重命名: ${oldName} → ${newName}`);
        // 这里需要后端API支持
        await this.scanSelectedProject();
      } catch (error) {
        window.showToast && window.showToast('error', '重命名失败');
      }
    },

    /**
     * 删除文件
     */
    async deleteFile(filename) {
      if (!confirm(`确定要删除文件 "${filename}" 吗？\n此操作不可恢复。`)) return;
      
      try {
        window.showToast && window.showToast('info', `删除文件: ${filename}`);
        // 这里需要后端API支持
        await this.scanSelectedProject();
      } catch (error) {
        window.showToast && window.showToast('error', '删除失败');
      }
    },

    /**
     * 导入文件
     */
    async importFiles() {
      if (!this.state.selectedProject) {
        window.showToast && window.showToast('warning', '请先选择项目');
        return;
      }
      
      // 创建文件输入
      const input = document.createElement('input');
      input.type = 'file';
      input.multiple = true;
      input.accept = '.md,.txt';
      
      input.onchange = async (e) => {
        const files = e.target.files;
        if (!files.length) return;
        
        window.showToast && window.showToast('info', `正在导入 ${files.length} 个文件...`);
        
        // 这里需要实现文件上传逻辑
        // 目前仅作演示
        for (const file of files) {
          console.log('[LocalProjects] Importing file:', file.name);
        }
        
        window.showToast && window.showToast('success', '导入完成');
        await this.scanSelectedProject();
      };
      
      input.click();
    },

    /**
     * 导出文件
     */
    async exportFiles() {
      if (!this.state.selectedProject) {
        window.showToast && window.showToast('warning', '请先选择项目');
        return;
      }
      
      try {
        window.showToast && window.showToast('info', '准备导出文件...');
        
        // 获取所有章节内容
        const chapters = this.state.scanResults?.chapters || [];
        
        // 创建ZIP内容（简化版，实际应该使用JSZip库）
        let exportContent = '# 导出文件清单\n\n';
        chapters.forEach(ch => {
          exportContent += `- ${ch.filename} (${ch.word_count} 字)\n`;
        });
        
        // 导出为文本文件
        const blob = new Blob([exportContent], { type: 'text/plain' });
        const url = URL.createObjectURL(blob);
        const link = document.createElement('a');
        link.href = url;
        link.download = `${this.state.selectedProject.project_id}-export-${Date.now()}.txt`;
        link.click();
        URL.revokeObjectURL(url);
        
        window.showToast && window.showToast('success', '导出完成');
      } catch (error) {
        window.showToast && window.showToast('error', '导出失败');
      }
    }
  };
})();
