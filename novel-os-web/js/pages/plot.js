/**
 * Novel OS - Plot Module (Volumes, Threads, Foreshadowing)
 */
;(function() {
  'use strict';

  window.renderVolumes = function(volumes) {
    var container = window.$("volumesResult");
    if (!volumes || volumes.length === 0) {
      container.innerHTML = '<p style="color:var(--muted);text-align:center;padding:20px;">No volumes</p>';
      return;
    }
    container.innerHTML = volumes.map(function(v) {
      return '<div class="list-item" onclick="window.selectVolume(' + v.volume_no + ')">' +
        '<div class="list-item-header"><span>Vol. ' + v.volume_no + ': ' + (v.title || 'Untitled') + '</span></div>' +
        '<div class="list-item-meta">Ch. ' + (v.start_chapter_no || '-') + ' - ' + (v.end_chapter_no || '-') + '</div></div>';
    }).join("");
  };

  window.renderThreads = function(threads) {
    var container = window.$("threadsResult");
    if (!threads || threads.length === 0) {
      container.innerHTML = '<p style="color:var(--muted);text-align:center;padding:20px;">No threads</p>';
      return;
    }
    container.innerHTML = threads.map(function(t) {
      return '<div class="list-item" onclick="window.selectThread(\'' + t.key + '\')">' +
        '<div class="list-item-header"><span>' + (t.title || t.key) + '</span></div>' +
        '<div class="list-item-meta">Type: ' + (t.thread_type || '') + ' | Status: ' + (t.status || '') + '</div></div>';
    }).join("");
  };

  window.renderChapterPlans = function(plans) {
    var container = window.$("chapterPlansResult");
    if (!plans || plans.length === 0) {
      container.innerHTML = '<p style="color:var(--muted);text-align:center;padding:20px;">No chapter plans</p>';
      return;
    }
    container.innerHTML = plans.map(function(p) {
      return '<div class="list-item">' +
        '<div class="list-item-header"><span>Chapter ' + p.chapter_no + '</span></div>' +
        '</div>';
    }).join("");
  };

  window.renderForeshadowingKanban = function(items) {
    var board = window.$("foreshadowingKanban");
    if (!board) return;
    if (!items || items.length === 0) {
      board.innerHTML = '<p style="color:var(--muted);text-align:center;padding:20px;">No foreshadowing items</p>';
      return;
    }
    board.innerHTML = items.map(function(item) {
      return '<div class="list-item" onclick="window.openForeshadowingDetail(\'' + item.key + '\')">' +
        '<div class="list-item-header"><span>[' + item.key + '] ' + (item.title || '') + '</span></div>' +
        '<div class="list-item-meta">Status: ' + (item.status || '') + ' | ' + (item.importance || '') + '</div></div>';
    }).join("");
  };
})();