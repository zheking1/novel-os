# Style Fingerprint 服务 — 风格一致性指纹服务

**源码**: `novel-os-mcp/src/novel_os_mcp/style_fingerprint.py` (373 行)

## 概述

Style Fingerprint 服务追踪长篇小说的写作风格，检测风格偏离。包含叙事视角追踪、句式结构分析、对话风格锚定、情绪基调基线和词汇指纹。

## 数据库表

| 表名 | 说明 |
|------|------|
| `style_profiles` | 风格配置档案 |
| `chapter_style_metrics` | 章级风格指标 (JSONB `style_data`) |

---

## 风格配置档案 (Style Profile)

### create_style_profile

创建或更新风格档案（`ON CONFLICT (project_id, profile_name)`）。

| 参数 | 类型 | 默认值 | 可选值 |
|------|------|------|------|
| `profile_name` | str | `"default"` | 档案名称 |
| `narrative_pov` | str | `"third_limited"` | `first` / `second` / `third_limited` / `third_omniscient` / `multiple` |
| `tense` | str | `"past"` | `past` (过去时) / `present` (现在时) / `mixed` (混合) |
| `tone` | str | `"neutral"` | 基调标签 |
| `target_metrics` | dict | `{}` | JSONB，目标风格指标 |

**叙事视角说明**:
- `first`: 第一人称 (我/我们)
- `second`: 第二人称 (你)
- `third_limited`: 第三人称有限视角
- `third_omniscient`: 第三人称全知视角
- `multiple`: 多视角切换

---

## 章级风格分析 (Chapter Style Analysis)

### analyze_chapter_style

解析单章的写作风格指标。纯本地计算，不依赖外部 API。

**分析指标**:

| 指标 | 计算方式 | 说明 |
|------|------|------|
| `word_count` | len(content) | 字数 |
| `char_count` | len(content) | 字符数 |
| `paragraph_count` | 非空段落数 | 段落数 |
| `sentence_count` | 按 `[.!?。！？]` 分割 | 句子数 |
| `avg_sentence_length` | 字数/句子数 | 平均句长 (字符) |
| `avg_paragraph_length` | 字数/段落数 | 平均段长 |
| `dialogue_ratio` | 引号内容数/段落数 | 对话占比 |
| `punctuation_density` | (感叹+问号+省略号)/字数*1000 | 标点密度 (千字) |
| `cn_ratio` | 中文字符/(中文+英文词) | 中文占比 |
| `vocab_richness` | 唯一词数/总词数 | 词汇丰富度 |
| `pov_detected` | 第一人称 vs 第三人称代词计数 | 检测到的视角 |
| `top_words` | Counter.most_common(20) | 高频词 TOP 20 |

**对话识别**: 正则匹配 `[""「」『』][^""「」『』]+[""「」『』]`。

**视角检测**:
- 第一人称标记: `我/我们` + 英文 `I/me/my/mine/we/us/our`
- 第三人称标记: `他/她/它/他们` + 英文 `he/she/his/her/him/they/them/their`
- 比较计数，阈值取多数

**存储**: 存入 `chapter_style_metrics` 表，`style_data` 为 JSONB。`ON CONFLICT (project_id, chapter_no)` 覆盖更新。

### batch_analyze_chapters

批量分析章节范围。从 `chapters` 表获取正文内容，逐章调用 `analyze_chapter_style`。

---

## 风格漂移检测 (Style Drift Detection)

### detect_style_drift

基于 z-score 检测当前章节是否偏离历史基线。

**检测指标** (metrics_to_check):
- `avg_sentence_length`
- `avg_paragraph_length`
- `dialogue_ratio`
- `punctuation_density`
- `vocab_richness`

**算法**:

```
1. 取 window (默认 20) 章之前的章节作为基线
2. 对每个指标计算:
   - baseline_avg = 基线均值
   - baseline_std = 基线标准差
   - z_score = |current_val - baseline_avg| / baseline_std
3. 若 z_score > 2.0 → 判定为漂移
```

**视角一致性**:
- 统计基线章节中的 majority POV
- 比较当前章的 `pov_detected`
- 不一致时也视为漂移

**返回值**:
- `drift_detected`: 是否存在漂移
- `drift_count`: 漂移指标数
- `drifts`: 每个漂移指标的详情 (metric, current, baseline_avg, baseline_std, z_score, direction)
- `pov_consistent`: 视角是否一致

---

## 风格趋势 (Style Trend)

### get_style_trend

获取指定指标的时序趋势数据。

**参数**: `metric` 可指定单个指标 (如 `avg_sentence_length`)，返回 `[{chapter_no, value}]`。

---

## 上下文摘要

### get_style_summary_for_context

为 LLM 上下文注入生成风格摘要:

**输出示例**:
```
== Style Context ==
  POV: third_limited, Tense: past, Tone: 严肃
  Recent avg: sent=45chars, para=280chars, dialogue=12.5%
  Dominant POV: third
```

---

## 工作流引导

1. 项目初始化 → `create_style_profile()` 设定风格基线
2. 每章完成后 → `analyze_chapter_style()` 分析本章风格
3. 批量检查 → `batch_analyze_chapters()` 覆盖章节范围
4. 漂移检查 → `detect_style_drift()` 对比基线
5. 趋势监控 → `get_style_trend()` 查看特定指标走势
6. 新章生成前 → `get_style_summary_for_context()` 注入风格上下文