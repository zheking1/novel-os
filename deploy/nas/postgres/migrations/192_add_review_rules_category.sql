-- =============================================
-- 192_add_review_rules_category.sql
-- 添加审查规则分类并修正数据
-- =============================================

-- 1. 创建审查规则分类
INSERT INTO categories (slug, name, name_en, description, icon, color, sort_order, is_system)
VALUES ('review_rules', '审查规则', 'Review Rules', 'AI生成小说的质量审查规则和标准', '🔍', '#dc2626', 9, true)
ON CONFLICT (slug) DO UPDATE SET
    name = EXCLUDED.name,
    name_en = EXCLUDED.name_en,
    description = EXCLUDED.description,
    icon = EXCLUDED.icon,
    color = EXCLUDED.color;

-- 2. 获取新分类ID
WITH review_cat AS (
    SELECT id FROM categories WHERE slug = 'review_rules'
)

-- 3. 修正 RS 编号并移动到审查规则分类
UPDATE knowledge_base
SET 
    code = SUBSTRING(code FROM 4),
    category_id = (SELECT id FROM review_cat)
WHERE source = 'opencode' AND code LIKE 'RS-RS-%';

-- 4. 统计结果
SELECT 
    (SELECT COUNT(*) FROM knowledge_base WHERE source = 'opencode' AND code LIKE 'RS-%') AS rs_count,
    (SELECT COUNT(*) FROM knowledge_base WHERE source = 'opencode' AND code LIKE 'GR-%') AS gr_count,
    (SELECT COUNT(*) FROM knowledge_base WHERE source = 'opencode' AND category_slug = 'review_rules') AS review_rules_count;