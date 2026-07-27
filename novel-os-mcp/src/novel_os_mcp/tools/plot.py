from typing import Any
import logging

from ..mcp_core import mcp
from ..deps import db, auth, plot_service
from ..tool_auth import get_principal, validate_required

logger = logging.getLogger("novel_os_mcp.tools.plot")


@mcp.tool(name="volume.upsert")
async def volume_upsert(
    workspace: str,
    project: str,
    volume_no: int,
    title: str | None = None,
    outline: str | None = None,
    status: str = "planned",
    start_chapter_no: int | None = None,
    end_chapter_no: int | None = None,
    summary: str | None = None,
    goals: list[dict[str, Any]] | None = None,
    metadata: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """创建或更新卷信息。定义卷的大纲、状态和章节范围。"""
    principal = await get_principal("write")
    logger.info("volume_upsert called")
    validate_required(locals(), "workspace", "project")
    project_id = await auth.resolve_project_id(workspace, project, principal, access="write")
    return await plot_service.upsert_volume(
        project_id=project_id,
        volume_no=volume_no,
        title=title,
        outline=outline,
        status=status,
        start_chapter_no=start_chapter_no,
        end_chapter_no=end_chapter_no,
        summary=summary,
        goals=goals or [],
        metadata=metadata or {},
    )


@mcp.tool(name="volume.get")
async def volume_get(
    workspace: str,
    project: str,
    volume_no: int | None = None,
    volume_id: str | None = None,
) -> dict[str, Any]:
    """获取单个卷详情。可用 volume_no（整数）或 volume_id（UUID）查询。"""
    principal = await get_principal("read")
    logger.info("volume_get called: volume_no=%s, volume_id=%s", volume_no, volume_id)
    validate_required(locals(), "workspace", "project")
    if volume_no is None and volume_id is None:
        raise ValueError("volume_no or volume_id is required")
    project_id = await auth.resolve_project_id(workspace, project, principal)
    result = await plot_service.get_volume(
        project_id=project_id, volume_no=volume_no, volume_id=volume_id,
    )
    if not result:
        return {"error": f"Volume not found"}
    return result


@mcp.tool(name="volume.list")
async def volume_list(
    workspace: str,
    project: str,
    statuses: list[str] | None = None,
    current_chapter_no: int | None = None,
    limit: int = 100,
) -> list[dict[str, Any]]:
    """列出所有卷。可按状态过滤，或查找包含指定章节的卷。"""
    principal = await get_principal("read")
    logger.info("volume_list called")
    validate_required(locals(), "workspace", "project")
    project_id = await auth.resolve_project_id(workspace, project, principal)
    return await plot_service.list_volumes(
        project_id=project_id,
        statuses=statuses,
        current_chapter_no=current_chapter_no,
        limit=limit,
    )


@mcp.tool(name="plot.thread.upsert")
async def plot_thread_upsert(
    workspace: str,
    project: str,
    key: str,
    title: str,
    thread_type: str = "side",
    status: str = "open",
    importance: str = "medium",
    volume_no: int | None = None,
    start_chapter_no: int | None = None,
    current_chapter_no: int | None = None,
    last_advanced_chapter_no: int | None = None,
    expected_next_chapter_no: int | None = None,
    stalled_after_chapters: int = 20,
    related_entity_ids: list[str] | None = None,
    related_foreshadowing_ids: list[str] | None = None,
    metadata: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """创建或更新情节线。追踪主线/支线的进展和停滞状态。"""
    principal = await get_principal("write")
    logger.info("plot_thread_upsert called")
    validate_required(locals(), "workspace", "project", "key", "title")
    project_id = await auth.resolve_project_id(workspace, project, principal, access="write")
    return await plot_service.upsert_plot_thread(
        project_id=project_id,
        key=key,
        title=title,
        thread_type=thread_type,
        status=status,
        importance=importance,
        volume_no=volume_no,
        start_chapter_no=start_chapter_no,
        current_chapter_no=current_chapter_no,
        last_advanced_chapter_no=last_advanced_chapter_no,
        expected_next_chapter_no=expected_next_chapter_no,
        stalled_after_chapters=stalled_after_chapters,
        related_entity_ids=related_entity_ids,
        related_foreshadowing_ids=related_foreshadowing_ids,
        metadata=metadata or {},
    )


@mcp.tool(name="plot.thread.list")
async def plot_thread_list(
    workspace: str,
    project: str,
    statuses: list[str] | None = None,
    thread_types: list[str] | None = None,
    importance: list[str] | None = None,
    volume_no: int | None = None,
    current_chapter_no: int | None = None,
    include_closed: bool = False,
    limit: int = 100,
) -> list[dict[str, Any]]:
    """列出情节线。支持按状态、类型、重要性、卷号过滤。"""
    principal = await get_principal("read")
    logger.info("plot_thread_list called")
    validate_required(locals(), "workspace", "project")
    project_id = await auth.resolve_project_id(workspace, project, principal)
    return await plot_service.list_plot_threads(
        project_id=project_id,
        statuses=statuses,
        thread_types=thread_types,
        importance=importance,
        volume_no=volume_no,
        current_chapter_no=current_chapter_no,
        include_closed=include_closed,
        limit=limit,
    )


@mcp.tool(name="plot.thread.advance")
async def plot_thread_advance(
    workspace: str,
    project: str,
    key: str,
    chapter_no: int,
    status: str | None = None,
    progress_note: str | None = None,
    expected_next_chapter_no: int | None = None,
    metadata: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """推进情节线到指定章节。更新进度、状态和预期下一章。"""
    principal = await get_principal("write")
    logger.info("plot.thread.advance: ws=%s prj=%s key=%s ch=%d", workspace, project, key, chapter_no)
    validate_required(locals(), "workspace", "project", "key")
    project_id = await auth.resolve_project_id(workspace, project, principal, access="write")
    return await plot_service.advance_plot_thread(
        project_id=project_id,
        key=key,
        chapter_no=chapter_no,
        status=status,
        progress_note=progress_note,
        expected_next_chapter_no=expected_next_chapter_no,
        metadata=metadata or {},
    )


@mcp.tool(name="plot.thread.check_stalled")
async def plot_thread_check_stalled(
    workspace: str,
    project: str,
    current_chapter_no: int,
    threshold_chapters: int | None = None,
    statuses: list[str] | None = None,
    limit: int = 100,
) -> list[dict[str, Any]]:
    """检测停滞的情节线。返回超过阈值章节数未推进的线索列表。"""
    principal = await get_principal("read")
    logger.info("plot_thread_check_stalled called")
    validate_required(locals(), "workspace", "project")
    project_id = await auth.resolve_project_id(workspace, project, principal)
    return await plot_service.check_stalled_threads(
        project_id=project_id,
        current_chapter_no=current_chapter_no,
        threshold_chapters=threshold_chapters,
        statuses=statuses,
        limit=limit,
    )


@mcp.tool(name="plot.thread.delete")
async def plot_thread_delete(
    workspace: str,
    project: str,
    key: str,
) -> dict[str, Any]:
    """物理删除剧情线。"""
    principal = await get_principal("write")
    logger.info("plot_thread_delete called")
    validate_required(locals(), "workspace", "project", "key")
    project_id = await auth.resolve_project_id(workspace, project, principal, access="write")
    return await plot_service.delete_thread(project_id=project_id, key=key)


@mcp.tool(name="plot.list_foreshadowing")
async def plot_list_foreshadowing(
    workspace: str,
    project: str,
    statuses: list[str] | None = None,
    importance: list[str] | None = None,
    layers: list[str] | None = None,
    overdue_at_chapter: int | None = None,
    limit: int = 50,
) -> list[dict[str, Any]]:
    """列出伏笔。支持按状态、重要性、层级过滤，可检测逾期伏笔。"""
    principal = await get_principal("read")
    logger.info("plot_list_foreshadowing called")
    validate_required(locals(), "workspace", "project")
    project_id = await auth.resolve_project_id(workspace, project, principal)
    return await plot_service.list_foreshadowing(
        project_id=project_id,
        statuses=statuses,
        importance=importance,
        limit=limit,
        layers=layers,
        overdue_at_chapter=overdue_at_chapter,
    )


@mcp.tool(name="plot.upsert_foreshadowing")
async def plot_upsert_foreshadowing(
    workspace: str,
    project: str,
    key: str,
    title: str,
    status: str = "planted",
    importance: str = "medium",
    expected_payoff_range: str | None = None,
    payload: dict[str, Any] | None = None,
    parent_foreshadowing_id: str | None = None,
    related_foreshadowing_ids: list[str] | None = None,
    trigger_on_payoff_ids: list[str] | None = None,
    blocks_payoff_until_ids: list[str] | None = None,
    layer: str = "visible",
    must_payoff: bool = False,
    payoff_deadline_chapter: int | None = None,
    payoff_deadline_volume: int | None = None,
    overdue_policy: str = "warn",
) -> dict[str, Any]:
    """创建或更新伏笔。管理伏笔的埋设、关联、回收和层级关系。"""
    principal = await get_principal("write")
    logger.info("plot.upsert_foreshadowing: ws=%s prj=%s key=%s title=%s status=%s", workspace, project, key, title, status)
    validate_required(locals(), "key", "title")
    project_id = await auth.resolve_project_id(workspace, project, principal, access="write")
    return await plot_service.upsert_foreshadowing(
        project_id=project_id,
        key=key,
        title=title,
        status=status,
        importance=importance,
        expected_payoff_range=expected_payoff_range,
        payload=payload or {},
        parent_foreshadowing_id=parent_foreshadowing_id,
        related_foreshadowing_ids=related_foreshadowing_ids or [],
        trigger_on_payoff_ids=trigger_on_payoff_ids or [],
        blocks_payoff_until_ids=blocks_payoff_until_ids or [],
        layer=layer,
        must_payoff=must_payoff,
        payoff_deadline_chapter=payoff_deadline_chapter,
        payoff_deadline_volume=payoff_deadline_volume,
        overdue_policy=overdue_policy,
    )


@mcp.tool(name="foreshadowing.bulk_status_update")
async def foreshadowing_bulk_status_update(
    workspace: str,
    project: str,
    status: str,
    keys: list[str] | None = None,
    ids: list[str] | None = None,
    reason: str | None = None,
    metadata: dict[str, Any] | None = None,
) -> list[dict[str, Any]]:
    """批量更新伏笔状态。可按 key 或 id 批量标记为已回收/废弃等。"""
    principal = await get_principal("write")
    logger.info("foreshadowing_bulk_status_update called")
    validate_required(locals(), "workspace", "project", "status")
    project_id = await auth.resolve_project_id(workspace, project, principal, access="write")
    return await plot_service.bulk_update_foreshadowing_status(
        project_id=project_id,
        status=status,
        keys=keys,
        ids=ids,
        reason=reason,
        metadata=metadata or {},
    )


@mcp.tool(name="foreshadowing.check_overdue")
async def foreshadowing_check_overdue(
    workspace: str,
    project: str,
    current_chapter_no: int,
    current_volume_no: int | None = None,
    include_optional: bool = True,
    limit: int = 100,
) -> list[dict[str, Any]]:
    """检查逾期伏笔。返回超过截止章节仍未回收的伏笔列表。"""
    principal = await get_principal("read")
    logger.info("foreshadowing_check_overdue called")
    validate_required(locals(), "workspace", "project")
    project_id = await auth.resolve_project_id(workspace, project, principal)
    return await plot_service.check_overdue_foreshadowing(
        project_id=project_id,
        current_chapter_no=current_chapter_no,
        current_volume_no=current_volume_no,
        include_optional=include_optional,
        limit=limit,
    )


@mcp.tool(name="foreshadowing.link")
async def foreshadowing_link(
    workspace: str,
    project: str,
    key: str,
    parent_key: str | None = None,
    related_keys: list[str] | None = None,
    trigger_on_payoff_keys: list[str] | None = None,
    blocks_payoff_until_keys: list[str] | None = None,
    replace: bool = False,
) -> dict[str, Any]:
    """建立伏笔间的关联关系。设置父子、触发、阻塞等依赖关系。"""
    principal = await get_principal("write")
    logger.info("foreshadowing_link called")
    validate_required(locals(), "workspace", "project", "key")
    project_id = await auth.resolve_project_id(workspace, project, principal, access="write")
    return await plot_service.link_foreshadowing(
        project_id=project_id,
        key=key,
        parent_key=parent_key,
        related_keys=related_keys,
        trigger_on_payoff_keys=trigger_on_payoff_keys,
        blocks_payoff_until_keys=blocks_payoff_until_keys,
        replace=replace,
    )


@mcp.tool(name="foreshadowing.payoff")
async def foreshadowing_payoff(
    workspace: str,
    project: str,
    key: str,
    payoff_chapter_no: int | None = None,
    payoff_chapter_id: str | None = None,
    payoff_note: str | None = None,
    status: str = "paid_off",
    trigger_related: bool = True,
    metadata: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """回收伏笔。标记伏笔已兑现，可触发关联伏笔的连锁回收。"""
    principal = await get_principal("write")
    logger.info("foreshadowing_payoff called")
    validate_required(locals(), "workspace", "project", "key")
    project_id = await auth.resolve_project_id(workspace, project, principal, access="write")
    return await plot_service.payoff_foreshadowing(
        project_id=project_id,
        key=key,
        payoff_chapter_no=payoff_chapter_no,
        payoff_chapter_id=payoff_chapter_id,
        payoff_note=payoff_note,
        status=status,
        trigger_related=trigger_related,
        metadata=metadata or {},
    )


@mcp.tool(name="plot.create_chapter_plan")
async def plot_create_chapter_plan(
    workspace: str,
    project: str,
    chapter_no: int,
    plan: dict[str, Any],
) -> dict[str, Any]:
    """创建章节大纲计划。定义章节的目标、场景和情节推进要点。"""
    principal = await get_principal("write")
    logger.info("plot_create_chapter_plan called")
    validate_required(locals(), "chapter_no", "plan")
    project_id = await auth.resolve_project_id(workspace, project, principal, access="write")
    return await plot_service.create_chapter_plan(
        project_id=project_id,
        chapter_no=chapter_no,
        plan=plan,
        username=principal.username,
    )


@mcp.tool(name="plot.list_chapter_plans")
async def plot_list_chapter_plans(
    workspace: str,
    project: str,
    status: str | None = None,
    limit: int = 100,
) -> list[dict[str, Any]]:
    """列出章节计划。可按状态过滤，返回所有已创建的大纲计划。"""
    principal = await get_principal("read")
    logger.info("plot_list_chapter_plans called")
    validate_required(locals(), "workspace", "project")
    project_id = await auth.resolve_project_id(workspace, project, principal)
    return await plot_service.list_chapter_plans(project_id=project_id, status=status, limit=limit)
