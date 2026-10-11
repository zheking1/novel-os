# 动态上下文预算方案

> 替代硬编码 8000 token，自动检测模型能力，按优先级动态分配上下文。

---

## 一、现状问题

```python
# context.py:977 — 写死的8000
total_budget = int(budget.get("total_tokens") or budget.get("max_tokens") or 8000)
```

- 模型 128K 上下文 → 浪费 120K 空间
- 模型只有 4K → 每个 section 都被过度压缩，信息失真
- 16 个 section 按固定百分比分配，不考虑实际需求

## 二、方案设计

### 2.1 自动检测上下文窗口

```python
async def _detect_context_window(self, project_id: str) -> int:
    """从模型配置中检测上下文窗口大小"""
    rows = await self._db.fetch(
        "SELECT model_name, provider, metadata FROM model_profiles "
        "WHERE project_id = $1 AND status = 'active' AND 'context' = ANY(task_types) "
        "ORDER BY is_default DESC LIMIT 1",
        project_id,
    )
    if not rows:
        rows = await self._db.fetch(
            "SELECT model_name, provider, metadata FROM model_profiles "
            "WHERE project_id IS NULL AND status = 'active' AND 'context' = ANY(task_types) "
            "ORDER BY is_default DESC LIMIT 1",
        )
    
    if rows:
        meta = rows[0].get("metadata") or {}
        # 从 metadata.max_tokens 或已知模型容量表推断
        known = {"gpt-4o": 128000, "gpt-4o-mini": 128000, "deepseek-v3": 64000,
                 "deepseek-r1": 128000, "glm-4": 128000, "claude-3.5": 200000}
        name = (rows[0].get("model_name") or "").lower()
        for k, v in known.items():
            if k in name: return int(meta.get("max_tokens") or v)
        return int(meta.get("max_tokens") or 8000)
    return 8000  # fallback
```

### 2.2 三级优先级分配

```
总预算 detected_window × 0.6（留 40% 给输出）

优先级 P0 (必须):  最小固定 → 有空间自动扩展
  规则         min=400, max=detected × 0.15
  角色状态      min=600, max=detected × 0.2  
  章纲         min=200, max=detected × 0.05

优先级 P1 (重要):  最少比例 → 随空间线性增长
  伏笔         min=300, max=detected × 0.08
  知识库        min=250, max=detected × 0.06
  通用知识      min=250, max=detected × 0.06
  项目知识      min=250, max=detected × 0.06
  设定文档      min=250, max=detected × 0.06

优先级 P2 (增强):  有剩余空间时加载
  实体关系      min=200, max=detected × 0.04
  近期摘要      min=300, max=detected × 0.06
  角色弧光      min=200, max=detected × 0.04
  节奏指引      min=150, max=detected × 0.03
  文风指引      min=150, max=detected × 0.03

优先级 P3 (可选):  充裕时才加载
  记忆检索      min=0,   max=detected × 0.03
  因果链        min=0,   max=detected × 0.03
  压缩上下文    min=0,   max=detected × 0.02
```

### 2.3 分配算法

```python
def _compute_dynamic_budgets(detected: int) -> dict:
    """两级分配：先保底，再按比例分配剩余"""
    remaining = int(detected * 0.6)
    budgets = {}
    
    # Round 1: 给每个 section 分配 min
    for name, min_tok in MIN_BUDGETS.items():
        budgets[name] = min_tok
        remaining -= min_tok
    
    if remaining <= 0:
        return budgets
    
    # Round 2: 按优先级权重分配剩余
    total_weight = sum(PRIORITY_WEIGHT[v] for v in budgets)
    for name, budget in budgets.items():
        extra = int(remaining * (PRIORITY_WEIGHT[name] / total_weight))
        budgets[name] = budget + extra
    
    return budgets
```

### 2.4 效果对比

| 模型 | 检测窗口 | 可用预算 | P0 section | P1 section | P3 section |
|---|---|---|---|---|---|
| gpt-4o-mini | 128K | 76K | 规则 19K + 状态 25K | 伏笔 10K + 知识 8K | 记忆 4K |
| deepseek-v3 | 64K | 38K | 规则 6K + 状态 8K | 伏笔 3K + 知识 2.5K | 记忆 1K |
| 老模型 4K | 4K | 2.4K | 规则 400 + 状态 600 | 伏笔 300 + 知识 250 | 全部跳过 |

---

## 三、开发计划

> 排期位置见 [roadmap.md](./roadmap.md) 阶段 2（D-06）。
> **必须在 D-08（动态规则检索）之前完成** —— 两者都改 `services/context.py`，串行执行避免冲突。

### 阶段 1：模型上下文容量探测

| 步骤 | 内容 | 预估 |
|---|---|---|
| 1.1 | 新增 `_detect_context_window()`：优先读 `model_profiles.metadata.max_tokens` | 5 min |
| 1.2 | 已知模型容量表兜底（gpt-4o / deepseek-v3 / claude-3.5 等） | 3 min |
| 1.3 | 确认 `model_profiles` 表有 `metadata` 字段可写 `max_tokens`（无则用 known table） | 2 min |

### 阶段 2：动态预算算法替换

| 步骤 | 内容 | 预估 |
|---|---|---|
| 2.1 | `_compute_section_budgets` 替换为两级分配（先保 min，再按优先级权重分剩余） | 10 min |
| 2.2 | 新增配置开关，保留旧实现，**默认走旧行为** | 3 min |

### 阶段 3：效果对比验证

| 步骤 | 内容 | 预估 |
|---|---|---|
| 3.1 | 按 §2.4 三档模型实测：128K / 64K / 4K | 5 min |
| 3.2 | 比对改造前后各 section 实际 token 数，确认无 section 被过度压缩 | 5 min |

### 阶段 4：部署验证

| 步骤 | 内容 | 预估 |
|---|---|---|
| 4.1 | 上传 + 重建 MCP 容器 + `context.preview` 回归 | 5 min |

### 改动文件

| 文件 | 改动 | 预估 |
|---|---|---|
| `services/context.py` | `_compute_section_budgets` 替换为动态算法 | 10 min |
| `services/context.py` | 新增 `_detect_context_window` | 5 min |
| `model_profiles` 表 | 确保有 `metadata.max_tokens`（无则加 known table） | 3 min |
| 部署 | 构建 + 验证 | 15 min |
| **合计** | | **~33 min** |

> 三档模型实测与开关验证已摊入阶段 3，故此处合计与分阶段表一致，均为 ~33 min（不含部署等待）。

### 回滚方案

- 配置开关切回旧 `_compute_section_budgets`（硬编码 8000），无需回滚代码
- 新算法**不写入任何数据**，回滚无副作用；`model_profiles.metadata` 变更也是幂等读取
- 开关默认保持旧行为，验证通过后再切换

### 验收标准

| 场景 | 预期 |
|---|---|
| 配置 128K 模型 | P0 section 预算放大到规则 19K / 状态 25K 量级，P3 section 正常加载 |
| 未配置模型（无 `max_tokens`） | 回落 8000，输出与改造前**完全一致** |
| 4K 老模型 | P3 section（记忆检索 / 因果链 / 压缩上下文）全部跳过，不报错 |
| 任意档位 | P0 section（规则 / 角色状态 / 章纲）预算均 ≥ 其 min 值，绝不为 0 |
| `context.preview` | 返回各 section 的实际 token 数，便于核对分配结果 |