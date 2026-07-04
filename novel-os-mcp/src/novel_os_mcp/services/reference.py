import logging
from typing import Any

from ..db import Database
from ..utils import json_dumps, row_to_dict, rows_to_dicts

logger = logging.getLogger("novel_os_mcp.services.reference")


class ReferenceService:
    """参考文献服务 - 管理参考文献库"""

    def __init__(self, db: Database):
        self._db = db

    async def get_references(
        self,
        project_id: str,
        category: str | None = None,
        limit: int = 100,
        offset: int = 0,
    ) -> dict[str, Any]:
        conditions = ["project_id = $1"]
        params: list[Any] = [project_id]
        idx = 2

        if category:
            conditions.append(f"category = ${idx}")
            params.append(category)
            idx += 1

        where = " AND ".join(conditions)

        count_row = await self._db.fetchrow(
            f"SELECT COUNT(*)::int AS total FROM reference_materials WHERE {where}",
            *params,
        )
        total = count_row["total"] if count_row else 0

        params.extend([limit, offset])
        rows = await self._db.fetch(
            f"""
            SELECT id::text, project_id::text, title, author, source_type, source_url,
                   category, tags, excerpt, notes, reliability_score, created_at, updated_at
            FROM reference_materials
            WHERE {where}
            ORDER BY created_at DESC
            LIMIT ${idx} OFFSET ${idx + 1}
            """,
            *params,
        )
        items = []
        for row in rows:
            r = row_to_dict(row)
            r["tags"] = list(r.get("tags") or [])
            items.append(r)
        return {"items": items, "total": total, "limit": limit, "offset": offset}

    async def create_reference(
        self,
        project_id: str,
        title: str,
        author: str | None = None,
        source_type: str = "web",
        source_url: str | None = None,
        category: str | None = None,
        tags: list[str] | None = None,
        excerpt: str | None = None,
        notes: str | None = None,
        reliability_score: float | None = None,
    ) -> dict[str, Any]:
        row = await self._db.fetchrow(
            """
            INSERT INTO reference_materials
              (project_id, title, author, source_type, source_url, category, tags, excerpt, notes, reliability_score)
            VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10)
            RETURNING id::text, project_id::text, title, author, source_type, source_url,
                      category, tags, excerpt, notes, reliability_score, created_at, updated_at
            """,
            project_id,
            title,
            author,
            source_type,
            source_url,
            category,
            json_dumps(tags) if tags else None,
            excerpt,
            notes,
            reliability_score,
        )
        r = row_to_dict(row)
        r["tags"] = list(r.get("tags") or [])
        return r

    async def update_reference(
        self,
        reference_id: str,
        title: str | None = None,
        author: str | None = None,
        source_type: str | None = None,
        source_url: str | None = None,
        category: str | None = None,
        tags: list[str] | None = None,
        excerpt: str | None = None,
        notes: str | None = None,
        reliability_score: float | None = None,
    ) -> dict[str, Any]:
        sets = []
        params: list[Any] = []
        idx = 1

        for name, val in [
            ("title", title),
            ("author", author),
            ("source_type", source_type),
            ("source_url", source_url),
            ("category", category),
            ("tags", json_dumps(tags) if tags else None),
            ("excerpt", excerpt),
            ("notes", notes),
            ("reliability_score", reliability_score),
        ]:
            if val is not None:
                sets.append(f"{name} = ${idx}")
                params.append(val)
                idx += 1

        if not sets:
            return {}

        sets.append(f"updated_at = NOW()")
        params.append(reference_id)

        row = await self._db.fetchrow(
            f"""
            UPDATE reference_materials
            SET {', '.join(sets)}
            WHERE id = ${idx}
            RETURNING id::text, project_id::text, title, author, source_type, source_url,
                      category, tags, excerpt, notes, reliability_score, created_at, updated_at
            """,
            *params,
        )
        r = row_to_dict(row)
        r["tags"] = list(r.get("tags") or [])
        return r

    async def delete_reference(self, reference_id: str) -> bool:
        result = await self._db.execute(
            "DELETE FROM reference_materials WHERE id = $1", reference_id
        )
        return result == "DELETE 1"
