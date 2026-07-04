#!/usr/bin/env sh
set -eu

cd /opt/novel-os

docker compose -f docker-compose.yml -f docker-compose.app.example.yml exec -T novel-os-mcp python - <<'PY'
import asyncio
import secrets

from novel_os_mcp.config import get_settings
from novel_os_mcp.db import Database
from novel_os_mcp.services import ComplianceService, ReviewService, RulesService, WorkspaceService


async def main() -> None:
    suffix = secrets.token_hex(4)
    username = f"verify_compliance_{suffix}"
    workspace_slug = f"verify-compliance-ws-{suffix}"
    project_slug = f"verify-compliance-project-{suffix}"

    db = Database(get_settings())
    await db.connect()
    workspace = WorkspaceService(db)
    rules = RulesService(db)
    compliance = ComplianceService(db, rules)
    review = ReviewService(db)
    try:
        await workspace.create_workspace(workspace_slug, "Verify Compliance Workspace", username)
        project = await workspace.create_project(
            workspace_slug,
            project_slug,
            "Verify Compliance Project",
            "temporary phase2 compliance verification",
            username,
        )
        project_id = project["id"]

        rule = await compliance.upsert_rule(
            project_id=project_id,
            rule_key="platform_forbidden_spell",
            title="Platform Forbidden Spell",
            content="forbidden-spell",
            category="platform_sensitive",
            patterns=["forbidden-spell"],
            match_type="keyword",
            severity="critical",
            hint="Remove or rewrite this platform-sensitive phrase.",
            username=username,
        )
        assert rule["rule_type"] == "compliance"
        assert rule["metadata"]["category"] == "platform_sensitive"

        listed = await compliance.list_rules(project_id=project_id, categories=["platform_sensitive"])
        assert listed["count"] == 1
        assert listed["rules"][0]["rule_key"] == "platform_forbidden_spell"

        safe = await compliance.check(
            project_id=project_id,
            text="The duel ends cleanly without sensitive terms.",
            username=username,
        )
        assert safe["ok"] is True
        assert safe["blocked"] is False
        assert safe["finding_count"] == 0

        risky = await compliance.check(
            project_id=project_id,
            content_items=[{"ref": "chapters/001.md", "text": "The forbidden-spell appears in the draft."}],
            username=username,
        )
        assert risky["ok"] is False
        assert risky["blocked"] is True
        assert risky["critical_count"] == 1
        assert risky["findings"][0]["item_ref"] == "chapters/001.md"

        job = await review.start_job(
            project_id=project_id,
            chapter_no=1,
            local_files=[{"kind": "chapter", "path_hint": "chapters/001.md", "sha256": "hash-compliance-ch1"}],
            dimensions=["compliance"],
            username=username,
        )
        blocked = await compliance.check(
            project_id=project_id,
            text="Another forbidden-spell should block the review job.",
            review_job_id=job["id"],
            create_revision_task=True,
            username=username,
        )
        assert blocked["blocked"] is True
        assert blocked["created_revision_tasks"] == 1

        tasks = await review.list_revision_tasks(project_id=project_id, status="open", severity=["blocking"], limit=10)
        assert len(tasks) == 1
        assert tasks[0]["review_job_id"] == job["id"]

        audit_row = await db.fetchrow(
            "SELECT count(*) AS count FROM audit_logs WHERE project_id = $1 AND action IN ('compliance.rule.upsert', 'compliance.check')",
            project_id,
        )
        assert audit_row["count"] >= 2

        print("phase2 compliance tools smoke ok")
    finally:
        await db.execute("DELETE FROM workspaces WHERE slug = $1", workspace_slug)
        await db.close()


asyncio.run(main())
PY
