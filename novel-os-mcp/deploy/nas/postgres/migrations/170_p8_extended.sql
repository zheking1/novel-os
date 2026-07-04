-- Phase 8: P2 远期扩展
-- 离线写作增强和语音输入

-- =====================================================
-- 1. 创建离线同步会话表
-- =====================================================

CREATE TABLE IF NOT EXISTS offline_sync_sessions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    project_id UUID NOT NULL,
    session_name VARCHAR(255) NOT NULL,
    description TEXT,
    status VARCHAR(50) DEFAULT 'active',  -- 'active', 'syncing', 'completed', 'partial', 'failed'
    total_changes INTEGER DEFAULT 0,
    synced_changes INTEGER DEFAULT 0,
    created_by VARCHAR(255),
    created_at TIMESTAMP DEFAULT NOW(),
    synced_at TIMESTAMP,
    updated_at TIMESTAMP DEFAULT NOW()
);

-- 索引
CREATE INDEX IF NOT EXISTS idx_offline_sync_sessions_project ON offline_sync_sessions(project_id);
CREATE INDEX IF NOT EXISTS idx_offline_sync_sessions_status ON offline_sync_sessions(status);

-- =====================================================
-- 2. 创建离线变更队列表
-- =====================================================

CREATE TABLE IF NOT EXISTS offline_change_queue (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    session_id UUID NOT NULL,
    change_type VARCHAR(50) NOT NULL,  -- 'upsert', 'delete', 'archive'
    entity_type VARCHAR(50) NOT NULL,  -- 'canon', 'entity', 'foreshadow', 'rule', etc.
    entity_id UUID NOT NULL,
    change_data JSONB DEFAULT '{}',
    status VARCHAR(50) DEFAULT 'pending',  -- 'pending', 'synced', 'failed', 'conflict'
    conflict_reason TEXT,
    created_at TIMESTAMP DEFAULT NOW(),
    synced_at TIMESTAMP
);

-- 索引
CREATE INDEX IF NOT EXISTS idx_offline_change_queue_session ON offline_change_queue(session_id);
CREATE INDEX IF NOT EXISTS idx_offline_change_queue_status ON offline_change_queue(status);

-- =====================================================
-- 3. 创建语音草稿表
-- =====================================================

CREATE TABLE IF NOT EXISTS voice_drafts (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    project_id UUID NOT NULL,
    chapter_no INTEGER,
    audio_data TEXT,  -- base64 编码的音频
    transcription TEXT NOT NULL,
    confidence FLOAT,  -- 语音识别置信度
    duration_seconds INTEGER,  -- 音频时长
    status VARCHAR(50) DEFAULT 'draft',  -- 'draft', 'converted', 'merged', 'discarded'
    converted_to_chapter_id UUID,
    created_by VARCHAR(255),
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

-- 索引
CREATE INDEX IF NOT EXISTS idx_voice_drafts_project ON voice_drafts(project_id);
CREATE INDEX IF NOT EXISTS idx_voice_drafts_chapter ON voice_drafts(chapter_no);
CREATE INDEX IF NOT EXISTS idx_voice_drafts_status ON voice_drafts(status);

-- =====================================================
-- 4. 创建关系图谱配置表
-- =====================================================

CREATE TABLE IF NOT EXISTS relationship_graph_configs (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    project_id UUID NOT NULL,
    config_name VARCHAR(255) NOT NULL,
    layout_type VARCHAR(50) DEFAULT 'force',  -- 'force', 'hierarchical', 'circular'
    node_colors JSONB DEFAULT '{}',  -- 各实体类型的颜色配置
    edge_styles JSONB DEFAULT '{}',  -- 各关系类型的线条样式
    visible_entity_types TEXT[] DEFAULT '{}',
    visible_relationship_types TEXT[] DEFAULT '{}',
    is_default BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW(),
    UNIQUE(project_id, config_name)
);

-- 索引
CREATE INDEX IF NOT EXISTS idx_relationship_graph_configs_project ON relationship_graph_configs(project_id);

-- =====================================================
-- 5. 创建模板市场配置表
-- =====================================================

CREATE TABLE IF NOT EXISTS template_marketplace (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    template_id UUID NOT NULL,
    project_id UUID NOT NULL,
    template_key VARCHAR(255) NOT NULL,
    category VARCHAR(100) NOT NULL,
    tags TEXT[] DEFAULT '{}',
    download_count INTEGER DEFAULT 0,
    rating FLOAT DEFAULT 0,
    is_featured BOOLEAN DEFAULT FALSE,
    is_verified BOOLEAN DEFAULT FALSE,
    published_at TIMESTAMP DEFAULT NOW(),
    last_download_at TIMESTAMP
);

-- 索引
CREATE INDEX IF NOT EXISTS idx_template_marketplace_category ON template_marketplace(category);
CREATE INDEX IF NOT EXISTS idx_template_marketplace_tags ON template_marketplace USING GIN(tags);
CREATE INDEX IF NOT EXISTS idx_template_marketplace_downloads ON template_marketplace(download_count DESC);

-- =====================================================
-- 6. 创建自动化测试结果表
-- =====================================================

CREATE TABLE IF NOT EXISTS automated_test_results (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    project_id UUID NOT NULL,
    test_suite VARCHAR(100) NOT NULL,
    test_name VARCHAR(255) NOT NULL,
    status VARCHAR(50) NOT NULL,  -- 'passed', 'failed', 'skipped'
    duration_ms INTEGER,
    error_message TEXT,
    stack_trace TEXT,
    created_at TIMESTAMP DEFAULT NOW()
);

-- 索引
CREATE INDEX IF NOT EXISTS idx_automated_test_results_project ON automated_test_results(project_id);
CREATE INDEX IF NOT EXISTS idx_automated_test_results_status ON automated_test_results(status);
CREATE INDEX IF NOT EXISTS idx_automated_test_results_suite ON automated_test_results(test_suite);

-- =====================================================
-- 7. 创建性能测试记录表
-- =====================================================

CREATE TABLE IF NOT EXISTS performance_test_results (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    project_id UUID NOT NULL,
    test_name VARCHAR(255) NOT NULL,
    test_type VARCHAR(50) NOT NULL,  -- 'load', 'stress', 'endurance', 'memory'
    metric_name VARCHAR(100) NOT NULL,
    metric_value FLOAT NOT NULL,
    metric_unit VARCHAR(50),
    threshold_value FLOAT,
    threshold_exceeded BOOLEAN DEFAULT FALSE,
    test_config JSONB DEFAULT '{}',
    created_at TIMESTAMP DEFAULT NOW()
);

-- 索引
CREATE INDEX IF NOT EXISTS idx_performance_test_results_project ON performance_test_results(project_id);
CREATE INDEX IF NOT EXISTS idx_performance_test_results_type ON performance_test_results(test_type);
CREATE INDEX IF NOT EXISTS idx_performance_test_results_created ON performance_test_results(created_at DESC);

COMMENT ON TABLE offline_sync_sessions IS '离线同步会话表';
COMMENT ON TABLE offline_change_queue IS '离线变更队列表';
COMMENT ON TABLE voice_drafts IS '语音草稿表';
COMMENT ON TABLE relationship_graph_configs IS '关系图谱配置表';
COMMENT ON TABLE template_marketplace IS '模板市场表';
COMMENT ON TABLE automated_test_results IS '自动化测试结果表';
COMMENT ON TABLE performance_test_results IS '性能测试记录表';
