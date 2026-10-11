# 系统管理页面

## sys-backup-page.js

备份管理页面。

### 功能

- 查看备份记录列表
- 创建备份
- 备份计划管理

### 使用的 MCP 工具

- `backup.create` — 创建备份
- `backup.list` — 列出备份

---

## sys-cache-page.js

Redis 缓存管理页面。

### 功能

- Redis 健康状态展示
- 缓存统计信息
- 缓存预热 (`cache.warm`)
- 缓存失效 (`cache.invalidate`)

### 使用的 MCP 工具

- `cache.health` — 缓存健康检查
- `cache.get_stats` — 获取统计
- `cache.warm` — 预热缓存
- `cache.invalidate` — 失效缓存

---

## users-page.js

用户管理页面（仅 admin 可见）。

### 功能

- 用户列表 (`user.list`)
- 创建用户 (`user.create`)
- 更新用户 (display_name, email, remark, status) (`user.update`)
- 删除用户 (`user.delete`)
- 注册开关 (`auth.allow_registration` 系统设置)

### 使用的 MCP 工具

- `user.list` — 列出用户
- `user.create` — 创建用户
- `user.update` — 更新用户
- `user.delete` — 删除用户

---

## template-list-page.js

提示词模板标准 CRUD 页面 (PAGE_CONFIG 模式)。

### 配置

```javascript
PAGE_CONFIG = {
  pageId: 'template-list',
  pageName: '模板管理',
  columns: [
    { key: 'name', header: '模板名称' },
    { key: 'template_type', header: '类型', type: 'badge' },
    { key: 'description', header: '描述', type: 'truncate' },
    { key: 'updated_at', header: '更新时间', type: 'date' }
  ],
  filters: [{ key: 'template_type', options: ['全部','system','user'] }],
  formFields: [
    { key: 'name', type: 'text', required: true },
    { key: 'template_key', type: 'text', required: true },
    { key: 'template_type', type: 'select', required: true },
    { key: 'description', type: 'textarea', rows: 2 },
    { key: 'template_content', type: 'textarea', rows: 10, required: true, monospace: true }
  ]
};
```

### 业务键

使用 `template_key` 而非 UUID 进行 editelete/get 操作。

### 使用的 MCP 工具

- `prompt.template.list` — 列出模板 (自动注入 project)
- `prompt.template.get` — 获取模板详情
- `prompt.template.upsert` — 创建/更新模板
- `prompt.template.delete` — 删除模板

---

## model-profiles-page.js

模型配置 CRUD 页面。

### 功能

- 模型列表（provider, model_name, status, task_types）
- 添加/编辑模型配置
- **每任务温度滑块**: 为每个 task_type 单独设置 temperature
- 激活/停用模型

### 使用的 MCP 工具

- `model.profile.list` — 列出模型
- `model.profile.upsert` — 创建/更新模型
- 删除用 `model.profile.upsert(status='inactive')` 软删除

---

## model-routes-page.js

模型路由配置页面。

### 使用的 MCP 工具

- 模型路由相关工具

---

## model-rate-limits-page.js

模型速率限制配置页面。

---

## connection-page.js

连接状态页面，显示与各服务的连接状态。

---

## health-page.js

系统健康检查页面，调用 `system.health` 展示服务状态。

---

## debug-page.js

调试面板，显示系统运行时信息。

---

## api-tokens-page.js

API Token 管理页面。

### 功能

- 列出 API Tokens
- 创建新 Token
- 删除 Token

### 使用的 MCP 工具

- `auth.create_api_token` — 创建 token
- 相关 list/delete 工具

---

## audit-logs-page.js

审计日志页面，只读展示操作记录。

---

## sync-status-page.js

数据同步状态页面。

---

## sync-conflicts-page.js

同步冲突解决页面，处理多端同步产生的数据冲突。

---

## offline-status-page.js

离线状态页面，显示离线模式和缓存数据状态。