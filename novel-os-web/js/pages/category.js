/**
 * Novel OS - Category Manager
 */
;(function() {
  'use strict';
  var cats = [];

  window.loadCategoryManage = async function() {
    setStatus('Loading...');
    try {
      var ws = 'default';
      var wsEl = document.getElementById('workspaceSelect');
      if (wsEl && wsEl.value) ws = wsEl.value;
      var r = await api('/api/tool',{tool:'setting.category.list',arguments:{workspace:ws}});
      if (r.ok) { cats = r.result || []; render(); setStatus(''); }
    } catch(e) { setStatus('Failed: '+e.message); }
  };

  function render() {
    var el = document.getElementById('categoryList');
    if (!el) return;
    if (!cats.length) { el.innerHTML = '<p class="empty-state">暂无分类</p>'; return; }
    var h = '';
    cats.forEach(function(c) {
      var cid = c.id || c.slug;
      h += '<div class="list-item"><div class="list-item-header">' +
        '<span style="font-weight:500;">' + escapeHtml(c.icon||'📁') + ' ' + escapeHtml(c.name) + '</span>' +
        '<span class="badge">' + escapeHtml(c.slug) + '</span></div>' +
        '<div class="list-item-meta">' + escapeHtml(c.description||'') + '</div>' +
        '<div class="list-item-meta" style="color:var(--accent)">' + escapeHtml((c.metadata&&c.metadata.type_description)||'') + '</div>' +
        '<div class="actions"><button class="btn btn-sm" onclick="window.showCategoryForm(\'' + escapeHtml(cid) + '\')">Edit</button>' +
        '<button class="btn btn-sm btn-danger" onclick="window.deleteCategory(\'' + escapeHtml(cid) + '\',' + (c.is_standard||false) + ')">Delete</button></div></div>';
    });
    el.innerHTML = h;
  }

  window.showCategoryForm = function(catId) {
    var c = catId ? cats.find(function(x){return(x.id||x.slug)===catId;}) : {};
    showModal(
      '<div class="modal-content"><h3>'+(catId?'Edit':'New')+' Category</h3>' +
      '<div class="form-group"><label>Slug</label><input id="cSlug" value="'+escapeHtml(c.slug||'')+'" '+(catId?'readonly':'')+'></div>' +
      '<div class="form-group"><label>Name</label><input id="cName" value="'+escapeHtml(c.name||'')+'"></div>' +
      '<div class="form-group"><label>Icon</label><input id="cIcon" value="'+escapeHtml(c.icon||'')+'"></div>' +
      '<div class="form-group"><label>Description</label><textarea id="cDesc" rows="2">'+escapeHtml(c.description||'')+'</textarea></div>' +
      '<div class="form-group"><label>Type Description (what levels/data this category stores)</label><textarea id="cTypeDesc" rows="3">'+escapeHtml((c.metadata&&c.metadata.type_description)||'')+'</textarea></div>' +
      '<div class="modal-actions"><button class="btn" onclick="window.saveCategory()">Save</button>' +
      '<button class="btn" onclick="closeModal()">Cancel</button></div></div>'
    );
  };

  window.saveCategory = async function() {
    var s = document.getElementById('cSlug').value.trim();
    var n = document.getElementById('cName').value.trim();
    if (!s || !n) { showToast('warning','Fill slug and name'); return; }
    var ws = 'default';
    var wsEl = document.getElementById('workspaceSelect');
    if (wsEl && wsEl.value) ws = wsEl.value;
    setStatus('Saving...');
    var r = await api('/api/tool',{tool:'setting.category.upsert',arguments:{
      workspace:ws, slug:s, name:n,
      icon:document.getElementById('cIcon').value||'📁',
      description:document.getElementById('cDesc').value.trim(),
      metadata:{type_description:document.getElementById('cTypeDesc').value.trim()}
    }});
    if (r.ok) { showToast('success','Saved'); closeModal(); loadCategoryManage(); }
  };

  window.deleteCategory = async function(catId, isStandard) {
    if (isStandard) { showToast('warning','Cannot delete standard category'); return; }
    if (!confirm('Delete?')) return;
    var ws = 'default';
    var wsEl = document.getElementById('workspaceSelect');
    if (wsEl && wsEl.value) ws = wsEl.value;
    var r = await api('/api/tool',{tool:'setting.category.delete',arguments:{workspace:ws,category_id:catId}});
    if (r.ok) { showToast('success','Deleted'); loadCategoryManage(); }
  };
})();