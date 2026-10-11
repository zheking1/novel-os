# ContextService - 章节生成上下文准备服务

## 概述

`ContextService` 是 Novel OS 的核心服务，负责在 AI 生成章节之前，从多个数据源组装上下文。它最大支持 **16 个独立 section**，根据章节类型动态分配 token 预算，最终输出一个结构化的 `context_pack` 供 LLM 使用。

**源码路径**: `novel-os-mcp/src/novel_os_mcp/services/context.py` (1401行)

## 注入依赖 (Constructor)

```python
ContextService(
    db: Database,                    # PostgreSQL 连接
    memory: MemoryService,           # 记忆/实体状态服务
    rules: RulesService,             # 规则系统
    plot: PlotService,               # 情节线/伏笔服务
    embedding_service: Any,          # 向量嵌入 (可选)
    rerank_service: Any,             # 重排序 (可选)
    character_arc_service: Any,      # 角色弧线 (可选)
    causality_service: Any,          # 因果链 (可选)
    pacing_service: Any,             # 节奏控制 (可选)
    style_fingerprint_service: Any,  # 风格指纹 (可选)
)
```

## 核心方法: `prepare_chapter_context()`

### 方法签名

```python
async def prepare_chapter_context(
    project_id: str,
    chapter_no: int,
    purpose: str,           # 用途标识，如 "draft" / "revision"
    focus: list[str],       # 关键词列表，如 ["战斗", "突破"]
    budget: dict[str, Any], # 预算配置
    volume_no: int | None = None,
    scope_refs: list[str] | None = None,     # 作用域引用角色名
    scope_types: list[str] | None = None,     # 作用域类型
    active_event_keys: list[str] | None = None,
    pov_mode: str = "omniscient",            # 视角只读
    pass_number: int | None = None,          # 多 pass 编号
    previous_context: dict[str, Any] | None = None,  # 前文上下文增量加载
) -> dict[str, Any]
```

### 返回值结构

```python
{
    "id": "uuid",              # context_packs 表主键
    "chapter_no": 42,
    "purpose": "draft",
    "focus": ["战斗", "突破"],
    "budget": {                # 预算元数据
        "total_tokens": 8000,
        "effective_tokens": 7760,
        "output_overhead": 240,
        "volume_no": 3,
        "pov_mode": "omniscient",
        "pacing_type": "climax"
    },
    "sections": [              # 16 个 section
        {
            "name": "active_rules",
            "content": [...] or "...",
            "tokens_estimated": 960,
            "source_count": 5
        },
        ...
    ],
    "retrieval_audit": [...],   # 各数据源检索统计
    "warnings": [...],          # 过期/超限/冲突警告
    "output_constraint": "...", # 生成约束指令
    "workflow_guide": {...},
}
```

## 完整执行算法 (包含)

### Step 1: 预算计算 `_compute_section_budgets()`

```python
@staticmethod
def _compute_section_budgets(pacing_type: str, total_tokens: int) -> dict[str, int]:
```

根据 `pacing_type` 从 `chapter_emotions` 表查找（默认 `"normal"`），为 16 个 section 分配 token 百分比，然后乘以 `total_tokens` 得到精确 token 数。

#### 默认基准百分比 (DEFAULT)

| Section | 百分比 | 8000 tokens 预算 |
|---------|--------|------------------|
| `active_rules` | 12% | 960 |
| `current_state` | 14% | 1120 |
| `knowledge_base` | 6% | 480 |
| `universal_knowledge` | 8% | 640 |
| `project_knowledge` | 8% | 640 |
| `canon_documents` | 8% | 640 |
| `entity_relationships` | 5% | 400 |
| `open_foreshadowing` | 7% | 560 |
| `recent_summaries` | 8% | 640 |
| `chapter_plan` | 4% | 320 |
| `relevant_memory` | 4% | 320 |
| `compressed_context` | 2% | 160 |
| `character_arcs` | 5% | 400 |
| `causal_chains` | 4% | 320 |
| `style_guidance` | 3% | 240 |
| `pacing_guidance` | 4% | 320 |

#### 节奏类型调整 (ADJUSTMENTS)

| 节奏类型 | 上调 | 下调 |
|---------|------|------|
| **climax** (高潮) | `current_state +4%`, `foreshadowing +3%`, `relationships +2%` | `compressed_context -2%`, `recent_summaries -4%`, `relevant_memory -2%`, `canon -1%` |
| **climax_buildup** (高潮铺垫) | `current_state +2%`, `foreshadowing +3%`, `relationships +2%`, `chapter_plan +2%` | `compressed_context -2%`, `recent_summaries -4%`, `relevant_memory -2%`, `canon -1%` |
| **breather** (喘息) | `relevant_memory +4%`, `knowledge_base +2%`, `canon +3%` | `current_state -6%` |
| **buildup** (铺垫) | `foreshadowing +3%`, `chapter_plan +2%`, `canon +2%` | `compressed_context -2%`, `recent_summaries -2%`, `relevant_memory -2%` |
| **resolution** (收尾) | `compressed_context +4%` | `foreshadowing -4%`, `relationships -2%` |
| **transition** (过渡) | `recent_summaries +3%`, `relevant_memory +3%`, `canon +2%` | `compressed_context -3%`, `current_state -3%`, `relationships -2%` |

调整后做归一化确保总和 = 1.0，然后乘以 `total_tokens` 取整数。

### Step 2: 输出开销扣减

```python
output_overhead = int(total_budget * 0.03)  # 3%
effective_budget = total_budget - output_overhead
```

### Step 3: 多 Pass 系统

`PASS_SECTIONS` 字典定义 4 个 pass，每个 pass 只加载需要的 section 子集：

| Pass | 包含的 Section |
|------|---------------|
| **1 (essential)** | `active_rules`, `chapter_plan`, `open_foreshadowing`, `knowledge_base`, `project_knowledge`, `canon_documents`, `compressed_context` |
| **2 (expanded)** | Pass 1 全部 + `current_state`, `universal_knowledge`, `entity_relationships`, `recent_summaries`, `relevant_memory`, `character_arcs`, `causal_chains` |
| **3 (review)** | `active_rules`, `current_state`, `knowledge_base`, `universal_knowledge`, `project_knowledge`, `canon_documents`, `entity_relationships`, `recent_summaries`, `relevant_memory`, `character_arcs`, `style_guidance` |
| **4 (complete)** | 全部 16 个 section |

不指定 `pass_number` 时加载全部。

### Step 4: 角色提取 `_extract_chapter_characters()`

从 `chapter_plans` 表中提取章节大纲文本，用空格分词后再用每个词去 `state_entities` 表中做 `ILIKE` 匹配，找到 `entity_type IN ('character', 'organization', 'faction')` 且 `lifecycle_status = 'active'` 的角色名（含别名），上限 20 个。

回退方案: 整个 plan 文本做 `position(lower(entity_name) in lower(plan_text))` 匹配。

### Step 5: 16 个 Section Loader

#### 5.1 `_load_rules_section()` - 规则加载
1. 调用 `RulesService.list_effective_rules()` 获取项目级规则 (canon/character/plot/style/forbidden/reveal_lock/lesson)
2. 调用 `RulesService.list_active_global()` 获取全局规则
3. 合并后如果 >30 条且有 `chapter_plan`，则进行场景过滤:
   - `_infer_scene_type()` 匹配战斗/修炼/交易/社交/探索/对话 6 种场景类型
   - `_rule_matches_context()` 检查规则元数据中的 genres 和 scene_types 过滤
4. 非 critical 规则通过 `_rank_rules_by_embedding()` 做余弦相似度排序
5. 如果仍 >30 条，调用 `_summarize_rules_if_needed()` 按 rule_group 聚合为摘要条目
6. 最后 `_trim_section()` 按 token 预算截断

#### 5.2 `_load_state_section()` - 实体状态加载
- 如果有 `previous_context` 且含 `current_state`，执行增量加载:
  - 找出 `previous_context` 中已知的 entity name 集合
  - `_load_delta_state()` 查询新加入或变更的 entities
  - 保留前文中仍有效的 entities
- 否则全量从 `state_entities JOIN state_snapshots` 查询
- 通过 `_rank_state_entities()` 按相关性重排 (直接角色匹配 +10分, 部分匹配 +5分, active +2分, exited -3分, 即将过期 +1分)
- 按 `state_limit` 参数限制数量 (默认 40)

#### 5.3 `_retrieve_knowledge_base()` - 知识库检索
1. 用 `chapter_characters` 前 10 名在 `knowledge_base` 表做 ILIKE 搜索 (title + content)
2. 用 `focus` 前 5 个术语同样搜索
3. 如果有 `genre`，对 `universal_knowledge` 表做 `plainto_tsquery('simple')` 全文搜索 + genre_tags 过滤
4. 如果 `_rerank` 可用且结果 >3 条，用 rerank 模型重新打分 (保留 top 15)
5. 按 `relevance_score` 降序排列

#### 5.4 `_load_canon_section()` - 权威文档加载
1. 用 `chapter_characters` 前 8 名构建 ILIKE 模式，查询 `canon_documents` 表 (status='active', review_status='approved')
2. 用 `focus` 前 5 个术语做 `plainto_tsquery('simple')` 全文搜索补充
3. 每个文档内容截取前 2000 字符

#### 5.5 `_load_relationships_section()` - 实体关系
- 用 `chapter_characters` 前 12 个名字查询 `entity_relationships` 表
- 按 `intensity DESC` + `source_chapter_no DESC` 排序，上限 30 条
- 返回 source/target 各自 name+type+attitude+intensity+known_by 标志

#### 5.6 `_load_arcs_section()` - 角色弧线
- 对每个 `chapter_characters` 前 8 名调用 `_character_arc.get_arc_summary_for_context()` (max 150 tokens)
- 过滤掉 "no arc data"

#### 5.7 `_load_causality_section()` - 因果链
- 调用 `_causality.get_causality_summary_for_context()` (max 300 tokens)
- 过滤掉 "No recent causal chains"

#### 5.8 `_load_style_section()` - 风格指南
- 调用 `_style_fingerprint.get_style_summary_for_context()` (max 150 tokens)

#### 5.9 `_load_pacing_section()` - 节奏指南
- 调用 `_pacing.get_pacing_summary_for_context()` (max 200 tokens)

#### 5.10 `_load_compressed_section()` - 压缩上下文
- 从 `compressed_contexts` 表查 (chapter_end >= current_chapter_no)，取最近的 5 条
- 包含 context_type, chapters 范围, summary, key_entities, emotion_arc

#### 5.11 `_load_uk_section()` - 通用知识
- 实例化 `KBService`，用 focus + chapter_characters 每个术语调用 `uk_search(limit=3)` 然后去重

#### 5.12 `_load_pk_section()` - 项目知识
- 实例化 `KBService`，调用 `world_get_state()` 获取世界状态
- 调用 `pk_list()` 获取 world_rule/character/faction 各最多 5 条

#### 5.13-5.16 其他 Loader
- **chapter_plan**: 直接从 `chapter_plans` 表查询
- **open_foreshadowing**: 调用 `PlotService.list_foreshadowing()` (planted/developing/ready_to_payoff, high/critical 重要度)
- **recent_summaries**: 增量模式下取前文 + 新 summary；否则调用 `MemoryService.recent_summaries()` 
- **relevant_memory**: 用 focus 前 3 个术语调用 `MemoryService.search()`

### Step 6: 组装 Section 对象

每个 section 通过 `_section()` 静态方法封装:

```python
{
    "name": "section_name",
    "content": json_string or string,
    "tokens_estimated": count,  # 中文 x1.5 + ASCII词 x1.3 + 4
    "source_count": item_count,
}
```

### Step 7: 溢出处理

如果 `used_tokens > effective_budget`:
1. 按 `TRIM_PRIORITY` 从低到高排序 section
2. 从低优先级 section 尾部逐项删除内容直到 token 低于预算
3. 记录 `overflow_warnings`

**TRIM_PRIORITY (越小越先裁切):**

| 优先级 | Section |
|--------|---------|
| 1 | `compressed_context` |
| 2 | `relevant_memory` |
| 3 | `recent_summaries` |
| 4 | `open_foreshadowing`, `style_guidance`, `pacing_guidance` |
| 5 | `chapter_plan` |
| 6 | `universal_knowledge`, `project_knowledge`, `causal_chains` |
| 7 | `entity_relationships`, `character_arcs` |
| 8 | `canon_documents`, `current_state` |
| 9 | `knowledge_base` |
| 10 | `active_rules` (最后裁切) |

如果在裁切后仍然超 budget，记录 `hard_overflow` 警告但不过硬阻断。

### Step 8: 警告生成 `_build_warnings()`

1. `overflow_warnings`: 裁切记录
2. `state_expiring`: snapshot 的 `expire_chapter_no` 在 `expiry_window` (默认 3 章) 内将过期
3. `rule_excluded`: 被 superseded/blocked 排除的规则
4. `foreshadowing_overdue`: 过期伏笔 (is_overdue=true)，若 overdue_policy = "block" 则阻塞

### Step 9: 输出约束生成 `_build_output_constraint()`

生成一个结构化的文本约束块:
- `MANDATORY RULES`: canon + forbidden 规则前 15 条
- `CHARACTERS IN THIS CHAPTER`: 角色列表
- `FOCUS TOPICS`: 焦点主题
- `OUTPUT FORMAT`: 生成指令 (直接写正文、不发明、保持模糊)

### Step 10: 写入数据库

```sql
INSERT INTO context_packs (project_id, chapter_no, purpose, focus, budget, sections, retrieval_audit, warnings)
VALUES (...)
RETURNING id, chapter_no, purpose, focus, budget, sections, retrieval_audit, warnings, created_at
```

## Token 估算

**静态方法**: `_estimate_tokens(text)`
```python
def _estimate_tokens(text: str) -> int:
    chinese_chars = sum(1 for ch in text if '\u4e00' <= ch <= '\u9fff')
    ascii_words = len(text.split()) - chinese_chars  # 近似
    return int(chinese_chars * 1.5 + max(0, ascii_words) * 1.3) + 4
```

## 场景类型推断 `_infer_scene_type()`

从 plan 文本中匹配关键词:

| 场景类型 | 关键词 |
|---------|--------|
| battle | 战斗、对决、交锋、大战、围剿、击杀 |
| cultivation | 修炼、突破、闭关、悟道、渡劫、炼丹 |
| trade | 拍卖、交易、兑换、购买、出售 |
| social | 宴会、宗门、朝堂、比武、会面 |
| exploration | 探索、秘境、遗迹、寻宝、古墓 |
| dialogue | 对话、谈判、商议、密谈、盘问 |

未匹配时返回 `["general"]`。

## 辅助方法

### `validate_context_pack()`
验证已生成的 context_pack:
1. 必含 section: active_rules, current_state, recent_summaries, open_foreshadowing, relevant_memory
2. token 不超 budget
3. 至少有一条 canon 规则
4. 至少有一条 critical 规则
5. overdue_policy=block 的伏笔 → error

### `preflight_generation()`
一键方法: `prepare_chapter_context()` + `validate_context_pack()` + 检查过期伏笔 → 返回 `can_generate` 标志。

### `prepare_segment_context()`
为章节分段 (opening/middle/ending) 准备上下文，段默认参数:

| Segment | recent_count | memory_limit | foreshadowing_limit |
|---------|-------------|--------------|---------------------|
| opening | 5 | 10 | 15 |
| middle | 8 | 20 | 20 |
| ending | 10 | 15 | 35 |

### `list_context_packs()` / `get_context_pack()`
查询历史 context_pack 记录。

## 涉及的数据库表

| 表名 | 访问方式 |
|------|---------|
| `context_packs` | INSERT / SELECT |
| `chapters` | SELECT volume_no |
| `chapter_emotions` | SELECT pacing_type |
| `chapter_plans` | SELECT plan |
| `state_entities` | SELECT + JOIN |
| `state_snapshots` | SELECT (is_current=true) |
| `canon_rules` | 通过 RulesService |
| `global_rules` | 通过 RulesService |
| `knowledge_base` | 直接 SELECT |
| `universal_knowledge` | 直接 SELECT + 全文搜索 |
| `canon_documents` | 直接 SELECT + 全文搜索 |
| `entity_relationships` | JOIN state_entities |
| `chapter_summaries` | 通过 MemoryService |
| `memory_chunks` | 通过 MemoryService |
| `compressed_contexts` | 直接 SELECT |
| `project_knowledge` | 通过 KBService |
| `world_snapshots` | 通过 KBService |