import logging
from typing import Any

from ..mcp_core import mcp
from ..deps import db, auth, gatekeeper_service
from ..tool_auth import get_principal, validate_required

logger = logging.getLogger("novel_os_mcp.tools.evolution")


@mcp.tool(name="evolution.logs")
async def evolution_logs(
    source_type: str | None = None,
    risk_level: str | None = None,
    target_table: str | None = None,
    limit: int = 50,
) -> list[dict[str, Any]]:
    """列出进化日志。管理员看全部，用户只看自己的。"""
    principal = await get_principal("read")
    logger.info("evolution_logs called")
    is_admin = "admin" in principal.scopes
    created_by = None if is_admin else principal.username
    return await gatekeeper_service.list_logs(
        source_type=source_type, risk_level=risk_level,
        target_table=target_table, created_by=created_by, limit=limit,
    )


@mcp.tool(name="evolution.rollback")
async def evolution_rollback(
    log_id: str,
) -> dict[str, Any]:
    """管理员回滚指定进化记录。"""
    principal = await get_principal("write")
    if "admin" not in principal.scopes:
        return {"ok": False, "error": "仅管理员可回滚"}
    logger.info("evolution_rollback called: %s", log_id)
    validate_required(locals(), "log_id")
    return await gatekeeper_service.rollback(log_id=log_id)


@mcp.tool(name="evolution.stats")
async def evolution_stats() -> dict[str, Any]:
    """进化统计：按来源类型/风险级别/目标表的分布。"""
    principal = await get_principal("read")
    logger.info("evolution_stats called")
    rows = await db.fetch(
        """SELECT source_type, risk_level, target_table, COUNT(*) as cnt
           FROM evolution_logs GROUP BY source_type, risk_level, target_table
           ORDER BY source_type, risk_level"""
    )
    return {
        "ok": True,
        "stats": [
            {"source_type": r["source_type"], "risk_level": r["risk_level"],
             "target_table": r["target_table"], "count": r["cnt"]}
            for r in rows
        ],
    }