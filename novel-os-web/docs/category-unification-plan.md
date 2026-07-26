# 知识分类体系统一方案

> 目标：消除系统内两套独立分类体系（`categories` + `ref_categories`），统一为 `ref_categories`。

---

## 一、需求文档

### 1.1 背景

当前系统存在两套分类体系：

| | `categories` (旧) | `ref_categories` (新) |
|---|---|---|
| 条目数 | 253 条 | 160 条 |
| slug 格式 | 中文/混合 `character_主角` | 英文 `world_building` |
| 关联的知识表 | `knowledge_base` (2327条目) | `universal_knowledge` (0条目) |
| 检索入口 | `rag.search_knowledge` → `knowledge_service.search_items` | `kb.uk.*` 系列 |
| 题材体系 | 无关联 | `genre_knowledge_config.included_categories` |

两套体系互不联通，导致：
- 题材策略配置的 `included_categories` 用 `ref_categories` slug，但 RAG 检索用 `categories` slug，无法按题材过滤知识
- `genre_preheat` 想加载 UK 条目但 `universal_knowledge` 为空
- UI 上有重复的分类管理功能

### 1.2 需求目标

1. **删除** 所有无引用或只被旧体系引用的表
2. **统一** 所有工具和页面使用 `ref_categories` 作为唯一分类树
3. **删除** 21 个旧 `knowledge.*` MCP 工具
4. **改造** `context.py`（章节生成上下文）不再依赖 `knowledge_base` 表
5. **改造** 2 个受影响的旧前端页面
6. **保证** 章节生成流程不中断

### 1.3 范围外的

- `setting_categories` 表 → 独立的 settings 体系，不受影响
- `state_entities` / `project_knowledge` → 当前无数据，留后续填充
- 知识条目数据的填充 → 未来任务

---

## 二、设计文档

### 2.1 数据层变更

#### 删除的表（5 张）

```sql
DROP TABLE categories;                  -- 旧分类表，被 ref_categories 替代
DROP TABLE setting_category_relations;   -- 零代码引用
DROP TABLE genre_category_bindings;      -- 被 genre_knowledge_config 替代
DROP TABLE knowledge_tags;              -- 零代码引用
DROP TABLE knowledge_vectors;           -- 零代码引用
```

#### 保留但清理引用的表

| 表 | 处理 |
|---|---|
| `knowledge_base` | 不删。`context.py` 查询它，改为查 `state_entities` + `project_knowledge` 后不再引用 |
| `user_knowledge` | 不删。先停用 `knowledge.user.*` 工具，后续统一到 `project_knowledge` 用户维度 |
| `knowledge_review` | 不删。先停用 `knowledge.review.*` 工具，后续统一到新的审核体系 |

### 2.2 代码层变更

#### 删除文件

| 文件 | 原因 |
|---|---|
| `novel-os-mcp/src/novel_os_mcp/knowledge_service.py` | 全部查询 `categories` + `knowledge_base`，被 `kb_service.py` 替代 |
| `novel-os-web/js/pages/knowledge.js` | 旧版 UK 管理页，调 `knowledge.item.list` |

#### 修改文件

| 文件 | 改动 |
|---|---|
| `context.py` | `_retrieve_knowledge_base()` → 改查 `state_entities` + `project_knowledge` |
| `tools/knowledge.py` | 删除 `knowledge.item.*` / `knowledge.user.*` / `knowledge.category.*` / `knowledge.bulk_import` / `knowledge.review.get` / `knowledge.review.stats` 共 21 个工具注册 |
| `tools/vector.py` | `rag_search_knowledge` 改为查 `universal_knowledge` 表 |
| `tools/knowledge_pack.py` | 清理对旧 `categories` 的引用（如有） |
| `js/pages/knowledge-stats-page.js` | 将 `knowledge.category.stats` 改为 `kb.uk.stats` |
| `js/pages/knowledge-review-page.js` | 将 `knowledge.review.*` 改为注释/占位（等新审核体系） |
| `js/pages/discussion-room-page.js` | L16 schema hint `categories` → `ref_categories` |
| `index.html` | 删除 `knowledge.js` 脚本引用 |
| `js/core/menu-manager.js` | 如需移除废弃菜单项 |
| `js/core/api-wrapper.js` | 清理 `knowledge.item.*` 的 API wrapper（如有） |

### 2.3 `context.py` 改造方案

原 `_retrieve_knowledge_base()` 从 `knowledge_base` 获取以下上下文：

| 查询目标 | 新数据源 | 查询方式 |
|---|---|---|
| 角色卡片 | `state_entities` | `WHERE entity_type = 'character' AND name ILIKE '%xxx%'` |
| 阵营信息 | `state_entities` | `WHERE entity_type = 'faction' AND name ILIKE '%xxx%'` |
| 力量体系 | `project_knowledge` | `WHERE category = 'power_system' AND project_id = $1` |
| 世界设定 | `project_knowledge` | `WHERE category = 'world_building' AND project_id = $1` |
| 情节参考 | `project_knowledge` | `WHERE category = 'plot_and_story' AND project_id = $1` |

若无数据返回空列表，不影响流程继续。

### 2.4 MCP 工具变更图谱

```
删除 (21个):
  knowledge.item.list/get/search/upsert/delete          → 用 kb.uk.* 替代
  knowledge.user.list/get/upsert/delete/create_from_base/submit_review/stats  → 暂无替代
  knowledge.category.list/get/stats/upsert/delete       → 用 kb.category.* 替代
  knowledge.bulk_import                                  → 用 kb.uk.create 批量替代
  knowledge.review.get/stats                             → 暂无替代

保留 (6个):
  knowledge.review.list/approve/reject                   → 知识审核页面仍用
  knowledge.audit_all/audit_status/council_debate_all    → 独立服务，不受影响
```

---

## 三、开发计划

### 阶段 1：保护性改造（context.py 解耦）

**目标**：让章节生成不依赖 `knowledge_base`

1. 修改 `context.py::_retrieve_knowledge_base()`
   - 角色查询 → `state_entities`
   - 阵营查询 → `state_entities`
   - 力量/世界/情节 → `project_knowledge`
2. 上传 + 重建 MCP 容器
3. 验证 `workflow.prepare_chapter_context` 不报错

### 阶段 2：前端适配

**目标**：消除旧工具的前端调用

1. 修改 `knowledge-stats-page.js` → `kb.uk.stats`
2. 修改 `knowledge-review-page.js` → 占位（暂无审核数据）
3. 修改 `discussion-room-page.js` → schema hint 修正
4. 删除 `knowledge.js`
5. 删除 `index.html` 中的 `knowledge.js` 引用
6. 上传 + 重建 Web 容器
7. 验证前端正常，无 JS 报错

### 阶段 3：后端清理

**目标**：删除旧工具和表

1. `tools/knowledge.py` — 删除 21 个旧工具注册
2. `tools/vector.py` — `rag_search_knowledge` 改查 `universal_knowledge`
3. 删除 `knowledge_service.py` 文件
4. 执行 SQL DROP 5 张表
5. 上传 + 重建 MCP 容器
6. 验证 `kb.genre.list`, `kb.category.tree`, `kb.uk.search` 等新工具正常
7. 验证 `rag.search_knowledge` 返回正常结构（允许空结果）

### 阶段 4：验证

1. 前端：题材策略页、分类管理页、UK 管理页正常
2. MCP：`kb.*` 系列工具全部可用
3. 章节生成：`workflow.prepare_chapter_context` 通过
4. RAG 检索：`rag.search_knowledge` 返回 ok（允许空结果）

### 预估工作量

| 阶段 | 内容 | 预估 |
|---|---|---|
| 1 | context.py 解耦 | 20 min |
| 2 | 前端适配 | 20 min |
| 3 | 后端清理 + DROP 表 | 15 min |
| 4 | 验证 | 10 min |
| **合计** | | **~65 min** |
