# 常见问题排查

## 1. "structured_content must be a dict or None" 错误

**症状**: MCP 工具调用返回 structured_content 错误。

**原因**: 工具返回了非 dict 值（如 `bool`, `str`, `list`）。

**修复**: 包装为 dict:
```python
# 错误
return await service.delete(project_id, key)  # 返回 bool

# 正确
deleted = await service.delete(project_id, key)
return {"ok": deleted, "key": key}
```

---

## 2. 页面显示占位符而非内容

**症状**: 导航到页面显示 "Coming soon" 或占位符。

**原因**: `init()` 未返回 `true`。

**修复**: `init()` 最后加 `return true;`

---

## 3. 删除按钮发送了错误的 ID

**症状**: 删除静默失败或删错。

**原因**: 用了 `item.id`（UUID）而非 `item.template_key`（业务键）。

**修复**: 使用业务键: `handleDelete('${item.template_key}')`

---

## 4. 弹窗未居中

**症状**: 弹窗出现在左上角或偏移。

**原因**: Tailwind `sm:block` 覆盖了 flex 居中。

**修复**:
```html
<!-- 错误 -->
<div class="flex min-h-screen items-center justify-center sm:block">

<!-- 正确 -->
<div class="fixed inset-0 z-50 flex items-center justify-center p-4">
```

弹窗内容需 `z-10`:
```html
<div class="max-w-lg w-full relative z-10 bg-white rounded-2xl shadow-xl">
```

---

## 5. MCP 工具未找到

**症状**: `Error calling tool 'xxx': Tool not found`

**原因**: MCP 容器未重建。

**修复**: 重建 MCP 容器（见部署命令）

---

## 6. 容器重启丢失修改

**症状**: 文件修改在容器重启后消失。

**原因**: 在容器内直接编辑。

**修复**: 始终先上传到源目录，再重建。

---

## 7. SPA 迁移后登录失败

**症状**: 登录页面显示但认证不持久。

**原因**: SPA 未在加载时检查认证状态。

**修复**: `app-core.js` 应调用 `/api/me` 检查。

---

## 8. 刷新后工作区/项目丢失

**症状**: 刷新后下拉框重置。

**原因**: 未持久化到 localStorage。

**修复**:
```javascript
localStorage.setItem('novel-workspace', workspace);
localStorage.setItem('novel-project', project);
```

---

## 9. init() 执行但页面空白

**症状**: init() 运行但无内容。

**原因**: render() 未能找到 `content-area`。

**修复**: `render()` 需先检查元素存在。

---

## 10. API 响应格式不匹配

**症状**: 数据加载但表格为空。

**原因**: API 返回 `{templates: [...]}` 但代码期望数组。

**修复**: loadData() 处理所有响应格式:
```javascript
if (Array.isArray(result)) { ... }
else if (result?.templates) { ... }
else if (result?.items) { ... }
else if (result?.data) { ... }
```

---

## 11. PowerShell 中文乱码

**症状**: plink 输出中文显示 `???`。

**解决方案**: 使用 `-raw` 参数或重定向到文件。

---

## 12. docker compose vs docker-compose

**症状**: `docker-compose` 命令不存在。

**原因**: NAS 使用 Compose v2。

**修复**: 使用 `docker compose`（无连字符）。

## 调试技巧

### 检查 MCP 工具注册
```bash
docker logs novel-os-mcp 2>&1 | tail -20
```

### 检查数据库内容
```bash
docker exec novel-postgres psql -U novel_os -d novel_os -c 'SELECT id, template_key, name FROM prompt_templates;'
```

### 查看容器状态
```bash
docker ps --format 'table {{.Names}}\t{{.Status}}'
```

### 查看 Web 日志
```bash
docker logs novel-os-web 2>&1 | tail -30
```