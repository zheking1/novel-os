# System Evolution 服务 — 系统级进化管理

**源码**: 
- `novel-os-mcp/src/novel_os_mcp/tools/system_evolution.py` (684 行)
- `novel-os-mcp/src/novel_os_mcp/ai_reviewer_worker.py` (211 行)
- `novel-os-mcp/src/novel_os_mcp/tools/system_notifications.py`

## 概述

System Evolution 服务实现 AI 驱动的系统级数据进化。覆盖从提案创建、AI 初审、管理员终审到实际应用的完整流程。

## 目标实体类型

| 类型 | 对应系统表 | 说明 |
|------|------|------|
| `style_profile` | `system_style_profiles` | 系统级文风档案 |
| `prompt_template` | `system_prompt_templates` | 系统级提示词模板 |
| `model_profile` | `system_model_profiles` | 系统级模型配置 |
| `knowledge_item` | `knowledge_entities` | 知识实体 |
| `setting_item` | `setting_items` | 设定项 |
| `genre_config` | `setting_genres` | 体裁配置 |

## 数据库表

| 表名 | 说明 |
|------|------|
| `system_evolution_proposals` | 进化提案 |
| `system_style_profiles` | 系统级风格档案 |
| `system_prompt_templates` | 系统级 Prompt 模板 |
| `system_model_profiles` | 系统级模型配置 |
| `system_notifications` | 系统通知 |

---

## 一、提案生命周期

### 状态流转

```
draft → ai_reviewing → ai_reviewed → pending_admin → admin_approved → applied
  ↑                          ↓               ↓                ↓
  └── request_changes        ai_rejected     pending_admin    admin_rejected
```

### 提案类型

| 类型 | 说明 | 需要 target_entity_key |
|------|------|------|
| `create` | 创建新实体 | 否 |
| `update` | 更新已有实体 | 是 |
| `delete` | 删除实体 | 是 |
| `merge` | 合并实体 | 是 |

---

## 二、提案管理工具

### system.evolution.propose

创建系统级进化提案:

| 参数 | 说明 |
|------|------|
| `title` | 提案标题 |
| `description` | 详细描述 |
| `proposal_type` | 提案类型 |
| `target_entity_type` | 目标实体类型 |
| `proposed_content` | 提案具体内容 (dict) |
| `evolution_reason` | 进化原因 |
| `target_entity_key` | 目标实体键 (更新/删除/合并时必填) |
| `evidence` | 支撑数据 |
| `source_project_id` / `source_chapter_no` | 来源追踪 |

提案创建后自动进入 `ai_reviewing` 状态。

### system.evolution.list

列出提案，支持按 `status`、`target_entity_type`、`proposal_type`、`submitted_by_me` 过滤。

返回 `ai_score` (从 `ai_review_result.score` 提取) 和 `is_ai_submitted`。

### system.evolution.get

获取提案完整详情，含:
- `ai_review_result`: AI 评审结果 (JSONB)
- `admin_review_result`: 管理员审核结果 (JSONB)
- `applied_at`, `applied_version`: 应用信息

### system.evolution.admin_review

管理员审批:

| decision | 行为 |
|------|------|
| `approve` | 状态 → `admin_approved`；调用 `_apply_proposal()` 应用变更；讨论室提案清理 `backup_snapshots` |
| `reject` | 状态 → `admin_rejected`；讨论室提案从 `backup_snapshots` 恢复原数据 |
| `request_changes` | 状态 → `draft` |

**权限**: 需要管理员权限（write scope + admin 角色）。

**来源兼容**: 支持 `ai_reviewed` (普通进化提案) 和 `pending_admin` (讨论室提案) 两种来源状态。

### system.evolution.get_history

查询指定实体的进化历史:

- 返回所有关联提案列表（`target_entity_type` + `target_entity_key` 匹配）
- `current_version`: 从对应系统表查询版本号

### system.evolution.retry_ai_review

手动重试 AI 初审。仅 `status=ai_rejected` 时可重试:

- `status` → `ai_reviewing`
- `ai_retry_count += 1`

---

## 三、提案应用 (_apply_proposal)

根据 `target_entity_type` 写入对应表:

| entity_type | 目标表 | 操作 |
|------|------|------|
| `setting_item` | `setting_items` | INSERT (auto_evolved 前缀) |
| `knowledge_item` | `knowledge_entities` | INSERT / ON CONFLICT UPDATE (source='system_evolution') |
| `style_profile` | `system_style_profiles` | INSERT / ON CONFLICT UPDATE |
| `prompt_template` | `system_prompt_templates` | INSERT / ON CONFLICT UPDATE template_content |
| `model_profile` | `model_profiles` | INSERT / ON CONFLICT UPDATE model_name |

---

## 四、AI 评审 Worker (ai_reviewer_worker)

### 概述

独立后台进程，持续轮询 `system_evolution_proposals` 表中 `status='ai_reviewing'` 的提案，调用 AI 进行评审。

### 配置 (环境变量)

| 变量 | 默认值 | 说明 |
|------|------|------|
| `DATABASE_URL` | - | PG 连接串 (必填) |
| `MCP_API_URL` | `http://novel-os-mcp:8787` | MCP 服务地址 |
| `POLL_INTERVAL` | 30 | 轮询间隔秒数 |
| `MAX_CONCURRENT` | 2 | 最大并发评审数 |

### 核心循环

```
while running:
    proposals = get_pending_proposals()  # status='ai_reviewing', retry_count < 3, LIMIT 10
    asyncio.gather(*process_proposal(p) for p in proposals)
    sleep(poll_interval)
```

### 并发控制

使用 `asyncio.Semaphore(MAX_CONCURRENT)` 限制同时进行的评审数。

### 重试机制

评审失败时:
- `ai_retry_count += 1`
- `ai_last_error` 记录错误信息 (截断 500 字)
- 最多重试 3 次

### 评审流程 (process_proposal)

1. 调用 `POST /mcp/tool` → `system.evolution.ai_review` 工具
2. 工具内部：评分 `necessity(0.3)` + `feasibility(0.3)` + `impact(0.2)` + `quality(0.2)`，阈值 0.8
3. 结果写入 `ai_review_result` (JSONB)
4. 状态 → `ai_reviewed` / `ai_rejected`

---

## 五、数据恢复 (_restore_from_backup)

管理员拒绝提案时的数据回滚，从 `backup_snapshots` 恢复:

| 数据源 | 表 | 操作 |
|------|------|------|
| `project_knowledge` | `project_knowledge` | UPDATE description, tags |
| `setting_items` | `setting_items` | UPDATE core_summary, level |
| `universal_knowledge` | `universal_knowledge` | UPDATE content, summary |
| `canon_rules` | `canon_rules` | UPDATE content, title |

---

## 六、通知

### system_notifications 相关

通知类型:

| 类型 | 说明 | 过期时间 |
|------|------|------|
| `evolution_proposal` | 新进化提案 | 90 天 |
| `system_update` | 系统更新 | 90 天 |
| `ai_review_completed` | AI 评审完成 | 90 天 |
| `admin_review_required` | 需要管理员审核 | 90 天 |

---

## 七、版本历史

系统级配置表支持版本历史:

| 表 | 版本策略 |
|------|------|
| `system_style_profiles` | 保留最近 10 个版本 |
| `system_prompt_templates` | 保留最近 10 个版本 |
| `system_model_profiles` | 保留最近 10 个版本 |

---

## 工作流引导

1. 创建提案 → `system.evolution.propose(title, proposal_type="create", target_entity_type="style_profile", proposed_content={...})`
2. AI 自动初审 → `AIReviewerWorker` 后台轮询处理
3. 查看提案 → `system.evolution.list(status="ai_reviewed")`
4. 管理员审批 → `system.evolution.admin_review(proposal_id, decision="approve", reason="...")`
5. 查看历史 → `system.evolution.get_history(target_entity_type, target_entity_key)`
6. 重试 → `system.evolution.retry_ai_review(proposal_id)`