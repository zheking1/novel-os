"""
Progressive Context Compression Service

Layered memory system for 20M+ character novels:
  Chapter → Arc → Volume → Series

Each layer compresses the previous, keeping context window manageable.
"""

from datetime import datetime
from typing import Any

from .db import Database
from .utils import json_dumps, row_to_dict, rows_to_dicts


class ContextCompressionService:
    """Manages hierarchical context compression for long-form novels."""

    def __init__(self, db: Database, llm_client: Any = None):
        self._db = db
        self._llm = llm_client

    # ------------------------------------------------------------------
    # Chapter Summary Compression
    # ------------------------------------------------------------------

    async def compress_chapter_summaries(
        self,
        project_id: str,
        chapter_no_start: int,
        chapter_no_end: int,
        target_tokens: int = 500,
    ) -> dict[str, Any]:
        """Compress a range of chapter summaries into a single compressed summary."""
        rows = await self._db.fetch(
            """
            SELECT c.chapter_no, c.title, s.content, s.metadata
            FROM chapters c
            JOIN chapter_summaries s ON s.chapter_id = c.id AND s.summary_type = 'chapter'
            WHERE c.project_id = $1
              AND c.chapter_no >= $2 AND c.chapter_no <= $3
            ORDER BY c.chapter_no
            """,
            project_id,
            chapter_no_start,
            chapter_no_end,
        )
        if not rows:
            return {"ok": False, "reason": "no_summaries_found"}

        summaries = rows_to_dicts(rows)
        combined = self._combine_summaries(summaries, target_tokens)

        async with self._db.acquire() as conn:
            async with conn.transaction():
                row = await conn.fetchrow(
                    """
                    INSERT INTO compressed_contexts
                      (project_id, compression_layer, chapter_range_start, chapter_range_end,
                       content, source_count, token_estimate, metadata)
                    VALUES ($1, 'chapter_batch', $2, $3, $4, $5, $6, $7::jsonb)
                    ON CONFLICT (project_id, compression_layer, chapter_range_start, chapter_range_end)
                    DO UPDATE SET content = EXCLUDED.content,
                                 source_count = EXCLUDED.source_count,
                                 token_estimate = EXCLUDED.token_estimate,
                                 metadata = EXCLUDED.metadata,
                                 updated_at = now()
                    RETURNING id::text, compression_layer, chapter_range_start, chapter_range_end,
                              source_count, token_estimate, created_at, updated_at
                    """,
                    project_id,
                    chapter_no_start,
                    chapter_no_end,
                    combined["content"],
                    len(summaries),
                    combined["token_estimate"],
                    json_dumps({"titles": [s.get("title") for s in summaries]}),
                )

        return {
            "ok": True,
            "id": row["id"],
            "layer": "chapter_batch",
            "range": [chapter_no_start, chapter_no_end],
            "source_count": len(summaries),
            "token_estimate": combined["token_estimate"],
        }

    # ------------------------------------------------------------------
    # Arc Summary Compression
    # ------------------------------------------------------------------

    async def compress_arc(
        self,
        project_id: str,
        arc_key: str,
        chapter_no_start: int,
        chapter_no_end: int,
        arc_label: str | None = None,
    ) -> dict[str, Any]:
        """Create an arc-level compressed summary from chapter summaries in the arc."""
        rows = await self._db.fetch(
            """
            SELECT c.chapter_no, c.title, s.content, s.metadata
            FROM chapters c
            JOIN chapter_summaries s ON s.chapter_id = c.id AND s.summary_type = 'chapter'
            WHERE c.project_id = $1
              AND c.chapter_no >= $2 AND c.chapter_no <= $3
            ORDER BY c.chapter_no
            """,
            project_id,
            chapter_no_start,
            chapter_no_end,
        )
        summaries = rows_to_dicts(rows)
        if not summaries:
            return {"ok": False, "reason": "no_summaries_found"}

        combined = self._combine_summaries(summaries, target_tokens=300)

        async with self._db.acquire() as conn:
            async with conn.transaction():
                row = await conn.fetchrow(
                    """
                    INSERT INTO compressed_contexts
                      (project_id, compression_layer, arc_key, chapter_range_start, chapter_range_end,
                       content, source_count, token_estimate, metadata)
                    VALUES ($1, 'arc', $2, $3, $4, $5, $6, $7, $8::jsonb)
                    ON CONFLICT (project_id, compression_layer, chapter_range_start, chapter_range_end)
                    DO UPDATE SET content = EXCLUDED.content,
                                 arc_key = EXCLUDED.arc_key,
                                 source_count = EXCLUDED.source_count,
                                 token_estimate = EXCLUDED.token_estimate,
                                 metadata = EXCLUDED.metadata,
                                 updated_at = now()
                    RETURNING id::text, compression_layer, arc_key, chapter_range_start, chapter_range_end,
                              source_count, token_estimate, created_at, updated_at
                    """,
                    project_id,
                    arc_key,
                    chapter_no_start,
                    chapter_no_end,
                    combined["content"],
                    len(summaries),
                    combined["token_estimate"],
                    json_dumps({
                        "arc_label": arc_label,
                        "titles": [s.get("title") for s in summaries],
                    }),
                )

        return {
            "ok": True,
            "id": row["id"],
            "layer": "arc",
            "arc_key": arc_key,
            "range": [chapter_no_start, chapter_no_end],
            "source_count": len(summaries),
            "token_estimate": combined["token_estimate"],
        }

    # ------------------------------------------------------------------
    # Volume Summary Compression
    # ------------------------------------------------------------------

    async def compress_volume(
        self,
        project_id: str,
        volume_no: int,
    ) -> dict[str, Any]:
        """Create a volume-level compressed summary from arc summaries + direct chapter summaries."""
        vol = await self._db.fetchrow(
            """
            SELECT id, start_chapter_no, end_chapter_no, summary, goals
            FROM volumes
            WHERE project_id = $1 AND volume_no = $2
            """,
            project_id,
            volume_no,
        )
        if not vol:
            return {"ok": False, "reason": "volume_not_found"}

        start = vol["start_chapter_no"]
        end = vol["end_chapter_no"]

        arc_rows = await self._db.fetch(
            """
            SELECT arc_key, content, chapter_range_start, chapter_range_end, token_estimate
            FROM compressed_contexts
            WHERE project_id = $1 AND compression_layer = 'arc'
              AND chapter_range_start >= $2 AND chapter_range_end <= $3
            ORDER BY chapter_range_start
            """,
            project_id,
            start,
            end,
        )
        arcs = rows_to_dicts(arc_rows)

        if not arcs:
            chapter_rows = await self._db.fetch(
                """
                SELECT c.chapter_no, c.title, s.content
                FROM chapters c
                JOIN chapter_summaries s ON s.chapter_id = c.id AND s.summary_type = 'chapter'
                WHERE c.project_id = $1 AND c.chapter_no >= $2 AND c.chapter_no <= $3
                ORDER BY c.chapter_no
                """,
                project_id,
                start,
                end,
            )
            summaries = rows_to_dicts(chapter_rows)
            combined = self._combine_summaries(summaries, target_tokens=500)
        else:
            combined = self._combine_summaries(
                [{"content": a["content"], "title": a["arc_key"]} for a in arcs],
                target_tokens=500,
            )

        vol_summary = vol["summary"] or ""
        content = f"[Volume {volume_no}]\n{vol_summary}\n\n{combined['content']}"

        async with self._db.acquire() as conn:
            async with conn.transaction():
                row = await conn.fetchrow(
                    """
                    INSERT INTO compressed_contexts
                      (project_id, compression_layer, volume_no, chapter_range_start, chapter_range_end,
                       content, source_count, token_estimate, metadata)
                    VALUES ($1, 'volume', $2, $3, $4, $5, $6, $7, $8::jsonb)
                    ON CONFLICT (project_id, compression_layer, chapter_range_start, chapter_range_end)
                    DO UPDATE SET content = EXCLUDED.content,
                                 volume_no = EXCLUDED.volume_no,
                                 source_count = EXCLUDED.source_count,
                                 token_estimate = EXCLUDED.token_estimate,
                                 metadata = EXCLUDED.metadata,
                                 updated_at = now()
                    RETURNING id::text, compression_layer, volume_no, chapter_range_start, chapter_range_end,
                              source_count, token_estimate, created_at, updated_at
                    """,
                    project_id,
                    volume_no,
                    start,
                    end,
                    content,
                    len(arcs) if arcs else len(summaries),
                    combined["token_estimate"],
                    json_dumps({"volume_goals": vol["goals"]}),
                )

        return {
            "ok": True,
            "id": row["id"],
            "layer": "volume",
            "volume_no": volume_no,
            "range": [start, end],
            "token_estimate": combined["token_estimate"],
        }

    # ------------------------------------------------------------------
    # Series Summary Compression
    # ------------------------------------------------------------------

    async def compress_series(self, project_id: str) -> dict[str, Any]:
        """Create a series-level compressed summary from all volume summaries."""
        vol_rows = await self._db.fetch(
            """
            SELECT volume_no, content, token_estimate
            FROM compressed_contexts
            WHERE project_id = $1 AND compression_layer = 'volume'
            ORDER BY volume_no
            """,
            project_id,
        )
        volumes = rows_to_dicts(vol_rows)

        if not volumes:
            return {"ok": False, "reason": "no_volume_summaries"}

        combined = self._combine_summaries(
            [{"content": v["content"], "title": f"Volume {v['volume_no']}"} for v in volumes],
            target_tokens=600,
        )

        async with self._db.acquire() as conn:
            async with conn.transaction():
                row = await conn.fetchrow(
                    """
                    INSERT INTO compressed_contexts
                      (project_id, compression_layer, content, source_count, token_estimate, metadata)
                    VALUES ($1, 'series', $2, $3, $4, $5::jsonb)
                    ON CONFLICT (project_id, compression_layer, chapter_range_start, chapter_range_end)
                    DO UPDATE SET content = EXCLUDED.content,
                                 source_count = EXCLUDED.source_count,
                                 token_estimate = EXCLUDED.token_estimate,
                                 metadata = EXCLUDED.metadata,
                                 updated_at = now()
                    RETURNING id::text, compression_layer, source_count, token_estimate,
                              created_at, updated_at
                    """,
                    project_id,
                    combined["content"],
                    len(volumes),
                    combined["token_estimate"],
                    json_dumps({"volume_count": len(volumes)}),
                )

        return {
            "ok": True,
            "id": row["id"],
            "layer": "series",
            "token_estimate": combined["token_estimate"],
        }

    # ------------------------------------------------------------------
    # Context Assembly with Compression
    # ------------------------------------------------------------------

    async def get_compressed_context(
        self,
        project_id: str,
        chapter_no: int,
        volume_no: int | None = None,
        budget_tokens: int = 4000,
    ) -> dict[str, Any]:
        """Build a compressed context pack for chapter generation.

        Returns layered summaries fitting within budget_tokens.
        """
        sections: list[dict[str, Any]] = []
        used_tokens = 0

        series_row = await self._db.fetchrow(
            """
            SELECT content, token_estimate
            FROM compressed_contexts
            WHERE project_id = $1 AND compression_layer = 'series'
            ORDER BY updated_at DESC LIMIT 1
            """,
            project_id,
        )
        if series_row and used_tokens + series_row["token_estimate"] <= budget_tokens:
            sections.append({
                "name": "series_summary",
                "content": series_row["content"],
                "tokens": series_row["token_estimate"],
            })
            used_tokens += series_row["token_estimate"]

        if volume_no:
            vol_row = await self._db.fetchrow(
                """
                SELECT content, token_estimate
                FROM compressed_contexts
                WHERE project_id = $1 AND compression_layer = 'volume' AND volume_no = $2
                """,
                project_id,
                volume_no,
            )
            if vol_row and used_tokens + vol_row["token_estimate"] <= budget_tokens:
                sections.append({
                    "name": "volume_summary",
                    "content": vol_row["content"],
                    "tokens": vol_row["token_estimate"],
                })
                used_tokens += vol_row["token_estimate"]

        arc_rows = await self._db.fetch(
            """
            SELECT arc_key, content, token_estimate, chapter_range_start, chapter_range_end
            FROM compressed_contexts
            WHERE project_id = $1 AND compression_layer = 'arc'
              AND chapter_range_start <= $2 AND chapter_range_end >= $2
            ORDER BY chapter_range_start
            """,
            project_id,
            chapter_no,
        )
        for arc_row in arc_rows:
            if used_tokens + arc_row["token_estimate"] <= budget_tokens:
                sections.append({
                    "name": f"arc:{arc_row['arc_key']}",
                    "content": arc_row["content"],
                    "tokens": arc_row["token_estimate"],
                })
                used_tokens += arc_row["token_estimate"]

        recent_start = max(1, chapter_no - 10)
        recent_rows = await self._db.fetch(
            """
            SELECT c.chapter_no, c.title, s.content
            FROM chapters c
            JOIN chapter_summaries s ON s.chapter_id = c.id AND s.summary_type = 'chapter'
            WHERE c.project_id = $1 AND c.chapter_no >= $2 AND c.chapter_no < $3
            ORDER BY c.chapter_no DESC
            LIMIT 8
            """,
            project_id,
            recent_start,
            chapter_no,
        )
        recent = list(reversed(rows_to_dicts(recent_rows)))
        recent_tokens = sum(len(s.get("content", "")) // 4 for s in recent)
        if used_tokens + recent_tokens <= budget_tokens:
            sections.append({
                "name": "recent_chapters",
                "content": "\n".join(
                    f"[Ch.{s['chapter_no']}] {s.get('title', '')}: {s.get('content', '')}"
                    for s in recent
                ),
                "tokens": recent_tokens,
            })
            used_tokens += recent_tokens

        return {
            "ok": True,
            "chapter_no": chapter_no,
            "volume_no": volume_no,
            "sections": sections,
            "total_tokens": used_tokens,
            "budget_tokens": budget_tokens,
            "within_budget": used_tokens <= budget_tokens,
        }

    # ------------------------------------------------------------------
    # Auto-Compress Trigger
    # ------------------------------------------------------------------

    async def auto_compress_after_commit(
        self,
        project_id: str,
        chapter_no: int,
    ) -> list[dict[str, Any]]:
        """Run compression after a chapter commit. Returns compression results."""
        results = []

        batch_size = 10
        batch_start = ((chapter_no - 1) // batch_size) * batch_size + 1
        batch_end = batch_start + batch_size - 1
        r = await self.compress_chapter_summaries(project_id, batch_start, batch_end)
        if r.get("ok"):
            results.append(r)

        if chapter_no % 50 == 0:
            arc_key = f"arc_{batch_start}_{batch_end}"
            r = await self.compress_arc(project_id, arc_key, batch_start, batch_end)
            if r.get("ok"):
                results.append(r)

        if chapter_no % 200 == 0:
            vol = await self._db.fetchrow(
                """
                SELECT volume_no FROM volumes
                WHERE project_id = $1
                  AND start_chapter_no <= $2 AND end_chapter_no >= $2
                """,
                project_id,
                chapter_no,
            )
            if vol:
                r = await self.compress_volume(project_id, vol["volume_no"])
                if r.get("ok"):
                    results.append(r)

        if chapter_no % 500 == 0:
            r = await self.compress_series(project_id)
            if r.get("ok"):
                results.append(r)

        return results

    async def check_knowledge_batch(
        self, project_id: str, chapter_no: int,
    ) -> dict[str, Any] | None:
        if chapter_no % 10 != 0:
            return None
        pk_count = await self._db.fetchval(
            "SELECT COUNT(*) FROM project_knowledge WHERE project_id = $1 AND created_at > (NOW() - INTERVAL '7 days')",
            project_id,
        )
        uk_count = await self._db.fetchval(
            "SELECT COUNT(*) FROM universal_knowledge WHERE source = 'discussion_room' AND created_at > (NOW() - INTERVAL '7 days')",
        )
        entity_count = await self._db.fetchval(
            "SELECT COUNT(*) FROM state_entities WHERE project_id = $1 AND lifecycle_status = 'active'",
            project_id,
        )
        total_new = (pk_count or 0) + (uk_count or 0) + (entity_count or 0)
        if total_new == 0:
            return None
        return {
            "is_batch_time": True,
            "chapter_no": chapter_no,
            "new_since_last_batch": {
                "project_knowledge": pk_count or 0,
                "universal_knowledge": uk_count or 0,
                "state_entities": entity_count or 0,
            },
            "suggestion": (
                f"已累计 {total_new} 条新知识。建议调 discussion_room.create_session 后台归纳"
                f"（第 {chapter_no - 9}-{chapter_no} 章），不阻塞下一章生成。"
            ),
        }

    async def check_volume_closure(
        self, project_id: str, chapter_no: int,
    ) -> dict[str, Any] | None:
        vol = await self._db.fetchrow(
            "SELECT volume_no, title, start_chapter_no, end_chapter_no FROM volumes WHERE project_id = $1 AND end_chapter_no = $2",
            project_id, chapter_no,
        )
        if not vol:
            return None
        rule_count = await self._db.fetchval(
            "SELECT COUNT(*) FROM canon_rules WHERE project_id = $1 AND promotion_status IS NULL AND is_deleted = false",
            project_id,
        )
        return {
            "is_volume_end": True,
            "volume_no": vol["volume_no"],
            "volume_title": vol["title"],
            "chapter_range": f"{vol['start_chapter_no']}-{vol['end_chapter_no']}",
            "pending_rule_count": rule_count or 0,
            "suggestion": f"第{vol['volume_no']}卷已完结。建议: 讨论室归纳本卷知识, 对{rule_count or 0}条待评估规则逐条判断是否升级为全局。",
        }

    # ------------------------------------------------------------------
    # List & Query
    # ------------------------------------------------------------------

    async def list_compressed_contexts(
        self,
        project_id: str,
        layer: str | None = None,
        limit: int = 50,
    ) -> list[dict[str, Any]]:
        conditions = ["project_id = $1"]
        params: list[Any] = [project_id]
        idx = 2
        if layer:
            conditions.append(f"compression_layer = ${idx}")
            params.append(layer)
            idx += 1
        params.append(limit)
        rows = await self._db.fetch(
            f"""
            SELECT id::text, compression_layer, arc_key, volume_no,
                   chapter_range_start, chapter_range_end,
                   source_count, token_estimate, metadata,
                   created_at, updated_at
            FROM compressed_contexts
            WHERE {' AND '.join(conditions)}
            ORDER BY updated_at DESC
            LIMIT ${idx}
            """,
            *params,
        )
        return rows_to_dicts(rows)

    async def delete_compressed_context(
        self,
        project_id: str,
        context_id: str,
    ) -> bool:
        result = await self._db.execute(
            "DELETE FROM compressed_contexts WHERE project_id = $1 AND id = $2",
            project_id,
            context_id,
        )
        return result.endswith("1")

    # ------------------------------------------------------------------
    # Cold Data Auto-Archiving
    # ------------------------------------------------------------------

    async def archive_old_data(
        self,
        project_id: str,
        current_chapter_no: int,
        keep_recent_volumes: int = 3,
        keep_recent_chapters: int = 100,
    ) -> dict[str, Any]:
        """Archive old data to keep queries fast at scale.

        Strategy:
        - Keep last N volumes of state_snapshots (mark older as is_current=false)
        - Compress old chapter_summaries into batch summaries
        - Archive old events to events_archive table
        - Keep only compressed_contexts for archived data
        """
        results = {
            "snapshots_archived": 0,
            "summaries_compressed": 0,
            "events_archived": 0,
        }

        vol_rows = await self._db.fetch(
            """
            SELECT volume_no, start_chapter_no, end_chapter_no
            FROM volumes
            WHERE project_id = $1
            ORDER BY volume_no DESC
            """,
            project_id,
        )
        volumes = rows_to_dicts(vol_rows)

        if len(volumes) > keep_recent_volumes:
            cutoff_volume = volumes[keep_recent_volumes - 1]["volume_no"]

            snap_result = await self._db.execute(
                """
                UPDATE state_snapshots
                SET is_current = false
                WHERE project_id = $1
                  AND effective_volume_no IS NOT NULL
                  AND effective_volume_no < $2
                  AND is_current = true
                """,
                project_id,
                cutoff_volume,
            )
            results["snapshots_archived"] = int(snap_result.split()[-1]) if snap_result else 0

            cutoff_chapter = volumes[keep_recent_volumes - 1]["start_chapter_no"]
            batch_size = 20
            for start in range(1, cutoff_chapter, batch_size):
                end = min(start + batch_size - 1, cutoff_chapter - 1)
                existing = await self._db.fetchrow(
                    """
                    SELECT id FROM compressed_contexts
                    WHERE project_id = $1 AND compression_layer = 'chapter_batch'
                      AND chapter_range_start = $2 AND chapter_range_end = $3
                    """,
                    project_id,
                    start,
                    end,
                )
                if not existing:
                    r = await self.compress_chapter_summaries(project_id, start, end, target_tokens=200)
                    if r.get("ok"):
                        results["summaries_compressed"] += 1

        if len(volumes) > keep_recent_volumes:
            cutoff_chapter = volumes[keep_recent_volumes - 1]["start_chapter_no"]
            archive_result = await self._db.execute(
                """
                INSERT INTO events_archive (project_id, chapter_id, event_order, title, summary, characters, locations, metadata)
                SELECT e.project_id, e.chapter_id, e.event_order, e.title, e.summary, e.characters, e.locations, e.metadata
                FROM events e
                JOIN chapters c ON c.id = e.chapter_id
                WHERE c.project_id = $1 AND c.chapter_no < $2
                  AND NOT EXISTS (SELECT 1 FROM events_archive ea WHERE ea.chapter_id = e.chapter_id AND ea.event_order = e.event_order)
                """,
                project_id,
                cutoff_chapter,
            )
            results["events_archived"] = int(archive_result.split()[-1]) if archive_result else 0

            await self._db.execute(
                """
                DELETE FROM events e
                USING chapters c
                WHERE e.chapter_id = c.id
                  AND c.project_id = $1 AND c.chapter_no < $2
                """,
                project_id,
                cutoff_chapter,
            )

        return {
            "ok": True,
            "current_chapter": current_chapter_no,
            "archived_before_volume": volumes[keep_recent_volumes - 1]["volume_no"] if len(volumes) > keep_recent_volumes else None,
            **results,
        }

    async def get_archive_stats(self, project_id: str) -> dict[str, Any]:
        """Get statistics about data distribution for archiving decisions."""
        stats = {}

        row = await self._db.fetchrow(
            "SELECT COUNT(*) AS cnt FROM state_snapshots WHERE project_id = $1 AND is_current = true",
            project_id,
        )
        stats["current_snapshots"] = row["cnt"] if row else 0

        row = await self._db.fetchrow(
            "SELECT COUNT(*) AS cnt FROM state_snapshots WHERE project_id = $1",
            project_id,
        )
        stats["total_snapshots"] = row["cnt"] if row else 0

        row = await self._db.fetchrow(
            "SELECT COUNT(*) AS cnt FROM chapter_summaries WHERE project_id = $1",
            project_id,
        )
        stats["chapter_summaries"] = row["cnt"] if row else 0

        row = await self._db.fetchrow(
            "SELECT COUNT(*) AS cnt FROM events WHERE project_id = $1",
            project_id,
        )
        stats["active_events"] = row["cnt"] if row else 0

        row = await self._db.fetchrow(
            "SELECT COUNT(*) AS cnt FROM events_archive WHERE project_id = $1",
            project_id,
        )
        stats["archived_events"] = row["cnt"] if row else 0

        row = await self._db.fetchrow(
            "SELECT COUNT(*) AS cnt FROM compressed_contexts WHERE project_id = $1",
            project_id,
        )
        stats["compressed_contexts"] = row["cnt"] if row else 0

        row = await self._db.fetchrow(
            """
            SELECT MIN(chapter_no) AS min_ch, MAX(chapter_no) AS max_ch
            FROM chapters WHERE project_id = $1
            """,
            project_id,
        )
        if row:
            stats["chapter_range"] = [row["min_ch"], row["max_ch"]]

        return stats

    # ------------------------------------------------------------------
    # Internal Helpers — Structured Extraction (not truncation)
    # ------------------------------------------------------------------

    def _combine_summaries(
        self,
        summaries: list[dict[str, Any]],
        target_tokens: int = 500,
    ) -> dict[str, Any]:
        """Combine summaries via structured extraction, not truncation.

        Extracts: chapter range, key events, characters mentioned,
        turning points, emotional arc. Fits within target_tokens.
        """
        if not summaries:
            return {"content": "", "token_estimate": 0}

        char_budget = target_tokens * 4

        chapter_range = f"Ch.{summaries[0].get('title') or summaries[0].get('chapter_no', '?')}~{summaries[-1].get('title') or summaries[-1].get('chapter_no', '?')}"

        all_content = " ".join(s.get("content", "") for s in summaries)

        import re
        cn_chars = re.findall(r'[\u4e00-\u9fff]{2,4}', all_content)
        char_freq: dict[str, int] = {}
        for c in cn_chars:
            char_freq[c] = char_freq.get(c, 0) + 1
        top_chars = sorted(char_freq.items(), key=lambda x: -x[1])[:15]
        characters = [c for c, _ in top_chars]

        sentences = re.split(r'[。！？\n]+', all_content)
        sentences = [s.strip() for s in sentences if len(s.strip()) > 10]

        keywords = set()
        for s in sentences:
            words = re.findall(r'[\u4e00-\u9fff]{2,6}', s)
            for w in words:
                if len(w) >= 3:
                    keywords.add(w)
        top_keywords = sorted(keywords)[:20]

        turning_points = []
        for s in sentences:
            if any(kw in s for kw in ['突破', '觉醒', '死亡', '牺牲', '转折', '意外', '震惊',
                                       '秘密', '真相', '背叛', '逆袭', '危机', '决战', '分离',
                                       '重逢', '复仇', '觉醒', '飞升', '渡劫', '涅槃']):
                turning_points.append(s[:80])

        emotional_arc = []
        for s in summaries[-5:]:
            content = s.get("content", "")
            if any(w in content for w in ['悲伤', '痛苦', '绝望', '死亡', '牺牲']):
                emotional_arc.append("低谷")
            elif any(w in content for w in ['胜利', '突破', '成功', '喜悦', '团聚']):
                emotional_arc.append("高潮")
            elif any(w in content for w in ['修炼', '准备', '计划', '布局']):
                emotional_arc.append("铺垫")
            else:
                emotional_arc.append("过渡")

        lines = [f"[{chapter_range}]"]
        if characters:
            lines.append(f"角色: {', '.join(characters[:8])}")
        if top_keywords:
            lines.append(f"关键词: {', '.join(top_keywords[:10])}")
        if turning_points:
            lines.append(f"转折: {'; '.join(turning_points[:3])}")
        if emotional_arc:
            unique_arc = []
            for a in emotional_arc:
                if not unique_arc or unique_arc[-1] != a:
                    unique_arc.append(a)
            lines.append(f"情绪弧: {'→'.join(unique_arc)}")

        combined = "\n".join(lines)

        if len(combined) > char_budget:
            combined = combined[:char_budget] + "..."

        return {
            "content": combined,
            "token_estimate": len(combined) // 4,
        }
