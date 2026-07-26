import logging
from typing import Any

from ..mcp_core import mcp
from ..deps import db, auth, kb_service
from ..tool_auth import get_principal, validate_required

logger = logging.getLogger("novel_os_mcp.tools.knowledge_pack")


@mcp.tool(name="kb.pack.genre.list")
async def kb_pack_genre_list() -> dict[str, Any]:
    """列出所有小说类型知识配置。返回每个类型包含/排除的分类。"""
    principal = await get_principal("read")
    configs = await kb_service.list_genre_configs()
    return {"configs": configs, "count": len(configs)}


@mcp.tool(name="kb.pack.genre.get")
async def kb_pack_genre_get(genre: str) -> dict[str, Any]:
    """获取指定小说类型的知识配置。"""
    principal = await get_principal("read")
    validate_required(locals(), "genre")
    config = await kb_service.get_genre_config(genre)
    if not config:
        return {"error": f"类型 {genre} 不存在"}
    return config


@mcp.tool(name="kb.pack.get")
async def kb_pack_get(workspace: str,
    project: str,
    project_id: str) -> dict[str, Any]:
    """获取项目知识包。返回启用的分类和自定义分类。"""
    principal = await get_principal("read")
    project_id = await auth.resolve_project_id(workspace, project, principal, access="read")
    validate_required(locals(), "workspace", "project", "project_id")
    pack = await kb_service.get_project_pack(project_id)
    if not pack:
        return {"error": "项目知识包不存在，请先创建"}
    return pack


@mcp.tool(name="kb.pack.create")
async def kb_pack_create(workspace: str,
    project: str,
    project_id: str, genre: str) -> dict[str, Any]:
    """创建项目知识包。基于小说类型自动配置启用的分类。"""
    principal = await get_principal("write")
    project_id = await auth.resolve_project_id(workspace, project, principal, access="write")
    validate_required(locals(), "workspace", "project", "project_id", "genre")
    pack = await kb_service.create_project_pack(project_id, genre)
    logger.info("kb_pack_create: %s genre=%s", project_id, genre)
    return pack


@mcp.tool(name="kb.pack.update")
async def kb_pack_update(
    workspace: str,
    project: str,
    project_id: str,
    active_categories: list[str] | None = None,
) -> dict[str, Any]:
    """更新项目知识包。可调整启用的分类列表。"""
    principal = await get_principal("write")
    project_id = await auth.resolve_project_id(workspace, project, principal, access="write")
    validate_required(locals(), "workspace", "project", "project_id")
    pack = await kb_service.update_project_pack(project_id, active_categories)
    return pack


@mcp.tool(name="kb.pack.custom.add")
async def kb_pack_custom_add(
    workspace: str,
    project: str,
    project_id: str,
    name: str,
    parent: str | None = None,
    description: str = "",
) -> dict[str, Any]:
    """添加自定义分类到项目知识包。"""
    principal = await get_principal("write")
    project_id = await auth.resolve_project_id(workspace, project, principal, access="write")
    validate_required(locals(), "workspace", "project", "project_id", "name")
    pack = await kb_service.add_custom_category(project_id, name, parent, description)
    logger.info("kb_pack_custom_add: %s name=%s", project_id, name)
    return pack


@mcp.tool(name="kb.pack.custom.remove")
async def kb_pack_custom_remove(
    workspace: str,
    project: str,
    project_id: str,
    name: str,
) -> dict[str, Any]:
    """移除项目知识包的自定义分类。"""
    principal = await get_principal("write")
    project_id = await auth.resolve_project_id(workspace, project, principal, access="write")
    validate_required(locals(), "workspace", "project", "project_id", "name")
    pack = await kb_service.remove_custom_category(project_id, name)
    return pack


@mcp.tool(name="kb.pack.categories")
async def kb_pack_categories(workspace: str,
    project: str,
    project_id: str) -> dict[str, Any]:
    """获取项目启用的所有分类（系统分类 + 自定义分类）。用于检索时过滤。"""
    principal = await get_principal("read")
    project_id = await auth.resolve_project_id(workspace, project, principal, access="read")
    validate_required(locals(), "workspace", "project", "project_id")
    categories = await kb_service.get_active_categories(project_id)
    return {"categories": categories, "count": len(categories)}
