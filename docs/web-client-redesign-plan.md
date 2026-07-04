# Novel OS Web 客户端完整改造方案

> 版本：v2.0 | 日期：2026-07-04 | 作者：AI + User

---

## 一、改造背景

### 1.1 当前问题

| 问题 | 描述 |
|------|------|
| **菜单重叠** | Project Knowledge (World Rules/Characters/Factions) 与 Settings (Canon Docs/Entities) 100% 重复，仅为只读过滤视图 |
| **功能缺失** | 缺少小说类型管理、自定义分类管理、类型与分类绑定等核心管理功能 |
| **架构混乱** | Knowledge Pack 放在 Local Project 下，与 UK 知识管理分离 |
| **扩展性差** | 缺乏对等级系统、物品、技能、地图、生物图鉴等知识图谱的支持 |
| **Local Project 定位不清** | 此 MCP 服务不需要本地文件绑定概念，生成的章节保存于用户本地即可 |

### 1.2 改造目标

1. **清理冗余**：删除重复菜单，简化菜单结构
2. **新增核心管理**：小说类型管理、分类管理、类型与分类绑定
3. **扩展知识图谱**：支持等级体系、物品图鉴、技能图鉴、地图地点、生物图鉴
4. **重建 UI**：以模块化方式重构，避免在大型 HTML 文件中做脆弱的字符串替换

---

## 二、数据库层改造

### 2.1 新增表

```sql
-- 等级定义表（支持多种等级类型）
CREATE TABLE level_definitions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    level_type VARCHAR(50) NOT NULL,        -- 等级类型: character, item, skill, tech, building
    level_name VARCHAR(100) NOT NULL,       -- 等级名称: 炼气、筑基、金丹...
    level_order INT DEFAULT 0,              -- 排序
    description TEXT,                       -- 等级描述
    numeric_range INT4RANGE,                -- 数值范围
    category_id UUID REFERENCES setting_categories(id),
    created_at TIMESTAMPTZ DEFAULT now()
);

-- 物品模板表
CREATE TABLE item_templates (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name VARCHAR(200) NOT NULL,
    item_type VARCHAR(50),                  -- weapon, armor, consumable, artifact, material
    rarity VARCHAR(20),                     -- common, rare, epic, legendary
    level_id UUID REFERENCES level_definitions(id),
    properties JSONB DEFAULT '{}',          -- {atk: 100, def: 50, effect: "..."}
    category_id UUID REFERENCES setting_categories(id),
    created_at TIMESTAMPTZ DEFAULT now()
);

-- 技能模板表
CREATE TABLE skill_templates (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name VARCHAR(200) NOT NULL,
    skill_type VARCHAR(50),                 -- spell, technique, talent, knowledge
    element VARCHAR(20),
    level_id UUID REFERENCES level_definitions(id),
    effects JSONB DEFAULT '{}',             -- {damage: 500, cost: 100, range: 10}
    prerequisites TEXT[] DEFAULT '{}',
    category_id UUID REFERENCES setting_categories(id),
    created_at TIMESTAMPTZ DEFAULT now()
);
```

### 2.2 扩展已有表

```sql
-- setting_categories 增加字段
ALTER TABLE setting_categories ADD COLUMN IF NOT EXISTS type_description TEXT;
ALTER TABLE setting_categories ADD COLUMN IF NOT EXISTS parent_id UUID REFERENCES setting_categories(id);
ALTER TABLE setting_categories ADD COLUMN IF NOT EXISTS applicable_genres TEXT[];
```

### 2.3 类型绑定表（已有，需确认）

```sql
-- genre_category_bindings（Phase 2 已创建）
-- genre_slug + category_id + is_required + priority
```

---

## 三、MCP 工具扩展

### 3.1 已有工具（Phase 3 已完成）

| 工具名 | 功能 | 状态 |
|--------|------|------|
| `setting.genre.upsert` | 创建/更新小说类型 | ✅ 已实现 |
| `setting.genre.delete` | 删除小说类型 | ✅ 已实现 |
| `setting.genre.list` | 列出所有类型 | ✅ 已实现 |
| `genre.binding.list` | 列出绑定关系 | ✅ 已实现 |
| `genre.binding.bulk_upsert` | 批量绑定 | ✅ 已实现 |
| `genre.binding.matrix` | 绑定矩阵 | ✅ 已实现 |

### 3.2 待新增工具

| 工具名 | 功能 | 优先级 |
|--------|------|--------|
| `setting.level.upsert` | 等级定义 CRUD | P1 |
| `setting.level.list` | 等级列表 | P1 |
| `setting.item.upsert` | 物品模板 CRUD | P2 |
| `setting.item.list` | 物品列表 | P2 |
| `setting.skill.upsert` | 技能模板 CRUD | P2 |
| `setting.skill.list` | 技能列表 | P2 |
| `genre.binding.recommend` | 根据类型自动推荐分类配置 | P2 |
| `project.init_from_genre` | 根据类型自动初始化项目所有配置 | P1 |

---

## 四、Web 客户端菜单重构

### 4.1 目标菜单结构

```
┌─────────────────────────────────────────────────┐
│ 新菜单结构                                        │
├─────────────────────────────────────────────────┤
│                                                  │
│  Project（项目内容）                               │
│  ├── Dashboard（总览）                            │
│  ├── 卷 & 章节管理                                │
│  │   ├── 卷管理                                   │
│  │   ├── 章节管理                                 │
│  │   └── 生成流水线                               │
│  ├── 故事设定                                     │
│  │   ├── Canon Docs（世界设定文档）               │
│  │   ├── Entities（人物/势力/地点实体）            │
│  │   ├── Writing Rules（创作规则）                │
│  │   └── Relationship Graph（关系图）             │
│  ├── 情节管理                                     │
│  │   ├── 情节线                                   │
│  │   └── 伏笔                                     │
│  │                                                │
│  World Settings（世界设定）           ← 新增组     │
│  ├── 📊 等级体系          ← 新增                   │
│  │   ├── 人物等级                                  │
│  │   ├── 物品等级                                  │
│  │   ├── 技能/功法等级                             │
│  │   ├── 科技等级                                  │
│  │   └── 建筑等级                                  │
│  ├── 🎒 物品图鉴          ← 新增                   │
│  │   ├── 武器                                      │
│  │   ├── 防具                                      │
│  │   ├── 丹药/消耗品                               │
│  │   ├── 法宝                                      │
│  │   └── 材料                                      │
│  ├── 📜 技能图鉴          ← 新增                   │
│  │   ├── 法术/技能                                 │
│  │   ├── 武技                                      │
│  │   ├── 天赋                                      │
│  │   └── 知识技能                                  │
│  ├── 🗺️ 地图与地点       ← 新增                   │
│  │   ├── 区域/城市                                 │
│  │   └── 建筑/秘境                                 │
│  └── 🐉 生物图鉴          ← 新增                   │
│      ├── 妖兽/怪物                                 │
│      └── NPC 模板                                  │
│                                                  │
│  Knowledge（知识管理）                             │
│  ├── 📖 小说类型管理        ← 新增                  │
│  ├── 📂 分类管理            ← 新增                  │
│  ├── 🔗 类型与分类绑定      ← 新增                  │
│  ├── 📦 知识包                                      │
│  ├── 知识库管理                                    │
│  ├── 自动搜索                                      │
│  └── 知识统计                                      │
│                                                  │
│  System（系统管理）                                 │
│  ├── 用户管理                                      │
│  ├── 模型配置                                      │
│  └── 系统健康                                      │
└─────────────────────────────────────────────────┘
```

### 4.2 删除项

| 删除 | 原因 |
|------|------|
| Project Knowledge 整个子菜单组 | 100% 与 Settings 重复 |
| Local Project 整个菜单组 | MCP 不需要本地文件绑定 |
| Local Projects 页面 | 同上 |
| Local Chapters 页面 | 同上 |
| Local Pipeline 页面 | 同上 |

---

## 五、技术方案

### 5.1 核心原则

1. **不使用大型 HTML 单文件**：改为前后端分离架构
2. **使用 Vue/React 或 vanilla JS 模块化**：每个菜单对应独立组件
3. **所有页面通过 API 获取数据**：不硬编码，不字符串替换

### 5.2 推荐技术栈

| 层级 | 技术选型 | 原因 |
|------|---------|------|
| 前端框架 | **Alpine.js + Tailwind CSS** 或 **Vue 3 CDN** | 轻量，无需构建工具 |
| 后端 API | 已有 `server.py` (Python HTTP Server) | 继续复用 |
| 数据交互 | 已有 `/api/tool` 代理到 MCP | 继续复用 |
| 样式 | Tailwind CSS CDN | 快速开发，响应式 |

### 5.3 推荐方案：Alpine.js SPA

```html
<!-- 主入口 index.html -->
<!DOCTYPE html>
<html>
<head>
  <script src="https://cdn.jsdelivr.net/npm/alpinejs@3"></script>
  <script src="https://cdn.tailwindcss.com"></script>
</head>
<body x-data="app">
  <!-- 侧边栏 -->
  <nav>
    <template x-for="menu in menus">
      <div @click="navigate(menu.id)" x-text="menu.label"></div>
    </template>
  </nav>
  
  <!-- 内容区 -->
  <main>
    <template x-if="currentPage === 'genre-manage'">
      <genre-manager></genre-manager>
    </template>
    <template x-if="currentPage === 'category-manage'">
      <category-manager></category-manager>
    </template>
    <!-- ... -->
  </main>
  
  <!-- 每个页面是独立组件 -->
  <script src="components/genre-manager.js"></script>
  <script src="components/category-manager.js"></script>
</body>
</html>
```

### 5.4 文件结构

```
novel-os-web/
├── index.html              # 主入口（SPA shell）
├── server.py               # 后端 API 代理
├── css/
│   └── app.css             # 全局样式
├── js/
│   ├── app.js              # SPA 路由和状态管理
│   ├── api.js              # API 调用封装
│   └── i18n.js             # 国际化
├── components/
│   ├── genre-manager.js    # 小说类型管理
│   ├── category-manager.js # 分类管理
│   ├── binding-matrix.js   # 类型-分类绑定矩阵
│   ├── level-manager.js    # 等级体系管理
│   ├── item-manager.js     # 物品管理
│   ├── skill-manager.js    # 技能管理
│   ├── map-manager.js      # 地图管理
│   ├── canon-manager.js    # Canon 文档（复用原有逻辑）
│   ├── entity-manager.js   # 实体管理（复用原有逻辑）
│   └── knowledge-pack.js   # 知识包配置
└── Dockerfile
```

---

## 六、实施计划

### Phase 1：基础框架（2 天）

| 任务 | 说明 | 工作量 |
|------|------|--------|
| 搭建 SPA 框架 | Alpine.js + Tailwind，路由系统 | 4h |
| 侧边栏菜单 | 动态菜单生成，导航切换 | 2h |
| API 层封装 | Promise 包装，错误处理 | 2h |
| 认证模块 | 登录/登出/Session 管理 | 2h |
| 工作区选择器 | 动态加载，联动项目选择 | 2h |

### Phase 2：现有功能迁移（2 天）

| 任务 | 说明 | 工作量 |
|------|------|--------|
| Canon Docs 页面 | 从原有逻辑迁移 | 4h |
| Entities 页面 | 从原有逻辑迁移 | 4h |
| Writing Rules 页面 | 从原有逻辑迁移 | 2h |
| 情节线/伏笔页面 | 从原有逻辑迁移 | 3h |
| 知识库页面 | 从原有逻辑迁移 | 3h |

### Phase 3：新增管理功能（2 天）

| 任务 | 说明 | 工作量 |
|------|------|--------|
| 小说类型管理 | 列表+弹窗编辑，12 种预设 | 3h |
| 分类管理 | 树形展示，增删改 | 4h |
| 类型-分类绑定 | 矩阵勾选界面 | 3h |
| 知识包配置 | 项目级别的分类启用 | 2h |

### Phase 4：知识图谱扩展（3 天）

| 任务 | 说明 | 工作量 |
|------|------|--------|
| 等级体系管理 | 多类型等级 CRUD | 4h |
| 物品图鉴 | 武器/防具/丹药等 | 4h |
| 技能图鉴 | 法术/武技/天赋 | 4h |
| 地图与地点 | 区域/城市/建筑 | 3h |
| 生物图鉴 | 怪物/NPC | 3h |

### Phase 5：部署上线（1 天）

| 任务 | 说明 | 工作量 |
|------|------|--------|
| Docker 构建 | 更新 Dockerfile，多阶段构建 | 2h |
| NAS 部署 | 替换现有容器 | 1h |
| 测试验证 | 功能测试，回归测试 | 3h |
| Git 提交 & 推送 | 保存所有改动 | 0.5h |

---

## 七、风险与对策

| 风险 | 对策 |
|------|------|
| 旧版兼容性 | 保留旧的 server.py API，新前端对接同一套 API |
| 数据迁移 | 使用现有的 setting_categories, genre_canonical 等表 |
| 组件间状态共享 | 使用 Alpine.js 全局 store 或简单 event bus |
| 浏览器兼容 | 使用标准 ES6+，不依赖需要编译的特性 |
| 国际化的中文 JSON 编码 | 使用 UTF-8 BOM 或无 BOM，注意 Windows/Linux 编码差异 |

---

## 八、对比：改造 vs 重写

| 维度 | 改造现有 HTML | 重写为 SPA |
|------|-------------|-----------|
| 开发难度 | 极高（字符串替换） | 中等（组件化） |
| 代码可维护性 | 极差（单文件 500KB） | 好（模块化） |
| 扩展性 | 无法扩展 | 容易扩展 |
| 风险 | 高（容易引入 bug） | 中（需要测试） |
| 开发时间 | 不可预估 | 约 10 天 |
| 推荐 | ❌ **不推荐** | ✅ **推荐** |

**结论：重写为 SPA 是唯一可行的方案。** 在 500KB 的单文件 HTML 中做字符串替换已被证明无法稳定工作。

---

## 九、当前系统已完成的改动（保留）

| 改动 | 文件 | 状态 |
|------|------|------|
| 数据库唯一约束修复 | `projects` 表 | ✅ |
| 数据库扩展（type_description, 分类, 绑定） | `setting_categories`, `genre_category_bindings` | ✅ |
| 12 种小说类型预设 | `genre_canonical` | ✅ |
| 10 种默认分类预设 | `setting_categories` | ✅ |
| 类型-分类绑定预设 | `genre_category_bindings` | ✅ |
| MCP 工具：genre CRUD | `setting.py`, `global_settings.py` | ✅ |
| MCP 工具：binding 管理 | `setting.py`, `global_settings.py` | ✅ |
| MCP 工具：workspace.list scope 修复 | `auth.py` | ✅ |
| MCP 工具：知识包自动创建 | `novel_wizard.py` | ✅ |
| MCP 工具：上下文检查知识包 | `context.py` | ✅ |
| 服务 Token scope 修复 | `auth.py` | ✅ |
| workflow.py docstring 修复 | `workflow.py` | ✅ |
| deps.py 缺失服务 stub | `deps.py` | ✅ |
| Web 客户端：loadWorkspaces | `index.html` | ✅ |
| Web 客户端：init async 修复 | `index.html` | ✅ |

---

*文档版本：v2.0*  
*创建日期：2026-07-04*  
*计划开始：待批准*