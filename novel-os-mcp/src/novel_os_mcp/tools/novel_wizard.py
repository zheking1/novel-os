"""Novel Creation Wizard - Interactive project setup for AI agents.

This module provides a conversational wizard for creating novel projects.
AI agents can call these tools to guide users through the setup process.
"""

from typing import Any
import logging
import uuid

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
    """启动小说创建向导，返回问题列表。
    
    AI Agent调用此工具开始创建流程，获取需要询问用户的问题列表。
    第一个问题询问用户选择已有工作区或新建。
    
    Returns:
        {
            "wizard_id": "uuid",  # 向导会话ID
            "questions": [...]     # 问题列表（含工作区选择）
        }
    """
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
    }


@mcp.tool(name="novel.wizard.generate")
async def novel_wizard_generate(
    wizard_id: str,
    answers: dict[str, Any],
) -> dict[str, Any]:
    """根据用户回答生成小说设定预览。
    
    AI Agent收集完用户答案后，调用此工具生成完整的项目设定。
    用户确认后，再调用 novel.wizard.commit 完成创建。
    
    Args:
        wizard_id: 向导会话ID（来自 novel.wizard.start）
        answers: 用户答案字典，键为question id，值为答案
        
    Returns:
        {
            "preview": {
                "project_profile": {...},
                "canon_documents": [...],
                "initial_entities": [...],
                "plot_threads": [...],
            },
            "confirm_prompt": "请确认以上设定，确认后调用 novel.wizard.commit"
        }
    """
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
    
    return {
        "wizard_id": wizard_id,
        "preview": {
            "project_profile": project_profile,
            "canon_documents": canon_documents,
            "initial_entities": initial_entities,
            "plot_threads": plot_threads,
            "initial_rules": initial_rules,
        },
        "message": "以上是根据用户回答生成的初始设定。请展示给用户确认。",
        "next_step": "用户确认后，调用 novel.wizard.commit 完成创建",
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
    
    # Create plot threads
    for thread in plot_threads:
        await _create_plot_thread(project_id, workspace, project_slug, thread)
    
    # Create initial rules
    for rule in initial_rules:
        await _create_rule(project_id, workspace, project_slug, rule)
    
    # Create initial volume
    await _create_initial_volume(project_id, workspace, project_slug)
    
    ws_msg = f"工作区「{workspace}」" if workspace_action == "new" else f"工作区「{workspace}」"
    
    return {
        "ok": True,
        "project_id": project_id,
        "workspace": workspace,
        "project": project_slug,
        "title": title,
        "message": f"小说项目《{title}》创建成功！（{ws_msg}）",
        "next_steps": [
            f"1. 开始创作第1卷：调用 volume 相关工具",
            f"2. 完善角色设定：调用 state.entity.upsert",
            f"3. 规划剧情：调用 plot.thread 和 plot.upsert_foreshadowing",
            f"4. 开始写作：调用 workflow.prepare_chapter_context",
        ],
    }


async def _create_canon_doc(project_id: str, workspace: str, project: str, doc: dict) -> None:
    """Helper to create canon document."""
    from ..deps import db
    try:
        await db.execute(
            """
            INSERT INTO canon_documents (project_id, doc_type, key, title, content, status, source_type)
            VALUES ($1, $2, $3, $4, $5, $6, 'wizard')
            ON CONFLICT (project_id, doc_type, key) DO UPDATE SET
                title = EXCLUDED.title,
                content = EXCLUDED.content,
                status = EXCLUDED.status,
                updated_at = now()
            """,
            project_id,
            doc.get("doc_type"),
            doc.get("key"),
            doc.get("title"),
            doc.get("content"),
            doc.get("status", "active"),
        )
    except Exception as e:
        logger.warning(f"Failed to create canon doc: {e}")


async def _create_entity(project_id: str, workspace: str, project: str, entity: dict) -> None:
    """Helper to create entity."""
    from ..deps import db
    try:
        await db.execute(
            """
            INSERT INTO state_entities (project_id, entity_type, name, aliases, importance, profile, lifecycle_status)
            VALUES ($1, $2, $3, $4, $5, $6::jsonb, 'active')
            ON CONFLICT (project_id, entity_type, name) DO UPDATE SET
                aliases = EXCLUDED.aliases,
                importance = EXCLUDED.importance,
                profile = EXCLUDED.profile,
                updated_at = now()
            """,
            project_id,
            entity.get("entity_type"),
            entity.get("name"),
            entity.get("aliases", []),
            entity.get("importance", "medium"),
            entity.get("profile", {}),
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
    """Helper to create rule."""
    from ..deps import db
    try:
        rule_key = f"wizard_{rule.get('rule_type')}_{uuid.uuid4().hex[:8]}"
        await db.execute(
            """
            INSERT INTO rules (project_id, rule_key, rule_type, title, content, severity, status, source)
            VALUES ($1, $2, $3, $4, $5, $6, 'active', 'wizard')
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


async def _create_initial_volume(project_id: str, workspace: str, project: str) -> None:
    """Helper to create initial volume."""
    from ..deps import db
    try:
        await db.execute(
            """
            INSERT INTO volumes (project_id, volume_no, title, status, start_chapter_no)
            VALUES ($1, 1, '第一卷', 'active', 1)
            ON CONFLICT (project_id, volume_no) DO NOTHING
            """,
            project_id,
        )
    except Exception as e:
        logger.warning(f"Failed to create initial volume: {e}")
