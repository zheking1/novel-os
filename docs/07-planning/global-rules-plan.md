# 全局规则管理方案

> 目标：统一创作规则和审查规则的管理，支持项目→全局升级流程，融入讨论室机制。

---

## 一、需求文档

### 1.1 现状问题

| 问题 | 详情 |
|---|---|
| 规则分散 | 创作规则（`rules-list-page.js`）和审查规则（`compliance-page.js`）分别在两个 UI 管理，但底层是同一张 `canon_rules` 表，只是 `rule_type` 不同 |
| 没有全局规则 | 所有规则都绑定 `project_id`，没有跨项目共享的全局规则 |
| 升级流程缺失 | 审查发现问题 → 创建项目规则 → 然后就停了，没有"是否该提升为全局规则"的评估环节 |
| 讨论室不参与 | 讨论室 `apply_results` 能写规则（`rule_type='discussion'`），但和项目规则/全局规则没有联动 |
| 规则类型混淆 | `canon_rules.scope` 字段有 `global/system/user/project` 四种值，但都是"项目内 global"，语义误导 |

### 1.2 需求目标

1. **新增全局规则表** — 跨项目生效的规则，区分创作规则和审查规则
2. **新增全局规则管理页** — 创建/编辑/删除/查看全局规则，按类型筛选
3. **统一项目规则页** — 合并创作规则和审查规则为一个页面，Tab 切换
4. **规则升级流程** — 项目规则 → 讨论室评估 → 升级为全局规则
5. **审查触发升级** — 审查环节产生新规则后，自动标记为"待评估"，触发讨论室

---

## 二、设计文档

### 2.1 数据层

#### 新增表：`global_rules`

```sql
CREATE TABLE global_rules (
    id              UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    rule_key        TEXT NOT NULL UNIQUE,
    rule_type       TEXT NOT NULL,          -- 'creative' | 'compliance'
    title           TEXT NOT NULL,
    content         TEXT NOT NULL,
    severity        TEXT NOT NULL DEFAULT 'warning',
    status          TEXT NOT NULL DEFAULT 'active',
    metadata        JSONB NOT NULL DEFAULT '{}',
    source_project_id UUID,                 -- 来源项目
    promoted_from_rule_id UUID,             -- 来源项目规则
    promoted_by     TEXT,                   -- 操作人
    discussion_id   TEXT,                   -- 关联讨论室会话
    created_at      TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at      TIMESTAMPTZ NOT NULL DEFAULT now()
);
```

#### `canon_rules` 新增字段

```sql
ALTER TABLE canon_rules ADD COLUMN promotion_status TEXT DEFAULT NULL;
-- 'pending_review' | 'promoted' | 'rejected'
ALTER TABLE canon_rules ADD COLUMN promoted_to_global_id UUID REFERENCES global_rules(id);
ALTER TABLE canon_rules ADD COLUMN discussion_id TEXT;
```

### 2.2 rule_type 统一规范

| rule_type | 含义 | 使用场景 |
|---|---|---|
| `creative` | 创作规则 | 角色行为、世界一致性、风格指南、情节约束 |
| `compliance` | 审查规则 | 敏感词、违禁内容、质量红线、格式要求 |

**废弃旧值**：`character`, `plot`, `world`, `style` 统一合并为 `creative`。

### 2.3 MCP 工具层

#### 新增工具（4 个）

| 工具 | 参数 | 说明 |
|---|---|---|
| `global_rules.list` | `rule_type?, status?, limit?` | 列出全局规则，支持按类型筛选 |
| `global_rules.upsert` | `rule_key, rule_type, title, content, severity?, status?, metadata?` | 创建/更新全局规则 |
| `global_rules.delete` | `rule_key` | 删除全局规则（软删除） |
| `global_rules.promote` | `workspace, project, rule_key, create_discussion?` | 将项目规则提升为全局规则，可选创建讨论室会话 |

#### 改造现有工具

| 工具 | 改动 |
|---|---|
| `rules.list` | 增加 `rule_type` 参数支持 `creative`/`compliance` 筛选 |
| `compliance.rule.*` | 保留但底层改为走 `rules.*`（兼容已存在的 JS 调用），标记 deprecated |
| `discussion_room.apply_results` | 新增 `type="promote_rule"` 处理，调用 `global_rules.promote` |

### 2.4 前端页面

#### 新增：全局规则管理页 (`global-rules-page.js`)

- 顶部 Tab：全部 / 创作规则 / 审查规则
- 表格列：rule_key, title, rule_type, severity, status, source_project, promoted_at
- 操作：新建 / 编辑 / 删除 / 禁用
- 不需要选择项目即可使用

#### 改造：项目规则页 (`rules-list-page.js`)

- 合并 `compliance-page.js` 的功能
- 顶部 Tab：创作规则 / 审查规则
- 每条规则新增"升级为全局"按钮 → 触发讨论室
- 升级状态标签：待评估 / 已升级 / 已拒绝
- 可查看关联的讨论室会话

#### 移除：`compliance-page.js`（功能合并到 rules-list-page.js）

#### 菜单调整

```diff
- 项目管理 > 设定管理 > 创作规则
- 项目管理 > 生成与审查 > 合规检查
+ 项目管理 > 设定管理 > 项目规则 (统一入口)
+ 知识库 > 知识管理 > 全局规则 (新增)
```

### 2.5 升级流程

```
审查 → 发现问题
  │
  ▼
创建项目规则 (promotion_status = 'pending_review')
  │
  ▼
触发讨论室 (create_discussion=true)
  │  讨论室评估：该规则是否适合所有项目？
  │  是 → 继续   否 → 标记 rejected
  │
  ▼
discussion_room.apply_results
  │  type="promote_rule"
  │
  ▼
global_rules.promote
  │  写入 global_rules
  │  更新 canon_rules.promotion_status = 'promoted'
  │  更新 canon_rules.promoted_to_global_id
  │
  ▼
全局规则生效 ──→ 所有项目在生成/审查时加载
```

### 2.6 上下文加载调整

`context.py` 中加载规则时，当前只查 `canon_rules WHERE project_id = $1`。需改为：

```python
-- 项目规则 + 全局规则
SELECT * FROM canon_rules WHERE project_id = $1 AND status = 'active'
UNION ALL
SELECT * FROM global_rules WHERE status = 'active'
```

---

## 三、开发计划

### 阶段 1：数据库 + 后端

1. 创建 `global_rules` 表
2. `canon_rules` 加字段
3. 新增 `global_rules.*` 4 个 MCP 工具
4. 改造 `rules.list` 支持 `creative`/`compliance`
5. 改造 `discussion_room.apply_results` 支持 `promote_rule`
6. 改造 `context.py` 加载全局规则

### 阶段 2：前端

1. 新增 `global-rules-page.js`
2. 改造 `rules-list-page.js` 合并合规检查
3. 删除 `compliance-page.js` 引用
4. 调整菜单

### 阶段 3：验证

1. 创建全局规则 → 在任意项目中生效
2. 项目规则 → 升级为全局 → 讨论室 → 全局规则生效
3. 审查 → 产生规则 → 触发讨论室 → 升级

### 工作量预估

| 阶段 | 内容 | 预估 |
|---|---|---|
| 1 | 数据库 + 后端 6 工具 + context.py | 40 min |
| 2 | 前端 2 页面 | 30 min |
| 3 | 验证 | 15 min |
| **合计** | | **~85 min** |