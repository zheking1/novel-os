"""上下文缓存服务 - Redis 缓存实现"""

import json
from typing import Any

import redis.asyncio as redis

from .config import Settings


class CacheService:
    """Redis 缓存服务 - 实现上下文缓存"""

    # 缓存键前缀
    PREFIX_CANON = "canon:"           # Canon 摘要
    PREFIX_ENTITY_STATE = "entity:"   # 实体状态
    PREFIX_CHAPTER_SUMMARY = "chapter:"  # 章节摘要
    PREFIX_RULES = "rules:"           # 规则摘要
    PREFIX_CONTEXT = "ctx:"           # 完整上下文包
    PREFIX_INDEX = "idx:"             # 缓存索引

    # 默认 TTL（秒）
    DEFAULT_TTL = 3600  # 1 小时
    MAX_TTL = 86400     # 24 小时

    def __init__(self, settings: Settings):
        self._settings = settings
        self._client: redis.Redis | None = None

    @property
    def client(self) -> redis.Redis:
        if self._client is None:
            self._client = redis.Redis(
                host=self._settings.redis_host,
                port=self._settings.redis_port,
                db=self._settings.redis_db,
                password=self._settings.redis_password,
                decode_responses=True,
            )
        return self._client

    async def ping(self) -> bool:
        """检查 Redis 连接"""
        try:
            await self.client.ping()
            return True
        except Exception:
            return False

    # ==========================================================================
    # 缓存键生成
    # ==========================================================================

    def _make_key(self, prefix: str, project_id: str, *parts: str) -> str:
        """生成缓存键"""
        return f"{prefix}{project_id}:{' '.join(parts)}"

    def canon_key(self, project_id: str, canon_id: str) -> str:
        """Canon 缓存键"""
        return self._make_key(self.PREFIX_CANON, project_id, canon_id)

    def entity_state_key(self, project_id: str, entity_id: str) -> str:
        """实体状态缓存键"""
        return self._make_key(self.PREFIX_ENTITY_STATE, project_id, entity_id)

    def chapter_summary_key(self, project_id: str, chapter_no: int) -> str:
        """章节摘要缓存键"""
        return self._make_key(self.PREFIX_CHAPTER_SUMMARY, project_id, str(chapter_no))

    def rules_key(self, project_id: str, scope: str = "effective") -> str:
        """规则缓存键"""
        return self._make_key(self.PREFIX_RULES, project_id, scope)

    def context_key(self, project_id: str, chapter_no: int, profile: str, pov: str) -> str:
        """完整上下文包缓存键"""
        return self._make_key(self.PREFIX_CONTEXT, project_id, str(chapter_no), profile, pov)

    def index_key(self, project_id: str) -> str:
        """缓存索引键"""
        return f"{self.PREFIX_INDEX}{project_id}"

    # ==========================================================================
    # Canon 摘要缓存
    # ==========================================================================

    async def get_canon_summary(self, project_id: str, canon_id: str) -> dict[str, Any] | None:
        """获取 Canon 摘要"""
        key = self.canon_key(project_id, canon_id)
        data = await self.client.get(key)
        if data:
            return json.loads(data)
        return None

    async def set_canon_summary(
        self,
        project_id: str,
        canon_id: str,
        summary: dict[str, Any],
        ttl: int | None = None,
    ) -> None:
        """设置 Canon 摘要"""
        key = self.canon_key(project_id, canon_id)
        await self.client.setex(key, ttl or self.DEFAULT_TTL, json.dumps(summary))
        await self._update_index(project_id, key)

    async def invalidate_canon(self, project_id: str, canon_id: str) -> None:
        """使 Canon 缓存失效"""
        key = self.canon_key(project_id, canon_id)
        await self.client.delete(key)
        await self._remove_from_index(project_id, key)

    # ==========================================================================
    # 实体状态缓存
    # ==========================================================================

    async def get_entity_state(self, project_id: str, entity_id: str) -> dict[str, Any] | None:
        """获取实体状态"""
        key = self.entity_state_key(project_id, entity_id)
        data = await self.client.get(key)
        if data:
            return json.loads(data)
        return None

    async def set_entity_state(
        self,
        project_id: str,
        entity_id: str,
        state: dict[str, Any],
        ttl: int | None = None,
    ) -> None:
        """设置实体状态"""
        key = self.entity_state_key(project_id, entity_id)
        await self.client.setex(key, ttl or self.DEFAULT_TTL, json.dumps(state))
        await self._update_index(project_id, key)

    async def invalidate_entity(self, project_id: str, entity_id: str) -> None:
        """使实体状态缓存失效"""
        key = self.entity_state_key(project_id, entity_id)
        await self.client.delete(key)
        await self._remove_from_index(project_id, key)

    # ==========================================================================
    # 章节摘要缓存
    # ==========================================================================

    async def get_chapter_summary(self, project_id: str, chapter_no: int) -> dict[str, Any] | None:
        """获取章节摘要"""
        key = self.chapter_summary_key(project_id, chapter_no)
        data = await self.client.get(key)
        if data:
            return json.loads(data)
        return None

    async def set_chapter_summary(
        self,
        project_id: str,
        chapter_no: int,
        summary: dict[str, Any],
        ttl: int | None = None,
    ) -> None:
        """设置章节摘要"""
        key = self.chapter_summary_key(project_id, chapter_no)
        await self.client.setex(key, ttl or self.DEFAULT_TTL, json.dumps(summary))
        await self._update_index(project_id, key)

    async def invalidate_chapter(self, project_id: str, chapter_no: int) -> None:
        """使章节摘要缓存失效"""
        key = self.chapter_summary_key(project_id, chapter_no)
        await self.client.delete(key)
        await self._remove_from_index(project_id, key)

    # ==========================================================================
    # 规则缓存
    # ==========================================================================

    async def get_rules_summary(self, project_id: str, scope: str = "effective") -> list[dict[str, Any]] | None:
        """获取规则摘要"""
        key = self.rules_key(project_id, scope)
        data = await self.client.get(key)
        if data:
            return json.loads(data)
        return None

    async def set_rules_summary(
        self,
        project_id: str,
        scope: str,
        rules: list[dict[str, Any]],
        ttl: int | None = None,
    ) -> None:
        """设置规则摘要"""
        key = self.rules_key(project_id, scope)
        await self.client.setex(key, ttl or self.DEFAULT_TTL, json.dumps(rules))
        await self._update_index(project_id, key)

    async def invalidate_rules(self, project_id: str) -> None:
        """使规则缓存失效"""
        # 删除所有 scope 的规则缓存
        pattern = f"{self.PREFIX_RULES}{project_id}:*"
        keys = []
        async for key in self.client.scan_iter(match=pattern):
            keys.append(key)
        if keys:
            await self.client.delete(*keys)
        # 清理索引
        await self._cleanup_index(project_id, pattern)

    # ==========================================================================
    # 完整上下文包缓存
    # ==========================================================================

    async def get_context_pack(
        self,
        project_id: str,
        chapter_no: int,
        profile: str,
        pov: str,
    ) -> dict[str, Any] | None:
        """获取完整上下文包"""
        key = self.context_key(project_id, chapter_no, profile, pov)
        data = await self.client.get(key)
        if data:
            return json.loads(data)
        return None

    async def set_context_pack(
        self,
        project_id: str,
        chapter_no: int,
        profile: str,
        pov: str,
        context: dict[str, Any],
        ttl: int | None = None,
    ) -> None:
        """设置完整上下文包"""
        key = self.context_key(project_id, chapter_no, profile, pov)
        await self.client.setex(key, ttl or self.MAX_TTL, json.dumps(context))
        await self._update_index(project_id, key)

    async def invalidate_context_pack(
        self,
        project_id: str,
        chapter_no: int | None = None,
    ) -> None:
        """使上下文包缓存失效"""
        if chapter_no is not None:
            # 删除特定章节的所有 profile/pov 组合
            pattern = f"{self.PREFIX_CONTEXT}{project_id}:{chapter_no}:*"
            keys = []
            async for key in self.client.scan_iter(match=pattern):
                keys.append(key)
            if keys:
                await self.client.delete(*keys)
            await self._cleanup_index(project_id, pattern)
        else:
            # 删除该项目的所有上下文包
            pattern = f"{self.PREFIX_CONTEXT}{project_id}:*"
            keys = []
            async for key in self.client.scan_iter(match=pattern):
                keys.append(key)
            if keys:
                await self.client.delete(*keys)
            await self._cleanup_index(project_id, pattern)

    # ==========================================================================
    # 批量失效
    # ==========================================================================

    async def invalidate_on_canon_update(self, project_id: str, canon_id: str) -> None:
        """Canon 更新时失效相关缓存"""
        await self.invalidate_canon(project_id, canon_id)
        # Canon 更新可能影响上下文包
        await self.invalidate_context_pack(project_id)

    async def invalidate_on_rules_update(self, project_id: str) -> None:
        """规则更新时失效相关缓存"""
        await self.invalidate_rules(project_id)
        # 规则更新影响上下文包
        await self.invalidate_context_pack(project_id)

    async def invalidate_on_final_commit(self, project_id: str, chapter_no: int) -> None:
        """Final commit 时失效相关缓存"""
        await self.invalidate_chapter(project_id, chapter_no)
        await self.invalidate_context_pack(project_id, chapter_no)

    async def invalidate_on_foreshadowing_update(self, project_id: str) -> None:
        """伏笔状态更新时失效相关缓存"""
        await self.invalidate_context_pack(project_id)

    # ==========================================================================
    # 缓存索引管理
    # ==========================================================================

    async def _update_index(self, project_id: str, key: str) -> None:
        """更新缓存索引"""
        index_key = self.index_key(project_id)
        await self.client.sadd(index_key, key)

    async def _remove_from_index(self, project_id: str, key: str) -> None:
        """从索引中移除"""
        index_key = self.index_key(project_id)
        await self.client.srem(index_key, key)

    async def _cleanup_index(self, project_id: str, pattern: str) -> None:
        """清理索引中已删除的键"""
        index_key = self.index_key(project_id)
        keys = []
        async for key in self.client.scan_iter(match=pattern):
            keys.append(key)
        if keys:
            await self.client.srem(index_key, *keys)

    async def get_project_cache_keys(self, project_id: str) -> list[str]:
        """获取项目所有缓存键"""
        index_key = self.index_key(project_id)
        return list(await self.client.smembers(index_key))

    async def get_cache_stats(self, project_id: str) -> dict[str, Any]:
        """获取缓存统计"""
        index_key = self.index_key(project_id)
        keys = list(await self.client.smembers(index_key))

        canon_count = 0
        entity_count = 0
        chapter_count = 0
        rules_count = 0
        context_count = 0
        other_count = 0

        for key in keys:
            if key.startswith(self.PREFIX_CANON):
                canon_count += 1
            elif key.startswith(self.PREFIX_ENTITY_STATE):
                entity_count += 1
            elif key.startswith(self.PREFIX_CHAPTER_SUMMARY):
                chapter_count += 1
            elif key.startswith(self.PREFIX_RULES):
                rules_count += 1
            elif key.startswith(self.PREFIX_CONTEXT):
                context_count += 1
            else:
                other_count += 1

        # 验证键是否存在
        valid_keys = []
        expired_keys = []
        for key in keys:
            if await self.client.exists(key):
                valid_keys.append(key)
            else:
                expired_keys.append(key)

        # 清理过期键
        if expired_keys:
            await self.client.srem(index_key, *expired_keys)

        return {
            "project_id": project_id,
            "total_keys": len(valid_keys),
            "by_type": {
                "canon": canon_count,
                "entity": entity_count,
                "chapter": chapter_count,
                "rules": rules_count,
                "context": context_count,
                "other": other_count,
            },
            "expired_cleaned": len(expired_keys),
        }

    # ==========================================================================
    # 缓存预热
    # ==========================================================================

    async def warm_context_cache(
        self,
        project_id: str,
        chapter_nos: list[int],
        profiles: list[str],
        povs: list[str],
    ) -> dict[str, int]:
        """预热上下文缓存 - 返回成功预热的数量"""
        warmed = 0
        for chapter_no in chapter_nos:
            for profile in profiles:
                for pov in povs:
                    key = self.context_key(project_id, chapter_no, profile, pov)
                    # 检查是否已缓存
                    if not await self.client.exists(key):
                        warmed += 1
                        # 标记为需要延迟加载
                        await self.client.setex(
                            f"{key}:pending",
                            300,  # 5 分钟标记过期
                            "1",
                        )
        return {"warmed": warmed, "total": len(chapter_nos) * len(profiles) * len(povs)}

    # ==========================================================================
    # 清除所有缓存
    # ==========================================================================

    async def clear_project_cache(self, project_id: str) -> int:
        """清除项目所有缓存，返回清除的键数量"""
        pattern = f"*:{project_id}:*"
        keys = []
        async for key in self.client.scan_iter(match=pattern):
            keys.append(key)

        if keys:
            await self.client.delete(*keys)

        # 清除索引
        index_key = self.index_key(project_id)
        await self.client.delete(index_key)

        return len(keys)
