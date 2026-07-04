#!/usr/bin/env sh
set -eu

cd /opt/novel-os

docker compose -f docker-compose.yml -f docker-compose.app.example.yml exec -T novel-os-mcp python - <<'PY'
import asyncio
import json
import secrets

from novel_os_mcp.config import get_settings
from novel_os_mcp.db import Database
from novel_os_mcp.services import ContextService, MemoryService, PlotService, RulesService, WorkspaceService
from novel_os_mcp.utils import json_dumps


def section_payload(pack, name):
    for section in pack["sections"]:
        if section["name"] == name:
            return json.loads(section["content"])
    raise AssertionError(f"missing section: {name}")


async def main() -> None:
    suffix = secrets.token_hex(4)
    username = f"verify_context_{suffix}"
    workspace_slug = f"verify-context-ws-{suffix}"
    project_slug = f"verify-context-project-{suffix}"

    db = Database(get_settings())
    await db.connect()
    workspace = WorkspaceService(db)
    memory = MemoryService(db)
    rules = RulesService(db)
    plot = PlotService(db)
    context = ContextService(db, memory, rules, plot)
    try:
        await workspace.create_workspace(workspace_slug, "Verify Context Workspace", username)
        assert len(await workspace.list_workspaces(username)) == 1
        project = await workspace.create_project(
            workspace_slug,
            project_slug,
            "Verify Context Project",
            "temporary phase2 context verification",
            username,
        )
        project_id = project["id"]

        await rules.upsert_rule(
            project_id=project_id,
            rule_key="canon_hard",
            rule_type="canon",
            title="Hard Canon",
            content="Power ranks cannot be skipped.",
            severity="critical",
            priority=10,
        )
        await rules.upsert_rule(
            project_id=project_id,
            rule_key="old_style",
            rule_type="style",
            title="Old Style",
            content="Old rule.",
            priority=50,
        )
        await rules.upsert_rule(
            project_id=project_id,
            rule_key="new_style",
            rule_type="style",
            title="New Style",
            content="New rule.",
            priority=40,
            supersedes_rule_ids=["old_style"],
        )
        await memory.upsert_snapshot(
            project_id=project_id,
            entity_type="character",
            name="Hero",
            state={"realm": "Foundation", "injury": "minor"},
            effective_chapter_no=8,
            expire_chapter_no=12,
            duration_type="temporary",
        )
        await plot.upsert_foreshadowing(
            project_id=project_id,
            key="visible_seed",
            title="Visible Seed",
            status="planted",
            importance="critical",
            layer="visible",
            must_payoff=True,
            payoff_deadline_chapter=9,
            overdue_policy="block",
        )
        await plot.upsert_foreshadowing(
            project_id=project_id,
            key="hidden_seed",
            title="Hidden Seed",
            status="planted",
            importance="critical",
            layer="hidden",
            must_payoff=True,
            payoff_deadline_chapter=20,
        )

        preflight = await context.preflight_generation(
            project_id=project_id,
            chapter_no=10,
            purpose="draft",
            focus=["Hero"],
            budget={"total_tokens": 20000, "recent_count": 3, "foreshadowing_limit": 10},
            volume_no=1,
            scope_refs=["Hero"],
            pov_mode="protagonist",
        )
        assert preflight["can_generate"] is False
        pack = preflight["context_pack"]
        rules_payload = section_payload(pack, "active_rules")
        rule_keys = {rule["rule_key"] for rule in rules_payload["rules"]}
        excluded_keys = {rule["rule_key"] for rule in rules_payload["excluded"]}
        assert "canon_hard" in rule_keys
        assert "new_style" in rule_keys
        assert "old_style" in excluded_keys

        state_payload = section_payload(pack, "current_state")
        assert state_payload[0]["name"] == "Hero"
        assert state_payload[0]["state"]["injury"] == "minor"

        foreshadowing_payload = section_payload(pack, "open_foreshadowing")
        foreshadowing_keys = {item["key"] for item in foreshadowing_payload}
        assert "visible_seed" in foreshadowing_keys
        assert "hidden_seed" not in foreshadowing_keys

        validation = await context.validate_context_pack(project_id=project_id, context_pack_id=pack["id"])
        assert validation["ok"] is False
        assert any(issue["type"] == "foreshadowing_overdue" for issue in validation["issues"])

        segment_pack = await context.prepare_segment_context(
            project_id=project_id,
            chapter_no=10,
            segment="ending",
            purpose="draft",
            focus=["Hero"],
            budget={"total_tokens": 20000},
            volume_no=1,
            scope_refs=["Hero"],
        )
        assert any(section["name"] == "segment_guidance" for section in segment_pack["sections"])
        print("phase2 context tools smoke ok")
    finally:
        await db.execute("DELETE FROM workspaces WHERE slug = $1", workspace_slug)
        await db.close()


asyncio.run(main())
PY
