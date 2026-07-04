-- Phase 6+: 性能优化 - 新增索引和查询优化

-- =====================================================
-- 1. Projects 表优化
-- =====================================================

-- 复合索引：加速项目列表查询
CREATE INDEX IF NOT EXISTS idx_projects_workspace_status ON projects(workspace_id, status);

-- =====================================================
-- 2. Chapters 表优化
-- =====================================================

-- 复合索引：加速按状态查询章节
CREATE INDEX IF NOT EXISTS idx_chapters_project_status ON chapters(project_id, status);

-- =====================================================
-- 3. Events 表优化
-- =====================================================

-- 复合索引：加速按角色和地点查询事件
CREATE INDEX IF NOT EXISTS idx_events_characters ON events USING GIN(characters);
CREATE INDEX IF NOT EXISTS idx_events_locations ON events USING GIN(locations);

-- =====================================================
-- 4. Characters 表优化
-- =====================================================

-- 索引：加速按角色查询
CREATE INDEX IF NOT EXISTS idx_characters_project_role ON characters(project_id, role);

-- =====================================================
-- 5. Canon Rules 表优化
-- =====================================================

-- 复合索引：加速规则查询
CREATE INDEX IF NOT EXISTS idx_canon_rules_project_severity ON canon_rules(project_id, severity);

-- =====================================================
-- 6. Foreshadowing 表优化
-- =====================================================

-- 复合索引：加速按状态和重要性查询
CREATE INDEX IF NOT EXISTS idx_foreshadowing_planted ON foreshadowing(project_id, planted_chapter_id);
CREATE INDEX IF NOT EXISTS idx_foreshadowing_payoff ON foreshadowing(project_id, payoff_chapter_id);

-- =====================================================
-- 7. Review Jobs 表优化
-- =====================================================

-- 复合索引：加速审查任务查询
CREATE INDEX IF NOT EXISTS idx_review_jobs_project_status ON review_jobs(project_id, status);

-- =====================================================
-- 8. Review Reports 表优化
-- =====================================================

-- 复合索引：加速审查报告查询
CREATE INDEX IF NOT EXISTS idx_review_reports_job ON review_reports(review_job_id);
CREATE INDEX IF NOT EXISTS idx_review_reports_chapter ON review_reports(chapter_id, report_type);

-- =====================================================
-- 9. Canon Documents 表优化
-- =====================================================

-- 复合索引：加速文档查询
CREATE INDEX IF NOT EXISTS idx_canon_docs_project_type ON canon_documents(project_id, doc_type);

-- =====================================================
-- 10. Memory Chunks 表优化
-- =====================================================

-- 复合索引：加速按源类型查询
CREATE INDEX IF NOT EXISTS idx_memory_chunks_source ON memory_chunks(project_id, source_type);

-- =====================================================
-- 11. User / Workspace / Member 表优化
-- =====================================================

-- 复合索引：加速成员查询
CREATE INDEX IF NOT EXISTS idx_workspace_members_workspace ON workspace_members(workspace_id, role);
CREATE INDEX IF NOT EXISTS idx_project_members_project ON project_members(project_id, role);

-- =====================================================
-- 12. Cache 表优化
-- =====================================================

-- 复合索引：加速缓存查询
CREATE INDEX IF NOT EXISTS idx_context_cache_project ON context_cache(project_id);
CREATE INDEX IF NOT EXISTS idx_context_cache_expiry ON context_cache(expires_at);

-- =====================================================
-- 13. Chapter Plans 表优化
-- =====================================================

-- 复合索引：加速章节计划查询
CREATE INDEX IF NOT EXISTS idx_chapter_plans_project_status ON chapter_plans(project_id, status);

-- =====================================================
-- 14. Prompt Templates 表优化
-- =====================================================

-- 复合索引：加速模板查询
CREATE INDEX IF NOT EXISTS idx_prompt_templates_project ON prompt_templates(project_id);
CREATE INDEX IF NOT EXISTS idx_prompt_templates_type ON prompt_templates(template_type);
CREATE INDEX IF NOT EXISTS idx_prompt_templates_genre ON prompt_templates(genre);

-- =====================================================
-- 15. Update statistics for query planner
-- =====================================================

ANALYZE projects;
ANALYZE chapters;
ANALYZE events;
ANALYZE characters;
ANALYZE canon_rules;
ANALYZE foreshadowing;
ANALYZE review_jobs;
ANALYZE review_reports;
ANALYZE memory_chunks;
ANALYZE canon_documents;

COMMENT ON TABLE vector_index_tasks IS '性能优化：新增索引加速查询';
