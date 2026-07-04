-- Migration 211: Re-categorize items into sub-categories
-- 基于内容关键词自动分配

-- plot_trope → 子分类
UPDATE universal_knowledge SET category_id = (
    SELECT id FROM ref_categories WHERE slug = 'trope_core'
) WHERE category_id = (SELECT id FROM ref_categories WHERE slug = 'plot_trope')
AND (
    topic ILIKE '%主线%' OR topic ILIKE '%核心%' OR topic ILIKE '%剧情%' OR
    topic ILIKE '%故事%' OR topic ILIKE '%主轴%' OR topic ILIKE '%大纲%' OR
    content ILIKE '%主线%' OR content ILIKE '%核心%'
);

UPDATE universal_knowledge SET category_id = (
    SELECT id FROM ref_categories WHERE slug = 'trope_emotion'
) WHERE category_id = (SELECT id FROM ref_categories WHERE slug = 'plot_trope')
AND (
    topic ILIKE '%感情%' OR topic ILIKE '%恋爱%' OR topic ILIKE '%情感%' OR
    topic ILIKE '%CP%' OR topic ILIKE '%爱情%' OR topic ILIKE '%暧昧%' OR
    content ILIKE '%感情%' OR content ILIKE '%恋爱%'
);

UPDATE universal_knowledge SET category_id = (
    SELECT id FROM ref_categories WHERE slug = 'trope_conflict'
) WHERE category_id = (SELECT id FROM ref_categories WHERE slug = 'plot_trope')
AND (
    topic ILIKE '%冲突%' OR topic ILIKE '%矛盾%' OR topic ILIKE '%对战%' OR
    topic ILIKE '%战斗%' OR topic ILIKE '%对决%' OR topic ILIKE '%斗争%' OR
    content ILIKE '%冲突%' OR content ILIKE '%矛盾%'
);

UPDATE universal_knowledge SET category_id = (
    SELECT id FROM ref_categories WHERE slug = 'trope_growth'
) WHERE category_id = (SELECT id FROM ref_categories WHERE slug = 'plot_trope')
AND (
    topic ILIKE '%成长%' OR topic ILIKE '%升级%' OR topic ILIKE '%突破%' OR
    topic ILIKE '%进阶%' OR topic ILIKE '%修炼%' OR topic ILIKE '%变强%' OR
    content ILIKE '%成长%' OR content ILIKE '%升级%'
);

UPDATE universal_knowledge SET category_id = (
    SELECT id FROM ref_categories WHERE slug = 'trope_daily'
) WHERE category_id = (SELECT id FROM ref_categories WHERE slug = 'plot_trope')
AND (
    topic ILIKE '%日常%' OR topic ILIKE '%轻松%' OR topic ILIKE '%搞笑%' OR
    topic ILIKE '%休闲%' OR topic ILIKE '%生活%' OR
    content ILIKE '%日常%' OR content ILIKE '%轻松%'
);

UPDATE universal_knowledge SET category_id = (
    SELECT id FROM ref_categories WHERE slug = 'trope_suspense'
) WHERE category_id = (SELECT id FROM ref_categories WHERE slug = 'plot_trope')
AND (
    topic ILIKE '%悬疑%' OR topic ILIKE '%反转%' OR topic ILIKE '%谜团%' OR
    topic ILIKE '%伏笔%' OR topic ILIKE '%揭秘%' OR topic ILIKE '%真相%' OR
    content ILIKE '%悬疑%' OR content ILIKE '%反转%'
);

-- char_template → 子分类
UPDATE universal_knowledge SET category_id = (
    SELECT id FROM ref_categories WHERE slug = 'char_protagonist'
) WHERE category_id = (SELECT id FROM ref_categories WHERE slug = 'char_template')
AND (
    topic ILIKE '%主角%' OR topic ILIKE '%男主%' OR topic ILIKE '%女主%' OR
    topic ILIKE '%主人公%' OR topic ILIKE '%龙傲天%' OR topic ILIKE '%废柴%' OR
    content ILIKE '%主角%' OR content ILIKE '%男主%'
);

UPDATE universal_knowledge SET category_id = (
    SELECT id FROM ref_categories WHERE slug = 'char_supporting'
) WHERE category_id = (SELECT id FROM ref_categories WHERE slug = 'char_template')
AND (
    topic ILIKE '%配角%' OR topic ILIKE '%女配%' OR topic ILIKE '%男配%' OR
    topic ILIKE '%师兄%' OR topic ILIKE '%师妹%' OR topic ILIKE '%朋友%' OR
    content ILIKE '%配角%'
);

UPDATE universal_knowledge SET category_id = (
    SELECT id FROM ref_categories WHERE slug = 'char_antagonist'
) WHERE category_id = (SELECT id FROM ref_categories WHERE slug = 'char_template')
AND (
    topic ILIKE '%反派%' OR topic ILIKE '%敌人%' OR topic ILIKE '%BOSS%' OR
    topic ILIKE '%魔王%' OR topic ILIKE '%恶人%' OR
    content ILIKE '%反派%' OR content ILIKE '%敌人%'
);

UPDATE universal_knowledge SET category_id = (
    SELECT id FROM ref_categories WHERE slug = 'char_group'
) WHERE category_id = (SELECT id FROM ref_categories WHERE slug = 'char_template')
AND (
    topic ILIKE '%群像%' OR topic ILIKE '%团队%' OR topic ILIKE '%宗门%' OR
    topic ILIKE '%家族%' OR topic ILIKE '%组织%' OR
    content ILIKE '%群像%'
);

-- geography → 子分类
UPDATE universal_knowledge SET category_id = (
    SELECT id FROM ref_categories WHERE slug = 'geo_natural'
) WHERE category_id = (SELECT id FROM ref_categories WHERE slug = 'geography')
AND (
    topic ILIKE '%山%' OR topic ILIKE '%河%' OR topic ILIKE '%气候%' OR
    topic ILIKE '%地形%' OR topic ILIKE '%森林%' OR topic ILIKE '%海洋%' OR
    content ILIKE '%山脉%' OR content ILIKE '%河流%'
);

UPDATE universal_knowledge SET category_id = (
    SELECT id FROM ref_categories WHERE slug = 'geo_city'
) WHERE category_id = (SELECT id FROM ref_categories WHERE slug = 'geography')
AND (
    topic ILIKE '%城市%' OR topic ILIKE '%宗门%' OR topic ILIKE '%建筑%' OR
    topic ILIKE '%城镇%' OR topic ILIKE '%学院%' OR
    content ILIKE '%城市%' OR content ILIKE '%宗门%'
);

UPDATE universal_knowledge SET category_id = (
    SELECT id FROM ref_categories WHERE slug = 'geo_region'
) WHERE category_id = (SELECT id FROM ref_categories WHERE slug = 'geography')
AND (
    topic ILIKE '%大陆%' OR topic ILIKE '%国家%' OR topic ILIKE '%区域%' OR
    topic ILIKE '%帝国%' OR topic ILIKE '%州%' OR
    content ILIKE '%大陆%' OR content ILIKE '%国家%'
);

UPDATE universal_knowledge SET category_id = (
    SELECT id FROM ref_categories WHERE slug = 'geo_special'
) WHERE category_id = (SELECT id FROM ref_categories WHERE slug = 'geography')
AND (
    topic ILIKE '%秘境%' OR topic ILIKE '%遗迹%' OR topic ILIKE '%禁地%' OR
    topic ILIKE '%洞府%' OR topic ILIKE '%古墓%' OR
    content ILIKE '%秘境%' OR content ILIKE '%遗迹%'
);

-- special_item → 子分类
UPDATE universal_knowledge SET category_id = (
    SELECT id FROM ref_categories WHERE slug = 'item_cheat'
) WHERE category_id = (SELECT id FROM ref_categories WHERE slug = 'special_item')
AND (
    topic ILIKE '%系统%' OR topic ILIKE '%金手指%' OR topic ILIKE '%外挂%' OR
    topic ILIKE '%异能%' OR topic ILIKE '%特殊能力%' OR
    content ILIKE '%系统%' OR content ILIKE '%金手指%'
);

UPDATE universal_knowledge SET category_id = (
    SELECT id FROM ref_categories WHERE slug = 'item_treasure'
) WHERE category_id = (SELECT id FROM ref_categories WHERE slug = 'special_item')
AND (
    topic ILIKE '%法宝%' OR topic ILIKE '%神器%' OR topic ILIKE '%宝物%' OR
    topic ILIKE '%武器%' OR topic ILIKE '%丹药%' OR
    content ILIKE '%法宝%' OR content ILIKE '%神器%'
);

UPDATE universal_knowledge SET category_id = (
    SELECT id FROM ref_categories WHERE slug = 'item_world'
) WHERE category_id = (SELECT id FROM ref_categories WHERE slug = 'special_item')
AND (
    topic ILIKE '%世界%' OR topic ILIKE '%背景%' OR topic ILIKE '%时代%' OR
    topic ILIKE '%设定%' OR topic ILIKE '%世界观%' OR
    content ILIKE '%世界观%' OR content ILIKE '%背景%'
);

-- structure_template → 子分类
UPDATE universal_knowledge SET category_id = (
    SELECT id FROM ref_categories WHERE slug = 'struct_opening'
) WHERE category_id = (SELECT id FROM ref_categories WHERE slug = 'structure_template')
AND (
    topic ILIKE '%开局%' OR topic ILIKE '%开篇%' OR topic ILIKE '%引入%' OR
    topic ILIKE '%第一章%' OR topic ILIKE '%起始%' OR
    content ILIKE '%开局%' OR content ILIKE '%开篇%'
);

UPDATE universal_knowledge SET category_id = (
    SELECT id FROM ref_categories WHERE slug = 'struct_middle'
) WHERE category_id = (SELECT id FROM ref_categories WHERE slug = 'structure_template')
AND (
    topic ILIKE '%中段%' OR topic ILIKE '%发展%' OR topic ILIKE '%高潮%' OR
    topic ILIKE '%转折%' OR topic ILIKE '%中期%' OR
    content ILIKE '%高潮%' OR content ILIKE '%转折%'
);

UPDATE universal_knowledge SET category_id = (
    SELECT id FROM ref_categories WHERE slug = 'struct_ending'
) WHERE category_id = (SELECT id FROM ref_categories WHERE slug = 'structure_template')
AND (
    topic ILIKE '%结局%' OR topic ILIKE '%收尾%' OR topic ILIKE '%结尾%' OR
    topic ILIKE '%完结%' OR topic ILIKE '%终章%' OR
    content ILIKE '%结局%' OR content ILIKE '%收尾%'
);

-- style_guide → 子分类
UPDATE universal_knowledge SET category_id = (
    SELECT id FROM ref_categories WHERE slug = 'style_platform'
) WHERE category_id = (SELECT id FROM ref_categories WHERE slug = 'style_guide')
AND (
    topic ILIKE '%平台%' OR topic ILIKE '%起点%' OR topic ILIKE '%番茄%' OR
    topic ILIKE '%纵横%' OR topic ILIKE '%晋江%' OR
    content ILIKE '%平台%'
);

UPDATE universal_knowledge SET category_id = (
    SELECT id FROM ref_categories WHERE slug = 'style_genre'
) WHERE category_id = (SELECT id FROM ref_categories WHERE slug = 'style_guide')
AND (
    topic ILIKE '%风格%' OR topic ILIKE '%类型%' OR topic ILIKE '%玄幻%' OR
    topic ILIKE '%都市%' OR topic ILIKE '%科幻%' OR
    content ILIKE '%风格%' OR content ILIKE '%类型%'
);

-- char_personality → 子分类
UPDATE universal_knowledge SET category_id = (
    SELECT id FROM ref_categories WHERE slug = 'personality_inner'
) WHERE category_id = (SELECT id FROM ref_categories WHERE slug = 'char_personality')
AND (
    topic ILIKE '%性格%' OR topic ILIKE '%心理%' OR topic ILIKE '%内向%' OR
    topic ILIKE '%外向%' OR topic ILIKE '%冷静%' OR
    content ILIKE '%性格%'
);

UPDATE universal_knowledge SET category_id = (
    SELECT id FROM ref_categories WHERE slug = 'personality_social'
) WHERE category_id = (SELECT id FROM ref_categories WHERE slug = 'char_personality')
AND (
    topic ILIKE '%职业%' OR topic ILIKE '%身份%' OR topic ILIKE '%地位%' OR
    topic ILIKE '%医生%' OR topic ILIKE '%教师%' OR topic ILIKE '%军人%' OR
    content ILIKE '%职业%'
);
