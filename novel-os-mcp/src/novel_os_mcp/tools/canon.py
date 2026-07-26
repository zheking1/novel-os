from typing import Any
import logging

from ..mcp_core import mcp
from ..deps import db, auth, canon_service, rules_service, compliance_service
from ..tool_auth import get_principal, validate_required, validate_length

logger = logging.getLogger("novel_os_mcp.tools.canon")


@mcp.tool(name="canon.doc.upsert")
async def canon_doc_upsert(
    workspace: str,
    project: str,
    doc_type: str,
    key: str,
    title: str,
    content: str,
    status: str = "active",
    scope: dict[str, Any] | None = None,
    review_status: str = "approved",
    source_type: str = "manual",
    source_id: str | None = None,
    related_rule_ids: list[str] | None = None,
    metadata: dict[str, Any] | None = None,
    change_reason: str | None = None,
) -> dict[str, Any]:
    """创建或更新设定文档。按 doc_type 分类存储，支持版本历史和变更追踪。"""
    principal = await get_principal("write")
    logger.info("canon_doc_upsert called")
    validate_required(locals(), "title", "content")
    validate_length(locals(), {"title": 200, "content": 50000})
    project_id = await auth.resolve_project_id(workspace, project, principal, access="write")
    return await canon_service.upsert_document(
        project_id=project_id,
        doc_type=doc_type,
        key=key,
        title=title,
        content=content,
        username=principal.username,
        status=status,
        scope=scope or {},
        review_status=review_status,
        source_type=source_type,
        source_id=source_id,
        related_rule_ids=related_rule_ids or [],
        metadata=metadata or {},
        change_reason=change_reason,
    )


@mcp.tool(name="canon.doc.list")
async def canon_doc_list(
    workspace: str,
    project: str,
    doc_types: list[str] | None = None,
    statuses: list[str] | None = None,
    review_status: str | None = None,
    query: str | None = None,
    limit: int = 100,
    offset: int = 0,
) -> list[dict[str, Any]]:
    """列出设定文档。支持按类型、状态、审核状态过滤和全文搜索。"""
    principal = await get_principal("read")
    logger.info("canon_doc_list called")
    validate_required(locals(), "workspace", "project")
    project_id = await auth.resolve_project_id(workspace, project, principal)
    return await canon_service.list_documents(
        project_id=project_id,
        doc_types=doc_types,
        statuses=statuses,
        review_status=review_status,
        query=query,
        limit=limit,
        offset=offset,
    )


@mcp.tool(name="canon.doc.get")
async def canon_doc_get(
    workspace: str,
    project: str,
    document_id: str | None = None,
    doc_type: str | None = None,
    key: str | None = None,
) -> dict[str, Any]:
    """获取单个设定文档。可通过 document_id 或 doc_type+key 组合定位。"""
    principal = await get_principal("read")
    logger.info("canon_doc_get called")
    validate_required(locals(), "workspace", "project")
    project_id = await auth.resolve_project_id(workspace, project, principal)
    return await canon_service.get_document(
        project_id=project_id,
        document_id=document_id,
        doc_type=doc_type,
        key=key,
    )


@mcp.tool(name="canon.doc.archive")
async def canon_doc_archive(
    workspace: str,
    project: str,
    document_id: str | None = None,
    doc_type: str | None = None,
    key: str | None = None,
    reason: str | None = None,
) -> dict[str, Any]:
    """归档设定文档。归档后文档不再生效，但保留历史记录可恢复。"""
    principal = await get_principal("write")
    logger.info("canon_doc_archive called")
    validate_required(locals(), "workspace", "project")
    project_id = await auth.resolve_project_id(workspace, project, principal, access="write")
    return await canon_service.archive_document(
        project_id=project_id,
        username=principal.username,
        document_id=document_id,
        doc_type=doc_type,
        key=key,
        reason=reason,
    )


@mcp.tool(name="canon.doc.history")
async def canon_doc_history(
    workspace: str,
    project: str,
    document_id: str | None = None,
    doc_type: str | None = None,
    key: str | None = None,
    limit: int = 50,
) -> list[dict[str, Any]]:
    """查看文档版本历史。返回指定文档的所有历史版本，支持分页。"""
    principal = await get_principal("read")
    logger.info("canon_doc_history called")
    validate_required(locals(), "workspace", "project")
    project_id = await auth.resolve_project_id(workspace, project, principal)
    return await canon_service.list_document_versions(
        project_id=project_id,
        document_id=document_id,
        doc_type=doc_type,
        key=key,
        limit=limit,
    )


@mcp.tool(name="canon.doc.restore")
async def canon_doc_restore(
    workspace: str,
    project: str,
    version: int,
    document_id: str | None = None,
    doc_type: str | None = None,
    key: str | None = None,
    reason: str | None = None,
) -> dict[str, Any]:
    """恢复文档到指定版本。创建新版本记录，内容回滚到目标版本。"""
    principal = await get_principal("write")
    logger.info("canon_doc_restore called")
    validate_required(locals(), "workspace", "project")
    project_id = await auth.resolve_project_id(workspace, project, principal, access="write")
    return await canon_service.restore_document(
        project_id=project_id,
        version=version,
        username=principal.username,
        document_id=document_id,
        doc_type=doc_type,
        key=key,
        reason=reason,
    )


@mcp.tool(name="rules.list")
async def rules_list(
    workspace: str,
    project: str,
    rule_types: list[str] | None = None,
    status: str | None = "active",
    chapter_no: int | None = None,
    volume_no: int | None = None,
) -> list[dict[str, Any]]:
    """列出创作规则。支持按类型、状态、章节、卷号过滤。传 status=null 返回所有状态。"""
    principal = await get_principal("read")
    logger.info("rules_list called")
    validate_required(locals(), "workspace", "project")
    project_id = await auth.resolve_project_id(workspace, project, principal)
    return await rules_service.list_rules(
        project_id=project_id,
        rule_types=rule_types,
        status=status,
        chapter_no=chapter_no,
        volume_no=volume_no,
    )


@mcp.tool(name="rules.list_effective")
async def rules_list_effective(
    workspace: str,
    project: str,
    rule_types: list[str] | None = None,
    chapter_no: int | None = None,
    volume_no: int | None = None,
    scope_refs: list[str] | None = None,
    scope_types: list[str] | None = None,
    active_event_keys: list[str] | None = None,
    include_blocked: bool = False,
) -> dict[str, Any]:
    """查询当前生效的规则。根据章节、卷号、作用域和活跃事件计算生效规则集。"""
    principal = await get_principal("read")
    logger.info("rules_list_effective called")
    validate_required(locals(), "workspace", "project")
    project_id = await auth.resolve_project_id(workspace, project, principal)
    return await rules_service.list_effective_rules(
        project_id=project_id,
        rule_types=rule_types,
        chapter_no=chapter_no,
        volume_no=volume_no,
        scope_refs=scope_refs,
        scope_types=scope_types,
        active_event_keys=active_event_keys,
        include_blocked=include_blocked,
    )


@mcp.tool(name="rules.check_conflict")
async def rules_check_conflict(
    workspace: str,
    project: str,
    rule_types: list[str] | None = None,
    chapter_no: int | None = None,
    volume_no: int | None = None,
    scope_refs: list[str] | None = None,
    scope_types: list[str] | None = None,
    active_event_keys: list[str] | None = None,
    text: str | None = None,
) -> dict[str, Any]:
    """检查规则冲突。分析当前规则集是否存在矛盾，可选传入文本做合规检测。"""
    principal = await get_principal("read")
    logger.info("rules_check_conflict called")
    validate_required(locals(), "workspace", "project")
    project_id = await auth.resolve_project_id(workspace, project, principal)
    return await rules_service.check_conflicts(
        project_id=project_id,
        rule_types=rule_types,
        chapter_no=chapter_no,
        volume_no=volume_no,
        scope_refs=scope_refs,
        scope_types=scope_types,
        active_event_keys=active_event_keys,
        text=text,
    )


@mcp.tool(name="rules.propose")
async def rules_propose(
    workspace: str,
    project: str,
    title: str,
    content: str,
    proposal_type: str = "create",
    source_type: str = "user",
    confidence: float | None = None,
    agreement: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """提交规则提案。支持创建/修改/删除类型，需经审批后生效。"""
    principal = await get_principal("write")
    logger.info("rules_propose called")
    validate_required(locals(), "title", "content")
    project_id = await auth.resolve_project_id(workspace, project, principal, access="write")
    return await rules_service.propose_rule(
        project_id=project_id,
        proposal={
            "title": title,
            "content": content,
            "proposal_type": proposal_type,
            "source_type": source_type,
            "confidence": confidence,
            "agreement": agreement or {},
        },
        username=principal.username,
    )


@mcp.tool(name="rules.upsert")
async def rules_upsert(
    workspace: str,
    project: str,
    rule_key: str,
    rule_type: str,
    title: str,
    content: str,
    scope: str = "global",
    severity: str = "warning",
    status: str = "active",
    metadata: dict[str, Any] | None = None,
    change_reason: str | None = None,
    source: str = "manual",
    scope_type: str = "global",
    scope_ref: str | None = None,
    scope_config: dict[str, Any] | None = None,
    priority: int = 100,
    effective_chapter_no: int | None = None,
    expire_chapter_no: int | None = None,
    effective_volume_no: int | None = None,
    expire_volume_no: int | None = None,
    is_temporary: bool = False,
    active_from_event: str | None = None,
    expire_on_event: str | None = None,
    conflict_policy: str = "priority",
    supersedes_rule_ids: list[str] | None = None,
    blocked_by_rule_ids: list[str] | None = None,
) -> dict[str, Any]:
    """创建或更新创作规则。支持作用域、优先级、有效期和冲突策略配置。"""
    principal = await get_principal("write")
    logger.info("rules_upsert called")
    validate_required(locals(), "rule_type", "title", "content")
    project_id = await auth.resolve_project_id(workspace, project, principal, access="write")
    return await rules_service.upsert_rule(
        project_id=project_id,
        rule_key=rule_key,
        rule_type=rule_type,
        title=title,
        content=content,
        scope=scope,
        severity=severity,
        status=status,
        metadata=metadata or {},
        change_reason=change_reason,
        source=source,
        scope_type=scope_type,
        scope_ref=scope_ref,
        scope_config=scope_config or {},
        priority=priority,
        effective_chapter_no=effective_chapter_no,
        expire_chapter_no=expire_chapter_no,
        effective_volume_no=effective_volume_no,
        expire_volume_no=expire_volume_no,
        is_temporary=is_temporary,
        active_from_event=active_from_event,
        expire_on_event=expire_on_event,
        conflict_policy=conflict_policy,
        supersedes_rule_ids=supersedes_rule_ids or [],
        blocked_by_rule_ids=blocked_by_rule_ids or [],
    )


@mcp.tool(name="rules.bulk_toggle")
async def rules_bulk_toggle(
    workspace: str,
    project: str,
    status: str,
    rule_keys: list[str] | None = None,
    rule_ids: list[str] | None = None,
    rule_types: list[str] | None = None,
    reason: str | None = None,
) -> list[dict[str, Any]]:
    """批量切换规则状态。可按 key、id 或类型批量启用/禁用规则。"""
    principal = await get_principal("write")
    logger.info("rules_bulk_toggle called")
    validate_required(locals(), "workspace", "project", "status")
    project_id = await auth.resolve_project_id(workspace, project, principal, access="write")
    return await rules_service.bulk_toggle_rules(
        project_id=project_id,
        status=status,
        rule_keys=rule_keys,
        rule_ids=rule_ids,
        rule_types=rule_types,
        reason=reason,
    )


@mcp.tool(name="rules.resolve_conflict")
async def rules_resolve_conflict(
    workspace: str,
    project: str,
    action: str,
    source_rule_key: str | None = None,
    source_rule_id: str | None = None,
    target_rule_keys: list[str] | None = None,
    target_rule_ids: list[str] | None = None,
    priority: int | None = None,
    reason: str | None = None,
) -> dict[str, Any]:
    """解决规则冲突。action 支持 suppress/merge/override，手动处理矛盾规则。"""
    principal = await get_principal("write")
    logger.info("rules_resolve_conflict called")
    validate_required(locals(), "workspace", "project", "action")
    project_id = await auth.resolve_project_id(workspace, project, principal, access="write")
    return await rules_service.resolve_conflict(
        project_id=project_id,
        action=action,
        source_rule_key=source_rule_key,
        source_rule_id=source_rule_id,
        target_rule_keys=target_rule_keys,
        target_rule_ids=target_rule_ids,
        priority=priority,
        reason=reason,
    )


@mcp.tool(name="rules.list_proposals")
async def rules_list_proposals(
    workspace: str,
    project: str,
    status: str | None = "proposed",
    limit: int = 100,
) -> list[dict[str, Any]]:
    """列出规则提案。默认显示待审批提案，可按状态过滤。"""
    principal = await get_principal("read")
    logger.info("rules_list_proposals called")
    validate_required(locals(), "workspace", "project")
    project_id = await auth.resolve_project_id(workspace, project, principal)
    return await rules_service.list_rule_proposals(project_id=project_id, status=status, limit=limit)


@mcp.tool(name="rules.apply_proposal")
async def rules_apply_proposal(
    workspace: str,
    project: str,
    proposal_id: str,
    decision: str,
    reason: str | None = None,
) -> dict[str, Any]:
    """审批规则提案。decision 支持 approve/reject，通过后自动执行提案操作。"""
    principal = await get_principal("write")
    logger.info("rules_apply_proposal called")
    validate_required(locals(), "workspace", "project", "proposal_id", "decision")
    project_id = await auth.resolve_project_id(workspace, project, principal, access="write")
    return await rules_service.apply_proposal(
        project_id=project_id,
        proposal_id=proposal_id,
        decision=decision,
        reason=reason,
        username=principal.username,
    )


@mcp.tool(name="rules.delete")
async def rules_delete(
    workspace: str,
    project: str,
    rule_key: str | None = None,
    rule_id: str | None = None,
) -> dict[str, Any]:
    """物理删除创作规则。支持按 rule_key 或 rule_id 删除。"""
    principal = await get_principal("write")
    logger.info("rules_delete called")
    validate_required(locals(), "workspace", "project")
    if not rule_key and not rule_id:
        raise ValueError("rule_key or rule_id is required")
    project_id = await auth.resolve_project_id(workspace, project, principal, access="write")
    return await rules_service.delete_rule(
        project_id=project_id,
        rule_key=rule_key,
        rule_id=rule_id,
    )


@mcp.tool(name="compliance.rule.upsert")
async def compliance_rule_upsert(
    workspace: str,
    project: str,
    rule_key: str,
    title: str,
    content: str,
    category: str = "custom",
    patterns: list[str] | None = None,
    match_type: str = "keyword",
    severity: str = "critical",
    status: str = "active",
    scope_type: str = "global",
    scope_ref: str | None = None,
    priority: int = 5,
    case_sensitive: bool = False,
    hint: str | None = None,
    metadata: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """创建或更新合规检查规则。支持关键词/正则匹配，用于文本合规性检测。"""
    principal = await get_principal("write")
    logger.info("compliance_rule_upsert called")
    validate_required(locals(), "workspace", "project", "rule_key", "title", "content")
    validate_length(locals(), {"title": 200, "content": 50000})
    project_id = await auth.resolve_project_id(workspace, project, principal, access="write")
    return await compliance_service.upsert_rule(
        project_id=project_id,
        rule_key=rule_key,
        title=title,
        content=content,
        category=category,
        patterns=patterns or [],
        match_type=match_type,
        severity=severity,
        status=status,
        scope_type=scope_type,
        scope_ref=scope_ref,
        priority=priority,
        case_sensitive=case_sensitive,
        hint=hint,
        metadata=metadata or {},
        username=principal.username,
    )


@mcp.tool(name="compliance.rule.list")
async def compliance_rule_list(
    workspace: str,
    project: str,
    status: str = "active",
    categories: list[str] | None = None,
    chapter_no: int | None = None,
    volume_no: int | None = None,
) -> dict[str, Any]:
    """列出合规规则。支持按状态、分类、章节、卷号过滤。"""
    principal = await get_principal("read")
    logger.info("compliance_rule_list called")
    validate_required(locals(), "workspace", "project")
    project_id = await auth.resolve_project_id(workspace, project, principal)
    return await compliance_service.list_rules(
        project_id=project_id,
        status=status,
        categories=categories or [],
        chapter_no=chapter_no,
        volume_no=volume_no,
    )


@mcp.tool(name="compliance.rule.delete")
async def compliance_rule_delete(
    workspace: str,
    project: str,
    rule_key: str,
) -> dict:
    """删除（软删除）合规检查规则"""
    principal = await get_principal("write")
    logger.info("compliance_rule_delete called")
    validate_required(locals(), "workspace", "project", "rule_key")
    project_id = await auth.resolve_project_id(workspace, project, principal, access="write")
    result = await rules_service.delete_rule(project_id=project_id, rule_key=rule_key)
    return {"ok": True, "rule_key": rule_key, "title": result.get("title")}


@mcp.tool(name="compliance.check")
async def compliance_check(
    workspace: str,
    project: str,
    text: str | None = None,
    content_items: list[dict[str, Any]] | None = None,
    chapter_no: int | None = None,
    volume_no: int | None = None,
    scope_refs: list[str] | None = None,
    scope_types: list[str] | None = None,
    review_job_id: str | None = None,
    create_revision_task: bool = False,
) -> dict[str, Any]:
    """执行合规检查。检测文本或内容项是否违反合规规则，可创建修订任务。"""
    principal = await get_principal(None)
    logger.info("compliance_check called")
    validate_required(locals(), "workspace", "project")
    if create_revision_task or review_job_id:
        principal.require("write")
        project_id = await auth.resolve_project_id(workspace, project, principal, access="write")
    else:
        principal.require("read")
        project_id = await auth.resolve_project_id(workspace, project, principal)
    return await compliance_service.check(
        project_id=project_id,
        text=text,
        content_items=content_items or [],
        chapter_no=chapter_no,
        volume_no=volume_no,
        scope_refs=scope_refs or [],
        scope_types=scope_types or [],
        review_job_id=review_job_id,
        create_revision_task=create_revision_task,
        username=principal.username,
    )
