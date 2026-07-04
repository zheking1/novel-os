from typing import Any
import logging

from ..mcp_core import mcp
from ..config import get_settings
from ..tool_auth import get_principal

settings = get_settings()
logger = logging.getLogger("novel_os_mcp.tools.admin")


@mcp.tool(name="admin.health")
async def admin_health() -> dict[str, Any]:
    """系统健康检查。验证数据库连接状态，返回核心服务配置信息，用于监控和诊断。"""
    principal = await get_principal("read")
    logger.info("admin_health called")
    db_ok = await db.fetchrow("SELECT 1 AS ok")
    return {
        "status": "ok",
        "database": bool(db_ok and db_ok["ok"] == 1),
        "qdrant_url": settings.qdrant_url,
        "redis_host": settings.redis_host,
    }
