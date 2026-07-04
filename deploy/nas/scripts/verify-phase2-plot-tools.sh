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
    username = f"verify_plot_{suffix}"
    workspace_slug = f"verify-plot-ws-{suffix}"
    project_slug = f"verify-plot-project-{suffix}"

    db = Database(get_settings())
    await db.connect()
    workspace = WorkspaceService(db)
    plot = PlotService(db)
    try:
        await workspace.create_workspace(workspace_slug, "Verify Plot Workspace", username)
        project = await workspace.create_project(
            workspace_slug,
            project_slug,
            "Verify Plot Project",
            "temporary phase2 plot verification",
            username,
        )
        project_id = project["id"]

        volume = await plot.upsert_volume(
            project_id=project_id,
            volume_no=1,
            title="Opening Volume",
            status="active",
            start_chapter_no=1,
            end_chapter_no=50,
            goals=[{"type": "main", "target": "open the central conflict"}],
        )
        thread = await plot.upsert_plot_thread(
            project_id=project_id,
            key="main_conflict",
            title="Main Conflict",
            thread_type="main",
            status="open",
            importance="critical",
            volume_no=1,
            start_chapter_no=1,
            last_advanced_chapter_no=5,
            stalled_after_chapters=5,
        )
        advanced = await plot.advance_plot_thread(
            project_id=project_id,
            key="main_conflict",
            chapter_no=8,
            progress_note="verified advancement",
            expected_next_chapter_no=12,
        )
        volumes = await plot.list_volumes(project_id=project_id, current_chapter_no=8)
        threads = await plot.list_plot_threads(project_id=project_id, current_chapter_no=14)
        stalled = await plot.check_stalled_threads(project_id=project_id, current_chapter_no=14)

        assert volume["volume_no"] == 1
        assert thread["key"] == "main_conflict"
        assert advanced["last_advanced_chapter_no"] == 8
        assert len(volumes) == 1
        assert volumes[0]["contains_current_chapter"] is True
        assert len(threads) == 1
        assert threads[0]["is_stalled"] is True
        assert len(stalled) == 1
        print("phase2 plot tools smoke ok")
    finally:
        await db.execute("DELETE FROM workspaces WHERE slug = $1", workspace_slug)
        await db.close()


asyncio.run(main())
PY
