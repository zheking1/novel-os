# Knowledge Audit 服务 — 多模型知识库审计

**源码**: `novel-os-mcp/src/novel_os_mcp/services/knowledge_audit.py` (291 行)

## 概述

Knowledge Audit 服务对知识库进行**多模型并行审计**，扫描所有知识分类，将已有知识发送给多个分析模型，生成缺口和改进的进化提案。

配合 `KnowledgeCouncilService` (`knowledge_council.py`) 进行多模型辩论裁决。

## 依赖服务

| 服务 | 路径 | 说明 |
|------|------|------|
| `KnowledgeCouncilService` | `services/knowledge_council.py` | 多模型辩论委员会 |

---

## 审计模式 (Mode)

| mode | 说明 | additions 限制 | updates 限制 |
|------|------|------|------|
| `None` (默认) | 新增 + 优化 | 最多 5 条 | 最多 3 条 |
| `"add"` | 仅新增 | 最多 8 条 | 0 条 |
| `"optimize"` | 仅优化 | 0 条 | 最多 5 条 |

---

## 核心方法：audit_all

### 执行流程

```
1. _list_categories(project_id) → 扫描四大知识分类
2. 对每个分类 → _audit_category()
   2a. _get_existing_knowledge() → 获取已有知识文本
   2b. 构建 audit_prompt → 要求输出 JSON
   2c. 并行调用多个 LLM 模型 (asyncio.gather)
   2d. 解析 JSON 结果 → 提取 additions + updates
   2e. _merge_to_proposals() → 去重合并
3. 汇总 total_proposals 和 categories 摘要
```

### 知识分类扫描 (_list_categories)

| 来源 | 查询 | 限制 |
|------|------|------|
| `universal_knowledge` | 按 `topic` 分组, COUNT DESC | top 10 |
| `knowledge_entities` | 按 `entity_type` 分组 | 全量 |
| `setting_items` | 按 `setting_categories.slug` 分组 (项目所属 workspace) | 全量 |
| `canon_rules` | 按 `rule_type` 分组 (project-scoped) | 全量 |

总计上限约 15 个分类。

---

## 模型选择

**优先模型列表** (按顺序):
1. `baidubce-deepseek-v4-flash`
2. `baidubce-deepseek-v3.2`
3. `baidubce-glm-5`

仅激活状态 (`status='active'`) 的模型参与审计。至少需要 1 个可用模型。

---

## Audi Prompt 模板

```
你正在审计知识库中的「{分类名}」分类。{模式指令}

【已有知识】
{现有知识的文本列表}

【你的任务】
分析当前知识库，找出缺口和改进点。输出 JSON（只输出 JSON，不要其他文字）：

{
  "additions": [
    {"title": "建议新增标题", "content": "详细内容", "reason": "补充理由"}
  ],
  "updates": [
    {"existing": "现有条目", "suggested_content": "更新后内容", "reason": "更新理由"}
  ]
}
```

> LLM 调用参数: `temperature=0.3`, `max_tokens=4096`

---

## 提案生成 (_merge_to_proposals)

**去重逻辑**: 按 `title` (或 `existing`) 作为去重键。

**多模型共识**: 同一 `title` 被多个模型提出时，`_model_count` 递增。

**提案格式**:
```json
{
  "title": "更新 通用知识-人物设定: xxx",
  "proposal_type": "create|update",
  "target_entity_type": "setting_item",
  "proposed_content": {
    "category": "query_value",
    "title": "key",
    "core_summary": "content/suggested_content"
  },
  "evolution_reason": "知识审计: {分类名} — {reason}",
  "evidence": "{\"model_count\": N, \"models\": [...]}"
}
```

---

## 提案保存 (save_proposals)

将审计提案写入 `system_evolution_proposals` 表:

- `status`: `"pending_review"` — 等待辩论委员会裁决
- `ai_submitter`: `"audit_{target_entity_type}"`
- `source_project_id`: 来源项目 ID

---

## 辩论委员会 (KnowledgeCouncilService)

### debate_all

对所有 `pending_review` 提案发起多模型辩论。

**共识规则**:
- 3 票: >= 2 票 approve → 通过
- 2 票: 2 票 approve → 通过
- 1 票: >= 1 票 approve → 通过

**辩论 Prompt**: 评估标准为实际价值、与已有知识冲突、表述准确性三个维度。

### 通过后执行

- `setting_item`: 写入 `setting_items` 表
- `knowledge_item`: 写入 `knowledge_entities` 表
- council 来源标记 `source='council_evolution'`

---

## 工作流引导

1. 触发审计 → `knowledge_audit.audit_all(mode="add")` 或 `mode=None`
2. 保存提案 → 自动写入 `system_evolution_proposals` (status=pending_review)
3. 辩论裁决 → `council_debate_all` → 多模型投票
4. 通过 → 自动应用到知识库