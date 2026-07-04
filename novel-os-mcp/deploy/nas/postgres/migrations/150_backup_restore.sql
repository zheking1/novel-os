-- Phase 6: 性能、容灾与运维
-- 备份恢复相关表

-- =====================================================
-- 1. 创建备份记录表
-- =====================================================

CREATE TABLE IF NOT EXISTS backup_records (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    project_id UUID,
    backup_type VARCHAR(50) NOT NULL,  -- 'full', 'incremental', 'config', 'project_export'
    storage_path TEXT,
    storage_type VARCHAR(50) DEFAULT 'local',  -- 'local', 'nas', 'cloud'
    status VARCHAR(50) DEFAULT 'pending',  -- 'pending', 'in_progress', 'completed', 'failed'
    file_size_bytes BIGINT,
    file_count INTEGER,
    checksum VARCHAR(255),
    compression_type VARCHAR(50),  -- 'gzip', 'bz2', 'xz', None
    started_at TIMESTAMP,
    completed_at TIMESTAMP,
    error_message TEXT,
    metadata JSONB DEFAULT '{}',
    created_at TIMESTAMP DEFAULT NOW()
);

-- 索引
CREATE INDEX IF NOT EXISTS idx_backup_records_project ON backup_records(project_id);
CREATE INDEX IF NOT EXISTS idx_backup_records_status ON backup_records(status);
CREATE INDEX IF NOT EXISTS idx_backup_records_type ON backup_records(backup_type);
CREATE INDEX IF NOT EXISTS idx_backup_records_created ON backup_records(created_at DESC);

-- =====================================================
-- 2. 创建备份计划表
-- =====================================================

CREATE TABLE IF NOT EXISTS backup_schedules (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    schedule_name VARCHAR(255) NOT NULL,
    project_id UUID,
    backup_type VARCHAR(50) NOT NULL DEFAULT 'incremental',
    schedule_type VARCHAR(50) NOT NULL DEFAULT 'daily',  -- 'hourly', 'daily', 'weekly', 'manual'
    cron_expression VARCHAR(100),
    retention_count INTEGER DEFAULT 7,  -- 保留多少个备份
    retention_days INTEGER DEFAULT 30,  -- 保留多少天
    storage_path TEXT,
    storage_type VARCHAR(50) DEFAULT 'local',
    enabled BOOLEAN DEFAULT TRUE,
    last_run_at TIMESTAMP,
    next_run_at TIMESTAMP,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

-- 索引
CREATE INDEX IF NOT EXISTS idx_backup_schedules_project ON backup_schedules(project_id);
CREATE INDEX IF NOT EXISTS idx_backup_schedules_enabled ON backup_schedules(enabled);

-- =====================================================
-- 3. 创建恢复记录表
-- =====================================================

CREATE TABLE IF NOT EXISTS restore_records (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    backup_record_id UUID NOT NULL,
    project_id UUID NOT NULL,
    restore_type VARCHAR(50) NOT NULL DEFAULT 'full',  -- 'full', 'partial', 'table'
    status VARCHAR(50) DEFAULT 'pending',  -- 'pending', 'in_progress', 'completed', 'failed'
    tables_restored JSONB DEFAULT '[]',
    records_restored_count BIGINT,
    started_at TIMESTAMP,
    completed_at TIMESTAMP,
    error_message TEXT,
    performed_by VARCHAR(255),
    metadata JSONB DEFAULT '{}',
    created_at TIMESTAMP DEFAULT NOW()
);

-- 索引
CREATE INDEX IF NOT EXISTS idx_restore_records_project ON restore_records(project_id);
CREATE INDEX IF NOT EXISTS idx_restore_records_backup ON restore_records(backup_record_id);
CREATE INDEX IF NOT EXISTS idx_restore_records_status ON restore_records(status);

-- =====================================================
-- 4. 创建项目导出记录表
-- =====================================================

CREATE TABLE IF NOT EXISTS project_export_records (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    project_id UUID NOT NULL,
    export_format VARCHAR(50) NOT NULL DEFAULT 'json',  -- 'json', 'jsonl', 'csv', 'zip'
    export_type VARCHAR(50) NOT NULL DEFAULT 'full',  -- 'full', 'incremental', 'settings_only'
    storage_path TEXT,
    file_size_bytes BIGINT,
    status VARCHAR(50) DEFAULT 'pending',
    started_at TIMESTAMP,
    completed_at TIMESTAMP,
    error_message TEXT,
    metadata JSONB DEFAULT '{}',
    created_at TIMESTAMP DEFAULT NOW()
);

-- 索引
CREATE INDEX IF NOT EXISTS idx_project_export_project ON project_export_records(project_id);
CREATE INDEX IF NOT EXISTS idx_project_export_status ON project_export_records(status);

COMMENT ON TABLE backup_records IS '备份记录表';
COMMENT ON TABLE backup_schedules IS '备份计划表';
COMMENT ON TABLE restore_records IS '恢复记录表';
COMMENT ON TABLE project_export_records IS '项目导出记录表';
