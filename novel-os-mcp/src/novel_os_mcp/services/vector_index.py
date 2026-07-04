import logging
from typing import Any

from ..db import Database
from ..vector import VectorIndex
from ..utils import json_dumps, row_to_dict, rows_to_dicts

logger = logging.getLogger("novel_os_mcp.services.vector_index")


class VectorIndexService:
    """向量索引服务 - 管理向量搜索索引"""

    def __init__(self, db: Database):
        self._db = db

    async def create_index(
        self,
        project_id: str,
        index_name: str,
        index_type: str = "hnsw",
        dimension: int = 1536,
        distance_metric: str = "cosine",
        description: str | None = None,
    ) -> dict[str, Any]:
        row = await self._db.fetchrow(
            """
            INSERT INTO vector_indexes
              (project_id, index_name, index_type, dimension, distance_metric, description, status)
            VALUES ($1, $2, $3, $4, $5, $6, 'active')
            RETURNING id::text, project_id::text, index_name, index_type, dimension,
                      distance_metric, description, status, created_at
            """,
            project_id,
            index_name,
            index_type,
            dimension,
            distance_metric,
            description,
        )
        return row_to_dict(row)

    async def get_indexes(
        self,
        project_id: str,
    ) -> list[dict[str, Any]]:
        rows = await self._db.fetch(
            """
            SELECT id::text, project_id::text, index_name, index_type, dimension,
                  distance_metric, description, status, item_count, created_at
            FROM vector_indexes
            WHERE project_id = $1
            ORDER BY created_at DESC
            """,
            project_id,
        )
        return rows_to_dicts(rows)

    async def update_index_status(
        self,
        index_id: str,
        status: str,
        item_count: int | None = None,
    ) -> dict[str, Any]:
        if item_count is not None:
            row = await self._db.fetchrow(
                """
                UPDATE vector_indexes SET status = $2, item_count = $3 WHERE id = $1
                RETURNING id::text, project_id::text, index_name, index_type, dimension,
                          distance_metric, description, status, item_count, created_at
                """,
                index_id,
                status,
                item_count,
            )
        else:
            row = await self._db.fetchrow(
                """
                UPDATE vector_indexes SET status = $2 WHERE id = $1
                RETURNING id::text, project_id::text, index_name, index_type, dimension,
                          distance_metric, description, status, item_count, created_at
                """,
                index_id,
                status,
            )
        return row_to_dict(row) if row else {}

    async def delete_index(self, index_id: str) -> bool:
        result = await self._db.execute("DELETE FROM vector_indexes WHERE id = $1", index_id)
        return result == "DELETE 1"

    async def add_items(
        self,
        index_id: str,
        items: list[dict[str, Any]],
    ) -> dict[str, Any]:
        added = 0
        for item in items:
            content = item.get("content", "")
            embedding = item.get("embedding")
            item_type = item.get("item_type", "text")
            source_id = item.get("source_id")
            metadata = item.get("metadata")

            if not content or embedding is None:
                continue

            await self._db.execute(
                """
                INSERT INTO vector_index_items
                  (index_id, content, embedding, item_type, source_id, metadata)
                VALUES ($1, $2, $3, $4, $5, $6)
                """,
                index_id,
                content,
                embedding,
                item_type,
                source_id,
                json_dumps(metadata) if metadata else None,
            )
            added += 1

        row = await self._db.fetchrow(
            """
            UPDATE vector_indexes
            SET item_count = (SELECT COUNT(*)::int FROM vector_index_items WHERE index_id = $1)
            WHERE id = $1
            RETURNING id::text, item_count
            """,
            index_id,
        )

        return {"added": added, "total": row["item_count"] if row else added}

    async def search(
        self,
        index_id: str,
        query_embedding: list[float],
        top_k: int = 10,
        item_type: str | None = None,
        filter_metadata: dict[str, Any] | None = None,
    ) -> list[dict[str, Any]]:
        conditions = ["index_id = $1"]
        params: list[Any] = [index_id]
        idx = 2

        if item_type:
            conditions.append(f"item_type = ${idx}")
            params.append(item_type)
            idx += 1

        where = " AND ".join(conditions)

        rows = await self._db.fetch(
            f"""
            SELECT id::text, content, item_type, source_id, metadata,
                   1 - (embedding <=> $2::vector) AS similarity
            FROM vector_index_items
            WHERE {where}
            ORDER BY embedding <=> $2::vector
            LIMIT ${idx}
            """,
            *params,
            query_embedding,
            top_k,
        )

        results = []
        for row in rows:
            r = row_to_dict(row)
            if r.get("metadata"):
                try:
                    import json
                    r["metadata"] = json.loads(r["metadata"]) if isinstance(r["metadata"], str) else r["metadata"]
                except Exception:
                    pass
            r["similarity"] = float(r.get("similarity", 0))
            results.append(r)

        return results

    async def delete_items(
        self,
        index_id: str,
        item_ids: list[str] | None = None,
        source_id: str | None = None,
    ) -> int:
        if item_ids:
            result = await self._db.execute(
                "DELETE FROM vector_index_items WHERE index_id = $1 AND id = ANY($2)",
                index_id,
                item_ids,
            )
        elif source_id:
            result = await self._db.execute(
                "DELETE FROM vector_index_items WHERE index_id = $1 AND source_id = $2",
                index_id,
                source_id,
            )
        else:
            result = await self._db.execute(
                "DELETE FROM vector_index_items WHERE index_id = $1",
                index_id,
            )

        count = int(result.split()[-1]) if result.startswith("DELETE") else 0

        await self._db.execute(
            """
            UPDATE vector_indexes
            SET item_count = (SELECT COUNT(*)::int FROM vector_index_items WHERE index_id = $1)
            WHERE id = $1
            """,
            index_id,
        )

        return count

    async def get_index_stats(
        self,
        index_id: str,
    ) -> dict[str, Any]:
        row = await self._db.fetchrow(
            """
            SELECT
              COUNT(*)::int AS total_items,
              COUNT(DISTINCT item_type)::int AS distinct_types,
              COUNT(DISTINCT source_id)::int AS distinct_sources
            FROM vector_index_items
            WHERE index_id = $1
            """,
            index_id,
        )
        return row_to_dict(row) if row else {}
