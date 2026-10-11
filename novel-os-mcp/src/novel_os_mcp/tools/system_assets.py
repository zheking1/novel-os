"""System Assets Tools - 系统级资源管理

提供系统级文风档案、提示词模板、模型配置的查询和管理工具。
"""

from typing import Any
import logging

from ..mcp_core import mcp
from ..deps import db, auth
from ..tool_auth import get_principal, validate_required

logger = logging.getLogger("novel_os_mcp.tools.system_assets")


# ============================================================================
# 系统级文风档案工具
# ============================================================================

@mcp.tool(name="system.style_profile.list")
async def system_style_profile_list(
    workspace: str,
    genre: str | None = None,
    status: str = "active",
    limit: int = 50,
    offset: int = 0,
    project: str | None = None,
) -> dict[str, Any]:
    """获取系统级文风档案列表。
    
    Args:
        genre: 按题材筛选
        status: 按状态筛选 (active/deprecated/draft)
        limit: 返回数量限制
        offset: 分页偏移
        
    Returns:
        {
            "profiles": [...],
            "total": 总数
        }
    """
    principal = await get_principal("read")
    
    conditions = ["status = $1"]
    params: list[Any] = [status]
    
    if genre:
        conditions.append(f"$2 = ANY(applicable_genres)")
        params.append(genre)
    
    # 查询总数
    total = await db.fetchval(
        f"SELECT COUNT(*) FROM system_style_profiles WHERE {' AND '.join(conditions)}",
        *params
    )
    
    # 查询数据
    params.extend([limit, offset])
    rows = await db.fetch(
        f"""
        SELECT 
            id::text, profile_key, display_name, narrative_pov, tense, tone,
            target_metrics, description, applicable_genres, version, status,
            created_at
        FROM system_style_profiles
        WHERE {' AND '.join(conditions)}
        ORDER BY display_name
        LIMIT ${len(params)-1} OFFSET ${len(params)}
        """,
        *params
    )
    
    profiles = []
    for row in rows:
        profiles.append({
            "id": row["id"],
            "profile_key": row["profile_key"],
            "display_name": row["display_name"],
            "narrative_pov": row["narrative_pov"],
            "tense": row["tense"],
            "tone": row["tone"],
            "target_metrics": row["target_metrics"],
            "description": row["description"],
            "applicable_genres": row["applicable_genres"],
            "version": row["version"],
            "status": row["status"],
            "created_at": row["created_at"].isoformat() if row["created_at"] else None,
        })
    
    return {
        "profiles": profiles,
        "total": total,
        "limit": limit,
        "offset": offset
    }


@mcp.tool(name="system.style_profile.get")
async def system_style_profile_get(
    workspace: str,
    profile_key: str,
    project: str | None = None,
) -> dict[str, Any]:
    """获取系统级文风档案详情。
    
    Args:
        profile_key: 文风档案业务键
        
    Returns:
        文风档案完整详情
    """
    principal = await get_principal("read")
    validate_required(locals(), "profile_key")
    
    row = await db.fetchrow(
        """
        SELECT 
            id::text, profile_key, display_name, narrative_pov, tense, tone,
            target_metrics, description, characteristics, sample_paragraphs,
            applicable_genres, version, version_history, status,
            created_from_proposal_id, created_at, updated_at
        FROM system_style_profiles
        WHERE profile_key = $1
        """,
        profile_key
    )
    
    if not row:
        raise ValueError(f"Style profile not found: {profile_key}")
    
    return {
        "id": row["id"],
        "profile_key": row["profile_key"],
        "display_name": row["display_name"],
        "narrative_pov": row["narrative_pov"],
        "tense": row["tense"],
        "tone": row["tone"],
        "target_metrics": row["target_metrics"],
        "description": row["description"],
        "characteristics": row["characteristics"],
        "sample_paragraphs": row["sample_paragraphs"],
        "applicable_genres": row["applicable_genres"],
        "version": row["version"],
        "version_history": row["version_history"],
        "status": row["status"],
        "created_from_proposal_id": row["created_from_proposal_id"],
        "created_at": row["created_at"].isoformat() if row["created_at"] else None,
        "updated_at": row["updated_at"].isoformat() if row["updated_at"] else None,
    }


@mcp.tool(name="system.style_profile.fork")
async def system_style_profile_fork(
    workspace: str,
    profile_key: str,
    project_id: str,
    customizations: dict[str, Any] | None = None,
    project: str | None = None,
) -> dict[str, Any]:
    """将系统级文风档案继承到项目。
    
    复制系统级文风档案到项目级，可以进行个性化调整。
    
    Args:
        profile_key: 系统文风档案键
        project_id: 目标项目ID
        customizations: 自定义调整（可选）
        
    Returns:
        {
            "project_profile_id": "项目级文风档案ID",
            "message": "继承成功"
        }
    """
    principal = await get_principal("write")
    await auth.require_project_access(principal, project_id, access="write")
    
    validate_required(locals(), "profile_key", "project_id")
    
    # 获取系统级文风档案
    system_profile = await db.fetchrow(
        """
        SELECT display_name, narrative_pov, tense, tone, target_metrics,
               description, characteristics, sample_paragraphs
        FROM system_style_profiles
        WHERE profile_key = $1 AND status = 'active'
        """,
        profile_key
    )
    
    if not system_profile:
        raise ValueError(f"Active style profile not found: {profile_key}")
    
    # 应用自定义调整
    profile_data = dict(system_profile)
    if customizations:
        profile_data.update(customizations)
    
    # 创建项目级文风档案
    # style_profiles 的真实列（见 203_style_fingerprint.sql）只有：
    #   project_id / profile_name / narrative_pov / tense / tone / target_metrics
    # 系统档案的 description / characteristics / sample_paragraphs 与来源标记
    # 均无对应列，统一折叠进 target_metrics，避免报 UndefinedColumn。
    import json

    metrics = profile_data.get("target_metrics") or {}
    if isinstance(metrics, str):
        try:
            metrics = json.loads(metrics)
        except (TypeError, ValueError):
            metrics = {}
    metrics = dict(metrics)
    metrics["_forked_from_system_key"] = profile_key
    metrics["_description"] = profile_data.get("description")
    metrics["_characteristics"] = profile_data.get("characteristics")
    metrics["_sample_paragraphs"] = profile_data.get("sample_paragraphs")

    row = await db.fetchrow(
        """
        INSERT INTO style_profiles
        (project_id, profile_name, narrative_pov, tense, tone, target_metrics)
        VALUES ($1, $2, $3, $4, $5, $6::jsonb)
        ON CONFLICT (project_id, profile_name) DO UPDATE
          SET narrative_pov = EXCLUDED.narrative_pov,
              tense = EXCLUDED.tense,
              tone = EXCLUDED.tone,
              target_metrics = EXCLUDED.target_metrics,
              updated_at = now()
        RETURNING id::text
        """,
        project_id,
        profile_data["display_name"],
        profile_data["narrative_pov"],
        profile_data["tense"],
        profile_data["tone"],
        json.dumps(metrics, ensure_ascii=False),
    )
    
    return {
        "project_profile_id": row["id"],
        "forked_from": profile_key,
        "message": f"成功继承文风档案 '{system_profile['display_name']}' 到项目"
    }


@mcp.tool(name="system.style_profile.create")
async def system_style_profile_create(
    workspace: str,
    profile_key: str,
    display_name: str,
    tone: str,
    description: str,
    narrative_pov: str = "third_limited",
    tense: str = "past",
    target_metrics: dict[str, Any] | None = None,
    characteristics: dict[str, Any] | None = None,
    sample_paragraphs: list[str] | None = None,
    applicable_genres: list[str] | None = None,
    project: str | None = None,
) -> dict[str, Any]:
    """创建系统级文风档案（管理员）。
    
    直接创建新的系统级文风档案。注意：通常应该通过进化流程创建。
    
    Args:
        profile_key: 唯一业务键
        display_name: 显示名称
        tone: 基调描述
        description: 详细描述
        narrative_pov: 叙事视角 (first/second/third_limited/third_omniscient)
        tense: 时态 (present/past)
        target_metrics: 目标指标
        characteristics: 风格特征
        sample_paragraphs: 示例段落
        applicable_genres: 适用题材
        
    Returns:
        {
            "id": "档案ID",
            "profile_key": "业务键",
            "message": "创建成功"
        }
    """
    principal = await get_principal("write")
    # await auth.require_admin(principal)
    
    validate_required(locals(), "profile_key", "display_name", "tone", "description")
    
    # 检查key是否已存在
    existing = await db.fetchval(
        "SELECT 1 FROM system_style_profiles WHERE profile_key = $1",
        profile_key
    )
    if existing:
        raise ValueError(f"Style profile with key '{profile_key}' already exists")
    
    row = await db.fetchrow(
        """
        INSERT INTO system_style_profiles 
        (profile_key, display_name, narrative_pov, tense, tone, target_metrics,
         description, characteristics, sample_paragraphs, applicable_genres, status)
        VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, 'active')
        RETURNING id::text
        """,
        profile_key, display_name, narrative_pov, tense, tone,
        target_metrics or {}, description, characteristics or {},
        sample_paragraphs or [], applicable_genres or []
    )
    
    return {
        "id": row["id"],
        "profile_key": profile_key,
        "display_name": display_name,
        "message": f"系统级文风档案 '{display_name}' 创建成功"
    }


# ============================================================================
# 系统级提示词模板工具
# ============================================================================

@mcp.tool(name="system.prompt_template.list")
async def system_prompt_template_list(
    workspace: str,
    template_type: str | None = None,
    genre: str | None = None,
    status: str = "active",
    limit: int = 50,
    offset: int = 0,
    project: str | None = None,
) -> dict[str, Any]:
    """获取系统级提示词模板列表。
    
    Args:
        template_type: 按类型筛选 (outline/scene/profile/polish/review)
        genre: 按题材筛选
        status: 按状态筛选
        limit: 返回数量限制
        offset: 分页偏移
        
    Returns:
        {
            "templates": [...],
            "total": 总数
        }
    """
    principal = await get_principal("read")
    
    conditions = ["status = $1"]
    params: list[Any] = [status]
    
    if template_type:
        conditions.append(f"template_type = ${len(params)+1}")
        params.append(template_type)
    
    if genre:
        conditions.append(f"(genre = ${len(params)+1} OR genre IS NULL)")
        params.append(genre)
    
    total = await db.fetchval(
        f"SELECT COUNT(*) FROM system_prompt_templates WHERE {' AND '.join(conditions)}",
        *params
    )
    
    params.extend([limit, offset])
    rows = await db.fetch(
        f"""
        SELECT 
            id::text, template_key, template_name, template_type,
            genre, scene, description, version, status, created_at
        FROM system_prompt_templates
        WHERE {' AND '.join(conditions)}
        ORDER BY template_type, template_name
        LIMIT ${len(params)-1} OFFSET ${len(params)}
        """,
        *params
    )
    
    templates = []
    for row in rows:
        templates.append({
            "id": row["id"],
            "template_key": row["template_key"],
            "template_name": row["template_name"],
            "template_type": row["template_type"],
            "genre": row["genre"],
            "scene": row["scene"],
            "description": row["description"],
            "version": row["version"],
            "status": row["status"],
            "created_at": row["created_at"].isoformat() if row["created_at"] else None,
        })
    
    return {
        "templates": templates,
        "total": total,
        "limit": limit,
        "offset": offset
    }


@mcp.tool(name="system.prompt_template.get")
async def system_prompt_template_get(
    workspace: str,
    template_key: str,
    project: str | None = None,
) -> dict[str, Any]:
    """获取系统级提示词模板详情。
    
    Args:
        template_key: 模板业务键
        
    Returns:
        模板完整详情
    """
    principal = await get_principal("read")
    validate_required(locals(), "template_key")
    
    row = await db.fetchrow(
        """
        SELECT 
            id::text, template_key, template_name, template_content,
            description, template_type, genre, scene, variables,
            version, version_history, status, created_at, updated_at
        FROM system_prompt_templates
        WHERE template_key = $1
        """,
        template_key
    )
    
    if not row:
        raise ValueError(f"Prompt template not found: {template_key}")
    
    return {
        "id": row["id"],
        "template_key": row["template_key"],
        "template_name": row["template_name"],
        "template_content": row["template_content"],
        "description": row["description"],
        "template_type": row["template_type"],
        "genre": row["genre"],
        "scene": row["scene"],
        "variables": row["variables"],
        "version": row["version"],
        "version_history": row["version_history"],
        "status": row["status"],
        "created_at": row["created_at"].isoformat() if row["created_at"] else None,
        "updated_at": row["updated_at"].isoformat() if row["updated_at"] else None,
    }


@mcp.tool(name="system.prompt_template.render")
async def system_prompt_template_render(
    workspace: str,
    template_key: str,
    variables: dict[str, Any],
    project: str | None = None,
) -> dict[str, Any]:
    """渲染提示词模板。
    
    使用提供的变量渲染模板内容。
    
    Args:
        template_key: 模板业务键
        variables: 模板变量值
        
    Returns:
        {
            "rendered_content": "渲染后的内容",
            "template_key": "模板键",
            "variables_used": [...]
        }
    """
    principal = await get_principal("read")
    validate_required(locals(), "template_key", "variables")
    
    # 获取模板
    template = await db.fetchrow(
        "SELECT template_content, variables FROM system_prompt_templates WHERE template_key = $1",
        template_key
    )
    
    if not template:
        raise ValueError(f"Prompt template not found: {template_key}")
    
    content = template["template_content"]
    template_vars = template["variables"] or []
    
    # 简单的变量替换
    rendered = content
    variables_used = []
    missing_vars = []
    
    for var in template_vars:
        var_name = var.get("name")
        placeholder = "{" + var_name + "}"
        
        if var_name in variables:
            value = variables[var_name]
            # 处理不同类型的值
            if isinstance(value, (list, dict)):
                value = str(value)
            rendered = rendered.replace(placeholder, str(value))
            variables_used.append(var_name)
        elif var.get("required", False):
            missing_vars.append(var_name)
    
    if missing_vars:
        raise ValueError(f"Missing required variables: {missing_vars}")
    
    return {
        "rendered_content": rendered,
        "template_key": template_key,
        "variables_used": variables_used,
        "missing_variables": missing_vars
    }


@mcp.tool(name="system.prompt_template.fork")
async def system_prompt_template_fork(
    workspace: str,
    template_key: str,
    project_id: str,
    custom_name: str | None = None,
    project: str | None = None,
) -> dict[str, Any]:
    """将系统级提示词模板导入到项目。
    
    Args:
        template_key: 系统模板键
        project_id: 目标项目ID
        custom_name: 自定义名称（可选）
        
    Returns:
        {
            "project_template_id": "项目级模板ID",
            "message": "导入成功"
        }
    """
    principal = await get_principal("write")
    validate_required(locals(), "template_key", "project_id")
    
    # 获取系统模板
    system_template = await db.fetchrow(
        """
        SELECT template_name, template_content, description, template_type,
               genre, scene, variables
        FROM system_prompt_templates
        WHERE template_key = $1 AND status = 'active'
        """,
        template_key
    )
    
    if not system_template:
        raise ValueError(f"Active prompt template not found: {template_key}")
    
    # 创建项目级模板
    # prompt_templates 的真实列（见 160_p7_enhancement.sql）：
    #   project_id / template_key / name / description / template_content /
    #   template_type / variables / genre / scene
    # 注意：列名是 name 而非 template_name；forked_from_system_key 仅 model_profiles 才有。
    import json

    name = custom_name or system_template["template_name"]

    row = await db.fetchrow(
        """
        INSERT INTO prompt_templates
        (project_id, template_key, name, template_content, description,
         template_type, genre, scene, variables)
        VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9::jsonb)
        ON CONFLICT (project_id, template_key) DO UPDATE
          SET name = EXCLUDED.name,
              template_content = EXCLUDED.template_content,
              description = EXCLUDED.description,
              template_type = EXCLUDED.template_type,
              genre = EXCLUDED.genre,
              scene = EXCLUDED.scene,
              variables = EXCLUDED.variables
        RETURNING id::text
        """,
        project_id,
        template_key,
        name,
        system_template["template_content"],
        system_template["description"],
        system_template["template_type"],
        system_template["genre"],
        system_template["scene"],
        json.dumps(system_template["variables"] or []),
    )
    
    return {
        "project_template_id": row["id"],
        "forked_from": template_key,
        "template_name": name,
        "message": f"成功导入模板 '{system_template['template_name']}' 到项目"
    }


# ============================================================================
# 系统级模型配置工具
# ============================================================================

@mcp.tool(name="system.model_profile.list")
async def system_model_profile_list(
    workspace: str,
    task_type: str | None = None,
    status: str = "active",
    limit: int = 50,
    offset: int = 0,
    project: str | None = None,
) -> dict[str, Any]:
    """获取系统级模型配置列表。
    
    Args:
        task_type: 按任务类型筛选
        status: 按状态筛选
        limit: 返回数量限制
        offset: 分页偏移
        
    Returns:
        {
            "profiles": [...],
            "total": 总数
        }
    """
    principal = await get_principal("read")
    
    conditions = ["status = $1"]
    params: list[Any] = [status]
    
    if task_type:
        conditions.append(f"$2 = ANY(task_types)")
        params.append(task_type)
    
    total = await db.fetchval(
        f"SELECT COUNT(*) FROM system_model_profiles WHERE {' AND '.join(conditions)}",
        *params
    )
    
    params.extend([limit, offset])
    rows = await db.fetch(
        f"""
        SELECT 
            id::text, profile_key, display_name, provider, model_name,
            task_types, recommended_for, version, status, created_at
        FROM system_model_profiles
        WHERE {' AND '.join(conditions)}
        ORDER BY display_name
        LIMIT ${len(params)-1} OFFSET ${len(params)}
        """,
        *params
    )
    
    profiles = []
    for row in rows:
        profiles.append({
            "id": row["id"],
            "profile_key": row["profile_key"],
            "display_name": row["display_name"],
            "provider": row["provider"],
            "model_name": row["model_name"],
            "task_types": row["task_types"],
            "recommended_for": row["recommended_for"],
            "version": row["version"],
            "status": row["status"],
            "created_at": row["created_at"].isoformat() if row["created_at"] else None,
        })
    
    return {
        "profiles": profiles,
        "total": total,
        "limit": limit,
        "offset": offset
    }


@mcp.tool(name="system.model_profile.get")
async def system_model_profile_get(
    workspace: str,
    profile_key: str,
    project: str | None = None,
) -> dict[str, Any]:
    """获取系统级模型配置详情。
    
    Args:
        profile_key: 配置业务键
        
    Returns:
        配置完整详情
    """
    principal = await get_principal("read")
    validate_required(locals(), "profile_key")
    
    row = await db.fetchrow(
        """
        SELECT 
            id::text, profile_key, display_name, provider, model_name,
            task_types, default_params, cost_config, rate_limit_config,
            recommended_for, version, version_history, status,
            created_at, updated_at
        FROM system_model_profiles
        WHERE profile_key = $1
        """,
        profile_key
    )
    
    if not row:
        raise ValueError(f"Model profile not found: {profile_key}")
    
    return {
        "id": row["id"],
        "profile_key": row["profile_key"],
        "display_name": row["display_name"],
        "provider": row["provider"],
        "model_name": row["model_name"],
        "task_types": row["task_types"],
        "default_params": row["default_params"],
        "cost_config": row["cost_config"],
        "rate_limit_config": row["rate_limit_config"],
        "recommended_for": row["recommended_for"],
        "version": row["version"],
        "version_history": row["version_history"],
        "status": row["status"],
        "created_at": row["created_at"].isoformat() if row["created_at"] else None,
        "updated_at": row["updated_at"].isoformat() if row["updated_at"] else None,
    }


@mcp.tool(name="system.model_profile.fork")
async def system_model_profile_fork(
    workspace: str,
    system_profile_key: str,
    user_customizations: dict[str, Any] | None = None,
    project: str | None = None,
) -> dict[str, Any]:
    """用户复制系统级模型配置。
    
    复制系统级模型配置到用户级，可以进行个性化调整。
    
    Args:
        system_profile_key: 系统配置键
        user_customizations: 用户自定义配置（可选）
        
    Returns:
        {
            "user_profile_id": "用户配置ID",
            "profile_key": "配置键",
            "message": "复制成功"
        }
    """
    principal = await get_principal("write")
    validate_required(locals(), "system_profile_key")
    
    # 获取系统配置
    system_profile = await db.fetchrow(
        """
        SELECT display_name, provider, model_name, task_types, default_params,
               cost_config, rate_limit_config
        FROM system_model_profiles
        WHERE profile_key = $1 AND status = 'active'
        """,
        system_profile_key
    )
    
    if not system_profile:
        raise ValueError(f"Active model profile not found: {system_profile_key}")
    
    # 生成用户配置key
    user_profile_key = f"{principal.username}_{system_profile_key}"
    
    # 应用用户自定义
    profile_data = dict(system_profile)
    if user_customizations:
        profile_data.update(user_customizations)
    
    # 创建用户级配置
    row = await db.fetchrow(
        """
        INSERT INTO model_profiles 
        (user_id, profile_key, display_name, provider, model_name, task_types,
         default_params, cost_config, rate_limit_config, is_system, forked_from_system_key)
        VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, false, $10)
        ON CONFLICT (user_id, profile_key) DO UPDATE SET
            display_name = EXCLUDED.display_name,
            provider = EXCLUDED.provider,
            model_name = EXCLUDED.model_name,
            task_types = EXCLUDED.task_types,
            default_params = EXCLUDED.default_params,
            cost_config = EXCLUDED.cost_config,
            rate_limit_config = EXCLUDED.rate_limit_config,
            updated_at = now()
        RETURNING id::text
        """,
        principal.user_id if hasattr(principal, 'user_id') else None,
        user_profile_key,
        profile_data["display_name"],
        profile_data["provider"],
        profile_data["model_name"],
        profile_data["task_types"],
        profile_data["default_params"],
        profile_data["cost_config"],
        profile_data["rate_limit_config"],
        system_profile_key
    )
    
    return {
        "user_profile_id": row["id"],
        "profile_key": user_profile_key,
        "forked_from": system_profile_key,
        "message": f"成功复制模型配置 '{system_profile['display_name']}'"
    }
