import logging
from typing import Any

from ..mcp_core import mcp
from ..deps import db, auth, kb_service
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
    query: str | None = None,
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


@mcp.tool(name="kb.uk.get")
async def kb_uk_get(entry_id: str) -> dict[str, Any]:
    """通过 ID 获取单条 universal_knowledge 条目详情。

    与 kb.uk.search 的区别：search 返回精简列表，本工具返回完整字段（含 content、
    structured_data、来源与可信度），供详情弹窗展示。
    """
    principal = await get_principal(None)
    logger.info("kb_uk_get called")
    validate_required(locals(), "entry_id")
    result = await kb_service.uk_entry_get(entry_id=entry_id)
    if not result:
        raise ValueError(f"UK 条目未找到（entry_id={entry_id}）")
    return result


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
    workspace: str,
    project: str,
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
    project_id = await auth.resolve_project_id(workspace, project, principal, access="write")
    logger.info("kb_pk_upsert called")
    validate_required(locals(), "key", "value")
    return await kb_service.pk_upsert(
        project_id=project_id, category=category, key=key, value=value,
        description=description, chapter_no=chapter_no, tags=tags,
    )


@mcp.tool(name="kb.pk.get")
async def kb_pk_get(workspace: str,
    project: str,
    project_id: str, category: str, key: str) -> dict[str, Any] | None:
    """获取单条项目知识。"""
    principal = await get_principal("read")
    project_id = await auth.resolve_project_id(workspace, project, principal, access="read")
    logger.info("kb_pk_get called")
    validate_required(locals(), "workspace", "project", "project_id", "category", "key")
    return await kb_service.pk_get(project_id=project_id, category=category, key=key)


@mcp.tool(name="kb.pk.list")
async def kb_pk_list(workspace: str,
    project: str,
    project_id: str, category: str | None = None) -> list[dict[str, Any]]:
    """列出项目知识条目。可按类别过滤。"""
    principal = await get_principal("read")
    project_id = await auth.resolve_project_id(workspace, project, principal, access="read")
    logger.info("kb_pk_list called")
    validate_required(locals(), "workspace", "project", "project_id")
    return await kb_service.pk_list(project_id=project_id, category=category)


@mcp.tool(name="kb.pk.delete")
async def kb_pk_delete(workspace: str,
    project: str,
    project_id: str, category: str, key: str) -> bool:
    """删除项目知识条目。"""
    principal = await get_principal("write")
    project_id = await auth.resolve_project_id(workspace, project, principal, access="write")
    logger.info("kb_pk_delete called")
    validate_required(locals(), "workspace", "project", "project_id", "category", "key")
    return await kb_service.pk_delete(project_id=project_id, category=category, key=key)


@mcp.tool(name="kb.world.get")
async def kb_world_get(workspace: str,
    project: str, chapter_no: int | None = None) -> dict[str, Any] | None:
    """获取世界状态快照。不传 chapter_no 返回最新版本。"""
    principal = await get_principal("read")
    project_id = await auth.resolve_project_id(workspace, project, principal, access="read")
    logger.info("kb_world_get called")
    return await kb_service.world_get_state(project_id=project_id, chapter_no=chapter_no)


@mcp.tool(name="kb.world.update")
async def kb_world_update(
    workspace: str,
    project: str,
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
    project_id = await auth.resolve_project_id(workspace, project, principal, access="write")
    logger.info("kb_world_update called")
    validate_required(locals(), "workspace", "project", "project_id", "chapter_no", "world_state")
    return await kb_service.world_update_state(
        project_id=project_id, chapter_no=chapter_no, world_state=world_state,
        story_time=story_time, story_year=story_year, story_era=story_era,
        story_progress=story_progress, character_count=character_count,
        active_threads=active_threads,
    )


@mcp.tool(name="kb.world.list")
async def kb_world_list(workspace: str,
    project: str,
    project_id: str, limit: int = 10) -> list[dict[str, Any]]:
    """列出最近的世界状态快照。"""
    principal = await get_principal("read")
    project_id = await auth.resolve_project_id(workspace, project, principal, access="read")
    logger.info("kb_world_list called")
    validate_required(locals(), "workspace", "project", "project_id")
    return await kb_service.world_list_snapshots(project_id=project_id, limit=limit)


@mcp.tool(name="kb.search.create_job")
async def kb_search_create_job(
    query_text: str,
    workspace: str,
    project: str,
    project_id: str | None = None,
    category_slug: str | None = None,
    chapter_no: int | None = None,
    triggered_by: str = "manual",
) -> dict[str, Any]:
    """创建知识自动搜索任务。后续执行 web_search 后调用 kb.auto.store。"""
    principal = await get_principal("read")
    project_id = await auth.resolve_project_id(workspace, project, principal, access="read")
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


@mcp.tool(name="kb.auto.search")
async def kb_auto_search(
    query: str,
    workspace: str,
    project: str,
    category_slug: str | None = None,
    chapter_no: int | None = None,
    triggered_by: str = "manual",
) -> dict[str, Any]:
    """创建知识自动搜索任务（kb.search.create_job 的别名入口）。

    只登记任务，不立即写入知识库；搜索完成后用 kb.search.complete_job 标记结果。

    Args:
        query: 搜索关键词
        workspace / project: 项目定位
        category_slug: 限定知识分类
        chapter_no: 关联章节号
        triggered_by: 触发来源，默认 manual

    Returns:
        {id, query_text, status, created_at}
    """
    principal = await get_principal("write")
    project_id = await auth.resolve_project_id(workspace, project, principal, access="write")
    logger.info("kb_auto_search called: query=%s", query)
    validate_required(locals(), "query")
    return await kb_service.search_create_job(
        query_text=query, project_id=project_id,
        category_slug=category_slug, chapter_no=chapter_no, triggered_by=triggered_by,
    )


@mcp.tool(name="kb.gap.create")
async def kb_gap_create(
    description: str,
    workspace: str,
    project: str,
    project_id: str | None = None,
    gap_type: str = "missing_knowledge",
    entity_name: str | None = None,
    entity_type: str | None = None,
    context: str | None = None,
) -> dict[str, Any]:
    """创建知识缺口记录。用于追踪缺失的知识条目。"""
    principal = await get_principal("write")
    project_id = await auth.resolve_project_id(workspace, project, principal, access="write")
    logger.info("kb_gap_create called")
    validate_required(locals(), "description")
    return await kb_service.gap_create(
        description=description, project_id=project_id, gap_type=gap_type,
        entity_name=entity_name, entity_type=entity_type, context=context,
    )


@mcp.tool(name="kb.gap.list")
async def kb_gap_list(
    workspace: str,
    project: str,
    project_id: str | None = None, resolved: bool = False
) -> list[dict[str, Any]]:
    """列出知识缺口。可按项目和解决状态过滤。"""
    principal = await get_principal("read")
    project_id = await auth.resolve_project_id(workspace, project, principal, access="read")
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
    workspace: str,
    project: str,
    project_id: str,
    genre: str,
) -> dict[str, Any]:
    """预加载题材相关的 UK 条目到 project_knowledge，加速上下文检索。"""
    principal = await get_principal(None)
    logger.info("kb_genre_preheat called")
    validate_required(locals(), "workspace", "project", "project_id", "genre")
    return await kb_service.genre_preheat(project_id=project_id, genre=genre)


@mcp.tool(name="kb.genre.update")
async def kb_genre_update(
    genre: str,
    included_categories: list[str] | None = None,
    excluded_categories: list[str] | None = None,
    description: str | None = None,
) -> dict[str, Any]:
    """更新题材知识配置，包括启用的分类、排除的分类等。"""
    principal = await get_principal("write")
    logger.info("kb_genre_update called for genre: %s", genre)
    validate_required(locals(), "genre")
    return await kb_service.genre_update_config(
        genre=genre,
        included_categories=included_categories,
        excluded_categories=excluded_categories,
        description=description,
    )


@mcp.tool(name="kb.genre.create")
async def kb_genre_create(
    slug: str,
    name: str,
    description: str | None = None,
    typical_elements: list[str] | None = None,
    target_audience: str | None = None,
    platform_tags: list[str] | None = None,
    aliases: list[str] | None = None,
    included_categories: list[str] | None = None,
    excluded_categories: list[str] | None = None,
) -> dict[str, Any]:
    """创建新题材。slug 为唯一标识，name 为显示名称。"""
    principal = await get_principal("write")
    logger.info("kb_genre_create called: %s", slug)
    validate_required(locals(), "slug", "name")
    return await kb_service.genre_create(
        slug=slug, name=name, description=description,
        typical_elements=typical_elements, target_audience=target_audience,
        platform_tags=platform_tags, aliases=aliases,
        included_categories=included_categories, excluded_categories=excluded_categories,
    )


@mcp.tool(name="kb.genre.delete")
async def kb_genre_delete(
    slug: str,
) -> dict[str, Any]:
    """删除题材及其知识配置。"""
    principal = await get_principal("write")
    logger.info("kb_genre_delete called: %s", slug)
    validate_required(locals(), "slug")
    return await kb_service.genre_delete(slug=slug)


@mcp.tool(name="kb.auto.search_and_store")
async def kb_auto_search_and_store(
    query: str,
    search_results: list[dict[str, Any]],
    workspace: str,
    project: str,
    project_id: str | None = None,
    category_slug: str | None = None,
    genre_tags: list[str] | None = None,
    chapter_no: int | None = None,
) -> dict[str, Any]:
    """一步完成：创建搜索任务 → 存储 web_search 结果 → 完成任务。

    Args:
        query: 搜索关键词
        search_results: web_search 结果，[{title, url, snippet}]
        category_slug: 知识分类 slug
        genre_tags: 题材标签
        project_id: 关联项目（可选）
        chapter_no: 关联章节（可选）

    Returns:
        {ok, job_id, entries_created, results_count}
    """
    principal = await get_principal("write")
    project_id = await auth.resolve_project_id(workspace, project, principal, access="write")
    logger.info("kb_auto_search_and_store called: query=%s", query)
    validate_required(locals(), "query", "search_results")
    return await kb_service.search_and_store(
        query=query, search_results=search_results,
        category_slug=category_slug, genre_tags=genre_tags,
        project_id=project_id, chapter_no=chapter_no,
    )


@mcp.tool(name="kb.gap.detect")
async def kb_gap_detect(
    workspace: str,
    project: str,
    project_id: str,
    chapter_plan: str | None = None,
    chapter_no: int | None = None,
) -> dict[str, Any]:
    """从章节大纲检测知识缺口。提取实体并检查是否存在于知识库。"""
    principal = await get_principal("read")
    project_id = await auth.resolve_project_id(workspace, project, principal, access="read")
    logger.info("kb_gap_detect called")
    validate_required(locals(), "workspace", "project", "project_id")
    return await kb_service.detect_gaps(
        project_id=project_id, chapter_plan=chapter_plan, chapter_no=chapter_no,
    )


@mcp.tool(name="kb.gap.analyze")
async def kb_gap_analyze(
    genre: str,
) -> dict[str, Any]:
    """分析题材知识缺口。返回每个分类已有UK条目数、是否需补充、优先级。"""
    principal = await get_principal("read")
    logger.info("kb_gap_analyze called: %s", genre)
    validate_required(locals(), "genre")
    return await kb_service.gap_analyze(genre=genre)


@mcp.tool(name="kb.world.auto_update")
async def kb_world_auto_update(
    workspace: str,
    project: str,
    chapter_no: int,
    generated_content: str,
    story_time: str | None = None,
    story_year: int | None = None,
    story_era: str | None = None,
) -> dict[str, Any]:
    """章节生成后自动更新世界状态。分析内容并更新 world_snapshots 和 state_entities。"""
    principal = await get_principal("write")
    logger.info("kb_world_auto_update called")
    validate_required(locals(), "workspace", "project", "chapter_no", "generated_content")
    project_id = await auth.resolve_project_id(workspace, project, principal, access="write")
    import re
    import json as json_module
    from ..deps import memory_service

    # Extract character names from content (simple heuristic: 2-4 Chinese chars + honorific)
    char_names = re.findall(r'[\u4e00-\u9fff]{2,4}(?:哥|姐|弟|妹|兄|叔|伯|爷|娘|先生|女士|大人|将军|陛下)', generated_content)
    # Also extract bare 2-3 char names that appear frequently
    all_names = re.findall(r'[\u4e00-\u9fff]{2,3}', generated_content)
    from collections import Counter
    freq_names = [n for n, c in Counter(all_names).items() if c >= 3 and n not in '什么 怎么 这么 因为 所以 然后 但是 虽然 如果 而且 或者 不过 只是 还是 就是 不是 是的 可以 没有 已经 知道 看到 想到 觉得 以为 开始 起来 出来 下来 回来 进来 过来 起来 上去 下去 进去 出去 回去 找到 得到 看到 听到 想到 感到'.split()]
    char_names = list(set(char_names + freq_names))[:10]

    # Extract location names (simple heuristic: 2-4 chars ending with common location suffixes)
    loc_names = re.findall(r'[\u4e00-\u9fff]{2,4}(?:山|谷|城|镇|村|宫|殿|塔|寺|观|洞|府|门|派|宗|教|国|洲|海|湖|河|原|林|岭|峰|崖|关|堡)', generated_content)
    loc_names = list(set(loc_names))[:5]

    # Extract key events (sentences containing event keywords)
    event_sentences = re.findall(r'[^。！？]*?(?:终于|突然|发现|遇到|决定|开始|结束|击败|获得|失去|来到|离开|创建|毁灭|宣布|签订)[^。！？]*[。！？]', generated_content)
    key_events = [s.strip() for s in event_sentences[:3]]

    # Build structured world state
    world_state = {
        "summary": generated_content[:300],
        "active_locations": loc_names,
        "key_events": key_events,
        "characters_mentioned": char_names,
        "story_time": story_time or "",
    }
    # Remove empty fields
    world_state = {k: v for k, v in world_state.items() if v}

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

    # Update state_entities for mentioned characters: auto-create + update chapter fields
    entities_created = 0
    entities_updated = 0
    for name in char_names:
        try:
            existing = await kb_service._db.fetchrow(
                "SELECT id, first_seen_chapter_no, last_seen_chapter_no FROM state_entities WHERE project_id = $1 AND entity_type = 'character' AND name = $2",
                project_id, name,
            )
            if existing:
                # Update last_seen_chapter_no (and first_seen if null)
                await kb_service._db.execute(
                    """UPDATE state_entities SET
                         last_seen_chapter_no = $3,
                         first_seen_chapter_no = COALESCE(first_seen_chapter_no, $3),
                         updated_at = now()
                       WHERE id = $1""",
                    existing["id"], project_id, chapter_no,
                )
                # Insert snapshot
                await kb_service._db.execute(
                    """INSERT INTO state_snapshots (project_id, entity_id, is_current, state, effective_chapter_no, source_type)
                       VALUES ($1, $2, true, $3::jsonb, $4, 'auto_update')""",
                    project_id, existing["id"],
                    json_module.dumps({"last_seen": f"chapter_{chapter_no}", "mentions": generated_content.count(name)}),
                    chapter_no,
                )
                entities_updated += 1
            else:
                # Auto-create entity
                summary_text = generated_content[:100].replace('\n', ' ') if len(generated_content) > 100 else generated_content.replace('\n', ' ')
                row = await kb_service._db.fetchrow(
                    """INSERT INTO state_entities (project_id, entity_type, name, lifecycle_status, importance, summary, first_seen_chapter_no, last_seen_chapter_no, source_type)
                       VALUES ($1, 'character', $2, 'active', 'medium', $3, $4, $4, 'auto_update')
                       ON CONFLICT (project_id, entity_type, name) DO UPDATE SET last_seen_chapter_no = $4, updated_at = now()
                       RETURNING id""",
                    project_id, name, summary_text, chapter_no,
                )
                # Create initial snapshot
                if row:
                    await kb_service._db.execute(
                        """INSERT INTO state_snapshots (project_id, entity_id, is_current, state, effective_chapter_no, source_type)
                           VALUES ($1, $2, true, $3::jsonb, $4, 'auto_update')""",
                        project_id, row["id"],
                        json_module.dumps({"first_seen": f"chapter_{chapter_no}", "status": "auto_created"}),
                        chapter_no,
                    )
                    entities_created += 1
        except Exception as e:
            logger.debug("Failed to update entity for character '%s': %s", name, e)

    # Also update the user-facing description: try extracting an alias from the first mention
    try:
        for name in char_names:
            # Find contextual alias: look for "XX（人称YY）" or "XX(又称YY)" patterns
            alias_match = re.search(rf'{re.escape(name)}\s*[（(]\s*(?:又称|人称|又名|别名)[：:]\s*([^）)]+)[）)]', generated_content)
            if alias_match:
                alias = alias_match.group(1).strip()
                await kb_service._db.execute(
                    "UPDATE state_entities SET aliases = array_append(aliases, $1) WHERE project_id = $2 AND name = $3 AND NOT ($1 = ANY(aliases))",
                    alias, project_id, name,
                )
    except Exception:
        pass

    return {
        "snapshot": snapshot,
        "characters_found": char_names,
        "entities_created": entities_created,
        "entities_updated": entities_updated,
    }

