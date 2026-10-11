# KBService - 知识库服务

## 概述

`KBService` 管理 Novel OS 的知识库系统，涵盖分类体系、知识实体、通用知识 (UK)、项目知识 (PK)、世界快照、题材策略、知识缺口检测和联网搜索等模块。

**源码路径**: `novel-os-mcp/src/novel_os_mcp/kb_service.py` (1390行)

## 注入依赖

```python
KBService(db: Database)
```

## 一、分类体系 (ref_categories)

### 树形结构

分类表 `ref_categories` 通过 `parent_id` 自引用形成树。

### list_categories()

三种模式:
- `include_all=True`: 查询全部 (带 child_count, entry_count 子查询)
- `parent_slug`: 查指定父节点的直接子节点
- 无参数: 查根节点 (parent_id IS NULL)

排序: `sort_order`

### CRUD

`category_create()` / `category_update()` / `category_delete()` (仅删除 is_system=false 的分类)

## 二、知识实体 (knowledge_entities)

### entity_create()

实体创建，字段: entity_type, name, content, summary, aliases, structured_data (JSONB), source, source_url, reliability (0.0-1.0), genre_tags, era。

### entity_search()

全文搜索: `search_vector @@ plainto_tsquery('simple', query)`

支持过滤: entity_type, genre (ANY(genre_tags)), era (ILIKE)

排序: `reliability DESC, use_count DESC`

### entity_update()

动态 SET 构建，支持字段: name, summary, content, source, source_url, era, status, aliases, genre_tags, structured_data, reliability。

### entity_list_relations()

查 knowledge_relations 表 (source→target)，支持 relation_type 过滤，无过滤时返回方向信息 (in/out)。

## 三、通用知识 UK (universal_knowledge)

### uk_search()

核心搜索方法，支持多维度过滤:

| 参数 | 过滤方式 |
|------|---------|
| `query` | `search_vector @@ plainto_tsquery('simple', query)` 全文搜索 |
| `category_slug` | **递归 CTE** 查找分类树中 slug 及其所有子分类 |
| `genre` | `$genre = ANY(uk.genre_tags)` |
| `era` | `uk.era ILIKE '%era%'` |
| `year` | `$year = ANY(uk.year_range)` |

排序: `reliability DESC, use_count DESC`

### uk_entry_create() / uk_entry_update() / uk_entry_delete()

标准 CRUD。创建时通过 category_slug → category_id 转换。更新支持动态字段。

### uk_stats()

统计: total, categories (distinct slug), from_web_search / from_manual 计数, avg_reliability。附带 `by_category` 分组统计。

## 四、项目知识 PK (project_knowledge)

### pk_upsert()

唯一约束: `(project_id, category, key)`。冲突时全量更新 value/description/chapter_no/tags。

### pk_list()

按 project_id 查询，可选 category 过滤，排除 `is_deleted=true`。

### pk_get() / pk_delete()

单条查询 (project_id+category+key) 和软删除。

## 五、世界快照 (world_snapshots)

### world_get_state()

查最新世界状态: 指定 chapter_no 精确查询，或 ORDER BY chapter_no DESC LIMIT 1。

### world_update_state()

唯一约束: `(project_id, chapter_no)`。字段: world_state (JSONB), story_time, story_year, story_era, story_progress (0-1), character_count, active_threads。

## 六、题材知识策略 (GENRE_STRATEGIES)

10 个硬编码题材策略:

| 题材 slug | 显示名 | 策略 | 时间线类型 |
|----------|--------|------|-----------|
| `historical_republic` | 民国历史 | real_historical | real_year (1912-1949) |
| `historical_ancient` | 古代历史 | real_historical | dynasty |
| `xianxia` | 仙侠 | progression | cultivation_progress |
| `xuanhuan` | 玄幻 | progression | power_progress |
| `sci-fi` | 科幻 | hybrid | future_year |
| `urban` | 都市 | real_modern | modern_year (2000-2030) |
| `post_apocalyptic` | 末日 | pure_fiction | post_disaster |
| `horror` | 灵异 | pure_fiction | floating |
| `game` | 游戏 | pure_fiction | game_time |
| `time_travel` | 穿越 | hybrid | cross_timeline |
| `isekai` | 异世界 | pure_fiction | floating |

每个策略包含: display_name, strategy, timeline_type, data_sources, search_keywords。

### 数据库扩展

通过 `genre_canonical` 和 `genre_knowledge_config` 表支持自定义配置。

### genre_list()

从 genre_canonical + genre_knowledge_config JOIN 查询，解析 included_categories slug → 中文名。fallback 到 GENRE_STRATEGIES。

### genre_preheat()

预热: 根据题材从 UK 查询相关知识条目，写入 PK (category="genre_template", key="preheat_{genre}_{cat}_{id}")。

### genre_get_search_keywords()

从 genre_canonical 的 typical_elements 和 platform_tags 生成搜索关键词，或 fallback 到 GENRE_STRATEGIES 的 search_keywords 模板。

## 七、知识缺口管理

### gap_analyze()

分析题材的知识缺口:

1. 获取 `genre_knowledge_config` 的 `included_categories` 列表
2. 对每个分类统计 UK 条目数
3. 核心分类 (power_system, world_building, character_setting, internal-energy, magic 及特定前缀): 预期 >= 3 条
4. 补充分类: 预期 >= 1 条
5. 返回 `should_fill: true` 的分类列表

### detect_gaps()

从章节大纲文本中检测知识缺口:

1. 正则提取 2-6 字中文词 `[\u4e00-\u9fff]{2,6}`
2. 去重 (前 20 个)
3. 分别检查 UK (topic ILIKE), PK (key ILIKE 或 value::text ILIKE), knowledge_entities (name ILIKE)
4. 三处均不存在的 → 记录为 gap (type="missing_entity")

### gap_create() / gap_list() / gap_resolve()

标准缺口管理 CRUD，写入 `ref_gap_logs` 表。

## 八、联网搜索 search_and_store()

三步流程:

```
Step 1: search_create_job() → 写入 ref_search_jobs (status='pending')
Step 2: 遍历 search_results，逐条 uk_entry_create() (source='web_search', reliability=0.5)
Step 3: search_complete_job() → 更新 status='completed', results_count, entries_created
```

## 九、项目知识包

### get_project_pack() / create_project_pack()

基于 `genre_knowledge_config` 的 included_categories 创建项目包。`ON CONFLICT (project_id) DO UPDATE`。

### update_project_pack()

更新 active_categories 和 custom_categories (JSONB)。

### add_custom_category() / remove_custom_category()

在 custom_categories JSONB 中添加/移除自定义分类。

## 十、涉及的数据库表

| 表名 | 操作 |
|------|------|
| `ref_categories` | SELECT / INSERT / UPDATE / DELETE |
| `knowledge_entities` | SELECT / INSERT / UPDATE |
| `knowledge_relations` | SELECT / INSERT (ON CONFLICT) |
| `universal_knowledge` | SELECT / INSERT / UPDATE / DELETE |
| `project_knowledge` | SELECT / INSERT / UPDATE / ... |
| `world_snapshots` | SELECT / INSERT (ON CONFLICT) |
| `ref_search_jobs` | INSERT / UPDATE |
| `ref_gap_logs` | INSERT / SELECT / UPDATE |
| `genre_canonical` | SELECT / INSERT / DELETE |
| `genre_knowledge_config` | SELECT / INSERT / UPDATE / DELETE |
| `project_knowledge_pack` | SELECT / INSERT / UPDATE |
| `setting_categories` | SELECT |