# MCP Tools Master Index

> Exhaustive index of ALL MCP tools across 29 tool modules.
> Module source: `novel-os-mcp/src/novel_os_mcp/tools/`

## Module Summary

> 下表 Count 列由脚本统计 `@mcp.tool` 装饰器数量得出，校验于 2026-10-11。
> 新增工具后请同步更新：
> ```powershell
> cd novel-os-mcp/src/novel_os_mcp/tools
> Get-ChildItem *.py | ForEach-Object {
>   $n = (Select-String -Path $_.FullName -Pattern '@mcp\.tool' -AllMatches |
>         ForEach-Object { $_.Matches.Count } | Measure-Object -Sum).Sum
>   "{0,-26} {1}" -f $_.Name, $n
> }
> ```

| # | Module File | Count | Namespace | Purpose | Key DB Tables |
|---|------------|-------|-----------|---------|--------------|
| 1 | `auth.py` | 20 | auth., user., workspace., project. | Auth, user CRUD, workspace/project management | users, workspaces, projects |
| 2 | `canon.py` | 20 | canon.doc., rules., compliance. | Setting docs, creative rules, compliance checking | canon_documents, canon_rules, compliance_rules |
| 3 | `context.py` | 21 | workflow., context., chapter., project. | Chapter context pack, generation workflow, chapter/project reset | context_packs, workflow_sessions, chapters, 15+ tables |
| 4 | `plot.py` | 16 | volume., plot., foreshadowing. | Volume management, plot threads, foreshadowing lifecycle | volumes, plot_threads, foreshadowing, chapter_plans |
| 5 | `memory.py` | 17 | state., memory. | Story entities, state snapshots, relationships, vector memory | state_entities, state_snapshots, entity_relationships |
| 6 | `kb.py` | 39 | kb. | Knowledge base: entities, UK, PK, world state, gaps, genre, auto-search | universal_knowledge, knowledge_entities, project_knowledge, world_snapshots, ref_categories |
| 7 | `setting.py` | 15 | setting. | Setting categories/items, genre resolve, CSV import/export | setting_categories, setting_items |
| 8 | `prompt.py` | 23 | prompt., context.weight., material., expectation., annotation., noun., search. | Prompt templates, context weights, reference materials, annotations, proper nouns, fulltext search | prompt_templates, context_weight_configs, reference_materials, chapter_annotations |
| 9 | `model.py` | 8 | model., cost. | Model profiles, routing rules, cost tracking/reporting, auto-assign | model_profiles, model_route_rules, cost_logs |
| 10 | `system.py` | 14 | cache., backup., restore., system. | Redis cache management, backups, system health, degradation | — (Redis, backup_records) |
| 11 | `skill.py` | 11 | skill., skill.step. | Skill CRUD, step management, semantic matching | skills, skill_steps |
| 12 | `graph.py` | 3 | graph. | Entity relationship graph data, subgraph, timeline | state_entities, entity_relationships |
| 13 | `review.py` | 14 | review. | Chapter review jobs, council config, model reports, aggregate, extract | review_jobs, review_reports, review_council_configs |
| 14 | `discussion_room.py` | 7 | discussion_room. | Multi-model discussion room: create, poll, resume, apply results | discussion_sessions |
| 15 | `system_assets.py` | 11 | system.style_profile., system.prompt_template., system.model_profile. | System-level style profiles, prompt templates, model profiles (list/get/fork/create) | system_style_profiles, system_prompt_templates, system_model_profiles |
| 16 | `system_evolution.py` | 6 | system.evolution. | Evolution proposals: create, list, get, admin review, history, retry | system_evolution_proposals |
| 17 | `system_notifications.py` | 5 | system.notification. | User notifications: list, mark read/all, delete, unread count | system_notifications |
| 18 | `vector.py` | 11 | vector.index., embedding., rag. | Vector index queue, embedding/rerank, RAG knowledge/event search | Qdrant collections |
| 19 | `sync.py` | 6 | sync. | File manifest import, hash submission, conflict resolution, project pack export | sync_files, sync_conflicts |
| 20 | `local.py` | 14 | local. | Local project registration, file scan, chapter read/write, review I/O, stats | chapter_index, setting_index, review_index |
| 21 | `archive.py` | 16 | archive., context.compression. | Volume archive/restore, context compression (chapters/arc/volume/series), auto-archive | compressed_contexts, archive_jobs |
| 22 | `novel_wizard.py` | 11 | novel.wizard., tone. | Novel creation wizard, world building, tone/rule management, knowledge proposal submission | (multi-table via commit) |
| 23 | `novel_gen.py` | 52 | arc., causality., novelty., pacing., style., pipeline. | Character arcs, event causality, novelty checks, pacing/emotion, style analysis, generation pipeline | character_arcs, causality_chains, chapter_emotions, chapter_style_metrics, generation_passes |
| 24 | `knowledge_pack.py` | 8 | kb.pack. | Project knowledge pack: genre config, create/update, custom categories | project_packs |
| 25 | `knowledge_audit.py` | 3 | knowledge. | Knowledge audit, council debate for proposals | system_evolution_proposals |
| 26 | `evolution.py` | 3 | evolution. | Evolution logs, rollback, stats | evolution_logs |
| 27 | `reference.py` | 3 | reference. | Reference sources, items, search | reference_sources, reference_items |
| 28 | `global_rules.py` | 4 | global_rules. | Global rules: list, upsert, delete, promote from project | global_rules |
| 29 | `admin.py` | 1 | admin. | System health check (DB, Redis, Qdrant) | — |
| **Total** | | **382** | | | |

## Detailed Module Documentation

For full tool signatures, parameters, and logic, see:

| File | Covers |
|------|--------|
| [auth-tools.md](./auth-tools.md) | Auth, user, workspace, project management |
| [canon-tools.md](./canon-tools.md) | Canon documents, creative rules, compliance |
| [context-tools.md](./context-tools.md) | Chapter context, workflow pipeline, reset |
| [plot-tools.md](./plot-tools.md) | Volumes, plot threads, foreshadowing |
| [memory-tools.md](./memory-tools.md) | Entities, state snapshots, relationships, vector memory |
| [kb-tools.md](./kb-tools.md) | Knowledge base: categories, entities, UK, PK, world, gaps, genre, packs, audit |
| [review-tools.md](./review-tools.md) | Chapter review jobs, council config, revision tasks |
| [discussion-room-tools.md](./discussion-room-tools.md) | Multi-model discussion room with 5-phase engine |
| [system-tools.md](./system-tools.md) | Cache, backup, system health, admin, assets, evolution proposals, notifications |
| [model-tools.md](./model-tools.md) | Model profiles, routing rules, cost tracking, auto-assign |
| [misc-tools.md](./misc-tools.md) | Settings, prompts, skills, graph, evolution, global rules, reference, vector, sync, local, archive, novel wizard, novel gen |

## Tool Naming Convention

- **Dots, not underscores:** `prompt.template.upsert` ✓, `prompt_template_upsert` ✗
- **Namespace grouping:** `auth.*`, `kb.*`, `state.*`, `review.*`, `workflow.*`
- **CRUD pattern:** `.list`, `.get`, `.create`/`.upsert`, `.update`, `.delete`
- **Key tools** return `workflow_guide` for AI tool orchestration
