import json
import logging
from typing import Any

from ..db import Database
from ..utils import json_dumps, row_to_dict

logger = logging.getLogger("novel_os_mcp.services.gatekeeper")


class GatekeeperService:
    def __init__(self, db: Database):
        self._db = db

    async def assess(
        self, project_id: str | None, action: str, target_table: str,
        content: dict, source_type: str, source_id: str = "",
        old_value: dict | None = None, created_by: str = "",
    ) -> dict[str, Any]:
        risk = self._rule_based_assess(action, target_table, source_type, content)
        log_entry = {
            "source_type": source_type,
            "source_id": source_id,
            "action": action,
            "target_table": target_table,
            "target_id": "",
            "old_value": json_dumps(old_value) if old_value else None,
            "new_value": json_dumps(content),
            "risk_level": risk["level"],
            "risk_reason": risk["reason"],
            "auto_applied": risk["auto_apply"],
            "created_by": created_by,
        }
        await self._db.connect()
        row = await self._db.fetchrow(
            """INSERT INTO evolution_logs (source_type, source_id, action, target_table, target_id,
               old_value, new_value, risk_level, risk_reason, auto_applied, created_by)
               VALUES ($1,$2,$3,$4,$5,$6::jsonb,$7::jsonb,$8,$9,$10,$11) RETURNING id""",
            log_entry["source_type"], log_entry["source_id"],
            log_entry["action"], log_entry["target_table"],
            "", log_entry["old_value"], log_entry["new_value"],
            log_entry["risk_level"], log_entry["risk_reason"],
            log_entry["auto_applied"], log_entry["created_by"],
        )
        log_entry["id"] = str(row["id"])
        return log_entry

    def _rule_based_assess(
        self, action: str, target_table: str, source_type: str, content: dict | None = None,
    ) -> dict:
        project_tables = {"project_knowledge", "canon_rules", "state_entities", "state_snapshots"}
        global_tables = {"global_rules", "universal_knowledge"}
        dangerous_tables = {"users", "workspaces", "projects", "api_tokens", "user_essions",
                           "system_settings", "system_evolution_proposals", "model_profiles"}

        if content:
            content_str = json.dumps(content, ensure_ascii=False).lower()
            if action == "DELETE":
                return {"level": "high", "reason": "删除操作已拦截，只能由管理员手动执行", "auto_apply": False}
            if target_table in dangerous_tables:
                return {"level": "high", "reason": f"禁止自动写入系统表 {target_table}，仅管理员可从 Web UI 操作", "auto_apply": False}
            danger_keywords = [
                "os.", "exec(", "eval(", "__import__", "subprocess", "rm -rf",
                "drop table", "truncate", "shutdown", "reboot",
            ]
            for kw in danger_keywords:
                if kw in content_str:
                    return {"level": "high", "reason": f"内容含危险关键词 '{kw}'，已被门禁拦截", "auto_apply": False}
            if target_table in global_tables and action == "UPDATE":
                return {"level": "medium", "reason": "修改已有全局数据可能影响其他项目，需管理员复核", "auto_apply": False}

        if target_table in project_tables:
            return {"level": "low", "reason": "项目级表，无风险", "auto_apply": True}
        if target_table in global_tables and source_type == "discussion_room":
            return {"level": "low", "reason": "讨论室多模型共识 + 内容无风险标记", "auto_apply": True}
        if target_table in global_tables:
            return {"level": "medium", "reason": f"单{source_type}建议的全局变更，需管理员复核", "auto_apply": False}
        return {"level": "low", "reason": "无风险", "auto_apply": True}

    async def list_logs(
        self, source_type: str | None = None, risk_level: str | None = None,
        target_table: str | None = None, created_by: str | None = None,
        limit: int = 50,
    ) -> list[dict]:
        conditions = []
        params: list[Any] = []
        idx = 1
        for col, val in [("source_type", source_type), ("risk_level", risk_level),
                          ("target_table", target_table), ("created_by", created_by)]:
            if val:
                conditions.append(f"{col} = ${idx}")
                params.append(val)
                idx += 1
        params.append(limit)
        rows = await self._db.fetch(
            f"SELECT * FROM evolution_logs WHERE {' AND '.join(conditions) if conditions else 'true'} ORDER BY created_at DESC LIMIT ${idx}",
            *params,
        )
        return [row_to_dict(r) for r in rows]

    async def rollback(self, log_id: str) -> dict:
        row = await self._db.fetchrow("SELECT * FROM evolution_logs WHERE id=$1", log_id)
        if not row:
            return {"ok": False, "error": "Log not found"}
        if row["old_value"] is None:
            return {"ok": False, "error": "No old_value to restore"}
        old = row["old_value"] if isinstance(row["old_value"], dict) else json.loads(row["old_value"])
        table = row["target_table"]
        if row["action"] in ("INSERT", "UPDATE"):
            await self._db.execute(f"DELETE FROM {table} WHERE id=$1", row["target_id"])
        elif row["action"] == "DELETE":
            cols = ", ".join(old.keys())
            vals = ", ".join(f"${i+1}" for i in range(len(old)))
            await self._db.execute(
                f"INSERT INTO {table} ({cols}) VALUES ({vals})", *old.values(),
            )
        await self._db.execute(
            """INSERT INTO evolution_logs (source_type, source_id, action, target_table, target_id,
               new_value, risk_level, risk_reason, auto_applied, created_by)
               VALUES ('user', $1, 'ROLLBACK', $2, $3, $4::jsonb, 'info', '管理员回滚操作', true, $5)""",
            row["id"], table, row["target_id"], json.dumps(old), "admin",
        )
        return {"ok": True, "rolled_back": True, "log_id": log_id}