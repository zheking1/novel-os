"""
Causality Chain Tracking Service

Tracks causal relationships between events for 20M+ character novels:
  Event A → causes → Event B → triggers → Foreshadowing C → payoff → Event D
"""

from datetime import datetime
from typing import Any

from .db import Database
from .utils import json_dumps, row_to_dict, rows_to_dicts


class CausalityService:
    """Tracks causal chains between events."""

    def __init__(self, db: Database):
        self._db = db

    # ------------------------------------------------------------------
    # Chain Recording
    # ------------------------------------------------------------------

    async def record_cause(
        self,
        project_id: str,
        cause_event_id: str | None = None,
        cause_chapter_no: int | None = None,
        cause_title: str | None = None,
        effect_event_id: str | None = None,
        effect_chapter_no: int | None = None,
        effect_title: str | None = None,
        causal_type: str = "direct",
        strength: float = 1.0,
        description: str | None = None,
        metadata: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        """Record a causal link between two events."""
        async with self._db.acquire() as conn:
            async with conn.transaction():
                row = await conn.fetchrow(
                    """
                    INSERT INTO causality_chains
                      (project_id, cause_event_id, cause_chapter_no, cause_title,
                       effect_event_id, effect_chapter_no, effect_title,
                       causal_type, strength, description, metadata)
                    VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11::jsonb)
                    RETURNING id::text, cause_chapter_no, effect_chapter_no,
                              causal_type, strength, description, created_at
                    """,
                    project_id,
                    cause_event_id,
                    cause_chapter_no,
                    cause_title,
                    effect_event_id,
                    effect_chapter_no,
                    effect_title,
                    causal_type,
                    strength,
                    description,
                    json_dumps(metadata or {}),
                )
        return row_to_dict(row)

    async def record_chain(
        self,
        project_id: str,
        chain: list[dict[str, Any]],
    ) -> dict[str, Any]:
        """Record a full causal chain from a list of events.

        Each item: {chapter_no, title, event_id?, causal_type?, description?}
        """
        if len(chain) < 2:
            return {"ok": False, "reason": "chain needs at least 2 events"}

        results = []
        for i in range(len(chain) - 1):
            src = chain[i]
            dst = chain[i + 1]
            r = await self.record_cause(
                project_id,
                cause_event_id=src.get("event_id"),
                cause_chapter_no=src.get("chapter_no"),
                cause_title=src.get("title"),
                effect_event_id=dst.get("event_id"),
                effect_chapter_no=dst.get("chapter_no"),
                effect_title=dst.get("title"),
                causal_type=dst.get("causal_type", "direct"),
                strength=dst.get("strength", 1.0),
                description=dst.get("description"),
            )
            results.append(r)

        return {"ok": True, "links_created": len(results), "chain": results}

    # ------------------------------------------------------------------
    # Chain Querying — PostgreSQL CTE recursive (no Python recursion)
    # ------------------------------------------------------------------

    async def get_chain_from_event(
        self,
        project_id: str,
        event_id: str,
        depth: int = 5,
    ) -> list[dict[str, Any]]:
        """Get causal chain forward from an event using PostgreSQL CTE."""
        rows = await self._db.fetch(
            """
            WITH RECURSIVE chain AS (
                SELECT id::text, cause_event_id, effect_event_id, cause_chapter_no,
                       effect_chapter_no, cause_title, effect_title,
                       causal_type, strength, description, 1 AS depth
                FROM causality_chains
                WHERE project_id = $1 AND cause_event_id = $2

                UNION ALL

                SELECT cc.id::text, cc.cause_event_id, cc.effect_event_id,
                       cc.cause_chapter_no, cc.effect_chapter_no,
                       cc.cause_title, cc.effect_title,
                       cc.causal_type, cc.strength, cc.description, ch.depth + 1
                FROM causality_chains cc
                JOIN chain ch ON cc.project_id = $1 AND cc.cause_event_id = ch.effect_event_id
                WHERE ch.depth < $3
            )
            SELECT DISTINCT ON (id) * FROM chain ORDER BY id, depth
            """,
            project_id,
            event_id,
            depth,
        )
        return rows_to_dicts(rows)

    async def get_chain_to_event(
        self,
        project_id: str,
        event_id: str,
        depth: int = 5,
    ) -> list[dict[str, Any]]:
        """Get causal chain backward to an event using PostgreSQL CTE."""
        rows = await self._db.fetch(
            """
            WITH RECURSIVE chain AS (
                SELECT id::text, cause_event_id, effect_event_id, cause_chapter_no,
                       effect_chapter_no, cause_title, effect_title,
                       causal_type, strength, description, 1 AS depth
                FROM causality_chains
                WHERE project_id = $1 AND effect_event_id = $2

                UNION ALL

                SELECT cc.id::text, cc.cause_event_id, cc.effect_event_id,
                       cc.cause_chapter_no, cc.effect_chapter_no,
                       cc.cause_title, cc.effect_title,
                       cc.causal_type, cc.strength, cc.description, ch.depth + 1
                FROM causality_chains cc
                JOIN chain ch ON cc.project_id = $1 AND cc.effect_event_id = ch.cause_event_id
                WHERE ch.depth < $3
            )
            SELECT DISTINCT ON (id) * FROM chain ORDER BY id, depth
            """,
            project_id,
            event_id,
            depth,
        )
        return rows_to_dicts(rows)

    async def get_chains_in_chapter_range(
        self,
        project_id: str,
        start_chapter: int,
        end_chapter: int,
        causal_type: str | None = None,
        limit: int = 100,
    ) -> list[dict[str, Any]]:
        """Get all causal links in a chapter range."""
        conditions = [
            "project_id = $1",
            "(cause_chapter_no >= $2 OR cause_chapter_no IS NULL)",
            "(effect_chapter_no <= $3 OR effect_chapter_no IS NULL)",
        ]
        params: list[Any] = [project_id, start_chapter, end_chapter]
        idx = 4
        if causal_type:
            conditions.append(f"causal_type = ${idx}")
            params.append(causal_type)
            idx += 1
        params.append(limit)
        rows = await self._db.fetch(
            f"""
            SELECT id::text, cause_event_id, effect_event_id,
                   cause_chapter_no, effect_chapter_no,
                   cause_title, effect_title,
                   causal_type, strength, description, created_at
            FROM causality_chains
            WHERE {' AND '.join(conditions)}
            ORDER BY cause_chapter_no, effect_chapter_no
            LIMIT ${idx}
            """,
            *params,
        )
        return rows_to_dicts(rows)

    # ------------------------------------------------------------------
    # Unresolved Causality Detection
    # ------------------------------------------------------------------

    async def find_unresolved_causes(
        self,
        project_id: str,
        up_to_chapter: int,
        limit: int = 50,
    ) -> list[dict[str, Any]]:
        """Find cause events that have no recorded effect yet."""
        rows = await self._db.fetch(
            """
            SELECT DISTINCT cc.cause_event_id, cc.cause_chapter_no, cc.cause_title,
                   cc.description AS cause_description
            FROM causality_chains cc
            WHERE cc.project_id = $1
              AND cc.cause_chapter_no <= $2
              AND cc.cause_event_id IS NOT NULL
              AND NOT EXISTS (
                SELECT 1 FROM causality_chains cc2
                WHERE cc2.project_id = $1 AND cc2.cause_event_id = cc.effect_event_id
              )
            ORDER BY cc.cause_chapter_no DESC
            LIMIT $3
            """,
            project_id,
            up_to_chapter,
            limit,
        )
        return rows_to_dicts(rows)

    async def find_dangling_effects(
        self,
        project_id: str,
        up_to_chapter: int,
        limit: int = 50,
    ) -> list[dict[str, Any]]:
        """Find effect events with no recorded cause."""
        rows = await self._db.fetch(
            """
            SELECT DISTINCT cc.effect_event_id, cc.effect_chapter_no, cc.effect_title,
                   cc.description AS effect_description
            FROM causality_chains cc
            WHERE cc.project_id = $1
              AND cc.effect_chapter_no <= $2
              AND cc.effect_event_id IS NOT NULL
              AND NOT EXISTS (
                SELECT 1 FROM causality_chains cc2
                WHERE cc2.project_id = $1 AND cc2.effect_event_id = cc.cause_event_id
              )
            ORDER BY cc.effect_chapter_no DESC
            LIMIT $3
            """,
            project_id,
            up_to_chapter,
            limit,
        )
        return rows_to_dicts(rows)

    # ------------------------------------------------------------------
    # Context-Friendly Summary
    # ------------------------------------------------------------------

    async def get_causality_summary_for_context(
        self,
        project_id: str,
        chapter_no: int,
        max_tokens: int = 300,
    ) -> str:
        """Get a compressed causality summary for context injection."""
        recent_chains = await self.get_chains_in_chapter_range(
            project_id,
            start_chapter=max(1, chapter_no - 20),
            end_chapter=chapter_no,
            limit=30,
        )
        if not recent_chains:
            return "No recent causal chains."

        lines = ["== Recent Causality Chains =="]
        for c in recent_chains:
            cause = c.get("cause_title") or f"Ch.{c.get('cause_chapter_no', '?')}"
            effect = c.get("effect_title") or f"Ch.{c.get('effect_chapter_no', '?')}"
            lines.append(f"  {cause} →[{c.get('causal_type', 'direct')}]→ {effect}")

        summary = "\n".join(lines)
        char_budget = max_tokens * 4
        if len(summary) > char_budget:
            summary = summary[:char_budget] + "..."
        return summary
