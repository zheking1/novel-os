-- =============================================
-- Novel OS 知识用户数据与审核流程迁移脚本
-- Version: 1.0
-- Date: 2026-06-30
-- Description: 创建用户私有知识库和审核记录表，支持多用户协作维护基础数据
-- =============================================

BEGIN;

-- =============================================
-- 1. 用户私有知识库表 user_knowledge
-- 用于存储用户对公共数据的个性化修改
-- =============================================
CREATE TABLE IF NOT EXISTS user_knowledge (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    
    -- 用户关联
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    
    -- 关联的公共知识条目（可为空，表示用户新建的条目）
    base_knowledge_id UUID REFERENCES knowledge_base(id) ON DELETE SET NULL,
    
    -- 核心字段（与knowledge_base一致）
    code VARCHAR(50),
    title VARCHAR(200) NOT NULL,
    content TEXT NOT NULL,
    summary TEXT,
    detail TEXT,
    examples TEXT,
    counter_examples TEXT,
    metadata JSONB DEFAULT '{}',
    
    -- 分类关联
    category_id UUID REFERENCES categories(id),
    
    -- 适用题材和技能
    applicable_genres TEXT[] DEFAULT '{}',
    applicable_skills TEXT[] DEFAULT '{}',
    level VARCHAR(20) DEFAULT 'knowledge',
    
    -- 状态：draft(草稿) / active(用户在用) / submitted(已提交审核)
    status VARCHAR(20) DEFAULT 'draft',
    
    -- 审核相关
    review_status VARCHAR(20) DEFAULT 'pending',  -- pending/approved/rejected
    review_comment TEXT,
    
    -- 统计
    view_count INTEGER DEFAULT 0,
    use_count INTEGER DEFAULT 0,
    
    -- 来源信息
    source VARCHAR(50) DEFAULT 'user',
    created_at TIMESTAMPTZ DEFAULT now(),
    updated_at TIMESTAMPTZ DEFAULT now()
);

-- =============================================
-- 2. 审核记录表 knowledge_review
-- 记录审核历史
-- =============================================
CREATE TABLE IF NOT EXISTS knowledge_review (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    
    -- 关联的用户知识条目
    user_knowledge_id UUID NOT NULL REFERENCES user_knowledge(id) ON DELETE CASCADE,
    
    -- 提交者
    submitter_id UUID NOT NULL REFERENCES users(id),
    submit_time TIMESTAMPTZ DEFAULT now(),
    submit_reason TEXT,
    
    -- 审核者
    reviewer_id UUID REFERENCES users(id),
    review_time TIMESTAMPTZ,
    review_status VARCHAR(20) DEFAULT 'pending',  -- pending/approved/rejected
    review_comment TEXT,
    
    -- 如果审核通过，记录合并到的公共条目ID
    merged_base_id UUID REFERENCES knowledge_base(id),
    
    -- 审核版本
    version INTEGER DEFAULT 1,
    created_at TIMESTAMPTZ DEFAULT now()
);

-- =============================================
-- 3. 索引创建
-- =============================================

-- 用户私有知识库索引
CREATE INDEX IF NOT EXISTS idx_user_knowledge_user ON user_knowledge(user_id);
CREATE INDEX IF NOT EXISTS idx_user_knowledge_base ON user_knowledge(base_knowledge_id);
CREATE INDEX IF NOT EXISTS idx_user_knowledge_category ON user_knowledge(category_id);
CREATE INDEX IF NOT EXISTS idx_user_knowledge_status ON user_knowledge(status);
CREATE INDEX IF NOT EXISTS idx_user_knowledge_review ON user_knowledge(review_status);
CREATE INDEX IF NOT EXISTS idx_user_knowledge_code ON user_knowledge(code);

-- 审核记录索引
CREATE INDEX IF NOT EXISTS idx_knowledge_review_user ON knowledge_review(user_knowledge_id);
CREATE INDEX IF NOT EXISTS idx_knowledge_review_status ON knowledge_review(review_status);
CREATE INDEX IF NOT EXISTS idx_knowledge_review_submitter ON knowledge_review(submitter_id);
CREATE INDEX IF NOT EXISTS idx_knowledge_review_reviewer ON knowledge_review(reviewer_id);

-- =============================================
-- 4. 更新触发器
-- =============================================
CREATE OR REPLACE FUNCTION update_user_knowledge_updated_at()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = now();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER update_user_knowledge_updated_at_trigger
    BEFORE UPDATE ON user_knowledge
    FOR EACH ROW
    EXECUTE FUNCTION update_user_knowledge_updated_at();

-- =============================================
-- 5. 更新knowledge_base表，添加审核相关字段
-- =============================================
ALTER TABLE IF EXISTS knowledge_base
ADD COLUMN IF NOT EXISTS last_reviewed_at TIMESTAMPTZ;

ALTER TABLE IF EXISTS knowledge_base
ADD COLUMN IF NOT EXISTS reviewed_by UUID REFERENCES users(id);

ALTER TABLE IF EXISTS knowledge_base
ADD COLUMN IF NOT EXISTS review_version INTEGER DEFAULT 1;

COMMIT;

-- =============================================
-- 验证查询
-- =============================================
SELECT '=== 新表创建验证 ===' as info;
SELECT table_name FROM information_schema.tables WHERE table_name IN ('user_knowledge', 'knowledge_review');

SELECT '=== knowledge_base新增字段验证 ===' as info;
SELECT column_name FROM information_schema.columns WHERE table_name = 'knowledge_base' AND column_name IN ('last_reviewed_at', 'reviewed_by', 'review_version');
