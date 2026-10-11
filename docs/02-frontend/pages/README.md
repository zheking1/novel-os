# 页面总览

> 共 68 个页面文件（严格 `*page.js`），位于 `novel-os-web/js/pages/`。另有 14 个 helper 模块和 6 个目录。

## 所有页面索引

| Page ID | 文件 | 用途 | 主要 MCP 工具 | 模式类型 |
|---|---|---|---|---|
| `home` | home-page.js (305行) | 工作台仪表盘 + 教程 | workspace.list, model.profile.list, project.list | Dashboard |
| `project-manage` | project-manage-page.js (377行) | 项目 CRUD | project.create/update/delete/list | Standard CRUD |
| `workspace-manage` | workspace-manage-page.js (426行) | 工作区 CRUD + 成员管理 | workspace.add_member/remove_member | Standard CRUD |
| `member-manage` | member-manage-page.js | 成员列表和角色管理 | workspace.list_members | Standard CRUD |
| `canon-list` | canon-list-page.js | Canon 条目列表 | canon.search/list | Standard CRUD |
| `entities-list` | entities-list-page.js | 8 种实体类型列表 | state.entity.list | Detail View |
| `entity-detail` | entity-detail-page.js | 实体详情(双栏+快照+关系) | state.entity.get, state.relationship.list, state.snapshot.list | Detail View |
| `rules-list` | rules-list-page.js | 规则条目列表 | rules.search/list | Standard CRUD |
| `plot-volumes` | plot-volumes-page.js | 卷 CRUD (goals textarea-to-array) | volume.list/upsert/delete | Standard CRUD |
| `plot-threads` | plot-threads-page.js | 情节线 CRUD + stalled 检测 | plot.thread.list/upsert/advance/check_stalled/delete | Interactive/Complex |
| `foreshadowing-list` | foreshadowing-list-page.js (451行) | 伏笔多层管理+回收+过期检查 | plot.list_foreshadowing/upsert_foreshadowing, foreshadowing.payoff/link/check_overdue | Interactive/Complex |
| `chapter-plans` | chapter-plans-page.js | 章节大纲卡片 | plot.list_chapter_plans/create_chapter_plan | Detail View |
| `context-preview` | context-preview-page.js | 上下文预览 | context.build/preview | Read-Only Display |
| `review-tasks` | review-tasks-page.js (460行) | 审核任务列表+启动审核+汇总 | review.list_revision_tasks/start_job/aggregate | Interactive/Complex |
| `review-council` | review-council-page.js | 审核委员会配置 | review.list_council_configs/upsert_council_config | Standard CRUD |
| `compliance` | compliance-page.js | 合规检查 | compliance.check | Read-Only Display |
| `pipeline` | pipeline-page.js | 内容生成流水线 | pipeline.generate | Interactive/Complex |
| `chapters` | chapters-page.js | 章节列表 | local.chapter.list | Standard CRUD |
| `project-world-rules` | project-world-rules-page.js | 世界观规则 | state.entity.list (world_rules) | Standard CRUD |
| `project-characters` | project-characters-page.js | 角色列表 (entity 过滤) | state.entity.list (character) | Standard CRUD |
| `project-factions` | project-factions-page.js | 势力列表 (entity 过滤) | state.entity.list (faction) | Standard CRUD |
| `project-world-state` | project-world-state-page.js | 世界状态 | state.entity.list (world_state) | Read-Only Display |
| `graph-view` | knowledge-graph-page.js (1211行) | D3.js 力导向图谱(项目模式) | graph.get_data | Tree/Graph |
| `local-projects` | local-projects-page.js | 本地项目 | local.project.list | Standard CRUD |
| `arc-characters` | arc-characters-page.js | 角色弧光分析 | arc.analyze_characters | Read-Only Display |
| `arc-tracking` | arc-tracking-page.js | 弧光追踪 | arc.track_progress | Read-Only Display |
| `pacing-analysis` | pacing-analysis-page.js | 节奏分析 | pacing.analyze | Read-Only Display |
| `world-snapshot` | world-snapshot-page.js | 世界快照 | world.snapshot | Read-Only Display |
| `uk-manage` | uk-manage-page.js | 通用知识管理 | kb.uk.search/create/update/delete | Standard CRUD |
| `kb-uk` | kb-uk-list-page.js | 通用知识库标准 CRUD | kb.uk.search/create/delete | Standard CRUD |
| `kb-pk` | kb-pk-list-page.js | 项目知识库标准 CRUD | kb.pk.list/upsert/delete | Standard CRUD |
| `kb-genres` | kb-genres-page.js | 题材策略管理 | kb.genre.list/get/keywords/preheat | Standard CRUD |
| `kb-categories` | kb-categories-page.js | 知识分类递归树 | kb.category.tree/list/create/update/delete | Tree/Graph |
| `kb-search` | kb-search-page.js | 多源知识搜索(高亮) | kb.search | Interactive/Complex |
| `kb-relations` | kb-relations-page.js | 知识实体关系 | kb.entity.search, kb.relationship | Interactive/Complex |
| `kb-init` | kb-init-page.js | 知识库初始化 | kb.init | Interactive/Complex |
| `knowledge-graph` | knowledge-graph-page.js (1211行) | D3.js 力导向图谱(全局模式) | graph.get_data/subgraph/timeline | Tree/Graph |
| `knowledge-stats` | knowledge-stats-page.js | 知识统计 | knowledge.stats | Read-Only Display |
| `knowledge-review` | knowledge-review-page.js | 知识审核 | knowledge.review | Standard CRUD |
| `knowledge-expiry` | knowledge-expiry-page.js | 知识过期管理 | knowledge.expiry | Standard CRUD |
| `expectations` | expectations-page.js | 预期管理 | plot.expectation | Standard CRUD |
| `auto-search` | kb-auto-search-page.js | 自动搜索配置 | kb.auto.search/create_job/store/search_and_store | Interactive/Complex |
| `global-rules` | global-rules-page.js | 全局规则管理 | global_rules.list/upsert/delete | Standard CRUD |
| `style-profiles` | style-profiles-page.js | 风格配置 | style.profile.list/upsert | Standard CRUD |
| `style-analysis` | style-analysis-page.js | 风格分析 | style.analyze | Read-Only Display |
| `style-drift` | style-drift-page.js | 风格偏移检测 | style.detect_drift | Read-Only Display |
| `tone-management` | tone-management-page.js | 基调（情绪底色）管理 | tone.list/upsert/delete/rule.upsert/rule.delete | Interactive/Complex |
| `materials` | materials-page.js | 素材库 | kb.material.list | Standard CRUD |
| `discussion-room` | discussion-room-page.js | AI 讨论室 | discussion.start/poll | Interactive/Complex |
| `evolution` | system-evolution-page.js (450行) | 系统进化提案(7 状态+AI评分) | evolution.proposal.list/upsert | Standard CRUD |
| `evolution-logs` | evolution-logs-page.js | 进化日志（含管理员回滚） | evolution.logs/rollback | Interactive/Complex |
| `notifications` | system-notifications-page.js | 系统通知 | notification.list | Read-Only Display |
| `template-list` | template-list-page.js | 提示词模板 CRUD | prompt.template.list/upsert/delete | Standard CRUD |
| `model-profiles` | model-profiles-page.js | 模型配置+温度滑块 | model.profile.list/upsert | Standard CRUD |
| `model-routes` | model-routes-page.js | 模型路由 | model.route.list/upsert | Standard CRUD |
| `model-rate-limits` | model-rate-limits-page.js | 速率限制 | model.rate_limit.list | Standard CRUD |
| `skill-manage` | skill-manage-page.js | Skill CRUD | skill.list/create/update/delete | Standard CRUD |
| `sync-status` | sync-status-page.js | 同步状态 | sync.status | Read-Only Display |
| `sync-conflicts` | sync-conflicts-page.js | 同步冲突解决 | sync.conflicts.resolve | Interactive/Complex |
| `audit-logs` | audit-logs-page.js | 审计日志 | audit.logs.list | Read-Only Display |
| `offline-status` | offline-status-page.js | 离线状态 | offline.status | Read-Only Display |
| `health` | health-page.js | 系统健康 | system.health | Dashboard |
| `cache` | sys-cache-page.js | Redis 健康和缓存统计 | cache.health/get_stats/warm/invalidate | Dashboard |
| `backup` | sys-backup-page.js | 备份记录和计划 | backup.create/list | Standard CRUD |
| `connection` | connection-page.js | 连接状态 | connection.status | Dashboard |
| `api-keys` | api-tokens-page.js | API Token 管理 | auth.create_api_token/list | Standard CRUD |
| `account` | account-page.js | 账户设置(改密码) | auth.change_password | Read-Only Display |
| `users` | users-page.js | 用户管理+注册开关 | user.list/create/update/delete | Standard CRUD |
| `debug` | debug-page.js | 调试面板 | — | Dashboard |

## 页面模式类型定义

| 类型 | 说明 | 特征 |
|---|---|---|
| **Standard CRUD** | 标准增删改查 | `PAGE_CONFIG` 模式，DataTable + Modal 表单 |
| **Custom CRUD** | 自定义增删改查 | 有自己的特殊交互逻辑，不完全遵循模板 |
| **Read-Only Display** | 只读展示 | 仅展示数据，无创建/编辑功能 |
| **Dashboard** | 仪表盘/概览 | 多面板卡片布局，聚合统计 |
| **Detail View** | 详情视图 | 复杂信息展示(双栏、卡片)，含关联数据 |
| **Tree/Graph** | 树/图可视化 | D3.js 力导向图或递归树 |
| **Interactive/Complex** | 交互/复杂 | 多步骤工作流、实时交互、轮询等 |