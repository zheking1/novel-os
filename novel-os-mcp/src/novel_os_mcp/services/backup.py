import logging
from typing import Any

from ..db import Database
from ..utils import json_dumps, row_to_dict, rows_to_dicts, ensure_json_value

logger = logging.getLogger("novel_os_mcp.services.backup")


class BackupService:
    """备份恢复服务 - 管理备份和恢复任务"""

    BACKUP_TYPE_FULL = "full"
    BACKUP_TYPE_INCREMENTAL = "incremental"
    BACKUP_TYPE_CONFIG = "config"
    BACKUP_TYPE_PROJECT_EXPORT = "project_export"

    STATUS_PENDING = "pending"
    STATUS_IN_PROGRESS = "in_progress"
    STATUS_COMPLETED = "completed"
    STATUS_FAILED = "failed"

    def __init__(self, db: Database):
        self._db = db

    async def create_backup_record(
        self,
        project_id: str | None,
        backup_type: str,
        storage_path: str | None = None,
        storage_type: str = "local",
    ) -> dict[str, Any]:
        row = await self._db.fetchrow(
            """
            INSERT INTO backup_records
              (project_id, backup_type, storage_path, storage_type, status)
            VALUES ($1, $2, $3, $4, 'pending')
            RETURNING id::text, project_id::text, backup_type, storage_path, storage_type, status, created_at
            """,
            project_id,
            backup_type,
            storage_path,
            storage_type,
        )
        return row_to_dict(row)

    async def update_backup_record(
        self,
        backup_id: str,
        status: str,
        file_size_bytes: int | None = None,
        file_count: int | None = None,
        checksum: str | None = None,
        compression_type: str | None = None,
        error_message: str | None = None,
    ) -> dict[str, Any]:
        if status == self.STATUS_IN_PROGRESS:
            row = await self._db.fetchrow(
                """
                UPDATE backup_records
                SET status = $2, started_at = NOW()
                WHERE id = $1
                RETURNING id::text, project_id::text, backup_type, storage_path, storage_type, status, started_at
                """,
                backup_id,
                status,
            )
        elif status == self.STATUS_COMPLETED:
            row = await self._db.fetchrow(
                """
                UPDATE backup_records
                SET status = $2, completed_at = NOW(),
                    file_size_bytes = COALESCE($3, file_size_bytes),
                    file_count = COALESCE($4, file_count),
                    checksum = COALESCE($5, checksum),
                    compression_type = COALESCE($6, compression_type)
                WHERE id = $1
                RETURNING id::text, project_id::text, backup_type, storage_path, storage_type, status,
                          file_size_bytes, file_count, checksum, compression_type, started_at, completed_at
                """,
                backup_id,
                status,
                file_size_bytes,
                file_count,
                checksum,
                compression_type,
            )
        elif status == self.STATUS_FAILED:
            row = await self._db.fetchrow(
                """
                UPDATE backup_records
                SET status = $2, completed_at = NOW(), error_message = $3
                WHERE id = $1
                RETURNING id::text, project_id::text, backup_type, status, error_message, started_at, completed_at
                """,
                backup_id,
                status,
                error_message,
            )
        else:
            row = await self._db.fetchrow(
                """
                UPDATE backup_records
                SET status = $2
                WHERE id = $1
                RETURNING id::text, project_id::text, backup_type, status
                """,
                backup_id,
                status,
            )
        return row_to_dict(row) if row else {}

    async def get_backup_records(
        self,
        project_id: str | None = None,
        backup_type: str | None = None,
        status: str | None = None,
        limit: int = 100,
    ) -> list[dict[str, Any]]:
        conditions = []
        params: list[Any] = []
        param_idx = 0

        if project_id:
            param_idx += 1
            conditions.append(f"project_id = ${param_idx}")
            params.append(project_id)

        if backup_type:
            param_idx += 1
            conditions.append(f"backup_type = ${param_idx}")
            params.append(backup_type)

        if status:
            param_idx += 1
            conditions.append(f"status = ${param_idx}")
            params.append(status)

        where_sql = f"WHERE {' AND '.join(conditions)}" if conditions else ""
        param_idx += 1
        params.append(limit)

        rows = await self._db.fetch(
            f"""
            SELECT id::text, project_id::text, backup_type, storage_path, storage_type, status,
                   file_size_bytes, file_count, checksum, compression_type,
                   started_at, completed_at, error_message, metadata, created_at
            FROM backup_records
            {where_sql}
            ORDER BY created_at DESC
            LIMIT ${param_idx}
            """,
            *params,
        )
        results = []
        for row in rows:
            r = row_to_dict(row)
            r["metadata"] = ensure_json_value(r.get("metadata"))
            results.append(r)
        return results

    async def get_backup_schedule(
        self,
        project_id: str | None = None,
    ) -> list[dict[str, Any]]:
        conditions = []
        params: list[Any] = []
        param_idx = 0

        if project_id:
            param_idx += 1
            conditions.append(f"project_id = ${param_idx}")
            params.append(project_id)

        where_sql = f"WHERE {' AND '.join(conditions)}" if conditions else ""

        rows = await self._db.fetch(
            f"""
            SELECT id::text, schedule_name, project_id::text, backup_type, schedule_type,
                   cron_expression, retention_count, retention_days, storage_path, storage_type,
                   enabled, last_run_at, next_run_at, created_at
            FROM backup_schedules
            {where_sql}
            ORDER BY schedule_name
            """,
            *params,
        )
        return [row_to_dict(row) for row in rows]

    async def upsert_backup_schedule(
        self,
        schedule_name: str,
        project_id: str | None,
        backup_type: str = "incremental",
        schedule_type: str = "daily",
        retention_count: int = 7,
        retention_days: int = 30,
        storage_path: str | None = None,
        storage_type: str = "local",
        enabled: bool = True,
    ) -> dict[str, Any]:
        row = await self._db.fetchrow(
            """
            INSERT INTO backup_schedules
              (schedule_name, project_id, backup_type, schedule_type, retention_count,
               retention_days, storage_path, storage_type, enabled)
            VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9)
            ON CONFLICT DO NOTHING
            RETURNING id::text, schedule_name, project_id::text, backup_type, schedule_type,
                      retention_count, retention_days, storage_path, storage_type, enabled
            """,
            schedule_name,
            project_id,
            backup_type,
            schedule_type,
            retention_count,
            retention_days,
            storage_path,
            storage_type,
            enabled,
        )
        if row is None:
            row = await self._db.fetchrow(
                """
                SELECT id::text, schedule_name, project_id::text, backup_type, schedule_type,
                       retention_count, retention_days, storage_path, storage_type, enabled
                FROM backup_schedules
                WHERE schedule_name = $1 AND (project_id = $2 OR (project_id IS NULL AND $2 IS NULL))
                """,
                schedule_name,
                project_id,
            )
        return row_to_dict(row) if row else {}

    async def create_restore_record(
        self,
        backup_record_id: str,
        project_id: str,
        restore_type: str = "full",
        performed_by: str | None = None,
    ) -> dict[str, Any]:
        row = await self._db.fetchrow(
            """
            INSERT INTO restore_records
              (backup_record_id, project_id, restore_type, performed_by)
            VALUES ($1, $2, $3, $4)
            RETURNING id::text, backup_record_id::text, project_id::text, restore_type, status, performed_by, created_at
            """,
            backup_record_id,
            project_id,
            restore_type,
            performed_by,
        )
        return row_to_dict(row)

    async def update_restore_record(
        self,
        restore_id: str,
        status: str,
        tables_restored: list[str] | None = None,
        records_restored_count: int | None = None,
        error_message: str | None = None,
    ) -> dict[str, Any]:
        if status == self.STATUS_IN_PROGRESS:
            row = await self._db.fetchrow(
                """
                UPDATE restore_records
                SET status = $2, started_at = NOW()
                WHERE id = $1
                RETURNING id::text, backup_record_id::text, project_id::text, restore_type, status, started_at
                """,
                restore_id,
                status,
            )
        elif status == self.STATUS_COMPLETED:
            row = await self._db.fetchrow(
                """
                UPDATE restore_records
                SET status = $2, completed_at = NOW(),
                    tables_restored = COALESCE($3::jsonb, tables_restored),
                    records_restored_count = COALESCE($4, records_restored_count)
                WHERE id = $1
                RETURNING id::text, backup_record_id::text, project_id::text, restore_type, status,
                          tables_restored, records_restored_count, started_at, completed_at
                """,
                restore_id,
                status,
                json_dumps(tables_restored) if tables_restored else None,
                records_restored_count,
            )
        elif status == self.STATUS_FAILED:
            row = await self._db.fetchrow(
                """
                UPDATE restore_records
                SET status = $2, completed_at = NOW(), error_message = $3
                WHERE id = $1
                RETURNING id::text, backup_record_id::text, project_id::text, restore_type, status,
                          error_message, started_at, completed_at
                """,
                restore_id,
                status,
                error_message,
            )
        else:
            row = await self._db.fetchrow(
                """
                UPDATE restore_records
                SET status = $2
                WHERE id = $1
                RETURNING id::text, status
                """,
                restore_id,
                status,
            )
        result = row_to_dict(row) if row else {}
        if "tables_restored" in result and result["tables_restored"]:
            result["tables_restored"] = list(result["tables_restored"])
        return result

    async def get_restore_records(
        self,
        project_id: str,
        limit: int = 100,
    ) -> list[dict[str, Any]]:
        rows = await self._db.fetch(
            """
            SELECT id::text, backup_record_id::text, project_id::text, restore_type, status,
                   tables_restored, records_restored_count, started_at, completed_at,
                   error_message, performed_by, created_at
            FROM restore_records
            WHERE project_id = $1
            ORDER BY created_at DESC
            LIMIT $2
            """,
            project_id,
            limit,
        )
        results = []
        for row in rows:
            r = row_to_dict(row)
            r["tables_restored"] = list(r.get("tables_restored") or [])
            results.append(r)
        return results
