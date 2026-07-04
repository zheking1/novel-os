/**
 * Novel OS - Entities Module
 */
;(function() {
  'use strict';

  var currentEntityId = null;

  window.renderEntityList = function(entities) {
    var container = window.$("entityListResult");
    if (!entities || entities.length === 0) {
      container.innerHTML = '<p style="color:var(--muted);text-align:center;padding:20px;">No entities found</p>';
      return;
    }
    container.innerHTML = entities.map(function(entity) {
      return '<div class="list-item" onclick="window.selectEntity(\'' + entity.id + '\',\'' + entity.entity_type + '\',\'' + entity.name + '\')">' +
        '<div class="list-item-header"><span>' + entity.name + '</span></div>' +
        '<div class="list-item-meta">' + entity.entity_type + ' | ' + (entity.importance || 'medium') + '</div>' +
      '</div>';
    }).join("");
  };

  window.selectEntity = function(id, entityType, name) {
    currentEntityId = id;
    window.$("entityType").value = entityType;
    window.$("entityName").value = name;
    window.loadEntityDetails(entityType, name);
  };

  window.loadEntityDetails = async function(entityType, name) {
    var base = window.getActiveProjectArgs();
    if (!base) return;
    window.setStatus(window.t("status.running"));
    var result = await window.api("/api/tool", { tool: "state.entity.get", arguments: Object.assign({}, base, {entity_type: entityType, name: name}) });
    if (result.ok && result.result) {
      var entity = result.result;
      currentEntityId = entity.id;
      window.$("entityType").value = entity.entity_type || "character";
      window.$("entityName").value = entity.name || "";
      window.$("entityStatus").value = entity.lifecycle_status || "active";
      window.$("entityImportance").value = entity.importance || "medium";
      window.goToPage("entities-create");
      window.setStatus(window.t("msg.loaded"));
    }
  };
})();