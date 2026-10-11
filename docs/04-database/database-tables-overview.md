# 数据库表总览

> **数据库**: `novel_os` / **用户**: `novel_os` / **扩展**: `vector` (pgvector)、`pg_trgm`、`uuid-ossp`
>
> 共 112 张表，按业务域分类如下。

---

## 目录

1. [Core Story（核心故事）— 10 张表](#1-core-story核心故事--10-张表)
2. [User & Workspace（用户与工作区）— 8 张表](#2-user--workspace用户与工作区--8-张表)
3. [Review & Analysis（审阅与分析）— 6 张表](#3-review--analysis审阅与分析--6-张表)
4. [Plot & Planning（情节与规划）— 5 张表](#4-plot--planning情节与规划--5-张表)
5. [Knowledge Base（知识库）— 15 张表](#5-knowledge-base知识库--15-张表)
6. [Genre & Style（题材与风格）— 7 张表](#6-genre--style题材与风格--7-张表)
7. [Character & Plot Analysis（角色与情节分析）— 3 张表](#7-character--plot-analysis角色与情节分析--3-张表)
8. [Context & Content（上下文与内容）— 12 张表](#8-context--content上下文与内容--12-张表)
9. [System & Evolution（系统与演进）— 5 张表](#9-system--evolution系统与演进--5-张表)
10. [Settings（设置）— 5 张表](#10-settings设置--5-张表)
11. [Model & Cost（模型与成本）— 3 张表](#11-model--cost模型与成本--3-张表)
12. [Operations（运维）— 8 张表](#12-operations运维--8-张表)
13. [Vector & Search（向量与搜索）— 5 张表](#13-vector--search向量与搜索--5-张表)
14. [Audit & Evolution（审计与演进）— 3 张表](#14-audit--evolution审计与演进--3-张表)
15. [Offline & Misc（离线与杂项）— 8 张表](#15-offline--misc离线与杂项--8-张表)
16. [Local（本地）— 6 张表](#16-local本地--6-张表)

---

## 1. Core Story（核心故事）— 10 张表

| # | 表名 | 用途 |
|---|------|------|
| 1 | `projects` | 项目定义：名称、描述、目标字数、默认流派、状态、当前章节号 |
| 2 | `chapters` | 章节定义：所属项目+卷、编号、标题、字数、状态、正文摘要 |
| 3 | `chapter_summaries` | 章节遥梗内容：主要事件、角色登场、情感走向、关键词 |
| 4 | `chapter_commits` | 章节版本控制：每次保存的完整快照（正文+元数据），支持 diff 与回滚 |
| 5 | `events` | 故事事件：发生于某章、涉及角色、事件类型、摘要、时间线位置 |
| 6 | `characters` | 故事角色：名称、别名、角色类型、性格特征、外貌、简介、所属派系 |
| 7 | `character_states` | 角色快照（按章节）：外观、位置、关系、动机、知识状态变化 |
| 8 | `canon_rules` | 世界规则/设定法：规则内容、类型、适用世界/种族、依赖规则 |
| 9 | `rule_versions` | canon_rules 版本历史，支持版本对比和回滚 |
| 10 | `foreshadowing` | 伏笔管理：伏笔标题、层级、重要性、是否必须回收、回收截止章节 |

---

## 2. User & Workspace（用户与工作区）— 8 张表

| # | 表名 | 用途 |
|---|------|------|
| 1 | `users` | 用户账户：用户名、密码散列、显示名、邮箱、角色、状态、备注 |
| 2 | `workspaces` | 工作区：名称、描述、所有者、创建时间、可见性设置 |
| 3 | `workspace_members` | 工作区成员：用户-工作区关联、角色（owner/admin/member/viewer） |
| 4 | `project_members` | 项目成员：用户-项目关联、角色（owner/editor/viewer） |
| 5 | `api_tokens` | 用户 API 令牌：令牌散列、名称、权限范围、过期时间、最后使用 |
| 6 | `local_project_bindings` | 本地项目绑定：本地项目 ID ↔ 服务器项目 ID 的映射关系 |
| 7 | `state_entities` | **故事运行态实体**：角色/location/faction/物品等实体，含摘要、描述、档案、别名、标签、重要性、生命周期状态、首次/最后出场章节 |
| 8 | `state_snapshots` | **实体状态快照**：按章节记录实体的摘要、描述、档案、外观、关系、动机变化 |

---

## 3. Review & Analysis（审阅与分析）— 6 张表

| # | 表名 | 用途 |
|---|------|------|
| 1 | `review_jobs` | 审阅任务：目标章节/章节区间、审阅维度、模式、状态、使用的模型配置 |
| 2 | `review_reports` | 审阅报告：每个维度的问题列表、建议、严重程度、相关原文引用 |
| 3 | `review_council_configs` | 众议审阅配置：多个审阅者（AI 角色）的权重、审查维度、聚合规则 |
| 4 | `revision_tasks` | 修改任务：关联审阅报告、状态、负责人、截止时间 |
| 5 | `revision_task_history` | 修改任务历史：状态变更、操作日志 |
| 6 | `review_model_metrics` | 审阅模型度量：各模型/角色的审阅准确率、误报率、响应时间 |

---

## 4. Plot & Planning（情节与规划）— 5 张表

| # | 表名 | 用途 |
|---|------|------|
| 1 | `volumes` | 卷定义：编号、标题、描述、目标章节数、状态、起始/结束章节 |
| 2 | `plot_threads` | 情节线：名称、所属项目、状态、优先级、依赖情节线、当前进度描述 |
| 3 | `chapter_plans` | 章节计划/大纲：所属章节、计划内容、状态、上一章计划 ID（形成计划链） |
| 4 | `chapter_annotations` | 章节注释：读者/编辑标记、问题定位、灵感记录 |
| 5 | `compressed_contexts` | 压缩上下文：大量历史章节的摘要压缩，供长上下文场景复用 |

---

## 5. Knowledge Base（知识库）— 15 张表

| # | 表名 | 用途 |
|---|------|------|
| 1 | `categories` | 知识分类：名称、父分类、描述、排序、项目+工作区范围 |
| 2 | `tags` | 知识标签：名称、颜色、所属项目/工作区 |
| 3 | `knowledge_base` | 项目知识条目：标题、内容、分类、状态、版本、来源 |
| 4 | `knowledge_tags` | 知识-标签多对多关联 |
| 5 | `knowledge_vectors` | 知识条目的向量嵌入（pgvector），用于语义搜索 |
| 6 | `user_knowledge` | 用户私有知识：用户级知识条目，跨项目复用 |
| 7 | `knowledge_review` | 知识审阅队列：待审核的知识条目，审核状态、审核人、意见 |

---

| # | 表名 | 用途 |
|---|------|------|
| 8 | `ref_categories` | 引文分类：参考文献的目录结构 |
| 9 | `knowledge_entities` | 知识实体（旧版）：名称、类型、摘要、别名、档案，与 `kb.pk.*` 工具对应 |
| 10 | `knowledge_relations` | 知识实体关系：源实体、目标实体、关系类型、强度 |
| 11 | `universal_knowledge` | 通用知识（UK）：跨项目共享的知识卡片，含 embedding、来源 URL、引用 |
| 12 | `project_knowledge` | 项目知识包：项目关联的知识模板/卡片集合 |
| 13 | `world_snapshots` | 世界快照：某时间点的完整世界观设定快照，含 JSONB 数据 |
| 14 | `ref_search_jobs` | 引文搜索任务：联网搜索知识并存入 UK 的任务记录 |
| 15 | `ref_gap_logs` | 知识缺口日志：检测到的知识缺失及其处理结果 |

---

## 6. Genre & Style（题材与风格）— 7 张表

| # | 表名 | 用途 |
|---|------|------|
| 1 | `genre_canonical` | 规范流派定义：流派名称、关键词、典型模式、适用知识策略 |
| 2 | `genre_knowledge_config` | 流派知识配置：每个流派对应的知识获取策略、URL 模板、搜索提示 |
| 3 | `project_knowledge_pack` | 项目知识包：项目使用的知识模板集合，关联 genre_canonical |
| 4 | `style_profiles` | 风格档案：写作风格参数（句式、节奏、用词、修辞偏好） |
| 5 | `chapter_style_metrics` | 章节风格度量：每章的实际风格指标（可读性、节奏得分、情感曲线） |
| 6 | `pacing_blueprints` | 节奏蓝图：章节/卷级别的节奏规划（高潮点、低谷、过渡） |
| 7 | `chapter_emotions` | 章节情感标注：每章的情感标签、强度、位置（开头/中间/结尾） |

---

## 7. Character & Plot Analysis（角色与情节分析）— 3 张表

| # | 表名 | 用途 |
|---|------|------|
| 1 | `character_arcs` | 角色弧线：角色发展曲线、转折点章节、成长指标 |
| 2 | `causality_chains` | 因果链：事件间因果关系、前因事件、后果事件、因果强度 |
| 3 | `generation_passes` | 生成流程记录：多轮生成（草稿→审阅→修订）的每轮输入输出 |

---

## 8. Context & Content（上下文与内容）— 12 张表

| # | 表名 | 用途 |
|---|------|------|
| 1 | `context_packs` | 上下文打包：将相关知识、角色、设定打包为生成用上下文 |
| 2 | `reference_sources` | 参考来源：外部参考文档的元信息（文件名、类型、上传时间） |
| 3 | `reference_items` | 参考条目：从参考来源中提取的片段/段落 |
| 4 | `reference_materials` | 参考资料：写作参考材料的内容存储 |
| 5 | `prompt_templates` | 提示词模板：名称、类别、系统提示、用户提示模板、参数 |
| 6 | `prompt_template_versions` | 模板版本：每次修改的记录，支持回滚和 A/B 对比 |
| 7 | `prompt_template_usage_logs` | 模板使用日志：调用时间、渲染结果快照、使用的参数值 |
| 8 | `context_weight_configs` | 上下文权重配置：不同类型上下文（角色/设定/前文）的权重分配 |
| 9 | `reader_expectations` | 读者预期管理（已废弃，请使用 `foreshadowing` 代替） |
| 10 | `chapter_versions` | 章节生成版本：AI 多轮生成的多版本内容对比 |
| 11 | `writing_stats` | 写作统计：日/周/月写作字数、时间、修改次数 |
| 12 | `proper_nouns` | 专有名词表：统一术语、人名、地名、物品名及其一致性检查 |

---

## 9. System & Evolution（系统与演进）— 5 张表

| # | 表名 | 用途 |
|---|------|------|
| 1 | `system_evolution_proposals` | 系统演进提案：功能建议、投票、采纳状态 |
| 2 | `system_style_profiles` | 系统级写作风格：全局默认风格参数 |
| 3 | `system_prompt_templates` | 系统级提示词模板：全局默认模板 |
| 4 | `system_model_profiles` | 系统级模型配置：全局默认模型参数 |
| 5 | `system_notifications` | 系统通知：广播通知、目标用户、已读状态 |

---

## 10. Settings（设置）— 5 张表

| # | 表名 | 用途 |
|---|------|------|
| 1 | `setting_categories` | 设置分类：系统→项目→用户，树形结构 |
| 2 | `setting_field_definitions` | 字段定义：字段名、类型、默认值、验证规则、UI 控件类型 |
| 3 | `setting_items` | 设置项值：实际的 key-value 配置 |
| 4 | `setting_category_relations` | 分类关联：setting_categories 之间的层次/依赖关系 |
| 5 | `global_rules` | 全局规则：跨项目的写作规则、审核规则、设定约束 |

---

## 11. Model & Cost（模型与成本）— 3 张表

| # | 表名 | 用途 |
|---|------|------|
| 1 | `model_profiles` | 模型配置：模型名称、endpoint、参数（temperature/top_p/max_tokens）、用途标签 |
| 2 | `model_route_rules` | 路由规则：根据任务类型/复杂度/成本选择不同模型的规则 |
| 3 | `model_usage_records` | 用量记录：每次调用使用的 token 数、成本、响应时间 |

---

## 12. Operations（运维）— 8 张表

| # | 表名 | 用途 |
|---|------|------|
| 1 | `backup_records` | 备份记录：备份类型（全量/增量）、文件路径、大小、校验和 |
| 2 | `backup_schedules` | 备份计划：定时备份策略（interval、保留份数、目标位置） |
| 3 | `restore_records` | 恢复记录：恢复操作日志、来源备份、恢复状态 |
| 4 | `archives` | 归档记录：项目/章节归档 |
| 5 | `archive_items` | 归档条目：归档包含的具体文件/章节列表 |
| 6 | `archive_schedules` | 归档计划：自动归档策略 |
| 7 | `archive_history` | 归档历史：归档操作的详细记录、状态、文件列表 |
| 8 | `project_export_records` | 项目导出记录：完整项目数据的导出历史、格式、文件大小 |

---

## 13. Vector & Search（向量与搜索）— 5 张表

| # | 表名 | 用途 |
|---|------|------|
| 1 | `memory_chunks` | 记忆分块：文本块及其向量嵌入，用于 RAG |
| 2 | `vector_index_jobs` | 向量索引任务：批量索引构建/更新任务 |
| 3 | `vector_index_tasks` | 向量索引发任务：每块文本的索引操作记录 |
| 4 | `vector_index_status` | 索引状态：各表的向量索引覆盖率、最新索引时间 |
| 5 | `vector_index_config` | 索引配置：分块策略、embedding 模型、相似度算法 |

---

## 14. Audit & Evolution（审计与演进）— 3 张表

| # | 表名 | 用途 |
|---|------|------|
| 1 | `audit_logs` | 审计日志：所有关键操作的用户、时间、操作类型、旧值/新值 |
| 2 | `evolution_logs` | 演进日志：系统/项目自动演进的决策记录（如自动调整规则权重） |
| 3 | `memory_chunk_index_history` | 记忆分块索引历史：chunk 的索引变更历史 |

---

## 15. Offline & Misc（离线与杂项）— 8 张表

| # | 表名 | 用途 |
|---|------|------|
| 1 | `offline_sync_sessions` | 离线同步会话：设备信息、最后同步时间、冲突处理策略 |
| 2 | `offline_change_queue` | 离线变更队列：离线期间累积的增删改操作，联网后批量执行 |
| 3 | `voice_drafts` | 语音草稿：语音输入的原始音频存储和转写文本 |
| 4 | `relationship_graph_configs` | 关系图配置：角色关系图的布局、筛选、展示参数 |
| 5 | `template_marketplace` | 模板市场：社区/系统提供的可复用模板（提示词、风格、知识包） |
| 6 | `automated_test_results` | 自动化测试结果：规则一致性检查、章节质量检查的批量结果 |
| 7 | `performance_test_results` | 性能测试结果：响应时间、吞吐量、内存使用的历史记录 |
| 8 | `fulltext_search_records` | 全文搜索记录：搜索日志、热门查询、无结果查询分析 |

---

## 16. Local（本地）— 6 张表

| # | 表名 | 用途 |
|---|------|------|
| 1 | `local_projects` | 本地项目元信息：路径、名称、最后同步时间、数据层级 |
| 2 | `chapter_index` | 本地章节索引：本地文件 ↔ 服务器章节 ID 的映射 |
| 3 | `setting_index` | 本地设置索引：本地设置 ↔ 服务器 setting_items 的映射 |
| 4 | `review_index` | 本地审阅索引：本地审阅记录 ↔ 服务器 review_reports 的映射 |
| 5 | `data_tier_config` | 数据分层配置：本地/服务器/云各层的数据存储策略 |
| 6 | `volume_archive_status` | 卷归档状态：本地与服务器归档同步状态 |

---

> **最后更新**: 2026-07-28