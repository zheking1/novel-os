-- Phase 7: P1 创作效率增强
-- Prompt 模板托管

-- =====================================================
-- 1. 创建 Prompt 模板表
-- =====================================================

CREATE TABLE IF NOT EXISTS prompt_templates (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    project_id UUID NOT NULL,
    template_key VARCHAR(255) NOT NULL,
    name VARCHAR(500) NOT NULL,
    description TEXT,
    template_content TEXT NOT NULL,
    template_type VARCHAR(50) DEFAULT 'system',  -- 'system', 'user', 'assistant'
    variables JSONB DEFAULT '[]',  -- 变量定义 [{name, type, default, required}]
    genre VARCHAR(100),  -- 适用的题材
    scene VARCHAR(100),  -- 适用场景
    version INTEGER DEFAULT 1,
    is_active BOOLEAN DEFAULT TRUE,
    is_system BOOLEAN DEFAULT FALSE,  -- 系统模板不可删除
    usage_count INTEGER DEFAULT 0,
    last_used_at TIMESTAMP,
    created_by VARCHAR(255),
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW(),
    UNIQUE(project_id, template_key)
);

-- 索引
CREATE INDEX IF NOT EXISTS idx_prompt_templates_project ON prompt_templates(project_id);
CREATE INDEX IF NOT EXISTS idx_prompt_templates_key ON prompt_templates(template_key);
CREATE INDEX IF NOT EXISTS idx_prompt_templates_genre ON prompt_templates(genre);
CREATE INDEX IF NOT EXISTS idx_prompt_templates_scene ON prompt_templates(scene);
CREATE INDEX IF NOT EXISTS idx_prompt_templates_active ON prompt_templates(is_active);

-- =====================================================
-- 2. 创建模板版本历史表
-- =====================================================

CREATE TABLE IF NOT EXISTS prompt_template_versions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    template_id UUID NOT NULL,
    version INTEGER NOT NULL,
    template_content TEXT NOT NULL,
    variables JSONB DEFAULT '[]',
    change_summary TEXT,
    created_by VARCHAR(255),
    created_at TIMESTAMP DEFAULT NOW(),
    UNIQUE(template_id, version)
);

-- 索引
CREATE INDEX IF NOT EXISTS idx_prompt_template_versions_template ON prompt_template_versions(template_id);

-- =====================================================
-- 3. 创建模板变量实例表 - 记录每次使用时的变量值
-- =====================================================

CREATE TABLE IF NOT EXISTS prompt_template_usage_logs (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    template_id UUID NOT NULL,
    project_id UUID NOT NULL,
    variables_used JSONB DEFAULT '{}',  -- 实际使用的变量值
    rendered_content TEXT,  -- 渲染后的内容（截断）
    tokens_used INTEGER,
    created_by VARCHAR(255),
    created_at TIMESTAMP DEFAULT NOW()
);

-- 索引
CREATE INDEX IF NOT EXISTS idx_prompt_template_usage_logs_template ON prompt_template_usage_logs(template_id);
CREATE INDEX IF NOT EXISTS idx_prompt_template_usage_logs_project ON prompt_template_usage_logs(project_id);
CREATE INDEX IF NOT EXISTS idx_prompt_template_usage_logs_created ON prompt_template_usage_logs(created_at DESC);

-- =====================================================
-- 4. 创建上下文权重配置表
-- =====================================================

CREATE TABLE IF NOT EXISTS context_weight_configs (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    project_id UUID NOT NULL,
    config_name VARCHAR(255) NOT NULL,
    profile VARCHAR(100) DEFAULT 'default',  -- 上下文profile
    weights JSONB NOT NULL DEFAULT '{}',  -- {canon: 1.0, entity: 0.8, rules: 0.9, ...}
    max_total_tokens INTEGER DEFAULT 8000,
    priority_order JSONB DEFAULT '[]',  -- 优先级顺序
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW(),
    UNIQUE(project_id, config_name, profile)
);

-- 索引
CREATE INDEX IF NOT EXISTS idx_context_weight_configs_project ON context_weight_configs(project_id);
CREATE INDEX IF NOT EXISTS idx_context_weight_configs_active ON context_weight_configs(is_active);

-- =====================================================
-- 5. 创建素材库表
-- =====================================================

CREATE TABLE IF NOT EXISTS reference_materials (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    project_id UUID NOT NULL,
    material_key VARCHAR(255) NOT NULL,
    title VARCHAR(500) NOT NULL,
    content TEXT,
    material_type VARCHAR(50) NOT NULL,  -- 'scene', 'dialogue', 'description', 'world', 'custom'
    category VARCHAR(100),  -- 分类
    tags TEXT[] DEFAULT '{}',
    source_url TEXT,
    source_credit VARCHAR(500),
    file_path VARCHAR(1000),  -- 本地文件路径
    usage_count INTEGER DEFAULT 0,
    favorite BOOLEAN DEFAULT FALSE,
    metadata JSONB DEFAULT '{}',
    created_by VARCHAR(255),
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW(),
    UNIQUE(project_id, material_key)
);

-- 索引
CREATE INDEX IF NOT EXISTS idx_reference_materials_project ON reference_materials(project_id);
CREATE INDEX IF NOT EXISTS idx_reference_materials_type ON reference_materials(material_type);
CREATE INDEX IF NOT EXISTS idx_reference_materials_category ON reference_materials(category);
CREATE INDEX IF NOT EXISTS idx_reference_materials_tags ON reference_materials USING GIN(tags);
CREATE INDEX IF NOT EXISTS idx_reference_materials_favorite ON reference_materials(favorite);

-- =====================================================
-- 6. 创建读者期待记录表
-- =====================================================

CREATE TABLE IF NOT EXISTS reader_expectations (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    project_id UUID NOT NULL,
    expectation_key VARCHAR(255) NOT NULL,
    title VARCHAR(500) NOT NULL,
    description TEXT,
    expectation_type VARCHAR(50) NOT NULL,  -- 'suspense', 'promise', 'foreshadow', ' payoff'
    status VARCHAR(50) DEFAULT 'active',  -- 'active', 'fulfilled', 'abandoned'
    chapter_no INTEGER,  -- 首次出现章节
    payoff_chapter_no INTEGER,  -- 回收章节
    importance VARCHAR(50) DEFAULT 'medium',  -- 'high', 'medium', 'low'
    tags TEXT[] DEFAULT '{}',
    metadata JSONB DEFAULT '{}',
    created_by VARCHAR(255),
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW(),
    UNIQUE(project_id, expectation_key)
);

-- 索引
CREATE INDEX IF NOT EXISTS idx_reader_expectations_project ON reader_expectations(project_id);
CREATE INDEX IF NOT EXISTS idx_reader_expectations_type ON reader_expectations(expectation_type);
CREATE INDEX IF NOT EXISTS idx_reader_expectations_status ON reader_expectations(status);
CREATE INDEX IF NOT EXISTS idx_reader_expectations_chapter ON reader_expectations(chapter_no);

-- =====================================================
-- 7. 创建批注表
-- =====================================================

CREATE TABLE IF NOT EXISTS chapter_annotations (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    project_id UUID NOT NULL,
    chapter_id UUID NOT NULL,
    chapter_no INTEGER NOT NULL,
    annotation_type VARCHAR(50) NOT NULL,  -- 'comment', 'note', 'revision', 'question'
    content TEXT NOT NULL,
    anchor_start INTEGER,  -- 批注锚点开始位置
    anchor_end INTEGER,  -- 批注锚点结束位置
    parent_id UUID,  -- 回复的批注ID
    resolve_status VARCHAR(50) DEFAULT 'open',  -- 'open', 'resolved'
    resolved_by VARCHAR(255),
    resolved_at TIMESTAMP,
    created_by VARCHAR(255),
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

-- 索引
CREATE INDEX IF NOT EXISTS idx_chapter_annotations_project ON chapter_annotations(project_id);
CREATE INDEX IF NOT EXISTS idx_chapter_annotations_chapter ON chapter_annotations(chapter_id);
CREATE INDEX IF NOT EXISTS idx_chapter_annotations_type ON chapter_annotations(annotation_type);
CREATE INDEX IF NOT EXISTS idx_chapter_annotations_resolved ON chapter_annotations(resolve_status);

-- =====================================================
-- 8. 创建正文版本记录表
-- =====================================================

CREATE TABLE IF NOT EXISTS chapter_versions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    project_id UUID NOT NULL,
    chapter_id UUID NOT NULL,
    chapter_no INTEGER NOT NULL,
    version_no INTEGER NOT NULL,
    content TEXT NOT NULL,
    word_count INTEGER,
    change_summary TEXT,
    created_by VARCHAR(255),
    created_at TIMESTAMP DEFAULT NOW(),
    UNIQUE(chapter_id, version_no)
);

-- 索引
CREATE INDEX IF NOT EXISTS idx_chapter_versions_chapter ON chapter_versions(chapter_id);
CREATE INDEX IF NOT EXISTS idx_chapter_versions_created ON chapter_versions(created_at DESC);

-- =====================================================
-- 9. 创建统计指标表
-- =====================================================

CREATE TABLE IF NOT EXISTS writing_stats (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    project_id UUID NOT NULL,
    stat_date DATE NOT NULL,
    stat_type VARCHAR(50) NOT NULL,  -- 'daily', 'volume', 'arc'
    chapter_no INTEGER,
    volume_no INTEGER,
    word_count INTEGER DEFAULT 0,
    chapters_completed INTEGER DEFAULT 0,
   爽点_count INTEGER DEFAULT 0,
    conflict_count INTEGER DEFAULT 0,
    foreshadow_count INTEGER DEFAULT 0,
    metadata JSONB DEFAULT '{}',
    created_at TIMESTAMP DEFAULT NOW(),
    UNIQUE(project_id, stat_date, stat_type, chapter_no)
);

-- 索引
CREATE INDEX IF NOT EXISTS idx_writing_stats_project ON writing_stats(project_id);
CREATE INDEX IF NOT EXISTS idx_writing_stats_date ON writing_stats(stat_date);
CREATE INDEX IF NOT EXISTS idx_writing_stats_type ON writing_stats(stat_type);

-- =====================================================
-- 10. 创建专有名词词典表
-- =====================================================

CREATE TABLE IF NOT EXISTS proper_nouns (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    project_id UUID NOT NULL,
    noun_key VARCHAR(255) NOT NULL,
    noun_value VARCHAR(500) NOT NULL,
    noun_type VARCHAR(50) NOT NULL,  -- 'character_name', 'place_name', 'faction_name', 'item_name', 'term'
    aliases TEXT[] DEFAULT '{}',  -- 别名
    description TEXT,
    locked BOOLEAN DEFAULT FALSE,  -- 锁定后不可自动修改
    usage_count INTEGER DEFAULT 0,
    first_chapter_no INTEGER,
    created_by VARCHAR(255),
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW(),
    UNIQUE(project_id, noun_key)
);

-- 索引
CREATE INDEX IF NOT EXISTS idx_proper_nouns_project ON proper_nouns(project_id);
CREATE INDEX IF NOT EXISTS idx_proper_nouns_type ON proper_nouns(noun_type);
CREATE INDEX IF NOT EXISTS idx_proper_nouns_locked ON proper_nouns(locked);

-- =====================================================
-- 11. 创建全文检索记录表（用于跨模块搜索）
-- =====================================================

CREATE TABLE IF NOT EXISTS fulltext_search_records (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    project_id UUID NOT NULL,
    source_type VARCHAR(50) NOT NULL,  -- 'chapter', 'canon', 'entity', 'foreshadow', 'rule', 'material'
    source_id UUID NOT NULL,
    source_key VARCHAR(255),  -- 可读标识
    title VARCHAR(500),
    content TEXT,
    search_vector tsvector,
    metadata JSONB DEFAULT '{}',
    updated_at TIMESTAMP DEFAULT NOW(),
    UNIQUE(source_type, source_id)
);

-- 索引
CREATE INDEX IF NOT EXISTS idx_fulltext_search_project ON fulltext_search_records(project_id);
CREATE INDEX IF NOT EXISTS idx_fulltext_search_type ON fulltext_search_records(source_type);
CREATE INDEX IF NOT EXISTS idx_fulltext_search_vector ON fulltext_search_records USING GIN(search_vector);

-- 触发器：自动更新 search_vector
CREATE OR REPLACE FUNCTION update_fulltext_search_vector()
RETURNS TRIGGER AS $$
BEGIN
    NEW.search_vector := to_tsvector('chinese', COALESCE(NEW.title, '') || ' ' || COALESCE(NEW.content, ''));
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER trg_fulltext_search_vector
    BEFORE INSERT OR UPDATE ON fulltext_search_records
    FOR EACH ROW EXECUTE FUNCTION update_fulltext_search_vector();

COMMENT ON TABLE prompt_templates IS 'Prompt 模板表';
COMMENT ON TABLE context_weight_configs IS '上下文权重配置表';
COMMENT ON TABLE reference_materials IS '素材库表';
COMMENT ON TABLE reader_expectations IS '读者期待记录表';
COMMENT ON TABLE chapter_annotations IS '章节批注表';
COMMENT ON TABLE chapter_versions IS '正文版本记录表';
COMMENT ON TABLE writing_stats IS '写作统计指标表';
COMMENT ON TABLE proper_nouns IS '专有名词词典表';
COMMENT ON TABLE fulltext_search_records IS '全文检索记录表';
