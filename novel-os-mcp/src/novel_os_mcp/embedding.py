"""
Embedding & Rerank Service

Reads model config from model_profiles (database), not env vars.
Supports OpenAI-compatible API format.
"""

import logging
from typing import Any

import httpx

from .db import Database
from .utils import row_to_dict

logger = logging.getLogger("novel_os_mcp.embedding")


class EmbeddingService:
    """Calls OpenAI-compatible embedding API. Config from model_profiles."""

    def __init__(self, db: Database):
        self._db = db
        self._clients: dict[str, httpx.AsyncClient] = {}

    async def _get_config(self, project_id: str) -> dict[str, Any] | None:
        """Get embedding model config from model_profiles for a project."""
        row = await self._db.fetchrow(
            """
            SELECT id::text, provider, model_name, default_params, metadata
            FROM model_profiles
            WHERE project_id = $1
              AND status = 'active'
              AND 'embedding' = ANY(task_types)
            ORDER BY is_default DESC, tier
            LIMIT 1
            """,
            project_id,
        )
        return row_to_dict(row) if row else None

    async def _get_client(self, provider: str, api_url: str) -> httpx.AsyncClient:
        key = f"{provider}:{api_url}"
        if key not in self._clients or self._clients[key].is_closed:
            self._clients[key] = httpx.AsyncClient(timeout=30.0)
        return self._clients[key]

    async def embed(
        self,
        project_id: str,
        texts: list[str],
    ) -> list[list[float]]:
        """Get embeddings for texts using project's configured embedding model."""
        config = await self._get_config(project_id)
        if not config:
            return []

        if not texts:
            return []

        # Parse default_params (asyncpg may return jsonb as string)
        params = config.get("default_params") or {}
        if isinstance(params, str):
            import json
            params = json.loads(params)

        api_url = params.get("api_url", "")
        api_key = params.get("api_key", "")
        dimensions = params.get("dimensions", 1024)

        if not api_url or not api_key:
            return []

        provider = config["provider"]
        client = await self._get_client(provider, api_url)
        url = f"{api_url.rstrip('/')}/v1/embeddings"
        headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
        }

        # SiliconFlow uses {text: "..."} format for input
        if provider == "siliconflow":
            # Call once per text, then combine results
            all_embeddings = []
            for text in texts:
                payload = {
                    "model": config["model_name"],
                    "input": text,
                }
                try:
                    resp = await client.post(url, json=payload, headers=headers)
                    resp.raise_for_status()
                    data = resp.json()
                    raw = data["data"]
                    if isinstance(raw, list) and len(raw) > 0:
                        all_embeddings.append(raw[0]["embedding"])
                    else:
                        all_embeddings.append([])
                except Exception as e:
                    logger.error(f"Embedding API error ({provider}): {e}")
                    all_embeddings.append([])
            return all_embeddings

        # Standard OpenAI-compatible format
        payload = {
            "model": config["model_name"],
            "input": texts,
        }
        if dimensions:
            payload["dimensions"] = dimensions

        try:
            resp = await client.post(url, json=payload, headers=headers)
            resp.raise_for_status()
            data = resp.json()
            raw = data["data"]
            raw.sort(key=lambda x: x["index"])
            return [item["embedding"] for item in raw]
        except Exception as e:
            logger.error(f"Embedding API error ({config['provider']}): {e}")
            return []

    async def embed_single(self, project_id: str, text: str) -> list[float]:
        results = await self.embed(project_id, [text])
        return results[0] if results else []

    async def close(self):
        for client in self._clients.values():
            if not client.is_closed:
                await client.aclose()


class RerankService:
    """Calls OpenAI-compatible rerank API. Config from model_profiles."""

    def __init__(self, db: Database):
        self._db = db
        self._clients: dict[str, httpx.AsyncClient] = {}

    async def _get_config(self, project_id: str) -> dict[str, Any] | None:
        row = await self._db.fetchrow(
            """
            SELECT id::text, provider, model_name, default_params, metadata
            FROM model_profiles
            WHERE project_id = $1
              AND status = 'active'
              AND 'rerank' = ANY(task_types)
            ORDER BY is_default DESC, tier
            LIMIT 1
            """,
            project_id,
        )
        return row_to_dict(row) if row else None

    async def _get_client(self, provider: str, api_url: str) -> httpx.AsyncClient:
        key = f"{provider}:{api_url}"
        if key not in self._clients or self._clients[key].is_closed:
            self._clients[key] = httpx.AsyncClient(timeout=30.0)
        return self._clients[key]

    async def rerank(
        self,
        project_id: str,
        query: str,
        documents: list[str],
        top_n: int = 5,
    ) -> list[dict[str, Any]]:
        """Rerank documents. Falls back to no-op if no rerank model configured."""
        config = await self._get_config(project_id)
        if not config or not documents:
            return [{"index": i, "score": 1.0, "text": doc} for i, doc in enumerate(documents[:top_n])]

        params = config.get("default_params") or {}
        if isinstance(params, str):
            import json
            params = json.loads(params)
        api_url = params.get("api_url", "")
        api_key = params.get("api_key", "")

        if not api_url or not api_key:
            return [{"index": i, "score": 1.0, "text": doc} for i, doc in enumerate(documents[:top_n])]

        client = await self._get_client(config["provider"], api_url)
        url = f"{api_url.rstrip('/')}/v1/rerank"
        headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
        }
        payload = {
            "model": config["model_name"],
            "query": query,
            "documents": documents,
            "top_n": top_n,
        }

        try:
            resp = await client.post(url, json=payload, headers=headers)
            resp.raise_for_status()
            data = resp.json()
            results = []
            for item in data.get("results", []):
                idx = item.get("index", 0)
                results.append({
                    "index": idx,
                    "score": item.get("relevance_score", 0),
                    "text": documents[idx] if idx < len(documents) else "",
                })
            return results
        except Exception as e:
            logger.error(f"Rerank API error ({config['provider']}): {e}")
            return [{"index": i, "score": 1.0, "text": doc} for i, doc in enumerate(documents[:top_n])]

    async def close(self):
        for client in self._clients.values():
            if not client.is_closed:
                await client.aclose()
