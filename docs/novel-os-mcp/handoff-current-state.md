# Novel OS MCP 当前开发状态

更新时间：2026-06-27

## 当前指针

```text
NEXT: Phase 3.3 实体面板
DOING: Phase 3.2 规则面板（已完成部署）
DONE: Phase 3.1 Canon 文档 + 项目选择器
```

当前主线是 Phase 3 Web 数据维护台升级。Phase 2 已全部完成。

## 阶段状态

| 阶段 | 名称 | 状态 | 当前说明 |
| --- | --- | --- | --- |
| Phase 0 | 基础部署与需求基线 | DONE | NAS compose、PostgreSQL、Qdrant、MCP、Web 登录、需求文档完成 |
| Phase 1 | P0 数据模型与迁移 | DONE | Canon 文档、版本、实体关系、状态时效、伏笔关联、规则作用域已完成 |
| Phase 2 | P0 MCP 核心工具 | DONE | 2.1-2.10 全部完成并通过 NAS 冒烟测试 |
| Phase 3 | Web 数据维护台 | DOING | 3.1 ✅ 项目选择器+Canon；3.2 ✅ 规则面板；3.3-3.8 待实现 |
| Phase 4 | 本地 AI Skill 对接 | TODO | skill 初版存在，但尚未深度串联全部 MCP 工具 |
| Phase 5 | 审查闭环与规则演化 | TODO | 已有审查学习基础，完整多模型调度和人工审批 UI 未完成 |
| Phase 6 | 性能、容灾与运维 | TODO | 有备份/健康检查脚本，缓存、限流、降级还未系统化 |
| Phase 7 | P1 创作效率增强 | TODO | Prompt 模板、商业看板、批量细纲、协作批注等未做 |
| Phase 8 | P2 远期扩展 | DEFERRED | 分布式、离线完整模式、模板市场、图谱等后置 |

## 已完成 MCP 能力

### 多用户与项目隔离

已实现：

- `user.create`
- `user.list`
- `workspace.create`
- `workspace.list`
- `workspace.add_member`
- `project.create`
- `project.list`
- `project.add_member`
- `project.list_members`
- `auth.create_api_token`
- `auth.list_api_tokens`
- `auth.revoke_api_token`

项目隔离基于 `workspace + project` 解析到 `project_id`。工具层必须继续保持这个模式。

### Canon 文档

已实现：

- `canon.doc.upsert`
- `canon.doc.list`
- `canon.doc.get`
- `canon.doc.archive`
- `canon.doc.history`
- `canon.doc.restore`

用途：保存硬设定、世界观、力量体系、题材模板、规则说明等可版本化结构化文档。不是保存正文。

### 规则系统

已实现：

- `rules.list`
- `rules.upsert`
- `rules.propose`
- `rules.list_proposals`
- `rules.apply_proposal`
- `rules.list_effective`
- `rules.check_conflict`
- `rules.bulk_toggle`
- `rules.resolve_conflict`

已支持：

- rule type
- scope type/ref/config
- priority
- temporary rule
- chapter/volume lifecycle
- active/expire event
- supersede/block
- proposal approval

### 合规审查

已实现：

- `compliance.rule.upsert`
- `compliance.rule.list`
- `compliance.check`

合规规则底层复用 `canon_rules`，`rule_type=compliance`。`compliance.check` 接收调用方传入的片段，不主动读取本地正文全文。critical/blocking 命中可阻断生成、创建 blocking 修订任务，并写入审计日志。

### 模型与成本

已实现：

- `model.profile.upsert`
- `model.profile.list`
- `model.route`
- `model.route_rule.upsert`
- `model.route_rule.list`
- `cost.record_usage`
- `cost.report`

模型与成本工具为每个项目提供可配置的模型档案（不保存 API key），支持 cheap/standard/premium/local 分层，支持按任务类型路由和 fallback 降级。成本记录支持按日/任务类型/模型/Profile/服务商/层级多维度统计。

### 实体、状态、关系

已实现：

- `state.entity.upsert`
- `state.entity.list`
- `state.entity.get`
- `state.entity.bulk_patch`
- `state.snapshot.upsert`
- `state.snapshot.list`
- `state.relationship.upsert`
- `state.relationship.list`

支持人物、势力、地点、道具及项目自定义实体。状态快照支持时效字段，生成上下文时可过滤过期状态。

### 剧情线、卷、章节计划

已实现：

- `volume.upsert`
- `volume.list`
- `plot.thread.upsert`
- `plot.thread.list`
- `plot.thread.advance`
- `plot.thread.check_stalled`
- `plot.create_chapter_plan`
- `plot.list_chapter_plans`

### 伏笔系统

已实现：

- `plot.upsert_foreshadowing`
- `plot.list_foreshadowing`
- `foreshadowing.bulk_status_update`
- `foreshadowing.check_overdue`
- `foreshadowing.link`
- `foreshadowing.payoff`

已支持：

- parent/child 关联
- related keys
- visible/hidden/backstage layer
- payoff deadline
- overdue 检查
- payoff 联动

### 记忆与向量

已实现：

- `memory.search`
- `memory.get_state`
- `memory.get_recent_summaries`
- `memory.rebuild_projection`
- `memory.pending_vector_chunks`
- `memory.upsert_vector`
- `memory.vector_search`

注意：embedding 生成应在本地/外部完成，MCP 保存向量索引和检索结果，不负责调用用户大模型 API。

### 上下文包

已实现：

- `workflow.prepare_chapter_context`
- `workflow.validate_context_pack`
- `workflow.preflight_generation`
- `workflow.prepare_segment_context`

已支持：

- token budget
- section 分配
- effective rules
- POV 伏笔过滤
- 状态生命周期过滤
- 即将过期状态提示
- 章节/分段上下文
- 生成前预检

### 本地同步

已实现：

- `sync.import_local_manifest`
- `sync.import_initial_project_pack`
- `sync.submit_file_hashes`
- `sync.list_conflicts`
- `sync.resolve_conflict`
- `sync.export_project_pack`

同步原则：

- 本地文件保留正文、大纲、细纲、草稿、审查文档。
- MCP 保存 path hint、hash、word count、结构化设定、状态、规则、伏笔等。
- 文件冲突必须显式处理，不能静默覆盖。

### 审查学习

已实现：

- `review.start_job`
- `review.submit_model_report`
- `review.aggregate`
- `review.extract_rule_proposals`
- `review.extract_state_updates`
- `review.extract_foreshadowing_updates`
- `review.evaluate_model_quality`
- `workflow.learn_from_review`
- `review.list_revision_tasks`
- `review.update_revision_task`
- `review.upsert_council_config`
- `review.list_council_configs`

已支持：

- 多模型报告提交
- consensus 聚合
- blocking/high/medium 修订任务
- rule proposal 提取
- state/foreshadowing proposal 提取
- model quality 粗评估
- critical/blocker 阻断下一章

## 当前 Web 状态

目录：

```text
novel-os-web/
```

当前 Web 已有：

- 登录/会话
- 中英文切换基础
- MCP tool 调用能力
- 部分项目/数据维护入口

但它仍不是完整生产后台。Phase 3 需要改造成：

- 项目选择器
- 项目总览
- 设定集维护
- 人物/势力/地点/道具维护
- 剧情线维护
- 伏笔看板
- 规则库
- 审查中心
- 上下文包预览
- 参考库
- 模型配置
- 同步与审计
- 调试工具

## 当前本地 Skill 状态

目录：

```text
skills/novel-os-local/
```

已有：

- `SKILL.md`
- `references/workflows.md`
- `scripts/novel_local.py`
- 一些本地命令：init、context、commit、review-start、review-submit、review-aggregate、rules-evolve、vector 等。

但遗留问题：

- 还未深度接入 Phase 2.7 同步工具。
- 还未把初始化沟通流程完全产品化。
- 还未把大纲/细纲/正文/审查模型配置接入 Phase 2.10。

## 最近验证状态

本地编译通过：

```text
python -m compileall novel-os-mcp/src
```

NAS Phase 2 全套冒烟通过：

```text
sh scripts/verify-phase2-state-tools.sh
sh scripts/verify-phase2-plot-tools.sh
sh scripts/verify-phase2-foreshadowing-tools.sh
sh scripts/verify-phase2-rules-tools.sh
sh scripts/verify-phase2-context-tools.sh
sh scripts/verify-phase2-sync-tools.sh
sh scripts/verify-phase2-review-learning-tools.sh
sh scripts/verify-phase2-compliance-tools.sh
docker compose -f docker-compose.yml -f docker-compose.app.example.yml ps novel-os-mcp
```

最后一次容器状态：

```text
novel-os-mcp Up, 127.0.0.1:8787->8787/tcp
```
