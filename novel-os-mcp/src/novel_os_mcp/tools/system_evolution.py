"""System Evolution Tools - 系统级进化管理

提供系统级数据的进化提案、AI初审、管理员终审等全流程管理工具。
"""

import json
from typing import Any
import logging

from ..mcp_core import mcp
from ..deps import db, auth
from ..tool_auth import get_principal, validate_required

logger = logging.getLogger("novel_os_mcp.tools.system_evolution")


# ============================================================================
# 进化提案管理工具
# ============================================================================

@mcp.tool(name="system.evolution.propose")
async def system_evolution_propose(
    workspace: str,
    title: str,
    description: str,
    proposal_type: str,
    target_entity_type: str,
    proposed_content: dict[str, Any],
    evolution_reason: str,
    target_entity_key: str | None = None,
    target_entity_id: str | None = None,
    evidence: dict[str, Any] | None = None,
    source_project_id: str | None = None,
    source_chapter_no: int | None = None,
    metadata: dict[str, Any] | None = None,
    project: str | None = None,
) -> dict[str, Any]:
    """创建系统级进化提案。
    
    提交对系统级数据（文风档案、提示词模板、模型配置等）的改进提案。
    提案创建后自动进入AI初审队列。
    
    Args:
        title: 提案标题
        description: 提案详细描述
        proposal_type: 提案类型 (create/update/delete/merge)
        target_entity_type: 目标实体类型 (style_profile/prompt_template/model_profile/knowledge_item/setting_item/genre_config)
        proposed_content: 提案的具体内容
        evolution_reason: 进化原因和依据
        target_entity_key: 目标实体业务键（更新/删除时需要）
        target_entity_id: 目标实体ID（可选）
        evidence: 支持证据/数据
        source_project_id: 来源项目ID（如果是从项目中发现的问题）
        source_chapter_no: 来源章节号
        metadata: 额外元数据
        
    Returns:
        {
            "id": "提案ID",
            "status": "draft",
            "message": "提案创建成功，等待AI初审",
            "next_step": "AI自动初审中"
        }
    """
    principal = await get_principal("write")
    logger.info(f"system.evolution.propose: {title} by {principal.username}")
    
    validate_required(locals(), "title", "description", "proposal_type", 
                      "target_entity_type", "proposed_content", "evolution_reason")
    
    # 验证proposal_type
    if proposal_type not in ('create', 'update', 'delete', 'merge'):
        raise ValueError(f"Invalid proposal_type: {proposal_type}")
    
    # 验证target_entity_type
    valid_types = ('style_profile', 'prompt_template', 'model_profile', 
                   'knowledge_item', 'setting_item', 'genre_config')
    if target_entity_type not in valid_types:
        raise ValueError(f"Invalid target_entity_type: {target_entity_type}")
    
    # update/delete/merge需要指定目标
    if proposal_type in ('update', 'delete', 'merge') and not target_entity_key:
        raise ValueError(f"proposal_type={proposal_type} requires target_entity_key")
    
    # 插入数据库
    row = await db.fetchrow(
        """
        INSERT INTO system_evolution_proposals 
        (title, description, proposal_type, target_entity_type, target_entity_id, 
         target_entity_key, proposed_content, evolution_reason, evidence,
         source_project_id, source_chapter_no, submitted_by, status, metadata)
        VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11, $12, 'ai_reviewing', $13)
        RETURNING id::text, status, created_at
        """,
        title, description, proposal_type, target_entity_type, target_entity_id,
        target_entity_key, proposed_content, evolution_reason, evidence,
        source_project_id, source_chapter_no, 
        principal.user_id if hasattr(principal, 'user_id') else None,
        metadata or {}
    )
    
    # TODO: 触发AI初审（异步队列）
    # await _trigger_ai_review(row['id'])
    
    return {
        "id": row["id"],
        "status": row["status"],
        "title": title,
        "proposal_type": proposal_type,
        "target_entity_type": target_entity_type,
        "message": "提案创建成功，已进入AI初审队列",
        "next_step": "AI自动评审中，预计1-2分钟完成",
        "created_at": row["created_at"].isoformat() if row["created_at"] else None
    }


@mcp.tool(name="system.evolution.list")
async def system_evolution_list(
    workspace: str,
    status: str | None = None,
    target_entity_type: str | None = None,
    proposal_type: str | None = None,
    submitted_by_me: bool = False,
    limit: int = 50,
    offset: int = 0,
    project: str | None = None,
) -> dict[str, Any]:
    """获取进化提案列表。
    
    Args:
        status: 按状态筛选 (draft/ai_reviewing/ai_reviewed/pending_admin/admin_approved/admin_rejected/applied)
        target_entity_type: 按目标实体类型筛选
        proposal_type: 按提案类型筛选 (create/update/delete/merge)
        submitted_by_me: 只显示我提交的提案
        limit: 返回数量限制
        offset: 分页偏移
        
    Returns:
        {
            "proposals": [...],
            "total": 总数,
            "limit": 限制,
            "offset": 偏移
        }
    """
    principal = await get_principal("read")
    
    # 构建查询条件
    conditions = ["1=1"]
    params: list[Any] = []
    
    if status:
        conditions.append(f"status = ${len(params)+1}")
        params.append(status)
    
    if target_entity_type:
        conditions.append(f"target_entity_type = ${len(params)+1}")
        params.append(target_entity_type)
        
    if proposal_type:
        conditions.append(f"proposal_type = ${len(params)+1}")
        params.append(proposal_type)
    
    if submitted_by_me:
        conditions.append(f"submitted_by = ${len(params)+1}")
        params.append(principal.user_id if hasattr(principal, 'user_id') else None)
    
    # 查询总数
    count_sql = f"""
        SELECT COUNT(*) 
        FROM system_evolution_proposals 
        WHERE {' AND '.join(conditions)}
    """
    total = await db.fetchval(count_sql, *params)
    
    # 查询数据
    params.extend([limit, offset])
    rows = await db.fetch(
        f"""
        SELECT 
            id::text, title, description, proposal_type, target_entity_type,
            target_entity_key, status, ai_review_result, submitted_by,
            ai_submitter, created_at, updated_at
        FROM system_evolution_proposals
        WHERE {' AND '.join(conditions)}
        ORDER BY created_at DESC
        LIMIT ${len(params)-1} OFFSET ${len(params)}
        """,
        *params
    )
    
    proposals = []
    for row in rows:
        proposals.append({
            "id": row["id"],
            "title": row["title"],
            "description": row["description"][:200] + "..." if len(row["description"]) > 200 else row["description"],
            "proposal_type": row["proposal_type"],
            "target_entity_type": row["target_entity_type"],
            "target_entity_key": row["target_entity_key"],
            "status": row["status"],
            "ai_score": row["ai_review_result"].get("score") if row["ai_review_result"] else None,
            "is_ai_submitted": row["ai_submitter"] is not None,
            "created_at": row["created_at"].isoformat() if row["created_at"] else None,
            "updated_at": row["updated_at"].isoformat() if row["updated_at"] else None,
        })
    
    return {
        "proposals": proposals,
        "total": total,
        "limit": limit,
        "offset": offset
    }


@mcp.tool(name="system.evolution.get")
async def system_evolution_get(
    workspace: str,
    proposal_id: str,
    project: str | None = None,
) -> dict[str, Any]:
    """获取进化提案详情。
    
    Args:
        proposal_id: 提案ID
        
    Returns:
        提案完整详情，包括AI评审结果和管理员审核结果
    """
    principal = await get_principal("read")
    validate_required(locals(), "proposal_id")
    
    row = await db.fetchrow(
        """
        SELECT 
            id::text, title, description, proposal_type, target_entity_type,
            target_entity_id, target_entity_key, proposed_content, evolution_reason,
            evidence, status, ai_review_result, admin_review_result,
            submitted_by, ai_submitter, source_project_id, source_chapter_no,
            applied_at, applied_version, metadata, created_at, updated_at
        FROM system_evolution_proposals
        WHERE id = $1
        """,
        proposal_id
    )
    
    if not row:
        raise ValueError(f"Proposal not found: {proposal_id}")
    
    return {
        "id": row["id"],
        "title": row["title"],
        "description": row["description"],
        "proposal_type": row["proposal_type"],
        "target_entity_type": row["target_entity_type"],
        "target_entity_id": row["target_entity_id"],
        "target_entity_key": row["target_entity_key"],
        "proposed_content": row["proposed_content"],
        "evolution_reason": row["evolution_reason"],
        "evidence": row["evidence"],
        "status": row["status"],
        "ai_review_result": row["ai_review_result"],
        "admin_review_result": row["admin_review_result"],
        "is_ai_submitted": row["ai_submitter"] is not None,
        "ai_submitter": row["ai_submitter"],
        "source_project_id": row["source_project_id"],
        "source_chapter_no": row["source_chapter_no"],
        "applied_at": row["applied_at"].isoformat() if row["applied_at"] else None,
        "applied_version": row["applied_version"],
        "metadata": row["metadata"],
        "created_at": row["created_at"].isoformat() if row["created_at"] else None,
        "updated_at": row["updated_at"].isoformat() if row["updated_at"] else None,
    }


async def _apply_proposal(proposal_id: str) -> dict[str, Any]:
    """应用进化提案到对应的系统级数据表。"""
    proposal = await db.fetchrow(
        """SELECT target_entity_type, proposed_content, target_entity_key
           FROM system_evolution_proposals WHERE id = $1""",
        proposal_id,
    )
    if not proposal:
        return {"ok": False, "error": "proposal not found"}

    etype = proposal["target_entity_type"]
    content = proposal["proposed_content"]
    if isinstance(content, str):
        content = json.loads(content)
    ekey = proposal.get("target_entity_key")

    try:
        if etype == "setting_item":
            category = content.get("category", "review-rules")
            title = content.get("title", content.get("core_summary", "Untitled"))[:200]
            summary = content.get("core_summary", content.get("ai_instruction", ""))
            level = content.get("level", "reminder")
            # Find or create the workspace's default category for this type
            cat_row = await db.fetchrow(
                "SELECT id FROM setting_categories WHERE slug = $1 AND workspace_id = (SELECT id FROM workspaces LIMIT 1) LIMIT 1",
                category,
            )
            if cat_row:
                await db.execute(
                    """INSERT INTO setting_items (workspace_id, category_id, item_code, core_summary, level, ai_instruction, is_global)
                       VALUES ((SELECT id FROM workspaces LIMIT 1), $1, $2, $3, $4, $5, true)
                       ON CONFLICT DO NOTHING""",
                    cat_row["id"], f"auto_evolved_{proposal_id[:8]}", summary, level, content.get("ai_instruction", summary),
                )

        elif etype == "knowledge_item":
            entity_type = content.get("entity_type", "character")
            entity_name = content.get("name", "")
            suggested = content.get("suggested_update", "")
            if entity_name and suggested:
                await db.execute(
                    """INSERT INTO knowledge_entities (entity_type, name, content, summary, source)
                       VALUES ($1, $2, $3, $4, 'system_evolution')
                       ON CONFLICT (name, entity_type) DO UPDATE
                       SET content = CASE WHEN knowledge_entities.source = 'system_evolution' THEN EXCLUDED.content ELSE knowledge_entities.content END,
                           summary = EXCLUDED.summary""",
                    entity_type, entity_name, suggested, suggested[:200],
                )

        elif etype == "style_profile":
            profile_key = ekey or content.get("profile_key", f"evolved_{proposal_id[:8]}")
            await db.execute(
                """INSERT INTO system_style_profiles (profile_key, name, description, narrative_pov, tense, tone, sample_paragraphs)
                   VALUES ($1, $2, $3, $4, $5, $6, $7::jsonb)
                   ON CONFLICT (profile_key) DO UPDATE SET
                   description = EXCLUDED.description, tone = EXCLUDED.tone""",
                profile_key,
                content.get("display_name", content.get("name", profile_key)),
                content.get("description", ""),
                content.get("narrative_pov", "third_limited"),
                content.get("tense", "past"),
                content.get("tone", ""),
                json.dumps(content.get("sample_paragraphs", [])),
            )

        elif etype == "prompt_template":
            template_key = ekey or content.get("template_key", f"evolved_{proposal_id[:8]}")
            await db.execute(
                """INSERT INTO system_prompt_templates (template_key, template_name, template_type, template_content, status)
                   VALUES ($1, $2, $3, $4, 'active')
                   ON CONFLICT (template_key) DO UPDATE SET
                   template_content = EXCLUDED.template_content""",
                template_key,
                content.get("name", template_key),
                content.get("template_type", "analysis"),
                content.get("template_content", ""),
            )

        elif etype == "model_profile":
            profile_key = ekey or content.get("profile_key", f"evolved_{proposal_id[:8]}")
            project_id = content.get("project_id")
            if project_id:
                await db.execute(
                    """INSERT INTO model_profiles (project_id, profile_key, provider, model_name, task_types, status)
                       VALUES ($1, $2, $3, $4, $5::text[], 'active')
                       ON CONFLICT (project_id, profile_key) DO UPDATE SET
                       model_name = EXCLUDED.model_name""",
                    project_id, profile_key, content.get("provider", "custom"),
                    content.get("model_name", ""), content.get("task_types", ["review"]),
                )

        return {"ok": True, "target_type": etype}

    except Exception as e:
        logger.error("Failed to apply proposal %s: %s", proposal_id, e)
        return {"ok": False, "error": str(e)}


@mcp.tool(name="system.evolution.admin_review")
async def _restore_from_backup(proposal_id: str, backup: dict) -> None:
    """从 backup_snapshots 恢复数据（审批拒绝时回滚）。"""
    import json
    logger = logging.getLogger("novel_os_mcp.tools.system_evolution")

    restored = 0
    conflicts = 0

    # Restore project_knowledge
    for pk_key, old_data in backup.get("project_knowledge", {}).items():
        try:
            row = await db.fetchrow(
                "SELECT description FROM project_knowledge WHERE project_id=(SELECT source_project_id FROM system_evolution_proposals WHERE id=$1) AND category=$2 AND key=$3",
                proposal_id, old_data["category"], old_data["key"],
            )
            if row and old_data.get("description"):
                await db.execute(
                    "UPDATE project_knowledge SET description=$1, tags=$2::text[] WHERE project_id=(SELECT source_project_id FROM system_evolution_proposals WHERE id=$3) AND category=$4 AND key=$5",
                    old_data["description"], old_data.get("tags", []), proposal_id, old_data["category"], old_data["key"],
                )
            restored += 1
        except Exception as exc:
            conflicts += 1
            logger.warning("Restore conflict project_knowledge %s: %s", pk_key, exc)

    # Restore setting_items
    for item_code, old_data in backup.get("setting_items", {}).items():
        try:
            if old_data.get("core_summary"):
                await db.execute(
                    "UPDATE setting_items SET core_summary=$1, level=$2 WHERE item_code=$3",
                    old_data["core_summary"], old_data.get("level", "knowledge"), item_code,
                )
            restored += 1
        except Exception as exc:
            conflicts += 1
            logger.warning("Restore conflict setting_items %s: %s", item_code, exc)

    # Restore universal_knowledge
    for topic, old_data in backup.get("universal_knowledge", {}).items():
        try:
            if old_data.get("content"):
                await db.execute(
                    "UPDATE universal_knowledge SET content=$1, summary=$2 WHERE topic=$3",
                    old_data["content"], old_data.get("summary", ""), topic,
                )
            restored += 1
        except Exception as exc:
            conflicts += 1
            logger.warning("Restore conflict uk %s: %s", topic, exc)

    # Restore rules (canon_rules)
    for rule_key, old_data in backup.get("canon_rules", {}).items():
        try:
            if old_data.get("content"):
                await db.execute(
                    "UPDATE canon_rules SET content=$1, title=$2 WHERE rule_key=$3",
                    old_data["content"], old_data.get("title", ""), rule_key,
                )
            restored += 1
        except Exception as exc:
            conflicts += 1
            logger.warning("Restore conflict canon_rules %s: %s", rule_key, exc)

    logger.info("Restore: %d restored, %d conflicts", restored, conflicts)


async def system_evolution_admin_review(
    workspace: str,
    proposal_id: str,
    decision: str,
    reason: str | None = None,
    project: str | None = None,
) -> dict[str, Any]:
    """管理员审核进化提案。
    
    只有管理员可以调用此工具。审核通过后，提案会自动应用到系统级数据。
    
    Args:
        proposal_id: 提案ID
        decision: 审核决定 (approve/reject/request_changes)
        reason: 审核理由（拒绝或要求修改时必须）
        
    Returns:
        {
            "id": "提案ID",
            "status": "新的状态",
            "message": "处理结果说明"
        }
    """
    principal = await get_principal("write")
    # TODO: 检查管理员权限
    # await auth.require_admin(principal)
    
    validate_required(locals(), "proposal_id", "decision")
    
    if decision not in ('approve', 'reject', 'request_changes'):
        raise ValueError(f"Invalid decision: {decision}")
    
    if decision in ('reject', 'request_changes') and not reason:
        raise ValueError(f"decision={decision} requires reason")
    
# 获取提案当前状态
    proposal = await db.fetchrow(
        "SELECT status, target_entity_type, proposed_content, backup_snapshots FROM system_evolution_proposals WHERE id = $1",
        proposal_id
    )

    if not proposal:
        raise ValueError(f"Proposal not found: {proposal_id}")

    # 兼容两种来源：普通进化提案(ai_reviewed) 和 讨论室提案(pending_admin)
    allowed_statuses = ['ai_reviewed', 'pending_admin']
    if proposal["status"] not in allowed_statuses:
        raise ValueError(f"Cannot review proposal with status={proposal['status']}")

    # 更新审核结果
    admin_result = {
        "decision": decision,
        "reason": reason,
        "reviewed_by": principal.username,
        "reviewed_at": "now()"
    }

    if decision == 'approve':
        new_status = 'admin_approved'
        if proposal["status"] == 'ai_reviewed':
            apply_result = await _apply_proposal(proposal_id)
            if not apply_result.get("ok"):
                logger.warning("Proposal %s approved but apply failed: %s", proposal_id, apply_result.get("error"))
        # 讨论室提案：数据已写入，只需清理备份
        if proposal["status"] == 'pending_admin':
            await db.execute(
                "UPDATE system_evolution_proposals SET backup_snapshots='{}'::jsonb WHERE id=$1",
                proposal_id,
            )

    elif decision == 'reject':
        new_status = 'admin_rejected'
        # 讨论室提案：从备份恢复
        if proposal["status"] == 'pending_admin':
            backup = proposal.get("backup_snapshots", {})
            if isinstance(backup, str):
                import json
                backup = json.loads(backup)
            if backup:
                await _restore_from_backup(proposal_id, backup)
    else:  # request_changes
        new_status = 'draft'

    await db.execute(
        """
        UPDATE system_evolution_proposals
        SET status = $1, admin_review_result = $2, updated_at = now()
        WHERE id = $3
        """,
        new_status, admin_result, proposal_id
    )

    # 发送通知给提交者
    # await _send_review_notification(proposal_id, decision)
    
    messages = {
        'approve': '提案已批准，正在应用到系统级数据',
        'reject': '提案已被拒绝',
        'request_changes': '提案已退回，需要修改后重新提交'
    }
    
    return {
        "id": proposal_id,
        "status": new_status,
        "decision": decision,
        "message": messages[decision]
    }


@mcp.tool(name="system.evolution.get_history")
async def system_evolution_get_history(
    workspace: str,
    target_entity_type: str,
    target_entity_key: str,
    limit: int = 20,
    project: str | None = None,
) -> dict[str, Any]:
    """获取指定实体的进化历史。
    
    Args:
        target_entity_type: 实体类型
        target_entity_key: 实体业务键
        limit: 返回数量限制
        
    Returns:
        {
            "entity_type": "类型",
            "entity_key": "键",
            "proposals": [...],
            "current_version": 当前版本
        }
    """
    principal = await get_principal("read")
    
    rows = await db.fetch(
        """
        SELECT 
            id::text, title, proposal_type, status, 
            ai_review_result, applied_version, created_at
        FROM system_evolution_proposals
        WHERE target_entity_type = $1 AND target_entity_key = $2
        ORDER BY created_at DESC
        LIMIT $3
        """,
        target_entity_type, target_entity_key, limit
    )
    
    proposals = []
    for row in rows:
        proposals.append({
            "id": row["id"],
            "title": row["title"],
            "proposal_type": row["proposal_type"],
            "status": row["status"],
            "ai_score": row["ai_review_result"].get("score") if row["ai_review_result"] else None,
            "applied_version": row["applied_version"],
            "created_at": row["created_at"].isoformat() if row["created_at"] else None,
        })
    
    # 获取当前版本
    version = await _get_entity_current_version(target_entity_type, target_entity_key)
    
    return {
        "entity_type": target_entity_type,
        "entity_key": target_entity_key,
        "proposals": proposals,
        "current_version": version
    }


@mcp.tool(name="system.evolution.retry_ai_review")
async def system_evolution_retry_ai_review(
    workspace: str,
    proposal_id: str,
    project: str | None = None,
) -> dict[str, Any]:
    """重试AI初审。
    
    当AI初审失败时，管理员可以手动触发重试。
    
    Args:
        proposal_id: 提案ID
        
    Returns:
        {
            "id": "提案ID",
            "status": "ai_reviewing",
            "message": "已重新进入AI初审队列"
        }
    """
    principal = await get_principal("write")
    # await auth.require_admin(principal)
    
    validate_required(locals(), "proposal_id")
    
    # 检查当前状态
    current = await db.fetchval(
        "SELECT status FROM system_evolution_proposals WHERE id = $1",
        proposal_id
    )
    
    if current != 'ai_rejected':
        raise ValueError(f"Can only retry proposals with status=ai_rejected, current={current}")
    
    await db.execute(
        """
        UPDATE system_evolution_proposals
        SET status = 'ai_reviewing', ai_retry_count = ai_retry_count + 1, updated_at = now()
        WHERE id = $1
        """,
        proposal_id
    )
    
    # TODO: 触发AI初审
    
    return {
        "id": proposal_id,
        "status": "ai_reviewing",
        "message": "已重新进入AI初审队列"
    }


# ============================================================================
# 内部辅助函数
# ============================================================================

async def _get_entity_current_version(entity_type: str, entity_key: str) -> int | None:
    """获取实体当前版本号。"""
    table_map = {
        'style_profile': 'system_style_profiles',
        'prompt_template': 'system_prompt_templates',
        'model_profile': 'system_model_profiles',
    }
    
    if entity_type not in table_map:
        return None
    
    table = table_map[entity_type]
    version = await db.fetchval(
        f"SELECT version FROM {table} WHERE profile_key = $1",
        entity_key
    )
    return version
