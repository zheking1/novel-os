import logging
import json
import hashlib
from datetime import datetime
from typing import Any

from ..db import Database
from ..utils import json_dumps, row_to_dict, rows_to_dicts
from .workspace import WorkspaceService
from .canon import CanonService
from .rules import RulesService
from .memory import MemoryService
from .plot import PlotService

logger = logging.getLogger("novel_os_mcp.services.sync")


class SyncService:
    """同步服务 - 处理项目数据同步"""

    STATUS_PENDING = "pending"
    STATUS_IN_PROGRESS = "in_progress"
    STATUS_COMPLETED = "completed"
    STATUS_FAILED = "failed"
    STATUS_CONFLICT = "conflict"

    def __init__(self, db: Database):
        self._db = db
        self.workspace_service = WorkspaceService(db)
        self.canon_service = CanonService(db)
        self.rules_service = RulesService(db)
        self.memory_service = MemoryService(db)
        self.plot_service = PlotService(db)

    async def create_sync_record(
        self,
        project_id: str,
        sync_type: str = "full",
        source: str = "local",
        target: str = "remote",
    ) -> dict[str, Any]:
        row = await self._db.fetchrow(
            """
            INSERT INTO sync_records
              (project_id, sync_type, source, target, status)
            VALUES ($1, $2, $3, $4, 'pending')
            RETURNING id::text, project_id::text, sync_type, source, target,
                      status, created_at
            """,
            project_id,
            sync_type,
            source,
            target,
        )
        return row_to_dict(row)

    async def update_sync_record(
        self,
        sync_id: str,
        status: str,
        items_synced: int | None = None,
        error_message: str | None = None,
        conflict_data: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        if status == self.STATUS_IN_PROGRESS:
            row = await self._db.fetchrow(
                """
                UPDATE sync_records
                SET status = $2, started_at = NOW()
                WHERE id = $1
                RETURNING id::text, project_id::text, sync_type, source, target, status, started_at
                """,
                sync_id,
                status,
            )
        elif status == self.STATUS_COMPLETED:
            row = await self._db.fetchrow(
                """
                UPDATE sync_records
                SET status = $2, completed_at = NOW(), items_synced = $3
                WHERE id = $1
                RETURNING id::text, project_id::text, sync_type, source, target,
                          status, items_synced, started_at, completed_at
                """,
                sync_id,
                status,
                items_synced,
            )
        elif status == self.STATUS_FAILED:
            row = await self._db.fetchrow(
                """
                UPDATE sync_records
                SET status = $2, completed_at = NOW(), error_message = $3
                WHERE id = $1
                RETURNING id::text, project_id::text, sync_type, source, target,
                          status, error_message, started_at, completed_at
                """,
                sync_id,
                status,
                error_message,
            )
        elif status == self.STATUS_CONFLICT:
            row = await self._db.fetchrow(
                """
                UPDATE sync_records
                SET status = $2, conflict_data = $3
                WHERE id = $1
                RETURNING id::text, project_id::text, sync_type, source, target,
                          status, conflict_data, created_at
                """,
                sync_id,
                status,
                json_dumps(conflict_data) if conflict_data else None,
            )
        else:
            row = await self._db.fetchrow(
                """
                UPDATE sync_records SET status = $2 WHERE id = $1
                RETURNING id::text, project_id::text, sync_type, source, target, status
                """,
                sync_id,
                status,
            )
        return row_to_dict(row) if row else {}

    async def get_sync_records(
        self,
        project_id: str,
        limit: int = 20,
    ) -> list[dict[str, Any]]:
        rows = await self._db.fetch(
            """
            SELECT id::text, project_id::text, sync_type, source, target, status,
                  items_synced, error_message, conflict_data, started_at, completed_at, created_at
            FROM sync_records
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
            if r.get("conflict_data"):
                try:
                    r["conflict_data"] = json.loads(r["conflict_data"]) if isinstance(r["conflict_data"], str) else r["conflict_data"]
                except (json.JSONDecodeError, TypeError):
                    pass
            results.append(r)
        return results

    async def export_project_data(
        self,
        project_id: str,
    ) -> dict[str, Any]:
        workspace = await self.workspace_service.get_workspace(project_id)
        canons = await self.canon_service.list_canon_items(project_id, limit=1000)
        rules = await self.rules_service.list_rules(project_id, limit=1000)
        memories = await self.memory_service.get_memories(project_id, limit=1000)
        plots = await self.plot_service.list_plots(project_id, limit=1000)

        export_data = {
            "version": "1.0",
            "exported_at": datetime.utcnow().isoformat(),
            "project_id": project_id,
            "workspace": workspace,
            "canons": canons,
            "rules": rules,
            "memories": memories,
            "plots": plots,
        }

        data_str = json_dumps(export_data, sort_keys=True)
        checksum = hashlib.sha256(data_str.encode()).hexdigest()

        return {
            "data": export_data,
            "checksum": checksum,
            "size_bytes": len(data_str.encode()),
        }

    async def import_project_data(
        self,
        project_id: str,
        data: dict[str, Any],
        conflict_strategy: str = "skip",
    ) -> dict[str, Any]:
        results = {"imported": {}, "skipped": [], "errors": []}

        if "canons" in data:
            for item in data["canons"]:
                try:
                    await self.canon_service.create_canon_item(
                        project_id=project_id,
                        title=item.get("title", ""),
                        content=item.get("content", ""),
                        category=item.get("category"),
                        item_type=item.get("item_type"),
                        source_chapter_id=item.get("source_chapter_id"),
                        importance=item.get("importance", "normal"),
                    )
                    results["imported"]["canons"] = results["imported"].get("canons", 0) + 1
                except Exception as e:
                    results["errors"].append({"type": "canon", "error": str(e)})

        if "rules" in data:
            for item in data["rules"]:
                try:
                    await self.rules_service.create_rule(
                        project_id=project_id,
                        rule_type=item.get("rule_type", "quality"),
                        title=item.get("title", ""),
                        description=item.get("description", ""),
                        severity=item.get("severity", "warning"),
                        category=item.get("category"),
                    )
                    results["imported"]["rules"] = results["imported"].get("rules", 0) + 1
                except Exception as e:
                    results["errors"].append({"type": "rule", "error": str(e)})

        if "memories" in data:
            for item in data["memories"]:
                try:
                    await self.memory_service.create_memory(
                        project_id=project_id,
                        content=item.get("content", ""),
                        memory_type=item.get("memory_type", "fact"),
                        category=item.get("category"),
                        importance=item.get("importance", "normal"),
                        source_chapter_id=item.get("source_chapter_id"),
                        related_characters=item.get("related_characters"),
                    )
                    results["imported"]["memories"] = results["imported"].get("memories", 0) + 1
                except Exception as e:
                    results["errors"].append({"type": "memory", "error": str(e)})

        if "plots" in data:
            for item in data["plots"]:
                try:
                    await self.plot_service.create_plot(
                        project_id=project_id,
                        title=item.get("title", ""),
                        description=item.get("description", ""),
                        plot_type=item.get("plot_type", "main"),
                        status=item.get("status", "planned"),
                    )
                    results["imported"]["plots"] = results["imported"].get("plots", 0) + 1
                except Exception as e:
                    results["errors"].append({"type": "plot", "error": str(e)})

        return results

    async def calculate_data_checksum(
        self,
        project_id: str,
    ) -> str:
        export_result = await self.export_project_data(project_id)
        return export_result["checksum"]

    async def get_sync_status(
        self,
        project_id: str,
    ) -> dict[str, Any]:
        row = await self._db.fetchrow(
            """
            SELECT
              COUNT(*)::int AS total_syncs,
              COUNT(*) FILTER (WHERE status = 'completed')::int AS completed,
              COUNT(*) FILTER (WHERE status = 'failed')::int AS failed,
              COUNT(*) FILTER (WHERE status = 'pending')::int AS pending,
              MAX(completed_at) AS last_sync_at
            FROM sync_records
            WHERE project_id = $1
            """,
            project_id,
        )
        return row_to_dict(row) if row else {}
