# Plot 服务 — 情节管理服务

**源码**: `novel-os-mcp/src/novel_os_mcp/services/plot.py` (776 行)

## 概述

Plot 服务负责管理长篇小说的卷（Volume）、情节线（Plot Thread）、伏笔（Foreshadowing）和章节计划（Chapter Plan），是故事结构的核心服务。

## 数据库表

| 表名 | 说明 |
|------|------|
| `volumes` | 卷/分册 |
| `plot_threads` | 情节线 |
| `foreshadowing` | 伏笔 |
| `chapter_plans` | 章节计划 |

---

## 卷管理 (Volumes)

### upsert_volume

创建或更新卷。唯一键：`(project_id, volume_no)`。

**字段**:

| 字段 | 类型 | 说明 |
|------|------|------|
| `volume_no` | int | 卷号，按写作顺序递增 |
| `title` | str | 卷标题 |
| `outline` | str | 卷大纲 |
| `status` | str | `planned` / `in_progress` / `completed` / `deleted` |
| `start_chapter_no` | int\|None | 起始章节号 |
| `end_chapter_no` | int\|None | 结束章节号 |
| `summary` | str\|None | 卷摘要 |
| `goals` | list[dict]\|None | JSONB，卷的目标列表 |
| `metadata` | dict\|None | JSONB 扩展元数据 |

**UPDATE 策略**: `title`/`outline`/`summary`/`start_chapter_no`/`end_chapter_no` 使用 `COALESCE`（新值替换空值）；`metadata` 使用 `||` 合并；`goals` 若为新空数组 `[]` 则保留旧值。

### list_volumes

列出卷，支持按 `statuses`、`current_chapter_no` 过滤。额外返回：
- `chapter_count`：该卷下关联章节的个数（LEFT JOIN chapters）
- `contains_current_chapter`：布尔值，当前章节是否在该卷范围内

### get_volume

按 `volume_id`（UUID）或 `volume_no` 获取单卷详情，含 `chapter_count`。

---

## 情节线管理 (Plot Threads)

### upsert_plot_thread

创建或更新情节线。唯一键：`(project_id, key)`。

**字段**:

| 字段 | 类型 | 默认值 | 说明 |
|------|------|------|------|
| `key` | str | - | 业务键 |
| `title` | str | - | 情节线标题 |
| `thread_type` | str | `"side"` | `main`/`side`/`subplot` 等 |
| `status` | str | `"open"` | `open`/`active`/`closed`/`resolved`/`archived` |
| `importance` | str | `"medium"` | `critical`/`high`/`medium`/`low` |
| `volume_no` | int\|None | None | 所属卷号 |
| `start_chapter_no` | int\|None | None | 起始章节号 |
| `current_chapter_no` | int\|None | None | 当前进度章节号 |
| `last_advanced_chapter_no` | int\|None | None | 上次推进章节号 |
| `expected_next_chapter_no` | int\|None | None | 预期下次推进章节号 |
| `stalled_after_chapters` | int | 20 | 停滞判定阈值：连续多少章未推进视为停滞 |
| `related_entity_ids` | list[str] | [] | 关联实体 ID 列表 |
| `related_foreshadowing_ids` | list[str] | [] | 关联伏笔 ID 列表 |

**校验**：插入时检查 `volume_no` 对应的卷是否存在；章节号引用仅做 warning 日志（允许在创建章节前先预设）。`related_entity_ids`/`related_foreshadowing_ids` 在传入 `NULL` 时保留旧值。

### list_plot_threads

列出情节线，支持按 `statuses`、`thread_types`、`importance`、`volume_no` 过滤。排序按重要性（critical 优先）→ `updated_at DESC`。

额外返回字段 `is_stalled`：当 `current_chapter_no - COALESCE(last_advanced_chapter_no, start_chapter_no, 0) >= stalled_after_chapters` 且状态非 closed/resolved/archived 时为 true。

### advance_plot_thread

推进情节线，将 `current_chapter_no` 和 `last_advanced_chapter_no` 更新为目标章节号。

**操作**：
1. 校验章节存在
2. 更新 `current_chapter_no` = `last_advanced_chapter_no` = 目标章节号
3. 可选更新 `expected_next_chapter_no`、`status`
4. 在 `metadata` 中追加 `last_progress_note`、`last_progress_chapter_no`、`last_progress_at`

### check_stalled_threads

**停滞检测算法**：

```sql
-- 核心逻辑
current_chapter_no - COALESCE(last_advanced_chapter_no, start_chapter_no, 0)
  >= COALESCE(threshold_chapters, stalled_after_chapters)
```

即：当前章节号与上次推进章节号（或起始章节号）的差值 >= 阈值时，判定为停滞。

**参数**：
- `current_chapter_no`：当前创作进度
- `threshold_chapters`：可选，覆盖各情节线自身的 `stalled_after_chapters`
- 排除 `closed`/`resolved`/`archived` 状态

**排序**：`stalled_by_chapters DESC → 重要性 DESC → updated_at`

**返回**：`stalled_by_chapters` 字段表示已停滞多少章。

### delete_thread

软删除（`is_deleted = true`），返回 `{deleted, key, title}`。

---

## 伏笔管理 (Foreshadowing)

### upsert_foreshadowing

创建或更新伏笔。唯一键：`(project_id, key)`。

**核心字段**:

| 字段 | 类型 | 默认值 | 说明 |
|------|------|------|------|
| `key` | str | - | 业务键 |
| `title` | str | - | 伏笔标题 |
| `status` | str | `"planted"` | `planted`/`developing`/`ready_to_payoff`/`paid_off`/`abandoned`/`archived` |
| `importance` | str | `"medium"` | `critical`/`high`/`medium`/`low` |
| `layer` | str | `"visible"` | **可见度层级**: `visible`（表层） / `subtle`（含蓄） / `deep`（深层） |
| `must_payoff` | bool | `false` | 是否必须回收 |
| `payoff_deadline_chapter` | int\|None | None | 回收截止章节号 |
| `payoff_deadline_volume` | int\|None | None | 回收截止卷号 |
| `overdue_policy` | str | `"warn"` | 过期策略: `warn`（警告）/ `escalate`（升级）/ `block`（阻止） |
| `expected_payoff_range` | str\|None | None | 预期回收范围描述 |
| `parent_foreshadowing_id` | UUID\|None | None | 父伏笔（父子关系） |
| `related_foreshadowing_ids` | list[str] | [] | 关联伏笔（兄弟关系） |
| `trigger_on_payoff_ids` | list[str] | [] | 回收时触发的伏笔 ID 列表 |
| `blocks_payoff_until_ids` | list[str] | [] | 阻塞回收的伏笔 ID 列表 |
| `payload` | dict | {} | JSONB 扩展数据 |

### list_foreshadowing

列出伏笔，支持按 `statuses`、`importance`、`layers`、`overdue_at_chapter`（超期判断）、`deadline_before_chapter`（截止窗口）过滤。

动态计算 `is_overdue` 字段：当 `payoff_deadline_chapter < overdue_at_chapter` 且状态非 `paid_off`/`abandoned`/`archived` 时为 true。

排序：超期优先 → 重要性 DESC → updated_at DESC。

### payoff_foreshadowing

**伏笔回收**：
1. 校验伏笔状态非 `paid_off`（禁止重复回收）
2. 通过 `payoff_chapter_no` 查找章节 UUID
3. 更新状态为 `paid_off` 或指定状态
4. 在 `payload` 中记录 `payoff_note`、`payoff_chapter_no`、`payoff_at`
5. 若 `trigger_related=true`，级联触发 `trigger_on_payoff_ids` 中的伏笔（状态 `planted` → `developing`）

返回值包含 `triggered` 字段，列出被触发的伏笔列表。使用数据库事务保证原子性。

### check_overdue_foreshadowing

**超期检测算法**：

```sql
-- 按章节超期
payoff_deadline_chapter IS NOT NULL AND payoff_deadline_chapter < current_chapter_no
-- 按卷超期
payoff_deadline_volume IS NOT NULL AND payoff_deadline_volume < current_volume_no
```

返回 `overdue_by_chapters`（超期章节数）和 `overdue_by_volumes`（超期卷数）。

排序：按 `overdue_policy` 严重程度（`block` > `escalate` > `warn`）→ `must_payoff` DESC → deadline 远近。

### link_foreshadowing

**伏笔关联**：支持建立父子关系和兄弟关系。

- `parent_key` → 设为 `parent_foreshadowing_id`（先查询 parent UUID）
- `related_keys` → 合并到 `related_foreshadowing_ids`
- `trigger_on_payoff_keys` → 合并到 `trigger_on_payoff_ids`
- `blocks_payoff_until_keys` → 合并到 `blocks_payoff_until_ids`
- `replace=False` 时追加合并；`replace=True` 时全量替换

使用 `dict.fromkeys()` 去重。

### bulk_update_foreshadowing_status

批量更新伏笔状态（按 `keys` 或 `ids`），在 `payload` 中记录 `last_status_reason` 和 `last_status_at`。

---

## 章节计划 (Chapter Plans)

### create_chapter_plan

创建章节大纲计划。关联 `users` 表获取 `created_by`。

### list_chapter_plans

列出章节计划，按 `chapter_no DESC → created_at DESC` 排序。

---

## 工作流引导 (workflow_guide)

AI 工具调用路径：
1. `plot.upsert_foreshadowing` — 创建伏笔
2. `plot.list_foreshadowing` + `plot.check_overdue_foreshadowing` — 检查超期伏笔
3. `plot.upsert_thread` / `plot.list_plot_threads` — 管理情节线进度
4. `plot.check_stalled_threads` — 检测停滞情节线
5. `plot.advance_plot_thread` — 推进情节线
6. `plot.payoff_foreshadowing` — 回收伏笔
7. `plot.create_chapter_plan` — 为下一章创建大纲