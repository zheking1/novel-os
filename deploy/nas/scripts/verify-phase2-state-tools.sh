#!/usr/bin/env sh
set -eu

cd /opt/novel-os

docker compose -f docker-compose.yml -f docker-compose.app.example.yml exec -T novel-os-mcp python - <<'PY'
import asyncio
import secrets
import uuid

from novel_os_mcp.config import get_settings
from novel_os_mcp.db import Database
from novel_os_mcp.services import MemoryService


async def create_temp_project(db: Database) -> str:
    suffix = secrets.token_hex(4)
    async with db.acquire() as conn:
        columns = await conn.fetch(
            """
            SELECT column_name, is_nullable, column_default
            FROM information_schema.columns
            WHERE table_schema = 'public' AND table_name = 'projects'
            """
        )
        project_columns = {row["column_name"]: row for row in columns}
        workspace_id = None
        if (
            "workspace_id" in project_columns
            and project_columns["workspace_id"]["is_nullable"] == "NO"
            and project_columns["workspace_id"]["column_default"] is None
        ):
            user = await conn.fetchrow(
                """
                INSERT INTO users (username, display_name, status)
                VALUES ($1, $2, 'active')
                RETURNING id
                """,
                f"verify_state_{suffix}",
                "Verify State",
            )
            workspace = await conn.fetchrow(
                """
                INSERT INTO workspaces (slug, name, owner_user_id)
                VALUES ($1, $2, $3)
                RETURNING id
                """,
                f"verify-state-{suffix}",
                "Verify State",
                user["id"],
            )
            workspace_id = workspace["id"]

        fields = []
        values = []
        if "id" in project_columns and project_columns["id"]["column_default"] is None:
            fields.append("id")
            values.append(uuid.uuid4())
        if "workspace_id" in project_columns and workspace_id is not None:
            fields.append("workspace_id")
            values.append(workspace_id)
        if "slug" in project_columns:
            fields.append("slug")
            values.append(f"verify-state-{suffix}")
        if "title" in project_columns:
            fields.append("title")
            values.append("Verify State Project")
        if "name" in project_columns:
            fields.append("name")
            values.append("Verify State Project")
        if "description" in project_columns:
            fields.append("description")
            values.append("temporary phase2 state tool verification")
        if (
            "status" in project_columns
            and project_columns["status"]["is_nullable"] == "NO"
            and project_columns["status"]["column_default"] is None
        ):
            fields.append("status")
            values.append("active")
        placeholders = ", ".join(f"${idx}" for idx in range(1, len(values) + 1))
        row = await conn.fetchrow(
            f"INSERT INTO projects ({', '.join(fields)}) VALUES ({placeholders}) RETURNING id",
            *values,
        )
        return str(row["id"])


async def main() -> None:
    db = Database(get_settings())
    await db.connect()
    memory = MemoryService(db)
    project_id = await create_temp_project(db)
    try:
        entity = await memory.upsert_entity(
            project_id=project_id,
            entity_type="character",
            name="Verify Hero",
            aliases=["VH"],
            profile={"baseline": "state tool smoke test"},
            tags=["verify"],
        )
        snapshot = await memory.upsert_snapshot(
            project_id=project_id,
            entity_id=entity["id"],
            state={"realm": "foundation", "injury": "temporary"},
            duration_type="temporary",
            effective_chapter_no=1,
            expire_chapter_no=3,
        )
        target = await memory.upsert_entity(
            project_id=project_id,
            entity_type="faction",
            name="Verify Sect",
        )
        relationship = await memory.upsert_relationship(
            project_id=project_id,
            relation_type="member_of",
            source_entity_id=entity["id"],
            target_entity_id=target["id"],
            attitude="loyal",
            intensity=0.8,
        )
        entities = await memory.list_entities(project_id=project_id, tags=["verify"])
        snapshots = await memory.list_snapshots(project_id=project_id, entity_id=entity["id"], current_only=True)
        relationships = await memory.list_relationships(project_id=project_id, entity_id=entity["id"])
        assert entity["name"] == "Verify Hero"
        assert snapshot["is_current"] is True
        assert relationship["relation_type"] == "member_of"
        assert len(entities) == 1
        assert len(snapshots) == 1
        assert len(relationships) == 1
        print("phase2 state tools smoke ok")
    finally:
        await db.execute("DELETE FROM projects WHERE id = $1", project_id)
        await db.close()


asyncio.run(main())
PY
