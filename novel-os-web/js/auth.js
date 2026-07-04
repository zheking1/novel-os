/**
 * Novel OS Auth - Workspace & Project management
 */
;(function() {
  'use strict';

  async function loadWorkspaces() {
    try {
      const result = await api("/api/tool", {
        tool: "workspace.list",
        arguments: {}
      });
      if (result.ok && Array.isArray(result.result)) {
        window.allWorkspaces = result.result;
        const sel = $("workspaceSelect");
        if (!sel) return;
        sel.innerHTML = '<option value="">-- Select --</option>';
        result.result.forEach(function(w) {
          const opt = document.createElement("option");
          opt.value = w.slug;
          opt.textContent = (w.name || w.slug) + ' (' + w.slug + ')';
          sel.appendChild(opt);
        });
        if (result.result.length > 0) {
          sel.value = result.result[0].slug;
          await loadProjects();
        }
      }
    } catch (e) {
      console.error("loadWorkspaces:", e);
    }
  }

  async function loadProjects() {
    var workspace = ($("workspaceSelect") && $("workspaceSelect").value) || '';
    if (!workspace) {
      setStatus("Error: workspace required");
      return;
    }
    setStatus("Loading...");
    try {
      const result = await api("/api/tool", {
        tool: "project.list",
        arguments: { workspace: workspace }
      });
      if (result.ok && Array.isArray(result.result)) {
        window.allProjects = result.result;
        var sel = $("projectSelect");
        if (!sel) return;
        var curVal = sel.value;
        sel.innerHTML = '<option value="">--</option>';
        result.result.forEach(function(p) {
          var opt = document.createElement("option");
          opt.value = p.slug;
          opt.textContent = (p.title || p.slug) + ' (' + p.slug + ')';
          sel.appendChild(opt);
        });
        if (curVal && result.result.find(function(p) { return p.slug === curVal; })) {
          sel.value = curVal;
        }
        setStatus("Loaded");
      } else {
        setStatus("Error");
      }
    } catch (e) {
      setStatus("Error");
      console.error(e);
    }
  }

  window.loadWorkspaces = loadWorkspaces;
  window.loadProjects = loadProjects;

  // Bind workspaceSelect onchange
  document.addEventListener('DOMContentLoaded', function() {
    var sel = $("workspaceSelect");
    if (sel) {
      sel.addEventListener('change', function() {
        window.currentWs = sel.value || "default";
        loadProjects();
      });
    }
  });

})();