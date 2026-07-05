/**
 * Novel OS - Context Preview Page
 * 上下文预览页面
 */
(function() {
  'use strict';

  window.ContextPreviewPage = {
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
              <h1 class="text-2xl font-bold text-gray-800">${t('nav.contextPreview')}</h1>
              <p class="text-gray-500 mt-1">预览章节生成时的上下文信息</p>
            </div>
            <button onclick="ContextPreviewPage.refresh()" 
                    class="px-4 py-2 bg-primary-600 text-white rounded-lg hover:bg-primary-700 transition-colors">
              ${t('common.refresh')}
            </button>
          </div>

          <div class="grid grid-cols-2 gap-4">
            <div>
              <label class="block text-sm font-medium text-gray-700 mb-1">选择卷</label>
              <select id="ctx-volume" onchange="ContextPreviewPage.loadChapters()" 
                      class="w-full px-4 py-2 border border-gray-300 rounded-lg">
                <option value="">全部</option>
              </select>
            </div>
            <div>
              <label class="block text-sm font-medium text-gray-700 mb-1">选择章节</label>
              <select id="ctx-chapter" onchange="ContextPreviewPage.loadContext()" 
                      class="w-full px-4 py-2 border border-gray-300 rounded-lg">
                <option value="">请选择章节</option>
              </select>
            </div>
          </div>

          <div class="grid grid-cols-3 gap-4">
            <div class="bg-white rounded-lg shadow p-4">
              <h3 class="font-medium text-gray-700 mb-2">📜 章节摘要</h3>
              <div id="ctx-summaries" class="text-sm text-gray-600 max-h-60 overflow-y-auto">
                <p class="text-gray-400">选择章节后显示</p>
              </div>
            </div>
            <div class="bg-white rounded-lg shadow p-4">
              <h3 class="font-medium text-gray-700 mb-2">👥 角色状态</h3>
              <div id="ctx-characters" class="text-sm text-gray-600 max-h-60 overflow-y-auto">
                <p class="text-gray-400">选择章节后显示</p>
              </div>
            </div>
            <div class="bg-white rounded-lg shadow p-4">
              <h3 class="font-medium text-gray-700 mb-2">🌍 世界状态</h3>
              <div id="ctx-world" class="text-sm text-gray-600 max-h-60 overflow-y-auto">
                <p class="text-gray-400">选择章节后显示</p>
              </div>
            </div>
          </div>

          <div class="bg-white rounded-lg shadow p-4">
            <h3 class="font-medium text-gray-700 mb-2">📝 压缩上下文</h3>
            <div id="ctx-compressed" class="text-sm text-gray-600 max-h-80 overflow-y-auto font-mono whitespace-pre-wrap">
              <p class="text-gray-400">选择章节后显示压缩后的上下文内容</p>
            </div>
          </div>
        </div>
      `;
    },

    async loadData() {
      try {
        const workspace = window.AppState.currentWorkspace;
        const project = window.AppState.currentProject;
        
        if (!workspace || !project) return;

        const volumes = await window.ApiClient.volume.list(workspace, project);
        const volumeSelect = document.getElementById('ctx-volume');
        volumeSelect.innerHTML = `<option value="">全部</option>` + 
          (volumes || []).map(v => `<option value="${v.volume_no}">第${v.volume_no}卷 - ${v.title || '未命名'}</option>`).join('');
      } catch (error) {
        console.error('[ContextPreview] Load error:', error);
      }
    },

    async loadChapters() {
      try {
        const workspace = window.AppState.currentWorkspace;
        const project = window.AppState.currentProject;
        const volumeNo = document.getElementById('ctx-volume').value;

        const chapters = await window.ApiClient.localChapter.list(project);
        const chapterSelect = document.getElementById('ctx-chapter');
        
        let filteredChapters = chapters || [];
        if (volumeNo) {
          // 按卷过滤章节
          filteredChapters = filteredChapters.filter(c => c.volume_no == volumeNo);
        }
        
        chapterSelect.innerHTML = `<option value="">请选择章节</option>` + 
          filteredChapters.map(c => `<option value="${c.chapter_no}">第${c.chapter_no}章 - ${c.title || '未命名'}</option>`).join('');
      } catch (error) {
        console.error('[ContextPreview] Load chapters error:', error);
      }
    },

    async loadContext() {
      const chapterNo = document.getElementById('ctx-chapter').value;
      if (!chapterNo) return;

      try {
        const workspace = window.AppState.currentWorkspace;
        const project = window.AppState.currentProject;

        // 加载压缩上下文
        const compressed = await window.ApiClient.contextCompression.getCompressed(project, parseInt(chapterNo));
        
        document.getElementById('ctx-compressed').textContent = compressed ? JSON.stringify(compressed, null, 2) : '暂无数据';
        
        // 加载世界状态
        const worldState = await window.ApiClient.kb.world.get(project, parseInt(chapterNo));
        document.getElementById('ctx-world').innerHTML = worldState ? 
          `<pre class="text-xs">${JSON.stringify(worldState.world_state, null, 2)}</pre>` : '暂无数据';
      } catch (error) {
        console.error('[ContextPreview] Load context error:', error);
      }
    },

    refresh() {
      this.loadData();
    }
  };
})();
