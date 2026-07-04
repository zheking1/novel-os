"""性能优化服务 - 批量操作、查询优化、请求合并"""

import asyncio
from typing import Any, Callable, Dict, List, Optional, Tuple

from .db import Database


class BatchQueryService:
    """批量查询服务 - 合并多个查询减少数据库往返"""

    def __init__(self, db: Database):
        self._db = db
        self._query_queue: List[Tuple[str, Tuple, Callable]] = []
        self._lock = asyncio.Lock()

    async def queue_query(
        self,
        query: str,
        params: Tuple = (),
        callback: Optional[Callable] = None,
    ) -> Any:
        """排队查询，会被批量执行"""
        async with self._lock:
            self._query_queue.append((query, params, callback))
            if len(self._query_queue) >= 10:
                await self._flush()
        return None

    async def _flush(self) -> None:
        """批量执行所有排队的查询"""
        async with self._lock:
            if not self._query_queue:
                return
            queries = list(self._query_queue)
            self._query_queue = []

        async with self._db.acquire() as conn:
            for query, params, callback in queries:
                try:
                    if query.strip().upper().startswith("SELECT"):
                        result = await conn.fetch(query, *params)
                        if callback:
                            callback(result)
                    else:
                        await conn.execute(query, *params)
                except Exception:
                    pass


class QueryOptimizationService:
    """查询优化服务 - 提供优化的查询方法"""

    def __init__(self, db: Database):
        self._db = db

    async def batch_get_chapters(
        self,
        project_id: str,
        chapter_nos: List[int],
    ) -> List[Dict[str, Any]]:
        """批量获取章节信息"""
        if not chapter_nos:
            return []

        placeholders = ",".join(["$" + str(i + 1) for i in range(len(chapter_nos))])
        rows = await self._db.fetch(
            f"""
            SELECT id::text, project_id::text, chapter_no, volume_no, title, status,
                   word_count, source_path, created_at, updated_at
            FROM chapters
            WHERE project_id = $1 AND chapter_no IN ({placeholders})
            ORDER BY chapter_no
            """,
            project_id,
            *chapter_nos,
        )
        return [dict(row) for row in rows]

    async def batch_get_characters(
        self,
        project_id: str,
        character_ids: List[str],
    ) -> List[Dict[str, Any]]:
        """批量获取角色信息"""
        if not character_ids:
            return []

        placeholders = ",".join(["$" + str(i + 1) for i in range(len(character_ids))])
        rows = await self._db.fetch(
            f"""
            SELECT id::text, project_id::text, name, aliases, role, profile,
                   created_at, updated_at
            FROM characters
            WHERE project_id = $1 AND id IN ({placeholders})
            """,
            project_id,
            *character_ids,
        )
        return [dict(row) for row in rows]

    async def batch_get_events(
        self,
        project_id: str,
        chapter_ids: List[str],
    ) -> List[Dict[str, Any]]:
        """批量获取事件信息"""
        if not chapter_ids:
            return []

        placeholders = ",".join(["$" + str(i + 1) for i in range(len(chapter_ids))])
        rows = await self._db.fetch(
            f"""
            SELECT id::text, project_id::text, chapter_id::text, event_order, title,
                   summary, occurred_at_label, characters, locations, metadata, created_at
            FROM events
            WHERE project_id = $1 AND chapter_id IN ({placeholders})
            ORDER BY chapter_id, event_order
            """,
            project_id,
            *chapter_ids,
        )
        return [dict(row) for row in rows]

    async def get_chapter_range(
        self,
        project_id: str,
        start_chapter: int,
        end_chapter: int,
    ) -> List[Dict[str, Any]]:
        """获取章节范围（优化后的连续查询）"""
        rows = await self._db.fetch(
            """
            SELECT id::text, project_id::text, chapter_no, volume_no, title, status,
                   word_count, source_path, created_at, updated_at
            FROM chapters
            WHERE project_id = $1 AND chapter_no BETWEEN $2 AND $3
            ORDER BY chapter_no
            """,
            project_id,
            start_chapter,
            end_chapter,
        )
        return [dict(row) for row in rows]

    async def search_canon_documents(
        self,
        project_id: str,
        query: str,
        limit: int = 20,
        doc_types: Optional[List[str]] = None,
    ) -> List[Dict[str, Any]]:
        """优化的 Canon 文档搜索"""
        if doc_types:
            placeholders = ",".join(["$" + str(i + 2) for i in range(len(doc_types))])
            rows = await self._db.fetch(
                f"""
                SELECT id::text, project_id::text, doc_type, key, title, status,
                       review_status, source_type, created_at, updated_at
                FROM canon_documents
                WHERE project_id = $1 AND doc_type IN ({placeholders})
                  AND (title ILIKE $2 OR key ILIKE $2)
                ORDER BY updated_at DESC
                LIMIT $3
                """,
                project_id,
                *doc_types,
                f"%{query}%",
                limit,
            )
        else:
            rows = await self._db.fetch(
                """
                SELECT id::text, project_id::text, doc_type, key, title, status,
                       review_status, source_type, created_at, updated_at
                FROM canon_documents
                WHERE project_id = $1 AND (title ILIKE $2 OR key ILIKE $2)
                ORDER BY updated_at DESC
                LIMIT $3
                """,
                project_id,
                f"%{query}%",
                limit,
            )
        return [dict(row) for row in rows]

    async def get_foreshadowing_stats(
        self,
        project_id: str,
    ) -> Dict[str, Any]:
        """获取伏笔统计（聚合查询）"""
        row = await self._db.fetchrow(
            """
            SELECT
                COUNT(*) as total,
                SUM(CASE WHEN status = 'planted' THEN 1 ELSE 0 END) as planted,
                SUM(CASE WHEN status = 'developing' THEN 1 ELSE 0 END) as developing,
                SUM(CASE WHEN status = 'ready_to_payoff' THEN 1 ELSE 0 END) as ready_to_payoff,
                SUM(CASE WHEN status = 'paid_off' THEN 1 ELSE 0 END) as paid_off,
                SUM(CASE WHEN status = 'abandoned' THEN 1 ELSE 0 END) as abandoned,
                SUM(CASE WHEN importance = 'high' OR importance = 'critical' THEN 1 ELSE 0 END) as high_importance
            FROM foreshadowing
            WHERE project_id = $1
            """,
            project_id,
        )
        return dict(row) if row else {
            "total": 0, "planted": 0, "developing": 0,
            "ready_to_payoff": 0, "paid_off": 0, "abandoned": 0, "high_importance": 0
        }


class RequestThrottlingService:
    """请求限流服务 - 防止并发过高"""

    def __init__(self):
        self._limits: Dict[str, Tuple[int, int, float]] = {}
        self._semaphores: Dict[str, asyncio.Semaphore] = {}

    def register_limit(
        self,
        key: str,
        max_concurrent: int = 10,
        rate_limit_per_second: int = 30,
    ) -> None:
        """注册限流规则"""
        self._limits[key] = (max_concurrent, rate_limit_per_second, 0.0)
        self._semaphores[key] = asyncio.Semaphore(max_concurrent)

    async def acquire(self, key: str) -> None:
        """获取限流许可"""
        semaphore = self._semaphores.get(key)
        if semaphore:
            await semaphore.acquire()

    def release(self, key: str) -> None:
        """释放限流许可"""
        semaphore = self._semaphores.get(key)
        if semaphore and semaphore.locked():
            try:
                semaphore.release()
            except ValueError:
                pass


class PerformanceMetricsService:
    """性能指标服务 - 收集和报告性能数据"""

    def __init__(self):
        self._metrics: Dict[str, List[float]] = {}
        self._timers: Dict[str, float] = {}

    def start_timer(self, operation: str) -> None:
        """开始计时"""
        import time
        self._timers[operation] = time.time()

    def end_timer(self, operation: str) -> float:
        """结束计时并返回耗时"""
        import time
        start = self._timers.get(operation)
        if start:
            duration = time.time() - start
            if operation not in self._metrics:
                self._metrics[operation] = []
            self._metrics[operation].append(duration)
            del self._timers[operation]
            return duration
        return 0.0

    def get_metrics(self) -> Dict[str, Dict[str, float]]:
        """获取所有指标的统计信息"""
        result = {}
        for operation, durations in self._metrics.items():
            if durations:
                result[operation] = {
                    "count": len(durations),
                    "min": min(durations),
                    "max": max(durations),
                    "avg": sum(durations) / len(durations),
                    "p95": sorted(durations)[int(len(durations) * 0.95)] if len(durations) >= 20 else 0,
                }
        return result

    def reset(self) -> None:
        """重置所有指标"""
        self._metrics.clear()
        self._timers.clear()
