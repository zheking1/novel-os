# Novel OS 系统需求规格说明书

> 版本：v1.0  
> 日期：2026-06-28  
> 状态：正式需求文档  
> 基于：requirements-and-dev-brief.md、global-settings-design.md、global-settings-optimization-plan.md、data-model.md

---

## 1. 项目概述

### 1.1 项目背景

Novel OS 是一个面向超长篇网络小说创作的 AI 辅助写作管理系统。系统目标是支持 2000 万字规模的小说创作，通过结构化数据管理、智能上下文检索、规则演化和多模型审查，确保 AI 生成的小说在设定一致性、人物稳定性、剧情连贯性和商业节奏上达到专业水准。

### 1.2 核心设计原则

1. **事实与文本分离**：MCP 保存结构化事实、状态、规则、摘要、索引和审查结构，正文等人类可编辑文档保存在用户本地
2. **有限上下文原则**：AI 每次只读取当前需要的局部上下文，通过上下文包（Context Pack）控制 token 预算
3. **审查不直接改事实**：审查结果生成修订任务、规则提案、状态提案，由人工或配置策略决定是否应用
4. **元数据驱动 + 标准化增强**：保留 JSONB 灵活性的同时，增加 BM25 检索优化字段、AI 专用字段和标准化分类体系
5. **冷热数据分层**：当前卷、最近章节、活跃实体为热数据；已完结卷、已回收伏笔、废弃设定为冷数据

### 1.3 目标用户

- **作者**：使用本地 AI 工具创作，维护小说数据
- **编辑**：审查和修正数据，审批规则提案
- **审阅者**：提交审查报告和修订建议
- **系统管理员**：服务器级维护和用户管理

---

## 2. 系统架构与角色边界

### 2.1 三层架构

```
┌─────────────────────────────────────────────────────────────┐
│  本地 AI 工具层（Local AI Tools）                           │
│  - Codex Skill / 本地脚本 / 桌面写作工具                     │
│  - 小说初始化、生成正文、调用大模型、提交结构化数据           │
│  - 保存正文、大纲、细纲、审查 Markdown 等人类可编辑文档       │
└──────────────────────┬──────────────────────────────────────┘
                       │ MCP 协议
┌──────────────────────▼──────────────────────────────────────┐
│  MCP 服务层（Model Context Protocol Server）               │
│  - 小说长期数据和规则中枢                                    │
│  - 结构化事实、规则、状态、伏笔、摘要、索引、审查结构         │
│  - 生成有限上下文包（Context Pack）                         │
│  - PostgreSQL + Qdrant + Redis                              │
└──────────────────────┬──────────────────────────────────────┘
                       │ HTTP / WebSocket
┌──────────────────────▼──────────────────────────────────────┐
│  Web 控制台层（Web Console）                                │
│  - 小说数据维护后台                                          │
│  - 设定集、人物/势力/地点/道具、规则库、伏笔看板             │
│  - 审查中心、上下文包预览、模型配置、同步与审计              │
└─────────────────────────────────────────────────────────────┘
```

### 2.2 角色职责边界

| 职责 | 本地 AI 工具 | MCP | Web 控制台 |
|------|------------|-----|-----------|
| 小说初始化访谈 | ✅ 负责 | - | - |
| 生成本地目录结构 | ✅ 负责 | - | - |
| 保存正文/大纲/细纲 | ✅ 负责 | - | - |
| 调用大模型生成 | ✅ 负责 | - | - |
| 保存结构化长期数据 | - | ✅ 负责 | - |
| 生成上下文包 | - | ✅ 负责 | - |
| 规则版本与审批 | - | ✅ 负责 | ✅ 可视化操作 |
| 维护设定/实体/伏笔 | - | ✅ 数据存储 | ✅ 编辑界面 |
| 审查聚合与学习 | - | ✅ 负责 | ✅ 可视化操作 |
| 用户/工作区管理 | - | ✅ 负责 | ✅ 可视化操作 |

---

## 3. 功能需求

### 3.1 身份与权限管理

#### 3.1.1 用户管理

**需求描述**：系统支持多用户，每个用户有独立的身份和权限。

**功能清单**：
- 用户注册与登录（用户名 + 密码）
- 用户信息管理（显示名称、邮箱）
- 用户状态管理（active / disabled）
- API Token 管理（创建、列出、撤销）

**数据字段**：
- `id`: UUID，主键
- `username`: 字符串，唯一
- `display_name`: 字符串
- `email`: 字符串，唯一，可空
- `password_hash`: 字符串，可空
- `status`: active / disabled
- `created_at`, `updated_at`: 时间戳

#### 3.1.2 工作区管理

**需求描述**：工作区是项目的容器，支持多工作区隔离。

**功能清单**：
- 创建工作区
- 列出工作区
- 工作区成员管理（添加、移除、角色分配）
- 工作区设置

**数据字段**：
- `id`: UUID，主键
- `slug`: 字符串，唯一
- `name`: 字符串
- `owner_user_id`: UUID，关联 users
- `settings`: JSONB
- `created_at`, `updated_at`: 时间戳

**工作区角色**：
- `owner`: 工作区拥有者，完全控制
- `editor`: 编辑，可维护项目内容
- `reviewer`: 审阅者，可提交审查与修订任务
- `reader`: 只读

#### 3.1.3 项目管理

**需求描述**：每个小说项目是独立的创作单元。

**功能清单**：
- 创建项目
- 列出项目
- 项目成员管理
- 项目设置
- 项目归档/恢复
- 本地项目绑定（路径提示、文件哈希、manifest）

**数据字段**：
- `id`: UUID，主键
- `workspace_id`: UUID，关联 workspaces
- `slug`: 字符串，工作区内唯一
- `title`: 字符串
- `description`: 文本
- `status`: active / archived
- `settings`: JSONB
- `created_at`, `updated_at`: 时间戳

**项目角色**：
- `owner`: 项目拥有者
- `author`: 作者，可维护项目内容
- `editor`: 编辑，可审查和修正数据
- `reviewer`: 审阅者，可提交审查
- `reader`: 只读

**权限矩阵**：

| 操作 | owner | author | editor | reviewer | reader |
|------|-------|--------|--------|----------|--------|
| 编辑基础设定草稿 | ✅ | ✅ | ✅ | ❌ | ❌ |
| 修改 active Canon | ✅ | 提案 | 提案/可配置 | ❌ | ❌ |
| 审批 Canon 变更 | ✅ | 可配置 | 可配置 | ❌ | ❌ |
| 编辑人物当前状态 | ✅ | ✅ | ✅ | 提案 | ❌ |
| 更新伏笔状态 | ✅ | ✅ | ✅ | 标记异常 | ❌ |
| 创建规则提案 | ✅ | ✅ | ✅ | ✅ | ❌ |
| 审批规则提案 | ✅ | 可配置 | 可配置 | ❌ | ❌ |
| 提交审查报告 | ✅ | ✅ | ✅ | ✅ | ❌ |
| 创建修订任务 | ✅ | ✅ | ✅ | ✅ | ❌ |
| 查看上下文包 | ✅ | ✅ | ✅ | ✅ | ✅ |

---

### 3.2 全局设定系统（Global Settings）

#### 3.2.1 分类管理

**需求描述**：支持自定义分类，同时预设 9 个标准分类。

**功能清单**：
- 创建分类
- 列出分类
- 更新分类
- 删除分类（标准分类不可删除，可隐藏）
- 分类字段定义管理

**预设标准分类**：

| 分类 slug | 分类名称 | 说明 |
|-----------|---------|------|
| genre-inference | 题材与调性推理 | 对应题材与调性推理 |
| golden-finger | 金手指与设定 | 对应金手指与设定 |
| character-template | 人设模板 | 对应人设与关系 |
| plot-template | 情节模板 | 对应桥段套路 |
| naming-rules | 命名规则 | 对应命名规则 |
| scene-writing | 场景写法 | 对应场景写法 |
| writing-techniques | 写作技法 | 对应写作技法 |
| rhythm-points | 爽点与节奏 | 对应爽点与节奏 |
| review-rules | 裁决规则 | 对应裁决规则 |

**分类数据字段**：
- `id`: UUID，主键
- `name`: 字符串（100字符）
- `slug`: 字符串（50字符），唯一
- `description`: 文本
- `icon`: 字符串（emoji）
- `sort_order`: 整数
- `is_active`: 布尔
- `is_standard`: 布尔（是否标准分类）
- `workspace_id`: UUID
- `created_at`, `updated_at`: 时间戳

**字段定义数据字段**：
- `id`: UUID，主键
- `category_id`: UUID，关联 setting_categories
- `field_name`: 字符串（100字符），显示用
- `field_key`: 字符串（50字符），代码用
- `field_type`: text / textarea / select / multiselect / number / boolean
- `options`: JSONB，select 类型的选项
- `is_required`: 布尔
- `is_searchable`: 布尔
- `default_value`: 字符串
- `sort_order`: 整数
- `created_at`: 时间戳

#### 3.2.2 设定项目管理

**需求描述**：每个分类下的具体设定条目，支持 BM25 检索优化字段和 AI 专用字段。

**功能清单**：
- 创建设定项目
- 批量创建（CSV 导入）
- 列出设定项目（分页、筛选、搜索）
- 获取单个项目详情
- 更新设定项目
- 删除设定项目
- 按标签搜索
- 获取关联项目

**核心检索字段**（BM25 优化）：
- `item_code`: 字符串（20字符），项目编码（如 GR-001）
- `keywords`: 文本数组，高权重触发词
- `intent_synonyms`: 文本数组，用户自然语言问法、黑话、俗语
- `core_summary`: 文本，核心摘要（高权重召回）
- `detailed_expansion`: 文本，详细展开

**AI 专用字段**：
- `ai_instruction`: 文本，大模型指令（直接给 AI 的执行指令）
- `poison_points`: 文本数组，毒点/反面案例警告

**分层与权重字段**：
- `level`: 知识补充 / 提醒 / 缺陷补偿
- `applicable_skills`: 文本数组，适用技能（init / plan / write / review 等）
- `applicable_genres`: 文本数组，适用题材（canonical genre）

**原有灵活字段**：
- `data`: JSONB，动态属性数据
- `tags`: 文本数组
- `is_global`: 布尔，是否全局共享
- `sort_order`: 整数

#### 3.2.3 题材规范化系统

**需求描述**：建立题材映射机制，支持 platform_tag → canonical genre 转换。

**功能清单**：
- 题材解析（用户输入 → canonical genre）
- 列出 canonical genre 列表
- 维护 platform tag 映射
- 维护别名和黑话

**Canonical Genre 列表**（15个）：
- 都市
- 玄幻
- 仙侠
- 奇幻
- 科幻
- 历史
- 悬疑
- 游戏
- 古言
- 现言
- 幻言
- 年代
- 种田
- 快穿
- 衍生

**数据字段**：
- `canonical_genre`: 字符串（20字符），主键
- `platform_tags`: 文本数组
- `aliases`: 文本数组
- `description`: 文本
- `created_at`: 时间戳

#### 3.2.4 BM25 智能检索

**需求描述**：实现多权重 BM25 检索算法，支持按技能、题材、分类过滤。

**检索权重设计**：
- `intent_synonyms`: 权重 4（用户意图最匹配）
- `keywords`: 权重 3（关键词匹配）
- `core_summary`: 权重 2（核心摘要）
- `detailed_expansion`: 权重 1（详细展开）

**功能清单**：
- 全文搜索（跨分类或指定分类）
- 按技能过滤
- 按题材过滤（自动规范化）
- 按分类过滤
- 是否包含毒点
- 相关性评分
- 检索来源说明

#### 3.2.5 CSV 导入导出

**需求描述**：支持规范化的 CSV 批量导入导出，降低用户使用门槛。

**CSV 必须列**：
- 编号（item_code）
- keywords（用 | 分隔）
- intent_synonyms（用 | 分隔）
- core_summary
- detailed_expansion
- ai_instruction
- poison_points（用 | 分隔）
- applicable_skills（用 | 分隔）
- applicable_genres（用 | 分隔）
- 其他动态字段（映射到 data JSONB）

**功能清单**：
- CSV 格式验证
- 批量导入
- 批量导出
- 导入结果统计
- 标准 CSV 模板下载

---

### 3.3 Canon 设定层

#### 3.3.1 Canon 文档管理

**需求描述**：小说中已经确认为事实、不能被模型随意改写的硬设定文档。

**文档类型**：
- `premise`: 基础设定
- `worldview`: 世界观
- `power_system`: 力量体系
- `golden_finger`: 金手指
- `character_bible`: 角色设定
- `faction_bible`: 势力设定
- `location_bible`: 地点设定
- `style_bible`: 文风基准
- `commercial_positioning`: 商业定位
- `forbidden`: 禁忌规则
- `other`: 其他

**功能清单**：
- 创建/更新 Canon 文档（upsert）
- 列出 Canon 文档（按类型、状态筛选）
- 获取单个文档详情
- 归档文档
- 查看历史版本
- 恢复历史版本
- 版本对比（P1）

**数据字段**：
- `id`: UUID，主键
- `project_id`: UUID，关联 projects
- `doc_type`: 文档类型（见上）
- `key`: 字符串，项目内唯一标识
- `title`: 字符串
- `content`: 文本
- `content_hash`: 字符串，内容哈希
- `status`: draft / active / archived / superseded
- `version`: 整数
- `scope`: global / volume / arc / chapter / character / faction
- `review_status`: unreviewed / reviewed / needs_review
- `source_type`: local_init / manual / review / chapter_commit / import
- `source_id`: UUID，可空
- `related_rule_ids`: UUID 数组
- `metadata`: JSONB
- `created_by`, `updated_by`: UUID
- `created_at`, `updated_at`: 时间戳

**约束规则**：
- 同一项目内 `doc_type + key` 唯一
- 修改 active Canon 自动生成版本
- 重要 Canon 修改必须记录审计
- Canon 变更必须有来源

#### 3.3.2 Canon 文档版本

**需求描述**：保存 Canon 历史版本，支持回滚和差异对比。

**功能清单**：
- 自动记录每次修改的版本
- 查看版本历史列表
- 查看版本详情
- 恢复到指定版本
- 版本对比（P1）

**数据字段**：
- `id`: UUID，主键
- `document_id`: UUID，关联 canon_documents
- `version`: 整数
- `content`: 文本
- `change_reason`: 文本
- `source`: 字符串
- `created_by`: UUID
- `created_at`: 时间戳

---

### 3.4 当前状态层

#### 3.4.1 实体管理

**需求描述**：管理小说中的人物、势力、地点、道具等实体。

**实体类型**：
- `character`: 人物
- `faction`: 势力
- `location`: 地点
- `item`: 道具
- `world`: 世界状态

**功能清单**：
- 创建/更新实体（upsert）
- 列出实体（按类型、状态、标签筛选）
- 获取实体详情
- 批量修改（bulk_patch）
- 实体搜索
- 导入导出（P1）

**人物字段**（data JSONB 中的标准字段）：
- `core_profile`: 核心设定
- `personality`: 性格底色
- `desire`: 当前欲望/长期目标
- `fear_or_flaw`: 缺陷/恐惧/弱点
- `power_level`: 当前境界/等级
- `abilities`: 能力列表
- `resources`: 资源
- `equipment`: 装备
- `faction`: 所属势力
- `state_tags`: 状态标签（injured / hidden_identity 等）
- `knowledge_state`: 角色知道什么
- `reader_knowledge`: 读者知道什么
- `current_location`: 当前位置
- `current_goal`: 当前目标
- `last_seen_chapter`: 最后出场章节

**势力字段**：
- `faction_type`: family / sect / company / guild / kingdom / organization / other
- `core_profile`: 核心设定
- `leader`: 领袖
- `members`: 成员列表
- `territory`: 领地
- `resources`: 资源
- `power_level`: 实力等级
- `attitude_to_protagonist`: 对主角态度
- `current_status`: 当前状态
- `known_secrets`: 已知秘密

**地点字段**：
- `location_type`: city / sect / secret_realm / dungeon / country / world / other
- `description`: 描述
- `rules`: 地点特殊规则
- `owners`: 所有者
- `connected_locations`: 关联地点
- `important_events`: 重要事件
- `current_status`: 当前状态
- `hidden_information`: 隐藏信息

**道具字段**：
- `item_type`: weapon / artifact / medicine / token / book / resource / other
- `description`: 描述
- `abilities`: 能力
- `limitations`: 限制
- `owner`: 所有者
- `origin`: 来源
- `current_status`: 当前状态
- `reveal_status`: unknown / hinted / revealed / misdirected

**实体基础字段**：
- `id`: UUID，主键
- `project_id`: UUID，关联 projects
- `entity_type`: 实体类型
- `name`: 字符串
- `aliases`: 文本数组
- `profile`: JSONB，核心档案
- `lifecycle_status`: active / inactive / departed / deceased / destroyed
- `importance`: low / medium / high / critical
- `tags`: 文本数组
- `first_appearance_chapter`: 整数
- `last_appearance_chapter`: 整数
- `source_type`: 字符串
- `metadata`: JSONB
- `created_at`, `updated_at`: 时间戳

**约束规则**：
- 同一项目内 `entity_type + name` 唯一
- 实体核心设定和当前状态分开存储
- 当前状态可由章节提交重建
- 人工修正必须记录来源和原因

#### 3.4.2 状态快照

**需求描述**：某个实体在某个时间点的结构化状态。

**功能清单**：
- 创建状态快照
- 列出快照（按实体、按章节）
- 获取当前状态
- 状态历史追溯

**数据字段**：
- `id`: UUID，主键
- `project_id`: UUID，关联 projects
- `entity_id`: UUID，关联 state_entities
- `chapter_id`: UUID，关联 chapters，可空
- `state`: JSONB，状态数据
- `is_current`: 布尔
- `source_commit_id`: UUID，关联 chapter_commits，可空

**状态生命周期字段**：
- `effective_chapter`: 整数，生效起始章节
- `expire_chapter`: 整数，过期章节
- `effective_volume`: 整数，生效起始卷
- `expire_volume`: 整数，过期卷
- `duration_type`: permanent / temporary / until_event / until_reviewed
- `expires_on_event`: 字符串，事件触发过期
- `confidence`: 数值，置信度
- `source_type`: 字符串，来源类型
- `source_id`: UUID，来源 ID
- `change_reason`: 文本，变更原因

**约束规则**：
- 过期状态默认不进入上下文包
- 即将过期状态可提示（3章内）
- 状态来源可追踪
- 临时状态必须有有效范围

#### 3.4.3 实体关系

**需求描述**：人物、势力、地点、道具之间的关系网络。

**关系类型**：
- `ally`: 盟友
- `enemy`: 敌人
- `mentor`: 师徒
- `lover`: 恋人
- `family`: 家人
- `rival`: 对手
- `debt`: 恩情/债务
- `secret`: 共享秘密
- `other`: 其他

**态度类型**：
- `trust`: 信任
- `fear`: 恐惧
- `hate`: 仇恨
- `admire`: 敬佩
- `suspicious`: 怀疑
- `neutral`: 中立

**功能清单**：
- 创建/更新关系
- 列出关系（按实体、按类型）
- 关系图查询（P1）
- 关系状态变更

**数据字段**：
- `source_entity_id`: UUID，源实体
- `target_entity_id`: UUID，目标实体
- `relation_type`: 关系类型
- `attitude`: 态度
- `intensity`: 整数 0-100，强度
- `known_by_source`: 布尔，源方是否知道
- `known_by_target`: 布尔，目标方是否知道
- `known_by_reader`: 布尔，读者是否知道
- `status`: active / hidden / broken / resolved
- `source_chapter`: 整数，来源章节
- `source_commit_id`: UUID，来源提交
- `metadata`: JSONB
- `created_at`: 时间戳

**约束规则**：
- A 对 B 的态度变化，不代表 B 自动知道
- 势力开战，不代表所有成员立刻知道
- 系统可以生成联动更新提案，但不应悄悄把推断写成硬事实
- 关系必须有可见性区分

---

### 3.5 剧情进度层

#### 3.5.1 卷管理

**需求描述**：管理小说的分卷结构。

**功能清单**：
- 创建/更新卷
- 列出卷
- 获取当前卷
- 卷状态管理（planned / active / complete）

**数据字段**：
- `id`: UUID，主键
- `project_id`: UUID，关联 projects
- `volume_no`: 整数，卷号
- `title`: 字符串
- `outline`: 文本，卷大纲
- `status`: planned / active / complete
- `metadata`: JSONB
- `created_at`, `updated_at`: 时间戳

**约束规则**：
- 同一项目内 `volume_no` 唯一

#### 3.5.2 剧情线管理

**需求描述**：管理主线、支线、情感线、对抗线等剧情脉络。

**剧情线类型**：
- `main`: 主线
- `side`: 支线
- `romance`: 情感线
- `mystery`: 悬疑线
- `enemy`: 对抗线
- `growth`: 成长线

**功能清单**：
- 创建/更新剧情线
- 列出剧情线（按类型、状态、重要度筛选）
- 推进剧情线
- 检测停滞剧情线
- 剧情线状态管理

**数据字段**：
- `id`: UUID，主键
- `project_id`: UUID，关联 projects
- `key`: 字符串，项目内唯一
- `title`: 字符串
- `thread_type`: 剧情线类型
- `status`: open / developing / resolved / paused / abandoned
- `importance`: low / medium / high / critical
- `current_stage`: 字符串，当前阶段
- `last_advanced_chapter`: 整数，最后推进章节
- `stalled_threshold`: 整数，停滞阈值（章数）
- `metadata`: JSONB
- `created_at`, `updated_at`: 时间戳

**约束规则**：
- 同一项目内 `key` 唯一
- 长时间未推进应触发告警

#### 3.5.3 章节计划

**需求描述**：每章的写作计划和细纲。

**功能清单**：
- 创建章节计划
- 列出章节计划
- 获取章节计划详情
- 更新章节计划
- 标记已使用/已废弃

**数据字段**：
- `id`: UUID，主键
- `project_id`: UUID，关联 projects
- `chapter_id`: UUID，关联 chapters，可空
- `chapter_no`: 整数
- `plan`: JSONB，计划内容
- `status`: planned / used / superseded
- `created_by`: UUID
- `created_at`, `updated_at`: 时间戳

---

### 3.6 伏笔管理

#### 3.6.1 伏笔 CRUD

**需求描述**：管理小说中的伏笔及其生命周期。

**伏笔状态**：
- `planted`: 已埋设
- `developing`: 发展中
- `misdirected`: 误导中
- `ready_to_payoff`: 可回收
- `paid_off`: 已回收
- `abandoned`: 废弃

**伏笔层级**：
- `surface`: 明线伏笔（读者能感知）
- `hidden`: 暗线伏笔（读者隐约感知）
- `behind_the_scene`: 幕后伏笔（作者/系统知道）

**功能清单**：
- 创建/更新伏笔
- 列出伏笔（按状态、重要度、层级、卷筛选）
- 获取伏笔详情
- 批量状态更新
- 伏笔关联管理
- 伏笔回收

**数据字段**：
- `id`: UUID，主键
- `project_id`: UUID，关联 projects
- `key`: 字符串，项目内唯一
- `title`: 字符串
- `status`: 伏笔状态
- `importance`: low / medium / high / critical
- `layer`: 伏笔层级
- `planted_chapter_id`: UUID，埋设章节
- `payoff_chapter_id`: UUID，回收章节
- `expected_payoff_range`: 字符串，预期回收范围
- `must_payoff`: 布尔，是否必须回收
- `payoff_deadline_chapter`: 整数，回收截止章节
- `payoff_deadline_volume`: 整数，回收截止卷
- `overdue_policy`: warn / create_task / block_generation
- `parent_foreshadowing_id`: UUID，父伏笔
- `related_foreshadowing_ids`: UUID 数组，关联伏笔
- `trigger_on_payoff_ids`: UUID 数组，回收时触发
- `blocks_payoff_until_ids`: UUID 数组，阻塞回收
- `reader_known`: 布尔，读者是否知道
- `protagonist_known`: 布尔，主角是否知道
- `related_character_ids`: UUID 数组
- `related_item_ids`: UUID 数组
- `related_location_ids`: UUID 数组
- `payload`: JSONB
- `created_at`, `updated_at`: 时间戳

**约束规则**：
- 同一项目内 `key` 唯一
- 每章提交后要更新伏笔状态
- 审查系统要检查是否误揭示、忘回收、回收不足
- 准备上下文时要检索当前相关伏笔

#### 3.6.2 伏笔逾期检查

**需求描述**：自动检查逾期未回收的伏笔，按重要度触发不同告警。

**告警阈值**：
- `critical`: 超过预计回收点 5 章未处理 → 创建 high 修订任务
- `high`: 超过预计回收点 10 章未处理 → 创建 medium 修订任务
- `medium`: 超过预计回收点 20 章未处理 → Web 提醒
- `low`: 仅在卷尾结算时提醒

**功能清单**：
- 检查逾期伏笔
- 批量检查
- 自动创建修订任务（按配置）
- 伏笔回收看板

---

### 3.7 规则系统

#### 3.7.1 规则管理

**需求描述**：约束 AI 行为的规则库，支持多种类型、严重级别和作用范围。

**规则类型**：
- `canon`: 硬设定，不可违背
- `character`: 人物性格、说话方式、行为边界
- `plot`: 剧情推进原则
- `style`: 文风和表达习惯
- `pacing`: 节奏要求
- `commercial`: 网文爽点、期待感、章末钩子
- `forbidden`: 禁止事项
- `reveal_lock`: 禁止提前揭露的信息
- `review`: 审查规则
- `lesson`: 从审查中沉淀出的经验
- `compliance`: 合规审查规则
- `power_system`: 力量体系规则

**严重级别**：
- `info`: 信息
- `warning`: 警告
- `error`: 错误
- `critical`: 严重

**规则状态**：
- `active`: 生效中
- `disabled`: 已禁用
- `superseded`: 已被取代

**作用范围类型**：
- `global`: 全局
- `volume`: 分卷
- `arc`: 篇章
- `plot_thread`: 剧情线
- `chapter_range`: 章节范围
- `character`: 角色
- `faction`: 势力
- `location`: 地点

**功能清单**：
- 创建/更新规则
- 列出规则（按类型、严重度、状态筛选）
- 获取当前有效规则（按章节、卷、角色等过滤）
- 批量启用/禁用
- 规则冲突检测
- 规则冲突解决

**数据字段**：
- `id`: UUID，主键
- `project_id`: UUID，关联 projects
- `rule_key`: 字符串，项目内唯一
- `rule_type`: 规则类型
- `title`: 字符串
- `content`: 文本
- `severity`: info / warning / error / critical
- `status`: active / disabled / superseded
- `version`: 整数
- `scope_type`: 作用范围类型
- `scope_ref`: 字符串，范围引用
- `effective_chapter_no`: 整数，生效起始章节
- `expire_chapter_no`: 整数，过期章节
- `effective_volume_no`: 整数，生效起始卷
- `expire_volume_no`: 整数，过期卷
- `active_from_event`: 字符串，事件激活
- `expire_on_event`: 字符串，事件过期
- `priority`: 整数，优先级
- `is_temporary`: 布尔，是否临时规则
- `conflict_policy`: override / merge / manual_review / disable_lower
- `scope_config`: JSONB
- `supersedes_rule_ids`: UUID 数组
- `blocked_by_rule_ids`: UUID 数组
- `metadata`: JSONB
- `created_at`, `updated_at`: 时间戳

**规则优先级（从高到低）**：
1. critical canon
2. reveal_lock
3. forbidden
4. character core
5. plot
6. power_system
7. style
8. pacing
9. commercial
10. review
11. lesson

**生效范围优先级**：
- chapter > arc > volume > character/faction > global

**约束规则**：
- 低范围规则不能违反高优先级硬规则
- 新规则进入前检查冲突
- 冲突必须记录和人工处理
- Critical 规则不可被 token 预算截断

#### 3.7.2 规则提案

**需求描述**：模型、审查系统、本地工具或用户发现需要长期生效的规则时，提交待审批的规则提案。

**提案类型**：
- `create`: 创建新规则
- `update`: 更新现有规则
- `disable`: 禁用规则

**提案状态**：
- `proposed`: 已提议
- `auto_applied`: 自动应用
- `approved`: 已批准
- `rejected`: 已拒绝
- `superseded`: 已被取代

**功能清单**：
- 创建规则提案
- 列出提案（按状态、类型筛选）
- 审批/拒绝提案
- 自动应用低风险规则（可配置）

**数据字段**：
- `id`: UUID，主键
- `project_id`: UUID，关联 projects
- `source_type`: review / user / commit / import
- `source_id`: UUID，可空
- `proposal_type`: create / update / disable
- `target_rule_id`: UUID，可空
- `title`: 字符串
- `content`: 文本
- `confidence`: 数值，置信度
- `agreement`: JSONB，提案详情（rule_type, scope_type, severity 等）
- `status`: proposed / auto_applied / approved / rejected / superseded
- `created_by`, `approved_by`: UUID
- `created_at`, `resolved_at`: 时间戳

#### 3.7.3 规则版本

**需求描述**：保存规则变更历史，支持追溯。

**数据字段**：
- `id`: UUID，主键
- `project_id`: UUID，关联 projects
- `rule_id`: UUID，关联 canon_rules
- `version`: 整数
- `content`: 文本
- `change_reason`: 文本
- `source`: 字符串
- `created_at`: 时间戳

#### 3.7.4 合规审查规则

**需求描述**：专门用于合规检查的规则，支持关键词、正则匹配。

**规则分类**：
- 政治敏感
- 色情低俗
- 暴力血腥
- 宗教敏感
- 其他违规

**功能清单**：
- 创建/更新合规规则
- 列出合规规则
- 文本合规检查
- 命中 critical 可阻断生成

---

### 3.8 章节与提交

#### 3.8.1 章节管理

**需求描述**：管理小说的章节列表和状态。

**章节状态**：
- `planned`: 计划中
- `drafted`: 草稿中
- `reviewed`: 已审查
- `accepted`: 已接受
- `published`: 已发布

**功能清单**：
- 创建章节
- 列出章节（分页、按卷、按状态筛选）
- 获取章节详情
- 更新章节状态
- 章节元数据管理

**数据字段**：
- `id`: UUID，主键
- `project_id`: UUID，关联 projects
- `chapter_no`: 整数
- `volume_no`: 整数，可空
- `title`: 字符串，可空
- `status`: 章节状态
- `local_path_hint`: 字符串，本地路径提示
- `content_hash`: 字符串，内容哈希
- `word_count`: 整数
- `created_at`, `updated_at`: 时间戳

**约束规则**：
- 同一项目内 `chapter_no` 唯一
- 正文不保存在 MCP，只保存路径提示和哈希

#### 3.8.2 章节提交（Chapter Commit）

**需求描述**：每章完成后的结构化提交记录，是状态更新的来源。

**提交类型**：
- `draft_commit`: 草稿提交
- `review_commit`: 审查提交
- `final_commit`: 最终提交
- `rollback_commit`: 回滚提交

**功能清单**：
- 提交章节 commit
- 列出 commit 历史
- 接受 commit（更新状态）
- 回滚 commit

**数据字段**：
- `id`: UUID，主键
- `project_id`: UUID，关联 projects
- `chapter_id`: UUID，关联 chapters
- `commit_no`: 整数
- `commit_type`: 提交类型
- `payload`: JSONB
- `accepted`: 布尔
- `accepted_by`: UUID，可空
- `accepted_at`: 时间戳，可空
- `created_by`: UUID，可空
- `created_at`: 时间戳

**Payload 必需字段**：
```json
{
  "summary": "short chapter summary",
  "events": [],
  "character_state_changes": [],
  "world_state_changes": [],
  "new_facts": [],
  "foreshadowing_changes": [],
  "plot_thread_changes": [],
  "rule_warnings": [],
  "next_chapter_hooks": [],
  "local_files": []
}
```

**约束规则**：
- 草稿 commit 不更新全局状态快照
- 草稿 commit 不进入默认上下文包
- final commit 才能更新当前状态、摘要、伏笔
- review commit 可创建审查任务，但不一定改变 Canon

---

### 3.9 记忆与检索

#### 3.9.1 章节摘要

**需求描述**：分层级的章节摘要，用于长期记忆检索。

**摘要层级**：
- `chapter_summary`: 单章摘要
- `ten_chapter_summary`: 十章摘要
- `volume_summary`: 卷摘要
- `book_summary`: 全书摘要

**每级摘要固定维度**：
- `main_events`: 主要事件
- `character_changes`: 人物变化
- `relationship_changes`: 关系变化
- `world_changes`: 世界变化
- `faction_changes`: 势力变化
- `item_changes`: 道具变化
- `foreshadowing_changes`: 伏笔变化
- `rule_impacts`: 规则影响
- `unresolved_hooks`: 未解决钩子
- `next_relevant_context`: 下一步相关上下文

**功能清单**：
- 创建摘要
- 列出摘要（按层级、按范围）
- 获取摘要详情
- 摘要搜索

**数据字段**：
- `id`: UUID，主键
- `project_id`: UUID，关联 projects
- `chapter_id`: UUID，关联 chapters，可空
- `summary_type`: chapter / ten_chapter / arc / volume / mega_arc / book
- `range_start`: 整数，范围起始，可空
- `range_end`: 整数，范围结束，可空
- `content`: 文本
- `structured_content`: JSONB，结构化摘要
- `metadata`: JSONB
- `created_at`: 时间戳

#### 3.9.2 事件

**需求描述**：小说中的重要事件，作为记忆检索的基本单元。

**功能清单**：
- 创建事件
- 列出事件（按章节、按人物、按地点筛选）
- 事件搜索
- 事件关联查询

**数据字段**：
- `id`: UUID，主键
- `project_id`: UUID，关联 projects
- `chapter_id`: UUID，关联 chapters，可空
- `event_order`: 整数，可空
- `title`: 字符串，可空
- `summary`: 文本
- `characters`: 文本数组
- `locations`: 文本数组
- `causes`: JSONB
- `consequences`: JSONB
- `metadata`: JSONB
- `created_at`: 时间戳

#### 3.9.3 记忆块与向量检索

**需求描述**：可被检索的长期信息片段，支持全文检索和向量检索。

**记忆块来源类型**：
- `chapter_summary`: 章节摘要
- `event`: 事件
- `state`: 状态
- `rule`: 规则
- `reference`: 参考资料
- `review`: 审查
- `lesson`: 经验教训

**功能清单**：
- 创建记忆块
- 全文检索
- 向量检索
- 混合检索（全文 + 向量 + 结构化过滤）
- 增量索引
- 重建索引

**数据字段**：
- `id`: UUID，主键
- `project_id`: UUID，关联 projects
- `source_type`: 来源类型
- `source_id`: UUID，可空
- `chunk_key`: 字符串
- `content`: 文本
- `qdrant_collection`: 字符串，可空
- `qdrant_point_id`: 字符串，可空
- `metadata`: JSONB
- `search_vector`: tsvector，生成列
- `created_at`: 时间戳

**检索评分字段**：
- `score`: 综合分数
- `source_type`: 来源类型
- `source_id`: 来源 ID
- `recency_score`: 时效性分数
- `importance_score`: 重要度分数
- `structural_match_score`: 结构化匹配分数
- `final_score`: 最终分数
- `reason`: 入选理由

**检索策略**：
- 结构化过滤 + 关键词检索 + 向量检索 + 去重/重排
- 结构化过滤优先级：project > branch > volume > plot_thread > entity > foreshadowing > status > chapter_range
- 低于相关性阈值的内容不得进入上下文包
- 冷数据默认降权
- 已归档支线默认不加载
- 检索命中必须记录进入上下文的理由

---

### 3.10 上下文包（Context Pack）

#### 3.10.1 上下文包生成

**需求描述**：生成有限上下文包，不让 AI 读全书。

**上下文 Profile**：
- `opening_volume`: 卷首，侧重卷目标、全局 Canon、新阶段规则
- `daily_chapter`: 日常推进，侧重近期摘要、人物状态、当前剧情线
- `battle_chapter`: 战斗章节，侧重力量体系、人物状态、战斗限制
- `reveal_chapter`: 揭示章节，侧重 reveal lock、读者已知/未知信息
- `payoff_chapter`: 伏笔回收，侧重活跃伏笔、前置条件、回收方式
- `ending_volume`: 卷尾，侧重伏笔结算、状态结算、下卷钩子
- `review_consistency`: 一致性审查，侧重 Canon、状态、规则、伏笔
- `review_commercial`: 商业节奏审查，侧重爽点、节奏、钩子、读者期待

**功能清单**：
- 生成章节上下文包
- 生成审查上下文包
- 上下文包验证
- 预生成校验
- 分段上下文包

**上下文包组成**：
- 当前章节计划
- 当前卷目标
- 当前人物状态
- 相关 Canon
- 相关伏笔
- 相关剧情线
- 最近章节摘要
- 长期记忆检索结果
- 当前生效规则
- 最近审查经验

**Token 预算分配（默认）**：
- Canon 摘要与硬设定：<= 20%
- 人物/势力/地点当前状态：<= 15%
- 伏笔与剧情线：<= 10%
- 历史摘要与长期记忆：<= 30%
- 规则与禁忌：<= 15%
- 审查经验：<= 10%

**默认 Token 预算**：
- 轻量任务：8k-12k tokens
- 普通章节：16k-24k tokens
- 超长篇关键章节：24k-32k tokens
- 审查任务：按审查维度单独预算

#### 3.10.2 上下文包验证

**需求描述**：验证上下文包的完整性和合规性。

**检查项**：
- 是否缺少硬 Canon
- 当前人物状态是否冲突
- 活跃伏笔是否与章节计划冲突
- 当前规则是否互相冲突
- 是否存在 Critical 审查任务未解决
- 是否存在禁止提前揭示的信息
- 是否加载了过期状态

**验证结果**：
- `pass`: 通过
- `warning`: 警告
- `blocked`: 阻断

#### 3.10.3 预生成校验

**需求描述**：在生成前检查是否满足生成条件。

**功能清单**：
- 预生成检查
- 返回是否可生成
- 返回警告和阻断项

#### 3.10.4 分段上下文

**需求描述**：长章节可拆成多段生成，每段有不同的上下文侧重。

**段落类型**：
- `opening`: 开篇
- `middle`: 中段
- `climax`: 高潮
- `ending_hook`: 结尾钩子

**每段上下文侧重**：
- 开篇：承接上一章、当前场景、读者期待
- 中段：冲突推进、人物状态、局部规则
- 高潮：力量体系、战斗限制、关键伏笔
- 结尾：章末钩子、未揭示信息、下一章引导

---

### 3.11 POV 视角隔离

#### 3.11.1 视角模式

**需求描述**：网文生成必须支持 POV 视角控制。

**视角模式**：
- `protagonist`: 主角视角
- `character`: 单角色视角
- `omniscient`: 上帝视角
- `reader`: 读者视角
- `reviewer`: 审查视角

**可见性策略**：
- `strict`: 严格隐藏角色未知信息（悬疑、幕后流）
- `balanced`: 默认网文模式，隐藏关键秘密，但允许加载作者提示
- `full`: 审查、设定维护、上帝视角分析

**功能清单**：
- 指定 POV 模式生成上下文
- 按角色过滤可见信息
- 按读者视角过滤

**视角规则**：
- 主角视角不能加载主角不知道的秘密
- 单角色视角不能加载该角色未知的幕后事实
- 上帝视角可加载完整事实，但写作提示必须避免直接泄露
- 审查视角可加载全部事实，用于检查是否误揭示
- 读者视角应加载读者已知事实，用于期待管理和悬念校验

---

### 3.12 审查系统

#### 3.12.1 审查配置

**需求描述**：配置多模型审查的 council。

**功能清单**：
- 创建审查配置
- 列出审查配置
- 更新审查配置
- 设置默认配置

**数据字段**：
- `id`: UUID，主键
- `project_id`: UUID，关联 projects
- `name`: 字符串
- `config`: JSONB
- `is_active`: 布尔
- `created_at`, `updated_at`: 时间戳

**配置内容**：
- 模型列表（模型名称、权重、审查维度）
- 维度权重配置
- 严重级别映射
- 自动创建修订任务的阈值
- 自动创建规则提案的阈值

#### 3.12.2 审查任务

**需求描述**：每次章节审查的任务记录。

**审查任务状态**：
- `pending`: 待处理
- `running`: 进行中
- `complete`: 已完成
- `failed`: 失败
- `aggregated`: 已聚合
- `blocked`: 阻断
- `resolved`: 已解决

**功能清单**：
- 启动审查任务
- 列出审查任务
- 获取审查任务详情
- 更新任务状态

**数据字段**：
- `id`: UUID，主键
- `project_id`: UUID，关联 projects
- `chapter_id`: UUID，关联 chapters
- `status`: 任务状态
- `config`: JSONB
- `created_by`: UUID，可空
- `created_at`, `updated_at`: 时间戳

#### 3.12.3 审查报告

**需求描述**：每个模型的审查报告和聚合报告。

**功能清单**：
- 提交模型报告
- 列出报告（按审查任务、按模型）
- 获取报告详情
- 聚合多模型报告

**数据字段**：
- `id`: UUID，主键
- `project_id`: UUID，关联 projects
- `review_job_id`: UUID，关联 review_jobs
- `chapter_id`: UUID，关联 chapters
- `model_id`: 字符串，可空
- `report_type`: model / consensus
- `score`: 数值
- `findings`: JSONB
- `summary`: 文本
- `created_at`: 时间戳

**审查维度**：

基础维度：
- 设定一致性
- 人物是否 OOC
- 剧情是否重复
- 节奏是否拖沓
- 爽点是否到位
- 章末钩子是否有效
- 是否误揭示伏笔
- 是否忘记重要伏笔
- 是否违背力量体系
- 是否违背人物当前状态
- 是否产生新设定但未记录

进阶维度：
- 读者期待管理
- 主角主动性
- 冲突密度
- 信息释放节奏
- 反派压迫感
- 成长反馈
- 商业爽点强度
- 连载稳定性

**问题严重级别**：
- `critical`: 阻断后续生成，必须人工处理
- `warning` / `high`: 生成修订建议，可继续但需提示
- `info` / `low`: 记录经验，不阻断

#### 3.12.4 修订任务

**需求描述**：从审查发现中生成的可执行修订任务。

**修订任务状态**：
- `open`: 待处理
- `accepted`: 已接受
- `dismissed`: 已驳回
- `done`: 已完成

**功能清单**：
- 从审查 findings 自动创建修订任务
- 列出修订任务
- 更新任务状态
- 分配负责人
- 任务详情

**数据字段**：
- `id`: UUID，主键
- `project_id`: UUID，关联 projects
- `chapter_id`: UUID，关联 chapters
- `review_job_id`: UUID，关联 review_jobs，可空
- `title`: 字符串
- `description`: 文本
- `severity`: low / medium / high / blocking
- `status`: open / accepted / dismissed / done
- `assignee_id`: UUID，可空
- `metadata`: JSONB
- `created_at`, `updated_at`: 时间戳

#### 3.12.5 审查学习

**需求描述**：从审查结果中提取可复用经验，形成规则提案、状态提案和伏笔提案。

**功能清单**：
- 提取规则提案
- 提取状态更新建议
- 提取伏笔更新建议
- 评估模型质量
- 学习闭环（learn_from_review）

**审查发现分流规则**：
- 硬错误 → revision_tasks
- 可复用写作经验 → rules.propose(type=lesson/style/review)
- 设定补充 → rules.propose(type=canon/character/plot)
- 状态变化遗漏 → state update proposal
- 伏笔问题 → foreshadowing update proposal
- 参考套路 → reference item

**约束规则**：
- 审查只能生成提案，不能自动改写硬 Canon
- 状态和伏笔只生成结构化建议，不直接改写正式事实
- 规则提案批准时会读取 agreement.rule，按真实类型创建规则

#### 3.12.6 模型质量评估

**需求描述**：评估每个审查模型的质量，支持动态权重调整。

**评估指标**：
- 提交报告数量
- 被人工确认的问题数量
- 被人工驳回的问题数量
- 生成规则提案数量
- 规则提案通过率
- 修订任务完成率
- 平均严重级别
- 与其他模型的一致度

**功能清单**：
- 模型质量评估
- 质量统计报表
- 权重调整建议

---

### 3.13 模型与成本管理

#### 3.13.1 模型配置

**需求描述**：管理可用的模型配置，支持分层和路由。

**模型层级**：
- `cheap`: 廉价模型（用于简单任务）
- `standard`: 标准模型（日常使用）
- `premium`: 高级模型（关键任务）
- `local`: 本地模型（离线/隐私场景）

**功能清单**：
- 创建/更新模型 profile
- 列出模型 profile
- 模型路由（按任务类型选择模型）
- 路由规则管理

**数据字段**：
- `id`: UUID，主键
- `project_id`: UUID，关联 projects，可空（全局模型可空）
- `model_key`: 字符串
- `model_name`: 字符串
- `tier`: cheap / standard / premium / local
- `provider`: 字符串
- `base_url`: 字符串，可空
- `supports`: 文本数组，支持的任务类型
- `cost_per_1k_input`: 数值
- `cost_per_1k_output`: 数值
- `max_tokens`: 整数
- `rpm_limit`: 整数，每分钟请求限制
- `tpm_limit`: 整数，每分钟 token 限制
- `is_active`: 布尔
- `metadata`: JSONB
- `created_at`, `updated_at`: 时间戳

**约束规则**：
- 不保存 API key，API key 由本地工具保管

#### 3.13.2 模型路由

**需求描述**：根据任务类型、成本预算等因素自动选择模型。

**路由规则字段**：
- `id`: UUID，主键
- `project_id`: UUID，关联 projects，可空
- `rule_name`: 字符串
- `task_type`: 字符串
- `priority_model_key`: 字符串
- `fallback_model_keys`: 文本数组
- `min_tier`: 字符串
- `max_cost_per_1k`: 数值
- `conditions`: JSONB
- `sort_order`: 整数
- `is_active`: 布尔
- `created_at`, `updated_at`: 时间戳

**功能清单**：
- 模型路由查询
- 路由规则管理
- Fallback 机制

#### 3.13.3 成本统计

**需求描述**：记录和统计 token 使用和成本。

**功能清单**：
- 记录使用量
- 成本报表（按日/任务类型/模型/项目）
- 成本预估
- 异常告警

**数据字段**：
- `id`: UUID，主键
- `project_id`: UUID，关联 projects，可空
- `model_key`: 字符串
- `task_type`: 字符串
- `input_tokens`: 整数
- `output_tokens`: 整数
- `total_tokens`: 整数
- `cost_amount`: 数值
- `cost_currency`: 字符串
- `context_pack_id`: UUID，可空
- `review_job_id`: UUID，可空
- `chapter_id`: UUID，可空
- `metadata`: JSONB
- `created_at`: 时间戳

---

### 3.14 同步与本地绑定

#### 3.14.1 本地项目绑定

**需求描述**：MCP 记录本地项目的路径提示和文件哈希，用于同步和审计。

**功能清单**：
- 注册本地绑定
- 提交文件哈希
- 列出本地绑定
- 同步状态检查

**数据字段**：
- `id`: UUID，主键
- `project_id`: UUID，关联 projects
- `user_id`: UUID，关联 users
- `client_id`: 字符串
- `local_root_hint`: 字符串
- `manifest`: JSONB
- `last_sync_at`: 时间戳，可空
- `created_at`, `updated_at`: 时间戳

**约束规则**：
- 同一项目、用户、客户端唯一
- MCP 不主动覆盖本地文件

#### 3.14.2 冲突管理

**需求描述**：处理本地和 MCP 之间的数据冲突。

**冲突类型**：
- 本地设定文档被人工修改
- Web 中结构化数据被修改
- 审查提案修改了同一规则
- 本地草稿与正式提交不一致

**冲突解决策略**：
- `local_wins`: 本地优先
- `mcp_wins`: MCP 优先
- `manual_merge`: 人工合并
- `create_proposal`: 创建提案
- `keep_both_as_branches`: 保留两者为分支

**默认策略**：
- 正文和本地 Markdown：本地优先
- 结构化 Canon：MCP 优先，但允许人工合并
- 审查提案：不直接覆盖，进入审批
- 草稿：默认不影响正式数据

**功能清单**：
- 列出冲突
- 解决冲突
- 冲突历史

#### 3.14.3 项目导入导出

**需求描述**：支持项目数据的批量导入导出。

**导出内容**：
- Canon 文档
- 规则
- 实体
- 当前状态快照
- 伏笔
- 卷
- 剧情线
- 本地绑定信息（可选）

**功能清单**：
- 导出项目包（JSON）
- 导入初始化项目包
- 导入本地 manifest
- 导入结果统计

---

### 3.15 参考库

#### 3.15.1 参考来源

**需求描述**：参考资料的来源管理。

**来源类型**：
- `webnovel_writer`: webnovel-writer 项目
- `manual`: 手动创建
- `import`: 导入

**功能清单**：
- 创建参考来源
- 列出参考来源
- 更新参考来源

**数据字段**：
- `id`: UUID，主键
- `workspace_id`: UUID，关联 workspaces，可空
- `project_id`: UUID，关联 projects，可空
- `source_type`: 来源类型
- `name`: 字符串
- `source_uri`: 字符串
- `license`: 字符串，可空
- `metadata`: JSONB
- `created_at`, `updated_at`: 时间戳

#### 3.15.2 参考条目

**需求描述**：具体的参考资料条目。

**条目类型**：
- `genre_template`: 题材模板
- `writing_pattern`: 写作模式
- `scene_pattern`: 场景模式
- `trope`: 桥段/套路
- `rubric`: 评分标准
- `agent_prompt`: Agent 提示词

**功能清单**：
- 创建参考条目
- 列出参考条目
- 搜索参考条目
- 更新参考条目

**数据字段**：
- `id`: UUID，主键
- `source_id`: UUID，关联 reference_sources
- `project_id`: UUID，关联 projects，可空
- `item_type`: 条目类型
- `key`: 字符串
- `title`: 字符串
- `content`: 文本
- `metadata`: JSONB
- `created_at`, `updated_at`: 时间戳

---

### 3.16 审计与日志

#### 3.16.1 审计日志

**需求描述**：记录所有重要操作，支持追溯。

**功能清单**：
- 记录操作日志
- 查询审计日志（按项目、用户、操作类型、时间范围）
- 操作详情查看

**数据字段**：
- `id`: UUID，主键
- `workspace_id`: UUID，可空
- `project_id`: UUID，可空
- `user_id`: UUID，可空
- `action`: 字符串
- `resource_type`: 字符串
- `resource_id`: UUID，可空
- `payload`: JSONB
- `created_at`: 时间戳

---

## 4. 非功能需求

### 4.1 性能需求

| 指标 | 目标 | 说明 |
|------|------|------|
| 上下文包生成时间 | < 2s | 普通章节上下文包 |
| 检索响应时间 | < 200ms | BM25 检索 |
| 列表接口响应 | < 500ms | 分页列表，默认 20 条 |
| 单章提交处理 | < 5s | 接受 commit 并更新状态 |
| 并发用户数 | >= 100 | 同时在线用户 |
| 支持项目规模 | 2000 万字 | 单本小说规模 |

### 4.2 可扩展性需求

- **水平扩展**：MCP 服务支持水平扩展（P2）
- **数据库扩展**：支持读写分离（P2）
- **冷热分离**：支持冷热数据分层存储
- **插件扩展**：支持自定义规则和检索策略

### 4.3 可靠性需求

- **可用性**：99.9% 月度可用性
- **数据备份**：PostgreSQL 定时全量备份
- **数据恢复**：支持从备份恢复，RTO < 1 小时
- **降级能力**：
  - Qdrant 不可用时降级到 PostgreSQL 全文检索
  - Redis 不可用时限制并发
  - 模型 API 不可用时使用备用模型或草稿模式

### 4.4 安全需求

- **数据隔离**：工作区和项目级别的数据严格隔离
- **认证授权**：所有 API 需要认证和权限校验
- **审计日志**：所有写操作记录审计日志
- **敏感数据**：不保存用户的大模型 API key
- **密码安全**：密码哈希存储（bcrypt 或同等强度）
- **传输安全**：HTTPS 传输

### 4.5 兼容性需求

- **浏览器兼容**：支持最新 2 个版本的 Chrome、Firefox、Safari
- **MCP 协议**：兼容标准 MCP 协议
- **数据迁移**：支持数据库 schema 版本化迁移
- **向前兼容**：新版本不破坏已有数据

### 4.6 可维护性需求

- **代码规范**：统一的代码风格和规范
- **文档完整**：API 文档、数据模型文档、部署文档
- **监控告警**：服务健康检查、错误告警
- **日志规范**：结构化日志，便于排查

---

## 5. 数据模型总览

### 5.1 核心表清单

| 表名 | 类别 | 优先级 | 说明 |
|------|------|--------|------|
| users | 身份 | P0 | 用户表 |
| workspaces | 身份 | P0 | 工作区表 |
| workspace_members | 身份 | P0 | 工作区成员 |
| api_tokens | 身份 | P0 | API Token |
| projects | 项目 | P0 | 项目表 |
| project_members | 项目 | P0 | 项目成员 |
| local_project_bindings | 项目 | P0 | 本地项目绑定 |
| setting_categories | 全局设定 | P0 | 设定分类 |
| setting_field_definitions | 全局设定 | P1 | 分类字段定义 |
| setting_items | 全局设定 | P0 | 设定项目 |
| genre_canonical | 全局设定 | P0 | 题材规范化 |
| canon_documents | Canon | P0 | Canon 文档 |
| canon_document_versions | Canon | P0 | Canon 版本 |
| state_entities | 状态 | P0 | 状态实体 |
| state_snapshots | 状态 | P0 | 状态快照 |
| entity_relationships | 状态 | P0 | 实体关系 |
| chapters | 章节 | P0 | 章节表 |
| chapter_commits | 章节 | P0 | 章节提交 |
| chapter_summaries | 记忆 | P0 | 章节摘要 |
| events | 记忆 | P0 | 事件表 |
| memory_chunks | 记忆 | P0 | 记忆块 |
| volumes | 剧情 | P0 | 卷表 |
| plot_threads | 剧情 | P0 | 剧情线 |
| chapter_plans | 剧情 | P0 | 章节计划 |
| foreshadowing | 伏笔 | P0 | 伏笔表 |
| canon_rules | 规则 | P0 | 规则表 |
| rule_proposals | 规则 | P0 | 规则提案 |
| rule_versions | 规则 | P0 | 规则版本 |
| review_council_configs | 审查 | P0 | 审查配置 |
| review_jobs | 审查 | P0 | 审查任务 |
| review_reports | 审查 | P0 | 审查报告 |
| revision_tasks | 审查 | P0 | 修订任务 |
| model_profiles | 模型 | P0 | 模型配置 |
| model_route_rules | 模型 | P0 | 路由规则 |
| model_usage_records | 模型 | P0 | 使用记录 |
| reference_sources | 参考 | P1 | 参考来源 |
| reference_items | 参考 | P1 | 参考条目 |
| audit_logs | 审计 | P0 | 审计日志 |
| context_packs | 上下文 | P1 | 上下文包记录 |
| vector_index_jobs | 搜索 | P1 | 向量索引任务 |

### 5.2 ER 关系概览

```
users ──┐
        ├─ workspace_members ── workspaces
        ├─ project_members ── projects ── local_project_bindings
        └─ api_tokens

projects ─┬─ canon_documents ── canon_document_versions
          ├─ state_entities ── state_snapshots
          │                 └─ entity_relationships
          ├─ chapters ── chapter_commits
          │          ├─ chapter_summaries
          │          ├─ events
          │          └─ chapter_plans
          ├─ volumes
          ├─ plot_threads
          ├─ foreshadowing
          ├─ canon_rules ── rule_proposals
          │            └─ rule_versions
          ├─ review_council_configs
          ├─ review_jobs ── review_reports
          │            └─ revision_tasks
          ├─ model_profiles ── model_route_rules
          └─ model_usage_records

workspaces ─┬─ setting_categories ── setting_field_definitions
            │                   └─ setting_items
            ├─ genre_canonical
            └─ reference_sources ── reference_items
```

---

## 6. MCP 工具接口规范

### 6.1 工具命名规范

- 使用 `.` 分隔层级，如 `canon.doc.upsert`
- 动词在后，名词在前
- 列表用 `list`，单个用 `get`，创建或更新用 `upsert`

### 6.2 核心工具清单

#### 身份与权限
- `admin.health` - 健康检查
- `auth.whoami` - 当前身份
- `auth.create_api_token` - 创建 API Token
- `auth.list_api_tokens` - 列出 API Token
- `auth.revoke_api_token` - 撤销 API Token
- `user.create` - 创建用户
- `user.list` - 列出用户
- `workspace.create` - 创建工作区
- `workspace.list` - 列出工作区
- `workspace.add_member` - 添加工作区成员
- `project.create` - 创建项目
- `project.list` - 列出项目
- `project.add_member` - 添加项目成员
- `project.list_members` - 列出项目成员
- `project.register_local_binding` - 注册本地绑定

#### 全局设定
- `setting.category.list` - 列出分类
- `setting.category.get` - 获取分类详情
- `setting.category.upsert` - 创建/更新分类
- `setting.category.delete` - 删除分类
- `setting.item.list` - 列出设定项目
- `setting.item.get` - 获取设定详情
- `setting.item.upsert` - 创建/更新设定
- `setting.item.bulk_upsert` - 批量创建设定
- `setting.item.delete` - 删除设定
- `setting.search` - BM25 智能检索
- `setting.genre.resolve` - 题材规范化
- `setting.genre.list` - 列出 canonical genre
- `setting.csv.import` - CSV 导入
- `setting.csv.export` - CSV 导出

#### Canon 文档
- `canon.doc.upsert` - 创建/更新 Canon 文档
- `canon.doc.list` - 列出 Canon 文档
- `canon.doc.get` - 获取 Canon 文档
- `canon.doc.archive` - 归档 Canon 文档
- `canon.doc.history` - 查看历史版本
- `canon.doc.restore` - 恢复历史版本

#### 实体与状态
- `state.entity.upsert` - 创建/更新实体
- `state.entity.list` - 列出实体
- `state.entity.get` - 获取实体详情
- `state.entity.bulk_patch` - 批量修改实体
- `state.snapshot.upsert` - 创建状态快照
- `state.snapshot.list` - 列出状态快照
- `state.relationship.upsert` - 创建/更新关系
- `state.relationship.list` - 列出关系

#### 剧情
- `volume.upsert` - 创建/更新卷
- `volume.list` - 列出卷
- `plot.thread.upsert` - 创建/更新剧情线
- `plot.thread.list` - 列出剧情线
- `plot.thread.advance` - 推进剧情线
- `plot.thread.check_stalled` - 检查停滞剧情线
- `plot.upsert_foreshadowing` - 创建/更新伏笔
- `plot.list_foreshadowing` - 列出伏笔
- `plot.create_chapter_plan` - 创建章节计划
- `plot.list_chapter_plans` - 列出章节计划

#### 伏笔增强
- `foreshadowing.bulk_status_update` - 批量更新伏笔状态
- `foreshadowing.check_overdue` - 检查逾期伏笔
- `foreshadowing.link` - 关联伏笔
- `foreshadowing.payoff` - 回收伏笔

#### 规则
- `rules.list` - 列出规则
- `rules.upsert` - 创建/更新规则
- `rules.list_effective` - 列出当前有效规则
- `rules.check_conflict` - 检查规则冲突
- `rules.resolve_conflict` - 解决规则冲突
- `rules.bulk_toggle` - 批量启用/禁用
- `rules.propose` - 创建规则提案
- `rules.list_proposals` - 列出规则提案
- `rules.apply_proposal` - 应用规则提案

#### 合规审查
- `compliance.rule.upsert` - 创建/更新合规规则
- `compliance.rule.list` - 列出合规规则
- `compliance.check` - 合规检查

#### 工作流
- `workflow.prepare_chapter_context` - 准备章节上下文
- `workflow.submit_chapter_commit` - 提交章节 commit
- `workflow.validate_context_pack` - 验证上下文包
- `workflow.preflight_generation` - 预生成校验
- `workflow.prepare_segment_context` - 生成分段上下文
- `workflow.learn_from_review` - 从审查中学习

#### 审查
- `review.start_job` - 启动审查任务
- `review.upsert_council_config` - 更新审查配置
- `review.list_council_configs` - 列出审查配置
- `review.submit_model_report` - 提交模型报告
- `review.aggregate` - 聚合审查报告
- `review.list_revision_tasks` - 列出修订任务
- `review.update_revision_task` - 更新修订任务
- `review.extract_rule_proposals` - 提取规则提案
- `review.extract_state_updates` - 提取状态更新
- `review.extract_foreshadowing_updates` - 提取伏笔更新
- `review.evaluate_model_quality` - 评估模型质量

#### 模型与成本
- `model.profile.upsert` - 创建/更新模型配置
- `model.profile.list` - 列出模型配置
- `model.route` - 模型路由
- `model.route_rule.upsert` - 创建/更新路由规则
- `model.route_rule.list` - 列出路由规则
- `cost.record_usage` - 记录使用量
- `cost.report` - 成本报表

#### 同步
- `sync.import_local_manifest` - 导入本地 manifest
- `sync.import_initial_project_pack` - 导入初始化项目包
- `sync.submit_file_hashes` - 提交文件哈希
- `sync.list_conflicts` - 列出冲突
- `sync.resolve_conflict` - 解决冲突
- `sync.export_project_pack` - 导出项目包

#### 记忆与检索
- `memory.search` - 记忆搜索
- `memory.get_state` - 获取当前状态
- `memory.get_recent_summaries` - 获取最近摘要
- `memory.rebuild_projection` - 重建投影
- `memory.pending_vector_chunks` - 待索引向量块
- `memory.upsert_vector` - 更新向量索引
- `memory.vector_search` - 向量搜索

#### 参考库
- `reference.source_create` - 创建参考来源
- `reference.item_add` - 添加参考条目
- `reference.search` - 搜索参考

### 6.3 工具调用规范

**请求格式**：
```json
{
  "tool": "tool.name",
  "arguments": {
    "param1": "value1",
    "param2": "value2"
  }
}
```

**响应格式**：
```json
{
  "success": true,
  "data": {},
  "warnings": [],
  "errors": [],
  "pagination": {
    "total": 100,
    "offset": 0,
    "limit": 20
  }
}
```

**错误响应**：
```json
{
  "success": false,
  "error": {
    "code": "ERROR_CODE",
    "message": "Error description",
    "details": {}
  }
}
```

---

## 7. 验收标准

### 7.1 P0 验收标准（核心闭环）

#### 数据模型
- [ ] 所有 P0 表结构创建完成
- [ ] 迁移脚本可重复执行
- [ ] 索引创建完成
- [ ] 数据完整性约束生效

#### MCP 工具
- [ ] 所有 P0 工具注册完成
- [ ] 每个工具有入参校验
- [ ] 权限校验生效（工作区/项目隔离）
- [ ] 错误返回结构化（非 Python 异常栈）
- [ ] 列表接口支持分页和筛选

#### 核心功能
- [ ] 可创建工作区和项目
- [ ] 可维护 Canon 文档（CRUD + 版本）
- [ ] 可维护实体和状态
- [ ] 可维护伏笔和剧情线
- [ ] 可维护规则和规则提案
- [ ] 可生成章节上下文包
- [ ] 可提交章节 commit
- [ ] 可启动审查和提交报告
- [ ] 可从审查中提取规则提案
- [ ] 可导入初始化项目包
- [ ] 可导出项目包

#### 性能
- [ ] 上下文包生成 < 3s
- [ ] 列表接口 < 500ms
- [ ] 100 并发不崩溃

#### 安全
- [ ] 所有写操作需要认证
- [ ] 跨项目数据隔离
- [ ] 审计日志记录完整
- [ ] 不保存 API key

### 7.2 P1 验收标准（体验增强）

- [ ] 全局设定系统完整可用
- [ ] BM25 智能检索
- [ ] 题材规范化
- [ ] CSV 导入导出
- [ ] 实体关系管理
- [ ] 伏笔看板
- [ ] 规则冲突检测
- [ ] 上下文包缓存
- [ ] 审查模型质量评估
- [ ] 商业节奏统计
- [ ] 批量维护工具
- [ ] 项目 JSON 快照

### 7.3 P2 验收标准（远期扩展）

- [ ] 人物/势力关系图谱
- [ ] 剧情事件模拟器
- [ ] 真正冷热分库
- [ ] 图形化剧情网络
- [ ] 模板市场
- [ ] 多端开放接口
- [ ] 项目分支与一键回滚
- [ ] 外部通知集成
- [ ] 分布式 MCP 水平扩展

---

## 8. 术语表

| 术语 | 定义 |
|------|------|
| MCP | Model Context Protocol，模型上下文协议 |
| Context Pack | 上下文包，MCP 组装给 AI 的有限上下文 |
| Canon | 小说中已经确认为事实的硬设定 |
| POV | Point of View，视角 |
| Commit | 章节提交，结构化的章节记录 |
| Foreshadowing | 伏笔，小说中预先埋设的线索 |
| BM25 | 一种信息检索的排序算法 |
| Canonical Genre | 规范化题材，统一的题材分类体系 |
| Payoff | 伏笔回收，揭示伏笔的真相 |
| OOC | Out of Character，人物性格崩坏 |
| RLS | Row Level Security，行级安全 |
| Payload | 提交数据中的实际内容 |
| Tier | 模型层级（cheap/standard/premium/local） |
| Revision Task | 修订任务，从审查中生成的待办事项 |

---

## 9. 参考文档

- requirements-and-dev-brief.md - 需求与开发简报
- global-settings-design.md - 全局设定系统设计
- global-settings-optimization-plan.md - 全局设定优化方案
- data-model.md - 数据模型文档
- tool-schema.md - 工具接口文档
- architecture.md - 架构文档
- development-plan.md - 开发计划
