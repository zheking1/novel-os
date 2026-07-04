#!/usr/bin/env sh
set -eu

cd /opt/novel-os

docker compose exec -T postgres psql --username novel_os --dbname novel_os <<'SQL'
SELECT table_name
FROM information_schema.tables
WHERE table_schema = 'public'
  AND table_name IN ('canon_documents', 'canon_document_versions')
ORDER BY table_name;

SELECT table_name, column_name
FROM information_schema.columns
WHERE table_schema = 'public'
  AND (
    (table_name = 'state_snapshots' AND column_name IN ('effective_chapter_no', 'expire_chapter_no', 'duration_type', 'source_type', 'metadata'))
    OR (table_name = 'foreshadowing' AND column_name IN ('parent_foreshadowing_id', 'layer', 'must_payoff', 'payoff_deadline_chapter', 'overdue_policy'))
    OR (table_name = 'canon_rules' AND column_name IN ('scope_type', 'scope_config', 'priority', 'is_temporary', 'conflict_policy'))
  )
ORDER BY table_name, column_name;
SQL
