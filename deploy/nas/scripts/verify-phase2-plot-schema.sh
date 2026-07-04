#!/usr/bin/env sh
set -eu

cd /opt/novel-os

docker compose exec -T postgres psql --username novel_os --dbname novel_os <<'SQL'
SELECT table_name, column_name
FROM information_schema.columns
WHERE table_schema = 'public'
  AND (
    (table_name = 'volumes' AND column_name IN (
      'start_chapter_no', 'end_chapter_no', 'summary', 'goals'
    ))
    OR (table_name = 'plot_threads' AND column_name IN (
      'volume_no', 'start_chapter_no', 'current_chapter_no',
      'last_advanced_chapter_no', 'expected_next_chapter_no',
      'stalled_after_chapters', 'related_entity_ids', 'related_foreshadowing_ids'
    ))
  )
ORDER BY table_name, column_name;
SQL
