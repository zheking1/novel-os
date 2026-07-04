#!/usr/bin/env sh
set -eu

POSTGRES_DB="${POSTGRES_DB:-novel_os}"
POSTGRES_USER="${POSTGRES_USER:-novel_os}"

for file in ./postgres/init/*.sql; do
  printf "Applying %s\n" "$file"
  docker compose exec -T postgres psql \
    --username "$POSTGRES_USER" \
    --dbname "$POSTGRES_DB" \
    --file - < "$file"
done

printf "Schema apply complete.\n"

