-- Migration 209: Fix child category parent_id
-- 强制更新所有子分类的 parent_id 指向正确的父分类

-- 角色参考 (character_ref)
UPDATE ref_categories SET parent_id = (
    SELECT id FROM ref_categories WHERE slug = 'character_ref'
) WHERE slug IN ('char_template', 'char_personality', 'naming_rules')
AND parent_id IS DISTINCT FROM (SELECT id FROM ref_categories WHERE slug = 'character_ref');

-- 物品装备 (equipment)
UPDATE ref_categories SET parent_id = (
    SELECT id FROM ref_categories WHERE slug = 'equipment'
) WHERE slug IN ('weapon_template', 'armor_template', 'consumable', 'material_resource', 'special_item')
AND parent_id IS DISTINCT FROM (SELECT id FROM ref_categories WHERE slug = 'equipment');

-- 生物生态 (creature)
UPDATE ref_categories SET parent_id = (
    SELECT id FROM ref_categories WHERE slug = 'creature'
) WHERE slug IN ('intelligent_race', 'beast_monster', 'plant_ecology', 'ecology_rules')
AND parent_id IS DISTINCT FROM (SELECT id FROM ref_categories WHERE slug = 'creature');

-- 世界设定 (world_setting)
UPDATE ref_categories SET parent_id = (
    SELECT id FROM ref_categories WHERE slug = 'world_setting'
) WHERE slug IN ('geography', 'faction_org', 'social_system', 'culture_custom')
AND parent_id IS DISTINCT FROM (SELECT id FROM ref_categories WHERE slug = 'world_setting');

-- 力量体系 (power_system)
UPDATE ref_categories SET parent_id = (
    SELECT id FROM ref_categories WHERE slug = 'power_system'
) WHERE slug IN ('cultivation_level', 'skill_technique', 'array_mechanism', 'rule_restriction')
AND parent_id IS DISTINCT FROM (SELECT id FROM ref_categories WHERE slug = 'power_system');

-- 历史文化 (history_culture)
UPDATE ref_categories SET parent_id = (
    SELECT id FROM ref_categories WHERE slug = 'history_culture'
) WHERE slug IN ('historical_event', 'legend_myth', 'biography', 'civilization_evolution')
AND parent_id IS DISTINCT FROM (SELECT id FROM ref_categories WHERE slug = 'history_culture');

-- 情节参考 (plot_ref)
UPDATE ref_categories SET parent_id = (
    SELECT id FROM ref_categories WHERE slug = 'plot_ref'
) WHERE slug IN ('plot_trope', 'structure_template', 'foreshadowing_tech', 'pacing_ref')
AND parent_id IS DISTINCT FROM (SELECT id FROM ref_categories WHERE slug = 'plot_ref');

-- 写作参考 (writing_ref)
UPDATE ref_categories SET parent_id = (
    SELECT id FROM ref_categories WHERE slug = 'writing_ref'
) WHERE slug IN ('scene_template', 'style_guide', 'forbidden_words')
AND parent_id IS DISTINCT FROM (SELECT id FROM ref_categories WHERE slug = 'writing_ref');

-- 通用素材 (general_material)
UPDATE ref_categories SET parent_id = (
    SELECT id FROM ref_categories WHERE slug = 'general_material'
) WHERE slug IN ('poetry_couplet', 'terminology', 'economy_currency')
AND parent_id IS DISTINCT FROM (SELECT id FROM ref_categories WHERE slug = 'general_material');
