/**
 * Novel OS - Genre-Category Binding Matrix
 */
;(function() {
  'use strict';
  var bData = {}, bGenres = [], bCats = [];

  window.loadBindingPage = async function() {
    setStatus('Loading...');
    var ws = 'default';
    var wsEl = document.getElementById('workspaceSelect');
    if (wsEl && wsEl.value) ws = wsEl.value;
    try {
      var results = await Promise.all([
        api('/api/tool',{tool:'setting.genre.list',arguments:{}}),
        api('/api/tool',{tool:'setting.category.list',arguments:{workspace:ws}}),
        api('/api/tool',{tool:'genre.binding.matrix',arguments:{}})
      ]);
      if (results[0].ok) bGenres = results[0].result || [];
      if (results[1].ok) bCats = results[1].result || [];
      if (results[2].ok && results[2].result && results[2].result.matrix)
        bData = results[2].result.matrix;
      render();
      setStatus('');
    } catch(e) { setStatus('Failed: '+e.message); }
  };

  function render() {
    var t = document.getElementById('bindingMatrix');
    var th = t.querySelector('thead tr');
    th.innerHTML = '<th>Category</th>';
    bGenres.forEach(function(g) {
      th.innerHTML += '<th style="font-size:11px;">' + escapeHtml(g.genre||g.name||g.slug) + '</th>';
    });
    var body = '';
    bCats.forEach(function(cat) {
      body += '<tr><td>' + escapeHtml(cat.name) + '<br><small>' + escapeHtml(cat.slug) + '</small></td>';
      bGenres.forEach(function(g) {
        var k = (g.slug||g.genre) + '||' + (cat.id||cat.slug) + '||all';
        var checked = bData[k] ? 'checked' : '';
        body += '<td style="text-align:center;"><input type="checkbox" data-genre="' + (g.slug||g.genre) + '" data-cat="' + (cat.id||cat.slug) + '" ' + checked + ' onchange="window.toggleBind(this)"></td>';
      });
      body += '</tr>';
    });
    t.querySelector('tbody').innerHTML = body;
  }

  window.toggleBind = function(cb) {
    bData[cb.dataset.genre + '||' + cb.dataset.cat + '||all'] = cb.checked;
  };

  window.saveAllBindings = async function() {
    var arr = [];
    document.querySelectorAll('#bindingMatrix input[type=checkbox]').forEach(function(cb) {
      arr.push({genre:cb.dataset.genre, category:cb.dataset.cat, is_required:cb.checked});
    });
    if (!arr.length) { showToast('warning','No data'); return; }
    setStatus('Saving...');
    var r = await api('/api/tool',{tool:'genre.binding.bulk_upsert',arguments:{bindings:arr}});
    if (r.ok) showToast('success','Saved');
    setStatus('');
  };
})();