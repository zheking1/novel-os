/**
 * Novel OS - Canon Documents Module
 */
;(function() {
  'use strict';

  window.renderCanonList = function(docs) {
    const container = window.$("canonListResult");
    if (!docs || docs.length === 0) {
      container.innerHTML = '<p style="color:var(--muted);text-align:center;padding:20px;">No documents found</p>';
      return;
    }
    container.innerHTML = docs.map(function(doc) {
      return '<div class="list-item" onclick="window.selectCanonDoc(\'' + doc.key + '\')">' +
        '<div class="list-item-header">' +
          '<span>' + (doc.title || doc.key) + '</span>' +
        '</div>' +
        '<div class="list-item-meta"><span>' + doc.key + '</span> | <span>' + doc.doc_type + '</span> | v' + doc.version + '</div>' +
        (doc.content ? '<div style="font-size:12px;color:var(--muted);margin-top:6px;">' + doc.content.substring(0, 150) + '</div>' : '') +
      '</div>';
    }).join("");
  };

  window.selectCanonDoc = function(key) {
    window.$("canonKey").value = key;
    window.loadCanonDoc(key);
  };

  window.loadCanonDoc = async function(key) {
    var base = window.getActiveProjectArgs();
    if (!base) return;
    var result = await window.api("/api/tool", { tool: "canon.doc.get", arguments: Object.assign({}, base, {key: key}) });
    if (result.ok && result.result) {
      var doc = result.result;
      window.$("canonKey").value = doc.key || "";
      window.$("canonTitle").value = doc.title || "";
      window.$("canonContent").value = doc.content || "";
      window.$("canonType").value = doc.doc_type || "other";
      window.$("canonStatus").value = doc.status || "active";
      window.$("canonReviewStatus").value = doc.review_status || "approved";
      window.$("canonSourceType").value = doc.source_type || "manual";
      window.goToPage("canon-create");
      window.setStatus(window.t("msg.loaded"));
    }
  };
})();