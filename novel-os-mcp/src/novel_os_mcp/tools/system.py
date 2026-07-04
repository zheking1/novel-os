import logging
from typing import Any

from ..mcp_core import mcp
from ..config import get_settings
from ..deps import db, auth, cache_service, backup_service, _health_service, _degradation_service
from ..tool_auth import get_principal, validate_required

logger = logging.getLogger("novel_os_mcp.tools.system")

settings = get_settings()


@mcp.tool(name="cache.health")
async def cache_health() -> dict[str, Any]:
    """检查 Redis 缓存健康状态"""
    principal = await get_principal("read")
    logger.info("cache_health called")
    is_healthy = await cache_service.ping()
    return {
        "redis": "connected" if is_healthy else "disconnected",
        "healthy": is_healthy,
    }


@mcp.tool(name="cache.get_stats")
async def cache_get_stats(
    workspace: str,
    project: str,
) -> dict[str, Any]:
    """获取项目缓存统计"""
    principal = await get_principal("read")
    logger.info("cache_get_stats called")
    validate_required(locals(), "workspace", "project")
    project_id = await auth.resolve_project_id(workspace, project, principal)
    return await cache_service.get_cache_stats(project_id)


@mcp.tool(name="cache.invalidate")
async def cache_invalidate(
    workspace: str,
    project: str,
    target: str,
    target_id: str | None = None,
) -> dict[str, Any]:
    """使缓存失效"""
    principal = await get_principal("write")
    logger.info("cache_invalidate called")
    validate_required(locals(), "workspace", "project", "target")
    project_id = await auth.resolve_project_id(workspace, project, principal, access="write")

    if target == "canon":
        if not target_id:
            raise ValueError("target_id required for canon invalidation")
        await cache_service.invalidate_on_canon_update(project_id, target_id)
        return {"invalidated": f"canon:{target_id}"}

    elif target == "entity":
        if not target_id:
            raise ValueError("target_id required for entity invalidation")
        await cache_service.invalidate_entity(project_id, target_id)
        return {"invalidated": f"entity:{target_id}"}

    elif target == "chapter":
        if not target_id:
            raise ValueError("target_id required for chapter invalidation")
        chapter_no = int(target_id)
        await cache_service.invalidate_on_final_commit(project_id, chapter_no)
        return {"invalidated": f"chapter:{chapter_no}"}

    elif target == "rules":
        await cache_service.invalidate_on_rules_update(project_id)
        return {"invalidated": "rules"}

    elif target == "context":
        chapter_no = int(target_id) if target_id else None
        await cache_service.invalidate_context_pack(project_id, chapter_no)
        return {"invalidated": f"context:{chapter_no or 'all'}"}

    elif target == "all":
        cleared = await cache_service.clear_project_cache(project_id)
        return {"invalidated": "all", "keys_cleared": cleared}

    else:
        raise ValueError(f"Unknown target: {target}")


@mcp.tool(name="cache.warm")
async def cache_warm(
    workspace: str,
    project: str,
    chapter_nos: list[int],
    profiles: list[str] | None = None,
    povs: list[str] | None = None,
) -> dict[str, Any]:
    """预热上下文缓存"""
    principal = await get_principal("write")
    logger.info("cache_warm called")
    validate_required(locals(), "workspace", "project", "chapter_nos")
    project_id = await auth.resolve_project_id(workspace, project, principal, access="write")

    if profiles is None:
        profiles = ["standard", "detailed"]
    if povs is None:
        povs = ["narrator"]

    return await cache_service.warm_context_cache(
        project_id=project_id,
        chapter_nos=chapter_nos,
        profiles=profiles,
        povs=povs,
    )


@mcp.tool(name="cache.get")
async def cache_get(
    workspace: str,
    project: str,
    target: str,
    target_id: str,
    profile: str | None = None,
    pov: str | None = None,
) -> dict[str, Any] | None:
    """获取缓存内容"""
    principal = await get_principal("read")
    logger.info("cache_get called")
    validate_required(locals(), "workspace", "project", "target", "target_id")
    project_id = await auth.resolve_project_id(workspace, project, principal)

    if target == "canon":
        return await cache_service.get_canon_summary(project_id, target_id)

    elif target == "entity":
        return await cache_service.get_entity_state(project_id, target_id)

    elif target == "chapter":
        chapter_no = int(target_id)
        return await cache_service.get_chapter_summary(project_id, chapter_no)

    elif target == "rules":
        return await cache_service.get_rules_summary(project_id, target_id)

    elif target == "context":
        if not profile or not pov:
            raise ValueError("profile and pov required for context retrieval")
        chapter_no = int(target_id)
        return await cache_service.get_context_pack(project_id, chapter_no, profile, pov)

    else:
        raise ValueError(f"Unknown target: {target}")


@mcp.tool(name="backup.create")
async def backup_create(
    workspace: str | None = None,
    project: str | None = None,
    backup_type: str = "incremental",
    storage_path: str | None = None,
) -> dict[str, Any]:
    """创建备份记录"""
    principal = await get_principal("admin")
    logger.info("backup_create called")

    project_id = None
    if project:
        project_id = await auth.resolve_project_id(workspace, project, principal)

    return await backup_service.create_backup_record(
        project_id=project_id,
        backup_type=backup_type,
        storage_path=storage_path,
    )


@mcp.tool(name="backup.list")
async def backup_list(
    workspace: str | None = None,
    project: str | None = None,
    backup_type: str | None = None,
    status: str | None = None,
    limit: int = 100,
) -> list[dict[str, Any]]:
    """获取备份记录列表"""
    principal = await get_principal("read")
    logger.info("backup_list called")

    project_id = None
    if project:
        project_id = await auth.resolve_project_id(workspace, project, principal)

    return await backup_service.get_backup_records(
        project_id=project_id,
        backup_type=backup_type,
        status=status,
        limit=limit,
    )


@mcp.tool(name="backup.schedule.upsert")
async def backup_schedule_upsert(
    schedule_name: str,
    workspace: str | None = None,
    project: str | None = None,
    backup_type: str = "incremental",
    schedule_type: str = "daily",
    retention_count: int = 7,
    retention_days: int = 30,
    enabled: bool = True,
) -> dict[str, Any]:
    """创建或更新备份计划"""
    principal = await get_principal("admin")
    logger.info("backup_schedule_upsert called")

    project_id = None
    if project:
        project_id = await auth.resolve_project_id(workspace, project, principal)

    return await backup_service.upsert_backup_schedule(
        schedule_name=schedule_name,
        project_id=project_id,
        backup_type=backup_type,
        schedule_type=schedule_type,
        retention_count=retention_count,
        retention_days=retention_days,
        enabled=enabled,
    )


@mcp.tool(name="backup.schedule.list")
async def backup_schedule_list(
    workspace: str | None = None,
    project: str | None = None,
) -> list[dict[str, Any]]:
    """获取备份计划列表"""
    principal = await get_principal("read")
    logger.info("backup_schedule_list called")

    project_id = None
    if project:
        project_id = await auth.resolve_project_id(workspace, project, principal)

    return await backup_service.get_backup_schedule(project_id=project_id)


@mcp.tool(name="restore.list")
async def restore_list(
    workspace: str,
    project: str,
    limit: int = 100,
) -> list[dict[str, Any]]:
    """获取恢复记录列表"""
    principal = await get_principal("read")
    logger.info("restore_list called")
    validate_required(locals(), "workspace", "project")
    project_id = await auth.resolve_project_id(workspace, project, principal)
    return await backup_service.get_restore_records(
        project_id=project_id,
        limit=limit,
    )


@mcp.tool(name="system.health")
async def system_health() -> dict[str, Any]:
    """获取系统健康状态"""
    principal = await get_principal("read")
    logger.info("system_health called")
    return await _health_service.get_all_health()


@mcp.tool(name="system.degradation_status")
async def system_degradation_status() -> dict[str, Any]:
    """获取降级状态"""
    principal = await get_principal("read")
    logger.info("system_degradation_status called")
    return await _degradation_service.update_status()


@mcp.tool(name="system.degradation_plan")
async def system_degradation_plan(
    failed_services: list[str],
) -> dict[str, Any]:
    """获取降级方案"""
    principal = await get_principal("read")
    logger.info("system_degradation_plan called")
    return _degradation_service.get_degradation_plan(failed_services)


@mcp.tool(name="system.fallback_strategy")
async def system_fallback_strategy(
    feature: str,
) -> str:
    """获取功能的降级策略"""
    principal = await get_principal("read")
    logger.info("system_fallback_strategy called")
    return _degradation_service.get_fallback_strategy(feature)
