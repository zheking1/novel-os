# 创建小说流程设计文档

**版本**: v1.0
**状态**: 待实现
**关联文档**: `docs/design/chapter-generation-flow.md`

---

## 1. 概述

用户说"创建小说"或"创建项目"时，Agent 严格按工具返回的 `workflow_guide.steps` 逐步执行，从信息收集到世界构建完成。

### 当前问题

| 问题 | 影响 |
|------|------|
| `novel.wizard.build_world` 完成时（phase>5, mode="done"）缺少 `next_tool` 指向章节生成 | Agent 不知道下一步做什么 |
| `novel.wizard.submit_knowledge_proposals` 没有返回 `workflow_guide` | Agent 调用后丢失执行上下文 |

---

## 2. 触发条件

| 用户输入（示例） | 匹配规则 |
|----------------|---------|
| 创建小说 | 进入本流程 |
| 创建项目 | 进入本流程 |
| 创建小说并生成前3章 | 本流程 → 完成后自动衔接生成章节流程 |
| 帮我写一部玄幻小说 | 进入本流程 |

---

## 3. 完整流程图

```
novel.wizard.start
  │ workflow_guide (steps=2)
  │
  ├─ Step 1: _agent_display ── 向用户收集信息 ── wait_user_confirm
  │   收集: 工作区选择、标题、题材、读者、故事核心、
  │         世界观、主角、力量体系、风格基调、预计字数
  │
  └─ Step 2: novel.wizard.generate ── next_step
       │ workflow_guide (steps=2)
       │
       ├─ Step 1: _agent_display ── 展示设定预览 ── wait_user_confirm
       │   展示: 项目档案、设定文档、初始实体、情节线、规则建议
       │
       └─ Step 2: novel.wizard.commit ── next_step
            │ workflow_guide (steps=1)
            │
            └─ Step 1: novel.wizard.build_world ── next_step
                 │ workflow_guide (phases=5, 自循环)
                 │
                 ├─ Phase 1: 卷纲结构
                 ├─ Phase 2: 知识库搭建
                 ├─ Phase 3: 逐卷深挖
                 ├─ Phase 4: 跨卷全局检查
                 └─ Phase 5: 逐章大纲
                      │
                      ▼
                  mode="done"  ← 【修改点1】加 next_tool
                      │
                      ▼
              workflow.prepare_chapter_context
              （如果需要生成章节）
```

---

## 4. 需要修改的 MCP 工具

### 修改点 1: `novel.wizard.build_world` — 完成态加跳转

**文件**: `novel-os-mcp/src/novel_os_mcp/tools/novel_wizard.py`
**位置**: build_world 函数末尾，phase > 5 的返回

**当前代码**（约 line 1950）:
```python
return {
    "phase": phase,
    "phases": phases,
    "message": "所有阶段已完成，世界构建结束。可进入章节生成。",
    "workflow_guide": {
        "mode": "done",
        ...
    },
}
```

**改为**:
```python
return {
    "phase": phase,
    "phases": phases,
    "message": "所有阶段已完成，世界构建结束。可进入章节生成。",
    "workflow_guide": {
        "mode": "done",
        "next_tool": "workflow.prepare_chapter_context",
        "description": "世界构建完成，可调用 workflow.prepare_chapter_context 开始生成章节",
        ...
    },
}
```

### 修改点 2: `novel.wizard.submit_knowledge_proposals` — 加 workflow_guide

**文件**: 同上
**位置**: submit_knowledge_proposals 函数末尾

**当前**: 只返回 `{"ok": True, ...}`，没有 `workflow_guide`

**改为**: 加 `workflow_guide`，指向 `novel.wizard.build_world` 继续构建
```python
"workflow_guide": {
    "mode": "strict",
    "phase": "知识提案已提交",
    "steps": [{
        "step_no": 1,
        "name": "继续世界构建",
        "tool": "novel.wizard.build_world",
        "params": {"workspace": workspace, "project": project},
        "next": "next_step",
    }],
}
```

---

## 5. 异常处理

| 场景 | 处理 |
|------|------|
| `novel.wizard.generate` 失败 | 报告用户，不静默跳过，询问是否重试 |
| `novel.wizard.commit` 失败（如项目 slug 重复） | 报告具体错误，让用户修正后重试 |
| `build_world` 某阶段失败 | 报告当前阶段和错误，询问是否跳过或重试 |
| 讨论室超时（Phase 3 审核门） | 报告超时，展示已有结果，询问是否跳过审核 |

---

## 6. 衔接生成章节流程

- 当用户在创建小说时包含章节生成指令（如"创建小说并生成前3章"），Agent 在 `build_world` 完成后自动调用 `workflow.prepare_chapter_context`
- 否则，`build_world` 完成后提示用户"可以开始生成章节了"