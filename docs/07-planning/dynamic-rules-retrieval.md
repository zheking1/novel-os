# 动态规则检索方案（最终版）

> 向量语义匹配为主 + 结构化后过滤为安全网 + LLM 归纳收敛 —— 一次到位，不做版本迭代。

---

## 一、现状分析

当前 `context.py::_load_rules_section` 全量加载有效规则，12% token 预算：

```python
effective_rules = await self._rules.list_effective_rules(
    project_id=project_id,
    rule_types=["canon", "character", "plot", "style", "forbidden", "reveal_lock", "lesson"],
    chapter_no=chapter_no, volume_no=volume_no,
    scope_refs=scope_refs or chapter_characters,
    scope_types=scope_types, active_event_keys=active_event_keys,
)
rules = self._trim_section("active_rules", effective_rules["rules"], token_budget)
```

问题：规则越多越膨胀，从不按 genre/scene 过滤，无归纳，无降级。

---

## 二、方案设计

### 2.1 总体架构：写入时预嵌 + 检索时四层匹配

```
┌─ 规则创建/更新时 ────────────────────────────────────┐
│  title + content → embed() → Qdrant "rules" 集合      │
│  同时写入 metadata: genres, scene_types, keywords     │
└──────────────────────────────────────────────────────┘

┌─ 章节生成检索时 ─────────────────────────────────────┐
│  章节大纲 → embed()                                  │
│    ↓                                                 │
│  Qdrant.search("rules", top_k=30)        ← 向量主路径  │
│    ↓                                                 │
│  post-filter: 匹配 genre + scene_type    ← 结构化安全网 │
│    ↓                                                 │
│  嵌入不可用 → fallback: tsvector keyword              │
│  结果 < 10 → 补充 SQL 按 genre 拉取                    │
│  结果 > 30 → LLM 按 rule_group 归并为摘要              │
└──────────────────────────────────────────────────────┘
```

### 2.2 规则元数据（`canon_rules.metadata` JSONB）

```json
{
  "genres": ["xianxia", "xuanhuan"],
  "scene_types": ["battle", "cultivation", "trade"],
  "character_tags": ["protagonist"],
  "rule_group": "power_system",
  "keywords": ["内力", "真气", "境界"],
  "summary_short": "内力不能跨境界使用",
  "embedding_id": "rules-abc123",
  "frequency_weight": 0.8
}
```

#### `rule_group` 枚举（对应 `ref_categories` 二级分类 slug）

| rule_group | 含义 |
|---|---|
| `power_system` | 能力与规则体系 |
| `world_building` | 世界设定一致性 |
| `character_setting` | 角色设定、人设约束 |
| `plot_and_story` | 情节逻辑、伏笔 |
| `writing_techniques` | 文风、描写规范 |
| `compliance` | 审查规则 |

### 2.3 检索四层流程

```python
async def _load_rules_section(self, project_id, chapter_no, volume_no,
                               genre, chapter_plan, chapter_characters, ...):

    # 层 0：始终加载 critical + compliance（不作任何过滤）
    critical_rules = await self._rules.list_active(
        project_id, severities=["critical"], scope_types=["global"])

    # 层 1：向量语义检索（主路径）
    semantic_rules = []
    if self._embedding and chapter_plan:
        try:
            plan_text = self._format_chapter_plan(chapter_plan)
            semantic_rules = await self._rules.search_by_embedding(
                project_id=project_id, query_text=plan_text,
                genre=genre, top_k=30,
            )
        except Exception:
            pass

    # 层 2：Fallback — 嵌入不可用时降级到 tsvector keyword
    if not semantic_rules:
        semantic_rules = await self._rules.search_by_keyword(
            project_id=project_id, query_text=plan_text,
            genre=genre, limit=30,
        )

    # 层 3：补充 — 结果不足时按 genre 拉取
    if len(semantic_rules) < 10:
        genre_rules = await self._rules.list_active(
            project_id, metadata_genre=genre, limit=20)
        semantic_rules = self._deduplicate(semantic_rules, genre_rules)

    # 去重 + 合并
    all_rules = self._deduplicate_and_rank(critical_rules + semantic_rules)

    # 层 4：溢出归纳 — 规则 > THRESHOLD 时 LLM 按 rule_group 归并
    if len(all_rules) > 30:
        summary = await self._summarize_rules_by_group(all_rules, genre)
        all_rules = [summary]

    return self._trim_section("active_rules", all_rules, token_budget)
```

### 2.4 场景类型推断

```python
SCENE_KEYWORDS = {
    "battle":       ["战斗", "对决", "交锋", "大战", "围剿", "击杀"],
    "cultivation":  ["修炼", "突破", "闭关", "悟道", "渡劫", "炼丹"],
    "trade":        ["拍卖", "交易", "兑换", "购买", "出售"],
    "social":       ["宴会", "宗门", "朝堂", "比武", "会面"],
    "exploration":  ["探索", "秘境", "遗迹", "寻宝", "古墓"],
    "dialogue":     ["对话", "谈判", "商议", "密谈", "盘问"],
    "transition":   ["赶路", "过渡", "日常", "休整"],
}

def _infer_scene_type(plan_text: str) -> list[str]:
    matches = []
    for scene, kws in SCENE_KEYWORDS.items():
        if any(kw in plan_text for kw in kws):
            matches.append(scene)
    return matches or ["general"]
```

### 2.5 向量写入（规则创建时）

```python
async def _index_rule_to_qdrant(self, rule_id: str, title: str, content: str,
                                 genres: list[str], rule_group: str):
    """规则 upsert 后自动调用"""
    text = f"{title} {content} {' '.join(genres)} {rule_group}"
    vector = await self._embedding.embed_single(project_id=None, text=text)
    await self._qdrant.upsert(
        collection_name="rules",
        points=[{
            "id": rule_id,
            "vector": vector,
            "payload": {
                "project_id": project_id,
                "genres": genres,
                "rule_group": rule_group,
                "title": title,
                "content": content[:500],
            }
        }]
    )
```

### 2.6 降级策略

| 场景 | 降级动作 |
|---|---|
| Qdrant 不可用 | 直接走 tsvector keyword 匹配 |
| embedding 服务不可用 | 同上 |
| 向量结果 < 10 条 | 补充 SQL 按 genre + scene 拉取 |
| 结果 > 30 条 | LLM 按 rule_group 归纳为摘要 |
| 全部不可用 | 加载所有 critical + 按 genre SQL 过滤（当前行为兜底） |

### 2.7 Rule Summary 表

```sql
CREATE TABLE rule_summaries (
    id              UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    project_id      UUID REFERENCES projects(id),
    rule_group      TEXT NOT NULL,
    genre           TEXT,
    summary         TEXT NOT NULL,
    source_rule_ids TEXT[],
    created_at      TIMESTAMPTZ NOT NULL DEFAULT now()
);
```

- 每次归纳后写入，`context.py` 优先查最新 summary
- 按 `(project_id, rule_group, genre)` 取最新一条
- 保留 `source_rule_ids` 可追溯原始规则

### 2.8 Token 预算动态分配

| 条件 | active_rules 预算 | 处理方式 |
|---|---|---|
| 规则 ≤ 30 | 12% | 逐条注入 |
| 规则 31-60 | 8% | 按相似度排序，前 20 条择优注入 |
| 规则 > 60 | 5% | 强制归纳，摘要替代 |

---

## 三、需要的组件（全部已就绪）

| 组件 | 位置 | 用途 |
|---|---|---|
| Qdrant `rules` 集合 | `novel-qdrant` 容器 | 规则向量存储 |
| `embedding_service` | `deps.py` | 规则嵌入 + 查询嵌入 |
| `canon_rules.metadata` | 已有 JSONB 字段 | 结构化标签 |
| model routing `task_type='summary'` | `model.py` | LLM 归纳 |

---

## 四、需要修改的文件

### 后端（3 新增 + 3 改造）

| 文件 | 改动 | 新/改 |
|---|---|---|
| `services/rules.py` | `index_to_qdrant()` — 规则创建/更新时自动调用 | 新增 |
| `services/rules.py` | `search_by_embedding()` — 向量检索 + 后过滤 | 新增 |
| `services/rules.py` | `search_by_keyword()` — tsvector 降级路径 | 新增 |
| `services/context.py` | 改造 `_load_rules_section` — 四层流程 | 改造 |
| `services/context.py` | 新增 `_infer_scene_type`、`_summarize_rules_by_group` | 新增 |
| `tools/canon.py` | `rules.upsert` — 保存后自动调 `index_to_qdrant()` | 改造 |

### 前端（1 改造）

| 文件 | 改动 |
|---|---|
| `rules-list-page.js` | 规则编辑表单增加 genre / scene_type / rule_group 选择器 |

### 数据库（1 新表）

| 改动 |
|---|
| 创建 `rule_summaries` 表 |
| `canon_rules.metadata` 格式规范化（已有字段，无需 DDL） |

---

## 五、与全局规则方案的关联

全局规则同样需要动态检索，复用同一套机制：

```
项目规则 → Qdrant "rules" collection (filtered by project_id)
全局规则 → Qdrant "rules" collection (project_id = NULL)
```

检索时同时查两条路径，合并结果。`global_rules` 表不存 vector——数据从 `canon_rules`（项目规则）和 `global_rules`（全局规则）分别写入 Qdrant 同一集合，靠 `project_id` 区分。

---

## 六、开发计划

> 排期位置见 [roadmap.md](./roadmap.md) 阶段 3（D-08）。
> **必须与 D-06（动态上下文预算）、D-07（全局规则）串行执行** —— 三者都改 `services/context.py`，并行必然冲突。

### 阶段 1：数据层

| 步骤 | 内容 | 预估 |
|---|---|---|
| 1.1 | `rule_summaries` 建表（已由 `deploy/nas/postgres/migrations/223_rule_summaries.sql` 提供，随阶段 0 执行） | 0 min（已完成） |
| 1.2 | 规范 `canon_rules.metadata` 写入格式：`genres` / `scene_types` / `rule_group` / `keywords` / `summary_short` | 5 min |

### 阶段 2：服务层（`services/rules.py` 三新增）

| 步骤 | 内容 | 预估 |
|---|---|---|
| 2.1 | `index_to_qdrant()` — 规则 upsert 后自动嵌入并写入 Qdrant `rules` 集合 | 12 min |
| 2.2 | `search_by_embedding()` — 向量检索 + genre / scene_type 后过滤 | 10 min |
| 2.3 | `search_by_keyword()` — tsvector 降级路径 | 8 min |

### 阶段 3：检索层（`services/context.py`）

| 步骤 | 内容 | 预估 |
|---|---|---|
| 3.1 | `_load_rules_section` 改为四层流程（critical → 向量 → 关键词兜底 → genre 补充） | 20 min |
| 3.2 | `_infer_scene_type()` 场景类型推断 | 5 min |
| 3.3 | `_summarize_rules_by_group()` 溢出归纳 | 5 min |

### 阶段 4：写入链路 + 前端

| 步骤 | 内容 | 预估 |
|---|---|---|
| 4.1 | `tools/canon.py::rules.upsert` 保存后调用 `index_to_qdrant()` | 5 min |
| 4.2 | `rules-list-page.js` 规则编辑表单增加 genre / scene_type / rule_group 选择器 | 10 min |

### 阶段 5：部署与验证

| 步骤 | 内容 | 预估 |
|---|---|---|
| 5.1 | 构建 + 部署 + 三档规则量验证（≤30 / 31-60 / >60） | 10 min |

### 工作量预估

| 阶段 | 内容 | 预估 |
|---|---|---|
| 1 | 数据层 | 5 min |
| 2 | 服务层三新增 | 30 min |
| 3 | 检索层四层流程 | 30 min |
| 4 | 写入链路 + 前端 | 15 min |
| 5 | 部署验证（含一次 MCP 容器重建） | 10 min |
| **合计** | | **~90 min**（不含部署等待时间，与 roadmap D-08 一致） |

### 回滚方案

- 保留原 `_load_rules_section` 实现，用配置开关切换（新算法默认关闭，验证通过后再开启）
- `index_to_qdrant()` 为旁路写入，关闭后 Qdrant `rules` 集合中的残留数据不影响检索正确性，清空即可
- `rule_summaries` 可安全 `TRUNCATE`，清空后自动回退到逐条注入
- 无 DDL 变更（建表已前置到阶段 0），回滚不需要迁移

### 验收标准

| 场景 | 预期 |
|---|---|
| 规则 ≤ 30 条 | 逐条注入，`active_rules` 预算 12%，结果集与改造前一致（允许排序不同） |
| 规则 31-60 条 | 按相似度取前 20 条，预算降至 8% |
| 规则 > 60 条 | 强制归纳，写入一条 `rule_summaries`，`source_rule_ids` 可追溯，预算降至 5% |
| Qdrant 容器停止 | 降级到 tsvector 关键词匹配，`workflow.prepare_chapter_context` 仍返回 ok |
| embedding 服务不可用 | 同上 |
| 任意档位 | `severity=critical` 且 `scope_type=global` 的规则**必须**出现在输出中（层 0 不过滤） |

---

## 七、总结

| 维度 | 方案 |
|---|---|
| 精准匹配 | 向量语义 ≥ tsvector keyword > genre 直接过滤 |
| 高度适配 | genre + scene_type + rule_group 三重结构化后过滤 |
| 溢出保护 | LLM 按 rule_group 分组归纳，动态调整 token 预算 |
| 全面降级 | embedding ↓ tsvector ↓ SQL genre ↓ 全量 critical |
| 一次到位 | 写入时预嵌向量 → 检索时四层匹配 → 结果自动归纳 |
| 新增组件 | 0 个 — Qdrant/embedding/model routing 均已部署 |