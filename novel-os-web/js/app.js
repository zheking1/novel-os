/**
 * Novel OS Web Client - Application Core
 * Auto-generated during modularization (Step 3)
 */
;(function() {
  'use strict';

// ===== $() =====
const $ = (id) => document.getElementById(id);
    function escapeHtml(str) {

// ===== escapeHtml() =====
function escapeHtml(str) {
      if (!str) return '';
      return String(str).replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;').replace(/"/g, '&quot;').replace(/'/g, '&#39;');
    }

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
          showToast("error", "请求失败 (" + response.status + ")", errText.substring(0, 200));
          return { error: errText };
        }
        var data = await response.json();
        if (data && data.error) {
          showToast("error", "API 错误", typeof data.error === "string" ? data.error : JSON.stringify(data.error).substring(0, 200));
        }
        return data;
      } catch (e) {
        showToast("error", "网络错误", e.message);
        return { error: e.message };
      }
    }


})();
