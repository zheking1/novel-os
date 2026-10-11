# Novelty 服务 — 新颖性检测服务

**源码**: `novel-os-mcp/src/novel_os_mcp/novelty.py` (395 行)

## 概述

Novelty 服务检测长篇（2000 万+ 字）小说中的重复模式，包括场景/情节重复（向量语义相似度）、描述去重、对话模式检测和情节节拍重复检测。

支持 **双模式**:
- **向量模式** (VectorIndex / Qdrant): 使用 embedding 向量进行语义相似度匹配
- **关键词模式** (fallback): 使用 Jaccard 关键词相似度

## 依赖文件

| 文件 | 说明 |
|------|------|
| `vector.py` | VectorIndex — Qdrant 向量索引接口 |

---

## 场景新颖性 (Scene Similarity)

### check_scene_novelty

检查场景描述是否与近期场景过于相似。

**参数**:

| 参数 | 类型 | 默认值 | 说明 |
|------|------|------|------|
| `scene_description` | str | - | 场景描述文本 |
| `window` | int | 50 | 回溯章节窗口 |
| `threshold` | float | 0.6 | 相似度阈值 |

**双模式路由**:
- 若 `self._vector` 存在 → `_check_scene_vector()` 向量语义搜索
- 否则 → 关键词匹配 fallback

#### 关键词模式

1. 从 `events` 表获取 `[chapter_no-window, chapter_no)` 范围内的事件
2. 使用 `_extract_keywords()` 提取场景关键词
3. **Jaccard 相似度**: `|交集| / |并集|`
4. 相似度 >= threshold 的场景列入 `similar_scenes`

#### 向量模式

1. 调用 `_get_embedding()` 获取场景的向量表示
2. 在 Qdrant `novel_events` 集合中搜索 top-10
3. 过滤 `score >= threshold` 且 `chapter_no < current_chapter_no` 的结果

---

## 描述去重 (Description Deduplication)

### check_description_novelty

检测描述文本是否与已有内容重复。

**数据源**: `memory_chunks` 表中 `source_type='event'` 且 `chunk_key LIKE 'chapter:%'` 的最近 200 条记录。

使用关键词相似度进行匹配（threshold 默认 0.7），返回 `similar_descriptions` 列表含 `preview` 前 100 字预览。

---

## 对话模式检测 (Dialogue Pattern Detection)

### check_dialogue_patterns

检测重复的对话结构和用语。

**数据源**: 近期章节的 `chapter_summaries`（`summary_type='chapter'`）。

**算法**:
1. 提取新对话中的词组模式 (`_extract_dialogue_patterns`)
2. 从已有摘要中用正则提取引号内对话文本
3. 使用 `_phrase_similarity()` (Jaccard) 比较
4. 相似度 > 0.8 判定为重叠

**返回**: `overlaps` 列表，含 `new_phrase`、`existing_phrase`、`similarity`、`existing_chapter`。

---

## 情节节拍重复 (Plot Beat Repetition)

### check_plot_beat_novelty

检测情节推进模式是否重复使用。

**数据源**: `events` 表 + `chapters` 表，获取近期事件。

**算法**:
1. 对每个 plot beat 提取关键词
2. 与 `window` (默认 100) 章内的所有事件做关键词相似度匹配
3. 相似度 >= threshold (默认 0.5) → 标记为重复

---

## 综合报告 (Full Novelty Check)

### full_novelty_check

一次性运行所有新颖性检测，生成综合报告。

**参数**:

| 参数 | 类型 | 说明 |
|------|------|------|
| `content` | str | 正文内容 |
| `scene_description` | str\|None | 场景描述 (可选) |
| `dialogues` | list[dict]\|None | 对话列表 (可选) |
| `plot_beats` | list[str]\|None | 情节节拍列表 (可选) |

**输出**:
```json
{
  "chapter_no": 50,
  "is_novel": false,
  "issue_count": 2,
  "issues": [
    {"type": "scene", "similar_count": 3},
    {"type": "description", "similar_count": 1}
  ],
  "checks": {
    "scene": {...},
    "description": {...},
    "dialogue": {...},
    "plot_beats": {...}
  }
}
```

---

## 内部工具

### 关键词提取 (_extract_keywords)

使用正则 `[\u4e00-\u9fff]+|[a-zA-Z]+` 提取中英文词，过滤停用词。

**停用词列表**: 含 50+ 中英文停用词（`的`, `了`, `是`, `the`, `a`, `is` 等）。

### 相似度计算

| 方法 | 算法 | 用途 |
|------|------|------|
| `_keyword_similarity` | Jaccard: `|交集|/|并集|` | 关键词集合相似度 |
| `_phrase_similarity` | 提取关键词后 Jaccard | 短语相似度 |

### 对话模式提取

- `_extract_dialogue_patterns`: 从对话 dict 列表取 `speaker` + `text[:100]`
- `_extract_dialogue_patterns_from_text`: 从纯文本用正则提取引号内容

---

## 工作流引导

1. 每章完成后 → `full_novelty_check()` 综合检测
2. 单独场景 → `check_scene_novelty()` 检测场景重复
3. 环境描述 → `check_description_novelty()` 检测描述重复
4. 对话编写 → `check_dialogue_patterns()` 检测对话模式重复
5. 情节设计 → `check_plot_beat_novelty()` 检测节拍重复