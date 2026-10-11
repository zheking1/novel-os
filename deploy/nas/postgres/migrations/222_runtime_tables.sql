-- Migration: 222_runtime_tables.sql
-- Description: 补齐代码已在读写、但仓库缺失建表 SQL 的 4 张运行时表
--              （global_rules / evolution_logs / ref_tones / ref_tone_rules）
--              以及 canon_rules 的规则升级字段
-- Date: 2026-10-10
-- Depends: 221_system_evolution_seed.sql
--          （第 5 节的触发器依赖 220_system_evolution.sql 创建的 update_updated_at_column 函数）
-- 背景: 见 docs/07-planning/roadmap.md 阶段 0（D-01）
--
-- 全部语句幂等（CREATE TABLE IF NOT EXISTS / ADD COLUMN IF NOT EXISTS），可重复执行。
-- 若目标库已手工建过这些表，本迁移不会改动其结构；列差异需先 \d 比对后手工 ALTER 补齐。

-- ========================================
-- 1. 全局规则表
-- ========================================

CREATE TABLE IF NOT EXISTS global_rules (
    id                    UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    rule_key              TEXT NOT NULL UNIQUE,
    rule_type             TEXT NOT NULL,          -- creative / compliance / polish
    title                 TEXT NOT NULL,
    content               TEXT NOT NULL,
    severity              TEXT NOT NULL DEFAULT 'warning',
    status                TEXT NOT NULL DEFAULT 'active',   -- active / inactive
    metadata              JSONB NOT NULL DEFAULT '{}'::jsonb,
    -- 升级溯源（来自哪个项目规则 / 谁操作的 / 哪个讨论室）
    source_project_id     UUID REFERENCES projects(id) ON DELETE SET NULL,
    promoted_from_rule_id UUID REFERENCES canon_rules(id) ON DELETE SET NULL,
    promoted_by           TEXT,
    discussion_id         TEXT,
    created_at            TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at            TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE INDEX IF NOT EXISTS idx_global_rules_status_type ON global_rules(status, rule_type);
CREATE INDEX IF NOT EXISTS idx_global_rules_source_project ON global_rules(source_project_id);

COMMENT ON TABLE global_rules IS '全局规则表 - 跨项目生效的创作/审查/润色规则';
COMMENT ON COLUMN global_rules.rule_type IS 'creative=创作规则 / compliance=审查规则 / polish=润色规则';

-- ========================================
-- 2. 进化日志表（gatekeeper 门禁审计）
-- ========================================

CREATE TABLE IF NOT EXISTS evolution_logs (
    id           UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    source_type  TEXT NOT NULL,        -- discussion_room / agent / user
    source_id    TEXT,                 -- session_id / chapter_no / username
    action       TEXT NOT NULL,        -- INSERT / UPDATE / DELETE / ROLLBACK
    target_table TEXT NOT NULL,        -- global_rules / universal_knowledge / canon_rules / ...
    target_id    TEXT,                 -- 写入后的目标记录 id
    old_value    JSONB,                -- 更新前值，用于回滚
    new_value    JSONB,                -- 写入的新值
    risk_level   TEXT,                 -- low / medium / high / info
    risk_reason  TEXT,                 -- gatekeeper 给出的理由
    auto_applied BOOLEAN DEFAULT false,
    proposal_id  UUID REFERENCES system_evolution_proposals(id) ON DELETE SET NULL,
    created_at   TIMESTAMPTZ DEFAULT now(),
    created_by   TEXT
);

CREATE INDEX IF NOT EXISTS idx_evolution_logs_created ON evolution_logs(created_at DESC);
CREATE INDEX IF NOT EXISTS idx_evolution_logs_source ON evolution_logs(source_type);
CREATE INDEX IF NOT EXISTS idx_evolution_logs_risk ON evolution_logs(risk_level);
CREATE INDEX IF NOT EXISTS idx_evolution_logs_target ON evolution_logs(target_table);
CREATE INDEX IF NOT EXISTS idx_evolution_logs_created_by ON evolution_logs(created_by) WHERE created_by IS NOT NULL;

COMMENT ON TABLE evolution_logs IS '进化日志表 - gatekeeper 风险评估后可追溯可回滚';
COMMENT ON COLUMN evolution_logs.risk_level IS 'low=直接写入 / medium=待管理员审批 / high=已拦截 / info=管理员回滚等系统动作';

-- ========================================
-- 3. 调性表（Tone System）
-- ========================================

CREATE TABLE IF NOT EXISTS ref_tones (
    id          UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    slug        TEXT NOT NULL UNIQUE,
    name        TEXT NOT NULL,
    description TEXT NOT NULL DEFAULT '',
    is_active   BOOLEAN NOT NULL DEFAULT true,
    sort_order  INTEGER NOT NULL DEFAULT 0
);

COMMENT ON TABLE ref_tones IS '故事基调表 - 项目向导选项 + 讨论室 tones 数据源';

CREATE TABLE IF NOT EXISTS ref_tone_rules (
    id         UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    tone_slug  TEXT NOT NULL,
    rule_type  TEXT NOT NULL,
    title      TEXT NOT NULL,
    content    TEXT NOT NULL,
    severity   TEXT NOT NULL DEFAULT 'warning',
    sort_order INTEGER NOT NULL DEFAULT 0
);

CREATE INDEX IF NOT EXISTS idx_ref_tone_rules_tone_slug ON ref_tone_rules(tone_slug);

COMMENT ON TABLE ref_tone_rules IS '基调关联规则表 - 项目创建时按基调批量写入 canon_rules';
COMMENT ON COLUMN ref_tone_rules.tone_slug IS '关联 ref_tones.slug，不建外键：删除基调时由 tone.delete 工具显式级联删除，避免迁移在已存在孤儿行的库上失败';

-- ========================================
-- 4. canon_rules 规则升级字段
-- ========================================

ALTER TABLE canon_rules ADD COLUMN IF NOT EXISTS promotion_status TEXT;
ALTER TABLE canon_rules ADD COLUMN IF NOT EXISTS promoted_to_global_id UUID REFERENCES global_rules(id) ON DELETE SET NULL;
ALTER TABLE canon_rules ADD COLUMN IF NOT EXISTS discussion_id TEXT;

COMMENT ON COLUMN canon_rules.promotion_status IS 'pending_review=待评估 / promoted=已升级为全局 / rejected=已拒绝';
COMMENT ON COLUMN canon_rules.promoted_to_global_id IS '升级后对应的 global_rules.id';

-- ========================================
-- 5. updated_at 触发器（复用 220 创建的 update_updated_at_column 函数）
-- ========================================

DROP TRIGGER IF EXISTS update_global_rules_updated_at ON global_rules;
CREATE TRIGGER update_global_rules_updated_at
    BEFORE UPDATE ON global_rules
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

-- ========================================
-- Migration Complete
-- ========================================

SELECT 'Migration 222_runtime_tables completed successfully' AS status;
