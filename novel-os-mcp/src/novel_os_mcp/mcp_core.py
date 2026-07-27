"""Shared MCP instance for all tool modules."""
import os
from fastmcp import FastMCP

# Tool filter: if set, only tools matching these prefixes are exposed
# Set via env NOVEL_OS_MCP_TOOL_WHITELIST (comma-separated prefixes)
_TOOL_WHITELIST = os.environ.get("NOVEL_OS_MCP_TOOL_WHITELIST", "").strip()
_TOOL_FILTER = [p.strip() for p in _TOOL_WHITELIST.split(",") if p.strip()] if _TOOL_WHITELIST else None

mcp = FastMCP(
    "novel-os-mcp",
    mask_error_details=False,
    instructions="""# Novel OS Agent 工作协议

## 核心规则
每个工具返回的 workflow_guide.steps 是唯一指令。按 step_no 依次执行，禁止跳步、禁止合并、禁止自行变通。
流程细节全在工具返回值中，不要根据本文档推理下一步。

## 可用入口
- 创建小说: novel.wizard.start
- 生成章节: workflow.prepare_chapter_context
- 审核章节: review.start_job
- 润色: pipeline.generate(task_type="polish")
- 查看状态: workspace.list / project.list / state.entity.list 等
- 配置: model.profile.* / review.*council* / prompt.template.*
""",
)


def apply_tool_filter():
    """Apply tool whitelist filter after all tools are registered."""
    if not _TOOL_FILTER:
        return
    tools = getattr(mcp._tool_manager, '_tools', mcp._tool_manager.tools) if hasattr(mcp, '_tool_manager') else {}
    for name in list(tools.keys()):
        if not any(name.startswith(prefix) for prefix in _TOOL_FILTER):
            del tools[name]
