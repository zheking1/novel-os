# Novel OS NAS Deployment

This directory is intended to be copied to the Ubuntu NAS path:

```sh
/opt/novel-os
```

It deploys the infrastructure needed by the future `novel-os-mcp` service:

- PostgreSQL 16 with `pgvector`
- Qdrant for vector search
- Optional Adminer for PostgreSQL inspection
- Novel OS Web console for browser-based MCP administration
- Initial database schema for novel memory, rules, plots, and reviews
- Qdrant collection initialization script

## 1. Copy Files

Copy the contents of this directory to the NAS:

```sh
mkdir -p /opt/novel-os
cd /opt/novel-os
```

## 2. Configure Environment

```sh
cp .env.example .env
```

Edit `.env` and set strong values for:

```sh
POSTGRES_PASSWORD=
QDRANT_API_KEY=
REDIS_PASSWORD=
```

Keep all paths under `/opt/novel-os`.

## 3. Start PostgreSQL and Qdrant

```sh
docker compose up -d postgres qdrant
```

Check status:

```sh
docker compose ps
docker logs novel-postgres --tail 100
docker logs novel-qdrant --tail 100
```

## 4. Initialize Qdrant Collections

Run from `/opt/novel-os` after editing `.env`:

```sh
set -a
. ./.env
set +a
sh ./scripts/init-qdrant.sh
```

The script creates:

```text
novel_memory_chunks
novel_reference_chunks
```

## 5. Optional Adminer

Adminer is bound to localhost by default.

```sh
docker compose --profile admin up -d adminer
```

Open an SSH tunnel if you need to access it from another machine:

```sh
ssh -L 8088:127.0.0.1:8088 root@${NAS_HOST}
```

Then open:

```text
http://127.0.0.1:8088
```

## 6. MCP App And Web Console

Start or rebuild the MCP app and web console:

```sh
docker compose -f docker-compose.yml -f docker-compose.app.example.yml up -d
```

The MCP server binds to `${NOVEL_MCP_BIND_ADDR:-127.0.0.1}:${NOVEL_MCP_PORT:-8787}`.
The web console binds to `${NOVEL_WEB_BIND_ADDR:-127.0.0.1}:${NOVEL_WEB_PORT:-8790}`.
Keep both on localhost and expose them through nginx when needed.

## 7. Operations

Install or run `pg_dump` from a PostgreSQL client environment, then:

```sh
set -a
. ./.env
set +a
PGPASSWORD="$POSTGRES_PASSWORD" sh ./scripts/backup-postgres.sh
```

Backups are written under:

```text
./data/backups/postgres
```

For container-based backup of PostgreSQL plus a Qdrant data archive:

```sh
sh ./scripts/backup-all.sh
```

For health checks:

```sh
sh ./scripts/health-check.sh
```

For logs:

```sh
sh ./scripts/logs-tail.sh novel-os-mcp
sh ./scripts/logs-tail.sh novel-os-web
```

## Security Notes

- Do not commit `.env`.
- PostgreSQL, Qdrant, and Adminer bind to `127.0.0.1` by default.
- Expose services to the LAN only when necessary.
- Do not give writing agents direct PostgreSQL or filesystem access.
- Route novel operations through `novel-os-mcp` once implemented.
