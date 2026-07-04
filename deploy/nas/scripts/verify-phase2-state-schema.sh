#!/usr/bin/env sh
set -eu

cd /opt/novel-os

docker compose exec -T postgres psql --username novel_os --dbname novel_os <<'SQL'
SELECT table_name
FROM information_schema.tables
WHERE table_schema = 'public'
  AND table_name = 'entity_relationships';

SELECT table_name, column_name
FROM information_schema.columns
WHERE table_schema = 'public'
  AND (
    (table_name = 'state_entities' AND column_name IN (
      'lifecycle_status', 'importance', 'tags', 'first_seen_chapter_no',
      'last_seen_chapter_no', 'source_type', 'source_id', 'metadata'
    ))
    OR (table_name = 'entity_relationships' AND column_name IN (
      'source_entity_id', 'target_entity_id', 'relation_type', 'attitude',
      'intensity', 'known_by_reader', 'status', 'source_chapter_no', 'metadata'
    ))
  )
ORDER BY table_name, column_name;
SQL
