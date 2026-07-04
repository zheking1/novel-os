-- Migration 208: Restructure Knowledge Base Categories
-- 从 5 个一级分类 → 9 个新分类

-- Step 1: Create new top-level categories
INSERT INTO ref_categories (slug, name, description, parent_id, sort_order, is_system) VALUES
('character_ref', '角色参考', '角色模板、性格原型、命名规则', NULL, 1, true),
('equipment', '物品装备', '武器、防具、消耗品、材料、特殊物品', NULL, 2, true),
('creature', '生物生态', '智慧种族、野兽怪物、植物生态、生态规则', NULL, 3, true),
('world_setting', '世界设定', '地理结构、势力组织、社会制度、文化习俗', NULL, 4, true),
('power_system', '力量体系', '修炼等级、功法技能、阵法机关、规则限制', NULL, 5, true),
('history_culture', '历史文化', '历史事件、传说典故、人物传记、文明演进', NULL, 6, true),
('plot_ref', '情节参考', '剧情套路、结构模板、伏笔技巧、节奏参考', NULL, 7, true),
('writing_ref', '写作参考', '场景模板、风格指南、禁词规则', NULL, 8, true),
('general_material', '通用素材', '诗词对联、专业术语、经济货币', NULL, 9, true)
ON CONFLICT (slug) DO NOTHING;

-- Step 2: Create child categories for 角色参考
INSERT INTO ref_categories (slug, name, description, parent_id, sort_order, is_system)
SELECT 'char_template', '角色模板', '龙傲天/废柴流/霸总等原型', id, 1, true FROM ref_categories WHERE slug = 'character_ref'
ON CONFLICT (slug) DO NOTHING;

INSERT INTO ref_categories (slug, name, description, parent_id, sort_order, is_system)
SELECT 'char_personality', '性格原型', 'MBTI/九型人格/经典性格', id, 2, true FROM ref_categories WHERE slug = 'character_ref'
ON CONFLICT (slug) DO NOTHING;

INSERT INTO ref_categories (slug, name, description, parent_id, sort_order, is_system)
SELECT 'naming_rules', '命名规则', '人名/地名/功法名规则', id, 3, true FROM ref_categories WHERE slug = 'character_ref'
ON CONFLICT (slug) DO NOTHING;

-- Step 3: Create child categories for 物品装备
INSERT INTO ref_categories (slug, name, description, parent_id, sort_order, is_system)
SELECT 'weapon_template', '武器模板', '剑/枪/法杖/激光枪/符箓', id, 1, true FROM ref_categories WHERE slug = 'equipment'
ON CONFLICT (slug) DO NOTHING;

INSERT INTO ref_categories (slug, name, description, parent_id, sort_order, is_system)
SELECT 'armor_template', '防具模板', '铠甲/护盾/结界', id, 2, true FROM ref_categories WHERE slug = 'equipment'
ON CONFLICT (slug) DO NOTHING;

INSERT INTO ref_categories (slug, name, description, parent_id, sort_order, is_system)
SELECT 'consumable', '消耗品', '丹药/药剂/符咒/绷带', id, 3, true FROM ref_categories WHERE slug = 'equipment'
ON CONFLICT (slug) DO NOTHING;

INSERT INTO ref_categories (slug, name, description, parent_id, sort_order, is_system)
SELECT 'material_resource', '材料资源', '矿石/草药/零件/数据', id, 4, true FROM ref_categories WHERE slug = 'equipment'
ON CONFLICT (slug) DO NOTHING;

INSERT INTO ref_categories (slug, name, description, parent_id, sort_order, is_system)
SELECT 'special_item', '特殊物品', '神器/系统/金手指/异能', id, 5, true FROM ref_categories WHERE slug = 'equipment'
ON CONFLICT (slug) DO NOTHING;

-- Step 4: Create child categories for 生物生态
INSERT INTO ref_categories (slug, name, description, parent_id, sort_order, is_system)
SELECT 'intelligent_race', '智慧种族', '人族/妖族/精灵/AI/外星人', id, 1, true FROM ref_categories WHERE slug = 'creature'
ON CONFLICT (slug) DO NOTHING;

INSERT INTO ref_categories (slug, name, description, parent_id, sort_order, is_system)
SELECT 'beast_monster', '野兽怪物', '妖兽/丧尸/异兽/机械兽', id, 2, true FROM ref_categories WHERE slug = 'creature'
ON CONFLICT (slug) DO NOTHING;

INSERT INTO ref_categories (slug, name, description, parent_id, sort_order, is_system)
SELECT 'plant_ecology', '植物生态', '仙草/毒植/变异植物', id, 3, true FROM ref_categories WHERE slug = 'creature'
ON CONFLICT (slug) DO NOTHING;

INSERT INTO ref_categories (slug, name, description, parent_id, sort_order, is_system)
SELECT 'ecology_rules', '生态规则', '食物链/进化/变异', id, 4, true FROM ref_categories WHERE slug = 'creature'
ON CONFLICT (slug) DO NOTHING;

-- Step 5: Create child categories for 世界设定
INSERT INTO ref_categories (slug, name, description, parent_id, sort_order, is_system)
SELECT 'geography', '地理结构', '大陆/星球/位面/服务器', id, 1, true FROM ref_categories WHERE slug = 'world_setting'
ON CONFLICT (slug) DO NOTHING;

INSERT INTO ref_categories (slug, name, description, parent_id, sort_order, is_system)
SELECT 'faction_org', '势力组织', '宗门/公司/政府/公会', id, 2, true FROM ref_categories WHERE slug = 'world_setting'
ON CONFLICT (slug) DO NOTHING;

INSERT INTO ref_categories (slug, name, description, parent_id, sort_order, is_system)
SELECT 'social_system', '社会制度', '阶级/法律/经济/教育', id, 3, true FROM ref_categories WHERE slug = 'world_setting'
ON CONFLICT (slug) DO NOTHING;

INSERT INTO ref_categories (slug, name, description, parent_id, sort_order, is_system)
SELECT 'culture_custom', '文化习俗', '语言/节日/礼仪/禁忌', id, 4, true FROM ref_categories WHERE slug = 'world_setting'
ON CONFLICT (slug) DO NOTHING;

-- Step 6: Create child categories for 力量体系
INSERT INTO ref_categories (slug, name, description, parent_id, sort_order, is_system)
SELECT 'cultivation_level', '修炼等级', '炼气→元婴/基因锁/异能等级', id, 1, true FROM ref_categories WHERE slug = 'power_system'
ON CONFLICT (slug) DO NOTHING;

INSERT INTO ref_categories (slug, name, description, parent_id, sort_order, is_system)
SELECT 'skill_technique', '功法技能', '功法/武技/法术/科技/异能', id, 2, true FROM ref_categories WHERE slug = 'power_system'
ON CONFLICT (slug) DO NOTHING;

INSERT INTO ref_categories (slug, name, description, parent_id, sort_order, is_system)
SELECT 'array_mechanism', '阵法机关', '阵法/结界/科技装置/陷阱', id, 3, true FROM ref_categories WHERE slug = 'power_system'
ON CONFLICT (slug) DO NOTHING;

INSERT INTO ref_categories (slug, name, description, parent_id, sort_order, is_system)
SELECT 'rule_restriction', '规则限制', '天道/物理法则/系统限制', id, 4, true FROM ref_categories WHERE slug = 'power_system'
ON CONFLICT (slug) DO NOTHING;

-- Step 7: Create child categories for 历史文化
INSERT INTO ref_categories (slug, name, description, parent_id, sort_order, is_system)
SELECT 'historical_event', '历史事件', '战争/灾难/变革/传说', id, 1, true FROM ref_categories WHERE slug = 'history_culture'
ON CONFLICT (slug) DO NOTHING;

INSERT INTO ref_categories (slug, name, description, parent_id, sort_order, is_system)
SELECT 'legend_myth', '传说典故', '神话/上古/都市传说', id, 2, true FROM ref_categories WHERE slug = 'history_culture'
ON CONFLICT (slug) DO NOTHING;

INSERT INTO ref_categories (slug, name, description, parent_id, sort_order, is_system)
SELECT 'biography', '人物传记', '历史名人/传说人物', id, 3, true FROM ref_categories WHERE slug = 'history_culture'
ON CONFLICT (slug) DO NOTHING;

INSERT INTO ref_categories (slug, name, description, parent_id, sort_order, is_system)
SELECT 'civilization_evolution', '文明演进', '科技树/修炼史/种族史', id, 4, true FROM ref_categories WHERE slug = 'history_culture'
ON CONFLICT (slug) DO NOTHING;

-- Step 8: Create child categories for 情节参考
INSERT INTO ref_categories (slug, name, description, parent_id, sort_order, is_system)
SELECT 'plot_trope', '剧情套路', '退婚/逆袭/重生/穿越/系统', id, 1, true FROM ref_categories WHERE slug = 'plot_ref'
ON CONFLICT (slug) DO NOTHING;

INSERT INTO ref_categories (slug, name, description, parent_id, sort_order, is_system)
SELECT 'structure_template', '结构模板', '三幕式/英雄之旅/无限流', id, 2, true FROM ref_categories WHERE slug = 'plot_ref'
ON CONFLICT (slug) DO NOTHING;

INSERT INTO ref_categories (slug, name, description, parent_id, sort_order, is_system)
SELECT 'foreshadowing_tech', '伏笔技巧', '埋设/回收/误导', id, 3, true FROM ref_categories WHERE slug = 'plot_ref'
ON CONFLICT (slug) DO NOTHING;

INSERT INTO ref_categories (slug, name, description, parent_id, sort_order, is_system)
SELECT 'pacing_ref', '节奏参考', '高潮/过渡/日常/战斗', id, 4, true FROM ref_categories WHERE slug = 'plot_ref'
ON CONFLICT (slug) DO NOTHING;

-- Step 9: Create child categories for 写作参考
INSERT INTO ref_categories (slug, name, description, parent_id, sort_order, is_system)
SELECT 'scene_template', '场景模板', '战斗/对话/描写/日常', id, 1, true FROM ref_categories WHERE slug = 'writing_ref'
ON CONFLICT (slug) DO NOTHING;

INSERT INTO ref_categories (slug, name, description, parent_id, sort_order, is_system)
SELECT 'style_guide', '风格指南', '文风/语气/视角', id, 2, true FROM ref_categories WHERE slug = 'writing_ref'
ON CONFLICT (slug) DO NOTHING;

INSERT INTO ref_categories (slug, name, description, parent_id, sort_order, is_system)
SELECT 'forbidden_words', '禁词规则', '不能写的/敏感内容', id, 3, true FROM ref_categories WHERE slug = 'writing_ref'
ON CONFLICT (slug) DO NOTHING;

-- Step 10: Create child categories for 通用素材
INSERT INTO ref_categories (slug, name, description, parent_id, sort_order, is_system)
SELECT 'poetry_couplet', '诗词对联', '可化用的', id, 1, true FROM ref_categories WHERE slug = 'general_material'
ON CONFLICT (slug) DO NOTHING;

INSERT INTO ref_categories (slug, name, description, parent_id, sort_order, is_system)
SELECT 'terminology', '专业术语', '各领域的', id, 2, true FROM ref_categories WHERE slug = 'general_material'
ON CONFLICT (slug) DO NOTHING;

INSERT INTO ref_categories (slug, name, description, parent_id, sort_order, is_system)
SELECT 'economy_currency', '经济货币', '灵石/金币/信用点/积分', id, 3, true FROM ref_categories WHERE slug = 'general_material'
ON CONFLICT (slug) DO NOTHING;

-- Step 11: Migrate existing knowledge items to new categories
-- Map old slugs to new slugs
UPDATE universal_knowledge SET category = 'char_template' WHERE category IN ('kb_character', 'kb_male_protagonist', 'kb_female_protagonist', 'kb_antagonist');
UPDATE universal_knowledge SET category = 'naming_rules' WHERE category = 'kb_naming';
UPDATE universal_knowledge SET category = 'plot_trope' WHERE category IN ('kb_plot_templates', 'kb_plot_archetype', 'kb_core_conflict');
UPDATE universal_knowledge SET category = 'scene_template' WHERE category IN ('kb_scene', 'kb_scene_template');
UPDATE universal_knowledge SET category = 'structure_template' WHERE category IN ('kb_narrative', 'kb_story_complexity', 'kb_pacing');
UPDATE universal_knowledge SET category = 'style_guide' WHERE category IN ('kb_style', 'kb_language', 'kb_world_tone', 'kb_emotion', 'kb_platform_style');
UPDATE universal_knowledge SET category = 'cultivation_level' WHERE category = 'kb_skill';
UPDATE universal_knowledge SET category = 'geography' WHERE category = 'kb_setting_background';
UPDATE universal_knowledge SET category = 'historical_event' WHERE category IN ('historical_figure', 'historical_event', 'historical_process', 'historical_geo');
UPDATE universal_knowledge SET category = 'social_system' WHERE category IN ('politics', 'economy', 'society');
UPDATE universal_knowledge SET category = 'culture_custom' WHERE category = 'culture';
UPDATE universal_knowledge SET category = 'terminology' WHERE category = 'technology';
UPDATE universal_knowledge SET category = 'char_template' WHERE category = 'kb_era_setting';
UPDATE universal_knowledge SET category = 'plot_trope' WHERE category = 'kb_ending_types';
UPDATE universal_knowledge SET category = 'char_template' WHERE category = 'kb_genre';
UPDATE universal_knowledge SET category = 'special_item' WHERE category = 'kb_cheat_types';
UPDATE universal_knowledge SET category = 'char_personality' WHERE category = 'kb_identity';
UPDATE universal_knowledge SET category = 'structure_template' WHERE category = 'kb_title_structure';
UPDATE universal_knowledge SET category = 'style_guide' WHERE category = 'kb_theme';
UPDATE universal_knowledge SET category = 'style_guide' WHERE category = 'kb_reader_groups';

-- Step 12: Update genre_tags for new categories
-- (genre_tags are used for filtering by novel type)
