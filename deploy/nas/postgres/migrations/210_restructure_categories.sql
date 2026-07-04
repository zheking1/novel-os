-- Migration 210: Restructure knowledge categories (3-5 levels) + tags
-- 基于 1493 条数据重新设计分类体系

-- ==================== 1. 剧情套路 (plot_trope: 800条) ====================
-- 原分类太粗，细分为 4 级

-- 一级：情节参考 (plot_ref) - 已存在
-- 二级：剧情套路 (plot_trope) - 已存在

-- 三级分类
INSERT INTO ref_categories (slug, name, description, parent_id, sort_order, is_system)
SELECT 'trope_core', '核心套路', '主线剧情核心套路', id, 1, true FROM ref_categories WHERE slug = 'plot_trope'
ON CONFLICT (slug) DO NOTHING;

INSERT INTO ref_categories (slug, name, description, parent_id, sort_order, is_system)
SELECT 'trope_emotion', '情感套路', '感情线相关套路', id, 2, true FROM ref_categories WHERE slug = 'plot_trope'
ON CONFLICT (slug) DO NOTHING;

INSERT INTO ref_categories (slug, name, description, parent_id, sort_order, is_system)
SELECT 'trope_conflict', '冲突套路', '矛盾冲突相关套路', id, 3, true FROM ref_categories WHERE slug = 'plot_trope'
ON CONFLICT (slug) DO NOTHING;

INSERT INTO ref_categories (slug, name, description, parent_id, sort_order, is_system)
SELECT 'trope_growth', '成长套路', '主角成长相关套路', id, 4, true FROM ref_categories WHERE slug = 'plot_trope'
ON CONFLICT (slug) DO NOTHING;

INSERT INTO ref_categories (slug, name, description, parent_id, sort_order, is_system)
SELECT 'trope_daily', '日常套路', '日常/轻松相关套路', id, 5, true FROM ref_categories WHERE slug = 'plot_trope'
ON CONFLICT (slug) DO NOTHING;

INSERT INTO ref_categories (slug, name, description, parent_id, sort_order, is_system)
SELECT 'trope_suspense', '悬疑套路', '悬疑/反转相关套路', id, 6, true FROM ref_categories WHERE slug = 'plot_trope'
ON CONFLICT (slug) DO NOTHING;

-- ==================== 2. 角色模板 (char_template: 353条) ====================
INSERT INTO ref_categories (slug, name, description, parent_id, sort_order, is_system)
SELECT 'char_protagonist', '主角模板', '主角类型模板', id, 1, true FROM ref_categories WHERE slug = 'char_template'
ON CONFLICT (slug) DO NOTHING;

INSERT INTO ref_categories (slug, name, description, parent_id, sort_order, is_system)
SELECT 'char_supporting', '配角模板', '配角类型模板', id, 2, true FROM ref_categories WHERE slug = 'char_template'
ON CONFLICT (slug) DO NOTHING;

INSERT INTO ref_categories (slug, name, description, parent_id, sort_order, is_system)
SELECT 'char_antagonist', '反派模板', '反派类型模板', id, 3, true FROM ref_categories WHERE slug = 'char_template'
ON CONFLICT (slug) DO NOTHING;

INSERT INTO ref_categories (slug, name, description, parent_id, sort_order, is_system)
SELECT 'char_group', '群像模板', '群体角色模板', id, 4, true FROM ref_categories WHERE slug = 'char_template'
ON CONFLICT (slug) DO NOTHING;

-- ==================== 3. 地理设定 (geography: 160条) ====================
INSERT INTO ref_categories (slug, name, description, parent_id, sort_order, is_system)
SELECT 'geo_natural', '自然地理', '山川河流/气候/地形', id, 1, true FROM ref_categories WHERE slug = 'geography'
ON CONFLICT (slug) DO NOTHING;

INSERT INTO ref_categories (slug, name, description, parent_id, sort_order, is_system)
SELECT 'geo_city', '城市建筑', '城市/宗门/建筑', id, 2, true FROM ref_categories WHERE slug = 'geography'
ON CONFLICT (slug) DO NOTHING;

INSERT INTO ref_categories (slug, name, description, parent_id, sort_order, is_system)
SELECT 'geo_region', '区域设定', '大陆/国家/区域', id, 3, true FROM ref_categories WHERE slug = 'geography'
ON CONFLICT (slug) DO NOTHING;

INSERT INTO ref_categories (slug, name, description, parent_id, sort_order, is_system)
SELECT 'geo_special', '特殊地点', '秘境/遗迹/禁地', id, 4, true FROM ref_categories WHERE slug = 'geography'
ON CONFLICT (slug) DO NOTHING;

-- ==================== 4. 性格原型 (char_personality: 50条) ====================
INSERT INTO ref_categories (slug, name, description, parent_id, sort_order, is_system)
SELECT 'personality_inner', '内在性格', '性格特征/心理', id, 1, true FROM ref_categories WHERE slug = 'char_personality'
ON CONFLICT (slug) DO NOTHING;

INSERT INTO ref_categories (slug, name, description, parent_id, sort_order, is_system)
SELECT 'personality_social', '社会身份', '职业/身份/地位', id, 2, true FROM ref_categories WHERE slug = 'char_personality'
ON CONFLICT (slug) DO NOTHING;

-- ==================== 5. 特殊物品 (special_item: 50条) ====================
INSERT INTO ref_categories (slug, name, description, parent_id, sort_order, is_system)
SELECT 'item_cheat', '金手指', '系统/外挂/特殊能力', id, 1, true FROM ref_categories WHERE slug = 'special_item'
ON CONFLICT (slug) DO NOTHING;

INSERT INTO ref_categories (slug, name, description, parent_id, sort_order, is_system)
SELECT 'item_treasure', '宝物道具', '法宝/神器/特殊物品', id, 2, true FROM ref_categories WHERE slug = 'special_item'
ON CONFLICT (slug) DO NOTHING;

INSERT INTO ref_categories (slug, name, description, parent_id, sort_order, is_system)
SELECT 'item_world', '世界设定', '世界观/背景/时代', id, 3, true FROM ref_categories WHERE slug = 'special_item'
ON CONFLICT (slug) DO NOTHING;

-- ==================== 6. 结构模板 (structure_template: 50条) ====================
INSERT INTO ref_categories (slug, name, description, parent_id, sort_order, is_system)
SELECT 'struct_opening', '开局结构', '开篇/引入/设定', id, 1, true FROM ref_categories WHERE slug = 'structure_template'
ON CONFLICT (slug) DO NOTHING;

INSERT INTO ref_categories (slug, name, description, parent_id, sort_order, is_system)
SELECT 'struct_middle', '中段结构', '发展/高潮/转折', id, 2, true FROM ref_categories WHERE slug = 'structure_template'
ON CONFLICT (slug) DO NOTHING;

INSERT INTO ref_categories (slug, name, description, parent_id, sort_order, is_system)
SELECT 'struct_ending', '结局结构', '收尾/伏笔回收', id, 3, true FROM ref_categories WHERE slug = 'structure_template'
ON CONFLICT (slug) DO NOTHING;

-- ==================== 7. 风格指南 (style_guide: 18条) ====================
INSERT INTO ref_categories (slug, name, description, parent_id, sort_order, is_system)
SELECT 'style_platform', '平台风格', '各平台文风要求', id, 1, true FROM ref_categories WHERE slug = 'style_guide'
ON CONFLICT (slug) DO NOTHING;

INSERT INTO ref_categories (slug, name, description, parent_id, sort_order, is_system)
SELECT 'style_genre', '类型风格', '不同小说类型风格', id, 2, true FROM ref_categories WHERE slug = 'style_guide'
ON CONFLICT (slug) DO NOTHING;

-- ==================== 8. 写作参考 (writing_ref: 11条) ====================
-- 这些条目内容混杂，需要重新分类
-- 伏笔相关 → 情节参考/伏笔技巧
-- 角色相关 → 角色参考
-- 风格相关 → 写作参考/风格指南

-- ==================== 9. 命名规则 (naming_rules: 1条) ====================
-- 保持原样

-- ==================== 10. 创建标签表 ====================
CREATE TABLE IF NOT EXISTS knowledge_tags (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    item_id UUID NOT NULL,
    tag VARCHAR(50) NOT NULL,
    tag_type VARCHAR(20) DEFAULT 'content',  -- content/emotion/style/technique/character/scene
    created_at TIMESTAMP DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_knowledge_tags_item ON knowledge_tags(item_id);
CREATE INDEX IF NOT EXISTS idx_knowledge_tags_tag ON knowledge_tags(tag);
CREATE INDEX IF NOT EXISTS idx_knowledge_tags_type ON knowledge_tags(tag_type);
