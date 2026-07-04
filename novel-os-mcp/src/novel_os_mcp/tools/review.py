from typing import Any
import logging

from ..mcp_core import mcp
from ..deps import db, auth, review_service
from ..tool_auth import get_principal, validate_required

logger = logging.getLogger("novel_os_mcp.tools.review")


@mcp.tool(name="review.start_job")
async def review_start_job(
    workspace: str,
    project: str,
    chapter_no: int,
    local_files: list[dict[str, Any]],
    dimensions: list[str],
) -> dict[str, Any]:
    """启动审核任务。指定章节文件和审核维度，创建多模型并行审核任务。"""
    principal = await get_principal("write")
    logger.info("review_start_job called")
    validate_required(locals(), "workspace", "project", "chapter_no", "local_files", "dimensions")
    project_id = await auth.resolve_project_id(workspace, project, principal, access="write")
    return await review_service.start_job(
        project_id=project_id,
        chapter_no=chapter_no,
        local_files=local_files,
        dimensions=dimensions,
        username=principal.username,
    )


@mcp.tool(name="review.upsert_council_config")
async def review_upsert_council_config(
    workspace: str,
    project: str,
    name: str,
    config: dict[str, Any],
    is_active: bool = False,
) -> dict[str, Any]:
    """创建或更新审核委员会配置。定义参与审核的模型及其角色。"""
    principal = await get_principal("write")
    logger.info("review_upsert_council_config called")
    validate_required(locals(), "workspace", "project", "name", "config")
    project_id = await auth.resolve_project_id(workspace, project, principal, access="write")
    return await review_service.upsert_council_config(
        project_id=project_id,
        name=name,
        config=config,
        is_active=is_active,
    )


@mcp.tool(name="review.list_council_configs")
async def review_list_council_configs(workspace: str, project: str) -> list[dict[str, Any]]:
    """列出审核委员会配置。返回项目下所有已定义的委员会配置。"""
    principal = await get_principal("read")
    logger.info("review_list_council_configs called")
    validate_required(locals(), "workspace", "project")
    project_id = await auth.resolve_project_id(workspace, project, principal)
    return await review_service.list_council_configs(project_id=project_id)


@mcp.tool(name="review.council.dispatch")
async def review_council_dispatch(
    workspace: str,
    project: str,
    review_job_id: str,
) -> dict[str, Any]:
    """获取活跃委员会配置中的待审核模型，用于并行分发。"""
    principal = await get_principal("read")
    logger.info("review_council_dispatch called")
    validate_required(locals(), "workspace", "project", "review_job_id")
    project_id = await auth.resolve_project_id(workspace, project, principal)
    return await review_service.get_council_dispatch(
        project_id=project_id,
        review_job_id=review_job_id,
    )


@mcp.tool(name="review.submit_model_report")
async def review_submit_model_report(
    workspace: str,
    project: str,
    review_job_id: str,
    model_id: str,
    score: float | None,
    summary: str,
    findings: list[dict[str, Any]],
    local_report_file: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """提交模型审核报告。模型完成审核后提交评分、摘要和发现列表。"""
    principal = await get_principal("write")
    logger.info("review_submit_model_report called")
    validate_required(locals(), "workspace", "project", "review_job_id", "model_id", "summary", "findings")
    project_id = await auth.resolve_project_id(workspace, project, principal, access="write")
    return await review_service.submit_model_report(
        project_id=project_id,
        review_job_id=review_job_id,
        model_id=model_id,
        score=score,
        summary=summary,
        findings=findings,
        local_report_file=local_report_file,
    )


@mcp.tool(name="review.list_revision_tasks")
async def review_list_revision_tasks(
    workspace: str,
    project: str,
    status: str | None = "open",
    severity: list[str] | None = None,
    limit: int = 100,
) -> list[dict[str, Any]]:
    """列出修订任务。可按状态和严重程度过滤，返回待处理的修订任务。"""
    principal = await get_principal("read")
    logger.info("review_list_revision_tasks called")
    validate_required(locals(), "workspace", "project")
    project_id = await auth.resolve_project_id(workspace, project, principal)
    return await review_service.list_revision_tasks(
        project_id=project_id,
        status=status,
        severity=severity,
        limit=limit,
    )


@mcp.tool(name="review.update_revision_task")
async def review_update_revision_task(
    workspace: str,
    project: str,
    task_id: str,
    status: str | None = None,
    metadata_patch: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """更新修订任务状态。标记任务为进行中/已完成，或更新元数据。"""
    principal = await get_principal("write")
    logger.info("review_update_revision_task called")
    validate_required(locals(), "workspace", "project", "task_id")
    project_id = await auth.resolve_project_id(workspace, project, principal, access="write")
    return await review_service.update_revision_task(
        project_id=project_id,
        task_id=task_id,
        status=status,
        metadata_patch=metadata_patch or {},
    )


@mcp.tool(name="review.aggregate")
async def review_aggregate(
    workspace: str,
    project: str,
    review_job_id: str,
    create_revision_tasks: bool = True,
) -> dict[str, Any]:
    """汇总审核结果。合并多个模型的审核报告，生成综合评分和修订建议。"""
    principal = await get_principal("write")
    logger.info("review_aggregate called")
    validate_required(locals(), "workspace", "project", "review_job_id")
    project_id = await auth.resolve_project_id(workspace, project, principal, access="write")
    return await review_service.aggregate(
        project_id=project_id,
        review_job_id=review_job_id,
        create_revision_tasks=create_revision_tasks,
    )


@mcp.tool(name="review.extract_rule_proposals")
async def review_extract_rule_proposals(
    workspace: str,
    project: str,
    review_job_id: str,
    create_proposals: bool = True,
    min_confidence: float = 0.0,
) -> dict[str, Any]:
    """从审核结果中提取规则提案。分析审核发现，自动生成创作规则建议。"""
    principal = await get_principal("write")
    logger.info("review_extract_rule_proposals called")
    validate_required(locals(), "workspace", "project", "review_job_id")
    project_id = await auth.resolve_project_id(workspace, project, principal, access="write")
    return await review_service.extract_rule_proposals(
        project_id=project_id,
        review_job_id=review_job_id,
        username=principal.username,
        create_proposals=create_proposals,
        min_confidence=min_confidence,
    )


@mcp.tool(name="review.extract_state_updates")
async def review_extract_state_updates(
    workspace: str,
    project: str,
    review_job_id: str,
) -> dict[str, Any]:
    """从审核结果中提取状态更新建议。识别需要更新的实体状态变化。"""
    principal = await get_principal("read")
    logger.info("review_extract_state_updates called")
    validate_required(locals(), "workspace", "project", "review_job_id")
    project_id = await auth.resolve_project_id(workspace, project, principal)
    return await review_service.extract_state_updates(project_id=project_id, review_job_id=review_job_id)


@mcp.tool(name="review.extract_foreshadowing_updates")
async def review_extract_foreshadowing_updates(
    workspace: str,
    project: str,
    review_job_id: str,
) -> dict[str, Any]:
    """从审核结果中提取伏笔更新建议。识别需要回收或新建的伏笔。"""
    principal = await get_principal("read")
    logger.info("review_extract_foreshadowing_updates called")
    validate_required(locals(), "workspace", "project", "review_job_id")
    project_id = await auth.resolve_project_id(workspace, project, principal)
    return await review_service.extract_foreshadowing_updates(project_id=project_id, review_job_id=review_job_id)


@mcp.tool(name="review.evaluate_model_quality")
async def review_evaluate_model_quality(
    workspace: str,
    project: str,
    review_job_id: str | None = None,
) -> dict[str, Any]:
    """评估模型审核质量。分析审核报告的准确性和一致性，输出质量评分。"""
    principal = await get_principal("read")
    logger.info("review_evaluate_model_quality called")
    validate_required(locals(), "workspace", "project")
    project_id = await auth.resolve_project_id(workspace, project, principal)
    return await review_service.evaluate_model_quality(project_id=project_id, review_job_id=review_job_id)
