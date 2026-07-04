from typing import Any
import logging

from ..mcp_core import mcp
from ..deps import db, auth, context_service, workflow_service, context_weight_service, review_service
from ..tool_auth import get_principal, validate_required, validate_length

logger = logging.getLogger("novel_os_mcp.tools.context")


@mcp.tool(name="workflow.prepare_chapter_context")
async def workflow_prepare_chapter_context(
    workspace: str,
    project: str,
    chapter_no: int,
    purpose: str = "draft",
    focus: list[str] | None = None,
    budget: dict[str, Any] | None = None,
    volume_no: int | None = None,
    scope_refs: list[str] | None = None,
    scope_types: list[str] | None = None,
    active_event_keys: list[str] | None = None,
    pov_mode: str = "omniscient",
    pass_number: int | None = None,
    previous_context: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """准备章节上下文。pass_number: 1=大纲 2=初稿 3=润色 4=验证。previous_context 用于增量加载。"""
    principal = await get_principal("read")
    logger.info("workflow_prepare_chapter_context called")
    validate_required(locals(), "chapter_no")
    project_id = await auth.resolve_project_id(workspace, project, principal)
    return await context_service.prepare_chapter_context(
        project_id=project_id,
        chapter_no=chapter_no,
        purpose=purpose,
        focus=focus or [],
        budget=budget or {},
        volume_no=volume_no,
        scope_refs=scope_refs,
        scope_types=scope_types,
        active_event_keys=active_event_keys,
        pov_mode=pov_mode,
        pass_number=pass_number,
        previous_context=previous_context,
    )


@mcp.tool(name="workflow.validate_context_pack")
async def workflow_validate_context_pack(
    workspace: str,
    project: str,
    context_pack_id: str | None = None,
    chapter_no: int | None = None,
) -> dict[str, Any]:
    """验证上下文包完整性。检查上下文包的数据质量和一致性。"""
    principal = await get_principal("read")
    logger.info("workflow_validate_context_pack called")
    validate_required(locals(), "workspace", "project")
    project_id = await auth.resolve_project_id(workspace, project, principal)
    return await context_service.validate_context_pack(
        project_id=project_id,
        context_pack_id=context_pack_id,
        chapter_no=chapter_no,
    )


@mcp.tool(name="context.list_packs")
async def context_list_packs(
    workspace: str,
    project: str,
    chapter_no: int | None = None,
    purpose: str | None = None,
    limit: int = 50,
) -> list[dict[str, Any]]:
    """列出上下文包。可按章节和用途过滤，返回已生成的上下文包列表。"""
    principal = await get_principal("read")
    logger.info("context_list_packs called")
    validate_required(locals(), "workspace", "project")
    project_id = await auth.resolve_project_id(workspace, project, principal)
    return await context_service.list_context_packs(
        project_id=project_id,
        chapter_no=chapter_no,
        purpose=purpose,
        limit=limit,
    )


@mcp.tool(name="context.get_pack")
async def context_get_pack(
    workspace: str,
    project: str,
    context_pack_id: str | None = None,
    chapter_no: int | None = None,
) -> dict[str, Any]:
    """获取上下文包详情。可通过 ID 或章节号定位上下文包。"""
    principal = await get_principal("read")
    logger.info("context_get_pack called")
    validate_required(locals(), "workspace", "project")
    project_id = await auth.resolve_project_id(workspace, project, principal)
    return await context_service.get_context_pack(
        project_id=project_id,
        context_pack_id=context_pack_id,
        chapter_no=chapter_no,
    )


@mcp.tool(name="workflow.preflight_generation")
async def workflow_preflight_generation(
    workspace: str,
    project: str,
    chapter_no: int,
    purpose: str = "draft",
    focus: list[str] | None = None,
    budget: dict[str, Any] | None = None,
    volume_no: int | None = None,
    scope_refs: list[str] | None = None,
    scope_types: list[str] | None = None,
    active_event_keys: list[str] | None = None,
    pov_mode: str = "omniscient",
) -> dict[str, Any]:
    """生成前预检。验证生成条件、预算和上下文完整性，返回预检报告。"""
    principal = await get_principal("read")
    logger.info("workflow_preflight_generation called")
    validate_required(locals(), "workspace", "project", "chapter_no")
    project_id = await auth.resolve_project_id(workspace, project, principal)
    return await context_service.preflight_generation(
        project_id=project_id,
        chapter_no=chapter_no,
        purpose=purpose,
        focus=focus or [],
        budget=budget or {},
        volume_no=volume_no,
        scope_refs=scope_refs,
        scope_types=scope_types,
        active_event_keys=active_event_keys,
        pov_mode=pov_mode,
    )


@mcp.tool(name="workflow.prepare_segment_context")
async def workflow_prepare_segment_context(
    workspace: str,
    project: str,
    chapter_no: int,
    segment: str,
    purpose: str = "draft",
    focus: list[str] | None = None,
    budget: dict[str, Any] | None = None,
    volume_no: int | None = None,
    scope_refs: list[str] | None = None,
    scope_types: list[str] | None = None,
    active_event_keys: list[str] | None = None,
    pov_mode: str = "omniscient",
) -> dict[str, Any]:
    """为章节片段准备上下文。按 segment 分段生成上下文，支持细粒度控制。"""
    principal = await get_principal("read")
    logger.info("workflow_prepare_segment_context called")
    validate_required(locals(), "workspace", "project", "chapter_no", "segment")
    project_id = await auth.resolve_project_id(workspace, project, principal)
    return await context_service.prepare_segment_context(
        project_id=project_id,
        chapter_no=chapter_no,
        segment=segment,
        purpose=purpose,
        focus=focus or [],
        budget=budget or {},
        volume_no=volume_no,
        scope_refs=scope_refs,
        scope_types=scope_types,
        active_event_keys=active_event_keys,
        pov_mode=pov_mode,
    )


@mcp.tool(name="workflow.submit_chapter_commit")
async def workflow_submit_chapter_commit(
    workspace: str,
    project: str,
    chapter_no: int,
    title: str | None,
    local_files: list[dict[str, Any]],
    commit: dict[str, Any],
    accept: bool = True,
) -> dict[str, Any]:
    """提交章节完成确认。将本地文件变更同步到远程项目，标记章节进度。"""
    principal = await get_principal("write")
    logger.info("workflow_submit_chapter_commit called")
    validate_required(locals(), "workspace", "project")
    project_id = await auth.resolve_project_id(workspace, project, principal, access="write")
    return await workflow_service.submit_chapter_commit(
        project_id=project_id,
        chapter_no=chapter_no,
        title=title,
        local_files=local_files,
        commit=commit,
        accept=accept,
        username=principal.username,
    )


@mcp.tool(name="workflow.list_audit_logs")
async def workflow_list_audit_logs(
    workspace: str,
    project: str,
    action: str | None = None,
    resource_type: str | None = None,
    limit: int = 50,
) -> list[dict[str, Any]]:
    """列出操作审计日志。可按操作类型和资源类型过滤。"""
    principal = await get_principal("read")
    logger.info("workflow_list_audit_logs called")
    validate_required(locals(), "workspace", "project")
    project_id = await auth.resolve_project_id(workspace, project, principal)
    return await workflow_service.list_audit_logs(
        project_id=project_id,
        action=action,
        resource_type=resource_type,
        limit=limit,
    )


@mcp.tool(name="workflow.validate_content")
async def workflow_validate_content(
    workspace: str,
    project: str,
    chapter_no: int,
    content: str,
) -> dict[str, Any]:
    """校验生成内容。检查禁词违规、角色存活、设定一致性和知识库一致性。"""
    principal = await get_principal("write")
    logger.info("workflow_validate_content called")
    validate_required(locals(), "workspace", "project", "chapter_no", "content")
    validate_length(locals(), {"content": 50000})
    project_id = await auth.resolve_project_id(workspace, project, principal, access="write")
    return await workflow_service.validate_generated_content(
        project_id=project_id,
        chapter_no=chapter_no,
        content=content,
    )


@mcp.tool(name="workflow.learn_from_review")
async def workflow_learn_from_review(
    workspace: str,
    project: str,
    review_job_id: str,
    create_revision_tasks: bool = True,
    create_rule_proposals: bool = True,
    block_on_critical: bool = True,
) -> dict[str, Any]:
    """从审核结果中学习。自动创建修订任务和规则提案，提升后续生成质量。"""
    principal = await get_principal("write")
    logger.info("workflow_learn_from_review called")
    validate_required(locals(), "workspace", "project", "review_job_id")
    project_id = await auth.resolve_project_id(workspace, project, principal, access="write")
    return await review_service.learn_from_review(
        project_id=project_id,
        review_job_id=review_job_id,
        username=principal.username,
        create_revision_tasks=create_revision_tasks,
        create_rule_proposals=create_rule_proposals,
        block_on_critical=block_on_critical,
    )
