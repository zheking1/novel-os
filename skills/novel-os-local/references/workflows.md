# Novel OS Local Workflows

## Directory Layout

The local project root should contain:

```text
.novel-os/
  project.json
  sync-state.json
outlines/
plans/
chapters/
  volume_001/
drafts/
reviews/
exports/
context/
```

## Init

`init` creates directories, writes `.novel-os/project.json`, calls
`project.create`, and registers the local binding with
`project.register_local_binding`. It also writes local examples:

- `.novel-os/review-models.example.json`
- `.novel-os/novel-os-pack.example.json`

For an existing project, regenerate examples with:

```bash
python scripts/novel_local.py templates-init --root .
```

## Model Profiles

Copy `.novel-os/model-config.example.json` to `.novel-os/model-config.json`.
The unified model config has three profiles:

- `outline` for outline and arc planning
- `draft` for prose generation
- `review` for multi-model review

Each profile can use different providers, models, temperatures, and token
budgets. Provider API keys stay local through environment variables such as
`NOVEL_OS_MODEL_API_KEY`, `OPENAI_API_KEY`, or `API_KEY`.

Generate an outline:

```bash
python scripts/novel_local.py outline-run --root . --brief "Write the next arc outline" --context-file context/ch0001.context.md --output-file outlines/arc_001.generated.md
```

Generate chapter prose:

```bash
python scripts/novel_local.py draft-run --root . --chapter 1 --context-file context/ch0001.context.md --plan-file plans/ch0001.md --output-file drafts/ch0001.generated.md
```

Use `--dry-run` on either command to write the prompt JSON without calling any
model.

## Auth

`whoami` confirms which server identity and scopes the local project is using:

```bash
python scripts/novel_local.py whoami --root .
```

`token-create` creates API tokens through `auth.create_api_token`. Run it with an
admin-capable local config or with `--mcp-url` while the server is still in
bring-up mode:

```bash
python scripts/novel_local.py token-create --root . --username friend_a --name "friend-a-local" --workspace friend_a --scope read --scope write
```

The returned token is shown only once. Put it in that user's local
`.novel-os/project.json` as `api_token`, or pass it to `init --api-token`.

`onboard-project` creates a user, workspace, project, project-scoped token, and
local project directory in one command. Run it from an admin-capable local
config; the generated project token is saved into the target local
`.novel-os/project.json` and is not printed:

```bash
python scripts/novel_local.py onboard-project --root . --project-root ../friend_novel --username friend_a --workspace friend_a --project demo --title "Demo Novel"
```

## Context

`context` calls `workflow.prepare_chapter_context`, saves JSON under
`context/chNNNN.context.json`, and writes a Markdown rendering under
`context/chNNNN.context.md`.

## Commit

`commit` reads a local chapter file only to compute hash and word count. It sends
the file path hint, hash, word count, summary, and optional structured event JSON
to `workflow.submit_chapter_commit`.

The local manuscript remains local.

## Review

Configure local review models through `.novel-os/model-config.json` profile
`review`. The older `.novel-os/review-models.json` format is still supported.
If no config exists, the local client falls back to a single default reviewer
that uses the local API key environment variables listed above:

```json
{
  "models": [
    {
      "id": "default-reviewer",
      "base_url": "https://api.openai.com/v1",
      "api_key_env": "OPENAI_API_KEY",
      "model": "gpt-4.1",
      "temperature": 0.2
    }
  ]
}
```

Start a review job:

```bash
python scripts/novel_local.py review-start --root . --chapter 1 --chapter-file chapters/volume_001/ch0001.md
```

The command writes `.novel-os/ch0001.review-job.json`. Use the returned `id` as
`review_job_id`.

Submit a model or manual report:

```bash
python scripts/novel_local.py review-submit --root . --review-job-id <uuid> --report-file reviews/volume_001/ch0001.report.json
```

Report JSON format:

```json
{
  "model_id": "manual-reviewer",
  "score": 82,
  "summary": "The opening hook works, but the protagonist motivation needs a clearer pressure point.",
  "findings": [
    {
      "dimension": "reader_pull",
      "severity": "medium",
      "target": "opening hook",
      "evidence": "The letter warns of danger but does not name a concrete cost.",
      "suggestion": "Add one immediate consequence if the protagonist ignores the auction."
    }
  ]
}
```

Aggregate all model reports:

```bash
python scripts/novel_local.py review-aggregate --root . --review-job-id <uuid>
```

Run configured models and submit reports automatically:

```bash
python scripts/novel_local.py review-run --root . --chapter 1 --chapter-file chapters/volume_001/ch0001.md --context-file context/ch0001.context.md
```

## Rule Evolution

`rules-evolve` reads a review aggregate and turns high-severity findings into
rule proposals. It defaults to `blocking` and `high` findings, writes proposals
as MCP rule proposals, and does not apply them unless `--auto-apply` is passed:

```bash
python scripts/novel_local.py rules-evolve --root . --review-job-id <uuid> --dry-run
python scripts/novel_local.py rules-evolve --root . --review-job-id <uuid>
```

Use `rules.list_proposals` and `rules.apply_proposal` through MCP or
`call-tool` to inspect and approve proposed rules.

## Skill Import

Convert `lingfengQAQ/webnovel-writer` or another compatible skill directory into
a structured Novel OS pack:

```bash
python scripts/novel_local.py webnovel-pack-build --source ./webnovel-writer --output ./webnovel-writer/novel-os-pack.json
```

Then import the local skill or reference directory into MCP reference storage:

```bash
python scripts/novel_local.py skill-import --root . --source ./webnovel-writer
```

If the source contains `novel-os-pack.json`, the importer reads structured
`items`, `rules`, and `review_councils`. Otherwise it scans `.md`, `.txt`, and
`.json`, `.csv`, `.yaml`, and `.yml` files and stores them as reference items.
Editable manuscript files still stay local; imported content is for shared
rules, templates, tropes, skills, and review configuration.

## Vector Index

Get memory chunks that do not yet have Qdrant vectors:

```bash
python scripts/novel_local.py vector-pending --root .
```

Generate embeddings locally using the user's own API key and upsert them in one
step:

```bash
python scripts/novel_local.py vector-run --root .
```

`vector-run` reads profile `embedding` from `.novel-os/model-config.json`. If no
config exists, it uses `text-embedding-3-small` with the same local API key
fallbacks as the writing and review profiles. Use `--dry-run` to only list
pending chunk ids.

Manual embedding upsert is still available. Save:

```json
{
  "chunk_id": "uuid",
  "vector": [0.01, 0.02, 0.03],
  "payload": {
    "source": "local-embedding-model"
  }
}
```

Upsert:

```bash
python scripts/novel_local.py vector-upsert --root . --embedding-file .novel-os/chunk.embedding.json
```

The MCP stores the vector in Qdrant and marks the memory chunk as indexed. The
API key used to create the embedding stays local.

## MCP URL

Use one of:

```text
http://127.0.0.1:8787/mcp
http://${NAS_HOST}:48083/mcp
```

The first URL is for SSH tunnel use. The second URL is the nginx reverse proxy
configured on the NAS LAN.
