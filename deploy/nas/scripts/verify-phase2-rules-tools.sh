#!/usr/bin/env sh
set -eu

cd /opt/novel-os

docker compose -f docker-compose.yml -f docker-compose.app.example.yml exec -T novel-os-mcp python - <<'PY'
import asyncio
import secrets

from novel_os_mcp.config import get_settings
from novel_os_mcp.db import Database
from novel_os_mcp.services import RulesService, WorkspaceService


async def main() -> None:
    suffix = secrets.token_hex(4)
    username = f"verify_rules_{suffix}"
    workspace_slug = f"verify-rules-ws-{suffix}"
    project_slug = f"verify-rules-project-{suffix}"

    db = Database(get_settings())
    await db.connect()
    workspace = WorkspaceService(db)
    rules = RulesService(db)
    try:
        await workspace.create_workspace(workspace_slug, "Verify Rules Workspace", username)
        project = await workspace.create_project(
            workspace_slug,
            project_slug,
            "Verify Rules Project",
            "temporary phase2 rules verification",
            username,
        )
        project_id = project["id"]

        await rules.upsert_rule(
            project_id=project_id,
            rule_key="canon_hard",
            rule_type="canon",
            title="Hard Canon",
            content="Hard canon must always load.",
            severity="critical",
            priority=10,
        )
        await rules.upsert_rule(
            project_id=project_id,
            rule_key="hero_voice",
            rule_type="character",
            title="Hero Voice",
            content="Hero speaks with restrained confidence.",
            scope_type="character",
            scope_ref="Hero",
            priority=20,
        )
        await rules.upsert_rule(
            project_id=project_id,
            rule_key="volume_secret_lock",
            rule_type="reveal_lock",
            title="Volume Secret Lock",
            content="Do not reveal the hidden mentor in volume 2.",
            scope_type="volume",
            scope_ref="2",
            severity="error",
            priority=15,
            effective_volume_no=2,
            expire_volume_no=3,
            is_temporary=True,
            metadata={"keywords": ["hidden mentor"]},
        )
        await rules.upsert_rule(
            project_id=project_id,
            rule_key="style_a",
            rule_type="style",
            title="Style A",
            content="Use shorter action beats.",
            priority=50,
        )
        await rules.upsert_rule(
            project_id=project_id,
            rule_key="style_b",
            rule_type="style",
            title="Style B",
            content="Use longer action beats.",
            priority=50,
        )
        await rules.upsert_rule(
            project_id=project_id,
            rule_key="old_style",
            rule_type="style",
            title="Old Style",
            content="Old style rule.",
            priority=90,
        )
        await rules.upsert_rule(
            project_id=project_id,
            rule_key="new_style",
            rule_type="style",
            title="New Style",
            content="New style rule.",
            priority=40,
            supersedes_rule_ids=["old_style"],
        )

        effective = await rules.list_effective_rules(
            project_id=project_id,
            volume_no=2,
            scope_refs=["Hero"],
        )
        effective_keys = {rule["rule_key"] for rule in effective["rules"]}
        excluded_keys = {rule["rule_key"] for rule in effective["excluded"]}
        assert "canon_hard" in effective_keys
        assert "hero_voice" in effective_keys
        assert "volume_secret_lock" in effective_keys
        assert "new_style" in effective_keys
        assert "old_style" not in effective_keys
        assert "old_style" in excluded_keys

        conflict = await rules.check_conflicts(
            project_id=project_id,
            volume_no=2,
            scope_refs=["Hero"],
            text="The hidden mentor steps out too early.",
        )
        conflict_types = {item["type"] for item in conflict["conflicts"]}
        assert "same_scope_same_priority" in conflict_types
        assert "supersedes_active_rule" in conflict_types
        assert conflict["text_match_count"] == 1

        reprioritized = await rules.resolve_conflict(
            project_id=project_id,
            action="set_priority",
            source_rule_key="style_b",
            priority=55,
            reason="verify priority resolution",
        )
        assert reprioritized["updated_count"] == 1
        assert reprioritized["updated"][0]["priority"] == 55

        superseded = await rules.resolve_conflict(
            project_id=project_id,
            action="supersede",
            source_rule_key="new_style",
            target_rule_keys=["old_style"],
            reason="verify supersede resolution",
        )
        assert superseded["updated_count"] == 1
        assert superseded["updated"][0]["status"] == "superseded"

        toggled = await rules.bulk_toggle_rules(
            project_id=project_id,
            rule_keys=["style_a"],
            status="disabled",
            reason="verify bulk toggle",
        )
        assert len(toggled) == 1
        assert toggled[0]["status"] == "disabled"

        after_toggle = await rules.list_effective_rules(
            project_id=project_id,
            volume_no=2,
            scope_refs=["Hero"],
        )
        after_keys = {rule["rule_key"] for rule in after_toggle["rules"]}
        assert "style_a" not in after_keys
        print("phase2 rules tools smoke ok")
    finally:
        await db.execute("DELETE FROM workspaces WHERE slug = $1", workspace_slug)
        await db.close()


asyncio.run(main())
PY
