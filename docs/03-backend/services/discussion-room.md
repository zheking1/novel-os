# Discussion Room — AI多模型讨论室服务

## 概述

Discussion Room 是 Novel OS 中最具创新性的功能模块，通过多个 AI 模型进行结构化辩论来达成知识共识。它包含两个独立的服务类:

- **KnowledgeDiscussionService** (`knowledge_discussion.py`, 159行): 多轮讨论共识引擎
- **KnowledgeCouncilService** (`knowledge_council.py`, 206行): 知识进化提案辩论委员会

**注意**: 这两个服务均不暴露为 MCP 工具，仅通过直接脚本调用（import 使用）。

## 一、KnowledgeDiscussionService — 多轮讨论共识

### 模型池

```python
MODEL_POOL = [
    "baidubce-deepseek-v4-flash",
    "baidubce-deepseek-v3.2",
    "baidubce-glm-5",
    "baidubce-deepseek-v4-pro",
    "baidubce-glm-5.1",
]
```

### 轮换方案 (ROTATION)

每轮使用 3 个模型，尽量每轮换掉 2/3:

| 轮次 | 模型组合 |
|------|---------|
| 0 | deepseek-v4-flash, deepseek-v3.2, glm-5 |
| 1 | deepseek-v4-pro, glm-5.1, deepseek-v4-flash |
| 2 | deepseek-v3.2, glm-5, deepseek-v4-pro |
| 3 | glm-5.1, deepseek-v4-flash, deepseek-v3.2 |

### 核心方法: `discuss()`

```python
async def discuss(
    project_id: str,
    title: str,                # 讨论标题
    round1_prompt: str,        # 第一轮提议 prompt
    review_prompt: str,        # 审阅 prompt (含 {proposals} 占位符)
    summary_prompt: str,       # 总结 prompt (含 {proposals} 占位符)
    max_rounds: int = 5,       # 最大轮数
) -> dict[str, Any]
```

### 返回结构

```python
{
    "title": "讨论标题",
    "summary": "最终共识总结",
    "rounds": 3,                # 实际执行轮数
    "consensus_reached": True,  # 是否达成共识
    "history": [
        {
            "round": 1,
            "type": "propose",  # propose / review
            "models": ["...", "..."],
            "results": [{"model": "...", "text": "..."}, ...]
        },
        {
            "round": 2,
            "type": "review",
            "models": ["...", "..."],
            "objections": [{"model": "...", "text": "..."}, ...]
        },
    ]
}
```

### 完整讨论流程

```
Round 1 (propose):
  ┌─────────────────────────────────────┐
  │ 3 个模型独立提出建议                  │
  │ 每个模型调用有 0.8s 间隔 (速率限制)    │
  │ 失败模型被跳过                         │
  │ 全部失败 → 返回空结果                  │
  └─────────────────────────────────────┘
                    ↓
        _merge_proposals() ─→ 合并所有提案
                    ↓
Round 2~N (review):
  ┌─────────────────────────────────────┐
  │ 3 个审阅模型检查合并文档               │
  │ prompt 中 {proposals} 替换为上一轮合并 │
  │ 每个模型判断是否有异议                 │
  │ 无异议的模型不记录                     │
  │ 全部无异议 → consensus_reached = True │
  └─────────────────────────────────────┘
                    ↓
        有异议 → _merge_proposals(合并+异议)
                    ↓ 循环
Final (summary):
  ┌─────────────────────────────────────┐
  │ 使用 ROTATION[0][0] 生成最终总结      │
  │ prompt 中 {proposals} 替换为最终合并   │
  │ 失败 → 直接使用合并文本作为总结        │
  └─────────────────────────────────────┘
```

### 异议检测 `_has_objections()`

判断模型输出是否包含异议，反模式匹配下列关键词即视为**无异议**:

```
"无异议", "没有异议", "同意", "没有补充", "无补充",
"no objection", "i agree", "no issues",
"没有意见", "全部同意", "认可", "完全同意"
```

若**没有**匹配到任何无异议关键词 → 存在异议。

### 模型调用 `_call_model()`

```python
await self._llm.chat_with_profile(
    project_id, profile_key,
    messages=[
        {"role": "system", "content": "你是小说创作知识库专家。输出要结构化、清晰、有实际价值。"},
        {"role": "user", "content": prompt}
    ],
    temperature=0.3,
    max_tokens=4096
)
```

### 提案合并 `_merge_proposals()`

简单拼接方案:

```
--- 来源 1 ---
模型A输出

--- 来源 2 ---
模型B输出

--- 来源 3 ---
模型C输出
```

## 二、KnowledgeCouncilService — 知识进化提案辩论

### 用途

对 `system_evolution_proposals` 表中 `status='pending_review'` 的知识进化提案进行多模型投票辩论，达成共识后自动应用到对应的系统表。

### 核心方法: `debate_all()`

```python
async def debate_all(project_id: str) -> dict[str, Any]
```

### 返回结构

```python
{
    "total": 5,
    "approved": 3,
    "rejected": 1,
    "errors": 1,
}
```

### 单提案辩论 `_debate_single()`

为每条提案构建评估 prompt:

```
【提案标题】 ...
【提案内容】 JSON
【提案理由】 ...
【评估标准】
  1. 是否具有实际价值？
  2. 是否与已有知识冲突？
  3. 表述是否准确完整？

输出 JSON: {"vote": "approve|reject", "confidence": 0.8, "reason": "..."}
```

### 投票模型选择策略

1. 使用固定的 3 个 review 模型: `deepseek-v4-flash`, `deepseek-v3.2`, `glm-5`
2. 逐个检查 `model_profiles` 表 status='active' 确认可用
3. 所有模型都不可用 → 返回 `{approved: false, error: "no models available"}`
4. 每次调用间隔 1.5s (速率限制)

### 共识规则

| 投票总数 | 批准阈值 |
|---------|---------|
| ≥ 3 | 批准票 ≥ 2 (2/3 多数) |
| = 2 | 批准票 = 2 (全票通过) |
| = 1 | 批准票 ≥ 1 |

### 投票结果为 consensus=true 时 → 应用提案

`_apply_proposal()` 根据 `target_entity_type` 写入对应表:

| target_entity_type | 目标表 | 写入内容 |
|-------------------|--------|---------|
| `setting_item` | `setting_items` | category=slug, item_code=council_xxx, core_summary |
| `knowledge_item` | `knowledge_entities` | entity_type, name, content=建议更新内容, source='council_evolution' |

### 状态机

```
pending_review → (辩论) → approved → (应用) → applied
                        → rejected
```

### JSON 解析 `_parse_json()`

自动处理 ``` 包裹的 JSON 块: 去除 markdown 标记后 `json.loads()`。

## 涉及的数据库表

| 表名 | 访问方式 |
|------|---------|
| `model_profiles` | SELECT (检查可用性) |
| `system_evolution_proposals` | SELECT / UPDATE |
| `setting_items` | INSERT |
| `knowledge_entities` | INSERT ON CONFLICT |
| `setting_categories` | SELECT |
| `workspaces` | SELECT |

## 速率限制

- Discussion: 每轮 model 调用间隔 **0.8s**
- Council: 每个 model 调用间隔 **1.5s**

## System Prompt

```python
# Discussion 各模型
"你是小说创作知识库专家。输出要结构化、清晰、有实际价值。"

# Council 评审模型
"你是知识库进化审核专家，评估提案是否应该采纳。输出 JSON 格式投票结果。"
```