import logging
from typing import Any

from ..mcp_core import mcp
from ..deps import db, auth, sync_service
from ..tool_auth import get_principal, validate_required

logger = logging.getLogger("novel_os_mcp.tools.sync")


@mcp.tool(name="sync.import_local_manifest")
async def sync_import_local_manifest(
    workspace: str,
    project: str,
    client_id: str,
    manifest: dict[str, Any],
    local_root_hint: str | None = None,
) -> dict[str, Any]:
    """导入本地文件清单。客户端上传本地文件状态，用于同步比对。"""
    principal = await get_principal("write")
    logger.info("sync_import_local_manifest called")
    validate_required(locals(), "workspace", "project", "client_id", "manifest")
    project_id = await auth.resolve_project_id(workspace, project, principal, access="write")
    return await sync_service.import_local_manifest(
        project_id=project_id,
        username=principal.username,
        client_id=client_id,
        manifest=manifest,
        local_root_hint=local_root_hint,
    )


@mcp.tool(name="sync.import_initial_project_pack")
async def sync_import_initial_project_pack(
    workspace: str,
    project: str,
    pack: dict[str, Any],
) -> dict[str, Any]:
    """导入初始项目包。首次同步时导入完整项目数据包。"""
    principal = await get_principal("write")
    logger.info("sync_import_initial_project_pack called")
    validate_required(locals(), "workspace", "project", "pack")
    project_id = await auth.resolve_project_id(workspace, project, principal, access="write")
    return await sync_service.import_initial_project_pack(
        project_id=project_id,
        username=principal.username,
        pack=pack,
    )


@mcp.tool(name="sync.submit_file_hashes")
async def sync_submit_file_hashes(
    workspace: str,
    project: str,
    client_id: str,
    files: list[dict[str, Any]],
    local_root_hint: str | None = None,
    accept_conflicts: bool = False,
) -> dict[str, Any]:
    """提交文件哈希。客户端提交文件哈希值用于检测变更和冲突。"""
    principal = await get_principal("write")
    logger.info("sync_submit_file_hashes called")
    validate_required(locals(), "workspace", "project", "client_id", "files")
    project_id = await auth.resolve_project_id(workspace, project, principal, access="write")
    return await sync_service.submit_file_hashes(
        project_id=project_id,
        username=principal.username,
        client_id=client_id,
        files=files,
        local_root_hint=local_root_hint,
        accept_conflicts=accept_conflicts,
    )


@mcp.tool(name="sync.list_conflicts")
async def sync_list_conflicts(
    workspace: str,
    project: str,
    client_id: str | None = None,
    manifest: dict[str, Any] | None = None,
) -> list[dict[str, Any]]:
    """列出同步冲突。返回当前待解决的文件同步冲突列表。"""
    principal = await get_principal("read")
    logger.info("sync_list_conflicts called")
    validate_required(locals(), "workspace", "project")
    project_id = await auth.resolve_project_id(workspace, project, principal)
    return await sync_service.list_conflicts(
        project_id=project_id,
        client_id=client_id,
        manifest=manifest,
    )


@mcp.tool(name="sync.resolve_conflict")
async def sync_resolve_conflict(
    workspace: str,
    project: str,
    action: str,
    conflict: dict[str, Any],
    reason: str | None = None,
) -> dict[str, Any]:
    """解决同步冲突。按指定操作（保留客户端/服务端/合并）解决文件冲突。"""
    principal = await get_principal("write")
    logger.info("sync_resolve_conflict called")
    validate_required(locals(), "workspace", "project", "action", "conflict")
    project_id = await auth.resolve_project_id(workspace, project, principal, access="write")
    return await sync_service.resolve_conflict(
        project_id=project_id,
        username=principal.username,
        action=action,
        conflict=conflict,
        reason=reason,
    )


@mcp.tool(name="sync.export_project_pack")
async def sync_export_project_pack(
    workspace: str,
    project: str,
    include_bindings: bool = False,
) -> dict[str, Any]:
    """导出项目包。导出完整项目数据包用于备份或跨设备同步。"""
    principal = await get_principal("read")
    logger.info("sync_export_project_pack called")
    validate_required(locals(), "workspace", "project")
    project_id = await auth.resolve_project_id(workspace, project, principal)
    return await sync_service.export_project_pack(
        project_id=project_id,
        include_bindings=include_bindings,
    )
