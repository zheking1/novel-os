/**
 * Novel OS - Knowledge Module (UK Management)
 */
;(function() {
  'use strict';

  // UK Statistics
  window.loadUkStats = async function() {
    try { return await window.api("/api/tool", { tool: "knowledge.stats", arguments: {} }); }
    catch(e) { return { error: e.message }; }
  };

  window.loadUkTree = async function() {
    try { return await window.api("/api/tool", { tool: "kb.category.tree", arguments: {} }); }
    catch(e) { return { error: e.message }; }
  };

  window.loadKnowledgeList = async function() {
    setStatus("Loading knowledge list...");
    var result = await window.api("/api/tool", { tool: "knowledge.item.list", arguments: { limit: 50 } });
    if (result.ok) {
      var el = window.$("knowledgeListResult");
      if (el) el.innerHTML = (result.result || []).map(function(i) {
        return '<div class="list-item"><div class="list-item-header"><span>' + window.escapeHtml(i.title || '') + '</span></div></div>';
      }).join("");
    }
    setStatus("");
  };

  window.loadKnowledgeStats = async function() {
    var result = await window.api("/api/tool", { tool: "knowledge.stats", arguments: {} });
    if (result.ok) {
      var s = result.result || {};
      var el = window.$("kbTotalItems"); if (el) el.textContent = s.total_items || 0;
      var el2 = window.$("kbActiveItems"); if (el2) el2.textContent = s.active_items || 0;
    }
  };

  window.loadCacheStats = async function() {
    var result = await window.api("/api/tool", { tool: "system.cache.get_stats", arguments: {} });
    var el = window.$("cacheStats");
    if (el && result) el.innerHTML = '<pre style="font-size:12px;">' + window.escapeHtml(JSON.stringify(result, null, 2)) + '</pre>';
  };
})();