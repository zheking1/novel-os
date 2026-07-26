import logging

from .config import get_settings
from .mcp_core import mcp  # noqa: F401

settings = get_settings()
logging.basicConfig(level=settings.log_level)
logger = logging.getLogger("novel_os_mcp")

# Use Redis for MCP session persistence (survives container restarts)
try:
    from key_value.aio.stores.redis.store import RedisStore
    from key_value.aio.adapters.pydantic.adapter import PydanticAdapter
    from fastmcp.server.server import StateValue
    redis_store = RedisStore(
        host=settings.redis_host, port=settings.redis_port, db=1,
        password=settings.redis_password,
    )
    mcp._state_storage = redis_store
    mcp._state_store = PydanticAdapter[StateValue](
        key_value=redis_store,
        pydantic_model=StateValue,
        default_collection="fastmcp_state",
    )
    logger.info("MCP session store: Redis (db=1) at %s:%s", settings.redis_host, settings.redis_port)
except Exception as e:
    logger.warning("Redis session store unavailable, using default memory store: %s", e)

# Monkey-patch FastMCP SSE sessions to survive container restarts via Redis
try:
    import redis.asyncio as aioredis
    from mcp.server.streamable_http_manager import StreamableHTTPSessionManager
    
    redis_sessions = aioredis.Redis(
        host=settings.redis_host, port=settings.redis_port, db=2,
        password=settings.redis_password,
        decode_responses=False,
    )
    
    _orig_create = StreamableHTTPSessionManager.create_transport
    
    async def _redis_create_transport(self, request):
        transport = await _orig_create(self, request)
        sid = getattr(transport, 'session_id', None)
        if sid:
            try:
                await redis_sessions.setex(f"mcp_sess:{sid}", 86400, b"1")
            except Exception: pass
        return transport
    
    _orig_handle_request = StreamableHTTPSessionManager.handle_request
    
    async def _redis_handle_request(self, request):
        # Check if session_id exists in Redis but transport was lost (restart)
        headers = getattr(request, 'headers', {}) or {}
        sid = headers.get('mcp-session-id') or headers.get('Mcp-Session-Id') or ''
        if sid and not sid.startswith('new_'):
            try:
                if not await _orig_get_inner(self, sid):
                    if await redis_sessions.exists(f"mcp_sess:{sid}"):
                        # Session valid in Redis, transport lost. Force re-init.
                        return self._create_session_response(sid)
            except Exception: pass
        return await _orig_handle_request(self, request)
    
    # Helper: try to get transport from memory (original behavior)
    async def _orig_get_inner(self, sid):
        try:
            return self._sessions.get(sid)
        except Exception:
            return None
    
    async def _create_session_response(self, sid):
        """Return a JSON-RPC error telling client to re-initialize."""
        try:
            import json
            from starlette.responses import JSONResponse
            return JSONResponse({
                "jsonrpc": "2.0",
                "error": {
                    "code": -32001,
                    "message": "Session lost after server restart. Please call initialize() again."
                }
            }, status_code=400)
        except Exception:
            return None
    
    StreamableHTTPSessionManager.create_transport = _redis_create_transport
    StreamableHTTPSessionManager.handle_request = _redis_handle_request
    logger.info("SSE session persistence: Redis (db=2) enabled — sessions survive restarts")
except Exception as e:
    logger.warning("SSE session persistence unavailable: %s", e)

# Import tool modules to trigger @mcp.tool registration
from . import tools  # noqa: E402, F401

# Apply tool whitelist filter
from .mcp_core import apply_tool_filter
apply_tool_filter()

# Import resources to trigger @mcp.resource registration
from . import resources  # noqa: E402, F401


def main() -> None:
    mcp.run(transport="http", host=settings.host, port=settings.port)


if __name__ == "__main__":
    main()
