# Novel OS MCP 项目需求摘要

更新时间：2026-06-27

本文档提炼当前需求，供新窗口快速理解业务目标。完整需求详见 [requirements-and-dev-brief.md](./requirements-and-dev-brief.md)。

## 目标场景

用户希望用 AI 长期生成并维护一部约 2000 万字规模的网络小说。系统必须解决：

- 超长上下文无法一次性喂给模型的问题。
- 长期设定、人设、境界、势力、伏笔、剧情线漂移问题。
- 多章节、多卷、多模型审查后的规则演化问题。
- 多用户、多小说、多工作区隔离问题。
- 正文、大纲、细纲等可人工编辑文件的本地保存问题。
- NAS 长期部署、低维护、可备份、可扩展问题。

## 核心边界

### MCP 保存什么

MCP 保存中心化、结构化、可检索、可审计的数据：

- workspace、project、user、api token
- Canon 文档和版本
- 规则、规则提案、规则版本
- 人物/势力/地点/道具等实体
- 当前状态快照、临时状态、状态过期字段
- 实体关系
- 卷、剧情线、章节计划
- 伏笔、伏笔关联、回收状态
- 章节摘要、十章摘要、卷摘要、全书摘要
- review job、review report、revision task
- 模型审查质量统计
- 本地文件 path hint、hash、word count
- memory chunks、vector index metadata
- audit logs

### 本地保存什么

本地保存作者可能直接编辑的文件：

- 原始大纲
- 细纲
- 章节正文
- 草稿
- 多版本正文
- 审查 Markdown/HTML
- 导出稿
- 临时灵感素材

MCP 只保存这些文件的路径提示、hash、字数、摘要和结构化提取结果。

## 数据分层

### 项目基础层

保存项目、题材、语言、目标平台、用户、工作区、成员、API token、项目绑定。

### Canon 设定层

保存硬设定和版本：

- 世界观
- 力量体系
- 金手指规则
- 禁止修改的基础设定
- 文风/题材模板
- 平台合规边界

硬 Canon 不允许审查系统自动改，只能生成提案并人工审批。

### 状态层

保存当前事实：

- 人物状态
- 境界/等级
- 伤势/buff/debuff
- 道具持有
- 阵营归属
- 关系变化
- 临时身份/伪装
- 生效章节、过期章节、持续类型

上下文包应优先加载当前事实，过滤过期状态。

### 剧情层

保存：

- 卷信息
- 主线/支线/情感线/商业节奏线
- 章节计划
- 剧情推进状态
- 停滞检查

### 伏笔层

保存：

- 明线伏笔
- 暗线伏笔
- 幕后伏笔
- parent/child 关联
- related keys
- 触发条件
- 预计回收范围
- 回收 deadline
- planted/revealed/resolved/abandoned 状态

### 规则层

规则用于约束生成和审查：

- canon
- character
- plot
- style
- pacing
- reveal_lock
- compliance
- lesson
- commercial

规则必须支持作用域、生命周期、优先级、临时规则、冲突处理和人工审批。

### 记忆层

分层摘要与检索：

- chapter summary
- ten-chapter summary
- volume summary
- book summary
- memory chunks
- vector search

长距离历史优先读高层摘要，必要时再检索细粒度记忆。

### 审查层

审查不直接改事实，输出：

- revision task
- rule proposal
- state proposal
- foreshadowing proposal
- model quality signal
- blocking decision

## 上下文包要求

上下文包是生成质量的核心。必须做到：

- AI 每次只读局部上下文，不读取全书。
- 硬 Canon、当前人物状态、生效规则永远优先。
- 近期章节、当前剧情线、活跃伏笔、相关历史通过预算裁剪。
- 超预算时先压缩历史摘要，不删除硬 Canon。
- 支持 chapter context 和 segment context。
- 支持 POV 隔离：主角视角、单角色视角、上帝视角、读者视角、审查视角。
- 自动过滤 superseded/blocked rule、abandoned foreshadowing、过期状态。

## 审查闭环要求

审查链路：

```text
本地 AI 生成章节
本地保存正文
提交结构化 commit
创建 review job
多个模型审查
提交 model reports
MCP aggregate
生成 revision tasks / rule proposals / state proposals / foreshadowing proposals
人工审批规则和事实更新
下一章上下文读取更新后的规则和状态
```

严重级别：

- Critical/Blocking：阻断下一章，强制人工修订。
- High/Warning：生成修订任务，作者可处理或跳过。
- Info/Low：记录经验，不阻塞。

## 模型配置需求

用户要求可灵活配置：

- 大纲撰写模型
- 细纲模型
- 正文模型
- 分段正文模型
- 润色模型
- 审查模型
- 合规审查模型
- 高端模型/低成本模型分层

默认可以使用当前 API key；审查默认可只用一个模型直接跑，但架构必须支持多个模型联合审查。

Phase 2.10 需要开始做模型 profile、路由和成本统计。

## Web 控制台定位

Web 不负责小说初始化对话。初始化应由本地 AI 工具/skill 完成。

Web 负责维护 MCP 中的数据：

- 项目选择
- Canon 文档
- 人物/势力/地点/道具
- 状态快照
- 关系网络数据
- 剧情线
- 伏笔
- 规则库
- 审查报告和修订任务
- 上下文包预览
- 同步冲突
- 审计日志
- 模型配置

Web 必须支持中英文切换。

## 多用户和多小说隔离

必须支持：

- 一个用户多个小说。
- 多个用户/朋友使用同一 MCP 服务。
- 每个 workspace/project 数据隔离。
- 每个项目可单独配置规则、模型、API token、上下文 profile。
- 不能跨项目泄漏设定、伏笔、正文路径、审查报告。

## P0 必须保证

- 数据结构足够支撑 2000 万字。
- 上下文包可控，不随字数增长而膨胀。
- 规则和状态能防漂移。
- 审查能阻断 critical 问题。
- 本地文件与 MCP 有 hash 同步契约。
- NAS 可部署、可备份、可冒烟验证。
- 新增功能必须有脚本验证。

## P1 重要增强

- Prompt 模板托管
- token 成本统计
- 连载商业节奏看板
- 读者期待库
- 批量维护工具
- 工程包导入导出
- 协作批注
- 上下文权重编辑器
- 批量细纲预生成
- 专有名词锁定
- 多版本正文差异对比
- 全局冲突看板
- 全书时间线校验

## P2 远期

- 完整离线创作模式
- 分布式 MCP 水平扩展
- 人物/势力图谱
- 题材模板市场
- 多实例部署

## 最重要的产品判断

不要把系统做成“一个大模型写完全部”。它应该是一个长期写作操作系统：

- 本地 AI 负责创作和文件产出。
- MCP 负责记忆、规则、事实、审查、检索和同步。
- Web 负责可视化维护。
- 审查系统负责发现漂移，但不越权自动改硬设定。
