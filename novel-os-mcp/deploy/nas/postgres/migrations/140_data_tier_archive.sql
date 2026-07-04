-- Phase 6: 性能、容灾与运维
-- 冷热归档任务表

-- =====================================================
-- 1. 创建数据分层配置表
-- =====================================================

CREATE TABLE IF NOT EXISTS data_tier_config (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    project_id UUID NOT NULL,
    tier VARCHAR(50) NOT NULL DEFAULT 'active',  -- 'active', 'recent', 'archive', 'deep_archive'
    table_name VARCHAR(255) NOT NULL,
    retention_days INTEGER DEFAULT 365,
    archive_condition JSONB DEFAULT '{}',  -- 归档条件
    auto_archive BOOLEAN DEFAULT TRUE,
    enabled BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW(),
    UNIQUE(project_id, tier, table_name)
);

-- 索引
CREATE INDEX IF NOT EXISTS idx_data_tier_config_project ON data_tier_config(project_id);
CREATE INDEX IF NOT EXISTS idx_data_tier_config_tier ON data_tier_config(tier);

-- =====================================================
-- 2. 创建归档历史记录表
-- =====================================================

CREATE TABLE IF NOT EXISTS archive_history (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    project_id UUID NOT NULL,
    table_name VARCHAR(255) NOT NULL,
    operation VARCHAR(50) NOT NULL,  -- 'archive', 'restore', 'delete', 'tier_change'
    from_tier VARCHAR(50),
    to_tier VARCHAR(50),
    record_count INTEGER DEFAULT 0,
    archive_path TEXT,  -- 归档文件路径
    status VARCHAR(50) DEFAULT 'success',  -- 'success', 'failed', 'partial'
    error_message TEXT,
    performed_by VARCHAR(255),
    metadata JSONB DEFAULT '{}',
    created_at TIMESTAMP DEFAULT NOW()
);

-- 索引
CREATE INDEX IF NOT EXISTS idx_archive_history_project ON archive_history(project_id);
CREATE INDEX IF NOT EXISTS idx_archive_history_table ON archive_history(table_name);
CREATE INDEX IF NOT EXISTS idx_archive_history_created ON archive_history(created_at DESC);

-- =====================================================
-- 3. 创建卷/章节归档状态表
-- =====================================================

CREATE TABLE IF NOT EXISTS volume_archive_status (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    project_id UUID NOT NULL,
    volume_no INTEGER NOT NULL,
    volume_title VARCHAR(500),
    status VARCHAR(50) DEFAULT 'active',  -- 'active', 'completed', 'archived'
    tier VARCHAR(50) DEFAULT 'active',  -- 'active', 'recent', 'archive', 'deep_archive'
    chapter_count INTEGER DEFAULT 0,
    word_count INTEGER DEFAULT 0,
    archived_at TIMESTAMP,
    archived_by VARCHAR(255),
    metadata JSONB DEFAULT '{}',
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW(),
    UNIQUE(project_id, volume_no)
);

-- 索引
CREATE INDEX IF NOT EXISTS idx_volume_archive_project ON volume_archive_status(project_id);
CREATE INDEX IF NOT EXISTS idx_volume_archive_status ON volume_archive_status(status);
CREATE INDEX IF NOT EXISTS idx_volume_archive_tier ON volume_archive_status(tier);

-- =====================================================
-- 4. 创建定时归档任务表
-- =====================================================

CREATE TABLE IF NOT EXISTS archive_schedules (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    project_id UUID,
    schedule_name VARCHAR(255) NOT NULL,
    schedule_type VARCHAR(50) NOT NULL,  -- 'daily', 'weekly', 'monthly', 'manual'
    cron_expression VARCHAR(100),
    tier_target VARCHAR(50) NOT NULL,  -- 'recent', 'archive', 'deep_archive'
    tables_to_archive JSONB DEFAULT '[]',  -- 要归档的表列表
    retention_days INTEGER DEFAULT 365,
    enabled BOOLEAN DEFAULT TRUE,
    last_run_at TIMESTAMP,
    next_run_at TIMESTAMP,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

-- 索引
CREATE INDEX IF NOT EXISTS idx_archive_schedules_project ON archive_schedules(project_id);
CREATE INDEX IF NOT EXISTS idx_archive_schedules_enabled ON archive_schedules(enabled);
CREATE INDEX IF NOT EXISTS idx_archive_schedules_next_run ON archive_schedules(next_run_at);

COMMENT ON TABLE data_tier_config IS '数据分层配置表';
COMMENT ON TABLE archive_history IS '归档历史记录表';
COMMENT ON TABLE volume_archive_status IS '卷归档状态表';
COMMENT ON TABLE archive_schedules IS '定时归档任务表';
