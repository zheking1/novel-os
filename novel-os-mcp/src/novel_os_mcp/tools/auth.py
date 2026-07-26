from typing import Any
import logging
import bcrypt

from ..mcp_core import mcp
from ..config import get_settings
from ..deps import db, auth, workspace_service
from ..tool_auth import get_principal, validate_required

settings = get_settings()
logger = logging.getLogger("novel_os_mcp.tools.auth")


def hash_password(password: str) -> str:
    """Hash password using bcrypt with cost factor 10."""
    return bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt(rounds=10)).decode("ascii")


def verify_password(password: str, hashed: str) -> bool:
    """Verify password against bcrypt hash."""
    try:
        return bcrypt.checkpw(password.encode("utf-8"), hashed.encode("ascii"))
    except Exception:
        return False


@mcp.tool(name="auth.whoami")
async def auth_whoami() -> dict[str, Any]:
    """获取当前用户身份信息。返回用户名、工作空间、项目ID、权限范围和认证模式。"""
    principal = await get_principal(None)
    logger.info("auth_whoami called")
    return {
        "username": principal.username,
        "workspace": principal.workspace,
        "project_id": principal.project_id,
        "scopes": sorted(principal.scopes),
        "auth_mode": settings.auth_mode,
    }


@mcp.tool(name="workspace.create")
async def workspace_create(slug: str, name: str) -> dict[str, Any]:
    """创建新工作空间。slug 为唯一标识符，name 为显示名称。"""
    principal = await get_principal("write")
    logger.info("workspace_create called")
    return await workspace_service.create_workspace(slug=slug, name=name, owner_username=principal.username)


@mcp.tool(name="workspace.list")
async def workspace_list(username: str | None = None) -> list[dict[str, Any]]:
    """列出工作空间。可按用户名过滤，返回用户所属或管理的所有工作空间。"""
    principal = await get_principal("read")
    logger.info("workspace_list called")
    # Non-admin users can only see their own workspaces
    if "admin" not in principal.scopes:
        username = principal.username
    return await workspace_service.list_workspaces(username=username)


@mcp.tool(name="workspace.add_member")
async def workspace_add_member(workspace: str, username: str, role: str = "writer") -> dict[str, Any]:
    """添加工作空间成员。role 支持 admin/writer/reader，默认 writer。"""
    principal = await get_principal("write")
    logger.info("workspace_add_member called")
    validate_required(locals(), "workspace", "username")
    return await workspace_service.add_workspace_member(workspace_slug=workspace, username=username, role=role)


@mcp.tool(name="project.add_member")
async def project_add_member(workspace: str, project: str, username: str, role: str = "writer") -> dict[str, Any]:
    """添加项目成员。覆盖工作空间级别权限，为特定项目分配角色。"""
    principal = await get_principal("admin")
    logger.info("project_add_member called")
    validate_required(locals(), "workspace", "project", "username")
    return await workspace_service.add_project_member(
        workspace_slug=workspace,
        project_slug=project,
        username=username,
        role=role,
    )


@mcp.tool(name="project.create")
async def project_create(workspace: str, slug: str, title: str, description: str | None = None) -> dict[str, Any]:
    """在工作空间内创建新项目。需要 write 权限和工作空间访问权。"""
    principal = await get_principal("write")
    logger.info("project_create called")
    validate_required(locals(), "workspace", "slug", "title")
    await auth.require_workspace_access(principal, workspace)
    return await workspace_service.create_project(
        workspace_slug=workspace,
        project_slug=slug,
        title=title,
        description=description,
        owner_username=principal.username,
    )


@mcp.tool(name="project.list")
async def project_list(workspace: str, username: str | None = None) -> list[dict[str, Any]]:
    """列出工作空间内的项目。非管理员只能看到自己有权限的项目。"""
    principal = await get_principal(None)
    logger.info("project_list called")
    if "admin" not in principal.scopes:
        await auth.require_workspace_access(principal, workspace)
        username = principal.username
    return await workspace_service.list_projects(workspace_slug=workspace, username=username)


@mcp.tool(name="project.list_members")
async def project_list_members(workspace: str, project: str) -> list[dict[str, Any]]:
    """列出项目所有成员。需要管理员权限。"""
    principal = await get_principal("admin")
    logger.info("project_list_members called")
    validate_required(locals(), "workspace", "project")
    return await workspace_service.list_project_members(workspace_slug=workspace, project_slug=project)


@mcp.tool(name="project.register_local_binding")
async def project_register_local_binding(
    workspace: str,
    project: str,
    client_id: str,
    local_root_hint: str | None = None,
    manifest: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """注册本地客户端与项目的绑定关系。用于同步本地文件和远程项目状态。"""
    principal = await get_principal("write")
    logger.info("project_register_local_binding called")
    validate_required(locals(), "workspace", "project", "client_id")
    project_id = await auth.resolve_project_id(workspace, project, principal, access="write")
    return await workspace_service.register_local_binding(
        project_id=project_id,
        username=principal.username,
        client_id=client_id,
        local_root_hint=local_root_hint,
        manifest=manifest or {},
    )


@mcp.tool(name="user.create")
async def user_create(
    username: str,
    display_name: str | None = None,
    email: str | None = None,
    status: str = "active",
    password: str | None = None,
) -> dict[str, Any]:
    """创建新用户。需要管理员权限，username 为唯一标识。
    
    Args:
        username: 用户名（唯一标识）
        display_name: 显示名称
        email: 邮箱
        status: 状态（默认active）
        password: 初始密码（明文传入，内部哈希存储。如为空则使用默认密码'123456'）
    """
    principal = await get_principal("admin")
    logger.info("user_create called")
    validate_required(locals(), "username")
    # Hash password (use default if not provided)
    password_hash = hash_password(password) if password else hash_password("123456")
    return await workspace_service.create_user(
        username=username,
        display_name=display_name,
        email=email,
        status=status,
        password_hash=password_hash,
    )


@mcp.tool(name="user.list")
async def user_list(status: str | None = None, limit: int = 100) -> list[dict[str, Any]]:
    """列出系统用户。可按状态过滤，默认返回所有活跃用户。"""
    principal = await get_principal("admin")
    logger.info("user_list called")
    return await workspace_service.list_users(status=status, limit=limit)


@mcp.tool(name="user.delete")
async def user_delete(username: str) -> dict[str, Any]:
    """删除用户。需要管理员权限。"""
    principal = await get_principal("admin")
    logger.info("user_delete called")
    validate_required(locals(), "username")
    return await workspace_service.delete_user(username=username)


@mcp.tool(name="project.delete")
async def project_delete(workspace: str, slug: str) -> dict[str, Any]:
    """删除项目。需要 write 权限和工作空间访问权。"""
    principal = await get_principal("write")
    logger.info("project_delete called")
    validate_required(locals(), "workspace", "slug")
    await auth.require_workspace_access(principal, workspace)
    return await workspace_service.delete_project(workspace_slug=workspace, project_slug=slug)


@mcp.tool(name="workspace.delete")
async def workspace_delete(slug: str) -> dict[str, Any]:
    """删除工作空间。"""
    principal = await get_principal("write")
    logger.info("workspace_delete called")
    validate_required(locals(), "slug")
    await auth.require_workspace_access(principal, slug, access="write")
    return await workspace_service.delete_workspace(slug=slug)


@mcp.tool(name="workspace.remove_member")
async def workspace_remove_member(workspace: str, username: str) -> dict[str, Any]:
    """移除工作空间成员。"""
    principal = await get_principal("write")
    logger.info("workspace_remove_member called")
    validate_required(locals(), "workspace", "username")
    return await workspace_service.remove_workspace_member(workspace_slug=workspace, username=username)


@mcp.tool(name="auth.list_api_tokens")
async def auth_list_api_tokens(
    workspace: str | None = None,
    project: str | None = None,
    include_revoked: bool = False,
) -> list[dict[str, Any]]:
    """列出 API 令牌。支持按工作空间、项目过滤，可包含已吊销令牌。
    
    普通用户只能查看自己的 token，管理员可以查看所有 token。
    """
    principal = await get_principal(None)  # Allow any authenticated user
    logger.info("auth_list_api_tokens called")
    
    # Determine target username
    if "admin" in principal.scopes:
        # Admin can list all tokens (no username filter)
        target_username = None
    else:
        # Regular user can only list own tokens
        target_username = principal.username
    
    return await workspace_service.list_api_tokens(
        username=target_username,
        workspace_slug=workspace,
        project_slug=project,
        include_revoked=include_revoked,
    )


@mcp.tool(name="auth.revoke_api_token")
async def auth_revoke_api_token(token_id: str) -> dict[str, Any]:
    """吊销指定 API 令牌。吊销后令牌立即失效，不可恢复。"""
    principal = await get_principal("admin")
    logger.info("auth_revoke_api_token called")
    validate_required(locals(), "token_id")
    return await workspace_service.revoke_api_token(token_id=token_id)


@mcp.tool(name="auth.create_api_token")
async def auth_create_api_token(
    name: str,
    scopes: list[str],
    username: str | None = None,
    workspace: str | None = None,
    project: str | None = None,
    expires_at: str | None = None,
) -> dict[str, Any]:
    """创建 API 令牌。 scopes 定义权限范围，可限定工作空间和项目。
    
    普通用户只能为自己创建 token（无需传入 username，自动使用当前登录用户）。
    管理员可以为其他用户创建 token（传入 username 参数）。
    """
    principal = await get_principal(None)  # Allow any authenticated user
    logger.info("auth_create_api_token called")
    validate_required(locals(), "name", "scopes")
    
    # Determine target username
    if "admin" in principal.scopes:
        # Admin can create token for any user (or self if username not provided)
        target_username = username or principal.username
    else:
        # Regular user can only create token for self
        if username and username != principal.username:
            raise PermissionError("Can only create token for yourself")
        target_username = principal.username
    
    # Ensure user exists in database (create if not exists)
    await workspace_service.ensure_user_exists(target_username)
    
    return await workspace_service.create_api_token(
        username=target_username,
        name=name,
        scopes=scopes,
        workspace_slug=workspace,
        project_slug=project,
        expires_at=expires_at,
    )


@mcp.tool(name="auth.login")
async def auth_login(username: str, password: str) -> dict[str, Any]:
    """用户登录验证。验证用户名和密码，返回用户信息。
    
    Args:
        username: 用户名
        password: 明文密码
        
    Returns:
        用户信息（不包含密码哈希）
    """
    logger.info(f"auth_login called for user: {username}")
    validate_required(locals(), "username", "password")
    
    # Get user from database
    row = await db.fetchrow(
        """
        SELECT id::text, username, display_name, email, status, password_hash, created_at, updated_at
        FROM users
        WHERE username = $1
        """,
        username,
    )
    
    if row is None:
        raise PermissionError("Invalid username or password")
    
    # Verify password
    stored_hash = row.get("password_hash") or ""
    if not stored_hash or not verify_password(password, stored_hash):
        raise PermissionError("Invalid username or password")
    
    # Update last login time
    await db.execute("UPDATE users SET last_login_at = now() WHERE id = $1", row["id"])
    
    # Return user info (exclude password_hash)
    return {
        "id": row["id"],
        "username": row["username"],
        "display_name": row["display_name"],
        "email": row["email"],
        "status": row["status"],
        "created_at": row["created_at"].isoformat() if row["created_at"] else None,
        "updated_at": row["updated_at"].isoformat() if row["updated_at"] else None,
    }


@mcp.tool(name="auth.change_password")
async def auth_change_password(
    username: str,
    old_password: str,
    new_password: str,
) -> dict[str, Any]:
    """修改用户密码。
    
    Args:
        username: 用户名
        old_password: 当前密码（验证用）
        new_password: 新密码
        
    Returns:
        修改结果
    """
    principal = await get_principal(None)
    logger.info(f"auth_change_password called for user: {username}")
    validate_required(locals(), "username", "old_password", "new_password")
    
    # Only admin or the user themselves can change password
    if principal.username != username and "admin" not in principal.scopes:
        raise PermissionError("Cannot change password for other users")
    
    # Get current password hash
    row = await db.fetchrow(
        "SELECT id, password_hash FROM users WHERE username = $1",
        username,
    )
    if row is None:
        raise ValueError(f"User not found: {username}")
    
    # Verify old password (skip if admin changing other's password without old_password check)
    if principal.username == username:
        stored_hash = row.get("password_hash") or ""
        if not stored_hash or not verify_password(old_password, stored_hash):
            raise PermissionError("Current password is incorrect")
    
    # Update password
    new_hash = hash_password(new_password)
    await db.execute(
        "UPDATE users SET password_hash = $1, updated_at = now() WHERE id = $2",
        new_hash,
        row["id"],
    )
    
    return {"ok": True, "username": username, "message": "Password changed successfully"}
