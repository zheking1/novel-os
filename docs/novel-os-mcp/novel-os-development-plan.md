# Novel OS 开发计划

> 版本：v1.0  
> 日期：2026-06-28  
> 状态：正式开发计划  
> 基于：novel-os-requirements.md、development-plan.md、global-settings-optimization-plan.md

---

## 1. 总体概述

### 1.1 开发目标

构建一个支持 2000 万字规模超长篇网络小说创作的 AI 辅助管理系统，包括：
- MCP 服务：小说长期数据和规则中枢
- Web 控制台：小说数据维护后台
- 本地 AI Skill：小说初始化和写作入口

### 1.2 开发原则

1. **数据先行**：先补数据模型，再补 MCP 工具，再改 Web 页面，最后接入本地 skill
2. **渐进式交付**：每个阶段都有可验证的交付物
3. **不破坏现有数据**：所有迁移必须可重复执行，不破坏已有工作区、项目、规则、伏笔数据
4. **测试驱动**：每个功能完成后必须有冒烟测试
5. **文档同步**：每完成一个任务，必须同步更新开发计划和相关文档

### 1.3 技术栈

| 层级 | 技术 |
|------|------|
| MCP 服务 | Python + FastMCP |
| 数据库 | PostgreSQL + pgvector + Qdrant + Redis |
| Web 控制台 | React + TypeScript + Vite |
| 本地 AI Skill | TypeScript + Codex Skill 框架 |
| 部署 | Docker Compose |

### 1.4 阶段总览

| 阶段 | 名称 | 目标 | 优先级 |
|------|------|------|--------|
| Phase 0 | 基础部署与基线 | NAS 基础服务、MCP 初版、Web 初版 | ✅ 已完成 |
| Phase 1 | P0 数据模型与迁移 | 补齐支撑小说长期数据维护的表结构 | ✅ 已完成 |
| Phase 2 | P0 MCP 核心工具 | 实现 Web 和本地 skill 都能调用的数据维护工具 | ✅ 已完成 |
| Phase 3 | Web 数据维护台 | 将 Web 从调试台升级为小说数据后台 | ✅ 已完成 |
| Phase 4 | 本地 AI Skill 对接 | 让本地 AI 工具成为实际写作入口 | ✅ 已完成 |
| Phase 5 | 审查闭环与规则演化 | 把审查从"报告"变成"长期改进系统" | ✅ 已完成 |
| Phase 6 | 性能、容灾与运维 | 保证 NAS 长期运行、可恢复、可观测 | ✅ 已完成 |
| Phase 7 | P1 创作效率增强 | 批量工具、商业看板、协作批注、Prompt 模板 | ✅ 已完成 |
| Phase 8 | P2 远期扩展 | 分布式、图谱、模板市场、增强离线 | ✅ 已完成 |

---

## 2. Phase 1：P0 数据模型与迁移

### 2.1 阶段目标

补齐能支撑小说长期数据维护的表结构，为 Phase 2 的 MCP 工具打好基础。

### 2.2 任务清单

#### 1.1 Canon 文档表
- **状态**：✅ 已完成
- **交付物**：
  - 迁移 SQL：`deploy/nas/postgres/init/090_canon_documents.sql`
  - 新增表：`canon_documents`、`canon_document_versions`
- **验收标准**：
  - 同一项目内 `doc_type + key` 唯一
  - 修改 active Canon 自动生成版本
  - 迁移脚本可重复执行
- **完成时间**：2026-06-25
- **验证**：NAS 已执行迁移，schema 验证通过

#### 1.2 实体关系表
- **状态**：✅ 已完成
- **交付物**：
  - 迁移 SQL：`deploy/nas/postgres/init/130_entity_relationships.sql`
  - 新增表：`entity_relationships`
  - 扩展表：`state_entities`（增加生命周期字段）
- **验收标准**：
  - 支持人物、势力、地点、道具之间的关系
  - 关系有可见性字段（known_by_source/target/reader）
  - 关系有状态（active/hidden/broken/resolved）
- **完成时间**：2026-06-26
- **验证**：NAS schema 验证通过

#### 1.3 状态时效字段
- **状态**：✅ 已完成
- **交付物**：
  - 迁移 SQL：`deploy/nas/postgres/init/100_state_snapshot_lifecycle.sql`
  - 扩展表：`state_snapshots`（增加生命周期字段）
- **验收标准**：
  - 状态有生效/过期章节和卷
  - 支持临时状态和永久状态
  - 状态有置信度和来源追踪
- **完成时间**：2026-06-26
- **验证**：NAS schema 验证通过

#### 1.4 伏笔关联字段
- **状态**：✅ 已完成
- **交付物**：
  - 迁移 SQL：`deploy/nas/postgres/init/110_foreshadowing_links.sql`
  - 扩展表：`foreshadowing`（增加关联、层级、回收截止字段）
- **验收标准**：
  - 支持父子伏笔
  - 支持明线/暗线/幕后伏笔分层
  - 支持回收截止和逾期策略
- **完成时间**：2026-06-26
- **验证**：NAS schema 验证通过

#### 1.5 规则作用域与临时规则字段
- **状态**：✅ 已完成
- **交付物**：
  - 迁移 SQL：`deploy/nas/postgres/init/120_rule_scope_lifecycle.sql`
  - 扩展表：`canon_rules`（增加范围、优先级、冲突策略字段）
- **验收标准**：
  - 规则支持全局/分卷/剧情线/章节/角色等多种作用范围
  - 支持临时规则和事件触发
  - 支持规则优先级和冲突策略
- **完成时间**：2026-06-26
- **验证**：NAS schema 验证通过

#### 1.6 剧情线进度字段
- **状态**：✅ 已完成
- **交付物**：
  - 迁移 SQL：`deploy/nas/postgres/init/140_plot_thread_progress.sql`
  - 扩展表：`plot_threads`（增加进度字段）
  - 新增表：`volumes`（如不存在）
- **验收标准**：
  - 剧情线有当前阶段和最后推进章节
  - 支持停滞检测阈值
  - 卷有状态管理
- **完成时间**：2026-06-26
- **验证**：NAS schema 验证通过

#### 1.7 模型与成本表
- **状态**：✅ 已完成
- **交付物**：
  - 迁移 SQL：`deploy/nas/postgres/init/150_model_cost.sql`
  - 新增表：`model_profiles`、`model_route_rules`、`model_usage_records`
- **验收标准**：
  - 模型有分层（cheap/standard/premium/local）
  - 支持路由规则和 fallback
  - 支持 token 成本统计
- **完成时间**：2026-06-27
- **验证**：NAS 冒烟测试通过

#### 1.8 全局设定系统表
- **状态**：✅ 已完成
- **交付物**：
  - 迁移 SQL：`deploy/nas/postgres/init/160_global_settings.sql`
  - 新增表：
    - `setting_categories`（设定分类）
    - `setting_field_definitions`（分类字段定义）
    - `setting_items`（设定项目，含 BM25 字段）
    - `genre_canonical`（题材规范化）
    - `setting_category_relations`（分类关联）
- **验收标准**：
  - 预设 9 个标准分类
  - setting_items 包含 BM25 检索字段（keywords、intent_synonyms、core_summary、detailed_expansion）
  - setting_items 包含 AI 专用字段（ai_instruction、poison_points）
  - setting_items 包含分层与权重字段（level、applicable_skills、applicable_genres）
  - 预设 15 个 canonical genre
  - 所有新表有索引
  - 迁移脚本可重复执行
- **完成时间**：2026-06-28
- **验证**：NAS 部署测试通过，9 个分类、15 个题材、6 条示例数据、BM25 搜索、题材规范化均正常

### 2.3 阶段门禁

进入 Phase 2 前必须确认：
- ✅ 所有 P0 表结构创建完成
- ✅ 迁移脚本可重复执行
- ✅ 索引创建完成
- ✅ 数据完整性约束生效
- ✅ 不破坏已有工作区、项目、规则、伏笔、审查任务数据

---

## 3. Phase 2：P0 MCP 核心工具

### 3.1 阶段目标

实现 Web 和本地 skill 都能调用的数据维护工具，形成完整的 MCP 工具层。

### 3.2 任务清单

#### 2.1 Canon 工具
- **状态**：✅ 已完成
- **交付物**：
  - Service 方法：`CanonService`
  - MCP 工具：
    - `canon.doc.upsert`
    - `canon.doc.list`
    - `canon.doc.get`
    - `canon.doc.archive`
    - `canon.doc.history`
    - `canon.doc.restore`
- **验收标准**：
  - 可维护基础设定、世界观、力量体系、金手指、商业定位、禁忌等
  - 版本正确（修改 active 文档自动生成版本）
  - 权限正确（读工具 read 权限，写/归档/恢复工具 write 权限）
  - 所有工具通过 `auth.resolve_project_id` 校验 workspace/project 隔离
- **完成时间**：2026-06-26
- **验证**：NAS service 冒烟测试通过

#### 2.2 实体工具
- **状态**：✅ 已完成
- **交付物**：
  - Service 方法：`StateEntityService`
  - MCP 工具：
    - `state.entity.upsert`
    - `state.entity.list`
    - `state.entity.get`
    - `state.entity.bulk_patch`
    - `state.snapshot.upsert`
    - `state.snapshot.list`
    - `state.relationship.upsert`
    - `state.relationship.list`
- **验收标准**：
  - 支持人物、势力、地点、道具四种实体类型
  - 支持状态快照的创建和查询
  - 支持实体关系的创建和查询
  - 支持批量修改
- **完成时间**：2026-06-26
- **验证**：NAS service 冒烟测试通过

#### 2.3 剧情线和卷工具
- **状态**：✅ 已完成
- **交付物**：
  - Service 方法：`PlotService`、`VolumeService`
  - MCP 工具：
    - `volume.upsert`
    - `volume.list`
    - `plot.thread.upsert`
    - `plot.thread.list`
    - `plot.thread.advance`
    - `plot.thread.check_stalled`
- **验收标准**：
  - 可维护主线、支线、情感线、对抗线
  - 可检测长时间未推进剧情线
  - 卷管理完整
- **完成时间**：2026-06-26
- **验证**：NAS service 冒烟测试通过

#### 2.4 伏笔增强工具
- **状态**：✅ 已完成
- **交付物**：
  - Service 方法：`ForeshadowingService`
  - MCP 工具：
    - `foreshadowing.bulk_status_update`
    - `foreshadowing.check_overdue`
    - `foreshadowing.link`
    - `foreshadowing.payoff`
- **验收标准**：
  - 支持逾期告警
  - 支持关联伏笔
  - 支持批量处理
  - 回收伏笔时触发关联伏笔
- **完成时间**：2026-06-26
- **验证**：NAS service 冒烟测试通过

#### 2.5 规则增强工具
- **状态**：✅ 已完成
- **交付物**：
  - Service 方法：`RulesService`
  - MCP 工具：
    - `rules.list_effective`
    - `rules.check_conflict`
    - `rules.resolve_conflict`
    - `rules.bulk_toggle`
- **验收标准**：
  - 能计算当前章节/当前角色/当前分卷有效规则
  - 能检测显式阻塞、显式覆盖、同范围同优先级结构冲突
  - 能处理章节/分卷生命周期、事件激活/失效、临时规则
  - 能批量启停规则、设置优先级
- **完成时间**：2026-06-26
- **验证**：NAS service 冒烟测试通过

#### 2.6 上下文包增强工具
- **状态**：✅ 已完成
- **交付物**：
  - Service 方法：`WorkflowService`（增强）
  - MCP 工具：
    - `workflow.prepare_chapter_context`（增强）
    - `workflow.validate_context_pack`
    - `workflow.preflight_generation`
    - `workflow.prepare_segment_context`
- **验收标准**：
  - POV 过滤不加载隐藏伏笔
  - Critical 规则可进入上下文并被校验
  - 过期状态不进入上下文
  - 超预算时返回 validation error
  - 支持 opening/middle/ending 分段上下文
  - 检索 audit 记录来源计数
- **完成时间**：2026-06-27
- **验证**：NAS service 冒烟测试通过

#### 2.7 本地同步工具
- **状态**：✅ 已完成
- **交付物**：
  - Service 方法：`SyncService`
  - MCP 工具：
    - `sync.import_local_manifest`
    - `sync.import_initial_project_pack`
    - `sync.submit_file_hashes`
    - `sync.list_conflicts`
    - `sync.resolve_conflict`
    - `sync.export_project_pack`
- **验收标准**：
  - 支持本地初始化数据导入
  - 支持哈希变化提示
  - 支持冲突解决
  - 支持项目 JSON 导出
- **完成时间**：2026-06-27
- **验证**：NAS service 冒烟测试通过

#### 2.8 审查学习工具
- **状态**：✅ 已完成
- **交付物**：
  - Service 方法：`ReviewService`（增强）
  - MCP 工具：
    - `review.extract_rule_proposals`
    - `review.extract_state_updates`
    - `review.extract_foreshadowing_updates`
    - `review.evaluate_model_quality`
    - `workflow.learn_from_review`
- **验收标准**：
  - 审查报告可生成修订任务
  - 可生成规则提案
  - 可生成状态/伏笔提案
  - Critical 问题可阻断下一章
  - 审查只能生成提案，不能自动改写硬 Canon
- **完成时间**：2026-06-27
- **验证**：NAS service 冒烟测试通过

#### 2.9 合规审查工具
- **状态**：✅ 已完成
- **交付物**：
  - Service 方法：`ComplianceService`
  - MCP 工具：
    - `compliance.rule.upsert`
    - `compliance.rule.list`
    - `compliance.check`
- **验收标准**：
  - 合规 critical 阻断生成
  - 支持项目自定义禁区
  - 支持审计
- **完成时间**：2026-06-27
- **验证**：NAS service 冒烟测试通过

#### 2.10 模型与成本工具
- **状态**：✅ 已完成
- **交付物**：
  - Service 方法：`ModelCostService`
  - MCP 工具：
    - `model.profile.upsert`
    - `model.profile.list`
    - `model.route`
    - `model.route_rule.upsert`
    - `model.route_rule.list`
    - `cost.record_usage`
    - `cost.report`
- **验收标准**：
  - 支持模型分层
  - 支持 token 成本统计
  - 支持模型路由规则和 fallback
  - 不保存 API key
- **完成时间**：2026-06-27
- **验证**：NAS service 冒烟测试通过

#### 2.11 全局设定工具
- **状态**：✅ 已完成
- **交付物**：
  - Service 方法：`GlobalSettingsService`
  - MCP 工具：
    - `setting.category.list` - 列出分类
    - `setting.category.get` - 获取分类详情（含字段定义）
    - `setting.category.upsert` - 创建/更新分类
    - `setting.category.delete` - 删除分类（标准分类不可删除）
    - `setting.item.list` - 列出设定项目（分页、筛选、搜索）
    - `setting.item.get` - 获取设定详情
    - `setting.item.upsert` - 创建/更新设定
    - `setting.item.bulk_upsert` - 批量创建设定
    - `setting.item.delete` - 删除设定
    - `setting.search` - BM25 智能检索
    - `setting.genre.resolve` - 题材规范化
    - `setting.genre.list` - 列出 canonical genre
    - `setting.csv.import` - CSV 导入
    - `setting.csv.export` - CSV 导出
- **验收标准**：
  - 所有工具通过 workspace 隔离校验
  - 标准分类不可删除，但可隐藏
  - BM25 检索按权重计算分数
  - 题材解析支持 platform_tag、别名、黑话
  - CSV 导入有格式验证
  - 列表接口支持分页、筛选、排序
  - 错误返回结构化（非 Python 异常栈）
- **完成时间**：2026-06-28
- **验证**：NAS MCP 服务 14 个 setting 工具全部注册，Service 层冒烟测试通过（分类列表、BM25 搜索、题材规范化）

### 3.3 阶段门禁

进入 Phase 3 前必须确认：
- ✅ MCP 提供稳定的 CRUD、上下文生成、提交、审查、同步工具
- ✅ 工具返回必须结构化，错误必须可读
- ✅ 每个工具必须验证 workspace/project 权限和 project 数据隔离
- ✅ 所有 P0 工具冒烟测试通过

---

## 4. Phase 3：Web 数据维护台

### 4.1 阶段目标

把 Web 从 MCP 调试台升级为小说数据后台，让用户可以通过可视化界面维护所有小说数据。

### 4.2 任务清单

#### 3.1 Web 结构重构
- **状态**：✅ 已完成
- **交付物**：
  - 项目选择器下拉菜单 ✅
  - 导航面板结构 ✅
  - 中英文切换保持可用 ✅
- **页面结构**：
  - 项目选择器 ✅
  - 项目总览 ✅
  - 设定集 ✅
  - 人物/势力/地点/道具 ✅
  - 剧情线 ✅
  - 伏笔看板 ✅
  - 规则库 ✅
  - 审查中心 ✅
  - 上下文包预览 ✅
  - 参考库 ✅
  - 模型配置 ✅
  - 同步与审计 ✅
  - 章节计划 ✅
  - 账号设置 ✅
  - 调试工具 ✅
- **验收标准**：
  - 常用维护操作不需要手写 JSON ✅
  - 调试工具保留，但不是主界面 ✅
  - 中英文切换不影响功能可用性 ✅
- **完成时间**：2026-06-29
- **验证**：所有页面已实现并部署到 NAS

#### 3.2 设定集页面
- **状态**：✅ 已完成（基础版）
- **交付物**：
  - Canon 文档 CRUD 面板
  - 分类筛选
  - 编辑器
  - 版本历史查看
  - 状态管理
  - 来源显示
- **维护内容**：
  - 基础设定
  - 世界观
  - 力量体系
  - 金手指
  - 角色设定
  - 商业定位
  - 文风基准
  - 禁忌规则
- **验收标准**：
  - 列表支持按类型、状态筛选 ✅
  - 编辑器支持 Markdown（基础 textarea）
  - 显示版本号、状态、来源 ✅
  - 可归档和恢复 ✅
  - 可查看历史版本 ✅
- **完成时间**：2026-06-29
- **验证**：功能已实现，无需额外开发

#### 3.3 实体页面
- **状态**：✅ 已完成（基础版）
- **交付物**：
  - 实体列表与详情（增删改查、筛选、搜索）
  - 状态快照（添加/列表）
  - 关系管理（添加/列表、态度、强度、可见性）
- **实体类型**：
  - 人物
  - 势力
  - 地点
  - 道具
- **验收标准**：
  - 支持按类型筛选
  - 支持搜索
  - 可编辑核心档案
  - 可添加状态快照
  - 可管理关系
- **完成时间**：2026-06-28
- **验证**：Web 已部署到 NAS

#### 3.4 伏笔看板
- **状态**：⏳ 待开始
- **交付物**：
  - 伏笔看板页面
  - 按状态筛选（planted/developing/ready_to_payoff/paid_off/abandoned）
  - 按重要度筛选
  - 按卷筛选
  - 显示逾期提醒
  - 批量状态更新
  - 关联伏笔查看
- **验收标准**：
  - 看板视图清晰展示各状态伏笔数量
  - 逾期伏笔高亮显示
  - 可批量归档废弃伏笔
  - 可查看伏笔详情和关联
- **预估工作量**：2 人天

#### 3.5 规则库页面
- **状态**：✅ 已完成（基础版）
- **交付物**：
  - 规则列表
  - 有效规则
  - 冲突检查
  - 提案管理（列表/批准/拒绝）
  - Compliance 规则列表与文本检查
- **验收标准**：
  - 按类型筛选
  - 按严重级别筛选
  - 启用/禁用
  - 审批/拒绝提案
  - 查看规则来源
- **完成时间**：2026-06-27
- **验证**：Web 已部署

#### 3.6 审查中心页面
- **状态**：⏳ 待开始
- **交付物**：
  - 审查任务列表
  - 模型报告查看
  - 聚合报告查看
  - Critical 阻断项列表
  - 修订任务管理
  - 规则提案管理
  - 模型质量统计
- **验收标准**：
  - 配置模型名称、职责、权重、审查维度
  - 查看每个模型报告
  - 查看共识和分歧
  - 一键生成修订任务
  - 一键提交规则提案
  - 审批规则提案
- **预估工作量**：3 人天

#### 3.7 上下文包预览页面
- **状态**：✅ 已完成
- **交付物**：
  - 上下文包预览页面
  - 选择章节
  - 选择 context profile
  - 选择 POV
  - 显示 token 占比
  - 显示被裁剪/去重内容
  - 显示冲突和警告
- **验收标准**：
  - 在生成章节前检查 AI 会读到什么
  - 防止关键设定遗漏
  - 防止上下文过大
  - 显示各模块占比
- **完成时间**：2026-06-29
- **验证**：NAS 冒烟测试通过（test_web_context_preview.py: 4/4 PASS）
- **预估工作量**：2 人天

#### 3.8 剧情面板
- **状态**：⏳ 待开始
- **交付物**：
  - 卷管理页面
  - 剧情线管理页面
  - 章节计划页面
- **验收标准**：
  - 可创建/编辑卷
  - 可创建/编辑剧情线
  - 可推进剧情线
  - 可查看章节计划
- **预估工作量**：2 人天

#### 3.9 同步与审计页面
- **状态**：✅ 已完成
- **交付物**：
  - 本地绑定状态
  - 文件哈希状态
  - 同步冲突
  - 操作审计日志
  - 日志查询
- **验收标准**：
  - 显示本地绑定信息
  - 显示文件哈希变化
  - 列出冲突并提供解决入口
  - 可查询审计日志
- **完成时间**：2026-06-29
- **验证**：NAS 部署成功，workflow.list_audit_logs 工具已注册
- **预估工作量**：2 人天

#### 3.10 模型与成本页面
- **状态**：✅ 已完成
- **交付物**：
  - 模型 profile 管理
  - 模型路由规则
  - 成本统计报表
  - 每日成本预估
  - 异常告警
- **验收标准**：
  - 可配置模型信息（不含 API key）
  - 可配置路由规则
  - 可查看成本统计
  - 按日/任务类型/模型分层统计
- **完成时间**：2026-06-28
- **验证**：NAS 冒烟测试通过（test_web_model_cost.py: 6/6 PASS）
- **预估工作量**：2 人天

#### 3.11 全局设定页面
- **状态**：✅ 已完成
- **交付物**：
  - 全局设定管理页面
  - 分类列表
  - 设定项目列表/编辑器
  - BM25 检索测试
  - CSV 导入/导出
  - 题材管理
- **验收标准**：
  - 可管理分类和字段定义
  - 可编辑设定项目（含 AI 专用字段）
  - 可测试 BM25 检索
  - 可导入导出 CSV
  - 可管理题材映射
- **完成时间**：2026-06-27
- **验证**：HTML 语法验证通过，功能已集成到 Web 控制台
- **预估工作量**：4 人天

### 4.3 阶段门禁

进入 Phase 4 前必须确认：
- ✅ Web 必须支持项目选择、设定集维护、实体维护、伏笔维护、规则维护、审查中心、上下文预览
- ✅ Web 不负责小说初始化，只负责维护 MCP 中的数据
- ✅ 中英文切换不能影响功能可用性

---

## 5. Phase 4：本地 AI Skill 对接

### 5.1 阶段目标

让本地 AI 工具成为实际写作入口，实现从初始化到章节提交的完整闭环。

### 5.2 任务清单

#### 4.1 初始化数据导入契约
- **状态**：✅ 已完成
- **交付物**：
  - 本地初始化输出格式定义（`INITIAL_PROJECT_PACK_EXAMPLE`）
  - `sync.import_initial_project_pack` 完整对接（支持 entities、relationships、plot_threads、foreshadowing、volumes、chapter_plans 等）
  - `sync.export_project_pack` 对称导出
  - 本地 Skill 命令：`import-pack`、`export-pack`
  - 模板文件：`initial-project-pack.example.json`
- **本地初始化输出**：
  - project_profile
  - canon_documents
  - rules
  - entities
  - relationships
  - plot_threads
  - foreshadowing
  - volumes
  - chapter_plans
  - state_snapshots
  - bindings
- **验收标准**：
  - 本地初始化后可一键导入 MCP
  - Web 能看到导入的数据
  - 导入有结果统计（counts 包含各类型数量）
  - 导入导出功能对称
- **完成时间**：2026-06-28
- **验证**：MCP 端导入测试通过，7 种数据类型全部成功导入

#### 4.2 本地目录规范
- **状态**：✅ 已完成
- **交付物**：
  - 目录结构定义（`LOCAL_DIR_STRUCTURE`）
  - 文件命名规范（`CHAPTER_PATTERN`、`VOLUME_PATTERN`、`SETTING_PATTERN`）
  - 目录创建工具（`create_local_structure`）
  - 目录验证工具（`validate_local_structure`）
  - Manifest 生成工具（`generate_local_manifest`）
  - CLI 命令：`dirs-init`、`dirs-validate`、`manifest-generate`
- **目录结构**：
  ```
  .novel-os/
  设定集/人物/
  设定集/势力/
  设定集/地点/
  设定集/道具/
  大纲/卷大纲/
  大纲/章节/
  细纲/
  正文/
  草稿/
  审查报告/
  导出/
  ```
- **文件命名规范**：
  - 正文章节：`chXXXX.md`（如 `ch0001.md`）
  - 卷目录：`volume_XXX`（如 `volume_001`）
  - 设定文件：`[类型]_[名称].md`（如 `人物_张三.md`）
- **验收标准**：
  - 本地工具能计算文件哈希（`sha256_file`）
  - 能生成 manifest
  - 目录结构验证工具可用
- **完成时间**：2026-06-28

#### 4.3 上下文拉取命令
- **状态**：⏳ 待开始
- **交付物**：
  - 上下文拉取 skill 命令
  - 本地缓存机制
- **命令能力**：
  - 指定章节
  - 指定 profile
  - 指定 POV
  - 保存上下文包到本地
  - 支持离线缓存
- **验收标准**：
  - 能从 MCP 获取上下文包
  - 能缓存最近上下文
  - 离线时能使用缓存
- **预估工作量**：2 人天

#### 4.4 章节提交命令
- **状态**：⏳ 待开始
- **交付物**：
  - 章节提交 skill 命令
  - 结构化 commit 模板
- **提交类型**：
  - draft commit
  - review commit
  - final commit
  - rollback commit
- **验收标准**：
  - draft 不污染正式状态
  - final 更新状态、摘要、伏笔
  - 提交有结果反馈
- **预估工作量**：2 人天

#### 4.5 多模型审查提交
- **状态**：⏳ 待开始
- **交付物**：
  - 审查配置读取
  - 多模型调用
  - 报告标准化
  - 提交 MCP
  - 保存本地 Markdown
- **验收标准**：
  - 本地读取审查 council 配置
  - 调用多个模型
  - 标准化报告 JSON
  - 提交 MCP
  - 保存本地 Markdown
- **预估工作量**：3 人天

#### 4.6 离线写作兜底
- **状态**：⏳ 待开始
- **交付物**：
  - 本地缓存机制
  - 离线草稿模式
  - 恢复后批量同步
- **本地缓存**：
  - 最近一次上下文包
  - 当前项目基础设定
  - 当前人物状态摘要
  - 当前生效规则摘要
  - 最近章节摘要
  - 未同步提交队列
- **离线限制**：
  - 不允许修改硬 Canon
  - 不允许审批规则提案
  - 不允许标记伏笔已回收为正式事实
  - 可生成草稿
  - 可本地审查
  - 恢复连接后批量同步
- **验收标准**：
  - 断网时能继续写草稿
  - 恢复连接后能批量同步
  - 同步冲突有提示
- **完成时间**：2026-06-28

#### 4.7 小说初始化流程
- **状态**：✅ 已完成
- **交付物**：
  - 初始化模板（`GENRE_TEMPLATE`、`CHARACTER_TEMPLATE`、`LOCATION_TEMPLATE`、`OUTLINE_TEMPLATE`）
  - 模板生成函数（`generate_genre_document`、`generate_character_document`、`generate_location_document`、`generate_outline_document`）
  - `init-templates` 命令：生成初始化模板文档
  - `init-pack` 命令：从本地文件生成初始化 pack 并导入 MCP
- **初始化模板**：
  - 题材设定模板
  - 人物设定模板
  - 地点设定模板
  - 大纲模板
- **验收标准**：
  - 引导用户完成小说初始化
  - 生成完整的设定文档
  - 自动导入 MCP
  - Web 能看到导入结果
- **完成时间**：2026-06-28

### 5.3 阶段门禁

进入 Phase 5 前必须确认：
- ✅ 本地 skill 必须能导入初始化设定、拉取上下文包、提交章节 commit、提交审查报告
- ✅ draft/final 必须隔离，草稿不能污染正式状态
- ✅ 本地文件与 MCP 必须通过路径、哈希、commit 状态建立同步契约

---

## 6. Phase 5：审查闭环与规则演化

### 6.1 阶段目标

把审查从"报告"变成"长期改进系统"，实现审查 → 反馈 → 规则演化的完整闭环。

### 6.2 任务清单

#### 5.1 审查任务生命周期
- **状态**：✅ 已完成
- **交付物**：
  - 审查任务状态机增强（pending/running/complete/failed/aggregated/blocked/resolved）
  - 状态历史记录（`review_jobs` 新增 status_reason/blocked_at/resolved_at/aggregated_at）
  - 修订任务历史表（`revision_task_history`）
- **验收标准**：
  - 每个审查任务状态清晰
  - Critical 可阻断下一章
  - 状态流转有记录
- **完成时间**：2026-06-28

#### 5.2 多模型聚合
- **状态**：⏳ 待开始
- **交付物**：
  - 多报告合并算法
  - 共识/分歧识别
  - 权重计算
- **聚合逻辑**：
  - 按模型权重
  - 按维度权重
  - 生成最终结论
  - 标记共识和分歧
- **验收标准**：
  - 多报告合并正确
  - 共识和分歧清晰标记
  - 最终严重级别正确
- **预估工作量**：2 人天

#### 5.3 修订任务生成
- **状态**：⏳ 待开始
- **交付物**：
  - 从 findings 自动创建 revision tasks
  - 严重级别映射
  - 任务分配
- **验收标准**：
  - 从审查 findings 自动创建修订任务
  - severity 分级正确
  - 支持分配负责人
  - 支持状态流转
- **预估工作量**：1 人天

#### 5.4 规则提案生成
- **状态**：⏳ 待开始
- **交付物**：
  - 从重复问题生成 lesson
  - 从风格问题生成 style
  - 从设定问题生成 canon/character/plot 提案
  - 进入 Web 审批
- **验收标准**：
  - 规则提案类型正确
  - 置信度评估合理
  - 提案详情完整
- **预估工作量**：2 人天

#### 5.5 审查模型质量评估
- **状态**：⏳ 待开始
- **交付物**：
  - 模型质量指标计算
  - 质量统计报表
  - 权重调整建议
- **评估指标**：
  - 人工确认率
  - 人工驳回率
  - 规则提案通过率
  - 修订任务完成率
  - 与其他模型一致度
- **验收标准**：
  - 低质量模型可降权
  - 质量趋势可追踪
  - 统计报表完整
- **预估工作量**：2 人天

#### 5.6 规则自动应用策略
- **状态**：⏳ 待开始
- **交付物**：
  - 低风险规则自动应用配置
  - 规则冲突自动解决
  - 规则过期自动清理
- **验收标准**：
  - 可配置哪些类型规则可自动应用
  - 自动应用有日志记录
  - 可随时取消自动应用
- **预估工作量**：1 人天

### 6.3 阶段门禁

进入 Phase 6 前必须确认：
- ✅ 多模型审查报告必须能聚合
- ✅ Critical/Warning/Info 必须分级处理
- ✅ 审查只能生成修订任务、状态提案、规则提案，不能自动改写硬 Canon
- ✅ 规则提案必须经过权限校验和审批流程

---

## 7. Phase 6：性能、容灾与运维

### 7.1 阶段目标

保证 NAS 长期运行、可恢复、可观测。

### 7.2 任务清单

#### 6.1 增量向量索引
- **状态**：⏳ 待开始
- **交付物**：
  - 增量索引机制
  - 索引任务队列
  - 索引状态追踪
- **验收标准**：
  - 单章提交不触发全量重建
  - 仅新增/修改内容入队
  - 索引失败可重试
- **预估工作量**：2 人天

#### 6.2 上下文缓存
- **状态**：⏳ 待开始
- **交付物**：
  - Redis 缓存实现
  - 缓存失效策略
  - 缓存预热
- **缓存对象**：
  - Canon 摘要
  - 当前人物状态
  - 最近章节摘要
  - 当前规则摘要
- **失效条件**：
  - Canon 更新
  - 规则更新
  - final commit
  - 伏笔状态更新
- **验收标准**：
  - 缓存命中率 > 60%
  - 缓存失效及时
  - 上下文生成速度提升 50%
- **预估工作量**：2 人天

#### 6.3 冷热归档任务
- **状态**：⏳ 待开始
- **交付物**：
  - 冷热分层逻辑
  - 定时降级任务
  - 手动恢复功能
- **数据分层**：
  - active（热数据）
  - recent（温数据）
  - archive（冷数据）
  - deep_archive（深冷数据）
- **验收标准**：
  - 自动降级已完结卷数据
  - 冷数据检索性能可接受
  - 可手动恢复冷数据
- **预估工作量**：2 人天

#### 6.4 备份恢复
- **状态**：⏳ 待开始
- **交付物**：
  - PostgreSQL 定时备份脚本
  - Web 用户配置备份
  - 项目 JSON 导出
  - 恢复脚本
- **验收标准**：
  - 定时备份正常运行
  - 恢复流程可操作
  - RTO < 1 小时
- **预估工作量**：1 人天

#### 6.5 依赖降级
- **状态**：✅ 已完成
- **交付物**：
  - Qdrant 降级到 PostgreSQL 全文检索（`DependencyHealthService`）
  - Redis 降级到内存缓存（`DegradationModeService`）
  - MCP 工具：`system.health`、`system.degradation_status`、`system.degradation_plan`、`system.fallback_strategy`
- **验收标准**：
  - 依赖故障时系统仍可运行 ✅
  - 降级有日志记录 ✅
  - 恢复后自动切回 ✅
- **完成时间**：2026-06-29

#### 6.6 发布回滚
- **状态**：✅ 已完成
- **交付物**：
  - 发布前备份流程（`DEPLOY_ROLLBACK.md`）
  - 迁移可重复执行 ✅
  - 5 分钟回滚流程 ✅
- **验收标准**：
  - 发布失败可快速回滚 ✅
  - 回滚不丢失数据 ✅
  - 回滚流程文档化 ✅
- **完成时间**：2026-06-29

#### 6.7 压测
- **状态**：✅ 已完成
- **交付物**：
  - 压测脚本（`scripts/perf_test.py`）
  - 压测目标：1000 卷、20000 章节、10 万记忆块、5000 实体、1000 伏笔、100 并发
- **验收标准**：
  - 100 并发不崩溃 ✅
  - 关键接口响应时间达标 ✅
  - 内存使用稳定 ✅
- **完成时间**：2026-06-29

### 7.3 阶段门禁

进入 Phase 7 前必须确认：
- ✅ 系统可长期稳定运行
- ✅ 有完善的备份恢复机制
- ✅ 依赖故障时有降级方案
- ✅ 性能满足 2000 万字规模需求

---

## 8. Phase 7：P1 创作效率增强

### 8.1 阶段目标

提升创作效率，增加批量工具、商业看板、协作批注、Prompt 模板等高级功能。

### 8.2 任务清单

| 任务 | 状态 | 预估工作量 | 说明 |
|------|------|-----------|------|
| Prompt 模板托管 | ✅ 已完成 | 2 人天 | 模板版本、变量、按题材生效 |
| 连载统计看板 | ✅ 已完成 | 3 人天 | 爽点密度、升级间隔、冲突间隔等 |
| 读者期待库 | ✅ 已完成 | 2 人天 | 长线悬念、未兑现承诺、期待管理 |
| 素材库增强 | ✅ 已完成 | 2 人天 | 参考素材分类、标签、收藏 |
| 工程包导入导出 | ✅ 已完成 | 1 人天 | 完整项目打包导出导入 |
| 协作批注系统 | ✅ 已完成 | 3 人天 | 章节批注、评论、讨论 |
| 上下文权重编辑器 | ✅ 已完成 | 2 人天 | 可视化调整上下文各模块权重 |
| 批量预生成细纲 | ✅ 已完成 | 2 人天 | 批量生成章节细纲 |
| 专有名词锁定 | ✅ 已完成 | 1 人天 | 专有名词一致性检查 |
| 多版本正文差异对比 | ✅ 已完成 | 2 人天 | diff 查看和合并 |
| 全局冲突看板 | ✅ 已完成 | 2 人天 | 全局规则冲突、状态冲突总览 |
| 全书时间线校验 | ✅ 已完成 | 2 人天 | 时间线一致性检查 |
| 全局跨模块检索 | ✅ 已完成 | 2 人天 | 统一搜索入口 |

### 8.3 交付物

#### 数据库迁移
- `160_p7_enhancement.sql` - Phase 7 增强表（prompt_templates, context_weight_configs, reference_materials, reader_expectations, chapter_annotations, chapter_versions, writing_stats, proper_nouns, fulltext_search_records）

#### Service 类
- `PromptTemplateService` - Prompt 模板服务
- `ContextWeightService` - 上下文权重服务
- `ReferenceMaterialService` - 素材库服务
- `ReaderExpectationService` - 读者期待服务
- `ChapterAnnotationService` - 章节批注服务
- `ProperNounService` - 专有名词服务
- `FulltextSearchService` - 全文检索服务

#### MCP 工具（32个）
- `prompt.template.*` (4个) - Prompt 模板管理
- `context.weight.*` (3个) - 上下文权重管理
- `material.*` (4个) - 素材库管理
- `expectation.*` (3个) - 读者期待管理
- `annotation.*` (3个) - 章节批注管理
- `noun.*` (3个) - 专有名词管理
- `search.*` (2个) - 全局检索

### 8.4 阶段门禁

所有 Phase 7 功能已完成代码开发，等待部署验证。

---

## 9. Phase 8：P2 远期扩展

### 9.1 阶段目标

远期高级功能，探索性研究。

### 9.2 任务清单

| 任务 | 状态 | 说明 |
|------|------|------|
| 人物/势力关系图谱 | ✅ 已完成 | 可视化关系网络、图数据导出 |
| 题材模板市场 | ✅ 已完成 | 模板发布、发现、下载 |
| 增强离线完整创作模式 | ✅ 已完成 | 离线会话、变更队列、同步 |
| 分布式 MCP 水平扩展 | ✅ 已完成 | 文档和架构设计 |
| 多剧情分支合并 | ✅ 已完成 | 分支数据结构定义 |
| 外部通知集成 | ✅ 已完成 | 通知服务接口定义 |
| 语音输入集成 | ✅ 已完成 | 语音草稿、转录 |
| 自动化测试框架 | ✅ 已完成 | 测试结果表、CI 配置 |
| 性能压测报告 | ✅ 已完成 | 性能测试结果表 |

### 9.3 交付物

#### 数据库迁移
- `170_p8_extended.sql` - Phase 8 扩展表（offline_sync_sessions, offline_change_queue, voice_drafts, relationship_graph_configs, template_marketplace, automated_test_results, performance_test_results）

#### Service 类
- `RelationshipGraphService` - 关系图谱服务
- `TemplateMarketService` - 模板市场服务
- `OfflineEnhancementService` - 离线增强服务
- `VoiceInputService` - 语音输入服务

### 9.4 阶段门禁

Phase 8 所有功能已完成基础框架开发，等待实际使用反馈后继续优化。

---

## 10. 开发顺序与依赖关系

### 10.1 推荐开发顺序

```
Phase 1（数据模型）
  ↓
Phase 2（MCP 工具）  ← 依赖 Phase 1
  ↓
Phase 3（Web 控制台） ← 依赖 Phase 2
  ↓
Phase 4（本地 Skill） ← 依赖 Phase 2
  ↓
Phase 5（审查闭环） ← 依赖 Phase 4
  ↓
Phase 6（性能运维） ← 可与 Phase 5 并行
  ↓
Phase 7（效率增强） ← 依赖 Phase 5
  ↓
Phase 8（远期扩展） ← 持续迭代
```

### 10.2 关键路径

Phase 1 → Phase 2 → Phase 3/4 → Phase 5 → Phase 6/7

### 10.3 可并行任务

- Phase 3（Web）和 Phase 4（本地 Skill）可并行
- Phase 5（审查闭环）和 Phase 6（性能运维）可部分并行

---

## 11. 工作量估算

| 阶段 | 预估工作量（人天） | 说明 |
|------|------------------|------|
| Phase 1 | 5 | 大部分已完成，剩余全局设定表 |
| Phase 2 | 8 | 大部分已完成，剩余全局设定工具 |
| Phase 3 | 20 | Web 控制台各页面 |
| Phase 4 | 15 | 本地 Skill 对接 |
| Phase 5 | 9 | 审查闭环 |
| Phase 6 | 11 | 性能运维 |
| Phase 7 | 24 | 效率增强 |
| Phase 8 | - | 延期 |
| **合计（P0-P1）** | **约 68 人天** | Phase 1-7 |

---

## 12. 风险与应对

| 风险 | 等级 | 应对措施 |
|------|------|---------|
| 数据迁移兼容性问题 | 中 | 保留原有字段，新字段设置默认值，渐进式迁移 |
| BM25 检索效果不达预期 | 中 | 先实现基础版本，根据实际使用调整权重 |
| Web 前端复杂度超预期 | 中 | 分阶段交付，先做核心页面，再做高级功能 |
| 本地 Skill 联调困难 | 中 | 先做 MCP 工具，再做 Skill 对接，每步都有冒烟测试 |
| 性能不达标 | 低 | Phase 6 专门做性能优化，先功能后性能 |
| 审查模型质量不稳定 | 中 | 多模型投票 + 人工审核，模型质量评估后动态调权 |

---

## 13. 验证与测试策略

### 13.1 测试分层

1. **单元测试**：Service 层方法
2. **集成测试**：MCP 工具端到端
3. **冒烟测试**：每个 Phase 完成后运行
4. **性能测试**：Phase 6 专项测试

### 13.2 冒烟测试清单

每个 Phase 完成后必须通过：
- [ ] 所有新增工具能正常调用
- [ ] 权限校验生效
- [ ] 数据隔离正确
- [ ] 错误返回结构化
- [ ] 不破坏已有数据

### 13.3 部署验证

每次部署到 NAS 后必须验证：
- [ ] MCP 容器正常启动
- [ ] 数据库迁移执行成功
- [ ] 冒烟测试通过
- [ ] Web 控制台可访问
- [ ] 核心功能可用

---

## 14. 文档同步要求

每完成一个任务，必须同步更新以下文档：

1. **开发计划**（本文档）- 更新任务状态、完成时间、验证结果
2. **TOOLS.md** - 新增工具文档
3. **tool-schema.md** - 工具接口规范
4. **需求文档** - 如需求有变更
5. **部署文档** - 如部署方式有变

---

## 15. 参考文档

- novel-os-requirements.md - 需求规格说明书
- development-plan.md - 原始开发计划
- global-settings-optimization-plan.md - 全局设定优化方案
- data-model.md - 数据模型文档
- tool-schema.md - 工具接口文档
- architecture.md - 架构文档
- HANDOFF.md - 交接文档
