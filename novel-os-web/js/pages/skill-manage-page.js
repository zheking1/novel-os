/**
 * Skill Manager Page
 * CRUD for AI skills
 */
(function() {
  window.SkillManagePage = {
    async init() {
      const contentArea = document.getElementById('content-area');
      contentArea.innerHTML = `
        <div class="flex items-center justify-between mb-6">
          <h1 class="text-2xl font-bold text-gray-800">${window.t('nav.skillManage') || '技能管理'}</h1>
          <button onclick="SkillManagePage.showCreateModal()" class="px-4 py-2 bg-primary-600 text-white rounded-lg hover:bg-primary-700 text-sm">➕ 创建技能</button>
        </div>
        <div id="skill-content" class="bg-white rounded-lg shadow">
          <div class="p-8 text-center text-gray-500">加载中...</div>
        </div>
      `;
      await this.loadData();
      return true;
    },

    async loadData() {
      const container = document.getElementById('skill-content');
      try {
        const result = await window.ApiClient.callTool('skill.list').catch(() => []);
        const skills = Array.isArray(result) ? result : (result?.skills || []);
        if (!skills || skills.length === 0) {
          container.innerHTML = `<div class="p-8 text-center text-gray-500">暂无技能</div>`;
          return;
        }
        container.innerHTML = `
          <div class="divide-y divide-gray-100">
            ${skills.map(s => `
              <div class="p-4 hover:bg-gray-50 flex items-center justify-between">
                <div>
                  <div class="font-medium text-gray-800">${s.name}</div>
                  <div class="text-sm text-gray-500">${s.description || ''}</div>
                  <div class="text-xs text-gray-400 mt-1">步骤: ${(s.steps || []).length} | 触发词: ${(s.trigger_words || []).join(', ') || '无'}</div>
                </div>
                <div class="flex gap-2">
                  <button onclick="SkillManagePage.viewSkill('${s.skill_id || s.id || s.name}')" class="px-3 py-1 bg-gray-100 text-gray-700 rounded text-xs">查看</button>
                  <button onclick="SkillManagePage.deleteSkill('${s.skill_id || s.id || s.name}')" class="px-3 py-1 bg-red-100 text-red-700 rounded text-xs">删除</button>
                </div>
              </div>
            `).join('')}
          </div>`;
      } catch (e) {
        container.innerHTML = `<div class="p-8 text-center text-red-500">加载失败: ${e.message}</div>`;
      }
    },

    async viewSkill(id) {
      try {
        const skill = await window.ApiClient.callTool('skill.get', { skill_id: id });
        window.ModalDialog.show({
          title: skill.name,
          content: `<pre class="text-sm bg-gray-50 p-4 rounded overflow-auto max-h-96">${JSON.stringify(skill, null, 2)}</pre>`,
          showCancel: false, confirmText: '关闭'
        });
      } catch (e) { alert('加载失败: ' + e.message); }
    },

    async deleteSkill(id) {
      if (!confirm('确定删除此技能？')) return;
      try {
        await window.ApiClient.callTool('skill.delete', { skill_id: id });
        await this.loadData();
      } catch (e) { alert('删除失败: ' + e.message); }
    },

    showCreateModal() {
      window.ModalDialog.show({
        title: '创建技能',
        content: `
          <div class="space-y-4">
            <div><label class="block text-sm font-medium mb-1">名称</label><input id="skill-name" class="w-full border rounded px-3 py-2" /></div>
            <div><label class="block text-sm font-medium mb-1">描述</label><textarea id="skill-desc" class="w-full border rounded px-3 py-2" rows="3"></textarea></div>
            <div><label class="block text-sm font-medium mb-1">触发词 (逗号分隔)</label><input id="skill-triggers" class="w-full border rounded px-3 py-2" /></div>
          </div>`,
        onConfirm: async () => {
          const name = document.getElementById('skill-name').value;
          const description = document.getElementById('skill-desc').value;
          const trigger_words = document.getElementById('skill-triggers').value.split(',').map(s => s.trim()).filter(Boolean);
          if (!name) { alert('名称不能为空'); return false; }
          await window.ApiClient.callTool('skill.create', { name, description, trigger_words });
          await this.loadData();
        }
      });
    }
  };
})();
