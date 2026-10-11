# 上下文压缩系统

## 概述

`ContextCompressionService` 实现渐进式分层压缩系统，专为 2000 万字以上的长篇小说设计。将海量章节内容逐层压缩为：**章节组 → 故事弧 → 卷 → 系列**，使每一层的上下文窗口保持可控。

---

## 压缩层级

```text
Chapter (原始) → Chapter Batch (10章一组) → Arc (故事弧) → Volume (卷) → Series (全书)
```

| 层级 | 存储表 | 目标 Token | 触发条件 |
|---|---|---|---|
| `chapter_batch` | `compressed_contexts` | 500 | 每 10 章 |
| `arc` | `compressed_contexts` | 300 | 每 50 章 |
| `volume` | `compressed_contexts` | 500 | 每 200 章 |
| `series` | `compressed_contexts` | 600 | 每 500 章 |

---

## 核心压缩方法

### compress_chapter_summaries

```python
r = await svc.compress_chapter_summaries(
    project_id, chapter_no_start=1, chapter_no_end=10, target_tokens=500
)
# returns: {"ok": True, "id": "...", "layer": "chapter_batch", "source_count": 10, ...}
```

1. 从 `chapters JOIN chapter_summaries` 读取指定范围的章节摘要
2. `_combine_summaries()` 提取结构化信息（见下文）
3. UPSERT 到 `compressed_contexts`（按 `project_id + compression_layer + chapter_range` 去重）

### compress_arc

```python
r = await svc.compress_arc(
    project_id, arc_key="arc_1_10", chapter_no_start=1, chapter_no_end=10,
    arc_label="觉醒篇"
)
```

- target_tokens 固定为 300
- 读取范围章节摘要后用 `_combine_summaries()` 压缩
- UPSERT 到 `compressed_contexts`，额外填充 `arc_key` 字段
- metadata 包含 `arc_label` 和标题列表

### compress_volume

```python
r = await svc.compress_volume(project_id, volume_no=1)
```

1. 从 `volumes` 表获取卷的起止章节和 `summary`、`goals`
2. 优先从 `compressed_contexts`（`layer='arc'`）读取该卷的弧级摘要
3. 若无弧摘要，回退到直接读取章节摘要
4. `_combine_summaries()` 压缩（target_tokens=500）
5. 拼接卷级别前缀：`[Volume {n}]\n{vol.summary}\n\n{compressed_content}`
6. UPSERT，填充 `volume_no` 字段。metadata 含 `volume_goals`

### compress_series

```python
r = await svc.compress_series(project_id)
```

1. 读取所有 `layer='volume'` 的压缩记录
2. `_combine_summaries()` 合并（target_tokens=600）
3. UPSERT 系列级摘要（无 `chapter_range` 约束）

---

## 上下文组装：get_compressed_context

```python
ctx = await svc.get_compressed_context(
    project_id, chapter_no=105, volume_no=2, budget_tokens=4000
)
# returns: {"ok": True, "sections": [...], "total_tokens": 3500, "within_budget": True}
```

按优先级逐层填充，每加一层检查 token 预算：

1. **Series 摘要**：最新一条，含全系列概览
2. **Volume 摘要**：当前卷的卷级压缩（若有 volume_no）
3. **重叠 Arc 摘要**：`chapter_range_start <= chapter_no <= chapter_range_end` 的所有弧级压缩
4. **最近 8 章摘要**：`chapter_no - 8` 到 `chapter_no - 1` 的原始章节摘要（从 `chapters JOIN chapter_summaries` 读取），按章节号升序排列

返回值：
- `sections`: 每个 section 包含 `name`、`content`、`tokens`
- `total_tokens`: 总计 token 数
- `budget_tokens`: 预算上限
- `within_budget`: 是否在预算内

---

## 自动触发：auto_compress_after_commit

每章节定稿（final commit）后自动调用，按章节号触发不同层级压缩：

```python
results = await svc.auto_compress_after_commit(project_id, chapter_no)
# returns: [{压缩结果}]
```

| 章节号条件 | 触发操作 |
|---|---|
| 每 10 章 | `compress_chapter_summaries`（batch_start = 对齐到 10 的起始） |
| `chapter_no % 50 == 0` | `compress_arc`（arc_key = `arc_{batch_start}_{batch_end}`） |
| `chapter_no % 200 == 0` | 查询当前卷号 → `compress_volume` |
| `chapter_no % 500 == 0` | `compress_series` |

---

## 知识批处理与卷完结检测

### check_knowledge_batch

每 10 章统计过去 7 天内新增的 `project_knowledge` + `universal_knowledge` + `state_entities` 数量，建议调用 `discussion_room.create_session` 后台归纳。

### check_volume_closure

检测当前章节是否为某卷的最后一章（`end_chapter_no == chapter_no`），若是则返回：
- 卷完结标记
- 待评估规则数量（`canon_rules` 中 `promotion_status IS NULL`）
- 建议进行卷级知识归纳和规则升级判定

---

## 冷数据归档：archive_old_data

```python
r = await svc.archive_old_data(
    project_id, current_chapter_no=500,
    keep_recent_volumes=3, keep_recent_chapters=100
)
```

当卷数超过 `keep_recent_volumes` 时：

1. **快照归档**：将 `keep_recent_volumes` 更早的 `state_snapshots.is_current` 标记为 false
2. **摘要压缩**：对归档范围的章节 `_combine_summaries`（target_tokens=200），分批（batch_size=20）写入 `compressed_contexts`
3. **事件迁移**：将归档章节的 `events` 复制到 `events_archive` 后删除原记录

---

## 内部辅助方法

### _combine_summaries(summaries, target_tokens=500)

结构化提取而非简单截断：

1. **章节范围**：`Ch.{first}~{last}`
2. **角色提取**：正则提取中文 2-4 字人名，按频率取前 15，最终展示前 8
3. **关键词**：正则提取 3+ 字中文词，去重后取前 20，最终展示前 10
4. **转折点**：扫描包含 [突破、觉醒、死亡、牺牲、转折、意外、震惊、秘密、真相、背叛、逆袭、危机、决战、分离、重逢、复仇、飞升、渡劫、涅槃] 的句子，取前 3 条（每条截断到 80 字）
5. **情绪弧**：分析最近 5 章的摘要：含 [悲伤/痛苦/绝望/死亡/牺牲] → 低谷；[胜利/突破/成功/喜悦/团聚] → 高潮；[修炼/准备/计划/布局] → 铺垫；其他 → 过渡。去重连续相同阶段

输出格式：
```
[Ch.1 觉醒~Ch.10 突破]
角色: 张三, 李四, 王五
关键词: 功法, 丹药, 宗门, 瓶颈
转折: 张三突破金丹境; 李四遭遇魔修伏击
情绪弧: 铺垫→高潮→低谷
```

### Token 估算

`token_estimate = len(combined_content) // 4`（中文字符 / 4 近似 token 数）

### 长度控制

若 `len(combined) > target_tokens * 4`，截断并追加 `...`。

---

## 其他方法

| 方法 | 说明 |
|---|---|
| `list_compressed_contexts(project_id, layer?)` | 列出压缩记录，支持按层级筛选 |
| `delete_compressed_context(project_id, context_id)` | 删除指定压缩记录 |
| `get_archive_stats(project_id)` | 获取数据分布统计：快照数、摘要数、活跃/归档事件数、章节范围等 |