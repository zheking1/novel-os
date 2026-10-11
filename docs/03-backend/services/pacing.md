# Pacing 服务 — 节奏与情绪曲线建模服务

**源码**: `novel-os-mcp/src/novel_os_mcp/pacing.py` (509 行)

## 概述

Pacing 服务管理长篇（2000 万+ 字）小说的叙事节奏和情绪曲线。包含卷级节奏蓝图、章级情绪跟踪、紧张/释放周期控制、高潮密度控制及读者沉浸度预测。

## 数据库表

| 表名 | 说明 |
|------|------|
| `pacing_blueprints` | 卷级节奏蓝图 |
| `chapter_emotions` | 章级情绪记录 |

---

## 卷级节奏蓝图 (Volume Pacing Blueprint)

### create_volume_blueprint

创建或更新卷级节奏蓝图（`ON CONFLICT (project_id, volume_no)`）。

**blueprint JSONB 结构**：

```json
{
  "target_arc_count": 3,
  "climax_chapters": [45, 80, 120],
  "breather_chapters": [46, 81],
  "tension_curve": {1: 0.3, 20: 0.5, 45: 0.9, 50: 0.4},
  "emotion_targets": {
    "chapter_range": [1, 50],
    "dominant_emotion": "希望",
    "intensity": 0.6
  },
  "pacing_notes": "前段缓慢铺垫，中段快速推进至第一次高潮"
}
```

| 蓝图字段 | 类型 | 说明 |
|------|------|------|
| `target_arc_count` | int | 目标弧光数量 |
| `climax_chapters` | list[int] | 高潮章节号列表 |
| `breather_chapters` | list[int] | 喘息章列表（高潮后的缓冲） |
| `tension_curve` | dict[int→float] | 紧张度曲线（章节号→0-1值） |
| `emotion_targets` | dict | 情绪目标配置 |
| `pacing_notes` | str | 节奏备注 |

### get_volume_blueprint / list_volume_blueprints

获取单卷蓝图或列出所有卷的蓝图。

---

## 节奏类型 (Pacing Types)

| 类型 | 常量值 | 说明 |
|------|------|------|
| 铺垫/上升 | `buildup` | 情节累积 |
| 高潮 | `climax` | 关键冲突点 |
| 喘息/缓冲 | `breather` | 高潮后的平缓章节 |
| 过渡 | `transition` | 场景/时间切换 |
| 高潮铺垫 | `climax_buildup` | 高潮前奏 |
| 收束/解决 | `resolution` | 冲突解决 |
| 常规 | `normal` | 日常推进 |

---

## 章级情绪记录 (Chapter Emotion)

### record_chapter_emotion

记录单章情绪数据（`ON CONFLICT (project_id, chapter_no)` 更新）。

| 参数 | 类型 | 默认值 | 说明 |
|------|------|------|------|
| `tension` | float | - | 紧张度 0.0（平静）~ 1.0（极度紧张） |
| `emotion` | str | - | 主导情绪标签 |
| `emotion_intensity` | float | - | 情绪强度 0.0-1.0 |
| `pacing_type` | str | `"normal"` | 节奏类型 |
| `word_count` | int\|None | None | 字数 |
| `metadata` | dict\|None | None | 扩展元数据 |

### get_emotion_curve

获取章节区间的情绪曲线数据。

**返回**：`[{chapter_no, tension, emotion, emotion_intensity, pacing_type}]`

用于绘制张力曲线图表。

---

## 节奏分析 (Pacing Analysis)

### analyze_pacing_rhythm

分析章节范围内的节奏韵律。

**计算指标**：
- `avg_tension`：平均紧张度
- `max_tension` / `min_tension`：极值
- `tension_range`：极差（波动幅度）
- `climax_count` / `breather_count` / `buildup_count`：各类型次数
- `sharp_transitions`：陡变跃迁（相邻章 tension 差 > 0.3）
- `avg_climax_gap`：高潮平均间隔章节数

### check_pacing_health

节奏健康检查，综合以下维度：

**内置规则**：
- 10+ 章范围内无高潮 → warning: "节奏可能太平"
- 高潮占比 > 30% → warning: "读者疲乏风险"
- 多高潮后无喘息章 → info: "建议增加休息点"
- 平均 tension > 0.8 → warning: "持续高紧张可能耗尽读者耐心"
- 平均 tension < 0.2 持续 20+ 章 → warning: "低紧张可能让读者乏味"

**蓝图对比**：若传入 `volume_no`，检查计划的高潮章节是否实际出现 → error: "遗漏计划高潮"

### compare_to_blueprint

比较实际张力曲线与计划的差异。

**算法**：
1. 获取蓝图中的 `tension_curve` 关键点
2. 使用**线性插值**（`_interpolate_planned`）计算每个章节的计划张力值
3. 计算偏差 `|actual - planned| > 0.2` 的章节
4. 汇总 `avg_deviation` 和 `max_deviation`

---

## 读者沉浸度预测 (Engagement Prediction)

### predict_engagement

基于近期节奏模式预测读者沉浸度。

**评分算法**（满分 100）：

| 因素 | 分值 |
|------|------|
| 基准分 | 50 |
| 张力有变化（variance > 0.02） | +15 |
| 近期有高潮 | +10 |
| 近期有喘息 | +5 |
| 平均 tension 在 0.3-0.7 | +10 |
| 平均 tension > 0.85 | -10 |
| 平均 tension < 0.15 | -5 |
| 趋势健康（-0.2 ≤ trend ≤ 0.3） | +5 |
| 趋势上升（trend > 0.5） | +8 |

**预测等级**：
- ≥ 75：`high_engagement`（高沉浸度）
- 50-74：`moderate_engagement`（中等）
- < 50：`risk_of_disengagement`（流失风险）

使用近 `window`（默认 10）章的数据进行判断。

---

## 上下文摘要 (Context-Friendly Summary)

### get_pacing_summary_for_context

为 LLM 上下文注入生成节奏摘要。

**输出示例**：
```
== Pacing Context (Ch.50) ==
  Recent avg tension: 0.62
  Current: tension=0.75, emotion=紧张, type=climax_buildup
  Recent pacing: buildup → climax_buildup → climax_buildup → climax
  Next planned climax: Ch.80 (30 chapters away)
```

---

## 工作流引导

1. 卷开始前 → `create_volume_blueprint()` 设定节奏蓝图
2. 每章完成后 → `record_chapter_emotion()` 记录情绪
3. 阶段性检查 → `analyze_pacing_rhythm()` + `check_pacing_health()`
4. 偏离检测 → `compare_to_blueprint()` 对比计划
5. 下一章前 → `predict_engagement()` 预判读者反应 + `get_pacing_summary_for_context()` 注入上下文