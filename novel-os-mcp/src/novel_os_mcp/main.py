import logging

from .config import get_settings
from .mcp_core import mcp  # noqa: F401

settings = get_settings()
logging.basicConfig(level=settings.log_level)
logger = logging.getLogger("novel_os_mcp")

# Import tool modules to trigger @mcp.tool registration
from . import tools  # noqa: E402, F401

# Import resources to trigger @mcp.resource registration
from . import resources  # noqa: E402, F401


def main() -> None:
    mcp.run(transport="http", host=settings.host, port=settings.port)


if __name__ == "__main__":
    main()
