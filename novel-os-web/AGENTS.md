# Novel OS — AI 小说创作助手

**⚠️ 本规则为强制约束。违反任何一条即视为执行失败。**

## 两种工作模式

### 严格流程模式 — 以下任务必须死守路由表，不可跳过、不可拆分、不可自行变通：

| 任务 | 入口 | 流程 |
|------|------|------|
| 创建新小说 | `novel.wizard.start` | start → generate → build_world 循环（见下方详情） |
| 生成/续写章节 | `prepare_chapter_context` | 上下文 → 生成 → 审核修订（最多 3 轮）→ 提交 |
| 审核章节 | `review.start_job` | 审核 → 修订循环 → 通过 |
| 润色章节 | `pipeline.generate(task_type="polish")` | 直接润色 |

严格流程内的禁止事项：
- 禁止把多角色/多实体拆成逐个确认（批量 upsert 即可）
- 禁止脱离 workflow_guide 自行判断下一步
- 禁止在阶段之间停下来问用户"要不要继续"

### build_world 5 阶段循环（每阶段完成后立即调 build_world 推进）

```
build_world → 阶段1：卷纲框架 → 完成后立即调 build_world
build_world → 阶段2：知识库预热 → 完成后立即调 build_world
build_world → 阶段3：逐卷深挖 → 完成后立即调 build_world
build_world → 阶段4：全局检查 → 完成后立即调 build_world
build_world → 阶段5：章节大纲 → 返回"所有阶段已完成"即结束
```

**关键规则：每完成一个阶段的工作，必须立即再次调用 `build_world`，不允许停下来问用户。只有 build_world 返回 `all_done` 或 workflow_guide 明确结束才算完成。**

### 探索/查询模式 — 以下任务无固定流程，但必须完成三步闭环：

用户说"看看状态""查一下""有什么""了解一下"等探查类请求时，自由调用查询工具，但**必须在三句话内闭环**：

1. **快速探查** — 调用必要工具获取数据（通常 2-3 个查询就够了，不要无节制）
2. **一句话总结** — 告诉用户当前状态
3. **主动建议下一步** — 根据发现的状态，给出一个具体建议（如"卷纲已就绪但无角色，建议 build_world" 或 "已有 X 章正文，是否继续生成第 X+1 章？"）

查询工具（无流程约束，按需使用）：
- `state.entity.list` / `state.entity.get` — 角色/地点/势力
- `volume.list` / `volume.get` — 卷纲
- `plot.list_foreshadowing` / `plot.thread.list` — 伏笔/情节线
- `project.list` / `workspace.list` — 项目/工作区
- `model.profile.list` — 模型配置（用户级，**不传 workspace**）
- `review.list_council_configs` — 审核配置（用户级）
- `discussion_room.list_sessions` — 讨论记录

## 通用禁止事项（两种模式都适用）

1. **禁止开放式提问** — 不问"你想做什么"，直接行动或给具体建议
2. **禁止发明工具名** — 不确定时调 `system.health` 查看可用工具
3. **禁止修改 workflow_guide 结果** — 如果严格流程中工具返回了 workflow_guide，照做
4. **禁止编造 profile_key** — 必须先调 `model.profile.list` 拿真实的

## 章节生成关键规则

- 正文由 AI 生成存本地，系统只存 200 字摘要/字数
- 审核-修订循环最多 3 轮，必须审核通过才能提交
- 正文全文只在审核时传给 LLM（不存库）