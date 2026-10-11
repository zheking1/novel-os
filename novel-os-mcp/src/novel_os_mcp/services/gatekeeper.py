import json
import logging
import os
from typing import Any

from ..db import Database
from ..utils import json_dumps, row_to_dict

logger = logging.getLogger("novel_os_mcp.services.gatekeeper")

# ---- 风险评估规则 ----
# 原为 _rule_based_assess 内的硬编码，上提为模块常量以便部署侧覆盖与单测。
PROJECT_TABLES = {"project_knowledge", "canon_rules", "state_entities", "state_snapshots"}
GLOBAL_TABLES = {"global_rules", "universal_knowledge"}
# 注意：历史上这里写成 "user_essions"（拼写错误），导致 user_sessions 未受保护，已修正。
DANGEROUS_TABLES = {"users", "workspaces", "projects", "api_tokens", "user_sessions",
                    "system_settings", "system_evolution_proposals", "model_profiles"}
DANGER_KEYWORDS = [
    "os.", "exec(", "eval(", "__import__", "subprocess", "rm -rf",
    "drop table", "truncate", "shutdown", "reboot",
]


def _extra_keywords() -> list[str]:
    """部署侧可通过 NOVEL_GATEKEEPER_DANGER_KEYWORDS 追加危险关键词（逗号分隔）。"""
    return [k.strip() for k in os.getenv("NOVEL_GATEKEEPER_DANGER_KEYWORDS", "").split(",") if k.strip()]


class GatekeeperService:
    def __init__(self, db: Database):
        self._db = db

    def evaluate(self, action: str, target_table: str, source_type: str,
                 content: dict | None = None) -> dict:
        """纯风险评估，不写库。供"先评估后写入"的调用方在落库前判断。

        Returns:
            {level: low|medium|high, reason: str, auto_apply: bool}
        """
        return self._rule_based_assess(action, target_table, source_type, content)

    async def assess(
        self, project_id: str | None, action: str, target_table: str,
        content: dict, source_type: str, source_id: str = "",
        old_value: dict | None = None, created_by: str = "",
        proposal_id: str | None = None, target_id: str = "",
    ) -> dict[str, Any]:
        """评估风险并写入 evolution_logs。

        Returns:
            log_entry；其中 auto_applied（及同义的 auto_apply）表示"是否允许自动写入"。
            调用方应据此决定是立即落库，还是转为待管理员审批的提案。
        """
        risk = self.evaluate(action, target_table, source_type, content)
        log_entry = {
            "source_type": source_type,
            "source_id": source_id,
            "action": action,
            "target_table": target_table,
            "target_id": target_id,
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
               old_value, new_value, risk_level, risk_reason, auto_applied, created_by, proposal_id)
               VALUES ($1,$2,$3,$4,$5,$6::jsonb,$7::jsonb,$8,$9,$10,$11,$12::uuid) RETURNING id""",
            log_entry["source_type"], log_entry["source_id"],
            log_entry["action"], log_entry["target_table"],
            log_entry["target_id"], log_entry["old_value"], log_entry["new_value"],
            log_entry["risk_level"], log_entry["risk_reason"],
            log_entry["auto_applied"], log_entry["created_by"],
            proposal_id,
        )
        log_entry["id"] = str(row["id"])
        log_entry["auto_apply"] = risk["auto_apply"]
        log_entry["proposal_id"] = proposal_id
        return log_entry

    async def link_proposal(self, log_ids: list[str], proposal_id: str) -> None:
        """把已产生的日志挂到提案上，使 evolution_logs.proposal_id 可追溯。"""
        if not log_ids:
            return
        await self._db.execute(
            "UPDATE evolution_logs SET proposal_id=$1::uuid WHERE id = ANY($2::uuid[])",
            proposal_id, log_ids,
        )

    def _rule_based_assess(
        self, action: str, target_table: str, source_type: str, content: dict | None = None,
    ) -> dict:
        if content:
            content_str = json.dumps(content, ensure_ascii=False).lower()
            if action == "DELETE":
                return {"level": "high", "reason": "删除操作已拦截，只能由管理员手动执行", "auto_apply": False}
            if target_table in DANGEROUS_TABLES:
                return {"level": "high", "reason": f"禁止自动写入系统表 {target_table}，仅管理员可从 Web UI 操作", "auto_apply": False}
            for kw in list(DANGER_KEYWORDS) + _extra_keywords():
                if kw in content_str:
                    return {"level": "high", "reason": f"内容含危险关键词 '{kw}'，已被门禁拦截", "auto_apply": False}
            if target_table in GLOBAL_TABLES and action == "UPDATE":
                return {"level": "medium", "reason": "修改已有全局数据可能影响其他项目，需管理员复核", "auto_apply": False}

        if target_table in PROJECT_TABLES:
            return {"level": "low", "reason": "项目级表，无风险", "auto_apply": True}
        if target_table in GLOBAL_TABLES and source_type == "discussion_room":
            return {"level": "low", "reason": "讨论室多模型共识 + 内容无风险标记", "auto_apply": True}
        if target_table in GLOBAL_TABLES:
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