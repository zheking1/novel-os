"""LLM Client — Unified interface for calling AI models via OpenAI-compatible API.
Reads model configuration from model_profiles table and calls /v1/chat/completions.
"""
import json
import logging
from typing import Any

import httpx

from .utils import json_dumps

logger = logging.getLogger("novel_os_mcp.llm_client")


class LLMClient:
    """Unified LLM client that reads model_profiles and calls OpenAI-compatible API."""

    def __init__(self, db):
        self._db = db
        self._clients: dict[str, httpx.AsyncClient] = {}

    async def _get_config(self, project_id: str, task_type: str) -> dict[str, Any] | None:
        """Find the best model profile for the given task_type. Models are user-level."""
        row = await self._db.fetchrow(
            """
            SELECT profile_key, provider, model_name, default_params, tier
            FROM model_profiles
            WHERE status = 'active'
              AND $1 = ANY(task_types)
            ORDER BY is_default DESC, tier
            LIMIT 1
            """,
            task_type,
        )
        return dict(row) if row else None

    async def _get_client(self, api_url: str) -> httpx.AsyncClient:
        if api_url not in self._clients or self._clients[api_url].is_closed:
            self._clients[api_url] = httpx.AsyncClient(timeout=120.0)
        return self._clients[api_url]

    async def chat(
        self,
        project_id: str,
        task_type: str,
        messages: list[dict[str, str]],
        temperature: float = 0.7,
        max_tokens: int = 4096,
    ) -> dict[str, Any]:
        """Call the AI model for chat completion.

        Args:
            project_id: Project UUID
            task_type: Task type matching model_profiles.task_types (e.g., 'outline', 'draft')
            messages: Chat messages array [{"role": "system"|"user"|"assistant", "content": "..."}]
            temperature: Generation temperature
            max_tokens: Max tokens to generate

        Returns:
            {"text": "...", "model": "...", "usage": {...}, "profile_key": "..."}

        Raises:
            ValueError if no suitable model found
        """
        config = await self._get_config(project_id, task_type)
        if not config:
            raise ValueError(f"No active model profile found for task_type='{task_type}'")

        params = config.get("default_params") or {}
        if isinstance(params, str):
            import json
            params = json.loads(params)

        api_url = params.get("api_url", "")
        api_key = params.get("api_key", "")
        model_name = config["model_name"]

        if not api_url or not api_key:
            raise ValueError(f"API URL or key not configured for profile '{config['profile_key']}'")

        # Only append path if not already a full endpoint URL
        url = api_url.rstrip("/")
        if not url.endswith("/chat/completions"):
            url += "/chat/completions"

        client = await self._get_client(url)
        payload = {
            "model": model_name,
            "messages": messages,
            "temperature": temperature,
            "max_tokens": max_tokens,
        }

        logger.info("LLM call: model=%s, task=%s, api=%s", model_name, task_type, url)
        headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
        }
        response = await client.post(url, json=payload, headers=headers)

        if response.status_code != 200:
            error_body = response.text[:500]
            logger.error("LLM API error %d: %s", response.status_code, error_body)
            raise RuntimeError(f"LLM API returned {response.status_code}: {error_body}")

        data = response.json()
        choices = data.get("choices", [])
        content = choices[0].get("message", {}).get("content", "") if choices else ""
        usage = data.get("usage", {})

        return {
            "text": content,
            "model": model_name,
            "usage": {"prompt_tokens": usage.get("prompt_tokens", 0),
                      "completion_tokens": usage.get("completion_tokens", 0),
                      "total_tokens": usage.get("total_tokens", 0)},
            "profile_key": config["profile_key"],
        }

    async def chat_simple(
        self,
        project_id: str,
        task_type: str,
        system_prompt: str,
        user_prompt: str,
        temperature: float = 0.7,
        max_tokens: int = 4096,
    ) -> dict[str, Any]:
        """Convenience method for single-turn chat with system+user prompts."""
        messages = []
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        messages.append({"role": "user", "content": user_prompt})
        return await self.chat(project_id, task_type, messages, temperature, max_tokens)

    async def chat_with_profile(
        self,
        project_id: str,
        profile_key: str,
        messages: list[dict[str, str]],
        temperature: float = 0.7,
        max_tokens: int = 4096,
    ) -> dict[str, Any]:
        """Call a specific model profile by profile_key (for multi-model audit/debate)."""
        config = await self._db.fetchrow(
            """SELECT profile_key, provider, model_name, default_params
               FROM model_profiles
               WHERE profile_key = $1 AND status = 'active'""",
            profile_key,
        )
        if not config:
            raise ValueError(f"Model profile '{profile_key}' not found or inactive")

        params = config["default_params"]
        if isinstance(params, str):
            params = json.loads(params)
        api_url = params.get("api_url", "")
        api_key = params.get("api_key", "")
        model_name = config["model_name"]

        if not api_url or not api_key:
            raise ValueError(f"API URL or key not configured for profile '{profile_key}'")

        url = api_url.rstrip("/")
        if not url.endswith("/chat/completions"):
            url += "/chat/completions"

        client = await self._get_client(url)
        payload = {
            "model": model_name,
            "messages": messages,
            "temperature": temperature,
            "max_tokens": max_tokens,
        }
        headers = {"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"}
        response = await client.post(url, json=payload, headers=headers)

        if response.status_code != 200:
            error_body = response.text[:500]
            logger.error("LLM API error %d for %s: %s", response.status_code, profile_key, error_body)
            raise RuntimeError(f"LLM API returned {response.status_code}: {error_body}")

        data = response.json()
        choices = data.get("choices", [])
        content = choices[0].get("message", {}).get("content", "") if choices else ""
        usage = data.get("usage", {})
        return {
            "text": content,
            "model": model_name,
            "profile_key": profile_key,
            "usage": {"prompt_tokens": usage.get("prompt_tokens", 0),
                      "completion_tokens": usage.get("completion_tokens", 0),
                      "total_tokens": usage.get("total_tokens", 0)},
        }