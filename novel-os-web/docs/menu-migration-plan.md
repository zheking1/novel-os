# Novel OS Web Client - 菜单结构迁移与功能完善计划

## 一、项目概述

### 1.1 背景
将 Novel OS Web Client 从单体 HTML（9205行）迁移到模块化 SPA 架构。当前已完成基础框架搭建，需要按照原始设计完善菜单结构和功能页面。

### 1.2 目标
- 恢复完整的三级菜单结构
- 实现所有功能页面
- 保持与原始设计一致的用户体验
- 支持中英文国际化

---

## 二、菜单结构设计

### 2.1 一级菜单（3个）

| 序号 | 菜单ID | 图标 | 中文名 | 英文名 | 需要项目 |
|------|--------|------|--------|--------|----------|
| 1 | project | 📚 | 项目管理 | Project | ✅ 是 |
| 2 | knowledge | 🧠 | 知识库 | Knowledge | ❌ 否 |
| 3 | system | ⚙️ | 系统管理 | System | ❌ 否 |

### 2.2 二级菜单（完整结构）

#### 📚 项目管理 (project)
需要选择项目后才显示此菜单

| 分组ID | 图标 | 中文名 | 英文名 | 子菜单项 |
|--------|------|--------|--------|----------|
| project-settings | ⚙️ | 设定管理 | Settings | Canon Docs, Entities, Writing Rules, Relationship Graph |
| project-plot | 📖 | 剧情管理 | Plot | Volumes & Chapters, Plot Threads, Foreshadowing |
| project-generation | 🔧 | 生成与审查 | Generation | Context Preview, Review Tasks, Compliance, Pipeline, Chapters |
| project-knowledge | 🗂️ | 项目知识 | Project Knowledge | World Rules, Characters, Factions, World State |
| project-local | 💻 | 本地项目 | Local Project | 知识包配置, 项目管理, 章节管理, 生成流水线 |

#### 🧠 知识库 (knowledge)
全局设置，不需要项目

| 分组ID | 图标 | 中文名 | 英文名 | 子菜单项 |
|--------|------|--------|--------|----------|
| knowledge-mgmt | 📚 | 知识管理 | Knowledge | Knowledge Manager, Auto Search, Knowledge Graph, Statistics |
| knowledge-review | 🔍 | 知识审查 | Review | Pending Review, Expiry Alerts |

#### ⚙️ 系统管理 (system)
全局设置，不需要项目

| 分组ID | 图标 | 中文名 | 英文名 | 子菜单项 |
|--------|------|--------|--------|----------|
| sys-model | 🤖 | 模型配置 | Models | Model Profiles, Cost Report |
| sys-template | 📋 | 模板管理 | Templates | My Templates, Marketplace |
| sys-skill | 🎯 | Skill 管理 | Skills | Skill Manager |
| sys-data | 💾 | 数据管理 | Data | Sync Status, Conflicts, Audit Logs, Offline Mode |
| sys-monitor | 📊 | 系统监控 | Monitoring | Health, Cache, Backup |
| sys-system | ℹ️ | 系统信息 | System Info | Connection, Account, Users, Debug Tools |

### 2.3 三级菜单（完整列表）

#### 项目管理 > 设定管理
| 页面ID | 中文名 | 英文名 | 需要项目 |
|--------|--------|--------|----------|
| canon-list | Canon文档 | Canon Docs | ✅ |
| entities-list | 实体列表 | Entities | ✅ |
| rules-list | 写作规则 | Writing Rules | ✅ |
| graph-view | 关系图 | Relationship Graph | ✅ |

#### 项目管理 > 剧情管理
| 页面ID | 中文名 | 英文名 | 需要项目 |
|--------|--------|--------|----------|
| plot-volumes | 卷章管理 | Volumes & Chapters | ✅ |
| plot-threads | 情节线 | Plot Threads | ✅ |
| foreshadowing-list | 伏笔管理 | Foreshadowing | ✅ |

#### 项目管理 > 生成与审查
| 页面ID | 中文名 | 英文名 | 需要项目 |
|--------|--------|--------|----------|
| context-preview | 上下文预览 | Context Preview | ✅ |
| review-tasks | 审查任务 | Review Tasks | ✅ |
| compliance | 合规检查 | Compliance | ✅ |
| pipeline | 生成流水线 | Pipeline | ✅ |
| chapters | 章节管理 | Chapters | ✅ |

#### 项目管理 > 项目知识
| 页面ID | 中文名 | 英文名 | 需要项目 |
|--------|--------|--------|----------|
| project-world-rules | 世界规则 | World Rules | ✅ |
| project-characters | 角色管理 | Characters | ✅ |
| project-factions | 势力管理 | Factions | ✅ |
| project-world-state | 世界状态 | World State | ✅ |

#### 项目管理 > 本地项目
| 页面ID | 中文名 | 英文名 | 需要项目 |
|--------|--------|--------|----------|
| knowledge-pack | 知识包配置 | Knowledge Pack | ✅ |
| local-projects | 项目管理 | Local Projects | ✅ |
| local-chapters | 章节管理 | Local Chapters | ✅ |
| local-pipeline | 生成流水线 | Local Pipeline | ✅ |

#### 知识库 > 知识管理
| 页面ID | 中文名 | 英文名 | 需要项目 |
|--------|--------|--------|----------|
| uk-manage | 知识管理器 | Knowledge Manager | ❌ |
| auto-search | 自动搜索 | Auto Search | ❌ |
| knowledge-graph | 知识图谱 | Knowledge Graph | ❌ |
| knowledge-stats | 知识统计 | Statistics | ❌ |

#### 知识库 > 知识审查
| 页面ID | 中文名 | 英文名 | 需要项目 |
|--------|--------|--------|----------|
| knowledge-review | 待审核 | Pending Review | ❌ |
| knowledge-expiry | 过期提醒 | Expiry Alerts | ❌ |

#### 系统管理 > 模型配置
| 页面ID | 中文名 | 英文名 | 需要项目 |
|--------|--------|--------|----------|
| model-profiles | 模型配置 | Model Profiles | ❌ |
| model-cost | 费用报表 | Cost Report | ❌ |

#### 系统管理 > 模板管理
| 页面ID | 中文名 | 英文名 | 需要项目 |
|--------|--------|--------|----------|
| template-list | 我的模板 | My Templates | ❌ |
| market-browse | 市场浏览 | Marketplace | ❌ |

#### 系统管理 > Skill 管理
| 页面ID | 中文名 | 英文名 | 需要项目 |
|--------|--------|--------|----------|
| skill-manage | Skill 管理器 | Skill Manager | ❌ |

#### 系统管理 > 数据管理
| 页面ID | 中文名 | 英文名 | 需要项目 |
|--------|--------|--------|----------|
| sync-status | 同步状态 | Sync Status | ❌ |
| sync-conflicts | 冲突处理 | Conflicts | ❌ |
| audit-logs | 审计日志 | Audit Logs | ❌ |
| offline-status | 离线模式 | Offline Mode | ❌ |

#### 系统管理 > 系统监控
| 页面ID | 中文名 | 英文名 | 需要项目 |
|--------|--------|--------|----------|
| sys-health | 健康状态 | Health | ❌ |
| sys-cache | 缓存管理 | Cache | ❌ |
| sys-backup | 备份管理 | Backup | ❌ |

#### 系统管理 > 系统信息
| 页面ID | 中文名 | 英文名 | 需要项目 |
|--------|--------|--------|----------|
| system-connection | 连接状态 | Connection | ❌ |
| system-account | 账户管理 | Account | ❌ |
| system-users | 用户管理 | Users | ❌ |
| system-debug | 调试工具 | Debug Tools | ❌ |

---

## 三、功能页面优先级

### P0 - 核心功能（必须实现）
1. **项目管理 > 设定管理**
   - Canon Docs（文档CRUD）
   - Entities（实体CRUD）
   - Writing Rules（规则CRUD）

2. **项目管理 > 剧情管理**
   - Volumes & Chapters（卷章结构）
   - Plot Threads（情节线管理）
   - Foreshadowing（伏笔管理）

3. **知识库 > 知识管理**
   - Knowledge Manager（知识条目CRUD）
   - Category Management（分类管理）
   - Genre Management（类型管理）
   - Genre-Category Binding（类型绑定）

4. **系统管理 > 系统监控**
   - Health（健康状态）

### P1 - 重要功能（应该实现）
1. **项目管理 > 生成与审查**
   - Context Preview
   - Review Tasks
   - Pipeline
   - Chapters

2. **项目管理 > 项目知识**
   - World Rules
   - Characters
   - Factions
   - World State

3. **系统管理 > 模型配置**
   - Model Profiles
   - Cost Report

### P2 - 辅助功能（可以后续实现）
1. **项目管理 > 本地项目**（所有子菜单）
2. **知识库 > 知识审查**（所有子菜单）
3. **系统管理 > 模板管理**（所有子菜单）
4. **系统管理 > Skill 管理**
5. **系统管理 > 数据管理**（所有子菜单）
6. **系统管理 > 系统信息**（所有子菜单）

---

## 四、技术实现方案

### 4.1 菜单管理器更新

更新 `js/core/menu-manager.js`，采用新的数据结构：

```javascript
const menuDefinition = {
  project: {
    id: 'project',
    labelKey: 'section.project',
    icon: '📚',
    requiresProject: true,
    groups: [
      {
        id: 'project-settings',
        labelKey: 'nav.settingsGroup',
        icon: '⚙️',
        items: [
          { id: 'canon-list', labelKey: 'nav.canonList', icon: '📄', path: '/project/canon' },
          // ...
        ]
      },
      // ...
    ]
  },
  // ...
};
```

### 4.2 页面路由更新

更新 `index.html` 中的 `navigateToPage()` 函数，支持所有页面路由：

```javascript
function navigateToPage(pageId) {
  switch (pageId) {
    // P0 - 设定管理
    case 'canon-list':
      // 加载Canon页面组件
      break;
    case 'entities-list':
      // 加载Entities页面组件
      break;
    // ... 其他页面
  }
}
```

### 4.3 页面组件创建

为每个页面创建独立的组件文件：

```
js/pages/
├── project/
│   ├── canon-list.js
│   ├── entities-list.js
│   ├── rules-list.js
│   ├── graph-view.js
│   ├── plot-volumes.js
│   ├── plot-threads.js
│   ├── foreshadowing-list.js
│   ├── context-preview.js
│   ├── review-tasks.js
│   ├── compliance.js
│   ├── pipeline.js
│   ├── chapters.js
│   ├── world-rules.js
│   ├── characters.js
│   ├── factions.js
│   ├── world-state.js
│   └── local/
│       ├── knowledge-pack.js
│       ├── local-projects.js
│       ├── local-chapters.js
│       └── local-pipeline.js
├── knowledge/
│   ├── uk-manage.js
│   ├── auto-search.js
│   ├── knowledge-graph.js
│   ├── knowledge-stats.js
│   ├── knowledge-review.js
│   └── knowledge-expiry.js
└── system/
    ├── model-profiles.js
    ├── model-cost.js
    ├── template-list.js
    ├── market-browse.js
    ├── skill-manage.js
    ├── sync-status.js
    ├── sync-conflicts.js
    ├── audit-logs.js
    ├── offline-status.js
    ├── sys-health.js
    ├── sys-cache.js
    ├── sys-backup.js
    ├── system-connection.js
    ├── system-account.js
    ├── system-users.js
    └── system-debug.js
```

### 4.4 国际化支持

更新 `i18n/zh.json` 和 `i18n/en.json`，添加所有菜单项的翻译键。

---

## 五、开发任务清单

### 阶段1：菜单结构更新
- [ ] 更新 `menu-manager.js` 菜单定义
- [ ] 更新 `i18n` 翻译文件
- [ ] 更新 `index.html` 路由函数
- [ ] 测试菜单显示和导航

### 阶段2：P0 核心页面实现
- [ ] Canon Docs 页面
- [ ] Entities 页面
- [ ] Writing Rules 页面
- [ ] Volumes & Chapters 页面
- [ ] Plot Threads 页面
- [ ] Foreshadowing 页面
- [ ] Knowledge Manager 页面
- [ ] Category Management 页面（已有）
- [ ] Genre Management 页面（已有）
- [ ] Genre-Category Binding 页面（已有）
- [ ] Health 页面（已有）

### 阶段3：P1 重要页面实现
- [ ] Context Preview 页面
- [ ] Review Tasks 页面
- [ ] Pipeline 页面
- [ ] Chapters 页面
- [ ] World Rules 页面
- [ ] Characters 页面
- [ ] Factions 页面
- [ ] World State 页面
- [ ] Model Profiles 页面
- [ ] Cost Report 页面

### 阶段4：P2 辅助页面实现
- [ ] 本地项目相关页面（4个）
- [ ] 知识审查相关页面（2个）
- [ ] 模板管理相关页面（2个）
- [ ] Skill 管理页面
- [ ] 数据管理相关页面（4个）
- [ ] 系统信息相关页面（4个）

---

## 六、验收标准

1. **菜单完整性**：所有菜单项都能正确显示
2. **导航功能**：点击菜单项能正确跳转到对应页面
3. **权限控制**：需要项目的菜单在未选择项目时隐藏
4. **国际化**：切换语言后菜单正确显示
5. **响应式**：菜单在不同屏幕尺寸下正常显示

---

*文档版本：v1.0*
*创建时间：2026-07-05*
