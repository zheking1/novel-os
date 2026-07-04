from typing import Any
from .db import Database
from .utils import row_to_dict, rows_to_dicts


class SkillService:
    """Skill 管理服务 - 使用已有的 skills 表结构"""

    def __init__(self, db: Database):
        self._db = db

    # ============================================================
    # Skills CRUD
    # ============================================================

    async def list_skills(self, active_only: bool = True) -> list[dict]:
        if active_only:
            rows = await self._db.fetch(
                "SELECT id::text, name, description, tags, scope, is_active, "
                "created_at, updated_at "
                "FROM skills WHERE is_active = true ORDER BY name"
            )
        else:
            rows = await self._db.fetch(
                "SELECT id::text, name, description, tags, scope, is_active, "
                "created_at, updated_at "
                "FROM skills ORDER BY name"
            )
        return rows_to_dicts(rows)

    async def get_skill(self, skill_id: str) -> dict | None:
        row = await self._db.fetchrow(
            "SELECT id::text, name, description, content, instruction, tags, scope, "
            "is_active, created_at, updated_at "
            "FROM skills WHERE id = $1", skill_id
        )
        if not row:
            return None
        skill = dict(row)
        skill["steps"] = await self.list_steps(skill_id)
        # Map tags to trigger_words for compatibility
        skill["trigger_words"] = skill.get("tags") or []
        return skill

    async def create_skill(
        self, name: str, description: str | None = None, content: str = "",
        trigger_words: list[str] | None = None, tool_hints: list[str] | None = None,
        sort_order: int = 0,
    ) -> dict:
        # Get a default user_id (use the first user or a system user)
        user_row = await self._db.fetchrow("SELECT id FROM users LIMIT 1")
        user_id = user_row["id"] if user_row else None
        
        if not user_id:
            raise ValueError("No user found in database")
        
        row = await self._db.fetchrow(
            "INSERT INTO skills (name, description, content, instruction, tags, scope, is_active, user_id) "
            "VALUES ($1, $2, $3, $4, $5, 'public', true, $6) "
            "RETURNING id::text, name, description, tags, scope, is_active, created_at",
            name, description, content, content, trigger_words or [], user_id,
        )
        return dict(row) if row else {}

    async def update_skill(
        self, skill_id: str, name: str | None = None, description: str | None = None,
        content: str | None = None, trigger_words: list[str] | None = None,
        tool_hints: list[str] | None = None, is_active: bool | None = None,
        sort_order: int | None = None,
    ) -> dict:
        sets, params, idx = [], [], 1
        if name is not None:
            sets.append(f"name = ${idx}"); params.append(name); idx += 1
        if description is not None:
            sets.append(f"description = ${idx}"); params.append(description); idx += 1
        if content is not None:
            sets.append(f"content = ${idx}"); params.append(content); idx += 1
            sets.append(f"instruction = ${idx}"); params.append(content); idx += 1
        if trigger_words is not None:
            sets.append(f"tags = ${idx}"); params.append(trigger_words); idx += 1
        if is_active is not None:
            sets.append(f"is_active = ${idx}"); params.append(is_active); idx += 1
        if not sets:
            return {}
        sets.append("updated_at = now()")
        params.append(skill_id)
        row = await self._db.fetchrow(
            f"UPDATE skills SET {', '.join(sets)} WHERE id = ${idx} "
            "RETURNING id::text, name, description, tags, scope, is_active, created_at, updated_at",
            *params,
        )
        return dict(row) if row else {}

    async def delete_skill(self, skill_id: str) -> bool:
        result = await self._db.execute("DELETE FROM skills WHERE id = $1", skill_id)
        return result and "DELETE" in result

    # ============================================================
    # Skill Steps
    # ============================================================

    async def list_steps(self, skill_id: str) -> list[dict]:
        rows = await self._db.fetch(
            "SELECT id::text, skill_id::text, step_order, step_name, tool_name, "
            "description, parameters, optional, conditional "
            "FROM skill_steps WHERE skill_id = $1 ORDER BY step_order",
            skill_id,
        )
        return rows_to_dicts(rows)

    async def add_step(
        self, skill_id: str, step_order: int, step_name: str,
        tool_name: str | None = None, description: str | None = None,
        parameters: dict | None = None, optional: bool = False,
        conditional: str | None = None,
    ) -> dict:
        row = await self._db.fetchrow(
            "INSERT INTO skill_steps (skill_id, step_order, step_name, tool_name, description, parameters, optional, conditional) "
            "VALUES ($1, $2, $3, $4, $5, $6::jsonb, $7, $8) "
            "RETURNING id::text, skill_id::text, step_order, step_name, tool_name, description, parameters, optional, conditional",
            skill_id, step_order, step_name, tool_name, description,
            parameters or {}, optional, conditional,
        )
        return dict(row) if row else {}

    async def update_step(
        self, step_id: str, step_order: int | None = None, step_name: str | None = None,
        tool_name: str | None = None, description: str | None = None,
        parameters: dict | None = None, optional: bool | None = None,
        conditional: str | None = None,
    ) -> dict:
        sets, params, idx = [], [], 1
        if step_order is not None:
            sets.append(f"step_order = ${idx}"); params.append(step_order); idx += 1
        if step_name is not None:
            sets.append(f"step_name = ${idx}"); params.append(step_name); idx += 1
        if tool_name is not None:
            sets.append(f"tool_name = ${idx}"); params.append(tool_name); idx += 1
        if description is not None:
            sets.append(f"description = ${idx}"); params.append(description); idx += 1
        if parameters is not None:
            sets.append(f"parameters = ${idx}::jsonb"); params.append(parameters); idx += 1
        if optional is not None:
            sets.append(f"optional = ${idx}"); params.append(optional); idx += 1
        if conditional is not None:
            sets.append(f"conditional = ${idx}"); params.append(conditional); idx += 1
        if not sets:
            return {}
        params.append(step_id)
        row = await self._db.fetchrow(
            f"UPDATE skill_steps SET {', '.join(sets)} WHERE id = ${idx} "
            "RETURNING id::text, skill_id::text, step_order, step_name, tool_name, description, parameters, optional, conditional",
            *params,
        )
        return dict(row) if row else {}

    async def delete_step(self, step_id: str) -> bool:
        result = await self._db.execute("DELETE FROM skill_steps WHERE id = $1", step_id)
        return result and "DELETE" in result

    async def delete_steps_by_skill(self, skill_id: str) -> bool:
        result = await self._db.execute("DELETE FROM skill_steps WHERE skill_id = $1", skill_id)
        return result and "DELETE" in result

    # ============================================================
    # Semantic Matching
    # ============================================================

    async def match_skills(self, query: str, limit: int = 3) -> list[dict]:
        """Match skills by keyword similarity."""
        rows = await self._db.fetch(
            """
            SELECT id::text, name, description, content, instruction, tags, scope,
                   ts_rank_cd(
                       to_tsvector('simple', COALESCE(name, '') || ' ' || COALESCE(description, '') || ' ' || array_to_string(tags, ' ')),
                       plainto_tsquery('simple', $1)
                   ) as rank
            FROM skills
            WHERE is_active = true
              AND to_tsvector('simple', COALESCE(name, '') || ' ' || COALESCE(description, '') || ' ' || array_to_string(tags, ' '))
                  @@ plainto_tsquery('simple', $1)
            ORDER BY rank DESC
            LIMIT $2
            """,
            query, limit,
        )
        result = rows_to_dicts(rows)
        for skill in result:
            skill["steps"] = await self.list_steps(skill["id"])
            skill["trigger_words"] = skill.get("tags") or []
        return result

    async def get_skill_by_name(self, name: str) -> dict | None:
        """Get skill by exact name."""
        row = await self._db.fetchrow(
            "SELECT id::text, name, description, content, instruction, tags, scope, "
            "is_active, created_at, updated_at "
            "FROM skills WHERE name = $1", name
        )
        if not row:
            return None
        skill = dict(row)
        skill["steps"] = await self.list_steps(skill["id"])
        skill["trigger_words"] = skill.get("tags") or []
        return skill
