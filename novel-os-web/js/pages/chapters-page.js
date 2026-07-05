/**
 * Novel OS - Chapters Page
 * 章节管理页面
 */
(function() {
  'use strict';

  window.ChaptersPage = {
    init() {
      this.render();
      this.loadData();
      return true;
    },

    render() {
      const contentArea = document.getElementById('content-area');
      contentArea.innerHTML = `
        <div class="space-y-4">
          <div class="flex items-center justify-between">
            <div>
              <h1 class="text-2xl font-bold text-gray-800">${t('nav.chapters')}</h1>
              <p class="text-gray-500 mt-1">管理小说章节</p>
            </div>
            <button onclick="ChaptersPage.showCreateModal()" 
                    class="px-4 py-2 bg-primary-600 text-white rounded-lg hover:bg-primary-700 transition-colors">
              ${t('common.new')} 章节
            </button>
          </div>

          <div class="flex gap-4 items-center">
            <input type="text" id="chapter-search" placeholder="${t('common.search')}..." 
                   class="flex-1 px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary-500">
            <select id="chapter-status-filter" onchange="ChaptersPage.loadData()" 
                    class="px-4 py-2 border border-gray-300 rounded-lg">
              <option value="">全部状态</option>
              <option value="draft">草稿</option>
              <option value="final">定稿</option>
              <option value="published">已发布</option>
            </select>
          </div>

          <div id="chapters-list-container" class="bg-white rounded-lg shadow">
            <div class="p-8 text-center text-gray-500">
              <div class="spinner w-8 h-8 border-4 border-primary-600 border-t-transparent rounded-full animate-spin mx-auto"></div>
              <p class="mt-2">${t('common.loading')}</p>
            </div>
          </div>
        </div>

        <!-- 创建/编辑章节模态框 -->
        <div id="chapter-modal" class="fixed inset-0 bg-black/50 z-50 hidden flex items-center justify-center">
          <div class="bg-white rounded-lg shadow-xl w-full max-w-2xl mx-4 max-h-[90vh] overflow-hidden">
            <div class="px-6 py-4 border-b border-gray-200 flex items-center justify-between">
              <h3 id="chapter-modal-title" class="text-lg font-semibold">新建章节</h3>
              <button onclick="ChaptersPage.hideModal()" class="text-gray-400 hover:text-gray-600">
                <svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12"/>
                </svg>
              </button>
            </div>
            <div class="p-6 overflow-y-auto max-h-[60vh]">
              <form id="chapter-form" onsubmit="ChaptersPage.saveChapter(event)">
                <input type="hidden" id="chapter-id">
                <div class="space-y-4">
                  <div class="grid grid-cols-2 gap-4">
                    <div>
                      <label class="block text-sm font-medium text-gray-700 mb-1">章节号 <span class="text-red-500">*</span></label>
                      <input type="number" id="chapter-number" required min="1"
                             class="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary-500">
                    </div>
                    <div>
                      <label class="block text-sm font-medium text-gray-700 mb-1">标题</label>
                      <input type="text" id="chapter-title"
                             class="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary-500">
                    </div>
                  </div>
                  <div class="grid grid-cols-2 gap-4">
                    <div>
                      <label class="block text-sm font-medium text-gray-700 mb-1">状态</label>
                      <select id="chapter-status" 
                              class="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary-500">
                        <option value="draft">草稿</option>
                        <option value="final">定稿</option>
                        <option value="published">已发布</option>
                      </select>
                    </div>
                    <div>
                      <label class="block text-sm font-medium text-gray-700 mb-1">卷号</label>
                      <input type="number" id="chapter-volume" min="1"
                             class="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary-500">
                    </div>
                  </div>
                  <div>
                    <label class="block text-sm font-medium text-gray-700 mb-1">摘要</label>
                    <textarea id="chapter-summary" rows="3"
                              class="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary-500"></textarea>
                  </div>
                  <div>
                    <label class="block text-sm font-medium text-gray-700 mb-1">正文内容</label>
                    <textarea id="chapter-content" rows="12"
                              class="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary-500 font-mono text-sm"></textarea>
                  </div>
                </div>
                <div class="mt-6 flex justify-end gap-3">
                  <button type="button" onclick="ChaptersPage.hideModal()" 
                          class="px-4 py-2 border border-gray-300 rounded-lg hover:bg-gray-50">
                    ${t('common.cancel')}
                  </button>
                  <button type="submit" 
                          class="px-4 py-2 bg-primary-600 text-white rounded-lg hover:bg-primary-700">
                    ${t('common.save')}
                  </button>
                </div>
              </form>
            </div>
          </div>
        </div>
      `;
    },

    async loadData() {
      const container = document.getElementById('chapters-list-container');
      try {
        const workspace = window.AppState.currentWorkspace;
        const project = window.AppState.currentProject;
        
        if (!workspace || !project) {
          container.innerHTML = `<div class="p-8 text-center text-gray-500">请先选择工作区和项目</div>`;
          return;
        }

        const result = await window.ApiClient.localChapter.list(project);
        this.renderList(result || []);
      } catch (error) {
        console.error('[Chapters] Load error:', error);
        container.innerHTML = `<div class="p-8 text-center text-red-500">加载失败: ${error.message}</div>`;
      }
    },

    renderList(chapters) {
      const container = document.getElementById('chapters-list-container');
      
      if (!chapters || chapters.length === 0) {
        container.innerHTML = `
          <div class="p-8 text-center text-gray-500">
            <div class="text-4xl mb-2">📝</div>
            <p>暂无章节</p>
            <p class="text-sm mt-2">点击右上角按钮创建第一个章节</p>
          </div>
        `;
        return;
      }

      container.innerHTML = `
        <div class="divide-y divide-gray-200">
          ${chapters.map(ch => `
            <div class="p-4 hover:bg-gray-50 transition-colors">
              <div class="flex items-start justify-between">
                <div class="flex-1 min-w-0">
                  <div class="flex items-center gap-2">
                    <span class="px-2 py-0.5 text-xs rounded-full bg-primary-100 text-primary-700 font-medium">第${ch.chapter_no}章</span>
                    <h3 class="font-medium text-gray-800 truncate">${ch.title || '未命名'}</h3>
                    <span class="px-2 py-0.5 text-xs rounded-full ${this.getStatusClass(ch.status)}">
                      ${ch.status}
                    </span>
                  </div>
                  ${ch.summary ? `<p class="text-sm text-gray-500 mt-1 line-clamp-2">${ch.summary}</p>` : ''}
                  <div class="flex items-center gap-4 mt-2 text-xs text-gray-400">
                    <span>字数: ${ch.word_count || 0}</span>
                    ${ch.volume_no ? `<span>卷: ${ch.volume_no}</span>` : ''}
                  </div>
                </div>
                <div class="flex items-center gap-2 ml-4">
                  <button onclick="ChaptersPage.editChapter('${ch.chapter_no}')" 
                          class="p-2 text-gray-400 hover:text-primary-600 hover:bg-primary-50 rounded transition-colors"
                          title="编辑">
                    <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M11 5H6a2 2 0 00-2 2v11a2 2 0 002 2h11a2 2 0 002-2v-5m-1.414-9.414a2 2 0 112.828 2.828L11.828 15H9v-2.828l8.586-8.586z"/>
                    </svg>
                  </button>
                  <button onclick="ChaptersPage.viewChapter(${ch.chapter_no})" 
                          class="p-2 text-gray-400 hover:text-green-600 hover:bg-green-50 rounded transition-colors"
                          title="查看">
                    <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M15 12a3 3 0 11-6 0 3 3 0 016 0z"/>
                      <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M2.458 12C3.732 7.943 7.523 5 12 5c4.478 0 8.268 2.943 9.542 7-1.274 4.057-5.064 7-9.542 7-4.477 0-8.268-2.943-9.542-7z"/>
                    </svg>
                  </button>
                </div>
              </div>
            </div>
          `).join('')}
        </div>
      `;
    },

    showCreateModal() {
      document.getElementById('chapter-modal-title').textContent = '新建章节';
      document.getElementById('chapter-id').value = '';
      document.getElementById('chapter-number').value = '';
      document.getElementById('chapter-title').value = '';
      document.getElementById('chapter-status').value = 'draft';
      document.getElementById('chapter-volume').value = '';
      document.getElementById('chapter-summary').value = '';
      document.getElementById('chapter-content').value = '';
      document.getElementById('chapter-modal').classList.remove('hidden');
    },

    hideModal() {
      document.getElementById('chapter-modal').classList.add('hidden');
    },

    async editChapter(chapterNo) {
      try {
        const project = window.AppState.currentProject;
        const chapter = await window.ApiClient.localChapter.read(project, chapterNo);
        
        document.getElementById('chapter-modal-title').textContent = '编辑章节';
        document.getElementById('chapter-number').value = chapter.chapter_no;
        document.getElementById('chapter-title').value = chapter.title || '';
        document.getElementById('chapter-status').value = chapter.status || 'draft';
        document.getElementById('chapter-volume').value = chapter.volume_no || '';
        document.getElementById('chapter-summary').value = chapter.summary || '';
        document.getElementById('chapter-content').value = chapter.content || '';
        document.getElementById('chapter-modal').classList.remove('hidden');
      } catch (error) {
        alert('加载章节失败: ' + error.message);
      }
    },

    async viewChapter(chapterNo) {
      try {
        const project = window.AppState.currentProject;
        const content = await window.ApiClient.localChapter.read(project, chapterNo);
        
        const container = document.getElementById('chapters-list-container');
        container.innerHTML = `
          <div class="p-4 border-b border-gray-200">
            <div class="flex items-center justify-between">
              <h3 class="font-medium text-gray-800">第${chapterNo}章</h3>
              <button onclick="ChaptersPage.loadData()" class="text-sm text-primary-600 hover:underline">返回列表</button>
            </div>
          </div>
          <div class="p-6 prose max-w-none">
            <pre class="whitespace-pre-wrap text-sm">${content || '暂无内容'}</pre>
          </div>
        `;
      } catch (error) {
        alert('加载失败: ' + error.message);
      }
    },

    async saveChapter(e) {
      e.preventDefault();
      const project = window.AppState.currentProject;
      const chapterNo = document.getElementById('chapter-number').value;
      
      const data = {
        title: document.getElementById('chapter-title').value,
        status: document.getElementById('chapter-status').value,
        volume_no: document.getElementById('chapter-volume').value ? parseInt(document.getElementById('chapter-volume').value) : undefined,
        summary: document.getElementById('chapter-summary').value || undefined,
        content: document.getElementById('chapter-content').value
      };

      try {
        await window.ApiClient.localChapter.write(project, parseInt(chapterNo), data.content);
        this.hideModal();
        this.loadData();
      } catch (error) {
        alert('保存失败: ' + error.message);
      }
    },

    getStatusClass(status) {
      const classes = {
        draft: 'bg-yellow-100 text-yellow-700',
        final: 'bg-green-100 text-green-700',
        published: 'bg-purple-100 text-purple-700'
      };
      return classes[status] || 'bg-gray-100 text-gray-600';
    }
  };
})();
