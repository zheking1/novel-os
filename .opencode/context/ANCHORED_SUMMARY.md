# Anchored Summary

## Goal
- Analyze and optimize the Novel OS system for 20M+ character novels. Build progressive context compression, multi-pass generation, character arc tracking, causality chains, novelty detection, pacing modeling, style fingerprinting, and RAG retrieval via embedding APIs.

## Constraints & Preferences
- Caveman mode active (level: full) unless "stop caveman" or "normal mode"
- Deployed on NAS `${NAS_HOST}`, path `/opt/novel-os`
- DB credentials: `novel_os` / `${POSTGRES_PASSWORD}`, Redis: `${REDIS_PASSWORD}`
- SSH: `root@${NAS_HOST}`, password `${NAS_SSH_PASSWORD}`
- MCP docker-compose: `docker-compose.yml` + `docker-compose.app.example.yml`
- Embedding/rerank config via `model_profiles` table (web UI), NOT env vars
- OpenAI-compatible API format for embedding/rerank platforms

## Progress
### Done
- Full project structure exploration, workflow mapping, all MCP tools cataloged
- **7 new services** built: `context_compression.py`, `multipass.py`, `character_arc.py`, `causality.py`, `novelty.py`, `pacing.py`, `style_fingerprint.py`, `embedding.py`
- **64+ new MCP tools** added across: context.compression (8), pipeline (7), arc (11), causality (7), novelty (5), pacing (11), style (8), embedding/rag (7), archive (2)
- **4 SQL migrations** deployed: `200_context_compression.sql`, `201_character_arcs_causality.sql`, `202_pacing_emotion.sql`, `203_style_fingerprint.sql`, `204_events_archive.sql`
- **7 critical defects fixed**: compression truncation → structured extraction, no token budget → section-level budget, rebuild_projection OOM → batch cursor, causality recursion → PostgreSQL CTE, novelty keyword match → vector semantic (via Qdrant), no archiving → auto-archive, token estimation `len//4` → Chinese-aware `chars*1.5`
- `prepare_chapter_context` rewritten: per-section token budgets (18/22/10/12/15/8/8/4%), dynamic overflow trimming, priority-based trim order
- `rebuild_projection` rewritten: batch_size=100 cursor pagination, incremental mode
- Causality traversal rewritten: PostgreSQL `WITH RECURSIVE` CTE, single query
- `embedding.py`: reads config from `model_profiles` table (not env), supports OpenAI-compatible API, project-scoped
- All code compiles clean, all deployments successful on NAS
- **Retrieval precision upgrades (R1, R3)**: Entity relevance ranking, knowledge_base RAG integration
- **Context overflow fixes (C1-C5)**: Token estimation fix, priority trimming, hard ceiling, output constraints, compliance validation

### In Progress
- Waiting for user to configure embedding/rerank models in web client (model_profiles table, task_types: `embedding` / `rerank`)

### Blocked
- Embedding/RAG integration into `prepare_chapter_context` not yet implemented (waiting for user confirmation of approach)

## Key Decisions
- Progressive compression uses **structured extraction** (characters, keywords, turning points, emotion arc) not LLM summarization or truncation
- Context budget split: rules 18%, state 22%, KB 10%, foreshadowing 12%, summaries 15%, plan 8%, memory 8%, compressed 4%, output overhead 3%
- Causality uses PostgreSQL CTE recursive instead of Python recursion (no N+1 queries)
- Embedding service reads config from `model_profiles` DB table, not env vars — user configures via web UI
- `events_archive` table for cold data; auto-archive keeps last 3 volumes hot
- `novelty.py` falls back to keyword matching if no embedding model configured
- Token estimation uses Chinese-aware `chars*1.5 + words*1.3` instead of naive `len//4`
- Entity ranking uses relevance scoring based on chapter characters, focus terms, and lifecycle status
- Knowledge base items retrieved by character name and focus term matching
- Output constraints appended to context to prevent hallucination
- Compliance validation checks forbidden keywords, dead character mentions, and canon conflicts

## Next Steps
- User configures embedding model in web client (`model_profiles`, task_types=`embedding`) and rerank model (task_types=`rerank`)
- Wire embedding vectors into `memory.search` for semantic retrieval (replace `plainto_tsquery`)
- Consider: embedding vectors for knowledge_base items (index into Qdrant on upsert)
- P2 remaining: batch vectorize existing knowledge_base items

## Critical Context
- Architecture: FastMCP server (Python 3.11+), PostgreSQL 16 + pgvector, Qdrant vector DB, Redis cache
- Components: `novel-os-mcp` (port 8787), `novel-os-web` (port 8790)
- `model_profiles` table: per-project model config with `task_types[]` array — supports `embedding`, `rerank`, completion tasks
- `model_route_rules` table: maps task_type → profile_key with priority and conditions
- `knowledge_base` table has full CRUD + `search_items()` but **not connected** to context assembly
- `memory_chunks` search uses `plainto_tsquery` (keyword), not vector semantic
- Docker rebuild command: `cd /opt/novel-os && docker compose -f docker-compose.yml -f docker-compose.app.example.yml build novel-os-mcp && docker compose -f docker-compose.yml -f docker-compose.app.example.yml up -d novel-os-mcp`
- NAS .env cleaned of embedding env vars (config now via DB)

## Relevant Files
- `D:\Project\novels codex\novel-os-mcp\src\novel_os_mcp\main.py`: All MCP tool definitions (~5500 lines), imports all new services
- `D:\Project\novels codex\novel-os-mcp\src\novel_os_mcp\services.py`: Core logic + rewritten `prepare_chapter_context` (section budgets + entity ranking + KB RAG + output constraints) + `validate_generated_content` + batch `rebuild_projection`
- `D:\Project\novels codex\novel-os-mcp\src\novel_os_mcp\context_compression.py`: Progressive compression (chapter→arc→volume→series) + structured extraction + auto-archive + archive stats
- `D:\Project\novels codex\novel-os-mcp\src\novel_os_mcp\multipass.py`: 4-pass pipeline (plan→draft→polish→verify) + continuity check
- `D:\Project\novels codex\novel-os-mcp\src\novel_os_mcp\character_arc.py`: Emotion/relationship/power/personality tracking + compressed summary for context
- `D:\Project\novels codex\novel-os-mcp\src\novel_os_mcp\causality.py`: Causal chains with PostgreSQL CTE recursive queries
- `D:\Project\novels codex\novel-os-mcp\src\novel_os_mcp\novelty.py`: Scene/description/dialogue/plot beat dedup, supports vector semantic via Qdrant
- `D:\Project\novels codex\novel-os-mcp\src\novel_os_mcp\pacing.py`: Volume blueprints, chapter emotion tracking, rhythm analysis, engagement prediction
- `D:\Project\novels codex\novel-os-mcp\src\novel_os_mcp\style_fingerprint.py`: POV/tense/tone profiles, chapter style metrics, drift detection
- `D:\Project\novels codex\novel-os-mcp\src\novel_os_mcp\embedding.py`: EmbeddingService + RerankService, reads config from `model_profiles` DB, OpenAI-compatible API
- `D:\Project\novels codex\novel-os-mcp\src\novel_os_mcp\config.py`: Pydantic settings (embedding env vars removed, now DB-driven)
- `D:\Project\novels codex\deploy\nas\postgres\migrations\200_context_compression.sql`: compressed_contexts table
- `D:\Project\novels codex\deploy\nas\postgres\migrations\201_character_arcs_causality.sql`: character_arcs, causality_chains, generation_passes tables
- `D:\Project\novels codex\deploy\nas\postgres\migrations\202_pacing_emotion.sql`: pacing_blueprints, chapter_emotions tables
- `D:\Project\novels codex\deploy\nas\postgres\migrations\203_style_fingerprint.sql`: style_profiles, chapter_style_metrics tables
- `D:\Project\novels codex\deploy\nas\postgres\migrations\204_events_archive.sql`: events_archive table
- `D:\Project\novels codex\deploy\nas\postgres\init\150_model_cost.sql`: model_profiles, model_route_rules tables (pre-existing)
- `D:\Project\novels codex\deploy\nas\docker-compose.app.example.yml`: MCP server docker-compose config
