"""MCP Resources - 标准工作流 SOP + 详细参考文档。"""
import logging

from .mcp_core import mcp

logger = logging.getLogger("novel_os_mcp.resources")


@mcp.resource("guide://workflow")
def get_workflow_guide() -> str:
    """Novel OS 完整工作流 SOP。任何 agent 换对话都能跟此文档执行。"""
    return r"""# Novel OS 标准工作流 SOP

> **原则**: 每次写作前必须先查上下文，写完后必须提交。禁止跳步。

---

## 阶段一：初始化（仅首次）

### 1.1 确认身份
```
auth.whoami
```
- 如果未登录 → 告诉用户需要先在 Web UI 登录
- 如果已登录 → 记住 username, workspace

### 1.2 检查现有项目
```
workspace.list
project.list(workspace=...)
```
- 有项目 → 跳到阶段二
- 无项目 → 继续 1.3

### 1.3 创建小说（对话式向导）
```
Step 1: novel.wizard.start
  → 返回 wizard_id + 问题列表

Step 2: 逐个询问用户问题，收集 answers 字典

Step 3: novel.wizard.generate(wizard_id, answers)
  → 返回 preview（设定预览）

Step 4: 展示 preview 给用户确认

Step 5: novel.wizard.commit(
  wizard_id,
  workspace="已有的workspace slug",
  project_slug="简短英文标识",
  preview=preview,
  workspace_action="existing"  // 或 "new" + workspace_name
)
  → 返回 project_id
```

### 1.4 完善设定（可选但推荐）
```
canon.doc.upsert(workspace, project, doc_type="worldview", key="main", ...)
canon.doc.upsert(workspace, project, doc_type="power_system", key="main", ...)
canon.doc.upsert(workspace, project, doc_type="character", key="protagonist", ...)
```

### 1.5 创建知识实体
```
kb.entity.create(entity_type="character", name="主角名", content="...", summary="...")
kb.entity.create(entity_type="location", name="地点", content="...")
kb.relation.create(from_entity_id, to_entity_id, relation_type="related_to")
```

---

## 阶段二：每章标准流程

> **严格按顺序执行，不可跳步。**

### 2.1 预检
```
workflow.preflight_generation(workspace, project, chapter_no)
```
返回: 上下文完整性、模型可用性、预算检查
- 如果有 blocking issue → 先修复再继续

### 2.2 准备上下文
```
workflow.prepare_chapter_context(
  workspace, project, chapter_no,
  purpose="draft",        // draft/polish/verify
  pass_number=2,          // 1=outline 2=draft 3=polish 4=verify
  focus=["plot", "character"],  // 可选：聚焦领域
  volume_no=1             // 可选：卷号
)
```
返回: context_pack（包含 16 个 section 的压缩上下文）

### 2.3 生成章节
**Agent 自行调用 LLM 生成**，使用 context_pack 作为上下文：
```
输入: context_pack + 用户指令
输出: 章节正文 (markdown)
```

### 2.4 记录生成结果
```
pipeline.run_full(
  project_id,
  chapter_no,
  plan={...},              // 大纲计划
  draft_content="...",     // 初稿内容
  polished_content="..."   // 润色后内容（可选）
)
```

### 2.5 内容校验
```
workflow.validate_content(workspace, project, chapter_no, content)
```
返回: 违规项、角色存活检查、设定一致性
- 如果有 critical issue → 修复后重新校验

### 2.6 提交章节
```
workflow.submit_chapter_commit(
  workspace, project, chapter_no,
  title="章节标题",
  local_files=[{"path": "ch001.md", "content": "..."}],
  commit={"message": "完成第1章", "author": "agent"}
)
```

---

## 阶段三：知识维护（写作过程中）

### 3.1 记录角色变化（每章写完后）
```
arc.record_emotion(project_id, character, chapter_no, emotion, intensity)
arc.record_personality(project_id, character, chapter_no, trait, old, new)
arc.record_power(project_id, character, chapter_no, old_level, new_level)
arc.record_relationship(project_id, character, chapter_no, target, old_rel, new_rel)
```

### 3.2 更新世界状态
```
kb.world.update(project_id, chapter_no, world_state={...})
```

### 3.3 管理伏笔
```
plot.upsert_foreshadowing(workspace, project, key, title, layer="visible")
plot.foreshadowing.payoff(workspace, project, key, payoff_chapter_no=...)
```

### 3.4 管理情节线
```
plot.thread.upsert(workspace, project, key, title, thread_type="main")
plot.thread.advance(workspace, project, key, chapter_no, progress_note="...")
```

---

## 阶段四：审核（可选但推荐）

### 4.1 启动多模型审核
```
review.start_job(
  workspace, project, chapter_no,
  local_files=[...],
  dimensions=["continuity", "style", "plot", "character"]
)
```

### 4.2 获取审核结果
```
review.aggregate(workspace, project, review_job_id)
```

### 4.3 修复问题
```
review.list_revision_tasks(workspace, project, status="open")
review.update_revision_task(workspace, project, task_id, status="completed")
```

---

## 常用查询

| 用途 | 工具 |
|------|------|
| 查看章节列表 | local.chapter.list(project_id) |
| 读取章节内容 | local.chapter.read(project_id, chapter_no) |
| 搜索知识 | kb.entity.search(query) |
| 全文搜索 | search.fulltext(workspace, project, query) |
| 查看专有名词 | noun.list(workspace, project) |
| 检查名词一致性 | noun.check(workspace, project, text) |
| 查看伏笔 | plot.list_foreshadowing(workspace, project) |
| 查看情节线 | plot.thread.list(workspace, project) |
| 查看角色弧光 | arc.get_character(project_id, character_name) |
| 查看因果链 | causality.get_summary(project_id, chapter_no) |
| 查看节奏曲线 | pacing.get_curve(project_id) |
| 查看文风 | style.get_profile(project_id) |

---

## 关键参数说明

### pass_number 含义
- 1 = 大纲阶段（dry，不写正文）
- 2 = 初稿阶段（wet，写正文）
- 3 = 润色阶段（refine，优化文风）
- 4 = 验证阶段（check，检查一致性）

### purpose 含义
- draft = 写初稿
- polish = 润色
- verify = 验证

### doc_type 含义
- premise = 核心梗概
- worldview = 世界观
- power_system = 力量体系
- character = 角色设定
- timeline = 时间线
- plot_outline = 剧情大纲

### entity_type 含义
- character = 角色
- location = 地点
- faction = 势力
- concept = 概念
- item = 物品

### relation_type 含义
- participated_in = 参与
- located_at = 位于
- belongs_to = 属于
- related_to = 相关
- caused_by = 导致
- same_as = 等同
- influenced_by = 受影响

### thread_type 含义
- main = 主线
- side = 支线

###伏笔 layer 含义
- visible = 明线（读者可见）
- hidden = 暗线（读者隐约感知）
- deep = 暗线（完全隐藏）
"""
