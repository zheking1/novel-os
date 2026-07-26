import logging
import re
from typing import Any

from ..db import Database
from ..utils import json_dumps, row_to_dict, rows_to_dicts, ensure_json_value
from .rules import RulesService

logger = logging.getLogger("novel_os_mcp.services.compliance")


class ComplianceService:
    def __init__(self, db: Database, rules_service: RulesService):
        self._db = db
        self._rules = rules_service

    @staticmethod
    def _normalize_patterns(patterns: list[str] | None, content: str | None) -> list[str]:
        cleaned = [str(pattern).strip() for pattern in (patterns or []) if str(pattern).strip()]
        if cleaned:
            return cleaned
        if content and content.strip():
            return [content.strip()]
        return []

    @staticmethod
    def _content_items(text: str | None, content_items: list[dict[str, Any]] | None) -> list[dict[str, Any]]:
        items: list[dict[str, Any]] = []
        if text:
            items.append({"ref": "text", "text": text})
        for index, item in enumerate(content_items or []):
            item_text = item.get("text") if isinstance(item, dict) else None
            if not item_text:
                continue
            items.append(
                {
                    "ref": item.get("ref") or item.get("path_hint") or f"item_{index + 1}",
                    "text": str(item_text),
                    "metadata": item.get("metadata") or {},
                }
            )
        return items

    @staticmethod
    def _excerpt(text: str, start: int, end: int, window: int = 24) -> str:
        left = max(0, start - window)
        right = min(len(text), end + window)
        return text[left:right]

    @staticmethod
    def _matches_for_pattern(
        text: str,
        pattern: str,
        match_type: str,
        case_sensitive: bool,
    ) -> list[dict[str, int | str]]:
        if not pattern:
            return []
        if match_type == "regex":
            flags = 0 if case_sensitive else re.IGNORECASE
            return [{"start": match.start(), "end": match.end(), "match": match.group(0)} for match in re.finditer(pattern, text, flags)]

        haystack = text if case_sensitive else text.lower()
        needle = pattern if case_sensitive else pattern.lower()
        matches: list[dict[str, int | str]] = []
        start = 0
        while True:
            index = haystack.find(needle, start)
            if index < 0:
                break
            end = index + len(pattern)
            matches.append({"start": index, "end": end, "match": text[index:end]})
            start = max(index + 1, end)
        return matches

    async def _audit(
        self,
        project_id: str,
        username: str | None,
        action: str,
        resource_type: str,
        resource_id: str | None,
        payload: dict[str, Any],
    ) -> None:
        await self._db.execute(
            """
            INSERT INTO audit_logs (user_id, action, resource_type, resource_id, payload)
            SELECT users.id, $2, $3, $4::uuid, $5::jsonb
            FROM users
            WHERE ($1::text IS NULL OR users.username = $1)
            UNION ALL
            SELECT NULL, $2, $3, $4::uuid, $5::jsonb
            WHERE $1::text IS NULL
            LIMIT 1
            """,
            username,
            action,
            resource_type,
            resource_id,
            json_dumps(payload),
        )

    async def upsert_rule(
        self,
        project_id: str,
        rule_key: str,
        title: str,
        content: str,
        category: str = "custom",
        patterns: list[str] | None = None,
        match_type: str = "keyword",
        severity: str = "critical",
        status: str = "active",
        scope_type: str = "global",
        scope_ref: str | None = None,
        priority: int = 5,
        case_sensitive: bool = False,
        hint: str | None = None,
        metadata: dict[str, Any] | None = None,
        username: str | None = None,
    ) -> dict[str, Any]:
        if match_type not in {"keyword", "contains", "regex"}:
            raise ValueError("match_type must be keyword, contains, or regex")
        rule_metadata = {
            **(metadata or {}),
            "category": category,
            "patterns": self._normalize_patterns(patterns, content),
            "match_type": match_type,
            "case_sensitive": case_sensitive,
            "hint": hint,
        }
        rule = await self._rules.upsert_rule(
            project_id=project_id,
            rule_key=rule_key,
            rule_type="compliance",
            title=title,
            content=content,
            scope="global",
            severity=severity,
            status=status,
            metadata=rule_metadata,
            change_reason="compliance.rule.upsert",
            source="compliance",
            scope_type=scope_type,
            scope_ref=scope_ref,
            priority=priority,
        )
        await self._audit(
            project_id=project_id,
            username=username,
            action="compliance.rule.upsert",
            resource_type="canon_rule",
            resource_id=rule.get("id"),
            payload={"rule_key": rule_key, "category": category, "severity": severity, "status": status},
        )
        return rule

    async def list_rules(
        self,
        project_id: str,
        status: str = "active",
        categories: list[str] | None = None,
        chapter_no: int | None = None,
        volume_no: int | None = None,
    ) -> dict[str, Any]:
        rules = await self._rules.list_rules(
            project_id=project_id,
            rule_types=["compliance"],
            status=status,
            chapter_no=chapter_no,
            volume_no=volume_no,
        )
        if categories:
            category_set = set(categories)
            rules = [rule for rule in rules if (rule.get("metadata") or {}).get("category") in category_set]
        return {"count": len(rules), "rules": rules}

    async def check(
        self,
        project_id: str,
        text: str | None = None,
        content_items: list[dict[str, Any]] | None = None,
        chapter_no: int | None = None,
        volume_no: int | None = None,
        scope_refs: list[str] | None = None,
        scope_types: list[str] | None = None,
        review_job_id: str | None = None,
        create_revision_task: bool = False,
        username: str | None = None,
    ) -> dict[str, Any]:
        items = self._content_items(text, content_items)
        if not items:
            raise ValueError("text or content_items is required")

        effective = await self._rules.list_effective_rules(
            project_id=project_id,
            rule_types=["compliance"],
            chapter_no=chapter_no,
            volume_no=volume_no,
            scope_refs=scope_refs,
            scope_types=scope_types,
        )
        findings: list[dict[str, Any]] = []
        for rule in effective["rules"]:
            metadata = rule.get("metadata") or {}
            match_type = metadata.get("match_type") or "keyword"
            case_sensitive = bool(metadata.get("case_sensitive"))
            patterns = self._normalize_patterns(metadata.get("patterns"), rule.get("content"))
            for pattern in patterns:
                for item in items:
                    try:
                        matches = self._matches_for_pattern(item["text"], pattern, match_type, case_sensitive)
                    except re.error as exc:
                        findings.append(
                            {
                                "type": "invalid_compliance_regex",
                                "rule_key": rule.get("rule_key"),
                                "title": rule.get("title"),
                                "severity": "blocking",
                                "category": metadata.get("category", "custom"),
                                "match_type": match_type,
                                "pattern": pattern,
                                "item_ref": item["ref"],
                                "message": f"Invalid compliance regex: {exc}",
                            }
                        )
                        continue
                    for match in matches:
                        start = int(match["start"])
                        end = int(match["end"])
                        findings.append(
                            {
                                "type": "compliance_match",
                                "rule_id": rule.get("id"),
                                "rule_key": rule.get("rule_key"),
                                "title": rule.get("title"),
                                "severity": rule.get("severity") or "critical",
                                "category": metadata.get("category", "custom"),
                                "match_type": match_type,
                                "pattern": pattern,
                                "matched_text": match["match"],
                                "item_ref": item["ref"],
                                "start": start,
                                "end": end,
                                "excerpt": self._excerpt(item["text"], start, end),
                                "hint": metadata.get("hint"),
                            }
                        )

        blocking_severities = {"critical", "blocker", "blocking"}
        critical_count = sum(1 for finding in findings if finding.get("severity") in blocking_severities)
        blocked = critical_count > 0
        created_revision_tasks = 0
        if blocked and create_revision_task and review_job_id:
            async with self._db.acquire() as conn:
                job = await conn.fetchrow(
                    "SELECT chapter_id FROM review_jobs WHERE project_id = $1 AND id = $2",
                    project_id,
                    review_job_id,
                )
                if job is None:
                    raise ValueError(f"Review job not found: {review_job_id}")
                for finding in findings:
                    if finding.get("severity") not in blocking_severities:
                        continue
                    await conn.execute(
                        """
                        INSERT INTO revision_tasks (project_id, chapter_id, review_job_id, title, description, severity, metadata)
                        VALUES ($1, $2, $3, $4, $5, 'blocking', $6::jsonb)
                        """,
                        project_id,
                        job["chapter_id"],
                        review_job_id,
                        finding.get("title") or finding.get("rule_key") or "Compliance finding",
                        finding.get("hint") or "Compliance critical finding blocks generation.",
                        json_dumps(finding),
                    )
                    created_revision_tasks += 1
                await conn.execute("UPDATE review_jobs SET status = 'blocked', updated_at = now() WHERE project_id = $1 AND id = $2", project_id, review_job_id)

        if blocked or create_revision_task:
            await self._audit(
                project_id=project_id,
                username=username,
                action="compliance.check",
                resource_type="review_job" if review_job_id else "project",
                resource_id=review_job_id,
                payload={
                    "blocked": blocked,
                    "critical_count": critical_count,
                    "finding_count": len(findings),
                    "checked_items": [item["ref"] for item in items],
                    "created_revision_tasks": created_revision_tasks,
                },
            )

        return {
            "ok": not blocked,
            "blocked": blocked,
            "critical_count": critical_count,
            "finding_count": len(findings),
            "findings": findings,
            "checked_items": [{"ref": item["ref"], "chars": len(item["text"])} for item in items],
            "rules_checked": len(effective["rules"]),
            "excluded_rules": effective["excluded"],
            "created_revision_tasks": created_revision_tasks,
        }
