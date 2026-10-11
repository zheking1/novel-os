import logging
import json
from typing import Any

from ..mcp_core import mcp
from ..deps import db, auth, llm_client, memory_service, multipass_service, review_service, causality_service, character_arc_service, novelty_service, pacing_service, style_fingerprint_service
from ..tool_auth import get_principal, validate_required

logger = logging.getLogger("novel_os_mcp.tools.novel_gen")


@mcp.tool(name="arc.record_emotion")
async def arc_record_emotion(
    workspace: str,
    project: str,
    project_id: str,
    character_name: str,
    chapter_no: int,
    emotion: str,
    intensity: float,
    cause: str | None = None,
) -> dict[str, Any]:
    """记录角色的情绪状态变化。"""
    logger.info("arc.record_emotion: ws=%s prj=%s ch=%d char=%s emotion=%s intensity=%.2f", workspace, project, chapter_no, character_name, emotion, intensity)
    principal = await get_principal("write")
    project_id = await auth.resolve_project_id(workspace, project, principal, access="write")
    logger.info("arc.record_emotion called")
    validate_required(locals(), "character_name", "emotion", "intensity")
    return await character_arc_service.record_emotion(
        project_id=project_id,
        character_name=character_name,
        chapter_no=chapter_no,
        emotion=emotion,
        intensity=intensity,
        cause=cause,
    )


@mcp.tool(name="arc.record_relationship")
async def arc_record_relationship(
    workspace: str,
    project: str,
    project_id: str,
    character_name: str,
    chapter_no: int,
    target_name: str,
    old_relation: str,
    new_relation: str,
    cause: str | None = None,
) -> dict[str, Any]:
    """记录角色关系变化。"""
    logger.info("arc.record_relationship: ws=%s prj=%s ch=%d char=%s target=%s %s->%s", workspace, project, chapter_no, character_name, target_name, old_relation, new_relation)
    principal = await get_principal("write")
    project_id = await auth.resolve_project_id(workspace, project, principal, access="write")
    logger.info("arc.record_relationship called")
    validate_required(locals(), "workspace", "project", "project_id", "character_name", "chapter_no", "target_name", "old_relation", "new_relation")
    return await character_arc_service.record_relationship_change(
        project_id=project_id,
        character_name=character_name,
        chapter_no=chapter_no,
        target_name=target_name,
        old_relation=old_relation,
        new_relation=new_relation,
        cause=cause,
    )


@mcp.tool(name="arc.record_power")
async def arc_record_power(
    workspace: str,
    project: str,
    project_id: str,
    character_name: str,
    chapter_no: int,
    old_level: str,
    new_level: str,
    method: str | None = None,
    note: str | None = None,
) -> dict[str, Any]:
    """记录角色实力变化。"""
    logger.info("arc.record_power: ws=%s prj=%s ch=%d char=%s %s->%s", workspace, project, chapter_no, character_name, old_level, new_level)
    principal = await get_principal("write")
    project_id = await auth.resolve_project_id(workspace, project, principal, access="write")
    logger.info("arc.record_power called")
    validate_required(locals(), "workspace", "project", "project_id", "character_name", "chapter_no", "old_level", "new_level")
    return await character_arc_service.record_power_change(
        project_id=project_id,
        character_name=character_name,
        chapter_no=chapter_no,
        old_level=old_level,
        new_level=new_level,
        method=method,
    )


@mcp.tool(name="arc.record_personality")
async def arc_record_personality(
    workspace: str,
    project: str,
    project_id: str,
    character_name: str,
    chapter_no: int,
    trait: str,
    old_value: Any,
    new_value: Any,
    reason: str | None = None,
) -> dict[str, Any]:
    """记录角色性格变化。"""
    logger.info("arc.record_personality: ws=%s prj=%s ch=%d char=%s trait=%s", workspace, project, chapter_no, character_name, trait)
    principal = await get_principal("write")
    project_id = await auth.resolve_project_id(workspace, project, principal, access="write")
    logger.info("arc.record_personality called")
    validate_required(locals(), "workspace", "project", "project_id", "character_name", "chapter_no", "trait", "old_value", "new_value")
    return await character_arc_service.record_personality_shift(
        project_id=project_id,
        character_name=character_name,
        chapter_no=chapter_no,
        trait=trait,
        old_value=old_value,
        new_value=new_value,
        reason=reason,
    )


@mcp.tool(name="arc.record_point")
async def arc_record_point(
    workspace: str,
    project: str,
    project_id: str,
    character_name: str,
    chapter_no: int,
    arc_type: str,
    state: dict[str, Any],
    change_summary: str | None = None,
    trigger_event: str | None = None,
    metadata: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """记录通用角色弧光点。用于记录任意类型的弧光状态快照，支持自定义弧光类型和元数据。"""
    principal = await get_principal("write")
    project_id = await auth.resolve_project_id(workspace, project, principal, access="write")
    logger.info("arc.record_point called")
    validate_required(locals(), "workspace", "project", "project_id", "character_name", "chapter_no", "arc_type", "state")
    return await character_arc_service.record_arc_point(
        project_id=project_id,
        character_name=character_name,
        chapter_no=chapter_no,
        arc_type=arc_type,
        state=state,
        change_summary=change_summary,
        trigger_event=trigger_event,
        metadata=metadata,
    )


@mcp.tool(name="arc.get_character")
async def arc_get_character(
    workspace: str,
    project: str,
    project_id: str,
    character_name: str,
    arc_type: str | None = None,
    from_chapter: int | None = None,
    to_chapter: int | None = None,
    limit: int = 100,
) -> list[dict[str, Any]]:
    """获取角色弧光历史。按章节范围和弧光类型查询角色的所有弧光记录。"""
    principal = await get_principal("read")
    project_id = await auth.resolve_project_id(workspace, project, principal, access="read")
    logger.info("arc.get_character called")
    validate_required(locals(), "workspace", "project", "project_id", "character_name")
    return await character_arc_service.get_character_arc(
        project_id=project_id,
        character_name=character_name,
        arc_type=arc_type,
        from_chapter=from_chapter,
        to_chapter=to_chapter,
        limit=limit,
    )


@mcp.tool(name="arc.get_latest_state")
async def arc_get_latest_state(
    workspace: str,
    project: str,
    project_id: str,
    character_name: str,
) -> dict[str, Any]:
    """获取角色最新弧光状态。返回角色所有弧光类型的最新状态快照。"""
    principal = await get_principal("read")
    project_id = await auth.resolve_project_id(workspace, project, principal, access="read")
    logger.info("arc.get_latest_state called")
    validate_required(locals(), "workspace", "project", "project_id", "character_name")
    return await character_arc_service.get_latest_arc_state(
        project_id=project_id,
        character_name=character_name,
    )


@mcp.tool(name="arc.get_emotion_timeline")
async def arc_get_emotion_timeline(
    workspace: str,
    project: str,
    project_id: str,
    character_name: str,
    from_chapter: int | None = None,
    to_chapter: int | None = None,
) -> list[dict[str, Any]]:
    """获取角色情感时间线。返回指定章节范围内角色的情感变化序列。"""
    principal = await get_principal("read")
    project_id = await auth.resolve_project_id(workspace, project, principal, access="read")
    logger.info("arc.get_emotion_timeline called")
    validate_required(locals(), "workspace", "project", "project_id", "character_name")
    return await character_arc_service.get_emotion_timeline(
        project_id=project_id,
        character_name=character_name,
        from_chapter=from_chapter,
        to_chapter=to_chapter,
    )


@mcp.tool(name="arc.get_power_progression")
async def arc_get_power_progression(
    workspace: str,
    project: str,
    project_id: str,
    character_name: str,
) -> list[dict[str, Any]]:
    """获取角色实力成长时间线。返回角色修为/技能等级的完整变化历程。"""
    principal = await get_principal("read")
    project_id = await auth.resolve_project_id(workspace, project, principal, access="read")
    logger.info("arc.get_power_progression called")
    validate_required(locals(), "workspace", "project", "project_id", "character_name")
    return await character_arc_service.get_power_progression(
        project_id=project_id,
        character_name=character_name,
    )


@mcp.tool(name="arc.get_relationship_evolution")
async def arc_get_relationship_evolution(
    workspace: str,
    project: str,
    project_id: str,
    character_name: str,
    target_name: str | None = None,
) -> list[dict[str, Any]]:
    """获取角色关系演变时间线。返回角色与目标角色之间关系的变化历程。"""
    principal = await get_principal("read")
    project_id = await auth.resolve_project_id(workspace, project, principal, access="read")
    logger.info("arc.get_relationship_evolution called")
    validate_required(locals(), "workspace", "project", "project_id", "character_name")
    return await character_arc_service.get_relationship_evolution(
        project_id=project_id,
        character_name=character_name,
        target_name=target_name,
    )


@mcp.tool(name="arc.get_summary_for_context")
async def arc_get_summary_for_context(
    workspace: str,
    project: str,
    project_id: str,
    character_name: str,
    current_chapter: int,
    max_tokens: int = 200,
) -> str:
    """获取压缩弧光摘要用于上下文注入。将角色弧光历史压缩为精炼摘要，控制token数量。"""
    principal = await get_principal("read")
    project_id = await auth.resolve_project_id(workspace, project, principal, access="read")
    logger.info("arc.get_summary_for_context called")
    validate_required(locals(), "workspace", "project", "project_id", "character_name", "current_chapter")
    return await character_arc_service.get_arc_summary_for_context(
        project_id=project_id,
        character_name=character_name,
        current_chapter=current_chapter,
        max_tokens=max_tokens,
    )


@mcp.tool(name="causality.record")
async def causality_record(
    workspace: str,
    project: str,
    project_id: str,
    cause_event_id: str | None = None,
    cause_chapter_no: int | None = None,
    cause_title: str | None = None,
    effect_event_id: str | None = None,
    effect_chapter_no: int | None = None,
    effect_title: str | None = None,
    causal_type: str = "direct",
    strength: float = 1.0,
    description: str | None = None,
    metadata: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """记录两个事件之间的因果关系链接。支持直接/间接因果类型和强度设定。"""
    principal = await get_principal("write")
    project_id = await auth.resolve_project_id(workspace, project, principal, access="write")
    logger.info("causality.record called")
    validate_required(locals(), "workspace", "project", "project_id")
    return await causality_service.record_cause(
        project_id=project_id,
        cause_event_id=cause_event_id,
        cause_chapter_no=cause_chapter_no,
        cause_title=cause_title,
        effect_event_id=effect_event_id,
        effect_chapter_no=effect_chapter_no,
        effect_title=effect_title,
        causal_type=causal_type,
        strength=strength,
        description=description,
        metadata=metadata,
    )


@mcp.tool(name="causality.record_chain")
async def causality_record_chain(
    workspace: str,
    project: str,
    project_id: str,
    chain: list[dict[str, Any]],
) -> dict[str, Any]:
    """记录完整因果链。从事件列表批量创建连续的因果关系链。"""
    principal = await get_principal("write")
    project_id = await auth.resolve_project_id(workspace, project, principal, access="write")
    logger.info("causality.record_chain called")
    validate_required(locals(), "chain")
    if not isinstance(chain, list) or len(chain) == 0:
        raise ValueError("chain 必须是非空列表")
    return await causality_service.record_chain(
        project_id=project_id,
        chain=chain,
    )


@mcp.tool(name="causality.get_forward")
async def causality_get_forward(
    workspace: str,
    project: str,
    project_id: str,
    event_id: str,
    depth: int = 5,
) -> list[dict[str, Any]]:
    """获取事件的正向因果链。从指定事件出发，查找其引发的后续事件链。"""
    principal = await get_principal("read")
    project_id = await auth.resolve_project_id(workspace, project, principal, access="read")
    logger.info("causality.get_forward called")
    validate_required(locals(), "workspace", "project", "project_id", "event_id")
    return await causality_service.get_chain_from_event(
        project_id=project_id,
        event_id=event_id,
        depth=depth,
    )


@mcp.tool(name="causality.get_backward")
async def causality_get_backward(
    workspace: str,
    project: str,
    project_id: str,
    event_id: str,
    depth: int = 5,
) -> list[dict[str, Any]]:
    """获取事件的反向因果链。从指定事件回溯，查找导致该事件的前因链。"""
    principal = await get_principal("read")
    project_id = await auth.resolve_project_id(workspace, project, principal, access="read")
    logger.info("causality.get_backward called")
    validate_required(locals(), "workspace", "project", "project_id", "event_id")
    return await causality_service.get_chain_to_event(
        project_id=project_id,
        event_id=event_id,
        depth=depth,
    )


@mcp.tool(name="causality.get_in_range")
async def causality_get_in_range(
    workspace: str,
    project: str,
    project_id: str,
    start_chapter: int,
    end_chapter: int,
    causal_type: str | None = None,
    limit: int = 100,
) -> list[dict[str, Any]]:
    """获取章节范围内的所有因果链接。可按因果类型筛选，返回指定区间的完整因果网络。"""
    principal = await get_principal("read")
    project_id = await auth.resolve_project_id(workspace, project, principal, access="read")
    logger.info("causality.get_in_range called")
    validate_required(locals(), "workspace", "project", "project_id", "start_chapter", "end_chapter")
    return await causality_service.get_chains_in_chapter_range(
        project_id=project_id,
        start_chapter=start_chapter,
        end_chapter=end_chapter,
        causal_type=causal_type,
        limit=limit,
    )


@mcp.tool(name="causality.find_unresolved")
async def causality_find_unresolved(
    workspace: str,
    project: str,
    project_id: str,
    up_to_chapter: int,
    limit: int = 50,
) -> list[dict[str, Any]]:
    """查找未解决的因果事件。找出已记录但尚未产生对应结果的起因事件（伏笔）。"""
    principal = await get_principal("read")
    project_id = await auth.resolve_project_id(workspace, project, principal, access="read")
    logger.info("causality.find_unresolved called")
    validate_required(locals(), "workspace", "project", "project_id", "up_to_chapter")
    return await causality_service.find_unresolved_causes(
        project_id=project_id,
        up_to_chapter=up_to_chapter,
        limit=limit,
    )


@mcp.tool(name="causality.find_dangling")
async def causality_find_dangling(
    workspace: str,
    project: str,
    project_id: str,
    up_to_chapter: int,
    limit: int = 50,
) -> list[dict[str, Any]]:
    """查找悬空结果事件。找出没有记录前因的结果事件（逻辑漏洞）。"""
    principal = await get_principal("read")
    project_id = await auth.resolve_project_id(workspace, project, principal, access="read")
    logger.info("causality.find_dangling called")
    validate_required(locals(), "workspace", "project", "project_id", "up_to_chapter")
    return await causality_service.find_dangling_effects(
        project_id=project_id,
        up_to_chapter=up_to_chapter,
        limit=limit,
    )


@mcp.tool(name="causality.get_summary")
async def causality_get_summary(
    workspace: str,
    project: str,
    project_id: str,
    chapter_no: int,
    max_tokens: int = 300,
) -> str:
    """获取压缩因果摘要用于上下文注入。将因果关系网络压缩为精炼摘要，控制token数量。"""
    principal = await get_principal("read")
    project_id = await auth.resolve_project_id(workspace, project, principal, access="read")
    logger.info("causality.get_summary called")
    validate_required(locals(), "workspace", "project", "project_id", "chapter_no")
    return await causality_service.get_causality_summary_for_context(
        project_id=project_id,
        chapter_no=chapter_no,
        max_tokens=max_tokens,
    )


@mcp.tool(name="novelty.check_scene")
async def novelty_check_scene(
    workspace: str,
    project: str,
    project_id: str,
    chapter_no: int,
    scene_description: str,
    window: int = 50,
    threshold: float = 0.6,
) -> dict[str, Any]:
    """检查场景新颖性。对比近N章场景描述，检测是否与已有场景过于相似。"""
    principal = await get_principal("read")
    project_id = await auth.resolve_project_id(workspace, project, principal, access="read")
    logger.info("novelty.check_scene called")
    validate_required(locals(), "workspace", "project", "project_id", "chapter_no", "scene_description")
    return await novelty_service.check_scene_novelty(
        project_id=project_id,
        chapter_no=chapter_no,
        scene_description=scene_description,
        window=window,
        threshold=threshold,
    )


@mcp.tool(name="novelty.check_description")
async def novelty_check_description(
    workspace: str,
    project: str,
    project_id: str,
    chapter_no: int,
    description: str,
    description_type: str = "general",
    window: int = 100,
    threshold: float = 0.7,
) -> dict[str, Any]:
    """检查描写新颖性。对比近N章描写内容，检测是否存在重复描写模式。"""
    principal = await get_principal("read")
    project_id = await auth.resolve_project_id(workspace, project, principal, access="read")
    logger.info("novelty.check_description called")
    validate_required(locals(), "workspace", "project", "project_id", "chapter_no", "description")
    return await novelty_service.check_description_novelty(
        project_id=project_id,
        chapter_no=chapter_no,
        description=description,
        description_type=description_type,
        window=window,
        threshold=threshold,
    )


@mcp.tool(name="novelty.check_dialogue")
async def novelty_check_dialogue(
    workspace: str,
    project: str,
    project_id: str,
    chapter_no: int,
    dialogues: list[dict[str, Any]],
    window: int = 30,
) -> dict[str, Any]:
    """检查对话重复性。分析对话模式，检测是否存在重复的对话结构或句式。"""
    principal = await get_principal("read")
    project_id = await auth.resolve_project_id(workspace, project, principal, access="read")
    logger.info("novelty.check_dialogue called")
    validate_required(locals(), "workspace", "project", "project_id", "chapter_no", "dialogues")
    return await novelty_service.check_dialogue_patterns(
        project_id=project_id,
        chapter_no=chapter_no,
        dialogues=dialogues,
        window=window,
    )


@mcp.tool(name="novelty.check_plot_beats")
async def novelty_check_plot_beats(
    workspace: str,
    project: str,
    project_id: str,
    chapter_no: int,
    plot_beats: list[str],
    window: int = 100,
    threshold: float = 0.5,
) -> dict[str, Any]:
    """检查情节节拍重复性。对比近N章情节节拍，检测是否存在套路化情节。"""
    principal = await get_principal("read")
    project_id = await auth.resolve_project_id(workspace, project, principal, access="read")
    logger.info("novelty.check_plot_beats called")
    validate_required(locals(), "workspace", "project", "project_id", "chapter_no", "plot_beats")
    return await novelty_service.check_plot_beat_novelty(
        project_id=project_id,
        chapter_no=chapter_no,
        plot_beats=plot_beats,
        window=window,
        threshold=threshold,
    )


@mcp.tool(name="novelty.full_check")
async def novelty_full_check(
    workspace: str,
    project: str,
    project_id: str,
    chapter_no: int,
    content: str,
    scene_description: str | None = None,
    dialogues: list[dict[str, Any]] | None = None,
    plot_beats: list[str] | None = None,
) -> dict[str, Any]:
    """执行全面新颖性检查。综合场景、描写、对话、情节节拍的新颖性分析并生成报告。"""
    principal = await get_principal("read")
    project_id = await auth.resolve_project_id(workspace, project, principal, access="read")
    logger.info("novelty.full_check called")
    validate_required(locals(), "workspace", "project", "project_id", "chapter_no", "content")
    return await novelty_service.full_novelty_check(
        project_id=project_id,
        chapter_no=chapter_no,
        content=content,
        scene_description=scene_description,
        dialogues=dialogues,
        plot_beats=plot_beats,
    )


@mcp.tool(name="pacing.create_blueprint")
async def pacing_create_blueprint(
    workspace: str,
    project: str,
    project_id: str,
    volume_no: int,
    blueprint: dict[str, Any],
) -> dict[str, Any]:
    """创建卷节奏蓝图。定义整卷的节奏规划，包括紧张度曲线和情绪节点。"""
    principal = await get_principal("write")
    project_id = await auth.resolve_project_id(workspace, project, principal, access="write")
    logger.info("pacing.create_blueprint called")
    validate_required(locals(), "workspace", "project", "blueprint", "volume_no")
    return await pacing_service.create_volume_blueprint(
        project_id=project_id,
        volume_no=volume_no,
        blueprint=blueprint,
    )


@mcp.tool(name="pacing.get_blueprint")
async def pacing_get_blueprint(
    workspace: str,
    project: str,
    project_id: str,
    volume_no: int,
) -> dict[str, Any] | None:
    """获取卷节奏蓝图。返回指定卷的节奏规划数据。"""
    principal = await get_principal("read")
    project_id = await auth.resolve_project_id(workspace, project, principal, access="read")
    logger.info("pacing.get_blueprint called")
    validate_required(locals(), "workspace", "project", "project_id", "volume_no")
    return await pacing_service.get_volume_blueprint(
        project_id=project_id,
        volume_no=volume_no,
    )


@mcp.tool(name="pacing.list_blueprints")
async def pacing_list_blueprints(
    workspace: str,
    project: str,
    project_id: str,
) -> list[dict[str, Any]]:
    """列出所有节奏蓝图。返回项目中所有卷的节奏规划列表。"""
    principal = await get_principal("read")
    project_id = await auth.resolve_project_id(workspace, project, principal, access="read")
    logger.info("pacing.list_blueprints called")
    validate_required(locals(), "workspace", "project", "project_id")
    return await pacing_service.list_volume_blueprints(project_id=project_id)


@mcp.tool(name="pacing.record_emotion")
async def pacing_record_emotion(
    workspace: str,
    project: str,
    project_id: str,
    chapter_no: int,
    tension: float,
    emotion: str,
    emotion_intensity: float,
    pacing_type: str = "normal",
    word_count: int | None = None,
    metadata: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """记录章节情绪/紧张度数据。

    Args:
        tension: 紧张度 0.0-1.0（0=平和，1=极度紧张）
        emotion: 情绪类型，如 joy/sadness/anger/fear 等
        emotion_intensity: 情绪强度 0.0-1.0（0=无，1=极强）
        pacing_type: 节奏类型，必须是: buildup/climax/breather/transition/climax_buildup/resolution/normal
    """
    principal = await get_principal("write")
    logger.info("pacing.record_emotion: ws=%s prj=%s ch=%d tension=%.2f emotion=%s intensity=%.2f type=%s", workspace, project, chapter_no, tension, emotion, emotion_intensity, pacing_type)
    project_id = await auth.resolve_project_id(workspace, project, principal, access="write")
    validate_required(locals(), "workspace", "project", "project_id", "chapter_no", "tension", "emotion", "emotion_intensity")

    # Auto-clamp values to valid range
    tension = max(0.0, min(1.0, tension))
    emotion_intensity = max(0.0, min(1.0, emotion_intensity))

    # Validate pacing_type against allowed enum
    VALID_PACING = {'buildup', 'climax', 'breather', 'transition', 'climax_buildup', 'resolution', 'normal'}
    if pacing_type not in VALID_PACING:
        raise ValueError(f"pacing_type 取值必须是: {', '.join(sorted(VALID_PACING))}，当前值为 '{pacing_type}'")
    return await pacing_service.record_chapter_emotion(
        project_id=project_id,
        chapter_no=chapter_no,
        tension=tension,
        emotion=emotion,
        emotion_intensity=emotion_intensity,
        pacing_type=pacing_type,
        word_count=word_count,
        metadata=metadata,
    )


@mcp.tool(name="pacing.get_emotion")
async def pacing_get_emotion(
    workspace: str,
    project: str,
    project_id: str,
    chapter_no: int,
) -> dict[str, Any] | None:
    """获取章节情绪数据。返回指定章节的紧张度、情绪类型和强度信息。"""
    principal = await get_principal("read")
    project_id = await auth.resolve_project_id(workspace, project, principal, access="read")
    logger.info("pacing.get_emotion called")
    validate_required(locals(), "workspace", "project", "project_id", "chapter_no")
    return await pacing_service.get_chapter_emotion(
        project_id=project_id,
        chapter_no=chapter_no,
    )


@mcp.tool(name="pacing.get_curve")
async def pacing_get_curve(
    workspace: str,
    project: str,
    project_id: str,
    from_chapter: int | None = None,
    to_chapter: int | None = None,
    limit: int = 500,
) -> list[dict[str, Any]]:
    """获取情绪曲线。返回指定章节范围内的紧张度变化曲线数据。"""
    principal = await get_principal("read")
    project_id = await auth.resolve_project_id(workspace, project, principal, access="read")
    logger.info("pacing.get_curve called")
    validate_required(locals(), "workspace", "project", "project_id")
    return await pacing_service.get_emotion_curve(
        project_id=project_id,
        from_chapter=from_chapter,
        to_chapter=to_chapter,
        limit=limit,
    )


@mcp.tool(name="pacing.analyze_rhythm")
async def pacing_analyze_rhythm(
    workspace: str,
    project: str,
    project_id: str,
    from_chapter: int,
    to_chapter: int,
) -> dict[str, Any]:
    """分析节奏韵律。分析指定章节区间的节奏模式，识别快慢交替规律。"""
    principal = await get_principal("read")
    project_id = await auth.resolve_project_id(workspace, project, principal, access="read")
    logger.info("pacing.analyze_rhythm called")
    validate_required(locals(), "workspace", "project", "project_id", "from_chapter", "to_chapter")
    return await pacing_service.analyze_pacing_rhythm(
        project_id=project_id,
        from_chapter=from_chapter,
        to_chapter=to_chapter,
    )


@mcp.tool(name="pacing.check_health")
async def pacing_check_health(
    workspace: str,
    project: str,
    project_id: str,
    from_chapter: int,
    to_chapter: int,
    volume_no: int | None = None,
) -> dict[str, Any]:
    """检查节奏健康度。对比蓝图和通用规则，检测节奏是否偏离合理范围。"""
    principal = await get_principal("read")
    project_id = await auth.resolve_project_id(workspace, project, principal, access="read")
    logger.info("pacing.check_health called")
    validate_required(locals(), "workspace", "project", "project_id", "from_chapter", "to_chapter")
    return await pacing_service.check_pacing_health(
        project_id=project_id,
        from_chapter=from_chapter,
        to_chapter=to_chapter,
        volume_no=volume_no,
    )


@mcp.tool(name="pacing.compare_blueprint")
async def pacing_compare_blueprint(
    workspace: str,
    project: str,
    project_id: str,
    volume_no: int,
    from_chapter: int,
    to_chapter: int,
) -> dict[str, Any]:
    """对比实际曲线与蓝图。将实际紧张度曲线与规划蓝图进行偏差分析。"""
    principal = await get_principal("read")
    project_id = await auth.resolve_project_id(workspace, project, principal, access="read")
    logger.info("pacing.compare_blueprint called")
    validate_required(locals(), "workspace", "project", "project_id", "volume_no", "from_chapter", "to_chapter")
    return await pacing_service.compare_to_blueprint(
        project_id=project_id,
        volume_no=volume_no,
        from_chapter=from_chapter,
        to_chapter=to_chapter,
    )


@mcp.tool(name="pacing.predict_engagement")
async def pacing_predict_engagement(
    workspace: str,
    project: str,
    project_id: str,
    chapter_no: int,
    window: int = 10,
) -> dict[str, Any]:
    """预测读者参与度。基于近期节奏模式预测后续章节的读者参与度。"""
    principal = await get_principal("read")
    project_id = await auth.resolve_project_id(workspace, project, principal, access="read")
    logger.info("pacing.predict_engagement called")
    validate_required(locals(), "workspace", "project", "project_id", "chapter_no")
    return await pacing_service.predict_engagement(
        project_id=project_id,
        chapter_no=chapter_no,
        window=window,
    )


@mcp.tool(name="pacing.get_summary")
async def pacing_get_summary(
    workspace: str,
    project: str,
    project_id: str,
    chapter_no: int,
    volume_no: int | None = None,
    max_tokens: int = 200,
) -> str:
    """获取压缩节奏摘要用于上下文注入。将节奏数据压缩为精炼摘要，控制token数量。"""
    principal = await get_principal("read")
    project_id = await auth.resolve_project_id(workspace, project, principal, access="read")
    logger.info("pacing.get_summary called")
    validate_required(locals(), "workspace", "project", "project_id", "chapter_no")
    return await pacing_service.get_pacing_summary_for_context(
        project_id=project_id,
        chapter_no=chapter_no,
        volume_no=volume_no,
        max_tokens=max_tokens,
    )


@mcp.tool(name="style.create_profile")
async def style_create_profile(
    workspace: str,
    project: str,
    project_id: str,
    profile_name: str = "default",
    narrative_pov: str = "third_limited",
    tense: str = "past",
    tone: str = "neutral",
    target_metrics: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """创建文风档案。定义项目的叙事视角、时态、语调等风格参数和目标指标。"""
    principal = await get_principal("write")
    project_id = await auth.resolve_project_id(workspace, project, principal, access="write")
    logger.info("style.create_profile called")
    validate_required(locals(), "workspace", "project", "project_id")
    return await style_fingerprint_service.create_style_profile(
        project_id=project_id,
        profile_name=profile_name,
        narrative_pov=narrative_pov,
        tense=tense,
        tone=tone,
        target_metrics=target_metrics,
    )


@mcp.tool(name="style.get_profile")
async def style_get_profile(
    workspace: str,
    project: str,
    project_id: str,
    profile_name: str = "default",
) -> dict[str, Any] | None:
    """获取文风档案。返回指定名称的风格配置参数。"""
    principal = await get_principal("read")
    project_id = await auth.resolve_project_id(workspace, project, principal, access="read")
    logger.info("style.get_profile called")
    validate_required(locals(), "workspace", "project", "project_id")
    return await style_fingerprint_service.get_style_profile(
        project_id=project_id,
        profile_name=profile_name,
    )


@mcp.tool(name="style.analyze_chapter")
async def style_analyze_chapter(
    workspace: str,
    project: str,
    project_id: str,
    chapter_no: int,
    content: str,
) -> dict[str, Any]:
    """分析章节文风指标。提取句长、词汇多样性、修辞手法等文风特征数据。"""
    principal = await get_principal("write")
    project_id = await auth.resolve_project_id(workspace, project, principal, access="write")
    logger.info("style.analyze_chapter called")
    validate_required(locals(), "workspace", "project", "project_id", "chapter_no", "content")
    return await style_fingerprint_service.analyze_chapter_style(
        project_id=project_id,
        chapter_no=chapter_no,
        content=content,
    )


@mcp.tool(name="style.get_chapter")
async def style_get_chapter(
    workspace: str,
    project: str,
    project_id: str,
    chapter_no: int,
) -> dict[str, Any] | None:
    """获取章节文风指标。返回已分析章节的文风特征数据。"""
    principal = await get_principal("read")
    project_id = await auth.resolve_project_id(workspace, project, principal, access="read")
    logger.info("style.get_chapter called")
    validate_required(locals(), "workspace", "project", "project_id", "chapter_no")
    return await style_fingerprint_service.get_chapter_style(
        project_id=project_id,
        chapter_no=chapter_no,
    )


@mcp.tool(name="style.detect_drift")
async def style_detect_drift(
    workspace: str,
    project: str,
    project_id: str,
    chapter_no: int,
    window: int = 20,
    threshold: float = 0.3,
) -> dict[str, Any]:
    """检测文风漂移。对比基准线检测文风是否偏离已建立的风格基线。"""
    principal = await get_principal("read")
    project_id = await auth.resolve_project_id(workspace, project, principal, access="read")
    logger.info("style.detect_drift called")
    validate_required(locals(), "workspace", "project", "project_id", "chapter_no")
    return await style_fingerprint_service.detect_style_drift(
        project_id=project_id,
        chapter_no=chapter_no,
        window=window,
        threshold=threshold,
    )


@mcp.tool(name="style.batch_analyze")
async def style_batch_analyze(
    workspace: str,
    project: str,
    project_id: str,
    from_chapter: int,
    to_chapter: int,
) -> dict[str, Any]:
    """批量分析章节文风。对指定章节范围进行批量文风特征提取和分析。"""
    principal = await get_principal("write")
    project_id = await auth.resolve_project_id(workspace, project, principal, access="write")
    logger.info("style.batch_analyze called")
    validate_required(locals(), "workspace", "project", "project_id", "from_chapter", "to_chapter")
    return await style_fingerprint_service.batch_analyze_chapters(
        project_id=project_id,
        from_chapter=from_chapter,
        to_chapter=to_chapter,
    )


@mcp.tool(name="style.get_trend")
async def style_get_trend(
    workspace: str,
    project: str,
    project_id: str,
    from_chapter: int | None = None,
    to_chapter: int | None = None,
    metric: str = "avg_sentence_length",
    limit: int = 100,
) -> list[dict[str, Any]]:
    """获取文风指标趋势。追踪特定文风指标在章节间的变化趋势。"""
    principal = await get_principal("read")
    project_id = await auth.resolve_project_id(workspace, project, principal, access="read")
    logger.info("style.get_trend called")
    validate_required(locals(), "workspace", "project", "project_id")
    return await style_fingerprint_service.get_style_trend(
        project_id=project_id,
        from_chapter=from_chapter,
        to_chapter=to_chapter,
        metric=metric,
        limit=limit,
    )


@mcp.tool(name="style.get_summary")
async def style_get_summary(
    workspace: str,
    project: str,
    project_id: str,
    chapter_no: int,
    max_tokens: int = 150,
) -> str:
    """获取压缩文风摘要用于上下文注入。将文风数据压缩为精炼摘要，控制token数量。"""
    principal = await get_principal("read")
    project_id = await auth.resolve_project_id(workspace, project, principal, access="read")
    logger.info("style.get_summary called")
    validate_required(locals(), "workspace", "project", "project_id", "chapter_no")
    return await style_fingerprint_service.get_style_summary_for_context(
        project_id=project_id,
        chapter_no=chapter_no,
        max_tokens=max_tokens,
    )


@mcp.tool(name="pipeline.create_plan")
async def pipeline_create_plan(
    workspace: str,
    project: str,
    project_id: str,
    chapter_no: int,
    volume_no: int | None = None,
    plan: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """创建或更新章节生成计划（第一轮）。定义大纲阶段的参数和上下文信息。"""
    principal = await get_principal("write")
    project_id = await auth.resolve_project_id(workspace, project, principal, access="write")
    logger.info("pipeline.create_plan called")
    validate_required(locals(), "workspace", "project", "project_id", "chapter_no")
    return await multipass_service.create_chapter_plan(
        project_id=project_id,
        chapter_no=chapter_no,
        volume_no=volume_no,
        plan=plan,
    )


@mcp.tool(name="pipeline.get_plan")
async def pipeline_get_plan(
    workspace: str,
    project: str,
    project_id: str,
    chapter_no: int,
) -> dict[str, Any] | None:
    """获取当前章节生成计划。返回指定章节的活跃生成计划。"""
    principal = await get_principal("read")
    project_id = await auth.resolve_project_id(workspace, project, principal, access="read")
    logger.info("pipeline.get_plan called")
    validate_required(locals(), "workspace", "project", "project_id", "chapter_no")
    return await multipass_service.get_chapter_plan(
        project_id=project_id,
        chapter_no=chapter_no,
    )


@mcp.tool(name="pipeline.record_pass")
async def pipeline_record_pass(
    workspace: str,
    project: str,
    project_id: str,
    chapter_no: int,
    pass_number: int,
    pass_type: str,
    content: str | None = None,
    metadata: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """记录生成轮次结果。记录大纲、初稿、润色等各轮次的输出内容和元数据。"""
    principal = await get_principal("write")
    project_id = await auth.resolve_project_id(workspace, project, principal, access="write")
    logger.info("pipeline.record_pass called")
    validate_required(locals(), "workspace", "project", "project_id", "chapter_no", "pass_number", "pass_type")
    pass_type_map = {"outline": "planning", "draft": "drafting", "polish": "polishing", "review": "verification", "manual": "drafting"}
    mapped_pass_type = pass_type_map.get(pass_type, pass_type)
    return await multipass_service.create_generation_pass(
        project_id=project_id,
        chapter_no=chapter_no,
        pass_number=pass_number,
        pass_type=mapped_pass_type,
        content=content,
        metadata=metadata,
    )


@mcp.tool(name="pipeline.get_passes")
async def pipeline_get_passes(
    workspace: str,
    project: str,
    chapter_no: int,
) -> list[dict[str, Any]]:
    """获取章节所有生成轮次。返回指定章节的全部生成轮次记录。"""
    principal = await get_principal("read")
    logger.info("pipeline.get_passes called")
    validate_required(locals(), "workspace", "project", "chapter_no")
    project_id = await auth.resolve_project_id(workspace, project, principal)
    return await multipass_service.get_generation_passes(
        project_id=project_id,
        chapter_no=chapter_no,
    )


@mcp.tool(name="pipeline.check_continuity")
async def pipeline_check_continuity(
    workspace: str,
    project: str,
    project_id: str,
    chapter_no: int,
    content: str,
) -> dict[str, Any]:
    """检查内容连续性。对比近章摘要检测生成内容的连贯性和逻辑一致性。"""
    principal = await get_principal("read")
    project_id = await auth.resolve_project_id(workspace, project, principal, access="read")
    logger.info("pipeline.check_continuity called")
    validate_required(locals(), "workspace", "project", "project_id", "chapter_no", "content")
    return await multipass_service.check_continuity(
        project_id=project_id,
        chapter_no=chapter_no,
        content=content,
    )


async def _extract_knowledge_from_content(
    project_id: str, chapter_no: int, content: str,
) -> dict[str, Any]:
    """用 analysis 模型从正文提取结构化知识并自动写入系统。"""
    if not content or len(content) < 100:
        return {"status": "skipped", "reason": "content too short"}

    system_prompt = """从以下章节内容中提取结构化知识，只输出 JSON：{
  "entities": [{"name": "", "entity_type": "character|faction|location|item", "summary": "", "is_new": true}],
  "relationships": [{"source": "", "target": "", "relation_type": "alliance|conflict|family|friendship|mentor|rivalry|other", "attitude": "positive|negative|neutral|mixed", "intensity": 0.5}],
  "locations": [{"name": "", "description": "", "is_new": true}],
  "events": [{"title": "", "description": "", "causal_type": "direct|indirect"}],
  "world_rules": [{"key": "", "content": ""}]
}
规则：entities 只包含本章出现的角色/势力/物品；is_new 表示首次出现；relationships 包含本章角色互动；locations 包含地理名称；events 包含重大事件；world_rules 包含新揭示的世界观规则。"""

    try:
        result = await llm_client.chat(
            project_id, "analysis",
            [{"role": "system", "content": system_prompt},
             {"role": "user", "content": f"【章节正文】\n{content[:8000]}"}],
            temperature=0.1, max_tokens=4096,
        )
    except ValueError as e:
        logger.warning("Knowledge extraction skipped (no analysis model): %s", e)
        return {"status": "skipped", "reason": str(e)}

    raw = result.get("text", "").strip()
    if not raw:
        return {"status": "skipped", "reason": "empty response"}

    # Strip markdown code fences
    if raw.startswith("```"):
        raw = raw.split("\n", 1)[-1]
        raw = raw.rsplit("\n", 1)[0] if raw.endswith("```") else raw
        if raw.endswith("```"):
            raw = raw[:-3]

    try:
        data = json.loads(raw)
    except json.JSONDecodeError:
        logger.warning("Failed to parse extraction JSON, raw=%s", raw[:200])
        return {"status": "error", "reason": "json parse failed"}

    stats: dict[str, int] = {"entities": 0, "relationships": 0, "world_rules": 0}

    # Write entities
    for ent in data.get("entities", []):
        name = ent.get("name", "").strip()
        etype = ent.get("entity_type", "character")
        summary = ent.get("summary", "")
        if not name:
            continue
        try:
            await memory_service.upsert_entity(
                project_id=project_id,
                entity_type=etype,
                name=name,
                summary=summary,
                first_seen_chapter_no=chapter_no if ent.get("is_new") else None,
                last_seen_chapter_no=chapter_no,
                source_type="auto_extract",
            )
            stats["entities"] += 1
        except Exception as e:
            logger.warning("Failed to upsert entity '%s': %s", name, e)

    # Write relationships
    for rel in data.get("relationships", []):
        src = rel.get("source", "").strip()
        tgt = rel.get("target", "").strip()
        rtype = rel.get("relation_type", "other")
        if not src or not tgt:
            continue
        try:
            await memory_service.upsert_relationship(
                project_id=project_id,
                source_name=src,
                target_name=tgt,
                relation_type=rtype,
                attitude=rel.get("attitude", "neutral"),
                intensity=rel.get("intensity", 0.5),
                source_chapter_no=chapter_no,
            )
            stats["relationships"] += 1
        except Exception as e:
            logger.warning("Failed to upsert relationship '%s->%s': %s", src, tgt, e)

    # Write world_rules
    for rule in data.get("world_rules", []):
        key = rule.get("key", "").strip()
        content = rule.get("content", "").strip()
        if not key or not content:
            continue
        try:
            await db.execute(
                """INSERT INTO project_knowledge (project_id, category, key, value)
                   VALUES ($1, 'world_rule', $2, $3::jsonb)
                   ON CONFLICT (project_id, category, key)
                   DO UPDATE SET value = EXCLUDED.value""",
                project_id, f"auto_{key}", json.dumps({"content": content, "chapter_no": chapter_no}),
            )
            stats["world_rules"] += 1
        except Exception as e:
            logger.warning("Failed to upsert world_rule '%s': %s", key, e)

    # Write events as causality chains
    for evt in data.get("events", []):
        title = evt.get("title", "").strip()
        desc = evt.get("description", "").strip()
        if not title:
            continue
        try:
            await causality_service.record_cause(
                project_id=project_id,
                cause_title=title,
                cause_chapter_no=chapter_no,
                description=desc,
                causal_type=evt.get("causal_type", "direct"),
            )
            stats.setdefault("events", 0)
            stats["events"] += 1
        except Exception as e:
            logger.warning("Failed to record event '%s': %s", title, e)

    logger.info("Knowledge extraction done: %s", stats)

    # Phase B: auto-detect and fill knowledge gaps
    try:
        all_names = []
        for ent in data.get("entities", []):
            n = ent.get("name", "").strip()
            if n:
                all_names.append(n)
        for loc in data.get("locations", []):
            n = loc.get("name", "").strip()
            if n:
                all_names.append(n)
        if all_names:
            gap_result = await _fill_knowledge_gaps(project_id, chapter_no, all_names)
            stats["gaps_found"] = gap_result.get("gaps_found", 0)
    except Exception as e:
        logger.warning("Knowledge gap filling failed: %s", e)

    return {"status": "ok", "stats": stats}


async def _fill_knowledge_gaps(
    project_id: str, chapter_no: int, names: list[str],
) -> dict[str, Any]:
    """检查实体/地名是否在知识库中存在，缺失则记录缺口并搜索内部已有知识。"""
    gaps_found = 0
    internal_hits = 0

    for name in names[:30]:  # limit to 30 per chapter
        # Check universal_knowledge
        uk = await db.fetchrow(
            "SELECT id, topic FROM universal_knowledge WHERE topic ILIKE '%' || $1 || '%' AND status = 'active' LIMIT 1",
            name,
        )
        # Check knowledge_entities
        ke = await db.fetchrow(
            "SELECT id, name FROM knowledge_entities WHERE name ILIKE '%' || $1 || '%' AND status = 'active' LIMIT 1",
            name,
        )
        # Check canon_documents
        cd = await db.fetchrow(
            "SELECT id, title FROM canon_documents WHERE project_id=$1 AND (title ILIKE '%' || $2 || '%' OR key ILIKE '%' || $2 || '%') AND status='active' LIMIT 1",
            project_id, name,
        )

        if uk or ke or cd:
            internal_hits += 1
            continue

        # Gap found — create gap record
        try:
            await db.execute(
                """INSERT INTO ref_gap_logs (project_id, gap_type, description, entity_name, chapter_no)
                   VALUES ($1, 'missing_knowledge', $2, $3, $4)""",
                project_id,
                f"章节 {chapter_no} 中出现但知识库中缺失: {name}",
                name, chapter_no,
            )
            gaps_found += 1
        except Exception as e:
            logger.warning("Failed to create gap log for '%s': %s", name, e)

    logger.info("Knowledge gap check: %d missing, %d internal hits out of %d", gaps_found, internal_hits, len(names[:30]))
    return {"gaps_found": gaps_found, "internal_hits": internal_hits, "checked": len(names[:30])}


@mcp.tool(name="pipeline.run_full")
async def pipeline_run_full(
    workspace: str,
    project: str,
    chapter_no: int,
    plan: dict[str, Any] | None = None,
    draft_content: str = "",
    polished_content: str | None = None,
    auto_generate: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """运行完整生成流水线（大纲→初稿→润色→验证）。

    通过 plan、draft_content、polished_content 参数传入内容。
    如需系统自动润色，请使用 pipeline.generate(task_type="polish")。

    Args:
        plan: 大纲内容（dict，由 AI 工具生成）
        draft_content: 初稿正文（由 AI 工具生成）
        polished_content: 润色后正文（由 AI 工具生成，可选）
        auto_generate: 已废弃 —— 此参数将报错
    """
    principal = await get_principal("write")
    logger.info("pipeline.run_full called, auto=%s", bool(auto_generate))
    validate_required(locals(), "workspace", "project", "chapter_no")
    project_id = await auth.resolve_project_id(workspace, project, principal, access="write")

    # Auto-generate using LLM if requested
    if auto_generate:
        raise ValueError(
            "系统未配置 outline/draft/polish 模型，不支持 auto_generate 参数。"
            "请由 AI 工具生成内容后，通过 plan/draft_content/polished_content 参数直接传入。"
        )

    result = await multipass_service.run_pipeline(
        project_id=project_id,
        chapter_no=chapter_no,
        plan=plan or {},
        draft_content=draft_content or "",
        polished_content=polished_content,
    )

    # Auto-extract knowledge from draft content
    if draft_content:
        try:
            extraction = await _extract_knowledge_from_content(project_id, chapter_no, draft_content)
            result["knowledge_extraction"] = extraction
        except Exception as e:
            logger.warning("Knowledge extraction failed: %s", e)
            result["knowledge_extraction"] = {"status": "error", "reason": str(e)}

    result["workflow_guide"] = {
        "phase": "写作流程",
        "current_step": "全部轮次完成",
        "next_tool": "workflow.submit_chapter_commit",
        "description": f"第{chapter_no}章四轮生成完成，建议执行以下下一步操作",
        "subsequent_actions": [
            {"tool": "workflow.submit_chapter_commit", "desc": "提交章节"},
            {"tool": "kb.world.auto_update", "desc": "自动更新世界状态"},
            {"tool": "arc.record_emotion", "desc": "记录角色情感变化"},
            {"tool": "arc.record_power", "desc": "记录角色实力变化"},
            {"tool": "arc.record_relationship", "desc": "记录角色关系变化"},
            {"tool": "arc.record_personality", "desc": "记录角色性格变化"},
            {"tool": "pacing.record_emotion", "desc": "记录章节节奏"},
            {"tool": "plot.thread.advance", "desc": "推进情节线进度"},
            {"tool": "foreshadowing.payoff", "desc": "回收到期伏笔"},
            {"tool": "review.start_job", "desc": "启动多模型审核"},
            {"tool": "workflow.learn_from_review", "desc": "从审核结果学习"},
            {"tool": "context_compression.auto_compress", "desc": "自动压缩上下文"},
        ],
    }
    return result


@mcp.tool(name="pipeline.status")
async def pipeline_status(
    workspace: str,
    project: str,
    chapter_no: int,
) -> dict[str, Any]:
    """获取流水线状态。返回章节当前所处的生成阶段和完成进度。"""
    principal = await get_principal("read")
    logger.info("pipeline.status called")
    validate_required(locals(), "workspace", "project", "chapter_no")
    project_id = await auth.resolve_project_id(workspace, project, principal)
    return await multipass_service.get_pipeline_status(
        project_id=project_id,
        chapter_no=chapter_no,
    )


@mcp.tool(name="pipeline.multi_review")
async def pipeline_multi_review(
    workspace: str,
    project: str,
    chapter_no: int,
    reviewers: list[dict[str, Any]],
    content: str = "",
) -> dict[str, Any]:
    """多模型审查。使用配置的多组模型对章节内容进行并行审查，返回各模型的审查报告。"""
    principal = await get_principal("write")
    logger.info("pipeline.multi_review called with %d reviewers", len(reviewers))
    validate_required(locals(), "workspace", "project", "chapter_no", "reviewers")
    project_id = await auth.resolve_project_id(workspace, project, principal, access="write")

    # Start a review job
    dimensions = [r.get("focus", "general") for r in reviewers]
    job = await review_service.start_job(
        project_id=project_id,
        chapter_no=chapter_no,
        dimensions=dimensions,
        username=principal.username,
    )
    job_id = job.get("job_id")

    # Create review reports for each configured reviewer
    reports = []
    for r in reviewers:
        model_key = r.get("model", "")
        focus = r.get("focus", "general")
        name = r.get("name", model_key)
        prompt_template = r.get("prompt", "")

        # Record the review report for this model
        report = await review_service.add_review_feedback(
            review_id=job_id or "",
            feedback_type=focus,
            content=f"模型: {model_key}\n审查维度: {focus}\n提示: {prompt_template}",
            severity="info",
        )
        reports.append({
            "model": model_key,
            "name": name,
            "focus": focus,
            "prompt": prompt_template,
            "status": "pending",
        })

    return {
        "ok": True,
        "job_id": job_id,
        "chapter_no": chapter_no,
        "reviewers": reports,
        "total_reviewers": len(reviewers),
    }


@mcp.tool(name="pipeline.generate")
async def pipeline_generate(
    workspace: str,
    project: str,
    chapter_no: int,
    task_type: str = "draft",
    system_prompt: str = "",
    user_prompt: str = "",
    summary: str | None = None,
    content: str | None = None,  # 废弃别名：等同 summary，保留以兼容旧调用方
    temperature: float = 0.7,
    max_tokens: int = 4096,
    save_pass: bool = True,
) -> dict[str, Any]:
    """记录生成内容到系统。正文保存在用户本地，此处只存 200 字摘要。

    两条路径二选一：
    1. 传 summary — 系统只存前 200 字（超出直接报错），统计字数存 generation_passes
    2. 传 user_prompt — 系统调用配置的模型生成

    Args:
        summary: 章节摘要（<=200 字；正文全文存本地，不要传入库）
        user_prompt: 用户提示词（与 summary 二选一，至少传一个）

    Args:
        workspace: 工作区
        project: 项目
        chapter_no: 章节号
        task_type: 任务类型 — outline(大纲)/draft(初稿)/polish(润色)/review(审核)/manual(手动)
        system_prompt: 系统提示词（仅 review 等系统模型任务时使用）
        user_prompt: 用户提示词（仅 review 等系统模型任务时使用）
        summary: AI 工具已生成的摘要（<=200 字）。传入后系统统计字数，不存全文。
        content: [已废弃] summary 的旧名，保留仅为兼容，请勿在新代码中使用。
        temperature: 生成温度（仅 review 等系统模型任务时使用）
        max_tokens: 最大 token 数（仅 review 等系统模型任务时使用）
        save_pass: 是否自动保存为 generation_pass

    Returns:
        生成结果，包含 text、model、usage 等
    """
    principal = await get_principal("write")
    # 兼容旧名：content 等同 summary
    if summary is None and content is not None:
        summary = content
    logger.info("pipeline.generate: ws=%s prj=%s ch=%d task=%s save_pass=%s has_summary=%s legacy_content=%s",
                workspace, project, chapter_no, task_type, save_pass, bool(summary), content is not None)
    validate_required(locals(), "workspace", "project", "chapter_no")
    project_id = await auth.resolve_project_id(workspace, project, principal, access="write")

    if summary is not None and len(summary) > 200:
        raise ValueError(
            f"summary 长度 {len(summary)} 超过 200 字上限；本参数只存摘要，正文请保存在本地"
        )

    # AI 工具已提供内容 → 直接保存，跳过 LLM
    if summary:
        result = {
            "text": summary,
            "model": "ai_tool",
            "usage": {"prompt_tokens": 0, "completion_tokens": 0, "total_tokens": 0},
        }
    else:
        # 走系统配置的模型（review/analysis 等）
        if not user_prompt:
            raise ValueError("不传入 summary 时必须提供 user_prompt")
        messages = []
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        messages.append({"role": "user", "content": user_prompt})
        try:
            result = await llm_client.chat(project_id, task_type, messages, temperature, max_tokens)
        except ValueError as e:
            raise ValueError(
                f"系统未配置 {task_type} 类型的模型，请传入 summary 参数由 AI 工具自行生成内容。"
                f"（{e}）"
            )

    # Save as generation pass
    if save_pass and result.get("text"):
        text = result["text"]
        pass_number = {"planning": 1, "outline": 1, "drafting": 2, "draft": 2, "polishing": 3, "polish": 3, "verification": 4, "review": 4, "manual": 2}.get(task_type, 2)
        word_count = len(text)
        pass_summary = text[:200].replace("\n", " ") if len(text) > 200 else text.replace("\n", " ")
        file_name = f"ch{chapter_no:02d}_{task_type}.md"
        folder_name = f"第{chapter_no:02d}章"
        pass_type_map = {"outline": "planning", "draft": "drafting", "polish": "polishing", "review": "verification", "manual": "drafting"}
        pass_type = pass_type_map.get(task_type, task_type)
        await multipass_service.create_generation_pass(
            project_id=project_id, chapter_no=chapter_no, pass_number=pass_number,
            pass_type=pass_type, content=pass_summary,
            metadata={
                "word_count": word_count,
                "file_path": f"{folder_name}/{file_name}",
                "summary": pass_summary,
            },
        )

        # Sync word_count to chapters
        try:
            await db.execute(
                "UPDATE chapters SET word_count = $1, updated_at = NOW() WHERE project_id = $2 AND chapter_no = $3",
                word_count, project_id, chapter_no,
            )
        except Exception:
            pass

        # Write chapter_summaries for drafting passes
        if pass_type == "drafting":
            try:
                ch_row = await db.fetchrow(
                    "SELECT id FROM chapters WHERE project_id = $1 AND chapter_no = $2",
                    project_id, chapter_no,
                )
                if ch_row:
                    await db.execute(
                        # chapter_summaries 没有 updated_at 列（见 010_core_schema.sql）。
                        # 旧写法带 updated_at = NOW() 会抛 UndefinedColumn，又被下面 except 静默吞掉，
                        # 摘要实际一直没写进去。这里只更新 content。
                        """INSERT INTO chapter_summaries (project_id, chapter_id, summary_type, content)
                           VALUES ($1, $2, 'chapter', $3)
                           ON CONFLICT (chapter_id, summary_type) DO UPDATE
                           SET content = EXCLUDED.content""",
                        project_id, ch_row["id"], pass_summary,
                    )
            except Exception as exc:
                logger.warning("write chapter_summaries failed for chapter %s: %s", chapter_no, exc)

    ret_actions = [
        "outline→draft→polish→review 顺序推进",
        "提交章节后调用 kb.world.auto_update 更新世界状态",
        "提交章节后调用 arc.record_* 记录角色弧光",
        "提交章节后调用 plot.thread.advance 推进剧情线",
        "提交章节后调用 foreshadowing.payoff 回收到期伏笔",
    ] if task_type != "review" else [
        "review 完成，润色后调用 workflow.submit_chapter_commit 提交章节",
        "提交章节后调用 kb.world.auto_update 更新世界状态",
        "提交章节后调用 arc.record_* 记录角色弧光",
        "提交章节后调用 plot.thread.advance 推进剧情线",
        "提交章节后调用 foreshadowing.payoff 回收到期伏笔",
    ]

    return {
        "ok": True,
        "text": result["text"],
        "model": result["model"],
        "usage": result["usage"],
        "chapter_no": chapter_no,
        "task_type": task_type,
        "_file_hint": {
            "message": "正文已记录摘要，请将完整正文保存到本地项目目录",
            "relative_path": f"第{chapter_no:02d}章/ch{chapter_no:02d}_{task_type}.md",
        },
        "workflow_guide": {
            "phase": "写作流程",
            "next_tool": "pipeline.generate" if task_type != "review" else "workflow.submit_chapter_commit",
            "description": f"第{chapter_no}章 {task_type} 生成完成",
            "next_actions": ret_actions,
            "workflow": [
                {"step": 1, "tool": "pipeline.generate", "task_type": "outline", "status": "done" if task_type == "outline" or task_type in ("draft", "polish", "review") else "pending", "desc": "生成大纲"},
                {"step": 2, "tool": "pipeline.generate", "task_type": "draft", "status": "done" if task_type == "draft" or task_type in ("polish", "review") else "pending", "desc": "生成初稿"},
                {"step": 3, "tool": "pipeline.generate", "task_type": "polish", "status": "done" if task_type == "polish" or task_type == "review" else "pending", "desc": "润色"},
                {"step": 4, "tool": "pipeline.generate", "task_type": "review", "status": "done" if task_type == "review" else "pending", "desc": "验证"},
                {"step": 5, "tool": "workflow.submit_chapter_commit", "status": "pending", "desc": "提交章节"},
            ],
        },
    }
