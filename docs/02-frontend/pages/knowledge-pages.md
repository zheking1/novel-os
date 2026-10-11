# 知识库页面

## kb-uk-list-page.js

通用知识库标准 CRUD 页面，使用 PAGE_CONFIG 模板。

### 配置

```javascript
PAGE_CONFIG = {
  pageId: 'kb-uk',
  pageName: '通用知识库',
  apiNamespace: 'kb.uk',
  columns: [
    { key: 'topic', header: '主题' },
    { key: 'category_slug', header: '分类', type: 'badge' },
    { key: 'summary', header: '摘要', type: 'truncate' },
    { key: 'reliability', header: '可信度', type: 'progress' },
    { key: 'updated_at', header: '更新时间', type: 'date' }
  ],
  filters: [{ key: 'category_slug', options: ['history','geography','culture',...] }],
  formFields: [
    { key: 'topic', type: 'text', required: true },
    { key: 'category_slug', type: 'select', required: true },
    { key: 'content', type: 'textarea', rows: 8, required: true },
    { key: 'summary', type: 'textarea', rows: 2 },
    { key: 'source', type: 'text' },
    { key: 'source_url', type: 'text' },
    { key: 'reliability', type: 'number' },
    { key: 'era', type: 'text' },
    { key: 'tags', type: 'text' }
  ]
};
```

### 工具调用

- `kb.uk.search` — 搜索通用知识 (带 category_slug+query 过滤)
- `kb.uk.create` — 创建知识条目
- `kb.uk.delete` — 删除知识条目 (使用 entry_id)

### 特殊处理

```javascript
// reliability 从字符串转数字
if (field.key === 'reliability') {
  data[field.key] = el.value ? parseFloat(el.value) : 0.5;
}
// tags 从逗号分隔字符串转数组
if (field.key === 'tags') {
  data[field.key] = el.value ? el.value.split(',').map(t => t.trim()).filter(Boolean) : [];
}
```

---

## kb-pk-list-page.js

项目知识库标准 CRUD 页面，结构与 UK 页面类似，使用 `kb.pk.list/upsert/delete` 工具。

---

## kb-search-page.js

多源知识搜索页面，支持查询高亮和多种知识源。

---

## kb-categories-page.js

知识分类管理，使用递归树渲染展示分类层级结构。

---

## kb-relations-page.js

知识实体关系管理页面。支持:
- 实体搜索
- 关系浏览

---

## knowledge-graph-page.js (1211行)

D3.js 力导向图谱可视化页面，功能最复杂的页面之一。

### 两种模式

- `mode: 'project'` — 项目级实体关系图
- `mode: 'global'` — 全局知识库关系图

### 核心功能

- **3 种布局模式**: D3.js forceSimulation
- **缩放/平移**: d3.zoom 变换
- **节点拖拽**: 拖拽节点重新定位
- **过滤**: 按实体类型、关系类型、最小强度过滤
- **高亮**: 点击节点高亮关联节点和边
- **子图**: 展开/折叠子图
- **SVG 渲染**: 节点 (圆圈 + 标签)、边 (线段 + 箭头)

### 状态管理

```javascript
state = {
  nodes: [], edges: [],
  selectedNode: null,
  selectedEdge: null,
  zoom: 1,
  transform: { x: 0, y: 0 },
  simulation: null,
  svg: null,
  g: null,
  mode: 'project',  // 'project' | 'global'
  filters: {
    entityTypes: [],
    relationTypes: [],
    minIntensity: 1
  }
};
```

---

## kb-genres-page.js

题材策略管理页面。管理和配置题材知识策略。

---

## kb-auto-search-page.js

自动搜索配置页面。管理联网搜索知识的触发条件和存储规则。

---

## kb-init-page.js

知识库初始化页面。引导用户完成知识库的初始填充。

---

## 知识审查相关页面

### knowledge-review-page.js

知识审核页面，审核知识条目的准确性和时效性。

### knowledge-expiry-page.js

知识过期管理，标记和清理过期知识条目。

### knowledge-stats-page.js

知识统计页面，展示知识库的统计分析数据。