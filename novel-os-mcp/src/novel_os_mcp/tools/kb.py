import logging
from typing import Any

from ..mcp_core import mcp
from ..deps import db, auth, kb_service, knowledge_service
from ..tool_auth import get_principal, validate_required, validate_length

logger = logging.getLogger("novel_os_mcp.tools.kb")


async def _get_user_id(username: str) -> str:
    """根据用户名获取用户ID"""
    row = await db.fetchrow("SELECT id::text FROM users WHERE username = $1", username)
    if not row:
        raise ValueError(f"用户未找到: {username}")
    return row["id"]


@mcp.tool(name="kb.category.list")
async def kb_category_list(parent_slug: str | None = None) -> list[dict[str, Any]]:
    """List knowledge categories. No parent_slug = top-level categories."""
    principal = await get_principal("read")
    logger.info("kb_category_list called")
    return await kb_service.list_categories(parent_slug=parent_slug)


@mcp.tool(name="kb.category.tree")
async def kb_category_tree() -> list[dict[str, Any]]:
    """List all knowledge categories as flat list with parent_id for tree building."""
    principal = await get_principal("read")
    logger.info("kb_category_tree called")
    return await kb_service.list_categories(include_all=True)


@mcp.tool(name="kb.category.create")
async def kb_category_create(
    slug: str,
    name: str,
    parent_id: str | None = None,
    description: str | None = None,
    sort_order: int = 0,
) -> dict[str, Any]:
    """创建知识分类。parent_id 为空则创建顶级分类。"""
    principal = await get_principal("write")
    logger.info("kb_category_create called")
    validate_required(locals(), "slug", "name")
    return await kb_service.category_create(
        slug=slug, name=name, parent_id=parent_id,
        description=description, sort_order=sort_order,
    )


@mcp.tool(name="kb.category.update")
async def kb_category_update(
    category_id: str,
    name: str | None = None,
    slug: str | None = None,
    description: str | None = None,
    sort_order: int | None = None,
    parent_id: str | None = None,
) -> dict[str, Any]:
    """更新知识分类属性。"""
    principal = await get_principal("write")
    logger.info("kb_category_update called")
    validate_required(locals(), "category_id")
    return await kb_service.category_update(
        category_id=category_id, name=name, slug=slug,
        description=description, sort_order=sort_order, parent_id=parent_id,
    )


@mcp.tool(name="kb.category.delete")
async def kb_category_delete(category_id: str) -> bool:
    """删除知识分类（不能删除系统分类）。"""
    principal = await get_principal("write")
    logger.info("kb_category_delete called")
    validate_required(locals(), "category_id")
    return await kb_service.category_delete(category_id=category_id)


@mcp.tool(name="kb.entity.create")
async def kb_entity_create(
    entity_type: str,
    name: str,
    content: str,
    summary: str | None = None,
    aliases: list[str] | None = None,
    structured_data: dict | None = None,
    source: str = "manual",
    source_url: str | None = None,
    reliability: float = 0.5,
    genre_tags: list[str] | None = None,
    era: str | None = None,
) -> dict[str, Any]:
    """创建知识实体（人物/事件/地点/势力/概念）。"""
    principal = await get_principal("write")
    logger.info("kb_entity_create called")
    validate_required(locals(), "name", "entity_type")
    return await kb_service.entity_create(
        entity_type=entity_type, name=name, content=content,
        summary=summary, aliases=aliases, structured_data=structured_data,
        source=source, source_url=source_url, reliability=reliability,
        genre_tags=genre_tags, era=era,
    )


@mcp.tool(name="kb.entity.get")
async def kb_entity_get(entity_id: str) -> dict[str, Any] | None:
    """通过 ID 获取知识实体详情。"""
    principal = await get_principal("read")
    logger.info("kb_entity_get called")
    validate_required(locals(), "entity_id")
    return await kb_service.entity_get(entity_id=entity_id)


@mcp.tool(name="kb.entity.search")
async def kb_entity_search(
    query: str,
    entity_type: str | None = None,
    genre: str | None = None,
    era: str | None = None,
    limit: int = 20,
) -> list[dict[str, Any]]:
    """搜索知识实体。支持按类型、题材、年代过滤。"""
    principal = await get_principal("read")
    logger.info("kb_entity_search called")
    return await kb_service.entity_search(
        query=query, entity_type=entity_type, genre=genre, era=era, limit=limit,
    )


@mcp.tool(name="kb.entity.update")
async def kb_entity_update(
    entity_id: str,
    name: str | None = None,
    entity_type: str | None = None,
    description: str | None = None,
    aliases: list[str] | None = None,
    traits: dict | None = None,
    status: str | None = None,
) -> dict[str, Any] | None:
    """更新知识实体字段。仅传入需要更新的字段。"""
    principal = await get_principal("write")
    logger.info("kb_entity_update called")
    fields = {}
    for k, v in {"name": name, "entity_type": entity_type, "description": description,
                  "aliases": aliases, "traits": traits, "status": status}.items():
        if v is not None:
            fields[k] = v
    return await kb_service.entity_update(entity_id=entity_id, **fields)


@mcp.tool(name="kb.relation.create")
async def kb_relation_create(
    from_entity_id: str,
    to_entity_id: str,
    relation_type: str,
    detail: str | None = None,
    strength: float = 1.0,
) -> dict[str, Any]:
    """创建两个实体间的关系。关系类型：participated_in/located_at/belongs_to/related_to/caused_by/same_as/influenced_by。"""
    principal = await get_principal("write")
    logger.info("kb_relation_create called")
    validate_required(locals(), "from_entity_id", "to_entity_id", "relation_type")
    return await kb_service.relation_create(
        from_entity_id=from_entity_id, to_entity_id=to_entity_id,
        relation_type=relation_type, detail=detail, strength=strength,
    )


@mcp.tool(name="kb.entity.list_relations")
async def kb_entity_list_relations(
    entity_id: str, relation_type: str | None = None
) -> list[dict[str, Any]]:
    """列出实体的所有关系。可按关系类型过滤。"""
    principal = await get_principal("read")
    logger.info("kb_entity_list_relations called")
    validate_required(locals(), "entity_id")
    return await kb_service.entity_list_relations(entity_id=entity_id, relation_type=relation_type)


@mcp.tool(name="kb.uk.search")
async def kb_uk_search(
    query: str,
    category_slug: str | None = None,
    genre: str | None = None,
    era: str | None = None,
    year: int | None = None,
    limit: int = 20,
) -> list[dict[str, Any]]:
    """搜索 universal_knowledge 知识库。支持关键词、分类、题材、年代过滤。"""
    principal = await get_principal(None)
    logger.info("kb_uk_search called")
    return await kb_service.uk_search(
        query=query, category_slug=category_slug, genre=genre,
        era=era, year=year, limit=limit,
    )


@mcp.tool(name="kb.uk.create")
async def kb_uk_create(
    topic: str,
    content: str,
    category_slug: str | None = None,
    summary: str | None = None,
    era: str | None = None,
    year_range: list[int] | None = None,
    genre_tags: list[str] | None = None,
    source: str = "manual",
    source_url: str | None = None,
    reliability: float = 0.5,
    tags: list[str] | None = None,
) -> dict[str, Any]:
    """创建 universal_knowledge 条目。"""
    principal = await get_principal(None)
    logger.info("kb_uk_create called")
    validate_required(locals(), "topic", "content")
    validate_length(locals(), {"topic": 200, "content": 100000})
    return await kb_service.uk_entry_create(
        topic=topic, content=content, category_slug=category_slug,
        summary=summary, era=era, year_range=year_range, genre_tags=genre_tags,
        source=source, source_url=source_url, reliability=reliability, tags=tags,
    )


@mcp.tool(name="kb.uk.update")
async def kb_uk_update(
    entry_id: str,
    topic: str | None = None,
    content: str | None = None,
    summary: str | None = None,
    era: str | None = None,
    source: str | None = None,
    source_url: str | None = None,
    status: str | None = None,
    reliability: float | None = None,
    genre_tags: list[str] | None = None,
    year_range: list[int] | None = None,
    tags: list[str] | None = None,
    structured_data: dict | None = None,
) -> dict[str, Any]:
    """更新 universal_knowledge 条目。仅传入需要更新的字段。"""
    principal = await get_principal(None)
    logger.info("kb_uk_update called")
    fields = {}
    for k, v in {"topic": topic, "content": content, "summary": summary, "era": era,
                  "source": source, "source_url": source_url, "status": status,
                  "reliability": reliability, "genre_tags": genre_tags, "year_range": year_range,
                  "tags": tags, "structured_data": structured_data}.items():
        if v is not None:
            fields[k] = v
    return await kb_service.uk_entry_update(entry_id=entry_id, **fields)


@mcp.tool(name="kb.uk.delete")
async def kb_uk_delete(entry_id: str) -> bool:
    """删除 universal_knowledge 条目。"""
    principal = await get_principal(None)
    logger.info("kb_uk_delete called")
    return await kb_service.uk_entry_delete(entry_id=entry_id)


@mcp.tool(name="kb.uk.stats")
async def kb_uk_stats(genre: str | None = None) -> dict[str, Any]:
    """获取 universal_knowledge 统计信息。可按题材过滤。"""
    principal = await get_principal(None)
    logger.info("kb_uk_stats called")
    return await kb_service.uk_stats(genre=genre)


@mcp.tool(name="kb.pk.upsert")
async def kb_pk_upsert(
    project_id: str,
    category: str,
    key: str,
    value: dict,
    description: str | None = None,
    chapter_no: int | None = None,
    tags: list[str] | None = None,
) -> dict[str, Any]:
    """创建或更新项目知识。类别：world_rule/character/faction/plot/world_state/timeline。"""
    principal = await get_principal("write")
    logger.info("kb_pk_upsert called")
    validate_required(locals(), "key", "value")
    return await kb_service.pk_upsert(
        project_id=project_id, category=category, key=key, value=value,
        description=description, chapter_no=chapter_no, tags=tags,
    )


@mcp.tool(name="kb.pk.get")
async def kb_pk_get(project_id: str, category: str, key: str) -> dict[str, Any] | None:
    """获取单条项目知识。"""
    principal = await get_principal("read")
    logger.info("kb_pk_get called")
    validate_required(locals(), "project_id", "category", "key")
    return await kb_service.pk_get(project_id=project_id, category=category, key=key)


@mcp.tool(name="kb.pk.list")
async def kb_pk_list(project_id: str, category: str | None = None) -> list[dict[str, Any]]:
    """列出项目知识条目。可按类别过滤。"""
    principal = await get_principal("read")
    logger.info("kb_pk_list called")
    validate_required(locals(), "project_id")
    return await kb_service.pk_list(project_id=project_id, category=category)


@mcp.tool(name="kb.pk.delete")
async def kb_pk_delete(project_id: str, category: str, key: str) -> bool:
    """删除项目知识条目。"""
    principal = await get_principal("write")
    logger.info("kb_pk_delete called")
    validate_required(locals(), "project_id", "category", "key")
    return await kb_service.pk_delete(project_id=project_id, category=category, key=key)


@mcp.tool(name="kb.world.get")
async def kb_world_get(project_id: str, chapter_no: int | None = None) -> dict[str, Any] | None:
    """获取世界状态快照。不传 chapter_no 返回最新版本。"""
    principal = await get_principal("read")
    logger.info("kb_world_get called")
    validate_required(locals(), "project_id")
    return await kb_service.world_get_state(project_id=project_id, chapter_no=chapter_no)


@mcp.tool(name="kb.world.update")
async def kb_world_update(
    project_id: str,
    chapter_no: int,
    world_state: dict,
    story_time: str | None = None,
    story_year: int | None = None,
    story_era: str | None = None,
    story_progress: float | None = None,
    character_count: int | None = None,
    active_threads: list[str] | None = None,
) -> dict[str, Any]:
    """更新指定章节的世界状态快照。"""
    principal = await get_principal("write")
    logger.info("kb_world_update called")
    validate_required(locals(), "project_id", "chapter_no", "world_state")
    return await kb_service.world_update_state(
        project_id=project_id, chapter_no=chapter_no, world_state=world_state,
        story_time=story_time, story_year=story_year, story_era=story_era,
        story_progress=story_progress, character_count=character_count,
        active_threads=active_threads,
    )


@mcp.tool(name="kb.world.list")
async def kb_world_list(project_id: str, limit: int = 10) -> list[dict[str, Any]]:
    """列出最近的世界状态快照。"""
    principal = await get_principal("read")
    logger.info("kb_world_list called")
    validate_required(locals(), "project_id")
    return await kb_service.world_list_snapshots(project_id=project_id, limit=limit)


@mcp.tool(name="kb.search.create_job")
async def kb_search_create_job(
    query_text: str,
    project_id: str | None = None,
    category_slug: str | None = None,
    chapter_no: int | None = None,
    triggered_by: str = "manual",
) -> dict[str, Any]:
    """创建知识自动搜索任务。后续执行 web_search 后调用 kb.auto.store。"""
    principal = await get_principal("read")
    logger.info("kb_search_create_job called")
    validate_required(locals(), "query_text")
    return await kb_service.search_create_job(
        query_text=query_text, project_id=project_id,
        category_slug=category_slug, chapter_no=chapter_no, triggered_by=triggered_by,
    )


@mcp.tool(name="kb.search.complete_job")
async def kb_search_complete_job(
    job_id: str, results_count: int, entries_created: int
) -> None:
    """标记搜索任务为已完成。记录结果数和创建条目数。"""
    principal = await get_principal("write")
    logger.info("kb_search_complete_job called")
    validate_required(locals(), "job_id", "results_count", "entries_created")
    await kb_service.search_complete_job(
        job_id=job_id, results_count=results_count, entries_created=entries_created,
    )


@mcp.tool(name="kb.gap.create")
async def kb_gap_create(
    description: str,
    project_id: str | None = None,
    gap_type: str = "missing_knowledge",
    entity_name: str | None = None,
    entity_type: str | None = None,
    context: str | None = None,
) -> dict[str, Any]:
    """创建知识缺口记录。用于追踪缺失的知识条目。"""
    principal = await get_principal("write")
    logger.info("kb_gap_create called")
    validate_required(locals(), "description")
    return await kb_service.gap_create(
        description=description, project_id=project_id, gap_type=gap_type,
        entity_name=entity_name, entity_type=entity_type, context=context,
    )


@mcp.tool(name="kb.gap.list")
async def kb_gap_list(
    project_id: str | None = None, resolved: bool = False
) -> list[dict[str, Any]]:
    """列出知识缺口。可按项目和解决状态过滤。"""
    principal = await get_principal("read")
    logger.info("kb_gap_list called")
    return await kb_service.gap_list(project_id=project_id, resolved=resolved)


@mcp.tool(name="kb.gap.resolve")
async def kb_gap_resolve(gap_id: str, entry_id: str | None = None) -> bool:
    """标记知识缺口为已解决。可关联解决用的知识条目。"""
    principal = await get_principal("write")
    logger.info("kb_gap_resolve called")
    return await kb_service.gap_resolve(gap_id=gap_id, entry_id=entry_id)


@mcp.tool(name="kb.genre.list")
async def kb_genre_list() -> list[dict[str, Any]]:
    """列出所有支持的题材策略。"""
    principal = await get_principal("read")
    logger.info("kb_genre_list called")
    return await kb_service.genre_list()


@mcp.tool(name="kb.genre.get")
async def kb_genre_get(genre_id: str) -> dict[str, Any] | None:
    """获取题材策略详情。"""
    principal = await get_principal("read")
    logger.info("kb_genre_get called")
    validate_required(locals(), "genre_id")
    return await kb_service.genre_get_strategy(genre_id=genre_id)


@mcp.tool(name="kb.genre.keywords")
async def kb_genre_keywords(
    genre_id: str,
    year: int | None = None,
    city: str | None = None,
    event: str | None = None,
    dynasty: str | None = None,
) -> list[str]:
    """根据题材生成搜索关键词。可用于知识库自动搜索。"""
    principal = await get_principal("read")
    logger.info("kb_genre_keywords called")
    kwargs = {}
    for k, v in {"year": year, "city": city, "event": event, "dynasty": dynasty}.items():
        if v is not None:
            kwargs[k] = v
    return await kb_service.genre_get_search_keywords(genre_id=genre_id, **kwargs)


@mcp.tool(name="kb.genre.preheat")
async def kb_genre_preheat(
    project_id: str,
    genre: str,
) -> dict[str, Any]:
    """预加载题材相关的 UK 条目到 project_knowledge，加速上下文检索。"""
    principal = await get_principal(None)
    logger.info("kb_genre_preheat called")
    validate_required(locals(), "project_id", "genre")
    return await kb_service.genre_preheat(project_id=project_id, genre=genre)


@mcp.tool(name="kb.auto.search")
async def kb_auto_search(
    query: str,
    category_slug: str | None = None,
    genre_tags: list[str] | None = None,
    project_id: str | None = None,
    chapter_no: int | None = None,
) -> dict[str, Any]:
    """步骤1：创建自动搜索任务。返回 job_id，执行 web_search 后调用 kb.auto.store。"""
    principal = await get_principal("read")
    logger.info("kb_auto_search called")
    return await kb_service.auto_search_and_organize(
        query=query, category_slug=category_slug, genre_tags=genre_tags,
        project_id=project_id, chapter_no=chapter_no,
    )


@mcp.tool(name="kb.auto.store")
async def kb_auto_store(
    job_id: str,
    search_results: list[dict],
    category_slug: str | None = None,
    genre_tags: list[str] | None = None,
) -> dict[str, Any]:
    """步骤2：将 web_search 结果存入 universal_knowledge。传入 [{title, url, snippet}] 格式。"""
    principal = await get_principal("write")
    logger.info("kb_auto_store called")
    validate_required(locals(), "job_id", "search_results")
    return await kb_service.organize_and_store(
        job_id=job_id, search_results=search_results,
        category_slug=category_slug, genre_tags=genre_tags,
    )


@mcp.tool(name="kb.gap.detect")
async def kb_gap_detect(
    project_id: str,
    chapter_plan: str | None = None,
    chapter_no: int | None = None,
) -> dict[str, Any]:
    """从章节大纲检测知识缺口。提取实体并检查是否存在于知识库。"""
    principal = await get_principal("read")
    logger.info("kb_gap_detect called")
    validate_required(locals(), "project_id")
    return await kb_service.detect_gaps(
        project_id=project_id, chapter_plan=chapter_plan, chapter_no=chapter_no,
    )


@mcp.tool(name="kb.world.auto_update")
async def kb_world_auto_update(
    project_id: str,
    chapter_no: int,
    generated_content: str,
    story_time: str | None = None,
    story_year: int | None = None,
    story_era: str | None = None,
) -> dict[str, Any]:
    """章节生成后自动更新世界状态。分析内容并更新 world_snapshots 和 state_entities。"""
    principal = await get_principal("read")
    logger.info("kb_world_auto_update called")
    validate_required(locals(), "project_id", "chapter_no", "generated_content")
    import re
    import json as json_module
    # Extract character names from content (simple heuristic)
    char_names = re.findall(r'[\u4e00-\u9fff]{2,4}(?:哥|姐|弟|妹|兄|叔|伯|爷|娘|先生|女士|大人|将军|陛下)', generated_content)
    char_names = list(set(char_names))[:10]

    # Build world state update
    world_state = {
        "last_chapter_summary": generated_content[:500],
        "characters_mentioned": char_names,
    }

    # Update world snapshot
    snapshot = await kb_service.world_update_state(
        project_id=project_id,
        chapter_no=chapter_no,
        world_state=world_state,
        story_time=story_time,
        story_year=story_year,
        story_era=story_era,
        character_count=len(char_names),
    )

    # Update state_entities for mentioned characters
    entities_updated = 0
    for name in char_names:
        try:
            # Check if entity exists
            existing = await kb_service._db.fetchrow(
                "SELECT id FROM state_entities WHERE project_id = $1 AND name = $2",
                project_id, name,
            )
            if existing:
                # Update snapshot
                await kb_service._db.execute(
                    """INSERT INTO state_snapshots (project_id, entity_id, is_current, state, effective_chapter_no, source_type)
                       SELECT $1, id, true, $3::jsonb, $4, 'auto_update'
                       FROM state_entities WHERE project_id = $1 AND id = $2
                       ON CONFLICT DO NOTHING""",
                    project_id, existing["id"],
                    json_module.dumps({"last_seen": f"chapter_{chapter_no}", "mentions": generated_content.count(name)}),
                    chapter_no,
                )
                entities_updated += 1
        except Exception:
            logger.debug("Failed to update state snapshot for character: %s", name)

    return {
        "snapshot": snapshot,
        "characters_found": char_names,
        "entities_updated": entities_updated,
    }


# ============================================================
# Knowledge Base System (KB) - Review Tools
# ============================================================

@mcp.tool(name="knowledge.category.list")
async def knowledge_category_list(
    include_inactive: bool = False,
) -> list[dict[str, Any]]:
    """列出所有知识分类"""
    principal = await get_principal("read")
    logger.info("knowledge_category_list called")
    return await knowledge_service.list_categories(include_inactive=include_inactive)


@mcp.tool(name="knowledge.category.get")
async def knowledge_category_get(
    category_id: str | None = None,
    slug: str | None = None,
) -> dict[str, Any]:
    """获取单个知识分类"""
    principal = await get_principal("read")
    logger.info("knowledge_category_get called")
    return await knowledge_service.get_category(category_id=category_id, slug=slug)


@mcp.tool(name="knowledge.category.stats")
async def knowledge_category_stats() -> list[dict[str, Any]]:
    """获取分类统计（每个分类的知识条目数）"""
    principal = await get_principal("read")
    logger.info("knowledge_category_stats called")
    return await knowledge_service.get_category_stats()


@mcp.tool(name="knowledge.category.upsert")
async def knowledge_category_upsert(
    slug: str,
    name: str,
    name_en: str | None = None,
    description: str | None = None,
    icon: str | None = None,
    color: str | None = None,
    sort_order: int | None = None,
    parent_id: str | None = None,
    is_system: bool = False,
) -> dict[str, Any]:
    """创建或更新知识分类（需要管理员权限）"""
    principal = await get_principal("write")
    logger.info("knowledge_category_upsert called")
    validate_required(locals(), "slug", "name")
    if "admin" not in principal.scopes:
        raise PermissionError("分类管理需要管理员权限（admin scope）")
    return await knowledge_service.upsert_category(
        slug=slug,
        name=name,
        name_en=name_en,
        description=description,
        icon=icon,
        color=color,
        sort_order=sort_order,
        parent_id=parent_id,
        is_system=is_system,
    )


@mcp.tool(name="knowledge.category.delete")
async def knowledge_category_delete(
    category_id: str | None = None,
    slug: str | None = None,
) -> bool:
    """删除知识分类（需要管理员权限）"""
    principal = await get_principal("write")
    logger.info("knowledge_category_delete called")
    if "admin" not in principal.scopes:
        raise PermissionError("分类管理需要管理员权限（admin scope）")
    return await knowledge_service.delete_category(category_id=category_id, slug=slug)


@mcp.tool(name="knowledge.item.list")
async def knowledge_item_list(
    category_slug: str | None = None,
    source: str | None = None,
    level: str | None = None,
    status: str | None = None,
    limit: int = 100,
    offset: int = 0,
) -> list[dict[str, Any]]:
    """列出知识条目"""
    principal = await get_principal("read")
    logger.info("knowledge_item_list called")
    return await knowledge_service.list_items(
        category_slug=category_slug,
        source=source,
        level=level,
        status=status,
        limit=limit,
        offset=offset,
    )


@mcp.tool(name="knowledge.item.get")
async def knowledge_item_get(
    item_id: str | None = None,
    code: str | None = None,
    increment_view: bool = True,
) -> dict[str, Any]:
    """获取单个知识条目详情"""
    principal = await get_principal("read")
    logger.info("knowledge_item_get called")
    item = await knowledge_service.get_item(item_id=item_id, code=code)
    if item and increment_view:
        await knowledge_service.increment_view_count(item["id"])
    return item


@mcp.tool(name="knowledge.item.search")
async def knowledge_item_search(
    query: str,
    category_slug: str | None = None,
    applicable_genre: str | None = None,
    applicable_skill: str | None = None,
    limit: int = 20,
) -> list[dict[str, Any]]:
    """搜索知识条目"""
    principal = await get_principal("read")
    logger.info("knowledge_item_search called")
    return await knowledge_service.search_items(
        query=query,
        category_slug=category_slug,
        applicable_genre=applicable_genre,
        applicable_skill=applicable_skill,
        limit=limit,
    )


@mcp.tool(name="knowledge.item.upsert")
async def knowledge_item_upsert(
    code: str,
    title: str,
    content: str,
    summary: str | None = None,
    detail: str | None = None,
    examples: str | None = None,
    counter_examples: str | None = None,
    metadata: dict[str, Any] | None = None,
    category_slug: str | None = None,
    source: str = "manual",
    source_file: str | None = None,
    applicable_genres: list[str] | None = None,
    applicable_skills: list[str] | None = None,
    level: str = "knowledge",
    status: str = "active",
) -> dict[str, Any]:
    """创建或更新知识条目"""
    principal = await get_principal("write")
    logger.info("knowledge_item_upsert called")
    validate_required(locals(), "code", "title", "content")
    return await knowledge_service.upsert_item(
        code=code,
        title=title,
        content=content,
        summary=summary,
        detail=detail,
        examples=examples,
        counter_examples=counter_examples,
        metadata=metadata,
        category_slug=category_slug,
        source=source,
        source_file=source_file,
        applicable_genres=applicable_genres,
        applicable_skills=applicable_skills,
        level=level,
        status=status,
    )


@mcp.tool(name="knowledge.item.delete")
async def knowledge_item_delete(
    item_id: str | None = None,
    code: str | None = None,
) -> bool:
    """删除知识条目"""
    principal = await get_principal("write")
    logger.info("knowledge_item_delete called")
    return await knowledge_service.delete_item(item_id=item_id, code=code)


@mcp.tool(name="knowledge.stats")
async def knowledge_stats() -> dict[str, Any]:
    """获取知识库统计"""
    principal = await get_principal("read")
    logger.info("knowledge_stats called")
    return await knowledge_service.get_stats()


@mcp.tool(name="knowledge.bulk_import")
async def knowledge_bulk_import(
    items: list[dict[str, Any]],
    source: str = "bulk_import",
) -> dict[str, Any]:
    """批量导入知识条目（需要管理员权限）"""
    principal = await get_principal("write")
    logger.info("knowledge_bulk_import called")
    validate_required(locals(), "items")
    if "admin" not in principal.scopes:
        raise PermissionError("批量导入需要管理员权限（admin scope）")
    return await knowledge_service.bulk_import(items=items, source=source)


@mcp.tool(name="knowledge.user.list")
async def knowledge_user_list(
    category_slug: str | None = None,
    status: str | None = None,
    review_status: str | None = None,
    limit: int = 100,
    offset: int = 0,
) -> list[dict[str, Any]]:
    """列出当前用户的私有知识条目"""
    principal = await get_principal("read")
    logger.info("knowledge_user_list called")
    user_id = await _get_user_id(principal.username)
    return await knowledge_service.get_user_items(
        user_id=user_id,
        category_slug=category_slug,
        status=status,
        review_status=review_status,
        limit=limit,
        offset=offset,
    )


@mcp.tool(name="knowledge.user.get")
async def knowledge_user_get(
    item_id: str,
) -> dict[str, Any]:
    """获取当前用户的单个私有知识条目"""
    principal = await get_principal("read")
    logger.info("knowledge_user_get called")
    validate_required(locals(), "item_id")
    user_id = await _get_user_id(principal.username)
    return await knowledge_service.get_user_item(user_id=user_id, item_id=item_id)


@mcp.tool(name="knowledge.user.upsert")
async def knowledge_user_upsert(
    title: str,
    content: str,
    item_id: str | None = None,
    code: str | None = None,
    summary: str | None = None,
    detail: str | None = None,
    examples: str | None = None,
    counter_examples: str | None = None,
    metadata: dict[str, Any] | None = None,
    category_slug: str | None = None,
    base_knowledge_id: str | None = None,
    applicable_genres: list[str] | None = None,
    applicable_skills: list[str] | None = None,
    level: str = "knowledge",
    status: str = "active",
) -> dict[str, Any]:
    """创建或更新当前用户的私有知识条目"""
    principal = await get_principal("write")
    logger.info("knowledge_user_upsert called")
    validate_required(locals(), "title", "content")
    user_id = await _get_user_id(principal.username)
    return await knowledge_service.upsert_user_item(
        user_id=user_id,
        title=title,
        content=content,
        item_id=item_id,
        code=code,
        summary=summary,
        detail=detail,
        examples=examples,
        counter_examples=counter_examples,
        metadata=metadata,
        category_slug=category_slug,
        base_knowledge_id=base_knowledge_id,
        applicable_genres=applicable_genres,
        applicable_skills=applicable_skills,
        level=level,
        status=status,
    )


@mcp.tool(name="knowledge.user.delete")
async def knowledge_user_delete(
    item_id: str,
) -> bool:
    """删除当前用户的私有知识条目"""
    principal = await get_principal("write")
    logger.info("knowledge_user_delete called")
    validate_required(locals(), "item_id")
    user_id = await _get_user_id(principal.username)
    return await knowledge_service.delete_user_item(user_id=user_id, item_id=item_id)


@mcp.tool(name="knowledge.user.create_from_base")
async def knowledge_user_create_from_base(
    base_knowledge_id: str,
) -> dict[str, Any]:
    """从公共知识条目创建用户私有副本"""
    principal = await get_principal("write")
    logger.info("knowledge_user_create_from_base called")
    validate_required(locals(), "base_knowledge_id")
    user_id = await _get_user_id(principal.username)
    return await knowledge_service.create_from_base(user_id=user_id, base_knowledge_id=base_knowledge_id)


@mcp.tool(name="knowledge.user.submit_review")
async def knowledge_user_submit_review(
    item_id: str,
    reason: str,
) -> dict[str, Any]:
    """提交用户知识条目进行审核"""
    principal = await get_principal("write")
    logger.info("knowledge_user_submit_review called")
    validate_required(locals(), "item_id", "reason")
    user_id = await _get_user_id(principal.username)
    return await knowledge_service.submit_for_review(user_id=user_id, item_id=item_id, reason=reason)


@mcp.tool(name="knowledge.user.stats")
async def knowledge_user_stats() -> dict[str, Any]:
    """获取当前用户的知识统计"""
    principal = await get_principal("read")
    logger.info("knowledge_user_stats called")
    user_id = await _get_user_id(principal.username)
    return await knowledge_service.get_user_stats(user_id=user_id)


@mcp.tool(name="knowledge.review.list")
async def knowledge_review_list(
    review_status: str | None = None,
    submitter_id: str | None = None,
    limit: int = 50,
    offset: int = 0,
) -> list[dict[str, Any]]:
    """列出审核列表（管理员权限）"""
    principal = await get_principal("read")
    logger.info("knowledge_review_list called")
    if "admin" not in principal.scopes:
        raise PermissionError("审核管理需要管理员权限（admin scope）")
    return await knowledge_service.list_review_items(
        review_status=review_status,
        submitter_id=submitter_id,
        limit=limit,
        offset=offset,
    )


@mcp.tool(name="knowledge.review.get")
async def knowledge_review_get(
    review_id: str,
) -> dict[str, Any]:
    """获取审核详情（管理员权限）"""
    principal = await get_principal("read")
    logger.info("knowledge_review_get called")
    if "admin" not in principal.scopes:
        raise PermissionError("审核管理需要管理员权限（admin scope）")
    return await knowledge_service.get_review_detail(review_id=review_id)


@mcp.tool(name="knowledge.review.approve")
async def knowledge_review_approve(
    review_id: str,
    comment: str | None = None,
) -> dict[str, Any]:
    """审核通过（管理员权限）"""
    principal = await get_principal("write")
    logger.info("knowledge_review_approve called")
    validate_required(locals(), "review_id")
    if "admin" not in principal.scopes:
        raise PermissionError("审核通过需要管理员权限（admin scope）")
    reviewer_id = await _get_user_id(principal.username)
    return await knowledge_service.approve_review(reviewer_id=reviewer_id, review_id=review_id, comment=comment)


@mcp.tool(name="knowledge.review.reject")
async def knowledge_review_reject(
    review_id: str,
    comment: str,
) -> dict[str, Any]:
    """审核拒绝（管理员权限）"""
    principal = await get_principal("write")
    logger.info("knowledge_review_reject called")
    validate_required(locals(), "review_id", "comment")
    if "admin" not in principal.scopes:
        raise PermissionError("审核拒绝需要管理员权限（admin scope）")
    reviewer_id = await _get_user_id(principal.username)
    return await knowledge_service.reject_review(reviewer_id=reviewer_id, review_id=review_id, comment=comment)


@mcp.tool(name="knowledge.review.stats")
async def knowledge_review_stats() -> dict[str, Any]:
    """获取审核统计（管理员权限）"""
    principal = await get_principal("read")
    logger.info("knowledge_review_stats called")
    if "admin" not in principal.scopes:
        raise PermissionError("审核统计需要管理员权限（admin scope）")
    return await knowledge_service.get_review_stats()
