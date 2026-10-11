# Canon Tools — 设定文档 & 创作规则

> Source: `novel-os-mcp/src/novel_os_mcp/tools/canon.py`
> Dependencies: `db`, `auth`, `canon_service`, `rules_service`, `compliance_service`

---

## canon.doc.upsert

```python
@mcp.tool(name="canon.doc.upsert")
async def canon_doc_upsert(
    workspace: str, project: str, doc_type: str, key: str,
    title: str, content: str, status: str = "active",
    scope: dict | None = None, review_status: str = "approved",
    source_type: str = "manual", source_id: str | None = None,
    related_rule_ids: list[str] | None = None,
    metadata: dict | None = None, change_reason: str | None = None,
) -> dict[str, Any]
```

**Purpose:** Create or update canon document. Type-categorized storage with version history and change tracking.

**Parameters:**
- `doc_type` — Document type (e.g., premise, worldview, system, character)
- `key` — Business key (UPSERT)
- `title` — Display title (max 200 chars), `content` (max 50000 chars)
- `review_status` — "approved" / "draft" / "pending_review"
- `scope` — Scope config dict for rules integration

**DB Tables:** `canon_documents`, `canon_document_versions` | **Service:** `canon_service.upsert_document()`

---

## canon.doc.list

```python
async def canon_doc_list(
    workspace: str, project: str,
    doc_types: list[str] | None = None, statuses: list[str] | None = None,
    review_status: str | None = None, query: str | None = None,
    limit: int = 100, offset: int = 0,
) -> list[dict[str, Any]]
```

**Purpose:** List canon documents with filtering and full-text search.

---

## canon.doc.get

```python
async def canon_doc_get(
    workspace: str, project: str,
    document_id: str | None = None,
    doc_type: str | None = None, key: str | None = None,
) -> dict[str, Any]
```

**Purpose:** Get single document by `document_id` OR `doc_type` + `key` combination.

---

## canon.doc.archive

```python
async def canon_doc_archive(
    workspace: str, project: str,
    document_id: str | None = None, doc_type: str | None = None,
    key: str | None = None, reason: str | None = None,
) -> dict[str, Any]
```

**Purpose:** Archive document (status → inactive, retains history, recoverable).

---

## canon.doc.history

```python
async def canon_doc_history(
    workspace: str, project: str,
    document_id: str | None = None, doc_type: str | None = None,
    key: str | None = None, limit: int = 50,
) -> list[dict[str, Any]]
```

**Purpose:** List all historical versions of a document.

---

## canon.doc.restore

```python
async def canon_doc_restore(
    workspace: str, project: str, version: int,
    document_id: str | None = None, doc_type: str | None = None,
    key: str | None = None, reason: str | None = None,
) -> dict[str, Any]
```

**Purpose:** Restore document to specific version. Creates new version record with rolled-back content.

---

## rules.list

```python
async def rules_list(
    workspace: str, project: str,
    rule_types: list[str] | None = None, status: str | None = "active",
    chapter_no: int | None = None, volume_no: int | None = None,
) -> list[dict[str, Any]]
```

**Purpose:** List creative rules. Pass `status=null` to return all statuses. Filter by type, chapter, volume.

**DB Tables:** `canon_rules` | **Service:** `rules_service.list_rules()`

---

## rules.list_effective

```python
async def rules_list_effective(
    workspace: str, project: str,
    rule_types: list[str] | None = None,
    chapter_no: int | None = None, volume_no: int | None = None,
    scope_refs: list[str] | None = None, scope_types: list[str] | None = None,
    active_event_keys: list[str] | None = None, include_blocked: bool = False,
) -> dict[str, Any]
```

**Purpose:** Query currently effective rules based on chapter, volume, scope, and active events. Returns computed effective rule set.

---

## rules.check_conflict

```python
async def rules_check_conflict(
    workspace: str, project: str,
    rule_types: list[str] | None = None,
    chapter_no: int | None = None, volume_no: int | None = None,
    scope_refs: list[str] | None = None, scope_types: list[str] | None = None,
    active_event_keys: list[str] | None = None,
    text: str | None = None,
) -> dict[str, Any]
```

**Purpose:** Analyze current rule set for contradictions. Optionally pass text for compliance detection.

---

## rules.propose

```python
async def rules_propose(
    workspace: str, project: str, title: str, content: str,
    proposal_type: str = "create", source_type: str = "user",
    confidence: float | None = None, agreement: dict | None = None,
) -> dict[str, Any]
```

**Purpose:** Submit rule proposal (create/modify/delete). Requires approval to take effect.

**DB Tables:** `rule_proposals` | **Service:** `rules_service.propose_rule()`

---

## rules.upsert

```python
async def rules_upsert(
    workspace: str, project: str,
    rule_key: str, rule_type: str, title: str, content: str,
    scope: str = "global", severity: str = "warning", status: str = "active",
    metadata: dict | None = None, change_reason: str | None = None,
    source: str = "manual", scope_type: str = "global", scope_ref: str | None = None,
    scope_config: dict | None = None, priority: int = 100,
    effective_chapter_no: int | None = None, expire_chapter_no: int | None = None,
    effective_volume_no: int | None = None, expire_volume_no: int | None = None,
    is_temporary: bool = False, active_from_event: str | None = None,
    expire_on_event: str | None = None, conflict_policy: str = "priority",
    supersedes_rule_ids: list[str] | None = None, blocked_by_rule_ids: list[str] | None = None,
) -> dict[str, Any]
```

**Purpose:** Create or update creative rules with full scope, lifecycle, and conflict management.

**Key Parameters:**
- **Scope:** `scope_type` (global/character/location/event/chapter/volume), `scope_ref` (specific entity key)
- **Lifecycle:** `effective_chapter_no`, `expire_chapter_no`, `effective_volume_no`, `expire_volume_no`
- **Events:** `active_from_event`, `expire_on_event`
- **Temporary:** `is_temporary=True`, auto-expires
- **Conflict:** `conflict_policy` (priority/suppress/merge), `supersedes_rule_ids`, `blocked_by_rule_ids`
- **Priority:** Higher = applied first (default 100)

---

## rules.bulk_toggle

```python
async def rules_bulk_toggle(
    workspace: str, project: str, status: str,
    rule_keys: list[str] | None = None, rule_ids: list[str] | None = None,
    rule_types: list[str] | None = None, reason: str | None = None,
) -> list[dict[str, Any]]
```

**Purpose:** Bulk enable/disable rules by key, id, or type.

---

## rules.resolve_conflict

```python
async def rules_resolve_conflict(
    workspace: str, project: str, action: str,
    source_rule_key: str | None = None, source_rule_id: str | None = None,
    target_rule_keys: list[str] | None = None, target_rule_ids: list[str] | None = None,
    priority: int | None = None, reason: str | None = None,
) -> dict[str, Any]
```

**Purpose:** Manually resolve rule conflict. `action`: suppress / merge / override.

---

## rules.list_proposals

```python
async def rules_list_proposals(
    workspace: str, project: str,
    status: str | None = "proposed", limit: int = 100,
) -> list[dict[str, Any]]
```

**Purpose:** List rule proposals. Default: pending proposals.

---

## rules.apply_proposal

```python
async def rules_apply_proposal(
    workspace: str, project: str,
    proposal_id: str, decision: str, reason: str | None = None,
) -> dict[str, Any]
```

**Purpose:** Approve/reject rule proposal. `decision`: approve / reject. Auto-executes on approve.

---

## rules.delete

```python
async def rules_delete(
    workspace: str, project: str,
    rule_key: str | None = None, rule_id: str | None = None,
) -> dict[str, Any]
```

**Purpose:** Physical delete of rule. By `rule_key` or `rule_id`. At least one required.

---

## compliance.rule.upsert

```python
async def compliance_rule_upsert(
    workspace: str, project: str, rule_key: str, title: str, content: str,
    category: str = "custom", patterns: list[str] | None = None,
    match_type: str = "keyword", severity: str = "critical",
    status: str = "active", scope_type: str = "global",
    scope_ref: str | None = None, priority: int = 5,
    case_sensitive: bool = False, hint: str | None = None,
    metadata: dict | None = None,
) -> dict[str, Any]
```

**Purpose:** Create/update compliance check rule. Supports keyword/regex patterns for text compliance detection.

**Parameters:**
- `match_type` — "keyword" / "regex"
- `severity` — "critical" / "warning" / "info"
- `case_sensitive` — Case-sensitive matching
- `hint` — Correction hint for violators

---

## compliance.rule.list

```python
async def compliance_rule_list(
    workspace: str, project: str,
    status: str = "active", categories: list[str] | None = None,
    chapter_no: int | None = None, volume_no: int | None = None,
) -> dict[str, Any]
```

**Purpose:** List compliance rules with filtering.

---

## compliance.rule.delete

```python
async def compliance_rule_delete(workspace: str, project: str, rule_key: str) -> dict
```

**Purpose:** Soft-delete compliance rule. Returns `{ok: True, rule_key, title}`.

---

## compliance.check

```python
async def compliance_check(
    workspace: str, project: str,
    text: str | None = None, content_items: list[dict] | None = None,
    chapter_no: int | None = None, volume_no: int | None = None,
    scope_refs: list[str] | None = None, scope_types: list[str] | None = None,
    review_job_id: str | None = None, create_revision_task: bool = False,
) -> dict[str, Any]
```

**Purpose:** Execute compliance check on text or content items. Can create revision tasks if violations found.

**Scope:** `read` for checking only; `write` if `create_revision_task=True`.

**DB Tables:** `compliance_rules` | **Service:** `compliance_service.check()`
