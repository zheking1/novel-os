# 故事实体和章节页面

## entities-list-page.js

实体列表页面，支持 8 种实体类型和生命周期状态过滤。

### 实体类型

`state.entity.list` 的 `entity_type` 参数支持: character, location, faction, event, item, concept, organization, race

### 生命周期状态

- `active` — 活跃
- `inactive` — 不活跃
- `deceased` — 已故
- `destroyed` — 已销毁
- `archived` — 已归档
- `planned` — 计划中

### 过滤逻辑

页面对工具调用的过滤参数:
```javascript
state.entity.list(workspace, project, entity_type?, lifecycle_status?, query?, tags?)
```

---

## entity-detail-page.js

实体详情页面，双栏布局。

### 布局

- **左栏**: 实体基本信息 (name, description, profile, aliases, tags, importance, lifecycle_status)
- **右栏**:
  - 快照时间线 (`state.snapshot.list`)
  - 关系管理 (`state.relationship.list/upsert`)

### 交互

- 查看/创建快照
- 管理实体间关系

---

## project-characters-page.js

角色专用视图，实际上是 `state.entity.list` 过滤 `entity_type='character'`。

---

## project-factions-page.js

势力专用视图，`entity_type='faction'`。

---

## project-world-rules-page.js

世界观规则页面，`entity_type` 可能为 world_rule 或类似类型。

---

## project-world-state-page.js

世界状态页面，展示项目世界观的当前状态快照。

---

## chapters-page.js

章节列表页面。

### 功能

- 列出项目的所有章节 (`local.chapter.list`)
- 显示章节号、状态、字数等
- 可能支持章节内容的查看

### 使用的 MCP 工具

- `local.chapter.list` — 带 workspace, project, limit 参数