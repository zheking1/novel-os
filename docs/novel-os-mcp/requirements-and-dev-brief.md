# Novel OS MCP 需求与开发简报

本文档用于统一我们已经开发的功能、正在讨论的需求，以及后续开发 `novel-os-mcp` 和 Web 控制台时的判断标准。

核心结论：

```text
本地 AI 工具负责初始化、生成、写作、调用大模型。
MCP 负责保存小说长期数据、规则、事实、伏笔、状态、审查结果。
Web 控制台负责维护 MCP 中的数据，不负责小说初始化问答。
```

## 1. 系统目标

目标是支持超长篇网络小说，例如 2000 万字规模。

系统必须满足：

- MCP 存全量长期数据。
- AI 每次只读当前需要的局部上下文。
- 规则库守底线，防止风格、人物、设定漂移。
- 状态快照提供当前事实。
- 检索系统找相关历史。
- 摘要系统压缩长期剧情。
- 审查系统发现问题，并把可复用经验沉淀为规则或任务。
- 多用户、多工作区、多小说之间数据隔离。
- 正文、大纲、细纲、审查 Markdown 等人类可编辑产物保存在用户本地目录。
- MCP 只保存结构化事实、规则、索引、摘要、哈希、路径提示和审查结构化数据。

## 2. 当前已经完成的基础能力

### 2.1 NAS 部署基础

已准备并部署：

- `novel-os-mcp`
- PostgreSQL + pgvector
- Qdrant
- Redis 连接
- Web 控制台 `novel-os-web`
- Docker Compose 部署文件
- 健康检查脚本
- 备份脚本
- 日志脚本
- Web 管理员 token 刷新脚本

### 2.2 MCP 已有模块

当前 MCP 已有工具大类：

- `admin.*`：健康检查。
- `auth.*`：当前身份、API token 管理。
- `user.*`：用户管理。
- `workspace.*`：工作区管理。
- `project.*`：小说项目管理、本地绑定。
- `rules.*`：规则列表、规则写入、规则提案、提案审批。
- `plot.*`：伏笔、章节计划。
- `memory.*`：记忆搜索、状态查询、摘要、向量索引。
- `reference.*`：参考资料来源、参考条目、搜索。
- `workflow.*`：准备章节上下文、提交章节结构化结果。
- `review.*`：审查配置、审查任务、模型报告、聚合、修订任务。

### 2.3 数据库已有主要表

已具备的核心表：

- 身份与权限：`users`、`workspaces`、`workspace_members`、`project_members`、`api_tokens`
- 小说项目：`projects`、`local_project_bindings`
- 章节与提交：`chapters`、`chapter_commits`、`chapter_summaries`
- 记忆与事件：`events`、`memory_chunks`
- 人物/状态：`characters`、`character_states`、`state_entities`、`state_snapshots`
- 规则：`canon_rules`、`rule_versions`、`rule_proposals`
- 伏笔与剧情：`foreshadowing`、`volumes`、`plot_threads`、`chapter_plans`
- 审查：`review_jobs`、`review_reports`、`review_council_configs`、`revision_tasks`
- 参考库：`reference_sources`、`reference_items`
- 上下文包：`context_packs`
- 向量任务：`vector_index_jobs`
- 审计：`audit_logs`

### 2.4 Web 控制台现状

当前 Web 已具备：

- 初次设置账号。
- 登录/退出。
- 中英文切换。
- 更新当前 Web 账号保存的 MCP URL 和 MCP token。
- 简单调用 MCP 工具。
- 简单管理用户、工作区、项目、规则提案、审查任务。

但它仍然偏“调试台”，不是小说数据维护后台。

## 3. 角色边界

### 3.1 本地 AI 工具负责什么

本地 AI 工具包括 Codex skill、本地脚本、桌面写作工具等。

它负责：

- 与用户沟通并初始化小说。
- 创建本地目录结构。
- 保存可人工编辑的文档：
  - 总纲
  - 分卷大纲
  - 章节细纲
  - 正文
  - 草稿
  - 审查 Markdown
  - 人工修订稿
- 使用用户自己的 API key 调用大模型。
- 向 MCP 写入结构化数据。
- 从 MCP 拉取上下文包用于生成下一章。
- 把章节完成后的事实、变化、伏笔、人物状态、审查结果提交给 MCP。

本地 AI 工具不应该把全部小说正文塞进 MCP。

### 3.2 MCP 负责什么

MCP 是小说长期数据和规则中枢。

它负责：

- 保存可检索、可版本化、可审查的小说长期数据。
- 保存 AI 生成下一章需要的结构化事实。
- 保存规则和规则版本。
- 保存伏笔和剧情进度。
- 保存人物、势力、地点、道具、世界状态。
- 保存章节摘要、事件、长期记忆块。
- 保存审查报告结构化结果。
- 保存审查后产生的修订任务和规则提案。
- 生成有限上下文包，不让 AI 读全书。

### 3.3 Web 控制台负责什么

Web 控制台不负责初始化小说。

它负责维护 MCP 中的数据：

- 查看和编辑小说基础设定。
- 查看和编辑规则库。
- 查看和编辑人物、势力、地点、道具、世界观、力量体系。
- 查看和编辑伏笔、剧情线、章节计划。
- 查看审查报告、修订任务、规则提案。
- 审批或拒绝规则提案。
- 查看上下文包预览。
- 查看数据变更审计。
- 配置审查模型名称、用途、维度和权重。

## 4. 小说生成数据应该如何分层存储

网络小说长期生成不能只存“文本”。必须把创作数据分层。

### 4.1 项目基础层

用途：告诉 AI 这本书是什么。

应保存：

- 书名
- 题材
- 标签
- 目标读者
- 目标字数
- 商业定位
- 核心卖点
- 主要爽点
- 节奏策略
- 文风基准
- 禁忌内容
- 更新策略

推荐存储：

- MCP：结构化项目配置、规则、基础设定文档。
- 本地：初始化访谈记录、人工可编辑的 `设定集/基础设定.md`。

### 4.2 Canon 设定层

用途：定义不能随便变的事实。

应保存：

- 世界观基本法则
- 力量体系
- 等级体系
- 地图和地域
- 宗门/家族/势力
- 金手指机制
- 主角核心设定
- 关键人物关系
- 时间线硬事实
- 已公开事实和未公开事实

推荐存储：

- MCP：`canon_rules`、未来可新增 `canon_documents` 或增强 `reference_items`。
- 本地：`设定集/世界观.md`、`设定集/力量体系.md`、`设定集/角色设定.md`。

要求：

- Canon 变更必须有版本。
- Canon 变更必须记录来源。
- 重要 Canon 不允许审查模型自动覆盖，只能提交提案。

### 4.3 当前状态层

用途：告诉 AI “现在发展到哪了”。

应保存：

- 人物当前境界/能力
- 人物当前关系
- 人物当前目标
- 人物伤势/资源/装备
- 势力当前态度
- 地点当前状态
- 道具当前归属
- 已发生但角色不知道的事实
- 读者已知道但角色不知道的事实

推荐存储：

- MCP：`state_entities`、`state_snapshots`、`character_states`。
- 本地：可导出的状态报表，不作为权威数据。

要求：

- 状态是投影，不是原始正文。
- 状态应能从 accepted chapter commit 重建。
- 状态必须有来源章节或来源提交。

### 4.4 剧情进度层

用途：告诉 AI 主线、支线、卷目标、当前阶段。

应保存：

- 总纲
- 分卷目标
- 当前卷进度
- 主线剧情线
- 支线剧情线
- 情感线
- 对抗线
- 悬疑线
- 每条剧情线状态
- 即将推进的剧情点

推荐存储：

- MCP：`volumes`、`plot_threads`、`chapter_plans`。
- 本地：`大纲/总纲.md`、`大纲/第xx卷.md`、`细纲/chapter_xxxx.md`。

要求：

- 大纲正文可在本地编辑。
- MCP 保存结构化版本和状态。
- AI 生成时读取当前卷、当前剧情线、当前章节计划，不读取全部大纲。

### 4.5 伏笔层

用途：管理长线回收，避免忘记或乱回收。

应保存：

- 伏笔 key
- 标题
- 埋设章节
- 预期回收范围
- 重要程度
- 状态：
  - `planted`
  - `developing`
  - `misdirected`
  - `ready_to_payoff`
  - `paid_off`
  - `abandoned`
- 读者是否知道
- 主角是否知道
- 相关人物/物品/地点
- 回收方式
- 禁止提前揭示的内容

推荐存储：

- MCP：`foreshadowing`。
- 本地：伏笔报告或看板导出。

要求：

- 每章提交后要更新伏笔状态。
- 审查系统要检查是否误揭示、忘回收、回收不足。
- 准备上下文时要检索当前相关伏笔。

### 4.6 规则层

用途：约束 AI 行为。

规则类型建议：

- `canon`：硬设定，不可违背。
- `character`：人物性格、说话方式、行为边界。
- `plot`：剧情推进原则。
- `style`：文风和表达习惯。
- `pacing`：节奏要求。
- `commercial`：网文爽点、期待感、章末钩子。
- `forbidden`：禁止事项。
- `reveal_lock`：禁止提前揭露的信息。
- `review`：审查规则。
- `lesson`：从审查中沉淀出的经验。

推荐存储：

- MCP：`canon_rules`、`rule_versions`、`rule_proposals`。
- 本地：规则导出文档。

要求：

- 规则有严重级别：
  - `info`
  - `warning`
  - `error`
  - `critical`
- 规则有状态：
  - `active`
  - `disabled`
  - `superseded`
- 审查只能生成规则提案，不能自动改硬 Canon。
- 软规则可配置自动应用。

### 4.7 审查层

用途：发现漂移、错误、节奏问题，并形成可执行反馈。

应保存：

- 审查任务
- 每个模型的审查报告
- 多模型聚合报告
- 问题列表
- 证据
- 修改建议
- 是否生成修订任务
- 是否生成规则提案
- 是否作为经验沉淀

推荐存储：

- MCP：`review_jobs`、`review_reports`、`revision_tasks`、`rule_proposals`。
- 本地：每个模型的原始 Markdown 报告和最终审查文档。

要求：

- 可以配置多个大模型联合审查。
- 模型 API key 默认由本地工具保存，不放 MCP。
- MCP 保存模型配置名称和审查维度，不强制保存密钥。
- 审查结果必须结构化，方便生成任务和规则。

### 4.8 记忆检索层

用途：在 2000 万字规模下让 AI 只读相关历史。

应保存：

- 章节摘要
- 多章摘要
- 卷摘要
- 事件
- 状态快照
- 规则
- 伏笔
- 审查经验
- 参考资料
- 向量索引状态

推荐存储：

- MCP/PostgreSQL：结构化数据和全文检索。
- Qdrant：向量检索。
- Redis：缓存、临时状态、任务锁。

要求：

- AI 不读全书。
- 上下文包要有 token budget。
- 检索结果要有来源和理由。

## 5. 审查如何反哺小说数据

审查系统不是单纯给分，而是长期维护小说稳定性的反馈闭环。

### 5.1 标准流程

```text
1. 本地 AI 写完章节
2. 本地保存正文和审查文档
3. 本地向 MCP 提交 chapter commit
4. MCP 创建 review job
5. 本地按配置调用多个模型审查
6. 本地提交每个模型的结构化 report
7. MCP 聚合报告
8. MCP 创建 revision tasks
9. MCP 创建 rule proposals
10. 用户或授权角色在 Web 审批规则提案
11. 通过的规则进入未来上下文包
```

### 5.2 审查维度建议

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

### 5.3 审查产物如何进入 MCP

审查发现应分流：

```text
硬错误 -> revision_tasks
可复用写作经验 -> rules.propose(type=lesson/style/review)
设定补充 -> rules.propose(type=canon/character/plot)
状态变化遗漏 -> state update proposal
伏笔问题 -> foreshadowing update proposal
参考套路 -> reference item
```

### 5.4 自动化边界

允许自动：

- 保存审查报告。
- 聚合模型意见。
- 创建修订任务。
- 创建规则提案。
- 对低风险 lesson/style 规则自动应用，前提是项目配置允许。

不允许自动：

- 覆盖硬 Canon。
- 改主角核心设定。
- 改力量体系基础规则。
- 删除伏笔。
- 把模型意见直接当事实。

## 6. Web 控制台应该变成什么

当前 Web 不应该继续扩展为“初始化向导”，而应改为“小说数据维护台”。

### 6.1 必须有的主导航

- 工作区与小说选择
- 项目总览
- 设定集
- 人物/势力/地点/道具
- 规则库
- 伏笔看板
- 剧情线与章节计划
- 记忆与摘要
- 审查中心
- 参考库
- 模型配置
- 审计与同步

### 6.2 设定集页面

维护：

- 基础设定
- 世界观
- 力量体系
- 金手指
- 角色设定
- 势力设定
- 地图地点
- 商业定位
- 文风基准
- 禁忌规则

能力：

- 列表查看
- 分类过滤
- 编辑正文
- 编辑结构化 metadata
- 查看版本
- 标记状态
- 导入本地初始化结果
- 导出 Markdown

### 6.3 规则库页面

维护：

- 当前生效规则
- 规则版本
- 规则提案
- 审查生成的规则候选

能力：

- 按类型筛选
- 按严重级别筛选
- 启用/禁用
- 审批/拒绝提案
- 查看规则来源

### 6.4 伏笔页面

维护：

- 开放伏笔
- 发展中伏笔
- 待回收伏笔
- 已回收伏笔
- 废弃伏笔

能力：

- 按重要程度筛选
- 按章节范围筛选
- 查看相关人物和剧情线
- 更新状态
- 标记禁止提前揭示

### 6.5 审查中心

维护：

- 审查配置
- 审查任务
- 多模型报告
- 聚合结论
- 修订任务
- 规则提案

能力：

- 配置模型名称、职责、权重、审查维度
- 查看每个模型报告
- 查看共识和分歧
- 一键生成修订任务
- 一键提交规则提案
- 审批规则提案

### 6.6 上下文包预览

用途：

- 在生成章节前检查 AI 会读到什么。
- 防止关键设定遗漏。
- 防止上下文过大。

应展示：

- Canon 摘要
- 当前人物状态
- 当前剧情线
- 开放伏笔
- 相关历史记忆
- 最近章节摘要
- 审查经验
- token 预算
- 检索来源

## 7. MCP 工具后续补齐建议

现有工具已经覆盖基础链路，但还需要更适合 Web 维护的工具。

### 7.1 设定文档工具

建议新增：

```text
canon.doc.upsert
canon.doc.list
canon.doc.get
canon.doc.archive
canon.doc.history
```

用途：

- 保存基础设定、世界观、力量体系、金手指、商业定位等长文档。
- 支持版本。
- 支持状态。
- 支持来源。

### 7.2 实体维护工具

建议新增：

```text
state.entity.upsert
state.entity.list
state.entity.get
state.snapshot.upsert
state.snapshot.list
```

用途：

- 维护人物、地点、势力、物品、世界状态。
- 让 Web 可直接编辑结构化状态。

### 7.3 剧情线工具

建议新增：

```text
plot.thread.upsert
plot.thread.list
volume.upsert
volume.list
```

用途：

- 维护主线、支线、卷目标。

### 7.4 审查学习工具

建议新增或完善：

```text
review.extract_rule_proposals
review.extract_state_updates
review.extract_foreshadowing_updates
workflow.learn_from_review
```

用途：

- 把审查结果变成规则提案、状态提案、伏笔更新提案。

### 7.5 本地同步工具

建议新增：

```text
sync.import_local_manifest
sync.export_project_pack
sync.list_local_bindings
```

用途：

- 本地 AI 工具初始化小说后，把设定文档结构化导入 MCP。
- Web 可查看 MCP 已知的本地文件路径提示和哈希。

## 8. 本地 AI 工具与 MCP 的初始化契约

小说初始化应该发生在本地。

本地初始化完成后，应提交给 MCP：

```json
{
  "project_profile": {},
  "canon_documents": [],
  "rules": [],
  "entities": [],
  "plot_threads": [],
  "foreshadowing": [],
  "volumes": [],
  "chapter_plan_seed": [],
  "local_files": []
}
```

MCP 接收后：

- 建立项目基础资料。
- 创建 Canon 文档。
- 创建规则。
- 创建实体。
- 创建剧情线。
- 创建伏笔。
- 创建本地绑定。
- 记录文件路径提示和哈希。

Web 之后负责维护这些数据。

## 9. 2000 万字规模下的关键原则

### 9.1 不让 AI 读全量

任何生成任务都必须通过上下文包。

上下文包由以下内容组成：

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

### 9.2 事实和文本分离

正文是文本。

MCP 保存的是事实、状态、规则、摘要、索引和审查结构。

### 9.3 审查结果不能直接变事实

审查模型可能误判。

所以审查结果应先变成：

- 修订任务
- 规则提案
- 状态提案
- 伏笔提案

再由用户或配置策略决定是否应用。

### 9.4 本地文档仍然重要

作者需要能人工修改：

- 正文
- 大纲
- 细纲
- 设定文档
- 审查文档

因此本地文件是创作工作区，MCP 是长期数据中枢。

## 10. 当前缺口清单

### 10.1 MCP 缺口

- 缺少通用 Canon 文档 CRUD。
- 缺少实体/状态的直接维护工具。
- 缺少剧情线和卷的直接维护工具。
- 缺少审查结果自动拆分为规则/状态/伏笔提案的完整工具。
- 缺少本地初始化结果批量导入工具。
- 缺少 Web 友好的列表/详情 API 聚合工具。

### 10.2 Web 缺口

- 仍偏 MCP 调试台。
- 没有小说数据后台的导航结构。
- 没有设定集维护页面。
- 没有人物/势力/地点/道具维护页面。
- 没有伏笔看板。
- 没有规则审批工作流页面。
- 没有审查中心页面。
- 没有上下文包预览页面。
- 没有本地文件绑定和同步状态页面。

### 10.3 本地 skill 缺口

- 初始化结果还需要标准化输出契约。
- 需要把 `webnovel-writer` 的初始化思想转换为本地 skill 流程。
- 需要导入 MCP 的批量提交命令。
- 需要章节完成后的结构化 commit 模板。
- 需要审查报告提交模板。

## 11. 推荐开发顺序

### 阶段 A：文档与数据契约

- 完成本需求文档。
- 确定 Canon 文档、实体、状态、剧情线、伏笔、规则的字段。
- 确定本地初始化导入 JSON 格式。

### 阶段 B：MCP 补齐数据维护工具

- 新增 `canon.doc.*`
- 新增 `state.entity.*`
- 新增 `plot.thread.*`
- 新增 `volume.*`
- 完善 `workflow.learn_from_review`

### 阶段 C：Web 改造成数据维护台

- 项目选择器。
- 设定集页面。
- 规则库页面。
- 伏笔页面。
- 审查中心页面。
- 上下文包预览页面。

### 阶段 D：本地 skill 对接

- 本地初始化小说。
- 生成本地目录。
- 导入初始化数据到 MCP。
- 拉取上下文包。
- 提交章节 commit。
- 提交多模型审查报告。

### 阶段 E：审查反哺闭环

- 多模型审查聚合。
- 自动生成修订任务。
- 自动生成规则提案。
- Web 审批规则提案。
- 新规则进入下一章上下文包。

## 12. 验收标准

一个小说项目可用的最低标准：

- 用户能在本地初始化小说并生成本地文档。
- 本地工具能把初始化结果写入 MCP。
- Web 能看到并编辑这些设定数据。
- Web 能看到规则、伏笔、人物状态、剧情线。
- 生成章节前能从 MCP 获取有限上下文包。
- 写完章节后能提交结构化 commit。
- 审查后能提交多个模型报告。
- MCP 能聚合审查结果并生成修订任务。
- 审查建议能生成规则提案。
- Web 能审批规则提案。
- 下一章上下文包能使用新规则。

## 13. 术语表

### Canon 设定

小说中已经确认为事实、不能被模型随意改写的硬设定。

例：

- 主角灵根类型。
- 世界力量体系。
- 某个神器的真实能力。
- 某个角色是否知道某个秘密。

Canon 可以更新，但必须有来源、版本、审批记录。

### 上下文包

生成某一章、某个细纲或某次审查时，MCP 按预算组装给 AI 的有限上下文。

上下文包不是全书内容，而是从规则、状态、伏笔、摘要、检索记忆、审查经验中抽取的当前必要信息。

### 记忆块

可被检索的长期信息片段。

来源可以是：

- 章节摘要
- 事件
- 人物状态
- 规则
- 伏笔
- 审查经验
- 参考资料

### 规则提案

模型、审查系统、本地工具或用户发现某条经验/约束需要长期生效时，提交给 MCP 的待审批规则。

规则提案不是正式规则。

### 状态快照

某个实体在某个时间点的结构化状态。

例：

- 主角第 128 章后的境界、伤势、装备、目标。
- 某势力当前对主角的态度。
- 某道具当前归属。

### 伏笔状态

伏笔在长篇剧情中的生命周期。

建议状态：

- `planted`：已埋设
- `developing`：发展中
- `misdirected`：误导中
- `ready_to_payoff`：可回收
- `paid_off`：已回收
- `abandoned`：废弃

### 本地绑定

本地 AI 工具报告给 MCP 的项目目录信息。

MCP 只保存路径提示、文件哈希、manifest，不直接拥有用户正文文件。

## 14. 核心字段规范

本节定义 P0 级别的数据字段标准。后续实现 MCP 工具和 Web 表单时应优先遵守。

### 14.1 Canon 文档字段

建议新增或抽象出 `canon_documents` 能力，即使底层先复用 `reference_items`，对外也应表现为 Canon 文档。

字段：

```text
id
project_id
doc_type          premise|worldview|power_system|golden_finger|character_bible|faction_bible|location_bible|style_bible|commercial_positioning|forbidden|other
key               项目内唯一标识
title
content
status            draft|active|archived|superseded
version
scope             global|volume|arc|chapter|character|faction
review_status     unreviewed|reviewed|needs_review
source_type       local_init|manual|review|chapter_commit|import
source_id
related_rule_ids
metadata
created_by
updated_by
created_at
updated_at
```

要求：

- `doc_type + key` 在同一项目内唯一。
- `active` Canon 修改必须生成版本。
- 重要 Canon 修改应进入审批或至少记录审计。
- Web 编辑时必须显示状态、版本、来源。

### 14.2 人物字段

人物既可以作为 `state_entities`，也可以有专门视图。

字段：

```text
id
project_id
entity_type = character
name
aliases
core_profile       核心设定
personality        性格底色
desire             当前欲望/长期目标
fear_or_flaw       缺陷/恐惧/弱点
power_level        当前境界/等级
abilities
resources
equipment
faction
relationships
state_tags         injured|hidden_identity|breakthrough_pending|enemy_alerted 等
knowledge_state    角色知道什么、不知道什么
reader_knowledge   读者知道什么
current_location
current_goal
last_seen_chapter
source_chapter
source_commit_id
updated_at
```

要求：

- 人物核心设定和当前状态分开。
- 当前状态可由章节提交重建。
- Web 允许人工修正，但要记录来源和原因。

### 14.3 势力字段

```text
id
project_id
entity_type = faction
name
aliases
faction_type       family|sect|company|guild|kingdom|organization|other
core_profile
leader
members
territory
resources
power_level
attitude_to_protagonist
relationships
current_status
known_secrets
last_updated_chapter
metadata
```

### 14.4 地点字段

```text
id
project_id
entity_type = location
name
aliases
location_type      city|sect|secret_realm|dungeon|country|world|other
description
rules              地点特殊规则
owners
connected_locations
important_events
current_status
hidden_information
metadata
```

### 14.5 道具字段

```text
id
project_id
entity_type = item
name
aliases
item_type          weapon|artifact|medicine|token|book|resource|other
description
abilities
limitations
owner
origin
current_status
reveal_status      unknown|hinted|revealed|misdirected
related_foreshadowing
metadata
```

### 14.6 上下文包 token 预算

默认建议：

```text
Canon 摘要与硬设定       <= 20%
人物/势力/地点当前状态   <= 15%
伏笔与剧情线             <= 10%
历史摘要与长期记忆       <= 30%
规则与禁忌               <= 15%
审查经验                 <= 10%
```

要求：

- 每个上下文包必须记录预算和实际估算 token。
- 超预算内容必须摘要或降级。
- 上下文包要记录检索来源和选择理由。
- Web 应提供上下文包预览，显示各模块占比。

## 15. 权限矩阵

### 15.1 推荐角色

```text
system_admin   服务器级维护
owner          工作区/项目拥有者
author         作者，可维护项目内容
editor         编辑，可审查和修正数据
reviewer       审阅者，可提交审查与修订任务
reader         只读
```

### 15.2 操作权限

| 操作 | system_admin | owner | author | editor | reviewer | reader |
| --- | --- | --- | --- | --- | --- | --- |
| 管理用户/工作区 | 是 | 工作区内 | 否 | 否 | 否 | 否 |
| 创建项目 | 是 | 是 | 可配置 | 否 | 否 | 否 |
| 编辑基础设定草稿 | 是 | 是 | 是 | 是 | 否 | 否 |
| 修改 active Canon | 是 | 是 | 提案 | 提案/可配置 | 否 | 否 |
| 审批 Canon 变更 | 是 | 是 | 可配置 | 可配置 | 否 | 否 |
| 编辑人物当前状态 | 是 | 是 | 是 | 是 | 提案 | 否 |
| 更新伏笔状态 | 是 | 是 | 是 | 是 | 标记异常 | 否 |
| 创建规则提案 | 是 | 是 | 是 | 是 | 是 | 否 |
| 审批规则提案 | 是 | 是 | 可配置 | 可配置 | 否 | 否 |
| 提交审查报告 | 是 | 是 | 是 | 是 | 是 | 否 |
| 创建修订任务 | 是 | 是 | 是 | 是 | 是 | 否 |
| 查看上下文包 | 是 | 是 | 是 | 是 | 是 | 是 |

### 15.3 权限实现建议

P0 阶段：

- 先用角色矩阵和代码判断。
- 所有写操作必须校验 workspace/project 权限。
- 硬 Canon 修改必须记录审计。

P1/P2 阶段：

- 再考虑新增 `permission_templates`、`role_permissions` 表。
- 支持项目自定义权限。
- 支持不同小说采用不同审批策略。

## 16. 错误处理、同步与容灾

### 16.1 本地文件与 MCP 一致性

本地 AI 工具提交给 MCP 的本地文件信息应包含：

```json
{
  "kind": "chapter|outline|plan|review|canon_doc",
  "path_hint": "chapters/volume_001/ch0128.md",
  "sha256": "hex",
  "word_count": 3200,
  "updated_at": "iso timestamp"
}
```

MCP 保存：

- 路径提示
- 哈希
- 文件类型
- 所属章节/设定/审查任务
- 最后同步时间

当本地文件哈希变化但 MCP 未更新：

- Web 显示“本地文件可能已变更”。
- 本地工具下次同步时提交差异。
- MCP 不主动覆盖本地文件。

### 16.2 失败重试

本地 AI 工具向 MCP 提交失败时：

- 本地写入 `sync-state` 或提交队列。
- 队列记录 payload、目标工具、重试次数、最后错误。
- 使用指数退避重试。
- 多次失败后在本地工具和 Web 中显示告警。

建议状态：

```text
pending
retrying
failed
synced
conflict
```

### 16.3 数据回滚

需要支持回滚的对象：

- Canon 文档
- 规则
- 人物/状态快照
- 伏笔状态
- 审查生成的规则提案

最低实现：

- 记录版本。
- 记录修改人。
- 记录修改原因。
- 支持 Web 查看历史。

后续实现：

- 支持一键恢复到历史版本。
- 支持对比差异。

### 16.4 备份恢复

备份策略：

- PostgreSQL 定时全量备份。
- 按项目导出 JSON 包。
- Qdrant 支持重建，因此优先备份源数据和索引任务状态。
- Web 用户配置和 MCP token 单独备份。

恢复流程：

```text
1. 恢复 PostgreSQL
2. 恢复 Web 用户配置
3. 检查项目和工作区
4. 重建全文索引
5. 重建向量索引
6. 校验本地绑定文件哈希
```

## 17. 规则冲突处理

规则冲突是长篇写作中必须处理的问题。

### 17.1 冲突类型

- 同一 `rule_key` 被重复定义。
- 同类型规则内容互相矛盾。
- 新规则违背更高优先级 Canon。
- 局部规则与全局规则冲突。
- 审查模型提出的规则与已有风格规则冲突。

### 17.2 优先级建议

规则优先级从高到低：

```text
critical canon
reveal_lock
forbidden
character core
plot
style
pacing
commercial
review
lesson
```

生效范围优先级：

```text
chapter > arc > volume > character/faction > global
```

但低范围规则不能违反高优先级硬规则。

### 17.3 解决流程

```text
1. 新规则进入前检查冲突
2. 如果冲突，标记 proposal = conflict
3. Web 展示冲突规则和差异
4. 人工选择：
   - 接受新规则并废弃旧规则
   - 修改新规则
   - 拒绝新规则
   - 限定新规则范围
5. 记录冲突解决日志
```

## 18. 审查模型质量评估

多模型审查不能默认每个模型都可靠。

### 18.1 需要记录的指标

对每个模型、每个项目、每个审查维度记录：

- 提交报告数量
- 被人工确认的问题数量
- 被人工驳回的问题数量
- 生成规则提案数量
- 规则提案通过率
- 修订任务完成率
- 平均严重级别
- 与其他模型的一致度

### 18.2 权重调整

审查配置应允许：

- 按模型设置权重。
- 按审查维度设置权重。
- 按小说类型设置默认维度。

例：

```text
玄幻：力量体系一致性、境界压制、伏笔回收权重更高。
都市：爽点节奏、人物动机、现实合理性权重更高。
悬疑：线索公平性、误导质量、信息释放节奏权重更高。
```

### 18.3 低质量模型处理

如果某模型长期误报：

- 降低权重。
- 仅保留参考意见。
- 从默认审查 council 中移除。

## 19. 性能与规模原则

针对 2000 万字级别项目，必须默认分页、增量和缓存。

### 19.1 列表接口

所有列表工具默认：

- `limit`
- `offset` 或 cursor
- 状态筛选
- 类型筛选
- 时间范围筛选
- 关键词筛选

禁止默认返回全量。

### 19.2 向量索引

策略：

- 只索引新增/修改的摘要、事件、状态、规则和参考项。
- 正文不直接全量入库。
- 原始正文由本地保管。
- Qdrant 可由 PostgreSQL 源数据重建。

### 19.3 上下文包缓存

可缓存：

- 高频 Canon 摘要
- 当前人物状态摘要
- 最近 10 章摘要
- 当前卷剧情线摘要
- 当前生效规则摘要

缓存失效条件：

- Canon 更新
- 规则更新
- 章节 commit 接受
- 状态快照更新
- 伏笔状态更新
- 审查 lesson 被审批

## 20. 多格式与开放接口

### 20.1 文件格式优先级

P0：

- Markdown
- JSON

P1：

- CSV

P2：

- Word
- Excel
- 第三方写作软件格式

原因：

- Markdown 适合作者手改。
- JSON 适合本地 AI 工具和 MCP 同步。
- Word/Excel 更适合后续导入导出，不应阻塞核心闭环。

### 20.2 开放接口

当前优先：

- MCP 工具协议。
- Web 自身 API。

后续可考虑：

- REST
- GraphQL
- Webhook

但这些不是 P0。

## 21. 多语言与本地化

### 21.1 项目语言

项目基础层应记录：

- 原文语言
- 目标市场
- 目标读者文化环境
- 本地化禁忌
- 专有名词翻译策略

### 21.2 Web 多语言

P0：

- 固定中英文文案。

P2：

- Web 文案配置表。
- 自定义翻译词条。
- 多语言项目模板。

## 22. 新手引导、可视化与通知

### 22.1 新手引导

本地 AI 工具应提供：

- 题材模板
- 设定模板
- 大纲模板
- 审查模板

Web 应提供：

- 首次进入项目的功能指引。
- 规则审批说明。
- 上下文包预览说明。
- 数据同步状态说明。

### 22.2 可视化

P1/P2 能力：

- 伏笔时间轴。
- 伏笔回收看板。
- 剧情线进度视图。
- 人物关系图。
- 上下文包 token 占比图。
- 审查问题严重级别统计。

### 22.3 告警与通知

通知事件：

- 规则提案待审批。
- 审查发现 critical 问题。
- 本地同步失败。
- 上下文包生成失败。
- 伏笔长期未回收。
- Canon 冲突。

通知渠道优先级：

```text
P0: Web 内提示、本地 AI 工具提示
P1: 邮件
P2: 钉钉/企业微信/Webhook
```

## 23. 示例场景

### 23.1 场景一：本地初始化玄幻小说并写入 MCP

```text
1. 作者在本地 AI 工具中启动小说初始化。
2. 本地 AI 工具与作者沟通题材、主角、金手指、世界观、力量体系、爽点、禁忌。
3. 本地 AI 工具生成本地目录：
   - 设定集/
   - 大纲/
   - 细纲/
   - 正文/
   - 审查报告/
4. 本地 AI 工具把初始化结果整理成 JSON。
5. 本地 AI 工具调用 MCP：
   - project.create
   - project.register_local_binding
   - canon.doc.upsert
   - rules.upsert
   - state.entity.upsert
   - plot.thread.upsert
   - plot.upsert_foreshadowing
6. Web 控制台可以查看和维护这些设定。
```

### 23.2 场景二：审查发现力量体系漂移

```text
1. 本地 AI 生成第 42 章。
2. 本地工具保存正文并提交 chapter commit。
3. 本地工具启动多个模型审查。
4. 模型 A 认为主角越级过大，违背力量体系。
5. 模型 B 认为可以接受，但需要补充代价。
6. 模型 C 认为读者爽点足够，但需要加限制说明。
7. MCP 聚合审查：
   - 创建一个 high 修订任务
   - 创建一个 rule proposal：越级战斗必须有代价或外部条件
   - 创建一个 state proposal：主角战后受伤
8. Web 中作者审批规则提案。
9. 下一章上下文包包含新规则和主角受伤状态。
```

## 24. 缺口优先级清单

### P0：没有这些就无法形成核心闭环

- Canon 文档 CRUD。
- 核心字段规范。
- 本地初始化数据导入契约。
- Web 设定集维护页面。
- 规则库和规则提案审批页面。
- 权限矩阵与硬 Canon 审批。
- 本地文件哈希与同步状态。
- 审查聚合到修订任务和规则提案。
- 上下文包预算和来源审计。
- 列表分页与筛选。

### P1：核心体验和鲁棒性增强

- 人物/势力/地点/道具状态维护工具。
- 伏笔看板。
- 剧情线和卷维护。
- 规则冲突检测。
- 审查模型质量评估。
- 本地提交失败重试队列。
- 上下文包缓存。
- 项目级备份导出。
- 审查中心 Web 页面。

### P2：扩展和高级体验

- Word/Excel/第三方写作软件导入导出。
- REST/GraphQL。
- 可视化剧情线编辑。
- 伏笔网络图。
- 人物关系图。
- 邮件/钉钉/企业微信通知。
- Web 文案配置表。
- 多语言项目模板。

## 25. 2000 万字规模生成控制规范

本节补充超长篇 AI 写作的生产级控制要求。核心目标不是让 AI 读取更多内容，而是让 MCP 更严格地决定：

```text
哪些内容必须进入上下文；
哪些内容应该被降权；
哪些内容已经过期；
哪些内容对当前视角不可见；
哪些冲突必须阻断生成。
```

### 25.1 上下文包分层加载策略

上下文包应支持动态预算，不同任务和篇幅可使用不同上限。

建议默认：

```text
轻量任务：8k-12k tokens
普通章节：16k-24k tokens
超长篇关键章节：24k-32k tokens
审查任务：按审查维度单独预算
```

加载优先级：

```text
硬 Canon
当前人物/势力/地点状态
当前生效规则
当前章节计划
当前剧情线
活跃伏笔
最近章节摘要
相关长期记忆
审查经验
参考素材
```

淘汰优先级：

```text
低相关参考素材
旧审查经验
远期历史记忆
非当前剧情线内容
已完结支线
低重要度伏笔
```

强制兜底：

- 硬 Canon 永远优先加载。
- 当前 POV 角色状态永远优先加载。
- 生效规则永远优先加载。
- Critical 规则不可被 token 预算截断。
- 过期、废弃、被替代的数据不得进入上下文包。

### 25.2 卷切换与冷启动策略

卷切换时不应继承上一卷全部上下文。

换卷默认保留：

- 全局 Canon
- 主角长期状态
- 主要势力状态
- 未回收核心伏笔
- 长线剧情线
- 上卷总结
- 上卷遗留任务

换卷默认降权：

- 上卷局部场景
- 上卷临时人物
- 已回收伏笔
- 已完结支线
- 已过期临时状态

冷启动生成时：

- 优先使用项目基础设定、总纲、第一卷目标、主角核心设定。
- 不加载无关参考库。
- 不加载未确认草稿数据。

### 25.3 上下文冲突过滤

生成上下文前必须过滤：

- `superseded` 规则。
- `disabled` 规则。
- `abandoned` 伏笔。
- 已过期状态快照。
- 已废弃剧情线。
- 未确认草稿 commit。
- 与当前项目/分支不一致的数据。

如果检索结果存在冲突：

```text
1. 优先保留高优先级规则和最新 active 状态
2. 记录冲突到 retrieval_audit
3. 非阻断冲突显示在上下文包预览
4. 阻断冲突创建预生成校验错误
```

### 25.4 角色视角隔离

网文生成必须支持 POV 视角控制。

建议上下文包增加：

```text
pov_mode: protagonist|character|omniscient|reader|reviewer
pov_character: optional
visibility_policy: strict|balanced|full
```

视角规则：

- 主角视角不能加载主角不知道的秘密。
- 单角色视角不能加载该角色未知的幕后事实。
- 上帝视角可加载完整事实，但写作提示必须避免直接泄露。
- 审查视角可加载全部事实，用于检查是否误揭示。
- 读者视角应加载读者已知事实，用于期待管理和悬念校验。

实体状态应区分：

- 客观事实。
- 角色已知事实。
- 读者已知事实。
- 作者/系统隐藏事实。

### 25.5 动态关系网络

人物关系不能只保存单人状态。需要支持关系边。

关系字段建议：

```text
source_entity_id
target_entity_id
relation_type        ally|enemy|mentor|lover|family|rival|debt|secret|other
attitude             trust|fear|hate|admire|suspicious|neutral
intensity            0-100
known_by_source      bool
known_by_target      bool
known_by_reader      bool
status               active|hidden|broken|resolved
source_chapter
source_commit_id
metadata
```

注意：

- A 对 B 的态度变化，不代表 B 自动知道。
- 势力开战，不代表所有成员立刻知道。
- 系统可以生成联动更新提案，但不应悄悄把推断写成硬事实。

### 25.6 状态时效与过期

临时状态必须有有效范围。

状态字段建议补充：

```text
effective_chapter
expire_chapter
effective_volume
expire_volume
duration_type        permanent|temporary|until_event|until_reviewed
expires_on_event
is_current
confidence
source_type
source_id
change_reason
```

典型临时状态：

- 伤势。
- 中毒。
- 临时 buff。
- 秘境限制。
- 伪装身份。
- 道具暂借。
- 阶段性禁用金手指。

生成上下文时：

- 过期状态默认不加载。
- 即将过期状态可提示。
- 不确定状态应标注低置信度。

### 25.7 变更溯源粒度

所有影响生成的数据变更都必须记录来源。

来源类型：

```text
local_init
local_draft
local_final_commit
web_manual_edit
review_report
review_proposal
rule_proposal
import
system_rebuild
rollback
```

用途：

- 追踪人设崩坏来源。
- 支持回滚。
- 支持审计。
- 支持区分草稿和正式事实。

### 25.8 伏笔连锁与回收阈值

伏笔应支持关联。

字段建议补充：

```text
parent_foreshadowing_id
related_foreshadowing_ids
trigger_on_payoff_ids
blocks_payoff_until_ids
layer                 surface|hidden|behind_the_scene
must_payoff           bool
payoff_deadline_chapter
payoff_deadline_volume
overdue_policy        warn|create_task|block_generation
```

伏笔分层：

- 明线伏笔：读者能感知。
- 暗线伏笔：读者隐约感知，但未明说。
- 幕后伏笔：作者/系统知道，角色和读者不知道。

回收策略：

- 主线核心伏笔必须回收或人工废弃。
- 支线伏笔可废弃，但必须记录原因。
- 超过回收阈值应生成审查告警或修订任务。

### 25.9 规则生效范围与临时规则

规则必须支持范围。

字段建议补充：

```text
scope_type       global|volume|arc|plot_thread|chapter_range|character|faction|location
scope_ref
starts_at_chapter
ends_at_chapter
starts_on_event
ends_on_event
priority
temporary
conflict_policy  override|merge|manual_review|disable_lower
```

规则类型优先级：

```text
critical canon
reveal_lock
forbidden
character
plot
power_system
style
pacing
commercial
review
lesson
```

临时规则示例：

- 秘境期间禁止使用某金手指。
- 当前压抑剧情阶段降低爽点密度。
- 某卷中主角必须隐藏身份。
- 某章前禁止揭示反派真实身份。

### 25.10 预生成校验

在本地 AI 调用大模型生成前，MCP 应支持轻量预检。

建议工具：

```text
workflow.validate_context_pack
workflow.preflight_generation
```

检查项：

- 是否缺少硬 Canon。
- 当前人物状态是否冲突。
- 活跃伏笔是否与章节计划冲突。
- 当前规则是否互相冲突。
- 是否存在 Critical 审查任务未解决。
- 是否存在禁止提前揭示的信息。
- 是否加载了过期状态。

预检结果：

```text
pass
warning
blocked
```

`blocked` 时本地工具应停止生成，提示作者处理。

### 25.11 分段生成上下文

长章节可拆成多段生成。

段落类型：

```text
opening
middle
climax
ending_hook
```

每段上下文不同：

- 开篇：承接上一章、当前场景、读者期待。
- 中段：冲突推进、人物状态、局部规则。
- 高潮：力量体系、战斗限制、关键伏笔。
- 结尾：章末钩子、未揭示信息、下一章引导。

MCP 可提供分段上下文包，本地工具负责实际分段生成。

### 25.12 审查阻断与章节回滚重审

审查问题分级：

```text
critical  阻断后续生成，必须人工处理
warning   生成修订建议，可继续但需提示
info      记录经验，不阻断
```

Critical 示例：

- 力量体系崩坏。
- 主角核心人设完全 OOC。
- 提前揭露关键伏笔。
- 与硬 Canon 冲突。
- 重要人物状态错误。

章节被本地人工大改后：

```text
1. 本地工具检测文件哈希变化
2. 提交 revised commit
3. MCP 标记旧摘要/状态/伏笔更新为需重建
4. 重新生成章节摘要
5. 重建相关状态快照
6. 重新审查
7. 更新修订任务和规则提案
```

### 25.13 草稿与正式提交隔离

提交类型：

```text
draft_commit
review_commit
final_commit
rollback_commit
```

规则：

- 草稿 commit 不更新全局状态快照。
- 草稿 commit 不进入默认上下文包。
- final commit 才能更新当前状态、摘要、伏笔。
- review commit 可创建审查任务，但不一定改变 Canon。

### 25.14 本地与 MCP 同步冲突

冲突来源：

- 本地设定文档被人工修改。
- Web 中结构化数据被修改。
- 审查提案修改了同一规则。
- 本地草稿与正式提交不一致。

冲突解决策略：

```text
local_wins
mcp_wins
manual_merge
create_proposal
keep_both_as_branches
```

默认建议：

- 正文和本地 Markdown：本地优先。
- 结构化 Canon：MCP 优先，但允许人工合并。
- 审查提案：不直接覆盖，进入审批。
- 草稿：默认不影响正式数据。

### 25.15 分层摘要规范

摘要必须结构化，不能只是一段自然语言。

摘要层级：

```text
chapter_summary
ten_chapter_summary
volume_summary
book_summary
```

每级摘要固定维度：

```text
main_events
character_changes
relationship_changes
world_changes
faction_changes
item_changes
foreshadowing_changes
rule_impacts
unresolved_hooks
next_relevant_context
```

长距离检索优先使用高层摘要。

### 25.16 冷热数据与归档

P0 阶段先做逻辑冷热分层，不急于拆数据库。

热数据：

- 当前卷。
- 最近 50 章。
- 当前活跃人物。
- 当前活跃剧情线。
- 当前活跃伏笔。
- 当前生效规则。

冷数据：

- 已完结卷。
- 已回收伏笔。
- 已归档支线。
- 废弃设定。
- 早期历史事件。

策略：

- 默认上下文包只加载热数据。
- 冷数据通过检索命中后再加载摘要。
- Qdrant 使用增量索引。
- 冷数据可降低检索权重。

### 25.17 多模型输出适配器

本地 AI 工具应把不同模型输出转换为统一结构。

适配对象：

- 大纲输出。
- 章节正文元数据。
- 章节 commit。
- 审查报告。
- 规则提案。
- 状态更新提案。

MCP 不应为每个模型写专用解析逻辑。

标准流程：

```text
model raw output
-> local adapter
-> normalized JSON
-> MCP tool
```

### 25.18 离线写作兜底

断连 MCP 时，本地 AI 工具应能继续低风险写作。

本地缓存：

- 最近一次上下文包。
- 当前项目基础设定。
- 当前人物状态摘要。
- 当前生效规则摘要。
- 最近章节摘要。
- 未同步提交队列。

离线限制：

- 不允许修改硬 Canon。
- 不允许审批规则提案。
- 不允许标记伏笔已回收为正式事实。
- 可生成草稿。
- 可本地审查。
- 恢复连接后批量同步。

### 25.19 批量维护能力

超长篇需要批量操作。

建议工具：

```text
state.entity.bulk_upsert
rules.bulk_update
foreshadowing.bulk_update
reference.bulk_import
sync.bulk_commit
```

Web 批量能力：

- 批量导入角色表。
- 批量修改势力立场。
- 批量归档废弃伏笔。
- 批量停用旧规则。
- 批量导入参考素材。

批量操作必须写审计日志。

### 25.20 项目快照与分支

超长篇经常重写大纲或探索分支剧情。

建议能力：

- 项目级快照。
- 单卷快照。
- 章节前快照。
- 分支项目。
- 分支间差异对比。

快照对象：

- Canon 文档。
- 规则。
- 实体状态。
- 伏笔。
- 剧情线。
- 摘要。
- 审查任务状态。

P0 可先支持导出项目 JSON 包。

P1/P2 再支持真正分支和一键回滚。

### 25.21 商业节奏调度

网文不是只要逻辑正确，还要连载可读。

建议统计：

- 每章爽点数量。
- 每卷爽点密度。
- 升级/突破间隔。
- 冲突间隔。
- 章末钩子达标率。
- 伏笔回收间隔。
- 主角主动行动占比。
- 审查问题趋势。

当节奏失衡：

- 创建 `commercial` 类型规则提案。
- 创建修订任务。
- 在上下文包中加入节奏提醒。

### 25.22 剧情冲突检测与事件模拟

P0 只做冲突检测，不做复杂推演。

检测对象：

- 人物行为是否违背当前状态。
- 势力行动是否违背关系网络。
- 道具流转是否有断点。
- 伏笔回收是否满足前置条件。
- 章节计划是否触犯 reveal lock。

P2 可考虑事件模拟器：

- 推演剧情线推进后的连锁影响。
- 预测潜在人设崩坏。
- 预测伏笔冲突。

### 25.23 P0/P1/P2 补充优先级

P0：

- 上下文包加载和淘汰策略。
- 上下文冲突过滤。
- POV 视角隔离。
- 状态过期字段。
- 变更溯源字段。
- 伏笔关联和回收阈值。
- 规则范围和临时规则。
- 预生成校验。
- 审查 Critical 阻断。
- 章节回滚重审。
- 草稿/正式提交隔离。
- 分层摘要规范。
- 增量向量索引。
- 离线缓存快照。
- 多模型输出适配器。

P1：

- 动态关系网络。
- 批量维护工具。
- 审查模型质量自动调权。
- 商业节奏统计。
- 上下文包缓存。
- 项目 JSON 快照。
- Web 数据冲突提示。
- 连载统计看板。
- 协作任务分配。

P2：

- 剧情事件模拟器。
- 真正冷热分库。
- 图形化剧情网络。
- 模板市场。
- 多端开放接口。
- 项目分支与一键回滚。
- 外部通知集成。

## 26. 落地执行标准与量化验收

本节把前文架构要求进一步转成可实现、可测试、可验收的工程标准。

### 26.1 上下文 Profile

上下文包不应只有一种固定模板。不同章节阶段、不同任务、不同审查目标应使用不同 `context_profile`。

建议 profile：

```text
opening_volume        卷首，侧重卷目标、全局 Canon、新阶段规则
daily_chapter         日常推进，侧重近期摘要、人物状态、当前剧情线
battle_chapter        战斗章节，侧重力量体系、人物状态、战斗限制
reveal_chapter        揭示章节，侧重 reveal lock、读者已知/未知信息
payoff_chapter        伏笔回收，侧重活跃伏笔、前置条件、回收方式
ending_volume         卷尾，侧重伏笔结算、状态结算、下卷钩子
review_consistency    一致性审查，侧重 Canon、状态、规则、伏笔
review_commercial     商业节奏审查，侧重爽点、节奏、钩子、读者期待
```

每个 profile 应配置：

```text
total_token_budget
canon_budget
state_budget
plot_budget
foreshadowing_budget
recent_summary_budget
long_memory_budget
rules_budget
review_lesson_budget
reference_budget
pov_policy
fallback_policy
```

### 26.2 上下文自动裁剪

token 超预算时不能简单删除整个模块。

裁剪顺序：

```text
1. 删除低相关参考素材
2. 压缩历史长期记忆
3. 压缩非当前剧情线摘要
4. 降低冷数据权重
5. 合并重复规则
6. 保留硬 Canon、当前状态、Critical 规则
```

二次压缩策略：

- 历史摘要超预算时，优先使用十章摘要或卷摘要。
- 多条相似记忆命中时，合并为一条摘要。
- 低置信度检索结果只进入 audit，不进入正文上下文。

### 26.3 POV 严格度配置

不同题材需要不同视角隔离。

建议：

```text
strict     悬疑、幕后流、多 POV，严格隐藏角色未知信息
balanced   默认网文模式，隐藏关键秘密，但允许加载作者提示
full       审查、设定维护、上帝视角分析
```

规则：

- 生成正文默认不使用 `full`。
- 审查可以使用 `full`。
- 悬疑类项目默认 `strict`。
- 爽文可使用 `balanced`，但 reveal lock 仍必须生效。

### 26.4 检索精准度标准

2000 万字项目必须避免低相关内容污染上下文。

检索应采用混合策略：

```text
结构化过滤 + 关键词检索 + 向量检索 + 去重/重排
```

结构化过滤优先级：

- project
- branch
- volume
- plot_thread
- entity
- foreshadowing
- status
- chapter_range

建议字段：

```text
score
source_type
source_id
recency_score
importance_score
structural_match_score
final_score
reason
```

默认规则：

- 低于相关性阈值的内容不得进入上下文包。
- 冷数据默认降权。
- 已归档支线默认不加载。
- 检索命中必须记录进入上下文的理由。

### 26.5 分层索引策略

向量索引不应只做全局索引。

建议分层：

```text
project_global
volume_level
plot_thread_level
entity_level
foreshadowing_level
review_lesson_level
reference_level
```

实现方式可以是：

- 同一 Qdrant collection 中用 payload 过滤。
- 或按项目/用途拆分 collection。

P0 优先 payload 过滤，P1/P2 再考虑拆 collection。

### 26.6 伏笔自动告警规则

伏笔应按重要度配置不同告警阈值。

建议：

```text
critical   超过预计回收点 5 章未处理，创建 high 修订任务
high       超过预计回收点 10 章未处理，创建 medium 修订任务
medium     超过预计回收点 20 章未处理，Web 提醒
low        仅在卷尾结算时提醒
```

告警来源：

- 超过 `payoff_deadline_chapter`
- 超过 `expected_payoff_range`
- 卷尾仍未回收
- 关联伏笔已回收但自身未更新
- 被审查模型标记为遗忘

### 26.7 剧情线进度校验

剧情线长期不推进会导致烂尾。

建议字段：

```text
last_advanced_chapter
expected_next_advance_chapter
stall_threshold
importance
status
```

校验规则：

- 主线连续 N 章未推进时创建 warning。
- 关键支线超过阈值未推进时创建 revision task。
- 情感线、对抗线、悬疑线可单独设置阈值。
- 卷尾必须检查所有 active 剧情线。

### 26.8 批量管理要求

Web 和 MCP 应支持超长篇批量维护。

最低批量能力：

- 按卷筛选伏笔。
- 按重要度筛选伏笔。
- 批量归档废弃伏笔。
- 批量修改剧情线状态。
- 批量导入实体。
- 批量修改势力立场。
- 批量停用旧规则。

批量操作要求：

- 必须二次确认。
- 必须写审计日志。
- 必须支持导出操作前快照。

### 26.9 性能 SLO

以下指标作为目标值，不是一开始的硬承诺。实现时应记录实际耗时并逐步优化。

P0 目标：

```text
普通列表查询：<= 1000ms
普通章节上下文包生成：<= 5s
单章提交处理：<= 5s
单章增量索引入队：<= 2s
Web 常用页面首屏：<= 2s
```

P1 目标：

```text
10 万级结构化数据列表查询：<= 1000ms
普通章节上下文包生成：<= 3s
当前卷重建索引：<= 10min
审查聚合：<= 10s
```

P2 目标：

```text
百万级结构化数据分页查询稳定
跨卷长期记忆检索稳定
多项目并发生成上下文可限流
可观测性能仪表盘
```

超时降级：

- 上下文包生成超时，降级使用缓存摘要。
- 向量检索超时，降级使用 PostgreSQL 全文检索。
- 参考库检索超时，跳过参考素材。
- 审查聚合超时，保留单模型报告并标记待聚合。

### 26.10 同步触发时机

本地 AI 工具应明确何时同步 MCP。

触发时机：

```text
项目初始化完成
本地设定文档确认后
章节计划确认后
章节正文定稿后
章节审查完成后
人工大改正文后
每日定时增量同步
手动点击同步
```

不应同步：

- 未确认草稿。
- 废弃大纲。
- 临时模型输出。
- 未通过本地格式校验的 JSON。

### 26.11 冲突解决优先级

默认策略：

```text
硬 Canon 冲突：MCP active 且已审批版本优先
人物当前状态冲突：最新 accepted chapter commit 优先
伏笔状态冲突：最新 accepted commit + Web 人工确认优先
规则冲突：高优先级类型 + 高严重级别 + 更小生效范围优先
本地正文冲突：本地文件优先，MCP 只保存路径和哈希
审查提案冲突：不直接覆盖，进入人工审批
草稿冲突：草稿不得污染正式数据
```

冲突处理结果：

- `resolved_by_local`
- `resolved_by_mcp`
- `manual_merged`
- `proposal_created`
- `branch_created`
- `ignored`

### 26.12 分支管理最低要求

P0 阶段：

- 区分草稿提交和正式提交。
- 草稿不更新全局状态。
- 支持导出项目 JSON 快照。

P1 阶段：

- 支持项目快照恢复。
- 支持正式分支和草稿分支。

P2 阶段：

- 支持多剧情分支。
- 支持分支差异对比。
- 支持分支合并提案。

### 26.13 验收测试建议

基础测试：

- 创建项目后导入初始化数据。
- Web 能查看并编辑 Canon。
- 本地提交章节后状态更新。
- 审查 Critical 能阻断下一章。
- 草稿提交不污染正式状态。
- 过期状态不进入上下文包。
- abandoned 伏笔不进入上下文包。
- POV strict 不泄露角色未知信息。
- 卷切换后旧卷局部信息降权。
- 本地文件哈希变化能触发同步提示。

规模测试：

- 1 万条规则分页正常。
- 10 万条记忆块检索可用。
- 1000 个伏笔可按卷和状态筛选。
- 5000 个人物/势力/地点实体可分页维护。
- 单章增量索引不触发全量重建。

## 27. 二期迭代与工程配套需求总览

本节整合后续补充建议，作为一期之后的迭代需求池，同时标记部分必须前置的一期能力。

优先级定义：

```text
P0：一期必须实现，缺失会导致千万字规模运行故障或核心闭环断裂
P1：二期迭代优化，大幅提升创作效率、降低人工维护成本
P2：远期可选扩展，面向商用工作室、多端、多实例和分布式场景
工程配套：贯穿全开发周期，测试、运维、发布、迁移、降级必须同步建设
```

### 27.1 模型调度与标准化生产体系

#### P0：模型分层分工池

模型不应只配置一个默认模型，而应按任务分工。

建议分层：

```text
light_model      低成本模型：草稿、细纲、轻量润色、预审查
main_model       主力模型：正文、常规审查、上下文整理
premium_model    高端模型：高潮剧情、伏笔回收、深度一致性审查、Canon 修订建议
local_model      本地模型：离线草稿、低风险校验、隐私敏感任务
```

MCP 或本地工具需要支持：

- 按任务类型选择模型。
- 按章节类型选择模型。
- 高端模型并发限制。
- 模型失败自动降级。
- 降级后写入告警日志。
- 模型输出异常率统计。

注意：

- API key 默认仍由本地工具保存。
- MCP 保存模型 profile、用途、权重、限制，不强制保存密钥。

#### P0：模型输出结构化校验层

所有进入 MCP 的模型产物必须先标准化。

需要校验：

- chapter commit
- review report
- rule proposal
- state update proposal
- foreshadowing update proposal
- outline/chapter plan

要求：

- 本地 skill 负责清洗不同模型输出。
- MCP 使用 JSON Schema 或等价规则做强校验。
- 非法格式拒收，并返回修复提示。
- 统计模型格式错误率。
- 高频格式错误模型降低权重或退出默认流程。

#### P0：全链路日志埋点

所有关键操作都应有统一日志字段。

字段建议：

```text
trace_id
workspace_id
project_id
user_id
client_id
operation_type
tool_name
resource_type
resource_id
duration_ms
result_status
error_code
error_message
stack_trace
token_usage
model_profile
created_at
```

Web 应提供日志检索：

- 按项目筛选。
- 按时间筛选。
- 按工具/操作筛选。
- 按错误类型筛选。
- 按耗时排序。

#### P1：Prompt 模板托管

建议新增 `prompt_templates` 能力。

模板类型：

- 初始化访谈。
- 基础设定整理。
- 总纲生成。
- 分卷大纲。
- 章节细纲。
- 正文分段。
- 审查。
- 规则提取。
- 状态提取。
- 伏笔提取。

字段建议：

```text
id
project_id nullable
template_type
key
title
content
variables
scope_type
scope_ref
version
status
created_by
updated_at
```

Web 能力：

- 编辑模板。
- 查看版本。
- 配置生效范围。
- 预览变量注入结果。

#### P1：Token 与成本统计

需要记录：

- 上下文包 token。
- 生成输入/输出 token。
- 审查输入/输出 token。
- 模型 profile。
- 章节/分卷/项目维度成本。

Web 看板：

- 单项目成本。
- 单卷成本。
- 单章节成本。
- 每日成本预估。
- 高成本任务排行。
- 成本阈值告警。

### 27.2 网文连载商业化与读者期待管理

#### P1：连载数据统计看板

产出指标：

- 总字数。
- 分卷字数。
- 日均更新。
- 断更预警。
- 章节完成率。

质量指标：

- OOC 次数。
- 设定冲突次数。
- Critical 审查问题。
- 逾期伏笔。
- 修订任务完成率。

商业指标：

- 爽点密度。
- 升级间隔。
- 冲突间隔。
- 章末钩子有效率。
- 主线推进频率。

#### P1：读者长线期待库

建议新增 `expectation_hooks` 能力。

用途：

- 存储长线悬念。
- 存储未兑现承诺。
- 存储读者核心期待。
- 约束 AI 持续铺垫。
- 检查过快填坑或长期搁置。

字段建议：

```text
key
title
expectation_type
status
introduced_chapter
expected_payoff_range
importance
related_foreshadowing_ids
related_plot_threads
notes
```

#### P1：工业化网文素材库增强

参考库应按网文生产细分。

素材类型：

- 打斗桥段。
- 对话模板。
- 升级打脸。
- 反转。
- 情感桥段。
- 压迫感描写。
- 章末钩子。
- 爽点结构。

要求：

- 按题材、境界、场景、剧情线打标签。
- 上下文包按当前章节类型匹配素材。
- 统计桥段复用率。
- 重复度过高时生成优化规则提案。

### 27.3 人机协同与批量创作工具

#### P0：退场实体自动降级

实体生命周期：

```text
active -> minor -> exited -> archived
```

规则：

- 连续 N 卷无出场的人物/势力/道具自动标记 `exited`。
- `exited` 默认不进入上下文。
- 检索命中时只加载极简摘要。
- 可手动恢复为 `active`。
- 全量历史快照保留。

#### P0：上下文包自动去重

组装上下文时需要去重：

- 重复 Canon。
- 重复事件。
- 重复规则。
- 同一状态多版本。
- 相似历史摘要。

去重策略：

- 保留高优先级。
- 保留最新 active。
- 保留来源更可靠的事实。
- 被去重内容写入上下文包 audit。
- Web 预览显示被去重条目。

#### P0：跨卷主线一致性预检

建议新增：

```text
workflow.validate_volume_switch
```

检查：

- 主线断层。
- 跨卷伏笔冲突。
- 人物境界/状态矛盾。
- Canon 冲突。
- 上卷遗留任务。
- 下卷目标是否承接。

失败时：

- 阻断换卷生成。
- 输出整改清单。
- 创建修订任务。

#### P1：完整工程包导入导出

工程包包含：

- Canon。
- 人物/势力/地点/道具。
- 规则。
- 剧情线。
- 伏笔。
- 审查配置。
- Prompt 模板。
- 上下文 profile。
- 本地绑定 manifest。

导出范围：

- 整项目。
- 单卷。
- 仅设定。
- 仅规则。
- 仅审查配置。

导入策略：

- 覆盖。
- 合并。
- 生成提案。
- 作为新分支导入。

所有导入导出写审计日志。

#### P1：批量维护工具集

建议新增：

```text
state.entity.bulk_patch
foreshadowing.bulk_status_update
rules.bulk_toggle
reference.bulk_import
canon.doc.bulk_import
```

Web 配套：

- CSV 导入。
- 批量操作表单。
- 操作前预览。
- 二次确认。
- 操作前快照。

#### P1：人工协作批注系统

Web 支持对以下对象批注：

- Canon。
- 人物。
- 剧情线。
- 伏笔。
- 审查报告。
- 修订任务。

批注可转换为：

- 修订任务。
- 规则提案。
- 状态提案。
- 待办事项。

支持：

- @成员。
- 分配负责人。
- 截止时间。
- 状态流转。

#### P1：自定义上下文权重编辑器

Web 可视化配置：

- Canon 权重。
- 人物状态权重。
- 伏笔权重。
- 规则权重。
- 记忆权重。
- 审查经验权重。
- 参考素材权重。

配置范围：

- 项目。
- 分卷。
- 剧情线。
- 章节类型。

#### P1：批量预生成细纲

支持批量生成数十章细纲，存入 `chapter_plans`。

要求：

- 批量预检剧情线。
- 批量检查伏笔冲突。
- 批量检查章节间节奏。
- 后续正文生成直接复用细纲。

#### P1：核心专有名词锁定

Canon 应支持关键词白名单。

用途：

- 防止人名写错。
- 防止境界名漂移。
- 防止神器名变体。
- 防止势力名称混用。

审查检测到错误时：

- 创建修订任务。
- 提醒本地工具修正。
- 上下文包强制注入标准名称。

#### P1：多版本正文差异对比

Web 可上传多版正文元数据或摘要进行对比。

检测：

- 人设差异。
- 剧情差异。
- 状态差异。
- 伏笔差异。
- 设定差异。

结果可生成：

- 状态更新提案。
- 伏笔更新提案。
- 事件更新。
- 修订任务。

### 27.4 超长文本数据治理与冷热归档

#### P0：数据生命周期归档

卷级生命周期：

```text
active -> recent -> archive -> deep_archive
```

建议：

- 当前卷：完整热加载。
- 近 10 卷：摘要轻量加载。
- 完结旧卷：默认不进上下文，仅检索命中进入。
- 远期旧卷：仅保留极简摘要，向量按需重建。

#### P0：冗余数据定时清理

可清理对象：

- 30 天未转正废弃草稿 commit。
- 过期驳回规则提案。
- 7 天以上完成/失败向量任务。
- 超 10 卷已回收或废弃伏笔详情。
- 临时上下文缓存。

要求：

- 清理前生成清单。
- 写审计日志。
- 支持恢复窗口。

### 27.5 合规安全与 API 权限管控

#### P0：分层合规审查

合规审查是独立维度，优先级高于普通剧情错误。

检查：

- 违禁词。
- 价值观风险。
- 地域/民族/宗教禁忌。
- 平台敏感规则。
- 项目自定义禁区。

合规 critical：

- 阻断章节进入下一步。
- 强制人工修订。
- 记录审计。

#### P0：数据脱敏与导出权限

项目所有者可控制：

- 是否允许完整导出。
- 是否允许导出核心 Canon。
- 是否允许导出结局设定。
- 是否允许导出终极伏笔。
- 是否允许导出审查报告。

导出时：

- 可脱敏核心金手指。
- 可脱敏终极伏笔。
- 可脱敏结局。
- 写入操作人、时间、项目水印。

#### P0：API Token 分级与限流

Token 类型：

```text
read_only
generate
review
editor
admin
```

限制：

- 按用户 QPS。
- 按工作区 QPS。
- 每日调用上限。
- 高风险工具二次权限。
- 异常高频调用自动临时限流。

### 27.6 可视化与全局辅助创作

#### P1：全局冲突总览看板

聚合展示：

- 规则冲突。
- 逾期伏笔。
- 未解决 Critical 审查任务。
- 人物状态矛盾。
- 停滞剧情线。
- 同步冲突。

支持一键跳转处理。

#### P1：全书时间线校验

Web 展示全书时间轴。

检测：

- 事件顺序颠倒。
- 人物同时出现在矛盾地点。
- 道具归属冲突。
- 闭关/旅行/战斗时间不合理。

#### P1：全局跨模块检索

统一搜索：

- 人物。
- 势力。
- 地点。
- 道具。
- 伏笔。
- 剧情线。
- 规则。
- 审查报告。
- 修订任务。

#### P2：关系图谱与模板市场

关系图谱：

- 人物关系。
- 势力关系。
- 隐藏秘密关系。
- 敌对/好感/信任强度。

模板市场：

- 玄幻。
- 都市。
- 古言。
- 悬疑。
- 科幻。

模板内容：

- Canon 模板。
- 力量体系模板。
- 通用规则。
- 审查维度。
- Prompt 模板。

### 27.7 离线与分布式架构预留

#### P2：增强离线完整创作模式

本地持久化离线包：

- 全套基础设定。
- 主要人物状态。
- 当前规则。
- 近百卷摘要。
- 当前伏笔。
- 当前章节计划。

断网时：

- 可生成草稿。
- 可本地审查。
- 不可审批硬 Canon。
- 不可提交正式状态。
- 联网后批量同步并展示冲突。

#### P2：分布式 MCP 预留

设计要求：

- 所有数据携带 workspace/project 隔离字段。
- 后台任务可幂等重试。
- Redis 锁可替换为分布式锁。
- Qdrant payload 支持项目级过滤和未来分片。
- 数据迁移脚本支持多版本升级。

### 27.8 边缘业务场景

#### P1：多 POV 批量校验

批量检查：

- 多视角信息泄露。
- 角色未知信息误写。
- 隐藏伏笔提前揭露。
- 读者视角信息不一致。

#### P1：阶段性剧情封印规则

支持：

- 分卷禁止开启支线。
- 阶段性禁止回收伏笔。
- 某角色暂时不能登场。
- 某金手指暂时失效。

#### P1：本地草稿自动清理

策略：

- 废弃草稿自动归档。
- 超期草稿自动删除或压缩。
- MCP 中无效 draft commit 定期清理。
- 清理前写审计并保留恢复窗口。

### 27.9 工程落地配套规范

工程配套为全阶段强制要求。

#### 分层测试

单元测试：

- MCP 工具。
- 字段校验。
- 规则冲突。
- 状态计算。
- 上下文过滤。

集成测试：

```text
本地初始化 -> 导入 MCP -> 生成章节 -> 提交 commit -> 多模型审查 -> 聚合 -> 规则提案 -> 审批 -> 下一章上下文
```

极限压测：

- 单项目 1000 卷。
- 2000 万字等价摘要和事件数据。
- 10 万级记忆块。
- 5000+ 实体。
- 1000+ 伏笔。

#### 环境规范

```text
dev   本地开发调试
test  自动化测试和压测
prod  NAS 生产部署
```

生产要求：

- 定时自动备份。
- 禁止手动改底层数据。
- 所有迁移脚本留痕。

#### 发布回滚

要求：

- 数据库结构变更向前兼容。
- 禁止无备份破坏性修改。
- 发布前备份 PostgreSQL。
- 发布前备份 Web 用户配置。
- 发布前备份向量任务配置。
- 定义 5 分钟快速回滚流程。

回滚触发：

- 数据同步错乱。
- 上下文包生成崩溃。
- 审查闭环失效。
- 登录/权限异常。
- 大范围写入错误。

#### 第三方依赖降级

Qdrant 宕机：

- 降级 PostgreSQL 全文检索。
- 标记检索精度下降。

Redis 断开：

- 使用本地/进程内短期缓存。
- 限制并发任务。
- 暂停非关键后台任务。

大模型 API 超时：

- 自动切换备用模型。
- 降级到草稿模式。
- 创建告警。

#### 数据迁移规范

要求：

- 所有迁移可重复执行。
- 所有迁移记录版本。
- 新版本自动适配旧字段。
- 千万级历史数据迁移必须支持批处理。
- 迁移失败可回滚或安全重试。

### 27.10 最终优先级总览

#### P0：一期核心开发

- 模型分层调度。
- 模型输出结构化校验。
- 全链路日志埋点。
- Token 成本统计与告警。
- 退场实体自动降级。
- 上下文去重。
- 跨卷主线一致性预检。
- 冷热数据生命周期归档。
- 冗余数据定时清理。
- POV 视角隔离。
- 状态时效过期。
- 伏笔回收告警。
- 规则作用域与临时规则。
- 合规分层审查。
- API Token 分级限流。
- 数据导出权限控制。

#### P1：二期效率增强

- Prompt 模板托管。
- 连载统计看板。
- 读者期待库。
- 工业化素材库增强。
- 工程包导入导出。
- 批量维护工具。
- 协作批注系统。
- 上下文权重编辑器。
- 批量细纲预生成。
- 专有名词锁定保护。
- 多版本正文差异对比。
- 全局冲突看板。
- 全书时间线校验。
- 全局跨模块检索。
- 多 POV 批量校验。
- 阶段性剧情封印规则。
- 本地草稿自动清理。

#### P2：远期扩展

- 人物/势力关系可视化图谱。
- 题材模板市场。
- 增强离线完整创作模式。
- 分布式 MCP 水平扩展。
- 多剧情分支合并。
- 外部通知集成。
