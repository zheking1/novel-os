"""
Character Arc Tracking Service

Tracks dynamic character evolution across 20M+ character novels:
  - Emotional state changes
  - Relationship evolution
  - Skill/power progression
  - Personality shifts
"""

from datetime import datetime
from typing import Any

from .db import Database
from .utils import json_dumps, row_to_dict, rows_to_dicts, ensure_json_value


class CharacterArcService:
    """Tracks character evolution across chapters and volumes."""

    def __init__(self, db: Database):
        self._db = db

    # ------------------------------------------------------------------
    # Arc Recording
    # ------------------------------------------------------------------

    async def record_arc_point(
        self,
        project_id: str,
        character_name: str,
        chapter_no: int,
        arc_type: str,
        state: dict[str, Any],
        change_summary: str | None = None,
        trigger_event: str | None = None,
        metadata: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        """Record a character arc evolution point."""
        entity = await self._resolve_character(project_id, character_name)

        async with self._db.acquire() as conn:
            async with conn.transaction():
                row = await conn.fetchrow(
                    """
                    INSERT INTO character_arcs
                      (project_id, entity_id, chapter_no, arc_type, state,
                       change_summary, trigger_event, metadata)
                    VALUES ($1, $2, $3, $4, $5::jsonb, $6, $7, $8::jsonb)
                    RETURNING id::text, chapter_no, arc_type, state, change_summary,
                              trigger_event, metadata, created_at
                    """,
                    project_id,
                    entity["id"],
                    chapter_no,
                    arc_type,
                    json_dumps(state),
                    change_summary,
                    trigger_event,
                    json_dumps(metadata or {}),
                )

        return {
            "ok": True,
            "character": character_name,
            **row_to_dict(row),
        }

    async def record_emotion(
        self,
        project_id: str,
        character_name: str,
        chapter_no: int,
        emotion: str,
        intensity: float,
        cause: str | None = None,
    ) -> dict[str, Any]:
        """Record emotional state."""
        return await self.record_arc_point(
            project_id, character_name, chapter_no,
            arc_type="emotion",
            state={"emotion": emotion, "intensity": intensity},
            change_summary=f"{emotion} (intensity: {intensity})",
            trigger_event=cause,
        )

    async def record_relationship_change(
        self,
        project_id: str,
        character_name: str,
        chapter_no: int,
        target_name: str,
        old_relation: str,
        new_relation: str,
        cause: str | None = None,
    ) -> dict[str, Any]:
        """Record relationship evolution."""
        return await self.record_arc_point(
            project_id, character_name, chapter_no,
            arc_type="relationship",
            state={
                "target": target_name,
                "old_relation": old_relation,
                "new_relation": new_relation,
            },
            change_summary=f"{old_relation} → {new_relation} with {target_name}",
            trigger_event=cause,
        )

    async def record_power_change(
        self,
        project_id: str,
        character_name: str,
        chapter_no: int,
        old_level: str,
        new_level: str,
        method: str | None = None,
    ) -> dict[str, Any]:
        """Record power/skill level change."""
        return await self.record_arc_point(
            project_id, character_name, chapter_no,
            arc_type="power",
            state={"old_level": old_level, "new_level": new_level, "method": method},
            change_summary=f"{old_level} → {new_level}",
            trigger_event=method,
        )

    async def record_personality_shift(
        self,
        project_id: str,
        character_name: str,
        chapter_no: int,
        trait: str,
        old_value: Any,
        new_value: Any,
        reason: str | None = None,
    ) -> dict[str, Any]:
        """Record personality trait change."""
        return await self.record_arc_point(
            project_id, character_name, chapter_no,
            arc_type="personality",
            state={"trait": trait, "old_value": old_value, "new_value": new_value},
            change_summary=f"{trait}: {old_value} → {new_value}",
            trigger_event=reason,
        )

    # ------------------------------------------------------------------
    # Arc Querying
    # ------------------------------------------------------------------

    async def get_character_arc(
        self,
        project_id: str,
        character_name: str,
        arc_type: str | None = None,
        from_chapter: int | None = None,
        to_chapter: int | None = None,
        limit: int = 100,
    ) -> list[dict[str, Any]]:
        """Get arc history for a character."""
        entity = await self._resolve_character(project_id, character_name)
        conditions = ["project_id = $1", "entity_id = $2"]
        params: list[Any] = [project_id, entity["id"]]
        idx = 3
        if arc_type:
            conditions.append(f"arc_type = ${idx}")
            params.append(arc_type)
            idx += 1
        if from_chapter is not None:
            conditions.append(f"chapter_no >= ${idx}")
            params.append(from_chapter)
            idx += 1
        if to_chapter is not None:
            conditions.append(f"chapter_no <= ${idx}")
            params.append(to_chapter)
            idx += 1
        params.append(limit)
        rows = await self._db.fetch(
            f"""
            SELECT id::text, chapter_no, arc_type, state, change_summary,
                   trigger_event, metadata, created_at
            FROM character_arcs
            WHERE {' AND '.join(conditions)}
            ORDER BY chapter_no
            LIMIT ${idx}
            """,
            *params,
        )
        return rows_to_dicts(rows)

    async def get_latest_arc_state(
        self,
        project_id: str,
        character_name: str,
    ) -> dict[str, Any]:
        """Get the latest arc state for a character (all arc types)."""
        entity = await self._resolve_character(project_id, character_name)
        rows = await self._db.fetch(
            """
            SELECT DISTINCT ON (arc_type)
                   arc_type, state, chapter_no, change_summary, created_at
            FROM character_arcs
            WHERE project_id = $1 AND entity_id = $2
            ORDER BY arc_type, chapter_no DESC
            """,
            project_id,
            entity["id"],
        )
        state = {}
        for row in rows:
            state[row["arc_type"]] = {
                "state": ensure_json_value(row["state"]),
                "chapter_no": row["chapter_no"],
                "change_summary": row["change_summary"],
            }
        return {
            "character": character_name,
            "arc_state": state,
        }

    async def get_emotion_timeline(
        self,
        project_id: str,
        character_name: str,
        from_chapter: int | None = None,
        to_chapter: int | None = None,
    ) -> list[dict[str, Any]]:
        """Get emotion timeline for a character."""
        return await self.get_character_arc(
            project_id, character_name,
            arc_type="emotion",
            from_chapter=from_chapter,
            to_chapter=to_chapter,
        )

    async def get_power_progression(
        self,
        project_id: str,
        character_name: str,
    ) -> list[dict[str, Any]]:
        """Get power progression timeline."""
        return await self.get_character_arc(
            project_id, character_name,
            arc_type="power",
        )

    async def get_relationship_evolution(
        self,
        project_id: str,
        character_name: str,
        target_name: str | None = None,
    ) -> list[dict[str, Any]]:
        """Get relationship evolution timeline."""
        arcs = await self.get_character_arc(
            project_id, character_name,
            arc_type="relationship",
        )
        if target_name:
            arcs = [
                a for a in arcs
                if (a.get("state") or {}).get("target") == target_name
            ]
        return arcs

    # ------------------------------------------------------------------
    # Arc Compression for Context
    # ------------------------------------------------------------------

    async def get_arc_summary_for_context(
        self,
        project_id: str,
        character_name: str,
        current_chapter: int,
        max_tokens: int = 200,
    ) -> str:
        """Get a compressed arc summary suitable for context injection."""
        entity = await self._resolve_character(project_id, character_name)
        rows = await self._db.fetch(
            """
            SELECT arc_type, state, change_summary, chapter_no
            FROM character_arcs
            WHERE project_id = $1 AND entity_id = $2 AND chapter_no <= $3
            ORDER BY chapter_no DESC
            LIMIT 20
            """,
            project_id,
            entity["id"],
            current_chapter,
        )
        if not rows:
            return f"{character_name}: no arc data"

        recent = list(reversed(rows_to_dicts(rows)))
        lines = [f"== {character_name} Arc =="]
        for r in recent:
            lines.append(f"  Ch.{r['chapter_no']}: [{r['arc_type']}] {r.get('change_summary', '')}")

        summary = "\n".join(lines)
        char_budget = max_tokens * 4
        if len(summary) > char_budget:
            summary = summary[:char_budget] + "..."
        return summary

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------

    async def _resolve_character(self, project_id: str, name: str) -> dict[str, Any]:
        row = await self._db.fetchrow(
            """
            SELECT id, entity_type, name FROM state_entities
            WHERE project_id = $1 AND entity_type = 'character' AND name = $2
            """,
            project_id,
            name,
        )
        if row is None:
            row = await self._db.fetchrow(
                """
                INSERT INTO state_entities (project_id, entity_type, name)
                VALUES ($1, 'character', $2)
                ON CONFLICT (project_id, entity_type, name)
                DO UPDATE SET updated_at = now()
                RETURNING id, entity_type, name
                """,
                project_id,
                name,
            )
        return dict(row)

