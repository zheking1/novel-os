/**
 * Arc Characters Page
 * 角色弧光追踪 - 追踪角色的成长、情感和关系变化
 */
(function() {
  window.ArcCharactersPage = {
    currentCharacter: null,

    async init() {
      const contentArea = document.getElementById('content-area');
      contentArea.innerHTML = `
        <div class="flex items-center justify-between mb-6">
          <h1 class="text-2xl font-bold text-gray-800">${window.t('nav.arcCharacters') || '角色弧光'}</h1>
          <div class="flex gap-2">
            <select id="character-selector" class="border rounded px-3 py-2 text-sm" onchange="ArcCharactersPage.onCharacterChange(this.value)">
              <option value="">选择角色...</option>
            </select>
            <button onclick="ArcCharactersPage.showRecordModal()" id="record-btn" class="px-4 py-2 bg-primary-600 text-white rounded-lg hover:bg-primary-700 text-sm" disabled>➕ 记录弧光点</button>
            <button onclick="ArcCharactersPage.loadData()" class="px-4 py-2 bg-gray-100 text-gray-700 rounded-lg hover:bg-gray-200 text-sm">🔄 刷新</button>
          </div>
        </div>
        <div id="arc-content">
          <div class="p-8 text-center text-gray-500 bg-white rounded-lg shadow">请先选择角色</div>
        </div>
      `;
      await this.loadCharacters();
      return true;
    },

    async loadCharacters() {
      try {
        const workspace = window.AppState.currentWorkspace || '';
        const project = window.AppState.currentProject || '';
        const result = await window.ApiClient.callTool('state.entity.list', {
          workspace,
          project,
          entity_type: 'character',
          limit: 100
        }).catch(() => []);
        const characters = Array.isArray(result) ? result : (result?.entities || result?.result || []);
        const selector = document.getElementById('character-selector');
        if (selector && characters.length > 0) {
          selector.innerHTML = '<option value="">选择角色...</option>' +
            characters.map(c => `<option value="${c.name}">${c.name}</option>`).join('');
        }
      } catch (e) {
        console.error('加载角色失败:', e);
      }
    },

    async onCharacterChange(characterName) {
      this.currentCharacter = characterName;
      document.getElementById('record-btn').disabled = !characterName;
      if (characterName) {
        await this.loadArcData();
      } else {
        document.getElementById('arc-content').innerHTML = '<div class="p-8 text-center text-gray-500 bg-white rounded-lg shadow">请先选择角色</div>';
      }
    },

    async loadArcData() {
      const container = document.getElementById('arc-content');
      if (!this.currentCharacter) return;

      container.innerHTML = '<div class="p-8 text-center text-gray-500 bg-white rounded-lg shadow">加载中...</div>';

      try {
        const workspace = window.AppState.currentWorkspace || '';
        const project = window.AppState.currentProject || '';
        const projectId = window.AppState.currentProjectId || project;

        // Load arc data
        const [latestState, rawTimeline, rawPower, relationships] = await Promise.all([
          window.ApiClient.callTool('arc.get_latest_state', { workspace, project, project_id: projectId, character_name: this.currentCharacter }).catch(() => null),
          window.ApiClient.callTool('arc.get_emotion_timeline', { workspace, project, project_id: projectId, character_name: this.currentCharacter }).catch(() => []),
          window.ApiClient.callTool('arc.get_power_progression', { workspace, project, project_id: projectId, character_name: this.currentCharacter }).catch(() => []),
          window.ApiClient.callTool('arc.get_relationship_evolution', { workspace, project, project_id: projectId, character_name: this.currentCharacter }).catch(() => [])
        ]);
        const emotionTimeline = Array.isArray(rawTimeline) ? rawTimeline : (rawTimeline?.timeline || []);
        const powerProgression = Array.isArray(rawPower) ? rawPower : (rawPower?.progression || []);
        const relationshipEvolution = Array.isArray(relationships) ? relationships : (relationships?.evolution || []);

        container.innerHTML = `
          <div class="grid grid-cols-1 lg:grid-cols-2 gap-6">
            <!-- 当前状态 -->
            <div class="bg-white rounded-lg shadow p-6">
              <h3 class="text-lg font-semibold mb-4">📊 当前状态</h3>
              <div class="max-h-60 overflow-y-auto">
                ${this.renderLatestState(latestState)}
              </div>
            </div>

            <!-- 情感时间线 -->
            <div class="bg-white rounded-lg shadow p-6">
              <h3 class="text-lg font-semibold mb-4">😊 情感变化</h3>
              ${this.renderEmotionTimeline(emotionTimeline)}
            </div>

            <!-- 实力成长 -->
            <div class="bg-white rounded-lg shadow p-6">
              <h3 class="text-lg font-semibold mb-4">⚡ 实力成长</h3>
              ${this.renderPowerProgression(powerProgression)}
            </div>

            <!-- 关系演变 -->
            <div class="bg-white rounded-lg shadow p-6">
              <h3 class="text-lg font-semibold mb-4">🤝 关系演变</h3>
              ${this.renderRelationships(relationshipEvolution)}
            </div>
          </div>
        `;
      } catch (e) {
        container.innerHTML = `<div class="p-8 text-center text-red-500 bg-white rounded-lg shadow">加载失败: ${e.message}</div>`;
      }
    },

    renderLatestState(state) {
      if (!state || Object.keys(state).length === 0) {
        return '<p class="text-gray-500">暂无状态数据</p>';
      }
      // arc.get_latest_state 返回 {character, arc_state: {emotion:{...}, power:{...}}}
      const arcState = state.arc_state || state;
      if (Object.keys(arcState).length === 0) {
        return '<p class="text-gray-500">暂无状态数据（通过 arc.record_* 记录后显示）</p>';
      }
      const labels = { emotion: '😊 情感', power: '⚡ 实力', relationship: '🤝 关系', personality: '🧠 性格' };
      return `
        <div class="space-y-3 text-sm">
          ${Object.entries(arcState).map(([type, data]) => {
            const dataState = typeof data.state === 'string' ? (JSON.parse(data.state) || {}) : (data.state || {});
            return `
            <div class="p-2 bg-gray-50 rounded">
              <div class="font-medium text-gray-700">${labels[type] || type}</div>
              <div class="text-xs text-gray-500 mt-1">第${data.chapter_no || '?'}章</div>
              ${data.change_summary ? `<div class="text-xs text-gray-600 mt-1">${data.change_summary}</div>` : ''}
              ${Object.keys(dataState).length ? `<div class="text-xs text-gray-400 mt-1">${Object.entries(dataState).map(([k, v]) => `${k}: ${v}`).join(' | ')}</div>` : ''}
            </div>
          `;}).join('')}
        </div>
      `;
    },

    renderEmotionTimeline(timeline) {
      if (!timeline || timeline.length === 0) {
        return '<p class="text-gray-500">暂无情感数据</p>';
      }
      return `
        <div class="space-y-2 max-h-64 overflow-y-auto">
          ${timeline.map(item => {
            const s = typeof item.state === 'string' ? (JSON.parse(item.state) || {}) : (item.state || {});
            const emotion = s.emotion || item.emotion || '?';
            const intensity = s.intensity !== undefined ? s.intensity : item.intensity;
            return `
            <div class="flex items-center gap-3 p-2 bg-gray-50 rounded">
              <span class="text-xs text-gray-500">第${item.chapter_no}章</span>
              <span class="font-medium">${emotion}</span>
              <span class="text-xs text-gray-400">强度: ${intensity}/1</span>
              ${item.change_summary ? `<span class="text-xs text-gray-500">${item.change_summary}</span>` : ''}
            </div>
          `;
          }).join('')}
        </div>
      `;
    },

    renderPowerProgression(progression) {
      if (!progression || progression.length === 0) {
        return '<p class="text-gray-500">暂无实力数据</p>';
      }
      return `
        <div class="space-y-2 max-h-64 overflow-y-auto">
          ${progression.map(item => {
            const s = typeof item.state === 'string' ? (JSON.parse(item.state) || {}) : (item.state || {});
            const oldLvl = s.old_level || item.old_level || '无';
            const newLvl = s.new_level || item.new_level || '无';
            const method = s.method || item.method;
            return `
            <div class="flex items-center gap-3 p-2 bg-gray-50 rounded">
              <span class="text-xs text-gray-500">第${item.chapter_no}章</span>
              <span class="text-xs text-gray-400">${oldLvl}</span>
              <span class="text-gray-400">→</span>
              <span class="font-medium text-green-600">${newLvl}</span>
              ${method ? `<span class="text-xs text-gray-400">(${method})</span>` : ''}
            </div>
          `;}).join('')}
        </div>
      `;
    },

    renderRelationships(relationships) {
      if (!relationships || relationships.length === 0) {
        return '<p class="text-gray-500">暂无关系数据</p>';
      }
      return `
        <div class="space-y-2 max-h-64 overflow-y-auto">
          ${relationships.map(item => {
            const s = typeof item.state === 'string' ? (JSON.parse(item.state) || {}) : (item.state || {});
            const target = s.target_name || s.target || item.target_name || item.target || '?';
            const oldRel = s.old_relation || item.old_relation || '无';
            const newRel = s.new_relation || item.new_relation || '无';
            return `
            <div class="flex items-center gap-3 p-2 bg-gray-50 rounded">
              <span class="font-medium">${target}</span>
              <span class="text-xs text-gray-400">${oldRel}</span>
              <span class="text-gray-400">→</span>
              <span class="font-medium text-blue-600">${newRel}</span>
              <span class="text-xs text-gray-500">第${item.chapter_no}章</span>
            </div>
          `;}).join('')}
        </div>
      `;
    },

    showRecordModal() {
      if (!this.currentCharacter) { alert('请先选择角色'); return; }

      ModalDialog.show({
        title: `记录弧光点: ${this.currentCharacter}`,
        size: 'lg',
        content: `
          <div class="space-y-4">
            <div>
              <label class="block text-sm font-medium mb-1">章节号 <span class="text-red-500">*</span></label>
              <input type="number" id="arc-chapter" class="w-full border rounded px-3 py-2" placeholder="例如: 15" />
            </div>
            <div>
              <label class="block text-sm font-medium mb-1">弧光类型 <span class="text-red-500">*</span></label>
              <select id="arc-type" class="w-full border rounded px-3 py-2" onchange="ArcCharactersPage.onArcTypeChange(this.value)">
                <option value="emotion">😊 情感变化</option>
                <option value="power">⚡ 实力成长</option>
                <option value="relationship">🤝 关系演变</option>
                <option value="personality">🧠 性格特质</option>
              </select>
            </div>
            <div id="arc-fields">
              <!-- 动态字段 -->
            </div>
          </div>`,
        onConfirm: async () => {
          const chapterNo = parseInt(document.getElementById('arc-chapter').value);
          const arcType = document.getElementById('arc-type').value;
          if (!chapterNo) { alert('请输入章节号'); return; }

          try {
            const projectId = window.AppState.currentProjectId || window.AppState.currentProject || '';
            
            if (arcType === 'emotion') {
              const emotion = document.getElementById('emotion-value').value.trim();
              const intensity = parseInt(document.getElementById('emotion-intensity').value);
              const cause = document.getElementById('emotion-cause').value.trim();
              if (!emotion) { alert('请输入情感类型'); return; }
              await window.ApiClient.callTool('arc.record_emotion', {
                workspace,
                project,
                character_name: this.currentCharacter,
                chapter_no: chapterNo,
                emotion,
                intensity,
                cause
              });
            } else if (arcType === 'power') {
              const newLevel = document.getElementById('power-new').value.trim();
              const oldLevel = document.getElementById('power-old').value.trim();
              const method = document.getElementById('power-method').value.trim();
              if (!newLevel) { alert('请输入新等级'); return; }
              await window.ApiClient.callTool('arc.record_power', {
                workspace,
                project,
                character_name: this.currentCharacter,
                chapter_no: chapterNo,
                new_level: newLevel,
                old_level: oldLevel || undefined,
                method: method || undefined
              });
            } else if (arcType === 'relationship') {
              const targetName = document.getElementById('rel-target').value.trim();
              const newRelation = document.getElementById('rel-new').value.trim();
              const oldRelation = document.getElementById('rel-old').value.trim();
              const cause = document.getElementById('rel-cause').value.trim();
              if (!targetName || !newRelation) { alert('请输入目标角色和新关系'); return; }
              await window.ApiClient.callTool('arc.record_relationship', {
                workspace,
                project,
                character_name: this.currentCharacter,
                chapter_no: chapterNo,
                target_name: targetName,
                new_relation: newRelation,
                old_relation: oldRelation || undefined,
                cause: cause || undefined
              });
            } else if (arcType === 'personality') {
              const trait = document.getElementById('pers-trait').value.trim();
              const newValue = document.getElementById('pers-new').value.trim();
              const oldValue = document.getElementById('pers-old').value.trim();
              const reason = document.getElementById('pers-reason').value.trim();
              if (!trait || !newValue) { alert('请输入特质和新值'); return; }
              await window.ApiClient.callTool('arc.record_personality', {
                workspace,
                project,
                character_name: this.currentCharacter,
                chapter_no: chapterNo,
                trait,
                new_value: newValue,
                old_value: oldValue || undefined,
                reason: reason || undefined
              });
            }

            ModalDialog.close();
            alert('弧光点记录成功');
            await this.loadArcData();
          } catch (e) { alert('记录失败: ' + e.message); }
        }
      });

      // Initialize fields
      this.onArcTypeChange('emotion');
    },

    onArcTypeChange(type) {
      const fieldsContainer = document.getElementById('arc-fields');
      if (!fieldsContainer) return;

      if (type === 'emotion') {
        fieldsContainer.innerHTML = `
          <div><label class="block text-sm font-medium mb-1">情感类型 <span class="text-red-500">*</span></label><input id="emotion-value" class="w-full border rounded px-3 py-2" placeholder="例如: 愤怒、喜悦、悲伤" /></div>
          <div><label class="block text-sm font-medium mb-1">强度 (1-10)</label><input type="number" id="emotion-intensity" class="w-full border rounded px-3 py-2" min="1" max="10" value="5" /></div>
          <div><label class="block text-sm font-medium mb-1">触发原因</label><textarea id="emotion-cause" class="w-full border rounded px-3 py-2" rows="2" placeholder="什么事件导致了这种情感变化？"></textarea></div>
        `;
      } else if (type === 'power') {
        fieldsContainer.innerHTML = `
          <div><label class="block text-sm font-medium mb-1">新等级 <span class="text-red-500">*</span></label><input id="power-new" class="w-full border rounded px-3 py-2" placeholder="例如: 金丹期、Level 5" /></div>
          <div><label class="block text-sm font-medium mb-1">原等级</label><input id="power-old" class="w-full border rounded px-3 py-2" placeholder="例如: 筑基期、Level 4" /></div>
          <div><label class="block text-sm font-medium mb-1">提升方式</label><input id="power-method" class="w-full border rounded px-3 py-2" placeholder="例如: 闭关修炼、获得传承" /></div>
        `;
      } else if (type === 'relationship') {
        fieldsContainer.innerHTML = `
          <div><label class="block text-sm font-medium mb-1">目标角色 <span class="text-red-500">*</span></label><input id="rel-target" class="w-full border rounded px-3 py-2" placeholder="另一个角色的名字" /></div>
          <div><label class="block text-sm font-medium mb-1">新关系 <span class="text-red-500">*</span></label><input id="rel-new" class="w-full border rounded px-3 py-2" placeholder="例如: 挚友、仇敌、恋人" /></div>
          <div><label class="block text-sm font-medium mb-1">原关系</label><input id="rel-old" class="w-full border rounded px-3 py-2" placeholder="例如: 陌生人、普通朋友" /></div>
          <div><label class="block text-sm font-medium mb-1">变化原因</label><textarea id="rel-cause" class="w-full border rounded px-3 py-2" rows="2" placeholder="关系变化的原因"></textarea></div>
        `;
      } else if (type === 'personality') {
        fieldsContainer.innerHTML = `
          <div><label class="block text-sm font-medium mb-1">性格特质 <span class="text-red-500">*</span></label><input id="pers-trait" class="w-full border rounded px-3 py-2" placeholder="例如: 勇敢、谨慎、善良" /></div>
          <div><label class="block text-sm font-medium mb-1">新值 <span class="text-red-500">*</span></label><input id="pers-new" class="w-full border rounded px-3 py-2" placeholder="例如: 非常勇敢、8/10" /></div>
          <div><label class="block text-sm font-medium mb-1">原值</label><input id="pers-old" class="w-full border rounded px-3 py-2" placeholder="例如: 一般勇敢、5/10" /></div>
          <div><label class="block text-sm font-medium mb-1">变化原因</label><textarea id="pers-reason" class="w-full border rounded px-3 py-2" rows="2" placeholder="性格变化的原因"></textarea></div>
        `;
      }
    },

    loadData() {
      if (this.currentCharacter) {
        this.loadArcData();
      }
    }
  };
})();
