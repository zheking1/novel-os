/**
 * Novel OS - Rules Module
 */
;(function() {
  'use strict';
  
  window.renderRulesResult = function(data, title, containerId) {
    var container = window.$(containerId);
    if (!container) return;
    if (!data || (Array.isArray(data) && data.length === 0)) {
      container.innerHTML = '<p style="color:var(--muted);">' + (title || 'No results') + '</p>';
      return;
    }
    if (Array.isArray(data)) {
      container.innerHTML = data.map(function(item) {
        return '<div class="result-item">' +
          '<strong>' + (item.title || item.key || item.rule_key || item.id || 'Rule') + '</strong>' +
          (item.content ? '<div style="font-size:12px;color:var(--muted);margin-top:4px;">' + item.content.substring(0, 200) + '</div>' : '') +
        '</div>';
      }).join("");
    }
  };

  window.renderRuleProposals = function(proposals) {
    var container = window.$("ruleProposalsResult");
    if (!proposals || proposals.length === 0) {
      container.innerHTML = '<p style="color:var(--muted);text-align:center;padding:20px;">No rule proposals</p>';
      return;
    }
    container.innerHTML = proposals.map(function(p) {
      return '<div class="list-item" onclick="window.selectRuleProposal(\'' + p.id + '\')">' +
        '<div class="list-item-header"><span>' + (p.rule_key || p.title) + '</span></div>' +
        '<div class="list-item-meta">' + (p.title || '') + ' | ' + (p.created_at || '') + '</div></div>';
    }).join("");
  };
})();