# 全局设定系统设计文档

> 版本：v1.1（优化版）
> 日期：2026-06-28
> 状态：设计优化完成
> 参考：webnovel-writer-opencode 项目分析
> 相关文档：[global-settings-optimization-plan.md](./global-settings-optimization-plan.md)

---

## 1. 背景与目标

### 1.1 背景

Novel OS 是一个用于 AI 生成小说的管理系统。系统需要管理两类数据：

- **全局共享数据**：所有小说项目都可以通用的基础设定
- **项目专属数据**：每个小说项目独有的创作数据

### 1.2 目标

设计一个**完全可定制的元数据驱动系统**，让用户可以：

1. 自行设计、添加、删除分类
2. 每个分类可以有不同的属性字段
3. 不影响 MCP 查询（MCP 通过通用接口操作，不依赖硬编码）

---

## 2. 架构分层

### 2.1 全局层（Workspace级 - 公共设定）

| 模块 | 说明 |
|------|------|
| 世界观模板 | 通用的世界观框架 |
| 小说分类体系 | 小说类型、流派、标签等分类标准 |
| 审查规则模板 | 合规审查规则库 |
| 通用实体类型定义 | 人物、势力、地点等实体类型的标准定义 |
| 金手指体系模板 | 能力系统模板 |
| 人设模板库 | 可复用的人物设定模板 |
| 情节模板库 | 可复用的情节桥段模板 |

### 2.2 项目层（Project级 - 专属数据）

| 模块 | 说明 |
|------|------|
| 大纲 | 小说整体大纲 |
| 剧情线 | 具体的剧情发展脉络 |
| 伏笔 | 项目专属的伏笔管理 |
| 实体实例 | 项目中的具体人物、势力、地点等 |
| 关系图 | 实体之间的关系网络 |
| 审查记录 | 该项目的审查历史和结果 |

---

## 3. 数据模型设计

### 3.1 类别定义表 (setting_categories)

用户自定义的所有分类：

```sql
CREATE TABLE setting_categories (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name VARCHAR(100) NOT NULL,              -- 分类名称（如"题材分类"）
    slug VARCHAR(50) NOT NULL UNIQUE,        -- URL友好名称
    description TEXT,                        -- 分类描述
    icon VARCHAR(10),                        -- 图标（如 emoji）
    sort_order INT DEFAULT 0,                -- 显示顺序
    is_active BOOLEAN DEFAULT TRUE,          -- 是否启用
    workspace_id UUID NOT NULL,              -- 所属工作区
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

CREATE INDEX idx_setting_categories_workspace ON setting_categories(workspace_id);
CREATE INDEX idx_setting_categories_slug ON setting_categories(slug);
```

### 3.2 字段定义表 (setting_field_definitions)

每个分类可以有**不同的属性字段**：

```sql
CREATE TABLE setting_field_definitions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    category_id UUID NOT NULL REFERENCES setting_categories(id),
    field_name VARCHAR(100) NOT NULL,        -- 字段名（如"题材别名"）
    field_key VARCHAR(50) NOT NULL,          -- 字段键（用于代码）
    field_type VARCHAR(20) NOT NULL,         -- text, textarea, select, multiselect, number, boolean
    options JSONB,                           -- 当类型为select时的选项列表
    is_required BOOLEAN DEFAULT FALSE,       -- 是否必填
    is_searchable BOOLEAN DEFAULT TRUE,      -- 是否可搜索
    default_value TEXT,                      -- 默认值
    sort_order INT DEFAULT 0,                -- 显示顺序
    created_at TIMESTAMP DEFAULT NOW()
);

CREATE INDEX idx_setting_field_definitions_category ON setting_field_definitions(category_id);
```

### 3.3 项目数据表 (setting_items)

实际的设定项目数据：

```sql
CREATE TABLE setting_items (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    category_id UUID NOT NULL REFERENCES setting_categories(id),
    workspace_id UUID NOT NULL,              -- 所属工作区
    item_code VARCHAR(20),                   -- 项目编码（如"GR-001"）
    data JSONB NOT NULL DEFAULT '{}',        -- 动态属性数据
    tags TEXT[] DEFAULT '{}',                -- 标签数组
    is_global BOOLEAN DEFAULT TRUE,          -- 是否全局共享
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

CREATE INDEX idx_setting_items_category ON setting_items(category_id);
CREATE INDEX idx_setting_items_workspace ON setting_items(workspace_id);
CREATE INDEX idx_setting_items_tags ON setting_items USING GIN(tags);
CREATE INDEX idx_setting_items_data ON setting_items USING GIN(data);
```

### 3.4 分类关联表 (setting_category_relations)

定义分类之间的依赖关系：

```sql
CREATE TABLE setting_category_relations (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    source_category_id UUID NOT NULL REFERENCES setting_categories(id),
    target_category_id UUID NOT NULL REFERENCES setting_categories(id),
    relation_type VARCHAR(50) NOT NULL,      -- 关系类型（如"推荐"）
    weight INT DEFAULT 0,                    -- 权重（用于排序）
    created_at TIMESTAMP DEFAULT NOW()
);

CREATE INDEX idx_setting_category_relations_source ON setting_category_relations(source_category_id);
CREATE INDEX idx_setting_category_relations_target ON setting_category_relations(target_category_id);
```

---

## 4. MCP 工具设计

### 4.1 类别管理

```python
# 列出所有分类
setting_list_categories(workspace_id, include_inactive=False)

# 获取分类详情（含字段定义）
setting_get_category(category_id or slug)

# 创建分类
setting_create_category(workspace_id, name, slug, description, fields, ...)

# 更新分类
setting_update_category(category_id, ...)

# 删除分类（可选：是否级联删除项目）
setting_delete_category(category_id, cascade=False)
```

### 4.2 项目 CRUD

```python
# 查询项目（按分类）
setting_list_items(
    workspace_id,
    category_id or category_slug,  # 支持按名称查询
    filters={},  # 动态过滤
    pagination={}
)

# 获取单个项目
setting_get_item(item_id)

# 创建项目
setting_create_item(
    workspace_id,
    category_id,  # 分类名称或ID都行
    data={},  # 动态数据
    tags=[],
    ...
)

# 批量创建项目（支持CSV导入）
setting_batch_create_items(workspace_id, category_id, items=[])

# 更新项目
setting_update_item(item_id, data={}, ...)

# 删除项目
setting_delete_item(item_id)
```

### 4.3 智能查询

```python
# 全文搜索（跨所有分类或指定分类）
setting_search(
    workspace_id,
    query,  # 搜索关键词
    categories=[],  # 可指定分类，不指定则搜索全部
    filters={},
    limit=20
)

# 按标签搜索
setting_search_by_tags(workspace_id, tags, category_id=None)

# 获取关联项目（如：选择"玄幻"题材后，自动返回推荐的"金手指体系"）
setting_get_related_items(
    category_id,
    item_id,
    relation_type="推荐"
)
```

### 4.4 AI 辅助查询

```python
# AI驱动的智能检索
setting_smart_query(
    workspace_id,
    intent="查找适合都市爽文的金手指体系",
    context={"题材": "都市", "风格": "爽文"}
)
```

---

## 5. Web 界面设计

### 5.1 全局设定管理页面结构

```
┌──────────────────────────────────────────────────────────┐
│  📂 全局设定管理                                          │
├──────────────────────────────────────────────────────────┤
│                                                          │
│  ┌─────────────┐  ┌────────────────────────────────┐    │
│  │ 分类列表     │  │  设定项目列表 / 编辑器            │    │
│  │             │  │                                 │    │
│  │ + 新建分类   │  │  [新增项目]  [导入CSV]          │    │
│  │             │  │  ─────────────────────────     │    │
│  │ 📚 题材分类  │  │  GR-001 玄幻退婚流            │    │
│  │ ⚡ 金手指体系│  │  GR-002 规则动物园             │    │
│  │ 👤 人设模板  │  │  ...                           │    │
│  │ 📖 情节模板  │  │                                 │    │
│  │ ⚖️ 审查规则  │  │                                 │    │
│  │             │  │                                 │    │
│  │ ─────────── │  │                                 │    │
│  │ ⚙️ 系统设置  │  │                                 │    │
│  └─────────────┘  └────────────────────────────────┘    │
│                                                          │
└──────────────────────────────────────────────────────────┘
```

### 5.2 项目编辑器（支持动态字段 + AI专用字段） - **优化版**

```
┌──────────────────────────────────────────────────────────┐
│  编辑：GR-001 玄幻退婚流                        [保存] [删除]│
├──────────────────────────────────────────────────────────┤
│                                                          │
│  编号: GR-001                              分类: 题材分类  │
│  ────────────────────────────────────────────────────    │
│                                                          │
│  **核心检索字段**（BM25优化）                             │
│  ────────────────────────────────────────────────────    │
│                                                          │
│  关键词: [退婚流|废材逆袭|莫欺少年穷____] (用|分隔)        │
│                                                          │
│  意图与同义词: [退婚打脸怎么写|三年之约____] (用|分隔)     │
│                                                          │
│  核心摘要: [退婚或逐出型起手必须先把尊严踩到底，再把反   │
│          击延迟兑现为长线承诺。__________________]        │
│          (textarea, 高权重召回)                           │
│                                                          │
│  详细展开: [退婚流不靠瞬间翻盘，而靠压抑、立誓、补刀和   │
│          后续兑现形成持续追读欲。__________________]      │
│          (textarea, 补充说明)                             │
│                                                          │
│  ────────────────────────────────────────────────────    │
│  **AI专用字段**                                          │
│  ────────────────────────────────────────────────────    │
│                                                          │
│  大模型指令: [先压后爆，耻辱必须转成长线兑现。_______]    │
│          (textarea, 直接给AI的执行指令)                   │
│                                                          │
│  毒点/反面案例: [打脸不能软收尾|主角还没兑现就被配角代打│
│          ___________________] (用|分隔，多个毒点)         │
│                                                          │
│  ────────────────────────────────────────────────────    │
│  **分类与权重**                                          │
│  ────────────────────────────────────────────────────    │
│                                                          │
│  适用技能: [✓init] [✓plan] [✓write] [ ] review         │
│                                                          │
│  适用题材: [✓玄幻] [✓仙侠] [ ] 都市  [ ] 科幻            │
│          (canonical genre，自动规范化)                    │
│                                                          │
│  层级: [✓知识补充] [ ] 提醒 [ ] 缺陷补偿                │
│                                                          │
│  ────────────────────────────────────────────────────    │
│  **动态字段**（原有JSONB）                               │
│  ────────────────────────────────────────────────────    │
│                                                          │
│  题材/流派: [玄幻退婚流________________]                   │
│                                                          │
│  题材别名: [退婚流|废材逆袭________________]  (用|分隔)    │
│                                                          │
│  核心调性: [先压后爆________________________________]     │
│                                                          │
│  节奏策略: [三章内必须有首次有效反打________________]     │
│                                                          │
│  推荐基础检索表: [命名规则|人设与关系|金手指与设定____]  │
│                                                          │
│  推荐动态检索表: [桥段套路|爽点与节奏|场景写法________]  │
│                                                          │
│  标签: [退婚|打脸|废材逆袭_______________] (用|分隔)      │
│                                                          │
│  ────────────────────────────────────────────────────    │
│                                                          │
│  [导入CSV]  [导出CSV]  [验证格式]                         │
│                                                          │
└──────────────────────────────────────────────────────────┘
```

**新增功能说明**：
- ✅ 核心检索字段区域（BM25优化）
- ✅ AI专用字段区域（ai_instruction + poison_points）
- ✅ 分类与权重区域（适用技能、适用题材、层级）
- ✅ 题材规范化提示（canonical genre，自动规范化）
- ✅ CSV导入导出按钮（规范化验证）

---

## 6. 系统优势

| 特性 | 说明 |
|------|------|
| 完全可定制 | 用户可任意增删分类和字段，不影响系统 |
| MCP 解耦 | MCP 通过分类名称查询，不依赖硬编码 |
| 动态字段 | 每个分类可有不同属性，通过 JSONB 存储 |
| 灵活搜索 | 支持按分类、标签、全文检索 |
| 级联安全 | 删除分类时可选择是否删除关联项目 |
| CSV 导入 | 支持批量导入设定数据 |

---

## 7. 待讨论事项

- [ ] 确认数据模型设计
- [ ] 确认 MCP 工具接口设计
- [ ] 确认 Web 界面布局
- [ ] 讨论项目创建流程：从全局模板初始化项目的基础数据
- [ ] 讨论设定之间的依赖关系如何实现

---

## 8. 参考资料

- [webnovel-writer-opencode CSV 参考](https://github.com/lujih/webnovel-writer-opencode/tree/master/.opencode/references/csv)
- 用户记录的设定项：
  - 叙事结构类型、核心冲突类型、世界观基调
  - 读者群体定位、故事复杂层级、叙事节奏模式
  - 情感驱动力、主题深度、题材分类、风格分类
  - 年代分类、语言与视角、角色身份职业
  - 发表平台风格、预设文风、标题结构
  - 金手指体系、男主人设预设、女主人设预设
  - 反派人设预设、情节模板、时空背景
  - 结局类型、时空背景（扩展）