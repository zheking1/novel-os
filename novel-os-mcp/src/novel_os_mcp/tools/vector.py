import logging
from typing import Any

from ..mcp_core import mcp
from ..deps import db, auth, vector_index_service, embedding_service, rerank_service, knowledge_service, vector_index, settings
from ..tool_auth import get_principal, validate_required
from ..utils import rows_to_dicts

logger = logging.getLogger("novel_os_mcp.tools.vector")


async def _vector_search_events(
    project_id: str,
    query_vector: list[float],
    limit: int,
) -> list[dict[str, Any]]:
    """Search events via Qdrant vector index."""
    if not vector_index:
        return []
    try:
        results = await vector_index.search(
            collection="novel_events",
            vector=query_vector,
            limit=limit,
            project_id=project_id,
        )
        return [
            {
                "id": r["id"],
                "score": r["score"],
                **r.get("payload", {}),
            }
            for r in results
        ]
    except Exception:
        logger.debug("Vector search events failed")
        return []


def _cosine_similarity(a: list[float], b: list[float]) -> float:
    """Compute cosine similarity between two vectors."""
    if not a or not b or len(a) != len(b):
        return 0.0
    dot = sum(x * y for x, y in zip(a, b))
    norm_a = sum(x * x for x in a) ** 0.5
    norm_b = sum(x * x for x in b) ** 0.5
    if norm_a == 0 or norm_b == 0:
        return 0.0
    return dot / (norm_a * norm_b)


@mcp.tool(name="vector.index.enqueue")
async def vector_index_enqueue(
    workspace: str,
    project: str,
    chunk_ids: list[str],
    collection: str = "memories",
    priority: int = 0,
) -> dict[str, Any]:
    """将内存块加入向量索引队列（增量索引）"""
    principal = await get_principal("write")
    logger.info("vector_index_enqueue called")
    validate_required(locals(), "chunk_ids")
    project_id = await auth.resolve_project_id(workspace, project, principal, access="write")
    return await vector_index_service.enqueue_bulk_index(
        project_id=project_id,
        chunk_ids=chunk_ids,
        collection=collection,
        priority=priority,
    )


@mcp.tool(name="vector.index.queue_stats")
async def vector_index_queue_stats(
    workspace: str,
    project: str | None = None,
) -> dict[str, Any]:
    """获取向量索引队列统计"""
    principal = await get_principal("read")
    logger.info("vector_index_queue_stats called")
    workspace_id = await auth.resolve_workspace_id(principal, workspace)

    if project:
        project_id = await auth.resolve_project_id(workspace, project, principal)
    else:
        project_id = None

    return await vector_index_service.get_queue_stats(project_id=project_id)


@mcp.tool(name="vector.index.pending_tasks")
async def vector_index_pending_tasks(
    workspace: str,
    project: str | None = None,
    collection: str | None = None,
    limit: int = 100,
) -> list[dict[str, Any]]:
    """获取待处理的向量索引任务"""
    principal = await get_principal("read")
    logger.info("vector_index_pending_tasks called")

    project_id = None
    if project:
        project_id = await auth.resolve_project_id(workspace, project, principal)

    return await vector_index_service.get_pending_tasks(
        project_id=project_id,
        limit=limit,
        collection=collection,
    )


@mcp.tool(name="vector.index.retry_failed")
async def vector_index_retry_failed(
    workspace: str,
    project: str | None = None,
    collection: str | None = None,
) -> dict[str, Any]:
    """重试失败的向量索引任务"""
    principal = await get_principal("write")
    logger.info("vector_index_retry_failed called")

    project_id = None
    if project:
        project_id = await auth.resolve_project_id(workspace, project, principal, access="write")

    return await vector_index_service.retry_failed_tasks(
        project_id=project_id,
        collection=collection,
    )


@mcp.tool(name="vector.index.status")
async def vector_index_status(
    workspace: str,
    project: str,
    collection: str = "memories",
) -> dict[str, Any] | None:
    """获取向量索引状态"""
    principal = await get_principal("read")
    logger.info("vector_index_status called")
    project_id = await auth.resolve_project_id(workspace, project, principal)
    return await vector_index_service.get_index_status(
        project_id=project_id,
        collection=collection,
    )


@mcp.tool(name="vector.index.process")
async def vector_index_process(
    worker_id: str,
    batch_size: int = 10,
) -> dict[str, Any]:
    """处理向量索引队列（worker 调用）"""
    principal = await get_principal("admin")
    logger.info("vector_index_process called")
    validate_required(locals(), "worker_id")
    return await vector_index_service.process_index_queue(
        worker_id=worker_id,
        batch_size=batch_size,
    )


@mcp.tool(name="embedding.status")
async def embedding_status(
    project_id: str,
) -> dict[str, Any]:
    """检查项目的 embedding 和 rerank 配置状态。"""
    principal = await get_principal(None)
    logger.info("embedding_status called")
    validate_required(locals(), "project_id")
    emb_config = await embedding_service._get_config(project_id)
    rr_config = await rerank_service._get_config(project_id)
    return {
        "embedding_configured": emb_config is not None,
        "embedding_provider": emb_config.get("provider") if emb_config else None,
        "embedding_model": emb_config.get("model_name") if emb_config else None,
        "rerank_configured": rr_config is not None,
        "rerank_provider": rr_config.get("provider") if rr_config else None,
        "rerank_model": rr_config.get("model_name") if rr_config else None,
    }


@mcp.tool(name="embedding.embed")
async def embedding_embed(
    project_id: str,
    texts: list[str],
) -> dict[str, Any]:
    """使用项目配置的模型生成文本向量。返回向量列表和维度信息。"""
    principal = await get_principal("write")
    logger.info("embedding_embed called")
    validate_required(locals(), "project_id", "texts")
    vectors = await embedding_service.embed(project_id=project_id, texts=texts)
    return {
        "ok": len(vectors) > 0,
        "count": len(vectors),
        "dimensions": len(vectors[0]) if vectors else 0,
        "vectors": vectors,
    }


@mcp.tool(name="embedding.rerank")
async def embedding_rerank(
    project_id: str,
    query: str,
    documents: list[str],
    top_n: int = 5,
) -> dict[str, Any]:
    """使用项目配置的模型对文档进行 rerank 排序。返回 top_n 相关结果。"""
    principal = await get_principal("write")
    logger.info("embedding_rerank called")
    validate_required(locals(), "project_id", "query", "documents")
    results = await rerank_service.rerank(project_id=project_id, query=query, documents=documents, top_n=top_n)
    return {
        "ok": True,
        "results": results,
    }


@mcp.tool(name="rag.search_knowledge")
async def rag_search_knowledge(
    project_id: str,
    query: str,
    category_slug: str | None = None,
    limit: int = 10,
) -> dict[str, Any]:
    """Search knowledge base using semantic embedding (RAG).

    Returns knowledge items relevant to the query.
    If embedding service is enabled, uses vector search.
    Falls back to keyword search if not available.
    """
    principal = await get_principal("read")
    logger.info("rag_search_knowledge called")

    query_vector = await embedding_service.embed_single(project_id=project_id, text=query)
    if query_vector:
        items = await knowledge_service.search_items(
            query=query,
            category_slug=category_slug,
            limit=limit * 2,
        )
        item_texts = [
            f"{item.get('title', '')} {item.get('summary', '') or item.get('content', '')[:200]}"
            for item in items
        ]
        if item_texts:
            item_vectors = await embedding_service.embed(project_id=project_id, texts=item_texts)
            scored = []
            for i, (item, vec) in enumerate(zip(items, item_vectors)):
                score = _cosine_similarity(query_vector, vec)
                scored.append({**item, "score": score})
            scored.sort(key=lambda x: x["score"], reverse=True)
            return {
                "ok": True,
                "method": "vector",
                "count": min(limit, len(scored)),
                "items": scored[:limit],
            }

    items = await knowledge_service.search_items(
        query=query,
        category_slug=category_slug,
        limit=limit,
    )
    return {
        "ok": True,
        "method": "keyword",
        "count": len(items),
        "items": items,
    }


@mcp.tool(name="rag.search_events")
async def rag_search_events(
    project_id: str,
    query: str,
    limit: int = 10,
) -> dict[str, Any]:
    """语义搜索事件。优先向量检索，无 embedding 时降级为关键词匹配。"""
    principal = await get_principal("read")
    logger.info("rag_search_events called")

    query_vector = await embedding_service.embed_single(project_id=project_id, text=query)
    if query_vector:
        results = await _vector_search_events(project_id, query_vector, limit)
        if results:
            return {"ok": True, "method": "vector", "count": len(results), "events": results}

    rows = await db.fetch(
        """
        SELECT e.id::text, e.title, e.summary, e.characters, e.locations,
               c.chapter_no, c.title AS chapter_title
        FROM events e
        JOIN chapters c ON c.id = e.chapter_id
        WHERE c.project_id = $1
          AND (e.title ILIKE $2 OR e.summary ILIKE $2)
        ORDER BY c.chapter_no DESC
        LIMIT $3
        """,
        project_id,
        f"%{query}%",
        limit,
    )
    return {"ok": True, "method": "keyword", "count": len(rows), "events": rows_to_dicts(rows)}
