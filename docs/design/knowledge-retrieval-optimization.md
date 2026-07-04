# Novel OS 知识检索架构优化计划

## 目标

让小说写作 Agent 在每个阶段（创建→生成→审查→进化）都能精准获取所需知识，
上下文不溢出，内容不遗漏。

---

## 现状分析

| # | 机制 | 状态 | 详情 |
|---|------|------|------|
| 1 | 动态预算分配 | ❌ 未实现 | 固定百分比，不按 pacing_type 调整 |
| 2 | 知识预热 | ⚠️ 部分 | genre 策略+关键词模板存在；auto_search 是手动2步，不自动创建项目知识 |
| 3 | 增量上下文 | ❌ 未实现 | 无 delta/diff，每次全量拉取 |
| 4 | 语义搜索 | ✅ 可用 | Embedding API + Qdrant + 余弦相似度 + 降级策略，完全可用 |
| 5 | 多模型审查团 | ⚠️ 部分 | 配置 CRUD 存在，aggregate 存在；但 start_job 不读 council 配置，无并行调度 |
| 6 | 因果链/伏笔/角色弧可视化 | ⚠️ 部分 | 后端数据 API 完整（CTE 递归、时间线、图节点/边）；RelationshipGraphService 未接入 main.py；无前端页面 |

---

## Phase 1：创建小说（项目初始化）

### 流程

```
输入：书名 + 体裁 + 简介
输出：项目知识库 + 世界规则 + 角色表 + 大纲
```

### 知识检索策略

```
1. genre.determine_strategy(书名+简介)
   → 返回 genre_slug（xianxia/scifi/urban...）

2. 根据 genre_slug 加载模板：
   - kb.uk.search(category_slug="kb_ending_types", genre=xianxia)
   - kb.uk.search(category_slug="kb_plot_templates", genre=xianxia)
   - kb.uk.search(category_slug="kb_character")
   - kb.uk.search(category_slug="kb_cheat_types")
   - kb.uk.search(category_slug="kb_naming")

3. genre.auto_search(书名+简介)
   → web_search 补充体裁知识
   → AI 整理写入 universal_knowledge

4. 生成项目基础：
   - world.upsert() → 世界设定
   - canon.batch_create() → 核心规则
   - entity.create() × N → 角色表
   - pacing.create_blueprint() → 节奏蓝图
   - style.create_profile() → 风格指纹
```

### 不做的事

- 不加载 state（还没有数据）
- 不加载 foreshadowing（还没有数据）
- 不加载 compressed（还没有数据）

---

## Phase 2：章节生成（核心循环）

### 动态预算分配（按 pacing_type）

```python
def dynamic_budget(chapter_plan, total=8000):
    base = {
        "rules": 0.15,
        "state": 0.18,
        "kb": 0.08,
        "universal": 0.12,
        "project": 0.12,
        "foreshadowing": 0.10,
        "summaries": 0.12,
        "plan": 0.06,
        "memory": 0.05,
        "compressed": 0.02,
    }

    pacing = chapter_plan.get("pacing_type", "buildup")

    if pacing == "climax":
        # 高潮章：多给状态和伏笔，少给压缩上下文
        base["state"] += 0.05
        base["foreshadowing"] += 0.04
        base["compressed"] = 0.00
        base["summaries"] -= 0.05
        base["memory"] -= 0.04

    elif pacing == "breather":
        # 过渡章：多给角色关系和记忆，少给状态
        base["state"] -= 0.08
        base["memory"] += 0.05
        base["kb"] += 0.03

    elif pacing == "buildup":
        # 铺垫章：多给伏笔和计划
        base["foreshadowing"] += 0.03
        base["plan"] += 0.03
        base["compressed"] = 0.00

    elif pacing == "resolution":
        # 收束章：多给压缩上下文，少给伏笔
        base["compressed"] += 0.05
        base["foreshadowing"] -= 0.05

    return {k: int(total * v) for k, v in base.items()}
```

### 4-Pass 每个 Pass 的知识检索

#### Pass 1 (Plan) — 大纲规划

```
输入：chapter_no + focus + context_pack
检索：
  - canon_rules (scope=chapter_characters, type=canon+character)
  - state_entities (相关角色当前状态)
  - foreshadowing (planned/developing)
  - recent_summaries (最近8章)
  - universal_knowledge (体裁写作技巧)
输出：plan JSON
```

#### Pass 2 (Draft) — 初稿生成

```
输入：plan + context_pack + state + rules
检索：
  - character_arc.get_summary_for_context(chapter_characters, max_tokens=500)
  - causality.get_backward(active_event_keys)  ← 因果链回溯
  - kb.uk.search(category_slug="kb_scene", query=场景关键词)
  - kb.uk.search(category_slug="kb_writing_technique", query=场景类型)
输出：draft text
```

#### Pass 3 (Polish) — 润色

```
输入：draft + style_profile + style_rules
检索：
  - style.get_summary()  ← 风格指纹摘要
  - canon_rules (scope=chapter_characters, type=style+forbidden)
  - kb.uk.search(category_slug="kb_pacing")  ← 节奏技巧
输出：polished text
```

#### Pass 4 (Verify) — 验证

```
输入：polished text
检索：
  - pipeline.check_continuity()  ← 实体提取+状态比对
  - novelty.full_check()  ← 新颖性检查
  - compliance.check()  ← 合规检查
输出：verification report
```

---

## Phase 3：章节审查

### 流程

```
1. review.start_job(chapter_ids, dimensions=["canon","character","plot","style"])
   → 多模型审查团（council）各自提交报告

2. review.aggregate()
   → 共识报告 + revision_tasks

3. review.learn_from_review()
   → extract_rule_proposals()   → 写入 canon_rules
   → extract_state_updates()    → 更新 state_entities
   → extract_foreshadowing_updates() → 更新 foreshadowing
   → evaluate_model_quality()   → 模型质量评分

4. 如果有 blocking findings：
   → workflow.validate_content() 阻止下一章
   → 生成修订建议
```

### 知识流

```
审查发现 → 规则提案 → canon_rules (新规则)
审查发现 → 状态更新 → state_entities (状态修正)
审查发现 → 伏笔更新 → foreshadowing (伏笔调整)
审查发现 → 通用知识 → universal_knowledge (写作经验)
```

---

## Phase 4：进化（学习循环）

### 压缩触发

```
每10章：context.compression.auto_compress()
  → 10章摘要 → 1个压缩摘要 (500 tokens)

每50章：context.compression.compress_arc()
  → 弧线摘要 (300 tokens)

每200章：context.compression.compress_volume()
  → 卷摘要 (500 tokens)
```

### 审查学习循环

```
每章审查后 learn_from_review()
  → 规则提案 → 人工确认 → canon_rules
  → 模型质量评分 → 动态调整模型权重
  → 风格漂移检测 → 自动修正建议
```

---

## 上下文精准获取策略

### 分层检索（Layered Retrieval）

```
Layer 0 (必加载): canon_rules + state_entities + chapter_plan
Layer 1 (按需加载): universal_knowledge + project_knowledge
Layer 2 (可选加载): foreshadowing + memory + compressed
Layer 3 (按需加载): character_arc + causality + style_summary
```

### 检索流程

```
1. prepare_chapter_context()
   → Layer 0 全部加载
   → Layer 1 按 genre + scene_type 选择
   → Layer 2 按 budget 剩余加载
   → Layer 3 按 focus keywords 搜索

2. 每个 Layer 内部：
   → 先 keyword 搜索（快速）
   → 再 semantic 搜索（精准，如果有 embedding）
   → 去重 + 相关性排名
   → trim_to_budget()
```

### 避免溢出的策略

```
1. 硬预算：每个 section 有 max_tokens，超出 trim
2. 优先级裁剪：compressed < memory < summaries < rules
3. 延迟加载：Pass 2 才加载 character_arc，Pass 3 才加载 style
4. 增量上下文：每章只追加 delta，不重传全部
5. 压缩历史：旧卷用 compressed_context 代替原始摘要
```

---

## 实现计划

### P0-1：动态预算分配

**目标：** `prepare_chapter_context` 根据 pacing_type 动态调整各 section 预算

**修改文件：** `services.py`

**实现：**

```python
# 在 prepare_chapter_context 开头，获取 chapter_plan 的 pacing_type
# 替换固定的 section_budgets 为动态计算

DYNAMIC_BUDGET_PRESETS = {
    "climax":    {"state": +0.05, "foreshadowing": +0.04, "compressed": -0.02, "summaries": -0.05, "memory": -0.02},
    "breather":  {"state": -0.08, "memory": +0.05, "kb": +0.03},
    "buildup":   {"foreshadowing": +0.03, "plan": +0.03, "compressed": -0.02, "summaries": -0.02, "memory": -0.02},
    "resolution":{"compressed": +0.05, "foreshadowing": -0.05, "state": +0.00},
    "transition":{"summaries": +0.03, "memory": +0.03, "compressed": -0.03, "state": -0.03},
}

DEFAULT_BUDGET = {
    "rules": 0.15, "state": 0.18, "kb": 0.08, "universal": 0.12,
    "project": 0.12, "foreshadowing": 0.10, "summaries": 0.12,
    "plan": 0.06, "memory": 0.05, "compressed": 0.02,
}

def compute_budget(pacing_type: str, total_tokens: int) -> dict[str, int]:
    budget = dict(DEFAULT_BUDGET)
    preset = DYNAMIC_BUDGET_PRESETS.get(pacing_type, {})
    for k, v in preset.items():
        budget[k] = max(0, budget.get(k, 0) + v)
    # 归一化确保总和=1.0
    total = sum(budget.values())
    if abs(total - 1.0) > 0.01:
        scale = 1.0 / total
        budget = {k: v * scale for k, v in budget.items()}
    return {k: int(total_tokens * v) for k, v in budget.items()}
```

**改动点：**
- 删除 `section_budgets` 固定字典
- 新增 `compute_budget()` 函数
- `prepare_chapter_context` 调用 `compute_budget(pacing_type, total_budget)`
- `pacing_type` 从 chapter_plan 获取，无 plan 时默认 "buildup"

---

### P0-2：Multipass 每 pass 传不同 context

**目标：** `run_full` 的 4 个 pass 使用不同知识子集，而非每次都传完整 context_pack

**修改文件：** `multipass.py`

**实现：**

```python
# run_full 中，每个 pass 调用 prepare_chapter_context 时传不同参数

PASS_CONFIGS = {
    1: {  # Plan pass
        "sections": ["active_rules", "current_state", "open_foreshadowing",
                     "recent_summaries", "universal_knowledge"],
        "include_arc": False,
        "include_causality": False,
        "include_style": False,
    },
    2: {  # Draft pass
        "sections": ["active_rules", "current_state", "knowledge_base",
                     "universal_knowledge", "project_knowledge",
                     "open_foreshadowing", "recent_summaries", "chapter_plan"],
        "include_arc": True,
        "include_causality": True,
        "include_style": False,
    },
    3: {  # Polish pass
        "sections": ["active_rules", "chapter_plan", "recent_summaries"],
        "include_arc": False,
        "include_causality": False,
        "include_style": True,
    },
    4: {  # Verify pass
        "sections": [],  # verify 不需要 context，只检查文本
        "include_arc": False,
        "include_causality": False,
        "include_style": False,
    },
}
```

**改动点：**
- `run_full` 根据 pass_number 选择 `PASS_CONFIGS`
- `prepare_chapter_context` 新增 `sections_filter` 参数，只加载指定 sections
- Pass 3 额外注入 style_summary
- Pass 4 不调用 prepare_chapter_context

---

### P0-3：知识预热

**目标：** 项目创建时自动加载体裁知识包到 universal_knowledge

**修改文件：** `kb_service.py` + `main.py`

**实现：**

```python
# kb_service.py 新增方法
async def genre_preheat(self, project_id: str, genre_slug: str) -> dict:
    """项目创建时预加载体裁知识"""
    results = {"loaded": 0, "skipped": 0}

    # 1. 加载体裁模板知识（结局类型、情节模板、角色原型等）
    template_categories = [
        "kb_ending_types", "kb_plot_templates", "kb_character",
        "kb_cheat_types", "kb_naming", "kb_scene",
        "kb_writing_technique", "kb_pacing",
    ]

    for cat_slug in template_categories:
        items = await self.uk_search(query="", category_slug=cat_slug, limit=50)
        for item in items:
            # 检查 genre_tags 是否匹配
            if item.get("genre_tags") and genre_slug not in item["genre_tags"]:
                results["skipped"] += 1
                continue
            results["loaded"] += 1

    # 2. 创建项目知识条目（world_rule 类别）
    # 将体裁模板转为项目知识
    pk_items = await self.pk_list(project_id, category="world_rule")
    if not pk_items:
        # 首次预热，创建基础世界规则
        genre_templates = await self.uk_search(
            query=genre_slug, category_slug="kb_setting_background", limit=10
        )
        for tpl in genre_templates:
            await self.pk_upsert(
                project_id=project_id,
                category="world_rule",
                topic=tpl["topic"],
                content=tpl["content"],
                source="genre_preheat",
            )

    return results

# main.py 新增 MCP 工具
@mcp.tool(name="kb.genre.preheat")
async def kb_genre_preheat(project_id: str, genre_slug: str) -> dict:
    """预加载体裁知识到项目"""
    return await kb_service.genre_preheat(project_id, genre_slug)
```

**改动点：**
- `kb_service.py` 新增 `genre_preheat()` 方法
- `main.py` 新增 `kb.genre.preheat` MCP 工具
- Agent 在创建项目后自动调用此工具

---

### P1-4：uk_search 支持 genre + scene_type 过滤

**目标：** 搜索通用知识时支持体裁和场景类型过滤

**修改文件：** `kb_service.py`

**实现：**

```python
# uk_search 新增参数
async def uk_search(
    self,
    query: str,
    category_slug: str | None = None,
    genre: str | None = None,       # 新增
    scene_type: str | None = None,  # 新增
    limit: int = 20,
) -> list[dict]:
    # ... 现有逻辑 ...

    # 新增：genre 过滤
    if genre:
        # 通过 tags 或 structured_data 过滤
        conditions.append(f"${idx} = ANY(uk.tags) OR uk.structured_data->>'applicable_genres' LIKE '%' || ${idx} || '%'")

    # 新增：scene_type 过滤（通过 tags）
    if scene_type:
        idx += 1
        params.append(scene_type)
        conditions.append(f"${idx} = ANY(uk.tags)")
```

**改动点：**
- `uk_search` 新增 `genre` 和 `scene_type` 参数
- 对应 SQL 条件追加
- MCP 工具 `kb.uk.search` 同步新增参数

---

### P1-5：_retrieve_knowledge_base 按 genre 分类检索

**目标：** 知识库检索从全文搜索改为按体裁分类搜索

**修改文件：** `services.py`

**实现：**

```python
async def _retrieve_knowledge_base(self, project_id, focus, characters, budget):
    # 现有：ILIKE 全文搜索
    # 改为：先按 genre 分类，再在分类内搜索

    # 1. 获取项目体裁
    project = await self._db.fetchrow(
        "SELECT genre FROM projects WHERE id = $1", project_id
    )
    genre = project.get("genre") if project else None

    # 2. 根据 genre 选择搜索策略
    if genre:
        # 搜索体裁相关的 UK 分类
        results = []
        for term in (focus or []) + (characters or [])[:3]:
            uk_results = await self._kb.uk_search(
                query=term,
                genre=genre,  # 新增参数
                limit=3
            )
            results.extend(uk_results)
    else:
        # 回退到全文搜索
        results = await self._kb.uk_search(query=" ".join(focus or []), limit=10)

    return results
```

---

### P1-6：多模型审查团调度

**目标：** start_job 读取 council 配置，并行派发审查任务

**修改文件：** `services.py`

**实现：**

```python
async def start_review_job(self, project_id, chapter_ids, dimensions):
    # 1. 读取活跃的 council 配置
    council = await self._db.fetchrow(
        "SELECT * FROM review_council_configs WHERE project_id = $1 AND is_active = true",
        project_id
    )

    if council:
        config = json.loads(council["config_json"])
        models = config.get("models", [])
        # 按维度分配模型
        dimension_assignments = {}
        for dim in dimensions:
            assigned = [m for m in models if dim in m.get("dimensions", [])]
            dimension_assignments[dim] = assigned or models[:1]  # fallback

    # 2. 创建 review_job
    job = await self._db.fetchrow(
        """INSERT INTO review_jobs (project_id, chapter_ids, dimensions, status)
           VALUES ($1, $2, $3, 'pending') RETURNING id""",
        project_id, chapter_ids, dimensions
    )

    # 3. 为每个模型×维度创建报告槽
    for dim, model_list in (dimension_assignments.items() if council else []):
        for model in model_list:
            await self._db.execute(
                """INSERT INTO review_model_reports (job_id, model_id, dimension, status)
                   VALUES ($1, $2, $3, 'pending')""",
                job["id"], model["id"], dim
            )

    return {"job_id": str(job["id"]), "assignments": dimension_assignments}
```

---

### P1-7：增量上下文

**目标：** prepare_chapter_context 支持传入上一章的 context_pack，只更新变化部分

**修改文件：** `services.py`

**实现：**

```python
async def prepare_chapter_context(
    self,
    project_id: str,
    chapter_no: int,
    purpose: str,
    focus: list[str],
    budget: dict[str, Any],
    previous_context: dict | None = None,  # 新增
    # ... 其他参数
):
    # 如果有 previous_context，复用不变的部分
    if previous_context:
        # state 只加载增量（新出现的实体或状态变化）
        prev_state_ids = {e.get("entity_id") for e in previous_context.get("current_state", [])}
        # 只加载上一章之后变化的 state
        delta_state = await self._load_delta_state(project_id, chapter_no, prev_state_ids)

        # summaries 追加最新一章
        prev_summaries = previous_context.get("recent_summaries", [])
        latest_summary = await self._memory.get_summary(project_id, chapter_no - 1)
        if latest_summary:
            summaries = [latest_summary] + prev_summaries[:7]  # 保持8章
        else:
            summaries = prev_summaries

        # rules 只加载变化
        prev_rules = {r["id"] for r in previous_context.get("active_rules", [])}
        delta_rules = await self._rules.list_delta_rules(project_id, chapter_no, prev_rules)
    else:
        # 全量加载（首章或无上文时）
        # ... 现有逻辑
```

---

### P2-8：RelationshipGraphService 接入

**目标：** 将 p8_services.py 的图服务暴露为 MCP 工具

**修改文件：** `main.py`

```python
from .p8_services import RelationshipGraphService

graph_service = RelationshipGraphService(db)

@mcp.tool(name="graph.get_relationship")
async def graph_get_relationship(project_id: str, chapter_no: int | None = None) -> dict:
    """获取角色关系图数据（nodes + edges）"""
    return await graph_service.get_graph_data(project_id, chapter_no)

@mcp.tool(name="graph.get_timeline")
async def graph_get_timeline(project_id: str, character_name: str) -> list[dict]:
    """获取角色关系时间线"""
    return await graph_service.get_timeline_data(project_id, character_name)
```

---

### P2-9：前端可视化页面

**目标：** 新增因果链、伏笔、角色弧、关系图可视化页面

**修改文件：** `index.html`

**页面规划：**

| 页面 | 数据源 | 可视化 |
|------|--------|--------|
| 因果链 | `causality.get_in_range` | 时间线 + 箭头链接 |
| 伏笔追踪 | `plot.list_foreshadowing` | 状态表格 + 时间轴 |
| 角色弧线 | `arc.get_character` | 折线图（情绪/力量/关系） |
| 关系图 | `graph.get_relationship` | 力导向图（D3/vis） |

---

### P2-10：压缩策略优化

**目标：** 替换 `_combine_summaries` 的截断逻辑为结构化提取

**修改文件：** `context_compression.py`

```python
async def _combine_summaries(self, summaries, target_tokens):
    # 现有：截断到 target_tokens * 4 字符
    # 改为：结构化提取

    combined = {
        "chapter_range": f"{summaries[0].get('chapter_no')}-{summaries[-1].get('chapter_no')}",
        "key_events": [],
        "characters_active": [],
        "emotional_arc": "",
        "plot_threads": [],
    }

    for s in summaries:
        # 提取关键事件
        events = extract_events(s.get("content", ""))
        combined["key_events"].extend(events)

        # 提取活跃角色
        chars = extract_characters(s.get("content", ""))
        combined["characters_active"].extend(chars)

    # 去重
    combined["characters_active"] = list(set(combined["characters_active"]))[:15]
    combined["key_events"] = combined["key_events"][:20]

    # 情绪弧线
    combined["emotional_arc"] = self._infer_emotional_arc(summaries)

    return json.dumps(combined, ensure_ascii=False)
```

---

## 待讨论的优化项

1. **风格自适应**：根据读者反馈自动调整风格参数
2. **伏笔自动检测**：检测未回收的伏笔
3. **角色弧线完整性**：检测角色弧线是否完整
4. **AI Agent 自主进化**：审查发现自动写入知识库，无需人工确认
