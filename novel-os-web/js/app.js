/**
 * Novel OS Web Client - Application Core
 */
;(function() {
  'use strict';

  // ===== $() =====
  const $ = (id) => document.getElementById(id);

  // ===== escapeHtml() =====
  function escapeHtml(str) {
    if (!str) return '';
    return String(str).replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;').replace(/"/g, '&quot;').replace(/'/g, '&#39;');
  }
  window.escapeHtml = escapeHtml;

  // ===== api() =====
  async function api(path, body) {
    try {
      const options = body ? {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(body)
      } : {};
      const response = await fetch(path, options);
      if (!response.ok) {
        var errText = await response.text().catch(function() { return response.statusText; });
        window.showToast("error", "请求失败 (" + response.status + ")", errText.substring(0, 200));
        return { error: errText };
      }
      var data = await response.json();
      if (data && data.error) {
        window.showToast("error", "API 错误", typeof data.error === "string" ? data.error : JSON.stringify(data.error).substring(0, 200));
      }
      return data;
    } catch (e) {
      window.showToast("error", "网络错误", e.message);
      return { error: e.message };
    }
  }
  window.api = api;

  // ===== showToast() =====
  function showToast(type, title, msg, duration) {
    duration = duration || 4000;
    var container = $("toastContainer");
    if (!container) return;
    var icons = { success: "✓", error: "✕", warning: "⚠", info: "ℹ" };
    var el = document.createElement("div");
    el.className = "toast " + type;
    el.innerHTML = '<span class="toast-icon">' + (icons[type] || "ℹ") + '</span>' +
      '<div class="toast-body"><div class="toast-title">' + escapeHtml(title) + '</div>' +
      (msg ? '<div class="toast-msg">' + escapeHtml(msg) + '</div>' : '') + '</div>' +
      '<button class="toast-close" onclick="this.parentElement.remove()">×</button>';
    container.appendChild(el);
    setTimeout(function() { el.classList.add("removing"); setTimeout(function() { el.remove(); }, 300); }, duration);
  }
  window.showToast = showToast;

  // ===== setStatus() =====
  function setStatus(text) {
    var el = $("statusMessage");
    if (el) { el.textContent = text; }
  }
  window.setStatus = setStatus;


  // ===== show() =====
  function show(id) {
    var el = document.getElementById(id);
    if (el) { el.classList.remove("hidden"); el.style.display = ""; }
  }
  window.show = show;

  // ===== t() =====
  function t(key) {
    var text = window.i18nTexts || {};
    return text[key] || key;
  }
  window.t = t;

  // ===== applyLanguage() =====
  function applyLanguage(language) {
    currentLanguage = language;
    window.i18nTexts = window.i18nData ? window.i18nData[language] : {};
    document.querySelectorAll("[data-i18n]").forEach(function(el) {
      var key = el.getAttribute("data-i18n");
      if (window.i18nTexts && window.i18nTexts[key]) {
        if (el.tagName === "INPUT" && el.type === "text") {
          el.placeholder = window.i18nTexts[key];
        } else {
          el.textContent = window.i18nTexts[key];
        }
      }
    });
  }
  window.applyLanguage = applyLanguage;

  // ===== parseJson() =====
  function parseJson(str) {
    try { return JSON.parse(str); } catch(e) { return null; }
  }
  window.parseJson = parseJson;

  // ===== parseCsv() =====
  function parseCsv(str) {
    if (!str) return [];
    var rows = str.trim().split("\n");
    if (rows.length < 2) return [];
    var headers = rows[0].split(",").map(function(h) { return h.trim(); });
    return rows.slice(1).map(function(row) {
      var obj = {};
      var cols = row.split(",");
      headers.forEach(function(h, i) { obj[h] = (cols[i] || "").trim(); });
      return obj;
    });
  }
  window.parseCsv = parseCsv;

  // ===== buildTree() =====
  function buildTree(items, idField, parentField, childrenField) {
    var tree = [];
    var map = {};
    items.forEach(function(item) { map[item[idField]] = item; item[childrenField] = []; });
    items.forEach(function(item) {
      var parent = map[item[parentField]];
      if (parent) { parent[childrenField].push(item); }
      else { tree.push(item); }
    });
    return tree;
  }
  window.buildTree = buildTree;

  // ===== renderMarkdown() =====
  function renderMarkdown(text) {
    if (!text) return "";
    return text
      .replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>')
      .replace(/\*(.*?)\*/g, '<em>$1</em>')
      .replace(/`(.*?)`/g, '<code>$1</code>')
      .replace(/^### (.*$)/gm, '<h3>$1</h3>')
      .replace(/^## (.*$)/gm, '<h2>$1</h2>')
      .replace(/^# (.*$)/gm, '<h1>$1</h1>')
      .replace(/^\- (.*$)/gm, '<li>$1</li>')
      .replace(/\n\n/g, '<br><br>');
  }
  window.renderMarkdown = renderMarkdown;

})();