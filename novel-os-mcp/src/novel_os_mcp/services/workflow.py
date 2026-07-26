import logging
from typing import Any

from ..db import Database
from ..utils import json_dumps, row_to_dict, rows_to_dicts

logger = logging.getLogger("novel_os_mcp.services.workflow")


class WorkflowService:
    """工作流服务 - 管理写作工作流和任务"""

    def __init__(self, db: Database):
        self._db = db

    async def create_workflow(
        self,
        project_id: str,
        name: str,
        description: str | None = None,
        workflow_type: str = "sequential",
    ) -> dict[str, Any]:
        row = await self._db.fetchrow(
            """
            INSERT INTO workflows (project_id, name, description, workflow_type, status)
            VALUES ($1, $2, $3, $4, 'active')
            RETURNING id::text, project_id::text, name, description, workflow_type,
                      status, created_at, updated_at
            """,
            project_id,
            name,
            description,
            workflow_type,
        )
        return row_to_dict(row)

    async def get_workflows(
        self,
        project_id: str,
        status: str | None = None,
    ) -> list[dict[str, Any]]:
        conditions = ["project_id = $1"]
        params: list[Any] = [project_id]
        idx = 2

        if status:
            conditions.append(f"status = ${idx}")
            params.append(status)
            idx += 1

        rows = await self._db.fetch(
            f"""
            SELECT id::text, project_id::text, name, description, workflow_type,
                  status, created_at, updated_at
            FROM workflows
            WHERE {' AND '.join(conditions)}
            ORDER BY created_at DESC
            """,
            *params,
        )
        return rows_to_dicts(rows)

    async def update_workflow(
        self,
        workflow_id: str,
        name: str | None = None,
        description: str | None = None,
        status: str | None = None,
    ) -> dict[str, Any]:
        sets = []
        params: list[Any] = []
        idx = 1

        for n, v in [("name", name), ("description", description), ("status", status)]:
            if v is not None:
                sets.append(f"{n} = ${idx}")
                params.append(v)
                idx += 1

        if not sets:
            return {}

        sets.append("updated_at = NOW()")
        params.append(workflow_id)

        row = await self._db.fetchrow(
            f"""
            UPDATE workflows SET {', '.join(sets)} WHERE id = ${idx}
            RETURNING id::text, project_id::text, name, description, workflow_type,
                      status, created_at, updated_at
            """,
            *params,
        )
        return row_to_dict(row) if row else {}

    async def add_workflow_step(
        self,
        workflow_id: str,
        name: str,
        step_type: str = "review",
        step_order: int = 0,
        config: dict[str, Any] | None = None,
        dependencies: list[str] | None = None,
    ) -> dict[str, Any]:
        row = await self._db.fetchrow(
            """
            INSERT INTO workflow_steps
              (workflow_id, name, step_type, step_order, config, dependencies, status)
            VALUES ($1, $2, $3, $4, $5, $6, 'pending')
            RETURNING id::text, workflow_id::text, name, step_type, step_order,
                      config, dependencies, status, created_at
            """,
            workflow_id,
            name,
            step_type,
            step_order,
            json_dumps(config) if config else None,
            json_dumps(dependencies) if dependencies else None,
        )
        r = row_to_dict(row)
        r["dependencies"] = list(r.get("dependencies") or [])
        return r

    async def get_workflow_steps(
        self,
        workflow_id: str,
    ) -> list[dict[str, Any]]:
        rows = await self._db.fetch(
            """
            SELECT id::text, workflow_id::text, name, step_type, step_order,
                  config, dependencies, status, result, created_at, completed_at
            FROM workflow_steps
            WHERE workflow_id = $1
            ORDER BY step_order
            """,
            workflow_id,
        )
        results = []
        for row in rows:
            r = row_to_dict(row)
            r["dependencies"] = list(r.get("dependencies") or [])
            results.append(r)
        return results

    async def update_step_status(
        self,
        step_id: str,
        status: str,
        result: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        if status == "completed":
            row = await self._db.fetchrow(
                """
                UPDATE workflow_steps
                SET status = $2, result = $3, completed_at = NOW()
                WHERE id = $1
                RETURNING id::text, workflow_id::text, name, step_type, step_order,
                          status, result, created_at, completed_at
                """,
                step_id,
                status,
                json_dumps(result) if result else None,
            )
        else:
            row = await self._db.fetchrow(
                """
                UPDATE workflow_steps SET status = $2 WHERE id = $1
                RETURNING id::text, workflow_id::text, name, step_type, step_order,
                          status, result, created_at
                """,
                step_id,
                status,
            )
        return row_to_dict(row) if row else {}

    async def create_task(
        self,
        project_id: str,
        title: str,
        description: str | None = None,
        task_type: str = "writing",
        priority: str = "normal",
        assigned_to: str | None = None,
        chapter_id: str | None = None,
        due_date: str | None = None,
    ) -> dict[str, Any]:
        row = await self._db.fetchrow(
            """
            INSERT INTO tasks
              (project_id, title, description, task_type, priority, assigned_to, chapter_id, due_date, status)
            VALUES ($1, $2, $3, $4, $5, $6, $7, $8, 'todo')
            RETURNING id::text, project_id::text, title, description, task_type,
                      priority, assigned_to, chapter_id::text, due_date, status, created_at
            """,
            project_id,
            title,
            description,
            task_type,
            priority,
            assigned_to,
            chapter_id,
            due_date,
        )
        return row_to_dict(row)

    async def get_tasks(
        self,
        project_id: str,
        status: str | None = None,
        assigned_to: str | None = None,
        task_type: str | None = None,
        limit: int = 50,
    ) -> list[dict[str, Any]]:
        conditions = ["project_id = $1"]
        params: list[Any] = [project_id]
        idx = 2

        for col, val in [("status", status), ("assigned_to", assigned_to), ("task_type", task_type)]:
            if val is not None:
                conditions.append(f"{col} = ${idx}")
                params.append(val)
                idx += 1

        params.append(limit)
        rows = await self._db.fetch(
            f"""
            SELECT id::text, project_id::text, title, description, task_type,
                  priority, assigned_to, chapter_id::text, due_date, status, created_at, completed_at
            FROM tasks
            WHERE {' AND '.join(conditions)}
            ORDER BY
              CASE priority WHEN 'urgent' THEN 0 WHEN 'high' THEN 1 WHEN 'normal' THEN 2 ELSE 3 END,
              created_at DESC
            LIMIT ${idx}
            """,
            *params,
        )
        return rows_to_dicts(rows)

    async def update_task(
        self,
        task_id: str,
        status: str | None = None,
        assigned_to: str | None = None,
        priority: str | None = None,
    ) -> dict[str, Any]:
        sets = []
        params: list[Any] = []
        idx = 1

        for n, v in [("status", status), ("assigned_to", assigned_to), ("priority", priority)]:
            if v is not None:
                sets.append(f"{n} = ${idx}")
                params.append(v)
                idx += 1

        if not sets:
            return {}

        if status == "completed":
            sets.append("completed_at = NOW()")

        params.append(task_id)
        row = await self._db.fetchrow(
            f"""
            UPDATE tasks SET {', '.join(sets)} WHERE id = ${idx}
            RETURNING id::text, project_id::text, title, description, task_type,
                      priority, assigned_to, chapter_id::text, due_date, status, created_at, completed_at
            """,
            *params,
        )
        return row_to_dict(row) if row else {}

    async def get_task_stats(self, project_id: str) -> dict[str, Any]:
        row = await self._db.fetchrow(
            """
            SELECT
              COUNT(*)::int AS total,
              COUNT(*) FILTER (WHERE status = 'todo')::int AS todo,
              COUNT(*) FILTER (WHERE status = 'in_progress')::int AS in_progress,
              COUNT(*) FILTER (WHERE status = 'completed')::int AS completed,
              COUNT(*) FILTER (WHERE due_date < NOW() AND status != 'completed')::int AS overdue
            FROM tasks
            WHERE project_id = $1
            """,
            project_id,
        )
        return row_to_dict(row) if row else {}

    # ------------------------------------------------------------------
    # Chapter Validation & Submission
    # ------------------------------------------------------------------

    async def validate_generated_content(
        self,
        project_id: str,
        chapter_no: int,
        content: str,
    ) -> dict[str, Any]:
        """校验章节内容：禁词、角色存活、设定一致性。"""
        issues: list[dict[str, Any]] = []

        # 1. Forbidden word check
        try:
            from .rules import RulesService
            rules_svc = RulesService(self._db)
            forbidden = await rules_svc.list_rules(
                project_id=project_id, rule_type="forbidden", status="active",
                chapter_no=chapter_no, limit=50)
            for rule in forbidden.get("rules", []):
                patterns = rule.get("patterns") or []
                content_lower = content.lower()
                for pattern in patterns:
                    if pattern.lower() in content_lower:
                        issues.append({
                            "type": "forbidden_word",
                            "severity": rule.get("severity", "critical"),
                            "rule_key": rule.get("rule_key"),
                            "matched": pattern,
                        })
        except Exception:
            logger.warning("Forbidden word check failed", exc_info=True)

        # 2. Character alive check
        try:
            rows = await self._db.fetch(
                """
                SELECT DISTINCT e.name
                FROM state_entities e
                WHERE e.project_id = $1
                  AND e.entity_type = 'character'
                  AND e.lifecycle_status = 'dead'
                """,
                project_id,
            )
            dead_names = {r["name"] for r in rows}
            content_lower = content.lower()
            for name in dead_names:
                if name.lower() in content_lower:
                    issues.append({
                        "type": "dead_character",
                        "severity": "error",
                        "name": name,
                        "message": f"Character '{name}' appears but is dead.",
                    })
        except Exception:
            logger.warning("Character alive check failed", exc_info=True)

        # 3. Setting consistency — 检查正文是否引用了活跃的设定文档，标记未引用的
        try:
            from .canon import CanonService
            canon_svc = CanonService(self._db)
            docs = await canon_svc.list_documents(
                project_id=project_id, status="active", limit=20)
            content_lower = content.lower()
            # 获取本章节涉及的角色名（用于判断哪些设定应被引用）
            char_rows = await self._db.fetch(
                "SELECT name FROM state_entities WHERE project_id = $1 AND entity_type = 'character' AND lifecycle_status = 'active'",
                project_id,
            )
            chapter_names = {r["name"].lower() for r in char_rows}
            doc_keys_verified = 0
            for doc in docs.get("documents", []):
                key = doc.get("key", "")
                title = doc.get("title", "")
                if not key:
                    continue
                # 设定 key 出现在正文中 → 已引用，通过
                if key.lower() in content_lower:
                    doc_keys_verified += 1
                    continue
                # 设定标题或 key 包含本章角色名，但 key 未出现在正文 → 可能遗漏
                title_lower = (title or "").lower()
                if chapter_names and chapter_names & set(title_lower.split()):
                    issues.append({
                        "type": "canon_missing_reference",
                        "severity": "warning",
                        "doc_key": key,
                        "doc_title": title,
                        "message": f"设定文档 '{title}' 与本章角色相关但未被引用",
                    })
            # 记录已校验通过的文档数（供日志参考）
            if doc_keys_verified > 0:
                logger.info("Setting consistency: %d canon docs verified", doc_keys_verified)
        except Exception:
            logger.warning("Setting consistency check failed", exc_info=True)

        return {
            "chapter_no": chapter_no,
            "issues": issues,
            "passed": len(issues) == 0,
            "issue_count": len(issues),
            "workflow_guide": {
                "phase": "内容校验",
                "passed": len(issues) == 0,
                "description": "校验通过→提交章节；不通过→修订后再提交",
                "next_step": "workflow.submit_chapter_commit" if len(issues) == 0 else "修订正文",
                "issue_count": len(issues),
                "blocking_count": len([i for i in issues if i.get("severity") in ("error", "critical")]),
            },
        }

    async def submit_chapter_commit(
        self,
        project_id: str,
        chapter_no: int,
        title: str | None,
        local_files: list[dict[str, Any]],
        commit: dict[str, Any],
        accept: bool,
        username: str,
    ) -> dict[str, Any]:
        """提交章节完成确认，写入 chapter_commits + audit_logs。"""
        # Resolve chapter_id — if not found, auto-create chapter record
        ch_row = await self._db.fetchrow(
            "SELECT id FROM chapters WHERE project_id = $1 AND chapter_no = $2",
            project_id, chapter_no,
        )
        chapter_id = ch_row["id"] if ch_row else None

        if not chapter_id:
            vol_row = await self._db.fetchrow(
                "SELECT volume_no FROM volumes WHERE project_id = $1 AND start_chapter_no <= $2 AND (end_chapter_no IS NULL OR end_chapter_no >= $2) LIMIT 1",
                project_id, chapter_no,
            )
            volume_no = vol_row["volume_no"] if vol_row else 1
            ch_row = await self._db.fetchrow(
                "INSERT INTO chapters (project_id, chapter_no, title, volume_no, status) VALUES ($1, $2, $3, $4, 'draft') RETURNING id",
                project_id, chapter_no, title or f"第{chapter_no}章", volume_no,
            )
            chapter_id = ch_row["id"]

        # 强制审核：检查是否有已完成（含已汇总）的审核任务
        if accept:
            review_count = await self._db.fetchval(
                """
                SELECT COUNT(*) FROM review_jobs
                WHERE project_id = $1 AND chapter_id = $2 AND status IN ('completed', 'aggregated')
                """,
                project_id, chapter_id,
            )
            if review_count == 0:
                raise PermissionError(
                    f"章节 {chapter_no} 尚未完成审核，请先调用 review.start_job 启动审核并等待审核完成后再提交。"
                    f"如需跳过审核，请传入 accept=false 仅保存记录。"
                )

        async with self._db.acquire() as conn:
            async with conn.transaction():
                # Insert commit
                commit_row = await conn.fetchrow(
                    """
                    INSERT INTO chapter_commits
                      (project_id, chapter_id, commit_no, payload, accepted, accepted_at)
                    VALUES ($1, $2, COALESCE(
                        (SELECT MAX(commit_no) + 1 FROM chapter_commits WHERE chapter_id = $2), 1
                    ), $3::jsonb, $4, CASE WHEN $4 THEN NOW() ELSE NULL END)
                    RETURNING id::text, commit_no, accepted, accepted_at, created_at
                    """,
                    project_id,
                    chapter_id,
                    json_dumps({"title": title, "local_files": local_files, **commit}),
                    accept,
                )

                # Update chapter status if accept
                if accept and chapter_id:
                    await conn.execute(
                        """
                        UPDATE chapters SET status = 'completed', title = COALESCE($3, title), updated_at = NOW()
                        WHERE id = $2 AND project_id = $1
                        """,
                        project_id, chapter_id, title,
                    )

                # Audit log
                await conn.execute(
                    """
                    INSERT INTO audit_logs (user_id, action, resource_type, resource_id, payload)
                    SELECT users.id, 'chapter_commit', 'chapter', $1::uuid, $2::jsonb
                    FROM users
                    WHERE users.username = $3
                    """,
                    chapter_id,
                    json_dumps({"chapter_no": chapter_no, "commit_no": commit_row["commit_no"], "accept": accept}),
                    username,
                )

        return {
            "chapter_no": chapter_no,
            "commit_id": commit_row["id"],
            "commit_no": commit_row["commit_no"],
            "accepted": commit_row["accepted"],
            "created_at": commit_row["created_at"],
            "workflow_guide": {
                "phase": "章节提交完成",
                "description": "章节已提交，下一步执行数据维护",
                "next_actions": [
                    {"tool": "kb.world.auto_update", "desc": "更新世界状态"},
                    {"tool": "arc.record_emotion", "desc": "记录角色情感变化"},
                    {"tool": "arc.record_power", "desc": "记录角色实力变化"},
                    {"tool": "arc.record_relationship", "desc": "记录角色关系变化"},
                    {"tool": "arc.record_personality", "desc": "记录角色性格变化"},
                    {"tool": "plot.thread.advance", "desc": "推进剧情线"},
                    {"tool": "foreshadowing.payoff", "desc": "回收到期伏笔"},
                    {"tool": "workflow.learn_from_review", "desc": "从审核学习（可选）"},
                ],
            },
        }

    async def list_audit_logs(
        self,
        project_id: str,
        action: str | None = None,
        resource_type: str | None = None,
        limit: int = 50,
    ) -> list[dict[str, Any]]:
        """列出审计日志。"""
        conditions: list[str] = []
        params: list[Any] = []
        idx = 1

        if action:
            conditions.append(f"action = ${idx}")
            params.append(action)
            idx += 1
        if resource_type:
            conditions.append(f"resource_type = ${idx}")
            params.append(resource_type)
            idx += 1

        params.append(limit)
        rows = await self._db.fetch(
            f"""
            SELECT id::text, user_id, action, resource_type,
                   resource_id::text, payload, created_at
            FROM audit_logs
            {f'WHERE {" AND ".join(conditions)}' if conditions else ''}
            ORDER BY created_at DESC
            LIMIT ${idx}
            """,
            *params,
        )
        return rows_to_dicts(rows)
