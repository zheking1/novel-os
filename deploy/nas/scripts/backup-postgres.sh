#!/usr/bin/env sh
set -eu

BACKUP_DIR="${BACKUP_DIR:-./data/backups/postgres}"
POSTGRES_HOST="${POSTGRES_HOST:-127.0.0.1}"
POSTGRES_PORT="${POSTGRES_PORT:-5432}"
POSTGRES_DB="${POSTGRES_DB:-novel_os}"
POSTGRES_USER="${POSTGRES_USER:-novel_os}"
RETENTION_DAYS="${RETENTION_DAYS:-14}"

mkdir -p "$BACKUP_DIR"
timestamp="$(date +%Y%m%d-%H%M%S)"
target="${BACKUP_DIR}/${POSTGRES_DB}-${timestamp}.dump"

pg_dump \
  --host "$POSTGRES_HOST" \
  --port "$POSTGRES_PORT" \
  --username "$POSTGRES_USER" \
  --format custom \
  --file "$target" \
  "$POSTGRES_DB"

find "$BACKUP_DIR" -type f -name "${POSTGRES_DB}-*.dump" -mtime "+${RETENTION_DAYS}" -delete
printf "Created backup: %s\n" "$target"

