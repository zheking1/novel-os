# Memory & Entity Tools — 故事实体、状态快照与记忆

> Source: `novel-os-mcp/src/novel_os_mcp/tools/memory.py`
> Dependencies: `db`, `auth`, `memory_service`, `embedding_service`, `vector_index`

---

## state.entity.upsert

```python
@mcp.tool(name="state.entity.upsert")
async def state_entity_upsert(
    workspace: str, project: str, entity_type: str, name: str,
    aliases: list[str] | None = None, summary: str | None = None,
    description: str | None = None, portrait_url: str | None = None,
    profile: dict | None = None, lifecycle_status: str = "active",
    importance: str = "medium", tags: list[str] | None = None,
    first_seen_chapter_no: int | None = None,
    last_seen_chapter_no: int | None = None,
    first_seen_volume_no: int | None = None,
    last_seen_volume_no: int | None = None,
    source_type: str = "manual", source_id: str | None = None,
    metadata: dict | None = None,
) -> dict[str, Any]
```

**Purpose:** Create/update story entity (character, location, item, faction, etc.). **USE THIS for character/faction, NOT `kb.pk.upsert`.**

**Parameters:**
- `entity_type` — character / location / faction / item / concept
- `profile: dict` — Structured attributes (e.g., `{age, appearance, personality, background, skills}`)
- `lifecycle_status` — active / deceased / departed / archived
- `importance` — high / medium / low
- `first_seen_chapter_no` / `last_seen_chapter_no` — Chapter tracking
- `first_seen_volume_no` / `last_seen_volume_no` — Volume tracking

**DB Tables:** `state_entities` | **Service:** `memory_service.upsert_entity()`

---

## state.entity.list

```python
async def state_entity_list(
    workspace: str, project: str,
    entity_type: str | None = None, lifecycle_status: str | None = None,
    query: str | None = None, tags: list[str] | None = None,
    include_archived: bool = False, limit: int = 100, offset: int = 0,
) -> list[dict[str, Any]]
```

**Purpose:** List story entities. Filter by type, status, tags, and full-text search.

---

## state.entity.get

```python
async def state_entity_get(
    workspace: str, project: str,
    entity_id: str | None = None,
    entity_type: str | None = None, name: str | None = None,
) -> dict[str, Any] | None
```

**Purpose:** Get single entity detail. By ID OR type+name combination.

---

## state.entity.bulk_patch

```python
async def state_entity_bulk_patch(
    workspace: str, project: str,
    entity_ids: list[str], patch: dict[str, Any],
) -> list[dict[str, Any]]
```

**Purpose:** Bulk patch — apply same field updates to multiple entities simultaneously.

**Scope:** `write`

---

## state.snapshot.upsert

```python
async def state_snapshot_upsert(
    workspace: str, project: str, state: dict[str, Any],
    entity_id: str | None = None, entity_type: str | None = None,
    name: str | None = None, chapter_no: int | None = None,
    chapter_id: str | None = None, source_commit_id: str | None = None,
    is_current: bool = True, effective_chapter_no: int | None = None,
    expire_chapter_no: int | None = None, effective_volume_no: int | None = None,
    expire_volume_no: int | None = None, duration_type: str = "persistent",
    expires_on_event: str | None = None, confidence: float | None = None,
    source_type: str = "manual", source_id: str | None = None,
    change_reason: str | None = None, metadata: dict | None = None,
) -> dict[str, Any]
```

**Purpose:** Create/update entity state snapshot at a specific chapter. Tracks state changes over time.

**Key Parameters:**
- `duration_type` — persistent / temporary / chapter_scoped / volume_scoped
- `is_current` — Whether this is the current active state
- `effective_chapter_no` / `expire_chapter_no` — Validity range
- `confidence` — 0.0-1.0 certainty of state accuracy
- `expires_on_event` — Event key that terminates this state
- `change_reason` — Why the state changed

**DB Tables:** `state_snapshots` | **Service:** `memory_service.upsert_snapshot()`

---

## state.snapshot.list

```python
async def state_snapshot_list(
    workspace: str, project: str,
    entity_id: str | None = None, entity_type: str | None = None,
    name: str | None = None, current_only: bool = False,
    current_chapter_no: int | None = None, include_expired: bool = True,
    limit: int = 100,
) -> list[dict[str, Any]]
```

**Purpose:** List entity snapshots. `current_only=True` returns only current state. `current_chapter_no` filters by effective range.

---

## state.snapshot.at_chapter

```python
async def state_snapshot_at_chapter(
    workspace: str, project: str, entity_name: str, chapter_no: int,
) -> dict[str, Any]
```

**Purpose:** Query entity state at specific chapter — for context backtracing. Returns the most recent state snapshot effective at that chapter.

---

## state.relationship.upsert

```python
async def state_relationship_upsert(
    workspace: str, project: str, relation_type: str,
    source_entity_id: str | None = None,
    source_entity_type: str | None = None, source_name: str | None = None,
    target_entity_id: str | None = None,
    target_entity_type: str | None = None, target_name: str | None = None,
    attitude: str | None = None, intensity: float | None = None,
    known_by_source: bool = True, known_by_target: bool = True,
    known_by_reader: bool = True, status: str = "active",
    source_chapter_no: int | None = None,
    source_chapter_id: str | None = None, source_commit_id: str | None = None,
    metadata: dict | None = None,
) -> dict[str, Any]
```

**Purpose:** Create/update entity relationship. Source and target identified by either `_entity_id` (UUID) or `_entity_type+_name` pair.

**Parameters:**
- `relation_type` — 主从 / 盟友 / 敌对 / 师徒 / 亲缘 / 恋慕 / other
- `attitude` — 忠诚 / 友善 / 中立 / 敌意 / 仇恨
- `intensity` — 0.0-1.0 strength
- `known_by_source/target/reader` — Knowledge flags (default all True)
- `source_chapter_no` — When relationship formed

**DB Tables:** `entity_relationships` | **Service:** `memory_service.upsert_relationship()`

---

## state.relationship.list

```python
async def state_relationship_list(
    workspace: str, project: str,
    entity_id: str | None = None, entity_type: str | None = None,
    name: str | None = None, relation_type: str | None = None,
    status: str | None = "active", include_reader_hidden: bool = True,
    limit: int = 100,
) -> list[dict[str, Any]]
```

**Purpose:** List entity relationships. Filter by entity, relation type, and status.

---

## memory.search

```python
async def memory_search(
    workspace: str, project: str, query: str,
    source_types: list[str] | None = None, limit: int = 20,
) -> list[dict[str, Any]]
```

**Purpose:** Semantic search across memories (entities, snapshots, summaries).

---

## memory.get_state

```python
async def memory_get_state(
    workspace: str, project: str, entity_type: str, name: str,
) -> dict[str, Any] | None
```

**Purpose:** Get entity current state snapshot by type and name.

---

## memory.get_recent_summaries

```python
async def memory_get_recent_summaries(
    workspace: str, project: str, before_chapter_no: int, count: int = 8,
) -> list[dict[str, Any]]
```

**Purpose:** Get recent chapter summaries before a given chapter number.

**DB Tables:** `chapter_summaries`

---

## memory.rebuild_projection

```python
async def memory_rebuild_projection(
    workspace: str, project: str, from_chapter_no: int | None = None,
) -> dict[str, Any]
```

**Purpose:** Rebuild memory projection from specified chapter — recalculates all entity current states.

---

## Vector Memory Tools

| Tool | Purpose |
|------|---------|
| `memory.pending_vector_chunks(workspace, project, limit?)` | Query un-indexed memory chunks |
| `memory.upsert_vector(workspace, project, chunk_id, vector, collection?, payload?)` | Write vector to Qdrant for semantic search |
| `memory.vector_search(workspace, project, vector, collection?, limit?)` | Qdrant vector similarity search |
| `memory.vectorize_pending(workspace, project, batch_size?)` | Vectorize pending memory chunks in batch |
