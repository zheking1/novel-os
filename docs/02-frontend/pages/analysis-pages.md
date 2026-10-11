# 分析类页面

## review-tasks-page.js (460行)

审核任务管理页面，支持多维度审核工作流。

### 功能

- 审核任务列表（分页: page+pageSize, totalTasks）
- **启动审核**: 选择章节, 选择审核维度 (checkboxes), 触发 `review.start_job`
- **汇总流程**: 多维度审核结果聚合 (`review.aggregate`)
- 任务状态: pending, processing, aggregated 等

### 关键逻辑

```javascript
page: 0,
pageSize: 10,
totalTasks: 0,

// 启动审核模态框
showStartModal() {
  // 章节选择
  // 维度选择 (checkboxes)
  // 提交 → review.start_job(chapter_no, dimensions)
}
```

### 使用的 MCP 工具

- `review.list_revision_tasks` — 列表 (支持 status, limit, chapter_no 过滤)
- `review.start_job` — 启动审核
- `review.aggregate` — 汇总审核结果

---

## compliance-page.js

合规检查页面。检查内容是否符合项目规范。

---

## pacing-analysis-page.js

节奏分析页面。分析章节节奏、段落分布等。

---

## world-snapshot-page.js

世界快照页面。展示项目世界观在各时间点的状态快照。

---

## arc-characters-page.js

角色弧光分析页面。分析角色的发展轨迹。

---

## arc-tracking-page.js

弧光追踪页面。持续追踪角色弧光的推进情况。

---

## style-analysis-page.js

风格分析页面。分析文本的风格特征。

---

## style-drift-page.js

风格偏移检测页面。对比不同章节的风格一致性。

---

## style-profiles-page.js

风格配置页面。定义和管理写作风格配置。

---

## tone-management-page.js

语气管理页面。配置和管理文本的语气特征。

---

## knowledge-stats-page.js

知识统计页面。展示知识库的统计数据和指标。

---

## knowledge-review-page.js

知识审核页面。审核知识条目的准确性和时效性。

---

## knowledge-expiry-page.js

知识过期管理页面。标记和清理过期知识条目。

---

## system-evolution-page.js (450行)

系统进化提案管理页面，使用 PAGE_CONFIG 模板。

### 7 种状态

```javascript
filters: [
  { key: 'status', options: [
    '全部状态',
    'draft',      // 草稿
    'pending',    // 待审核
    'approved',   // 已通过
    'rejected',   // 已拒绝
    'implemented',// 已实施
    'rolled_back',// 已回滚
    'archived'    // 已归档
  ]}
]
```

### AI 评分

`ai_review_score` 列显示 AI 自动初审评分。

### 使用的 MCP 工具

- 进化提案相关 upsert/list 工具

---

## skill-manage-page.js

Skill 管理页面。

### 功能

- Skill 列表 (name, description, trigger_words)
- Skill Step 管理 (步骤的增删改)

### 使用的 MCP 工具

- `skill.list` — 列出 Skill
- `skill.create` / `skill.update` / `skill.delete`
- `skill.step.list` / `skill.step.add` / `skill.step.update` / `skill.step.delete`