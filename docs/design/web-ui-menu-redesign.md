# Novel OS Web UI 菜单重构设计文档

> 版本: v1.0
> 状态: 确认
> 创建时间: 2026-07-01

---

## 1. 重构目标

### 1.1 当前问题

| 问题 | 说明 |
|------|------|
| 顶层分组过多 | 16个顶层菜单，认知负担大 |
| 项目/系统混淆 | 项目内容和系统设置混在一起 |
| 概念分组不清 | Canon/Entities/Rules 都是「设定」但分开了 |
| 知识库定位模糊 | 知识库放在项目数据里，没有独立地位 |
| 缺乏层级 | 扁平结构，无法快速定位 |

### 1.2 重构原则

| 原则 | 说明 |
|------|------|
| 三级分组 | 顶层 ≤ 5个，每层 ≤ 8个，每组 ≤ 6个子项 |
| 概念清晰 | 同一类功能放在一起，不同类严格分离 |
| 用户心智模型 | 按用户工作流组织，不按技术架构组织 |
| 渐进展示 | 默认折叠，需要时展开 |
| 项目感知 | 无项目时隐藏项目相关菜单 |

---

## 2. 菜单结构设计

### 2.1 顶层架构

```
Novel OS
├── 📚 项目内容（Project）    ← 用户创作小说的工作区
├── 🧠 知识库（Knowledge）    ← 通用知识 + 项目知识
└── ⚙️ 系统（System）         ← 配置、模板、数据管理
```

### 2.2 项目内容（Project）

#### 分组逻辑
用户创作小说时最常用的功能：设定、剧情、生成、审查。

#### 菜单结构

```
📚 项目内容
│
├── 📖 设定管理
│   ├── 设定文档        → Canon Docs（世界观、背景、规则文档）
│   ├── 角色/势力       → Entities（人物、组织、势力档案）
│   ├── 写作规则        → Rules（canon/character/plot/style/forbidden）
│   └── 关系图          → Relationship Graph（实体关联可视化）
│
├── 📖 剧情管理
│   ├── 卷与章节        → Volumes + Chapter Plans（卷规划、章大纲）
│   ├── 剧情线          → Plot Threads（主线/支线追踪）
│   └── 伏笔            → Foreshadowing（伏笔埋设与兑现）
│
├── 📖 生成与审查
│   ├── 上下文预览      → Context Preview（查看 context_pack 内容）
│   ├── 审查任务        → Review Tasks（AI 审查 + 人工审查）
│   └── 合规检查        → Compliance（规则违规检测）
│
└── 📖 项目知识
    ├── 世界设定        → Project Knowledge: world_rules
    ├── 角色档案        → Project Knowledge: characters
    ├── 势力档案        → Project Knowledge: factions
    └── 世界状态        → World Snapshots（世界状态快照）
```

#### 页面映射

| 菜单项 | 当前页面 | 新页面ID | 说明 |
|--------|---------|---------|------|
| 设定文档 | canon-list, canon-create | canon-list | 保留 |
| 角色/势力 | entities-list, entities-create, entities-relations | entities-list | 合并为一个入口 |
| 写作规则 | rules-list, rules-proposals | rules-list | 合并 |
| 关系图 | graph-view | graph-view | 保留 |
| 卷与章节 | plot-volumes, chapter-plans | plot-volumes | 合并 |
| 剧情线 | plot-threads | plot-threads | 保留 |
| 伏笔 | foreshadowing-list | foreshadowing-list | 保留 |
| 上下文预览 | context-preview | context-preview | 保留 |
| 审查任务 | review-tasks | review-tasks | 保留 |
| 合规检查 | rules-compliance | compliance-check | 改名 |
| 世界设定 | - | project-world-rules | 新增 |
| 角色档案 | - | project-characters | 新增 |
| 势力档案 | - | project-factions | 新增 |
| 世界状态 | - | project-world-state | 新增 |

### 2.3 知识库（Knowledge）

#### 分组逻辑
知识库是跨项目共享的资源，独立于具体小说项目。

#### 菜单结构

```
🧠 知识库
│
├── 📖 通用知识
│   ├── 历史资料        → Universal Knowledge: 历史类
│   ├── 时代背景        → Universal Knowledge: 背景类
│   ├── 题材模板        → Universal Knowledge: 设定类
│   ├── 专业知识        → Universal Knowledge: 专业类
│   └── 写作参考        → Universal Knowledge: 写作类
│
├── 📖 知识管理
│   ├── 搜索与补充      → Auto Search（触发 web_search 补充知识）
│   ├── 知识图谱        → Knowledge Graph（实体关联可视化）
│   └── 知识统计        → Knowledge Stats（各分类知识量统计）
│
└── 📖 知识审查
    ├── 待审核          → Knowledge Review（AI 生成条目的人工审核）
    └── 过期提醒        → Knowledge Expiry（需要重新验证的条目）
```

#### 页面映射

| 菜单项 | 当前页面 | 新页面ID | 说明 |
|--------|---------|---------|------|
| 历史资料 | knowledge-stats, knowledge-maintain | uk-history | 按分类筛选 |
| 时代背景 | - | uk-era | 新增 |
| 题材模板 | - | uk-genre | 新增 |
| 专业知识 | - | uk-professional | 新增 |
| 写作参考 | - | uk-writing | 新增 |
| 搜索与补充 | - | auto-search | 新增 |
| 知识图谱 | - | knowledge-graph | 新增 |
| 知识统计 | knowledge-stats | knowledge-stats | 保留 |
| 待审核 | knowledge-review | knowledge-review | 保留 |
| 过期提醒 | - | knowledge-expiry | 新增 |

### 2.4 系统（System）

#### 分组逻辑
系统配置、模板管理、数据维护，与具体小说项目无关。

#### 菜单结构

```
⚙️ 系统
│
├── 📖 模型配置
│   ├── 模型管理        → Model Profiles（embedding/rerank/completion 配置）
│   └── 成本报告        → Cost Report（模型使用统计）
│
├── 📖 模板
│   ├── 我的模板        → Templates（prompt 模板管理）
│   └── 模板市场        → Template Market（社区模板）
│
├── 📖 数据管理
│   ├── 同步状态        → Sync Status（本地-云端同步）
│   ├── 冲突处理        → Sync Conflicts（数据冲突解决）
│   ├── 审计日志        → Audit Logs（操作记录）
│   └── 离线模式        → Offline Mode（离线数据管理）
│
└── 📖 系统设置
    ├── 连接设置        → Connection（MCP 服务器连接）
    ├── 账户管理        → Account（个人信息）
    ├── 用户管理        → Users（多用户管理）
    └── 调试工具        → Debug Tools（日志、测试）
```

#### 页面映射

| 菜单项 | 当前页面 | 新页面ID | 说明 |
|--------|---------|---------|------|
| 模型管理 | model-profiles | model-profiles | 保留 |
| 成本报告 | model-cost | model-cost | 保留 |
| 我的模板 | template-list, template-create | template-list | 合并 |
| 模板市场 | market-browse | market-browse | 保留 |
| 同步状态 | sync-status | sync-status | 保留 |
| 冲突处理 | sync-conflicts | sync-conflicts | 保留 |
| 审计日志 | audit-logs | audit-logs | 保留 |
| 离线模式 | offline-status | offline-status | 保留 |
| 连接设置 | system-connection | system-connection | 保留 |
| 账户管理 | system-account | system-account | 保留 |
| 用户管理 | system-users | system-users | 保留 |
| 调试工具 | system-debug | system-debug | 保留 |

---

## 3. 代码实现

### 3.1 HTML 结构变更

#### 当前结构

```html
<div class="menu-group" data-menu="canon">...</div>
<div class="menu-group" data-menu="entities">...</div>
<div class="menu-group" data-menu="workflow">...</div>
...  (16 个 menu-group)
```

#### 新结构

```html
<!-- 项目内容 -->
<div class="menu-section" data-section="project">
  <div class="menu-section-header">
    <span class="menu-section-icon">📚</span>
    <span class="menu-section-title" data-i18n="section.project">项目内容</span>
  </div>
  <div class="menu-section-body">
    <div class="menu-group" data-menu="project-settings">
      <div class="menu-group-header">
        <span class="menu-group-icon">⚙️</span>
        <span class="menu-label" data-i18n="nav.settingsGroup">设定管理</span>
        <span class="menu-arrow">▶</span>
      </div>
      <div class="submenu">
        <div class="submenu-item" data-page="canon-list">设定文档</div>
        <div class="submenu-item" data-page="entities-list">角色/势力</div>
        <div class="submenu-item" data-page="rules-list">写作规则</div>
        <div class="submenu-item" data-page="graph-view">关系图</div>
      </div>
    </div>
    <div class="menu-group" data-menu="project-plot">
      <div class="menu-group-header">...</div>
      <div class="submenu">...</div>
    </div>
    <div class="menu-group" data-menu="project-generation">
      <div class="menu-group-header">...</div>
      <div class="submenu">...</div>
    </div>
    <div class="menu-group" data-menu="project-knowledge">
      <div class="menu-group-header">...</div>
      <div class="submenu">...</div>
    </div>
  </div>
</div>

<!-- 知识库 -->
<div class="menu-section" data-section="knowledge">
  <div class="menu-section-header">...</div>
  <div class="menu-section-body">...</div>
</div>

<!-- 系统 -->
<div class="menu-section" data-section="system">
  <div class="menu-section-header">...</div>
  <div class="menu-section-body">...</div>
</div>
```

### 3.2 CSS 样式变更

```css
/* 新增：菜单大区（顶层） */
.menu-section {
  margin-bottom: 8px;
}

.menu-section-header {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 8px 12px;
  font-size: 11px;
  font-weight: 600;
  text-transform: uppercase;
  letter-spacing: 0.5px;
  color: var(--muted);
  cursor: pointer;
  user-select: none;
}

.menu-section-header:hover {
  color: var(--text);
}

.menu-section-body {
  padding-left: 4px;
}

.menu-section.collapsed .menu-section-body {
  display: none;
}

/* 修改：菜单分组（二级） */
.menu-group {
  margin-bottom: 2px;
}

.menu-group-header {
  display: flex;
  align-items: center;
  gap: 6px;
  padding: 6px 12px;
  border-radius: 6px;
  cursor: pointer;
  transition: background 0.15s;
}

.menu-group-header:hover {
  background: var(--bg-hover);
}

.menu-group-icon {
  font-size: 14px;
  width: 20px;
  text-align: center;
}

/* 保持：子菜单项（三级） */
.submenu-item {
  padding: 5px 12px 5px 40px;
  font-size: 13px;
  cursor: pointer;
  border-radius: 6px;
  transition: background 0.15s;
}

.submenu-item:hover {
  background: var(--bg-hover);
}

.submenu-item.active {
  color: var(--accent);
  font-weight: 500;
}
```

### 3.3 JavaScript 变更

#### 导航逻辑

```javascript
// 当前：平铺查找
function navigateTo(pageName) {
  document.querySelectorAll(".submenu-item").forEach(item => {
    item.classList.remove("active");
    if (item.dataset.page === pageName) {
      item.classList.add("active");
      // 展开父级 menu-group
      const menuGroup = item.closest(".menu-group");
      if (menuGroup) menuGroup.classList.add("open");
    }
  });
}

// 新增：查找并展开所有父级
function navigateTo(pageName) {
  // 1. 清除所有激活状态
  document.querySelectorAll(".submenu-item").forEach(item => {
    item.classList.remove("active");
  });

  // 2. 找到目标页面
  const target = document.querySelector(`.submenu-item[data-page="${pageName}"]`);
  if (!target) return;

  // 3. 激活目标
  target.classList.add("active");

  // 4. 展开所有父级
  const menuGroup = target.closest(".menu-group");
  if (menuGroup) menuGroup.classList.add("open");

  const menuSection = target.closest(".menu-section");
  if (menuSection) menuSection.classList.remove("collapsed");

  // 5. 滚动到可见区域
  target.scrollIntoView({ behavior: "smooth", block: "nearest" });
}
```

#### 折叠/展开逻辑

```javascript
// 菜单大区折叠/展开
document.querySelectorAll(".menu-section-header").forEach(header => {
  header.addEventListener("click", () => {
    const section = header.closest(".menu-section");
    section.classList.toggle("collapsed");
    // 保存状态到 localStorage
    localStorage.setItem(`menu-section-${section.dataset.section}`,
      section.classList.contains("collapsed") ? "collapsed" : "open");
  });
});

// 恢复折叠状态
document.querySelectorAll(".menu-section").forEach(section => {
  const saved = localStorage.getItem(`menu-section-${section.dataset.section}`);
  if (saved === "collapsed") {
    section.classList.add("collapsed");
  }
});
```

#### 项目感知

```javascript
// 无项目时隐藏项目相关内容
function updateMenuForProject(hasProject) {
  const projectSection = document.querySelector('[data-section="project"]');
  if (projectSection) {
    projectSection.style.display = hasProject ? "block" : "none";
  }
}

// 根据当前项目切换
function onProjectChange(project) {
  updateMenuForProject(!!project);
  // 更新项目名称显示
  document.querySelectorAll(".project-name").forEach(el => {
    el.textContent = project?.name || "未选择项目";
  });
}
```

### 3.4 国际化 (i18n)

```javascript
// 新增翻译 key
const translations = {
  en: {
    "section.project": "Project",
    "section.knowledge": "Knowledge",
    "section.system": "System",
    "nav.settingsGroup": "Settings",
    "nav.plotGroup": "Plot",
    "nav.generationGroup": "Generation",
    "nav.projectKnowledgeGroup": "Project Knowledge",
    "nav.historyGroup": "History",
    "nav.knowledgeMgmtGroup": "Management",
    "nav.knowledgeReviewGroup": "Review",
    "nav.modelGroup": "Models",
    "nav.templateGroup": "Templates",
    "nav.dataGroup": "Data",
    "nav.systemGroup": "System",
  },
  zh: {
    "section.project": "项目内容",
    "section.knowledge": "知识库",
    "section.system": "系统",
    "nav.settingsGroup": "设定管理",
    "nav.plotGroup": "剧情管理",
    "nav.generationGroup": "生成与审查",
    "nav.projectKnowledgeGroup": "项目知识",
    "nav.historyGroup": "通用知识",
    "nav.knowledgeMgmtGroup": "知识管理",
    "nav.knowledgeReviewGroup": "知识审查",
    "nav.modelGroup": "模型配置",
    "nav.templateGroup": "模板",
    "nav.dataGroup": "数据管理",
    "nav.systemGroup": "系统设置",
  }
};
```

---

## 4. 页面迁移计划

### 4.1 需要合并的页面

| 当前页面 | 合并到 | 说明 |
|---------|--------|------|
| canon-create | canon-list | 创建功能作为列表页的按钮 |
| entities-create | entities-list | 创建功能作为列表页的按钮 |
| entities-relations | graph-view | 关系图统一入口 |
| rules-proposals | rules-list | 提案作为规则列表的标签页 |
| template-create | template-list | 创建功能作为列表页的按钮 |

### 4.2 需要新增的页面

| 页面ID | 标题 | 功能 |
|--------|------|------|
| project-world-rules | 世界设定 | 管理项目的世界规则 |
| project-characters | 角色档案 | 管理项目角色卡 |
| project-factions | 势力档案 | 管理项目势力档案 |
| project-world-state | 世界状态 | 查看世界状态快照 |
| uk-history | 历史资料 | 浏览/搜索历史知识 |
| uk-era | 时代背景 | 浏览/搜索时代背景 |
| uk-genre | 题材模板 | 浏览/搜索题材设定 |
| uk-professional | 专业知识 | 浏览/搜索专业知识 |
| uk-writing | 写作参考 | 浏览/搜索写作参考 |
| auto-search | 搜索补充 | 触发 web_search 补充知识 |
| knowledge-graph | 知识图谱 | 实体关联可视化 |
| knowledge-expiry | 过期提醒 | 需要验证的知识条目 |

### 4.3 需要重命名的页面

| 当前页面ID | 新页面ID | 标题 |
|-----------|---------|------|
| rules-compliance | compliance-check | 合规检查 |
| knowledge-stats | knowledge-stats | 知识统计（保留） |
| knowledge-review | knowledge-review | 知识审查（保留） |

---

## 5. 实现阶段

| Phase | 内容 | 优先级 | 预估工时 |
|-------|------|--------|---------|
| Phase 1 | HTML 结构重构（三级菜单） | P0 | 2h |
| Phase 2 | CSS 样式更新 | P0 | 1h |
| Phase 3 | JavaScript 导航逻辑更新 | P0 | 1h |
| Phase 4 | i18n 翻译更新 | P0 | 0.5h |
| Phase 5 | 合并现有页面 | P1 | 2h |
| Phase 6 | 新增项目知识页面 | P1 | 3h |
| Phase 7 | 新增知识库页面 | P1 | 4h |
| Phase 8 | 项目感知逻辑 | P2 | 1h |
| Phase 9 | 响应式适配 | P2 | 1h |
| Phase 10 | 无障碍优化 | P3 | 1h |

---

## 6. 验收标准

| 标准 | 说明 |
|------|------|
| 三级分组 | 顶层 ≤ 5个，每层 ≤ 8个，每组 ≤ 6个子项 |
| 导航正确 | 点击任意菜单项能正确跳转到对应页面 |
| 折叠记忆 | 折叠/展开状态保存到 localStorage |
| 项目感知 | 无项目时隐藏「项目内容」大区 |
| 响应式 | 移动端侧边栏可折叠 |
| i18n | 中英文切换正常 |
| 无障碍 | 键盘导航、屏幕阅读器支持 |
| 性能 | 菜单切换无卡顿 |
