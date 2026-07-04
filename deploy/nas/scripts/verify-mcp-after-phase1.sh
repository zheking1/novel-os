#!/usr/bin/env sh
set -eu

cd /opt/novel-os

docker compose -f docker-compose.yml -f docker-compose.app.example.yml ps novel-os-mcp
docker logs novel-os-mcp --tail 80

docker compose -f docker-compose.yml -f docker-compose.app.example.yml exec -T novel-os-mcp python - <<'PY'
from novel_os_mcp.main import mcp  # noqa: F401

print("novel_os_mcp.main import ok")
PY
