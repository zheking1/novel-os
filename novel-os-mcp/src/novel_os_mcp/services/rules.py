import logging
from typing import Any

from ..db import Database
from ..utils import json_dumps, row_to_dict, rows_to_dicts, ensure_json_value

logger = logging.getLogger("novel_os_mcp.services.rules")


class RulesService:
    def __init__(self, db: Database):
        self._db = db

    def _normalize_rule(self, rule: dict[str, Any] | None) -> dict[str, Any] | None:
        if rule is None:
            return None
        normalized = dict(rule)
        normalized["metadata"] = ensure_json_value(normalized.get("metadata") or {})
        normalized["scope_config"] = ensure_json_value(normalized.get("scope_config") or {})
        normalized["supersedes_rule_ids"] = list(normalized.get("supersedes_rule_ids") or [])
        normalized["blocked_by_rule_ids"] = list(normalized.get("blocked_by_rule_ids") or [])
        return normalized

    def _normalize_rules(self, rules: list[dict[str, Any]]) -> list[dict[str, Any]]:
        return [rule for rule in (self._normalize_rule(rule) for rule in rules) if rule is not None]

    def _rule_identifiers(self, rule: dict[str, Any]) -> set[str]:
        return {str(rule.get("id", "")), str(rule.get("rule_key", ""))} - {""}

    def _rule_scope_matches(
        self,
        rule: dict[str, Any],
        chapter_no: int | None,
        volume_no: int | None,
        scope_refs: list[str] | None,
        scope_types: list[str] | None,
    ) -> bool:
        scope_type = rule.get("scope_type") or rule.get("scope") or "global"
        scope_ref = rule.get("scope_ref")
        if scope_types and scope_type not in scope_types and scope_type != "global":
            return False
        if scope_type == "global":
            return True
        if scope_type == "chapter":
            return chapter_no is not None and (scope_ref is None or str(scope_ref) == str(chapter_no))
        if scope_type == "volume":
            return volume_no is not None and (scope_ref is None or str(scope_ref) == str(volume_no))
        if scope_refs is None:
            return True
        return scope_ref in scope_refs

    def _event_lifecycle_matches(self, rule: dict[str, Any], active_event_keys: list[str] | None) -> bool:
        event_keys = set(active_event_keys or [])
        active_from_event = rule.get("active_from_event")
        expire_on_event = rule.get("expire_on_event")
        if active_from_event and active_from_event not in event_keys:
            return False
        if expire_on_event and expire_on_event in event_keys:
            return False
        return True

    def _filter_rules_for_context(
        self,
        rules: list[dict[str, Any]],
        chapter_no: int | None,
        volume_no: int | None,
        scope_refs: list[str] | None,
        scope_types: list[str] | None,
        active_event_keys: list[str] | None,
        include_blocked: bool,
    ) -> dict[str, Any]:
        matched = [
            rule
            for rule in rules
            if self._rule_scope_matches(rule, chapter_no, volume_no, scope_refs, scope_types)
            and self._event_lifecycle_matches(rule, active_event_keys)
        ]
        if include_blocked:
            return {"rules": matched, "excluded": []}

        active_identifiers: set[str] = set()
        for rule in matched:
            active_identifiers.update(self._rule_identifiers(rule))

        superseded_identifiers: set[str] = set()
        for rule in matched:
            superseded_identifiers.update(str(value) for value in (rule.get("supersedes_rule_ids") or []))

        kept: list[dict[str, Any]] = []
        excluded: list[dict[str, Any]] = []
        for rule in matched:
            identifiers = self._rule_identifiers(rule)
            blockers = set(str(value) for value in (rule.get("blocked_by_rule_ids") or []))
            if identifiers & superseded_identifiers:
                excluded.append({**rule, "excluded_reason": "superseded"})
            elif blockers & active_identifiers:
                excluded.append({**rule, "excluded_reason": "blocked"})
            else:
                kept.append(rule)
        return {"rules": kept, "excluded": excluded}

    async def list_rules(
        self,
        project_id: str,
        rule_types: list[str] | None,
        status: str | None = "active",
        chapter_no: int | None = None,
        volume_no: int | None = None,
    ) -> list[dict[str, Any]]:
        conditions = ["project_id = $1", "is_deleted = false"]
        params: list[Any] = [project_id]
        idx = 2
        
        if status is not None:
            conditions.append(f"status = ${idx}")
            params.append(status)
            idx += 1
        
        if rule_types:
            conditions.append(f"rule_type = ANY(${idx}::text[])")
            params.append(rule_types)
            idx += 1
        
        conditions.append(f"(${idx}::int IS NULL OR effective_chapter_no IS NULL OR effective_chapter_no <= ${idx})")
        params.append(chapter_no)
        idx += 1
        conditions.append(f"(${idx}::int IS NULL OR expire_chapter_no IS NULL OR expire_chapter_no >= ${idx})")
        params.append(chapter_no)
        idx += 1
        conditions.append(f"(${idx}::int IS NULL OR effective_volume_no IS NULL OR effective_volume_no <= ${idx})")
        params.append(volume_no)
        idx += 1
        conditions.append(f"(${idx}::int IS NULL OR expire_volume_no IS NULL OR expire_volume_no >= ${idx})")
        params.append(volume_no)
        
        rows = await self._db.fetch(
            f"""
            SELECT id::text, rule_key, rule_type, scope, scope_type, scope_ref, scope_config,
                   title, content, severity, status, version, priority,
                   effective_chapter_no, expire_chapter_no, effective_volume_no, expire_volume_no,
                   is_temporary, active_from_event, expire_on_event, conflict_policy,
                   supersedes_rule_ids, blocked_by_rule_ids, metadata
            FROM canon_rules
            WHERE {' AND '.join(conditions)}
            ORDER BY priority ASC, rule_type, rule_key
            """,
            *params,
        )
        return rows_to_dicts(rows)

    async def list_effective_rules(
        self,
        project_id: str,
        rule_types: list[str] | None = None,
        chapter_no: int | None = None,
        volume_no: int | None = None,
        scope_refs: list[str] | None = None,
        scope_types: list[str] | None = None,
        active_event_keys: list[str] | None = None,
        include_blocked: bool = False,
    ) -> dict[str, Any]:
        rules = await self.list_rules(
            project_id=project_id,
            rule_types=rule_types,
            status="active",
            chapter_no=chapter_no,
            volume_no=volume_no,
        )
        filtered = self._filter_rules_for_context(
            rules=rules,
            chapter_no=chapter_no,
            volume_no=volume_no,
            scope_refs=scope_refs,
            scope_types=scope_types,
            active_event_keys=active_event_keys,
            include_blocked=include_blocked,
        )
        return {
            "rules": filtered["rules"],
            "excluded": filtered["excluded"],
            "count": len(filtered["rules"]),
            "excluded_count": len(filtered["excluded"]),
        }

    async def check_conflicts(
        self,
        project_id: str,
        rule_types: list[str] | None = None,
        chapter_no: int | None = None,
        volume_no: int | None = None,
        scope_refs: list[str] | None = None,
        scope_types: list[str] | None = None,
        active_event_keys: list[str] | None = None,
        text: str | None = None,
    ) -> dict[str, Any]:
        effective = await self.list_effective_rules(
            project_id=project_id,
            rule_types=rule_types,
            chapter_no=chapter_no,
            volume_no=volume_no,
            scope_refs=scope_refs,
            scope_types=scope_types,
            active_event_keys=active_event_keys,
            include_blocked=True,
        )
        rules = effective["rules"]
        identifiers_by_rule: dict[str, dict[str, Any]] = {}
        for rule in rules:
            for identifier in self._rule_identifiers(rule):
                identifiers_by_rule[identifier] = rule

        conflicts: list[dict[str, Any]] = []
        for rule in rules:
            for blocked_by in rule.get("blocked_by_rule_ids") or []:
                blocker = identifiers_by_rule.get(str(blocked_by))
                if blocker:
                    conflicts.append(
                        {
                            "type": "blocked_by_active_rule",
                            "severity": "warning",
                            "rule": rule,
                            "conflicting_rule": blocker,
                            "message": f"{rule['rule_key']} is blocked by active rule {blocker['rule_key']}",
                        }
                    )
            for superseded in rule.get("supersedes_rule_ids") or []:
                target = identifiers_by_rule.get(str(superseded))
                if target:
                    conflicts.append(
                        {
                            "type": "supersedes_active_rule",
                            "severity": "info",
                            "rule": rule,
                            "conflicting_rule": target,
                            "message": f"{rule['rule_key']} supersedes active rule {target['rule_key']}",
                        }
                    )

        grouped: dict[tuple[Any, ...], list[dict[str, Any]]] = {}
        for rule in rules:
            key = (
                rule.get("rule_type"),
                rule.get("scope_type") or rule.get("scope"),
                rule.get("scope_ref"),
                rule.get("effective_chapter_no"),
                rule.get("expire_chapter_no"),
                rule.get("effective_volume_no"),
                rule.get("expire_volume_no"),
            )
            grouped.setdefault(key, []).append(rule)
        for group_rules in grouped.values():
            by_priority: dict[int, list[dict[str, Any]]] = {}
            for rule in group_rules:
                by_priority.setdefault(int(rule.get("priority") or 100), []).append(rule)
            for same_priority_rules in by_priority.values():
                contents = {rule.get("content") for rule in same_priority_rules}
                if len(same_priority_rules) > 1 and len(contents) > 1:
                    conflicts.append(
                        {
                            "type": "same_scope_same_priority",
                            "severity": "warning",
                            "rules": same_priority_rules,
                            "message": "Multiple active rules share the same type, scope, lifecycle, and priority.",
                        }
                    )

        text_matches: list[dict[str, Any]] = []
        if text:
            lowered_text = text.lower()
            for rule in rules:
                metadata = rule.get("metadata") or {}
                keywords = metadata.get("keywords") if isinstance(metadata, dict) else None
                if not isinstance(keywords, list):
                    keywords = []
                matches = [str(keyword) for keyword in keywords if str(keyword).lower() in lowered_text]
                if matches:
                    text_matches.append(
                        {
                            "rule": rule,
                            "matched_keywords": matches,
                            "severity": rule.get("severity", "warning"),
                        }
                    )

        return {
            "ok": len(conflicts) == 0,
            "conflict_count": len(conflicts),
            "conflicts": conflicts,
            "text_match_count": len(text_matches),
            "text_matches": text_matches,
        }

    async def bulk_toggle_rules(
        self,
        project_id: str,
        status: str,
        rule_keys: list[str] | None = None,
        rule_ids: list[str] | None = None,
        rule_types: list[str] | None = None,
        reason: str | None = None,
    ) -> list[dict[str, Any]]:
        if status not in {"active", "disabled", "superseded", "archived"}:
            raise ValueError("status must be active, disabled, superseded, or archived")
        if not rule_keys and not rule_ids and not rule_types:
            raise ValueError("rule_keys, rule_ids, or rule_types is required")
        rows = await self._db.fetch(
            """
            UPDATE canon_rules
            SET status = $2,
                metadata = metadata || $6::jsonb,
                updated_at = now()
            WHERE project_id = $1
              AND ($3::text[] IS NULL OR rule_key = ANY($3::text[]))
              AND ($4::text[] IS NULL OR id::text = ANY($4::text[]))
              AND ($5::text[] IS NULL OR rule_type = ANY($5::text[]))
            RETURNING id::text, rule_key, rule_type, scope, scope_type, scope_ref,
                      title, severity, status, version, priority, metadata
            """,
            project_id,
            status,
            rule_keys,
            rule_ids,
            rule_types,
            json_dumps({"last_toggle_reason": reason} if reason else {}),
        )
        return rows_to_dicts(rows)

    async def resolve_conflict(
        self,
        project_id: str,
        action: str,
        source_rule_key: str | None = None,
        source_rule_id: str | None = None,
        target_rule_keys: list[str] | None = None,
        target_rule_ids: list[str] | None = None,
        priority: int | None = None,
        reason: str | None = None,
    ) -> dict[str, Any]:
        if action not in {"disable", "supersede", "block", "set_priority"}:
            raise ValueError("action must be disable, supersede, block, or set_priority")
        if action in {"supersede", "block", "set_priority"} and not (source_rule_key or source_rule_id):
            raise ValueError("source_rule_key or source_rule_id is required for this action")
        if action == "set_priority" and priority is None:
            raise ValueError("priority is required for set_priority")
        if action in {"disable", "supersede", "block"} and not (target_rule_keys or target_rule_ids):
            raise ValueError("target_rule_keys or target_rule_ids is required for this action")

        async with self._db.acquire() as conn:
            async with conn.transaction():
                source = None
                if source_rule_key or source_rule_id:
                    source = await conn.fetchrow(
                        """
                        SELECT id::text, rule_key
                        FROM canon_rules
                        WHERE project_id = $1
                          AND ($2::text IS NULL OR rule_key = $2)
                          AND ($3::text IS NULL OR id::text = $3)
                        FOR UPDATE
                        """,
                        project_id,
                        source_rule_key,
                        source_rule_id,
                    )
                    if source is None:
                        raise ValueError("Source rule not found")

                updated_rows = []
                target_identifiers = list(target_rule_keys or []) + list(target_rule_ids or [])
                if action == "disable":
                    updated_rows = await conn.fetch(
                        """
                        UPDATE canon_rules
                        SET status = 'disabled',
                            metadata = metadata || $4::jsonb,
                            updated_at = now()
                        WHERE project_id = $1
                          AND (($2::text[] IS NOT NULL AND rule_key = ANY($2::text[]))
                               OR ($3::text[] IS NOT NULL AND id::text = ANY($3::text[])))
                        RETURNING id::text, rule_key, rule_type, title, status, priority, metadata
                        """,
                        project_id,
                        target_rule_keys,
                        target_rule_ids,
                        json_dumps({"disabled_reason": reason} if reason else {}),
                    )
                elif action == "supersede":
                    updated_rows = await conn.fetch(
                        """
                        UPDATE canon_rules
                        SET status = 'superseded',
                            metadata = metadata || $4::jsonb,
                            updated_at = now()
                        WHERE project_id = $1
                          AND (($2::text[] IS NOT NULL AND rule_key = ANY($2::text[]))
                               OR ($3::text[] IS NOT NULL AND id::text = ANY($3::text[])))
                        RETURNING id::text, rule_key, rule_type, title, status, priority, metadata
                        """,
                        project_id,
                        target_rule_keys,
                        target_rule_ids,
                        json_dumps({"superseded_by": source["rule_key"], "resolve_reason": reason}),
                    )
                    await conn.execute(
                        """
                        UPDATE canon_rules
                        SET supersedes_rule_ids = (
                              SELECT ARRAY(SELECT DISTINCT unnest(supersedes_rule_ids || $4::text[]))
                            ),
                            updated_at = now()
                        WHERE project_id = $1
                          AND (($2::text IS NULL OR rule_key = $2)
                               AND ($3::text IS NULL OR id::text = $3))
                        """,
                        project_id,
                        source_rule_key,
                        source_rule_id,
                        target_identifiers,
                    )
                elif action == "block":
                    updated_rows = await conn.fetch(
                        """
                        UPDATE canon_rules
                        SET blocked_by_rule_ids = (
                              SELECT ARRAY(SELECT DISTINCT unnest(blocked_by_rule_ids || $4::text[]))
                            ),
                            metadata = metadata || $5::jsonb,
                            updated_at = now()
                        WHERE project_id = $1
                          AND (($2::text[] IS NOT NULL AND rule_key = ANY($2::text[]))
                               OR ($3::text[] IS NOT NULL AND id::text = ANY($3::text[])))
                        RETURNING id::text, rule_key, rule_type, title, status, priority, blocked_by_rule_ids, metadata
                        """,
                        project_id,
                        target_rule_keys,
                        target_rule_ids,
                        [source["rule_key"], source["id"]],
                        json_dumps({"blocked_reason": reason} if reason else {}),
                    )
                elif action == "set_priority":
                    updated_rows = await conn.fetch(
                        """
                        UPDATE canon_rules
                        SET priority = $4,
                            metadata = metadata || $5::jsonb,
                            updated_at = now()
                        WHERE project_id = $1
                          AND (($2::text IS NULL OR rule_key = $2)
                               AND ($3::text IS NULL OR id::text = $3))
                        RETURNING id::text, rule_key, rule_type, title, status, priority, metadata
                        """,
                        project_id,
                        source_rule_key,
                        source_rule_id,
                        priority,
                        json_dumps({"priority_reason": reason} if reason else {}),
                    )
        return {
            "action": action,
            "source_rule": row_to_dict(source) if source else None,
            "updated": self._normalize_rules(rows_to_dicts(updated_rows)),
            "updated_count": len(updated_rows),
        }

    async def upsert_rule(
        self,
        project_id: str,
        rule_key: str,
        rule_type: str,
        title: str,
        content: str,
        scope: str = "global",
        severity: str = "warning",
        status: str = "active",
        metadata: dict[str, Any] | None = None,
        change_reason: str | None = None,
        source: str = "manual",
        scope_type: str = "global",
        scope_ref: str | None = None,
        scope_config: dict[str, Any] | None = None,
        priority: int = 100,
        effective_chapter_no: int | None = None,
        expire_chapter_no: int | None = None,
        effective_volume_no: int | None = None,
        expire_volume_no: int | None = None,
        is_temporary: bool = False,
        active_from_event: str | None = None,
        expire_on_event: str | None = None,
        conflict_policy: str = "priority",
        supersedes_rule_ids: list[str] | None = None,
        blocked_by_rule_ids: list[str] | None = None,
    ) -> dict[str, Any]:
        async with self._db.acquire() as conn:
            async with conn.transaction():
                current = await conn.fetchrow(
                    "SELECT id, version, content FROM canon_rules WHERE project_id = $1 AND rule_key = $2 FOR UPDATE",
                    project_id,
                    rule_key,
                )
                if current is None:
                    row = await conn.fetchrow(
                        """
                        INSERT INTO canon_rules (
                          project_id, rule_key, rule_type, scope, title, content, severity, status, version, metadata,
                          scope_type, scope_ref, scope_config, priority,
                          effective_chapter_no, expire_chapter_no, effective_volume_no, expire_volume_no,
                          is_temporary, active_from_event, expire_on_event, conflict_policy,
                          supersedes_rule_ids, blocked_by_rule_ids
                        )
                        VALUES (
                          $1, $2, $3, $4, $5, $6, $7, $8, 1, $9::jsonb,
                          $10, $11, $12::jsonb, $13,
                          $14, $15, $16, $17,
                          $18, $19, $20, $21,
                          $22::text[], $23::text[]
                        )
                        RETURNING id, id::text AS id_text, rule_key, rule_type, scope, scope_type, scope_ref,
                                  scope_config, title, content, severity, status, version, priority,
                                  effective_chapter_no, expire_chapter_no, effective_volume_no, expire_volume_no,
                                  is_temporary, active_from_event, expire_on_event, conflict_policy,
                                  supersedes_rule_ids, blocked_by_rule_ids, metadata
                        """,
                        project_id,
                        rule_key,
                        rule_type,
                        scope,
                        title,
                        content,
                        severity,
                        status,
                        json_dumps(metadata or {}),
                        scope_type,
                        scope_ref,
                        json_dumps(scope_config or {}),
                        priority,
                        effective_chapter_no,
                        expire_chapter_no,
                        effective_volume_no,
                        expire_volume_no,
                        is_temporary,
                        active_from_event,
                        expire_on_event,
                        conflict_policy,
                        supersedes_rule_ids or [],
                        blocked_by_rule_ids or [],
                    )
                    version = 1
                else:
                    version = int(current["version"]) + 1
                    row = await conn.fetchrow(
                        """
                        UPDATE canon_rules
                        SET rule_type = $3, scope = $4, title = $5, content = $6,
                            severity = $7, status = $8, version = $9,
                            metadata = $10::jsonb,
                            scope_type = $11,
                            scope_ref = $12,
                            scope_config = $13::jsonb,
                            priority = $14,
                            effective_chapter_no = $15,
                            expire_chapter_no = $16,
                            effective_volume_no = $17,
                            expire_volume_no = $18,
                            is_temporary = $19,
                            active_from_event = $20,
                            expire_on_event = $21,
                            conflict_policy = $22,
                            supersedes_rule_ids = $23::text[],
                            blocked_by_rule_ids = $24::text[],
                            updated_at = now()
                        WHERE project_id = $1 AND rule_key = $2
                        RETURNING id, id::text AS id_text, rule_key, rule_type, scope, scope_type, scope_ref,
                                  scope_config, title, content, severity, status, version, priority,
                                  effective_chapter_no, expire_chapter_no, effective_volume_no, expire_volume_no,
                                  is_temporary, active_from_event, expire_on_event, conflict_policy,
                                  supersedes_rule_ids, blocked_by_rule_ids, metadata
                        """,
                        project_id,
                        rule_key,
                        rule_type,
                        scope,
                        title,
                        content,
                        severity,
                        status,
                        version,
                        json_dumps(metadata or {}),
                        scope_type,
                        scope_ref,
                        json_dumps(scope_config or {}),
                        priority,
                        effective_chapter_no,
                        expire_chapter_no,
                        effective_volume_no,
                        expire_volume_no,
                        is_temporary,
                        active_from_event,
                        expire_on_event,
                        conflict_policy,
                        supersedes_rule_ids or [],
                        blocked_by_rule_ids or [],
                    )
                await conn.execute(
                    """
                    INSERT INTO rule_versions (project_id, rule_id, version, content, change_reason, source)
                    VALUES ($1, $2, $3, $4, $5, $6)
                    ON CONFLICT (rule_id, version) DO NOTHING
                    """,
                    project_id,
                    row["id"],
                    version,
                    content,
                    change_reason,
                    source,
                )
        result = row_to_dict(row)
        result["id"] = result.pop("id_text")
        return self._normalize_rule(result)

    async def list_rule_proposals(
        self,
        project_id: str,
        status: str | None = "proposed",
        limit: int = 100,
    ) -> list[dict[str, Any]]:
        rows = await self._db.fetch(
            """
            SELECT id::text, source_type, source_id::text, proposal_type, target_rule_id::text,
                   title, content, confidence, agreement, status, created_at, resolved_at
            FROM rule_proposals
            WHERE project_id = $1
              AND ($2::text IS NULL OR status = $2)
            ORDER BY created_at DESC
            LIMIT $3
            """,
            project_id,
            status,
            limit,
        )
        return rows_to_dicts(rows)

    async def propose_rule(self, project_id: str, proposal: dict[str, Any], username: str) -> dict[str, Any]:
        row = await self._db.fetchrow(
            """
            INSERT INTO rule_proposals (
              project_id, source_type, source_id, proposal_type, target_rule_id,
              title, content, confidence, agreement, status, created_by
            )
            SELECT $1, $2, NULL, $3, NULL, $4, $5, $6, $7::jsonb, 'proposed', users.id
            FROM users
            WHERE users.username = $8
            RETURNING id::text, proposal_type, title, content, confidence, agreement, status, created_at
            """,
            project_id,
            proposal.get("source_type", "user"),
            proposal.get("proposal_type", "create"),
            proposal["title"],
            proposal["content"],
            proposal.get("confidence"),
            json_dumps(proposal.get("agreement", {})),
            username,
        )
        if row is None:
            raise ValueError(f"User not found: {username}")
        return row_to_dict(row)

    async def apply_proposal(self, project_id: str, proposal_id: str, decision: str, reason: str | None, username: str) -> dict[str, Any]:
        if decision not in {"approve", "reject"}:
            raise ValueError("decision must be approve or reject")
        async with self._db.acquire() as conn:
            async with conn.transaction():
                user = await conn.fetchrow("SELECT id FROM users WHERE username = $1", username)
                if user is None:
                    raise ValueError(f"User not found: {username}")
                proposal = await conn.fetchrow(
                    """
                    SELECT *
                    FROM rule_proposals
                    WHERE project_id = $1 AND id = $2
                    FOR UPDATE
                    """,
                    project_id,
                    proposal_id,
                )
                if proposal is None:
                    raise ValueError(f"Rule proposal not found: {proposal_id}")
                if decision == "reject":
                    row = await conn.fetchrow(
                        """
                        UPDATE rule_proposals
                        SET status = 'rejected', approved_by = $3, resolved_at = now()
                        WHERE project_id = $1 AND id = $2
                        RETURNING id::text, status, title, content, resolved_at
                        """,
                        project_id,
                        proposal_id,
                        user["id"],
                    )
                    return row_to_dict(row)

                if proposal["proposal_type"] == "create":
                    rule_key = "rule_" + str(proposal["id"]).replace("-", "_")
                    agreement = ensure_json_value(proposal["agreement"]) or {}
                    rule_data = agreement.get("rule") or agreement.get("rule_candidate") or {}
                    rule = await conn.fetchrow(
                        """
                        INSERT INTO canon_rules (
                          project_id, rule_key, rule_type, scope, title, content, severity, status, version, metadata,
                          scope_type, scope_ref, scope_config, priority,
                          effective_chapter_no, expire_chapter_no, effective_volume_no, expire_volume_no,
                          is_temporary, active_from_event, expire_on_event, conflict_policy,
                          supersedes_rule_ids, blocked_by_rule_ids
                        )
                        VALUES (
                          $1, $2, $3, $4, $5, $6, $7, 'active', 1, $8::jsonb,
                          $9, $10, $11::jsonb, $12,
                          $13, $14, $15, $16,
                          $17, $18, $19, $20,
                          COALESCE($21::text[], ARRAY[]::text[]),
                          COALESCE($22::text[], ARRAY[]::text[])
                        )
                        RETURNING id, id::text AS id_text, rule_key, rule_type, title, content, status, version
                        """,
                        project_id,
                        rule_key,
                        rule_data.get("rule_type", "style"),
                        rule_data.get("scope", "global"),
                        proposal["title"],
                        proposal["content"],
                        rule_data.get("severity", "warning"),
                        json_dumps({"source_proposal_id": str(proposal["id"]), "apply_reason": reason, "agreement": agreement}),
                        rule_data.get("scope_type", "global"),
                        rule_data.get("scope_ref"),
                        json_dumps(rule_data.get("scope_config", {})),
                        rule_data.get("priority", 100),
                        rule_data.get("effective_chapter_no"),
                        rule_data.get("expire_chapter_no"),
                        rule_data.get("effective_volume_no"),
                        rule_data.get("expire_volume_no"),
                        rule_data.get("is_temporary", False),
                        rule_data.get("active_from_event"),
                        rule_data.get("expire_on_event"),
                        rule_data.get("conflict_policy", "priority"),
                        rule_data.get("supersedes_rule_ids", []),
                        rule_data.get("blocked_by_rule_ids", []),
                    )
                    await conn.execute(
                        """
                        INSERT INTO rule_versions (project_id, rule_id, version, content, change_reason, source)
                        VALUES ($1, $2, 1, $3, $4, 'proposal')
                        """,
                        project_id,
                        rule["id"],
                        proposal["content"],
                        reason,
                    )
                elif proposal["proposal_type"] == "update":
                    if proposal["target_rule_id"] is None:
                        raise ValueError("update proposal requires target_rule_id")
                    current = await conn.fetchrow(
                        "SELECT id, version FROM canon_rules WHERE project_id = $1 AND id = $2 FOR UPDATE",
                        project_id,
                        proposal["target_rule_id"],
                    )
                    if current is None:
                        raise ValueError("Target rule not found")
                    next_version = int(current["version"]) + 1
                    rule = await conn.fetchrow(
                        """
                        UPDATE canon_rules
                        SET title = $3, content = $4, version = $5, updated_at = now()
                        WHERE project_id = $1 AND id = $2
                        RETURNING id, id::text AS id_text, rule_key, rule_type, title, content, status, version
                        """,
                        project_id,
                        proposal["target_rule_id"],
                        proposal["title"],
                        proposal["content"],
                        next_version,
                    )
                    await conn.execute(
                        """
                        INSERT INTO rule_versions (project_id, rule_id, version, content, change_reason, source)
                        VALUES ($1, $2, $3, $4, $5, 'proposal')
                        """,
                        project_id,
                        rule["id"],
                        next_version,
                        proposal["content"],
                        reason,
                    )
                else:
                    raise ValueError(f"Unsupported proposal_type: {proposal['proposal_type']}")

                await conn.execute(
                    """
                    UPDATE rule_proposals
                    SET status = 'approved', approved_by = $3, resolved_at = now()
                    WHERE project_id = $1 AND id = $2
                    """,
                    project_id,
                    proposal_id,
                    user["id"],
                )
        return {
            "proposal_id": proposal_id,
            "decision": decision,
            "rule": {
                "id": rule["id_text"],
                "rule_key": rule["rule_key"],
                "rule_type": rule["rule_type"],
                "title": rule["title"],
                "status": rule["status"],
                "version": rule["version"],
            },
        }

    async def delete_rule(self, project_id: str, rule_key: str | None = None, rule_id: str | None = None) -> dict[str, Any]:
        """软删除规则"""
        if not rule_key and not rule_id:
            raise ValueError("rule_key or rule_id is required")
        
        conditions = ["project_id = $1"]
        params: list[Any] = [project_id]
        idx = 2
        
        if rule_key:
            conditions.append(f"rule_key = ${idx}")
            params.append(rule_key)
            idx += 1
        if rule_id:
            conditions.append(f"id::text = ${idx}")
            params.append(rule_id)
            idx += 1
        
        row = await self._db.fetchrow(
            f"""
            UPDATE canon_rules SET is_deleted = true, updated_at = now()
            WHERE {' AND '.join(conditions)}
            RETURNING id::text, rule_key, title, rule_type
            """,
            *params,
        )
        if not row:
            raise ValueError(f"规则不存在")
        return {"deleted": True, "rule_key": row["rule_key"], "title": row["title"]}

    async def list_active_global(self, rule_type: str | None = None) -> list[dict[str, Any]]:
        conditions = ["status = 'active'"]
        params: list[Any] = []
        if rule_type:
            conditions.append("rule_type = $1")
            params.append(rule_type)
        rows = await self._db.fetch(
            f"SELECT * FROM global_rules WHERE {' AND '.join(conditions)} ORDER BY created_at DESC LIMIT 200",
            *params,
        )
        return rows_to_dicts(rows)

    async def list_global_rules(
        self, rule_type: str | None = None, status: str = "active", limit: int = 100
    ) -> list[dict[str, Any]]:
        conditions = ["status = $1"]
        params: list[Any] = [status]
        idx = 2
        if rule_type:
            conditions.append(f"rule_type = ${idx}")
            params.append(rule_type)
            idx += 1
        params.append(limit)
        rows = await self._db.fetch(
            f"""SELECT * FROM global_rules WHERE {' AND '.join(conditions)}
                ORDER BY created_at DESC LIMIT ${idx}""",
            *params,
        )
        return rows_to_dicts(rows)

    async def upsert_global_rule(
        self, rule_key: str, rule_type: str, title: str, content: str,
        severity: str = "warning", status: str = "active",
        metadata: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        await self._db.connect()
        row = await self._db.fetchrow(
            """INSERT INTO global_rules (rule_key, rule_type, title, content, severity, status, metadata)
               VALUES ($1, $2, $3, $4, $5, $6, $7)
               ON CONFLICT (rule_key) DO UPDATE SET
                 rule_type = $2, title = $3, content = $4, severity = $5,
                 status = $6, metadata = coalesce($7, global_rules.metadata),
                 updated_at = NOW()
               RETURNING *""",
            rule_key, rule_type, title, content, severity, status,
            json_dumps(metadata or {}),
        )
        return row_to_dict(row) if row else {"ok": True, "rule_key": rule_key}

    async def delete_global_rule(self, rule_key: str) -> dict[str, Any]:
        await self._db.connect()
        row = await self._db.fetchrow(
            "UPDATE global_rules SET status = 'inactive', updated_at = NOW() WHERE rule_key = $1 RETURNING rule_key, title",
            rule_key,
        )
        if not row:
            return {"ok": False, "error": f"Global rule not found: {rule_key}"}
        return {"ok": True, "deleted": True, "rule_key": row["rule_key"], "title": row["title"]}

    async def promote_to_global(
        self, project_id: str, rule_key: str, promoted_by: str = "",
        discussion_id: str = "",
    ) -> dict[str, Any]:
        await self._db.connect()
        project_rule = await self._db.fetchrow(
            "SELECT * FROM canon_rules WHERE project_id = $1 AND rule_key = $2 AND is_deleted = false",
            project_id, rule_key,
        )
        if not project_rule:
            return {"ok": False, "error": f"Project rule not found: {rule_key}"}
        global_row = await self._db.fetchrow(
            """INSERT INTO global_rules (rule_key, rule_type, title, content, severity, status,
               metadata, source_project_id, promoted_from_rule_id, promoted_by, discussion_id)
               VALUES ($1, $2, $3, $4, $5, 'active', $6, $7, $8, $9, $10)
               ON CONFLICT (rule_key) DO UPDATE SET
                 rule_type = $2, title = $3, content = $4, severity = $5,
                 metadata = $6, promoted_by = $9, discussion_id = $10,
                 updated_at = NOW()
               RETURNING *""",
            rule_key,
            project_rule.get("rule_type", "creative"),
            project_rule["title"],
            project_rule["content"],
            project_rule.get("severity", "warning"),
            json_dumps(project_rule.get("metadata") or {}),
            project_id,
            project_rule["id"],
            promoted_by,
            discussion_id,
        )
        await self._db.execute(
            "UPDATE canon_rules SET promotion_status = 'promoted', promoted_to_global_id = $1, discussion_id = $2 WHERE project_id = $3 AND rule_key = $4",
            global_row["id"], discussion_id, project_id, rule_key,
        )
        return {
            "ok": True,
            "global_rule": row_to_dict(global_row),
            "project_rule_key": rule_key,
        }
