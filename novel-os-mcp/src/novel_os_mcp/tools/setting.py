import logging
from typing import Any

from ..mcp_core import mcp
from ..deps import db, auth, global_settings_service
from ..tool_auth import get_principal, validate_required

logger = logging.getLogger("novel_os_mcp.tools.setting")


@mcp.tool(name="setting.category.list")
async def setting_category_list(
    workspace: str,
    is_active: bool | None = True,
) -> list[dict[str, Any]]:
    """列出 workspace 下的设置分类。支持按启用状态过滤。"""
    principal = await get_principal("read")
    logger.info("setting_category_list called")
    validate_required(locals(), "workspace")
    workspace_id = await auth.resolve_workspace_id(principal, workspace)
    return await global_settings_service.list_categories(
        workspace_id=workspace_id,
        is_active=is_active,
    )


@mcp.tool(name="setting.category.get")
async def setting_category_get(
    workspace: str,
    category_id: str | None = None,
    slug: str | None = None,
) -> dict[str, Any]:
    """获取单个设置分类。通过 category_id 或 slug 查询。"""
    principal = await get_principal("read")
    logger.info("setting_category_get called")
    validate_required(locals(), "workspace")
    workspace_id = await auth.resolve_workspace_id(principal, workspace)
    result = await global_settings_service.get_category(
        workspace_id=workspace_id,
        category_id=category_id,
        slug=slug,
    )
    if not result:
        raise ValueError(f"设置分类未找到（category_id={category_id}, slug={slug}）")
    return result


@mcp.tool(name="setting.category.upsert")
async def setting_category_upsert(
    workspace: str,
    slug: str,
    name: str,
    description: str | None = None,
    icon: str = "📁",
    sort_order: int = 0,
    is_standard: bool = False,
    metadata: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """创建或更新设置分类。slug 唯一标识，重复则更新。"""
    principal = await get_principal("write")
    logger.info("setting_category_upsert called")
    validate_required(locals(), "workspace", "slug", "name")
    workspace_id = await auth.resolve_workspace_id(principal, workspace)
    return await global_settings_service.upsert_category(
        workspace_id=workspace_id,
        slug=slug,
        name=name,
        username=principal.username,
        description=description,
        icon=icon,
        sort_order=sort_order,
        is_standard=is_standard,
        metadata=metadata,
    )


@mcp.tool(name="setting.category.delete")
async def setting_category_delete(
    workspace: str,
    category_id: str,
) -> dict[str, Any]:
    """删除指定设置分类及其下所有条目。"""
    principal = await get_principal("write")
    logger.info("setting_category_delete called")
    validate_required(locals(), "workspace")
    workspace_id = await auth.resolve_workspace_id(principal, workspace)
    return await global_settings_service.delete_category(
        workspace_id=workspace_id,
        category_id=category_id,
    )


@mcp.tool(name="setting.item.list")
async def setting_item_list(
    workspace: str,
    category_id: str | None = None,
    is_global: bool | None = None,
    level: str | None = None,
    tags: list[str] | None = None,
    limit: int = 100,
    offset: int = 0,
) -> list[dict[str, Any]]:
    """列出 workspace 下的设置条目。支持按分类、全局性、级别、标签过滤。"""
    principal = await get_principal("read")
    logger.info("setting_item_list called")
    validate_required(locals(), "workspace")
    workspace_id = await auth.resolve_workspace_id(principal, workspace)
    return await global_settings_service.list_items(
        workspace_id=workspace_id,
        category_id=category_id,
        is_global=is_global,
        level=level,
        tags=tags,
        limit=limit,
        offset=offset,
    )


@mcp.tool(name="setting.item.get")
async def setting_item_get(
    workspace: str,
    item_id: str | None = None,
    item_code: str | None = None,
) -> dict[str, Any]:
    """获取单个设置条目详情。通过 item_id 或 item_code 查询。"""
    principal = await get_principal("read")
    logger.info("setting_item_get called")
    validate_required(locals(), "workspace")
    workspace_id = await auth.resolve_workspace_id(principal, workspace)
    result = await global_settings_service.get_item(
        workspace_id=workspace_id,
        item_id=item_id,
        item_code=item_code,
    )
    if not result:
        raise ValueError(f"设置条目未找到（item_id={item_id}, item_code={item_code}）")
    return result


@mcp.tool(name="setting.item.upsert")
async def setting_item_upsert(
    workspace: str,
    category_id: str,
    core_summary: str,
    item_code: str | None = None,
    keywords: list[str] | None = None,
    intent_synonyms: list[str] | None = None,
    detailed_expansion: str | None = None,
    ai_instruction: str | None = None,
    poison_points: list[str] | None = None,
    level: str = "knowledge",
    applicable_skills: list[str] | None = None,
    applicable_genres: list[str] | None = None,
    data: dict[str, Any] | None = None,
    tags: list[str] | None = None,
    is_global: bool = True,
    sort_order: int = 0,
    metadata: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """创建或更新设置条目。含摘要、关键词、AI 指令等字段，支持按技能和题材过滤。"""
    principal = await get_principal("write")
    logger.info("setting_item_upsert called")
    validate_required(locals(), "workspace", "category_id", "core_summary")
    workspace_id = await auth.resolve_workspace_id(principal, workspace)
    return await global_settings_service.upsert_item(
        workspace_id=workspace_id,
        category_id=category_id,
        username=principal.username,
        item_code=item_code,
        core_summary=core_summary,
        keywords=keywords,
        intent_synonyms=intent_synonyms,
        detailed_expansion=detailed_expansion,
        ai_instruction=ai_instruction,
        poison_points=poison_points,
        level=level,
        applicable_skills=applicable_skills,
        applicable_genres=applicable_genres,
        data=data,
        tags=tags,
        is_global=is_global,
        sort_order=sort_order,
        metadata=metadata,
    )


@mcp.tool(name="setting.item.bulk_upsert")
async def setting_item_bulk_upsert(
    workspace: str,
    category_id: str,
    items: list[dict[str, Any]],
) -> dict[str, Any]:
    """批量创建或更新设置条目。返回 created/updated/error 统计。"""
    principal = await get_principal("write")
    logger.info("setting_item_bulk_upsert called")
    validate_required(locals(), "workspace", "category_id", "items")
    workspace_id = await auth.resolve_workspace_id(principal, workspace)

    created = 0
    updated = 0
    errors = []

    for i, item in enumerate(items):
        try:
            result = await global_settings_service.upsert_item(
                workspace_id=workspace_id,
                category_id=category_id,
                username=principal.username,
                **item,
            )
            if result.get("created_at") == result.get("updated_at"):
                created += 1
            else:
                updated += 1
        except Exception as e:
            errors.append({"index": i, "error": str(e)})

    return {
        "created": created,
        "updated": updated,
        "errors": errors,
    }


@mcp.tool(name="setting.item.delete")
async def setting_item_delete(
    workspace: str,
    item_id: str,
) -> dict[str, Any]:
    """删除指定设置条目。"""
    principal = await get_principal("write")
    logger.info("setting_item_delete called")
    validate_required(locals(), "workspace")
    workspace_id = await auth.resolve_workspace_id(principal, workspace)
    return await global_settings_service.delete_item(
        workspace_id=workspace_id,
        item_id=item_id,
    )


@mcp.tool(name="setting.search")
async def setting_search(
    workspace: str,
    query: str,
    category_id: str | None = None,
    level: str | None = None,
    skill: str | None = None,
    genre: str | None = None,
    limit: int = 20,
    offset: int = 0,
) -> list[dict[str, Any]]:
    """BM25 全文搜索设置条目。支持按分类、级别、技能、题材过滤。"""
    principal = await get_principal("read")
    logger.info("setting_search called")
    validate_required(locals(), "workspace", "query")
    workspace_id = await auth.resolve_workspace_id(principal, workspace)
    return await global_settings_service.bm25_search(
        workspace_id=workspace_id,
        query=query,
        category_id=category_id,
        level=level,
        skill=skill,
        genre=genre,
        limit=limit,
        offset=offset,
    )


@mcp.tool(name="setting.genre.resolve")
async def setting_genre_resolve(
    input_text: str,
) -> list[dict[str, Any]]:
    """将输入文本解析为匹配的题材列表。用于模糊匹配题材名称。"""
    principal = await get_principal("read")
    logger.info("setting_genre_resolve called")
    validate_required(locals(), "input_text")
    return await global_settings_service.resolve_genre(input_text=input_text)


@mcp.tool(name="setting.genre.list")
async def setting_genre_list() -> list[dict[str, Any]]:
    """列出所有系统预设题材。"""
    principal = await get_principal("read")
    logger.info("setting_genre_list called")
    return await global_settings_service.list_genres()


@mcp.tool(name="setting.csv.import")
async def setting_csv_import(
    workspace: str,
    category_id: str,
    csv_content: str,
) -> dict[str, Any]:
    """从 CSV 内容批量导入设置条目到指定分类。"""
    principal = await get_principal("write")
    logger.info("setting_csv_import called")
    validate_required(locals(), "workspace", "category_id", "csv_content")
    workspace_id = await auth.resolve_workspace_id(principal, workspace)
    return await global_settings_service.csv_import(
        workspace_id=workspace_id,
        category_id=category_id,
        username=principal.username,
        csv_content=csv_content,
    )


@mcp.tool(name="setting.csv.export")
async def setting_csv_export(
    workspace: str,
    category_id: str | None = None,
) -> str:
    """导出设置条目为 CSV 格式字符串。可按分类过滤。"""
    principal = await get_principal("read")
    logger.info("setting_csv_export called")
    validate_required(locals(), "workspace")
    workspace_id = await auth.resolve_workspace_id(principal, workspace)
    return await global_settings_service.csv_export(
        workspace_id=workspace_id,
        category_id=category_id,
    )
