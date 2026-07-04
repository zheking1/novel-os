# Run

## Docker Compose On NAS

Copy `novel-os-mcp/` under:

```text
/opt/novel-os/novel-os-mcp
```

Then run:

```sh
cd /opt/novel-os
docker compose -f docker-compose.yml -f docker-compose.app.example.yml up -d --build novel-os-mcp
```

For first bring-up you can use:

```env
NOVEL_OS_AUTH_MODE=dev
NOVEL_OS_DEV_USER=admin
NOVEL_OS_DEV_WORKSPACE=default
```

Before exposing the service through nginx, create an admin token while still in
`dev` mode, store it locally, then switch:

```env
NOVEL_OS_AUTH_MODE=token
```

The MCP server then requires `Authorization: Bearer <token>` on every tool call.

## Local Dev

```sh
cd novel-os-mcp
python -m venv .venv
. .venv/bin/activate
pip install -e .
novel-os-mcp
```
