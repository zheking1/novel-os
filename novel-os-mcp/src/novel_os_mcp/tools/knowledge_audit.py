"""Knowledge Audit Tools — 多模型知识审计与辩论 MCP 入口"""
import logging
from typing import Any

from ..mcp_core import mcp
from ..tool_auth import get_principal, validate_required
from ..deps import db, auth, llm_client

logger = logging.getLogger("novel_os_mcp.tools.knowledge_audit")


@mcp.tool(name="knowledge.audit_all")
async def knowledge_audit_all(
    workspace: str,
    project: str,
    mode: str | None = None,
) -> dict[str, Any]:
    """审计所有知识分类，生成进化提案（等待辩论委员会裁决）。

    Args:
        workspace: 工作区
        project: 项目
        mode: 审计模式，None=新增+优化, "add"=只新增, "optimize"=只优化

    Returns:
        {total_proposals, categories: {name: {proposals, models_used}}}
    """
    principal = await get_principal("write")
    logger.info("knowledge.audit_all called, mode=%s", mode)
    validate_required(locals(), "workspace", "project")
    if mode is not None and mode not in ("add", "optimize"):
        raise ValueError("mode must be None, 'add', or 'optimize'")
    project_id = await auth.resolve_project_id(workspace, project, principal, access="write")

    from ..services.knowledge_audit import KnowledgeAuditService
    svc = KnowledgeAuditService(db, llm_client)
    result = await svc.audit_all(project_id, mode=mode)

    # Save proposals
    all_proposals = result.get("_proposals", [])

    save_result = await svc.save_proposals(project_id, all_proposals)

    mode_label = {"add": "新增", "optimize": "优化", None: "新增+优化"}
    return {
        "ok": True,
        "mode": mode,
        "total_categories": len(result.get("categories", {})),
        "total_proposals": save_result["saved"],
        "categories": {k: {"proposals": v.get("proposals", 0) if isinstance(v, dict) else 0, "models_used": v.get("models_used", []) if isinstance(v, dict) else []} for k, v in result.get("categories", {}).items()},
        "message": f"{mode_label[mode]}审计完成，共 {save_result['saved']} 条提案待辩论委员会裁决",
    }


@mcp.tool(name="knowledge.audit_status")
async def knowledge_audit_status(
    workspace: str,
    project: str,
) -> dict[str, Any]:
    """查看审计进度和结果统计。

    Returns:
        {total_proposals, pending_review, applied, rejected}
    """
    principal = await get_principal("read")
    logger.info("knowledge.audit_status called")
    validate_required(locals(), "workspace", "project")
    project_id = await auth.resolve_project_id(workspace, project, principal)

    rows = await db.fetch(
        """SELECT status, count(*) as cnt
           FROM system_evolution_proposals
           WHERE source_project_id=$1
           GROUP BY status""",
        project_id,
    )
    counts = {r["status"]: r["cnt"] for r in rows}
    return {
        "total": sum(counts.values()),
        "pending_review": counts.get("pending_review", 0),
        "applied": counts.get("applied", 0),
        "rejected": counts.get("rejected", 0),
    }


@mcp.tool(name="knowledge.council_debate_all")
async def knowledge_council_debate_all(
    workspace: str,
    project: str,
) -> dict[str, Any]:
    """对所有 pending_review 提案发起辩论委员会裁决。

    Returns:
        {total, approved, rejected, errors}
    """
    principal = await get_principal("write")
    logger.info("knowledge.council_debate_all called")
    validate_required(locals(), "workspace", "project")
    project_id = await auth.resolve_project_id(workspace, project, principal, access="write")

    from ..services.knowledge_council import KnowledgeCouncilService
    svc = KnowledgeCouncilService(db, llm_client)
    result = await svc.debate_all(project_id)

    return {
        "ok": True,
        "total": result["total"],
        "approved": result["approved"],
        "rejected": result["rejected"],
        "errors": result["errors"],
        "message": f"辩论完成：{result['approved']} 条通过，{result['rejected']} 条拒绝",
    }