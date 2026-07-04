/**
 * Novel OS - Genre Manager
 */
;(function() {
  'use strict';
  var genres = [];

  window.loadGenreManage = async function() {
    setStatus('Loading...');
    try {
      var r = await api('/api/tool', {tool:'setting.genre.list',arguments:{}});
      if (r.ok) { genres = r.result || []; render(); setStatus(''); }
    } catch(e) { setStatus('Failed: '+e.message); }
  };

  function render() {
    var el = document.getElementById('genreList');
    if (!el) return;
    if (!genres.length) { el.innerHTML = '<p class="empty-state">暂无类型</p>'; return; }
    var h = '';
    genres.forEach(function(g) {
      var s = g.slug || g.genre || '';
      h += '<div class="list-item"><div class="list-item-header">' +
        '<span style="font-weight:500;">' + escapeHtml(g.name || s) + '</span>' +
        '<span class="badge">' + escapeHtml(s) + '</span></div>' +
        '<div class="list-item-meta">' + escapeHtml(g.description||'') + '</div>' +
        '<div class="actions"><button class="btn btn-sm" onclick="window.showGenreForm(\'' + escapeHtml(s) + '\')">Edit</button>' +
        '<button class="btn btn-sm btn-danger" onclick="window.deleteGenre(\'' + escapeHtml(s) + '\')">Delete</button></div></div>';
    });
    el.innerHTML = h;
  }

  window.showGenreForm = function(slug) {
    var g = slug ? genres.find(function(x){return(x.slug||x.genre)===slug;}) : {};
    showModal(
      '<div class="modal-content"><h3>'+(slug?'Edit':'New')+' Genre</h3>' +
      '<div class="form-group"><label>Slug</label><input id="gSlug" value="'+escapeHtml(g.slug||g.genre||'')+'"></div>' +
      '<div class="form-group"><label>Name</label><input id="gName" value="'+escapeHtml(g.name||'')+'"></div>' +
      '<div class="form-group"><label>Description</label><textarea id="gDesc" rows="3">'+escapeHtml(g.description||'')+'</textarea></div>' +
      '<div class="form-group"><label>Aliases (comma separated)</label><input id="gAliases" value="'+escapeHtml((g.aliases||[]).join(','))+'"></div>' +
      '<div class="form-group"><label>Typical Elements (comma)</label><input id="gElements" value="'+escapeHtml((g.typical_elements||[]).join(','))+'"></div>' +
      '<div class="modal-actions"><button class="btn" onclick="window.saveGenre()">Save</button>' +
      '<button class="btn" onclick="closeModal()">Cancel</button></div></div>'
    );
  };

  window.saveGenre = async function() {
    var s = document.getElementById('gSlug').value.trim();
    var n = document.getElementById('gName').value.trim();
    if (!s || !n) { showToast('warning','Fill slug and name'); return; }
    setStatus('Saving...');
    var r = await api('/api/tool',{tool:'setting.genre.upsert',arguments:{
      slug:s, name:n, description:document.getElementById('gDesc').value.trim(),
      aliases:(document.getElementById('gAliases').value||'').split(',').map(function(v){return v.trim();}).filter(Boolean),
      typical_elements:(document.getElementById('gElements').value||'').split(',').map(function(v){return v.trim();}).filter(Boolean)
    }});
    if (r.ok) { showToast('success','Saved'); closeModal(); loadGenreManage(); }
  };

  window.deleteGenre = async function(slug) {
    if (!confirm('Delete '+slug+'?')) return;
    var r = await api('/api/tool',{tool:'setting.genre.delete',arguments:{slug:slug}});
    if (r.ok) { showToast('success','Deleted'); loadGenreManage(); }
  };
})();