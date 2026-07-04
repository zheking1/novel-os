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
          allWorkspaces = result.result;
          const sel = $("workspaceSelect");
          sel.innerHTML = '<option value="">-- Select --</option>';
          result.result.forEach(w => {
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

  window.loadWorkspaces = loadWorkspaces;

Status(t("msg.loaded"));
        } else {
          setStatus(t("status.error"));
        }

  window.loadProjects = loadProjects;


})();
