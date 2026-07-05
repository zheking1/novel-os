# Novel OS Web Client - Troubleshooting Guide

## Common Issues and Solutions

### 1. "structured_content must be a dict or None" Error

**Symptom**: MCP tool call returns error about `structured_content`.

**Cause**: The MCP tool returns a non-dict value (e.g., `bool`, `str`, `list`).

**Fix**: Wrap the return value in a dict:
```python
# WRONG
return await service.delete(project_id, key)  # Returns bool

# CORRECT
deleted = await service.delete(project_id, key)
return {"ok": deleted, "key": key}
```

---

### 2. Page Shows Placeholder Instead of Content

**Symptom**: Navigating to a page shows "Coming soon" or placeholder text.

**Cause**: The page's `init()` method returns `undefined` instead of `true`.

**Fix**: Ensure `init()` returns `true`:
```javascript
init() {
  this.render();
  this.loadData();
  return true;  // CRITICAL
}
```

---

### 3. Delete Button Sends Wrong ID

**Symptom**: Delete fails silently or deletes wrong item.

**Cause**: Using `item.id` (UUID) instead of `item.template_key` (business key).

**Fix**: Use the business key for API calls:
```javascript
// WRONG - sends UUID
onclick="handleDelete('${item.id || item.template_key}')"

// CORRECT - sends template_key
onclick="handleDelete('${item.template_key}')"
```

---

### 4. Modal Dialog Not Centered

**Symptom**: Modal appears at top-left or offset from center.

**Cause**: `sm:block` Tailwind class overrides flex centering at ≥640px.

**Fix**: Use simple flex centering without responsive overrides:
```html
<!-- WRONG -->
<div class="flex min-h-screen items-center justify-center sm:block sm:p-0">

<!-- CORRECT -->
<div class="fixed inset-0 z-50 flex items-center justify-center p-4">
```

Also ensure modal content has `z-10` to sit above the backdrop:
```html
<div class="max-w-lg w-full relative z-10 bg-white rounded-2xl shadow-xl">
```

---

### 5. MCP Tool Not Found

**Symptom**: `Error calling tool 'xxx.xxx.xxx': Tool not found`

**Cause**: MCP container hasn't been rebuilt after adding/changing tools.

**Fix**: Rebuild MCP container:
```bash
plink -batch -pw "${NAS_SSH_PASSWORD}" root@${NAS_HOST} "cd /opt/novel-os && docker compose -f docker-compose.yml -f docker-compose.app.example.yml up -d --build novel-os-mcp"
```

---

### 6. Container Restart Loses Changes

**Symptom**: File changes disappear after container restart.

**Cause**: Files were modified inside the container, not in the source directory.

**Fix**: Always:
1. Upload to source directory first (`/opt/novel-os/novel-os-web/...`)
2. Then rebuild the container

---

### 7. Login Fails After SPA Migration

**Symptom**: Login screen shows but authentication doesn't persist.

**Cause**: The SPA doesn't check auth status on load.

**Fix**: Ensure `app-core.js` calls `/api/me` on load:
```javascript
async function checkAuth() {
  try {
    const resp = await fetch('/api/me');
    if (resp.ok) {
      const data = await resp.json();
      window.AppState.username = data.username;
      // Show main app
    }
  } catch (e) {
    // Show login screen
  }
}
```

---

### 8. Workspace/Project Selection Lost on Refresh

**Symptom**: After page refresh, workspace/project dropdowns reset.

**Cause**: Selections not persisted to localStorage.

**Fix**: Save to localStorage on change, restore on init:
```javascript
// Save
localStorage.setItem('novel-workspace', workspace);
localStorage.setItem('novel-project', project);

// Restore
window.AppState.currentWorkspace = localStorage.getItem('novel-workspace');
window.AppState.currentProject = localStorage.getItem('novel-project');
```

---

### 9. `init()` Called But Page Not Rendered

**Symptom**: `init()` runs but content area stays empty.

**Cause**: `init()` returns before `render()` completes, or `render()` finds no `content-area` element.

**Fix**: Ensure `render()` targets the correct element:
```javascript
render() {
  const contentArea = document.getElementById('content-area');
  if (!contentArea) return;
  contentArea.innerHTML = `...`;
}
```

---

### 10. API Response Format Mismatch

**Symptom**: Data loads but table shows empty.

**Cause**: API returns `{templates: [...]}` but code expects raw array.

**Fix**: Handle all response formats in `loadData()`:
```javascript
if (Array.isArray(result)) {
  this.currentData = result;
} else if (result?.templates) {
  this.currentData = result.templates;
} else if (result?.items) {
  this.currentData = result.items;
} else if (result?.data) {
  this.currentData = result.data;
} else {
  this.currentData = [];
}
```

---

### 11. Chinese Characters Garbled in PowerShell

**Symptom**: plink/plink output shows `???` or mojibake for Chinese text.

**Cause**: PowerShell encoding mismatch with plink.

**Solution**: Use `plink` with `-raw` flag or redirect to file and read separately. Avoid piping Chinese text through plink.

---

### 12. `docker compose` vs `docker-compose`

**Symptom**: `docker-compose` command not found.

**Cause**: NAS uses Docker Compose v2 (plugin syntax).

**Fix**: Use `docker compose` (no hyphen):
```bash
# WRONG
docker-compose up -d

# CORRECT
docker compose up -d
```

---

## Debugging Tips

### Check MCP Tool Registration
```bash
plink -batch -pw "${NAS_SSH_PASSWORD}" root@${NAS_HOST} "docker logs novel-os-mcp 2>&1 | tail -20"
```

### Check Database Contents
```bash
plink -batch -pw "${NAS_SSH_PASSWORD}" root@${NAS_HOST} "docker exec novel-postgres psql -U novel_os -d novel_os -c 'SELECT id, template_key, name FROM prompt_templates;'"
```

### Check Container Status
```bash
plink -batch -pw "${NAS_SSH_PASSWORD}" root@${NAS_HOST} "docker ps --format 'table {{.Names}}\t{{.Status}}'"
```

### View Web Container Logs
```bash
plink -batch -pw "${NAS_SSH_PASSWORD}" root@${NAS_HOST} "docker logs novel-os-web 2>&1 | tail -30"
```
