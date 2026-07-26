import logging
import json
from typing import Any

from ..db import Database
from ..utils import json_dumps, row_to_dict, rows_to_dicts

logger = logging.getLogger("novel_os_mcp.services.archive")


class ArchiveService:
    """归档服务 - 管理数据归档和清理"""

    def __init__(self, db: Database):
        self._db = db

    async def create_archive(
        self,
        project_id: str,
        archive_type: str,
        name: str,
        description: str | None = None,
        retention_days: int = 365,
        compress: bool = True,
    ) -> dict[str, Any]:
        row = await self._db.fetchrow(
            """
            INSERT INTO archives
              (project_id, archive_type, name, description, retention_days, compress, status)
            VALUES ($1, $2, $3, $4, $5, $6, 'active')
            RETURNING id::text, project_id::text, archive_type, name, description,
                      retention_days, compress, status, created_at
            """,
            project_id,
            archive_type,
            name,
            description,
            retention_days,
            compress,
        )
        return row_to_dict(row)

    async def get_archives(
        self,
        project_id: str,
        archive_type: str | None = None,
    ) -> list[dict[str, Any]]:
        conditions = ["project_id = $1"]
        params: list[Any] = [project_id]
        idx = 2

        if archive_type:
            conditions.append(f"archive_type = ${idx}")
            params.append(archive_type)
            idx += 1

        rows = await self._db.fetch(
            f"""
            SELECT id::text, project_id::text, archive_type, name, description,
                  retention_days, compress, status, item_count, size_bytes,
                  last_archived_at, created_at
            FROM archives
            WHERE {' AND '.join(conditions)}
            ORDER BY created_at DESC
            """,
            *params,
        )
        return rows_to_dicts(rows)

    async def update_archive_status(
        self,
        archive_id: str,
        status: str,
        item_count: int | None = None,
        size_bytes: int | None = None,
    ) -> dict[str, Any]:
        if item_count is not None:
            row = await self._db.fetchrow(
                """
                UPDATE archives
                SET status = $2, item_count = $3, size_bytes = $4, last_archived_at = NOW()
                WHERE id = $1
                RETURNING id::text, project_id::text, archive_type, name, status,
                          item_count, size_bytes, last_archived_at, created_at
                """,
                archive_id,
                status,
                item_count,
                size_bytes,
            )
        else:
            row = await self._db.fetchrow(
                """
                UPDATE archives SET status = $2 WHERE id = $1
                RETURNING id::text, project_id::text, archive_type, name, status, created_at
                """,
                archive_id,
                status,
            )
        return row_to_dict(row) if row else {}

    async def delete_archive(self, archive_id: str) -> bool:
        result = await self._db.execute("DELETE FROM archives WHERE id = $1", archive_id)
        return result == "DELETE 1"

    async def archive_chapters(
        self,
        archive_id: str,
        project_id: str,
        older_than_days: int | None = None,
        status_filter: str | None = None,
    ) -> dict[str, Any]:
        conditions = ["project_id = $1", "is_deleted = false"]
        params: list[Any] = [project_id]
        idx = 2

        if older_than_days:
            conditions.append(f"created_at < NOW() - INTERVAL '1 day' * ${idx}")
            params.append(older_than_days)
            idx += 1

        if status_filter:
            conditions.append(f"status = ${idx}")
            params.append(status_filter)
            idx += 1

        where = " AND ".join(conditions)

        rows = await self._db.fetch(
            f"SELECT id FROM chapters WHERE {where}",
            *params,
        )

        archived_count = 0
        for row in rows:
            chapter_id = row["id"]
            await self._db.execute(
                """
                INSERT INTO archive_items (archive_id, item_type, item_id, original_data)
                SELECT $1, 'chapter', id::text, row_to_json(chapters.*)
                FROM chapters WHERE id = $2
                """,
                archive_id,
                chapter_id,
            )
            await self._db.execute(
                "UPDATE chapters SET is_deleted = true WHERE id = $1",
                chapter_id,
            )
            archived_count += 1

        await self._db.execute(
            """
            UPDATE archives
            SET item_count = COALESCE(item_count, 0) + $2, last_archived_at = NOW()
            WHERE id = $1
            """,
            archive_id,
            archived_count,
        )

        return {"archived_count": archived_count}

    async def restore_from_archive(
        self,
        archive_id: str,
        item_ids: list[str] | None = None,
    ) -> dict[str, Any]:
        if item_ids:
            rows = await self._db.fetch(
                """
                SELECT id::text, item_type, item_id, original_data
                FROM archive_items
                WHERE archive_id = $1 AND item_id = ANY($2)
                """,
                archive_id,
                item_ids,
            )
        else:
            rows = await self._db.fetch(
                """
                SELECT id::text, item_type, item_id, original_data
                FROM archive_items
                WHERE archive_id = $1
                """,
                archive_id,
            )

        restored = 0
        for row in rows:
            item = row_to_dict(row)
            if item["item_type"] == "chapter":
                data = json.loads(item["original_data"]) if isinstance(item["original_data"], str) else item["original_data"]
                await self._db.execute(
                    """
                    UPDATE chapters SET is_deleted = false WHERE id = $1
                    """,
                    item["item_id"],
                )
                restored += 1

        return {"restored_count": restored}

    async def get_archive_stats(
        self,
        project_id: str,
    ) -> dict[str, Any]:
        row = await self._db.fetchrow(
            """
            SELECT
              COUNT(*)::int AS total_archives,
              COALESCE(SUM(item_count), 0)::int AS total_items,
              COALESCE(SUM(size_bytes), 0)::bigint AS total_size_bytes
            FROM archives
            WHERE project_id = $1
            """,
            project_id,
        )
        return row_to_dict(row) if row else {}
