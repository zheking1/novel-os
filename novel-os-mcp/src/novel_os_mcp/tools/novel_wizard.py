"""Novel Creation Wizard - Interactive project setup for AI agents.

This module provides a conversational wizard for creating novel projects.
AI agents can call these tools to guide users through the setup process.
"""

from typing import Any
import logging
import uuid
import json
from datetime import datetime

from ..mcp_core import mcp
from ..deps import db, auth, workspace_service
from ..tool_auth import get_principal, validate_required

logger = logging.getLogger("novel_os_mcp.tools.novel_wizard")


# Default wizard questions for novel creation
DEFAULT_QUESTIONS = [
    {
        "id": "title",
        "question": "小说标题是什么？",
        "type": "text",
        "required": True,
        "placeholder": "例如：仙逆",
    },
    {
        "id": "genre",
        "question": "小说类型/题材是什么？",
        "type": "select",
        "required": True,
        "options": ["玄幻", "仙侠", "科幻", "奇幻", "武侠", "都市", "历史", "军事", "悬疑", "言情", "其他"],
    },
    {
        "id": "target_audience",
        "question": "目标读者群体是？",
        "type": "select",
        "required": True,
        "options": ["男性读者", "女性读者", "青少年", "全年龄"],
    },
    {
        "id": "premise",
        "question": "一句话概括故事核心（故事梗概）：",
        "type": "textarea",
        "required": True,
        "placeholder": "例如：一个平凡少年获得神秘法宝，踏上逆天改命的修仙之路...",
    },
    {
        "id": "world_setting",
        "question": "故事发生的世界/时代背景是？",
        "type": "textarea",
        "required": True,
        "placeholder": "例如：修真世界，强者为尊，凡人可修炼成仙...",
    },
    {
        "id": "protagonist",
        "question": "主角的基本信息（姓名、性格、目标）：",
        "type": "textarea",
        "required": True,
        "placeholder": "例如：王林，坚毅执着，为了复活亲人而修仙...",
    },
    {
        "id": "power_system",
        "question": "修炼/力量体系是什么？（如果有）",
        "type": "textarea",
        "required": False,
        "placeholder": "例如：炼气→筑基→金丹→元婴→化神→炼虚→合体→大乘→渡劫",
    },
    {
        "id": "tone_style",
        "question": "故事基调和风格？",
        "type": "select",
        "required": True,
        "options": ["热血爽文", "暗黑压抑", "轻松搞笑", "悬疑烧脑", "虐心催泪", "正剧严肃"],
    },
    {
        "id": "estimated_length",
        "question": "预计总字数？",
        "type": "select",
        "required": True,
        "options": ["50万字以下", "50-100万字", "100-200万字", "200-500万字", "500万字以上"],
    },
]


@mcp.tool(name="novel.wizard.start")
async def novel_wizard_start() -> dict[str, Any]:
    """启动小说创建向导，返回问题列表。"""
    principal = await get_principal("read")
    wizard_id = str(uuid.uuid4())
    logger.info(f"novel_wizard_start: {wizard_id}")
    
    # 查询已有工作区
    workspaces = await workspace_service.list_workspaces()
    
    # 构建工作区选择选项
    ws_options = []
    for ws in workspaces:
        ws_options.append({
            "label": f"{ws['name']} ({ws['slug']})",
            "value": f"existing:{ws['slug']}",
        })
    ws_options.append({"label": "新建工作区", "value": "new"})
    
    workspace_question = {
        "id": "workspace_selection",
        "question": "项目放在哪个工作区？",
        "type": "select",
        "required": True,
        "options": ws_options,
    }
    
    # 如果选了新建，需要额外输入
    workspace_new_question = {
        "id": "workspace_new_slug",
        "question": "新建工作区的标识（slug，如 my-novels）：",
        "type": "text",
        "required": False,
        "placeholder": "留空则用 default",
    }
    
    return {
        "wizard_id": wizard_id,
        "questions": [workspace_question, workspace_new_question] + DEFAULT_QUESTIONS,
        "message": "请根据以下问题收集用户信息。先询问工作区选择，完成后调用 novel.wizard.generate",
        "workflow_guide": {
            "mode": "strict",
            "steps": [
                {
                    "step_no": 1, "name": "收集用户回答",
                    "tool": "_agent_display",
                    "params": {"instruction": "向用户依次询问以下问题，收集完整答案。工作区：列出已有工作区让用户选或新建。书名：中文书名。题材：玄幻/都市/历史/科幻等。一句话梗概：核心冲突。世界观设定：时代背景、修炼体系等。主人公：姓名、特点。篇幅：100-200万字/200-400万字等。基调：热血爽文/暗黑压抑/轻松搞笑等"},
                    "next": "wait_user_confirm",
                },
                {
                    "step_no": 2, "name": "生成设定预览",
                    "tool": "novel.wizard.generate",
                    "params": {"wizard_id": wizard_id, "answers": "$from_step_1"},
                    "next": "next_step",
                },
            ],
        },
    }


@mcp.tool(name="novel.wizard.generate")
async def novel_wizard_generate(
    wizard_id: str,
    answers: dict[str, Any],
) -> dict[str, Any]:
    """根据用户回答生成小说设定预览。"""
    principal = await get_principal("read")
    logger.info(f"novel_wizard_generate: {wizard_id}")
    validate_required(locals(), "wizard_id", "answers")
    
    # Extract basic info
    title = answers.get("title", "未命名小说")
    genre = answers.get("genre", "玄幻")
    premise = answers.get("premise", "")
    world_setting = answers.get("world_setting", "")
    protagonist = answers.get("protagonist", "")
    power_system = answers.get("power_system", "")
    tone_style = answers.get("tone_style", "热血爽文")
    target_audience = answers.get("target_audience", "男性读者")
    estimated_length = answers.get("estimated_length", "100-200万字")
    
    # Generate project profile
    project_profile = {
        "title": title,
        "genre": genre,
        "target_audience": target_audience,
        "tone_style": tone_style,
        "estimated_length": estimated_length,
        "status": "active",
    }
    
    # Generate canon documents
    canon_documents = [
        {
            "doc_type": "premise",
            "key": "premise",
            "title": "故事梗概",
            "content": premise,
            "status": "active",
        },
        {
            "doc_type": "worldview",
            "key": "worldview",
            "title": "世界观设定",
            "content": world_setting,
            "status": "active",
        },
    ]
    
    if power_system:
        canon_documents.append({
            "doc_type": "power_system",
            "key": "power_system",
            "title": "修炼体系",
            "content": power_system,
            "status": "active",
        })
    
    # Parse protagonist info (simple extraction)
    protagonist_name = protagonist.split("，")[0].split(",")[0].strip() if protagonist else "主角"
    if not protagonist_name:
        protagonist_name = "主角"
    
    # Generate initial entities
    initial_entities = [
        {
            "entity_type": "character",
            "name": protagonist_name,
            "aliases": [],
            "importance": "high",
            "profile": {
                "role": "protagonist",
                "description": protagonist,
            },
        },
    ]
    
    # Generate plot threads
    plot_threads = [
        {
            "key": "main",
            "title": f"{protagonist_name}的主线故事",
            "thread_type": "main",
            "importance": "high",
            "status": "open",
        },
    ]
    
    # Generate initial rules based on tone/style
    initial_rules = _generate_rules_by_tone(tone_style)
    
    # 推荐系统级配置
    recommended_configs = await _recommend_system_configs(
        genre=genre,
        tone=tone_style,
        length=estimated_length
    )
    
    return {
        "wizard_id": wizard_id,
        "preview": {
            "project_profile": project_profile,
            "canon_documents": canon_documents,
            "initial_entities": initial_entities,
            "plot_threads": plot_threads,
            "initial_rules": initial_rules,
        },
        "recommendations": {
            "style_profiles": recommended_configs.get('style_profiles', []),
            "prompt_templates": recommended_configs.get('prompt_templates', []),
            "model_profiles": recommended_configs.get('model_profiles', []),
        },
        "message": "以上是根据用户回答生成的初始设定。请展示给用户确认。",
        "workflow_guide": {
            "mode": "strict",
            "steps": [
                {
                    "step_no": 1, "name": "展示设定预览并等用户确认",
                    "tool": "_agent_display",
                    "params": {"instruction": "展示以下设定预览给用户：书名、题材、梗概、世界观、主人公、篇幅、基调。包含推荐的系统配置（风格/模板/模型）。用户确认后进入下一步。"},
                    "next": "wait_user_confirm",
                },
                {
                    "step_no": 2, "name": "创建项目",
                    "tool": "novel.wizard.commit",
                    "params": {
                        "wizard_id": wizard_id,
                        "workspace": "$from_answers.workspace",
                        "project_slug": "$from_answers.project_slug",
                        "preview": "$preview",
                        "confirm": True,
                    },
                    "next": "next_step",
                },
            ],
        },
    }


def _generate_rules_by_tone(tone_style: str) -> list[dict]:
    """根据故事基调生成初始规则。"""
    rules = [
        {
            "rule_type": "global",
            "title": "禁止事项",
            "content": "主角不能死亡，世界观设定不能自相矛盾",
            "severity": "critical",
        },
    ]
    
    if tone_style == "热血爽文":
        rules.append({
            "rule_type": "style",
            "title": "节奏控制",
            "content": "每章必须有爽点或反转，保持高密度情节推进",
            "severity": "warning",
        })
    elif tone_style == "暗黑压抑":
        rules.append({
            "rule_type": "style",
            "title": "氛围营造",
            "content": "保持压抑紧张的氛围，适当穿插希望之光避免读者弃书",
            "severity": "info",
        })
    elif tone_style == "轻松搞笑":
        rules.append({
            "rule_type": "style",
            "title": "幽默元素",
            "content": "适当加入轻松幽默的对话和情节，避免过度沉重的描写",
            "severity": "info",
        })
    
    return rules


@mcp.tool(name="novel.wizard.commit")
async def novel_wizard_commit(
    wizard_id: str,
    workspace: str,
    project_slug: str,
    preview: dict[str, Any],
    confirm: bool = True,
    workspace_action: str = "existing",
    workspace_name: str | None = None,
    selected_configs: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """确认并创建小说项目。
    
    用户确认设定后，AI Agent调用此工具实际创建项目。
    支持选择已有工作区或自动新建工作区。
    
    Args:
        wizard_id: 向导会话ID
        workspace: 工作空间slug（已有的或新建的）
        project_slug: 项目slug（短标识符，如 xianni）
        preview: 来自 novel.wizard.generate 的 preview 数据
        confirm: 必须设为 True 确认创建
        workspace_action: "existing" 使用已有工作区, "new" 自动创建工作区
        workspace_name: 新建工作区时的显示名称，留空则用 workspace slug
        
    Returns:
        {
            "ok": True,
            "project_id": "...",
            "workspace": "...",
            "project": "...",
            "message": "项目创建成功",
            "next_steps": [...]  # 建议的下一步操作
        }
    """
    principal = await get_principal("write")
    logger.info(f"novel_wizard_commit: {wizard_id} -> {workspace}/{project_slug} (action={workspace_action})")
    validate_required(locals(), "wizard_id", "workspace", "project_slug", "preview")
    
    if not confirm:
        raise ValueError("confirm must be True to create project")
    
    # 根据 action 处理 workspace
    if workspace_action == "new":
        # 自动创建工作区
        ws_name = workspace_name or workspace
        logger.info(f"Creating workspace: {workspace} ({ws_name})")
        await workspace_service.create_workspace(
            slug=workspace, name=ws_name, owner_username=principal.username
        )
    else:
        # 使用已有工作区，检查访问权限
        await auth.require_workspace_access(principal, workspace)
    
    # Extract data from preview
    project_profile = preview.get("project_profile", {})
    canon_documents = preview.get("canon_documents", [])
    initial_entities = preview.get("initial_entities", [])
    plot_threads = preview.get("plot_threads", [])
    initial_rules = preview.get("initial_rules", [])
    
    title = project_profile.get("title", project_slug)
    
    # Create project
    project_result = await workspace_service.create_project(
        workspace_slug=workspace,
        project_slug=project_slug,
        title=title,
        description=project_profile.get("genre", ""),
        owner_username=principal.username,
    )
    
    project_id = project_result.get("id")
    
    # Create canon documents
    for doc in canon_documents:
        await _create_canon_doc(project_id, workspace, project_slug, doc)
    
    # Create entities
    for entity in initial_entities:
        await _create_entity(project_id, workspace, project_slug, entity)
        # Also create initial character arc and relationship for protagonist
        if entity.get("entity_type") == "character" and entity.get("name"):
            await _create_initial_arc(project_id, entity["name"])
    
    # Create world state snapshot
    await _create_world_state(project_id, project_profile, canon_documents)
    
    # Create plot threads
    for thread in plot_threads:
        await _create_plot_thread(project_id, workspace, project_slug, thread)
    
    # Create initial rules
    for rule in initial_rules:
        await _create_rule(project_id, workspace, project_slug, rule)
    
# Create initial volume (minimal — AI tool can add more detail)
    await _create_initial_volume(project_id, workspace, project_slug,
                                 estimated_length=project_profile.get("estimated_length", "100-200万字"),
                                 genre=project_profile.get("genre", "玄幻"),
                                 tone=project_profile.get("tone_style", "热血爽文"))

    # Import system configs if selected
    config_import_results = None
    if selected_configs:
        config_import_results = await _fork_system_configs_to_project(
            project_id=project_id,
            workspace=workspace,
            project_slug=project_slug,
            selected_configs=selected_configs,
            principal=principal
        )
    
    ws_msg = f"工作区「{workspace}」" if workspace_action == "new" else f"工作区「{workspace}」"
    
    # 构建返回消息
    message = f"小说项目《{title}》创建成功！（{ws_msg}）"
    if config_import_results:
        imported_count = (
            config_import_results.get("style_profiles_imported", 0) +
            config_import_results.get("templates_imported", 0) +
            config_import_results.get("model_profiles_imported", 0)
        )
        if imported_count > 0:
            message += f" 已导入 {imported_count} 个系统配置。"
    
    result = {
        "ok": True,
        "project_id": project_id,
        "workspace": workspace,
        "project": project_slug,
        "title": title,
        "message": message,
        "config_import": config_import_results,
        "next_steps": [
            f"1. 调 novel.wizard.build_world(workspace='{workspace}', project='{project_slug}') 启动全自动世界构建",
            f"2. 系统会引导你逐步完成：卷纲 → 逐卷深挖 → 全局检查 → 章节大纲",
            f"3. 全部完成后开始写作章节",
        ],
        "workflow_guide": {
            "mode": "strict",
            "steps": [
                {
                    "step_no": 1, "name": "启动世界构建",
                    "tool": "novel.wizard.build_world",
                    "params": {"workspace": workspace, "project": project_slug},
                    "next": "next_step",
                },
            ],
        },
        "local_dir_hint": {
            "message": f"请在本地创建小说项目目录 {project_slug}，用于存放章节正文文件",
            "suggested_structure": {
                "project_root": f"./{project_slug}/",
                "chapter_folders": "第01章/、第02章/、...",
                "chapter_files": "ch01_draft.md、ch01_outline.md、ch01_review.md",
                "outline_files": "ch01_outline.md",
                "revision_files": "第01章/审查报告/",
            },
        },
    }
    
    if config_import_results and config_import_results.get("errors"):
        result["warnings"] = config_import_results["errors"]
    
    return result


async def _create_canon_doc(project_id: str, workspace: str, project: str, doc: dict) -> None:
    """Helper to create canon document."""
    from ..deps import db
    import hashlib
    try:
        content = doc.get("content", "")
        content_hash = hashlib.md5(content.encode()).hexdigest()
        await db.execute(
            """
            INSERT INTO canon_documents (project_id, doc_type, key, title, content, content_hash, status, source_type)
            VALUES ($1, $2, $3, $4, $5, $6, 'active', 'wizard')
            ON CONFLICT (project_id, doc_type, key) DO UPDATE SET
                title = EXCLUDED.title,
                content = EXCLUDED.content,
                content_hash = EXCLUDED.content_hash,
                status = EXCLUDED.status,
                updated_at = now()
            """,
            project_id,
            doc.get("doc_type"),
            doc.get("key"),
            doc.get("title"),
            content,
            content_hash,
        )
    except Exception as e:
        logger.warning(f"Failed to create canon doc: {e}")


async def _create_entity(project_id: str, workspace: str, project: str, entity: dict) -> None:
    """Helper to create entity with initial state snapshot."""
    from ..deps import db
    try:
        profile_str = json.dumps(entity.get("profile", {}), ensure_ascii=False)
        row = await db.fetchrow(
            """
            INSERT INTO state_entities (project_id, entity_type, name, aliases, summary, description, tags,
                                        importance, profile, lifecycle_status,
                                        first_seen_chapter_no, last_seen_chapter_no)
            VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9::jsonb, 'active', 1, 1)
            ON CONFLICT (project_id, entity_type, name) DO UPDATE SET
                aliases = EXCLUDED.aliases,
                summary = COALESCE(EXCLUDED.summary, state_entities.summary),
                description = COALESCE(EXCLUDED.description, state_entities.description),
                tags = CASE WHEN $7 IS NULL THEN state_entities.tags ELSE EXCLUDED.tags END,
                importance = EXCLUDED.importance,
                profile = EXCLUDED.profile,
                updated_at = now()
            RETURNING id
            """,
            project_id,
            entity.get("entity_type"),
            entity.get("name"),
            entity.get("aliases", []),
            entity.get("summary"),
            entity.get("description"),
            entity.get("tags"),
            entity.get("importance", "medium"),
            profile_str,
        )
        # Create initial state snapshot
        if row:
            entity_id = row["id"]
            await db.execute(
                """
                INSERT INTO state_snapshots (project_id, entity_id, state, is_current,
                                             effective_chapter_no, change_reason, source_type, duration_type)
                VALUES ($1, $2, $3::jsonb, true, 1, '角色创建', 'wizard', 'persistent')
                ON CONFLICT DO NOTHING
                """,
                project_id, entity_id, profile_str,
            )
    except Exception as e:
        logger.warning(f"Failed to create entity: {e}")


async def _create_plot_thread(project_id: str, workspace: str, project: str, thread: dict) -> None:
    """Helper to create plot thread."""
    from ..deps import db
    try:
        await db.execute(
            """
            INSERT INTO plot_threads (project_id, key, title, thread_type, importance, status, start_chapter_no)
            VALUES ($1, $2, $3, $4, $5, $6, 1)
            ON CONFLICT (project_id, key) DO UPDATE SET
                title = EXCLUDED.title,
                thread_type = EXCLUDED.thread_type,
                importance = EXCLUDED.importance,
                updated_at = now()
            """,
            project_id,
            thread.get("key"),
            thread.get("title"),
            thread.get("thread_type", "side"),
            thread.get("importance", "medium"),
            thread.get("status", "open"),
        )
    except Exception as e:
        logger.warning(f"Failed to create plot thread: {e}")


async def _create_rule(project_id: str, workspace: str, project: str, rule: dict) -> None:
    """Helper to create rule in canon_rules table."""
    from ..deps import db
    try:
        rule_key = f"wizard_{rule.get('rule_type')}_{uuid.uuid4().hex[:8]}"
        await db.execute(
            """
            INSERT INTO canon_rules (project_id, rule_key, rule_type, title, content, severity, status, scope)
            VALUES ($1, $2, $3, $4, $5, $6, 'active', 'global')
            ON CONFLICT (project_id, rule_key) DO UPDATE SET
                title = EXCLUDED.title,
                content = EXCLUDED.content,
                severity = EXCLUDED.severity,
                updated_at = now()
            """,
            project_id,
            rule_key,
            rule.get("rule_type"),
            rule.get("title"),
            rule.get("content"),
            rule.get("severity", "warning"),
        )
    except Exception as e:
        logger.warning(f"Failed to create rule: {e}")


async def _create_initial_arc(project_id: str, character_name: str) -> None:
    """Create initial character arc."""
    from ..deps import db
    try:
        entity = await db.fetchrow(
            "SELECT id FROM state_entities WHERE project_id = $1 AND name = $2",
            project_id, character_name)
        if entity:
            await db.execute(
                """
                INSERT INTO character_arcs (project_id, entity_id, chapter_no, arc_type, state, change_summary)
                VALUES ($1, $2, 0, 'emotion', '{"emotion": "平静", "intensity": 0.5}', '角色初始状态')
                ON CONFLICT DO NOTHING
                """, project_id, entity["id"])
    except Exception as e:
        logger.warning(f"Failed to create initial arc: {e}")


async def _recommend_system_configs(
    genre: str | None,
    tone: str | None,
    length: str | None
) -> dict[str, list[dict]]:
    """根据小说类型推荐系统级配置和相关知识。
    
    Args:
        genre: 小说类型/题材
        tone: 故事基调
        length: 预计字数
        
    Returns:
        {
            "style_profiles": [...],
            "prompt_templates": [...],
            "model_profiles": [...],
            "setting_recommendations": [],  # 按类别分组的设定建议
            "world_templates": [],           # 世界观模板
        }
    """
    from ..deps import db
    
    configs = {
        "style_profiles": [],
        "prompt_templates": [],
        "model_profiles": [],
        "setting_recommendations": [],
        "world_templates": [],
    }
    
    # 如果 genre 为空，先返回已配置的风格/模板/模型
    if not genre:
        return configs
    
    try:
        # 推荐文风档案
        rows = await db.fetch(
            """
            SELECT profile_key, display_name, description, tone, applicable_genres
            FROM system_style_profiles
            WHERE ($1 = ANY(applicable_genres) OR applicable_genres IS NULL OR applicable_genres = '{}')
            AND status = 'active'
            ORDER BY 
                CASE WHEN $1 = ANY(applicable_genres) THEN 0 ELSE 1 END,
                CASE WHEN tone = $2 THEN 0 ELSE 1 END,
                created_at DESC
            LIMIT 3
            """,
            genre, tone
        )
        configs["style_profiles"] = [dict(row) for row in rows]
        
        # 推荐提示词模板
        rows = await db.fetch(
            """
            SELECT template_key, template_name, description, template_type, genre as template_genre
            FROM system_prompt_templates
            WHERE (genre = $1 OR genre IS NULL)
            AND status = 'active'
            ORDER BY template_type, template_name
            LIMIT 5
            """,
            genre
        )
        configs["prompt_templates"] = [dict(row) for row in rows]
        
        # 推荐模型配置
        rows = await db.fetch(
            """
            SELECT profile_key, display_name, provider, model_name, task_types, recommended_for
            FROM system_model_profiles
            WHERE status = 'active'
            ORDER BY display_name
            LIMIT 3
            """
        )
        configs["model_profiles"] = [dict(row) for row in rows]
        
        # 推荐系统设定（按类别分组）
        setting_categories = [
            "genre-inference", "character-template", "plot-template",
            "naming-rules", "scene-writing", "writing-techniques",
            "rhythm-points", "review-rules", "golden-finger"
        ]
        setting_recs = []
        for cat in setting_categories:
            items = await db.fetch(
                """
                SELECT si.category_slug, si.item_key, si.title, si.core_summary,
                       si.ai_instruction, si.poison_points, si.applicable_genres, si.level
                FROM setting_items si
                JOIN setting_categories sc ON sc.slug = si.category_slug
                WHERE si.category_slug = $1
                  AND si.status = 'active'
                  AND ($2 = ANY(si.applicable_genres) OR si.applicable_genres IS NULL OR si.applicable_genres = '{}')
                  AND si.level IN ('knowledge', 'reminder')
                ORDER BY si.sort_order, si.title
                LIMIT 5
                """,
                cat, genre
            )
            if items:
                setting_recs.append({
                    "category": cat,
                    "items": [dict(r) for r in items]
                })
        configs["setting_recommendations"] = setting_recs
        
        # 推荐世界观模板
        world_rows = await db.fetch(
            """
            SELECT DISTINCT ON (wk.key) wk.key, wk.name, wk.summary, wk.tags, wk.applicable_genres
            FROM knowledge_entities wk
            WHERE wk.entity_type IN ('world_setting', 'world')
              AND (wk.applicable_genres IS NULL OR $1 = ANY(wk.applicable_genres))
              AND wk.status = 'active'
            ORDER BY wk.key, wk.name
            LIMIT 5
            """,
            genre
        )
        configs["world_templates"] = [dict(r) for r in world_rows]
        
    except Exception as e:
        logger.warning(f"Failed to recommend system configs: {e}")
    
    return configs


async def _fork_system_configs_to_project(
    project_id: str,
    workspace: str,
    project_slug: str,
    selected_configs: dict[str, Any],
    principal: Any
) -> dict[str, Any]:
    """导入选中的系统级配置到项目。
    
    Args:
        project_id: 项目ID
        workspace: 工作区
        project_slug: 项目slug
        selected_configs: 选中的配置
        principal: 当前用户
        
    Returns:
        导入结果统计
    """
    from ..deps import db
    
    results = {
        "style_profiles_imported": 0,
        "templates_imported": 0,
        "model_profiles_imported": 0,
        "errors": []
    }
    
    # 导入文风档案
    if selected_configs.get("style_profile"):
        try:
            system_profile = await db.fetchrow(
                """
                SELECT * FROM system_style_profiles
                WHERE profile_key = $1 AND status = 'active'
                """,
                selected_configs["style_profile"]
            )
            
            if system_profile:
                # 导入为项目级文风档案
                await db.execute(
                    """
                    INSERT INTO style_profiles 
                    (project_id, profile_key, display_name, narrative_pov, tense, tone,
                     target_metrics, description, characteristics, sample_paragraphs,
                     status, forked_from_system_key)
                    VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, 'active', $11)
                    ON CONFLICT (project_id, profile_key) DO UPDATE SET
                        display_name = EXCLUDED.display_name,
                        tone = EXCLUDED.tone,
                        target_metrics = EXCLUDED.target_metrics,
                        description = EXCLUDED.description,
                        updated_at = now()
                    """,
                    project_id,
                    system_profile["profile_key"],
                    system_profile["display_name"],
                    system_profile["narrative_pov"],
                    system_profile["tense"],
                    system_profile["tone"],
                    system_profile["target_metrics"],
                    system_profile["description"],
                    system_profile["characteristics"],
                    system_profile["sample_paragraphs"],
                    system_profile["profile_key"]
                )
                results["style_profiles_imported"] += 1
        except Exception as e:
            results["errors"].append(f"Style profile import failed: {e}")
            logger.warning(f"Failed to import style profile: {e}")
    
    # 导入提示词模板
    if selected_configs.get("prompt_templates"):
        for template_key in selected_configs["prompt_templates"]:
            try:
                system_template = await db.fetchrow(
                    """
                    SELECT * FROM system_prompt_templates
                    WHERE template_key = $1 AND status = 'active'
                    """,
                    template_key
                )
                
                if system_template:
                    await db.execute(
                        """
                        INSERT INTO prompt_templates
                        (project_id, template_key, template_name, template_content, description,
                         template_type, genre, scene, variables, status, forked_from_system_key)
                        VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, 'active', $10)
                        ON CONFLICT (project_id, template_key) DO UPDATE SET
                            template_name = EXCLUDED.template_name,
                            template_content = EXCLUDED.template_content,
                            updated_at = now()
                        """,
                        project_id,
                        system_template["template_key"],
                        system_template["template_name"],
                        system_template["template_content"],
                        system_template["description"],
                        system_template["template_type"],
                        system_template["genre"],
                        system_template["scene"],
                        system_template["variables"],
                        system_template["template_key"]
                    )
                    results["templates_imported"] += 1
            except Exception as e:
                results["errors"].append(f"Template {template_key} import failed: {e}")
                logger.warning(f"Failed to import template {template_key}: {e}")
    
    # 导入模型配置到用户配置
    if selected_configs.get("model_profile") and principal:
        try:
            system_profile = await db.fetchrow(
                """
                SELECT * FROM system_model_profiles
                WHERE profile_key = $1 AND status = 'active'
                """,
                selected_configs["model_profile"]
            )
            
            if system_profile and hasattr(principal, 'user_id'):
                user_profile_key = f"{principal.username}_{system_profile['profile_key']}"
                await db.execute(
                    """
                    INSERT INTO model_profiles
                    (user_id, profile_key, display_name, provider, model_name, task_types,
                     default_params, cost_config, rate_limit_config, is_system, forked_from_system_key)
                    VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, false, $10)
                    ON CONFLICT (user_id, profile_key) DO UPDATE SET
                        display_name = EXCLUDED.display_name,
                        provider = EXCLUDED.provider,
                        model_name = EXCLUDED.model_name,
                        updated_at = now()
                    """,
                    principal.user_id,
                    user_profile_key,
                    system_profile["display_name"],
                    system_profile["provider"],
                    system_profile["model_name"],
                    system_profile["task_types"],
                    system_profile["default_params"],
                    system_profile["cost_config"],
                    system_profile["rate_limit_config"],
                    system_profile["profile_key"]
                )
                results["model_profiles_imported"] += 1
        except Exception as e:
            results["errors"].append(f"Model profile import failed: {e}")
            logger.warning(f"Failed to import model profile: {e}")
    
    return results


async def _create_initial_volume(project_id: str, workspace: str, project: str,
                                  estimated_length: str = "100-200万字",
                                  genre: str = "玄幻",
                                  tone: str = "热血爽文") -> None:
    """Helper to create initial volume with proper metadata."""
    from ..deps import db
    try:
        metadata_str = json.dumps({"genre": genre, "estimated_length": estimated_length, "tone": tone}, ensure_ascii=False)
        goals_str = json.dumps([
            {"title": "引入世界观", "description": "展示故事发生的世界和基本规则"},
            {"title": "引入主角", "description": "介绍主角的背景、性格和初始目标"},
            {"title": "引发冲突", "description": "触发故事主线冲突，推动主角踏上旅程"},
        ], ensure_ascii=False)
        outline_str = f"首卷：为整个故事奠定基础，介绍世界观、主要角色和核心冲突。风格：{tone}"
        await db.execute(
            """
            INSERT INTO volumes (project_id, volume_no, title, status, start_chapter_no,
                                 outline, metadata, goals)
            VALUES ($1, 1, '第一卷', 'active', 1, $2, $3::jsonb, $4::jsonb)
            ON CONFLICT (project_id, volume_no) DO UPDATE SET
                outline = EXCLUDED.outline, metadata = EXCLUDED.metadata, goals = EXCLUDED.goals
            """,
            project_id, outline_str, metadata_str, goals_str,
        )
    except Exception as e:
        logger.warning(f"Failed to create initial volume: {e}")


@mcp.tool(name="novel.wizard.submit_knowledge_proposals")
async def novel_wizard_submit_knowledge_proposals(
    workspace: str,
    project: str,
    proposals: list[dict[str, Any]],
) -> dict[str, Any]:
    """提交用户采纳的AI推荐知识作为进化提案，等待管理员审批。
    
    当AI推荐的知识被用户采纳后，通过此工具提交到系统。
    管理员审批通过后，知识将补充到系统知识库。
    
    Args:
        workspace: 工作区
        project: 项目
        proposals: 知识提案列表，每个提案包含:
            - title: 提案标题
            - description: 详细描述
            - proposal_type: 'create' / 'update'（默认 create）
            - target_entity_type: 目标类型：'setting_item' / 'knowledge_item' / 'genre_config' / 'style_profile' / 'prompt_template'
            - proposed_content: 建议的内容（object）
            - evolution_reason: 进化理由
            - source_model: 来源模型标识
            - evidence: 支持证据（object，可选）
            
    Returns:
        提交结果
    """
    principal = await get_principal("write")
    logger.info("novel_wizard_submit_knowledge_proposals called with %d proposals", len(proposals))
    validate_required(locals(), "workspace", "project", "proposals")
    project_id = await auth.resolve_project_id(workspace, project, principal, access="write")

    if not proposals:
        return {"ok": True, "submitted": 0, "message": "无提案需要提交"}

    user_row = await db.fetchrow("SELECT id FROM users WHERE username = $1", principal.username)
    user_id = user_row["id"] if user_row else None

    results = {"submitted": 0, "errors": []}
    for prop in proposals:
        title = prop.get("title", "").strip()
        description = prop.get("description", prop.get("content", "")).strip()
        ptype = prop.get("proposal_type", "create")
        target_type = prop.get("target_entity_type", "setting_item")
        proposed_content = prop.get("proposed_content", {})
        evolution_reason = prop.get("evolution_reason", prop.get("reasoning", "AI推荐"))
        ai_submitter = prop.get("source_model", "ai_generated")
        evidence = prop.get("evidence", {})

        if not title or not description:
            results["errors"].append("跳过无效提案: title或description为空")
            continue

        try:
            row = await db.fetchrow(
                """
                INSERT INTO system_evolution_proposals
                    (title, description, proposal_type, target_entity_type,
                     proposed_content, evolution_reason, source_project_id,
                     ai_submitter, evidence, status)
                VALUES ($1, $2, $3, $4, $5::jsonb, $6, $7, $8, $9::jsonb, 'draft')
                RETURNING id::text
                """,
                title,
                description,
                ptype,
                target_type,
                json.dumps(proposed_content, ensure_ascii=False),
                evolution_reason,
                project_id,
                ai_submitter,
                json.dumps(evidence, ensure_ascii=False),
            )
            results["submitted"] += 1
            logger.info("Submitted knowledge proposal: %s (%s)", title, target_type)
        except Exception as e:
            results["errors"].append(f"提交 '{title}' 失败: {e}")
            logger.warning("Failed to submit proposal '%s': %s", title, e)

    # 创建系统通知
    if results["submitted"] > 0:
        try:
            project_row = await db.fetchrow("SELECT title FROM projects WHERE id = $1", project_id)
            project_title = project_row["title"] if project_row else project
            await db.execute(
                """
                INSERT INTO system_notifications (type, title, content, is_global)
                VALUES ($1, $2, $3, true)
                """,
                "evolution_proposal",
                f"新的知识提案",
                f"项目《{project_title}》提交了 {results['submitted']} 个知识提案待审批",
            )
        except Exception as e:
            logger.warning("Failed to create notification: %s", e)

    return {
        "ok": len(results["errors"]) == 0,
        "submitted": results["submitted"],
        "errors": results["errors"],
        "message": f"成功提交 {results['submitted']} 个知识提案，等待管理员审批",
    }


# ============================================================
# 题材 → 搜索建议映射
# ============================================================

GENRE_SEARCH_SUGGESTIONS = {
    "historical_ancient": {
        "display_name": "古代历史",
        "suggestions": [
            {"category": "character", "label": "历史人物", "keywords": ["{dynasty} 著名历史人物 生平", "{dynasty} 人物 性格 成就"]},
            {"category": "event", "label": "历史事件", "keywords": ["{dynasty} 重要历史事件 战争", "{dynasty} 重大事件 时间线"]},
            {"category": "setting", "label": "政治制度", "keywords": ["{dynasty} 官制 科举 三省六部", "{dynasty} 法律制度 礼仪"]},
            {"category": "setting", "label": "文化风俗", "keywords": ["{dynasty} 文化 服饰 饮食 风俗", "{dynasty} 社会生活 日常"]},
            {"category": "location", "label": "地理布局", "keywords": ["{dynasty} 都城 城市布局 坊市", "{dynasty} 地理 行政区划"]},
            {"category": "setting", "label": "军事体系", "keywords": ["{dynasty} 军队 兵制 兵器", "{dynasty} 著名战役"]},
        ],
        "genre_tags": ["历史"],
    },
    "historical_republic": {
        "display_name": "民国历史",
        "suggestions": [
            {"category": "character", "label": "历史人物", "keywords": ["民国 著名人物 生平", "民国 军阀 政治人物"]},
            {"category": "event", "label": "历史事件", "keywords": ["民国 重大历史事件", "辛亥革命 北伐 抗日战争"]},
            {"category": "setting", "label": "社会制度", "keywords": ["民国 政治制度 租界", "民国 经济 工业"]},
            {"category": "setting", "label": "文化风俗", "keywords": ["民国 文化 服饰 建筑", "民国 上海 百乐门 报业"]},
            {"category": "location", "label": "城市地理", "keywords": ["民国 上海 法租界 外滩", "民国 南京 北京 城市"]},
        ],
        "genre_tags": ["历史"],
    },
    "xianxia": {
        "display_name": "仙侠",
        "suggestions": [
            {"category": "setting", "label": "修炼体系", "keywords": ["修仙 修炼体系 境界划分", "修真 功法 丹药 法宝"]},
            {"category": "setting", "label": "世界观", "keywords": ["仙侠 世界观 仙界 灵界", "修真 门派 洞天福地"]},
            {"category": "character", "label": "角色灵感", "keywords": ["仙侠 角色 设定 模板", "修仙 人物 性格 天赋"]},
        ],
        "genre_tags": ["仙侠"],
    },
    "xuanhuan": {
        "display_name": "玄幻",
        "suggestions": [
            {"category": "setting", "label": "力量体系", "keywords": ["玄幻 力量体系 等级 设定", "魔法 斗气 血脉 天赋"]},
            {"category": "setting", "label": "种族设定", "keywords": ["玄幻 种族 设定 龙族 精灵", "异界 物种 世界观"]},
            {"category": "character", "label": "角色灵感", "keywords": ["玄幻 主角 设定 模板", "玄幻 反派 势力 设计"]},
        ],
        "genre_tags": ["玄幻"],
    },
    "sci-fi": {
        "display_name": "科幻",
        "suggestions": [
            {"category": "setting", "label": "科技设定", "keywords": ["科幻 未来科技 人工智能 量子", "太空 殖民 星际 航行"]},
            {"category": "setting", "label": "世界观", "keywords": ["科幻 世界观 设定 赛博朋克", "未来 社会 制度 经济"]},
            {"category": "event", "label": "科学前沿", "keywords": ["最新 科技 突破 2024 2025", "航天 生物 科技 进展"]},
        ],
        "genre_tags": ["科幻"],
    },
    "urban": {
        "display_name": "都市",
        "suggestions": [
            {"category": "setting", "label": "职业知识", "keywords": ["金融 投资 商业 职场", "律师 医生 警察 职业"]},
            {"category": "setting", "label": "社会背景", "keywords": ["当代 社会 热点 行业", "现代 城市 生活 文化"]},
            {"category": "event", "label": "行业资讯", "keywords": ["最新 行业 动态 趋势", "商业 案例 成功 创业"]},
        ],
        "genre_tags": ["都市"],
    },
    "post_apocalyptic": {
        "display_name": "末日",
        "suggestions": [
            {"category": "setting", "label": "生存体系", "keywords": ["末日 生存 知识 野外 技能", "灾难 类型 核辐射 病毒"]},
            {"category": "setting", "label": "世界观", "keywords": ["末日 世界观 设定 基地", "废土 变异 生物 危险"]},
        ],
        "genre_tags": ["末日"],
    },
    "horror": {
        "display_name": "灵异",
        "suggestions": [
            {"category": "setting", "label": "灵异体系", "keywords": ["灵异 鬼怪 分类 设定", "恐怖 规则 禁忌 民俗"]},
            {"category": "setting", "label": "民俗文化", "keywords": ["民间 传说 鬼故事 民俗", "风水 命理 道术 法术"]},
        ],
        "genre_tags": ["灵异"],
    },
    "game": {
        "display_name": "游戏",
        "suggestions": [
            {"category": "setting", "label": "游戏系统", "keywords": ["游戏 系统 设定 技能树", "MMORPG 副本 装备 职业"]},
            {"category": "setting", "label": "世界观", "keywords": ["游戏 世界观 地图 势力", "网游 公会 阵营 设定"]},
        ],
        "genre_tags": ["游戏"],
    },
    "time_travel": {
        "display_name": "穿越",
        "suggestions": [
            {"category": "setting", "label": "穿越设定", "keywords": ["穿越 设定 金手指 系统", "重生 回到过去 改变历史"]},
            {"category": "setting", "label": "时代背景", "keywords": ["古代 历史 知识 穿越 必备", "穿越 古代 生存 指南"]},
        ],
        "genre_tags": ["穿越"],
    },
    "isekai": {
        "display_name": "异世界",
        "suggestions": [
            {"category": "setting", "label": "世界观", "keywords": ["异世界 设定 召唤 转生", "异界 冒险 魔法 剑与魔法"]},
            {"category": "setting", "label": "角色灵感", "keywords": ["异世界 角色 设定 模板", "异界 种族 职业 技能"]},
        ],
        "genre_tags": ["异世界"],
    },
}


@mcp.tool(name="novel.wizard.get_deepen_suggestions")
async def novel_wizard_get_deepen_suggestions(
    workspace: str,
    project: str,
    project_id: str,
) -> dict[str, Any]:
    """获取项目设定深化建议。commit 后调用，返回按 section 分组的深化任务。

    每个 task 包含 tool、params_template、search_suggestions。
    AI 工具逐个 section 询问用户，逐步执行。
    - params_template 中的具体内容由 AI 工具（AI工具）生成
    - search_suggestions 需要 AI 工具先 web_search → kb.auto.search_and_store

    Args:
        project_id: 项目 ID

    Returns:
        6 个 section 的深化建议，按 priority 排序
    """
    principal = await get_principal("read")
    project_id = await auth.resolve_project_id(workspace, project, principal, access="read")
    logger.info("get_deepen_suggestions called: project_id=%s", project_id)

    # 获取项目信息（含 workspace 和 project slug）
    project_row = await db.fetchrow(
        """
        SELECT p.title, p.description, p.slug AS project_slug,
               w.slug AS workspace_slug
        FROM projects p
        JOIN workspaces w ON w.id = p.workspace_id
        WHERE p.id = $1
        """, project_id
    )
    if not project_row:
        return {"error": f"项目 {project_id} 不存在"}

    title = project_row["title"]
    genre_raw = project_row.get("description", "")
    project_slug = project_row["project_slug"]
    workspace_slug = project_row["workspace_slug"]

    # 尝试从 description 中解析 genre（也可能从 world_snapshots 获取）
    genre_map = {
        "民国": "historical_republic", "历史": "historical_ancient",
        "仙侠": "xianxia", "玄幻": "xuanhuan",
        "科幻": "sci-fi", "都市": "urban",
        "末日": "post_apocalyptic", "灵异": "horror",
        "游戏": "game", "穿越": "time_travel", "异世界": "isekai",
    }
    genre_key = None
    for kw, key in genre_map.items():
        if kw in genre_raw:
            genre_key = key
            break

    # 获取题材策略
    from ..deps import kb_service
    from ..kb_service import KBService
    gen_strategy = None
    if genre_key:
        try:
            gen_strategy = await kb_service.genre_get_strategy(genre_key)
        except Exception:
            gen_strategy = None
        if not gen_strategy:
            gen_strategy = KBService.GENRE_STRATEGIES.get(genre_key)

    # 获取题材搜索建议
    genre_search = GENRE_SEARCH_SUGGESTIONS.get(genre_key, {})
    search_items = genre_search.get("suggestions", [])
    genre_tags = genre_search.get("genre_tags", [genre_raw])
    dynasty = ""
    if gen_strategy:
        dynasties = gen_strategy.get("dynasties", [])
        if dynasties:
            dynasty = dynasties[len(dynasties) // 2]  # 取中间朝代

    # 填充搜索关键词模板
    filled_searches = []
    for item in search_items:
        keywords = item.get("keywords", [])
        for kw in keywords:
            filled = kw.replace("{dynasty}", dynasty).replace("{year}", "1900")
            if filled != kw or dynasty:
                filled_searches.append({
                    "category": item["category"],
                    "label": item["label"],
                    "query": filled,
                })
        if not keywords:
            filled_searches.append({
                "category": item["category"],
                "label": item["label"],
                "query": item.get("label", ""),
            })

    # 去重
    seen = set()
    unique_searches = []
    for s in filled_searches:
        if s["query"] not in seen:
            seen.add(s["query"])
            unique_searches.append(s)

    # 替换 params_template 中的占位符
    def _fill_template(template: dict) -> dict:
        s = json.dumps(template, ensure_ascii=False)
        s = s.replace('"workspace": "-"', f'"workspace": "{workspace_slug}"')
        s = s.replace('"project": "-"', f'"project": "{project_slug}"')
        return json.loads(s)

    # 构建 6 个 section
    sections = [
        {
            "id": "knowledge_base",
            "title": "知识库预热",
            "priority": 0,
            "goal": f"基于「{title}」({genre_raw}题材)，搭建背景知识库",
            "guidance": f"""
## 你的任务：为「{title}」搭建知识库

**工作模式**：先做、再展示、用户确认后继续。

### 步骤 1：创建知识包
调 kb.pack.create(workspace="{workspace_slug}", project="{project_slug}", project_id="{project_id}", genre="{genre_key or genre_raw}")
→ 创建项目专属知识包，自动绑定题材分类

### 步骤 2：分析知识缺口
调 kb.gap.analyze(genre="{genre_key or genre_raw}")
→ 返回每个分类的已有知识条目数和 should_fill=true/false
→ 向用户报告：「已检查知识库，发现 N 个分类需要补充」
→ 带用户确认要补充哪些分类

### 步骤 3：生成知识（对话式）
从 should_fill=true 的分类中选 1 个，用你的 LLM 生成该分类的知识建议：
- 每条知识包含：topic（主题）、content（1-2段内容）、category_slug（分类标识）
- 展示给用户：「我为【{genre_raw}】的【分类名】准备了这些知识点，你看合适吗？」
- 用户确认后调 kb.pk.upsert 写入，继续下一个分类
- 重复直到所有缺失分类补完，或用户说「够了」
""",
            "tasks": [],
        },
        {
            "id": "world_setting",
            "title": "世界观设定",
            "priority": 1,
            "goal": f"基于「{title}（{genre_raw}）」完善世界观规则和地点势力",
            "guidance": f"""
## 你的任务：为「{title}」设计世界观

**工作模式**：先生成详细建议，再让用户调整

### 核心世界规则
用 LLM 生成世界观核心设定，包含：
- 时间背景（时代、年份）
- 核心规则（物理法则/魔法体系/社会制度）
- 关键冲突（世界的主要矛盾）

生成后展示给用户：「这是我想的世界观框架，你希望调整哪些？」

用户确认后调 canon.doc.upsert(doc_type="world", key="world_background", title="世界观设定", content="生成的完整设定")

### 地点设计（3-5 个）
对每个地点，用 LLM 生成：
- 名称、类型（城市/区域/秘境）
- 地理位置描述
- 在故事中的意义（主角出生地/决战地/关键场景）

每生成一个就展示：「我设计了一个【地点名】，位于【描述】，你满意吗？」
用户确认 → state.entity.upsert(entity_type="location", ...)

### 势力设计（2-4 个）
对每个势力，用 LLM 生成：
- 名称、类型（政府/宗门/帮派/组织）
- 势力范围、核心理念
- 与主角的关联

展示：「我设计了【势力名】，核心理念是【xxx】，与主角的关系是【xxx】」
确认 → state.entity.upsert(entity_type="faction", ...)
""",
            "tasks": [],
        },
        {
            "id": "characters",
            "title": "角色深化",
            "priority": 2,
            "goal": f"「{title}」的角色体系",
            "guidance": f"""
## 你的任务：为「{title}」设计角色体系

**工作模式**：先生成详细人设，再让用户调整

### 主角深化
用 LLM 生成主角完整 profile：
- 性格标签（3-5 个核心特质）
- 背景故事（关键经历和转折点）
- 核心动机（他想要什么、害怕什么）
- 优势和弱点
- 成长弧线（起点的身份 → 终点的身份）

展示：「我为主角设计了这些设定，你看需要调整哪些？」
确认 → state.entity.upsert(name="主角名", entity_type="character", ...)

### 配角设计（2-4 个）
每个配角生成：
- 姓名、身位
- 与主角的关系定位（导师/挚友/竞争对手/爱慕者）
- 对主线的推动方式

展示：「我新增了一个配角【名字】，定位是【xxx】，与主角互动方式是【xxx】」
确认 → state.entity.upsert → 继续下一个

### 反派设计（1-2 个）
生成反派的：
- 姓名、动机、与主角的核心理念冲突
- 实力层次、势力范围

### 关系网
所有角色创建后，调 state.relationship.upsert 建立关系
展示关系图，确认无误
""",
            "tasks": [],
        },
        {
            "id": "volumes",
            "title": "卷纲规划",
            "priority": 3,
            "goal": f"「{title}」多卷结构",
            "guidance": f"""
## 你的任务：将「{title}」的故事分解为多卷

**工作模式**：先生成 3-5 卷的建议，逐卷确认

### 卷结构设计
用 LLM 生成 3-5 卷的概要：
- 每卷的标题、主题
- 起止章节范围（每卷 20-40 章）
- 该卷的主要冲突
- 关键人物该卷的状态变化

展示所有卷规划：「我把故事分成 {3-5} 卷，你看这个结构合适吗？」

确认后逐卷创建：
volume.upsert("volume_no": n, "title": "卷名", "summary": "该卷概要",
  "goals": [{{"title": "目标1", "description": "..."}}],
  "start_chapter_no": m, "end_chapter_no": n)
""",
            "tasks": [],
        },
        {
            "id": "chapters",
            "title": "章节规划",
            "priority": 4,
            "goal": f"「{title}」第一卷章节大纲",
            "guidance": f"""
## 你的任务：为第一卷规划前 5-10 章

**工作模式**：每生成 2-3 章展示给用户，确认后继续

### 单章模板（每章）
用 LLM 生成：
- 章节标题
- 核心情节点
- 人物出场安排
- 场景/地点
- 情感基调

展示：「第 N 章安排了【核心事件】，出场角色【xxx】，你看合适吗？」

确认 → plot.create_chapter_plan(chapter_no=n, plan={{...}})
继续下一章，建议总 5-10 章
""",
            "tasks": [],
        },
        {
            "id": "plot_threads",
            "title": "剧情线与伏笔",
            "priority": 5,
            "goal": f"「{title}」的剧情架构和悬念",
            "guidance": f"""
## 你的任务：铺设剧情线和伏笔

### 主线定义
用 LLM 生成主线剧情：
- 线名、高潮节点
- 起止章节
- 影响角色

展示 → plot.thread.upsert(key="main_story", title="主线名", ...)

### 支线（2-3 条）
生成支线：
- 替换线、成长线、感情线等
- 与主线的交汇点

展示 → plot.thread.upsert(...)

### 伏笔（3-5 个）
生成伏笔：
- visible 层：明显的伏笔
- hidden 层：回顾才能发现的
- deep 层：贯穿全书的暗线

展示每个伏笔 → plot.upsert_foreshadowing(...)
""",
            "tasks": [],
        },
    ]

    return {
        "project_id": project_id,
        "project_title": title,
        "genre": genre_key or genre_raw,
        "genre_display": genre_search.get("display_name", genre_raw) if genre_search else genre_raw,
        "sections": sections,
        "workflow_guide": {
            "phase": "深化设定",
            "next_section": sections[0]["id"],
            "description": "6 个 section 按 priority 顺序（0→5）逐个执行。每个 section 的 guidance 包含详细步骤，先生成建议再让用户调整。",
            "execution_tips": [
                "先问用户是否开始本 section",
                "严格遵循 guidance 中的步骤顺序",
                "先生成具体内容，再展示给用户确认或调整",
                "用户说「通过」或「继续」才进入下一步",
                "用户不满意可以让用户指出调整方向，重新生成",
            ],
        },
    }


@mcp.tool(name="novel.wizard.build_world")
async def novel_wizard_build_world(
    workspace: str,
    project: str,
) -> dict[str, Any]:
    """启动全自动小说世界构建流程。commit 后调用此工具替代 get_deepen_suggestions。

    返回分 4 个阶段的完整构建计划，agent 按阶段自动推进直到所有设定完备。
    每阶段有明确的完成标准，agent 批量生成内容 → 展示 → 用户确认/调整 → 继续。
    不限要素数量，直到 agent 和用户双方确认该阶段无遗漏。

    Returns:
        workflow_guide 包含 4 个阶段，每个阶段有 phases[current/next/total] 跟踪进度
    """
    principal = await get_principal("read")
    logger.info("build_world called")
    project_id = await auth.resolve_project_id(workspace, project, principal, access="read")

    # 获取项目信息
    project_row = await db.fetchrow(
        "SELECT p.title, p.description, w.slug AS workspace_slug, p.slug AS project_slug FROM projects p JOIN workspaces w ON w.id = p.workspace_id WHERE p.id = $1",
        project_id,
    )
    if not project_row:
        return {"error": "项目不存在"}

    title = project_row["title"]
    genre_raw = project_row.get("description", "") or "玄幻"
    ws_slug = project_row["workspace_slug"]
    prj_slug = project_row["project_slug"]

    # 统计现有数据
    existing_volumes = await db.fetchval("SELECT COUNT(*) FROM volumes WHERE project_id = $1", project_id) or 0
    existing_entities = await db.fetchval("SELECT COUNT(*) FROM state_entities WHERE project_id = $1", project_id) or 0
    existing_chapters = await db.fetchval("SELECT COUNT(*) FROM chapters WHERE project_id = $1", project_id) or 0
    existing_kb = await db.fetchval("SELECT COUNT(*) FROM project_knowledge WHERE project_id = $1", project_id) or 0
    existing_foreshadowing = await db.fetchval("SELECT COUNT(*) FROM foreshadowing WHERE project_id = $1", project_id) or 0

    phase = 1
    if existing_volumes > 0:
        phase = 2
    if existing_kb > 3:
        phase = 3
    if existing_entities > 3 and existing_foreshadowing > 2 and existing_chapters == 0:
        phase = 4
    if existing_chapters > 0:
        phase = 5

    # 查询卷列表（用于阶段3确定当前卷）
    vol_rows = await db.fetch(
        "SELECT volume_no, title, start_chapter_no, end_chapter_no FROM volumes WHERE project_id=$1 ORDER BY volume_no",
        project_id,
    )
    volume_count = len(vol_rows) or existing_volumes

    # 阶段3：确定当前处理到第几卷
    current_volume = 1
    if phase == 3 and volume_count > 0:
        # 简单启发式：实体数 / 每卷最低实体数(4) = 大致完成的卷数
        entities_per_volume = max(existing_entities // volume_count, 1) if volume_count > 0 else 0
        completed_volumes = min(existing_entities // max(entities_per_volume or 4, 4), volume_count - 1)
        current_volume = completed_volumes + 1

    # 构建结构化 workflow_guide
    guide = {
        "mode": "strict",
        "phase": phase,
        "total_phases": 5,
        "stats": {
            "volumes": existing_volumes,
            "entities": existing_entities,
            "chapters": existing_chapters,
            "knowledge_entries": existing_kb,
            "foreshadowing": existing_foreshadowing,
        },
        "steps": [],
    }

    if phase <= 5:
        guide["steps"] = _build_world_steps(
            phase=phase,
            ws_slug=ws_slug,
            prj_slug=prj_slug,
            project_id=project_id,
            title=title,
            genre=genre_raw,
            vol_rows=vol_rows,
            current_volume=current_volume,
            volume_count=volume_count,
            existing_volumes=existing_volumes,
            existing_kb=existing_kb,
            existing_entities=existing_entities,
        )
    else:
        guide["mode"] = "done"
        guide["message"] = "所有阶段已完成，世界构建结束。可进入章节生成。"

    return {
        "project_id": project_id,
        "workspace": ws_slug,
        "project": prj_slug,
        "title": title,
        "genre": genre_raw,
        "phase": phase,
        "phases": {str(i): "completed" if i < phase else ("current" if i == phase else "pending") for i in range(1, 6)},
        "stats": {"volumes": existing_volumes, "entities": existing_entities, "chapters": existing_chapters, "knowledge_entries": existing_kb},
        "workflow_guide": guide,
    }

def _build_world_steps(
    phase: int, ws_slug: str, prj_slug: str, project_id: str,
    title: str, genre: str, vol_rows: list, current_volume: int,
    volume_count: int, existing_volumes: int, existing_kb: int,
    existing_entities: int,
) -> list[dict]:
    """根据当前阶段生成结构化步骤列表。"""
    steps = []

    if phase == 1:
        steps.extend([
            {
                "step_no": 1, "name": "生成卷纲结构",
                "tool": "_agent_display",
                "params": {
                    "instruction": f"为「{title}」({genre})生成卷纲结构。每卷包含：标题、主题、章节范围(每卷20-40章)、核心冲突、主角状态变化。生成后展示给用户。"
                },
                "expected_format": "卷号 | 标题 | 章节范围 | 核心冲突",
                "next": "wait_user_confirm",
            },
            {
                "step_no": 2, "name": "创建卷",
                "tool": "volume.upsert",
                "batch": True,
                "params": {"workspace": ws_slug, "project": prj_slug},
                "params_from": "step_1_result",
                "next": "repeat_until_done",
            },
            {
                "step_no": 3, "name": "重新调用 build_world 推进到下一阶段",
                "tool": "novel.wizard.build_world",
                "params": {"workspace": ws_slug, "project": prj_slug},
                "next": "next_step",
            },
        ])

    elif phase == 2:
        steps.extend([
            {
                "step_no": 1, "name": "创建项目知识包",
                "tool": "kb.pack.create",
                "params": {"workspace": ws_slug, "project": prj_slug, "project_id": project_id, "genre": genre},
                "next": "next_step",
            },
            {
                "step_no": 2, "name": "分析知识缺口",
                "tool": "kb.gap.analyze",
                "params": {"genre": genre},
                "next": "next_step",
            },
            {
                "step_no": 3, "name": "启动讨论室生成知识",
                "tool": "discussion_room.create_session",
                "params": {
                    "workspace": ws_slug, "project": prj_slug,
                    "topic": f"为'{title}'({genre})生成背景知识，补齐以下缺口：[用步骤2返回的 should_fill 列表]",
                    "data_source": "knowledge-entries",
                    "output_type": "knowledge",
                },
                "next": "next_step",
            },
            {
                "step_no": 4, "name": "等待讨论完成",
                "tool": "discussion_room.get_updates",
                "params": {"session_id": "$from_step_3"},
                "next": "wait_for_async",
                "poll": {"interval": 5, "max_retries": 40, "field": "status", "until": "status == 'completed'"},
            },
            {
                "step_no": 5, "name": "应用讨论室结果",
                "tool": "discussion_room.apply_results",
                "params": {"session_id": "$from_step_3"},
                "next": "next_step",
            },
            {
                "step_no": 6, "name": "预加载通用知识",
                "tool": "kb.genre.preheat",
                "params": {"workspace": ws_slug, "project": prj_slug, "project_id": project_id, "genre": genre},
                "next": "next_step",
            },
            {
                "step_no": 7, "name": "重新调用 build_world 推进到下一阶段",
                "tool": "novel.wizard.build_world",
                "params": {"workspace": ws_slug, "project": prj_slug},
                "next": "next_step",
            },
        ])

    elif phase == 3:
        # 获取当前卷信息
        vol_info = {}
        if vol_rows and current_volume <= len(vol_rows):
            v = vol_rows[current_volume - 1]
            vol_info = {
                "volume_no": v["volume_no"],
                "title": v["title"],
                "start_chapter": v["start_chapter_no"],
                "end_chapter": v["end_chapter_no"],
            }

        steps.extend([
            {
                "step_no": 1, "name": "展示要素需求清单",
                "tool": "_agent_display",
                "params": {
                    "instruction": f"第{current_volume}卷「{vol_info.get('title','')}」(第{vol_info.get('start_chapter','?')}-{vol_info.get('end_chapter','?')}章)。根据卷纲生成要素需求清单。最低：新地点≥2、新角色≥3、新势力≥1、新伏笔≥2。列出具体要素名称和说明。"
                },
                "volume_no": current_volume,
                "volume_title": vol_info.get("title", ""),
                "next": "wait_user_confirm",
            },
            {
                "step_no": 2, "name": "批量创建角色",
                "tool": "state.entity.upsert",
                "batch": True,
                "params": {"entity_type": "character", "workspace": ws_slug, "project": prj_slug, "project_id": project_id},
                "params_from": "step_1_confirmed",
                "note": "每次调用必须填: name, summary(50-200字描述角色作用和特点), importance(high/medium/low), profile(json{age,appearance,personality,background,skills})。建议填: aliases[], tags[], description",
                "next": "repeat_until_done",
            },
            {
                "step_no": 3, "name": "批量创建地点",
                "tool": "state.entity.upsert",
                "batch": True,
                "params": {"entity_type": "location", "workspace": ws_slug, "project": prj_slug, "project_id": project_id},
                "params_from": "step_1_confirmed",
                "note": "每次调用必须填: name, summary(地点描述和故事作用), importance, description(详细环境描写)",
                "next": "repeat_until_done",
            },
            {
                "step_no": 4, "name": "批量创建势力",
                "tool": "state.entity.upsert",
                "batch": True,
                "params": {"entity_type": "faction", "workspace": ws_slug, "project": prj_slug, "project_id": project_id},
                "params_from": "step_1_confirmed",
                "note": "每次调用必须填: name, summary(势力目标和特点), importance, description(组织结构/历史背景)。profile(json{members,territory,goals})",
                "next": "repeat_until_done",
            },
            {
                "step_no": 5, "name": "批量创建伏笔",
                "tool": "plot.upsert_foreshadowing",
                "batch": True,
                "params": {"workspace": ws_slug, "project": prj_slug},
                "params_from": "step_1_confirmed",
                "note": "必填: key(英文标识), title, importance(high/medium/low), layer(visible/hidden/deep)。付费伏笔填 must_payoff=true 和 payoff_deadline_chapter",
                "next": "repeat_until_done",
            },
            {
                "step_no": 6, "name": "逐章自诊报告",
                "tool": "_agent_evaluate",
                "params": {
                    "instruction": f"逐章(第{vol_info.get('start_chapter','?')}-{vol_info.get('end_chapter','?')}章)检查：每个场景所需的地点、角色、势力、伏笔是否都已创建。用 ✓/✗ 格式列出。有✗则回到步骤2补缺，全部✓则进入下一步。"
                },
                "on_fail": "goto_step_2",
                "next": "next_step",
            },
            {
                "step_no": 7, "name": "启动讨论室把关",
                "tool": "discussion_room.create_session",
                "params": {
                    "workspace": ws_slug, "project": prj_slug,
                    "topic": f"审查第{current_volume}卷'{vol_info.get('title','')}'设定完备性",
                    "data_source": "entities",
                    "output_type": "review",
                },
                "next": "next_step",
            },
            {
                "step_no": 8, "name": "等待讨论完成",
                "tool": "discussion_room.get_updates",
                "params": {"session_id": "$from_step_7"},
                "next": "wait_for_async",
                "poll": {"interval": 5, "max_retries": 40, "field": "status", "until": "status == 'completed'"},
            },
            {
                "step_no": 9, "name": "读取审查结论并决定下一步",
                "tool": "discussion_room.get_session",
                "params": {"session_id": "$from_step_7"},
                "condition": "summary 包含'不完备' → 回到步骤2补缺；包含'完备' → 下一步",
                "next": "next_step",
            },
            {
                "step_no": 10, "name": "重新调用 build_world 推进到下一卷或下一阶段",
                "tool": "novel.wizard.build_world",
                "params": {"workspace": ws_slug, "project": prj_slug},
                "display_before": f"第{current_volume}卷完成：地点X个 角色Y个 势力Z个 伏笔W个（统计后填入实际数字）\nAgent诊断 ✓ / 讨论室 ✓",
                "next": "wait_user_confirm",
            },
        ])

    elif phase == 4:
        steps.extend([
            {
                "step_no": 1, "name": "跨卷全局检查",
                "tool": "_agent_evaluate",
                "params": {
                    "instruction": f"对「{title}」的 {existing_volumes} 卷进行全局一致性检查：\n1. 逐个角色检查成长弧线是否完整\n2. 逐个伏笔检查是否有回收计划\n3. 逐卷检查世界规则是否有矛盾\n4. 列出所有遗漏和矛盾\n5. 补全后输出完成报告"
                },
                "next": "wait_user_confirm",
            },
            {
                "step_no": 2, "name": "重新调用 build_world 推进到下一阶段",
                "tool": "novel.wizard.build_world",
                "params": {"workspace": ws_slug, "project": prj_slug},
                "next": "next_step",
            },
        ])

    elif phase == 5:
        steps.extend([
            {
                "step_no": 1, "name": "逐章生成大纲",
                "tool": "_agent_display",
                "params": {
                    "instruction": f"为「{title}」的全部 {existing_volumes} 卷逐章生成大纲。每章包含：标题、场景(2-4个)、出场人物、剧情推进要点、节奏控制。生成后展示。"
                },
                "next": "wait_user_confirm",
            },
            {
                "step_no": 2, "name": "批量创建章节大纲",
                "tool": "plot.create_chapter_plan",
                "batch": True,
                "params": {"workspace": ws_slug, "project": prj_slug},
                "params_from": "step_1_confirmed",
                "next": "repeat_until_done",
            },
            {
                "step_no": 3, "name": "检查完成状态",
                "tool": "novel.wizard.build_world",
                "params": {"workspace": ws_slug, "project": prj_slug},
                "display_before": "全部卷、全部章大纲创建完毕。世界构建完成！",
                "next": "next_step",
            },
        ])

    return steps

async def _create_world_state(
    project_id: str, project_profile: dict, canon_docs: list[dict]) -> None:
    """Create initial world state snapshot from project settings."""
    from ..deps import db
    try:
        genre = project_profile.get("genre", "未知")
        tone = project_profile.get("tone_style", "未知")
        world_state = json.dumps({
            "genre": genre, "tone": tone, "established": True,
            "initialized_at": str(datetime.utcnow()),
        }, ensure_ascii=False)
        await db.execute(
            """
            INSERT INTO world_snapshots (project_id, chapter_no, world_state, story_progress, story_era)
            VALUES ($1, 0, $2::jsonb, 0.0, $3)
            """,
            project_id, world_state, genre,
        )
    except Exception as e:
        logger.warning(f"Failed to create world state: {e}")
