# 工具/实用页面

## discussion-room-page.js

AI 讨论室 — 模拟多个 AI 角色进行讨论。

### 功能

- 创建讨论室
- 添加参与者 (AI 模型)
- 设定讨论主题
- 实时轮询讨论结果
- 展示对话内容

### 使用的 MCP 工具

- `discussion.start` — 开始讨论
- `discussion.poll` — 轮询讨论结果

---

## pipeline-page.js

内容生成流水线页面。

### 功能

- 选择生成任务类型 (上下文/起草/润色/审核)
- 触发流水线执行
- 轮询/展示执行状态
- 查看生成结果

### 使用的 MCP 工具

- `pipeline.generate` — 执行生成任务 (task_type: polish/review/draft/context)

---

## canon-list-page.js

Canon 条目管理页面。

### 功能

- Canon 列表和搜索
- 管理项目规则和准则

---

## rules-list-page.js

规则列表页面。管理项目的写作规则。

---

## review-council-page.js

审核委员会配置页面。

### 功能

- 配置审核委员会的成员模型
- 为每个审核维度分配模型
- 维度模型映射管理

### 使用的 MCP 工具

- `review.list_council_configs`
- `review.upsert_council_config`

---

## expectations-page.js

预期管理页面。设定和管理读者对剧情的预期。

---

## global-rules-page.js

全局规则管理页面。跨项目的通用写作规则（仅 admin）。

---

## materials-page.js

素材库页面。管理创作素材 (图片、参考资料等)。

---

## system-notifications-page.js

系统通知页面。展示系统级通知和消息。

---

## evolution-logs-page.js

进化日志页面。展示系统进化的历史记录（仅 admin）。

---

## binding-matrix-manager.js

绑定矩阵管理页面。管理实体间的绑定关系矩阵。

---

## context-preview-page.js

上下文预览页面。在生成前预览将注入的上下文信息。

### 使用的 MCP 工具

- 上下文构建和预览工具

---

## local-projects-page.js

本地项目页面。管理本地存储的项目文件。

---

## level-manager.js

分级管理器 (Item Level 管理)。

基于 Alpine 组件 `itemLevelManager`:
- 管理分级配置 (如重要度等级)
- CRUD: name, desc, order, range
- 存储: `setting.category` (slug='item-level') + `setting.item`

---

## category-manager.js

分类管理器。管理知识库/素材的分类体系。

---

## genre-manager.js

题材管理器。管理和配置创作题材。