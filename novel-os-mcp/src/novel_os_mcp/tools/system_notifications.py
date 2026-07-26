"""System Notifications Tools - 站内通知管理

提供站内通知的查询、标记已读、删除等功能。
"""

from typing import Any
import logging

from ..mcp_core import mcp
from ..deps import db, auth
from ..tool_auth import get_principal, validate_required

logger = logging.getLogger("novel_os_mcp.tools.system_notifications")


# ============================================================================
# 通知查询工具
# ============================================================================

@mcp.tool(name="system.notification.list")
async def system_notification_list(
    workspace: str,
    project: str | None = None,
    is_unread_only: bool = False,
    notification_type: str | None = None,
    limit: int = 50,
    offset: int = 0,
) -> dict[str, Any]:
    """获取用户的站内通知列表。
    
    返回用户个人的通知和全局通知。
    
    Args:
        is_unread_only: 只显示未读通知
        notification_type: 按类型筛选 (evolution_proposal/system_update/ai_review_completed/admin_review_required)
        limit: 返回数量限制
        offset: 分页偏移
        
    Returns:
        {
            "notifications": [...],
            "unread_count": 未读数量,
            "total": 总数
        }
    """
    principal = await get_principal("read")
    user_id = principal.user_id if hasattr(principal, 'user_id') else None
    
    # 构建查询条件
    conditions = ["(user_id = $1 OR is_global = true)"]
    params: list[Any] = [user_id]
    
    if is_unread_only:
        conditions.append("is_read = false")
    
    if notification_type:
        conditions.append(f"type = ${len(params)+1}")
        params.append(notification_type)
    
    # 查询总数和未读数
    total_result = await db.fetchrow(
        f"""
        SELECT 
            COUNT(*) as total,
            COUNT(*) FILTER (WHERE is_read = false) as unread_count
        FROM system_notifications 
        WHERE {' AND '.join(conditions)}
        """,
        *params
    )
    
    # 查询通知数据
    params.extend([limit, offset])
    rows = await db.fetch(
        f"""
        SELECT 
            id::text, type, title, content, is_read, read_at,
            related_proposal_id, is_global, created_at
        FROM system_notifications
        WHERE {' AND '.join(conditions)}
        ORDER BY created_at DESC
        LIMIT ${len(params)-1} OFFSET ${len(params)}
        """,
        *params
    )
    
    notifications = []
    for row in rows:
        notifications.append({
            "id": row["id"],
            "type": row["type"],
            "title": row["title"],
            "content": row["content"],
            "is_read": row["is_read"],
            "read_at": row["read_at"].isoformat() if row["read_at"] else None,
            "related_proposal_id": row["related_proposal_id"],
            "is_global": row["is_global"],
            "created_at": row["created_at"].isoformat() if row["created_at"] else None,
        })
    
    return {
        "notifications": notifications,
        "unread_count": total_result["unread_count"] if total_result else 0,
        "total": total_result["total"] if total_result else 0,
        "limit": limit,
        "offset": offset
    }


@mcp.tool(name="system.notification.mark_read")
async def system_notification_mark_read(
    workspace: str,
    notification_id: str,
    project: str | None = None,
) -> dict[str, Any]:
    """标记通知为已读。
    
    Args:
        notification_id: 通知ID
        
    Returns:
        {
            "id": "通知ID",
            "is_read": true,
            "message": "已标记为已读"
        }
    """
    principal = await get_principal("write")
    validate_required(locals(), "notification_id")
    
    user_id = principal.user_id if hasattr(principal, 'user_id') else None
    
    # 验证通知归属
    notification = await db.fetchrow(
        "SELECT user_id, is_global FROM system_notifications WHERE id = $1",
        notification_id
    )
    
    if not notification:
        raise ValueError(f"Notification not found: {notification_id}")
    
    # 检查权限（只能标记自己的通知或全局通知）
    if not notification["is_global"] and notification["user_id"] != user_id:
        raise ValueError("Cannot mark other user's notification as read")
    
    await db.execute(
        """
        UPDATE system_notifications
        SET is_read = true, read_at = now()
        WHERE id = $1
        """,
        notification_id
    )
    
    return {
        "id": notification_id,
        "is_read": True,
        "message": "已标记为已读"
    }


@mcp.tool(name="system.notification.mark_all_read")
async def system_notification_mark_all_read(
    workspace: str,
    notification_type: str | None = None,
    project: str | None = None,
) -> dict[str, Any]:
    """标记所有通知为已读。
    
    Args:
        notification_type: 只标记特定类型的通知（可选）
        
    Returns:
        {
            "marked_count": 标记数量,
            "message": "已标记X条通知为已读"
        }
    """
    principal = await get_principal("write")
    user_id = principal.user_id if hasattr(principal, 'user_id') else None
    
    conditions = ["(user_id = $1 OR is_global = true)", "is_read = false"]
    params: list[Any] = [user_id]
    
    if notification_type:
        conditions.append(f"type = ${len(params)+1}")
        params.append(notification_type)
    
    result = await db.execute(
        f"""
        UPDATE system_notifications
        SET is_read = true, read_at = now()
        WHERE {' AND '.join(conditions)}
        """,
        *params
    )
    
    # 解析影响行数
    marked_count = int(result.split()[-1]) if result else 0
    
    return {
        "marked_count": marked_count,
        "message": f"已标记 {marked_count} 条通知为已读"
    }


@mcp.tool(name="system.notification.delete")
async def system_notification_delete(
    workspace: str,
    notification_id: str,
    project: str | None = None,
) -> dict[str, Any]:
    """删除通知。
    
    Args:
        notification_id: 通知ID
        
    Returns:
        {
            "id": "通知ID",
            "message": "已删除"
        }
    """
    principal = await get_principal("write")
    validate_required(locals(), "notification_id")
    
    user_id = principal.user_id if hasattr(principal, 'user_id') else None
    
    # 验证通知归属
    notification = await db.fetchrow(
        "SELECT user_id, is_global FROM system_notifications WHERE id = $1",
        notification_id
    )
    
    if not notification:
        raise ValueError(f"Notification not found: {notification_id}")
    
    # 检查权限
    if not notification["is_global"] and notification["user_id"] != user_id:
        raise ValueError("Cannot delete other user's notification")
    
    await db.execute(
        "DELETE FROM system_notifications WHERE id = $1",
        notification_id
    )
    
    return {
        "id": notification_id,
        "message": "已删除"
    }


@mcp.tool(name="system.notification.get_unread_count")
async def system_notification_get_unread_count(
    workspace: str,
    project: str | None = None,
) -> dict[str, Any]:
    """获取未读通知数量。
    
    Returns:
        {
            "unread_count": 未读数量,
            "by_type": {
                "evolution_proposal": 2,
                "system_update": 1,
                ...
            }
        }
    """
    principal = await get_principal("read")
    user_id = principal.user_id if hasattr(principal, 'user_id') else None
    
    # 查询总数
    total = await db.fetchval(
        """
        SELECT COUNT(*) 
        FROM system_notifications 
        WHERE (user_id = $1 OR is_global = true) AND is_read = false
        """,
        user_id
    )
    
    # 按类型统计
    rows = await db.fetch(
        """
        SELECT type, COUNT(*) as count
        FROM system_notifications 
        WHERE (user_id = $1 OR is_global = true) AND is_read = false
        GROUP BY type
        """,
        user_id
    )
    
    by_type = {row["type"]: row["count"] for row in rows}
    
    return {
        "unread_count": total,
        "by_type": by_type
    }


# ============================================================================
# 内部通知发送函数（供其他模块调用）
# ============================================================================

async def _send_notification(
    user_id: str | None,
    notification_type: str,
    title: str,
    content: str,
    is_global: bool = False,
    related_proposal_id: str | None = None,
) -> dict[str, Any]:
    """内部函数：发送站内通知。
    
    Args:
        user_id: 接收者ID（None表示发送给所有管理员）
        notification_type: 通知类型
        title: 标题
        content: 内容
        is_global: 是否全局通知
        related_proposal_id: 关联的提案ID
        
    Returns:
        {"id": "通知ID", "message": "发送成功"}
    """
    row = await db.fetchrow(
        """
        INSERT INTO system_notifications 
        (user_id, type, title, content, is_global, related_proposal_id)
        VALUES ($1, $2, $3, $4, $5, $6)
        RETURNING id::text
        """,
        user_id, notification_type, title, content, is_global, related_proposal_id
    )
    
    logger.info(f"Notification sent: {title} to user={user_id}, global={is_global}")
    
    return {
        "id": row["id"],
        "message": "通知发送成功"
    }


async def _send_evolution_proposal_notification(
    proposal_id: str,
    proposal_title: str,
    status: str,
) -> None:
    """发送进化提案相关通知。"""
    
    if status == 'ai_reviewed':
        # AI初审完成，通知管理员
        await _send_notification(
            user_id=None,  # 发送给所有管理员
            notification_type='admin_review_required',
            title=f'新的进化提案待审核: {proposal_title}',
            content=f'提案ID: {proposal_id}\n标题: {proposal_title}\n状态: AI初审已完成，等待管理员审核',
            is_global=True,
            related_proposal_id=proposal_id
        )
    
    elif status == 'admin_approved':
        # 管理员批准，通知提交者
        proposal = await db.fetchrow(
            "SELECT submitted_by, title FROM system_evolution_proposals WHERE id = $1",
            proposal_id
        )
        if proposal and proposal["submitted_by"]:
            await _send_notification(
                user_id=proposal["submitted_by"],
                notification_type='evolution_proposal',
                title=f'您的进化提案已通过: {proposal_title}',
                content=f'提案: {proposal_title}\n状态: 已批准并应用到系统',
                related_proposal_id=proposal_id
            )
    
    elif status == 'admin_rejected':
        # 管理员拒绝，通知提交者
        proposal = await db.fetchrow(
            "SELECT submitted_by, title, admin_review_result FROM system_evolution_proposals WHERE id = $1",
            proposal_id
        )
        if proposal and proposal["submitted_by"]:
            reason = proposal["admin_review_result"].get("reason", "未提供理由") if proposal["admin_review_result"] else "未提供理由"
            await _send_notification(
                user_id=proposal["submitted_by"],
                notification_type='evolution_proposal',
                title=f'您的进化提案被拒绝: {proposal_title}',
                content=f'提案: {proposal_title}\n状态: 被拒绝\n原因: {reason}',
                related_proposal_id=proposal_id
            )


async def _cleanup_expired_notifications() -> int:
    """清理过期的站内通知。
    
    Returns:
        清理的数量
    """
    result = await db.execute(
        "DELETE FROM system_notifications WHERE expires_at < now()"
    )
    
    # 解析影响行数
    deleted_count = int(result.split()[-1]) if result else 0
    
    if deleted_count > 0:
        logger.info(f"Cleaned up {deleted_count} expired notifications")
    
    return deleted_count
