import logging
from typing import Any

from ..mcp_core import mcp
from ..deps import db, auth, prompt_template_service, reference_material_service, reader_expectation_service, chapter_annotation_service, proper_noun_service, fulltext_search_service, context_weight_service
from ..tool_auth import get_principal, validate_required

logger = logging.getLogger("novel_os_mcp.tools.prompt")


@mcp.tool(name="prompt.template.upsert")
async def prompt_template_upsert(
    workspace: str,
    project: str,
    template_key: str,
    name: str,
    template_content: str,
    description: str | None = None,
    template_type: str = "system",
    variables: list[dict[str, Any]] | None = None,
    genre: str | None = None,
    scene: str | None = None,
) -> dict[str, Any]:
    """创建或更新 Prompt 模板"""
    principal = await get_principal("write")
    logger.info("prompt_template_upsert called")
    validate_required(locals(), "workspace", "project", "template_key", "name", "template_content")
    project_id = await auth.resolve_project_id(workspace, project, principal, access="write")
    return await prompt_template_service.upsert_template(
        project_id=project_id,
        template_key=template_key,
        name=name,
        template_content=template_content,
        description=description,
        template_type=template_type,
        variables=variables,
        genre=genre,
        scene=scene,
        created_by=principal.username,
    )


@mcp.tool(name="prompt.template.get")
async def prompt_template_get(
    workspace: str,
    project: str,
    template_key: str,
) -> dict[str, Any] | None:
    """获取 Prompt 模板"""
    principal = await get_principal("read")
    logger.info("prompt_template_get called")
    validate_required(locals(), "workspace", "project", "template_key")
    project_id = await auth.resolve_project_id(workspace, project, principal)
    return await prompt_template_service.get_template(project_id, template_key)


@mcp.tool(name="prompt.template.list")
async def prompt_template_list(
    workspace: str,
    project: str | None = None,
    genre: str | None = None,
    scene: str | None = None,
    template_type: str | None = None,
    limit: int = 100,
) -> list[dict[str, Any]]:
    """列出 Prompt 模板。project 为 null 时返回 workspace 下所有模板。"""
    principal = await get_principal("read")
    logger.info("prompt_template_list called")
    if project:
        project_id = await auth.resolve_project_id(workspace, project, principal)
        return await prompt_template_service.list_templates(
            project_id=project_id,
            genre=genre,
            scene=scene,
            template_type=template_type,
            limit=limit,
        )
    else:
        # Cross-project query
        return await prompt_template_service.list_templates_by_workspace(
            workspace=workspace,
            principal=principal,
            genre=genre,
            scene=scene,
            template_type=template_type,
            limit=limit,
        )


@mcp.tool(name="prompt.template.render")
async def prompt_template_render(
    workspace: str,
    project: str,
    template_key: str,
    variables: dict[str, Any],
) -> dict[str, Any]:
    """渲染 Prompt 模板"""
    principal = await get_principal("write")
    logger.info("prompt_template_render called")
    validate_required(locals(), "workspace", "project", "template_key", "variables")
    project_id = await auth.resolve_project_id(workspace, project, principal, access="write")
    return await prompt_template_service.render_template(project_id, template_key, variables)


@mcp.tool(name="prompt.template.delete")
async def prompt_template_delete(
    workspace: str,
    project: str,
    template_key: str,
) -> dict[str, Any]:
    """删除 Prompt 模板"""
    principal = await get_principal("write")
    logger.info("prompt_template_delete called")
    validate_required(locals(), "workspace", "project", "template_key")
    project_id = await auth.resolve_project_id(workspace, project, principal, access="write")
    return await prompt_template_service.delete_template(project_id=project_id, template_key=template_key)


@mcp.tool(name="context.weight.upsert")
async def context_weight_upsert(
    workspace: str,
    project: str,
    config_name: str,
    weights: dict[str, float],
    profile: str = "default",
    max_total_tokens: int = 8000,
    priority_order: list[str] | None = None,
) -> dict[str, Any]:
    """创建或更新上下文权重配置。控制不同信息源在 context pack 中的占比。"""
    principal = await get_principal("write")
    logger.info("context_weight_upsert called")
    validate_required(locals(), "workspace", "project", "config_name", "weights")
    project_id = await auth.resolve_project_id(workspace, project, principal, access="write")
    return await context_weight_service.upsert_config(
        project_id=project_id,
        config_name=config_name,
        weights=weights,
        profile=profile,
        max_total_tokens=max_total_tokens,
        priority_order=priority_order,
    )


@mcp.tool(name="context.weight.get")
async def context_weight_get(
    workspace: str,
    project: str,
    config_name: str,
    profile: str = "default",
) -> dict[str, Any] | None:
    """获取上下文权重配置详情。"""
    principal = await get_principal("read")
    logger.info("context_weight_get called")
    validate_required(locals(), "workspace", "project", "config_name")
    project_id = await auth.resolve_project_id(workspace, project, principal)
    return await context_weight_service.get_config(project_id, config_name, profile)


@mcp.tool(name="context.weight.list")
async def context_weight_list(
    workspace: str,
    project: str,
    profile: str | None = None,
) -> list[dict[str, Any]]:
    """列出项目的上下文权重配置列表。"""
    principal = await get_principal("read")
    logger.info("context_weight_list called")
    validate_required(locals(), "workspace", "project")
    project_id = await auth.resolve_project_id(workspace, project, principal)
    return await context_weight_service.list_configs(project_id, profile)


@mcp.tool(name="material.upsert")
async def material_upsert(
    workspace: str,
    project: str,
    material_key: str,
    title: str,
    material_type: str,
    content: str | None = None,
    category: str | None = None,
    tags: list[str] | None = None,
    source_url: str | None = None,
) -> dict[str, Any]:
    """创建或更新参考素材。素材类型包括参考文本、图片链接等。"""
    principal = await get_principal("write")
    logger.info("material_upsert called")
    validate_required(locals(), "workspace", "project", "material_key", "title", "material_type")
    project_id = await auth.resolve_project_id(workspace, project, principal, access="write")
    return await reference_material_service.upsert_material(
        project_id=project_id,
        material_key=material_key,
        title=title,
        material_type=material_type,
        content=content,
        category=category,
        tags=tags,
        source_url=source_url,
        created_by=principal.username,
    )


@mcp.tool(name="material.get")
async def material_get(
    workspace: str,
    project: str,
    material_key: str,
) -> dict[str, Any] | None:
    """获取单个参考素材详情。"""
    principal = await get_principal("read")
    logger.info("material_get called")
    validate_required(locals(), "workspace", "project", "material_key")
    project_id = await auth.resolve_project_id(workspace, project, principal)
    return await reference_material_service.get_material(project_id, material_key)


@mcp.tool(name="material.list")
async def material_list(
    workspace: str,
    project: str,
    material_type: str | None = None,
    category: str | None = None,
    tags: list[str] | None = None,
    favorite: bool | None = None,
    search: str | None = None,
    limit: int = 100,
) -> list[dict[str, Any]]:
    """列出参考素材。支持按类型、分类、标签、收藏状态过滤。"""
    principal = await get_principal("read")
    logger.info("material_list called")
    validate_required(locals(), "workspace", "project")
    project_id = await auth.resolve_project_id(workspace, project, principal)
    return await reference_material_service.list_materials(
        project_id=project_id,
        material_type=material_type,
        category=category,
        tags=tags,
        favorite=favorite,
        search=search,
        limit=limit,
    )


@mcp.tool(name="material.favorite")
async def material_favorite(
    workspace: str,
    project: str,
    material_key: str,
) -> dict[str, Any]:
    """切换素材的收藏/取消收藏状态。"""
    principal = await get_principal("write")
    logger.info("material_favorite called")
    validate_required(locals(), "workspace", "project", "material_key")
    project_id = await auth.resolve_project_id(workspace, project, principal, access="write")
    return await reference_material_service.toggle_favorite(project_id, material_key)


@mcp.tool(name="expectation.upsert")
async def expectation_upsert(
    workspace: str,
    project: str,
    expectation_key: str,
    title: str,
    expectation_type: str,
    description: str | None = None,
    chapter_no: int | None = None,
    importance: str = "medium",
    tags: list[str] | None = None,
) -> dict[str, Any]:
    """创建或更新读者期待（伏笔/悬念）。记录伏笔埋设章节和重要程度。"""
    principal = await get_principal("write")
    logger.info("expectation_upsert called")
    validate_required(locals(), "workspace", "project", "expectation_key", "title", "expectation_type")
    project_id = await auth.resolve_project_id(workspace, project, principal, access="write")
    return await reader_expectation_service.upsert_expectation(
        project_id=project_id,
        expectation_key=expectation_key,
        title=title,
        expectation_type=expectation_type,
        description=description,
        chapter_no=chapter_no,
        importance=importance,
        tags=tags,
        created_by=principal.username,
    )


@mcp.tool(name="expectation.list")
async def expectation_list(
    workspace: str,
    project: str,
    status: str | None = None,
    expectation_type: str | None = None,
    importance: str | None = None,
    limit: int = 100,
) -> list[dict[str, Any]]:
    """列出读者期待。支持按状态、类型、重要程度过滤。"""
    principal = await get_principal("read")
    logger.info("expectation_list called")
    validate_required(locals(), "workspace", "project")
    project_id = await auth.resolve_project_id(workspace, project, principal)
    return await reader_expectation_service.list_expectations(
        project_id=project_id,
        status=status,
        expectation_type=expectation_type,
        importance=importance,
        limit=limit,
    )


@mcp.tool(name="expectation.fulfill")
async def expectation_fulfill(
    workspace: str,
    project: str,
    expectation_key: str,
    payoff_chapter_no: int,
) -> dict[str, Any]:
    """标记读者期待已回收。记录回收章节号。"""
    principal = await get_principal("write")
    logger.info("expectation_fulfill called")
    validate_required(locals(), "workspace", "project", "expectation_key", "payoff_chapter_no")
    project_id = await auth.resolve_project_id(workspace, project, principal, access="write")
    return await reader_expectation_service.mark_fulfilled(project_id, expectation_key, payoff_chapter_no)


@mcp.tool(name="annotation.create")
async def annotation_create(
    workspace: str,
    project: str,
    chapter_id: str,
    chapter_no: int,
    annotation_type: str,
    content: str,
    anchor_start: int | None = None,
    anchor_end: int | None = None,
    parent_id: str | None = None,
) -> dict[str, Any]:
    """创建章节批注。支持文本锚点定位和父子批注关系。"""
    principal = await get_principal("write")
    logger.info("annotation_create called")
    validate_required(locals(), "workspace", "project", "chapter_id", "chapter_no", "annotation_type", "content")
    project_id = await auth.resolve_project_id(workspace, project, principal, access="write")
    return await chapter_annotation_service.create_annotation(
        project_id=project_id,
        chapter_id=chapter_id,
        chapter_no=chapter_no,
        annotation_type=annotation_type,
        content=content,
        anchor_start=anchor_start,
        anchor_end=anchor_end,
        parent_id=parent_id,
        created_by=principal.username,
    )


@mcp.tool(name="annotation.list")
async def annotation_list(
    workspace: str,
    project: str,
    chapter_id: str | None = None,
    annotation_type: str | None = None,
    resolve_status: str | None = None,
) -> list[dict[str, Any]]:
    """列出章节批注。支持按章节、类型、解决状态过滤。"""
    principal = await get_principal("read")
    logger.info("annotation_list called")
    validate_required(locals(), "workspace", "project")
    project_id = await auth.resolve_project_id(workspace, project, principal)
    return await chapter_annotation_service.list_annotations(
        project_id=project_id,
        chapter_id=chapter_id,
        annotation_type=annotation_type,
        resolve_status=resolve_status,
    )


@mcp.tool(name="annotation.resolve")
async def annotation_resolve(
    workspace: str,
    project: str,
    annotation_id: str,
) -> dict[str, Any]:
    """将批注标记为已解决。记录处理人。"""
    principal = await get_principal("write")
    logger.info("annotation_resolve called")
    validate_required(locals(), "workspace", "project", "annotation_id")
    project_id = await auth.resolve_project_id(workspace, project, principal, access="write")
    return await chapter_annotation_service.resolve_annotation(
        project_id=project_id,
        annotation_id=annotation_id,
        resolved_by=principal.username,
    )


@mcp.tool(name="noun.upsert")
async def noun_upsert(
    workspace: str,
    project: str,
    noun_key: str,
    noun_value: str,
    noun_type: str,
    aliases: list[str] | None = None,
    description: str | None = None,
    locked: bool = False,
    first_chapter_no: int | None = None,
) -> dict[str, Any]:
    """创建或更新专有名词。支持别名、锁定状态和首次出现章节。"""
    principal = await get_principal("write")
    logger.info("noun_upsert called")
    validate_required(locals(), "workspace", "project", "noun_key", "noun_value", "noun_type")
    project_id = await auth.resolve_project_id(workspace, project, principal, access="write")
    return await proper_noun_service.upsert_noun(
        project_id=project_id,
        noun_key=noun_key,
        noun_value=noun_value,
        noun_type=noun_type,
        aliases=aliases,
        description=description,
        locked=locked,
        first_chapter_no=first_chapter_no,
        created_by=principal.username,
    )


@mcp.tool(name="noun.list")
async def noun_list(
    workspace: str,
    project: str,
    noun_type: str | None = None,
    locked: bool | None = None,
    search: str | None = None,
) -> list[dict[str, Any]]:
    """列出项目专有名词。支持按类型、锁定状态和关键词过滤。"""
    principal = await get_principal("read")
    logger.info("noun_list called")
    validate_required(locals(), "workspace", "project")
    project_id = await auth.resolve_project_id(workspace, project, principal)
    return await proper_noun_service.list_nouns(
        project_id=project_id,
        noun_type=noun_type,
        locked=locked,
        search=search,
    )


@mcp.tool(name="noun.check")
async def noun_check(
    workspace: str,
    project: str,
    text: str,
) -> dict[str, Any]:
    """检查文本中专有名词的一致性。检测错别字和不一致用法。"""
    principal = await get_principal("read")
    logger.info("noun_check called")
    validate_required(locals(), "workspace", "project", "text")
    project_id = await auth.resolve_project_id(workspace, project, principal)
    return await proper_noun_service.check_consistency(project_id, text)


@mcp.tool(name="search.fulltext")
async def search_fulltext(
    workspace: str,
    project: str,
    query: str,
    source_types: list[str] | None = None,
    limit: int = 50,
) -> list[dict[str, Any]]:
    """全文检索项目内容。支持按来源类型（章节、知识条目等）过滤。"""
    principal = await get_principal("read")
    logger.info("search_fulltext called")
    validate_required(locals(), "workspace", "project", "query")
    project_id = await auth.resolve_project_id(workspace, project, principal)
    return await fulltext_search_service.search(
        project_id=project_id,
        query=query,
        source_types=source_types,
        limit=limit,
    )


@mcp.tool(name="search.index")
async def search_index(
    workspace: str,
    project: str,
    source_type: str,
    source_id: str,
    title: str,
    content: str,
    source_key: str | None = None,
) -> dict[str, Any]:
    """将内容索引到全文检索引擎。用于新增/更新可搜索内容。"""
    principal = await get_principal("write")
    logger.info("search_index called")
    validate_required(locals(), "workspace", "project", "source_type", "source_id", "title", "content")
    project_id = await auth.resolve_project_id(workspace, project, principal, access="write")
    return await fulltext_search_service.index_record(
        project_id=project_id,
        source_type=source_type,
        source_id=source_id,
        title=title,
        content=content,
        source_key=source_key,
    )
