#!/usr/bin/env sh
set -eu

cd /opt/novel-os

docker compose -f docker-compose.yml -f docker-compose.app.example.yml exec -T novel-os-mcp python - <<'PY'
import asyncio
import secrets

from novel_os_mcp.config import get_settings
from novel_os_mcp.db import Database
from novel_os_mcp.services import ReviewService, RulesService, WorkspaceService


async def main() -> None:
    suffix = secrets.token_hex(4)
    username = f"verify_learning_{suffix}"
    workspace_slug = f"verify-learning-ws-{suffix}"
    project_slug = f"verify-learning-project-{suffix}"

    db = Database(get_settings())
    await db.connect()
    workspace = WorkspaceService(db)
    review = ReviewService(db)
    rules = RulesService(db)
    try:
        await workspace.create_workspace(workspace_slug, "Verify Learning Workspace", username)
        project = await workspace.create_project(
            workspace_slug,
            project_slug,
            "Verify Learning Project",
            "temporary phase2 review learning verification",
            username,
        )
        project_id = project["id"]

        job = await review.start_job(
            project_id=project_id,
            chapter_no=12,
            local_files=[{"kind": "chapter", "path_hint": "chapters/012.md", "sha256": "hash-ch12"}],
            dimensions=["ooc", "state", "foreshadowing"],
            username=username,
        )
        review_job_id = job["id"]

        await review.submit_model_report(
            project_id=project_id,
            review_job_id=review_job_id,
            model_id="model_a",
            score=72,
            summary="Hero over-explains under pressure; jade token payoff is drifting.",
            findings=[
                {
                    "dimension": "ooc",
                    "severity": "critical",
                    "target": "Hero",
                    "evidence": "Hero explains too much while threatened.",
                    "suggestion": "Use shorter action-led responses in pressure scenes.",
                    "confidence": 0.91,
                    "rule_candidate": {
                        "rule_type": "character",
                        "title": "Hero pressure voice",
                        "content": "When Hero is threatened, prefer short actions and restrained lines over long explanations.",
                        "severity": "error",
                        "scope_type": "character",
                        "scope_ref": "Hero",
                        "priority": 20,
                    },
                    "state_update": {
                        "entity_type": "character",
                        "name": "Hero",
                        "state": {"pressure_response": "short_action_first"},
                        "duration_type": "persistent",
                        "confidence": 0.88,
                    },
                },
                {
                    "dimension": "foreshadowing",
                    "severity": "high",
                    "target": "Jade Token",
                    "suggestion": "Move payoff deadline closer to the sect trial.",
                    "foreshadowing_update": {
                        "key": "jade_token",
                        "title": "Jade Token",
                        "status": "planted",
                        "importance": "high",
                        "layer": "visible",
                        "payoff_deadline_chapter": 20,
                        "payload": {"review_note": "deadline adjusted by review"},
                    },
                },
            ],
            local_report_file={"path_hint": "reviews/012.model_a.md", "sha256": "review-a"},
        )

        await review.submit_model_report(
            project_id=project_id,
            review_job_id=review_job_id,
            model_id="model_b",
            score=84,
            summary="Main issue confirmed, but chapter can be repaired.",
            findings=[
                {
                    "dimension": "pacing",
                    "severity": "warning",
                    "target": "Middle beat",
                    "suggestion": "Trim exposition before the duel.",
                    "confidence": 0.72,
                }
            ],
            local_report_file={"path_hint": "reviews/012.model_b.md", "sha256": "review-b"},
        )

        learned = await review.learn_from_review(
            project_id=project_id,
            review_job_id=review_job_id,
            username=username,
            create_revision_tasks=True,
            create_rule_proposals=True,
            block_on_critical=True,
        )
        assert learned["blocked_next_chapter"] is True
        assert learned["rule_proposals"]["count"] == 1
        assert learned["state_updates"]["count"] == 1
        assert learned["foreshadowing_updates"]["count"] == 1
        assert len(learned["model_quality"]["models"]) == 2

        tasks = await review.list_revision_tasks(project_id=project_id, status="open", severity=["blocking", "high", "medium"], limit=20)
        severities = {task["severity"] for task in tasks}
        assert "blocking" in severities
        assert "high" in severities

        deduped = await review.extract_rule_proposals(
            project_id=project_id,
            review_job_id=review_job_id,
            username=username,
            create_proposals=True,
        )
        assert deduped["count"] == 1
        assert deduped["proposals"][0].get("deduplicated") is True

        proposal_id = learned["rule_proposals"]["proposals"][0]["id"]
        approved = await rules.apply_proposal(
            project_id=project_id,
            proposal_id=proposal_id,
            decision="approve",
            reason="verify review learning apply",
            username=username,
        )
        assert approved["rule"]["rule_type"] == "character"
        assert approved["rule"]["status"] == "active"

        print("phase2 review learning tools smoke ok")
    finally:
        await db.execute("DELETE FROM workspaces WHERE slug = $1", workspace_slug)
        await db.close()


asyncio.run(main())
PY
