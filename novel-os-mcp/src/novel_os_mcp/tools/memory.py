from typing import Any
import logging

from ..mcp_core import mcp
from ..config import get_settings
from ..deps import db, auth, memory_service, embedding_service, vector_index
from ..tool_auth import get_principal, validate_required

settings = get_settings()
logger = logging.getLogger("novel_os_mcp.tools.memory")


@mcp.tool(name="memory.search")
async def memory_search(
    workspace: str,
    project: str,
    query: str,
    source_types: list[str] | None = None,
    limit: int = 20,
) -> list[dict[str, Any]]:
    """语义搜索记忆。根据查询文本检索相关实体、快照和摘要。"""
    principal = await get_principal("read")
    logger.info("memory_search called")
    validate_required(locals(), "workspace", "project", "query")
    project_id = await auth.resolve_project_id(workspace, project, principal)
    return await memory_service.search(project_id=project_id, query=query, source_types=source_types, limit=limit)


@mcp.tool(name="memory.get_state")
async def memory_get_state(
    workspace: str,
    project: str,
    entity_type: str,
    name: str,
) -> dict[str, Any] | None:
    """获取实体当前状态。按类型和名称查询实体的最新快照。"""
    principal = await get_principal("read")
    logger.info("memory_get_state called")
    validate_required(locals(), "workspace", "project", "entity_type", "name")
    project_id = await auth.resolve_project_id(workspace, project, principal)
    return await memory_service.get_state(project_id=project_id, entity_type=entity_type, name=name)


@mcp.tool(name="state.entity.upsert")
async def state_entity_upsert(
    workspace: str,
    project: str,
    entity_type: str,
    name: str,
    aliases: list[str] | None = None,
    summary: str | None = None,
    description: str | None = None,
    portrait_url: str | None = None,
    profile: dict[str, Any] | None = None,
    lifecycle_status: str = "active",
    importance: str = "medium",
    tags: list[str] | None = None,
    first_seen_chapter_no: int | None = None,
    last_seen_chapter_no: int | None = None,
    first_seen_volume_no: int | None = None,
    last_seen_volume_no: int | None = None,
    source_type: str = "manual",
    source_id: str | None = None,
    metadata: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """创建或更新故事实体。实体可以是角色、地点、物品等，支持别名和属性档案。"""
    principal = await get_principal("write")
    logger.info("state_entity_upsert called")
    validate_required(locals(), "entity_type", "name")
    project_id = await auth.resolve_project_id(workspace, project, principal, access="write")
    return await memory_service.upsert_entity(
        project_id=project_id,
        entity_type=entity_type,
        name=name,
        aliases=aliases,
        summary=summary,
        description=description,
        portrait_url=portrait_url,
        profile=profile or {},
        lifecycle_status=lifecycle_status,
        importance=importance,
        tags=tags,
        first_seen_chapter_no=first_seen_chapter_no,
        last_seen_chapter_no=last_seen_chapter_no,
        first_seen_volume_no=first_seen_volume_no,
        last_seen_volume_no=last_seen_volume_no,
        source_type=source_type,
        source_id=source_id,
        metadata=metadata or {},
    )


@mcp.tool(name="state.entity.list")
async def state_entity_list(
    workspace: str,
    project: str,
    entity_type: str | None = None,
    lifecycle_status: str | None = None,
    query: str | None = None,
    tags: list[str] | None = None,
    include_archived: bool = False,
    limit: int = 100,
    offset: int = 0,
) -> list[dict[str, Any]]:
    """列出故事实体。支持按类型、状态、标签过滤和全文搜索。"""
    principal = await get_principal("read")
    logger.info("state_entity_list called")
    validate_required(locals(), "workspace", "project")
    project_id = await auth.resolve_project_id(workspace, project, principal)
    return await memory_service.list_entities(
        project_id=project_id,
        entity_type=entity_type,
        lifecycle_status=lifecycle_status,
        query=query,
        tags=tags,
        include_archived=include_archived,
        limit=limit,
        offset=offset,
    )


@mcp.tool(name="state.entity.get")
async def state_entity_get(
    workspace: str,
    project: str,
    entity_id: str | None = None,
    entity_type: str | None = None,
    name: str | None = None,
) -> dict[str, Any] | None:
    """获取单个实体详情。可通过 ID 或类型+名称组合查询。"""
    principal = await get_principal("read")
    logger.info("state_entity_get called")
    validate_required(locals(), "workspace", "project")
    project_id = await auth.resolve_project_id(workspace, project, principal)
    return await memory_service.get_entity(
        project_id=project_id,
        entity_id=entity_id,
        entity_type=entity_type,
        name=name,
    )


@mcp.tool(name="state.entity.bulk_patch")
async def state_entity_bulk_patch(
    workspace: str,
    project: str,
    entity_ids: list[str],
    patch: dict[str, Any],
) -> list[dict[str, Any]]:
    """批量更新实体属性。对多个实体应用相同的字段补丁。"""
    principal = await get_principal("write")
    logger.info("state_entity_bulk_patch called")
    validate_required(locals(), "workspace", "project")
    project_id = await auth.resolve_project_id(workspace, project, principal, access="write")
    return await memory_service.bulk_patch_entities(project_id=project_id, entity_ids=entity_ids, patch=patch)


@mcp.tool(name="state.snapshot.upsert")
async def state_snapshot_upsert(
    workspace: str,
    project: str,
    state: dict[str, Any],
    entity_id: str | None = None,
    entity_type: str | None = None,
    name: str | None = None,
    chapter_no: int | None = None,
    chapter_id: str | None = None,
    source_commit_id: str | None = None,
    is_current: bool = True,
    effective_chapter_no: int | None = None,
    expire_chapter_no: int | None = None,
    effective_volume_no: int | None = None,
    expire_volume_no: int | None = None,
    duration_type: str = "persistent",
    expires_on_event: str | None = None,
    confidence: float | None = None,
    source_type: str = "manual",
    source_id: str | None = None,
    change_reason: str | None = None,
    metadata: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """创建或更新实体状态快照。记录实体在特定章节的状态变化。"""
    principal = await get_principal("write")
    logger.info("state_snapshot_upsert called")
    validate_required(locals(), "workspace", "project")
    project_id = await auth.resolve_project_id(workspace, project, principal, access="write")
    return await memory_service.upsert_snapshot(
        project_id=project_id,
        state=state,
        entity_id=entity_id,
        entity_type=entity_type,
        name=name,
        chapter_no=chapter_no,
        chapter_id=chapter_id,
        source_commit_id=source_commit_id,
        is_current=is_current,
        effective_chapter_no=effective_chapter_no,
        expire_chapter_no=expire_chapter_no,
        effective_volume_no=effective_volume_no,
        expire_volume_no=expire_volume_no,
        duration_type=duration_type,
        expires_on_event=expires_on_event,
        confidence=confidence,
        source_type=source_type,
        source_id=source_id,
        change_reason=change_reason,
        metadata=metadata or {},
    )


@mcp.tool(name="state.snapshot.list")
async def state_snapshot_list(
    workspace: str,
    project: str,
    entity_id: str | None = None,
    entity_type: str | None = None,
    name: str | None = None,
    current_only: bool = False,
    current_chapter_no: int | None = None,
    include_expired: bool = True,
    limit: int = 100,
) -> list[dict[str, Any]]:
    """列出实体快照。可按实体筛选，支持只查当前有效快照。"""
    principal = await get_principal("read")
    logger.info("state_snapshot_list called")
    validate_required(locals(), "workspace", "project")
    project_id = await auth.resolve_project_id(workspace, project, principal)
    return await memory_service.list_snapshots(
        project_id=project_id,
        entity_id=entity_id,
        entity_type=entity_type,
        name=name,
        current_only=current_only,
        current_chapter_no=current_chapter_no,
        include_expired=include_expired,
        limit=limit,
    )


@mcp.tool(name="state.snapshot.at_chapter")
async def state_snapshot_at_chapter(
    workspace: str,
    project: str,
    entity_name: str,
    chapter_no: int,
) -> dict[str, Any]:
    """查询实体在指定章节时的状态。返回该章节时刻的完整状态快照，用于上下文回溯。"""
    principal = await get_principal("read")
    logger.info("state_snapshot_at_chapter called: %s @ ch%d", entity_name, chapter_no)
    validate_required(locals(), "workspace", "project", "entity_name", "chapter_no")
    project_id = await auth.resolve_project_id(workspace, project, principal)
    return await memory_service.get_snapshot_at_chapter(
        project_id=project_id,
        entity_name=entity_name,
        chapter_no=chapter_no,
    )


@mcp.tool(name="state.relationship.upsert")
async def state_relationship_upsert(
    workspace: str,
    project: str,
    relation_type: str,
    source_entity_id: str | None = None,
    source_entity_type: str | None = None,
    source_name: str | None = None,
    target_entity_id: str | None = None,
    target_entity_type: str | None = None,
    target_name: str | None = None,
    attitude: str | None = None,
    intensity: float | None = None,
    known_by_source: bool = True,
    known_by_target: bool = True,
    known_by_reader: bool = True,
    status: str = "active",
    source_chapter_no: int | None = None,
    source_chapter_id: str | None = None,
    source_commit_id: str | None = None,
    metadata: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """创建或更新实体间关系。至少传入 (source_entity_id) 或 (source_entity_type+source_name) 来标识源实体。target 同理。

    Args:
        relation_type: 关系类型，如 主从/盟友/敌对/师徒/亲缘/恋慕
        source_entity_id: 源实体 UUID（优先）
        source_entity_type: 源实体类型，如 character/location/faction
        source_name: 源实体名称
        target_entity_id: 目标实体 UUID（优先）
        target_entity_type: 目标实体类型
        target_name: 目标实体名称
        attitude: 关系态度，如 忠诚/友善/中立/敌意/仇恨
        intensity: 关系强度 0.0-1.0
    """
    principal = await get_principal("write")
    logger.info("state_relationship_upsert called")
    validate_required(locals(), "workspace", "project")
    project_id = await auth.resolve_project_id(workspace, project, principal, access="write")
    return await memory_service.upsert_relationship(
        project_id=project_id,
        relation_type=relation_type,
        source_entity_id=source_entity_id,
        source_entity_type=source_entity_type,
        source_name=source_name,
        target_entity_id=target_entity_id,
        target_entity_type=target_entity_type,
        target_name=target_name,
        attitude=attitude,
        intensity=intensity,
        known_by_source=known_by_source,
        known_by_target=known_by_target,
        known_by_reader=known_by_reader,
        status=status,
        source_chapter_no=source_chapter_no,
        source_chapter_id=source_chapter_id,
        source_commit_id=source_commit_id,
        metadata=metadata or {},
    )


@mcp.tool(name="state.relationship.list")
async def state_relationship_list(
    workspace: str,
    project: str,
    entity_id: str | None = None,
    entity_type: str | None = None,
    name: str | None = None,
    relation_type: str | None = None,
    status: str | None = "active",
    include_reader_hidden: bool = True,
    limit: int = 100,
) -> list[dict[str, Any]]:
    """列出实体关系。支持按实体、关系类型和状态过滤。"""
    principal = await get_principal("read")
    logger.info("state_relationship_list called")
    validate_required(locals(), "workspace", "project")
    project_id = await auth.resolve_project_id(workspace, project, principal)
    return await memory_service.list_relationships(
        project_id=project_id,
        entity_id=entity_id,
        entity_type=entity_type,
        name=name,
        relation_type=relation_type,
        status=status,
        include_reader_hidden=include_reader_hidden,
        limit=limit,
    )


@mcp.tool(name="memory.get_recent_summaries")
async def memory_get_recent_summaries(
    workspace: str,
    project: str,
    before_chapter_no: int,
    count: int = 8,
) -> list[dict[str, Any]]:
    """获取最近的章节摘要。返回指定章节之前的历史摘要列表。"""
    principal = await get_principal("read")
    logger.info("memory_get_recent_summaries called")
    validate_required(locals(), "workspace", "project")
    project_id = await auth.resolve_project_id(workspace, project, principal)
    return await memory_service.recent_summaries(project_id=project_id, before_chapter_no=before_chapter_no, count=count)


@mcp.tool(name="memory.rebuild_projection")
async def memory_rebuild_projection(
    workspace: str,
    project: str,
    from_chapter_no: int | None = None,
) -> dict[str, Any]:
    """重建记忆投影。从指定章节重新计算所有实体的当前状态。"""
    principal = await get_principal("write")
    logger.info("memory_rebuild_projection called")
    validate_required(locals(), "workspace", "project")
    project_id = await auth.resolve_project_id(workspace, project, principal, access="write")
    return await memory_service.rebuild_projection(project_id=project_id, from_chapter_no=from_chapter_no)


@mcp.tool(name="memory.pending_vector_chunks")
async def memory_pending_vector_chunks(
    workspace: str,
    project: str,
    limit: int = 50,
) -> list[dict[str, Any]]:
    """查询待向量化的记忆块。返回尚未建立向量索引的数据块。"""
    principal = await get_principal("read")
    logger.info("memory_pending_vector_chunks called")
    validate_required(locals(), "workspace", "project")
    project_id = await auth.resolve_project_id(workspace, project, principal)
    return await memory_service.pending_vector_chunks(project_id=project_id, limit=limit)


@mcp.tool(name="memory.upsert_vector")
async def memory_upsert_vector(
    workspace: str,
    project: str,
    chunk_id: str,
    vector: list[float],
    collection: str | None = None,
    payload: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """写入向量到 Qdrant。为指定记忆块存储向量嵌入，用于语义搜索。"""
    principal = await get_principal("write")
    logger.info("memory_upsert_vector called")
    validate_required(locals(), "workspace", "project", "chunk_id")
    project_id = await auth.resolve_project_id(workspace, project, principal, access="write")
    point_id = chunk_id
    target_collection = collection or settings.qdrant_memory_collection
    qdrant_payload = {
        "project_id": project_id,
        "chunk_id": chunk_id,
        **(payload or {}),
    }
    await vector_index.upsert_memory_point(
        collection=target_collection,
        point_id=point_id,
        vector=vector,
        payload=qdrant_payload,
    )
    return await memory_service.mark_vector_indexed(
        project_id=project_id,
        chunk_id=chunk_id,
        collection=target_collection,
        point_id=point_id,
    )


@mcp.tool(name="memory.vector_search")
async def memory_vector_search(
    workspace: str,
    project: str,
    vector: list[float],
    collection: str | None = None,
    limit: int = 10,
) -> list[dict[str, Any]]:
    """向量相似度搜索。在 Qdrant 中查找与给定向量最相似的记忆块。"""
    principal = await get_principal("read")
    logger.info("memory_vector_search called")
    validate_required(locals(), "workspace", "project")
    project_id = await auth.resolve_project_id(workspace, project, principal)
    return await vector_index.search(
        collection=collection or settings.qdrant_memory_collection,
        vector=vector,
        limit=limit,
        project_id=project_id,
    )


@mcp.tool(name="memory.vectorize_pending")
async def memory_vectorize_pending(
    workspace: str,
    project: str,
    batch_size: int = 10,
) -> dict[str, Any]:
    """向量化待处理的记忆块，用于语义搜索。"""
    principal = await get_principal("write")
    logger.info("memory_vectorize_pending called")
    validate_required(locals(), "workspace", "project")
    project_id = await auth.resolve_project_id(workspace, project, principal, access="write")
    return await memory_service.vectorize_pending_chunks(
        project_id=project_id,
        batch_size=batch_size,
    )
