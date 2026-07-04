#!/usr/bin/env python
import sys
sys.path.insert(0, '/app/src')
import asyncio
from novel_os_mcp.config import get_settings
from novel_os_mcp.db import Database
from novel_os_mcp.services import SyncService, CanonService, RulesService, MemoryService, PlotService, WorkspaceService

settings = get_settings()

async def main():
    db = Database(settings)
    await db.connect()

    canon = CanonService(db)
    rules = RulesService(db)
    memory = MemoryService(db)
    plot = PlotService(db)
    workspace = WorkspaceService(db)

    sync = SyncService(db, workspace, canon, rules, memory, plot)

    rows = await db.fetch("SELECT id::text, slug FROM projects LIMIT 1")
    if not rows:
        print("No projects found, creating test project...")
        await db.execute(
            "INSERT INTO workspaces (slug, name) VALUES ('test_ws', 'Test WS') ON CONFLICT DO NOTHING"
        )
        ws = await db.fetchrow("SELECT id FROM workspaces WHERE slug = 'test_ws'")
        await db.execute(
            "INSERT INTO projects (workspace_id, slug, title) VALUES ($1, 'test_proj', 'Test Project') ON CONFLICT DO NOTHING",
            ws["id"]
        )
        row = await db.fetchrow("SELECT id::text FROM projects WHERE slug = 'test_proj'")
        project_id = row["id"]
    else:
        project_id = rows[0]["id"]
        print(f"Using project: {rows[0]['slug']} ({project_id})")

    test_pack = {
        "version": 1,
        "canon_documents": [
            {
                "doc_type": "world",
                "key": "test_world_import",
                "title": "Test World Import",
                "content": "A test world for import verification.",
                "status": "active",
            }
        ],
        "rules": [
            {
                "rule_key": "test.import.rule",
                "rule_type": "style",
                "title": "Test Import Rule",
                "content": "Test rule content.",
                "severity": "warning",
                "status": "active",
            }
        ],
        "entities": [
            {
                "entity_type": "character",
                "name": "Test Import Character",
                "core_profile": "A test character.",
            }
        ],
        "plot_threads": [
            {
                "thread_key": "test_import_thread",
                "title": "Test Import Plot Thread",
                "thread_type": "main",
                "importance": "high",
                "status": "open",
            }
        ],
        "foreshadowing": [
            {
                "key": "test_import_foreshadow",
                "title": "Test Import Foreshadowing",
                "status": "planted",
                "importance": "medium",
                "layer": "visible",
            }
        ],
        "volumes": [
            {
                "volume_no": 99,
                "title": "Test Import Volume",
                "status": "planned",
                "start_chapter_no": 9901,
                "end_chapter_no": 9910,
            }
        ],
        "chapter_plans": [
            {
                "chapter_no": 9901,
                "plan": {"title": "Chapter 9901", "summary": "Import test plan."},
            }
        ],
    }

    result = await sync.import_initial_project_pack(
        project_id=project_id,
        username="admin",
        pack=test_pack,
    )

    print("Import result:", result)
    imported = result.get("imported", {})

    expected = {
        "canon_documents": 1,
        "rules": 1,
        "entities": 1,
        "plot_threads": 1,
        "foreshadowing": 1,
        "volumes": 1,
        "chapter_plans": 1,
    }

    all_ok = True
    for key, expected_count in expected.items():
        actual = imported.get(key, 0)
        status = "OK" if actual == expected_count else "FAIL"
        if status == "FAIL":
            all_ok = False
        print(f"  {key}: {actual} (expected {expected_count}) - {status}")

    await db.disconnect()

    if all_ok:
        print("\nAll tests PASSED!")
        sys.exit(0)
    else:
        print("\nSome tests FAILED!")
        sys.exit(1)

if __name__ == "__main__":
    asyncio.run(main())