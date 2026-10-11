# 生成章节流程设计文档

**版本**: v1.0
**状态**: 待实现
**关联文档**: `docs/design/novel-creation-flow.md`

---

## 1. 概述

用户说"生成章节"/"生成第X章"/"生成N章"时，Agent 严格按 `workflow.prepare_chapter_context` 返回的 14 步流程执行，支持多章连续生成。

### 当前问题

| 问题 | 严重度 | 影响 |
|------|--------|------|
| 14 步结束后没有"生成下一章"的 step | 致命 | 用户说"生成3章"只生成1章就停了 |
| `review.aggregate` 的 `next_tool` 直接指到 `workflow.submit_chapter_commit`，跳过润色 | 高 | 不走 `prepare_chapter_context` 时、审核后直接提交未润色的文本 |
| `pipeline.generate` 的 `next_actions` 把 `review.start_job` 排在 `submit` 后面 | 中 | 不走 `prepare_chapter_context` 时、审核顺序错误 |

---

## 2. 触发条件

| 用户输入 | 解析结果 | 行为 |
|---------|---------|------|
| 生成章节 | 查最小待生成章节号 → `chapter_no` | 生成 1 章 |
| 生成第5章 | `chapter_no=5, count=1` | 生成第 5 章 |
| 生成3章 | 查最小 → `chapter_no`, `count=3` | 连续生成 3 章 |
| 生成第5到第10章 | `chapter_no=5, end_chapter=10` | 连续生成 5-10 章 |
| 创建第8章 | 同"生成第8章" | 同上 |

**确定最小待生成章节号的逻辑**：
1. 查询 `chapters` 表，找最大已完成章节号 → `max_completed`
2. `chapter_no = max_completed + 1`（如果有已完成章节）
3. 如果无任何章节 → `chapter_no = 1`
4. 如果 `max_completed` 为 NULL → `chapter_no = 1`

---

## 3. 完整流程（单章 14+1 步）

```
workflow.prepare_chapter_context(chapter_no=N)
  │
  ├─ Step 1:  预检                        workflow.preflight_generation    → next_step
  ├─ Step 2:  获取上下文包                  _agent_evaluate                  → next_step
  ├─ Step 3:  生成初稿并记录                _agent_evaluate                  → next_step
  ├─ Step 4:  内容校验                      workflow.validate_content        → next_step
  ├─ Step 5:  启动审核                      review.start_job                 → next_step
  ├─ Step 6:  等待审核完成                  discussion_room.get_updates       → wait_for_async
  ├─ Step 7:  获取审核结论                  discussion_room.get_session      → next_step
  ├─ Step 8:  审核结论判定                  _agent_evaluate                  → goto_step:7 (fail)
  ├─ Step 9:  润色终稿                      pipeline.generate(polish)        → next_step
  ├─ Step 10: 保存终稿到本地                _agent_evaluate                  → next_step
  ├─ Step 11: 提交章节                      workflow.submit_chapter_commit   → next_step
  ├─ Step 12: 记录情绪节奏                  pacing.record_emotion            → next_step
  ├─ Step 13: 记录角色弧光                  arc.record_*                     → next_step
  ├─ Step 14: 维护情节线/伏笔               plot.thread.advance + foreshadowing.* → wait_user_confirm
  │
  └─ Step 15: 判断是否继续                  _agent_evaluate                  → 【新增】
       │
       ├─ 还有下一章 → chapter_no += 1, 回到 Step 1
       └─ 已完成全部 → 结束
```

### 步 8 判定规则（审核结论）

```
审核结论包含"通过"且无严重问题 → 进入步 9（润色）
审核结论包含"不完备"/"需修订"/"存在问题" → 回到步 7 修订正文、重新审核
已循环 3 轮仍不通过 → 暂停、报告用户、不静默跳过
```

### 步 15 判定规则（继续还是停止）【新增】

```
剩余章节数 > 0 → chapter_no += 1, 调用 workflow.prepare_chapter_context(chapter_no=新章节号)
剩余章节数 == 0 → 输出完成摘要，流程结束
```

**Agent 需跟踪的上下文**：
- `start_chapter_no`: 起始章节号
- `end_chapter_no`: 目标结束章节号（可为 None 表示只生成 1 章）
- `remaining_count`: 剩余待生成章数

---

## 4. 多章生成循环

```
用户: 生成 3 章
  │
  ├─ 计算 chapter_no = 最小待生成章节号（假设 5）
  ├─ remaining_count = 3
  │
  ├─ 生成 chapter 5  [14+1步] ✓
  │   remaining_count = 2
  ├─ 生成 chapter 6  [14+1步] ✓
  │   remaining_count = 1
  └─ 生成 chapter 7  [14+1步] ✓
      remaining_count = 0 → 完成
```

---

## 5. 需要修改的 MCP 工具

### 修改点 1: `workflow.prepare_chapter_context` — 加 Step 15

**文件**: `novel-os-mcp/src/novel_os_mcp/tools/context.py`
**位置**: `prepare_chapter_context` 函数，workflow_guide.steps 末尾

**当前**: 14 步，最后一步 `wait_user_confirm`

**新增 Step 15**:
```python
{
    "step_no": 15,
    "name": "判断是否继续生成下一章",
    "tool": "_agent_evaluate",
    "params": {
        "instruction": (
            "检查当前上下文中的 remaining_count 或 end_chapter_no。"
            "如果还有剩余章节待生成：chapter_no += 1，"
            "调用 workflow.prepare_chapter_context(chapter_no=新章节号) 启动下一章。"
            "如果已全部完成：输出完成摘要（总章数、总字数、审核通过率），流程结束。"
        ),
    },
    "next": "next_step",
    "note": "多章自动连续生成的关键步骤",
}
```

### 修改点 2: `review.aggregate` — 修正 next_tool

**文件**: `novel-os-mcp/src/novel_os_mcp/tools/review.py`
**位置**: `review_aggregate` 函数，workflow_guide 返回值

**当前**: `next_tool: "workflow.submit_chapter_commit"` — 跳过了润色/保存/节奏/弧光/情节线

**改为**: `next_tool: "pipeline.generate"`，加 `next_tool_params: {"task_type": "polish"}`
```python
"next_tool": "pipeline.generate",
"next_tool_params": {"task_type": "polish"},
"description": "审核通过，进入润色阶段。审核不通过需修订后重新审核。",
```

> **注意**: 此修改仅影响 Agent 不走 `prepare_chapter_context` 完整流程（单独调 `review.aggregate`）时的行为。走 14 步流程时，步 8→步 9 由 workflow_guide 控制，不受 `review.aggregate` 的 `next_tool` 影响。

### 修改点 3: `pipeline.generate` — 修正 next_actions 顺序

**文件**: `novel-os-mcp/src/novel_os_mcp/tools/novel_gen.py`
**位置**: `pipeline_generate` 函数，workflow_guide.next_actions

**当前**: `review.start_job` 排在 `workflow.submit_chapter_commit` 之后

**改为**: 调整顺序，审核在前、提交在后
```python
"next_actions": [
    "outline → draft → polish 顺序推进",
    "当 review 完成后，调用 workflow.submit_chapter_commit 提交章节",
    "然后调用 kb.world.auto_update 更新世界状态",
    "然后调用 arc.record_* 记录角色弧光",
    "然后调用 plot.thread.advance 推进剧情线",
    "然后调用 foreshadowing.payoff 回收到期伏笔",
],
```

> **注意**: 此修改仅影响 Agent 不走 `prepare_chapter_context` 完整流程时的行为。

---

## 6. 异常处理

| 场景 | 处理 |
|------|------|
| 步 4 校验不通过（禁词/死角色） | Agent 修订正文后重新校验，最多 3 次。超过 3 次暂停报告 |
| 步 6 讨论室超时（240 次轮询/20分钟） | 报告超时、展示已有结果、询问是否跳过审核 |
| 步 8 审核 3 轮不通过 | 暂停、输出审核报告摘要、等待用户决策 |
| 步 11 提交失败（无 chapter 记录） | 自动创建 chapter 记录后重试 |
| 多章循环中某章失败 | 暂停、报告当前进度和错误、不静默跳过 |

---

## 7. 与创建小说流程的衔接

```
创建小说流程 → build_world done
  │
  ├─ 用户单独说"创建小说" → 提示"可以开始生成章节了"，等待用户指令
  │
  └─ 用户说"创建小说并生成前3章" → 自动进入本流程，start_chapter_no=1, count=3
```