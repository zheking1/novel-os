#!/usr/bin/env sh
set -eu

ROOT_DIR="$(CDPATH= cd -- "$(dirname -- "$0")/.." && pwd)"
cd "$ROOT_DIR"

LINES="${LINES:-120}"
SERVICE="${1:-novel-os-mcp}"

docker compose -f docker-compose.yml -f docker-compose.app.example.yml logs --tail "$LINES" "$SERVICE"
