import logging
from typing import Any

from ..mcp_core import mcp
from ..deps import db, auth, archive_service, context_compression_service
from ..tool_auth import get_principal, validate_required

logger = logging.getLogger("novel_os_mcp.tools.archive")


@mcp.tool(name="archive.volume")
async def archive_volume(
    workspace: str,
    project: str,
    volume_no: int,
    to_tier: str = "archive",
) -> dict[str, Any]:
    """归档卷数据"""
    principal = await get_principal("write")
    logger.info("archive.volume called")
    validate_required(locals(), "workspace", "project")
    project_id = await auth.resolve_project_id(workspace, project, principal, access="write")
    return await archive_service.archive_volume(
        project_id=project_id,
        volume_no=volume_no,
        to_tier=to_tier,
        performed_by=principal.username,
    )


@mcp.tool(name="archive.restore")
async def archive_restore(
    workspace: str,
    project: str,
    volume_no: int,
    to_tier: str = "active",
) -> dict[str, Any]:
    """恢复卷数据"""
    principal = await get_principal("write")
    logger.info("archive.restore called")
    validate_required(locals(), "workspace", "project")
    project_id = await auth.resolve_project_id(workspace, project, principal, access="write")
    return await archive_service.restore_volume(
        project_id=project_id,
        volume_no=volume_no,
        to_tier=to_tier,
        performed_by=principal.username,
    )


@mcp.tool(name="archive.volume_status")
async def archive_volume_status(
    workspace: str,
    project: str,
    tier: str | None = None,
) -> list[dict[str, Any]]:
    """获取卷归档状态"""
    principal = await get_principal("read")
    logger.info("archive.volume_status called")
    validate_required(locals(), "workspace", "project")
    project_id = await auth.resolve_project_id(workspace, project, principal)
    return await archive_service.get_volume_archive_status(
        project_id=project_id,
        tier=tier,
    )


@mcp.tool(name="archive.history")
async def archive_history(
    workspace: str,
    project: str,
    table_name: str | None = None,
    limit: int = 100,
) -> list[dict[str, Any]]:
    """获取归档历史"""
    principal = await get_principal("read")
    logger.info("archive.history called")
    validate_required(locals(), "workspace", "project")
    project_id = await auth.resolve_project_id(workspace, project, principal)
    return await archive_service.get_archive_history(
        project_id=project_id,
        table_name=table_name,
        limit=limit,
    )


@mcp.tool(name="archive.schedule.create")
async def archive_schedule_create(
    workspace: str | None = None,
    project: str | None = None,
    schedule_name: str = "默认归档任务",
    schedule_type: str = "monthly",
    tier_target: str = "archive",
    tables_to_archive: list[str] | None = None,
    retention_days: int = 365,
    enabled: bool = True,
) -> dict[str, Any]:
    """创建定时归档任务"""
    principal = await get_principal("admin")
    logger.info("archive.schedule.create called")

    project_id = None
    if project:
        project_id = await auth.resolve_project_id(workspace, project, principal)

    if tables_to_archive is None:
        tables_to_archive = ["volumes", "chapters", "plot_threads"]

    return await archive_service.create_archive_schedule(
        project_id=project_id,
        schedule_name=schedule_name,
        schedule_type=schedule_type,
        tier_target=tier_target,
        tables_to_archive=tables_to_archive,
        retention_days=retention_days,
        enabled=enabled,
    )


@mcp.tool(name="archive.schedule.list")
async def archive_schedule_list(
    workspace: str | None = None,
    project: str | None = None,
    enabled: bool | None = None,
) -> list[dict[str, Any]]:
    """获取定时归档任务列表"""
    principal = await get_principal("read")
    logger.info("archive.schedule.list called")

    project_id = None
    if project:
        project_id = await auth.resolve_project_id(workspace, project, principal)

    return await archive_service.get_archive_schedules(
        project_id=project_id,
        enabled=enabled,
    )


@mcp.tool(name="archive.tier_config.get")
async def archive_tier_config_get(
    workspace: str,
    project: str,
    tier: str | None = None,
    table_name: str | None = None,
) -> list[dict[str, Any]]:
    """获取数据分层配置"""
    principal = await get_principal("read")
    logger.info("archive.tier_config.get called")
    validate_required(locals(), "workspace", "project")
    project_id = await auth.resolve_project_id(workspace, project, principal)
    return await archive_service.get_tier_config(
        project_id=project_id,
        tier=tier,
        table_name=table_name,
    )


@mcp.tool(name="context.compression.compress_chapters")
async def context_compression_compress_chapters(
    workspace: str,
    project: str,
    project_id: str,
    chapter_no_start: int,
    chapter_no_end: int,
    target_tokens: int = 500,
) -> dict[str, Any]:
    """压缩章节摘要。将指定范围的章节摘要合并为单一批次摘要，控制token数量。"""
    principal = await get_principal("write")
    project_id = await auth.resolve_project_id(workspace, project, principal, access="write")
    logger.info("context.compression.compress_chapters called")
    validate_required(locals(), "workspace", "project", "project_id", "chapter_no_start", "chapter_no_end")
    return await context_compression_service.compress_chapter_summaries(
        project_id=project_id,
        chapter_no_start=chapter_no_start,
        chapter_no_end=chapter_no_end,
        target_tokens=target_tokens,
    )


@mcp.tool(name="context.compression.compress_arc")
async def context_compression_compress_arc(
    workspace: str,
    project: str,
    project_id: str,
    arc_key: str,
    chapter_no_start: int,
    chapter_no_end: int,
    arc_label: str | None = None,
) -> dict[str, Any]:
    """压缩弧光摘要。将弧光的章节摘要合并为弧光级别的摘要。"""
    principal = await get_principal("write")
    project_id = await auth.resolve_project_id(workspace, project, principal, access="write")
    logger.info("context.compression.compress_arc called")
    validate_required(locals(), "workspace", "project", "project_id", "arc_key", "chapter_no_start", "chapter_no_end")
    return await context_compression_service.compress_arc(
        project_id=project_id,
        arc_key=arc_key,
        chapter_no_start=chapter_no_start,
        chapter_no_end=chapter_no_end,
        arc_label=arc_label,
    )


@mcp.tool(name="context.compression.compress_volume")
async def context_compression_compress_volume(
    workspace: str,
    project: str,
    project_id: str,
    volume_no: int,
) -> dict[str, Any]:
    """压缩卷内容摘要。将整卷内容压缩为卷级别的精炼摘要。"""
    principal = await get_principal("write")
    project_id = await auth.resolve_project_id(workspace, project, principal, access="write")
    logger.info("context.compression.compress_volume called")
    validate_required(locals(), "workspace", "project", "project_id", "volume_no")
    return await context_compression_service.compress_volume(
        project_id=project_id,
        volume_no=volume_no,
    )


@mcp.tool(name="context.compression.compress_series")
async def context_compression_compress_series(
    workspace: str,
    project: str,
    project_id: str,
) -> dict[str, Any]:
    """压缩系列摘要。将所有卷摘要合并为系列级别的全局摘要。"""
    principal = await get_principal("write")
    project_id = await auth.resolve_project_id(workspace, project, principal, access="write")
    logger.info("context.compression.compress_series called")
    validate_required(locals(), "workspace", "project", "project_id")
    return await context_compression_service.compress_series(project_id=project_id)


@mcp.tool(name="context.compression.get_compressed")
async def context_compression_get_compressed(
    workspace: str,
    project: str,
    chapter_no: int,
    volume_no: int | None = None,
    budget_tokens: int = 4000,
) -> dict[str, Any]:
    """获取压缩上下文。在token预算内返回章节生成所需的压缩上下文数据。"""
    principal = await get_principal("read")
    project_id = await auth.resolve_project_id(workspace, project, principal, access="read")
    logger.info("context.compression.get_compressed called")
    validate_required(locals(), "workspace", "project", "chapter_no")
    return await context_compression_service.get_compressed_context(
        project_id=project_id,
        chapter_no=chapter_no,
        volume_no=volume_no,
        budget_tokens=budget_tokens,
    )


@mcp.tool(name="context.compression.auto_compress")
async def context_compression_auto_compress(
    workspace: str,
    project: str,
    chapter_no: int,
) -> dict[str, Any]:
    """执行自动压缩。章节提交后自动触发，在批次/弧光/卷/系列边界执行压缩。"""
    principal = await get_principal("write")
    project_id = await auth.resolve_project_id(workspace, project, principal, access="write")
    logger.info("context.compression.auto_compress called")
    validate_required(locals(), "workspace", "project", "chapter_no")
    results = await context_compression_service.auto_compress_after_commit(
        project_id=project_id,
        chapter_no=chapter_no,
    )
    volume_info = await context_compression_service.check_volume_closure(
        project_id, chapter_no,
    )
    knowledge_batch = await context_compression_service.check_knowledge_batch(
        project_id, chapter_no,
    )
    return {"ok": True, "results": results, "volume_closure": volume_info, "knowledge_batch": knowledge_batch}


@mcp.tool(name="context.compression.list")
async def context_compression_list(
    workspace: str,
    project: str,
    project_id: str,
    layer: str | None = None,
    limit: int = 50,
) -> list[dict[str, Any]]:
    """列出压缩上下文。返回已压缩的上下文列表，可按层级筛选。"""
    principal = await get_principal("read")
    project_id = await auth.resolve_project_id(workspace, project, principal, access="read")
    logger.info("context.compression.list called")
    validate_required(locals(), "workspace", "project", "project_id")
    return await context_compression_service.list_compressed_contexts(
        project_id=project_id,
        layer=layer,
        limit=limit,
    )


@mcp.tool(name="archive.auto_archive")
async def archive_auto_archive(
    workspace: str,
    project: str,
    project_id: str,
    current_chapter_no: int,
    keep_recent_volumes: int = 3,
    keep_recent_chapters: int = 100,
) -> dict[str, Any]:
    """自动归档旧数据。保留近期卷和章节，归档历史数据以保持查询性能。"""
    principal = await get_principal("write")
    project_id = await auth.resolve_project_id(workspace, project, principal, access="write")
    logger.info("archive.auto_archive called")
    validate_required(locals(), "workspace", "project", "project_id", "current_chapter_no")
    return await context_compression_service.archive_old_data(
        project_id=project_id,
        current_chapter_no=current_chapter_no,
        keep_recent_volumes=keep_recent_volumes,
        keep_recent_chapters=keep_recent_chapters,
    )


@mcp.tool(name="archive.get_stats")
async def archive_get_stats(
    workspace: str,
    project: str,
    project_id: str,
) -> dict[str, Any]:
    """获取数据分布统计。返回各表的数据量分布，用于归档决策。"""
    principal = await get_principal("read")
    project_id = await auth.resolve_project_id(workspace, project, principal, access="read")
    logger.info("archive.get_stats called")
    validate_required(locals(), "workspace", "project", "project_id")
    return await context_compression_service.get_archive_stats(project_id=project_id)
