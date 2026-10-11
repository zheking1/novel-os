# 剧情管理页面

## plot-volumes-page.js

卷 (Volume) CRUD 页面。

### 功能

- 列出项目的所有卷
- 创建/编辑/删除卷
- **特殊处理**: goals 字段 textarea 输入，回车分隔 → 数组存储

```javascript
// goals textarea 处理
const goals = document.getElementById('volume-goals').value
  .split('\n')
  .map(s => s.trim())
  .filter(Boolean);

await ApiClient.callTool('volume.upsert', { workspace, project, slug, title, goals, ... });
```

### 使用的 MCP 工具

- `volume.list` — 列出卷
- `volume.upsert` — 创建/更新卷
- `volume.delete` — 删除卷
- `volume.get` — 获取单个卷详情

---

## plot-threads-page.js

情节线 (Thread) 管理页面。

### 功能

- 列出项目的情节线
- 创建/编辑/删除情节线
- **停滞检测**: 调用 `plot.thread.check_stalled` 检查情节线是否停滞
- **推进情节线**: 调用 `plot.thread.advance` 标记进展

### 使用的 MCP 工具

- `plot.thread.list` — 列出情节线
- `plot.thread.upsert` — 创建/更新情节线
- `plot.thread.delete` — 删除情节线
- `plot.thread.advance` — 推进情节线
- `plot.thread.check_stalled` — 检测停滞

---

## foreshadowing-list-page.js (451行)

伏笔管理页面，功能最丰富的剧情管理页面。

### 功能

- 伏笔列表，支持多层筛选
- 创建/编辑伏笔 (含 layer, importance, must_payoff, payoff_deadline 等参数)
- **回收工作流**: 标记伏笔已回收 (`foreshadowing.payoff`)
- **关联伏笔**: 链接两个伏笔 (`foreshadowing.link`)
- **过期检查**: 检查超期未回收的伏笔 (`foreshadowing.check_overdue`)

### 伏笔参数

```javascript
plot.upsert_foreshadowing(
  key, title,
  layer?,           // 伏笔层级
  importance?,      // 重要度 (critical/high/medium/low)
  status?,          // 状态
  must_payoff?,     // 是否必须回收
  payoff_deadline_chapter?,  // 回收期限章节号
  payoff_deadline_volume?,   // 回收期限卷号
  overdue_policy?   // 过期策略
)
```

### 使用的 MCP 工具

- `plot.list_foreshadowing` — 列出伏笔
- `plot.upsert_foreshadowing` — 创建/更新伏笔
- `foreshadowing.payoff` — 标记回收
- `foreshadowing.link` — 关联伏笔
- `foreshadowing.check_overdue` — 过期检查

---

## chapter-plans-page.js

章节大纲 (Chapter Plan) 卡片页面。

### 功能

- 列出/创建章节大纲
- 卡片式布局，每张卡显示章节计划信息

### 使用的 MCP 工具

- `plot.list_chapter_plans` — 列出章节大纲
- `plot.create_chapter_plan` — 创建章节大纲