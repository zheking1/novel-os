---
name: novel-os-local
description: Local Novel OS writing workflow for projects whose manuscript files stay on the user's machine while a central novel-os-mcp server stores rules, canon, memory, foreshadowing, review data, and structured commits. Use when initializing a local novel workspace, fetching MCP context packs, saving outlines/chapters/reviews locally, submitting chapter commits, or coordinating local API-key model generation and review with Novel OS MCP.
---

# Novel OS Local

Use this skill when working in a local novel project that syncs structured data
to a central `novel-os-mcp` server.

## Boundary

Keep editable outputs local:

- `outlines/`
- `plans/`
- `chapters/`
- `drafts/`
- `reviews/`
- `exports/`

Use MCP for central intelligence:

- Rules and canon
- Character/world state
- Foreshadowing and plot state
- Chapter summaries and commits
- Review reports and rule proposals
- Reference templates and search metadata

Do not upload full manuscript text unless the user explicitly asks. Submit
summaries, events, hashes, word counts, and structured state changes.

## Local Script

Use `scripts/novel_local.py` for deterministic local operations.

Common commands:

```bash
python scripts/novel_local.py init --root . --mcp-url http://${NAS_HOST}:48083/mcp --workspace default --project demo --title "Demo Novel"
python scripts/novel_local.py templates-init --root .
python scripts/novel_local.py init-templates --root . --title "My Novel" --genre "都市"
python scripts/novel_local.py init-pack --root . --output initial-pack.json
python scripts/novel_local.py whoami --root .
python scripts/novel_local.py onboard-project --root . --project-root ../friend_novel --username friend_a --workspace friend_a --project demo --title "Demo Novel"
python scripts/novel_local.py token-create --root . --username friend_a --name "friend-a-local" --workspace friend_a --scope read --scope write
python scripts/novel_local.py webnovel-pack-build --source ./webnovel-writer --output ./webnovel-writer/novel-os-pack.json
python scripts/novel_local.py skill-import --root . --source ./webnovel-writer
python scripts/novel_local.py import-pack --root . --pack-file ./my-project/pack.json
python scripts/novel_local.py export-pack --root . --output ./exports/project-pack.json
python scripts/novel_local.py dirs-init --root . --force
python scripts/novel_local.py dirs-validate --root .
python scripts/novel_local.py manifest-generate --root . --output manifest.json
python scripts/novel_local.py outline-run --root . --brief "Write the next arc outline" --context-file context/ch0001.context.md --dry-run
python scripts/novel_local.py draft-run --root . --chapter 1 --context-file context/ch0001.context.md --plan-file plans/ch0001.md --output-file drafts/ch0001.generated.md --dry-run
python scripts/novel_local.py context --root . --chapter 1 --focus "auction" --focus "token"
python scripts/novel_local.py context --root . --chapter 1 --offline
python scripts/novel_local.py context-list --root .
python scripts/novel_local.py context-clear --root . --chapter 1
python scripts/novel_local.py commit --root . --chapter 1 --title "Chapter 1" --summary "Short summary." --chapter-file chapters/volume_001/ch0001.md --commit-type final
python scripts/novel_local.py commit --root . --chapter 1 --offline --commit-type draft
python scripts/novel_local.py queue-list --root .
python scripts/novel_local.py queue-sync --root .
python scripts/novel_local.py review-start --root . --chapter 1 --chapter-file chapters/volume_001/ch0001.md
python scripts/novel_local.py review-run --root . --chapter 1 --chapter-file chapters/volume_001/ch0001.md --context-file context/ch0001.context.md
python scripts/novel_local.py review-submit --root . --review-job-id <uuid> --report-file reviews/volume_001/ch0001.report.json
python scripts/novel_local.py review-aggregate --root . --review-job-id <uuid>
python scripts/novel_local.py rules-evolve --root . --review-job-id <uuid> --dry-run
python scripts/novel_local.py vector-pending --root .
python scripts/novel_local.py vector-run --root . --dry-run
python scripts/novel_local.py vector-upsert --root . --embedding-file .novel-os/chunk.embedding.json
```

Use `--mcp-url http://127.0.0.1:8787/mcp` when connected by SSH tunnel.
Use `--mcp-url http://${NAS_HOST}:48083/mcp` for the configured nginx reverse
proxy on the NAS LAN.

## Workflow

1. Initialize local workspace with `init`.
2. Fetch context for the next chapter with `context`.
3. Write/edit local outline, plan, draft, and chapter files.
4. Submit a structured commit with `commit`.
5. Run local model generation and review with the user's own API key environment variables.
6. Save review Markdown under `reviews/`.
7. Submit structured review reports to MCP.
8. Generate rule proposals from review consensus, then approve them when useful.
9. Generate embeddings locally with the user's own API keys and upsert them to MCP/Qdrant.

For detailed command behavior, read `references/workflows.md`.
