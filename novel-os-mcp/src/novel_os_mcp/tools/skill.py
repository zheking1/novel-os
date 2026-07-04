import logging
from typing import Any
from ..mcp_core import mcp
from ..deps import skill_service
from ..tool_auth import get_principal, validate_required

logger = logging.getLogger("novel_os_mcp.tools.skill")


# ============================================================
# Skill CRUD
# ============================================================

@mcp.tool(name="skill.list")
async def skill_list(active_only: bool = True) -> list[dict[str, Any]]:
    """列出所有 skill。"""
    principal = await get_principal("read")
    logger.info("skill_list called")
    return await skill_service.list_skills(active_only=active_only)


@mcp.tool(name="skill.get")
async def skill_get(skill_id: str) -> dict[str, Any] | None:
    """获取 skill 详情（含步骤）。"""
    principal = await get_principal("read")
    logger.info("skill_get called")
    validate_required(locals(), "skill_id")
    return await skill_service.get_skill(skill_id=skill_id)


@mcp.tool(name="skill.get_by_name")
async def skill_get_by_name(name: str) -> dict[str, Any] | None:
    """通过名称获取 skill。"""
    principal = await get_principal("read")
    logger.info("skill_get_by_name called")
    validate_required(locals(), "name")
    return await skill_service.get_skill_by_name(name=name)


@mcp.tool(name="skill.create")
async def skill_create(
    name: str,
    description: str | None = None,
    content: str = "",
    trigger_words: list[str] | None = None,
    tool_hints: list[str] | None = None,
    sort_order: int = 0,
) -> dict[str, Any]:
    """创建 skill。"""
    principal = await get_principal("write")
    logger.info("skill_create called")
    validate_required(locals(), "name")
    return await skill_service.create_skill(
        name=name, description=description, content=content,
        trigger_words=trigger_words, tool_hints=tool_hints, sort_order=sort_order,
    )


@mcp.tool(name="skill.update")
async def skill_update(
    skill_id: str,
    name: str | None = None,
    description: str | None = None,
    content: str | None = None,
    trigger_words: list[str] | None = None,
    tool_hints: list[str] | None = None,
    is_active: bool | None = None,
    sort_order: int | None = None,
) -> dict[str, Any]:
    """更新 skill。"""
    principal = await get_principal("write")
    logger.info("skill_update called")
    validate_required(locals(), "skill_id")
    return await skill_service.update_skill(
        skill_id=skill_id, name=name, description=description, content=content,
        trigger_words=trigger_words, tool_hints=tool_hints, is_active=is_active,
        sort_order=sort_order,
    )


@mcp.tool(name="skill.delete")
async def skill_delete(skill_id: str) -> bool:
    """删除 skill（含所有步骤）。"""
    principal = await get_principal("write")
    logger.info("skill_delete called")
    validate_required(locals(), "skill_id")
    return await skill_service.delete_skill(skill_id=skill_id)


# ============================================================
# Skill Steps
# ============================================================

@mcp.tool(name="skill.step.list")
async def skill_step_list(skill_id: str) -> list[dict[str, Any]]:
    """列出 skill 的所有步骤。"""
    principal = await get_principal("read")
    logger.info("skill_step_list called")
    validate_required(locals(), "skill_id")
    return await skill_service.list_steps(skill_id=skill_id)


@mcp.tool(name="skill.step.add")
async def skill_step_add(
    skill_id: str,
    step_order: int,
    step_name: str,
    tool_name: str | None = None,
    description: str | None = None,
    parameters: dict | None = None,
    optional: bool = False,
    conditional: str | None = None,
) -> dict[str, Any]:
    """添加 skill 步骤。"""
    principal = await get_principal("write")
    logger.info("skill_step_add called")
    validate_required(locals(), "skill_id", "step_order", "step_name")
    return await skill_service.add_step(
        skill_id=skill_id, step_order=step_order, step_name=step_name,
        tool_name=tool_name, description=description, parameters=parameters,
        optional=optional, conditional=conditional,
    )


@mcp.tool(name="skill.step.update")
async def skill_step_update(
    step_id: str,
    step_order: int | None = None,
    step_name: str | None = None,
    tool_name: str | None = None,
    description: str | None = None,
    parameters: dict | None = None,
    optional: bool | None = None,
    conditional: str | None = None,
) -> dict[str, Any]:
    """更新 skill 步骤。"""
    principal = await get_principal("write")
    logger.info("skill_step_update called")
    validate_required(locals(), "step_id")
    return await skill_service.update_step(
        step_id=step_id, step_order=step_order, step_name=step_name,
        tool_name=tool_name, description=description, parameters=parameters,
        optional=optional, conditional=conditional,
    )


@mcp.tool(name="skill.step.delete")
async def skill_step_delete(step_id: str) -> bool:
    """删除 skill 步骤。"""
    principal = await get_principal("write")
    logger.info("skill_step_delete called")
    validate_required(locals(), "step_id")
    return await skill_service.delete_step(step_id=step_id)


# ============================================================
# Semantic Matching
# ============================================================

@mcp.tool(name="skill.match")
async def skill_match(query: str, limit: int = 3) -> list[dict[str, Any]]:
    """根据用户意图匹配相关 skill（含完整内容和步骤）。"""
    principal = await get_principal("read")
    logger.info("skill_match called")
    validate_required(locals(), "query")
    return await skill_service.match_skills(query=query, limit=limit)
