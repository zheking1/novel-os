# Novel OS MCP Tool Schema

Tool names use dotted module prefixes. The MCP implementation can expose them as
exact names or translate dots to underscores if the selected framework requires
that.

All mutating tools require an API token with a matching scope. Read tools still
check workspace and project membership.

## Common Identifiers

Most tools accept:

```json
{
  "workspace": "friend_01",
  "project": "xianxia_001"
}
```

The server resolves those slugs to IDs and checks permissions.

## Auth And Workspace

### auth.whoami

Returns the current user, workspaces, roles, and token scopes.

Input:

```json
{}
```

### workspace.create

Creates a workspace. Owner or system admin only.

Input:

```json
{
  "slug": "friend_01",
  "name": "Friend 01"
}
```

### project.create

Creates a project inside a workspace.

Input:

```json
{
  "workspace": "friend_01",
  "slug": "xianxia_001",
  "title": "仙途未央",
  "description": "Long-form xianxia project"
}
```

### project.register_local_binding

Registers a local client/workspace binding. This records metadata only.

Input:

```json
{
  "workspace": "friend_01",
  "project": "xianxia_001",
  "client_id": "desktop-codex-main",
  "local_root_hint": "D:/Novels/xianxia_001",
  "manifest": {
    "chapters_dir": "chapters",
    "plans_dir": "plans",
    "reviews_dir": "reviews"
  }
}
```

## Canon Document Tools

Canon documents maintain structured long-term setting material in MCP. They are
for worldbuilding, power systems, character baselines, faction notes, project
constraints, style bibles, and other durable facts. Editable manuscripts,
outlines, and detailed local drafts stay in the local author directory.

### canon.doc.upsert

Creates or updates a Canon document and records a new version.

Input:

```json
{
  "workspace": "friend_01",
  "project": "xianxia_001",
  "doc_type": "world",
  "key": "power_system.main",
  "title": "主力量体系",
  "content": "境界分为炼气、筑基、金丹、元婴...",
  "status": "active",
  "scope": {
    "kind": "global"
  },
  "review_status": "approved",
  "source_type": "manual",
  "source_id": null,
  "related_rule_ids": [],
  "metadata": {
    "language": "zh-CN"
  },
  "change_reason": "initial canon import"
}
```

### canon.doc.list

Lists Canon documents with filters.

Input:

```json
{
  "workspace": "friend_01",
  "project": "xianxia_001",
  "doc_types": ["world", "character"],
  "statuses": ["active"],
  "review_status": "approved",
  "query": "力量体系",
  "limit": 100,
  "offset": 0
}
```

### canon.doc.get

Gets one Canon document by `document_id` or by `doc_type + key`.

Input:

```json
{
  "workspace": "friend_01",
  "project": "xianxia_001",
  "doc_type": "world",
  "key": "power_system.main"
}
```

### canon.doc.archive

Archives one Canon document and records a version.

Input:

```json
{
  "workspace": "friend_01",
  "project": "xianxia_001",
  "doc_type": "world",
  "key": "power_system.old",
  "reason": "superseded by new power system"
}
```

### canon.doc.history

Lists document versions.

Input:

```json
{
  "workspace": "friend_01",
  "project": "xianxia_001",
  "doc_type": "world",
  "key": "power_system.main",
  "limit": 20
}
```

### canon.doc.restore

Restores a historical version as a new current version.

Input:

```json
{
  "workspace": "friend_01",
  "project": "xianxia_001",
  "doc_type": "world",
  "key": "power_system.main",
  "version": 2,
  "reason": "rollback bad edit"
}
```

## Workflow Tools

### workflow.prepare_chapter_context

Builds a bounded context pack for local chapter generation.

Input:

```json
{
  "workspace": "friend_01",
  "project": "xianxia_001",
  "chapter_no": 128,
  "purpose": "draft",
  "focus": ["天火令", "拍卖会", "林家背叛"],
  "volume_no": 3,
  "scope_refs": ["主角名", "main_thread"],
  "pov_mode": "protagonist",
  "budget": {
    "total_tokens": 24000,
    "canon_tokens": 2500,
    "state_tokens": 4500,
    "recent_summary_tokens": 4500,
    "long_memory_tokens": 6500,
    "plot_tokens": 3500,
    "reference_tokens": 2000,
    "review_lesson_tokens": 1000
  }
}
```

Output:

```json
{
  "context_pack_id": "uuid",
  "chapter_no": 128,
  "sections": [
    {"name": "canon", "content": "...", "tokens_estimated": 1200},
    {"name": "state", "content": "...", "tokens_estimated": 2200}
  ],
  "retrieval_audit": [
    {"source_type": "foreshadowing", "source_id": "uuid", "reason": "focus match"}
  ],
  "warnings": []
}
```

### workflow.validate_context_pack

Validates an existing context pack by id or latest pack for a chapter. It checks
required sections, estimated token budget, overdue foreshadowing warnings, and
whether core guardrail rules are present.

Input:

```json
{
  "workspace": "friend_01",
  "project": "xianxia_001",
  "context_pack_id": "uuid"
}
```

### workflow.preflight_generation

Builds a context pack and immediately validates whether generation should
continue. This is the preferred tool before calling a writing model.

Input:

```json
{
  "workspace": "friend_01",
  "project": "xianxia_001",
  "chapter_no": 128,
  "purpose": "draft",
  "focus": ["主角名", "拍卖会"],
  "volume_no": 3,
  "scope_refs": ["主角名"],
  "pov_mode": "protagonist",
  "budget": {
    "total_tokens": 24000,
    "recent_count": 8,
    "foreshadowing_limit": 30
  }
}
```

### workflow.prepare_segment_context

Builds a context pack for one chapter segment. Supported segment names are
`opening`, `middle`, and `ending`; other names are accepted with generic
guidance.

Input:

```json
{
  "workspace": "friend_01",
  "project": "xianxia_001",
  "chapter_no": 128,
  "segment": "ending",
  "purpose": "draft",
  "focus": ["伏笔A", "章末钩子"],
  "volume_no": 3,
  "scope_refs": ["主角名"],
  "budget": {
    "total_tokens": 12000
  }
}
```

### workflow.submit_chapter_commit

Submits structured facts extracted from a local chapter. The local chapter file
remains local.

Input:

```json
{
  "workspace": "friend_01",
  "project": "xianxia_001",
  "chapter_no": 128,
  "title": "残片发热",
  "local_files": [
    {
      "kind": "chapter",
      "path_hint": "chapters/volume_001/ch0128.md",
      "sha256": "hex",
      "word_count": 2680
    }
  ],
  "commit": {
    "summary": "主角进入拍卖会并发现天火令残片。",
    "events": [],
    "character_state_changes": [],
    "world_state_changes": [],
    "new_facts": [],
    "foreshadowing_changes": [],
    "plot_thread_changes": [],
    "rule_warnings": [],
    "next_chapter_hooks": []
  },
  "accept": true
}
```

### workflow.learn_from_review

Creates revision tasks, lesson memories, and rule proposals from review reports.

Input:

```json
{
  "workspace": "friend_01",
  "project": "xianxia_001",
  "chapter_no": 128,
  "review_job_id": "uuid",
  "auto_apply_soft_rules": true
}
```

## Memory Tools

### memory.search

Hybrid search over summaries, events, rules, states, reviews, and references.

Input:

```json
{
  "workspace": "friend_01",
  "project": "xianxia_001",
  "query": "天火令残片第一次发热",
  "filters": {
    "source_types": ["event", "foreshadowing", "rule"],
    "chapter_range": [1, 128]
  },
  "limit": 20
}
```

### memory.get_state

Returns current projected state for an entity.

Input:

```json
{
  "workspace": "friend_01",
  "project": "xianxia_001",
  "entity_type": "character",
  "name": "萧临"
}
```

### memory.get_recent_summaries

Input:

```json
{
  "workspace": "friend_01",
  "project": "xianxia_001",
  "before_chapter_no": 128,
  "count": 8
}
```

## State Tools

### state.entity.upsert

Creates or updates a structured entity such as a character, faction, location, or item.

Input:

```json
{
  "workspace": "friend_01",
  "project": "xianxia_001",
  "entity_type": "character",
  "name": "萧临",
  "aliases": ["萧家少主"],
  "profile": {
    "baseline": "外冷内热，重诺"
  },
  "lifecycle_status": "active",
  "importance": "main",
  "tags": ["主角", "剑修"],
  "first_seen_chapter_no": 1,
  "source_type": "manual"
}
```

### state.entity.list

Lists entities with optional type, lifecycle, keyword, and tag filters.

Input:

```json
{
  "workspace": "friend_01",
  "project": "xianxia_001",
  "entity_type": "character",
  "lifecycle_status": "active",
  "query": "萧",
  "tags": ["剑修"],
  "include_archived": false,
  "limit": 100,
  "offset": 0
}
```

### state.entity.get

Gets one entity by `entity_id` or by `entity_type` + `name`, including current state.

Input:

```json
{
  "workspace": "friend_01",
  "project": "xianxia_001",
  "entity_type": "character",
  "name": "萧临"
}
```

### state.entity.bulk_patch

Bulk patches entity maintenance fields. Supported patch keys: `aliases`, `profile`,
`lifecycle_status`, `importance`, `tags`, seen chapter/volume fields, `source_type`,
`source_id`, and `metadata`.

Input:

```json
{
  "workspace": "friend_01",
  "project": "xianxia_001",
  "entity_ids": ["38c4f2e0-0000-0000-0000-000000000001"],
  "patch": {
    "lifecycle_status": "exited",
    "metadata": {
      "reason": "连续多卷未出场"
    }
  }
}
```

### state.snapshot.upsert

Creates a state snapshot. If `is_current` is true, previous current snapshots for
the same entity are marked non-current. The entity can be referenced by ID or by
`entity_type` + `name`; missing named entities are created.

Input:

```json
{
  "workspace": "friend_01",
  "project": "xianxia_001",
  "entity_type": "character",
  "name": "萧临",
  "chapter_no": 128,
  "state": {
    "realm": "筑基后期",
    "injury": "右臂经脉轻伤"
  },
  "duration_type": "temporary",
  "effective_chapter_no": 128,
  "expire_chapter_no": 131,
  "source_type": "manual",
  "change_reason": "人工修订状态"
}
```

### state.snapshot.list

Lists snapshots for one entity or a filtered entity group.

Input:

```json
{
  "workspace": "friend_01",
  "project": "xianxia_001",
  "entity_type": "character",
  "name": "萧临",
  "current_only": true,
  "current_chapter_no": 130,
  "include_expired": false,
  "limit": 50
}
```

### state.relationship.upsert

Creates or updates a relationship between two entities. Source and target can be
referenced by ID or by type/name. Missing named entities are created.

Input:

```json
{
  "workspace": "friend_01",
  "project": "xianxia_001",
  "source_entity_type": "character",
  "source_name": "萧临",
  "target_entity_type": "faction",
  "target_name": "赤霄宗",
  "relation_type": "member_of",
  "attitude": "loyal",
  "intensity": 0.85,
  "known_by_reader": true,
  "source_chapter_no": 12
}
```

### state.relationship.list

Lists active or historical relationships. `include_reader_hidden=false` hides
relationships not yet known to the reader.

Input:

```json
{
  "workspace": "friend_01",
  "project": "xianxia_001",
  "entity_type": "character",
  "name": "萧临",
  "status": "active",
  "include_reader_hidden": false,
  "limit": 100
}
```

### memory.rebuild_projection

Rebuilds current state from accepted chapter commits. Admin/editor only.

Input:

```json
{
  "workspace": "friend_01",
  "project": "xianxia_001",
  "from_chapter_no": 1
}
```

## Plot Tools

### volume.upsert

Creates or updates a volume. Volumes are structural metadata for context and
progress management; full outlines remain local files unless summarized here.

Input:

```json
{
  "workspace": "friend_01",
  "project": "xianxia_001",
  "volume_no": 2,
  "title": "北境秘境",
  "outline": "主角进入北境，完成筑基后期到金丹前置铺垫。",
  "status": "active",
  "start_chapter_no": 101,
  "end_chapter_no": 180,
  "summary": "北境卷聚焦秘境、宗门冲突和第一条长线伏笔回收。",
  "goals": [
    {
      "type": "power",
      "target": "完成金丹契机"
    }
  ]
}
```

### volume.list

Lists project volumes and optionally marks which volume contains a chapter.

Input:

```json
{
  "workspace": "friend_01",
  "project": "xianxia_001",
  "statuses": ["planned", "active"],
  "current_chapter_no": 128,
  "limit": 100
}
```

### plot.thread.upsert

Creates or updates a plot thread such as main line, side line, romance line,
commercial hook, or antagonist line.

Input:

```json
{
  "workspace": "friend_01",
  "project": "xianxia_001",
  "key": "main_north_secret_realm",
  "title": "北境秘境主线",
  "thread_type": "main",
  "status": "open",
  "importance": "critical",
  "volume_no": 2,
  "start_chapter_no": 101,
  "last_advanced_chapter_no": 120,
  "expected_next_chapter_no": 128,
  "stalled_after_chapters": 10,
  "related_foreshadowing_ids": ["sky_fire_token"]
}
```

### plot.thread.list

Lists plot threads and can flag stalled threads relative to the current chapter.

Input:

```json
{
  "workspace": "friend_01",
  "project": "xianxia_001",
  "thread_types": ["main", "side"],
  "statuses": ["open"],
  "volume_no": 2,
  "current_chapter_no": 136,
  "include_closed": false,
  "limit": 100
}
```

### plot.thread.advance

Marks a plot thread as advanced at a chapter.

Input:

```json
{
  "workspace": "friend_01",
  "project": "xianxia_001",
  "key": "main_north_secret_realm",
  "chapter_no": 136,
  "progress_note": "主角发现秘境核心阵眼，主线推进。",
  "expected_next_chapter_no": 140
}
```

### plot.thread.check_stalled

Finds open threads that have not advanced for too many chapters.

Input:

```json
{
  "workspace": "friend_01",
  "project": "xianxia_001",
  "current_chapter_no": 150,
  "threshold_chapters": 12,
  "statuses": ["open"],
  "limit": 50
}
```

### plot.create_chapter_plan

Input:

```json
{
  "workspace": "friend_01",
  "project": "xianxia_001",
  "chapter_no": 128,
  "plan": {
    "goal": "发现天火令残片",
    "scenes": [],
    "must_include": [],
    "must_not_reveal": []
  }
}
```

### plot.list_foreshadowing

Input:

```json
{
  "workspace": "friend_01",
  "project": "xianxia_001",
  "statuses": ["planted", "developing", "ready_to_payoff"],
  "importance": ["high", "critical"],
  "layers": ["visible", "hidden"],
  "overdue_at_chapter": 128,
  "limit": 50
}
```

### plot.upsert_foreshadowing

Input:

```json
{
  "workspace": "friend_01",
  "project": "xianxia_001",
  "key": "sky_fire_token_heat",
  "title": "天火令残片发热",
  "status": "developing",
  "importance": "high",
  "expected_payoff_range": "160-180",
  "payload": {
    "note": "残片对主角血脉有轻微反应。"
  },
  "layer": "hidden",
  "must_payoff": true,
  "payoff_deadline_chapter": 180,
  "overdue_policy": "warn"
}
```

### foreshadowing.bulk_status_update

Bulk updates foreshadowing status by keys or IDs.

Input:

```json
{
  "workspace": "friend_01",
  "project": "xianxia_001",
  "keys": ["sky_fire_token_heat", "hidden_master_identity"],
  "status": "archived",
  "reason": "支线废弃",
  "metadata": {
    "operator_note": "人工归档"
  }
}
```

### foreshadowing.check_overdue

Lists planted/developing foreshadowing that passed payoff deadlines.

Input:

```json
{
  "workspace": "friend_01",
  "project": "xianxia_001",
  "current_chapter_no": 190,
  "current_volume_no": 3,
  "include_optional": false,
  "limit": 50
}
```

### foreshadowing.link

Links one foreshadowing item to parent, related, trigger, or blocking keys.

Input:

```json
{
  "workspace": "friend_01",
  "project": "xianxia_001",
  "key": "sky_fire_token_heat",
  "parent_key": "sky_fire_token",
  "related_keys": ["ancient_fire_map"],
  "trigger_on_payoff_keys": ["north_realm_gate"],
  "blocks_payoff_until_keys": ["bloodline_awakened"],
  "replace": false
}
```

### foreshadowing.payoff

Marks foreshadowing as paid off and optionally triggers linked foreshadowing.

Input:

```json
{
  "workspace": "friend_01",
  "project": "xianxia_001",
  "key": "sky_fire_token_heat",
  "payoff_chapter_no": 176,
  "payoff_note": "主角确认残片是天火令核心钥匙。",
  "trigger_related": true,
  "metadata": {
    "payoff_type": "main_reveal"
  }
}
```

## Rules Tools

### rules.list

Input:

```json
{
  "workspace": "friend_01",
  "project": "xianxia_001",
  "rule_type": ["canon", "style", "review"],
  "scope": ["global", "character"],
  "status": "active"
}
```

### rules.propose

Input:

```json
{
  "workspace": "friend_01",
  "project": "xianxia_001",
  "proposal_type": "create",
  "rule_type": "style",
  "title": "主角压迫场景少解释",
  "content": "主角在威胁和反击场景中应优先行动，台词短促克制。",
  "confidence": 0.86,
  "source": {
    "type": "review",
    "id": "uuid"
  }
}
```

### rules.apply_proposal

Input:

```json
{
  "workspace": "friend_01",
  "project": "xianxia_001",
  "proposal_id": "uuid",
  "decision": "approve",
  "reason": "符合主角长期风格"
}
```

### rules.check_conflict

Checks active scoped rules for structural conflicts. If `text` is provided, the
tool also reports lightweight keyword hits from `metadata.keywords`; deep prose
judgement remains the job of the review pipeline.

Input:

```json
{
  "workspace": "friend_01",
  "project": "xianxia_001",
  "chapter_no": 128,
  "volume_no": 3,
  "scope_refs": ["主角名", "main_thread"],
  "scope_types": ["global", "character", "plot_thread"],
  "text": "short excerpt or generated summary",
  "rule_types": ["canon", "reveal_lock", "character"]
}
```

Output:

```json
{
  "ok": false,
  "conflict_count": 1,
  "conflicts": [
    {
      "type": "same_scope_same_priority",
      "severity": "warning",
      "message": "Multiple active rules share the same type, scope, lifecycle, and priority."
    }
  ],
  "text_match_count": 1,
  "text_matches": []
}
```

### rules.list_effective

Returns rules active for the requested chapter, volume, scope refs, and optional
event keys. Rules explicitly superseded or blocked by other active rules are
reported in `excluded` unless `include_blocked=true`.

Input:

```json
{
  "workspace": "friend_01",
  "project": "xianxia_001",
  "rule_types": ["canon", "character", "plot", "style"],
  "chapter_no": 128,
  "volume_no": 3,
  "scope_refs": ["主角名", "main_thread"],
  "active_event_keys": ["secret_revealed"],
  "include_blocked": false
}
```

### rules.bulk_toggle

Bulk enables, disables, archives, or marks rules as superseded. At least one of
`rule_keys`, `rule_ids`, or `rule_types` is required.

Input:

```json
{
  "workspace": "friend_01",
  "project": "xianxia_001",
  "status": "disabled",
  "rule_keys": ["old_style_rule"],
  "reason": "已被新版节奏规则替代"
}
```

### rules.resolve_conflict

Applies a structured conflict-resolution action.

Supported actions:

```text
disable
supersede
block
set_priority
```

Input:

```json
{
  "workspace": "friend_01",
  "project": "xianxia_001",
  "action": "supersede",
  "source_rule_key": "new_style_rule",
  "target_rule_keys": ["old_style_rule"],
  "reason": "新版规则覆盖旧版规则"
}
```

## Compliance Tools

Compliance tools manage platform-sensitive or project-specific forbidden zones
as rules. They inspect supplied snippets only; local manuscript files remain in
the author's workspace.

### compliance.rule.upsert

Creates or updates a compliance rule. The rule is stored as
`rule_type=compliance`; `metadata.patterns`, `metadata.match_type`, and
`metadata.category` drive matching.

Input:

```json
{
  "workspace": "friend_01",
  "project": "xianxia_001",
  "rule_key": "platform_forbidden_spell",
  "title": "平台敏感禁区",
  "content": "禁止出现该敏感表达",
  "category": "platform_sensitive",
  "patterns": ["forbidden-spell"],
  "match_type": "keyword",
  "severity": "critical",
  "scope_type": "global",
  "priority": 5,
  "hint": "改写或删除该表达"
}
```

### compliance.rule.list

Lists active compliance rules, optionally filtered by category and chapter or
volume lifecycle.

Input:

```json
{
  "workspace": "friend_01",
  "project": "xianxia_001",
  "status": "active",
  "categories": ["platform_sensitive", "custom"],
  "chapter_no": 128,
  "volume_no": 3
}
```

### compliance.check

Checks supplied snippets against active compliance rules. If any critical or
blocking rule matches, the result blocks generation. When `review_job_id` and
`create_revision_task=true` are supplied, the tool creates blocking revision
tasks, marks the review job as blocked, and writes audit logs.

Input:

```json
{
  "workspace": "friend_01",
  "project": "xianxia_001",
  "chapter_no": 128,
  "volume_no": 3,
  "content_items": [
    {
      "ref": "chapters/volume_003/ch0128.md",
      "text": "short generated excerpt or chapter summary"
    }
  ],
  "review_job_id": "uuid",
  "create_revision_task": true
}
```

Output:

```json
{
  "ok": false,
  "blocked": true,
  "critical_count": 1,
  "finding_count": 1,
  "findings": [
    {
      "type": "compliance_match",
      "rule_key": "platform_forbidden_spell",
      "severity": "critical",
      "category": "platform_sensitive",
      "item_ref": "chapters/volume_003/ch0128.md",
      "start": 18,
      "end": 33,
      "excerpt": "..."
    }
  ],
  "created_revision_tasks": 1
}
```

## Sync Tools

### sync.import_local_manifest

Registers or refreshes a local client binding. The manifest should describe
local editable files by path hint and hash; MCP stores references, not the full
manuscript text.

Input:

```json
{
  "workspace": "friend_01",
  "project": "xianxia_001",
  "client_id": "author-laptop",
  "local_root_hint": "D:/novels/xianxia_001",
  "manifest": {
    "version": 1,
    "files": [
      {
        "kind": "chapter",
        "chapter_no": 128,
        "volume_no": 3,
        "title": "雷池开门",
        "path_hint": "chapters/volume_003/ch0128.md",
        "sha256": "hex",
        "word_count": 3200
      }
    ]
  }
}
```

### sync.import_initial_project_pack

Imports structured initialization data produced by a local AI skill or author
tool. Use this for Canon, rules, entities, state snapshots, plot threads,
volumes, and foreshadowing. Long editable prose should remain local.

Input:

```json
{
  "workspace": "friend_01",
  "project": "xianxia_001",
  "pack": {
    "version": 1,
    "local_manifest": {
      "client_id": "author-laptop",
      "local_root_hint": "D:/novels/xianxia_001",
      "files": []
    },
    "canon_documents": [
      {
        "doc_type": "world",
        "key": "core_power_system",
        "title": "核心力量体系",
        "content": "境界必须逐级突破。"
      }
    ],
    "rules": [
      {
        "rule_key": "canon_rank_order",
        "rule_type": "canon",
        "title": "境界顺序",
        "content": "不得跳过大境界。",
        "severity": "critical",
        "priority": 10
      }
    ],
    "entities": [
      {
        "entity_type": "character",
        "name": "主角",
        "profile": {"role": "protagonist"},
        "importance": "critical"
      }
    ],
    "state_snapshots": [
      {
        "entity_type": "character",
        "name": "主角",
        "state": {"realm": "练气一层"},
        "chapter_no": 1
      }
    ],
    "foreshadowing": [
      {
        "key": "jade_token",
        "title": "玉符来历",
        "importance": "high",
        "payload": {"hint": "上古传承钥匙"}
      }
    ],
    "volumes": [
      {"volume_no": 1, "title": "初入仙途", "status": "active"}
    ],
    "plot_threads": [
      {"key": "main_path", "title": "主线修行", "thread_type": "main"}
    ]
  }
}
```

### sync.submit_file_hashes

Submits incremental local file hash changes. If a chapter hash differs from the
MCP recorded hash, the tool reports a conflict and does not overwrite by
default.

Input:

```json
{
  "workspace": "friend_01",
  "project": "xianxia_001",
  "client_id": "author-laptop",
  "local_root_hint": "D:/novels/xianxia_001",
  "accept_conflicts": false,
  "files": [
    {
      "kind": "chapter",
      "chapter_no": 128,
      "volume_no": 3,
      "title": "雷池开门",
      "path_hint": "chapters/volume_003/ch0128.md",
      "sha256": "new_hex",
      "word_count": 3400
    }
  ]
}
```

### sync.list_conflicts

Lists stored binding conflicts, or checks a supplied manifest against MCP state.

Input:

```json
{
  "workspace": "friend_01",
  "project": "xianxia_001",
  "client_id": "author-laptop"
}
```

### sync.resolve_conflict

Supported actions:

```text
accept_local
keep_mcp
mark_ignored
```

Input:

```json
{
  "workspace": "friend_01",
  "project": "xianxia_001",
  "action": "accept_local",
  "conflict": {
    "target_type": "chapter",
    "chapter_no": 128,
    "local_key": "chapters/volume_003/ch0128.md",
    "local_hash": "new_hex",
    "mcp_hash": "old_hex",
    "local": {
      "kind": "chapter",
      "chapter_no": 128,
      "path_hint": "chapters/volume_003/ch0128.md",
      "sha256": "new_hex",
      "word_count": 3400
    }
  },
  "reason": "作者本地定稿覆盖旧 hash"
}
```

### sync.export_project_pack

Exports structured MCP project data for migration or backup. This is not a full
manuscript export.

Input:

```json
{
  "workspace": "friend_01",
  "project": "xianxia_001",
  "include_bindings": true
}
```

## Review Tools

### review.get_council_config

Input:

```json
{
  "workspace": "friend_01",
  "project": "xianxia_001"
}
```

### review.start_job

Creates a review job. Local clients then run model calls with local API keys.

Input:

```json
{
  "workspace": "friend_01",
  "project": "xianxia_001",
  "chapter_no": 128,
  "local_files": [
    {"kind": "chapter", "path_hint": "chapters/volume_001/ch0128.md", "sha256": "hex"}
  ],
  "dimensions": ["consistency", "ooc", "pacing", "reader_pull", "foreshadowing"]
}
```

### review.submit_model_report

Input:

```json
{
  "workspace": "friend_01",
  "project": "xianxia_001",
  "review_job_id": "uuid",
  "model_id": "claude_sonnet_local_key",
  "score": 82,
  "summary": "节奏较稳，但主角台词略解释过多。",
  "findings": [
    {
      "dimension": "ooc",
      "severity": "medium",
      "target": "主角",
      "evidence": "面对威胁时解释过多。",
      "suggestion": "改成短句和行动。",
      "rule_candidate": {
        "rule_type": "style",
        "title": "主角压迫场景少解释",
        "content": "..."
      }
    }
  ],
  "local_report_file": {
    "path_hint": "reviews/volume_001/ch0128.claude.review.md",
    "sha256": "hex"
  }
}
```

### review.aggregate

Aggregates model reports into a consensus report and rule proposals.

Input:

```json
{
  "workspace": "friend_01",
  "project": "xianxia_001",
  "review_job_id": "uuid",
  "create_rule_proposals": true,
  "create_revision_tasks": true
}
```

### review.extract_rule_proposals

Extracts rule candidates from model findings. Findings should carry
`rule_candidate` objects. When `create_proposals=true`, proposals are written to
`rule_proposals` for later approval; approved proposals create typed/scoped
rules from `agreement.rule`.

Input:

```json
{
  "workspace": "friend_01",
  "project": "xianxia_001",
  "review_job_id": "uuid",
  "create_proposals": true,
  "min_confidence": 0.6
}
```

### review.extract_state_updates

Extracts proposed entity state updates from model findings. This does not write
current state directly; it returns structured proposals for local/Web review.

Input:

```json
{
  "workspace": "friend_01",
  "project": "xianxia_001",
  "review_job_id": "uuid"
}
```

Expected finding shape:

```json
{
  "dimension": "state",
  "severity": "warning",
  "state_update": {
    "entity_type": "character",
    "name": "主角",
    "state": {"realm": "筑基初期"},
    "effective_chapter_no": 128,
    "duration_type": "persistent"
  }
}
```

### review.extract_foreshadowing_updates

Extracts proposed foreshadowing changes from review findings. This does not
directly plant/pay off/abandon foreshadowing.

Input:

```json
{
  "workspace": "friend_01",
  "project": "xianxia_001",
  "review_job_id": "uuid"
}
```

Expected finding shape:

```json
{
  "dimension": "foreshadowing",
  "severity": "high",
  "foreshadowing_update": {
    "key": "jade_token",
    "title": "玉符来历",
    "status": "planted",
    "importance": "high",
    "payoff_deadline_chapter": 180,
    "payload": {"review_note": "回收过晚，需要提前铺垫"}
  }
}
```

### review.evaluate_model_quality

Summarizes model review quality signals from scores and finding severity. This
is a lightweight automatic estimate until human review accuracy metrics are
added.

Input:

```json
{
  "workspace": "friend_01",
  "project": "xianxia_001",
  "review_job_id": "uuid"
}
```

### workflow.learn_from_review

Runs the review learning loop: aggregate model reports, create revision tasks,
create rule proposals, extract state/foreshadowing proposals, evaluate model
quality, and mark the job blocked when critical findings exist.

Input:

```json
{
  "workspace": "friend_01",
  "project": "xianxia_001",
  "review_job_id": "uuid",
  "create_revision_tasks": true,
  "create_rule_proposals": true,
  "block_on_critical": true
}
```

## Reference Tools

### reference.import_webnovel_writer

Imports templates, rubrics, and workflow prompts from a checked-out
`webnovel-writer` repository path on the server.

Input:

```json
{
  "workspace": "friend_01",
  "project": "xianxia_001",
  "repo_path": "/opt/novel-os/reference/webnovel-writer",
  "import_types": ["genre_template", "writing_pattern", "rubric", "agent_prompt"]
}
```

### reference.search

Input:

```json
{
  "workspace": "friend_01",
  "project": "xianxia_001",
  "query": "拍卖会 爽点 节奏",
  "item_types": ["scene_pattern", "writing_pattern"],
  "limit": 10
}
```

## Model & Cost Tools

### model.profile.upsert

Create or update a model profile for a project. Does not store API keys.

Input:

```json
{
  "workspace": "friend_01",
  "project": "xianxia_001",
  "profile_key": "gpt4o_standard",
  "display_name": "GPT-4o Standard",
  "provider": "openai",
  "model_name": "gpt-4o",
  "task_types": ["chapter_draft", "chapter_segment", "polish", "review"],
  "tier": "standard",
  "default_params": {"temperature": 0.7, "max_tokens": 4000},
  "cost_config": {"input_per_1k": 0.0025, "output_per_1k": 0.01},
  "rate_limit_config": {"requests_per_minute": 60},
  "is_default": true,
  "status": "active",
  "metadata": {}
}
```

### model.profile.list

List model profiles with optional filtering.

Input:

```json
{
  "workspace": "friend_01",
  "project": "xianxia_001",
  "task_type": "review",
  "status": "active",
  "tier": "premium"
}
```

### model.route

Route to recommended model for a task type. Returns primary and fallback profiles.

Input:

```json
{
  "workspace": "friend_01",
  "project": "xianxia_001",
  "task_type": "chapter_draft",
  "chapter_no": 42,
  "volume_no": 3
}
```

Returns:

```json
{
  "task_type": "chapter_draft",
  "primary": { "profile_key": "...", "model_name": "...", "provider": "...", "tier": "...", "default_params": {}, "cost_config": {} },
  "fallbacks": [],
  "route_rule": null,
  "source": "task_type_default"
}
```

### model.route_rule.upsert

Create or update a model routing rule.

Input:

```json
{
  "workspace": "friend_01",
  "project": "xianxia_001",
  "task_type": "review",
  "profile_key": "premium_model",
  "priority": 10,
  "conditions": {},
  "fallback_profile_keys": ["standard_model"],
  "status": "active",
  "metadata": {}
}
```

### model.route_rule.list

List model routing rules.

Input:

```json
{
  "workspace": "friend_01",
  "project": "xianxia_001",
  "task_type": "review",
  "status": "active"
}
```

### cost.record_usage

Record a model usage event with token counts and cost.

Input:

```json
{
  "workspace": "friend_01",
  "project": "xianxia_001",
  "task_type": "chapter_draft",
  "profile_key": "standard_model",
  "source_type": "generation",
  "source_id": "chapter_042",
  "input_tokens": 1500,
  "output_tokens": 3000,
  "cached_tokens": 0,
  "total_tokens": 4500,
  "cost_amount": 0.03375,
  "currency": "USD",
  "latency_ms": 2500,
  "success": true,
  "error_code": null,
  "metadata": {}
}
```

### cost.report

Get cost and usage report grouped by day, task_type, model, profile, provider, or tier.

Input:

```json
{
  "workspace": "friend_01",
  "project": "xianxia_001",
  "group_by": "task_type",
  "task_types": ["chapter_draft", "review"],
  "profile_keys": null,
  "from_date": "2026-06-01",
  "to_date": "2026-07-01"
}
```

Returns:

```json
{
  "project_id": "...",
  "group_by": "task_type",
  "from_date": "...",
  "to_date": "...",
  "summary": {
    "usage_count": 100,
    "total_input_tokens": 50000,
    "total_output_tokens": 100000,
    "total_tokens": 150000,
    "total_cost": 1.25,
    "success_count": 95,
    "error_count": 5
  },
  "groups": [
    {
      "period": "chapter_draft",
      "usage_count": 60,
      "total_tokens": 90000,
      "total_cost": 0.75,
      "avg_latency_ms": 2000
    }
  ]
}
```

## Admin Tools

### admin.health

Input:

```json
{}
```

### admin.rebuild_indexes

Input:

```json
{
  "workspace": "friend_01",
  "project": "xianxia_001",
  "targets": ["postgres_fts", "qdrant"]
}
```

### admin.audit

Input:

```json
{
  "workspace": "friend_01",
  "project": "xianxia_001",
  "limit": 100
}
```
