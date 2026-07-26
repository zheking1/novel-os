from typing import Any
import logging

from ..mcp_core import mcp
from ..config import get_settings
from ..deps import db
from ..tool_auth import get_principal

settings = get_settings()
logger = logging.getLogger("novel_os_mcp.tools.admin")


@mcp.tool(name="admin.health")
async def admin_health() -> dict[str, Any]:
    """系统健康检查。验证数据库连接状态，返回核心服务配置信息，用于监控和诊断。"""
    import time
    start = time.time()
    principal = await get_principal("read")
    logger.info("admin_health called")

    def _ok(v: Any) -> str:
        return "ok" if v else "error"

    # Database check
    db_ok = False
    try:
        row = await db.fetchrow("SELECT 1 AS ok")
        db_ok = bool(row and row["ok"] == 1)
    except Exception as e:
        logger.warning("health db check failed: %s", e)

    # Redis check
    redis_ok = False
    try:
        from redis.asyncio import Redis as AsyncRedis
        rc = AsyncRedis.from_url(settings.redis_url, socket_connect_timeout=2)
        await rc.ping()
        await rc.aclose()
        redis_ok = True
    except Exception as e:
        logger.warning("health redis check failed: %s", e)

    # Qdrant check
    qdrant_ok = False
    try:
        import httpx
        headers = {}
        if settings.qdrant_api_key:
            headers["Authorization"] = f"Bearer {settings.qdrant_api_key}"
        async with httpx.AsyncClient(timeout=3) as client:
            r = await client.get(f"{settings.qdrant_url}/healthz", headers=headers)
            qdrant_ok = r.status_code == 200
    except Exception as e:
        logger.warning("health qdrant check failed: %s", e)

    latency_ms = round((time.time() - start) * 1000)
    return {
        "status": _ok(db_ok and redis_ok and qdrant_ok),
        "healthy": db_ok and redis_ok and qdrant_ok,
        "database": _ok(db_ok),
        "db_connected": db_ok,
        "mcp": "ok",
        "mcp_connected": True,
        "qdrant": _ok(qdrant_ok),
        "redis": _ok(redis_ok),
        "qdrant_url": settings.qdrant_url,
        "redis_host": settings.redis_host,
        "latency": latency_ms,
    }
