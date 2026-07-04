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

})();