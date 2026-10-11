# Plot Tools — 卷管理、情节线与伏笔

> Source: `novel-os-mcp/src/novel_os_mcp/tools/plot.py`
> Dependencies: `db`, `auth`, `plot_service`

---

## volume.upsert

```python
@mcp.tool(name="volume.upsert")
async def volume_upsert(
    workspace: str, project: str, volume_no: int,
    title: str | None = None, outline: str | None = None,
    status: str = "planned", start_chapter_no: int | None = None,
    end_chapter_no: int | None = None, summary: str | None = None,
    goals: list[dict] | None = None, metadata: dict | None = None,
) -> dict[str, Any]
```

**Purpose:** Create or update volume. Defines outline, status, and chapter range.

**Parameters:**
- `volume_no: int` — Volume number
- `status` — planned / active / completed
- `start_chapter_no`, `end_chapter_no` — Chapter range
- `goals` — List of `{title, description}` dicts

**DB Tables:** `volumes` | **Service:** `plot_service.upsert_volume()`

---

## volume.get

```python
async def volume_get(
    workspace: str, project: str,
    volume_no: int | None = None, volume_id: str | None = None,
) -> dict[str, Any]
```

**Purpose:** Get single volume. Query by `volume_no` (integer) or `volume_id` (UUID). Returns error dict if not found.

---

## volume.list

```python
async def volume_list(
    workspace: str, project: str,
    statuses: list[str] | None = None, current_chapter_no: int | None = None,
    limit: int = 100,
) -> list[dict[str, Any]]
```

**Purpose:** List all volumes. Filter by status or find volume containing specific chapter.

---

## plot.thread.upsert

```python
async def plot_thread_upsert(
    workspace: str, project: str, key: str, title: str,
    thread_type: str = "side", status: str = "open",
    importance: str = "medium", volume_no: int | None = None,
    start_chapter_no: int | None = None, current_chapter_no: int | None = None,
    last_advanced_chapter_no: int | None = None,
    expected_next_chapter_no: int | None = None,
    stalled_after_chapters: int = 20,
    related_entity_ids: list[str] | None = None,
    related_foreshadowing_ids: list[str] | None = None,
    metadata: dict | None = None,
) -> dict[str, Any]
```

**Purpose:** Create/update plot thread. Tracks main/side thread progress and stall detection.

**Parameters:**
- `thread_type` — main / side
- `stalled_after_chapters` — Chapters without advancement before flagging as stalled (default 20)
- `related_entity_ids` — Linked entity IDs
- `related_foreshadowing_ids` — Linked foreshadowing IDs

**DB Tables:** `plot_threads` | **Service:** `plot_service.upsert_plot_thread()`

---

## plot.thread.list

```python
async def plot_thread_list(
    workspace: str, project: str,
    statuses: list[str] | None = None, thread_types: list[str] | None = None,
    importance: list[str] | None = None, volume_no: int | None = None,
    current_chapter_no: int | None = None, include_closed: bool = False,
    limit: int = 100,
) -> list[dict[str, Any]]
```

**Purpose:** List plot threads with multi-dimensional filtering.

---

## plot.thread.advance

```python
async def plot_thread_advance(
    workspace: str, project: str, key: str, chapter_no: int,
    status: str | None = None, progress_note: str | None = None,
    expected_next_chapter_no: int | None = None, metadata: dict | None = None,
) -> dict[str, Any]
```

**Purpose:** Advance plot thread to specified chapter. Updates progress, status, and expected next chapter.

---

## plot.thread.check_stalled

```python
async def plot_thread_check_stalled(
    workspace: str, project: str, current_chapter_no: int,
    threshold_chapters: int | None = None, statuses: list[str] | None = None,
    limit: int = 100,
) -> list[dict[str, Any]]
```

**Purpose:** Detect stalled threads — returns threads exceeding the threshold chapters without advancement.

---

## plot.thread.delete

```python
async def plot_thread_delete(workspace: str, project: str, key: str) -> dict[str, Any]
```

**Purpose:** Physical delete of plot thread.

---

## plot.create_chapter_plan

```python
async def plot_create_chapter_plan(
    workspace: str, project: str, chapter_no: int, plan: dict,
) -> dict[str, Any]
```

**Purpose:** Create chapter outline plan. Defines chapter goals, scenes, and plot advancement points.

**DB Tables:** `chapter_plans` | **Service:** `plot_service.create_chapter_plan()`

---

## plot.list_chapter_plans

```python
async def plot_list_chapter_plans(
    workspace: str, project: str, status: str | None = None, limit: int = 100,
) -> list[dict[str, Any]]
```

**Purpose:** List chapter plans. Filter by status.

---

## plot.upsert_foreshadowing (RECOMMENDED)

```python
async def plot_upsert_foreshadowing(
    workspace: str, project: str, key: str, title: str,
    status: str = "planted", importance: str = "medium",
    expected_payoff_range: str | None = None, payload: dict | None = None,
    parent_foreshadowing_id: str | None = None,
    related_foreshadowing_ids: list[str] | None = None,
    trigger_on_payoff_ids: list[str] | None = None,
    blocks_payoff_until_ids: list[str] | None = None,
    layer: str = "visible", must_payoff: bool = False,
    payoff_deadline_chapter: int | None = None,
    payoff_deadline_volume: int | None = None,
    overdue_policy: str = "warn",
) -> dict[str, Any]
```

**Purpose:** Create/update foreshadowing. **RECOMMENDED** over deprecated `expectation.*` tools. Manages planting, linking, payoff, and hierarchy.

**Parameters:**
- `layer` — visible / hidden / deep
- `must_payoff` — Must be resolved (creates obligation)
- `payoff_deadline_chapter/volume` — Deadline for resolution
- `overdue_policy` — warn / block / auto_remind
- `trigger_on_payoff_ids` — Foreshadowing to auto-payoff when this is resolved
- `blocks_payoff_until_ids` — Dependencies that must be resolved first

**DB Tables:** `foreshadowing` | **Service:** `plot_service.upsert_foreshadowing()`

---

## plot.list_foreshadowing

```python
async def plot_list_foreshadowing(
    workspace: str, project: str,
    statuses: list[str] | None = None, importance: list[str] | None = None,
    layers: list[str] | None = None, overdue_at_chapter: int | None = None,
    limit: int = 50,
) -> list[dict[str, Any]]
```

**Purpose:** List foreshadowing items. Support overdue detection by passing `overdue_at_chapter`.

---

## foreshadowing.payoff

```python
async def foreshadowing_payoff(
    workspace: str, project: str, key: str,
    payoff_chapter_no: int | None = None, payoff_chapter_id: str | None = None,
    payoff_note: str | None = None, status: str = "paid_off",
    trigger_related: bool = True, metadata: dict | None = None,
) -> dict[str, Any]
```

**Purpose:** Mark foreshadowing as paid off. When `trigger_related=True`, auto-payoffs linked foreshadowing items.

---

## foreshadowing.link

```python
async def foreshadowing_link(
    workspace: str, project: str, key: str,
    parent_key: str | None = None, related_keys: list[str] | None = None,
    trigger_on_payoff_keys: list[str] | None = None,
    blocks_payoff_until_keys: list[str] | None = None,
    replace: bool = False,
) -> dict[str, Any]
```

**Purpose:** Establish relationships between foreshadowing items — parent/child, related, trigger, blocking dependencies.

---

## foreshadowing.bulk_status_update

```python
async def foreshadowing_bulk_status_update(
    workspace: str, project: str, status: str,
    keys: list[str] | None = None, ids: list[str] | None = None,
    reason: str | None = None, metadata: dict | None = None,
) -> list[dict[str, Any]]
```

**Purpose:** Bulk update foreshadowing status by key or id.

---

## foreshadowing.check_overdue

```python
async def foreshadowing_check_overdue(
    workspace: str, project: str, current_chapter_no: int,
    current_volume_no: int | None = None, include_optional: bool = True,
    limit: int = 100,
) -> list[dict[str, Any]]
```

**Purpose:** Check overdue foreshadowing — returns items past their `payoff_deadline_chapter` that haven't been resolved.
