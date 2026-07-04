/**
 * Novel OS - Review Module
 */
;(function() {
  'use strict';

  window.renderReviewList = function(reviews) {
    var container = window.$("reviewListResult");
    if (!reviews || reviews.length === 0) {
      container.innerHTML = '<p style="color:var(--muted);text-align:center;padding:20px;">No reviews</p>';
      return;
    }
    container.innerHTML = reviews.map(function(r) {
      return '<div class="list-item" onclick="window.selectReviewItem(\'' + r.id + '\')">' +
        '<div class="list-item-header"><span>Review ' + (r.chapter_no || r.id) + '</span></div>' +
        '<div class="list-item-meta">' + (r.status || '') + ' | ' + (r.created_at || '') + '</div></div>';
    }).join("");
  };

  window.renderReviewDetail = function(review) {
    if (!review) return;
    window.$("reviewDetailTitle").textContent = 'Review: ' + (review.chapter_no || review.id);
    window.$("reviewDetailContent").innerHTML = 
      '<pre style="font-size:12px;background:var(--bg);padding:12px;border-radius:6px;overflow-x:auto;">' + 
      window.JSON.stringify(review, null, 2) + '</pre>';
  };

  window.renderRevisionTasks = function(tasks) {
    var container = window.$("revisionTasksResult");
    if (!tasks || tasks.length === 0) {
      container.innerHTML = '<p style="color:var(--muted);">No revision tasks</p>';
      return;
    }
    container.innerHTML = tasks.map(function(t) {
      return '<div class="list-item">' +
        '<div class="list-item-header"><span>' + (t.title || 'Task') + '</span></div>' +
        '<div class="list-item-meta">' + (t.severity || '') + ' | ' + (t.status || '') + '</div></div>';
    }).join("");
  };

  window.renderCouncilConfigs = function(configs) {
    var container = window.$("councilConfigsResult");
    if (!configs || configs.length === 0) {
      container.innerHTML = '<p style="color:var(--muted);">No council configs</p>';
      return;
    }
    container.innerHTML = configs.map(function(c) {
      return '<div class="list-item">' +
        '<div class="list-item-header"><span>' + (c.name || 'Config') + '</span></div>' +
        '</div>';
    }).join("");
  };
})();