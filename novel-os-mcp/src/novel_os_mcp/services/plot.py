import logging
from typing import Any

from ..db import Database
from ..utils import json_dumps, row_to_dict, rows_to_dicts, ensure_json_value

logger = logging.getLogger("novel_os_mcp.services.plot")


class PlotService:
    def __init__(self, db: Database):
        self._db = db

    async def upsert_volume(
        self,
        project_id: str,
        volume_no: int,
        title: str | None = None,
        outline: str | None = None,
        status: str = "planned",
        start_chapter_no: int | None = None,
        end_chapter_no: int | None = None,
        summary: str | None = None,
        goals: list[dict[str, Any]] | None = None,
        metadata: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        row = await self._db.fetchrow(
            """
            INSERT INTO volumes (
              project_id, volume_no, title, outline, status, start_chapter_no,
              end_chapter_no, summary, goals, metadata
            )
            VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9::jsonb, $10::jsonb)
            ON CONFLICT (project_id, volume_no)
            DO UPDATE SET title = COALESCE(EXCLUDED.title, volumes.title),
                          outline = COALESCE(EXCLUDED.outline, volumes.outline),
                          status = EXCLUDED.status,
                          start_chapter_no = COALESCE(EXCLUDED.start_chapter_no, volumes.start_chapter_no),
                          end_chapter_no = COALESCE(EXCLUDED.end_chapter_no, volumes.end_chapter_no),
                          summary = COALESCE(EXCLUDED.summary, volumes.summary),
                          goals = CASE WHEN $9::jsonb = '[]'::jsonb THEN volumes.goals ELSE EXCLUDED.goals END,
                          metadata = volumes.metadata || EXCLUDED.metadata,
                          updated_at = now()
            RETURNING id::text, volume_no, title, outline, status, start_chapter_no,
                      end_chapter_no, summary, goals, metadata, created_at, updated_at
            """,
            project_id,
            volume_no,
            title,
            outline,
            status,
            start_chapter_no,
            end_chapter_no,
            summary,
            json_dumps(goals or []),
            json_dumps(metadata or {}),
        )
        return row_to_dict(row)

    async def list_volumes(
        self,
        project_id: str,
        statuses: list[str] | None = None,
        current_chapter_no: int | None = None,
        limit: int = 100,
    ) -> list[dict[str, Any]]:
        rows = await self._db.fetch(
            """
            SELECT v.id::text, v.volume_no, v.title, v.outline, v.status,
                   v.start_chapter_no, v.end_chapter_no, v.summary, v.goals,
                   v.metadata, v.created_at, v.updated_at,
                   count(c.id)::int AS chapter_count,
                   (
                     $3::int IS NOT NULL
                     AND (v.start_chapter_no IS NULL OR v.start_chapter_no <= $3)
                     AND (v.end_chapter_no IS NULL OR v.end_chapter_no >= $3)
                   ) AS contains_current_chapter
            FROM volumes v
            LEFT JOIN chapters c ON c.project_id = v.project_id AND c.volume_no = v.volume_no
            WHERE v.project_id = $1 AND v.is_deleted = false
              AND ($2::text[] IS NULL OR v.status = ANY($2::text[]))
            GROUP BY v.id
            ORDER BY v.volume_no
            LIMIT $4
            """,
            project_id,
            statuses,
            current_chapter_no,
            limit,
        )
        return rows_to_dicts(rows)

    async def get_volume(
        self,
        project_id: str,
        volume_no: int | None = None,
        volume_id: str | None = None,
    ) -> dict[str, Any] | None:
        if volume_id:
            row = await self._db.fetchrow(
                """
                SELECT v.id::text, v.volume_no, v.title, v.outline, v.status,
                       v.start_chapter_no, v.end_chapter_no, v.summary, v.goals,
                       v.metadata, v.created_at, v.updated_at,
                       count(c.id)::int AS chapter_count
                FROM volumes v
                LEFT JOIN chapters c ON c.project_id = v.project_id AND c.volume_no = v.volume_no
                WHERE v.id = $1 AND v.is_deleted = false
                GROUP BY v.id
                """,
                volume_id,
            )
        elif volume_no is not None:
            row = await self._db.fetchrow(
                """
                SELECT v.id::text, v.volume_no, v.title, v.outline, v.status,
                       v.start_chapter_no, v.end_chapter_no, v.summary, v.goals,
                       v.metadata, v.created_at, v.updated_at,
                       count(c.id)::int AS chapter_count
                FROM volumes v
                LEFT JOIN chapters c ON c.project_id = v.project_id AND c.volume_no = v.volume_no
                WHERE v.project_id = $1 AND v.volume_no = $2 AND v.is_deleted = false
                GROUP BY v.id
                """,
                project_id,
                volume_no,
            )
        else:
            return None
        if not row:
            return None
        return row_to_dict(row)

    async def upsert_plot_thread(
        self,
        project_id: str,
        key: str,
        title: str,
        thread_type: str = "side",
        status: str = "open",
        importance: str = "medium",
        volume_no: int | None = None,
        start_chapter_no: int | None = None,
        current_chapter_no: int | None = None,
        last_advanced_chapter_no: int | None = None,
        expected_next_chapter_no: int | None = None,
        stalled_after_chapters: int = 20,
        related_entity_ids: list[str] | None = None,
        related_foreshadowing_ids: list[str] | None = None,
        metadata: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        # Validate volume_no exists if provided
        if volume_no is not None:
            vol = await self._db.fetchval("SELECT 1 FROM volumes WHERE project_id = $1 AND volume_no = $2 AND status != 'deleted'", project_id, volume_no)
            if not vol:
                raise ValueError(f"卷不存在: volume_no={volume_no}")
        # Validate chapter numbers exist if provided（仅提示，不强制阻止章节创建前提供章节参考号）
        for cn_field, cn_label in [(start_chapter_no, "start_chapter_no"), (current_chapter_no, "current_chapter_no"), (expected_next_chapter_no, "expected_next_chapter_no")]:
            if cn_field is not None:
                ch = await self._db.fetchval("SELECT 1 FROM chapters WHERE project_id = $1 AND chapter_no = $2", project_id, cn_field)
                if not ch:
                    logger.warning(f"plot.thread '{key}' references chapter {cn_label}={cn_field} which does not exist yet")
        row = await self._db.fetchrow(
            """
            INSERT INTO plot_threads (
              project_id, key, title, thread_type, status, importance, volume_no,
              start_chapter_no, current_chapter_no, last_advanced_chapter_no,
              expected_next_chapter_no, stalled_after_chapters, related_entity_ids,
              related_foreshadowing_ids, metadata
            )
            VALUES (
              $1, $2, $3, $4, $5, $6, $7,
              $8, $9, $10, $11, $12,
              COALESCE($13::text[], ARRAY[]::text[]),
              COALESCE($14::text[], ARRAY[]::text[]),
              $15::jsonb
            )
            ON CONFLICT (project_id, key)
            DO UPDATE SET title = EXCLUDED.title,
                          thread_type = EXCLUDED.thread_type,
                          status = EXCLUDED.status,
                          importance = EXCLUDED.importance,
                          volume_no = COALESCE(EXCLUDED.volume_no, plot_threads.volume_no),
                          start_chapter_no = COALESCE(EXCLUDED.start_chapter_no, plot_threads.start_chapter_no),
                          current_chapter_no = COALESCE(EXCLUDED.current_chapter_no, plot_threads.current_chapter_no),
                          last_advanced_chapter_no = COALESCE(EXCLUDED.last_advanced_chapter_no, plot_threads.last_advanced_chapter_no),
                          expected_next_chapter_no = COALESCE(EXCLUDED.expected_next_chapter_no, plot_threads.expected_next_chapter_no),
                          stalled_after_chapters = EXCLUDED.stalled_after_chapters,
                          related_entity_ids = CASE WHEN $13::text[] IS NULL THEN plot_threads.related_entity_ids ELSE EXCLUDED.related_entity_ids END,
                          related_foreshadowing_ids = CASE WHEN $14::text[] IS NULL THEN plot_threads.related_foreshadowing_ids ELSE EXCLUDED.related_foreshadowing_ids END,
                          metadata = plot_threads.metadata || EXCLUDED.metadata,
                          updated_at = now()
            RETURNING id::text, key, title, thread_type, status, importance, volume_no,
                      start_chapter_no, current_chapter_no, last_advanced_chapter_no,
                      expected_next_chapter_no, stalled_after_chapters, related_entity_ids,
                      related_foreshadowing_ids, metadata, created_at, updated_at
            """,
            project_id,
            key,
            title,
            thread_type,
            status,
            importance,
            volume_no,
            start_chapter_no,
            current_chapter_no,
            last_advanced_chapter_no,
            expected_next_chapter_no,
            stalled_after_chapters,
            related_entity_ids,
            related_foreshadowing_ids,
            json_dumps(metadata or {}),
        )
        return row_to_dict(row)

    async def list_plot_threads(
        self,
        project_id: str,
        statuses: list[str] | None = None,
        thread_types: list[str] | None = None,
        importance: list[str] | None = None,
        volume_no: int | None = None,
        current_chapter_no: int | None = None,
        include_closed: bool = False,
        limit: int = 100,
    ) -> list[dict[str, Any]]:
        rows = await self._db.fetch(
            """
            SELECT id::text, key, title, thread_type, status, importance, volume_no,
                   start_chapter_no, current_chapter_no, last_advanced_chapter_no,
                   expected_next_chapter_no, stalled_after_chapters, related_entity_ids,
                   related_foreshadowing_ids, metadata, created_at, updated_at,
                   (
                     $6::int IS NOT NULL
                     AND status NOT IN ('closed', 'resolved', 'archived')
                     AND ($6 - COALESCE(last_advanced_chapter_no, start_chapter_no, 0)) >= stalled_after_chapters
                   ) AS is_stalled
            FROM plot_threads
            WHERE project_id = $1 AND is_deleted = false
              AND ($2::text[] IS NULL OR status = ANY($2::text[]))
              AND ($3::text[] IS NULL OR thread_type = ANY($3::text[]))
              AND ($4::text[] IS NULL OR importance = ANY($4::text[]))
              AND ($5::int IS NULL OR volume_no = $5)
              AND ($7::boolean = true OR status NOT IN ('closed', 'resolved', 'archived'))
            ORDER BY
              CASE importance
                WHEN 'critical' THEN 1
                WHEN 'high' THEN 2
                WHEN 'medium' THEN 3
                ELSE 4
              END,
              updated_at DESC
            LIMIT $8
            """,
            project_id,
            statuses,
            thread_types,
            importance,
            volume_no,
            current_chapter_no,
            include_closed,
            limit,
        )
        return rows_to_dicts(rows)

    async def advance_plot_thread(
        self,
        project_id: str,
        key: str,
        chapter_no: int,
        status: str | None = None,
        progress_note: str | None = None,
        expected_next_chapter_no: int | None = None,
        metadata: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        # Validate chapter exists
        ch = await self._db.fetchrow("SELECT id FROM chapters WHERE project_id = $1 AND chapter_no = $2", project_id, chapter_no)
        if ch is None:
            raise ValueError(f"章节不存在: chapter_no={chapter_no}")
        row = await self._db.fetchrow(
            """
            UPDATE plot_threads
            SET current_chapter_no = $3::int,
                last_advanced_chapter_no = $3::int,
                expected_next_chapter_no = COALESCE($5::int, expected_next_chapter_no),
                status = COALESCE($4::text, status),
                metadata = metadata
                  || jsonb_build_object(
                       'last_progress_note', $6::text,
                       'last_progress_chapter_no', $3::int,
                       'last_progress_at', to_jsonb(now())
                     )
                  || $7::jsonb,
                updated_at = now()
            WHERE project_id = $1 AND key = $2
            RETURNING id::text, key, title, thread_type, status, importance, volume_no,
                      start_chapter_no, current_chapter_no, last_advanced_chapter_no,
                      expected_next_chapter_no, stalled_after_chapters, related_entity_ids,
                      related_foreshadowing_ids, metadata, created_at, updated_at
            """,
            project_id,
            key,
            chapter_no,
            status,
            expected_next_chapter_no,
            progress_note,
            json_dumps(metadata or {}),
        )
        if row is None:
            raise ValueError(f"Plot thread not found: {key}")
        return row_to_dict(row)

    async def check_stalled_threads(
        self,
        project_id: str,
        current_chapter_no: int,
        threshold_chapters: int | None = None,
        statuses: list[str] | None = None,
        limit: int = 100,
    ) -> list[dict[str, Any]]:
        rows = await self._db.fetch(
            """
            SELECT id::text, key, title, thread_type, status, importance, volume_no,
                   start_chapter_no, current_chapter_no, last_advanced_chapter_no,
                   expected_next_chapter_no, stalled_after_chapters, related_entity_ids,
                   related_foreshadowing_ids, metadata, created_at, updated_at,
                   ($2 - COALESCE(last_advanced_chapter_no, start_chapter_no, 0))::int AS stalled_by_chapters
            FROM plot_threads
            WHERE project_id = $1 AND is_deleted = false
              AND status NOT IN ('closed', 'resolved', 'archived')
              AND ($4::text[] IS NULL OR status = ANY($4::text[]))
              AND ($2 - COALESCE(last_advanced_chapter_no, start_chapter_no, 0)) >= COALESCE($3::int, stalled_after_chapters)
            ORDER BY stalled_by_chapters DESC, importance, updated_at
            LIMIT $5
            """,
            project_id,
            current_chapter_no,
            threshold_chapters,
            statuses,
            limit,
        )
        return rows_to_dicts(rows)

    async def list_foreshadowing(
        self,
        project_id: str,
        statuses: list[str] | None,
        importance: list[str] | None,
        limit: int,
        layers: list[str] | None = None,
        overdue_at_chapter: int | None = None,
        deadline_before_chapter: int | None = None,
    ) -> list[dict[str, Any]]:
        conditions = [
            "project_id = $1",
            "is_deleted = false",
            "($2::text[] IS NULL OR status = ANY($2::text[]))",
            "($3::text[] IS NULL OR importance = ANY($3::text[]))",
            "($6::text[] IS NULL OR layer = ANY($6::text[]))",
        ]
        params: list[Any] = [project_id, statuses, importance, limit, overdue_at_chapter, layers]
        idx = 7

        # Proximity filter: only include foreshadowing with payoff deadline within window
        if deadline_before_chapter is not None:
            conditions.append(f"(${idx}::int IS NULL OR payoff_deadline_chapter IS NULL OR payoff_deadline_chapter <= ${idx})")
            params.append(deadline_before_chapter)
            idx += 1

        rows = await self._db.fetch(
            f"""
            SELECT id::text, key, title, status, importance, expected_payoff_range,
                   parent_foreshadowing_id::text, related_foreshadowing_ids,
                   trigger_on_payoff_ids, blocks_payoff_until_ids, layer, must_payoff,
                   payoff_deadline_chapter, payoff_deadline_volume, overdue_policy,
                   (
                     $5::int IS NOT NULL
                     AND payoff_deadline_chapter IS NOT NULL
                     AND payoff_deadline_chapter < $5
                     AND status NOT IN ('paid_off', 'abandoned', 'archived')
                   ) AS is_overdue,
                   payload, created_at, updated_at
            FROM foreshadowing
            WHERE {' AND '.join(conditions)}
            ORDER BY
              CASE WHEN (
                $5::int IS NOT NULL
                AND payoff_deadline_chapter IS NOT NULL
                AND payoff_deadline_chapter < $5
                AND status NOT IN ('paid_off', 'abandoned', 'archived')
              ) THEN 0 ELSE 1 END,
              CASE importance
                WHEN 'critical' THEN 1
                WHEN 'high' THEN 2
                WHEN 'medium' THEN 3
                ELSE 4
              END,
              updated_at DESC
            LIMIT $4
            """,
            *params,
        )
        return rows_to_dicts(rows)

    async def upsert_foreshadowing(
        self,
        project_id: str,
        key: str,
        title: str,
        status: str = "planted",
        importance: str = "medium",
        expected_payoff_range: str | None = None,
        payload: dict[str, Any] | None = None,
        parent_foreshadowing_id: str | None = None,
        related_foreshadowing_ids: list[str] | None = None,
        trigger_on_payoff_ids: list[str] | None = None,
        blocks_payoff_until_ids: list[str] | None = None,
        layer: str = "visible",
        must_payoff: bool = False,
        payoff_deadline_chapter: int | None = None,
        payoff_deadline_volume: int | None = None,
        overdue_policy: str = "warn",
    ) -> dict[str, Any]:
        row = await self._db.fetchrow(
            """
            INSERT INTO foreshadowing (
              project_id, key, title, status, importance, expected_payoff_range, payload,
              parent_foreshadowing_id, related_foreshadowing_ids, trigger_on_payoff_ids,
              blocks_payoff_until_ids, layer, must_payoff, payoff_deadline_chapter,
              payoff_deadline_volume, overdue_policy
            )
            VALUES (
              $1, $2, $3, $4, $5, $6, $7::jsonb,
              $8::uuid, $9::text[], $10::text[],
              $11::text[], $12, $13, $14,
              $15, $16
            )
            ON CONFLICT (project_id, key)
            DO UPDATE SET title = EXCLUDED.title,
                          status = EXCLUDED.status,
                          importance = EXCLUDED.importance,
                          expected_payoff_range = EXCLUDED.expected_payoff_range,
                          payload = EXCLUDED.payload,
                          parent_foreshadowing_id = EXCLUDED.parent_foreshadowing_id,
                          related_foreshadowing_ids = EXCLUDED.related_foreshadowing_ids,
                          trigger_on_payoff_ids = EXCLUDED.trigger_on_payoff_ids,
                          blocks_payoff_until_ids = EXCLUDED.blocks_payoff_until_ids,
                          layer = EXCLUDED.layer,
                          must_payoff = EXCLUDED.must_payoff,
                          payoff_deadline_chapter = EXCLUDED.payoff_deadline_chapter,
                          payoff_deadline_volume = EXCLUDED.payoff_deadline_volume,
                          overdue_policy = EXCLUDED.overdue_policy,
                          updated_at = now()
            RETURNING id::text, key, title, status, importance, expected_payoff_range,
                      parent_foreshadowing_id::text, related_foreshadowing_ids,
                      trigger_on_payoff_ids, blocks_payoff_until_ids, layer, must_payoff,
                      payoff_deadline_chapter, payoff_deadline_volume, overdue_policy,
                      payload, created_at, updated_at
            """,
            project_id,
            key,
            title,
            status,
            importance,
            expected_payoff_range,
            json_dumps(payload or {}),
            parent_foreshadowing_id,
            related_foreshadowing_ids or [],
            trigger_on_payoff_ids or [],
            blocks_payoff_until_ids or [],
            layer,
            must_payoff,
            payoff_deadline_chapter,
            payoff_deadline_volume,
            overdue_policy,
        )
        return row_to_dict(row)

    async def bulk_update_foreshadowing_status(
        self,
        project_id: str,
        status: str,
        keys: list[str] | None = None,
        ids: list[str] | None = None,
        reason: str | None = None,
        metadata: dict[str, Any] | None = None,
    ) -> list[dict[str, Any]]:
        if not keys and not ids:
            raise ValueError("keys or ids is required")
        rows = await self._db.fetch(
            """
            UPDATE foreshadowing
            SET status = $4,
                payload = payload
                  || jsonb_build_object(
                       'last_status_reason', $5::text,
                       'last_status_at', to_jsonb(now())
                     )
                  || $6::jsonb,
                updated_at = now()
            WHERE project_id = $1
              AND (
                ($2::text[] IS NOT NULL AND key = ANY($2::text[]))
                OR ($3::uuid[] IS NOT NULL AND id = ANY($3::uuid[]))
              )
            RETURNING id::text, key, title, status, importance, expected_payoff_range,
                      parent_foreshadowing_id::text, related_foreshadowing_ids,
                      trigger_on_payoff_ids, blocks_payoff_until_ids, layer, must_payoff,
                      payoff_deadline_chapter, payoff_deadline_volume, overdue_policy,
                      payoff_chapter_id::text, payload, created_at, updated_at
            """,
            project_id,
            keys,
            ids,
            status,
            reason,
            json_dumps(metadata or {}),
        )
        return rows_to_dicts(rows)

    async def check_overdue_foreshadowing(
        self,
        project_id: str,
        current_chapter_no: int,
        current_volume_no: int | None = None,
        include_optional: bool = True,
        limit: int = 100,
    ) -> list[dict[str, Any]]:
        rows = await self._db.fetch(
            """
            SELECT id::text, key, title, status, importance, expected_payoff_range,
                   parent_foreshadowing_id::text, related_foreshadowing_ids,
                   trigger_on_payoff_ids, blocks_payoff_until_ids, layer, must_payoff,
                   payoff_deadline_chapter, payoff_deadline_volume, overdue_policy,
                   payoff_chapter_id::text, payload, created_at, updated_at,
                   CASE
                     WHEN payoff_deadline_chapter IS NOT NULL AND payoff_deadline_chapter < $2
                     THEN ($2 - payoff_deadline_chapter)::int
                     ELSE NULL
                   END AS overdue_by_chapters,
                   CASE
                     WHEN $3::int IS NOT NULL AND payoff_deadline_volume IS NOT NULL AND payoff_deadline_volume < $3
                     THEN ($3 - payoff_deadline_volume)::int
                     ELSE NULL
                   END AS overdue_by_volumes
            FROM foreshadowing
            WHERE project_id = $1
              AND status NOT IN ('paid_off', 'abandoned', 'archived')
              AND ($4::boolean = true OR must_payoff = true)
              AND (
                (payoff_deadline_chapter IS NOT NULL AND payoff_deadline_chapter < $2)
                OR ($3::int IS NOT NULL AND payoff_deadline_volume IS NOT NULL AND payoff_deadline_volume < $3)
              )
            ORDER BY
              CASE overdue_policy
                WHEN 'block' THEN 1
                WHEN 'escalate' THEN 2
                WHEN 'warn' THEN 3
                ELSE 4
              END,
              must_payoff DESC,
              payoff_deadline_chapter NULLS LAST,
              updated_at DESC
            LIMIT $5
            """,
            project_id,
            current_chapter_no,
            current_volume_no,
            include_optional,
            limit,
        )
        return rows_to_dicts(rows)

    async def link_foreshadowing(
        self,
        project_id: str,
        key: str,
        parent_key: str | None = None,
        related_keys: list[str] | None = None,
        trigger_on_payoff_keys: list[str] | None = None,
        blocks_payoff_until_keys: list[str] | None = None,
        replace: bool = False,
    ) -> dict[str, Any]:
        async with self._db.acquire() as conn:
            row = await conn.fetchrow(
                """
                SELECT id, key, related_foreshadowing_ids, trigger_on_payoff_ids,
                       blocks_payoff_until_ids
                FROM foreshadowing
                WHERE project_id = $1 AND key = $2
                """,
                project_id,
                key,
            )
            if row is None:
                raise ValueError(f"Foreshadowing not found: {key}")
            parent_id = None
            if parent_key:
                parent = await conn.fetchrow(
                    "SELECT id FROM foreshadowing WHERE project_id = $1 AND key = $2",
                    project_id,
                    parent_key,
                )
                if parent is None:
                    raise ValueError(f"Parent foreshadowing not found: {parent_key}")
                parent_id = parent["id"]

            def merge(existing, incoming):
                if incoming is None:
                    return list(existing or [])
                if replace:
                    return list(dict.fromkeys(incoming))
                return list(dict.fromkeys([*(existing or []), *incoming]))

            updated = await conn.fetchrow(
                """
                UPDATE foreshadowing
                SET parent_foreshadowing_id = COALESCE($3::uuid, parent_foreshadowing_id),
                    related_foreshadowing_ids = $4::text[],
                    trigger_on_payoff_ids = $5::text[],
                    blocks_payoff_until_ids = $6::text[],
                    updated_at = now()
                WHERE project_id = $1 AND key = $2
                RETURNING id::text, key, title, status, importance, expected_payoff_range,
                          parent_foreshadowing_id::text, related_foreshadowing_ids,
                          trigger_on_payoff_ids, blocks_payoff_until_ids, layer, must_payoff,
                          payoff_deadline_chapter, payoff_deadline_volume, overdue_policy,
                          payoff_chapter_id::text, payload, created_at, updated_at
                """,
                project_id,
                key,
                parent_id,
                merge(row["related_foreshadowing_ids"], related_keys),
                merge(row["trigger_on_payoff_ids"], trigger_on_payoff_keys),
                merge(row["blocks_payoff_until_ids"], blocks_payoff_until_keys),
            )
        return row_to_dict(updated)

    async def payoff_foreshadowing(
        self,
        project_id: str,
        key: str,
        payoff_chapter_no: int | None = None,
        payoff_chapter_id: str | None = None,
        payoff_note: str | None = None,
        status: str = "paid_off",
        trigger_related: bool = True,
        metadata: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        async with self._db.acquire() as conn:
            async with conn.transaction():
                current = await conn.fetchrow(
                    """
                    SELECT id, key, status, trigger_on_payoff_ids
                    FROM foreshadowing
                    WHERE project_id = $1 AND key = $2
                    """,
                    project_id,
                    key,
                )
                if current is None:
                    raise ValueError(f"Foreshadowing not found: {key}")
                if current["status"] == "paid_off":
                    raise ValueError(f"伏笔 '{key}' 已被回收，禁止重复回收")
                if payoff_chapter_id is None and payoff_chapter_no is not None:
                    chapter = await conn.fetchrow(
                        "SELECT id FROM chapters WHERE project_id = $1 AND chapter_no = $2",
                        project_id,
                        payoff_chapter_no,
                    )
                    payoff_chapter_id = str(chapter["id"]) if chapter else None
                if payoff_chapter_no is not None and payoff_chapter_id is None:
                    raise ValueError(f"章节不存在: chapter_no={payoff_chapter_no}")
                row = await conn.fetchrow(
                    """
                    UPDATE foreshadowing
                    SET status = $3,
                        payoff_chapter_id = COALESCE($4::uuid, payoff_chapter_id),
                        payload = payload
                          || jsonb_build_object(
                               'payoff_note', $5::text,
                               'payoff_chapter_no', $6::int,
                               'payoff_at', to_jsonb(now())
                             )
                          || $7::jsonb,
                        updated_at = now()
                    WHERE project_id = $1 AND key = $2
                    RETURNING id::text, key, title, status, importance, expected_payoff_range,
                              parent_foreshadowing_id::text, related_foreshadowing_ids,
                              trigger_on_payoff_ids, blocks_payoff_until_ids, layer, must_payoff,
                              payoff_deadline_chapter, payoff_deadline_volume, overdue_policy,
                              payoff_chapter_id::text, payload, created_at, updated_at
                    """,
                    project_id,
                    key,
                    status,
                    payoff_chapter_id,
                    payoff_note,
                    payoff_chapter_no,
                    json_dumps(metadata or {}),
                )
                triggered = []
                trigger_keys = list(current["trigger_on_payoff_ids"] or [])
                if trigger_related and trigger_keys:
                    triggered_rows = await conn.fetch(
                        """
                        UPDATE foreshadowing
                        SET status = CASE WHEN status = 'planted' THEN 'developing' ELSE status END,
                            payload = payload || jsonb_build_object('triggered_by_payoff_key', $2::text),
                            updated_at = now()
                        WHERE project_id = $1 AND key = ANY($3::text[])
                        RETURNING id::text, key, title, status
                        """,
                        project_id,
                        key,
                        trigger_keys,
                    )
                    triggered = rows_to_dicts(triggered_rows)
        result = row_to_dict(row)
        result["triggered"] = triggered
        return result

    async def list_chapter_plans(
        self,
        project_id: str,
        status: str | None = None,
        limit: int = 100,
    ) -> list[dict[str, Any]]:
        rows = await self._db.fetch(
            """
            SELECT id::text, chapter_no, plan, status, created_at, updated_at
            FROM chapter_plans
            WHERE project_id = $1
              AND ($2::text IS NULL OR status = $2)
            ORDER BY chapter_no DESC, created_at DESC
            LIMIT $3
            """,
            project_id,
            status,
            limit,
        )
        return rows_to_dicts(rows)

    async def create_chapter_plan(
        self,
        project_id: str,
        chapter_no: int,
        plan: dict[str, Any],
        username: str,
    ) -> dict[str, Any]:
        row = await self._db.fetchrow(
            """
            INSERT INTO chapter_plans (project_id, chapter_no, plan, status, created_by)
            SELECT $1, $2, $3::jsonb, 'planned', users.id
            FROM users
            WHERE users.username = $4
            RETURNING id::text, chapter_no, plan, status, created_at, updated_at
            """,
            project_id,
            chapter_no,
            json_dumps(plan),
            username,
        )
        if row is None:
            raise ValueError(f"User not found: {username}")
        return row_to_dict(row)

    async def delete_thread(self, project_id: str, key: str) -> dict[str, Any]:
        """软删除剧情线"""
        row = await self._db.fetchrow(
            "UPDATE plot_threads SET is_deleted = true WHERE project_id = $1 AND key = $2 RETURNING key, title",
            project_id, key,
        )
        if not row:
            raise ValueError(f"情节线不存在: {key}")
        return {"deleted": True, "key": row["key"], "title": row["title"]}
