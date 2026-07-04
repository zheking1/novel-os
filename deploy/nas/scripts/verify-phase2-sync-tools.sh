#!/usr/bin/env sh
set -eu

cd /opt/novel-os

docker compose -f docker-compose.yml -f docker-compose.app.example.yml exec -T novel-os-mcp python - <<'PY'
import asyncio
import secrets

from novel_os_mcp.config import get_settings
from novel_os_mcp.db import Database
from novel_os_mcp.services import (
    CanonService,
    MemoryService,
    PlotService,
    RulesService,
    SyncService,
    WorkspaceService,
)


async def main() -> None:
    suffix = secrets.token_hex(4)
    username = f"verify_sync_{suffix}"
    workspace_slug = f"verify-sync-ws-{suffix}"
    project_slug = f"verify-sync-project-{suffix}"

    db = Database(get_settings())
    await db.connect()
    workspace = WorkspaceService(db)
    canon = CanonService(db)
    rules = RulesService(db)
    memory = MemoryService(db)
    plot = PlotService(db)
    sync = SyncService(db, workspace, canon, rules, memory, plot)
    try:
        await workspace.create_workspace(workspace_slug, "Verify Sync Workspace", username)
        project = await workspace.create_project(
            workspace_slug,
            project_slug,
            "Verify Sync Project",
            "temporary phase2 sync verification",
            username,
        )
        project_id = project["id"]

        manifest = {
            "version": 1,
            "client_id": "verify-local",
            "local_root_hint": "/novels/verify",
            "files": [
                {
                    "kind": "chapter",
                    "chapter_no": 1,
                    "volume_no": 1,
                    "title": "Opening",
                    "path_hint": "chapters/001.md",
                    "sha256": "hash-chapter-1-a",
                    "word_count": 3200,
                }
            ],
        }
        imported_manifest = await sync.import_local_manifest(
            project_id=project_id,
            username=username,
            client_id="verify-local",
            manifest=manifest,
            local_root_hint="/novels/verify",
        )
        assert imported_manifest["binding"]["client_id"] == "verify-local"
        assert imported_manifest["conflict_count"] == 0

        initial_pack = {
            "local_manifest": manifest,
            "canon_documents": [
                {
                    "doc_type": "world",
                    "key": "core",
                    "title": "Core World",
                    "content": "Qi ranks advance one stage at a time.",
                }
            ],
            "rules": [
                {
                    "rule_key": "canon_rank_order",
                    "rule_type": "canon",
                    "title": "Rank Order",
                    "content": "Do not skip major realms.",
                    "severity": "critical",
                    "priority": 10,
                }
            ],
            "entities": [
                {
                    "entity_type": "character",
                    "name": "Hero",
                    "aliases": ["MC"],
                    "profile": {"role": "protagonist"},
                    "importance": "critical",
                }
            ],
            "state_snapshots": [
                {
                    "entity_type": "character",
                    "name": "Hero",
                    "state": {"realm": "Qi Gathering"},
                    "chapter_no": 1,
                    "source_type": "import",
                }
            ],
            "foreshadowing": [
                {
                    "key": "jade_token",
                    "title": "Jade Token",
                    "importance": "high",
                    "payload": {"hint": "legacy key"},
                }
            ],
            "volumes": [
                {
                    "volume_no": 1,
                    "title": "Awakening",
                    "status": "active",
                    "start_chapter_no": 1,
                }
            ],
            "plot_threads": [
                {
                    "key": "main_path",
                    "title": "Main Path",
                    "thread_type": "main",
                    "importance": "critical",
                    "volume_no": 1,
                }
            ],
        }
        imported_pack = await sync.import_initial_project_pack(project_id=project_id, username=username, pack=initial_pack)
        assert imported_pack["imported"]["canon_documents"] == 1
        assert imported_pack["imported"]["rules"] == 1
        assert imported_pack["imported"]["entities"] == 1
        assert imported_pack["imported"]["state_snapshots"] == 1
        assert imported_pack["imported"]["foreshadowing"] == 1
        assert imported_pack["imported"]["volumes"] == 1
        assert imported_pack["imported"]["plot_threads"] == 1

        first_hash_submit = await sync.submit_file_hashes(
            project_id=project_id,
            username=username,
            client_id="verify-local",
            files=manifest["files"],
            local_root_hint="/novels/verify",
        )
        assert first_hash_submit["chapters_upserted"] == 1
        assert first_hash_submit["conflict_count"] == 0

        changed_file = {
            "kind": "chapter",
            "chapter_no": 1,
            "volume_no": 1,
            "title": "Opening Revised",
            "path_hint": "chapters/001.md",
            "sha256": "hash-chapter-1-b",
            "word_count": 3400,
        }
        conflict_submit = await sync.submit_file_hashes(
            project_id=project_id,
            username=username,
            client_id="verify-local",
            files=[changed_file],
            local_root_hint="/novels/verify",
        )
        assert conflict_submit["chapters_upserted"] == 0
        assert conflict_submit["conflict_count"] == 1
        conflict = conflict_submit["conflicts"][0]
        assert conflict["target_type"] == "chapter"
        assert conflict["local_hash"] == "hash-chapter-1-b"
        assert conflict["mcp_hash"] == "hash-chapter-1-a"

        resolved = await sync.resolve_conflict(
            project_id=project_id,
            username=username,
            action="accept_local",
            conflict=conflict,
            reason="verify accepts local file hash",
        )
        assert resolved["resolved"] is True

        conflicts_after_resolve = await sync.list_conflicts(
            project_id=project_id,
            client_id="verify-local",
            manifest={"files": [changed_file]},
        )
        assert conflicts_after_resolve == []

        exported = await sync.export_project_pack(project_id=project_id, include_bindings=True)
        assert exported["version"] == 1
        assert len(exported["canon_documents"]) == 1
        assert len(exported["rules"]) == 1
        assert len(exported["entities"]) == 1
        assert len(exported["state_snapshots"]) >= 1
        assert len(exported["foreshadowing"]) == 1
        assert len(exported["volumes"]) == 1
        assert len(exported["plot_threads"]) == 1
        assert len(exported["local_bindings"]) == 1

        print("phase2 sync tools smoke ok")
    finally:
        await db.execute("DELETE FROM workspaces WHERE slug = $1", workspace_slug)
        await db.close()


asyncio.run(main())
PY
