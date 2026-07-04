-- Phase 5: 审查闭环与规则演化
-- 增强审查任务生命周期和修订任务表

-- =====================================================
-- 1. 增强 review_jobs 表 - 添加更多状态和字段
-- =====================================================

ALTER TABLE review_jobs ADD COLUMN IF NOT EXISTS status_reason TEXT;
ALTER TABLE review_jobs ADD COLUMN IF NOT EXISTS blocked_at TIMESTAMP;
ALTER TABLE review_jobs ADD COLUMN IF NOT EXISTS resolved_at TIMESTAMP;
ALTER TABLE review_jobs ADD COLUMN IF NOT EXISTS aggregated_at TIMESTAMP;

-- 更新状态约束
DO $$
BEGIN
    IF EXISTS (
        SELECT 1 FROM pg_constraint
        WHERE conname = 'review_jobs_status_check'
    ) THEN
        ALTER TABLE review_jobs DROP CONSTRAINT review_jobs_status_check;
    END IF;
END $$;

ALTER TABLE review_jobs ADD CONSTRAINT review_jobs_status_check
    CHECK (status IN ('pending', 'running', 'complete', 'failed', 'aggregated', 'blocked', 'resolved'));

-- =====================================================
-- 2. 创建 revision_tasks 状态历史表
-- =====================================================

CREATE TABLE IF NOT EXISTS revision_task_history (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    revision_task_id UUID NOT NULL,
    old_status VARCHAR(50),
    new_status VARCHAR(50) NOT NULL,
    changed_by VARCHAR(255),
    change_reason TEXT,
    metadata JSONB,
    created_at TIMESTAMP DEFAULT NOW()
);

-- =====================================================
-- 3. 创建审查模型质量评估表
-- =====================================================

CREATE TABLE IF NOT EXISTS review_model_metrics (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    model_id VARCHAR(255) NOT NULL,
    project_id UUID NOT NULL,
    total_reports INTEGER DEFAULT 0,
    human_confirmed INTEGER DEFAULT 0,
    human_rejected INTEGER DEFAULT 0,
    rule_proposals_created INTEGER DEFAULT 0,
    rule_proposals_approved INTEGER DEFAULT 0,
    revision_tasks_created INTEGER DEFAULT 0,
    revision_tasks_completed INTEGER DEFAULT 0,
    agreement_with_consensus FLOAT DEFAULT 0,
    average_score FLOAT,
    last_calculated_at TIMESTAMP,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW(),
    UNIQUE(model_id, project_id)
);

-- =====================================================
-- 4. 创建规则提案表
-- =====================================================

CREATE TABLE IF NOT EXISTS rule_proposals (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    project_id UUID NOT NULL,
    chapter_id UUID,
    review_job_id UUID,
    revision_task_id UUID,
    proposal_type VARCHAR(50) NOT NULL,  -- 'style', 'canon', 'character', 'plot', 'lesson'
    title VARCHAR(500) NOT NULL,
    content TEXT NOT NULL,
    confidence FLOAT DEFAULT 0.5,
    source_model_id VARCHAR(255),
    source_finding_key TEXT,
    status VARCHAR(50) DEFAULT 'pending',  -- 'pending', 'approved', 'rejected', 'auto_applied'
    reviewed_by VARCHAR(255),
    reviewed_at TIMESTAMP,
    review_notes TEXT,
    auto_apply BOOLEAN DEFAULT FALSE,
    auto_applied_at TIMESTAMP,
    created_by VARCHAR(255),
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

-- 索引
CREATE INDEX IF NOT EXISTS idx_rule_proposals_status ON rule_proposals(status);
CREATE INDEX IF NOT EXISTS idx_rule_proposals_type ON rule_proposals(proposal_type);
CREATE INDEX IF NOT EXISTS idx_rule_proposals_project ON rule_proposals(project_id);

-- =====================================================
-- 5. 创建审查报告质量评估索引
-- =====================================================

CREATE INDEX IF NOT EXISTS idx_review_model_metrics_project ON review_model_metrics(project_id);
CREATE INDEX IF NOT EXISTS idx_revision_task_history_task ON revision_task_history(revision_task_id);

COMMENT ON TABLE review_jobs IS '审查任务表 - 管理审查任务的完整生命周期';
COMMENT ON COLUMN review_jobs.status IS '状态: pending/running/complete/failed/aggregated/blocked/resolved';
COMMENT ON TABLE review_model_metrics IS '审查模型质量评估表 - 追踪每个模型的表现';
COMMENT ON TABLE rule_proposals IS '规则提案表 - 从审查中发现的问题生成规则提案';
