import logging
from typing import Any

from ..mcp_core import mcp
from ..deps import db, auth, model_cost_service
from ..tool_auth import get_principal, validate_required

logger = logging.getLogger("novel_os_mcp.tools.model")


@mcp.tool(name="model.profile.upsert")
async def model_profile_upsert(
    workspace: str,
    project: str,
    profile_key: str,
    display_name: str,
    provider: str,
    model_name: str,
    task_types: list[str] | None = None,
    tier: str = "standard",
    default_params: dict[str, Any] | None = None,
    cost_config: dict[str, Any] | None = None,
    rate_limit_config: dict[str, Any] | None = None,
    is_default: bool = False,
    status: str = "active",
    metadata: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """创建或更新模型配置文件。定义 provider、模型名、费用和速率限制参数。"""
    principal = await get_principal("write")
    logger.info("model_profile_upsert called")
    validate_required(locals(), "provider", "model_name")
    project_id = await auth.resolve_project_id(workspace, project, principal, access="write")
    return await model_cost_service.upsert_profile(
        project_id=project_id,
        profile_key=profile_key,
        display_name=display_name,
        provider=provider,
        model_name=model_name,
        task_types=task_types or [],
        tier=tier,
        default_params=default_params or {},
        cost_config=cost_config or {},
        rate_limit_config=rate_limit_config or {},
        is_default=is_default,
        status=status,
        metadata=metadata or {},
        username=principal.username,
    )


@mcp.tool(name="model.profile.list")
async def model_profile_list(
    workspace: str,
    project: str | None = None,
    task_type: str | None = None,
    status: str | None = "active",
    tier: str | None = None,
) -> list[dict[str, Any]]:
    """列出模型配置文件。支持按任务类型、状态、层级过滤。project 为 null 时返回当前用户所有配置。"""
    principal = await get_principal("read")
    logger.info("model_profile_list called")
    if project:
        project_id = await auth.resolve_project_id(workspace, project, principal)
        return await model_cost_service.list_profiles(
            project_id=project_id,
            task_type=task_type,
            status=status,
            tier=tier,
        )
    else:
        # Return all profiles for current user (cross-project, user-scoped)
        return await model_cost_service.list_profiles_by_user(
            username=principal.username,
            task_type=task_type,
            status=status,
            tier=tier,
        )


@mcp.tool(name="model.route")
async def model_route(
    workspace: str,
    project: str,
    task_type: str,
    chapter_no: int | None = None,
    volume_no: int | None = None,
) -> dict[str, Any]:
    """根据任务类型和上下文章节路由到最合适的模型配置。"""
    principal = await get_principal("read")
    logger.info("model_route called")
    project_id = await auth.resolve_project_id(workspace, project, principal)
    return await model_cost_service.route_model(
        project_id=project_id,
        task_type=task_type,
        chapter_no=chapter_no,
        volume_no=volume_no,
    )


@mcp.tool(name="model.route_rule.upsert")
async def model_route_rule_upsert(
    workspace: str,
    project: str,
    task_type: str,
    profile_key: str,
    priority: int = 100,
    conditions: dict[str, Any] | None = None,
    fallback_profile_keys: list[str] | None = None,
    status: str = "active",
    metadata: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """创建或更新模型路由规则。按优先级匹配任务类型到模型配置。"""
    principal = await get_principal("write")
    logger.info("model_route_rule_upsert called")
    validate_required(locals(), "task_type", "profile_key")
    project_id = await auth.resolve_project_id(workspace, project, principal, access="write")
    return await model_cost_service.upsert_route_rule(
        project_id=project_id,
        task_type=task_type,
        profile_key=profile_key,
        priority=priority,
        conditions=conditions or {},
        fallback_profile_keys=fallback_profile_keys or [],
        status=status,
        metadata=metadata or {},
    )


@mcp.tool(name="model.route_rule.list")
async def model_route_rule_list(
    workspace: str,
    project: str,
    task_type: str | None = None,
    status: str | None = "active",
) -> list[dict[str, Any]]:
    """列出项目模型路由规则。支持按任务类型和状态过滤。"""
    principal = await get_principal("read")
    logger.info("model_route_rule_list called")
    project_id = await auth.resolve_project_id(workspace, project, principal)
    return await model_cost_service.list_route_rules(
        project_id=project_id,
        task_type=task_type,
        status=status,
    )


@mcp.tool(name="cost.record_usage")
async def cost_record_usage(
    workspace: str,
    project: str,
    task_type: str,
    profile_key: str | None = None,
    provider: str | None = None,
    model_name: str | None = None,
    source_type: str | None = None,
    source_id: str | None = None,
    input_tokens: int = 0,
    output_tokens: int = 0,
    cached_tokens: int = 0,
    total_tokens: int | None = None,
    cost_amount: float | None = None,
    currency: str = "USD",
    latency_ms: int | None = None,
    success: bool = True,
    error_code: str | None = None,
    metadata: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """记录一次模型调用的 token 用量和费用。用于成本追踪和统计。"""
    principal = await get_principal("write")
    logger.info("cost_record_usage called")
    validate_required(locals(), "task_type")
    project_id = await auth.resolve_project_id(workspace, project, principal, access="write")
    return await model_cost_service.record_usage(
        project_id=project_id,
        task_type=task_type,
        profile_key=profile_key,
        provider=provider,
        model_name=model_name,
        source_type=source_type,
        source_id=source_id,
        input_tokens=input_tokens,
        output_tokens=output_tokens,
        cached_tokens=cached_tokens,
        total_tokens=total_tokens,
        cost_amount=cost_amount,
        currency=currency,
        latency_ms=latency_ms,
        success=success,
        error_code=error_code,
        metadata=metadata or {},
        username=principal.username,
    )


@mcp.tool(name="cost.report")
async def cost_report(
    workspace: str,
    project: str,
    group_by: str = "day",
    task_types: list[str] | None = None,
    profile_keys: list[str] | None = None,
    from_date: str | None = None,
    to_date: str | None = None,
) -> dict[str, Any]:
    """生成费用报表。支持按天/周/月分组，可按任务类型和模型过滤。"""
    principal = await get_principal("read")
    logger.info("cost_report called")
    project_id = await auth.resolve_project_id(workspace, project, principal)
    return await model_cost_service.cost_report(
        project_id=project_id,
        group_by=group_by,
        task_types=task_types,
        profile_keys=profile_keys,
        from_date=from_date,
        to_date=to_date,
    )
