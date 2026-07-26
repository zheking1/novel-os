-- Migration: 220_system_evolution.sql
-- Description: 系统级进化架构核心表创建
-- Author: OpenCode AI Agent
-- Date: 2024-01-15
-- Depends: 213_model_profiles_user_id.sql

-- ========================================
-- 1. 系统级进化提案表
-- ========================================

CREATE TABLE IF NOT EXISTS system_evolution_proposals (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    
    -- 提案基本信息
    title TEXT NOT NULL,
    description TEXT NOT NULL,
    proposal_type TEXT NOT NULL CHECK (proposal_type IN ('create', 'update', 'delete', 'merge')),
    
    -- 目标系统级数据
    target_entity_type TEXT NOT NULL CHECK (target_entity_type IN (
        'style_profile', 'prompt_template', 'model_profile', 
        'knowledge_item', 'setting_item', 'genre_config'
    )),
    target_entity_id UUID,
    target_entity_key TEXT,
    
    -- 提案内容
    proposed_content JSONB NOT NULL,
    
    -- 进化依据
    evolution_reason TEXT NOT NULL,
    evidence JSONB,
    source_project_id UUID REFERENCES projects(id) ON DELETE SET NULL,
    source_chapter_no INTEGER,
    
    -- 状态流转: draft → ai_reviewing → ai_reviewed → pending_admin → admin_approved/rejected → applied
    status TEXT NOT NULL DEFAULT 'draft',
    
    -- AI初审结果
    ai_review_result JSONB,
    ai_retry_count INTEGER DEFAULT 0,
    ai_last_error TEXT,
    
    -- 管理员审核结果
    admin_review_result JSONB,
    
    -- 提交者
    submitted_by UUID REFERENCES users(id) ON DELETE SET NULL,
    ai_submitter TEXT,
    
    -- 执行信息
    applied_at TIMESTAMPTZ,
    applied_version INTEGER,
    
    -- 元数据
    metadata JSONB NOT NULL DEFAULT '{}'::jsonb,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE INDEX idx_evolution_proposals_status ON system_evolution_proposals(status);
CREATE INDEX idx_evolution_proposals_entity ON system_evolution_proposals(target_entity_type, target_entity_id);
CREATE INDEX idx_evolution_proposals_created ON system_evolution_proposals(created_at DESC);
CREATE INDEX idx_evolution_proposals_ai_submitter ON system_evolution_proposals(ai_submitter) WHERE ai_submitter IS NOT NULL;

COMMENT ON TABLE system_evolution_proposals IS '系统级进化提案表 - AI自动初审 → 管理员终审';
COMMENT ON COLUMN system_evolution_proposals.status IS '状态: draft/ai_reviewing/ai_reviewed/pending_admin/admin_approved/admin_rejected/applied';
COMMENT ON COLUMN system_evolution_proposals.ai_review_result IS 'AI初审结果: {score, verdict, reasoning, risk_assessment, suggestions}';
COMMENT ON COLUMN system_evolution_proposals.admin_review_result IS '管理员审核结果: {decision, reason, reviewed_by, reviewed_at}';

-- ========================================
-- 2. 系统级文风档案表
-- ========================================

CREATE TABLE IF NOT EXISTS system_style_profiles (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    profile_key TEXT NOT NULL UNIQUE,
    display_name TEXT NOT NULL,
    
    -- 风格定义
    narrative_pov TEXT NOT NULL DEFAULT 'third_limited',
    tense TEXT NOT NULL DEFAULT 'past',
    tone TEXT NOT NULL,
    target_metrics JSONB NOT NULL DEFAULT '{}'::jsonb,
    
    -- 详细描述
    description TEXT,
    characteristics JSONB,
    sample_paragraphs TEXT[],
    
    -- 适用题材
    applicable_genres TEXT[],
    
    -- 版本管理（方案A: JSONB存储最近10版本）
    version INTEGER NOT NULL DEFAULT 1,
    version_history JSONB NOT NULL DEFAULT '[]'::jsonb,
    
    -- 状态
    status TEXT NOT NULL DEFAULT 'active' CHECK (status IN ('active', 'deprecated', 'draft')),
    
    -- 来源追踪
    created_from_proposal_id UUID REFERENCES system_evolution_proposals(id) ON DELETE SET NULL,
    
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE INDEX idx_system_style_profiles_status ON system_style_profiles(status);
CREATE INDEX idx_system_style_profiles_genres ON system_style_profiles USING GIN(applicable_genres);

COMMENT ON TABLE system_style_profiles IS '系统级文风档案 - 所有项目可参考，需通过进化流程修改';
COMMENT ON COLUMN system_style_profiles.version_history IS '最近10个版本的历史记录';

-- ========================================
-- 3. 系统级提示词模板表
-- ========================================

CREATE TABLE IF NOT EXISTS system_prompt_templates (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    template_key TEXT NOT NULL UNIQUE,
    template_name TEXT NOT NULL,
    
    -- 模板内容
    template_content TEXT NOT NULL,
    description TEXT,
    
    -- 分类标签
    template_type TEXT NOT NULL,
    genre TEXT,
    scene TEXT,
    
    -- 变量定义
    variables JSONB NOT NULL DEFAULT '[]'::jsonb,
    
    -- 版本管理
    version INTEGER NOT NULL DEFAULT 1,
    version_history JSONB NOT NULL DEFAULT '[]'::jsonb,
    
    -- 状态
    status TEXT NOT NULL DEFAULT 'active',
    
    -- 来源追踪
    created_from_proposal_id UUID REFERENCES system_evolution_proposals(id) ON DELETE SET NULL,
    
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE INDEX idx_system_prompt_templates_type ON system_prompt_templates(template_type);
CREATE INDEX idx_system_prompt_templates_genre ON system_prompt_templates(genre);

COMMENT ON TABLE system_prompt_templates IS '系统级提示词模板 - 所有项目可导入，需通过进化流程修改';

-- ========================================
-- 4. 系统级模型配置表
-- ========================================

CREATE TABLE IF NOT EXISTS system_model_profiles (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    profile_key TEXT NOT NULL UNIQUE,
    display_name TEXT NOT NULL,
    
    -- 模型信息
    provider TEXT NOT NULL,
    model_name TEXT NOT NULL,
    task_types TEXT[] NOT NULL,
    
    -- 配置
    default_params JSONB NOT NULL DEFAULT '{}'::jsonb,
    cost_config JSONB NOT NULL DEFAULT '{}'::jsonb,
    rate_limit_config JSONB NOT NULL DEFAULT '{}'::jsonb,
    
    -- 推荐场景
    recommended_for JSONB,
    
    -- 版本管理
    version INTEGER NOT NULL DEFAULT 1,
    version_history JSONB NOT NULL DEFAULT '[]'::jsonb,
    
    -- 状态
    status TEXT NOT NULL DEFAULT 'active',
    
    -- 来源追踪
    created_from_proposal_id UUID REFERENCES system_evolution_proposals(id) ON DELETE SET NULL,
    
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE INDEX idx_system_model_profiles_status ON system_model_profiles(status);
CREATE INDEX idx_system_model_profiles_task_types ON system_model_profiles USING GIN(task_types);

COMMENT ON TABLE system_model_profiles IS '系统级模型配置预设 - 用户可复制使用';

-- ========================================
-- 5. 站内通知表
-- ========================================

CREATE TABLE IF NOT EXISTS system_notifications (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    
    -- 接收者 (null表示发给所有管理员)
    user_id UUID REFERENCES users(id) ON DELETE CASCADE,
    is_global BOOLEAN NOT NULL DEFAULT FALSE,
    
    -- 通知内容
    type TEXT NOT NULL CHECK (type IN ('evolution_proposal', 'system_update', 'ai_review_completed', 'admin_review_required')),
    title TEXT NOT NULL,
    content TEXT NOT NULL,
    
    -- 关联数据
    related_proposal_id UUID REFERENCES system_evolution_proposals(id) ON DELETE CASCADE,
    
    -- 状态
    is_read BOOLEAN NOT NULL DEFAULT FALSE,
    read_at TIMESTAMPTZ,
    
    -- 过期时间 (90天)
    expires_at TIMESTAMPTZ NOT NULL DEFAULT (now() + interval '90 days'),
    
    created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE INDEX idx_system_notifications_user ON system_notifications(user_id, is_read, created_at DESC);
CREATE INDEX idx_system_notifications_global ON system_notifications(is_global, is_read, created_at DESC) WHERE is_global = TRUE;
CREATE INDEX idx_system_notifications_expires ON system_notifications(expires_at);

COMMENT ON TABLE system_notifications IS '站内通知表 - 系统级进化相关通知，保留90天';

-- ========================================
-- 6. 修改现有model_profiles表
-- ========================================

-- 添加系统级标记
ALTER TABLE model_profiles ADD COLUMN IF NOT EXISTS is_system BOOLEAN NOT NULL DEFAULT FALSE;
ALTER TABLE model_profiles ADD COLUMN IF NOT EXISTS forked_from_system_key TEXT;

CREATE INDEX idx_model_profiles_is_system ON model_profiles(is_system) WHERE is_system = TRUE;

COMMENT ON COLUMN model_profiles.is_system IS '是否为系统级配置（管理员维护）';
COMMENT ON COLUMN model_profiles.forked_from_system_key IS '从哪个系统配置复制而来';

-- ========================================
-- 7. 创建更新触发器
-- ========================================

CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = now();
    RETURN NEW;
END;
$$ language 'plpgsql';

-- 为所有新表添加更新触发器
DROP TRIGGER IF EXISTS update_system_evolution_proposals_updated_at ON system_evolution_proposals;
CREATE TRIGGER update_system_evolution_proposals_updated_at
    BEFORE UPDATE ON system_evolution_proposals
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

DROP TRIGGER IF EXISTS update_system_style_profiles_updated_at ON system_style_profiles;
CREATE TRIGGER update_system_style_profiles_updated_at
    BEFORE UPDATE ON system_style_profiles
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

DROP TRIGGER IF EXISTS update_system_prompt_templates_updated_at ON system_prompt_templates;
CREATE TRIGGER update_system_prompt_templates_updated_at
    BEFORE UPDATE ON system_prompt_templates
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

DROP TRIGGER IF EXISTS update_system_model_profiles_updated_at ON system_model_profiles;
CREATE TRIGGER update_system_model_profiles_updated_at
    BEFORE UPDATE ON system_model_profiles
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

-- ========================================
-- 8. 创建版本历史维护函数
-- ========================================

CREATE OR REPLACE FUNCTION maintain_version_history()
RETURNS TRIGGER AS $$
DECLARE
    new_history_entry JSONB;
    current_history JSONB;
BEGIN
    -- 构建新版本历史条目
    new_history_entry = jsonb_build_object(
        'version', OLD.version,
        'content', row_to_json(OLD),
        'archived_at', now()
    );
    
    -- 获取当前历史
    current_history = COALESCE(OLD.version_history, '[]'::jsonb);
    
    -- 添加新条目到开头
    NEW.version_history = jsonb_insert(current_history, '{0}', new_history_entry);
    
    -- 只保留最近10个版本
    IF jsonb_array_length(NEW.version_history) > 10 THEN
        NEW.version_history = NEW.version_history - (jsonb_array_length(NEW.version_history) - 1);
    END IF;
    
    -- 版本号+1
    NEW.version = OLD.version + 1;
    
    RETURN NEW;
END;
$$ language 'plpgsql';

-- 为需要版本管理的表添加触发器
DROP TRIGGER IF EXISTS maintain_style_profile_version ON system_style_profiles;
CREATE TRIGGER maintain_style_profile_version
    BEFORE UPDATE ON system_style_profiles
    FOR EACH ROW
    WHEN (OLD.version IS NOT NULL)
    EXECUTE FUNCTION maintain_version_history();

DROP TRIGGER IF EXISTS maintain_prompt_template_version ON system_prompt_templates;
CREATE TRIGGER maintain_prompt_template_version
    BEFORE UPDATE ON system_prompt_templates
    FOR EACH ROW
    WHEN (OLD.version IS NOT NULL)
    EXECUTE FUNCTION maintain_version_history();

DROP TRIGGER IF EXISTS maintain_model_profile_version ON system_model_profiles;
CREATE TRIGGER maintain_model_profile_version
    BEFORE UPDATE ON system_model_profiles
    FOR EACH ROW
    WHEN (OLD.version IS NOT NULL)
    EXECUTE FUNCTION maintain_version_history();

-- ========================================
-- 9. 创建清理过期通知的定时任务函数
-- ========================================

CREATE OR REPLACE FUNCTION cleanup_expired_notifications()
RETURNS INTEGER AS $$
DECLARE
    deleted_count INTEGER;
BEGIN
    DELETE FROM system_notifications
    WHERE expires_at < now();
    
    GET DIAGNOSTICS deleted_count = ROW_COUNT;
    RETURN deleted_count;
END;
$$ language 'plpgsql';

COMMENT ON FUNCTION cleanup_expired_notifications() IS '清理过期的站内通知，建议每天运行一次';

-- ========================================
-- Migration Complete
-- ========================================

SELECT 'Migration 220_system_evolution completed successfully' as status;
