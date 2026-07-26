from typing import Any
import logging

from ..mcp_core import mcp
from ..deps import db, auth, review_service
from ..tool_auth import get_principal, validate_required
from ..utils import json_dumps, ensure_json_value

logger = logging.getLogger("novel_os_mcp.tools.review")


@mcp.tool(name="review.start_job")
async def review_start_job(
    workspace: str,
    project: str,
    chapter_no: int,
    dimensions: list[str],
    local_files: list[dict[str, Any]] | None = None,
) -> dict[str, Any]:
    """启动审核任务。指定章节文件和审核维度，创建多模型并行审核任务。local_files 为空时自动从 local chapter 获取。"""
    principal = await get_principal("write")
    logger.info("review_start_job called")
    validate_required(locals(), "workspace", "project", "chapter_no", "dimensions")
    project_id = await auth.resolve_project_id(workspace, project, principal, access="write")
    # 自动注入 AI 痕迹检测维度（所有审核员都需检查）
    if "ai_detection" not in dimensions:
        dimensions = dimensions + ["ai_detection"]
    result = await review_service.start_job(
        project_id=project_id,
        chapter_no=chapter_no,
        local_files=local_files or [],
        dimensions=dimensions,
        username=principal.username,
    )
    result["workflow_guide"] = {
        "phase": "章节审核",
        "next_tool": "review.submit_model_report",
        "description": f"审核任务已创建。等待各模型提交审核报告。所有报告提交后调用 review.aggregate 汇总",
        "workflow": [
            {"step": 1, "tool": "review.start_job", "status": "done", "desc": "创建审核任务"},
            {"step": 2, "tool": "review.submit_model_report", "status": "pending", "desc": "各模型提交审核报告"},
            {"step": 3, "tool": "review.aggregate", "status": "pending", "desc": "汇总审核结果"},
            {"step": 4, "tool": "review.submit_evolution_proposals", "status": "pending", "desc": "提取进化提案"},
            {"step": 5, "tool": "workflow.learn_from_review", "status": "pending", "desc": "从审核结果学习"},
        ],
    }
    return result


@mcp.tool(name="review.upsert_council_config")
async def review_upsert_council_config(
    name: str = "默认审核委员会",
    config: dict[str, Any] = {},
    is_active: bool = False,
) -> dict[str, Any]:
    """创建或更新审核委员会配置。每个用户独立配置。"""
    principal = await get_principal("write")
    logger.info("review_upsert_council_config called")
    validate_required(locals(), "name", "config")
    return await review_service.upsert_council_config(
        user_id=principal.username,
        name=name,
        config=config,
        is_active=is_active,
    )


@mcp.tool(name="review.list_council_configs")
async def review_list_council_configs() -> list[dict[str, Any]]:
    """列出当前用户的审核委员会配置。用户级别。"""
    principal = await get_principal("read")
    logger.info("review_list_council_configs called")
    return await review_service.list_council_configs(user_id=principal.username)


@mcp.tool(name="review.council.dispatch")
async def review_council_dispatch(
    review_job_id: str,
) -> dict[str, Any]:
    """获取活跃委员会配置中的待审核模型，用于并行分发。"""
    principal = await get_principal("read")
    logger.info("review_council_dispatch called")
    validate_required(locals(), "review_job_id")
    return await review_service.get_council_dispatch(
        username=principal.username,
        review_job_id=review_job_id,
    )


@mcp.tool(name="review.submit_model_report")
async def review_submit_model_report(
    workspace: str,
    project: str,
    review_job_id: str,
    model_id: str,
    content: str | None = None,
    score: float | None = None,
    summary: str | None = None,
    findings: list[dict[str, Any]] | None = None,
    local_report_file: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """提交章节正文给模型审核，或直接提交审核报告。

    传入 content 时，系统会自动调用该模型的 LLM 结合上下文进行审核。
    不传 content 时，直接存储传入的 score/summary/findings。

    Args:
        workspace: 工作区
        project: 项目
        review_job_id: 审核任务 ID（来自 start_job）
        model_id: 模型 key（来自 council_dispatch）
        content: 章节正文。传入后系统会自动拉取前文摘要、角色状态等上下文，调用 LLM 审核
        score: 审核评分（0-100，不传 content 时必填）
        summary: 审核摘要（不传 content 时必填）
        findings: 发现问题列表（不传 content 时必填）
        local_report_file: 本地报告文件信息（可选）
    """
    principal = await get_principal("write")
    logger.info("review_submit_model_report called: model=%s, has_content=%s", model_id, bool(content))
    validate_required(locals(), "workspace", "project", "review_job_id", "model_id")
    project_id = await auth.resolve_project_id(workspace, project, principal, access="write")
    return await review_service.submit_model_report(
        project_id=project_id,
        review_job_id=review_job_id,
        model_id=model_id,
        content=content,
        score=score,
        summary=summary,
        findings=findings or [],
        local_report_file=local_report_file,
    )


@mcp.tool(name="review.list_revision_tasks")
async def review_list_revision_tasks(
    workspace: str,
    project: str,
    status: str | None = None,
    severity: list[str] | None = None,
    limit: int = 100,
    offset: int = 0,
    task_id: str | None = None,
) -> list[dict[str, Any]]:
    """列出审核任务（review_jobs）。支持按状态过滤。status=null 返回全部。"""
    principal = await get_principal("read")
    logger.info("review_list_revision_tasks called")
    validate_required(locals(), "workspace", "project")
    project_id = await auth.resolve_project_id(workspace, project, principal)
    return await review_service.list_revision_tasks(
        project_id=project_id,
        status=status,
        severity=severity,
        limit=limit,
        offset=offset,
        task_id=task_id,
    )


@mcp.tool(name="review.list_jobs")
async def review_list_jobs(
    workspace: str,
    project: str,
    status: str | None = None,
    limit: int = 50,
) -> list[dict[str, Any]]:
    """列出审核任务（review_jobs）。支持按状态过滤。"""
    principal = await get_principal("read")
    logger.info("review_list_jobs called")
    validate_required(locals(), "workspace", "project")
    project_id = await auth.resolve_project_id(workspace, project, principal)
    from ..services.review import ReviewService
    svc = ReviewService(db)
    return await svc.list_jobs(
        project_id=project_id,
        status=status,
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
    result = await review_service.aggregate(
        project_id=project_id,
        review_job_id=review_job_id,
        create_revision_tasks=create_revision_tasks,
    )
    result["workflow_guide"] = {
        "phase": "章节审核",
        "review_round": 1,
        "max_rounds": 3,
        "next_tool": "workflow.submit_chapter_commit",
        "description": "审核完成。如果还有 findings 需要修改，修订正文后重新调用 review.start_job（最多3轮）。审核通过后，调 pipeline.generate(task_type='polish', content=正文) 用系统润色模型润色，然后 submit_chapter_commit 提交。",
        "loop_instruction": "如果 aggregate 结果中有 severity>=warning 的 findings → 修订正文 → 再次 review.start_job。无意见或达到第3轮 → 润色 → 提交",
        "next_steps": [
            {"tool": "review.start_job", "condition": "有 findings 需要修改", "desc": "修订后重新审核（最多3轮）"},
            {"tool": "pipeline.generate", "condition": "审核通过", "desc": "用系统 polish 模型润色正文"},
            {"tool": "workflow.submit_chapter_commit", "condition": "润色完成", "desc": "提交章节"},
        ],
        "workflow": [
            {"step": 1, "tool": "review.start_job", "status": "done", "desc": "创建审核任务"},
            {"step": 2, "tool": "review.submit_model_report", "status": "done", "desc": "各模型提交审核报告"},
            {"step": 3, "tool": "review.aggregate", "status": "done", "desc": "汇总审核结果"},
            {"step": 4, "tool": "[修订正文 | 润色]", "status": "pending", "desc": "有意见→修订→重新审核；通过→润色"},
            {"step": 5, "tool": "workflow.submit_chapter_commit", "status": "pending", "desc": "提交章节"},
        ],
    }
    return result


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


@mcp.tool(name="review.submit_evolution_proposals")
async def review_submit_evolution_proposals(
    workspace: str,
    project: str,
    review_job_id: str,
    auto_submit: bool = True,
) -> dict[str, Any]:
    """从审核结果中自动提取可进化的发现，提交为系统进化提案。
    
    AI模型在审核中发现的问题（如风格偏移、角色OOC、节奏问题等），
    可以被自动提取并转为系统知识进化提案，提交管理审评。
    管理员审批通过后，这些知识会补充到系统知识库，使系统持续进化。
    
    Args:
        workspace: 工作区
        project: 项目
        review_job_id: 审核任务ID
        auto_submit: 是否自动提交为进化提案（默认 true）
        
    Returns:
        提交结果，包含提取到的提案列表
    """
    principal = await get_principal("write")
    logger.info("review_submit_evolution_proposals called")
    validate_required(locals(), "workspace", "project", "review_job_id")
    project_id = await auth.resolve_project_id(workspace, project, principal, access="write")

    # Get reports and extract findings
    reports = await db.fetch(
        "SELECT * FROM review_reports WHERE review_job_id = $1", review_job_id
    )
    all_findings = []
    for r in reports:
        findings = ensure_json_value(r['findings']) if isinstance(r.get('findings'), str) else (r.get('findings') or [])
        if isinstance(findings, list):
            all_findings.extend(findings)

    if not all_findings:
        return {"ok": True, "submitted": 0, "proposals": [], "message": "无可提取的进化内容"}

    # Extract evolution proposals
    proposals = await review_service._extract_evolution_from_findings(
        project_id=project_id,
        review_job_id=review_job_id,
        findings=all_findings,
    )

    if not proposals:
        return {"ok": True, "submitted": 0, "proposals": [], "message": "未发现需要进化的内容"}

    # Auto-submit or return for review
    submitted = 0
    if auto_submit:
        result = await review_service.submit_evolution_proposals_from_review(
            project_id=project_id,
            review_job_id=review_job_id,
            findings=all_findings,
        )
        submitted = result["submitted"]

        if submitted > 0:
            # Notify admins
            try:
                project_row = await db.fetchrow(
                    "SELECT title FROM projects WHERE id = $1", project_id
                )
                project_title = project_row["title"] if project_row else project
                await db.execute(
                    """
                    INSERT INTO system_notifications (type, title, content, is_global)
                    VALUES ($1, $2, $3, true)
                    """,
                    "ai_review_completed",
                    f"审查自动进化提案",
                    f"审查任务 {review_job_id[:8]} 自动提交了 {submitted} 个进化提案",
                )
            except Exception as e:
                logger.warning("Failed to create notification: %s", e)

    result = {
        "ok": True,
        "submitted": submitted,
        "total_extracted": len(proposals),
        "proposals": proposals,
        "message": f"成功提取 {len(proposals)} 个进化提案{'，已自动提交 ' + str(submitted) if submitted else '，等待确认'}",
    }
    result["workflow_guide"] = {
        "phase": "章节审核",
        "next_tool": "workflow.learn_from_review",
        "description": "进化提案已提交。下一步调用 workflow.learn_from_review 从审核结果创建修订任务和规则提案",
        "workflow": [
            {"step": 1, "tool": "review.start_job", "status": "done", "desc": "创建审核任务"},
            {"step": 2, "tool": "review.submit_model_report", "status": "done", "desc": "各模型提交审核报告"},
            {"step": 3, "tool": "review.aggregate", "status": "done", "desc": "汇总审核结果"},
            {"step": 4, "tool": "review.submit_evolution_proposals", "status": "done", "desc": "提取进化提案"},
            {"step": 5, "tool": "workflow.learn_from_review", "status": "pending", "desc": "从审核结果学习"},
        ],
    }
    return result
