import hashlib
import logging
import secrets
from datetime import datetime
from typing import Any

from ..db import Database
from ..utils import json_dumps, row_to_dict, rows_to_dicts, ensure_json_value

logger = logging.getLogger("novel_os_mcp.services.workspace")


class WorkspaceService:
    def __init__(self, db: Database):
        self._db = db

    async def ensure_dev_user(self, username: str, workspace_slug: str) -> None:
        async with self._db.acquire() as conn:
            async with conn.transaction():
                user = await conn.fetchrow(
                    """
                    INSERT INTO users (username, display_name, status)
                    VALUES ($1, $1, 'active')
                    ON CONFLICT (username) DO UPDATE SET updated_at = now()
                    RETURNING id
                    """,
                    username,
                )
                workspace = await conn.fetchrow(
                    """
                    INSERT INTO workspaces (slug, name, owner_user_id)
                    VALUES ($1, $1, $2)
                    ON CONFLICT (slug) DO UPDATE SET updated_at = now()
                    RETURNING id
                    """,
                    workspace_slug,
                    user["id"],
                )
                await conn.execute(
                    """
                    INSERT INTO workspace_members (workspace_id, user_id, role)
                    VALUES ($1, $2, 'owner')
                    ON CONFLICT (workspace_id, user_id) DO UPDATE SET role = EXCLUDED.role
                    """,
                    workspace["id"],
                    user["id"],
                )

    async def create_user(
        self,
        username: str,
        display_name: str | None = None,
        email: str | None = None,
        status: str = "active",
        password_hash: str | None = None,
    ) -> dict[str, Any]:
        row = await self._db.fetchrow(
            """
            INSERT INTO users (username, nickname, status, password_hash)
            VALUES ($1, $2, $3, $4)
            ON CONFLICT (username)
            DO UPDATE SET nickname = COALESCE(EXCLUDED.nickname, users.nickname),
                          status = EXCLUDED.status,
                          password_hash = COALESCE(EXCLUDED.password_hash, users.password_hash),
                          updated_at = now()
            RETURNING id::text, username, nickname as display_name, status, created_at, updated_at
            """,
            username,
            display_name or username,
            status,
            password_hash,
        )
        return row_to_dict(row)

    async def ensure_user_exists(self, username: str) -> None:
        """Ensure user exists in database. Create with default values if not exists."""
        # Default password hash for '123456' using bcrypt
        default_password_hash = '$2b$10$92IXUNpkjO0rOQ5byMi.Ye4oKoEa3Ro9llC/.og/at2.uheWG/igi'
        await self._db.execute(
            """
            INSERT INTO users (username, nickname, status, password_hash)
            VALUES ($1, $1, 'active', $2)
            ON CONFLICT (username) DO NOTHING
            """,
            username,
            default_password_hash,
        )

    async def list_users(self, status: str | None = None, limit: int = 100) -> list[dict[str, Any]]:
        rows = await self._db.fetch(
            """
            SELECT id::text, username, nickname as display_name, status, created_at, updated_at
            FROM users
            WHERE ($1::text IS NULL OR status = $1)
            ORDER BY username
            LIMIT $2
            """,
            status,
            limit,
        )
        return rows_to_dicts(rows)

    async def create_workspace(self, slug: str, name: str, owner_username: str) -> dict[str, Any]:
        async with self._db.acquire() as conn:
            async with conn.transaction():
                user = await conn.fetchrow("SELECT id FROM users WHERE username = $1", owner_username)
                if user is None:
                    user = await conn.fetchrow(
                        """
                        INSERT INTO users (username, display_name, status)
                        VALUES ($1, $1, 'active')
                        RETURNING id
                        """,
                        owner_username,
                    )
                row = await conn.fetchrow(
                    """
                    INSERT INTO workspaces (slug, name, owner_user_id)
                    VALUES ($1, $2, $3)
                    ON CONFLICT (slug) DO UPDATE SET name = EXCLUDED.name, updated_at = now()
                    RETURNING id::text, slug, name, created_at, updated_at
                    """,
                    slug,
                    name,
                    user["id"],
                )
                await conn.execute(
                    """
                    INSERT INTO workspace_members (workspace_id, user_id, role)
                    VALUES ($1, $2, 'owner')
                    ON CONFLICT (workspace_id, user_id) DO UPDATE SET role = 'owner'
                    """,
                    row["id"],
                    user["id"],
                )
        return row_to_dict(row)

    async def list_workspaces(self, username: str | None = None) -> list[dict[str, Any]]:
        rows = await self._db.fetch(
            """
            SELECT w.id::text, w.slug, w.name, w.settings, w.created_at, w.updated_at,
                   wm.role AS member_role
            FROM workspaces w
            LEFT JOIN workspace_members wm ON wm.workspace_id = w.id
            LEFT JOIN users u ON u.id = wm.user_id
            WHERE ($1::text IS NULL OR u.username = $1)
            ORDER BY w.slug
            """,
            username,
        )
        return rows_to_dicts(rows)

    async def add_workspace_member(self, workspace_slug: str, username: str, role: str = "reader") -> dict[str, Any]:
        if role not in {"owner", "writer", "reader"}:
            raise ValueError("role must be owner, writer, or reader")
        async with self._db.acquire() as conn:
            async with conn.transaction():
                user = await conn.fetchrow("SELECT id FROM users WHERE username = $1", username)
                if user is None:
                    raise ValueError(f"User not found: {username}")
                workspace = await conn.fetchrow("SELECT id FROM workspaces WHERE slug = $1", workspace_slug)
                if workspace is None:
                    raise ValueError(f"Workspace not found: {workspace_slug}")
                row = await conn.fetchrow(
                    """
                    INSERT INTO workspace_members (workspace_id, user_id, role)
                    VALUES ($1, $2, $3)
                    ON CONFLICT (workspace_id, user_id)
                    DO UPDATE SET role = EXCLUDED.role
                    RETURNING workspace_id::text, user_id::text, role, created_at
                    """,
                    workspace["id"],
                    user["id"],
                    role,
                )
        return row_to_dict(row)

    async def create_project(
        self,
        workspace_slug: str,
        project_slug: str,
        title: str,
        description: str | None,
        owner_username: str,
    ) -> dict[str, Any]:
        async with self._db.acquire() as conn:
            async with conn.transaction():
                workspace = await conn.fetchrow("SELECT id FROM workspaces WHERE slug = $1", workspace_slug)
                if workspace is None:
                    raise ValueError(f"Workspace not found: {workspace_slug}")
                user = await conn.fetchrow("SELECT id FROM users WHERE username = $1", owner_username)
                if user is None:
                    raise ValueError(f"User not found: {owner_username}")
                row = await conn.fetchrow(
                    """
                    INSERT INTO projects (workspace_id, slug, title, description, status)
                    VALUES ($1, $2, $3, $4, 'active')
                    ON CONFLICT (workspace_id, slug)
                    DO UPDATE SET title = EXCLUDED.title, description = EXCLUDED.description, updated_at = now()
                    RETURNING id::text, slug, title, description, status, created_at, updated_at
                    """,
                    workspace["id"],
                    project_slug,
                    title,
                    description,
                )
                await conn.execute(
                    """
                    INSERT INTO project_members (project_id, user_id, role)
                    VALUES ($1, $2, 'owner')
                    ON CONFLICT (project_id, user_id) DO UPDATE SET role = 'owner'
                    """,
                    row["id"],
                    user["id"],
                )
        return row_to_dict(row)

    async def list_projects(self, workspace_slug: str, username: str | None = None) -> list[dict[str, Any]]:
        rows = await self._db.fetch(
            """
            SELECT p.id::text, p.slug, p.title, p.description, p.status, p.settings,
                   p.created_at, p.updated_at, pm.role AS member_role
            FROM projects p
            JOIN workspaces w ON w.id = p.workspace_id
            LEFT JOIN project_members pm ON pm.project_id = p.id
            LEFT JOIN users u ON u.id = pm.user_id
            WHERE w.slug = $1
              AND ($2::text IS NULL OR u.username = $2)
            ORDER BY p.slug
            """,
            workspace_slug,
            username,
        )
        return rows_to_dicts(rows)

    async def list_project_members(self, workspace_slug: str, project_slug: str) -> list[dict[str, Any]]:
        rows = await self._db.fetch(
            """
            SELECT u.id::text AS user_id, u.username, u.display_name, u.email, u.status,
                   pm.role, pm.created_at
            FROM project_members pm
            JOIN users u ON u.id = pm.user_id
            JOIN projects p ON p.id = pm.project_id
            JOIN workspaces w ON w.id = p.workspace_id
            WHERE w.slug = $1 AND p.slug = $2
            ORDER BY pm.role, u.username
            """,
            workspace_slug,
            project_slug,
        )
        return rows_to_dicts(rows)

    async def add_project_member(
        self,
        workspace_slug: str,
        project_slug: str,
        username: str,
        role: str = "writer",
    ) -> dict[str, Any]:
        if role not in {"owner", "writer", "reader"}:
            raise ValueError("role must be owner, writer, or reader")
        async with self._db.acquire() as conn:
            async with conn.transaction():
                user = await conn.fetchrow("SELECT id FROM users WHERE username = $1", username)
                if user is None:
                    raise ValueError(f"User not found: {username}")
                project = await conn.fetchrow(
                    """
                    SELECT p.id, p.workspace_id
                    FROM projects p
                    JOIN workspaces w ON w.id = p.workspace_id
                    WHERE w.slug = $1 AND p.slug = $2
                    """,
                    workspace_slug,
                    project_slug,
                )
                if project is None:
                    raise ValueError(f"Project not found: {workspace_slug}/{project_slug}")
                await conn.execute(
                    """
                    INSERT INTO workspace_members (workspace_id, user_id, role)
                    VALUES ($1, $2, 'reader')
                    ON CONFLICT (workspace_id, user_id) DO NOTHING
                    """,
                    project["workspace_id"],
                    user["id"],
                )
                row = await conn.fetchrow(
                    """
                    INSERT INTO project_members (project_id, user_id, role)
                    VALUES ($1, $2, $3)
                    ON CONFLICT (project_id, user_id)
                    DO UPDATE SET role = EXCLUDED.role
                    RETURNING project_id::text, user_id::text, role, created_at
                    """,
                    project["id"],
                    user["id"],
                    role,
                )
        return row_to_dict(row)

    async def register_local_binding(
        self,
        project_id: str,
        username: str,
        client_id: str,
        local_root_hint: str | None,
        manifest: dict[str, Any],
    ) -> dict[str, Any]:
        async with self._db.acquire() as conn:
            user = await conn.fetchrow("SELECT id FROM users WHERE username = $1", username)
            if user is None:
                raise ValueError(f"User not found: {username}")
            row = await conn.fetchrow(
                """
                INSERT INTO local_project_bindings (project_id, user_id, client_id, local_root_hint, manifest, last_sync_at)
                VALUES ($1, $2, $3, $4, $5::jsonb, now())
                ON CONFLICT (project_id, user_id, client_id)
                DO UPDATE SET local_root_hint = EXCLUDED.local_root_hint,
                              manifest = EXCLUDED.manifest,
                              last_sync_at = now(),
                              updated_at = now()
                RETURNING id::text, client_id, local_root_hint, manifest, last_sync_at, created_at, updated_at
                """,
                project_id,
                user["id"],
                client_id,
                local_root_hint,
                json_dumps(manifest),
            )
        return row_to_dict(row)

    async def create_api_token(
        self,
        username: str,
        name: str,
        scopes: list[str],
        workspace_slug: str | None = None,
        project_slug: str | None = None,
        expires_at: datetime | str | None = None,
    ) -> dict[str, Any]:
        token = "nos_" + secrets.token_urlsafe(32)
        token_hash = hashlib.sha256(token.encode("utf-8")).hexdigest()
        async with self._db.acquire() as conn:
            async with conn.transaction():
                user = await conn.fetchrow("SELECT id FROM users WHERE username = $1", username)
                if user is None:
                    raise ValueError(f"User not found: {username}")
                workspace_id = None
                project_id = None
                if workspace_slug:
                    workspace = await conn.fetchrow("SELECT id FROM workspaces WHERE slug = $1", workspace_slug)
                    if workspace is None:
                        raise ValueError(f"Workspace not found: {workspace_slug}")
                    workspace_id = workspace["id"]
                    await conn.execute(
                        """
                        INSERT INTO workspace_members (workspace_id, user_id, role)
                        VALUES ($1, $2, 'writer')
                        ON CONFLICT (workspace_id, user_id) DO NOTHING
                        """,
                        workspace_id,
                        user["id"],
                    )
                if project_slug:
                    if not workspace_slug:
                        raise ValueError("project-scoped tokens require workspace")
                    project = await conn.fetchrow(
                        "SELECT id FROM projects WHERE workspace_id = $1 AND slug = $2",
                        workspace_id,
                        project_slug,
                    )
                    if project is None:
                        raise ValueError(f"Project not found: {workspace_slug}/{project_slug}")
                    project_id = project["id"]
                    await conn.execute(
                        """
                        INSERT INTO project_members (project_id, user_id, role)
                        VALUES ($1, $2, 'writer')
                        ON CONFLICT (project_id, user_id) DO NOTHING
                        """,
                        project_id,
                        user["id"],
                    )
                row = await conn.fetchrow(
                    """
                    INSERT INTO api_tokens (user_id, workspace_id, project_id, name, token_hash, scopes, expires_at)
                    VALUES ($1, $2, $3, $4, $5, $6, $7::timestamptz)
                    RETURNING id::text, name, scopes, expires_at, created_at
                    """,
                    user["id"],
                    workspace_id,
                    project_id,
                    name,
                    token_hash,
                    scopes,
                    expires_at,
                )
        result = row_to_dict(row)
        result["token"] = token
        result["workspace"] = workspace_slug
        result["project"] = project_slug
        return result

    async def list_api_tokens(
        self,
        username: str | None = None,
        workspace_slug: str | None = None,
        project_slug: str | None = None,
        include_revoked: bool = False,
    ) -> list[dict[str, Any]]:
        rows = await self._db.fetch(
            """
            SELECT t.id::text, u.username, w.slug AS workspace, p.slug AS project,
                   t.name, t.scopes, t.expires_at, t.last_used_at, t.created_at, t.revoked_at
            FROM api_tokens t
            JOIN users u ON u.id = t.user_id
            LEFT JOIN workspaces w ON w.id = t.workspace_id
            LEFT JOIN projects p ON p.id = t.project_id
            WHERE ($1::text IS NULL OR u.username = $1)
              AND ($2::text IS NULL OR w.slug = $2)
              AND ($3::text IS NULL OR p.slug = $3)
              AND ($4::boolean OR t.revoked_at IS NULL)
            ORDER BY t.created_at DESC
            """,
            username,
            workspace_slug,
            project_slug,
            include_revoked,
        )
        return rows_to_dicts(rows)

    async def revoke_api_token(self, token_id: str) -> dict[str, Any]:
        row = await self._db.fetchrow(
            """
            UPDATE api_tokens
            SET revoked_at = COALESCE(revoked_at, now())
            WHERE id = $1
            RETURNING id::text, name, scopes, revoked_at
            """,
            token_id,
        )
        if row is None:
            raise ValueError(f"API token not found: {token_id}")
        return row_to_dict(row)
