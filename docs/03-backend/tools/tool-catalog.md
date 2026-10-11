# Novel OS — MCP 工具目录

本文档完整列出所有 MCP 工具及其参数签名。

> 共约 200+ 个工具，按功能模块分节。参数中 `?` 表示可选。

## 1. Auth & User Management (`auth.py`)

| 工具名 | 参数 | 权限 | 说明 |
|-------|------|------|------|
| `auth.whoami` | — | read | 获取当前用户身份信息 |
| `auth.login` | `username`, `password` | — | 用户登录验证 |
| `auth.change_password` | `username`, `old_password`, `new_password` | read | 修改用户密码 |
| `auth.list_api_tokens` | `workspace?`, `project?`, `include_revoked?` | read | 列出 API 令牌 |
| `auth.create_api_token` | `name`, `scopes`, `username?`, `workspace?`, `project?`, `expires_at?` | read | 创建 API 令牌 |
| `auth.revoke_api_token` | `token_id` | admin | 吊销 API 令牌 |
| `user.create` | `username`, `display_name?`, `email?`, `status?`, `password?` | admin | 创建新用户 |
| `user.list` | `status?`, `limit?` | admin | 列出系统用户 |
| `user.delete` | `username` | admin | 删除用户 |

## 2. Workspace & Project (`auth.py`)

| 工具名 | 参数 | 权限 | 说明 |
|-------|------|------|------|
| `workspace.create` | `slug`, `name` | write | 创建新工作空间 |
| `workspace.list` | `username?` | read | 列出工作空间 |
| `workspace.add_member` | `workspace`, `username`, `role?` | write | 添加工作空间成员 |
| `workspace.remove_member` | `workspace`, `username` | write | 移除工作空间成员 |
| `workspace.delete` | `slug` | write | 删除工作空间 |
| `project.create` | `workspace`, `slug`, `title`, `description?` | write | 创建新项目 |
| `project.list` | `workspace`, `username?` | read | 列出项目 |
| `project.list_members` | `workspace`, `project` | admin | 列出项目成员 |
| `project.add_member` | `workspace`, `project`, `username`, `role?` | admin | 添加项目成员 |
| `project.delete` | `workspace`, `slug` | write | 删除项目 |
| `project.register_local_binding` | `workspace`, `project`, `client_id`, `local_root_hint?`, `manifest?` | write | 注册本地客户端绑定 |

## 3. Admin & Health (`admin.py`)

| 工具名 | 参数 | 权限 | 说明 |
|-------|------|------|------|
| `admin.health` | — | read | 系统健康检查（DB/Redis/Qdrant） |

## 4. System (`system.py`)

| 工具名 | 参数 | 权限 | 说明 |
|-------|------|------|------|
| `system.health` | — | read | 获取系统健康状态 |
| `system.degradation_status` | — | read | 获取降级状态 |
| `system.degradation_plan` | `failed_services` | read | 获取降级方案 |
| `system.fallback_strategy` | `feature` | read | 获取功能降级策略 |

## 5. Cache (`system.py`)

| 工具名 | 参数 | 权限 | 说明 |
|-------|------|------|------|
| `cache.health` | — | read | 检查 Redis 缓存健康状态 |
| `cache.get_stats` | `workspace`, `project` | read | 获取项目缓存统计 |
| `cache.get` | `workspace`, `project`, `target`, `target_id`, `profile?`, `pov?` | read | 获取缓存内容 |
| `cache.invalidate` | `workspace`, `project`, `target`, `target_id?` | write | 使缓存失效 |
| `cache.warm` | `workspace`, `project`, `chapter_nos`, `profiles?`, `povs?` | write | 预热上下文缓存 |

## 6. Backup & Restore (`system.py`)

| 工具名 | 参数 | 权限 | 说明 |
|-------|------|------|------|
| `backup.create` | `workspace?`, `project?`, `backup_type?`, `storage_path?` | admin | 创建备份记录 |
| `backup.list` | `workspace?`, `project?`, `backup_type?`, `status?`, `limit?` | read | 获取备份记录列表 |
| `backup.schedule.upsert` | `schedule_name`, `workspace?`, `project?`, `backup_type?`, `schedule_type?`, `retention_count?`, `retention_days?`, `enabled?` | admin | 创建/更新备份计划 |
| `backup.schedule.list` | `workspace?`, `project?` | read | 获取备份计划列表 |
| `restore.list` | `workspace`, `project`, `limit?` | read | 获取恢复记录列表 |

## 7. Knowledge Base — Categories (`kb.py`)

| 工具名 | 参数 | 权限 | 说明 |
|-------|------|------|------|
| `kb.category.list` | `parent_slug?` | read | 列出知识分类 |
| `kb.category.tree` | — | read | 列出所有知识分类（含 parent_id） |
| `kb.category.create` | `slug`, `name`, `parent_id?`, `description?`, `sort_order?` | write | 创建知识分类 |
| `kb.category.update` | `category_id`, `name?`, `slug?`, `description?`, `sort_order?`, `parent_id?` | write | 更新知识分类 |
| `kb.category.delete` | `category_id` | write | 删除知识分类 |

## 8. Knowledge Base — Entities (`kb.py`)

| 工具名 | 参数 | 权限 | 说明 |
|-------|------|------|------|
| `kb.entity.create` | `entity_type`, `name`, `content`, `summary?`, `aliases?`, `structured_data?`, `source?`, `source_url?`, `reliability?`, `genre_tags?`, `era?` | write | 创建知识实体 |
| `kb.entity.get` | `entity_id` | read | 获取知识实体详情 |
| `kb.entity.search` | `query`, `entity_type?`, `genre?`, `era?`, `limit?` | read | 搜索知识实体 |
| `kb.entity.update` | `entity_id`, `name?`, `entity_type?`, `description?`, `aliases?`, `traits?`, `status?` | write | 更新知识实体 |
| `kb.relation.create` | `from_entity_id`, `to_entity_id`, `relation_type`, `detail?`, `strength?` | write | 创建实体关系 |
| `kb.entity.list_relations` | `entity_id`, `relation_type?` | read | 列出实体关系 |

## 9. Knowledge Base — Universal Knowledge (`kb.py`)

| 工具名 | 参数 | 权限 | 说明 |
|-------|------|------|------|
| `kb.uk.search` | `query?`, `category_slug?`, `genre?`, `era?`, `year?`, `limit?` | — | 搜索 UK 知识库 |
| `kb.uk.create` | `topic`, `content`, `category_slug?`, `summary?`, `era?`, `year_range?`, `genre_tags?`, `source?`, `source_url?`, `reliability?`, `tags?` | — | 创建 UK 条目 |
| `kb.uk.update` | `entry_id`, `topic?`, `content?`, `summary?`, `era?`, `source?`, `source_url?`, `status?`, `reliability?`, `genre_tags?`, `year_range?`, `tags?`, `structured_data?` | — | 更新 UK 条目 |
| `kb.uk.delete` | `entry_id` | — | 删除 UK 条目 |
| `kb.uk.stats` | `genre?` | — | 获取 UK 统计信息 |

## 10. Knowledge Base — Project Knowledge (`kb.py`)

| 工具名 | 参数 | 权限 | 说明 |
|-------|------|------|------|
| `kb.pk.upsert` | `workspace`, `project`, `project_id`, `category`, `key`, `value`, `description?`, `chapter_no?`, `tags?` | write | 创建/更新项目知识 |
| `kb.pk.get` | `workspace`, `project`, `project_id`, `category`, `key` | read | 获取单条项目知识 |
| `kb.pk.list` | `workspace`, `project`, `project_id`, `category?` | read | 列出项目知识条目 |
| `kb.pk.delete` | `workspace`, `project`, `project_id`, `category`, `key` | write | 删除项目知识条目 |

## 11. Knowledge Base — World State (`kb.py`)

| 工具名 | 参数 | 权限 | 说明 |
|-------|------|------|------|
| `kb.world.get` | `workspace`, `project`, `chapter_no?` | read | 获取世界状态快照 |
| `kb.world.update` | `workspace`, `project`, `project_id`, `chapter_no`, `world_state`, `story_time?`, `story_year?`, `story_era?`, `story_progress?`, `character_count?`, `active_threads?` | write | 更新世界状态快照 |
| `kb.world.list` | `workspace`, `project`, `project_id`, `limit?` | read | 列出世界状态快照 |
| `kb.world.auto_update` | `workspace`, `project`, `chapter_no`, `generated_content`, `story_time?`, `story_year?`, `story_era?` | write | 章节生成后自动更新世界状态 |

## 12. Knowledge Base — Search & Store (`kb.py`)

| 工具名 | 参数 | 权限 | 说明 |
|-------|------|------|------|
| `kb.search.create_job` | `query_text`, `workspace`, `project`, `project_id?`, `category_slug?`, `chapter_no?`, `triggered_by?` | read | 创建知识自动搜索任务 |
| `kb.search.complete_job` | `job_id`, `results_count`, `entries_created` | write | 标记搜索任务已完成 |
| `kb.auto.search_and_store` | `query`, `search_results`, `workspace`, `project`, `project_id?`, `category_slug?`, `genre_tags?`, `chapter_no?` | write | 一步：搜索+存储 |

## 13. Knowledge Base — Gaps (`kb.py`)

| 工具名 | 参数 | 权限 | 说明 |
|-------|------|------|------|
| `kb.gap.create` | `description`, `workspace`, `project`, `project_id?`, `gap_type?`, `entity_name?`, `entity_type?`, `context?` | write | 创建知识缺口记录 |
| `kb.gap.list` | `workspace`, `project`, `project_id?`, `resolved?` | read | 列出知识缺口 |
| `kb.gap.resolve` | `gap_id`, `entry_id?` | write | 标记知识缺口已解决 |
| `kb.gap.detect` | `workspace`, `project`, `project_id`, `chapter_plan?`, `chapter_no?` | read | 从章节大纲检测知识缺口 |
| `kb.gap.analyze` | `genre` | read | 分析题材知识缺口 |

## 14. Knowledge Base — Genre (`kb.py`)

| 工具名 | 参数 | 权限 | 说明 |
|-------|------|------|------|
| `kb.genre.list` | — | read | 列出所有题材策略 |
| `kb.genre.get` | `genre_id` | read | 获取题材策略详情 |
| `kb.genre.keywords` | `genre_id`, `year?`, `city?`, `event?`, `dynasty?` | read | 生成题材搜索关键词 |
| `kb.genre.preheat` | `workspace`, `project`, `project_id`, `genre` | — | 预加载题材 UK 条目 |
| `kb.genre.update` | `genre`, `included_categories?`, `excluded_categories?`, `description?` | write | 更新题材知识配置 |
| `kb.genre.create` | `slug`, `name`, `description?`, `typical_elements?`, `target_audience?`, `platform_tags?`, `aliases?`, `included_categories?`, `excluded_categories?` | write | 创建新题材 |
| `kb.genre.delete` | `slug` | write | 删除题材 |


## 15. Knowledge Pack (`knowledge_pack.py`)

| 工具名 | 参数 | 权限 | 说明 |
|-------|------|------|------|
| `kb.pack.genre.list` | — | read | 列出所有小说类型知识配置 |
| `kb.pack.genre.get` | `genre` | read | 获取指定类型知识配置 |
| `kb.pack.get` | `workspace`, `project`, `project_id` | read | 获取项目知识包 |
| `kb.pack.create` | `workspace`, `project`, `project_id`, `genre` | write | 创建项目知识包 |
| `kb.pack.update` | `workspace`, `project`, `project_id`, `active_categories?` | write | 更新项目知识包 |
| `kb.pack.custom.add` | `workspace`, `project`, `project_id`, `name`, `parent?`, `description?` | write | 添加自定义分类 |
| `kb.pack.custom.remove` | `workspace`, `project`, `project_id`, `name` | write | 移除自定义分类 |
| `kb.pack.categories` | `workspace`, `project`, `project_id` | read | 获取项目启用分类 |

## 16. Knowledge Audit (`knowledge_audit.py`)

| 工具名 | 参数 | 权限 | 说明 |
|-------|------|------|------|
| `knowledge.audit_all` | `workspace`, `project`, `mode?` | write | 审计所有知识分类 |
| `knowledge.audit_status` | `workspace`, `project` | read | 查看审计进度 |
| `knowledge.council_debate_all` | `workspace`, `project` | read | 辩论委员会裁决 |

## 17. Settings (`setting.py`)

| 工具名 | 参数 | 权限 | 说明 |
|-------|------|------|------|
| `setting.category.list` | `workspace`, `is_active?` | read | 列出设置分类 |
| `setting.category.get` | `workspace`, `category_id?`, `slug?` | read | 获取设置分类 |
| `setting.category.upsert` | `workspace`, `slug`, `name`, `description?`, `icon?`, `sort_order?`, `is_standard?`, `metadata?` | write | 创建/更新设置分类 |
| `setting.category.delete` | `workspace`, `category_id` | write | 删除设置分类 |
| `setting.item.list` | `workspace`, `category_id?`, `is_global?`, `level?`, `tags?`, `limit?`, `offset?` | read | 列出设置条目 |
| `setting.item.get` | `workspace`, `item_id?`, `item_code?` | read | 获取设置条目 |
| `setting.item.upsert` | `workspace`, `category_id`, `core_summary`, `item_code?`, `keywords?`, `intent_synonyms?`, `detailed_expansion?`, `ai_instruction?`, `poison_points?`, `level?`, `applicable_skills?`, `applicable_genres?`, `data?`, `tags?`, `is_global?`, `sort_order?`, `metadata?` | write | 创建/更新设置条目 |
| `setting.item.bulk_upsert` | `workspace`, `category_id`, `items` | write | 批量导入设置条目 |
| `setting.item.delete` | `workspace`, `item_id` | write | 删除设置条目 |
| `setting.search` | `workspace`, `query`, `category_id?`, `level?`, `skill?`, `genre?`, `limit?`, `offset?` | read | BM25 搜索设置条目 |
| `setting.genre.list` | — | read | 列出系统预设题材 |
| `setting.genre.resolve` | `input_text` | read | 模糊匹配题材名称 |
| `setting.genre.delete` | `slug` | write | 删除题材 |
| `setting.csv.import` | `workspace`, `category_id`, `csv_content` | write | CSV 批量导入 |
| `setting.csv.export` | `workspace`, `category_id?` | read | 导出为 CSV |

## 18. Prompt Templates (`prompt.py`)

| 工具名 | 参数 | 权限 | 说明 |
|-------|------|------|------|
| `prompt.template.upsert` | `workspace`, `project`, `template_key`, `name`, `template_content`, `description?`, `template_type?`, `variables?`, `genre?`, `scene?` | write | 创建/更新 Prompt 模板 |
| `prompt.template.get` | `workspace`, `project`, `template_key` | read | 获取 Prompt 模板 |
| `prompt.template.list` | `workspace`, `project?`, `genre?`, `scene?`, `template_type?`, `limit?` | read | 列出 Prompt 模板 |
| `prompt.template.render` | `workspace`, `project`, `template_key`, `variables` | write | 渲染 Prompt 模板 |
| `prompt.template.delete` | `workspace`, `project`, `template_key` | write | 删除 Prompt 模板 |

## 19. Context Weights (`prompt.py`)

| 工具名 | 参数 | 权限 | 说明 |
|-------|------|------|------|
| `context.weight.upsert` | `workspace`, `project`, `config_name`, `weights`, `profile?`, `max_total_tokens?`, `priority_order?` | write | 创建/更新权重配置 |
| `context.weight.get` | `workspace`, `project`, `config_name`, `profile?` | read | 获取权重配置 |
| `context.weight.list` | `workspace`, `project`, `profile?` | read | 列出权重配置 |

## 20. Reference Materials (`prompt.py`)

| 工具名 | 参数 | 权限 | 说明 |
|-------|------|------|------|
| `material.upsert` | `workspace`, `project`, `material_key`, `title`, `material_type`, `content?`, `category?`, `tags?`, `source_url?` | write | 创建/更新参考素材 |
| `material.get` | `workspace`, `project`, `material_key` | read | 获取参考素材详情 |
| `material.list` | `workspace`, `project`, `material_type?`, `category?`, `tags?`, `favorite?`, `search?`, `limit?` | read | 列出参考素材 |
| `material.favorite` | `workspace`, `project`, `material_key` | write | 切换收藏状态 |

## 21. Reader Expectations (Deprecated) (`prompt.py`)

| 工具名 | 参数 | 权限 | 说明 |
|-------|------|------|------|
| `expectation.upsert` | `workspace`, `project`, `expectation_key`, `title`, `expectation_type`, `description?`, `chapter_no?`, `importance?`, `tags?` | write | 创建/更新读者期待 |
| `expectation.list` | `workspace`, `project`, `status?`, `expectation_type?`, `importance?`, `limit?` | read | 列出读者期待 |
| `expectation.fulfill` | `workspace`, `project`, `expectation_key`, `payoff_chapter_no` | write | 标记已回收 |

## 22. Chapter Annotations (`prompt.py`)

| 工具名 | 参数 | 权限 | 说明 |
|-------|------|------|------|
| `annotation.create` | `workspace`, `project`, `chapter_id`, `chapter_no`, `annotation_type`, `content`, `anchor_start?`, `anchor_end?`, `parent_id?` | write | 创建章节批注 |
| `annotation.list` | `workspace`, `project`, `chapter_id?`, `annotation_type?`, `resolve_status?` | read | 列出章节批注 |
| `annotation.resolve` | `workspace`, `project`, `annotation_id` | write | 标记批注已解决 |

## 23. Proper Nouns (`prompt.py`)

| 工具名 | 参数 | 权限 | 说明 |
|-------|------|------|------|
| `noun.upsert` | `workspace`, `project`, `noun_key`, `noun_value`, `noun_type`, `aliases?`, `description?`, `locked?`, `first_chapter_no?` | write | 创建/更新专有名词 |
| `noun.list` | `workspace`, `project`, `noun_type?`, `locked?`, `search?` | read | 列出专有名词 |
| `noun.check` | `workspace`, `project`, `text` | read | 检查一致性 |

## 24. Fulltext Search (`prompt.py`)

| 工具名 | 参数 | 权限 | 说明 |
|-------|------|------|------|
| `search.fulltext` | `workspace`, `project`, `query`, `source_types?`, `limit?` | read | 全文检索 |
| `search.index` | `workspace`, `project`, `source_type`, `source_id`, `title`, `content`, `source_key?` | write | 索引内容 |

## 25. Model Profiles (`model.py`)

| 工具名 | 参数 | 权限 | 说明 |
|-------|------|------|------|
| `model.profile.upsert` | `profile_key`, `display_name?`, `provider?`, `model_name?`, `task_types?`, `tier?`, `default_params?`, `cost_config?`, `rate_limit_config?`, `is_default?`, `status?`, `metadata?`, `is_contributed?` | write | 创建/更新模型配置 |
| `model.profile.list` | `task_type?`, `status?`, `tier?` | read | 列出模型配置 |
| `model.route` | `workspace`, `project`, `task_type`, `chapter_no?`, `volume_no?` | read | 路由到最佳模型 |
| `model.route_rule.upsert` | `workspace`, `project`, `task_type`, `profile_key`, `priority?`, `conditions?`, `fallback_profile_keys?`, `status?`, `metadata?` | write | 创建/更新路由规则 |
| `model.route_rule.list` | `workspace`, `project`, `task_type?`, `status?` | read | 列出路由规则 |
| `model.auto_assign` | `workspace`, `project` | write | 自动分析并分配任务 |

## 26. Cost Tracking (`model.py`)

| 工具名 | 参数 | 权限 | 说明 |
|-------|------|------|------|
| `cost.record_usage` | `workspace`, `project`, `task_type`, `profile_key?`, `provider?`, `model_name?`, `source_type?`, `source_id?`, `input_tokens?`, `output_tokens?`, `cached_tokens?`, `total_tokens?`, `cost_amount?`, `currency?`, `latency_ms?`, `success?`, `error_code?`, `metadata?` | write | 记录模型用量 |
| `cost.report` | `workspace`, `project`, `group_by?`, `task_types?`, `profile_keys?`, `from_date?`, `to_date?` | read | 生成费用报表 |

## 27. Discussion Room (`discussion_room.py`)

| 工具名 | 参数 | 权限 | 说明 |
|-------|------|------|------|
| `discussion_room.create_session` | `workspace`, `project`, `topic`, `model_keys?`, `rate_limit_delay?`, `rate_limit_retries?`, `data_source?`, `data_category?`, `output_type?` | write | 创建讨论会话 |
| `discussion_room.get_updates` | `session_id` | read | 轻量轮询状态 |
| `discussion_room.list_sessions` | `workspace`, `project`, `status?`, `limit?` | read | 列出历史会话 |
| `discussion_room.get_session` | `session_id` | read | 获取完整会话 |
| `discussion_room.resume_session` | `workspace`, `project`, `session_id`, `new_topic?`, `rate_limit_delay?`, `rate_limit_retries?` | write | 继续讨论 |
| `discussion_room.apply_results` | `workspace`, `project`, `session_id` | write | 应用到知识库 |
| `discussion_room.delete_session` | `workspace`, `project`, `session_id` | write | 删除会话 |


## 28. Review (`review.py`)

| 工具名 | 参数 | 权限 | 说明 |
|-------|------|------|------|
| `review.start_job` | `workspace`, `project`, `chapter_no`, `dimensions`, `local_files?`, `chapter_content?` | write | 启动审核任务（讨论室模式） |
| `review.list_jobs` | `workspace`, `project`, `status?`, `limit?` | read | 列出审核任务 |
| `review.aggregate` | `workspace`, `project`, `review_job_id`, `create_revision_tasks?` | write | 汇总审核结果 |
| `review.list_revision_tasks` | `workspace`, `project`, `status?`, `severity?`, `limit?`, `offset?`, `task_id?` | read | 列出修订任务 |
| `review.update_revision_task` | `workspace`, `project`, `task_id`, `status?`, `metadata_patch?` | write | 更新修订任务 |
| `review.upsert_council_config` | `name?`, `config?`, `is_active?` | write | 审核委员会配置 |
| `review.list_council_configs` | — | read | 列出委员会配置 |
| `review.council.dispatch` | `review_job_id` | read | 获取待审核模型 |
| `review.submit_model_report` | `workspace`, `project`, `review_job_id`, `model_id`, `content?`, `score?`, `summary?`, `findings?`, `local_report_file?` | write | 提交模型审核报告 |
| `review.extract_rule_proposals` | `workspace`, `project`, `review_job_id`, `create_proposals?`, `min_confidence?` | write | 提取规则提案 |
| `review.extract_state_updates` | `workspace`, `project`, `review_job_id` | read | 提取状态更新 |
| `review.extract_foreshadowing_updates` | `workspace`, `project`, `review_job_id` | read | 提取伏笔更新 |
| `review.evaluate_model_quality` | `workspace`, `project`, `review_job_id?` | read | 评估审核质量 |
| `review.submit_evolution_proposals` | `workspace`, `project`, `review_job_id`, `auto_submit?` | write | 提交进化提案 |

## 29. Plot — Volumes (`plot.py`)

| 工具名 | 参数 | 权限 | 说明 |
|-------|------|------|------|
| `volume.upsert` | `workspace`, `project`, `volume_no`, `title?`, `outline?`, `status?`, `start_chapter_no?`, `end_chapter_no?`, `summary?`, `goals?`, `metadata?` | write | 创建/更新卷 |
| `volume.get` | `workspace`, `project`, `volume_no?`, `volume_id?` | read | 获取卷详情 |
| `volume.list` | `workspace`, `project`, `statuses?`, `current_chapter_no?`, `limit?` | read | 列出所有卷 |

## 30. Plot — Plot Threads (`plot.py`)

| 工具名 | 参数 | 权限 | 说明 |
|-------|------|------|------|
| `plot.thread.upsert` | `workspace`, `project`, `key`, `title`, `thread_type?`, `status?`, `importance?`, `volume_no?`, `start_chapter_no?`, `current_chapter_no?`, `last_advanced_chapter_no?`, `expected_next_chapter_no?`, `stalled_after_chapters?`, `related_entity_ids?`, `related_foreshadowing_ids?`, `metadata?` | write | 创建/更新情节线 |
| `plot.thread.list` | `workspace`, `project`, `statuses?`, `thread_types?`, `importance?`, `volume_no?`, `current_chapter_no?`, `include_closed?`, `limit?` | read | 列出情节线 |
| `plot.thread.advance` | `workspace`, `project`, `key`, `chapter_no`, `status?`, `progress_note?`, `expected_next_chapter_no?`, `metadata?` | write | 推进情节线 |
| `plot.thread.check_stalled` | `workspace`, `project`, `current_chapter_no`, `threshold_chapters?`, `statuses?`, `limit?` | read | 检测停滞情节线 |
| `plot.thread.delete` | `workspace`, `project`, `key` | write | 删除情节线 |

## 31. Plot — Foreshadowing (`plot.py`)

| 工具名 | 参数 | 权限 | 说明 |
|-------|------|------|------|
| `plot.upsert_foreshadowing` | `workspace`, `project`, `key`, `title`, `status?`, `importance?`, `expected_payoff_range?`, `payload?`, `parent_foreshadowing_id?`, `related_foreshadowing_ids?`, `trigger_on_payoff_ids?`, `blocks_payoff_until_ids?`, `layer?`, `must_payoff?`, `payoff_deadline_chapter?`, `payoff_deadline_volume?`, `overdue_policy?` | write | 创建/更新伏笔 |
| `plot.list_foreshadowing` | `workspace`, `project`, `statuses?`, `importance?`, `layers?`, `overdue_at_chapter?`, `limit?` | read | 列出伏笔 |
| `foreshadowing.bulk_status_update` | `workspace`, `project`, `status`, `keys?`, `ids?`, `reason?`, `metadata?` | write | 批量更新伏笔 |
| `foreshadowing.check_overdue` | `workspace`, `project`, `current_chapter_no`, `current_volume_no?`, `include_optional?`, `limit?` | read | 检查逾期伏笔 |
| `foreshadowing.link` | `workspace`, `project`, `key`, `parent_key?`, `related_keys?`, `trigger_on_payoff_keys?`, `blocks_payoff_until_keys?`, `replace?` | write | 建立伏笔关联 |
| `foreshadowing.payoff` | `workspace`, `project`, `key`, `payoff_chapter_no?`, `payoff_chapter_id?`, `payoff_note?`, `status?`, `trigger_related?`, `metadata?` | write | 回收伏笔 |

## 32. Plot — Chapter Plans (`plot.py`)

| 工具名 | 参数 | 权限 | 说明 |
|-------|------|------|------|
| `plot.create_chapter_plan` | `workspace`, `project`, `chapter_no`, `plan` | write | 创建章节大纲 |
| `plot.list_chapter_plans` | `workspace`, `project`, `status?`, `limit?` | read | 列出章节计划 |

## 33. Canon Documents (`canon.py`)

| 工具名 | 参数 | 权限 | 说明 |
|-------|------|------|------|
| `canon.doc.upsert` | `workspace`, `project`, `doc_type`, `key`, `title`, `content`, `status?`, `scope?`, `review_status?`, `source_type?`, `source_id?`, `related_rule_ids?`, `metadata?`, `change_reason?` | write | 创建/更新设定文档 |
| `canon.doc.list` | `workspace`, `project`, `doc_types?`, `statuses?`, `review_status?`, `query?`, `limit?`, `offset?` | read | 列出设定文档 |
| `canon.doc.get` | `workspace`, `project`, `document_id?`, `doc_type?`, `key?` | read | 获取设定文档 |
| `canon.doc.archive` | `workspace`, `project`, `document_id?`, `doc_type?`, `key?`, `reason?` | write | 归档设定文档 |
| `canon.doc.history` | `workspace`, `project`, `document_id?`, `doc_type?`, `key?`, `limit?` | read | 查看版本历史 |
| `canon.doc.restore` | `workspace`, `project`, `version`, `document_id?`, `doc_type?`, `key?`, `reason?` | write | 恢复历史版本 |


## 34. Rules (`canon.py`)

| 工具名 | 参数 | 权限 | 说明 |
|-------|------|------|------|
| `rules.list` | `workspace`, `project`, `rule_types?`, `status?`, `chapter_no?`, `volume_no?` | read | 列出项目规则（传 `status=null` 返回全部状态） |
| `rules.list_effective` | `workspace`, `project`, `rule_types?`, `chapter_no?`, `volume_no?`, `scope_refs?`, `scope_types?`, `active_event_keys?`, `include_blocked?` | read | 列出当前生效规则 |
| `rules.check_conflict` | `workspace`, `project`, `rule_types?`, `chapter_no?`, `volume_no?`, `scope_refs?`, `scope_types?`, `active_event_keys?`, `text?` | read | 检查规则冲突，可选传入文本做合规检测 |
| `rules.propose` | `workspace`, `project`, `title`, `content`, `proposal_type?`, `source_type?`, `confidence?`, `agreement?` | write | 提交规则提案 |
| `rules.upsert` | `workspace`, `project`, `rule_key`, `rule_type`, `title`, `content`, `scope?`, `severity?`, `status?`, `metadata?`, `change_reason?`, `source?`, `scope_type?`, `scope_ref?`, `scope_config?`, `priority?`, `effective_chapter_no?`, `expire_chapter_no?`, `effective_volume_no?`, `expire_volume_no?`, `is_temporary?`, `active_from_event?`, `expire_on_event?`, `conflict_policy?`, `supersedes_rule_ids?`, `blocked_by_rule_ids?` | write | 创建/更新规则（支持作用域、优先级、有效期、冲突策略） |
| `rules.bulk_toggle` | `workspace`, `project`, `status`, `rule_keys?`, `rule_ids?`, `rule_types?`, `reason?` | write | 批量启停规则（`status` 必填） |
| `rules.resolve_conflict` | `workspace`, `project`, `action`, `source_rule_key?`, `source_rule_id?`, `target_rule_keys?`, `target_rule_ids?`, `priority?`, `reason?` | write | 解决规则冲突（`action`: suppress/merge/override） |
| `rules.list_proposals` | `workspace`, `project`, `status?`, `limit?` | read | 列出规则提案 |
| `rules.apply_proposal` | `workspace`, `project`, `proposal_id`, `decision`, `reason?` | write | 审批提案（`decision`: approve/reject） |
| `rules.delete` | `workspace`, `project`, `rule_key?`, `rule_id?` | write | 删除规则（二者至少填一） |

## 35. Compliance (`canon.py`)

| 工具名 | 参数 | 权限 | 说明 |
|-------|------|------|------|
| `compliance.rule.upsert` | `workspace`, `project`, `rule_key`, `title`, `content`, `category?`, `patterns?`, `match_type?`, `severity?`, `status?`, `scope_type?`, `scope_ref?`, `priority?`, `case_sensitive?`, `hint?`, `metadata?` | write | 创建/更新合规规则（关键词/正则匹配） |
| `compliance.rule.list` | `workspace`, `project`, `status?`, `categories?`, `chapter_no?`, `volume_no?` | read | 列出合规规则 |
| `compliance.rule.delete` | `workspace`, `project`, `rule_key` | write | 删除（软删除）合规规则 |
| `compliance.check` | `workspace`, `project`, `text?`, `content_items?`, `chapter_no?`, `volume_no?`, `scope_refs?`, `scope_types?`, `review_job_id?`, `create_revision_task?` | read | 执行合规检查；后两个参数需要 write 权限 |

## 36. Global Rules (`global_rules.py`)

| 工具名 | 参数 | 权限 | 说明 |
|-------|------|------|------|
| `global_rules.list` | `rule_type?`, `status?`, `limit?` | read | 列出全局规则 |
| `global_rules.upsert` | `rule_key`, `rule_type`, `title`, `content`, `severity?`, `status?`, `metadata?` | write | 创建/更新全局规则 |
| `global_rules.delete` | `rule_key` | write | 删除全局规则 |
| `global_rules.promote` | `workspace`, `project`, `rule_key` | write | 项目规则提升为全局 |

## 37. Memory & Semantics (`memory.py`)

| 工具名 | 参数 | 权限 | 说明 |
|-------|------|------|------|
| `memory.search` | `workspace`, `project`, `query`, `source_types?`, `limit?` | read | 语义搜索记忆 |
| `memory.get_state` | `workspace`, `project`, `entity_type`, `name` | read | 获取实体当前状态 |
| `memory.get_recent_summaries` | `workspace`, `project`, `before_chapter_no`, `count?` | read | 获取最近章节摘要 |
| `memory.rebuild_projection` | `workspace`, `project`, `from_chapter_no?` | write | 重建记忆投影 |
| `memory.pending_vector_chunks` | `workspace`, `project`, `limit?` | read | 待向量化块 |
| `memory.upsert_vector` | `workspace`, `project`, `chunk_id`, `vector`, `collection?`, `payload?` | write | 写入向量 |
| `memory.vector_search` | `workspace`, `project`, `vector`, `collection?`, `limit?` | read | 向量搜索 |
| `memory.vectorize_pending` | `workspace`, `project`, `batch_size?` | write | 批量向量化 |

## 38. State Entities (`memory.py`)

| 工具名 | 参数 | 权限 | 说明 |
|-------|------|------|------|
| `state.entity.upsert` | `workspace`, `project`, `entity_type`, `name`, `aliases?`, `summary?`, `description?`, `portrait_url?`, `profile?`, `lifecycle_status?`, `importance?`, `tags?`, `first_seen_chapter_no?`, `last_seen_chapter_no?`, `first_seen_volume_no?`, `last_seen_volume_no?`, `source_type?`, `source_id?`, `metadata?` | write | 创建/更新故事实体 |
| `state.entity.list` | `workspace`, `project`, `entity_type?`, `lifecycle_status?`, `query?`, `tags?`, `include_archived?`, `limit?`, `offset?` | read | 列出故事实体 |
| `state.entity.get` | `workspace`, `project`, `entity_id?`, `entity_type?`, `name?` | read | 获取实体详情 |
| `state.entity.bulk_patch` | `workspace`, `project`, `entity_ids`, `patch` | write | 批量更新实体 |

## 39. State Snapshots (`memory.py`)

| 工具名 | 参数 | 权限 | 说明 |
|-------|------|------|------|
| `state.snapshot.upsert` | `workspace`, `project`, `state`, `entity_id?`, `entity_type?`, `name?`, `chapter_no?`, `chapter_id?`, `source_commit_id?`, `is_current?`, `effective_chapter_no?`, `expire_chapter_no?`, `effective_volume_no?`, `expire_volume_no?`, `duration_type?`, `expires_on_event?`, `confidence?`, `source_type?`, `source_id?`, `change_reason?`, `metadata?` | write | 创建/更新快照 |
| `state.snapshot.list` | `workspace`, `project`, `entity_id?`, `entity_type?`, `name?`, `current_only?`, `current_chapter_no?`, `include_expired?`, `limit?` | read | 列出快照 |
| `state.snapshot.at_chapter` | `workspace`, `project`, `entity_name`, `chapter_no` | read | 指定章节时刻状态 |

## 40. State Relationships (`memory.py`)

| 工具名 | 参数 | 权限 | 说明 |
|-------|------|------|------|
| `state.relationship.upsert` | `workspace`, `project`, `relation_type`, `source_entity_id?`, `source_entity_type?`, `source_name?`, `target_entity_id?`, `target_entity_type?`, `target_name?`, `attitude?`, `intensity?`, `known_by_source?`, `known_by_target?`, `known_by_reader?`, `status?`, `source_chapter_no?`, `source_chapter_id?`, `source_commit_id?`, `metadata?` | write | 创建/更新关系 |
| `state.relationship.list` | `workspace`, `project`, `entity_id?`, `entity_type?`, `name?`, `relation_type?`, `status?`, `include_reader_hidden?`, `limit?` | read | 列出关系 |


## 41. Context & Workflow (`context.py`)

| 工具名 | 参数 | 权限 | 说明 |
|-------|------|------|------|
| `workflow.prepare_chapter_context` | `workspace`, `project`, `chapter_no`, `purpose?`, `focus?`, `budget?`, `volume_no?`, `scope_refs?`, `scope_types?`, `active_event_keys?`, `pov_mode?`, `pass_number?`, `previous_context?` | read | 准备章节上下文（返回 workflow_guide） |
| `workflow.preflight_generation` | `workspace`, `project`, `chapter_no`, `purpose?`, `focus?`, `budget?`, `volume_no?`, `scope_refs?`, `scope_types?`, `active_event_keys?`, `pov_mode?` | read | 生成前预检 |
| `workflow.prepare_segment_context` | `workspace`, `project`, `chapter_no`, `segment`, `purpose?`, `focus?`, `budget?`, `volume_no?`, `scope_refs?`, `scope_types?`, `active_event_keys?`, `pov_mode?` | read | 片段上下文 |
| `workflow.submit_chapter_commit` | `workspace`, `project`, `chapter_no`, `title?`, `local_files`, `commit` | write | 提交章节 |
| `workflow.validate_content` | `workspace`, `project`, `chapter_no`, `content` | write | 校验生成内容 |
| `workflow.validate_context_pack` | `workspace`, `project`, `context_pack_id?`, `chapter_no?` | read | 验证上下文包完整性 |
| `workflow.learn_from_review` | `workspace`, `project`, `review_job_id`, `create_revision_tasks?`, `create_rule_proposals?`, `block_on_critical?` | write | 从审核学习 |
| `workflow.list_audit_logs` | `workspace`, `project`, `action?`, `resource_type?`, `limit?` | read | 审计日志 |
| `workflow.get_chapter_generation_prompt` | `workspace`, `project`, `chapter_no`, `focus?`, `volume_no?`, `pov_mode?`, `pass_number?` | read | 生成章节完整 Prompt |
| `workflow.start_chapter_generation` | `workspace`, `project`, `chapter_no`, `focus?`, `volume_no?`, `pov_mode?` | read | 启动分步生成 |
| `workflow.next_step` | `session_id`, `result?` | read | 推进工作流 |
| `workflow.jump_to_step` | `session_id`, `step_no` | read | 跳至指定步骤 |
| `workflow.get_current_step` | `session_id` | read | 获取当前步骤 |
| `workflow.pause_session` | `session_id` | read | 暂停会话 |
| `workflow.resume_session` | `session_id` | read | 恢复会话 |
| `workflow.list_sessions` | `workspace`, `project` | read | 列出工作流会话 |
| `workflow.abort_chapter_generation` | `session_id` | read | 中止生成 |
| `chapter.reset` | `workspace`, `project`, `chapter_no`, `keep_entities?` | write | 重置章节数据 |
| `project.reset` | `workspace`, `project`, `keep_entities?`, `delete_local_files?` | write | 重置整个项目 |
| `context.list_packs` | `workspace`, `project`, `chapter_no?`, `purpose?`, `limit?` | read | 列出上下文包 |
| `context.get_pack` | `workspace`, `project`, `context_pack_id?`, `chapter_no?` | read | 获取上下文包 |

## 42. Character Arc (`novel_gen.py`)

| 工具名 | 参数 | 权限 | 说明 |
|-------|------|------|------|
| `arc.record_emotion` | `workspace`, `project`, `project_id`, `character_name`, `chapter_no`, `emotion`, `intensity`, `cause?` | write | 记录情绪变化 |
| `arc.record_relationship` | `workspace`, `project`, `project_id`, `character_name`, `chapter_no`, `target_name`, `old_relation`, `new_relation`, `cause?` | write | 记录关系变化 |
| `arc.record_power` | `workspace`, `project`, `project_id`, `character_name`, `chapter_no`, `old_level`, `new_level`, `method?`, `note?` | write | 记录实力变化 |
| `arc.record_personality` | `workspace`, `project`, `project_id`, `character_name`, `chapter_no`, `trait`, `old_value`, `new_value`, `reason?` | write | 记录性格变化 |
| `arc.record_point` | `workspace`, `project`, `project_id`, `character_name`, `chapter_no`, `point_type`, `description`, `intensity?` | write | 记录弧光节点 |
| `arc.get_character` | `workspace`, `project`, `character_name` | read | 获取角色弧光 |
| `arc.get_latest_state` | `workspace`, `project`, `character_name` | read | 获取最新状态 |
| `arc.get_emotion_timeline` | `workspace`, `project`, `character_name`, `limit?` | read | 情绪时间线 |
| `arc.get_power_progression` | `workspace`, `project`, `character_name` | read | 实力进阶路线 |
| `arc.get_relationship_evolution` | `workspace`, `project`, `character_name`, `target_name` | read | 关系演变 |
| `arc.get_summary_for_context` | `workspace`, `project`, `character_name`, `current_chapter_no?` | read | 角色上下文摘要 |

## 43. Causality (`novel_gen.py`)

| 工具名 | 参数 | 权限 | 说明 |
|-------|------|------|------|
| `causality.record` | `workspace`, `project`, `project_id`, `cause_chapter_no`, `effect_chapter_no`, `description`, `cause_type?`, `effect_type?`, `strength?`, `tags?` | write | 记录因果关系 |
| `causality.record_chain` | `workspace`, `project`, `project_id`, `chain_id`, `chapters`, `summaries`, `chain_type?`, `tags?` | write | 记录因果链 |
| `causality.get_forward` | `workspace`, `project`, `chapter_no`, `limit?` | read | 前向因果 |
| `causality.get_backward` | `workspace`, `project`, `chapter_no`, `limit?` | read | 后向因果 |
| `causality.get_in_range` | `workspace`, `project`, `from_chapter`, `to_chapter`, `limit?` | read | 范围因果 |
| `causality.find_unresolved` | `workspace`, `project`, `limit?` | read | 未解决的因果 |
| `causality.find_dangling` | `workspace`, `project`, `limit?` | read | 悬空因果 |
| `causality.get_summary` | `workspace`, `project`, `chapter_no` | read | 因果摘要 |

## 44. Novelty Check (`novel_gen.py`)

| 工具名 | 参数 | 权限 | 说明 |
|-------|------|------|------|
| `novelty.check_scene` | `workspace`, `project`, `content`, `context?` | read | 场景新颖度检测 |
| `novelty.check_description` | `workspace`, `project`, `content`, `context?` | read | 描写新颖度检测 |
| `novelty.check_dialogue` | `workspace`, `project`, `content`, `context?` | read | 对话新颖度检测 |
| `novelty.check_plot_beats` | `workspace`, `project`, `content`, `context?` | read | 情节节奏新颖度 |
| `novelty.full_check` | `workspace`, `project`, `content`, `chapter_no?` | read | 全面新颖度检测 |

## 45. Pacing (`novel_gen.py`)

| 工具名 | 参数 | 权限 | 说明 |
|-------|------|------|------|
| `pacing.create_blueprint` | `workspace`, `project`, `project_id`, `blueprint`, `title?`, `description?` | write | 创建节奏蓝图 |
| `pacing.get_blueprint` | `workspace`, `project`, `project_id`, `blueprint_id?` | read | 获取节奏蓝图 |
| `pacing.list_blueprints` | `workspace`, `project`, `project_id` | read | 列出节奏蓝图 |
| `pacing.record_emotion` | `workspace`, `project`, `project_id`, `chapter_no`, `tension`, `emotion`, `emotion_intensity?`, `pacing_type?` | write | 记录情绪节奏 |
| `pacing.get_emotion` | `workspace`, `project`, `chapter_no?`, `limit?` | read | 获取情绪数据 |
| `pacing.get_curve` | `workspace`, `project`, `from_chapter?`, `to_chapter?` | read | 情绪曲线 |
| `pacing.analyze_rhythm` | `workspace`, `project`, `chapter_no`, `content` | read | 分析节奏 |
| `pacing.check_health` | `workspace`, `project`, `current_chapter_no?` | read | 节奏健康检查 |
| `pacing.compare_blueprint` | `workspace`, `project`, `project_id`, `blueprint_id`, `current_chapter_no?` | read | 对比蓝图 |
| `pacing.predict_engagement` | `workspace`, `project`, `from_chapter?`, `to_chapter?` | read | 预测读者参与度 |
| `pacing.get_summary` | `workspace`, `project`, `chapter_no` | read | 节奏摘要 |

## 46. Style Fingerprint (`novel_gen.py`)

| 工具名 | 参数 | 权限 | 说明 |
|-------|------|------|------|
| `style.create_profile` | `workspace`, `project`, `project_id`, `profile_name`, `base_chapters?`, `style_params?` | write | 创建风格指纹 |
| `style.get_profile` | `workspace`, `project`, `project_id?`, `profile_name?` | read | 获取风格指纹 |
| `style.analyze_chapter` | `workspace`, `project`, `project_id?`, `chapter_no`, `content`, `profile_name?` | write | 分析章节风格 |
| `style.get_chapter` | `workspace`, `project`, `chapter_no` | read | 获取章节风格 |
| `style.detect_drift` | `workspace`, `project`, `project_id?`, `chapter_no`, `content`, `profile_name?`, `threshold?` | read | 检测风格漂移 |
| `style.batch_analyze` | `workspace`, `project`, `project_id?`, `chapter_nos`, `profile_name?` | write | 批量分析 |
| `style.get_trend` | `workspace`, `project`, `project_id?`, `from_chapter?`, `to_chapter?` | read | 风格趋势 |
| `style.get_summary` | `workspace`, `project`, `project_id?`, `profile_name?` | read | 风格摘要 |

## 47. Pipeline (`novel_gen.py`)

| 工具名 | 参数 | 权限 | 说明 |
|-------|------|------|------|
| `pipeline.create_plan` | `workspace`, `project`, `chapter_no`, `plan` | write | 创建生成计划 |
| `pipeline.get_plan` | `workspace`, `project`, `chapter_no` | read | 获取生成计划 |
| `pipeline.record_pass` | `workspace`, `project`, `chapter_no`, `pass_type`, `pass_number`, `model_key?`, `input_tokens?`, `output_tokens?`, `metadata?` | write | 记录生成 pass |
| `pipeline.get_passes` | `workspace`, `project`, `chapter_no`, `pass_type?` | read | 获取 pass 记录 |
| `pipeline.check_continuity` | `workspace`, `project`, `from_chapter`, `to_chapter` | read | 检查连续性 |
| `pipeline.run_full` | `workspace`, `project`, `chapter_no`, `plan?`, `draft_content?`, `polish_content?`, `review_notes?` | write | 记录完整流水线 |
| `pipeline.status` | `workspace`, `project`, `chapter_no` | read | 流水线状态 |
| `pipeline.multi_review` | `workspace`, `project`, `chapter_no`, `models`, `content`, `dimensions?` | write | 多模型审核 |
| `pipeline.generate` | `workspace`, `project`, `chapter_no`, `task_type`, `summary?`, `content?`(废弃别名), `user_prompt?`, `system_prompt?`, `temperature?`, `max_tokens?` | write | 单次 LLM 生成；`summary` 上限 200 字，正文全文不入库 |


## 48. Graph (`graph.py`)

| 工具名 | 参数 | 权限 | 说明 |
|-------|------|------|------|
| `graph.get_data` | `workspace`, `project`, `entity_types?`, `depth?` | read | 获取关系图数据 |
| `graph.get_subgraph` | `workspace`, `project`, `center_entity`, `depth?` | read | 获取子图 |
| `graph.get_timeline` | `workspace`, `project`, `entity_name` | read | 获取关系时间线 |

## 49. Skills (`skill.py`)

| 工具名 | 参数 | 权限 | 说明 |
|-------|------|------|------|
| `skill.list` | `active_only?` | read | 列出所有 skill |
| `skill.get` | `skill_id` | read | 获取 skill 详情 |
| `skill.get_by_name` | `name` | read | 通过名称获取 |
| `skill.create` | `name`, `description?`, `content?`, `trigger_words?`, `tool_hints?`, `sort_order?` | write | 创建 skill |
| `skill.update` | `skill_id`, `name?`, `description?`, `content?`, `trigger_words?`, `tool_hints?`, `is_active?`, `sort_order?` | write | 更新 skill |
| `skill.delete` | `skill_id` | write | 删除 skill |
| `skill.step.list` | `skill_id` | read | 列出步骤 |
| `skill.step.add` | `skill_id`, `step_order`, `action_type`, `params?`, `description?`, `required?` | write | 添加步骤 |
| `skill.step.update` | `step_id`, `step_order?`, `action_type?`, `params?`, `description?`, `required?` | write | 更新步骤 |
| `skill.step.delete` | `step_id` | write | 删除步骤 |

## 50. Evolution (`evolution.py`)

| 工具名 | 参数 | 权限 | 说明 |
|-------|------|------|------|
| `evolution.logs` | `source_type?`, `risk_level?`, `target_table?`, `limit?` | read | 列出进化日志 |
| `evolution.rollback` | `log_id` | admin | 回滚进化记录 |
| `evolution.stats` | — | read | 进化统计 |

## 51. Novel Wizard (`novel_wizard.py`)

`novel_wizard.py` 共注册 **11 个工具**：本节 6 个 `novel.wizard.*` + §53 的 5 个 `tone.*`。

| 工具名 | 参数 | 权限 | 说明 |
|-------|------|------|------|
| `novel.wizard.start` | — | read | 启动小说创建向导，返回 `wizard_id` 与问题列表（基调选项来自 `ref_tones`） |
| `novel.wizard.generate` | `wizard_id`, `answers` | read | 提交向导答案，生成项目预览（早期文档记作 `novel.wizard.submit`，已改名） |
| `novel.wizard.commit` | `wizard_id`, `workspace`, `project_slug`, `preview`, `confirm?`, `workspace_action?`, `workspace_name?`, `selected_configs?` | write | 确认并创建小说项目（建项目、首卷、按基调生成初始规则） |
| `novel.wizard.get_deepen_suggestions` | `workspace`, `project`, `project_id` | read | commit 后获取设定深化建议，返回按 section 分组的深化任务 |
| `novel.wizard.build_world` | `workspace`, `project` | read | 全自动世界构建流程（commit 后调用，替代 `get_deepen_suggestions`），返回 4 阶段构建计划 |
| `novel.wizard.submit_knowledge_proposals` | `workspace`, `project`, `proposals` | write | 把 AI 推荐且被采纳的知识提交为进化提案，等待管理员审批 |

> ⚠️ `novel.wizard.status` 并不存在，早期文档有记载，请以源码为准。
> 同文件注册的 `tone.*` 5 个工具见 [§53 Tone Management](#53-tone-management-novel_wizardpy)。

## 52. Archive & Compression (`archive.py`)

| 工具名 | 参数 | 权限 | 说明 |
|-------|------|------|------|
| `archive.volume` | `workspace`, `project`, `volume_no`, `reason?` | write | 归档卷 |
| `archive.restore` | `workspace`, `project`, `volume_no` | write | 恢复卷 |
| `archive.volume_status` | `workspace`, `project`, `volume_no` | read | 卷归档状态 |
| `archive.history` | `workspace`, `project`, `limit?` | read | 归档历史 |
| `archive.schedule.create` | `workspace`, `project`, `volume_no`, `schedule_type?`, `at_conditions?`, `expire_days?` | write | 创建归档计划 |
| `archive.schedule.list` | `workspace`, `project` | read | 列出归档计划 |
| `archive.tier_config.get` | `workspace`, `project` | read | 分层配置 |
| `archive.auto_archive` | `workspace`, `project`, `current_volume_no`, `current_chapter_no?` | write | 自动归档 |
| `archive.get_stats` | `workspace`, `project` | read | 归档统计 |
| `context.compression.compress_chapters` | `workspace`, `project`, `chapter_nos`, `target_time?`, `strategy?` | write | 压缩章节上下文 |
| `context.compression.compress_arc` | `workspace`, `project`, `from_chapter`, `to_chapter`, `title?` | write | 压缩弧光上下文 |
| `context.compression.compress_volume` | `workspace`, `project`, `volume_no`, `title?` | write | 压缩卷上下文 |
| `context.compression.compress_series` | `workspace`, `project`, `title?` | write | 压缩系列上下文 |
| `context.compression.get_compressed` | `workspace`, `project`, `target_type?`, `target_id?`, `level?` | read | 获取压缩结果 |
| `context.compression.auto_compress` | `workspace`, `project`, `chapter_no`, `strategy?` | write | 自动压缩 |
| `context.compression.list` | `workspace`, `project`, `target_type?`, `level?`, `limit?` | read | 列出压缩记录 |

## 53. Tone Management (`novel_wizard.py`)

> 故事基调（情绪底色）及其关联创作规则。数据模型与消费链路见 [03-backend/tone-system.md](../tone-system.md)。
> 建表 SQL 见 `deploy/nas/postgres/migrations/222_runtime_tables.sql`。

| 工具名 | 参数 | 权限 | 说明 |
|-------|------|------|------|
| `tone.list` | — | read | 列出所有基调，每条附带 `rules` 数组 |
| `tone.upsert` | `slug`, `name`, `description?`, `is_active?`, `sort_order?` | admin | 按 `slug` 冲突更新 |
| `tone.delete` | `slug` | admin | 删除基调及其所有关联规则（工具内显式级联） |
| `tone.rule.upsert` | `tone_slug`, `rule_type`, `title`, `content`, `severity?`, `sort_order?`, `rule_id?` | admin | 传 `rule_id` 更新，否则新建 |
| `tone.rule.delete` | `rule_id` | admin | 删除单条基调规则 |

---

*最后更新: 2026-10-11 | 来源: novel-os-mcp/src/novel_os_mcp/tools/*.py*
