#!/usr/bin/env sh
set -eu

ROOT_DIR="$(CDPATH= cd -- "$(dirname -- "$0")/.." && pwd)"
cd "$ROOT_DIR"

if [ -f ./.env ]; then
  set -a
  . ./.env
  set +a
fi

BACKUP_ROOT="${BACKUP_ROOT:-./data/backups}"
RETENTION_DAYS="${RETENTION_DAYS:-14}"
POSTGRES_DB="${POSTGRES_DB:-novel_os}"
POSTGRES_USER="${POSTGRES_USER:-novel_os}"
timestamp="$(date +%Y%m%d-%H%M%S)"

mkdir -p "$BACKUP_ROOT/postgres" "$BACKUP_ROOT/qdrant" "$BACKUP_ROOT/config"

pg_target="$BACKUP_ROOT/postgres/${POSTGRES_DB}-${timestamp}.dump"
docker compose -f docker-compose.yml -f docker-compose.app.example.yml exec -T postgres \
  pg_dump --username "$POSTGRES_USER" --format custom "$POSTGRES_DB" > "$pg_target"
printf "Created PostgreSQL backup: %s\n" "$pg_target"

if [ -d ./data/qdrant ]; then
  qdrant_target="$BACKUP_ROOT/qdrant/qdrant-${timestamp}.tar.gz"
  tar -czf "$qdrant_target" -C ./data qdrant
  printf "Created Qdrant data archive: %s\n" "$qdrant_target"
fi

config_target="$BACKUP_ROOT/config/config-${timestamp}.tar.gz"
tar -czf "$config_target" \
  --exclude='./data' \
  --exclude='./.env' \
  docker-compose.yml docker-compose.app.example.yml postgres scripts config 2>/dev/null || true
printf "Created config archive: %s\n" "$config_target"

find "$BACKUP_ROOT" -type f \( -name "*.dump" -o -name "*.tar.gz" \) -mtime "+${RETENTION_DAYS}" -delete
