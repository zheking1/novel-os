-- Migration 206: Local Storage Index
-- 本地存储索引：章节、审查、设定元数据（不存全文）
-- 目标：2000万字小说，DB只存摘要+结构化数据，长文本留本地

-- 章节索引（不存正文）
CREATE TABLE IF NOT EXISTS chapter_index (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    project_id UUID NOT NULL,
    chapter_no INT NOT NULL,
    volume_no INT DEFAULT 1,
    title VARCHAR(200),
    status VARCHAR(20) DEFAULT 'planned',  -- planned/draft/revised/final
    word_count INT DEFAULT 0,
    summary TEXT,                          -- 200-500字摘要
    local_path VARCHAR(500),               -- 本地相对路径（如 第01章/ch01_final.md）
    outline_path VARCHAR(500),             -- 章纲路径
    pov_mode VARCHAR(20) DEFAULT 'third',  -- first/third/omniscient
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW(),
    UNIQUE(project_id, chapter_no)
);

-- 审查索引（不存报告全文）
CREATE TABLE IF NOT EXISTS review_index (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    project_id UUID NOT NULL,
    chapter_id UUID REFERENCES chapter_index(id) ON DELETE CASCADE,
    chapter_no INT,
    model_name VARCHAR(100),
    score FLOAT,                           -- 综合评分 0-100
    passed BOOLEAN DEFAULT FALSE,
    issues JSONB DEFAULT '[]',             -- [{type, severity, description}]
    summary TEXT,                          -- 总体意见摘要
    local_path VARCHAR(500),               -- 审查报告路径
    created_at TIMESTAMP DEFAULT NOW()
);

-- 设定索引
CREATE TABLE IF NOT EXISTS setting_index (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    project_id UUID NOT NULL,
    category VARCHAR(50),                  -- character/world/faction/rule/technique
    name VARCHAR(200) NOT NULL,
    keywords TEXT[] DEFAULT ARRAY[]::TEXT[],          -- 关键词
    summary TEXT,                          -- 摘要
    local_path VARCHAR(500),
    structured_data JSONB,                 -- .json 文件存完整数据
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

-- 本地项目注册表
CREATE TABLE IF NOT EXISTS local_projects (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    project_id UUID NOT NULL UNIQUE,
    local_root VARCHAR(500) NOT NULL,      -- 本地项目根目录
    last_scan_at TIMESTAMP,
    file_count INT DEFAULT 0,
    total_words INT DEFAULT 0,
    chapter_count INT DEFAULT 0,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

-- 索引
CREATE INDEX IF NOT EXISTS idx_chapter_project ON chapter_index(project_id);
CREATE INDEX IF NOT EXISTS idx_chapter_status ON chapter_index(project_id, status);
CREATE INDEX IF NOT EXISTS idx_review_chapter ON review_index(chapter_id);
CREATE INDEX IF NOT EXISTS idx_review_project ON review_index(project_id);
CREATE INDEX IF NOT EXISTS idx_setting_project ON setting_index(project_id);
CREATE INDEX IF NOT EXISTS idx_setting_category ON setting_index(project_id, category);
CREATE INDEX IF NOT EXISTS idx_local_project ON local_projects(project_id);

-- 向量集合（Qdrant，代码层管理）
-- chapter_summaries: embedding(summary + keywords), payload: {project_id, chapter_no, title, status, local_path}
-- setting_summaries: embedding(summary + keywords), payload: {project_id, category, name, local_path}
