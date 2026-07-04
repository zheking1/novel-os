-- =============================================
-- 191_knowledge_to_canon.sql
-- 将 knowledge_base 数据迁移到 canon_documents
-- =============================================

-- 使用 default 项目作为系统知识库的宿主项目
-- 项目 ID: 00000000-0000-0000-0000-000000000002
-- 管理员用户 ID: 26180c6c-8da5-4084-b30d-5bdc77d36692

-- 插入 knowledge_base 数据到 canon_documents
INSERT INTO canon_documents (
    project_id,
    doc_type,
    key,
    title,
    content,
    content_hash,
    status,
    version,
    scope,
    review_status,
    source_type,
    source_id,
    related_rule_ids,
    metadata,
    created_by,
    updated_by
)
SELECT
    '00000000-0000-0000-0000-000000000002'::uuid AS project_id,
    COALESCE(c.slug, 'knowledge_qa') AS doc_type,
    kb.code AS key,
    kb.title,
    kb.content,
    encode(digest(kb.content, 'md5'), 'hex') AS content_hash,
    kb.status,
    1 AS version,
    '{}'::jsonb AS scope,
    'approved' AS review_status,
    'opencode' AS source_type,
    kb.code AS source_id,
    ARRAY[]::text[] AS related_rule_ids,
    jsonb_build_object(
        'applicable_genres', kb.applicable_genres,
        'applicable_skills', kb.applicable_skills,
        'level', kb.level,
        'source_file', kb.source_file,
        'summary', kb.summary,
        'detail', kb.detail,
        'examples', kb.examples,
        'counter_examples', kb.counter_examples,
        'original_metadata', kb.metadata
    ) AS metadata,
    '26180c6c-8da5-4084-b30d-5bdc77d36692'::uuid AS created_by,
    '26180c6c-8da5-4084-b30d-5bdc77d36692'::uuid AS updated_by
FROM knowledge_base kb
LEFT JOIN categories c ON c.id = kb.category_id
WHERE kb.source = 'opencode'
  AND NOT EXISTS (
    SELECT 1 FROM canon_documents cd
    WHERE cd.project_id = '00000000-0000-0000-0000-000000000002'
      AND cd.doc_type = COALESCE(c.slug, 'knowledge_qa')
      AND cd.key = kb.code
);

-- 统计结果
SELECT 'Migration completed' AS status;

SELECT
    (SELECT COUNT(*) FROM knowledge_base WHERE source = 'opencode') AS source_count,
    (SELECT COUNT(*) FROM canon_documents WHERE source_type = 'opencode') AS migrated_count;

-- 按 doc_type 统计
SELECT doc_type, COUNT(*) as count
FROM canon_documents
WHERE source_type = 'opencode'
GROUP BY doc_type
ORDER BY count DESC;
