import uuid
from datetime import datetime
from typing import Any
import json
import logging

from ..mcp_core import mcp
from ..deps import db, auth, context_service, workflow_service, context_weight_service, review_service
from ..tool_auth import get_principal, validate_required, validate_length
from ..utils import json_dumps

logger = logging.getLogger("novel_os_mcp.tools.context")


@mcp.tool(name="workflow.prepare_chapter_context")
async def workflow_prepare_chapter_context(
    workspace: str,
    project: str,
    chapter_no: int,
    purpose: str = "draft",
    focus: list[str] | None = None,
    budget: dict[str, Any] | None = None,
    volume_no: int | None = None,
    scope_refs: list[str] | None = None,
    scope_types: list[str] | None = None,
    active_event_keys: list[str] | None = None,
    pov_mode: str = "omniscient",
    pass_number: int | None = None,
    previous_context: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """准备章节上下文并返回完整生成流水线步骤。

    pass_number: 1=大纲 2=初稿 3=润色 4=验证。previous_context 用于增量加载。

    返回 workflow_guide.steps 严格执行：草稿→润色→审核→提交→角色弧光。
    """
    principal = await get_principal("read")
    logger.info("workflow_prepare_chapter_context called")
    validate_required(locals(), "chapter_no")
    project_id = await auth.resolve_project_id(workspace, project, principal)
    ctx = await context_service.prepare_chapter_context(
        project_id=project_id,
        chapter_no=chapter_no,
        purpose=purpose,
        focus=focus or [],
        budget=budget or {},
        volume_no=volume_no,
        scope_refs=scope_refs,
        scope_types=scope_types,
        active_event_keys=active_event_keys,
        pov_mode=pov_mode,
        pass_number=pass_number,
        previous_context=previous_context,
    )
    ctx["workflow_guide"] = {
        "mode": "strict",
        "steps": [
            {
                "step_no": 1, "name": "预检",
                "tool": "workflow.preflight_generation",
                "params": {"workspace": workspace, "project": project, "chapter_no": chapter_no, "purpose": purpose, "focus": focus or [], "budget": budget or {}, "volume_no": volume_no, "pov_mode": pov_mode},
                "next": "next_step",
            },
            {
                "step_no": 2, "name": "获取上下文包",
                "tool": "_agent_evaluate",
                "params": {"instruction": "已获取上下文包（含规则/实体状态/知识库/前情摘要/伏笔/角色弧光/风格指引等），仔细阅读其中约束信息后进入下一步生成初稿"},
                "next": "next_step",
            },
            {
                "step_no": 3, "name": "生成初稿",
                "tool": "pipeline.generate",
                "params": {"workspace": workspace, "project": project, "chapter_no": chapter_no, "task_type": "draft", "content": "$draft_content"},
                "next": "next_step",
                "note": "AI 根据上下文包约束生成正文，填入 content 字段"
            },
            {
                "step_no": 4, "name": "保存初稿到本地",
                "tool": "_agent_evaluate",
                "params": {"instruction": "将步骤3生成的初稿正文保存到本地文件。目录: chapters/第`chapter_no:02d`章/，文件名: ch`chapter_no:02d`_draft.md。保存完整正文到该路径。"},
                "next": "next_step",
            },
            {
                "step_no": 5, "name": "记录生成结果",
                "tool": "pipeline.run_full",
                "params": {"workspace": workspace, "project": project, "chapter_no": chapter_no, "draft_content": "$from_step_3.text"},
                "next": "next_step",
            },
            {
                "step_no": 6, "name": "内容校验",
                "tool": "workflow.validate_content",
                "params": {"workspace": workspace, "project": project, "chapter_no": chapter_no, "content": "$from_step_3.text"},
                "next": "next_step",
            },
            {
                "step_no": 7, "name": "启动审核",
                "tool": "review.start_job",
                "params": {
                    "workspace": workspace, "project": project, "chapter_no": chapter_no,
                    "dimensions": ["character_consistency", "plot_logic", "writing_quality", "foreshadowing_integrity"],
                    "chapter_content": "$from_step_3.text",
                },
                "next": "next_step",
                "note": "审核初稿全文。不通过则修订后回到步骤5重新跑"
            },
            {
                "step_no": 8, "name": "等待审核完成",
                "tool": "discussion_room.get_updates",
                "params": {"session_id": "$from_step_7.session_id"},
                "next": "wait_for_async",
                "poll": {"interval": 5, "max_retries": 240, "field": "status", "until": "status IN ('completed','partial')"},
                "note": "⚠️ 禁止跳过。审核是必须环节，不通过不能提交。等多久都要等。",
            },
            {
                "step_no": 9, "name": "获取审核结论",
                "tool": "discussion_room.get_session",
                "params": {"session_id": "$from_step_7.session_id"},
                "next": "next_step",
            },
            {
                "step_no": 10, "name": "审核结论判定",
                "tool": "_agent_evaluate",
                "params": {
                    "instruction": "读取步骤9返回的 status 和 responses 数组。\n\n如果 status='partial'：遍历 responses 中所有 role='reviewer' 的 content，提取全部审查意见，去重后分类为「已解决」「未解决」「新增」，输出结构化报告。根据「未解决」修订正文，然后跳回步骤7(review.start_job)创建新审核 session。新 session 的 topic 追加「未解决问题列表+修订后正文」。无限循环直到共识达成。\n\n如果 status='completed' 且 consensus_reached=true：【必须先执行审核补充项，再进入下一步】。读取 summary 和 responses 中所有 role='reviewer' 的 content，提取所有「需补充」「需创建」「建议添加」的设定项，逐条执行：缺角色→调 state.entity.upsert(必须填name/summary/importance/profile)，缺地点→调 state.entity.upsert(必须填name/summary/importance)，缺伏笔→调 plot.upsert_foreshadowing(必须填key/title/importance/layer)，需正文微调→直接改动用 pipeline.generate 保存修订版。全部补充完成后才进入下一步(润色)。禁止跳过补充直接润色。"
                },
                "goto_step": 7,
                "goto_note": "跳回 step7 时 review.start_job 的 chapter_content 用修订后的最新正文，topic 追加未解决问题列表",
                "next": "next_step",
            },
            {
                "step_no": 11, "name": "润色终稿",
                "tool": "pipeline.generate",
                "params": {"workspace": workspace, "project": project, "chapter_no": chapter_no, "task_type": "polish", "content": "$from_step_3.text"},
                "next": "next_step",
                "note": "审核通过后润色。content 取步骤3的初稿（如果审核中修订过，用修订后正文）"
            },
            {
                "step_no": 12, "name": "保存终稿到本地",
                "tool": "_agent_evaluate",
                "params": {"instruction": "将步骤11润色后的终稿正文保存到本地文件。目录: chapters/第`chapter_no:02d`章/，文件名: ch`chapter_no:02d`_final.md。保存完整正文。"},
                "next": "next_step",
            },
            {
                "step_no": 13, "name": "提交章节",
                "tool": "workflow.submit_chapter_commit",
                "params": {"workspace": workspace, "project": project, "chapter_no": chapter_no, "title": "$title", "local_files": "$local_files", "commit": "$commit"},
                "next": "next_step",
            },
            {
                "step_no": 14, "name": "记录情绪节奏",
                "tool": "pacing.record_emotion",
                "params": {"workspace": workspace, "project": project, "project_id": project_id, "chapter_no": chapter_no, "tension": "$tension", "emotion": "$emotion", "emotion_intensity": "$intensity", "pacing_type": "$pacing_type"},
                "next": "next_step",
            },
            {
                "step_no": 15, "name": "维护角色弧光",
                "tool": "_agent_evaluate",
                "params": {"instruction": "根据本章内容，依次调用：1) arc.record_relationship 记录角色关系变化 2) arc.record_personality 记录性格演变 3) arc.record_power 记录实力变化（如无变化可跳过）"},
                "next": "next_step",
            },
            {
                "step_no": 16, "name": "维护情节线/伏笔",
                "tool": "_agent_evaluate",
                "params": {"instruction": "根据本章内容：1) 调 plot.thread.advance 推进涉及的情节线，必须传 thread_type(main/side)、current_chapter_no、progress_note(本章进展)；缺少 thread_type 的工具调用将被拒绝。2) 调 plot.thread.upsert 创建本章新出现的情节线，必须填 key、title、thread_type、importance。3) 调 plot.upsert_foreshadowing 记录本章新埋的伏笔，必须填 key、title、importance、layer。4) 调 foreshadowing.payoff 标记本章回收的伏笔"},
                "next": "wait_user_confirm",
            },
        ],
    }
    return ctx


@mcp.tool(name="workflow.validate_context_pack")
async def workflow_validate_context_pack(
    workspace: str,
    project: str,
    context_pack_id: str | None = None,
    chapter_no: int | None = None,
) -> dict[str, Any]:
    """验证上下文包完整性。检查上下文包的数据质量和一致性。"""
    principal = await get_principal("read")
    logger.info("workflow_validate_context_pack called")
    validate_required(locals(), "workspace", "project")
    project_id = await auth.resolve_project_id(workspace, project, principal)
    return await context_service.validate_context_pack(
        project_id=project_id,
        context_pack_id=context_pack_id,
        chapter_no=chapter_no,
    )


@mcp.tool(name="context.list_packs")
async def context_list_packs(
    workspace: str,
    project: str,
    chapter_no: int | None = None,
    purpose: str | None = None,
    limit: int = 50,
) -> list[dict[str, Any]]:
    """列出上下文包。可按章节和用途过滤，返回已生成的上下文包列表。"""
    principal = await get_principal("read")
    logger.info("context_list_packs called")
    validate_required(locals(), "workspace", "project")
    project_id = await auth.resolve_project_id(workspace, project, principal)
    return await context_service.list_context_packs(
        project_id=project_id,
        chapter_no=chapter_no,
        purpose=purpose,
        limit=limit,
    )


@mcp.tool(name="context.get_pack")
async def context_get_pack(
    workspace: str,
    project: str,
    context_pack_id: str | None = None,
    chapter_no: int | None = None,
) -> dict[str, Any]:
    """获取上下文包详情。可通过 ID 或章节号定位上下文包。"""
    principal = await get_principal("read")
    logger.info("context_get_pack called")
    validate_required(locals(), "workspace", "project")
    project_id = await auth.resolve_project_id(workspace, project, principal)
    return await context_service.get_context_pack(
        project_id=project_id,
        context_pack_id=context_pack_id,
        chapter_no=chapter_no,
    )


@mcp.tool(name="workflow.preflight_generation")
async def workflow_preflight_generation(
    workspace: str,
    project: str,
    chapter_no: int,
    purpose: str = "draft",
    focus: list[str] | None = None,
    budget: dict[str, Any] | None = None,
    volume_no: int | None = None,
    scope_refs: list[str] | None = None,
    scope_types: list[str] | None = None,
    active_event_keys: list[str] | None = None,
    pov_mode: str = "omniscient",
) -> dict[str, Any]:
    """生成前预检。验证生成条件、预算和上下文完整性，返回预检报告。"""
    principal = await get_principal("read")
    logger.info("workflow_preflight_generation called")
    validate_required(locals(), "workspace", "project", "chapter_no")
    project_id = await auth.resolve_project_id(workspace, project, principal)
    return await context_service.preflight_generation(
        project_id=project_id,
        chapter_no=chapter_no,
        purpose=purpose,
        focus=focus or [],
        budget=budget or {},
        volume_no=volume_no,
        scope_refs=scope_refs,
        scope_types=scope_types,
        active_event_keys=active_event_keys,
        pov_mode=pov_mode,
    )


@mcp.tool(name="workflow.prepare_segment_context")
async def workflow_prepare_segment_context(
    workspace: str,
    project: str,
    chapter_no: int,
    segment: str,
    purpose: str = "draft",
    focus: list[str] | None = None,
    budget: dict[str, Any] | None = None,
    volume_no: int | None = None,
    scope_refs: list[str] | None = None,
    scope_types: list[str] | None = None,
    active_event_keys: list[str] | None = None,
    pov_mode: str = "omniscient",
) -> dict[str, Any]:
    """为章节片段准备上下文。按 segment 分段生成上下文，支持细粒度控制。"""
    principal = await get_principal("read")
    logger.info("workflow_prepare_segment_context called")
    validate_required(locals(), "workspace", "project", "chapter_no", "segment")
    project_id = await auth.resolve_project_id(workspace, project, principal)
    return await context_service.prepare_segment_context(
        project_id=project_id,
        chapter_no=chapter_no,
        segment=segment,
        purpose=purpose,
        focus=focus or [],
        budget=budget or {},
        volume_no=volume_no,
        scope_refs=scope_refs,
        scope_types=scope_types,
        active_event_keys=active_event_keys,
        pov_mode=pov_mode,
    )


@mcp.tool(name="workflow.submit_chapter_commit")
async def workflow_submit_chapter_commit(
    workspace: str,
    project: str,
    chapter_no: int,
    title: str | None,
    local_files: list[dict[str, Any]],
    commit: dict[str, Any],
) -> dict[str, Any]:
    """提交章节完成确认。必须先完成审核（review.start_job）。"""
    principal = await get_principal("write")
    logger.info("workflow_submit_chapter_commit called")
    validate_required(locals(), "workspace", "project")
    project_id = await auth.resolve_project_id(workspace, project, principal, access="write")
    return await workflow_service.submit_chapter_commit(
        project_id=project_id,
        chapter_no=chapter_no,
        title=title,
        local_files=local_files,
        commit=commit,
        username=principal.username,
    )


@mcp.tool(name="workflow.list_audit_logs")
async def workflow_list_audit_logs(
    workspace: str,
    project: str,
    action: str | None = None,
    resource_type: str | None = None,
    limit: int = 50,
) -> list[dict[str, Any]]:
    """列出操作审计日志。可按操作类型和资源类型过滤。"""
    principal = await get_principal("read")
    logger.info("workflow_list_audit_logs called")
    validate_required(locals(), "workspace", "project")
    project_id = await auth.resolve_project_id(workspace, project, principal)
    return await workflow_service.list_audit_logs(
        project_id=project_id,
        action=action,
        resource_type=resource_type,
        limit=limit,
    )


@mcp.tool(name="workflow.validate_content")
async def workflow_validate_content(
    workspace: str,
    project: str,
    chapter_no: int,
    content: str,
) -> dict[str, Any]:
    """校验生成内容。检查禁词违规、角色存活、设定一致性和知识库一致性。"""
    principal = await get_principal("write")
    logger.info("workflow_validate_content called")
    validate_required(locals(), "workspace", "project", "chapter_no", "content")
    validate_length(locals(), {"content": 50000})
    project_id = await auth.resolve_project_id(workspace, project, principal, access="write")
    return await workflow_service.validate_generated_content(
        project_id=project_id,
        chapter_no=chapter_no,
        content=content,
    )


@mcp.tool(name="workflow.learn_from_review")
async def workflow_learn_from_review(
    workspace: str,
    project: str,
    review_job_id: str,
    create_revision_tasks: bool = True,
    create_rule_proposals: bool = True,
    block_on_critical: bool = True,
) -> dict[str, Any]:
    """从审核结果中学习。自动创建修订任务和规则提案，提升后续生成质量。"""
    principal = await get_principal("write")
    logger.info("workflow_learn_from_review called")
    validate_required(locals(), "workspace", "project", "review_job_id")
    project_id = await auth.resolve_project_id(workspace, project, principal, access="write")
    return await review_service.learn_from_review(
        project_id=project_id,
        review_job_id=review_job_id,
        username=principal.username,
        create_revision_tasks=create_revision_tasks,
        create_rule_proposals=create_rule_proposals,
        block_on_critical=block_on_critical,
    )


def _fmt_section(ctx: dict, key: str) -> str:
    """Format a context section as readable text."""
    data = ctx.get(key) or ctx.get("sections", {}).get(key) or []
    if not data:
        return "（无）"
    if isinstance(data, str):
        return data[:600]
    if isinstance(data, list):
        lines = []
        for item in data[:10]:
            if isinstance(item, dict):
                parts = []
                for k, v in item.items():
                    if v is not None and v != "" and k not in ("id", "project_id"):
                        s = str(v)
                        if len(s) > 150:
                            s = s[:150] + "..."
                        parts.append(f"{k}: {s}")
                lines.append("  - " + " | ".join(parts[:5]))
            else:
                lines.append(f"  - {item}")
        return "\n".join(lines) if lines else "（无）"
    return str(data)[:600]


@mcp.tool(name="workflow.get_chapter_generation_prompt")
async def workflow_get_chapter_generation_prompt(
    workspace: str,
    project: str,
    chapter_no: int,
    focus: list[str] | None = None,
    volume_no: int | None = None,
    pov_mode: str = "third_person_limited",
    pass_number: int = 2,
) -> dict[str, Any]:
    """生成章节创作的标准 Prompt。返回完整的流程指引和工具调用模板，
    可直接交给 subagent 执行章节生成任务。

    Args:
        workspace: 工作区
        project: 项目
        chapter_no: 章节号
        focus: 本章重点关注方向（角色、情节等）
        volume_no: 卷号
        pov_mode: 视角模式
        pass_number: 1=大纲 2=初稿 3=润色 4=验证

    Returns:
        prompt 字段可直接作为 subagent 系统提示词
    """
    principal = await get_principal("read")
    logger.info("workflow_get_chapter_generation_prompt: ch=%d", chapter_no)
    validate_required(locals(), "workspace", "project", "chapter_no")
    project_id = await auth.resolve_project_id(workspace, project, principal)

    # 1. 预检
    preflight = None
    try:
        preflight = await context_service.preflight_generation(
            project_id=project_id, chapter_no=chapter_no,
            purpose="draft", focus=focus or [], volume_no=volume_no,
            pov_mode=pov_mode,
        )
    except Exception:
        pass

    # 2. 上下文
    ctx = {}
    try:
        ctx = await context_service.prepare_chapter_context(
            project_id=project_id, chapter_no=chapter_no,
            purpose="draft", focus=focus or [], volume_no=volume_no,
            pov_mode=pov_mode, pass_number=pass_number,
        )
    except Exception:
        pass

    # 3. 项目信息
    proj = await db.fetchrow(
        "SELECT title, slug FROM projects WHERE id = $1", project_id
    )
    project_title = proj["title"] if proj else project
    project_slug = proj["slug"] if proj else project

    # 4. 章节信息
    ch_info = await db.fetchrow(
        "SELECT title, volume_no FROM chapters WHERE project_id = $1 AND chapter_no = $2",
        project_id, chapter_no,
    ) or {}
    vn = volume_no or ch_info.get("volume_no") or 1
    vol_info = await db.fetchrow(
        "SELECT title FROM volumes WHERE project_id = $1 AND volume_no = $2",
        project_id, vn,
    ) or {}

    # 5. 模型列表
    model_rows = await db.fetch(
        "SELECT profile_key, display_name, task_types, provider, model_name, rate_limit_config, tier FROM model_profiles WHERE status = 'active' ORDER BY is_default DESC, tier"
    )
    model_list = [{
        "key": r["profile_key"],
        "name": r["display_name"] or r["profile_key"],
        "tasks": r["task_types"] or [],
        "provider": r["provider"],
        "tier": r["tier"],
        "rate_limit": r["rate_limit_config"],
    } for r in model_rows]

    # 审核模型分析 + 用户委员会配置
    council_cfg = {}
    try:
        council = await db.fetchrow(
            "SELECT config FROM review_council_configs WHERE user_id = $1 AND is_active = true ORDER BY created_at DESC LIMIT 1",
            principal.username,
        )
        if council:
            cfg_raw = council["config"]
            if isinstance(cfg_raw, str): cfg_raw = json.loads(cfg_raw)
            council_cfg = cfg_raw
    except Exception: pass

    review_models = [m for m in model_list if "review" in (m.get("tasks") or [])]
    review_count = len(review_models)
    model_count = min(council_cfg.get("model_count", review_count), review_count)
    dims_per_model = council_cfg.get("dimensions_per_model", 1)
    review_mode = council_cfg.get("review_mode", "parallel")
    has_rate_limit = any(
        m.get("rate_limit") and isinstance(m["rate_limit"], dict)
        and (m.get("rate_limit", {}).get("requests_per_minute") or 0) < 10
        for m in review_models[:model_count]
    )
    if has_rate_limit and review_mode == "parallel":
        review_mode = "serial"  # force serial if rate limited

    if council_cfg:
        review_note = f"委员会配置：{model_count}个模型 × {dims_per_model}维度/模型（+AI痕迹），{review_mode}模式"
    else:
        # 自动生成默认配置：最多3个模型，每模型审核1维度，串行模式
        model_count = min(3, review_count) if review_count > 0 else 0
        dims_per_model = 1
        review_mode = "serial"
        review_note = f"自动默认：{model_count}个审核模型（最多3），每模型{dims_per_model}维度+AI痕迹，串行模式"

    # 7. 已有草稿
    existing_pass = await db.fetchrow(
        "SELECT pass_type, pass_number FROM generation_passes WHERE project_id = $1 AND chapter_no = $2 ORDER BY created_at DESC LIMIT 1",
        project_id, chapter_no,
    )

    # --- 构建 prompt ---
    vol_title = vol_info.get("title", f"第{vn}卷")
    ch_title = ch_info.get("title", f"第{chapter_no}章")
    folder_name = f"第{chapter_no:02d}章"
    task_name = ["大纲", "初稿", "润色", "验证"][min(pass_number - 1, 3)]
    file_name = f"ch{chapter_no:02d}_{['outline','draft','polish','review'][min(pass_number-1,3)]}.md"
    pol_name = f"ch{chapter_no:02d}_polish.md"

    # 审核维度
    dims = ["consistency", "quality", "pacing", "character", "ai_detection"]
    dim_labels = {"consistency": "一致性", "quality": "质量", "pacing": "节奏", "character": "角色", "ai_detection": "AI痕迹检测"}

    # 构建步骤列表
    steps = [
        {"step": 1, "name": "预检", "tool": "preflight_generation", "required": True},
        {"step": 2, "name": "上下文", "tool": "prepare_chapter_context", "required": True},
        {"step": 3, "name": "生成正文", "action": "创作", "required": True},
        {"step": 4, "name": "记录到系统", "tool": "pipeline.run_full", "required": True},
        {"step": 5, "name": "校验", "tool": "validate_content", "required": True},
        {"step": 6, "name": "保存本地文件", "action": "写入本地", "required": True},
        {"step": 7, "name": "审核-修订循环", "tool": "review.*", "required": True, "substeps": [
            {"step": "7.0", "tool": "review.list_council_configs → 空则 auto-config", "desc": "检查/自动配置审核委员会"},
            {"step": "7.1", "tool": "review.start_job", "desc": "启动审核"},
            {"step": "7.2", "tool": "review.submit_model_report", "desc": "各模型提交审核报告"},
            {"step": "7.3", "tool": "review.aggregate", "desc": "汇总，有意见→修订→回到7.1，无意见→继续"},
        ]},
        {"step": 8, "name": "提交完成", "tool": "submit_chapter_commit", "required": True},
        {"step": 9, "name": "维护", "tool": "多工具", "required": True},
        {"step": 10, "name": "从审核学习", "tool": "learn_from_review", "optional": True},
        {"step": 11, "name": "压缩上下文", "tool": "auto_compress", "optional": True},
    ]

    # 审核委员会信息
    review_info_lines = []
    if review_models:
        review_info_lines.append(f"审核委员会：{model_count}个模型 ({review_mode}模式)")
        for m in review_models[:model_count]:
            info = f"  - {m['key']} ({m['name']})"
            rl = m.get("rate_limit")
            if rl and isinstance(rl, dict):
                info += f" [限制:{rl.get('requests_per_minute','?')}rpm]"
            review_info_lines.append(info)
    else:
        review_info_lines.append("未配置审核模型")

    # 构建 prompt
    prompt = f"""# 章节创作任务：{project_title}

## 基本信息
- 项目: {project_slug}
- 卷: {vol_title}
- 章节: {ch_title}
- 任务类型: {task_name}
- 视角: {pov_mode}
- 本地文件: {folder_name}/{file_name}
- 润色文件: {folder_name}/{pol_name}
{'（此章已有草稿，正在续写/修改）' if existing_pass else '（首次创作此章）'}

## 可用模型
{chr(10).join(f"- {m['name']} ({m['provider']}) : {', '.join(m['tasks'])}" for m in model_list) if model_list else '⚠️ 未配置模型'}

## 预检报告
{('✅ 上下文完整性: 第' + str(preflight.get('total_sections_loaded', '')) + '/' + str(preflight.get('total_sections', '')) + ' 节' if preflight and preflight.get('total_sections') else '⚠️ 预检跳过' ) if preflight else '⚠️ 预检不可用'}
{('⚠️ 阻塞问题: ' + str(len(preflight.get('blocking_issues', [])))) if preflight and preflight.get('blocking_issues') else ''}

## 上下文

### 1. 当前角色状态
{_fmt_section(ctx, 'current_state')}

### 2. 活跃规则
{_fmt_section(ctx, 'active_rules')}

### 3. 设定文档
{_fmt_section(ctx, 'canon_documents')}

### 4. 实体关系
{_fmt_section(ctx, 'entity_relationships')}

### 5. 活跃伏笔
{_fmt_section(ctx, 'open_foreshadowing')}

### 6. 近期章节摘要
{_fmt_section(ctx, 'recent_summaries')}

### 7. 章节规划
{_fmt_section(ctx, 'chapter_plan')}

### 8. 节奏指引
{_fmt_section(ctx, 'pacing_guidance')}

### 9. 风格指引
{_fmt_section(ctx, 'style_guidance')}

### 10. 停滞线程警告
{_fmt_section(ctx, 'stalled_threads')}

### 11. 阻塞问题
{_fmt_section(ctx, 'blocking_issues')}

### 12. 写作知识
{_fmt_section(ctx, 'global_settings')}

## 执行步骤

按每个工具的 `workflow_guide.next_tool` 依次执行：
preflight → context → 创作 → record → validate → 存本地 → review循环 → commit → 维护 → 学习 → 压缩

### 步骤 4：记录到系统（只传元数据，不传正文！）
```
pipeline.run_full(
  workspace: "{workspace}",
  project: "{project_slug}",
  chapter_no: {chapter_no},
  plan: {{"summary": "大纲摘要"}},
  draft_content: "正文前200字摘要"  # ⚠️ 只传摘要，不传全文
)
```

### 步骤 7：审核-修订循环（讨论室多模型辩论模式）

7.1 启动审核任务（自动创建讨论室）
```
review.start_job(
  workspace: "{workspace}",
  project: "{project_slug}",
  chapter_no: {chapter_no},
  dimensions: {json.dumps(dims, ensure_ascii=False)}
)
```
→ 系统自动收集审核上下文 → 启动讨论室多模型辩论
→ 输出 session_id 和 review_job_id

7.2 查看讨论结果
```
review.aggregate(review_job_id="<7.1的review_job_id>")
→ 或 discussion_room.get_session(session_id="<7.1的session_id>")
→ 读取 summary 获取审查结论
```

7.3 根据结论处理
→ 有修改意见 → 修订正文 → 回到 7.1（最多3轮）
→ 无意见 → 7.4 润色

7.4 系统润色
```
pipeline.generate(
  workspace: "{workspace}",
  project: "{project_slug}",
  chapter_no: {chapter_no},
  task_type: "polish",
  content: "正文全文",
  user_prompt: "请润色以下章节，提升文笔质量"
)
```
→ 系统自动选 polish 模型生成润色版 → 保存到 {folder_name}/{pol_name}

### 步骤 8：提交完成
```
workflow.submit_chapter_commit(
  workspace: "{workspace}",
  project: "{project_slug}",
  chapter_no: {chapter_no},
  title: "{ch_title}",
  local_files: [{{"path": "{folder_name}/{file_name}"}}],
  commit: {{"pass_number": {pass_number}}}
)
```

> **重要**：步骤4只传摘要不传全文。步骤7正文传LLM不存库。
"""

    return {
        "ok": True,
        "chapter_no": chapter_no,
        "project_title": project_title,
        "project_slug": project_slug,
        "prompt": prompt,
        "context_pack_id": ctx.get("_pack_id"),
        "file_hint": {
            "folder": folder_name,
            "filename": file_name,
            "polish_filename": pol_name,
        },
        "review_config": {
            "has_council": bool(council_cfg),
            "reviewers": [m["key"] for m in review_models[:model_count]],
            "dimensions": dims,
        },
        "steps": steps,
        "workflow_guide": {
            "phase": "章节生成",
            "next_tool": "preflight_generation",
            "description": f"第{chapter_no}章完整流程已生成，prompt 字段可直接作为 subagent 提示词",
        },
    }


# ============================================================
# 交互式分步引导系统
# ============================================================

MAX_SESSIONS_PER_PROJECT = 3

CHAPTER_STEPS = [
    {"id": 1,  "name": "预检",         "tool": "workflow.preflight_generation",     "required": True,  "description": "检查角色存活、预算、上下文完整性"},
    {"id": 2,  "name": "获取上下文",    "tool": "workflow.prepare_chapter_context",  "required": True,  "description": "获取包含规则、状态、伏笔等 18 个 section 的上下文包"},
    {"id": 3,  "name": "创作正文",      "tool": None,                                 "required": True,  "description": "根据上下文生成 2500-4000 字章节正文"},
    {"id": 4,  "name": "记录元数据",    "tool": "pipeline.run_full",                  "required": True,  "description": "传入 draft_content=摘要（不传全文）记录到 generation_passes"},
    {"id": 5,  "name": "校验内容",      "tool": "workflow.validate_content",          "required": True,  "description": "检查禁词违规、设定一致性"},
    {"id": 6,  "name": "保存本地文件",  "tool": None,                                 "required": True,  "description": "将正文写入本地文件"},
    {"id": 7,  "name": "审核修订循环",  "tool": "review.start_job",                   "required": True,  "description": "auto-config→审核→意见→修订→再审核，循环至无意见"},
    {"id": 8,  "name": "提交完成",      "tool": "workflow.submit_chapter_commit",     "required": True,  "description": "提交章节并标记完成"},
    {"id": 9,  "name": "维护",          "tool": "多工具",                             "required": True,  "description": "记录弧光、更新世界状态、推进剧情线"},
    {"id": 10, "name": "从审核学习",    "tool": "workflow.learn_from_review",         "optional": True,  "description": "从审核结果提取规则改进建议"},
    {"id": 11, "name": "压缩上下文",    "tool": "context_compression.auto_compress",  "optional": True,  "description": "压缩本章为摘要供后续使用"},
]

@mcp.tool(name="workflow.start_chapter_generation")
async def workflow_start_chapter_generation(
    workspace: str, project: str, chapter_no: int,
    focus: list[str] | None = None, volume_no: int | None = None,
    pov_mode: str = "third_person_limited",
) -> dict[str, Any]:
    principal = await get_principal("read")
    validate_required(locals(), "workspace", "project", "chapter_no")
    project_id = await auth.resolve_project_id(workspace, project, principal)
    session_id = uuid.uuid4().hex[:16]
    await db.execute("DELETE FROM workflow_sessions WHERE project_id=$1 AND id NOT IN (SELECT id FROM workflow_sessions WHERE project_id=$1 AND status='active' ORDER BY chapter_no DESC,created_at DESC LIMIT $2) AND updated_at<NOW()-INTERVAL'24 hours'", project_id, MAX_SESSIONS_PER_PROJECT)
    steps_json = json_dumps([dict(s) for s in CHAPTER_STEPS])
    await db.execute("INSERT INTO workflow_sessions(id,workspace,project,project_id,chapter_no,current_step,total_steps,steps,history,focus,volume_no,pov_mode,status) VALUES($1,$2,$3,$4,$5,1,$6,$7::jsonb,'[]'::jsonb,$8,$9,$10,'active')", session_id, workspace, project, project_id, chapter_no, len(CHAPTER_STEPS), steps_json, focus or [], volume_no, pov_mode)
    return {"session_id": session_id, "step": 1, "total_steps": len(CHAPTER_STEPS), "status": "active", "instruction": _step_text(workspace, project, chapter_no, 1)}

@mcp.tool(name="workflow.next_step")
async def workflow_next_step(session_id: str, result: dict[str, Any] | None = None) -> dict[str, Any]:
    row = await db.fetchrow("SELECT * FROM workflow_sessions WHERE id=$1 AND status='active'", session_id)
    if not row:
        raise ValueError(f"会话 {session_id} 不存在或已过期")
    s = dict(row)
    cur = s["current_step"]
    steps = json.loads(s["steps"])
    history = json.loads(s["history"])
    history.append({"step": cur, "name": steps[cur - 1]["name"], "result": result, "at": datetime.utcnow().isoformat()})

    ok, err = await _validate_step_db(s["project_id"], s["chapter_no"], cur)
    if not ok:
        await db.execute("UPDATE workflow_sessions SET history=$1::jsonb,updated_at=now() WHERE id=$2", json_dumps(history), session_id)
        return {"session_id": session_id, "step": cur, "name": steps[cur - 1]["name"], "status": "failed", "error": err}

    nxt = cur + 1
    await db.execute("UPDATE workflow_sessions SET current_step=$1,history=$2::jsonb,updated_at=now() WHERE id=$3", nxt, json_dumps(history), session_id)
    if nxt > s["total_steps"]:
        return await _complete_session(session_id)
    return {"session_id": session_id, "step": nxt, "total_steps": s["total_steps"], "status": "active", "instruction": _step_text(s["workspace"], s["project"], s["chapter_no"], nxt)}

@mcp.tool(name="workflow.jump_to_step")
async def workflow_jump_to_step(session_id: str, step_no: int) -> dict[str, Any]:
    row = await db.fetchrow("SELECT * FROM workflow_sessions WHERE id=$1", session_id)
    if not row or step_no < 1 or step_no > row["total_steps"]:
        raise ValueError(f"无效步骤 {step_no}")
    await db.execute("UPDATE workflow_sessions SET current_step=$1,status='active',updated_at=now() WHERE id=$2", step_no, session_id)
    return {"session_id": session_id, "step": step_no, "status": "active"}

@mcp.tool(name="workflow.get_current_step")
async def workflow_get_current_step(session_id: str) -> dict[str, Any]:
    row = await db.fetchrow("SELECT * FROM workflow_sessions WHERE id=$1", session_id)
    if not row:
        raise ValueError(f"会话 {session_id} 不存在")
    s = dict(row)
    if s["current_step"] > s["total_steps"]:
        return await _complete_session(session_id)
    return {"session_id": session_id, "current_step": s["current_step"], "total_steps": s["total_steps"], "status": s["status"], "instruction": _step_text(s["workspace"], s["project"], s["chapter_no"], s["current_step"])}

@mcp.tool(name="workflow.pause_session")
async def workflow_pause_session(session_id: str) -> dict[str, Any]:
    await db.execute("UPDATE workflow_sessions SET status='paused',updated_at=now() WHERE id=$1", session_id)
    return {"ok": True, "session_id": session_id, "status": "paused"}

@mcp.tool(name="workflow.resume_session")
async def workflow_resume_session(session_id: str) -> dict[str, Any]:
    r = await db.fetchrow("UPDATE workflow_sessions SET status='active',updated_at=now() WHERE id=$1 AND status='paused' RETURNING chapter_no,current_step", session_id)
    if not r:
        raise ValueError(f"会话 {session_id} 不存在或未暂停")
    return {"ok": True, "session_id": session_id, "chapter_no": r["chapter_no"], "current_step": r["current_step"]}

@mcp.tool(name="workflow.list_sessions")
async def workflow_list_sessions(workspace: str, project: str) -> list[dict[str, Any]]:
    principal = await get_principal("read")
    validate_required(locals(), "workspace", "project")
    project_id = await auth.resolve_project_id(workspace, project, principal)
    rows = await db.fetch("SELECT id,chapter_no,current_step,total_steps,status,created_at,updated_at FROM workflow_sessions WHERE project_id=$1 ORDER BY chapter_no DESC,created_at DESC LIMIT 10", project_id)
    return [dict(r) for r in rows]

@mcp.tool(name="workflow.abort_chapter_generation")
async def workflow_abort_chapter_generation(session_id: str) -> dict[str, Any]:
    await db.execute("UPDATE workflow_sessions SET status='aborted',updated_at=now() WHERE id=$1", session_id)
    return {"ok": True}

async def _validate_step_db(project_id: str, chapter_no: int, step: int) -> tuple[bool, str]:
    if step == 4:
        r = await db.fetchrow("SELECT id FROM generation_passes WHERE project_id=$1 AND chapter_no=$2 LIMIT 1", project_id, chapter_no)
        return (r is not None, "未找到 generation_passes 记录")
    if step == 7:
        ch = await db.fetchrow("SELECT id FROM chapters WHERE project_id=$1 AND chapter_no=$2", project_id, chapter_no)
        if ch:
            j = await db.fetchrow("SELECT status FROM review_jobs WHERE project_id=$1 AND chapter_id=$2 ORDER BY created_at DESC LIMIT 1", project_id, ch["id"])
            if j:
                return (j["status"] in ("completed", "aggregated"), f"审核状态为 {j['status']}")
        return (False, "未找到审核任务")
    if step == 9:
        ch = await db.fetchrow("SELECT status FROM chapters WHERE project_id=$1 AND chapter_no=$2", project_id, chapter_no)
        return (ch and ch["status"] == "completed", "章节未标记为 completed")
    return (True, "")


def _step_text(ws: str, proj: str, ch: int, step: int) -> str:
    texts = {
        1: f"调 preflight_generation(workspace={ws}, project={proj}, chapter_no={ch}) 检查角色存活、预算、上下文完整性",
        2: f"调 prepare_chapter_context(workspace={ws}, project={proj}, chapter_no={ch}) 获取上下文包",
        3: "根据上下文生成 2500-4000 字章节正文",
        4: f"调 pipeline.run_full(workspace={ws}, project={proj}, chapter_no={ch}, draft_content=摘要) 只传摘要不传全文",
        5: f"调 workflow.validate_content(workspace={ws}, project={proj}, chapter_no={ch}, content=摘要)",
        6: f"保存正文到本地 第{ch:02d}章/ch{ch:02d}_draft.md",
        7: f"审核-修订循环: auto-config→review.start_job→submit→aggregate→有意见则修订→再审核，直到无意见",
        8: f"调 workflow.submit_chapter_commit(workspace={ws}, project={proj}, chapter_no={ch}, title='第{ch}章', local_files=[{{'path': '第{ch:02d}章/ch{ch:02d}_draft.md'}}], commit={{'pass_number': 2}})",
        9: "维护: arc/kb.world/plot.thread/foreshadowing",
        10: "调 workflow.learn_from_review",
        11: f"调 context_compression.auto_compress(chapter_no={ch})",
    }
    return texts.get(step, "未知步骤")


async def _complete_session(session_id: str) -> dict:
    await db.execute("UPDATE workflow_sessions SET status='completed',updated_at=now() WHERE id=$1", session_id)
    row = await db.fetchrow("SELECT chapter_no,total_steps FROM workflow_sessions WHERE id=$1", session_id)
    return {"session_id": session_id, "step": "complete", "chapter_no": row["chapter_no"] if row else 0, "summary": {"total": row["total_steps"] if row else 0}, "workflow_guide": {"phase": "完成"}}


@mcp.tool(name="chapter.reset")
async def chapter_reset(
    workspace: str,
    project: str,
    chapter_no: int,
    keep_entities: bool = True,
) -> dict[str, Any]:
    """重置章节：删除该章节的所有辅助数据（审核、节奏、弧光、摘要等），以便重新生成。

    keep_entities=True 时保留该章创建的角色/势力/地点等实体，只清过程数据。
    keep_entities=False 时也会删除该章的状态快照。

    Args:
        workspace: 工作区
        project: 项目
        chapter_no: 要重置的章节号
        keep_entities: 是否保留实体（默认保留）
    """
    principal = await get_principal("write")
    logger.info("chapter.reset called: ch=%d", chapter_no)
    validate_required(locals(), "workspace", "project", "chapter_no")
    project_id = await auth.resolve_project_id(workspace, project, principal, access="write")

    # 获取 chapter_id
    ch = await db.fetchrow(
        "SELECT id FROM chapters WHERE project_id = $1 AND chapter_no = $2",
        project_id, chapter_no,
    )
    chapter_id = ch["id"] if ch else None

    deleted = {}

    # 1. generation_passes
    r = await db.execute("DELETE FROM generation_passes WHERE project_id = $1 AND chapter_no = $2", project_id, chapter_no)
    deleted["generation_passes"] = str(r).split()[-1] if r else "0"

    # 2. chapter_plans
    r = await db.execute("DELETE FROM chapter_plans WHERE project_id = $1 AND chapter_no = $2", project_id, chapter_no)
    deleted["chapter_plans"] = str(r).split()[-1] if r else "0"

    # 3. chapter_emotions
    r = await db.execute("DELETE FROM chapter_emotions WHERE project_id = $1 AND chapter_no = $2", project_id, chapter_no)
    deleted["chapter_emotions"] = str(r).split()[-1] if r else "0"

    # 4. chapter_style_metrics
    r = await db.execute("DELETE FROM chapter_style_metrics WHERE project_id = $1 AND chapter_no = $2", project_id, chapter_no)
    deleted["chapter_style_metrics"] = str(r).split()[-1] if r else "0"

    # 5. chapter_summaries (需要 JOIN chapters)
    if chapter_id:
        r = await db.execute("DELETE FROM chapter_summaries WHERE chapter_id = $1", chapter_id)
        deleted["chapter_summaries"] = str(r).split()[-1] if r else "0"

    # 6. review_jobs + review_reports
    if chapter_id:
        await db.execute("DELETE FROM review_reports WHERE review_job_id IN (SELECT id FROM review_jobs WHERE chapter_id = $1)", chapter_id)
        r = await db.execute("DELETE FROM review_jobs WHERE chapter_id = $1", chapter_id)
        deleted["review_jobs"] = str(r).split()[-1] if r else "0"

    # 7. chapter_commits
    if chapter_id:
        r = await db.execute("DELETE FROM chapter_commits WHERE chapter_id = $1", chapter_id)
        deleted["chapter_commits"] = str(r).split()[-1] if r else "0"

    # 8. character_arcs
    r = await db.execute("DELETE FROM character_arcs WHERE project_id = $1 AND chapter_no = $2", project_id, chapter_no)
    deleted["character_arcs"] = str(r).split()[-1] if r else "0"

    # 9. causality_chains
    r = await db.execute(
        "DELETE FROM causality_chains WHERE project_id = $1 AND (cause_chapter_no = $2 OR effect_chapter_no = $2)",
        project_id, chapter_no,
    )
    deleted["causality_chains"] = str(r).split()[-1] if r else "0"

    # 10. world_snapshots
    r = await db.execute("DELETE FROM world_snapshots WHERE project_id = $1 AND chapter_no = $2", project_id, chapter_no)
    deleted["world_snapshots"] = str(r).split()[-1] if r else "0"

    # 11. context_packs
    r = await db.execute("DELETE FROM context_packs WHERE project_id = $1 AND chapter_no = $2", project_id, chapter_no)
    deleted["context_packs"] = str(r).split()[-1] if r else "0"

    # 12. compressed_contexts
    r = await db.execute(
        "DELETE FROM compressed_contexts WHERE project_id = $1 AND (chapter_range_start <= $2 AND (chapter_range_end IS NULL OR chapter_range_end >= $2))",
        project_id, chapter_no,
    )
    deleted["compressed_contexts"] = str(r).split()[-1] if r else "0"

    # 13. foreshadowing (only in this chapter)
# 13. foreshadowing - 跳过，没有 chapter_no 列，不影响重置

    # 14. state_snapshots (optional)
    if not keep_entities and chapter_id:
        r = await db.execute("DELETE FROM state_snapshots WHERE project_id = $1 AND effective_chapter_no = $2", project_id, chapter_no)
        deleted["state_snapshots"] = str(r).split()[-1] if r else "0"

    # 15. chapters
    if chapter_id:
        await db.execute("DELETE FROM chapters WHERE id = $1", chapter_id)
        deleted["chapters"] = "1"

    # 16. workflow_sessions
    await db.execute(
        "DELETE FROM workflow_sessions WHERE project_id = $1 AND chapter_no = $2",
        project_id, chapter_no,
    )
    deleted["workflow_sessions"] = "1"

    return {
        "ok": True,
        "chapter_no": chapter_no,
        "deleted": deleted,
        "message": f"第{chapter_no}章数据已重置，{'(实体已保留)' if keep_entities else '（实体已清理）'}",
        "keep_entities": keep_entities,
    }


@mcp.tool(name="project.reset")
async def project_reset(
    workspace: str,
    project: str,
    keep_entities: bool = True,
    delete_local_files: bool = True,
) -> dict[str, Any]:
    """重置项目：清空所有章节数据、审核、弧光、世界状态等，删除本地文件，保留项目、模型配置、用户设定。

    keep_entities=True 保留角色/势力/地点等实体定义。
    delete_local_files=True 同时删除 NAS 上的章节文件。

    Args:
        workspace: 工作区
        project: 项目
        keep_entities: 是否保留实体（默认保留）
        delete_local_files: 是否删除本地文件（默认删除）
    """
    principal = await get_principal("write")
    logger.info("project.reset called: ws=%s, proj=%s", workspace, project)
    validate_required(locals(), "workspace", "project")
    project_id = await auth.resolve_project_id(workspace, project, principal, access="write")

    import os, shutil

    # 1. Get all chapters
    chapters = await db.fetch(
        "SELECT chapter_no FROM chapters WHERE project_id = $1 ORDER BY chapter_no",
        project_id,
    )
    chapter_nos = [r["chapter_no"] for r in chapters]

    # 2. Reset each chapter
    chapter_results = {}
    for ch_no in chapter_nos:
        try:
            from .context import chapter_reset
            r = await chapter_reset(workspace, project, ch_no, keep_entities=keep_entities)
            chapter_results[str(ch_no)] = r.get("deleted", {})
        except Exception as e:
            chapter_results[str(ch_no)] = {"error": str(e)}

    # 3. Delete project-level data
    deleted_project = {}

    r = await db.execute("DELETE FROM foreshadowing WHERE project_id = $1", project_id)
    deleted_project["foreshadowing"] = str(r).split()[-1] if r else "0"

    r = await db.execute("DELETE FROM plot_threads WHERE project_id = $1", project_id)
    deleted_project["plot_threads"] = str(r).split()[-1] if r else "0"

    r = await db.execute("DELETE FROM chapter_plans WHERE project_id = $1", project_id)
    deleted_project["chapter_plans"] = str(r).split()[-1] if r else "0"

    r = await db.execute("DELETE FROM world_snapshots WHERE project_id = $1", project_id)
    deleted_project["world_snapshots"] = str(r).split()[-1] if r else "0"

    r = await db.execute("DELETE FROM context_packs WHERE project_id = $1", project_id)
    deleted_project["context_packs"] = str(r).split()[-1] if r else "0"

    r = await db.execute("DELETE FROM compressed_contexts WHERE project_id = $1", project_id)
    deleted_project["compressed_contexts"] = str(r).split()[-1] if r else "0"

    r = await db.execute("DELETE FROM causality_chains WHERE project_id = $1", project_id)
    deleted_project["causal_chains"] = str(r).split()[-1] if r else "0"

    r = await db.execute("DELETE FROM character_arcs WHERE project_id = $1", project_id)
    deleted_project["character_arcs"] = str(r).split()[-1] if r else "0"

    r = await db.execute("DELETE FROM chapter_emotions WHERE project_id = $1", project_id)
    deleted_project["chapter_emotions"] = str(r).split()[-1] if r else "0"

    r = await db.execute("DELETE FROM chapter_style_metrics WHERE project_id = $1", project_id)
    deleted_project["chapter_style_metrics"] = str(r).split()[-1] if r else "0"

    r = await db.execute("DELETE FROM workflow_sessions WHERE project_id = $1", project_id)
    deleted_project["workflow_sessions"] = str(r).split()[-1] if r else "0"

    # audit_logs has no project_id column — skip

    if not keep_entities:
        r = await db.execute("DELETE FROM state_snapshots WHERE project_id = $1", project_id)
        deleted_project["state_snapshots"] = str(r).split()[-1] if r else "0"
        r = await db.execute("DELETE FROM state_entities WHERE project_id = $1", project_id)
        deleted_project["state_entities"] = str(r).split()[-1] if r else "0"
        r = await db.execute("DELETE FROM entity_relationships WHERE project_id = $1", project_id)
        deleted_project["entity_relationships"] = str(r).split()[-1] if r else "0"

    # Reset volumes to planned
    await db.execute("UPDATE volumes SET status='planned', start_chapter_no=NULL, end_chapter_no=NULL WHERE project_id=$1", project_id)

    # 4. Delete local files
    local_files_deleted = 0
    if delete_local_files:
        try:
            from ..local_service import LocalService
            svc = LocalService(db)
            proj_info = await svc.get_project(project_id)
            if proj_info:
                local_root = proj_info["local_root"]
                for ch_no in chapter_nos:
                    folder = f"第{ch_no:02d}章"
                    folder_path = os.path.join(local_root, folder)
                    if os.path.exists(folder_path):
                        shutil.rmtree(folder_path)
                        local_files_deleted += 1
                # Also delete the project index
                index_path = os.path.join(local_root, ".novel-index.json")
                if os.path.exists(index_path):
                    os.remove(index_path)
        except Exception as e:
            logger.warning("Failed to delete local files: %s", e)

    return {
        "ok": True,
        "project": project,
        "chapters_reset": len(chapter_nos),
        "chapters_detail": chapter_results,
        "project_data_deleted": deleted_project,
        "local_folders_deleted": local_files_deleted,
        "keep_entities": keep_entities,
        "message": f"项目已重置：{len(chapter_nos)} 章已清理，本地文件已{'删除' if delete_local_files else '保留'}，实体已{'保留' if keep_entities else '清理'}",
    }
