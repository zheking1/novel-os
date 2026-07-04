#!/usr/bin/env sh
set -eu

cd /opt/novel-os

docker compose -f docker-compose.yml -f docker-compose.app.example.yml exec -T novel-os-mcp python - <<'PY'
import asyncio
import secrets

from novel_os_mcp.config import get_settings
from novel_os_mcp.db import Database
from novel_os_mcp.services import PlotService, WorkspaceService


async def main() -> None:
    suffix = secrets.token_hex(4)
    username = f"verify_foreshadowing_{suffix}"
    workspace_slug = f"verify-foreshadowing-ws-{suffix}"
    project_slug = f"verify-foreshadowing-project-{suffix}"

    db = Database(get_settings())
    await db.connect()
    workspace = WorkspaceService(db)
    plot = PlotService(db)
    try:
        await workspace.create_workspace(workspace_slug, "Verify Foreshadowing Workspace", username)
        project = await workspace.create_project(
            workspace_slug,
            project_slug,
            "Verify Foreshadowing Project",
            "temporary phase2 foreshadowing verification",
            username,
        )
        project_id = project["id"]

        await plot.upsert_foreshadowing(
            project_id=project_id,
            key="seed_a",
            title="Seed A",
            status="planted",
            importance="critical",
            must_payoff=True,
            payoff_deadline_chapter=5,
            overdue_policy="warn",
        )
        await plot.upsert_foreshadowing(
            project_id=project_id,
            key="seed_b",
            title="Seed B",
            status="planted",
            importance="medium",
        )
        linked = await plot.link_foreshadowing(
            project_id=project_id,
            key="seed_a",
            related_keys=["seed_b"],
            trigger_on_payoff_keys=["seed_b"],
        )
        overdue = await plot.check_overdue_foreshadowing(
            project_id=project_id,
            current_chapter_no=10,
            include_optional=False,
        )
        payoff = await plot.payoff_foreshadowing(
            project_id=project_id,
            key="seed_a",
            payoff_chapter_no=8,
            payoff_note="verified payoff",
            trigger_related=True,
        )
        updated = await plot.bulk_update_foreshadowing_status(
            project_id=project_id,
            keys=["seed_b"],
            status="archived",
            reason="verified archive",
        )

        assert linked["related_foreshadowing_ids"] == ["seed_b"]
        assert linked["trigger_on_payoff_ids"] == ["seed_b"]
        assert len(overdue) == 1
        assert overdue[0]["key"] == "seed_a"
        assert payoff["status"] == "paid_off"
        assert len(payoff["triggered"]) == 1
        assert payoff["triggered"][0]["key"] == "seed_b"
        assert len(updated) == 1
        assert updated[0]["status"] == "archived"
        print("phase2 foreshadowing tools smoke ok")
    finally:
        await db.execute("DELETE FROM workspaces WHERE slug = $1", workspace_slug)
        await db.close()


asyncio.run(main())
PY
