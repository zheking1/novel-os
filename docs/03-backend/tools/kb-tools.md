# Knowledge Base Tools — 知识库全栈

> Source: `tools/kb.py`, `tools/knowledge_pack.py`, `tools/knowledge_audit.py`
> Dependencies: `db`, `auth`, `kb_service`

---

## kb.category — 知识分类

### kb.category.list

```python
@mcp.tool(name="kb.category.list")
async def kb_category_list(parent_slug: str | None = None) -> list[dict[str, Any]]
```

**Purpose:** 列出知识分类。不传 `parent_slug` 时返回顶级分类。

### kb.category.tree

```python
@mcp.tool(name="kb.category.tree")
async def kb_category_tree() -> list[dict[str, Any]]
```

**Purpose:** 列出所有分类为扁平列表（含 `parent_id`），前端可据此构建树。

### kb.category.create

```python
async def kb_category_create(
    slug: str, name: str,
    parent_id: str | None = None, description: str | None = None,
    sort_order: int = 0,
) -> dict[str, Any]
```

**Purpose:** 创建知识分类。`parent_id` 为空则顶级。

### kb.category.update

```python
async def kb_category_update(
    category_id: str, name: str | None = None, slug: str | None = None,
    description: str | None = None, sort_order: int | None = None,
    parent_id: str | None = None,
) -> dict[str, Any]
```

### kb.category.delete

```python
async def kb_category_delete(category_id: str) -> bool
```

**Purpose:** 删除分类。不可删除系统分类。

**DB Tables:** `ref_categories` | **Service:** `kb_service`

---

## kb.entity — 知识实体

### kb.entity.create

```python
async def kb_entity_create(
    entity_type: str, name: str, content: str,
    summary: str | None = None, aliases: list[str] | None = None,
    structured_data: dict | None = None, source: str = "manual",
    source_url: str | None = None, reliability: float = 0.5,
    genre_tags: list[str] | None = None, era: str | None = None,
) -> dict[str, Any]
```

**Purpose:** 创建知识实体（人物/事件/地点/势力/概念）。注意：**故事中的角色/势力请用 `state.entity.upsert` 而非此工具。**

**DB Tables:** `knowledge_entities` | **Service:** `kb_service`

### kb.entity.get

```python
async def kb_entity_get(entity_id: str) -> dict[str, Any] | None
```

### kb.entity.search

```python
async def kb_entity_search(
    query: str, entity_type: str | None = None, genre: str | None = None,
    era: str | None = None, limit: int = 20,
) -> list[dict[str, Any]]
```

### kb.entity.update

```python
async def kb_entity_update(
    entity_id: str, name: str | None = None, entity_type: str | None = None,
    description: str | None = None, aliases: list[str] | None = None,
    traits: dict | None = None, status: str | None = None,
) -> dict[str, Any] | None
```

### kb.relation.create

```python
async def kb_relation_create(
    from_entity_id: str, to_entity_id: str, relation_type: str,
    detail: str | None = None, strength: float = 1.0,
) -> dict[str, Any]
```

**Purpose:** 创建实体关系。类型：`participated_in` / `located_at` / `belongs_to` / `related_to` / `caused_by` / `same_as` / `influenced_by`

### kb.entity.list_relations

```python
async def kb_entity_list_relations(
    entity_id: str, relation_type: str | None = None,
) -> list[dict[str, Any]]
```

---

## kb.uk — 通用知识

### kb.uk.search

```python
async def kb_uk_search(
    query: str | None = None, category_slug: str | None = None,
    genre: str | None = None, era: str | None = None,
    year: int | None = None, limit: int = 20,
) -> list[dict[str, Any]]
```

**Purpose:** 搜索 `universal_knowledge` 库。关键词/分类/题材/年代多维度过滤。**无权限要求。**

### kb.uk.create

```python
async def kb_uk_create(
    topic: str, content: str, category_slug: str | None = None,
    summary: str | None = None, era: str | None = None,
    year_range: str | None = None, genre_tags: list[str] | None = None,
    source: str = "manual", source_url: str | None = None,
    reliability: float = 0.5, tags: list[str] | None = None,
) -> dict[str, Any]
```

### kb.uk.update

```python
async def kb_uk_update(
    entry_id: str, topic: str | None = None, content: str | None = None,
    summary: str | None = None, era: str | None = None,
    source: str | None = None, source_url: str | None = None,
    status: str | None = None, reliability: float | None = None,
    genre_tags: list[str] | None = None, year_range: str | None = None,
    tags: list[str] | None = None, structured_data: dict | None = None,
) -> dict[str, Any]
```

### kb.uk.delete

```python
async def kb_uk_delete(entry_id: str) -> bool
```

### kb.uk.stats

```python
async def kb_uk_stats(genre: str | None = None) -> dict[str, Any]
```

**DB Tables:** `universal_knowledge` | **Service:** `kb_service`

---

## kb.pk — 项目知识

### kb.pk.upsert

```python
async def kb_pk_upsert(
    workspace: str, project: str, project_id: str,
    category: str, key: str, value: str,
    description: str | None = None, chapter_no: int | None = None,
    tags: list[str] | None = None,
) -> dict[str, Any]
```

### kb.pk.get

```python
async def kb_pk_get(
    workspace: str, project: str, project_id: str, category: str, key: str,
) -> dict[str, Any]
```

### kb.pk.list

```python
async def kb_pk_list(
    workspace: str, project: str, project_id: str, category: str | None = None,
) -> list[dict[str, Any]]
```

### kb.pk.delete

```python
async def kb_pk_delete(
    workspace: str, project: str, project_id: str, category: str, key: str,
) -> bool
```

**DB Tables:** `project_knowledge` | **Service:** `kb_service`

---

## kb.world — 世界状态

### kb.world.get

```python
async def kb_world_get(
    workspace: str, project: str, chapter_no: int | None = None,
) -> dict[str, Any]
```

**Purpose:** 获取最近的世界状态快照。可指定章节号查询特定时刻。

### kb.world.update

```python
async def kb_world_update(
    workspace: str, project: str, project_id: str, chapter_no: int,
    world_state: str, story_time: str | None = None,
    story_year: int | None = None, story_era: str | None = None,
    story_progress: str | None = None, character_count: int | None = None,
    active_threads: int | None = None,
) -> dict[str, Any]
```

### kb.world.list

```python
async def kb_world_list(
    workspace: str, project: str, project_id: str, limit: int = 100,
) -> list[dict[str, Any]]
```

### kb.world.auto_update

```python
async def kb_world_auto_update(
    workspace: str, project: str, chapter_no: int, generated_content: str,
    story_time: str | None = None, story_year: int | None = None,
    story_era: str | None = None,
) -> dict[str, Any]
```

**DB Tables:** `world_snapshots` | **Service:** `kb_service`

---

## kb.search — 自动搜索

### kb.search.create_job

```python
async def kb_search_create_job(
    query_text: str, workspace: str, project: str,
    project_id: str | None = None, category_slug: str | None = None,
    chapter_no: int | None = None, triggered_by: str | None = None,
) -> dict[str, Any]
```

### kb.search.complete_job

```python
async def kb_search_complete_job(
    job_id: str, results_count: int, entries_created: int,
) -> dict[str, Any]
```

### kb.auto.search_and_store

```python
async def kb_auto_search_and_store(
    query: str, search_results: list[dict], workspace: str, project: str,
    project_id: str | None = None, category_slug: str | None = None,
    genre_tags: list[str] | None = None, chapter_no: int | None = None,
) -> dict[str, Any]
```

**Purpose:** 一键完成联网搜索+知识存储。Agent 完成搜索后将结果传入此工具，系统自动写入 UK 库并关联到项目。

**DB Tables:** `search_jobs` | **Service:** `kb_service`

---

## kb.gap — 知识缺口

### kb.gap.create

```python
async def kb_gap_create(
    description: str, workspace: str, project: str,
    project_id: str | None = None, gap_type: str | None = None,
    entity_name: str | None = None, entity_type: str | None = None,
    context: str | None = None,
) -> dict[str, Any]
```

### kb.gap.list

```python
async def kb_gap_list(
    workspace: str, project: str, project_id: str | None = None,
    resolved: bool | None = None,
) -> list[dict[str, Any]]
```

### kb.gap.resolve

```python
async def kb_gap_resolve(gap_id: str, entry_id: str | None = None) -> bool
```

### kb.gap.detect

```python
async def kb_gap_detect(
    workspace: str, project: str, project_id: str,
    chapter_plan: dict | None = None, chapter_no: int | None = None,
) -> list[dict[str, Any]]
```

**Purpose:** 从章节大纲自动检测潜在的知识缺口（AI 分析缺失的背景设定/角色信息等）。

### kb.gap.analyze

```python
async def kb_gap_analyze(genre: str) -> dict[str, Any]
```

**Purpose:** 分析指定题材的常见知识缺口模式。

**DB Tables:** `knowledge_gaps` | **Service:** `kb_service`

---

## kb.genre — 题材策略

### kb.genre.list

```python
async def kb_genre_list() -> list[dict[str, Any]]
```

### kb.genre.get

```python
async def kb_genre_get(genre_id: str) -> dict[str, Any]
```

### kb.genre.keywords

```python
async def kb_genre_keywords(
    genre_id: str, year: int | None = None, city: str | None = None,
    event: str | None = None, dynasty: str | None = None,
) -> list[str]
```

**Purpose:** 生成题材专属搜索关键词。

### kb.genre.preheat

```python
async def kb_genre_preheat(
    workspace: str, project: str, project_id: str, genre: str,
) -> dict[str, Any]
```

**Purpose:** 预加载该题材相关的 UK 条目。用于项目初始化时批量获取参考知识。

### kb.genre.update

```python
async def kb_genre_update(
    genre: str, included_categories: list[str] | None = None,
    excluded_categories: list[str] | None = None,
    description: str | None = None,
) -> dict[str, Any]
```

### kb.genre.create

```python
async def kb_genre_create(
    slug: str, name: str, description: str | None = None,
    typical_elements: list[str] | None = None,
    target_audience: str | None = None, platform_tags: list[str] | None = None,
    aliases: list[str] | None = None,
    included_categories: list[str] | None = None,
    excluded_categories: list[str] | None = None,
) -> dict[str, Any]
```

### kb.genre.delete

```python
async def kb_genre_delete(slug: str) -> dict[str, Any]
```

**DB Tables:** `genre_knowledge_config`, `genre_canonical` | **Service:** `kb_service`

---

## kb.pack — 项目知识包

> Source: `tools/knowledge_pack.py`

### kb.pack.genre.list

```python
async def kb_pack_genre_list() -> dict[str, Any]
```

**Purpose:** 列出所有可用的小说类型知识配置。

### kb.pack.genre.get

```python
async def kb_pack_genre_get(genre: str) -> dict[str, Any]
```

### kb.pack.get

```python
async def kb_pack_get(workspace: str, project: str, project_id: str) -> dict[str, Any]
```

### kb.pack.create

```python
async def kb_pack_create(workspace: str, project: str, project_id: str, genre: str) -> dict[str, Any]
```

**Purpose:** 基于小说类型创建项目知识包，自动配置启用的分类。

### kb.pack.update

```python
async def kb_pack_update(
    workspace: str, project: str, project_id: str,
    active_categories: list[str] | None = None,
) -> dict[str, Any]
```

### kb.pack.custom.add

```python
async def kb_pack_custom_add(
    workspace: str, project: str, project_id: str,
    name: str, parent: str | None = None, description: str | None = None,
) -> dict[str, Any]
```

### kb.pack.custom.remove

```python
async def kb_pack_custom_remove(
    workspace: str, project: str, project_id: str, name: str,
) -> dict[str, Any]
```

### kb.pack.categories

```python
async def kb_pack_categories(workspace: str, project: str, project_id: str) -> dict[str, Any]
```

**DB Tables:** `project_packs` | **Service:** `kb_service`

---

## knowledge — 知识审计

> Source: `tools/knowledge_audit.py`

### knowledge.audit_all

```python
async def knowledge_audit_all(
    workspace: str, project: str, mode: str | None = None,
) -> dict[str, Any]
```

**Purpose:** 审计所有知识分类，生成进化提案。`mode`: `None`（新增+优化）/ `"add"` / `"optimize"`。

### knowledge.audit_status

```python
async def knowledge_audit_status(workspace: str, project: str) -> dict[str, Any]
```

### knowledge.council_debate_all

```python
async def knowledge_council_debate_all(workspace: str, project: str) -> dict[str, Any]
```

**Purpose:** 辩论委员会对提案进行裁决。

**DB Tables:** `system_evolution_proposals` | **Service:** `KnowledgeAuditService`