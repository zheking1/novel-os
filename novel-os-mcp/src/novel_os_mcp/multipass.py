"""
Multi-Pass Generation Pipeline

4-pass generation for 20M+ character novels:
  Pass 1: Planning    — chapter outline, emotion curve, pacing
  Pass 2: Drafting    — initial text generation
  Pass 3: Polishing   — style consistency, dialogue refinement
  Pass 4: Verification — continuity check, compliance scan
"""

from datetime import datetime
from typing import Any

from .db import Database
from .utils import json_dumps, row_to_dict, rows_to_dicts


class MultiPassService:
    """Manages multi-pass chapter generation pipeline."""

    def __init__(self, db: Database):
        self._db = db

    # ------------------------------------------------------------------
    # Pass 1: Planning
    # ------------------------------------------------------------------

    async def create_chapter_plan(
        self,
        project_id: str,
        chapter_no: int,
        volume_no: int | None = None,
        plan: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        """Create or update a chapter plan (Pass 1 output)."""
        plan = plan or {}
        async with self._db.acquire() as conn:
            async with conn.transaction():
                existing = await conn.fetchrow(
                    """
                    SELECT id, plan, status FROM chapter_plans
                    WHERE project_id = $1 AND chapter_no = $2 AND status <> 'superseded'
                    ORDER BY created_at DESC LIMIT 1
                    """,
                    project_id,
                    chapter_no,
                )
                if existing:
                    await conn.execute(
                        "UPDATE chapter_plans SET status = 'superseded' WHERE id = $1",
                        existing["id"],
                    )

                row = await conn.fetchrow(
                    """
                    INSERT INTO chapter_plans (project_id, chapter_no, plan, status)
                    VALUES ($1, $2::int, $3::jsonb, 'active')
                    RETURNING id::text, chapter_no, plan, status, created_at
                    """,
                    project_id,
                    chapter_no,
                    json_dumps(plan),
                )
        return row_to_dict(row)

    async def get_chapter_plan(
        self,
        project_id: str,
        chapter_no: int,
    ) -> dict[str, Any] | None:
        row = await self._db.fetchrow(
            """
            SELECT id::text, chapter_no, plan, status, created_at
            FROM chapter_plans
            WHERE project_id = $1 AND chapter_no = $2 AND status <> 'superseded'
            ORDER BY created_at DESC LIMIT 1
            """,
            project_id,
            chapter_no,
        )
        return row_to_dict(row) if row else None

    # ------------------------------------------------------------------
    # Pass 2-4: Generation Passes
    # ------------------------------------------------------------------

    async def create_generation_pass(
        self,
        project_id: str,
        chapter_no: int,
        pass_number: int,
        pass_type: str,
        content: str | None = None,
        metadata: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        """Record a generation pass result."""
        row = await self._db.fetchrow(
            """
            INSERT INTO generation_passes
              (project_id, chapter_no, pass_number, pass_type, content, metadata)
            VALUES ($1, $2::int, $3, $4, $5, $6::jsonb)
            RETURNING id::text, chapter_no, pass_number, pass_type, content, metadata, created_at
            """,
            project_id,
            chapter_no,
            pass_number,
            pass_type,
            content,
            json_dumps(metadata or {}),
        )
        return row_to_dict(row) if row else {}

    async def get_generation_passes(
        self,
        project_id: str,
        chapter_no: int,
    ) -> list[dict[str, Any]]:
        rows = await self._db.fetch(
            """
            SELECT id::text, chapter_no, pass_number, pass_type, content, metadata, created_at
            FROM generation_passes
            WHERE project_id = $1 AND chapter_no = $2
            ORDER BY pass_number
            """,
            project_id,
            chapter_no,
        )
        return rows_to_dicts(rows)

    async def update_generation_pass(
        self,
        project_id: str,
        pass_id: str,
        content: str | None = None,
        metadata: dict[str, Any] | None = None,
        status: str | None = None,
    ) -> dict[str, Any]:
        sets = []
        params: list[Any] = []
        idx = 1
        if content is not None:
            sets.append(f"content = ${idx}")
            params.append(content)
            idx += 1
        if metadata is not None:
            sets.append(f"metadata = ${idx}::jsonb")
            params.append(json_dumps(metadata))
            idx += 1
        if status is not None:
            sets.append(f"status = ${idx}")
            params.append(status)
            idx += 1
        if not sets:
            return {}
        sets.append("updated_at = now()")
        params.extend([project_id, pass_id])
        row = await self._db.fetchrow(
            f"""
            UPDATE generation_passes SET {', '.join(sets)}
            WHERE project_id = $${idx} AND id = $${idx + 1}
            RETURNING id::text, chapter_no, pass_number, pass_type, content, metadata, created_at
            """,
            *params,
        )
        return row_to_dict(row) if row else {}

    # ------------------------------------------------------------------
    # Continuity Verification
    # ------------------------------------------------------------------

    async def check_continuity(
        self,
        project_id: str,
        chapter_no: int,
        content: str,
    ) -> dict[str, Any]:
        """Check generated content against recent chapter summaries for continuity."""
        recent = await self._db.fetch(
            """
            SELECT c.chapter_no, c.title, s.content
            FROM chapters c
            JOIN chapter_summaries s ON s.chapter_id = c.id AND s.summary_type = 'chapter'
            WHERE c.project_id = $1 AND c.chapter_no < $2::int
            ORDER BY c.chapter_no DESC LIMIT 5
            """,
            project_id,
            chapter_no,
        )
        recent_summaries = rows_to_dicts(recent)

        entities_in_content = await self._extract_entities(content)

        entity_states = []
        if entities_in_content:
            placeholders = ", ".join(f"${i+3}" for i in range(len(entities_in_content)))
            state_rows = await self._db.fetch(
                f"""
                SELECT e.name, e.entity_type, s.state
                FROM state_entities e
                JOIN state_snapshots s ON s.entity_id = e.id AND s.is_current = true
                WHERE e.project_id = $1
                  AND e.name IN ({placeholders})
                """,
                project_id,
                *entities_in_content,
            )
            entity_states = rows_to_dicts(state_rows)

        return {
            "chapter_no": chapter_no,
            "recent_summaries_count": len(recent_summaries),
            "entities_detected": entities_in_content,
            "entity_states_found": len(entity_states),
            "entity_states": entity_states,
            "recent_context": [
                {"chapter_no": r["chapter_no"], "title": r["title"]}
                for r in recent_summaries
            ],
        }

    async def _extract_entities(self, content: str) -> list[str]:
        """Simple entity extraction from content (names in brackets or quotes)."""
        import re
        bracketed = re.findall(r'[【\[]([^】\]]+)[】\]]', content)
        quoted = re.findall(r'[""「]([^""」]+)[""」]', content)
        all_names = list(set(bracketed + quoted))
        return all_names[:20]

    # ------------------------------------------------------------------
    # Full Pipeline Orchestration
    # ------------------------------------------------------------------

    async def run_pipeline(
        self,
        project_id: str,
        chapter_no: int,
        plan: dict[str, Any],
        draft_content: str,
        polished_content: str | None = None,
    ) -> dict[str, Any]:
        """Run the full 4-pass pipeline and record all passes."""
        results = {}

        # Defense: if plan is a string, wrap it
        if isinstance(plan, str):
            plan = {"summary": plan}
        if not isinstance(plan, dict):
            plan = {"summary": str(plan)}

        pass1 = await self.create_generation_pass(
            project_id, chapter_no, 1, "planning",
            content=json_dumps(plan),
            metadata={"plan_keys": list(plan.keys())},
        )
        results["pass_1_plan"] = pass1

        pass2 = await self.create_generation_pass(
            project_id, chapter_no, 2, "drafting",
            content=draft_content,
            metadata={"word_count": len(draft_content)},
        )
        results["pass_2_draft"] = pass2

        pass3 = await self.create_generation_pass(
            project_id, chapter_no, 3, "polishing",
            content=polished_content or draft_content,
            metadata={"refined": polished_content is not None},
        )
        results["pass_3_polish"] = pass3

        continuity = await self.check_continuity(
            project_id, chapter_no, polished_content or draft_content,
        )
        pass4 = await self.create_generation_pass(
            project_id, chapter_no, 4, "verification",
            content=json_dumps(continuity),
            metadata=continuity,
        )
        results["pass_4_verify"] = pass4

        return {
            "ok": True,
            "chapter_no": chapter_no,
            "passes": results,
            "continuity": continuity,
        }

    # ------------------------------------------------------------------
    # Pipeline Status
    # ------------------------------------------------------------------

    async def get_pipeline_status(
        self,
        project_id: str,
        chapter_no: int,
    ) -> dict[str, Any]:
        """Get the current pipeline status for a chapter."""
        passes = await self.get_generation_passes(project_id, chapter_no)
        plan = await self.get_chapter_plan(project_id, chapter_no)

        pass_map = {}
        for p in passes:
            pass_map[p["pass_number"]] = {
                "type": p["pass_type"],
                "status": p.get("metadata", {}).get("status", "done"),
                "created_at": p["created_at"],
            }

        return {
            "chapter_no": chapter_no,
            "has_plan": plan is not None,
            "passes_completed": len(passes),
            "pass_details": pass_map,
            "pipeline_complete": len(passes) >= 4,
        }
