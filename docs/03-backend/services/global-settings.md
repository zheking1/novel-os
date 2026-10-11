# Global Settings 服务 — 全局设定管理

**源码**: `novel-os-mcp/src/novel_os_mcp/global_settings.py` (628 行)

## 概述

Global Settings 服务管理写作设定系统，包含分类管理、设定项目的全文检索、题材规范化和 CSV 导入导出。

## 数据库表/视图/函数

| 名称 | 类型 | 说明 |
|------|------|------|
| `setting_categories` | 表 | 设定分类 |
| `setting_field_definitions` | 表 | 分类的字段定义 |
| `setting_items` | 表 | 设定项目 |
| `setting_category_relations` | 表 | 分类层级关系 |
| `fn_setting_items_bm25_search` | 数据库函数 | BM25 全文检索 |
| `fn_genre_resolve` | 数据库函数 | 题材规范化解析 |
| `v_setting_items_overview` | 视图 | 设定项目全局视图 |
| `v_genre_canonical_list` | 视图 | 规范题材列表 |

---

## 一、分类管理 (Setting Categories)

### 分类属性

| 字段 | 类型 | 说明 |
|------|------|------|
| `name` | str | 分类名称 |
| `slug` | str | 唯一标识 (workspace-scoped) |
| `description` | str\|None | 描述 |
| `icon` | str | 图标 (emoji) |
| `sort_order` | int | 排序 |
| `is_standard` | bool | 是否标准分类 (不可删除) |
| `is_active` | bool | 是否启用 |

### list_categories

列出 workspace 下的所有分类，按 `sort_order, name` 排序。`is_active=None` 时列出全部。

### get_category

获取分类详情，**自动附加 `field_definitions`**（从 `setting_field_definitions` 表 JOIN）。

### upsert_category

创建/更新分类（`ON CONFLICT (workspace_id, slug)`）。`created_by` / `updated_by` 记录操作用户。

### delete_category

- 标准分类 (`is_standard=true`): 仅隐藏 (`is_active = false`)，不物理删除
- 非标准分类: 物理删除（字段定义级联删除）

---

## 二、字段定义 (Field Definitions)

字段定义通过 `get_category()` 返回，存储在 `setting_field_definitions` 表中。

### 7 种字段类型

| 类型 | 常量 | 说明 |
|------|------|------|
| 文本 | `text` | 单行文本 |
| 文本域 | `textarea` | 多行文本 |
| 下拉 | `select` | 单选下拉，需 `options` |
| 多选 | `multiselect` | 多选，需 `options` |
| 数字 | `number` | 数值输入 |
| 布尔 | `boolean` | 开关 |
| JSON | `json` | JSON 编辑器 |

### 字段属性

| 属性 | 说明 |
|------|------|
| `field_key` | 字段键名 |
| `field_name` | 显示名称 |
| `is_required` | 是否必填 |
| `is_searchable` | 是否参与搜索 |
| `default_value` | 默认值 |
| `placeholder` | 占位提示 |
| `help_text` | 帮助说明 |

---

## 三、设定项目管理 (Setting Items)

### 设定项属性

| 字段 | 类型 | 说明 |
|------|------|------|
| `item_code` | str | 唯一编码 (格式: `GS-0001`) |
| `core_summary` | str | **核心摘要** (必填) |
| `detailed_expansion` | str\|None | 详细展开 |
| `ai_instruction` | str\|None | AI 使用指令 |
| `keywords` | list[str] | 关键词 |
| `intent_synonyms` | list[str] | 意图同义词 |
| `poison_points` | list[str] | 毒点/注意事项 |
| `level` | str | 级别 |
| `applicable_skills` | list[str] | 适用技能 |
| `applicable_genres` | list[str] | 适用题材 |
| `data` | dict | JSONB 扩展数据 |
| `tags` | list[str] | 标签 |
| `is_global` | bool | 是否全局可用 |
| `sort_order` | int | 排序 |

### 三种级别 (Level)

| 级别 | 常量 | 说明 |
|------|------|------|
| 知识 | `knowledge` | 写作知识点 |
| 提醒 | `reminder` | 创作提醒 |
| 缺陷补偿 | `defect_compensation` | AI 缺陷补偿指令 |

### list_items

支持 `category_id`、`is_global`、`level`、`tags` 过滤。全局项 (`is_global=true`) 跨 workspace 可见。

### upsert_item

- 若未提供 `item_code`，自动生成 `GS-{count+1:04d}` 格式编码
- `ON CONFLICT (workspace_id, item_code)`

### delete_item

软删除 (`is_active = false`)。

---

## 四、BM25 全文检索

### bm25_search

调用 PostgreSQL 函数 `fn_setting_items_bm25_search` 进行 BM25 检索:

```sql
SELECT * FROM fn_setting_items_bm25_search(
    query, workspace_id, category_id, level, skill, genre, limit, offset
)
```

**检索维度**: `category_id`, `level`, `skill`, `genre` 可作为过滤条件。

**返回字段**: 含 `applicable_skills`、`applicable_genres`、`tags`（转为 Python list）。

---

## 五、题材规范化 (Genre Resolution)

### resolve_genre

调用 `fn_genre_resolve(input_text)` 解析自由文本输入为规范题材标签。

### list_genres

从 `v_genre_canonical_list` 视图列出所有规范题材，含 `platform_tags`、`aliases`。

### delete_genre

软删除 (`is_active = false`)，通过 `slug` 定位。

### upsert_genre (可用)

MCP 工具 `setting.genre.upsert` 提供。

---

## 六、CSV 导入导出

### csv_import

从 CSV 文本导入设定项:

**CSV 列**: `item_code`, `keywords`, `intent_synonyms`, `core_summary`, `detailed_expansion`, `ai_instruction`, `poison_points`, `level`, `applicable_skills`, `applicable_genres`, `tags`

- 数组字段使用 `|` 分隔符（`_parse_array` 解析）
- 逐行调用 `upsert_item`，错误记录到 `errors` 列表

### csv_export

导出为 CSV 文本，数组字段用 `|` 连接。

---

## 工作流引导

1. 初始化 → `setting.category.upsert()` 创建分类 + 字段定义
2. 添加知识 → `setting.item.upsert()` 创建设定项
3. 全文检索 → `setting.item.search()` → 底层调用 `bm25_search()`
4. 题材处理 → `setting.genre.resolve(input_text)` 规范化
5. 批量导入 → `setting.item.csv_import(csv_content)` / `csv_export()` 导出