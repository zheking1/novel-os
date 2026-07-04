-- =============================================
-- Novel OS PRESETS分类扩展迁移脚本
-- Version: 1.0
-- Date: 2026-06-30
-- Description: 为PRESETS.md数据创建新的分类体系
-- =============================================

BEGIN;

-- =============================================
-- 1. 新增大类：世界观设计
-- =============================================

INSERT INTO categories (slug, name, name_en, description, icon, color, sort_order, is_system) VALUES
('world_design', '世界观设计', 'World Design', '世界观基调、年代设定、核心冲突、主题深度等', 'globe', '#8BC34A', 11, true)
ON CONFLICT (slug) DO NOTHING;

-- =============================================
-- 2. 新增大类：读者分析
-- =============================================

INSERT INTO categories (slug, name, name_en, description, icon, color, sort_order, is_system) VALUES
('reader_analysis', '读者分析', 'Reader Analysis', '读者群体定位、发表平台风格等', 'users', '#FFC107', 12, true)
ON CONFLICT (slug) DO NOTHING;

-- =============================================
-- 3. 新增大类：情节模板
-- =============================================

INSERT INTO categories (slug, name, name_en, description, icon, color, sort_order, is_system) VALUES
('plot_templates', '情节模板', 'Plot Templates', '成长/感情/冒险/权谋/悬疑/日常等情节模板', 'grid', '#E91E63', 13, true)
ON CONFLICT (slug) DO NOTHING;

-- =============================================
-- 4. 新增二级分类：世界观设计 -> 世界观基调
-- =============================================

INSERT INTO categories (slug, name, name_en, description, icon, color, sort_order, parent_id, is_system) VALUES
('world_tone', '世界观基调', 'World Tone', '希望/绝望/灰色/冷峻等世界观氛围基调', 'palette', '#4CAF50', 1, (SELECT id FROM categories WHERE slug = 'world_design'), true)
ON CONFLICT (slug) DO NOTHING;

-- =============================================
-- 5. 新增二级分类：世界观设计 -> 年代设定
-- =============================================

INSERT INTO categories (slug, name, name_en, description, icon, color, sort_order, parent_id, is_system) VALUES
('era_setting', '年代设定', 'Era Setting', '远古/古代/民国/现代/未来等时间设定', 'clock', '#2196F3', 2, (SELECT id FROM categories WHERE slug = 'world_design'), true)
ON CONFLICT (slug) DO NOTHING;

-- =============================================
-- 6. 新增二级分类：世界观设计 -> 核心冲突
-- =============================================

INSERT INTO categories (slug, name, name_en, description, icon, color, sort_order, parent_id, is_system) VALUES
('core_conflict', '核心冲突', 'Core Conflict', '人与天命/社会/他人/自我等核心冲突类型', 'swords', '#FF9800', 3, (SELECT id FROM categories WHERE slug = 'world_design'), true)
ON CONFLICT (slug) DO NOTHING;

-- =============================================
-- 7. 新增二级分类：世界观设计 -> 主题深度
-- =============================================

INSERT INTO categories (slug, name, name_en, description, icon, color, sort_order, parent_id, is_system) VALUES
('theme_depth', '主题深度', 'Theme Depth', '娱乐/社会/哲学/伦理等主题深度层级', 'lightbulb', '#9C27B0', 4, (SELECT id FROM categories WHERE slug = 'world_design'), true)
ON CONFLICT (slug) DO NOTHING;

-- =============================================
-- 8. 新增二级分类：世界观设计 -> 情感驱动力
-- =============================================

INSERT INTO categories (slug, name, name_en, description, icon, color, sort_order, parent_id, is_system) VALUES
('emotion_driver', '情感驱动力', 'Emotion Driver', '复仇/救赎/守护等情感驱动类型', 'heart', '#E91E63', 5, (SELECT id FROM categories WHERE slug = 'world_design'), true)
ON CONFLICT (slug) DO NOTHING;

-- =============================================
-- 9. 新增二级分类：世界观设计 -> 故事复杂度
-- =============================================

INSERT INTO categories (slug, name, name_en, description, icon, color, sort_order, parent_id, is_system) VALUES
('story_complexity', '故事复杂度', 'Story Complexity', '纯爽文/轻悬疑/中等复杂度等层级', 'puzzle', '#00BCD4', 6, (SELECT id FROM categories WHERE slug = 'world_design'), true)
ON CONFLICT (slug) DO NOTHING;

-- =============================================
-- 10. 新增二级分类：读者分析 -> 读者群体
-- =============================================

INSERT INTO categories (slug, name, name_en, description, icon, color, sort_order, parent_id, is_system) VALUES
('reader_groups', '读者群体', 'Reader Groups', '青少年/年轻书虫/全年龄等读者定位', 'users', '#FFC107', 1, (SELECT id FROM categories WHERE slug = 'reader_analysis'), true)
ON CONFLICT (slug) DO NOTHING;

-- =============================================
-- 11. 新增二级分类：读者分析 -> 平台风格
-- =============================================

INSERT INTO categories (slug, name, name_en, description, icon, color, sort_order, parent_id, is_system) VALUES
('platform_style', '平台风格', 'Platform Style', '起点/番茄/晋江等平台风格指南', 'globe', '#FF5722', 2, (SELECT id FROM categories WHERE slug = 'reader_analysis'), true)
ON CONFLICT (slug) DO NOTHING;

-- =============================================
-- 12. 新增二级分类：创作方法论 -> 叙事结构
-- =============================================

INSERT INTO categories (slug, name, name_en, description, icon, color, sort_order, parent_id, is_system) VALUES
('narrative_structure', '叙事结构', 'Narrative Structure', '线性/非线性/多线并行等叙事结构', 'git-branch', '#3F51B5', 1, (SELECT id FROM categories WHERE slug = 'writing_technique'), true)
ON CONFLICT (slug) DO NOTHING;

-- =============================================
-- 13. 新增二级分类：创作方法论 -> 叙事视角
-- =============================================

INSERT INTO categories (slug, name, name_en, description, icon, color, sort_order, parent_id, is_system) VALUES
('narrative_perspective', '叙事视角', 'Narrative Perspective', '第一/第三人称/多视角等视角选择', 'eye', '#607D8B', 2, (SELECT id FROM categories WHERE slug = 'writing_technique'), true)
ON CONFLICT (slug) DO NOTHING;

-- =============================================
-- 14. 新增二级分类：创作方法论 -> 文风模式
-- =============================================

INSERT INTO categories (slug, name, name_en, description, icon, color, sort_order, parent_id, is_system) VALUES
('writing_style', '文风模式', 'Writing Style', '经典/强爽点/简洁直白等文风模式', 'type', '#009688', 3, (SELECT id FROM categories WHERE slug = 'writing_technique'), true)
ON CONFLICT (slug) DO NOTHING;

-- =============================================
-- 15. 新增二级分类：创作方法论 -> 语言选择
-- =============================================

INSERT INTO categories (slug, name, name_en, description, icon, color, sort_order, parent_id, is_system) VALUES
('language_choice', '语言选择', 'Language Choice', '中文/英文/中英混合等语言选择', 'languages', '#8BC34A', 4, (SELECT id FROM categories WHERE slug = 'writing_technique'), true)
ON CONFLICT (slug) DO NOTHING;

-- =============================================
-- 16. 新增二级分类：题材调性 -> 风格分类
-- =============================================

INSERT INTO categories (slug, name, name_en, description, icon, color, sort_order, parent_id, is_system) VALUES
('style_categories', '风格分类', 'Style Categories', '爽文/正剧/甜宠/热血等40种风格', 'palette', '#E91E63', 1, (SELECT id FROM categories WHERE slug = 'genre_guide'), true)
ON CONFLICT (slug) DO NOTHING;

-- =============================================
-- 17. 新增二级分类：人物设计 -> 身份职业
-- =============================================

INSERT INTO categories (slug, name, name_en, description, icon, color, sort_order, parent_id, is_system) VALUES
('identity_occupation', '身份职业', 'Identity Occupation', '50种男主+50种女主身份职业', 'briefcase', '#4CAF50', 1, (SELECT id FROM categories WHERE slug = 'character'), true)
ON CONFLICT (slug) DO NOTHING;

-- =============================================
-- 18. 新增二级分类：人物设计 -> 男主人设
-- =============================================

INSERT INTO categories (slug, name, name_en, description, icon, color, sort_order, parent_id, is_system) VALUES
('male_protagonist', '男主人设', 'Male Protagonist', '霸道总裁/废柴逆袭等100种男主人设', 'user', '#2196F3', 2, (SELECT id FROM categories WHERE slug = 'character'), true)
ON CONFLICT (slug) DO NOTHING;

-- =============================================
-- 19. 新增二级分类：人物设计 -> 女主人设
-- =============================================

INSERT INTO categories (slug, name, name_en, description, icon, color, sort_order, parent_id, is_system) VALUES
('female_protagonist', '女主人设', 'Female Protagonist', '清纯小白花/御姐女王等100种女主人设', 'user', '#E91E63', 3, (SELECT id FROM categories WHERE slug = 'character'), true)
ON CONFLICT (slug) DO NOTHING;

-- =============================================
-- 20. 新增二级分类：人物设计 -> 反派人设
-- =============================================

INSERT INTO categories (slug, name, name_en, description, icon, color, sort_order, parent_id, is_system) VALUES
('antagonist', '反派人设', 'Antagonist', '笑面虎/疯狂科学家等100种反派人设', 'skull', '#F44336', 4, (SELECT id FROM categories WHERE slug = 'character'), true)
ON CONFLICT (slug) DO NOTHING;

-- =============================================
-- 21. 新增二级分类：金手指设定 -> 金手指类型
-- =============================================

INSERT INTO categories (slug, name, name_en, description, icon, color, sort_order, parent_id, is_system) VALUES
('cheat_types', '金手指类型', 'Cheat Types', '系统流/传承流/重生穿越等50种金手指', 'gift', '#FFC107', 1, (SELECT id FROM categories WHERE slug = 'skill'), true)
ON CONFLICT (slug) DO NOTHING;

-- =============================================
-- 22. 新增二级分类：命名规范 -> 标题结构
-- =============================================

INSERT INTO categories (slug, name, name_en, description, icon, color, sort_order, parent_id, is_system) VALUES
('title_structure', '标题结构', 'Title Structure', 'XX之XX/XX:XX等50种标题结构', 'header', '#9C27B0', 1, (SELECT id FROM categories WHERE slug = 'naming'), true)
ON CONFLICT (slug) DO NOTHING;

-- =============================================
-- 23. 新增二级分类：情节模板 -> 成长模板
-- =============================================

INSERT INTO categories (slug, name, name_en, description, icon, color, sort_order, parent_id, is_system) VALUES
('growth_templates', '成长模板', 'Growth Templates', '废柴觉醒/名师收徒等50种成长情节', 'trending-up', '#4CAF50', 1, (SELECT id FROM categories WHERE slug = 'plot_templates'), true)
ON CONFLICT (slug) DO NOTHING;

-- =============================================
-- 24. 新增二级分类：情节模板 -> 感情模板
-- =============================================

INSERT INTO categories (slug, name, name_en, description, icon, color, sort_order, parent_id, is_system) VALUES
('romance_templates', '感情模板', 'Romance Templates', '一见钟情/日久生情等50种感情情节', 'heart', '#E91E63', 2, (SELECT id FROM categories WHERE slug = 'plot_templates'), true)
ON CONFLICT (slug) DO NOTHING;

-- =============================================
-- 25. 新增二级分类：情节模板 -> 冒险模板
-- =============================================

INSERT INTO categories (slug, name, name_en, description, icon, color, sort_order, parent_id, is_system) VALUES
('adventure_templates', '冒险模板', 'Adventure Templates', '秘境探险/寻宝之旅等50种冒险情节', 'compass', '#2196F3', 3, (SELECT id FROM categories WHERE slug = 'plot_templates'), true)
ON CONFLICT (slug) DO NOTHING;

-- =============================================
-- 26. 新增二级分类：情节模板 -> 权谋模板
-- =============================================

INSERT INTO categories (slug, name, name_en, description, icon, color, sort_order, parent_id, is_system) VALUES
('politics_templates', '权谋模板', 'Politics Templates', '夺嫡之争/宫斗上位等50种权谋情节', 'shield', '#FF9800', 4, (SELECT id FROM categories WHERE slug = 'plot_templates'), true)
ON CONFLICT (slug) DO NOTHING;

-- =============================================
-- 27. 新增二级分类：情节模板 -> 悬疑模板
-- =============================================

INSERT INTO categories (slug, name, name_en, description, icon, color, sort_order, parent_id, is_system) VALUES
('mystery_templates', '悬疑模板', 'Mystery Templates', '解密追踪等50种悬疑情节', 'search', '#9C27B0', 5, (SELECT id FROM categories WHERE slug = 'plot_templates'), true)
ON CONFLICT (slug) DO NOTHING;

-- =============================================
-- 28. 新增二级分类：情节模板 -> 日常模板
-- =============================================

INSERT INTO categories (slug, name, name_en, description, icon, color, sort_order, parent_id, is_system) VALUES
('daily_templates', '日常模板', 'Daily Templates', '生活成长等日常情节', 'coffee', '#795548', 6, (SELECT id FROM categories WHERE slug = 'plot_templates'), true)
ON CONFLICT (slug) DO NOTHING;

-- =============================================
-- 29. 新增二级分类：世界观设计 -> 时空背景
-- =============================================

INSERT INTO categories (slug, name, name_en, description, icon, color, sort_order, parent_id, is_system) VALUES
('setting_background', '时空背景', 'Setting Background', '现代/古代/异世界/末世等时空背景', 'map', '#00BCD4', 7, (SELECT id FROM categories WHERE slug = 'world_design'), true)
ON CONFLICT (slug) DO NOTHING;

-- =============================================
-- 30. 新增二级分类：质量保障 -> 结局类型
-- =============================================

INSERT INTO categories (slug, name, name_en, description, icon, color, sort_order, parent_id, is_system) VALUES
('ending_types', '结局类型', 'Ending Types', '500种结局类型组合', 'flag', '#607D8B', 1, (SELECT id FROM categories WHERE slug = 'genre_guide'), true)
ON CONFLICT (slug) DO NOTHING;

COMMIT;

-- =============================================
-- 验证查询
-- =============================================

SELECT '=== PRESETS新增分类统计 ===' as info;
SELECT slug, name, parent_id FROM categories WHERE slug IN (
    'world_design', 'reader_analysis', 'plot_templates',
    'world_tone', 'era_setting', 'core_conflict', 'theme_depth',
    'emotion_driver', 'story_complexity', 'reader_groups', 'platform_style',
    'narrative_structure', 'narrative_perspective', 'writing_style',
    'language_choice', 'style_categories', 'identity_occupation',
    'male_protagonist', 'female_protagonist', 'antagonist', 'cheat_types',
    'title_structure', 'growth_templates', 'romance_templates',
    'adventure_templates', 'politics_templates', 'mystery_templates',
    'daily_templates', 'setting_background', 'ending_types'
) ORDER BY parent_id, sort_order;