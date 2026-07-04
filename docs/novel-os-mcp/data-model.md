# Novel OS MCP Data Model

This document defines the main tables needed by `novel-os-mcp`.

The existing NAS schema is a foundation. It should be expanded before the MCP
server is implemented.

## Identity And Permissions

### users

```text
id uuid pk
username text unique
display_name text
email text unique nullable
password_hash text nullable
status text active|disabled
created_at timestamptz
updated_at timestamptz
```

### workspaces

```text
id uuid pk
slug text unique
name text
owner_user_id uuid fk users
settings jsonb
created_at timestamptz
updated_at timestamptz
```

### workspace_members

```text
workspace_id uuid fk workspaces
user_id uuid fk users
role text owner|editor|reviewer|reader
created_at timestamptz
primary key(workspace_id, user_id)
```

### api_tokens

```text
id uuid pk
user_id uuid fk users
workspace_id uuid fk workspaces nullable
name text
token_hash text unique
scopes text[]
expires_at timestamptz nullable
last_used_at timestamptz nullable
created_at timestamptz
revoked_at timestamptz nullable
```

## Projects And Local Bindings

### projects

```text
id uuid pk
workspace_id uuid fk workspaces
slug text
title text
description text
status text active|archived
settings jsonb
created_at timestamptz
updated_at timestamptz
unique(workspace_id, slug)
```

### project_members

```text
project_id uuid fk projects
user_id uuid fk users
role text owner|editor|reviewer|reader
created_at timestamptz
primary key(project_id, user_id)
```

### local_project_bindings

MCP does not manage local paths directly. This table records client-reported
bindings and file hashes for sync and audit.

```text
id uuid pk
project_id uuid fk projects
user_id uuid fk users
client_id text
local_root_hint text
manifest jsonb
last_sync_at timestamptz nullable
created_at timestamptz
updated_at timestamptz
unique(project_id, user_id, client_id)
```

## Chapters And Commits

### chapters

```text
id uuid pk
project_id uuid fk projects
chapter_no int
volume_no int nullable
title text nullable
status text planned|drafted|reviewed|accepted|published
local_path_hint text nullable
content_hash text nullable
word_count int
created_at timestamptz
updated_at timestamptz
unique(project_id, chapter_no)
```

### chapter_commits

The commit is the structured accounting record for a chapter. It is not the
whole manuscript.

```text
id uuid pk
project_id uuid fk projects
chapter_id uuid fk chapters
commit_no int
payload jsonb
accepted bool
accepted_by uuid fk users nullable
accepted_at timestamptz nullable
created_by uuid fk users nullable
created_at timestamptz
unique(chapter_id, commit_no)
```

Required payload fields:

```json
{
  "summary": "short chapter summary",
  "events": [],
  "character_state_changes": [],
  "world_state_changes": [],
  "new_facts": [],
  "foreshadowing_changes": [],
  "plot_thread_changes": [],
  "rule_warnings": [],
  "next_chapter_hooks": [],
  "local_files": []
}
```

## Memory And Projection

### chapter_summaries

```text
id uuid pk
project_id uuid fk projects
chapter_id uuid fk chapters nullable
summary_type text chapter|ten_chapter|arc|volume|mega_arc|book
range_start int nullable
range_end int nullable
content text
metadata jsonb
created_at timestamptz
```

### events

```text
id uuid pk
project_id uuid fk projects
chapter_id uuid fk chapters nullable
event_order int nullable
title text nullable
summary text
characters text[]
locations text[]
causes jsonb
consequences jsonb
metadata jsonb
created_at timestamptz
```

### state_entities

Generic registry for things that can have projected state.

```text
id uuid pk
project_id uuid fk projects
entity_type text character|location|item|faction|world
name text
aliases text[]
profile jsonb
created_at timestamptz
updated_at timestamptz
unique(project_id, entity_type, name)
```

### state_snapshots

```text
id uuid pk
project_id uuid fk projects
entity_id uuid fk state_entities
chapter_id uuid fk chapters nullable
state jsonb
is_current bool
source_commit_id uuid fk chapter_commits nullable
created_at timestamptz
```

## Plot

### volumes

```text
id uuid pk
project_id uuid fk projects
volume_no int
title text
outline text
status text planned|active|complete
metadata jsonb
unique(project_id, volume_no)
```

### plot_threads

```text
id uuid pk
project_id uuid fk projects
key text
title text
thread_type text main|side|romance|mystery|enemy|growth
status text open|developing|resolved|paused|abandoned
importance text low|medium|high|critical
metadata jsonb
created_at timestamptz
updated_at timestamptz
unique(project_id, key)
```

### chapter_plans

```text
id uuid pk
project_id uuid fk projects
chapter_id uuid fk chapters nullable
chapter_no int
plan jsonb
status text planned|used|superseded
created_by uuid fk users nullable
created_at timestamptz
updated_at timestamptz
```

### foreshadowing

```text
id uuid pk
project_id uuid fk projects
key text
title text
status text planted|developing|misdirected|ready_to_payoff|paid_off|abandoned
importance text low|medium|high|critical
planted_chapter_id uuid nullable
payoff_chapter_id uuid nullable
expected_payoff_range text nullable
payload jsonb
created_at timestamptz
updated_at timestamptz
unique(project_id, key)
```

## Rules

### canon_rules

```text
id uuid pk
project_id uuid fk projects
rule_key text
rule_type text canon|character|plot|review|style|lesson|forbidden|reveal_lock
scope text global|volume|arc|chapter|character
title text
content text
severity text info|warning|error|critical
status text active|disabled|superseded
version int
metadata jsonb
created_at timestamptz
updated_at timestamptz
unique(project_id, rule_key)
```

### rule_proposals

```text
id uuid pk
project_id uuid fk projects
source_type text review|user|commit|import
source_id uuid nullable
proposal_type text create|update|disable
target_rule_id uuid nullable
title text
content text
confidence numeric
agreement jsonb
status text proposed|auto_applied|approved|rejected|superseded
created_by uuid nullable
approved_by uuid nullable
created_at timestamptz
resolved_at timestamptz nullable
```

### rule_versions

```text
id uuid pk
project_id uuid fk projects
rule_id uuid fk canon_rules
version int
content text
change_reason text
source text
created_at timestamptz
unique(rule_id, version)
```

## Review

### review_council_configs

```text
id uuid pk
project_id uuid fk projects
name text
config jsonb
is_active bool
created_at timestamptz
updated_at timestamptz
```

### review_jobs

```text
id uuid pk
project_id uuid fk projects
chapter_id uuid fk chapters
status text pending|running|complete|failed
config jsonb
created_by uuid nullable
created_at timestamptz
updated_at timestamptz
```

### review_reports

```text
id uuid pk
project_id uuid fk projects
review_job_id uuid fk review_jobs
chapter_id uuid fk chapters
model_id text nullable
report_type text model|consensus
score numeric
findings jsonb
summary text
created_at timestamptz
```

### revision_tasks

```text
id uuid pk
project_id uuid fk projects
chapter_id uuid fk chapters
review_job_id uuid nullable
title text
description text
severity text low|medium|high|blocking
status text open|accepted|dismissed|done
metadata jsonb
created_at timestamptz
updated_at timestamptz
```

## Reference Library

### reference_sources

```text
id uuid pk
workspace_id uuid fk workspaces nullable
project_id uuid fk projects nullable
source_type text webnovel_writer|manual|import
name text
source_uri text
license text nullable
metadata jsonb
created_at timestamptz
updated_at timestamptz
```

### reference_items

```text
id uuid pk
source_id uuid fk reference_sources
project_id uuid fk projects nullable
item_type text genre_template|writing_pattern|scene_pattern|trope|rubric|agent_prompt
key text
title text
content text
metadata jsonb
created_at timestamptz
updated_at timestamptz
```

## Search

### memory_chunks

```text
id uuid pk
project_id uuid fk projects
source_type text chapter_summary|event|state|rule|reference|review|lesson
source_id uuid nullable
chunk_key text
content text
qdrant_collection text nullable
qdrant_point_id text nullable
metadata jsonb
search_vector tsvector generated
created_at timestamptz
unique(project_id, chunk_key)
```

## Audit

### audit_logs

```text
id uuid pk
workspace_id uuid nullable
project_id uuid nullable
user_id uuid nullable
action text
resource_type text
resource_id uuid nullable
payload jsonb
created_at timestamptz
```

