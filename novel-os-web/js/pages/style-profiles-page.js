/**
 * Style Profiles Page
 * 文风档案管理
 */
(function() {
  window.StyleProfilesPage = {
    profiles: [],

    async init() {
      var ca = document.getElementById('content-area');
      ca.innerHTML = '<div class="flex items-center justify-between mb-6"><h1 class="text-2xl font-bold text-gray-800">文风档案</h1><div class="flex gap-2"><button onclick="StyleProfilesPage.showCreateModal()" class="px-4 py-2 bg-primary-600 text-white rounded-lg hover:bg-primary-700 text-sm">+ 新建档案</button><button onclick="StyleProfilesPage.reload()" class="px-4 py-2 bg-gray-100 text-gray-700 rounded-lg hover:bg-gray-200 text-sm">刷新</button></div></div><div id="style-content" class="bg-white rounded-lg shadow"><div class="p-8 text-center text-gray-500">加载中...</div></div>';
      await this.reload();
      return true;
    },

    async reload() {
      var el = document.getElementById('style-content');
      try {
        var ws = window.AppState.currentWorkspace;
        var prj = window.AppState.currentProject;
        if (!ws || !prj) { el.innerHTML = '<div class="p-8 text-center text-gray-500">请先选择一个项目</div>'; return; }
        var pid = window.AppState.currentProjectId || prj;
        var r = await window.ApiClient.callTool('style.get_profile', { workspace: ws, project: prj, project_id: pid, profile_name: 'default' }).catch(function() { return null; });
        this.profiles = r ? (Array.isArray(r) ? r : [r]) : [];
        if (!this.profiles.length) { el.innerHTML = '<div class="p-8 text-center text-gray-500">暂无文风档案</div>'; return; }
        var h = '<div class="overflow-x-auto"><table class="w-full text-sm"><thead class="bg-gray-50"><tr><th class="px-4 py-3 text-left">名称</th><th class="px-4 py-3 text-left">视角</th><th class="px-4 py-3 text-left">时态</th><th class="px-4 py-3 text-left">语调</th></tr></thead><tbody class="divide-y divide-gray-100">';
        for (var i = 0; i < this.profiles.length; i++) {
          var p = this.profiles[i];
          h += '<tr class="hover:bg-gray-50"><td class="px-4 py-3 font-medium">' + (p.profile_name || 'default') + '</td><td class="px-4 py-3">' + (p.narrative_pov || '-') + '</td><td class="px-4 py-3">' + (p.tense || '-') + '</td><td class="px-4 py-3">' + (p.tone || '-') + '</td></tr>';
        }
        h += '</tbody></table></div>';
        el.innerHTML = h;
      } catch(e) { el.innerHTML = '<div class="p-8 text-center text-red-500">加载失败: ' + e.message + '</div>'; }
    },

    showCreateModal() {
      ModalDialog.show({
        title: '新建文风档案',
        content: '<div class="space-y-3"><div><label class="block text-sm font-medium mb-1">档案名</label><input id="sp-name" class="w-full border rounded px-3 py-2" value="default"></div><div><label class="block text-sm font-medium mb-1">视角</label><select id="sp-pov" class="w-full border rounded px-3 py-2"><option value="third_limited">第三人称有限</option><option value="third_omniscient">第三人称全知</option><option value="first_person">第一人称</option></select></div><div><label class="block text-sm font-medium mb-1">时态</label><select id="sp-tense" class="w-full border rounded px-3 py-2"><option value="past">过去时</option><option value="present">现在时</option></select></div><div><label class="block text-sm font-medium mb-1">语调</label><select id="sp-tone" class="w-full border rounded px-3 py-2"><option value="neutral">中性</option><option value="formal">正式</option><option value="casual">随意</option><option value="dramatic">戏剧化</option></select></div></div>',
        onConfirm: async function() {
          var ws = window.AppState.currentWorkspace;
          var prj = window.AppState.currentProject;
          if (!ws || !prj) { alert('请先选择一个项目'); return; }
          var n = document.getElementById('sp-name').value.trim() || 'default';
          var p = document.getElementById('sp-pov').value;
          var t = document.getElementById('sp-tense').value;
          var to = document.getElementById('sp-tone').value;
          await window.ApiClient.callTool('style.create_profile', {
            workspace: window.AppState.currentWorkspace,
            project: window.AppState.currentProject,
            project_id: window.AppState.currentProjectId || window.AppState.currentProject,
            profile_name: n, narrative_pov: p, tense: t, tone: to
          });
          ModalDialog.close();
          await StyleProfilesPage.loadData();
        }
      });
    }
  };
})();