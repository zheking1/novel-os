"""Tool authentication & validation helpers — eliminate boilerplate."""
import logging
from typing import Any, Callable
from functools import wraps

from .deps import db, auth

logger = logging.getLogger("novel_os_mcp.tools")


async def get_principal(permission: str = "read"):
    """Connect to DB and return authenticated principal with required permission."""
    await db.connect()
    principal = await auth.current_principal()
    if permission:
        principal.require(permission)
    return principal


def validate_required(data: dict[str, Any], *fields: str):
    """Raise ValueError if any required field is missing or empty."""
    for f in fields:
        v = data.get(f)
        if v is None or (isinstance(v, str) and not v.strip()):
            raise ValueError(f"缺少必填参数: {f}")


def validate_length(data: dict[str, Any], limits: dict[str, int]):
    """Raise ValueError if any field exceeds its max length."""
    for f, max_len in limits.items():
        v = data.get(f)
        if isinstance(v, str) and len(v) > max_len:
            raise ValueError(f"{f} 超过最大长度 {max_len}（当前 {len(v)}）")
