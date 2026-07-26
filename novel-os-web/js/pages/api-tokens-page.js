/**
 * API Key 管理页面
 * 用户在此创建和管理 MCP 连接用的 API Key
 */
(function() {
  'use strict';

  window.ApiKeysPage = {
    keys: [],

    init() { this.render(); this.loadData(); return true; },

    render() {
      document.getElementById('content-area').innerHTML = `
        <div class="space-y-4 max-w-3xl">
          <div class="flex items-center justify-between">
            <div>
              <h1 class="text-2xl font-bold">🔑 API Key 管理</h1>
              <p class="text-gray-500 mt-1">创建 API Key 用于 AI 工具（Claude/ChatGPT/Trae）连接 Novel OS MCP 服务</p>
            </div>
            <button onclick="ApiKeysPage.create()" id="create-key-btn" class="px-4 py-2 bg-primary-600 text-white rounded-lg hover:bg-primary-700 text-sm">+ 创建 Key</button>
          </div>

          <div id="keys-container" class="bg-white rounded-lg shadow">
            <div class="p-8 text-center text-gray-500">加载中...</div>
          </div>

          <div id="config-hint" class="bg-blue-50 border border-blue-200 rounded-lg p-4 text-sm hidden">
            <h3 class="font-medium text-blue-800 mb-2">📖 AI 工具 MCP 配置</h3>
            <pre class="text-xs text-blue-700 overflow-x-auto" id="config-snippet"></pre>
          </div>
        </div>
      `;
    },

    async loadData() {
      try {
        this.keys = (await window.ApiClient.callTool('auth.list_api_tokens', {}) || [])
          .filter(k => !k.name.startsWith('__system_') && !k.name.startsWith('web-service') && k.name !== 'service_token' && !k.name.startsWith('auto_'));
        this.renderList();
      } catch(e) {
        document.getElementById('keys-container').innerHTML = `<div class="p-8 text-center text-red-500">加载失败</div>`;
      }
    },

    renderList() {
      const c = document.getElementById('keys-container');
      if (!this.keys.length) {
        c.innerHTML = `<div class="p-8 text-center text-gray-500">暂无 API Key，点击右上角创建一个</div>`;
        return;
      }
      const hint = document.getElementById('config-hint');
      hint.classList.remove('hidden');
      hint.querySelector('#config-snippet').textContent = JSON.stringify({
        mcpServers: {
          "novel-os": {
            url: "https://novel.example.com/mcp",
            headers: { "apiKey": this.keys[0].token_preview || "&lt;你的Key&gt;" }
          }
        }
      }, null, 2);

      c.innerHTML = `<div class="divide-y divide-gray-200">${this.keys.map(k => `
        <div class="p-4 hover:bg-gray-50 flex items-center justify-between">
          <div>
            <div class="font-medium text-sm">🔑 ${k.name || 'Key'}</div>
            <div class="text-xs text-gray-400 mt-1">创建于 ${k.created_at ? new Date(k.created_at).toLocaleString() : '—'} · 最后使用 ${k.last_used_at ? new Date(k.last_used_at).toLocaleString() : '—'}</div>
          </div>
          <div class="flex items-center gap-2">
            <button onclick="ApiKeysPage.copyKey('${k.id}')" class="text-xs px-3 py-1 border rounded hover:bg-gray-100">复制</button>
            <button onclick="ApiKeysPage.revoke('${k.id}', '${k.name}')" class="text-red-500 text-xs hover:text-red-700">删除</button>
          </div>
        </div>`).join('')}</div>`;
    },

async create() {
      var opts = [
        { label: '7 天', value: 7 },
        { label: '30 天', value: 30 },
        { label: '90 天', value: 90 },
        { label: '1 年', value: 365 },
        { label: '永久有效', value: 0 }
      ];
      ModalDialog.show({
        title: '创建 API Key',
        content: '<div class="space-y-4">' +
          '<div><label class="block text-sm font-medium mb-1">名称</label><input id="api-key-name" class="w-full border rounded px-3 py-2" placeholder="如 claude、trae"></div>' +
          '<div><label class="block text-sm font-medium mb-1">过期时间</label><select id="api-key-expire" class="w-full border rounded px-3 py-2">' +
          opts.map(function(o) { return '<option value="' + o.value + '">' + o.label + '</option>'; }).join('') +
          '</select></div></div>',
        onConfirm: async function() {
          var name = document.getElementById('api-key-name').value.trim();
          if (!name) { alert('名称不能为空'); return; }
          var days = parseInt(document.getElementById('api-key-expire').value);
          var args = { name: name, scopes: ['read','write'] };
          if (days > 0) {
            var dt = new Date();
            dt.setDate(dt.getDate() + days);
            args.expires_at = dt.toISOString();
          }
          try {
            var result = await window.ApiClient.callTool('auth.create_api_token', args);
            var token = result.token;
            var saved = JSON.parse(localStorage.getItem('api_keys') || '{}');
            saved[result.id] = { name: name, token: token, created: result.created_at };
            localStorage.setItem('api_keys', JSON.stringify(saved));
            prompt('✅ 请复制你的 API Key（Ctrl+C）：', token);
            ApiKeysPage.loadData();
          } catch(e) { alert('创建失败: ' + (e.message || '未知错误')); }
        }
      });

    },

    async copyKey(id) {
      const saved = JSON.parse(localStorage.getItem('api_keys') || '{}');
      const entry = saved[id];
      if (entry?.token) {
        prompt('🔑 API Key（Ctrl+C 复制）：', entry.token);
      } else {
        alert('Key 已过期或未保存。请重新创建一个。');
      }
    },

    async revoke(id, name) {
      if (name.startsWith('__system_') || name.startsWith('web-service')) {
        alert('系统 Token 不可删除');
        return;
      }
      if (!confirm(`确定删除 Token "${name}"？立即失效。`)) return;
      try {
        await window.ApiClient.callTool('auth.revoke_api_token', { token_id: id });
        // Clean localStorage
        const saved = JSON.parse(localStorage.getItem('api_keys') || '{}');
        delete saved[id];
        localStorage.setItem('api_keys', JSON.stringify(saved));
        this.loadData();
      } catch(e) { alert('删除失败: ' + e.message); }
    }
  };
})();