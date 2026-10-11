from dataclasses import dataclass
from hashlib import sha256

from fastmcp.server.dependencies import get_http_headers

from .config import Settings
from .db import Database


@dataclass(frozen=True)
class Principal:
    username: str
    workspace: str | None
    project_id: str | None
    scopes: set[str]

    def require(self, scope: str) -> None:
        if "admin" not in self.scopes and scope not in self.scopes:
            raise PermissionError(f"Missing required scope: {scope}")


class AuthService:
    def __init__(self, settings: Settings, db: Database):
        self._settings = settings
        self._db = db

    async def current_principal(self) -> Principal:
        mode = self._settings.auth_mode.lower().strip()
        if mode == "dev":
            return Principal(
                username=self._settings.dev_user,
                workspace=self._settings.dev_workspace,
                project_id=None,
                scopes=self._settings.dev_scope_set,
            )
        if mode == "token":
            return await self._token_principal()
        raise PermissionError(f"Unsupported NOVEL_OS_AUTH_MODE: {self._settings.auth_mode}")

    async def _token_principal(self) -> Principal:
        token = self._bearer_token()
        token_hash = sha256(token.encode("utf-8")).hexdigest()
        row = await self._db.fetchrow(
            """
            SELECT
              t.id AS token_id,
              t.scopes,
              t.project_id::text AS project_id,
              u.username,
              u.status AS user_status,
              w.slug AS workspace_slug
            FROM api_tokens t
            JOIN users u ON u.id = t.user_id
            LEFT JOIN workspaces w ON w.id = t.workspace_id
            WHERE t.token_hash = $1
              AND t.revoked_at IS NULL
              AND (t.expires_at IS NULL OR t.expires_at > now())
            """,
            token_hash,
        )
        if row is None or row["user_status"] != "active":
            raise PermissionError("API Key 无效或已过期。请在 Web UI「系统管理 → API Key 管理」中检查或重新创建")
        await self._db.execute("UPDATE api_tokens SET last_used_at = now() WHERE id = $1", row["token_id"])
        return Principal(
            username=row["username"],
            workspace=row["workspace_slug"],
            project_id=row["project_id"],
            scopes=set(row["scopes"] or []),
        )

    @staticmethod
    def _bearer_token() -> str:
        headers = get_http_headers(include={"apikey"})
        # Check apiKey header (Trae MCP client compatible)
        token = headers.get("apikey") or headers.get("apiKey") or headers.get("ApiKey") or ""
        if token:
            return token
        raise PermissionError("缺少 apiKey 请求头。请在 MCP 客户端配置中添加 headers.apiKey 字段，值为你在 Web UI「API Key 管理」中创建的 Key")

    @staticmethod
    def _role_allows(role: str | None, access: str) -> bool:
        if access == "read":
            return role in {"owner", "writer", "reader"}
        if access == "write":
            return role in {"owner", "writer"}
        return False

    async def require_workspace_access(self, principal: Principal, workspace_slug: str, access: str = "read") -> None:
        if "admin" in principal.scopes:
            return
        if principal.workspace is not None and principal.workspace != workspace_slug:
            raise PermissionError(f"Token is scoped to workspace: {principal.workspace}")
        row = await self._db.fetchrow(
            """
            SELECT wm.role
            FROM workspace_members wm
            JOIN workspaces w ON w.id = wm.workspace_id
            JOIN users u ON u.id = wm.user_id
            WHERE w.slug = $1
              AND u.username = $2
              AND u.status = 'active'
            """,
            workspace_slug,
            principal.username,
        )
        if row is None or not self._role_allows(row["role"], access):
            workspaces = await self._db.fetch(
                "SELECT w.slug FROM workspace_members wm JOIN workspaces w ON w.id = wm.workspace_id WHERE wm.user_id = (SELECT id FROM users WHERE username = $1)",
                principal.username,
            )
            available = [w["slug"] for w in workspaces]
            hint = f"你有权限的工作区: {', '.join(available)}" if available else "你没有加入任何工作区，请先通过 Web UI 登录创建个人工作区"
            raise PermissionError(f"无权限访问工作区 '{workspace_slug}'。{hint}")

    async def require_project_access(self, principal: Principal, project_id: str, access: str = "read") -> None:
        if "admin" in principal.scopes:
            return
        if principal.project_id is not None and principal.project_id != project_id:
            raise PermissionError("Token is scoped to a different project")
        row = await self._db.fetchrow(
            """
            SELECT pm.role
            FROM project_members pm
            JOIN users u ON u.id = pm.user_id
            WHERE pm.project_id = $1
              AND u.username = $2
              AND u.status = 'active'
            """,
            project_id,
            principal.username,
        )
        if row is None or not self._role_allows(row["role"], access):
            raise PermissionError("无权限访问该项目。你可能不是该项目成员，请让项目 owner 添加你")

    async def require_admin(self, principal: Principal) -> None:
        """要求管理员权限。用于系统级终审等敏感工具。"""
        if "admin" not in principal.scopes:
            raise PermissionError(
                f"需要管理员权限。当前 token scopes={sorted(principal.scopes)}，"
                f"用户 '{principal.username}' 不是管理员。"
            )

    async def resolve_project_id(
        self,
        workspace_slug: str,
        project_slug: str,
        principal: Principal | None = None,
        access: str = "read",
    ) -> str:
        if principal is not None:
            await self.require_workspace_access(principal, workspace_slug)
        row = await self._db.fetchrow(
            """
            SELECT p.id::text AS project_id
            FROM projects p
            JOIN workspaces w ON w.id = p.workspace_id
            WHERE w.slug = $1 AND p.slug = $2
            """,
            workspace_slug,
            project_slug,
        )
        if row is None:
            raise ValueError(f"Project not found: {workspace_slug}/{project_slug}")
        if principal is not None:
            await self.require_project_access(principal, row["project_id"], access)
        return row["project_id"]

    async def resolve_workspace_id(
        self,
        principal: Principal,
        workspace_slug: str,
        access: str = "read",
    ) -> str:
        await self.require_workspace_access(principal, workspace_slug, access)
        row = await self._db.fetchrow(
            """
            SELECT id::text AS workspace_id
            FROM workspaces
            WHERE slug = $1
            """,
            workspace_slug,
        )
        if row is None:
            raise ValueError(f"Workspace not found: {workspace_slug}")
        return row["workspace_id"]
