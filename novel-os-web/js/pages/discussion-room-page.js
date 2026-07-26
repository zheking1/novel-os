(function() {
  'use strict';
  console.log('[DiscussionRoomPage] Loading...');

  const PAGE_ID = 'discussion-room';
  let sessionId = null;
  let pollTimer = null;
  let isPolling = false;
  let lastResponseCount = 0;
  let currentInterval = 3000;

  const DATA_SOURCES = {
    canon: { label: 'Canon文档', hint: 'NEED: docs  # 设定文档（世界观/梗概等）' },
    entities: { label: '实体管理', hint: 'NEED: entities entity_type=类型 keywords=关键词  # 故事实体' },
    rules: { label: '创作规则', hint: 'NEED: schema table=canon_rules  # 先查表结构\nNEED: pk category=角色模板  # 已有规则' },
    'knowledge-entries': { label: '知识条目', hint: 'NEED: uk keywords=关键词  # 通用知识库\nNEED: schema table=ref_categories  # 分类树' },
    genres: { label: '题材策略', hint: 'NEED: schema table=genre_knowledge_config  # 题材配置\nNEED: schema table=genre_canonical  # 题材类型' },
    relations: { label: '实体关系', hint: 'NEED: entities entity_type=角色  # 实体\nNEED: schema table=knowledge_relations' },
    materials: { label: '参考素材', hint: 'NEED: schema table=reference_materials' },
  };

  function getCategoryHint(catSlug) {
    if (!catSlug) return '';
    return `（分类: ${catSlug}）\nNEED: uk keywords=关键词  # 此分类下的通用知识`;
  }

  function isNearBottom(el) {
    return el.scrollHeight - el.scrollTop - el.clientHeight < 80;
  }

  window.DiscussionRoomPage = {
    async init() {
      this.render();
      this.loadSavedConfig();
      this.loadModelList();
      this.loadHistory();
      return true;
    },

    CONFIG_KEY: 'discussion_room_config',

    getConfig() {
      return {
        models: Array.from(document.querySelectorAll('.disc-model-cb:checked')).map(cb => cb.value),
        control: document.getElementById('disc-control').value,
        delay: document.getElementById('disc-delay').value,
        retries: document.getElementById('disc-retries').value,
        dataSource: document.getElementById('disc-data-source').value,
        dataCategory: document.getElementById('disc-data-category').value,
      };
    },

    saveConfig() {
      const cfg = this.getConfig();
      try { localStorage.setItem(this.CONFIG_KEY, JSON.stringify(cfg)); } catch(e) {}
    },

    loadSavedConfig() {
      try {
        const raw = localStorage.getItem(this.CONFIG_KEY);
        if (!raw) return;
        const cfg = JSON.parse(raw);
        const self = this;
        setTimeout(() => {
          if (cfg.dataSource) {
            document.getElementById('disc-data-source').value = cfg.dataSource;
            document.getElementById('disc-data-source-header').value = cfg.dataSource;
            self.onDataSourceChange();
          }
          if (cfg.dataCategory) {
            document.getElementById('disc-data-category').value = cfg.dataCategory;
          }
          if (cfg.delay) document.getElementById('disc-delay').value = cfg.delay;
          if (cfg.retries) document.getElementById('disc-retries').value = cfg.retries;
          if (cfg.control) document.getElementById('disc-control').value = cfg.control;
          if (cfg.models) {
            document.querySelectorAll('.disc-model-cb').forEach(cb => {
              cb.checked = cfg.models.includes(cb.value);
            });
          }
          document.getElementById('disc-delay-val').textContent = cfg.delay || '1.5';
        }, 100);
      } catch(e) {}
    },

    render() {
      const container = document.getElementById('content-area');
      container.innerHTML = `
        <div class="p-6 max-w-7xl mx-auto">
          <div class="flex items-center justify-between mb-4">
            <h1 class="text-2xl font-bold">🏠 多模型讨论室</h1>
            <div class="flex items-center gap-2">
              <select id="disc-data-source-header"
                class="px-3 py-2 text-sm border rounded-lg bg-white text-gray-700 max-w-[180px]"
                onchange="DiscussionRoomPage.onHeaderDataSourceChange()">
                <optgroup label="📁 设定管理（用户）">
                  <option value="canon">📄 Canon文档</option>
                  <option value="entities">👥 实体管理</option>
                  <option value="rules">📋 创作规则</option>
                </optgroup>
                <optgroup label="🧠 知识管理（管理员）">
                  <option value="knowledge-entries">📖 知识条目</option>
                  <option value="genres">🎨 题材策略</option>
                  <option value="relations">🔗 实体关系</option>
                  <option value="materials">📎 参考素材</option>
                </optgroup>
              </select>
              <button onclick="DiscussionRoomPage.openConfig()"
                class="px-4 py-2 bg-gray-100 text-gray-700 rounded-lg hover:bg-gray-200 border font-medium text-sm">
                ⚙️ 配置
              </button>
              <button onclick="DiscussionRoomPage.openGuide()"
                class="px-4 py-2 bg-gray-100 text-gray-700 rounded-lg hover:bg-gray-200 border font-medium text-sm">
                📖 指南
              </button>
            </div>
          </div>

          <div class="grid grid-cols-1 lg:grid-cols-4 gap-4">
            <!-- Left: History -->
            <div class="lg:col-span-1 space-y-3">
              <div class="bg-white rounded-lg shadow p-3">
                <div class="flex items-center justify-between mb-2">
                  <h2 class="text-sm font-semibold">📜 历史话题</h2>
                  <button id="disc-new-btn" onclick="DiscussionRoomPage.newTopic()"
                    class="text-xs px-2 py-1 bg-primary-600 text-white rounded hover:bg-primary-700 hidden">
                    ✏️ 新建
                  </button>
                </div>
                <div id="disc-history-list" class="space-y-1 max-h-[500px] overflow-y-auto text-xs">
                  <div class="text-gray-400 py-4 text-center">加载中...</div>
                </div>
              </div>
            </div>

            <!-- Center: Messages + Input -->
            <div class="lg:col-span-3 space-y-3">
              <div id="disc-messages" class="bg-white rounded-lg shadow p-4 min-h-[450px] max-h-[550px] overflow-y-auto space-y-3">
                <div class="text-center text-gray-400 py-20">
                  <div class="text-4xl mb-2">💬</div>
                  <p>输入话题并点击「开始讨论」</p>
                  <p class="text-xs mt-1">控制模型会自动分析、组织讨论并总结</p>
                </div>
              </div>

              <div class="bg-white rounded-lg shadow p-4">
                <div class="flex gap-3">
                  <textarea id="disc-topic" rows="2" class="flex-1 border rounded-lg px-3 py-2 text-sm resize-none"
                    placeholder="输入你想讨论的问题...&#10;例如：主角模板的知识条目是否合理？"></textarea>
                  <div class="flex flex-col gap-2 shrink-0">
                    <button id="disc-start-btn" onclick="DiscussionRoomPage.startDiscussion()"
                      class="px-4 py-2 bg-primary-600 text-white rounded-lg hover:bg-primary-700 font-medium text-sm whitespace-nowrap">
                      ▶️ 开始
                    </button>
                    <button id="disc-stop-btn" onclick="DiscussionRoomPage.stopDiscussion()"
                      class="px-4 py-2 bg-red-600 text-white rounded-lg hover:bg-red-700 font-medium text-sm hidden">
                      ⏹ 结束
                    </button>
                    <button id="disc-apply-btn" onclick="DiscussionRoomPage.applyResults()"
                      class="px-4 py-2 bg-green-600 text-white rounded-lg hover:bg-green-700 font-medium text-sm hidden">
                      ✅ 应用
                    </button>
                    <button id="disc-continue-btn" onclick="DiscussionRoomPage.continueDiscussion()"
                      class="px-4 py-2 bg-amber-600 text-white rounded-lg hover:bg-amber-700 font-medium text-sm hidden">
                      🔄 继续讨论
                    </button>
                  </div>
                </div>
                <div id="disc-status" class="mt-2 text-xs text-gray-500">等待开始...</div>
              </div>
            </div>
          </div>
        </div>

        <!-- Config Modal -->
        <div id="config-modal" class="fixed inset-0 bg-black bg-opacity-40 flex items-center justify-center z-50 hidden">
          <div class="bg-white rounded-xl shadow-xl p-6 w-full max-w-md mx-4">
            <div class="flex items-center justify-between mb-4">
              <h2 class="text-lg font-semibold">⚙️ 讨论配置</h2>
              <button onclick="DiscussionRoomPage.closeConfig()" class="text-gray-400 hover:text-gray-600 text-xl">&times;</button>
            </div>

            <label class="block text-sm font-medium text-gray-700 mb-1">参与模型</label>
            <div id="disc-models" class="space-y-1 text-sm mb-3">
              <div class="text-gray-400">加载中...</div>
            </div>

            <label class="block text-sm font-medium text-gray-700 mb-1">控制模型</label>
            <select id="disc-control" class="w-full border rounded-lg px-3 py-2 text-sm mb-3"></select>

            <label class="block text-sm font-medium text-gray-700 mb-1">数据来源</label>
            <select id="disc-data-source" class="w-full border rounded-lg px-3 py-2 text-sm mb-1" onchange="DiscussionRoomPage.onDataSourceChange()">
              <optgroup label="📁 设定管理（用户）">
                <option value="canon">📄 Canon文档</option>
                <option value="entities">👥 实体管理</option>
                <option value="rules">📋 创作规则</option>
              </optgroup>
              <optgroup label="🧠 知识管理（管理员）">
                <option value="knowledge-entries">📖 知识条目</option>
                <option value="genres">🎨 题材策略</option>
                <option value="relations">🔗 实体关系</option>
                <option value="materials">📎 参考素材</option>
              </optgroup>
            </select>
            <select id="disc-data-category" class="w-full border rounded-lg px-3 py-2 text-sm mb-3 hidden">
              <option value="">— 全部分类 —</option>
            </select>

            <label class="block text-sm font-medium text-gray-700 mb-1">调用间隔 <span id="disc-delay-val" class="font-medium">1.5</span>s</label>
            <input id="disc-delay" type="range" min="0.5" max="5" step="0.1" value="1.5"
              class="w-full mb-3" oninput="document.getElementById('disc-delay-val').textContent=this.value">

            <label class="block text-sm font-medium text-gray-700 mb-1">429 重试次数</label>
            <input id="disc-retries" type="number" min="0" max="10" value="3"
              class="w-full border rounded-lg px-3 py-2 text-sm mb-4">

            <button onclick="DiscussionRoomPage.closeConfig()"
              class="w-full px-4 py-2 bg-primary-600 text-white rounded-lg hover:bg-primary-700 font-medium text-sm">
              确认
            </button>
          </div>
        </div>
        <!-- Guide Modal -->
        <div id="guide-modal" class="fixed inset-0 bg-black bg-opacity-40 flex items-center justify-center z-50 hidden">
          <div class="bg-white rounded-xl shadow-xl w-full max-w-3xl mx-4 max-h-[85vh] flex flex-col">
            <div class="flex items-center justify-between p-4 border-b shrink-0">
              <h2 class="text-lg font-semibold">📖 讨论室使用指南</h2>
              <button onclick="DiscussionRoomPage.closeGuide()" class="text-gray-400 hover:text-gray-600 text-xl">&times;</button>
            </div>
            <div id="guide-content" class="p-4 overflow-y-auto text-sm leading-relaxed text-gray-700 space-y-2">
              <div class="text-center text-gray-400 py-8">加载中...</div>
            </div>
          </div>
        </div>
      `;
    },

    openConfig() {
      document.getElementById('config-modal').classList.remove('hidden');
      this.loadCategoryDropdown();
    },

    closeConfig() {
      document.getElementById('config-modal').classList.add('hidden');
      this.saveConfig();
    },

    closeGuide() {
      document.getElementById('guide-modal').classList.add('hidden');
    },

    GUIDE_MD: `# 讨论室 — 用户指南

讨论室是一个**多 AI 模型协作讨论**的工具。多个模型围绕一个话题发表意见、互相审阅、逐步收敛，最终产出可执行的共识方案并应用到知识库。

---

## 一、快速开始

1. 打开「讨论室」页面
2. 点击右上角 ⚙️ 配置：
   - **选择模型**：勾选参与讨论的 AI 模型（建议 3~5 个）
   - **数据源**：选择讨论基于哪种数据（设定管理 / 知识管理）
   - **分类**：选择讨论聚焦的知识分类
   - **速率/轮次**：控制讨论速度和深度
3. 在输入框输入话题，点击「开始讨论」
4. 等待讨论完成，审阅共识草案
5. 点击「应用」将结果写入知识库（需管理员审批）

---

## 二、讨论流程

\`\`\`
用户输入话题
    ↓
① 话题分析（控制模型）
   - 分析用户意图：审查知识 / 提出建议 / 解决争议
   - 决定是否需要涉及分类讨论
    ↓
② 数据请求（控制模型）
   - 输出 NEED: 行查询相关数据
   - 后端从数据库拉取内容供模型参考
    ↓
③ 分析（控制模型）
   - 基于查询到的数据输出分析结论
    ↓
④ 多方提议（讨论模型）
   - 每个模型独立输出自己的建议方案
   - 方案包含具体可操作的知识条目
    ↓
⑤ 归纳共识（控制模型）
   - 汇总各模型提议，输出一份**纯共识草案**
   - 草案包含：
     · 文本共识（各模型一致认可的内容）
     · \`\`\`json 数据变更块（可直接执行的条目增改）
     · \`\`\`schema 结构变更块（如需修改表结构）
   - **如果有表结构变更，后续数据条目基于变更后的结构设计**
    ↓
⑥ 审阅草案（讨论模型）
   - 每个模型审阅共识草案
   - 完全同意 → 回复「无异议」
   - 有异议 → 逐条指出不同意的内容和理由
    ↓
   ┌─ 全部无异议 ─→ ⑦ 完成，草案成为最终结果
   │
   └─ 存在异议 ─→ 只讨论争议点 → 重新归纳 → 再审阅
                  （最多 3 轮，超时取最后一次归纳）
\`\`\`

---

## 三、核心机制

### 3.1 纯共识草案

控制模型不输出「已达成一致」和「仍存在分歧」两个列表，而是**基于多数意见直接输出一份各方可接受的草案**。审阅模型对草案内容表态——完全接受就说「无异议」，不接受就指出问题。异议点会在下一轮专门讨论。

### 3.2 争议聚焦

当出现异议时，下一轮**只讨论被提出的争议点**，不重复全部话题。控制模型会把每个争议的内容和理由提供给所有模型，让他们针对争议点发表修改意见，然后重新归纳。

### 3.3 两套变更分开处理

| 变更类型 | 标记 | 谁来执行 | 说明 |
|---------|------|---------|------|
| 知识数据 | \`\`\`json | 系统自动 | 写入对应表，备份旧数据，创建待审批提案 |
| 表结构 | \`\`\`schema | 管理员手动 | 不自动执行，列在提案中供管理员评估后手动操作 |

有 \`\`\`schema 时，\`\`\`json 中的数据条目会**假设新结构已存在**来设计，确保结构变更和数据变更一致。

---

## 四、应用结果

点击「应用」后：

1. 系统解析 \`\`\`json 块中的条目
2. 按类型写入对应表：
   - \`knowledge\` → \`universal_knowledge\`（通用知识库）
   - \`setting\` → \`setting_items\`（设置条目）
   - \`rule\` → \`canon_rules\`（创作规则）
   - \`category\` → \`ref_categories\`（分类）
3. 写入前备份旧数据
4. 创建 \`pending_admin\` 状态的进化提案
5. 管理员审批：
   - **通过**：删除备份，变更永久生效
   - **拒绝**：从备份还原，回滚所有变更

---

## 五、常见问题

**Q: 讨论一直有异议怎么办？**
A: 最多 3 轮，超时后取最后一次归纳作为最终结果，但 \`consensus_reached=false\`，无法应用。建议调整话题范围或补充数据后重开讨论。

**Q: 应用时报错「总结中未找到有效的 JSON 知识条目」？**
A: 控制模型未输出 \`\`\`json 块，说明模型认为这次讨论是纯分析性质，没有可执行的数据变更。可以在话题中明确要求输出具体条目。

**Q: 表结构变更谁来执行？**
A: 管理员。\`\`\`schema 块会列在提案中，管理员可以在系统管理 → 进化提案中看到具体 SQL 语句，评估后手动执行。

**Q: 数据源选哪个？**
A: 「设定管理」面向普通用户的 Canon 文档/实体/规则；「知识管理」面向管理员的知识条目/题材策略等。
`,

    async openGuide() {
      document.getElementById('guide-modal').classList.remove('hidden');
      const contentEl = document.getElementById('guide-content');
      const md = this.GUIDE_MD;
      let html = md
        .replace(/^### (.+)$/gm, '<h3 class="text-base font-bold mt-4 mb-2">$1</h3>')
        .replace(/^## (.+)$/gm, '<h2 class="text-lg font-bold mt-5 mb-2">$1</h2>')
        .replace(/^# (.+)$/gm, '<h1 class="text-xl font-bold mt-5 mb-2">$1</h1>')
        .replace(/^(\d+\.) (.+)$/gm, '<li class="ml-4 list-decimal">$2</li>')
        .replace(/^- (.+)$/gm, '<li class="ml-4 list-disc">$1</li>')
        .replace(/\*\*(.+?)\*\*/g, '<strong>$1</strong>')
        .replace(/`(.+?)`/g, '<code class="bg-gray-100 px-1 rounded text-xs">$1</code>')
        .replace(/---/g, '<hr class="my-3 border-gray-200">');
      // Convert tables before paragraph wrapping
      html = html.replace(/\n(\|.+\|\n(?:\|.+\|\n?)*)/g, (_m, tbl) => {
        const rows = tbl.trim().split('\n').filter(r => r.trim());
        if (rows.length < 2) return tbl;
        let table = '<table class="w-full text-sm border-collapse my-3"><tbody>';
        rows.forEach((row, i) => {
          if (i === 1) return; // skip separator row
          const cells = row.split('|').filter(c => c.trim()).map(c => c.trim());
          table += '<tr>';
          cells.forEach(c => {
            table += `<td class="border px-2 py-1 ${i === 0 ? 'font-semibold bg-gray-50' : ''}">${c}</td>`;
          });
          table += '</tr>';
        });
        return table + '</tbody></table>';
      });
      html = html
        .replace(/\n\n/g, '</p><p class="mb-2">')
        .replace(/\n/g, '<br>');
      html = '<p class="mb-2">' + html + '</p>';
      contentEl.innerHTML = html;
    },

    onHeaderDataSourceChange() {
      const val = document.getElementById('disc-data-source-header').value;
      document.getElementById('disc-data-source').value = val;
      this.onDataSourceChange();
      this.saveConfig();
    },

    async loadCategoryDropdown() {
      try {
        const res = await window.ApiClient.callTool('kb.category.tree', {});
        const cats = Array.isArray(res) ? res : [];
        const sel = document.getElementById('disc-data-category');
        sel.innerHTML = '<option value="">— 全部分类 —</option>';
        cats.forEach(c => {
          const opt = document.createElement('option');
          opt.value = c.slug;
          opt.textContent = '  '.repeat(c.level || 0) + c.name;
          sel.appendChild(opt);
        });
      } catch (e) {
        // ignore
      }
    },

    onDataSourceChange() {
      const isUk = document.getElementById('disc-data-source').value === 'knowledge-entries';
      document.getElementById('disc-data-category').classList.toggle('hidden', !isUk);
      document.getElementById('disc-data-source-header').value = document.getElementById('disc-data-source').value;
    },

    async loadModelList() {
      try {
        const res = await window.ApiClient.callTool('model.profile.list');
        const models = res?.profiles || res?.data || res || [];
        const container = document.getElementById('disc-models');
        const controlSelect = document.getElementById('disc-control');
        container.innerHTML = '';
        controlSelect.innerHTML = '';

        const pool = ['baidubce-deepseek-v4-flash', 'baidubce-deepseek-v3.2', 'baidubce-glm-5',
                      'baidubce-deepseek-v4-pro', 'baidubce-glm-5.1'];

        pool.forEach((key, idx) => {
          const div = document.createElement('label');
          div.className = 'flex items-center gap-2 cursor-pointer text-sm';
          const checked = idx < 3 ? 'checked' : '';
          div.innerHTML = `<input type="checkbox" class="disc-model-cb" value="${key}" ${checked}>
            <span>${key.replace('baidubce-', '')}</span>`;
          container.appendChild(div);

          const opt = document.createElement('option');
          opt.value = key;
          opt.textContent = key.replace('baidubce-', '');
          controlSelect.appendChild(opt);
        });
      } catch (e) {
        console.error('Failed to load models:', e);
      }
    },

    async loadHistory() {
      try {
        const res = await window.ApiClient.callTool('discussion_room.list_sessions', {
          workspace: window.AppState.currentWorkspace || 'default',
          project: window.AppState.currentProject || '',
          limit: 20,
        });
        const list = document.getElementById('disc-history-list');
        const sessions = res.sessions || [];
        if (sessions.length === 0) {
          list.innerHTML = '<div class="text-gray-400 py-4 text-center">暂无历史话题</div>';
          return;
        }
        list.innerHTML = '';
        sessions.forEach(s => {
          const div = document.createElement('div');
          const statusIcon = {completed: '✅', applied: '📦', pending_admin: '⏳', running: '🔄', rate_limited: '⚠️'}[s.status] || '❓';
          const canResume = s.status === 'running' && !s.consensus_reached;
          div.className = `group p-2 rounded-lg cursor-pointer border transition-colors relative
            ${canResume ? 'border-amber-200 bg-amber-50 hover:bg-amber-100' : 'border-gray-100 hover:bg-gray-50'}`;
          div.innerHTML = `
            <div class="flex items-center justify-between">
              <span class="font-medium truncate flex-1">${this.escapeHtml(s.topic.slice(0, 30))}</span>
              <span class="shrink-0 ml-1">${statusIcon}</span>
            </div>
            <div class="text-gray-400 mt-0.5">
              ${s.created_at ? s.created_at.slice(0, 10) : ''} · ${s.phase}
              ${s.consensus_reached ? '· ✅共识' : ''}
              ${canResume ? '<span class="text-amber-600 font-medium">· 可续传</span>' : ''}
            </div>
            <button class="delete-session-btn absolute top-1 right-1 w-5 h-5 flex items-center justify-center
              text-gray-300 hover:text-red-500 hover:bg-red-50 rounded text-xs"
              data-sid="${s.session_id}" title="删除此讨论">&times;</button>
          `;
          div.onclick = (e) => {
            if (e.target.closest('.delete-session-btn')) return;
            this.loadSession(s.session_id);
          };
          list.appendChild(div);
        });
        // Bind delete buttons
        list.querySelectorAll('.delete-session-btn').forEach(btn => {
          btn.onclick = (e) => {
            e.stopPropagation();
            this.deleteSession(btn.dataset.sid);
          };
        });
        // Show "New Topic" button if there are messages
        this.toggleNewBtn();
      } catch (e) {
        console.error('Failed to load history:', e);
      }
    },

    async loadSession(sid) {
      try {
        const res = await window.ApiClient.callTool('discussion_room.get_session', { session_id: sid });
        const msgContainer = document.getElementById('disc-messages');
        msgContainer.innerHTML = '';

        if (res.responses) {
          res.responses.forEach((r, idx) => {
            const msgId = `${r.model}-${r.phase}-${idx}`;
            const isUser = r.role === 'user';
            const roleIcon = isUser ? '👤' : r.role === 'control' ? '🧠' : r.role === 'reviewer' ? '🔍' : r.role === 'approver' ? '✅' : '💬';
            const roleName = isUser ? '我' : r.model;
            const phaseLabel = {analyze: '分析', propose: '提议', review_r2: '审阅1', review_r3: '审阅2', review_r4: '审阅3', summary: '总结'}[r.phase] || r.phase;
            this.addMessage(r.role, `${roleIcon} ${roleName}`, r.content, phaseLabel, msgId);
          });
        }

        if (res.summary) {
          this.addMessage('system', '📋 总结', res.summary);
        }
        if (res.consensus_reached) {
          this.addMessage('system', '✅ 共识', '讨论已达成共识');
        }

        // Show appropriate buttons based on status
        if (res.status === 'completed' || res.consensus_reached) {
          // Show continue and apply buttons for completed sessions
          sessionId = sid;
          document.getElementById('disc-start-btn').classList.remove('hidden');
          document.getElementById('disc-continue-btn').classList.remove('hidden');
          if (res.status !== 'applied' && res.status !== 'pending_admin') {
            document.getElementById('disc-apply-btn').classList.remove('hidden');
          }
        }
        if (res.status === 'pending_admin') {
          this.addMessage('system', '⏳ 待审批', '此讨论结果已应用，等待管理员审批');
          sessionId = sid;
        }
        if (res.status === 'applied') {
          this.addMessage('system', '📦 已应用', '此讨论的结果已审批通过并写入知识库');
          sessionId = sid;
        }
        if (res.status === 'running' && !res.consensus_reached) {
          this.addMessage('system', '🔄 未完成', '此讨论尚未完成，可继续输入新内容点击「开始」发起新的一轮');
          sessionId = sid;
          document.getElementById('disc-start-btn').classList.remove('hidden');
          document.getElementById('disc-stop-btn').classList.remove('hidden');
        }

        this.toggleNewBtn();
      } catch (e) {
        console.error('Failed to load session:', e);
      }
    },

    toggleNewBtn() {
      const msgs = document.getElementById('disc-messages');
      const hasContent = msgs.querySelector('.msg-entry') || !msgs.querySelector('.text-center.py-20');
      document.getElementById('disc-new-btn').classList.toggle('hidden', !hasContent);
    },

    newTopic() {
      if (pollTimer) { clearInterval(pollTimer); pollTimer = null; }
      isPolling = false;
      sessionId = null;
      document.getElementById('disc-messages').innerHTML = `
        <div class="text-center text-gray-400 py-20">
          <div class="text-4xl mb-2">💬</div>
          <p>输入话题并点击「开始讨论」</p>
        </div>
      `;
      document.getElementById('disc-topic').value = '';
      document.getElementById('disc-start-btn').classList.remove('hidden');
      document.getElementById('disc-stop-btn').classList.add('hidden');
      document.getElementById('disc-apply-btn').classList.add('hidden');
      document.getElementById('disc-status').textContent = '等待开始...';
      document.getElementById('disc-new-btn').classList.add('hidden');
      document.getElementById('disc-continue-btn').classList.add('hidden');
    },

    async continueDiscussion() {
      const topic = document.getElementById('disc-topic').value.trim();
      if (!topic) { alert('请输入继续讨论的话题'); return; }
      if (!sessionId) { alert('没有可继续的会话'); return; }

      const delay = parseFloat(document.getElementById('disc-delay').value) || 1.5;
      const retries = parseInt(document.getElementById('disc-retries').value) || 3;

      document.getElementById('disc-start-btn').classList.add('hidden');
      document.getElementById('disc-continue-btn').classList.add('hidden');
      document.getElementById('disc-apply-btn').classList.add('hidden');

      this.addMessage('user', '👤 我', topic);
      this.addMessage('system', '🔄 系统', '正在继续讨论...');

      try {
        await window.ApiClient.callTool('discussion_room.resume_session', {
          workspace: 'default', project: 'xiyu-tieqi', session_id: sessionId,
          new_topic: topic,
          rate_limit_delay: delay, rate_limit_retries: retries,
        });
        this.startPolling();
      } catch (e) {
        this.addMessage('error', '系统', `续传失败: ${e.message}`);
        this.resetButtons();
      }
    },

    async deleteSession(sid) {
      if (!confirm('确认删除此讨论？删除后不可恢复。')) return;
      try {
        await window.ApiClient.callTool('discussion_room.delete_session', {
          workspace: 'default', project: 'xiyu-tieqi', session_id: sid,
        });
        // If current view is this session, clear it
        if (sessionId === sid) this.newTopic();
        this.loadHistory();
      } catch (e) {
        alert('删除失败: ' + e.message);
      }
    },

    async startDiscussion() {
      // If continuing an existing session, delegate to continueDiscussion
      if (sessionId) {
        this.continueDiscussion();
        return;
      }

      const topic = document.getElementById('disc-topic').value.trim();
      if (!topic) { alert('请输入讨论话题'); return; }

      const checkboxes = document.querySelectorAll('.disc-model-cb:checked');
      const selected = Array.from(checkboxes).map(cb => cb.value);
      if (selected.length < 2) { alert('至少选择 2 个模型'); return; }

      const controlModel = document.getElementById('disc-control').value;
      const models = [controlModel, ...selected.filter(m => m !== controlModel)];
      const delay = parseFloat(document.getElementById('disc-delay').value) || 1.5;
      const retries = parseInt(document.getElementById('disc-retries').value) || 3;
      const dataSource = document.getElementById('disc-data-source').value;
      const dataCategory = document.getElementById('disc-data-category').value;
      const dsInfo = DATA_SOURCES[dataSource] || { hint: '' };
      const catHint = dataCategory ? `（分类: ${dataCategory}）` : '';

      document.getElementById('disc-start-btn').classList.add('hidden');
      document.getElementById('disc-stop-btn').classList.remove('hidden');
      document.getElementById('disc-apply-btn').classList.add('hidden');
      document.getElementById('disc-continue-btn').classList.add('hidden');
      document.getElementById('disc-messages').innerHTML = '';

      this.addMessage('system', '🧠 控制模型', '正在分析话题并组织讨论...');

      // Show user's own question as a message
      this.addMessage('user', '👤 我', topic);

      try {
        const res = await window.ApiClient.callTool('discussion_room.create_session', {
          workspace: window.AppState.currentWorkspace || 'default',
          project: window.AppState.currentProject || '',
          topic: topic,
          model_keys: models,
          rate_limit_delay: delay,
          rate_limit_retries: retries,
          data_source: dataSource,
          data_category: dataCategory || undefined,
        });
        sessionId = res.session_id;
        this.addMessage('system', '🧠 控制模型', `话题分析完成，组建讨论组：${models.slice(1).join(', ')}`);
        this.toggleNewBtn();
        this.startPolling();
      } catch (e) {
        this.addMessage('error', '系统', `启动失败: ${e.message}`);
        this.resetButtons();
      }
    },

    async resumeSession() {
      const sid = sessionId;
      if (!sid) return;

      const delay = parseFloat(document.getElementById('disc-delay').value) || 1.5;
      const retries = parseInt(document.getElementById('disc-retries').value) || 3;

      document.getElementById('disc-start-btn').classList.add('hidden');
      document.getElementById('disc-resume-btn').classList.add('hidden');
      document.getElementById('disc-messages').innerHTML = '';

      this.addMessage('system', '🔄 系统', '正在继续讨论...');

      try {
        await window.ApiClient.callTool('discussion_room.resume_session', {
          workspace: 'default', project: 'xiyu-tieqi', session_id: sid,
          rate_limit_delay: delay, rate_limit_retries: retries,
        });
        const sess = await window.ApiClient.callTool('discussion_room.get_session', { session_id: sid });
        if (sess.responses) {
          sess.responses.forEach((r, idx) => {
            const msgId = `${r.model}-${r.phase}-${idx}`;
            const isUser = r.role === 'user';
            const roleIcon = isUser ? '👤' : r.role === 'control' ? '🧠' : r.role === 'reviewer' ? '🔍' : r.role === 'approver' ? '✅' : '💬';
            const roleName = isUser ? '我' : r.model;
            const phaseLabel = {analyze: '分析', propose: '提议', review_r2: '审阅1', review_r3: '审阅2', review_r4: '审阅3', summary: '总结'}[r.phase] || r.phase;
            this.addMessage(r.role, `${roleIcon} ${roleName}`, r.content, phaseLabel, msgId);
          });
        }
        sessionId = sid;
        this.toggleNewBtn();
        this.startPolling();
      } catch (e) {
        this.addMessage('error', '系统', `续传失败: ${e.message}`);
        this.resetButtons();
      }
    },

    startPolling() {
      if (pollTimer) clearInterval(pollTimer);
      isPolling = true;
      lastResponseCount = 0;
      currentInterval = 3000;
      pollTimer = setInterval(() => this.pollUpdates(), currentInterval);
    },

    async pollUpdates() {
      if (!sessionId) return;
      try {
        const res = await window.ApiClient.callTool('discussion_room.get_updates', {
          session_id: sessionId,
        });
        if (res.error) { this.addMessage('error', '系统', res.error); this.stopPolling(); return; }

        this.updateStatus(res);

        const msgContainer = document.getElementById('disc-messages');
        const respCount = (res.responses || []).length;

        // Adaptive backoff: if no new messages, increase interval up to 5s
        if (respCount > lastResponseCount) {
          lastResponseCount = respCount;
          currentInterval = 3000;
        } else {
          currentInterval = Math.min(currentInterval + 500, 5000);
        }
        clearInterval(pollTimer);
        pollTimer = setInterval(() => this.pollUpdates(), currentInterval);

        if (res.responses) {
          const msgContainer = document.getElementById('disc-messages');
          const existingIds = new Set();
          msgContainer.querySelectorAll('.msg-entry').forEach(el => existingIds.add(el.dataset.msgId));

          res.responses.forEach((r, idx) => {
            const msgId = `${r.model}-${r.phase}-${idx}`;
            if (existingIds.has(msgId)) return;

            const isUser = r.role === 'user';
            const roleIcon = isUser ? '👤' : r.role === 'control' ? '🧠' : r.role === 'reviewer' ? '🔍' : r.role === 'approver' ? '✅' : '💬';
            const roleName = isUser ? '我' : r.model;
            const phaseLabel = {analyze: '分析中', propose: '提议', review_r2: '审阅1', review_r3: '审阅2', review_r4: '审阅3', summary: '总结', topic_analysis: '话题分析', data_plan: '数据请求'}[r.phase] || r.phase;
            this.addMessage(r.role, `${roleIcon} ${roleName}`, r.content, phaseLabel, msgId);
          });
        }

        if (res.consensus_reached) {
          this.addMessage('system', '✅ 共识达成', res.summary || '讨论完成');
          this.stopPolling();
          document.getElementById('disc-apply-btn').classList.remove('hidden');
          document.getElementById('disc-continue-btn').classList.remove('hidden');
          this.loadHistory();
        }
        if (res.status === 'completed' && !res.consensus_reached) {
          this.addMessage('system', '📋 讨论结束', res.summary || '未达成共识');
          this.stopPolling();
          document.getElementById('disc-continue-btn').classList.remove('hidden');
          this.loadHistory();
        }
        if (res.status === 'applied') {
          this.stopPolling();
          this.loadHistory();
        }
      } catch (e) {
        console.error('Poll error:', e);
      }
    },

    stopPolling() {
      if (pollTimer) { clearInterval(pollTimer); pollTimer = null; }
      isPolling = false;
      this.resetButtons();
    },

    stopDiscussion() {
      this.stopPolling();
      this.addMessage('system', '⏹ 系统', '讨论已手动结束');
    },

    async applyResults() {
      document.getElementById('disc-apply-btn').disabled = true;
      document.getElementById('disc-apply-btn').textContent = '⏳...';
      try {
        const res = await window.ApiClient.callTool('discussion_room.apply_results', {
          workspace: 'default',
          project: 'xiyu-tieqi',
          session_id: sessionId,
        });
        if (res.ok) {
          this.addMessage('system', '✅ 系统', '讨论结果已成功应用到知识库！');
          document.getElementById('disc-apply-btn').textContent = '✅ 已应用';
          this.loadHistory();
        } else {
          this.addMessage('error', '系统', `应用失败: ${res.error}`);
          document.getElementById('disc-apply-btn').disabled = false;
          document.getElementById('disc-apply-btn').textContent = '✅ 应用';
        }
      } catch (e) {
        this.addMessage('error', '系统', `应用失败: ${e.message}`);
        document.getElementById('disc-apply-btn').disabled = false;
        document.getElementById('disc-apply-btn').textContent = '✅ 应用';
      }
    },

    addMessage(role, title, content, phase, msgId) {
      const container = document.getElementById('disc-messages');
      const empty = container.querySelector('.text-center.py-20');
      if (empty) empty.remove();

      const wasNearBottom = isNearBottom(container);

      const bgColor = {
        control: 'bg-blue-50 border-blue-200',
        discuss: 'bg-white border-gray-200',
        reviewer: 'bg-yellow-50 border-yellow-200',
        approver: 'bg-green-50 border-green-200',
        user: 'bg-gray-100 border-gray-300',
        system: 'bg-purple-50 border-purple-200',
        error: 'bg-red-50 border-red-200',
      }[role] || 'bg-white border-gray-200';

      const div = document.createElement('div');
      div.className = `msg-entry border rounded-lg p-3 ${bgColor}`;
      if (msgId) div.dataset.msgId = msgId;

      const displayContent = content || '';

      div.innerHTML = `
        <div class="flex items-center justify-between mb-1">
          <span class="font-semibold text-sm">${title}</span>
          ${phase ? `<span class="text-xs text-gray-400">${phase}</span>` : ''}
        </div>
        <div class="text-sm text-gray-700 whitespace-pre-wrap leading-relaxed">${this.escapeHtml(displayContent)}</div>
      `;
      container.appendChild(div);

      // Only scroll if user was already near bottom
      if (wasNearBottom) {
        requestAnimationFrame(() => { container.scrollTop = container.scrollHeight; });
      }
    },

    updateStatus(res) {
      const statusEl = document.getElementById('disc-status');
      const phaseLabels = {analyzing: '🔍 分析中', proposing: '💬 提议阶段', reviewing: '🔄 审阅', summarizing: '📝 总结中', completed: '✅ 完成'};
      statusEl.textContent = `${phaseLabels[res.phase] || res.phase} · 第 ${res.round || 0} 轮 · ${res.consensus_reached ? '✅ 共识' : '⏳ 讨论中'}`;
    },

    resetButtons() {
      document.getElementById('disc-start-btn').classList.remove('hidden');
      document.getElementById('disc-stop-btn').classList.add('hidden');
    },

    escapeHtml(text) {
      if (!text) return '';
      return text.replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;')
        .replace(/\n/g, '<br>');
    },
  };
})();