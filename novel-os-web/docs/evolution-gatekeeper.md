# 进化门禁系统

> 所有进化产出经 gatekeeper 模型风险评估后决定直接写入或待管理员审批，全程可追溯可回滚。

---

## 一、需求

1. 讨论室/Agent/用户产生的知识、规则等进化产出，不能无脑写入全局表
2. 不能全部靠管理员人工审核
3. 用 gatekeeper 模型自动评估风险：低风险直接写，中高风险管理员审批
4. 所有进化操作记录 evolution_log，支持管理员回滚
5. 普通用户不能通过 Web UI 修改全局内容

---

## 二、设计

### 2.1 权限模型

| 操作 | 用户 | 讨论室 | Agent | 管理员 |
|---|---|---|---|---|
| 读全局规则/UK | ✅ | ✅ | ✅ | ✅ |
| 写全局规则/UK | ❌ | ⚠️门禁 | ⚠️门禁 | ✅ |
| 写项目规则/PK | ✅ | ✅ | ✅ | ✅ |
| 审批中高风险 | ❌ | ❌ | ❌ | ✅ |
| 回滚进化 | ❌ | ❌ | ❌ | ✅ |
| 查进化日志 | 自己的 | 自己的 | 自己的 | 全部 |

### 2.2 门禁流程

```
进化产出（source: discussion_room/agent/user）
    │
    ▼
gatekeeper 模型评估
    │  输入: {type, content, target_table, source_type, old_value?}
    │  输出: {risk: low/medium/high, reason, auto_apply}
    │
    ├─ risk=low → 直接写入目标表 + evolution_log
    │
    └─ risk=medium/high → system_evolution_proposals(pending_admin)
                            + evolution_log
                              ↓
                          管理员 Web UI 审批 / 拒绝
                              ↓
                          审批通过 → 写入目标表 + evolution_log(已审批)
```

### 2.3 风险判定规则

gatekeeper 模型的 system prompt 指导原则：

| 条件 | 风险 | 处理 |
|---|---|---|
| 写入项目级表（PK/canon_rules/state_entities）| low，自动通过 |
| 写入全局表 + 讨论室多模型共识 | low，自动通过 |
| 写入全局表 + 单 Agent 建议 | medium，管理员审 |
| 修改/覆盖已有全局规则/UK | medium，管理员审 |
| 删除全局数据 | high，管理员审 |
| source=user（Web UI 手动）| 跳过门禁，直接写 |

### 2.4 数据表

#### `evolution_logs`

```sql
CREATE TABLE evolution_logs (
    id           UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    source_type  TEXT NOT NULL,        -- discussion_room / agent / user
    source_id    TEXT,                 -- session_id / chapter_no / username
    action       TEXT NOT NULL,        -- INSERT / UPDATE / DELETE
    target_table TEXT NOT NULL,        -- global_rules / universal_knowledge / canon_rules / ...
    target_id    TEXT,                 -- 写入后的目标记录 id
    old_value    JSONB,                -- 更新前值，用于回滚
    new_value    JSONB,                -- 写入的新值
    risk_level   TEXT,                 -- low / medium / high
    risk_reason  TEXT,                 -- gatekeeper 给出的理由
    auto_applied BOOLEAN DEFAULT false, -- 是否自动写入
    proposal_id  UUID REFERENCES system_evolution_proposals(id), -- 关联待审提案
    created_at   TIMESTAMPTZ DEFAULT now(),
    created_by   TEXT                  -- username
);
```

### 2.5 MCP 工具

| 工具 | 说明 |
|---|---|
| `evolution.logs` | 列出进化日志，管理员看全部，用户看自己的 |
| `evolution.rollback` | 管理员回滚指定日志，恢复 old_value 到 target_table |
| `evolution.stats` | 进化统计：按 source_type/risk_level/target_table 分布 |

### 2.6 前端页面

| 页面 | 功能 |
|---|---|
| `evolution-logs-page.js` | 进化日志列表 + 筛选（来源/风险/表）+ 回滚按钮（管理员）|
| `global-rules-page.js` | 改造：普通用户只读，新建/编辑/删除仅管理员可见 |

### 2.7 讨论室接入

`discussion_room.apply_results` 中，全局级写入（UK/global_rules）改走 gatekeeper 而非直接写表。

---

## 三、开发计划

### 阶段 1：数据库 + 后端基础

| 步骤 | 内容 | 预估 |
|---|---|---|
| 1.1 | 创建 `evolution_logs` 表 | 2 min |
| 1.2 | 新增 `services/gatekeeper.py` | 15 min |
| 1.3 | 新增 `tools/evolution.py`（logs/list/rollback） | 8 min |

### 阶段 2：改造讨论室

| 步骤 | 内容 | 预估 |
|---|---|---|
| 2.1 | `apply_results` 全局级走 gatekeeper | 10 min |
| 2.2 | `create_session` 优先使用项目级 discussion 模型 | 5 min |

### 阶段 3：前端

| 步骤 | 内容 | 预估 |
|---|---|---|
| 3.1 | `evolution-logs-page.js` | 15 min |
| 3.2 | `global-rules-page.js` 只读模式 | 5 min |
| 3.3 | 菜单 + index.html 注册 | 3 min |

### 阶段 4：部署验证

| 步骤 | 内容 | 预估 |
|---|---|---|
| 4.1 | 部署 + 验证完整流程 | 10 min |

### 合计

~73 min