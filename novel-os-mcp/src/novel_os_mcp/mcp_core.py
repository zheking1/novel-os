"""Shared MCP instance for all tool modules."""
from fastmcp import FastMCP

mcp = FastMCP(
    "novel-os-mcp",
    instructions="""# Novel OS Agent 工作协议

## 铁律
1. 每章写作前必须调 workflow.prepare_chapter_context
2. 每章写完必须调 pipeline.run_full + submit_chapter_commit
3. 禁止跳步、禁止凭空捏造设定

## 首次使用（创建小说）
1. auth.whoami → 确认身份
2. workspace.list + project.list → 检查现有项目
3. novel.wizard.start → 收集用户回答 → novel.wizard.generate → novel.wizard.commit
4. 补充设定: canon.doc.upsert, kb.entity.create, state.entity.upsert

## 每章标准流程（严格按顺序）
1. workflow.preflight_generation → 预检
2. workflow.prepare_chapter_context → 拿上下文包
3. Agent 用上下文包调 LLM 生成章节正文
4. pipeline.run_full → 记录生成结果
5. workflow.validate_content → 内容校验
6. workflow.submit_chapter_commit → 提交

## 写作过程中维护知识
- arc.record_* → 记录角色弧光
- kb.world.update → 更新世界状态
- plot.upsert_foreshadowing → 管理伏笔
- plot.thread.advance → 推进情节线

## 审核（可选）
review.start_job → review.aggregate → review.list_revision_tasks

## 详细参考
调用 resource guide://workflow 获取完整 SOP 文档。

## 认证
auth.whoami | workspace.list | project.list(workspace)
""",
)
