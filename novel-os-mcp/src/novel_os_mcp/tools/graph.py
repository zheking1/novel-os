from typing import Any
import logging

from ..mcp_core import mcp
from ..deps import db, auth, graph_service
from ..tool_auth import get_principal, validate_required

logger = logging.getLogger("novel_os_mcp.tools.graph")


@mcp.tool(name="graph.get_data")
async def graph_get_data(
    workspace: str,
    project: str,
    entity_types: list[str] | None = None,
    depth: int = 2,
) -> dict[str, Any]:
    """获取关系图数据。返回节点和边数据用于可视化，可按实体类型筛选。"""
    principal = await get_principal("read")
    logger.info("graph_get_data called")
    validate_required(locals(), "workspace", "project")
    project_id = await auth.resolve_project_id(workspace, project, principal)
    return await graph_service.get_graph_data(
        project_id=project_id,
        entity_types=entity_types,
        depth=depth,
    )


@mcp.tool(name="graph.get_subgraph")
async def graph_get_subgraph(
    workspace: str,
    project: str,
    center_entity: str,
    depth: int = 2,
) -> dict[str, Any]:
    """获取子图。以指定实体为中心获取指定深度的关系子图。"""
    principal = await get_principal("read")
    logger.info("graph_get_subgraph called")
    validate_required(locals(), "workspace", "project")
    project_id = await auth.resolve_project_id(workspace, project, principal)
    return await graph_service.get_subgraph(
        project_id=project_id,
        center_entity=center_entity,
        depth=depth,
    )


@mcp.tool(name="graph.get_timeline")
async def graph_get_timeline(
    workspace: str,
    project: str,
    entity_name: str,
) -> dict[str, Any]:
    """获取实体关系时间线。返回指定实体关系变化的时序数据。"""
    principal = await get_principal("read")
    logger.info("graph_get_timeline called")
    validate_required(locals(), "workspace", "project")
    project_id = await auth.resolve_project_id(workspace, project, principal)
    return await graph_service.get_timeline_data(
        project_id=project_id,
        entity_name=entity_name,
    )
