/**
 * Tone Management Page - 基调管理
 */
(function() {
  window.ToneManagementPage = {
    tones: [],

    async init() {
      document.getElementById('content-area').innerHTML = `
        <div class="space-y-4">
          <div class="flex items-center justify-between">
            <h1 class="text-2xl font-bold text-gray-800">🎭 基调管理</h1>
            <button onclick="ToneManagementPage.showToneModal()" class="px-4 py-2 bg-primary-600 text-white rounded-lg hover:bg-primary-700">+ 新增基调</button>
          </div>
          <div id="tone-list" class="space-y-4">加载中...</div>
        </div>`;
      await this.loadTones();
      return true;
    },

    async loadTones() {
      try {
        const res = await window.ApiClient.callTool('tone.list').catch(() => []);
        this.tones = Array.isArray(res) ? res : [];
        const container = document.getElementById('tone-list');
        if (!this.tones.length) {
          container.innerHTML = '<div class="p-8 text-center text-gray-500 bg-white rounded-lg shadow">暂无基调，点击右上角新增</div>';
          return;
        }
        container.innerHTML = this.tones.map(t => `
          <div class="bg-white rounded-lg shadow p-4">
            <div class="flex items-center justify-between">
              <div>
                <h3 class="font-semibold text-gray-800">${t.name} <span class="text-xs text-gray-400">${t.slug}</span></h3>
                <p class="text-sm text-gray-500 mt-1">${t.description || '—'}</p>
                <span class="px-2 py-0.5 text-xs rounded-full ${t.is_active ? 'bg-green-100 text-green-700' : 'bg-gray-100 text-gray-500'}">${t.is_active ? '启用' : '禁用'}</span>
              </div>
              <div class="flex gap-2">
                <button onclick="ToneManagementPage.showRuleModal('${t.slug}')" class="px-3 py-1 text-xs bg-blue-50 text-blue-600 rounded hover:bg-blue-100">管理规则</button>
                <button onclick="ToneManagementPage.showToneModal('${t.slug}','${t.name}','${(t.description||'').replace(/'/g,"\\'")}',${t.is_active},${t.sort_order})" class="px-3 py-1 text-xs bg-gray-100 text-gray-600 rounded hover:bg-gray-200">编辑</button>
                <button onclick="ToneManagementPage.deleteTone('${t.slug}','${t.name}')" class="px-3 py-1 text-xs bg-red-50 text-red-600 rounded hover:bg-red-100">删除</button>
              </div>
            </div>
            ${t.rules && t.rules.length ? `
              <div class="mt-3 pt-3 border-t border-gray-100">
                <p class="text-xs text-gray-500 mb-2">关联规则 (${t.rules.length}条):</p>
                ${t.rules.map(r => `<div class="flex justify-between text-xs py-1"><span class="text-gray-600">[${r.rule_type}] ${r.title}</span><span class="text-gray-400">${r.severity}</span></div>`).join('')}
              </div>
            ` : ''}
          </div>
        `).join('');
      } catch(e) { console.error(e); }
    },

    showToneModal(slug, name, desc, active, order) {
      const isEdit = !!slug;
      ModalDialog.show({
        title: isEdit ? '编辑基调' : '新增基调',
        size: 'md',
        content: `
          <div class="space-y-3">
            <div><label class="block text-sm font-medium">Slug <span class="text-red-500">*</span></label><input id="tone-slug" class="w-full border rounded px-3 py-2" value="${slug||''}" ${isEdit?'readonly':''} placeholder="英文标识，如 hot-blooded"></div>
            <div><label class="block text-sm font-medium">名称 <span class="text-red-500">*</span></label><input id="tone-name" class="w-full border rounded px-3 py-2" value="${name||''}" placeholder="热血爽文"></div>
            <div><label class="block text-sm font-medium">描述</label><textarea id="tone-desc" class="w-full border rounded px-3 py-2" rows="2">${desc||''}</textarea></div>
            <div class="flex gap-4">
              <label class="flex items-center gap-2"><input type="checkbox" id="tone-active" ${active!==false?'checked':''}> 启用</label>
              <div class="flex-1"><label class="block text-sm font-medium">排序</label><input type="number" id="tone-order" class="w-full border rounded px-3 py-2" value="${order||0}"></div>
            </div>
          </div>`,
        onConfirm: async () => {
          const s = document.getElementById('tone-slug').value.trim();
          const n = document.getElementById('tone-name').value.trim();
          if (!s || !n) { alert('Slug和名称必填'); return; }
          await window.ApiClient.callTool('tone.upsert', {
            slug: s, name: n,
            description: document.getElementById('tone-desc')?.value || '',
            is_active: document.getElementById('tone-active').checked,
            sort_order: parseInt(document.getElementById('tone-order').value) || 0
          });
          ModalDialog.close();
          this.loadTones();
        }
      });
    },

    async deleteTone(slug, name) {
      if (!confirm(`确认删除基调「${name}」及其所有关联规则？`)) return;
      await window.ApiClient.callTool('tone.delete', { slug });
      this.loadTones();
    },

    showRuleModal(toneSlug) {
      const tone = this.tones.find(t => t.slug === toneSlug);
      const rules = tone?.rules || [];
      ModalDialog.show({
        title: `管理规则 - ${tone?.name || toneSlug}`,
        size: 'lg',
        content: `
          <div class="space-y-3">
            <div id="rule-list" class="space-y-2 max-h-96 overflow-y-auto">
              ${rules.map(r => `
                <div class="flex items-center justify-between p-2 bg-gray-50 rounded">
                  <div class="flex-1">
                    <span class="font-medium text-sm">[${r.rule_type}] ${r.title}</span>
                    <p class="text-xs text-gray-500">${r.content}</p>
                  </div>
                  <div class="flex gap-1 ml-2">
                    <button onclick="ToneManagementPage.editRule('${toneSlug}','${r.id}','${r.rule_type}','${(r.title||'').replace(/'/g,"\\'")}','${(r.content||'').replace(/'/g,"\\'").replace(/"/g,'&quot;')}','${r.severity}')" class="px-2 py-1 text-xs bg-gray-100 rounded">编辑</button>
                    <button onclick="ToneManagementPage.deleteRule('${r.id}')" class="px-2 py-1 text-xs bg-red-50 text-red-600 rounded">删除</button>
                  </div>
                </div>
              `).join('') || '<p class="text-gray-500 text-sm">暂无规则</p>'}
            </div>
            <button onclick="ToneManagementPage.showRuleForm('${toneSlug}')" class="w-full px-4 py-2 bg-primary-600 text-white rounded-lg">+ 新增规则</button>
          </div>`,
      });
    },

    showRuleForm(toneSlug, id, type, title, content, severity) {
      const isEdit = !!id;
      ModalDialog.show({
        title: isEdit ? '编辑规则' : '新增规则',
        size: 'md',
        content: `
          <div class="space-y-3">
            <div><label class="block text-sm font-medium">类型</label><select id="rule-type" class="w-full border rounded px-3 py-2">
              <option value="style" ${type==='style'?'selected':''}>风格规则</option>
              <option value="forbidden" ${type==='forbidden'?'selected':''}>禁止规则</option>
              <option value="global" ${type==='global'?'selected':''}>全局规则</option>
            </select></div>
            <div><label class="block text-sm font-medium">标题 <span class="text-red-500">*</span></label><input id="rule-title" class="w-full border rounded px-3 py-2" value="${title||''}"></div>
            <div><label class="block text-sm font-medium">内容 <span class="text-red-500">*</span></label><textarea id="rule-content" class="w-full border rounded px-3 py-2" rows="3">${content||''}</textarea></div>
            <div><label class="block text-sm font-medium">级别</label><select id="rule-severity" class="w-full border rounded px-3 py-2">
              <option value="info" ${severity==='info'?'selected':''}>信息</option>
              <option value="warning" ${severity==='warning'?'selected':''}>警告</option>
              <option value="critical" ${severity==='critical'?'selected':''}>严重</option>
            </select></div>
          </div>`,
        onConfirm: async () => {
          const t = document.getElementById('rule-type').value;
          const ti = document.getElementById('rule-title').value.trim();
          const c = document.getElementById('rule-content').value.trim();
          if (!ti || !c) { alert('标题和内容必填'); return; }
          await window.ApiClient.callTool('tone.rule.upsert', {
            tone_slug: toneSlug, rule_type: t, title: ti, content: c,
            severity: document.getElementById('rule-severity').value, rule_id: id || null
          });
          ModalDialog.close();
          this.showRuleModal(toneSlug);
        }
      });
    },

    editRule(slug, id, type, title, content, severity) {
      this.showRuleForm(slug, id, type, title, content, severity);
    },

    async deleteRule(id) {
      if (!confirm('确认删除此规则？')) return;
      // 先记住所属基调，删除后要重新打开它的规则弹窗
      const slug = this.tones.find(t => t.rules?.some(r => r.id === id))?.slug;
      await window.ApiClient.callTool('tone.rule.delete', { rule_id: id });
      // 重新拉取数据，否则 this.tones 仍是旧快照，被删规则会残留在列表里
      await this.loadTones();
      if (slug) this.showRuleModal(slug);
    },
  };
})();