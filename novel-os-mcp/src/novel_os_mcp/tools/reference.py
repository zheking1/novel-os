import logging
from typing import Any

from ..mcp_core import mcp
from ..deps import db, auth, reference_service
from ..tool_auth import get_principal, validate_required

logger = logging.getLogger("novel_os_mcp.tools.reference")


@mcp.tool(name="reference.source_create")
async def reference_source_create(
    workspace: str | None,
    project: str | None,
    source_type: str,
    name: str,
    source_uri: str | None = None,
    license: str | None = None,
    metadata: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """创建参考资料源。注册新的参考来源（文档、网址、数据库等），支持工作区和项目作用域。"""
    principal = await get_principal("write")
    logger.info("reference_source_create called")
    validate_required(locals(), "source_type", "name")
    workspace_id = None
    project_id = None
    if workspace and project:
        project_id = await auth.resolve_project_id(workspace, project, principal, access="write")
        row = await db.fetchrow("SELECT workspace_id::text FROM projects WHERE id = $1", project_id)
        workspace_id = row["workspace_id"] if row else None
    elif workspace:
        await auth.require_workspace_access(principal, workspace)
        row = await db.fetchrow("SELECT id::text FROM workspaces WHERE slug = $1", workspace)
        if row is None:
            raise ValueError(f"Workspace not found: {workspace}")
        workspace_id = row["id"]
    elif "admin" not in principal.scopes:
        raise PermissionError("Global reference sources require admin")
    return await reference_service.upsert_source(
        workspace_id=workspace_id,
        project_id=project_id,
        source_type=source_type,
        name=name,
        source_uri=source_uri,
        license=license,
        metadata=metadata or {},
    )


@mcp.tool(name="reference.item_add")
async def reference_item_add(
    source_id: str,
    workspace: str | None,
    project: str | None,
    item_type: str,
    key: str,
    content: str,
    title: str | None = None,
    metadata: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """添加参考条目。向资料源添加具体参考内容（设定、人物、术语等）。"""
    principal = await get_principal("write")
    logger.info("reference_item_add called")
    validate_required(locals(), "source_id", "item_type", "key", "content")
    project_id = None
    if workspace and project:
        project_id = await auth.resolve_project_id(workspace, project, principal, access="write")
    elif "admin" not in principal.scopes:
        raise PermissionError("Workspace or project scoped reference items are required")
    return await reference_service.add_item(
        source_id=source_id,
        project_id=project_id,
        item_type=item_type,
        key=key,
        title=title,
        content=content,
        metadata=metadata or {},
    )


@mcp.tool(name="reference.search")
async def reference_search(
    workspace: str | None,
    project: str | None,
    query: str,
    item_types: list[str] | None = None,
    limit: int = 20,
) -> list[dict[str, Any]]:
    """搜索参考资料。按关键词搜索参考条目，支持类型筛选和作用域限定。"""
    principal = await get_principal("read")
    logger.info("reference_search called")
    validate_required(locals(), "query")
    workspace_id = None
    project_id = None
    if workspace and project:
        project_id = await auth.resolve_project_id(workspace, project, principal)
        row = await db.fetchrow("SELECT workspace_id::text FROM projects WHERE id = $1", project_id)
        workspace_id = row["workspace_id"] if row else None
    elif workspace:
        await auth.require_workspace_access(principal, workspace)
        row = await db.fetchrow("SELECT id::text FROM workspaces WHERE slug = $1", workspace)
        if row is None:
            raise ValueError(f"Workspace not found: {workspace}")
        workspace_id = row["id"]
    elif "admin" not in principal.scopes:
        raise PermissionError("Global reference search requires admin")
    return await reference_service.search(
        workspace_id=workspace_id,
        project_id=project_id,
        query=query,
        item_types=item_types,
        limit=limit,
    )
