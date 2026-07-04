from typing import Any

from qdrant_client import AsyncQdrantClient
from qdrant_client.http import models

from .config import Settings


class VectorIndex:
    def __init__(self, settings: Settings):
        self._settings = settings
        self._client: AsyncQdrantClient | None = None

    @property
    def client(self) -> AsyncQdrantClient:
        if self._client is None:
            self._client = AsyncQdrantClient(
                url=self._settings.qdrant_url,
                api_key=self._settings.qdrant_api_key,
            )
        return self._client

    async def upsert_memory_point(
        self,
        collection: str,
        point_id: str,
        vector: list[float],
        payload: dict[str, Any],
    ) -> None:
        await self.client.upsert(
            collection_name=collection,
            points=[
                models.PointStruct(
                    id=point_id,
                    vector=vector,
                    payload=payload,
                )
            ],
        )

    async def search(
        self,
        collection: str,
        vector: list[float],
        limit: int,
        project_id: str | None = None,
    ) -> list[dict[str, Any]]:
        query_filter = None
        if project_id:
            query_filter = models.Filter(
                must=[
                    models.FieldCondition(
                        key="project_id",
                        match=models.MatchValue(value=project_id),
                    )
                ]
            )
        results = await self.client.search(
            collection_name=collection,
            query_vector=vector,
            query_filter=query_filter,
            limit=limit,
            with_payload=True,
        )
        return [
            {
                "id": str(item.id),
                "score": item.score,
                "payload": item.payload or {},
            }
            for item in results
        ]

