import logging
import json
from typing import Any

from ..mcp_core import mcp
from ..deps import character_arc_service, pacing_service, causality_service, style_fingerprint_service, novelty_service, multipass_service
from ..tool_auth import get_principal, validate_required

logger = logging.getLogger("novel_os_mcp.tools.novel_gen")


@mcp.tool(name="arc.record_emotion")
async def arc_record_emotion(
    project_id: str,
    character_name: str,
    chapter_no: int,
    emotion: str,
    intensity: float,
    cause: str | None = None,
) -> dict[str, Any]:
    """记录角色情感状态。用于追踪角色在特定章节的情感变化，包含情感类型、强度和触发原因。"""
    principal = await get_principal("write")
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
    project_id: str,
    character_name: str,
    chapter_no: int,
    target_name: str,
    old_relation: str,
    new_relation: str,
    cause: str | None = None,
) -> dict[str, Any]:
    """记录角色关系变化。追踪两个角色之间关系的转变，记录旧关系、新关系及变化原因。"""
    principal = await get_principal("write")
    logger.info("arc.record_relationship called")
    validate_required(locals(), "project_id", "character_name", "chapter_no", "target_name", "old_relation", "new_relation")
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
    project_id: str,
    character_name: str,
    chapter_no: int,
    old_level: str,
    new_level: str,
    method: str | None = None,
) -> dict[str, Any]:
    """记录角色实力等级变化。追踪修为/技能等级的提升或降低，记录变化方式。"""
    principal = await get_principal("write")
    logger.info("arc.record_power called")
    validate_required(locals(), "project_id", "character_name", "chapter_no", "old_level", "new_level")
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
    project_id: str,
    character_name: str,
    chapter_no: int,
    trait: str,
    old_value: Any,
    new_value: Any,
    reason: str | None = None,
) -> dict[str, Any]:
    """记录角色性格特质变化。追踪性格特征从旧值到新值的转变，记录变化原因。"""
    principal = await get_principal("write")
    logger.info("arc.record_personality called")
    validate_required(locals(), "project_id", "character_name", "chapter_no", "trait", "old_value", "new_value")
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
    logger.info("arc.record_point called")
    validate_required(locals(), "project_id", "character_name", "chapter_no", "arc_type", "state")
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
    project_id: str,
    character_name: str,
    arc_type: str | None = None,
    from_chapter: int | None = None,
    to_chapter: int | None = None,
    limit: int = 100,
) -> list[dict[str, Any]]:
    """获取角色弧光历史。按章节范围和弧光类型查询角色的所有弧光记录。"""
    principal = await get_principal("read")
    logger.info("arc.get_character called")
    validate_required(locals(), "project_id", "character_name")
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
    project_id: str,
    character_name: str,
) -> dict[str, Any]:
    """获取角色最新弧光状态。返回角色所有弧光类型的最新状态快照。"""
    principal = await get_principal("read")
    logger.info("arc.get_latest_state called")
    validate_required(locals(), "project_id", "character_name")
    return await character_arc_service.get_latest_arc_state(
        project_id=project_id,
        character_name=character_name,
    )


@mcp.tool(name="arc.get_emotion_timeline")
async def arc_get_emotion_timeline(
    project_id: str,
    character_name: str,
    from_chapter: int | None = None,
    to_chapter: int | None = None,
) -> list[dict[str, Any]]:
    """获取角色情感时间线。返回指定章节范围内角色的情感变化序列。"""
    principal = await get_principal("read")
    logger.info("arc.get_emotion_timeline called")
    validate_required(locals(), "project_id", "character_name")
    return await character_arc_service.get_emotion_timeline(
        project_id=project_id,
        character_name=character_name,
        from_chapter=from_chapter,
        to_chapter=to_chapter,
    )


@mcp.tool(name="arc.get_power_progression")
async def arc_get_power_progression(
    project_id: str,
    character_name: str,
) -> list[dict[str, Any]]:
    """获取角色实力成长时间线。返回角色修为/技能等级的完整变化历程。"""
    principal = await get_principal("read")
    logger.info("arc.get_power_progression called")
    validate_required(locals(), "project_id", "character_name")
    return await character_arc_service.get_power_progression(
        project_id=project_id,
        character_name=character_name,
    )


@mcp.tool(name="arc.get_relationship_evolution")
async def arc_get_relationship_evolution(
    project_id: str,
    character_name: str,
    target_name: str | None = None,
) -> list[dict[str, Any]]:
    """获取角色关系演变时间线。返回角色与目标角色之间关系的变化历程。"""
    principal = await get_principal("read")
    logger.info("arc.get_relationship_evolution called")
    validate_required(locals(), "project_id", "character_name")
    return await character_arc_service.get_relationship_evolution(
        project_id=project_id,
        character_name=character_name,
        target_name=target_name,
    )


@mcp.tool(name="arc.get_summary_for_context")
async def arc_get_summary_for_context(
    project_id: str,
    character_name: str,
    current_chapter: int,
    max_tokens: int = 200,
) -> str:
    """获取压缩弧光摘要用于上下文注入。将角色弧光历史压缩为精炼摘要，控制token数量。"""
    principal = await get_principal("read")
    logger.info("arc.get_summary_for_context called")
    validate_required(locals(), "project_id", "character_name", "current_chapter")
    return await character_arc_service.get_arc_summary_for_context(
        project_id=project_id,
        character_name=character_name,
        current_chapter=current_chapter,
        max_tokens=max_tokens,
    )


@mcp.tool(name="causality.record")
async def causality_record(
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
    logger.info("causality.record called")
    validate_required(locals(), "project_id")
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
    project_id: str,
    chain: list[dict[str, Any]],
) -> dict[str, Any]:
    """记录完整因果链。从事件列表批量创建连续的因果关系链。"""
    principal = await get_principal("write")
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
    project_id: str,
    event_id: str,
    depth: int = 5,
) -> list[dict[str, Any]]:
    """获取事件的正向因果链。从指定事件出发，查找其引发的后续事件链。"""
    principal = await get_principal("read")
    logger.info("causality.get_forward called")
    validate_required(locals(), "project_id", "event_id")
    return await causality_service.get_chain_from_event(
        project_id=project_id,
        event_id=event_id,
        depth=depth,
    )


@mcp.tool(name="causality.get_backward")
async def causality_get_backward(
    project_id: str,
    event_id: str,
    depth: int = 5,
) -> list[dict[str, Any]]:
    """获取事件的反向因果链。从指定事件回溯，查找导致该事件的前因链。"""
    principal = await get_principal("read")
    logger.info("causality.get_backward called")
    validate_required(locals(), "project_id", "event_id")
    return await causality_service.get_chain_to_event(
        project_id=project_id,
        event_id=event_id,
        depth=depth,
    )


@mcp.tool(name="causality.get_in_range")
async def causality_get_in_range(
    project_id: str,
    start_chapter: int,
    end_chapter: int,
    causal_type: str | None = None,
    limit: int = 100,
) -> list[dict[str, Any]]:
    """获取章节范围内的所有因果链接。可按因果类型筛选，返回指定区间的完整因果网络。"""
    principal = await get_principal("read")
    logger.info("causality.get_in_range called")
    validate_required(locals(), "project_id", "start_chapter", "end_chapter")
    return await causality_service.get_chains_in_chapter_range(
        project_id=project_id,
        start_chapter=start_chapter,
        end_chapter=end_chapter,
        causal_type=causal_type,
        limit=limit,
    )


@mcp.tool(name="causality.find_unresolved")
async def causality_find_unresolved(
    project_id: str,
    up_to_chapter: int,
    limit: int = 50,
) -> list[dict[str, Any]]:
    """查找未解决的因果事件。找出已记录但尚未产生对应结果的起因事件（伏笔）。"""
    principal = await get_principal("read")
    logger.info("causality.find_unresolved called")
    validate_required(locals(), "project_id", "up_to_chapter")
    return await causality_service.find_unresolved_causes(
        project_id=project_id,
        up_to_chapter=up_to_chapter,
        limit=limit,
    )


@mcp.tool(name="causality.find_dangling")
async def causality_find_dangling(
    project_id: str,
    up_to_chapter: int,
    limit: int = 50,
) -> list[dict[str, Any]]:
    """查找悬空结果事件。找出没有记录前因的结果事件（逻辑漏洞）。"""
    principal = await get_principal("read")
    logger.info("causality.find_dangling called")
    validate_required(locals(), "project_id", "up_to_chapter")
    return await causality_service.find_dangling_effects(
        project_id=project_id,
        up_to_chapter=up_to_chapter,
        limit=limit,
    )


@mcp.tool(name="causality.get_summary")
async def causality_get_summary(
    project_id: str,
    chapter_no: int,
    max_tokens: int = 300,
) -> str:
    """获取压缩因果摘要用于上下文注入。将因果关系网络压缩为精炼摘要，控制token数量。"""
    principal = await get_principal("read")
    logger.info("causality.get_summary called")
    validate_required(locals(), "project_id", "chapter_no")
    return await causality_service.get_causality_summary_for_context(
        project_id=project_id,
        chapter_no=chapter_no,
        max_tokens=max_tokens,
    )


@mcp.tool(name="novelty.check_scene")
async def novelty_check_scene(
    project_id: str,
    chapter_no: int,
    scene_description: str,
    window: int = 50,
    threshold: float = 0.6,
) -> dict[str, Any]:
    """检查场景新颖性。对比近N章场景描述，检测是否与已有场景过于相似。"""
    principal = await get_principal("read")
    logger.info("novelty.check_scene called")
    validate_required(locals(), "project_id", "chapter_no", "scene_description")
    return await novelty_service.check_scene_novelty(
        project_id=project_id,
        chapter_no=chapter_no,
        scene_description=scene_description,
        window=window,
        threshold=threshold,
    )


@mcp.tool(name="novelty.check_description")
async def novelty_check_description(
    project_id: str,
    chapter_no: int,
    description: str,
    description_type: str = "general",
    window: int = 100,
    threshold: float = 0.7,
) -> dict[str, Any]:
    """检查描写新颖性。对比近N章描写内容，检测是否存在重复描写模式。"""
    principal = await get_principal("read")
    logger.info("novelty.check_description called")
    validate_required(locals(), "project_id", "chapter_no", "description")
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
    project_id: str,
    chapter_no: int,
    dialogues: list[dict[str, Any]],
    window: int = 30,
) -> dict[str, Any]:
    """检查对话重复性。分析对话模式，检测是否存在重复的对话结构或句式。"""
    principal = await get_principal("read")
    logger.info("novelty.check_dialogue called")
    validate_required(locals(), "project_id", "chapter_no", "dialogues")
    return await novelty_service.check_dialogue_patterns(
        project_id=project_id,
        chapter_no=chapter_no,
        dialogues=dialogues,
        window=window,
    )


@mcp.tool(name="novelty.check_plot_beats")
async def novelty_check_plot_beats(
    project_id: str,
    chapter_no: int,
    plot_beats: list[str],
    window: int = 100,
    threshold: float = 0.5,
) -> dict[str, Any]:
    """检查情节节拍重复性。对比近N章情节节拍，检测是否存在套路化情节。"""
    principal = await get_principal("read")
    logger.info("novelty.check_plot_beats called")
    validate_required(locals(), "project_id", "chapter_no", "plot_beats")
    return await novelty_service.check_plot_beat_novelty(
        project_id=project_id,
        chapter_no=chapter_no,
        plot_beats=plot_beats,
        window=window,
        threshold=threshold,
    )


@mcp.tool(name="novelty.full_check")
async def novelty_full_check(
    project_id: str,
    chapter_no: int,
    content: str,
    scene_description: str | None = None,
    dialogues: list[dict[str, Any]] | None = None,
    plot_beats: list[str] | None = None,
) -> dict[str, Any]:
    """执行全面新颖性检查。综合场景、描写、对话、情节节拍的新颖性分析并生成报告。"""
    principal = await get_principal("read")
    logger.info("novelty.full_check called")
    validate_required(locals(), "project_id", "chapter_no", "content")
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
    project_id: str,
    volume_no: int,
    blueprint: dict[str, Any],
) -> dict[str, Any]:
    """创建卷节奏蓝图。定义整卷的节奏规划，包括紧张度曲线和情绪节点。"""
    principal = await get_principal("write")
    logger.info("pacing.create_blueprint called")
    validate_required(locals(), "blueprint_name", "volume_no")
    return await pacing_service.create_volume_blueprint(
        project_id=project_id,
        volume_no=volume_no,
        blueprint=blueprint,
    )


@mcp.tool(name="pacing.get_blueprint")
async def pacing_get_blueprint(
    project_id: str,
    volume_no: int,
) -> dict[str, Any] | None:
    """获取卷节奏蓝图。返回指定卷的节奏规划数据。"""
    principal = await get_principal("read")
    logger.info("pacing.get_blueprint called")
    validate_required(locals(), "project_id", "volume_no")
    return await pacing_service.get_volume_blueprint(
        project_id=project_id,
        volume_no=volume_no,
    )


@mcp.tool(name="pacing.list_blueprints")
async def pacing_list_blueprints(
    project_id: str,
) -> list[dict[str, Any]]:
    """列出所有节奏蓝图。返回项目中所有卷的节奏规划列表。"""
    principal = await get_principal("read")
    logger.info("pacing.list_blueprints called")
    validate_required(locals(), "project_id")
    return await pacing_service.list_volume_blueprints(project_id=project_id)


@mcp.tool(name="pacing.record_emotion")
async def pacing_record_emotion(
    project_id: str,
    chapter_no: int,
    tension: float,
    emotion: str,
    emotion_intensity: float,
    pacing_type: str = "normal",
    word_count: int | None = None,
    metadata: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """记录章节情绪/紧张度数据。用于追踪每章的节奏类型、紧张度和情绪强度。"""
    principal = await get_principal("write")
    logger.info("pacing.record_emotion called")
    validate_required(locals(), "project_id", "chapter_no", "tension", "emotion", "emotion_intensity")
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
    project_id: str,
    chapter_no: int,
) -> dict[str, Any] | None:
    """获取章节情绪数据。返回指定章节的紧张度、情绪类型和强度信息。"""
    principal = await get_principal("read")
    logger.info("pacing.get_emotion called")
    validate_required(locals(), "project_id", "chapter_no")
    return await pacing_service.get_chapter_emotion(
        project_id=project_id,
        chapter_no=chapter_no,
    )


@mcp.tool(name="pacing.get_curve")
async def pacing_get_curve(
    project_id: str,
    from_chapter: int | None = None,
    to_chapter: int | None = None,
    limit: int = 500,
) -> list[dict[str, Any]]:
    """获取情绪曲线。返回指定章节范围内的紧张度变化曲线数据。"""
    principal = await get_principal("read")
    logger.info("pacing.get_curve called")
    validate_required(locals(), "project_id")
    return await pacing_service.get_emotion_curve(
        project_id=project_id,
        from_chapter=from_chapter,
        to_chapter=to_chapter,
        limit=limit,
    )


@mcp.tool(name="pacing.analyze_rhythm")
async def pacing_analyze_rhythm(
    project_id: str,
    from_chapter: int,
    to_chapter: int,
) -> dict[str, Any]:
    """分析节奏韵律。分析指定章节区间的节奏模式，识别快慢交替规律。"""
    principal = await get_principal("read")
    logger.info("pacing.analyze_rhythm called")
    validate_required(locals(), "project_id", "from_chapter", "to_chapter")
    return await pacing_service.analyze_pacing_rhythm(
        project_id=project_id,
        from_chapter=from_chapter,
        to_chapter=to_chapter,
    )


@mcp.tool(name="pacing.check_health")
async def pacing_check_health(
    project_id: str,
    from_chapter: int,
    to_chapter: int,
    volume_no: int | None = None,
) -> dict[str, Any]:
    """检查节奏健康度。对比蓝图和通用规则，检测节奏是否偏离合理范围。"""
    principal = await get_principal("read")
    logger.info("pacing.check_health called")
    validate_required(locals(), "project_id", "from_chapter", "to_chapter")
    return await pacing_service.check_pacing_health(
        project_id=project_id,
        from_chapter=from_chapter,
        to_chapter=to_chapter,
        volume_no=volume_no,
    )


@mcp.tool(name="pacing.compare_blueprint")
async def pacing_compare_blueprint(
    project_id: str,
    volume_no: int,
    from_chapter: int,
    to_chapter: int,
) -> dict[str, Any]:
    """对比实际曲线与蓝图。将实际紧张度曲线与规划蓝图进行偏差分析。"""
    principal = await get_principal("read")
    logger.info("pacing.compare_blueprint called")
    validate_required(locals(), "project_id", "volume_no", "from_chapter", "to_chapter")
    return await pacing_service.compare_to_blueprint(
        project_id=project_id,
        volume_no=volume_no,
        from_chapter=from_chapter,
        to_chapter=to_chapter,
    )


@mcp.tool(name="pacing.predict_engagement")
async def pacing_predict_engagement(
    project_id: str,
    chapter_no: int,
    window: int = 10,
) -> dict[str, Any]:
    """预测读者参与度。基于近期节奏模式预测后续章节的读者参与度。"""
    principal = await get_principal("read")
    logger.info("pacing.predict_engagement called")
    validate_required(locals(), "project_id", "chapter_no")
    return await pacing_service.predict_engagement(
        project_id=project_id,
        chapter_no=chapter_no,
        window=window,
    )


@mcp.tool(name="pacing.get_summary")
async def pacing_get_summary(
    project_id: str,
    chapter_no: int,
    volume_no: int | None = None,
    max_tokens: int = 200,
) -> str:
    """获取压缩节奏摘要用于上下文注入。将节奏数据压缩为精炼摘要，控制token数量。"""
    principal = await get_principal("read")
    logger.info("pacing.get_summary called")
    validate_required(locals(), "project_id", "chapter_no")
    return await pacing_service.get_pacing_summary_for_context(
        project_id=project_id,
        chapter_no=chapter_no,
        volume_no=volume_no,
        max_tokens=max_tokens,
    )


@mcp.tool(name="style.create_profile")
async def style_create_profile(
    project_id: str,
    profile_name: str = "default",
    narrative_pov: str = "third_limited",
    tense: str = "past",
    tone: str = "neutral",
    target_metrics: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """创建文风档案。定义项目的叙事视角、时态、语调等风格参数和目标指标。"""
    principal = await get_principal("write")
    logger.info("style.create_profile called")
    validate_required(locals(), "project_id")
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
    project_id: str,
    profile_name: str = "default",
) -> dict[str, Any] | None:
    """获取文风档案。返回指定名称的风格配置参数。"""
    principal = await get_principal("read")
    logger.info("style.get_profile called")
    validate_required(locals(), "project_id")
    return await style_fingerprint_service.get_style_profile(
        project_id=project_id,
        profile_name=profile_name,
    )


@mcp.tool(name="style.analyze_chapter")
async def style_analyze_chapter(
    project_id: str,
    chapter_no: int,
    content: str,
) -> dict[str, Any]:
    """分析章节文风指标。提取句长、词汇多样性、修辞手法等文风特征数据。"""
    principal = await get_principal("write")
    logger.info("style.analyze_chapter called")
    validate_required(locals(), "project_id", "chapter_no", "content")
    return await style_fingerprint_service.analyze_chapter_style(
        project_id=project_id,
        chapter_no=chapter_no,
        content=content,
    )


@mcp.tool(name="style.get_chapter")
async def style_get_chapter(
    project_id: str,
    chapter_no: int,
) -> dict[str, Any] | None:
    """获取章节文风指标。返回已分析章节的文风特征数据。"""
    principal = await get_principal("read")
    logger.info("style.get_chapter called")
    validate_required(locals(), "project_id", "chapter_no")
    return await style_fingerprint_service.get_chapter_style(
        project_id=project_id,
        chapter_no=chapter_no,
    )


@mcp.tool(name="style.detect_drift")
async def style_detect_drift(
    project_id: str,
    chapter_no: int,
    window: int = 20,
    threshold: float = 0.3,
) -> dict[str, Any]:
    """检测文风漂移。对比基准线检测文风是否偏离已建立的风格基线。"""
    principal = await get_principal("read")
    logger.info("style.detect_drift called")
    validate_required(locals(), "project_id", "chapter_no")
    return await style_fingerprint_service.detect_style_drift(
        project_id=project_id,
        chapter_no=chapter_no,
        window=window,
        threshold=threshold,
    )


@mcp.tool(name="style.batch_analyze")
async def style_batch_analyze(
    project_id: str,
    from_chapter: int,
    to_chapter: int,
) -> dict[str, Any]:
    """批量分析章节文风。对指定章节范围进行批量文风特征提取和分析。"""
    principal = await get_principal("write")
    logger.info("style.batch_analyze called")
    validate_required(locals(), "project_id", "from_chapter", "to_chapter")
    return await style_fingerprint_service.batch_analyze_chapters(
        project_id=project_id,
        from_chapter=from_chapter,
        to_chapter=to_chapter,
    )


@mcp.tool(name="style.get_trend")
async def style_get_trend(
    project_id: str,
    from_chapter: int | None = None,
    to_chapter: int | None = None,
    metric: str = "avg_sentence_length",
    limit: int = 100,
) -> list[dict[str, Any]]:
    """获取文风指标趋势。追踪特定文风指标在章节间的变化趋势。"""
    principal = await get_principal("read")
    logger.info("style.get_trend called")
    validate_required(locals(), "project_id")
    return await style_fingerprint_service.get_style_trend(
        project_id=project_id,
        from_chapter=from_chapter,
        to_chapter=to_chapter,
        metric=metric,
        limit=limit,
    )


@mcp.tool(name="style.get_summary")
async def style_get_summary(
    project_id: str,
    chapter_no: int,
    max_tokens: int = 150,
) -> str:
    """获取压缩文风摘要用于上下文注入。将文风数据压缩为精炼摘要，控制token数量。"""
    principal = await get_principal("read")
    logger.info("style.get_summary called")
    validate_required(locals(), "project_id", "chapter_no")
    return await style_fingerprint_service.get_style_summary_for_context(
        project_id=project_id,
        chapter_no=chapter_no,
        max_tokens=max_tokens,
    )


@mcp.tool(name="pipeline.create_plan")
async def pipeline_create_plan(
    project_id: str,
    chapter_no: int,
    volume_no: int | None = None,
    plan: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """创建或更新章节生成计划（第一轮）。定义大纲阶段的参数和上下文信息。"""
    principal = await get_principal("write")
    logger.info("pipeline.create_plan called")
    validate_required(locals(), "project_id", "chapter_no")
    return await multipass_service.create_chapter_plan(
        project_id=project_id,
        chapter_no=chapter_no,
        volume_no=volume_no,
        plan=plan,
    )


@mcp.tool(name="pipeline.get_plan")
async def pipeline_get_plan(
    project_id: str,
    chapter_no: int,
) -> dict[str, Any] | None:
    """获取当前章节生成计划。返回指定章节的活跃生成计划。"""
    principal = await get_principal("read")
    logger.info("pipeline.get_plan called")
    validate_required(locals(), "project_id", "chapter_no")
    return await multipass_service.get_chapter_plan(
        project_id=project_id,
        chapter_no=chapter_no,
    )


@mcp.tool(name="pipeline.record_pass")
async def pipeline_record_pass(
    project_id: str,
    chapter_no: int,
    pass_number: int,
    pass_type: str,
    content: str | None = None,
    metadata: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """记录生成轮次结果。记录大纲、初稿、润色等各轮次的输出内容和元数据。"""
    principal = await get_principal("write")
    logger.info("pipeline.record_pass called")
    validate_required(locals(), "project_id", "chapter_no", "pass_number", "pass_type")
    return await multipass_service.create_generation_pass(
        project_id=project_id,
        chapter_no=chapter_no,
        pass_number=pass_number,
        pass_type=pass_type,
        content=content,
        metadata=metadata,
    )


@mcp.tool(name="pipeline.get_passes")
async def pipeline_get_passes(
    project_id: str,
    chapter_no: int,
) -> list[dict[str, Any]]:
    """获取章节所有生成轮次。返回指定章节的全部生成轮次记录。"""
    principal = await get_principal("read")
    logger.info("pipeline.get_passes called")
    validate_required(locals(), "project_id", "chapter_no")
    return await multipass_service.get_generation_passes(
        project_id=project_id,
        chapter_no=chapter_no,
    )


@mcp.tool(name="pipeline.check_continuity")
async def pipeline_check_continuity(
    project_id: str,
    chapter_no: int,
    content: str,
) -> dict[str, Any]:
    """检查内容连续性。对比近章摘要检测生成内容的连贯性和逻辑一致性。"""
    principal = await get_principal("read")
    logger.info("pipeline.check_continuity called")
    validate_required(locals(), "project_id", "chapter_no", "content")
    return await multipass_service.check_continuity(
        project_id=project_id,
        chapter_no=chapter_no,
        content=content,
    )


@mcp.tool(name="pipeline.run_full")
async def pipeline_run_full(
    project_id: str,
    chapter_no: int,
    plan: dict[str, Any],
    draft_content: str,
    polished_content: str | None = None,
) -> dict[str, Any]:
    """运行完整四轮生成流水线（大纲→初稿→润色→验证）。一次性执行全部生成阶段。"""
    principal = await get_principal("write")
    logger.info("pipeline.run_full called")
    validate_required(locals(), "project_id", "chapter_no", "plan", "draft_content")
    return await multipass_service.run_pipeline(
        project_id=project_id,
        chapter_no=chapter_no,
        plan=plan,
        draft_content=draft_content,
        polished_content=polished_content,
    )


@mcp.tool(name="pipeline.status")
async def pipeline_status(
    project_id: str,
    chapter_no: int,
) -> dict[str, Any]:
    """获取流水线状态。返回章节当前所处的生成阶段和完成进度。"""
    principal = await get_principal("read")
    logger.info("pipeline.status called")
    validate_required(locals(), "project_id", "chapter_no")
    return await multipass_service.get_pipeline_status(
        project_id=project_id,
        chapter_no=chapter_no,
    )
