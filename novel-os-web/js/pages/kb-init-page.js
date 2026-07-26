/**
 * KB Init Page
 * 知识初始化 - 为项目批量初始化知识库
 */
(function() {
  window.KbInitPage = {
    async init() {
      const contentArea = document.getElementById('content-area');
      contentArea.innerHTML = `
        <div class="flex items-center justify-between mb-6">
          <h1 class="text-2xl font-bold text-gray-800">${window.t('nav.kbInit') || '知识初始化'}</h1>
        </div>
        <div class="grid grid-cols-1 md:grid-cols-2 gap-6">
          <div class="bg-white rounded-lg shadow p-6">
            <h3 class="font-semibold mb-4">📦 知识包初始化</h3>
            <div class="space-y-3">
              <div><label class="block text-sm font-medium mb-1">选择题材</label><select id="init-genre" class="w-full border rounded px-3 py-2"></select></div>
              <button onclick="KbInitPage.initPack()" class="w-full px-4 py-2 bg-primary-600 text-white rounded-lg">创建知识包</button>
            </div>
          </div>
          <div class="bg-white rounded-lg shadow p-6">
            <h3 class="font-semibold mb-4">🔥 知识预加载</h3>
            <p class="text-sm text-gray-600 mb-4">将选定题材的通用知识预加载到当前项目</p>
            <button onclick="KbInitPage.preheat()" class="w-full px-4 py-2 bg-orange-600 text-white rounded-lg">预加载知识</button>
          </div>
          <div class="bg-white rounded-lg shadow p-6">
            <h3 class="font-semibold mb-4">📋 检测知识缺口</h3>
            <p class="text-sm text-gray-600 mb-4">基于当前章节大纲检测缺失的知识条目</p>
            <div><label class="block text-sm font-medium mb-1">章节号</label><input type="number" id="gap-chapter" class="w-full border rounded px-3 py-2 mb-3" /></div>
            <button onclick="KbInitPage.detectGaps()" class="w-full px-4 py-2 bg-green-600 text-white rounded-lg">检测缺口</button>
          </div>
          <div class="bg-white rounded-lg shadow p-6">
            <h3 class="font-semibold mb-4">📖 项目知识包信息</h3>
            <div id="pack-info" class="text-sm text-gray-600">加载中...</div>
          </div>
        </div>`;
      await this.loadGenres();
      await this.loadPackInfo();
      return true;
    },

    async loadGenres() {
      const sel = document.getElementById('init-genre');
      try {
        const r = await window.ApiClient.callTool('kb.genre.list');
        const genres = Array.isArray(r) ? r : (r?.result || []);
        sel.innerHTML = genres.map(g => `<option value="${g.id||g.slug}">${g.name||g.id}</option>`).join('');
      } catch(e) { sel.innerHTML = '<option>加载失败</option>'; }
    },

    async loadPackInfo() {
      try {
        const pid = window.AppState.currentProjectId || window.AppState.currentProject;
        if (!pid) { document.getElementById('pack-info').textContent = '请先选择项目'; return; }
        const r = await window.ApiClient.callTool('kb.pack.get', { workspace: window.AppState.currentWorkspace, project: window.AppState.currentProject });
        const info = r?.active_categories || r?.result?.active_categories || [];
        document.getElementById('pack-info').innerHTML = info.length ? info.map(c => `<span class="px-2 py-1 bg-blue-100 text-blue-700 rounded text-xs mr-1">${c}</span>`).join('') : '未配置知识包';
      } catch(e) { document.getElementById('pack-info').textContent = '加载失败'; }
    },

    async initPack() {
      const genre = document.getElementById('init-genre').value;
      const pid = window.AppState.currentProjectId || window.AppState.currentProject;
      if (!pid) { ModalDialog.alert('请先选择项目'); return; }
      try {
        await window.ApiClient.callTool('kb.pack.create', { workspace: window.AppState.currentWorkspace, project: window.AppState.currentProject, genre });
        ModalDialog.alert('知识包创建成功');
        this.loadPackInfo();
      } catch(e) { ModalDialog.alert('失败: ' + e.message); }
    },

    async preheat() {
      const genre = document.getElementById('init-genre').value;
      const pid = window.AppState.currentProjectId || window.AppState.currentProject;
      if (!pid) { ModalDialog.alert('请先选择项目'); return; }
      try {
        await window.ApiClient.callTool('kb.genre.preheat', { workspace: window.AppState.currentWorkspace, project: window.AppState.currentProject, genre });
        ModalDialog.alert('预加载成功');
      } catch(e) { ModalDialog.alert('失败: ' + e.message); }
    },

    async detectGaps() {
      const ch = parseInt(document.getElementById('gap-chapter').value);
      if (!ch) { ModalDialog.alert('请输入章节号'); return; }
      const pid = window.AppState.currentProjectId || window.AppState.currentProject;
      try {
        const r = await window.ApiClient.callTool('kb.gap.detect', { workspace: window.AppState.currentWorkspace, project: window.AppState.currentProject, chapter_no: ch });
        ModalDialog.alert('检测完成，请查看知识缺口列表');
      } catch(e) { ModalDialog.alert('失败: ' + e.message); }
    },

    loadData() {}
  };
})();