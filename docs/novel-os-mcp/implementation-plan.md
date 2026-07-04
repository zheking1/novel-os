# Novel OS MCP Implementation Plan

This is the recommended implementation order.

## Phase 1: Server Skeleton

- Python project with FastMCP
- Pydantic settings loaded from environment variables
- PostgreSQL async connection pool
- Qdrant client
- Redis client
- Request auth middleware
- Structured logging
- Health tool

Deliverable:

```text
novel-os-mcp starts locally and exposes admin.health/auth.whoami
```

## Phase 2: Multi-User Core

- users
- workspaces
- workspace_members
- projects
- project_members
- api_tokens
- local_project_bindings
- audit_logs

Deliverable:

```text
create workspace/project, issue token, register local binding
```

## Phase 3: Rules And Plot

- canon_rules
- rule_versions
- rule_proposals
- plot_threads
- chapter_plans
- foreshadowing

Deliverable:

```text
rules.list/rules.propose/rules.apply_proposal
plot.create_chapter_plan/plot.list_foreshadowing
```

## Phase 4: Memory And Projection

- chapters
- chapter_commits
- chapter_summaries
- events
- state_entities
- state_snapshots
- memory_chunks
- projection engine from accepted commits

Deliverable:

```text
workflow.submit_chapter_commit updates current projected state
memory.get_state and memory.search work
```

## Phase 5: Context Builder

- Context budget schema
- Hybrid retrieval
- Section prioritization
- Retrieval audit
- Context pack persistence

Deliverable:

```text
workflow.prepare_chapter_context returns bounded context packs
```

## Phase 6: Review Council

- review_council_configs
- review_jobs
- review_reports
- revision_tasks
- report aggregation
- rule proposal extraction

Deliverable:

```text
local clients can submit multi-model reports and aggregate them
```

## Phase 7: Reference Import

- reference_sources
- reference_items
- importer for webnovel-writer templates and rubrics
- reference search index

Deliverable:

```text
reference.import_webnovel_writer and reference.search
```

## Phase 8: Docker Integration

- Build Dockerfile for novel-os-mcp
- Add service to docker-compose
- Add migration runner
- Add environment examples

Deliverable:

```text
NAS deployment can start novel-os-mcp beside postgres/qdrant
```

## Phase 9: Local Skill

This is a separate project, but its contract is defined by this MCP.

- Initialize local directory
- Pull context pack
- Save local plans/chapters/reviews
- Run local model calls with local API keys
- Submit commits and review reports

Deliverable:

```text
users can write locally while MCP stores central memory and rules
```

