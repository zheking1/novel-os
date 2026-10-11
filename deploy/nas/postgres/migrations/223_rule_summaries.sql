-- Migration: 223_rule_summaries.sql
-- Description: 规则归纳摘要表（动态规则检索方案），规则条数超阈值时由 LLM 按 rule_group 归并后写入
-- Date: 2026-10-10
-- Depends: 222_runtime_tables.sql
-- 背景: 见 docs/07-planning/dynamic-rules-retrieval.md §2.7 与 roadmap 阶段 3（D-08）
--
-- 注意: 当前代码尚未引用此表，仅随动态规则检索方案一并落地。

CREATE TABLE IF NOT EXISTS rule_summaries (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    project_id      UUID REFERENCES projects(id) ON DELETE CASCADE,
    rule_group      TEXT NOT NULL,     -- power_system / world_building / character_setting / ...
    genre           TEXT,
    summary         TEXT NOT NULL,
    source_rule_ids TEXT[],            -- 被归纳的原始规则 id，便于追溯
    created_at      TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE INDEX IF NOT EXISTS idx_rule_summaries_lookup ON rule_summaries(project_id, rule_group, genre, created_at DESC);

COMMENT ON TABLE rule_summaries IS '规则归纳摘要表 - 规则过多时按 rule_group 归并，替代逐条注入';
COMMENT ON COLUMN rule_summaries.source_rule_ids IS '参与本次归纳的原始 canon_rules.id 列表';

SELECT 'Migration 223_rule_summaries completed successfully' AS status;
