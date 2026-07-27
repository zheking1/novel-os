"""MCP Resources — 工作流参考。"""
import logging

from .mcp_core import mcp

logger = logging.getLogger("novel_os_mcp.resources")


@mcp.resource("guide://workflow")
def get_workflow_guide() -> str:
    """Novel OS 工作流参考。完整流程由每个工具返回的 workflow_guide.steps 提供。"""
    return """# Novel OS 工作流

每个工具返回的 workflow_guide.steps 是唯一指令。按 step_no 依次执行，禁止跳步。

## 入口工具
- 创建小说: novel.wizard.start
- 生成章节: workflow.prepare_chapter_context
- 审核章节: review.start_job
- 润色: pipeline.generate(task_type="polish")

## 配置工具
- model.profile.list / model.profile.upsert
- review.list_council_configs / review.upsert_council_config
- prompt.template.list / prompt.template.upsert
- discussion_room.create_session
"""