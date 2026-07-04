-- Phase 6: 性能、容灾与运维
-- 增量向量索引任务队列表

-- =====================================================
-- 1. 创建向量索引任务队列表
-- =====================================================

CREATE TABLE IF NOT EXISTS vector_index_tasks (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    project_id UUID NOT NULL,
    chunk_id UUID NOT NULL,
    collection VARCHAR(255) NOT NULL,
    status VARCHAR(50) DEFAULT 'pending',  -- 'pending', 'processing', 'completed', 'failed'
    priority INTEGER DEFAULT 0,  -- 0=normal, 1=high, -1=low
    attempts INTEGER DEFAULT 0,
    max_attempts INTEGER DEFAULT 3,
    error_message TEXT,
    queued_at TIMESTAMP DEFAULT NOW(),
    started_at TIMESTAMP,
    completed_at TIMESTAMP,
    last_error_at TIMESTAMP,
    metadata JSONB DEFAULT '{}',
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

-- 索引
CREATE INDEX IF NOT EXISTS idx_vector_index_tasks_status ON vector_index_tasks(status);
CREATE INDEX IF NOT EXISTS idx_vector_index_tasks_project ON vector_index_tasks(project_id);
CREATE INDEX IF NOT EXISTS idx_vector_index_tasks_priority ON vector_index_tasks(priority DESC, queued_at ASC);
CREATE INDEX IF NOT EXISTS idx_vector_index_tasks_chunk ON vector_index_tasks(chunk_id);

-- =====================================================
-- 2. 创建向量索引状态表 - 追踪每个 collection 的索引状态
-- =====================================================

CREATE TABLE IF NOT EXISTS vector_index_status (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    project_id UUID NOT NULL,
    collection VARCHAR(255) NOT NULL,
    total_chunks INTEGER DEFAULT 0,
    indexed_chunks INTEGER DEFAULT 0,
    failed_chunks INTEGER DEFAULT 0,
    last_indexed_at TIMESTAMP,
    last_full_reindex_at TIMESTAMP,
    is_incremental BOOLEAN DEFAULT TRUE,
    index_version INTEGER DEFAULT 1,
    metadata JSONB DEFAULT '{}',
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW(),
    UNIQUE(project_id, collection)
);

-- 索引
CREATE INDEX IF NOT EXISTS idx_vector_index_status_project ON vector_index_status(project_id);

-- =====================================================
-- 3. 创建索引配置表 - 存储索引策略配置
-- =====================================================

CREATE TABLE IF NOT EXISTS vector_index_config (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    project_id UUID NOT NULL,
    collection VARCHAR(255) NOT NULL,
    batch_size INTEGER DEFAULT 100,
    retry_delay_seconds INTEGER DEFAULT 60,
    max_concurrent INTEGER DEFAULT 5,
    priority_enabled BOOLEAN DEFAULT TRUE,
    auto_retry BOOLEAN DEFAULT TRUE,
    enabled BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW(),
    UNIQUE(project_id, collection)
);

-- =====================================================
-- 4. 创建内存块索引历史表 - 追踪索引变化
-- =====================================================

CREATE TABLE IF NOT EXISTS memory_chunk_index_history (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    chunk_id UUID NOT NULL,
    project_id UUID NOT NULL,
    operation VARCHAR(50) DEFAULT 'index',  -- 'index', 'reindex', 'delete'
    old_point_id VARCHAR(255),
    new_point_id VARCHAR(255),
    collection VARCHAR(255),
    status VARCHAR(50) DEFAULT 'success',  -- 'success', 'failed'
    error_message TEXT,
    indexed_at TIMESTAMP DEFAULT NOW()
);

-- 索引
CREATE INDEX IF NOT EXISTS idx_memory_chunk_index_history_chunk ON memory_chunk_index_history(chunk_id);
CREATE INDEX IF NOT EXISTS idx_memory_chunk_index_history_project ON memory_chunk_index_history(project_id);
CREATE INDEX IF NOT EXISTS idx_memory_chunk_index_history_indexed ON memory_chunk_index_history(indexed_at);

COMMENT ON TABLE vector_index_tasks IS '向量索引任务队列表 - 管理增量索引任务';
COMMENT ON TABLE vector_index_status IS '向量索引状态表 - 追踪每个 collection 的索引状态';
COMMENT ON TABLE vector_index_config IS '向量索引配置表 - 存储索引策略配置';
COMMENT ON TABLE memory_chunk_index_history IS '内存块索引历史表 - 追踪索引变化';
