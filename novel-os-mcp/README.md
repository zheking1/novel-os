# novel-os-mcp

Single MCP server for the Novel OS architecture.

The server stores central intelligence:

- Rules and canon
- Character/world state projections
- Foreshadowing and plot state
- Chapter commits and summaries
- Review reports and rule proposals
- Reference templates and search metadata

Generated manuscripts, outlines, plans, and human-editable review documents stay
in each user's local project directory.

## Environment

```env
DATABASE_URL=postgresql://novel_os:password@postgres:5432/novel_os
QDRANT_URL=http://qdrant:6333
QDRANT_API_KEY=...
REDIS_HOST=${NAS_HOST}
REDIS_PORT=6379
REDIS_DB=0
REDIS_PASSWORD=...
NOVEL_OS_AUTH_MODE=token
NOVEL_OS_DEV_USER=admin
NOVEL_OS_DEV_WORKSPACE=default
NOVEL_OS_DEV_SCOPES=admin,read,write
```

`NOVEL_OS_AUTH_MODE=dev` is for early local/NAS bring-up only. Production should
use token authentication.
