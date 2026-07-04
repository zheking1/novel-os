# Novel OS MCP Architecture

`novel-os-mcp` is a single MCP server with modular internals. It is the central
memory, rule, reference, plot, and review service for long-form webnovel
production.

It does not own the user's manuscript files. Local clients or local Codex skills
own generated chapters, outlines, detailed plans, draft files, and editable
review documents.

## Core Principle

```text
MCP stores durable intelligence.
Local workspace stores editable outputs.
```

Central MCP stores:

- Users, workspaces, projects, permissions, and audit logs
- Canon, rules, style policies, forbidden items, and reveal locks
- Character, location, item, faction, and world state projections
- Plot threads, arcs, foreshadowing, chapter commits, and summaries
- Reference templates, writing patterns, genre patterns, and review rubrics
- Structured review reports, rule proposals, and rule version history
- Search metadata and vector index references

Local workspace stores:

- Master outline Markdown
- Volume outlines
- Chapter plans and scene breakdowns
- Generated chapters and drafts
- Human-edited revisions
- Human-readable review Markdown
- Exports and backups chosen by the user

## Deployment Shape

Runtime services:

```text
novel-os-mcp
postgres + pgvector
qdrant
redis
optional dashboard
optional adminer
```

Only `novel-os-mcp` should be exposed to writing clients. PostgreSQL, Qdrant, and
Redis must stay private to the NAS or Docker network.

## Logical Modules

The MCP process is one server, but code is organized as modules:

```text
auth        users, workspaces, project membership, API tokens
memory      summaries, events, state projections, memory chunks
plot        arcs, threads, chapter plans, foreshadowing
rules       canon, soft rules, reveal locks, proposals, versions
reference   webnovel-writer imports, templates, patterns, rubrics
review      multi-model review reports, consensus, revision tasks
workflow    prepare context, accept local commits, learn from review
admin       health, backup metadata, index rebuilds, migrations
```

## Multi-User Model

Each user can belong to multiple workspaces. Each workspace can contain multiple
projects.

```text
user -> workspace_members -> workspace -> project_members -> project
```

Recommended roles:

```text
system_admin   server maintenance only
owner          manage workspace, members, projects, and rules
editor         write and commit chapters, propose rules
reviewer       submit reviews and revision tasks
reader         read context, summaries, and reports
```

API keys for LLM providers should normally stay local to each user. The central
MCP can store model profile names and review council configuration, but should
not require provider secrets unless the user explicitly enables server-side
model calls later.

## Local Output Contract

Every local client registers a local project binding:

```yaml
workspace_slug: friend_01
project_slug: xianxia_001
local_root: D:/Novels/xianxia_001
mcp_url: https://nas.example.com/mcp
```

The local client should maintain:

```text
.novel-os/project.yml
.novel-os/sync-state.json
outlines/
plans/
chapters/
drafts/
reviews/
exports/
```

The MCP stores local file metadata and content hashes, not authoritative editable
files.

## Chapter Lifecycle

```text
1. Local client requests workflow.prepare_chapter_context
2. MCP builds a bounded context pack from rules, state, plot, memory, and reference
3. Local client uses the user's own API keys to draft content
4. Local client saves outline/plan/chapter/review Markdown locally
5. Local client submits structured chapter commit to MCP
6. MCP validates commit, updates projections, indexes memory, and tracks plot/rules
7. Review council output creates findings, revision tasks, and rule proposals
8. Approved or auto-applicable soft rules affect future context packs
```

## Context Pack Budgeting

AI should never read the whole book. `workflow.prepare_chapter_context` must use
explicit budgets:

```text
canon and reveal locks
current state projection
current arc and chapter plan
recent chapter summaries
relevant long-term memories
open foreshadowing and plot threads
style and review rules
last review lessons
```

Each section has a token budget and a priority. Overflow content is summarized or
excluded with retrieval audit records.

## Rule Evolution

Rules are data, not code. Rules have versions and proposals.

Rule classes:

```text
canon          requires owner approval
character      requires owner or project editor approval
plot           requires project editor approval
review         can auto-apply if confidence is high
style          can auto-apply if configured
lesson         can auto-store as experience memory
```

No model should silently rewrite canon. Models submit `rule_proposals`.

## Review Council

The central MCP stores review configuration and structured reports. Actual model
calls can be local-first:

```text
local model call -> structured report -> MCP review.submit_model_report
```

Later, server-side model calls can be added without changing the data model.

Review flow:

```text
review.start_job
review.submit_model_report
review.aggregate
review.generate_revision_tasks
rules.create_proposals_from_review
workflow.learn_from_review
```

## Storage Boundary

PostgreSQL is the source of truth for structured data.

Qdrant stores vector points for searchable memory and references. Qdrant point
payloads contain metadata and short text, not full manuscript ownership.

Local files remain the user's editable source for generated prose.

## Future Dashboard

The dashboard should use the same APIs and permissions as MCP tools.

Dashboard views:

- Workspace and project selector
- Rule library and proposal approval
- Character and world state projections
- Plot threads and foreshadowing board
- Context pack preview
- Review council reports and revision tasks
- Reference template browser
- Sync and audit logs

