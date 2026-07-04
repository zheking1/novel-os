/**
 * Novel OS - system.js
 * Auto-extracted module
 */
;(function(window) {
// ===== init_model_profiles_fn() =====
function init_model_profiles_fn() {
        if (modelProfilesInitStarted) return;
        modelProfilesInitStarted = true;
        $("modelProfilesListBtn").click();
      }
  window.init_model_profiles_fn = init_model_profiles_fn;

// ===== init_model_cost_fn() =====
function init_model_cost_fn() {
        if (modelCostInitStarted) return;
        modelCostInitStarted = true;
        // Set default date range (last 30 days)
        const today = new Date().toISOString().split('T')[0];
        const thirtyDaysAgo = new Date(Date.now() - 30 * 24 * 60 * 60 * 1000).toISOString().split('T')[0];
        $("costReportFromDate").value = thirtyDaysAgo;
        $("costReportToDate").value = today;
        $("costReportBtn").click();
      }
  window.init_model_cost_fn = init_model_cost_fn;

// ===== init_template_list_fn() =====
function init_template_list_fn() {
        if (templateListInitStarted) return;
        templateListInitStarted = true;
        $("templateListBtn").click();
      }
  window.init_template_list_fn = init_template_list_fn;

// ===== renderModelProfiles() =====
function renderModelProfiles(profiles) {
        const container = $("modelProfilesResult");
        if (!profiles || profiles.length === 0) {
          container.innerHTML = '<p style="color:var(--muted);text-align:center;padding:20px;">No model profiles</p>';
          return;
        }
        container.innerHTML = profiles.map(p => `
          <div class="list-item" onclick="selectModelProfile('${p.profile_key}')">
            <div class="list-item-header">
              <span>${p.display_name}</span>
              <div style="display:flex;gap:6px;">
                ${p.is_default ? '<span class="badge badge-success">Default</span>' : ''}
                <span class="badge ${p.tier === 'premium' ? 'badge-warning' : 'badge-active'}">${p.tier}</span>
                <span class="badge ${p.status === 'active' ? 'badge-success' : 'badge-archived'}">${p.status}</span>
              </div>
            </div>
            <div class="list-item-meta">
              ${p.provider} / ${p.model_name} | Tasks: ${p.task_types?.join(', ') || '-'}
            </div>
          </div>
        `).join("");
      }
  window.renderModelProfiles = renderModelProfiles;

// ===== renderOfflineQueue() =====
function renderOfflineQueue() {
        // Show local projects that need sync
        api("/api/tool", { tool: "local.project.list", arguments: {} }).then(function(result) {
          var projects = (result && result.projects) ? result.projects : [];
          $("offlineQueueCount").textContent = projects.length;
          if (projects.length > 0) {
            $("offlineQueueList").innerHTML = projects.map(function(p) {
              return '<div class="offline-queue-item">' +
                '<div class="offline-queue-header">' +
                  '<span class="offline-queue-type">项目</span>' +
                  '<span class="offline-queue-action">' + escapeHtml(p.project_id) + '</span>' +
                '</div>' +
                '<div class="offline-queue-title">' + escapeHtml(p.local_root || "") + '</div>' +
                '<div class="offline-queue-time">' + (p.last_scan_at ? "最后扫描: " + p.last_scan_at : "未扫描") + '</div>' +
              '</div>';
            }).join("");
          } else {
            $("offlineQueueList").innerHTML = '<p style="color:var(--muted);">暂无注册项目</p>';
          }
        });
      }
  window.renderOfflineQueue = renderOfflineQueue;

// ===== renderMarketTemplates() =====
function renderMarketTemplates(templates) {
        $("marketPopularList").innerHTML = templates.slice(0, 3).map(function(t) {
          return '<div class="market-card" onclick="openMarketDetail(\'' + (t.key || t.id) + '\')">' +
            '<div class="market-card-header">' +
              '<span class="market-card-name">' + escapeHtml(t.name || t.key) + '</span>' +
            '</div>' +
            '<div class="market-card-desc">' + escapeHtml(t.description || "") + '</div>' +
            '<div class="market-card-meta">' +
              '<span class="market-tag">' + escapeHtml(t.type || "") + '</span>' +
              '<span class="market-tag">' + escapeHtml(t.genre || "") + '</span>' +
            '</div>' +
          '</div>';
        }).join("");

        $("marketNewGrid").innerHTML = templates.map(function(t) {
          return '<div class="market-grid-card" onclick="openMarketDetail(\'' + (t.key || t.id) + '\')">' +
            '<div class="market-grid-icon">📋</div>' +
            '<div class="market-grid-name">' + escapeHtml(t.name || t.key) + '</div>' +
            '<div class="market-grid-desc">' + escapeHtml((t.description || "").substring(0, 50)) + '</div>' +
            '<div class="market-grid-footer">' +
              '<span class="market-tag">' + escapeHtml(t.type || "") + '</span>' +
            '</div>' +
          '</div>';
        }).join("");
      }
  window.renderMarketTemplates = renderMarketTemplates;

// ===== loadMarketTemplates() =====
async function loadMarketTemplates() {
        var result = await api("/api/tool", { tool: "prompt.template.list", arguments: { limit: 100 } });
        if (result && result.templates) {
          marketTemplatesCache = result.templates;
          renderMarketTemplates(marketTemplatesCache);
        } else {
          $("marketPopularList").innerHTML = '<p style="color:var(--muted);">暂无模板</p>';
          $("marketNewGrid").innerHTML = '';
        }
      }
  window.loadMarketTemplates = loadMarketTemplates;

// ===== renderTemplates() =====
function renderTemplates(templates) {
        const container = $("templateListResult");
        if (!templates || templates.length === 0) {
          container.innerHTML = '<p style="color:var(--muted);text-align:center;padding:20px;">No templates</p>';
          return;
        }
        container.innerHTML = templates.map(t => `
          <div class="template-card" onclick="selectTemplate('${t.id}')">
            <div class="template-card-header">
              <span class="template-card-name">${escapeHtml(t.name)}</span>
              <span class="badge ${t.template_type === 'system' ? 'badge-success' : t.template_type === 'user' ? 'badge-warning' : 'badge-active'}">${t.template_type}</span>
            </div>
            <div class="template-card-key">${t.template_key}</div>
            <div class="template-card-desc">${escapeHtml(t.description || '')}</div>
            <div class="template-card-meta">
              ${t.genre ? `<span class="template-tag">${t.genre}</span>` : ''}
              ${t.scene ? `<span class="template-tag">${t.scene}</span>` : ''}
            </div>
          </div>
        `).join("");
      }
  window.renderTemplates = renderTemplates;

// ===== renderGraph() =====
function renderGraph(nodes, links) {
        const svg = $("graphSvg");
        const width = svg.parentElement.clientWidth;
        const height = 450;
        svg.setAttribute("width", width);
        svg.setAttribute("height", height);

        const padding = 50;
        const nodeRadius = 25;
        const colors = {
          character: "#3b82f6",
          faction: "#10b981",
          location: "#f59e0b"
        };

        let html = '<defs>';
        Object.keys(colors).forEach(type => {
          html += `<marker id="arrowhead-${type}" markerWidth="10" markerHeight="7" refX="20" refY="3.5" orient="auto">
            <polygon points="0 0, 10 3.5, 0 7" fill="${colors[type]}" />
          </marker>`;
        });
        html += '</defs>';

        links.forEach((link, idx) => {
          const source = nodes.find(n => n.id === link.source);
          const target = nodes.find(n => n.id === link.target);
          if (!source || !target) return;
          const sourceAngle = (source.index * 2 * Math.PI) / nodes.length;
          const targetAngle = (target.index * 2 * Math.PI) / nodes.length;
          const cx = width / 2;
          const cy = height / 2;
          const r = Math.min(width, height) / 2 - padding;
          const x1 = cx + r * Math.cos(sourceAngle);
          const y1 = cy + r * Math.sin(sourceAngle);
          const x2 = cx + r * Math.cos(targetAngle);
          const y2 = cy + r * Math.sin(targetAngle);
          html += `<line x1="${x1}" y1="${y1}" x2="${x2}" y2="${y2}" class="graph-link" stroke="#cbd5e1" stroke-width="2" />`;
        });

        nodes.forEach((node, idx) => {
          const angle = (idx * 2 * Math.PI) / nodes.length;
          const cx = width / 2;
          const cy = height / 2;
          const r = Math.min(width, height) / 2 - padding;
          const x = cx + r * Math.cos(angle);
          const y = cy + r * Math.sin(angle);
          const color = colors[node.type] || "#6b7280";
          html += `<circle cx="${x}" cy="${y}" r="${nodeRadius}" fill="${color}" class="graph-node" stroke="white" stroke-width="2" />`;
          html += `<text x="${x}" y="${y + 5}" class="graph-label" fill="white" font-weight="bold">${escapeHtml(node.name.substring(0, 3))}</text>`;
          html += `<text x="${x}" y="${y + nodeRadius + 20}" class="graph-label" font-size="11">${escapeHtml(node.name)}</text>`;
        });

        svg.innerHTML = html;

        const legend = $("graphLegend");
        legend.innerHTML = Object.keys(colors).map(type => `
          <div class="graph-legend-item">
            <span class="graph-legend-dot" style="background:${colors[type]}"></span>
            <span>${type}</span>
          </div>
        `).join("");
      }
  window.renderGraph = renderGraph;

// ===== loadApiTokens() =====
async function loadApiTokens() {
        const workspace = $("workspace")?.value || $("workspaceSelect")?.value || null;
        const args = { include_revoked: false };
        if (workspace) args.workspace = workspace;
        const result = await api("/api/tool", {
          tool: "auth.list_api_tokens",
          arguments: args
        });
        const container = $("apiTokensList");
        if (!container) return;
        if (!result.ok || !Array.isArray(result.result)) {
          container.innerHTML = '<div style="color: var(--muted); font-size: 13px; padding: 12px; text-align: center;">' + t("account.loadTokensFailed") + '</div>';
          return;
        }
        const tokens = result.result.filter(t => !t.revoked_at);
        if (tokens.length === 0) {
          container.innerHTML = '<div style="color: var(--muted); font-size: 13px; padding: 12px; text-align: center;">' + t("account.noTokens") + '</div>';
          return;
        }
        container.innerHTML = tokens.map(token => `
          <div style="display: flex; justify-content: space-between; align-items: center; padding: 10px; border-bottom: 1px solid var(--line); font-size: 13px;">
            <div>
              <div style="font-weight: 500;">${escapeHtml(token.name)}</div>
              <div style="color: var(--muted); font-size: 11px;">${(token.scopes || []).join(', ')} · ${token.created_at ? new Date(token.created_at).toLocaleDateString() : ''}</div>
            </div>
            <button class="btn-secondary btn-sm" onclick="revokeToken('${token.id}')" style="font-size: 12px; padding: 4px 8px;">${t("action.revoke")}</button>
          </div>
        `).join('');
      }
  window.loadApiTokens = loadApiTokens;

// ===== loadSystemHealth() =====
async function loadSystemHealth() {
      setStatus("加载系统状态...");
      var result = await api("/api/tool", { tool: "admin.health", arguments: {} });
      var cards = $("healthCards");
      if (result && !result.error) {
        cards.innerHTML =
          '<div class="panel" style="padding:16px;text-align:center;">' +
            '<div style="font-size:24px;margin-bottom:4px;">' + (result.database ? "🟢" : "🔴") + '</div>' +
            '<div style="font-size:13px;font-weight:500;">数据库</div>' +
            '<div style="font-size:12px;color:var(--muted);">' + (result.database ? "正常" : "异常") + '</div>' +
          '</div>' +
          '<div class="panel" style="padding:16px;text-align:center;">' +
            '<div style="font-size:24px;margin-bottom:4px;">🟢</div>' +
            '<div style="font-size:13px;font-weight:500;">Qdrant</div>' +
            '<div style="font-size:12px;color:var(--muted);">' + escapeHtml(result.qdrant_url || "") + '</div>' +
          '</div>' +
          '<div class="panel" style="padding:16px;text-align:center;">' +
            '<div style="font-size:24px;margin-bottom:4px;">🟢</div>' +
            '<div style="font-size:13px;font-weight:500;">Redis</div>' +
            '<div style="font-size:12px;color:var(--muted);">' + escapeHtml(result.redis_host || "") + '</div>' +
          '</div>' +
          '<div class="panel" style="padding:16px;text-align:center;">' +
            '<div style="font-size:24px;margin-bottom:4px;">🟢</div>' +
            '<div style="font-size:13px;font-weight:500;">MCP Server</div>' +
            '<div style="font-size:12px;color:var(--muted);">运行中</div>' +
          '</div>';
        $("healthDetail").innerHTML = '<pre style="font-size:12px;background:var(--bg);padding:12px;border-radius:6px;overflow-x:auto;">' + escapeHtml(JSON.stringify(result, null, 2)) + '</pre>';
      } else {
        cards.innerHTML = '<div style="grid-column:1/-1;text-align:center;color:var(--danger);">无法获取系统状态</div>';
      }
    }
  window.loadSystemHealth = loadSystemHealth;

// ===== loadBackupList() =====
async function loadBackupList() {
      var result = await api("/api/tool", { tool: "backup.list", arguments: {} });
      var el = $("backupList");
      if (result && result.backups && result.backups.length > 0) {
        el.innerHTML = result.backups.map(function(b) {
          return '<div class="list-item">' +
            '<div class="list-item-header"><span>' + escapeHtml(b.filename || b.id) + '</span><span class="badge">' + (b.type || "full") + '</span></div>' +
            '<div class="list-item-meta">' + (b.created_at || "") + ' — ' + (b.size || "") + '</div>' +
            '</div>';
        }).join("");
      } else {
        el.innerHTML = '<p style="color:var(--muted);">暂无备份</p>';
      }
    }
  window.loadBackupList = loadBackupList;

// ===== saveBackupSchedule() =====
async function saveBackupSchedule() {
      var interval = parseInt($("backupInterval").value);
      if (!interval || interval < 1) { showToast("warning", "请输入有效间隔"); return; }
      var result = await api("/api/tool", { tool: "backup.schedule.upsert", arguments: Object.assign(baseProjectArgs(), { interval_hours: interval, enabled: true }) });
      if (result && !result.error) {
        showToast("success", "备份计划已保存");
      }
    }
  window.saveBackupSchedule = saveBackupSchedule;

// ===== createBackup() =====
async function createBackup() {
      setStatus("创建备份...");
      var result = await api("/api/tool", { tool: "backup.create", arguments: Object.assign(baseProjectArgs(), { backup_type: "full" }) });
      if (result && !result.error) {
        showToast("success", "备份已创建");
        loadBackupList();
      }
    }
  window.createBackup = createBackup;

})(window);
