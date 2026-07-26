import logging
from typing import Any

from ..mcp_core import mcp
from ..deps import db, auth, rules_service
from ..tool_auth import get_principal, validate_required

logger = logging.getLogger("novel_os_mcp.tools.global_rules")


@mcp.tool(name="global_rules.list")
async def global_rules_list(
    rule_type: str | None = None,
    status: str = "active",
    limit: int = 100,
) -> list[dict[str, Any]]:
    """列出全局规则。可按类型（creative/compliance）筛选。"""
    principal = await get_principal("read")
    logger.info("global_rules_list called")
    return await rules_service.list_global_rules(
        rule_type=rule_type, status=status, limit=limit
    )


@mcp.tool(name="global_rules.upsert")
async def global_rules_upsert(
    rule_key: str,
    rule_type: str,
    title: str,
    content: str,
    severity: str = "warning",
    status: str = "active",
    metadata: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """创建或更新全局规则。rule_type: creative / compliance。"""
    principal = await get_principal("write")
    logger.info("global_rules_upsert called: %s", rule_key)
    validate_required(locals(), "rule_key", "rule_type", "title", "content")
    if rule_type not in ("creative", "compliance", "polish"):
        return {"ok": False, "error": "rule_type must be 'creative', 'compliance', or 'polish'"}
    return await rules_service.upsert_global_rule(
        rule_key=rule_key, rule_type=rule_type, title=title, content=content,
        severity=severity, status=status, metadata=metadata,
    )


@mcp.tool(name="global_rules.delete")
async def global_rules_delete(
    rule_key: str,
) -> dict[str, Any]:
    """删除全局规则（软删除为 inactive）。"""
    principal = await get_principal("write")
    logger.info("global_rules_delete called: %s", rule_key)
    validate_required(locals(), "rule_key")
    return await rules_service.delete_global_rule(rule_key=rule_key)


@mcp.tool(name="global_rules.promote")
async def global_rules_promote(
    workspace: str,
    project: str,
    rule_key: str,
) -> dict[str, Any]:
    """将项目规则提升为全局规则，同时标记项目规则已升级。"""
    principal = await get_principal("write")
    project_id = await auth.resolve_project_id(workspace, project, principal, access="write")
    logger.info("global_rules_promote called: %s/%s → %s", workspace, project, rule_key)
    validate_required(locals(), "rule_key")
    return await rules_service.promote_to_global(
        project_id=project_id, rule_key=rule_key,
        promoted_by=principal.username,
    )
