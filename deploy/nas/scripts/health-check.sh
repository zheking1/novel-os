#!/usr/bin/env sh
set -eu

ROOT_DIR="$(CDPATH= cd -- "$(dirname -- "$0")/.." && pwd)"
cd "$ROOT_DIR"

if [ -f ./.env ]; then
  set -a
  . ./.env
  set +a
fi

COMPOSE_FILES="-f docker-compose.yml -f docker-compose.app.example.yml"
MCP_URL="http://${NOVEL_MCP_BIND_ADDR:-127.0.0.1}:${NOVEL_MCP_PORT:-8787}/mcp"
WEB_URL="http://${NOVEL_WEB_BIND_ADDR:-127.0.0.1}:${NOVEL_WEB_PORT:-8790}/health"
QDRANT_URL="http://${QDRANT_BIND_ADDR:-127.0.0.1}:${QDRANT_HTTP_PORT:-6333}/collections"

docker compose $COMPOSE_FILES ps

printf "\nPostgreSQL:\n"
docker compose $COMPOSE_FILES exec -T postgres pg_isready -U "${POSTGRES_USER:-novel_os}" -d "${POSTGRES_DB:-novel_os}"

printf "\nQdrant:\n"
qdrant_header=""
if [ -n "${QDRANT_API_KEY:-}" ]; then
  qdrant_header="-H api-key:${QDRANT_API_KEY}"
fi
curl -fsS $qdrant_header "$QDRANT_URL" >/dev/null && printf "ok %s\n" "$QDRANT_URL"

printf "\nMCP port:\n"
curl -sS -o /dev/null -w "http %{http_code} reachable\n" "$MCP_URL" || true

printf "\nWeb:\n"
curl -fsS "$WEB_URL"
printf "\n"
