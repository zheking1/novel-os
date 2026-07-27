"""Discussion Room Tools — 多模型讨论室 MCP 入口
会话持久化到数据库，支持历史话题查看和续传。
"""
import json
import logging
import uuid
from typing import Any

from ..mcp_core import mcp
from ..tool_auth import get_principal, validate_required
from ..deps import db, auth, llm_client, gatekeeper_service
from ..utils import json_dumps

logger = logging.getLogger("novel_os_mcp.tools.discussion_room")

MODEL_POOL = [
    "ds-v4-flash", "ds-v32", "glm-5",
    "ds-v4-pro", "glm-51",
]

ROTATION = [
    ["ds-v4-flash", "ds-v32", "glm-5"],
    ["ds-v4-pro", "glm-51", "ds-v4-flash"],
    ["ds-v32", "glm-5", "ds-v4-pro"],
]

async def _pick_contributed_models(db, user_id: str) -> list[str]:
    rows = await db.fetch(
        """SELECT mp.profile_key, mp.model_name, mp.provider,
                  COALESCE(SUM(CASE WHEN el.id IS NOT NULL THEN 1 ELSE 0 END), 0) as use_count
           FROM model_profiles mp
           LEFT JOIN evolution_logs el ON el.source_id LIKE '%%' || mp.profile_key || '%%'
              AND el.source_type = 'discussion_room' AND el.created_at > NOW() - INTERVAL '7 days'
           WHERE (mp.task_types && ARRAY['review','analysis','draft','outline','polish','context'] OR mp.is_contributed = true)
             AND mp.status = 'active'
           GROUP BY mp.profile_key, mp.model_name, mp.provider
           ORDER BY use_count ASC""",
    )
    if not rows:
        return []
    picked = []
    seen_cores = set()
    for r in rows:
        core = r["model_name"].rpartition("/")[2] or r["model_name"]
        if core in seen_cores:
            continue
        picked.append(r["profile_key"])
        seen_cores.add(core)
        if len(picked) >= 3:
            break
    return picked




@mcp.tool(name="discussion_room.create_session")
async def discussion_room_create_session(
    workspace: str,
    project: str,
    topic: str,
    model_keys: list[str] | None = None,
    rate_limit_delay: float = 1.5,
    rate_limit_retries: int = 3,
    data_source: str = "knowledge-entries",
    data_category: str | None = None,
    output_type: str = "knowledge",
) -> dict[str, Any]:
    """创建讨论会话并存入数据库。

    Args:
        workspace: 工作区
        project: 项目
        topic: 讨论话题
        model_keys: 模型列表，不传自动选择
        rate_limit_delay: 调用间隔
        rate_limit_retries: 重试次数
        data_source: 数据来源
        data_category: 分类筛选
        output_type: 输出类型
            - "knowledge": 输出JSON知识条目（默认，用于知识库维护）
            - "review": 输出自然语言审查结论（"完备"或"缺XX"）
    """
    principal = await get_principal("write")
    logger.info("discussion_room.create_session: topic=%s output_type=%s", topic[:50], output_type)
    validate_required(locals(), "workspace", "project", "topic")

    pid = await auth.resolve_project_id(workspace, project, principal, access="write")

    if not model_keys:
        model_keys = await _pick_contributed_models(db, principal.username)

    if not model_keys or len(model_keys) < 2:
        return {"ok": False, "error": "讨论模型不足。请至少贡献2个模型到讨论池（模型配置页中勾选'贡献给讨论室'），或联系管理员配置全局讨论模型。"}

    session_id = str(uuid.uuid4())
    control_model = model_keys[0]
    disc_models = model_keys[1:]

    user_entry = json_dumps({
        "role": "user", "model": "user", "phase": "question",
        "content": topic,
        "timestamp": str(__import__("datetime").datetime.utcnow()),
    })

    await db.execute(
        """INSERT INTO discussion_sessions
           (id, workspace, project, topic, control_model, discussion_models,
            phase, round, status, responses, history)
           VALUES ($1, $2, $3, $4, $5, $6::text[], 'analyzing', 0, 'running', $7::jsonb, $8::jsonb)""",
        session_id, workspace, project, topic, control_model, disc_models,
        f"[{user_entry}]", json_dumps({"data_source": data_source, "data_category": data_category, "output_type": output_type}),
    )
    logger.info("Session %s created in DB", session_id)

    # Start background discussion
    import asyncio
    asyncio.ensure_future(_run_discussion(
        session_id, pid, principal.username, topic, model_keys, rate_limit_delay, rate_limit_retries, data_source, data_category, output_type,
    ))

    return {
        "session_id": session_id, "topic": topic, "phase": "analyzing",
        "control_model": control_model, "discussion_models": disc_models,
        "message": "讨论已启动",
    }


@mcp.tool(name="discussion_room.get_updates")
async def discussion_room_get_updates(session_id: str) -> dict[str, Any]:
    """获取讨论会话的最新状态。"""
    row = await db.fetchrow(
        "SELECT * FROM discussion_sessions WHERE id = $1", session_id,
    )
    if not row:
        return {"error": "session not found"}
    return {
        "session_id": session_id,
        "phase": row["phase"],
        "round": row["round"],
        "responses": row["responses"] if isinstance(row["responses"], list) else json.loads(row["responses"]),
        "consensus_reached": row["consensus_reached"],
        "summary": row["summary"],
        "status": row["status"],
        "control_model": row["control_model"],
        "discussion_models": row["discussion_models"],
    }


@mcp.tool(name="discussion_room.list_sessions")
async def discussion_room_list_sessions(
    workspace: str,
    project: str,
    status: str | None = None,
    limit: int = 20,
) -> dict[str, Any]:
    """列出历史讨论会话。

    Args:
        workspace: 工作区
        project: 项目
        status: 筛选状态 (running/completed/applied/rate_limited)，不传返回全部
        limit: 最多返回条数
    """
    principal = await get_principal("read")
    logger.info("discussion_room.list_sessions")
    rows = await db.fetch(
        """SELECT id, topic, control_model, discussion_models, phase, round,
                  status, consensus_reached, created_at
           FROM discussion_sessions
           WHERE workspace=$1 AND project=$2
           AND ($3::text IS NULL OR status=$3)
           ORDER BY created_at DESC LIMIT $4""",
        workspace, project, status, limit,
    )
    return {
        "sessions": [{
            "session_id": r["id"],
            "topic": r["topic"],
            "status": r["status"],
            "phase": r["phase"],
            "round": r["round"],
            "control_model": r["control_model"],
            "discussion_models": r["discussion_models"],
            "consensus_reached": r["consensus_reached"],
            "created_at": str(r["created_at"]),
        } for r in rows],
    }


@mcp.tool(name="discussion_room.get_session")
async def discussion_room_get_session(session_id: str) -> dict[str, Any]:
    """获取单个会话完整记录。"""
    row = await db.fetchrow(
        "SELECT * FROM discussion_sessions WHERE id = $1", session_id,
    )
    if not row:
        return {"error": "session not found"}
    return {
        "session_id": session_id,
        "topic": row["topic"],
        "control_model": row["control_model"],
        "discussion_models": row["discussion_models"],
        "phase": row["phase"],
        "round": row["round"],
        "status": row["status"],
        "consensus_reached": row["consensus_reached"],
        "summary": row["summary"],
        "responses": row["responses"] if isinstance(row["responses"], list) else json.loads(row["responses"]),
        "created_at": str(row["created_at"]),
    }


@mcp.tool(name="discussion_room.resume_session")
async def discussion_room_resume_session(
    workspace: str,
    project: str,
    session_id: str,
    new_topic: str = "",
    rate_limit_delay: float = 1.5,
    rate_limit_retries: int = 3,
) -> dict[str, Any]:
    """从断点继续讨论。new_topic 可选，传入用户新增的问题。"""
    principal = await get_principal("write")
    logger.info("discussion_room.resume_session: %s", session_id)
    row = await db.fetchrow(
        "SELECT * FROM discussion_sessions WHERE id = $1", session_id,
    )
    if not row:
        return {"error": "session not found"}

    # Reset state to allow re-running
    await db.execute(
        "UPDATE discussion_sessions SET status='running', phase='proposing', round=0, consensus_reached=false, updated_at=NOW() WHERE id=$1",
        session_id,
    )

    # Append user's new question to responses
    user_content = new_topic or row["topic"]
    user_entry = json_dumps({
        "role": "user", "model": "user", "phase": "question",
        "content": user_content,
        "timestamp": str(__import__("datetime").datetime.utcnow()),
    })
    await db.execute(
        "UPDATE discussion_sessions SET responses = responses || $2::jsonb WHERE id=$1",
        session_id, user_entry,
    )

    pid = await auth.resolve_project_id(workspace, project, principal, access="write")
    topic = row["topic"]
    model_keys = [row["control_model"]] + list(row["discussion_models"])

    import asyncio
    asyncio.ensure_future(_continue_discussion(
        session_id, pid, principal.username, topic, model_keys, rate_limit_delay, rate_limit_retries,
    ))

    return {"ok": True, "message": "讨论已继续"}


@mcp.tool(name="discussion_room.apply_results")
async def discussion_room_apply_results(
    workspace: str, project: str, session_id: str,
) -> dict[str, Any]:
    """将讨论结果应用到知识库，创建待审批提案。"""
    import re, json
    principal = await get_principal("write")
    logger.info("discussion_room.apply_results: %s", session_id)
    row = await db.fetchrow(
        "SELECT * FROM discussion_sessions WHERE id = $1", session_id,
    )
    if not row:
        return {"ok": False, "error": "session not found"}
    if not row["consensus_reached"]:
        return {"ok": False, "error": "尚未达成共识"}
    if not row["summary"]:
        return {"ok": False, "error": "总结为空"}

    pid = await auth.resolve_project_id(workspace, project, principal, access="write")

    # Ensure DB columns exist
    for col in ["backup_snapshots", "session_id", "affected_tables"]:
        await db.execute(f"""
            DO $$ BEGIN
                IF NOT EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name='system_evolution_proposals' AND column_name='{col}') THEN
                    ALTER TABLE system_evolution_proposals ADD COLUMN {col} {'jsonb' if col == 'backup_snapshots' else 'text' if col == 'session_id' else 'text[]'};
                END IF;
            END $$;
        """)

    # Extract JSON items from summary (data changes — auto execute)
    items = []
    m_data = re.search(r'```json\s*(\{.*?\})\s*```', row["summary"], re.DOTALL)
    if m_data:
        try:
            parsed = json.loads(m_data.group(1))
            category = parsed.get("category", "通用")
            items = parsed.get("items", [])
        except json.JSONDecodeError:
            pass

    # Extract schema changes from summary (admin review only — not executed)
    schema_changes = []
    m_schema = re.search(r'```schema\s*(\{.*?\})\s*```', row["summary"], re.DOTALL)
    if m_schema:
        try:
            sp = json.loads(m_schema.group(1))
            schema_changes = sp.get("changes", [])
        except json.JSONDecodeError:
            pass

    if not items and not schema_changes:
        return {"ok": False, "error": "总结中未找到有效的 JSON 知识条目或 schema 变更"}

    backup_snapshots = {}
    applied_items = []
    errors = []

    for item in items:
        item_name = item.get("name", "")
        item_type = item.get("type", "knowledge")
        item_desc = item.get("description", "")

        # Handle category creation first
        if item_type == "category":
            try:
                slug = item.get("slug", item_name)[:50]
                parent_slug = item.get("parent_slug", "")
                cat_desc = item_desc or item.get("description", "")
                # Find parent_id if parent_slug provided
                parent_id = None
                if parent_slug:
                    p = await db.fetchrow("SELECT id FROM ref_categories WHERE slug=$1", parent_slug)
                    if p:
                        parent_id = p["id"]
                # Upsert category
                existing = await db.fetchrow("SELECT id FROM ref_categories WHERE slug=$1", slug)
                if existing:
                    await db.execute("UPDATE ref_categories SET name=$1, description=$2, parent_id=$3 WHERE id=$4",
                                     item_name[:100], cat_desc, parent_id, existing["id"])
                else:
                    await db.execute("INSERT INTO ref_categories (slug, name, description, parent_id) VALUES ($1, $2, $3, $4)",
                                     slug, item_name[:100], cat_desc, parent_id)
                applied_items.append(f"category:{slug}")
            except Exception as exc:
                errors.append(f"分类创建失败 {item_name}: {exc}")
            continue

        table = {"knowledge": "universal_knowledge", "setting": "setting_items", "rule": "canon_rules", "entity": "knowledge_entities", "state": "state_snapshots", "global_rule": "global_rules"}.get(item_type, "universal_knowledge")

        try:
            if table == "universal_knowledge":
                uk_cat = item.get("category_slug", category)[:50]
                # Find category_id
                cat_row = await db.fetchrow(
                    "SELECT id FROM ref_categories WHERE slug=$1 LIMIT 1", uk_cat,
                )
                cat_id = cat_row["id"] if cat_row else None
                # Backup
                old = await db.fetchrow(
                    "SELECT content, summary FROM universal_knowledge WHERE topic=$1",
                    item_name,
                )
                if old:
                    backup_snapshots.setdefault("universal_knowledge", {})[item_name] = {
                        "topic": item_name, "content": old["content"], "summary": old["summary"],
                    }
                # Upsert by topic
                old_row = await db.fetchrow("SELECT id FROM universal_knowledge WHERE topic=$1", item_name)
                if old_row:
                    await db.execute(
                        "UPDATE universal_knowledge SET content=$1, summary=$2, category_id=$3, source='discussion_room', updated_at=NOW() WHERE id=$4",
                        item_desc, item_desc[:200], cat_id, old_row["id"],
                    )
                else:
                    await db.execute(
                        "INSERT INTO universal_knowledge (topic, content, summary, category_id, source) VALUES ($1, $2, $3, $4, 'discussion_room')",
                        item_name, item_desc, item_desc[:200], cat_id,
                    )
                applied_items.append(f"{table}:{item_name}")

            elif table == "setting_items":
                # Allow item to specify category_slug, fallback to discussion category
                cat_slug = item.get("category_slug", category)
                cat_row = await db.fetchrow(
                    "SELECT id FROM setting_categories WHERE slug=$1 LIMIT 1",
                    cat_slug,
                )
                if not cat_row:
                    # Auto-create category if it doesn't exist
                    cat_id = str(__import__("uuid").uuid4())
                    ws_row = await db.fetchrow("SELECT id FROM workspaces WHERE slug=$1", workspace)
                    await db.execute(
                        "INSERT INTO setting_categories (id, workspace_id, slug, name) VALUES ($1, $2, $3, $4) ON CONFLICT DO NOTHING",
                        cat_id, ws_row["id"], cat_slug, cat_slug,
                    )
                    cat_row = await db.fetchrow(
                        "SELECT id FROM setting_categories WHERE slug=$1 LIMIT 1",
                        cat_slug,
                    )
                if not cat_row:
                    errors.append(f"分类创建失败: {cat_slug}")
                    continue
                old = await db.fetchrow(
                    "SELECT core_summary, level FROM setting_items WHERE item_code=$1",
                    item_name,
                )
                if old:
                    backup_snapshots.setdefault("setting_items", {})[item_name] = {
                        "item_code": item_name, "core_summary": old["core_summary"], "level": old["level"],
                    }
                await db.execute(
                    """INSERT INTO setting_items (workspace_id, category_id, item_code, core_summary, level, is_global)
                       VALUES ((SELECT id FROM workspaces WHERE slug=$1 LIMIT 1), $2, $3, $4, $5, true)
                       ON CONFLICT (workspace_id, item_code) DO UPDATE SET
                       core_summary=EXCLUDED.core_summary, level=EXCLUDED.level, category_id=EXCLUDED.category_id""",
                    workspace, cat_row["id"], item_name, item_desc,
                    {"knowledge": "knowledge", "setting": "knowledge", "rule": "knowledge"}.get(item_type, "knowledge"),
                )
                applied_items.append(f"{table}:{item_name}")

            elif table == "canon_rules":
                # Write to canon_rules (the proper rules table used by the frontend)
                rule_key = f"disc_{item_name[:50]}_{session_id[:8]}"
                old = await db.fetchrow(
                    "SELECT id, content, title FROM canon_rules WHERE project_id=$1 AND rule_key=$2",
                    pid, rule_key,
                )
                if old:
                    backup_snapshots.setdefault("canon_rules", {})[rule_key] = {
                        "rule_key": rule_key, "content": old["content"], "title": old["title"],
                    }
                    await db.execute(
                        "UPDATE canon_rules SET content=$1, title=$2, updated_at=NOW() WHERE id=$3",
                        item_desc, item_name[:200], old["id"],
                    )
                else:
                    await db.execute(
                        """INSERT INTO canon_rules (project_id, rule_key, rule_type, scope, title, content, status)
                           VALUES ($1, $2, 'discussion', 'system', $3, $4, 'active')""",
                        pid, rule_key, item_name[:200], item_desc,
                    )
                applied_items.append(f"{table}:{rule_key}")

            elif table == "knowledge_entities":
                entity_type = item.get("entity_type", "character")
                old_row = await db.fetchrow(
                    "SELECT id FROM knowledge_entities WHERE name=$1 AND entity_type=$2",
                    item_name, entity_type,
                )
                if old_row:
                    await db.execute(
                        "UPDATE knowledge_entities SET content=$1, summary=$2, source='discussion_room', updated_at=NOW() WHERE id=$3",
                        item_desc, item_desc[:200], old_row["id"],
                    )
                else:
                    await db.execute(
                        "INSERT INTO knowledge_entities (entity_type, name, content, summary, source) VALUES ($1, $2, $3, $4, 'discussion_room')",
                        entity_type, item_name, item_desc, item_desc[:200],
                    )
                applied_items.append(f"{table}:{item_name}")

            elif table == "state_snapshots":
                # state items reference existing entities
                entity_id = item.get("entity_id", "")
                chapter_no = item.get("chapter_no", 0)
                state_data = json_dumps(item.get("state", {}))
                await db.execute(
                    """INSERT INTO state_snapshots (project_id, entity_id, chapter_no, state, source_type, is_current)
                       VALUES ($1, $2, $3, $4::jsonb, 'discussion_room', true)""",
                    pid, entity_id, chapter_no, state_data,
                )
                applied_items.append(f"{table}:{item_name}")

            elif table == "global_rules":
                rule_key = f"disc_global_{item_name[:30]}_{session_id[:8]}"
                rule_type = item.get("rule_type", "creative")
                old_row = await db.fetchrow("SELECT id FROM global_rules WHERE rule_key=$1", rule_key)
                if old_row:
                    await db.execute(
                        "UPDATE global_rules SET title=$1, content=$2, rule_type=$3, updated_at=NOW() WHERE id=$4",
                        item_name[:200], item_desc, rule_type, old_row["id"],
                    )
                else:
                    await db.execute(
                        """INSERT INTO global_rules (rule_key, rule_type, title, content, severity, status, discussion_id)
                           VALUES ($1, $2, $3, $4, 'warning', 'active', $5)""",
                        rule_key, rule_type, item_name[:200], item_desc, session_id,
                    )
                applied_items.append(f"{table}:{rule_key}")

            # Gatekeeper log for global tables
            if table in ("global_rules", "universal_knowledge"):
                await gatekeeper_service.assess(
                    project_id=pid, action="INSERT" if item_type == "knowledge" else "UPDATE",
                    target_table=table, content={"name": item_name, "desc": item_desc[:200]},
                    source_type="discussion_room", source_id=session_id, created_by=principal.username,
                )

        except Exception as exc:
            errors.append(f"{item_name}: {exc}")
            logger.warning("apply item %s failed: %s", item_name, exc)

    # Create pending_admin proposal — use UUID-compatible id
    import uuid as _uuid
    proposal_id = str(_uuid.uuid4())
    desc_parts = []
    if applied_items:
        desc_parts.append(f"{len(applied_items)} 条数据变更")
    if schema_changes:
        desc_parts.append(f"{len(schema_changes)} 条结构变更（需管理员手动执行）")
    if errors:
        desc_parts.append(f"{len(errors)} 条错误")
    await db.execute(
        """INSERT INTO system_evolution_proposals
           (id, title, description, proposal_type, target_entity_type, proposed_content,
            evolution_reason, source_project_id, ai_submitter, status, backup_snapshots, session_id, affected_tables)
           VALUES ($1, $2, $3, $4, $5, $6::jsonb, $7, $8, $9, $10, $11::jsonb, $12, $13::text[])""",
        proposal_id,
        f"讨论室: {row['topic'][:50]}",
        "、".join(desc_parts) or f"来自讨论室 session {session_id}",
        "create", "setting_item",
        json.dumps({"summary": row["summary"], "applied_items": applied_items, "schema_changes": schema_changes, "errors": errors}),
        f"讨论室应用: {row['topic'][:30]}", pid, "discussion_room", "pending_admin",
        json.dumps(backup_snapshots), session_id, list(set(t.split(":")[0] for t in applied_items)),
    )

    # Audit log
    await db.execute(
        """INSERT INTO audit_logs (user_id, action, resource_type, resource_id, payload)
           VALUES ((SELECT id FROM users WHERE username=$1), 'discussion_apply', 'discussion_session', $2, $3::jsonb)""",
        principal.username if hasattr(principal, 'username') else "admin",
        session_id,
        json.dumps({"item_count": len(applied_items), "error_count": len(errors), "proposal_id": proposal_id}),
    )

    await db.execute(
        "UPDATE discussion_sessions SET status='pending_admin', updated_at=NOW() WHERE id=$1",
        session_id,
    )

    msg = f"已创建待审批提案 {proposal_id}，变更 {len(applied_items)} 条知识条目"
    if schema_changes:
        msg += f"，{len(schema_changes)} 条结构变更待手动处理"
    if errors:
        msg += f"，{len(errors)} 条失败"
    return {"ok": True, "message": msg, "proposal_id": proposal_id, "applied": len(applied_items), "schema_changes": len(schema_changes), "errors": len(errors)}


@mcp.tool(name="discussion_room.delete_session")
async def discussion_room_delete_session(
    workspace: str, project: str, session_id: str,
) -> dict[str, bool | str]:
    """彻底删除讨论会话及其所有数据。"""
    principal = await get_principal("write")
    logger.info("discussion_room.delete_session: %s", session_id)
    row = await db.fetchrow(
        "SELECT id FROM discussion_sessions WHERE id=$1 AND workspace=$2 AND project=$3",
        session_id, workspace, project,
    )
    if not row:
        return {"ok": False, "error": "session not found"}
    await db.execute("DELETE FROM discussion_sessions WHERE id=$1", session_id)
    return {"ok": True, "message": "已删除"}


# ========== Background Discussion Engine ==========

async def _append_response(session_id: str, role: str, model: str, phase: str, content: str) -> None:
    """向会话的 responses 数组追加一条记录。"""
    import json
    entry = json_dumps({
        "role": role, "model": model, "phase": phase,
        "content": content, "timestamp": str(__import__("datetime").datetime.utcnow()),
    })
    await db.execute(
        "UPDATE discussion_sessions SET responses = responses || $2::jsonb, updated_at=NOW() WHERE id=$1",
        session_id, entry,
    )


async def _update_phase(session_id: str, phase: str, round_num: int = 0, **kwargs) -> None:
    sets = ["phase=$2", "round=$3", "updated_at=NOW()"]
    params = [session_id, phase, round_num]
    idx = 4
    for k, v in kwargs.items():
        sets.append(f"{k}=${idx}")
        params.append(v)
        idx += 1
    await db.execute(
        f"UPDATE discussion_sessions SET {','.join(sets)} WHERE id=$1", *params,
    )
    # 讨论室完成后，自动同步关联的 review_job 状态
    if phase == "completed" and kwargs.get("status") == "completed":
        await db.execute(
            "UPDATE review_jobs SET status = 'aggregated', aggregated_at = NOW(), updated_at = NOW() WHERE session_id = $1",
            session_id,
        )


async def _query_data(project_id: str, source: str, **filters) -> list[dict]:
    """按 source 和 filters 查询知识库。返回行列表。"""
    try:
        if source == "entities":
            where = "project_id=$1"
            args = [project_id]
            idx = 2
            if filters.get("entity_type"):
                where += f" AND entity_type=${idx}"
                args.append(filters["entity_type"])
                idx += 1
            if filters.get("keywords"):
                where += f" AND (name ILIKE ${idx} OR summary ILIKE ${idx})"
                args.append(f"%{filters['keywords']}%")
                idx += 1
            rows = await db.fetch(
                f"SELECT entity_type, name, summary, tags, importance FROM state_entities WHERE {where} ORDER BY importance DESC LIMIT 50",
                *args,
            )
            return [dict(r) for r in rows]

        elif source == "pk":
            where = "project_id=$1"
            args = [project_id]
            idx = 2
            if filters.get("category"):
                where += f" AND category=${idx}"
                args.append(filters["category"])
                idx += 1
            if filters.get("keywords"):
                where += f" AND (key ILIKE ${idx} OR description ILIKE ${idx})"
                args.append(f"%{filters['keywords']}%")
                idx += 1
            rows = await db.fetch(
                f"SELECT category, key, description, tags FROM project_knowledge WHERE {where} LIMIT 50",
                *args,
            )
            return [dict(r) for r in rows]

        elif source == "items":
            where = "TRUE"
            args = []
            if filters.get("category"):
                where += " AND category_id=(SELECT id FROM setting_categories WHERE slug=$1 AND workspace='default')"
                args.append(filters["category"])
            if filters.get("keywords"):
                where += f" AND (core_summary ILIKE ${len(args)+1} OR item_code ILIKE ${len(args)+1})"
                args.append(f"%{filters['keywords']}%")
            rows = await db.fetch(
                f"SELECT item_code, core_summary, keywords, level FROM setting_items WHERE {where} LIMIT 50",
                *args,
            )
            return [dict(r) for r in rows]

        elif source == "uk":
            where = "TRUE"
            args = []
            if filters.get("category"):
                where += " AND uk.category_id=(SELECT id FROM ref_categories WHERE slug=$1)"
                args.append(filters["category"])
            if filters.get("keywords"):
                idx = len(args) + 1
                where += f" AND (uk.topic ILIKE ${idx} OR uk.content ILIKE ${idx} OR uk.summary ILIKE ${idx})"
                args.append(f"%{filters['keywords']}%")
            rows = await db.fetch(
                f"SELECT uk.topic, uk.summary, uk.content, uk.tags, rc.slug as category_slug FROM universal_knowledge uk LEFT JOIN ref_categories rc ON rc.id = uk.category_id WHERE {where} LIMIT 20",
                *args,
            )
            return [dict(r) for r in rows]

        elif source == "schema":
            table = filters.get("table", "")
            if not table:
                return []
            rows = await db.fetch(
                "SELECT column_name, data_type, is_nullable, column_default FROM information_schema.columns WHERE table_name=$1 AND table_schema='public' ORDER BY ordinal_position",
                table,
            )
            return [dict(r) for r in rows]

        elif source == "docs":
            rows = await db.fetch(
                "SELECT doc_type, key, title FROM canon_documents WHERE project_id=$1 AND status='active' LIMIT 30",
                project_id,
            )
            return [dict(r) for r in rows]

        return []
    except Exception as exc:
        logger.warning("_query_data(%s) failed: %s", source, exc)
        return []


def _format_data(results: list[dict], label: str, fields: list[str]) -> str:
    """格式化查询结果为文本。"""
    if not results:
        return ""
    lines = [f"### {label}"]
    for r in results:
        parts = []
        for f in fields:
            v = r.get(f)
            if v:
                if isinstance(v, list):
                    v = ", ".join(v[:5])
                parts.append(f"{f}={v}")
        lines.append("- " + " ".join(parts))
    return "\n".join(lines)


async def _data_plan_to_queries(project_id: str, plan_text: str) -> str:
    """解析控制模型的数据需求计划，执行查询，返回格式化结果。"""
    results = []
    for line in plan_text.split("\n"):
        line = line.strip()
        if line.startswith("NEED:"):
            parts = line[5:].strip().split()
            if not parts:
                continue
            source = parts[0].lower()
            filters = {}
            for p in parts[1:]:
                if "=" in p:
                    k, v = p.split("=", 1)
                    filters[k.strip()] = v.strip().strip('"').strip("'")
            rows = await _query_data(project_id, source, **filters)
            if source == "entities":
                formatted = _format_data(rows, f"实体 ({filters.get('entity_type','all')})", ["name", "entity_type", "importance", "summary"])
            elif source == "pk":
                formatted = _format_data(rows, f"项目知识 ({filters.get('category','all')})", ["category", "key", "description"])
            elif source == "items":
                formatted = _format_data(rows, f"设定条目 ({filters.get('keywords','all')})", ["item_code", "core_summary", "level"])
            elif source == "uk":
                formatted = _format_data(rows, f"通用知识 ({filters.get('keywords','all')})", ["topic", "summary", "category_slug"])
            elif source == "schema":
                formatted = _format_data(rows, f"表结构 ({filters.get('table','')})", ["column_name", "data_type", "is_nullable", "column_default"])
            elif source == "docs":
                formatted = _format_data(rows, "设定文档", ["doc_type", "key", "title"])
            else:
                formatted = ""
            if formatted:
                results.append(formatted)
    # Auto-fallback: if all NEED queries returned empty, try keyword scan across all sources
    if not results:
        import re
        # Extract Chinese keywords from the plan text
        keywords = re.findall(r'[\u4e00-\u9fff]{2,}', plan_text)
        keyword = keywords[0] if keywords else ""
        if keyword:
            fallback_sources = [
                ("docs", {}),
                ("entities", {"keywords": keyword}),
                ("pk", {"keywords": keyword}),
                ("items", {"keywords": keyword}),
                ("uk", {"keywords": keyword}),
            ]
            for fb_source, fb_filters in fallback_sources:
                rows = await _query_data(project_id, fb_source, **fb_filters)
                if rows:
                    if fb_source == "entities":
                        formatted = _format_data(rows, f"实体 ({keyword})", ["name", "entity_type", "importance", "summary"])
                    elif fb_source == "pk":
                        formatted = _format_data(rows, f"项目知识 ({keyword})", ["category", "key", "description"])
                    elif fb_source == "items":
                        formatted = _format_data(rows, f"设定条目 ({keyword})", ["item_code", "core_summary", "level"])
                    elif fb_source == "uk":
                        formatted = _format_data(rows, f"通用知识 ({keyword})", ["topic", "summary", "category_slug"])
                    elif fb_source == "docs":
                        formatted = _format_data(rows, "设定文档", ["doc_type", "key", "title"])
                    else:
                        formatted = ""
                    if formatted:
                        results.append(f"⚠️ 系统补充查询（模型未明确请求，自动尝试）：\n{formatted}")
    return "\n\n".join(results) if results else ""


async def _run_discussion(
    session_id: str, project_id: str, user_id: str, topic: str, model_keys: list[str],
    delay: float, retries: int, data_source: str = "knowledge-entries",
    data_category: str | None = None,
    output_type: str = "knowledge",
) -> None:
    """完整讨论流程（新建）。"""
    import asyncio
    control = model_keys[0]
    discuss_models = model_keys[1:]

    # Data source hints
    cat_suffix = f"（分类: {data_category}）" if data_category else ""
    source_hints = {
        "canon": "本次讨论的数据来源是「Canon文档」。\n数据表: canon_documents\n类型字段: doc_type（如 premise/worldview/system）\n查询: NEED: docs  # 设定文档\n结构: NEED: schema table=canon_documents",
        "entities": "本次讨论的数据来源是「实体管理」。\n数据表: state_entities\n类型字段: entity_type（如 character/location/faction）\n查询: NEED: entities entity_type=类型 keywords=关键词\n结构: NEED: schema table=state_entities",
        "rules": "本次讨论的数据来源是「创作规则」。\n数据表: canon_rules\n类型字段: rule_type（如 character/plot/world）\n查询: NEED: items category=角色模板\n结构: NEED: schema table=canon_rules",
        "knowledge-entries": "本次讨论的数据来源是「知识条目」" + cat_suffix + "。\n数据表: universal_knowledge\n分类表: ref_categories（slug 作分类标识）\n查询: NEED: uk category=分类slug keywords=关键词\n结构: NEED: schema table=universal_knowledge\n分类结构: NEED: schema table=ref_categories",
        "genres": "本次讨论的数据来源是「题材策略」。\n数据表: genre_knowledge_config + genre_canonical\n结构: NEED: schema table=genre_knowledge_config\n结构: NEED: schema table=genre_canonical",
        "relations": "本次讨论的数据来源是「实体关系」。\n数据表: knowledge_entities + knowledge_relations\n结构: NEED: schema table=knowledge_relations",
        "materials": "本次讨论的数据来源是「参考素材」。\n数据表: reference_materials + reference_sources\n结构: NEED: schema table=reference_materials",
    }
    source_context = source_hints.get(data_source, source_hints["knowledge-entries"])

    system_context = (
        "你是 Novel OS 讨论室的控制模型。你运行在多模型讨论后台，输出直接传给其他 AI 模型，用户看不到。\n\n"
        f"{source_context}\n\n"
        "## 你的职责\n"
        "1. 分析话题，输出 NEED 行请求数据\n"
        "2. 收到数据后，直接输出分析结论和讨论议题\n"
        "3. 引导讨论模型提建议\n"
        "4. 讨论结束后生成共识\n\n"
        "## 重要规则\n"
        "- 你的输出给其他 AI 模型看，不是给用户看。直接分析，不要提问或征求意见。\n"
        "- 如果所有数据源都查不到，告知用户数据不存在，询问是否需要创建。\n"
        "- 需要写入知识库时，先用 `NEED: schema table=目标表名` 查询表结构，再在 JSON 中指定正确的列名。\n"
        "- 判断是否需要涉及分类讨论：如果话题涉及分类/结构/整理，可先查分类树再查数据；否则直接查数据。\n\n"
        "## 可输出的 JSON type 说明\n"
        '```\n'
        "type=category  # 创建分类（需提供 slug, name, parent_slug, description）\n"
        "type=knowledge # 写入 universal_knowledge（通用知识条目）\n"
        "type=setting   # 写入 setting_items（设定条目）\n"
        "type=rule      # 写入 canon_rules（创作规则）\n"
        '```\n'
        "## 通用查询（所有来源均可使用）\n"
        '```\n'
        "NEED: schema table=上面列出的表名  # 查结构时用上面写的表名，不要猜\n"
        '```\n'
        "请根据上方的数据来源说明输出对应的 NEED 行。查表结构时务必使用上面列出的确切表名，不要自己编造表名："
    )
    # Phase -1: Topic analysis
    topic_analysis = await _call(user_id, control, [
        {"role": "system", "content": "你是 Novel OS 讨论室的话题分析模型。你的任务是在用户发起话题后，先理解意图，不要查询数据，不要输出 NEED 行。\n\n分析以下三个方面：\n1. 用户的核心意图是什么？（完善设定/审查知识/规划情节/补充知识/解决创作问题）\n2. 话题是否涉及分类或结构问题？如果涉及，需要查看分类树；否则直接关注数据内容。\n3. 后续讨论的重点方向是什么？"},
        {"role": "user", "content": topic},
    ], delay, retries)
    analysis_text = topic_analysis.get("text", "")
    await _append_response(session_id, "control", control, "topic_analysis", analysis_text)

    # Phase 0: Control model requests data
    plan_resp = await _call(user_id, control, [
        {"role": "system", "content": system_context},
        {"role": "user", "content": topic},
    ], delay, retries)
    plan_text = plan_resp.get("text", "")
    await _append_response(session_id, "control", control, "data_plan", plan_text)

    # Execute queries based on plan
    queried_data = await _data_plan_to_queries(project_id, plan_text)

    # Phase 1: Control model analyzes with data
    analysis = await _call(user_id, control, [
        {"role": "system", "content": "你是讨论控制模型。以下是系统根据你的数据需求查询到的结果：" + (f"\n\n{queried_data}" if queried_data else "\n\n(未找到相关数据)") + "\n\n基于这些数据直接输出分析结论和讨论议题。你的输出给其他 AI 模型看，不要提问。"},
        {"role": "user", "content": topic},
    ], delay, retries)
    text = analysis.get("text", "")
    await _append_response(session_id, "control", control, "analyze", text)

    # Phase 2: Proposal round
    data_context = f"\n\n查询到的数据：\n{queried_data}" if queried_data else ""
    prompt = f"话题：{topic}\n控制模型分析：{text}{data_context}\n\n请提出你的完整建议。"

    # Proposal system prompt: different for knowledge vs review
    if output_type == "review":
        proposal_system = "你是小说创作审查专家。请审查设定完备性，逐条指出遗漏的角色、地点、势力、伏笔或设定矛盾。每条缺项说明：缺什么、为什么需要、建议如何补充。如无遗漏请明确说「无遗漏」。"
    else:
        proposal_system = "你是小说创作知识库专家。请输出具体、可操作的知识条目建议，包含分类归属。"

    objections_history = []
    max_rounds = 10

    for main_round in range(max_rounds):
        # Phase 2: Proposals (skip on subsequent rounds, only discuss disputes)
        if main_round == 0:
            for mk in discuss_models:
                r = await _call(user_id, mk, [
                    {"role": "system", "content": proposal_system},
                    {"role": "user", "content": prompt},
                ], delay, retries)
                await _append_response(session_id, "discuss", mk, "propose", r.get("text", ""))
                await asyncio.sleep(delay)
        else:
            # Re-propose: only discuss remaining disputes
            dispute_ctx = "\n\n".join([f"争议 {i+1}: {d}" for i, d in enumerate(objections_history[-1])])
            for mk in discuss_models:
                r = await _call(user_id, mk, [
                    {"role": "system", "content": proposal_system},
                    {"role": "user", "content": f"话题：{topic}\n\n待解决的争议：\n{dispute_ctx}\n\n请针对每个争议点给出你的意见。"},
                ], delay, retries)
                await _append_response(session_id, "discuss", mk, "repropose", r.get("text", ""))
                await asyncio.sleep(delay)

        # Phase 3: Control model creates interim summary of all proposals
        resp_rows = await db.fetch(
            "SELECT responses FROM discussion_sessions WHERE id=$1", session_id,
        )
        all_resp = resp_rows[0]["responses"] if resp_rows else []
        if isinstance(all_resp, str):
            all_resp = json.loads(all_resp)

        recent = [r for r in all_resp if r.get("phase") in ("propose", "repropose", "analyze")]
        merged_recent = "\n\n".join([f"--- {r['model']} ---\n{r['content']}" for r in recent[-6:]])

        # Summary prompt: different for knowledge vs review
        if output_type == "review":
            summary_system = (
                '你是讨论归纳模型。汇总各审查模型对设定完备性的审查意见，给出最终审查结论。\n\n'
                '输出格式要求：\n'
                '1. 首行必须是「结论：完备」或「结论：不完备」\n'
                '2. 如不完备，按类别逐条列出所有缺项：\n'
                '   - 角色遗漏：[角色名] [原因] [建议]\n'
                '   - 地点遗漏：[地点名] [原因] [建议]\n'
                '   - 势力遗漏：[势力名] [原因] [建议]\n'
                '   - 伏笔遗漏：[伏笔描述] [原因] [建议]\n'
                '   - 设定矛盾：[矛盾描述] [原因] [建议]\n'
                '3. 如果是"完备"，简要说明理由（1-2句）\n'
                '4. 不要输出任何 JSON 块或代码块'
            )
        else:
            summary_system = (
                '你是讨论归纳模型。汇总各模型的最新提议，输出一份**纯共识草案**。\n\n'
                '规则：\n'
                '1. 必须解决前面轮次中审阅模型提出的所有异议，给出各方都能接受的方案\n'
                '2. 只包含各模型基本达成一致的结论，有分歧取多数派立场\n'
                '3. 不要列出"分歧点"或"异议"\n'
                '4. 这份草案将交由各模型审阅，他们还会继续提出异议，直到所有异议都解决\n'
                '5. 如果草案包含 ` ```schema ` 表结构变更，则后续 ` ```json ` 知识条目**应基于变更后的表结构设计**（假设变更已生效）\n\n'
                '在草案末尾，按需输出以下 JSON 块：\n\n'
                '1. 知识数据变更（自动执行）：\n'
                '```json\n'
                '{\n  "category": "分类slug",\n  "items": [\n    {"name": "条目名", "description": "内容描述", "type": "knowledge/setting/rule/entity/state/global_rule/category"}\n  ]\n}\n'
                '```\n\n'
                '2. 表结构变更（需管理员手动执行，如无则省略此块）：\n'
                '```schema\n'
                '{\n  "changes": [\n    {"table": "表名", "action": "add_column/drop_column/alter_type", "column": "字段名", "type": "字段类型", "reason": "变更原因"}\n  ]\n}\n'
                '```'
            )

        interim_summary = await _call(user_id, control, [
            {"role": "system", "content": summary_system},
            {"role": "user", "content": f"话题：{topic}\n\n各模型提议：\n{merged_recent}\n\n请输出纯共识草案，必须解决上一轮审阅中提出的所有异议。"},
        ], delay, retries)
        interim_text = interim_summary.get("text", "")
        await _append_response(session_id, "control", control, "consolidate", interim_text)

        # Phase 4: Review models check the interim summary
        objections = []
        objection_texts = []
        review_models = ROTATION[main_round % len(ROTATION)]
        for mk in review_models:
            r = await _call(user_id, mk, [
                {"role": "system", "content": "审阅讨论归纳。如果完全同意回复「无异议」，否则逐条指出你不同意的具体内容和理由。讨论会继续直到所有异议解决，请务必诚实地指出所有你不同意的地方。"},
                {"role": "user", "content": f"审阅以下关于「{topic}」的讨论归纳：\n\n{interim_text}"},
            ], delay, retries)
            text = r.get("text", "")
            # Check for explicit objection indicators first
            has_obj = any(p in text.lower() for p in ["不同意", "有争议", "需要修改", "需要调整", "有不同意见", "持保留意见"])
            if not has_obj:
                # Only check approval keywords if no explicit objection found
                has_obj = not any(kw in text.lower() for kw in ["无异议", "没有异议", "同意", "no objection", "i agree"])
            await _append_response(
                session_id, "reviewer" if has_obj else "approver", mk, f"review_r{main_round+1}", text,
            )
            if has_obj:
                objections.append(mk)
                objection_texts.append(f"[{mk}] {text[:200]}")
            await asyncio.sleep(delay)

        objections_history.append(objection_texts)

        if not objections:
            # No objections → interim_summary becomes final
            summary_text = interim_text
            consensus = True
            break
    else:
        # Max rounds reached, use last interim summary as final
        summary_text = interim_text
        consensus = False

    await _update_phase(session_id, "completed", round_num=main_round + 1,
                        status="completed", consensus_reached=consensus,
                        summary=summary_text)
    logger.info("Session %s completed, consensus=%s, rounds=%d", session_id, consensus, main_round + 1)


async def _continue_discussion(
    session_id: str, project_id: str, user_id: str, topic: str, model_keys: list[str],
    delay: float, retries: int,
) -> None:
    """续传讨论（从当前 phase 继续）。"""
    import asyncio, json
    row = await db.fetchrow(
        "SELECT phase, round, responses, history FROM discussion_sessions WHERE id=$1", session_id,
    )
    if not row:
        return
    phase = row["phase"]
    responses = row["responses"]
    if isinstance(responses, str):
        responses = json.loads(responses)

    control = model_keys[0]
    discuss_models = model_keys[1:]

    # Read data_source and output_type from history
    history = row["history"]
    if isinstance(history, str):
        history = json.loads(history)
    data_source = (history or {}).get("data_source", "knowledge-entries")
    output_type = (history or {}).get("output_type", "knowledge")

    if phase == "analyzing":
        # 直接跑 proposal
        pass
    elif phase == "proposing":
        # 检查缺少哪些模型的 proposal
        existing_models = {r["model"] for r in responses if r["phase"] == "propose"}
        for mk in discuss_models:
            if mk not in existing_models:
                res_proposal_system = "你是小说创作审查专家。请审查设定完备性，逐条指出遗漏。" if output_type == "review" else "你是小说创作知识库专家。"
                r = await _call(user_id, mk, [
                    {"role": "system", "content": res_proposal_system},
                    {"role": "user", "content": f"话题：{topic}\n请提出你的完整建议。"},
                ], delay, retries)
                await _append_response(session_id, "discuss", mk, "propose", r.get("text", ""))
                await asyncio.sleep(delay)
    elif phase.startswith("review"):
        # 已有部分 objections，继续审阅后续模型
        pass  # 简化：直接重新跑一轮 review

    # 后续跑 review rounds + summary（同 _run_discussion）
    # 为简化实现，直接调用完整流程的分析+提议阶段（已有 responses 会被追加但无影响）
    # 更优方案：检测断点精确恢复
    await _run_discussion(session_id, project_id, user_id, topic, model_keys, delay, retries, data_source, None, output_type)


async def _call(
    user_id: str, model: str, messages: list[dict], delay: float, max_retries: int,
) -> dict:
    """调用模型，带限流和重试。"""
    import asyncio
    for attempt in range(max_retries + 1):
        try:
            return await llm_client.chat_with_profile(
                user_id, model, messages, temperature=0.3, max_tokens=4096,
            )
        except Exception as e:
            err = str(e)
            if "429" in err and attempt < max_retries:
                wait = 10 * (attempt + 1)
                logger.warning("429 for %s, retry %d after %ds", model, attempt + 1, wait)
                await asyncio.sleep(wait)
            else:
                logger.warning("Model %s failed: %s", model, err)
                return {"text": f"[模型调用失败: {err[:100]}]"}
        finally:
            await asyncio.sleep(delay)
    return {"text": "[重试耗尽]"}