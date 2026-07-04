# Initial MCP Tools

This first implementation intentionally exposes a small stable set.

## Admin

- `admin.health`

## Auth

- `auth.whoami`
- `auth.create_api_token`

`NOVEL_OS_AUTH_MODE=token` requires `Authorization: Bearer <token>`. Tokens can
be scoped to one workspace and can carry `admin`, `read`, and `write` scopes.

## Workspace And Project

- `user.create`
- `workspace.create`
- `workspace.add_member`
- `project.create`
- `project.register_local_binding`

## Canon Documents

- `canon.doc.upsert`
- `canon.doc.list`
- `canon.doc.get`
- `canon.doc.archive`
- `canon.doc.history`
- `canon.doc.restore`

Canon documents store structured long-term novel settings such as worldbuilding,
power systems, character baselines, faction notes, style bibles, and project
constraints. They are versioned in MCP, while full manuscript files remain in
the local author workspace.

## Rules

- `rules.list`
- `rules.list_effective`
- `rules.check_conflict`
- `rules.propose`
- `rules.upsert`
- `rules.bulk_toggle`
- `rules.resolve_conflict`
- `rules.list_proposals`
- `rules.apply_proposal`

Rule tools support scoped and temporary rules for global, volume, chapter,
character, plot-thread, and project-defined contexts. `rules.list_effective`
returns the active rules for a requested chapter/volume/scope and reports rules
excluded by explicit supersede/block links. `rules.check_conflict` performs
structural conflict checks and lightweight keyword matching for rules that carry
`metadata.keywords`.

## Compliance

- `compliance.rule.upsert`
- `compliance.rule.list`
- `compliance.check`

Compliance tools store project-specific forbidden zones as evolvable rules and
check generated snippets without uploading full local manuscripts. Critical
matches block generation, can create blocking revision tasks for a review job,
and write audit logs for rule changes and blocking checks.

## Model & Cost

- `model.profile.upsert`
- `model.profile.list`
- `model.route`
- `model.route_rule.upsert`
- `model.route_rule.list`
- `cost.record_usage`
- `cost.report`

Model & cost tools let each project configure LLM profiles for different task
types (outline, draft, review, compliance, etc.) and track token usage and costs.
API keys are never stored in MCP — they are managed by the local client or
calling environment. `model.route` returns a recommended primary model plus
fallbacks based on routing rules and task type defaults. `cost.report` provides
aggregated usage and cost statistics grouped by day, task type, model, profile,
provider, or tier.

## Plot

- `volume.upsert`
- `volume.list`
- `plot.thread.upsert`
- `plot.thread.list`
- `plot.thread.advance`
- `plot.thread.check_stalled`
- `plot.list_foreshadowing`
- `foreshadowing.bulk_status_update`
- `foreshadowing.check_overdue`
- `foreshadowing.link`
- `foreshadowing.payoff`
- `plot.create_chapter_plan`

## Memory

- `memory.search`
- `memory.get_state`
- `memory.get_recent_summaries`
- `memory.rebuild_projection`
- `memory.pending_vector_chunks`
- `memory.upsert_vector`
- `memory.vector_search`

## State

- `state.entity.upsert`
- `state.entity.list`
- `state.entity.get`
- `state.entity.bulk_patch`
- `state.snapshot.upsert`
- `state.snapshot.list`
- `state.relationship.upsert`
- `state.relationship.list`

State tools maintain structured entities, current/temporary state snapshots, and
entity relationships. They support characters, factions, locations, items, and
other project-defined entity types. Full prose remains in local files.

## Workflow

- `workflow.prepare_chapter_context`
- `workflow.validate_context_pack`
- `workflow.preflight_generation`
- `workflow.prepare_segment_context`
- `workflow.submit_chapter_commit`
- `workflow.learn_from_review`

This accepts structured chapter metadata from a local user workspace. It does
not upload or own the full local manuscript.

Context tools build bounded generation packs for local AI clients. They filter
rules through `rules.list_effective`, keep prose files local, report excluded
rules and expiring state as warnings, support POV-safe foreshadowing layers, and
provide preflight validation before a chapter or chapter segment is generated.

## Sync

- `sync.import_local_manifest`
- `sync.import_initial_project_pack`
- `sync.submit_file_hashes`
- `sync.list_conflicts`
- `sync.resolve_conflict`
- `sync.export_project_pack`

Sync tools bind a local writing folder to an MCP project without uploading full
manuscript prose. They store local path hints, file hashes, word counts, and
structured project data such as Canon, rules, entity state, plot threads, and
foreshadowing. Hash conflicts are reported explicitly and require either an
accepted local resolution or a keep-MCP decision.

## Review

- `review.start_job`
- `review.submit_model_report`
- `review.aggregate`
- `review.extract_rule_proposals`
- `review.extract_state_updates`
- `review.extract_foreshadowing_updates`
- `review.evaluate_model_quality`

Review learning tools extract structured follow-up work from model reports.
They can create revision tasks, create rule proposals for human approval,
return state and foreshadowing update proposals, evaluate model quality, and
mark a review job as blocking when critical findings should stop the next
chapter. They do not directly rewrite Canon, entity state, or foreshadowing
facts.
