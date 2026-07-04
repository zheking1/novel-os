"""依赖降级服务 - Qdrant/Redis 降级方案"""

import logging
from typing import Any

from .config import Settings

logger = logging.getLogger("novel_os_mcp")


class DependencyHealthService:
    """依赖健康检查与降级服务"""

    def __init__(self, settings: Settings):
        self._settings = settings

    async def check_qdrant_health(self) -> dict[str, Any]:
        """检查 Qdrant 健康状态"""
        try:
            import httpx
            async with httpx.AsyncClient(timeout=5.0) as client:
                response = await client.get(f"{self._settings.qdrant_url}/health")
                if response.status_code == 200:
                    return {"healthy": True, "url": self._settings.qdrant_url, "status": "operational"}
                return {"healthy": False, "url": self._settings.qdrant_url, "status": f"http_{response.status_code}"}
        except Exception as exc:
            logger.warning(f"Qdrant health check failed: {exc}")
            return {"healthy": False, "url": self._settings.qdrant_url, "error": str(exc)}

    async def check_redis_health(self) -> dict[str, Any]:
        """检查 Redis 健康状态"""
        try:
            import redis.asyncio as redis
            client = redis.Redis(
                host=self._settings.redis_host,
                port=self._settings.redis_port,
                db=self._settings.redis_db,
                password=self._settings.redis_password,
                socket_timeout=5.0,
            )
            await client.ping()
            await client.aclose()
            return {"healthy": True, "url": self._settings.redis_url, "status": "operational"}
        except Exception as exc:
            logger.warning(f"Redis health check failed: {exc}")
            return {"healthy": False, "url": self._settings.redis_url, "error": str(exc)}

    async def check_database_health(self) -> dict[str, Any]:
        """检查数据库健康状态"""
        try:
            from ..db import Database
            db = Database(self._settings)
            await db.connect()
            result = await db.fetchrow("SELECT 1 as health")
            await db.close()
            return {"healthy": True, "status": "operational"}
        except Exception as exc:
            logger.warning(f"Database health check failed: {exc}")
            return {"healthy": False, "error": str(exc)}

    async def get_all_health(self) -> dict[str, Any]:
        """获取所有依赖健康状态"""
        qdrant = await self.check_qdrant_health()
        redis = await self.check_redis_health()
        db = await self.check_database_health()

        all_healthy = qdrant["healthy"] and redis["healthy"] and db["healthy"]

        return {
            "healthy": all_healthy,
            "qdrant": qdrant,
            "redis": redis,
            "database": db,
            "degradation_mode": not all_healthy,
        }

    def get_degradation_plan(self, failed_services: list[str]) -> dict[str, Any]:
        """获取降级方案"""
        plan = {
            "degradation_level": 0,
            "available_services": [],
            "degraded_services": [],
            "actions": [],
        }

        if "qdrant" in failed_services:
            plan["degraded_services"].append("qdrant")
            plan["actions"].append({
                "service": "qdrant",
                "action": "fallback_to_pg_fulltext",
                "description": "使用 PostgreSQL 全文检索替代向量搜索",
            })

        if "redis" in failed_services:
            plan["degraded_services"].append("redis")
            plan["actions"].append({
                "service": "redis",
                "action": "fallback_to_memory_cache",
                "description": "使用进程内内存缓存替代 Redis",
            })

        plan["degradation_level"] = len(plan["degraded_services"])
        plan["available_services"] = [s for s in ["qdrant", "redis", "database"] if s not in failed_services]

        return plan


class DegradationModeService:
    """降级模式服务 - 管理降级状态"""

    # 降级级别
    LEVEL_NORMAL = 0      # 全部正常
    LEVEL_REDIS_DEGRADED = 1    # Redis 降级
    LEVEL_QDRANT_DEGRADED = 2   # Qdrant 降级
    LEVEL_BOTH_DEGRADED = 3     # 两者都降级
    LEVEL_CRITICAL = 4          # 严重降级

    def __init__(self, settings: Settings):
        self._settings = settings
        self._health_service = DependencyHealthService(settings)
        self._current_level = self.LEVEL_NORMAL
        self._degraded_services: set[str] = set()

    @property
    def current_level(self) -> int:
        return self._current_level

    @property
    def degraded_services(self) -> set[str]:
        return self._degraded_services.copy()

    async def update_status(self) -> dict[str, Any]:
        """更新降级状态"""
        health = await self._health_service.get_all_health()

        self._degraded_services = set()
        if not health["qdrant"]["healthy"]:
            self._degraded_services.add("qdrant")
        if not health["redis"]["healthy"]:
            self._degraded_services.add("redis")
        if not health["database"]["healthy"]:
            self._degraded_services.add("database")

        # 计算降级级别
        if "database" in self._degraded_services:
            self._current_level = self.LEVEL_CRITICAL
        elif "qdrant" in self._degraded_services and "redis" in self._degraded_services:
            self._current_level = self.LEVEL_BOTH_DEGRADED
        elif "qdrant" in self._degraded_services:
            self._current_level = self.LEVEL_QDRANT_DEGRADED
        elif "redis" in self._degraded_services:
            self._current_level = self.LEVEL_REDIS_DEGRADED
        else:
            self._current_level = self.LEVEL_NORMAL

        return {
            "level": self._current_level,
            "degraded_services": list(self._degraded_services),
            "health": health,
            "can_continue": self._current_level < self.LEVEL_CRITICAL,
        }

    def is_qdrant_degraded(self) -> bool:
        return "qdrant" in self._degraded_services

    def is_redis_degraded(self) -> bool:
        return "redis" in self._degraded_services

    def is_database_degraded(self) -> bool:
        return "database" in self._degraded_services

    def get_fallback_strategy(self, feature: str) -> str:
        """获取功能降级策略"""
        strategies = {
            # 向量搜索降级到全文检索
            "vector_search": "pg_fulltext_search" if self.is_qdrant_degraded() else "qdrant",
            # 缓存降级到内存
            "cache": "memory_cache" if self.is_redis_degraded() else "redis",
            # 数据库只读
            "database_write": "readonly" if self.is_database_degraded() else "readwrite",
        }
        return strategies.get(feature, "unavailable")
