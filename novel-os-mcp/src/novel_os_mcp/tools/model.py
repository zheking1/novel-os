import logging
import re
from typing import Any

from ..mcp_core import mcp
from ..deps import db, auth, model_cost_service
from ..tool_auth import get_principal, validate_required

logger = logging.getLogger("novel_os_mcp.tools.model")


@mcp.tool(name="model.profile.upsert")
async def model_profile_upsert(
    profile_key: str,
    display_name: str | None = None,
    provider: str | None = None,
    model_name: str | None = None,
    task_types: list[str] | None = None,
    tier: str | None = None,
    default_params: dict[str, Any] | None = None,
    cost_config: dict[str, Any] | None = None,
    rate_limit_config: dict[str, Any] | None = None,
    is_default: bool | None = None,
    status: str | None = None,
    metadata: dict[str, Any] | None = None,
    is_contributed: bool | None = None,
) -> dict[str, Any]:
    """创建或更新模型配置文件。用户级别，定义 provider、模型名、费用和速率限制参数。

    如需删除（软删除），传入相应 profile_key + status='inactive' 即可。
    更新时只需传入需要修改的字段。"""
    principal = await get_principal("write")
    logger.info("model_profile_upsert called")
    return await model_cost_service.upsert_profile(
        profile_key=profile_key,
        display_name=display_name,
        provider=provider,
        model_name=model_name,
        task_types=task_types,
        tier=tier,
        default_params=default_params,
        cost_config=cost_config,
        rate_limit_config=rate_limit_config,
        is_default=is_default,
        status=status,
        metadata=metadata,
        username=principal.username,
    )


@mcp.tool(name="model.profile.list")
async def model_profile_list(
    task_type: str | None = None,
    status: str | None = "active",
    tier: str | None = None,
) -> list[dict[str, Any]]:
    """列出模型配置文件。支持按任务类型、状态、层级过滤。返回当前用户所有配置。模型是用户级别的。"""
    principal = await get_principal("read")
    logger.info("model_profile_list called, username=%s", principal.username)
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


@mcp.tool(name="model.auto_assign")
async def model_auto_assign(
    workspace: str,
    project: str,
) -> dict[str, Any]:
    """自动分析所有模型的能力并分配任务类型。AI 工具可调用此工具获取建议，确认后调用 model.profile.upsert 更新。"""
    principal = await get_principal("write")
    logger.info("model_auto_assign called")
    validate_required(locals(), "workspace", "project")

    models = await model_cost_service.list_profiles_by_user(
        username=principal.username, status=None,
    )

    assignments = []
    for m in models:
        name = (m.get("model_name") or "").lower()
        pk = m.get("profile_key", "")
        tasks = []

        # Analyze model name to determine capabilities
        # Embedding models: small params, specific embedding models
        if any(kw in name for kw in ("embed", "e5", "bge", "gte", "text-embedding")):
            tasks.append("embedding")
        elif any(kw in name for kw in ("rerank", "bge-rerank")):
            tasks.append("rerank")

        # Analysis models: good for style/pacing/arc analysis
        if any(kw in name for kw in ("deepseek", "glm-z1", "qwen3", "qwen2.5", "glm4")):
            if "embed" not in name and "rerank" not in name:
                tasks.append("analysis")

        # Review models: most general instruct models can review
        if any(kw in name for kw in ("instruct", "chat", "deepseek", "qwen", "glm")):
            if "embed" not in name and "rerank" not in name:
                tasks.append("review")

        # Context models: good for context compression/summarization
        if any(kw in name for kw in ("qwen2.5", "qwen3", "deepseek")):
            if "embed" not in name and "rerank" not in name:
                tasks.append("context")

        # Deduplicate
        tasks = list(dict.fromkeys(tasks))

        # If no tasks assigned but model is active, give generic ones
        if not tasks and m.get("status") == "active":
            tasks = ["review"]

        assignments.append({
            "profile_key": pk,
            "model_name": m.get("model_name"),
            "current_tasks": m.get("task_types") or [],
            "suggested_tasks": tasks,
        })

    return {
        "total_models": len(models),
        "assignments": assignments,
        "instruction": "请 review 上述建议，确认后依次调用 model.profile.upsert(workspace, project, profile_key=key, task_types=[...]) 更新",
    }
