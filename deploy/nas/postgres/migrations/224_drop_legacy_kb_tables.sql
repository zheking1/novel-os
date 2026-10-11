-- Migration: 224_drop_legacy_kb_tables.sql
-- Description: 删除旧知识体系的 5 张废弃表（roadmap 阶段 1 / D-10）
-- Date: 2026-10-10
-- Depends: 223_rule_summaries.sql
-- 背景: docs/07-planning/roadmap.md 阶段 1；设计见 docs/07-planning/category-unification.md §2.1
--
-- ⚠️⚠️ 本迁移是破坏性的，不可回滚。执行前必须完成：
--
--   1. 确认阶段 1-A（context.py 解耦 knowledge_base）已部署并验证通过
--   2. 逐表备份（--data-only，保留结构）：
--        docker exec -i novel-postgres pg_dump -U novel_os -d novel_os \
--          --data-only -t categories -t setting_category_relations \
--          -t genre_category_bindings -t knowledge_tags -t knowledge_vectors \
--          > /tmp/legacy_kb_tables_backup_$(date +%Y%m%d).sql
--   3. 确认应用已停写（本迁移只删表，不涉及业务写入，但避免并发报错）
--
-- 已核实（2026-10-10）：
--   - 5 张表在 novel-os-mcp/src 下的 Python 代码引用数均为 0
--   - 前端 js/pages 下也无任何调用
--   - genre_category_bindings 在仓库 SQL 中没有 CREATE 语句，可能不存在；IF EXISTS 会安全跳过
--   - knowledge_tags 实际结构是 190 的联合表（knowledge_id + tag_id），
--     210 的独立表（item_id/tag/tag_type）因 IF NOT EXISTS 从未被创建
--
-- 保留（不要删）：
--   - knowledge_base  —— 孤儿表，category-unification 明确保留
--   - tags            —— 未列入删除清单
--   - setting_categories —— settings 体系在用，本迁移只删它的关联表 setting_category_relations

-- ========================================
-- 1. 解除 knowledge_base → categories 的外键
--    knowledge_base.category_id REFERENCES categories(id)，
--    不先解除的话 DROP TABLE categories 会被拒绝。
--    约束名是建表时自动生成的，这里动态查找，避免硬编码名字不匹配。
-- ========================================

DO $$
DECLARE
    fk_name TEXT;
BEGIN
    FOR fk_name IN
        SELECT conname
        FROM pg_constraint
        WHERE conrelid = 'knowledge_base'::regclass
          AND contype = 'f'
          AND confrelid = 'categories'::regclass
    LOOP
        EXECUTE format('ALTER TABLE knowledge_base DROP CONSTRAINT %I', fk_name);
        RAISE NOTICE 'dropped FK % on knowledge_base', fk_name;
    END LOOP;
END $$;

-- ========================================
-- 2. 删除废弃表
--    顺序：先删引用别人的表，再删被引用表（categories）
-- ========================================

DROP TABLE IF EXISTS knowledge_tags;
DROP TABLE IF EXISTS knowledge_vectors;
DROP TABLE IF EXISTS setting_category_relations;
DROP TABLE IF EXISTS genre_category_bindings;
DROP TABLE IF EXISTS categories;

-- ========================================
-- Migration Complete
-- ========================================

SELECT 'Migration 224_drop_legacy_kb_tables completed successfully' AS status;
