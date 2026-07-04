-- ============================================================================
-- Global Settings System - 全局设定系统
-- ============================================================================
-- 版本: v1.1
-- 日期: 2026-06-28
-- 描述: 全局设定系统的数据模型，包含分类管理、设定项目管理、BM25检索字段、AI专用字段、题材规范化
-- 依赖: 001_extensions.sql, 010_core_schema.sql, 020_multi_user_workspace.sql
-- ============================================================================

-- ---------------------------------------------------------------------------
-- 1. 删除已有表（如果存在）
-- ---------------------------------------------------------------------------

DROP TABLE IF EXISTS setting_category_relations CASCADE;
DROP TABLE IF EXISTS setting_field_definitions CASCADE;
DROP TABLE IF EXISTS setting_items CASCADE;
DROP TABLE IF EXISTS setting_categories CASCADE;
DROP TABLE IF EXISTS genre_canonical CASCADE;

-- ---------------------------------------------------------------------------
-- 2. 设定分类表 (setting_categories)
-- ---------------------------------------------------------------------------

CREATE TABLE IF NOT EXISTS setting_categories (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    workspace_id UUID NOT NULL REFERENCES workspaces(id) ON DELETE CASCADE,
    name TEXT NOT NULL,
    slug TEXT NOT NULL,
    description TEXT,
    icon TEXT DEFAULT '📁',
    sort_order INTEGER NOT NULL DEFAULT 0,
    is_active BOOLEAN NOT NULL DEFAULT TRUE,
    is_standard BOOLEAN NOT NULL DEFAULT FALSE,
    metadata JSONB NOT NULL DEFAULT '{}'::jsonb,
    created_by UUID REFERENCES users(id) ON DELETE SET NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    UNIQUE(workspace_id, slug)
);

-- 分类索引
CREATE INDEX IF NOT EXISTS idx_setting_categories_workspace
    ON setting_categories(workspace_id, is_active, sort_order);
CREATE INDEX IF NOT EXISTS idx_setting_categories_slug
    ON setting_categories(slug) WHERE is_active = TRUE;

COMMENT ON TABLE setting_categories IS '设定分类表，支持自定义分类和标准分类';

-- ---------------------------------------------------------------------------
-- 3. 分类字段定义表 (setting_field_definitions)
-- ---------------------------------------------------------------------------

CREATE TABLE IF NOT EXISTS setting_field_definitions (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    category_id UUID NOT NULL REFERENCES setting_categories(id) ON DELETE CASCADE,
    field_name TEXT NOT NULL,
    field_key TEXT NOT NULL,
    field_type TEXT NOT NULL CHECK (field_type IN ('text', 'textarea', 'select', 'multiselect', 'number', 'boolean', 'json')),
    options JSONB NOT NULL DEFAULT '[]'::jsonb,
    is_required BOOLEAN NOT NULL DEFAULT FALSE,
    is_searchable BOOLEAN NOT NULL DEFAULT FALSE,
    default_value TEXT,
    placeholder TEXT,
    help_text TEXT,
    sort_order INTEGER NOT NULL DEFAULT 0,
    metadata JSONB NOT NULL DEFAULT '{}'::jsonb,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    UNIQUE(category_id, field_key)
);

-- 字段定义索引
CREATE INDEX IF NOT EXISTS idx_setting_field_definitions_category
    ON setting_field_definitions(category_id, sort_order);

COMMENT ON TABLE setting_field_definitions IS '分类字段定义表，定义每个分类下设定项目的字段结构';

-- ---------------------------------------------------------------------------
-- 4. 设定项目表 (setting_items)
-- ---------------------------------------------------------------------------

CREATE TABLE IF NOT EXISTS setting_items (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    category_id UUID NOT NULL REFERENCES setting_categories(id) ON DELETE CASCADE,
    workspace_id UUID NOT NULL REFERENCES workspaces(id) ON DELETE CASCADE,
    item_code TEXT,
    
    -- BM25 检索优化字段（多权重搜索）
    keywords TEXT[] NOT NULL DEFAULT ARRAY[]::TEXT[],
    intent_synonyms TEXT[] NOT NULL DEFAULT ARRAY[]::TEXT[],
    core_summary TEXT NOT NULL,
    detailed_expansion TEXT,
    
    -- AI 专用字段
    ai_instruction TEXT,
    poison_points TEXT[] NOT NULL DEFAULT ARRAY[]::TEXT[],
    
    -- 分层与权重字段
    level TEXT NOT NULL DEFAULT 'knowledge' CHECK (level IN ('knowledge', 'reminder', 'defect_compensation')),
    applicable_skills TEXT[] NOT NULL DEFAULT ARRAY[]::TEXT[],
    applicable_genres TEXT[] NOT NULL DEFAULT ARRAY[]::TEXT[],
    
    -- 原有灵活字段
    data JSONB NOT NULL DEFAULT '{}'::jsonb,
    tags TEXT[] NOT NULL DEFAULT ARRAY[]::TEXT[],
    is_global BOOLEAN NOT NULL DEFAULT TRUE,
    sort_order INTEGER NOT NULL DEFAULT 0,
    
    -- 审计字段
    metadata JSONB NOT NULL DEFAULT '{}'::jsonb,
    created_by UUID REFERENCES users(id) ON DELETE SET NULL,
    updated_by UUID REFERENCES users(id) ON DELETE SET NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    
    -- 唯一约束
    UNIQUE(workspace_id, item_code),
    UNIQUE(category_id, item_code)
);

-- 设定项目索引
CREATE INDEX IF NOT EXISTS idx_setting_items_workspace_category
    ON setting_items(workspace_id, category_id, is_global, sort_order);
CREATE INDEX IF NOT EXISTS idx_setting_items_code
    ON setting_items(item_code) WHERE item_code IS NOT NULL;
CREATE INDEX IF NOT EXISTS idx_setting_items_level
    ON setting_items(level);
CREATE INDEX IF NOT EXISTS idx_setting_items_keywords
    ON setting_items USING GIN(keywords);
CREATE INDEX IF NOT EXISTS idx_setting_items_intent_synonyms
    ON setting_items USING GIN(intent_synonyms);
CREATE INDEX IF NOT EXISTS idx_setting_items_poison_points
    ON setting_items USING GIN(poison_points);
CREATE INDEX IF NOT EXISTS idx_setting_items_tags
    ON setting_items USING GIN(tags);
CREATE INDEX IF NOT EXISTS idx_setting_items_skills
    ON setting_items USING GIN(applicable_skills);
CREATE INDEX IF NOT EXISTS idx_setting_items_genres
    ON setting_items USING GIN(applicable_genres);
CREATE INDEX IF NOT EXISTS idx_setting_items_global
    ON setting_items(workspace_id, is_global);

COMMENT ON TABLE setting_items IS '设定项目表，包含BM25检索字段、AI专用字段、分层权重字段';

COMMENT ON COLUMN setting_items.keywords IS '关键词数组，高权重触发词（BM25权重A）';
COMMENT ON COLUMN setting_items.intent_synonyms IS '意图同义词数组，用户自然语言问法、黑话、俗语（BM25权重B）';
COMMENT ON COLUMN setting_items.core_summary IS '核心摘要，高权重召回（BM25权重C）';
COMMENT ON COLUMN setting_items.detailed_expansion IS '详细展开，低权重（BM25权重D）';
COMMENT ON COLUMN setting_items.ai_instruction IS '大模型指令，直接给AI的执行指令';
COMMENT ON COLUMN setting_items.poison_points IS '毒点/反面案例警告数组';
COMMENT ON COLUMN setting_items.level IS '分层：knowledge=知识补充，reminder=提醒，defect_compensation=缺陷补偿';
COMMENT ON COLUMN setting_items.applicable_skills IS '适用技能：init, plan, write, review等';
COMMENT ON COLUMN setting_items.applicable_genres IS '适用题材（canonical genre）';

-- ---------------------------------------------------------------------------
-- 5. 题材规范化表 (genre_canonical)
-- ---------------------------------------------------------------------------

CREATE TABLE IF NOT EXISTS genre_canonical (
    canonical_genre TEXT PRIMARY KEY,
    platform_tags TEXT[] NOT NULL DEFAULT ARRAY[]::TEXT[],
    aliases TEXT[] NOT NULL DEFAULT ARRAY[]::TEXT[],
    description TEXT,
    metadata JSONB NOT NULL DEFAULT '{}'::jsonb,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

-- 题材索引
CREATE INDEX IF NOT EXISTS idx_genre_canonical_tags
    ON genre_canonical USING GIN(platform_tags);
CREATE INDEX IF NOT EXISTS idx_genre_canonical_aliases
    ON genre_canonical USING GIN(aliases);

COMMENT ON TABLE genre_canonical IS '题材规范化表，建立题材映射机制';

-- ---------------------------------------------------------------------------
-- 6. 分类关联表 (setting_category_relations)
-- ---------------------------------------------------------------------------

CREATE TABLE IF NOT EXISTS setting_category_relations (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    parent_category_id UUID NOT NULL REFERENCES setting_categories(id) ON DELETE CASCADE,
    child_category_id UUID NOT NULL REFERENCES setting_categories(id) ON DELETE CASCADE,
    relation_type TEXT NOT NULL DEFAULT 'contains' CHECK (relation_type IN ('contains', 'related', 'conflicts')),
    metadata JSONB NOT NULL DEFAULT '{}'::jsonb,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    UNIQUE(parent_category_id, child_category_id)
);

-- 分类关联索引
CREATE INDEX IF NOT EXISTS idx_setting_category_relations_parent
    ON setting_category_relations(parent_category_id);
CREATE INDEX IF NOT EXISTS idx_setting_category_relations_child
    ON setting_category_relations(child_category_id);

COMMENT ON TABLE setting_category_relations IS '分类关联表，定义分类之间的包含/关联/冲突关系';

-- ---------------------------------------------------------------------------
-- 7. 种子数据：9个标准分类（使用 Default Workspace）
-- ---------------------------------------------------------------------------

INSERT INTO setting_categories (id, workspace_id, name, slug, description, icon, sort_order, is_active, is_standard) VALUES
    ('00000000-0000-0000-0000-000000000001', '2fa7fe16-c1f0-414f-9589-7837be6663b6', '题材与调性推理', 'genre-inference', '对应题材与调性推理，包括题材选择、调性设定、目标读者群体分析', '🎭', 10, TRUE, TRUE),
    ('00000000-0000-0000-0000-000000000002', '2fa7fe16-c1f0-414f-9589-7837be6663b6', '金手指与设定', 'golden-finger', '对应金手指与设定，包括主角特殊能力、系统设定、特殊道具', '⚡', 20, TRUE, TRUE),
    ('00000000-0000-0000-0000-000000000003', '2fa7fe16-c1f0-414f-9589-7837be6663b6', '人设模板', 'character-template', '对应人设模板，包括主角/配角性格、背景、成长曲线', '👤', 30, TRUE, TRUE),
    ('00000000-0000-0000-0000-000000000004', '2fa7fe16-c1f0-414f-9589-7837be6663b6', '情节模板', 'plot-template', '对应情节模板，包括桥段套路、爽点设计、情绪节奏', '📖', 40, TRUE, TRUE),
    ('00000000-0000-0000-0000-000000000005', '2fa7fe16-c1f0-414f-9589-7837be6663b6', '命名规则', 'naming-rules', '对应命名规则，包括人物/地点/技能/势力命名规范', '✏️', 50, TRUE, TRUE),
    ('00000000-0000-0000-0000-000000000006', '2fa7fe16-c1f0-414f-9589-7837be6663b6', '场景写法', 'scene-writing', '对应场景写法，包括场景类型、描写重点、氛围营造', '🎬', 60, TRUE, TRUE),
    ('00000000-0000-0000-0000-000000000007', '2fa7fe16-c1f0-414f-9589-7837be6663b6', '写作技法', 'writing-techniques', '对应写作技法，包括叙事视角、节奏控制、信息释放', '📝', 70, TRUE, TRUE),
    ('00000000-0000-0000-0000-000000000008', '2fa7fe16-c1f0-414f-9589-7837be6663b6', '爽点与节奏', 'rhythm-points', '对应爽点与节奏，包括高潮设计、期待感营造、章末钩子', '🔥', 80, TRUE, TRUE),
    ('00000000-0000-0000-0000-000000000009', '2fa7fe16-c1f0-414f-9589-7837be6663b6', '裁决规则', 'review-rules', '对应裁决规则，包括质量标准、常见问题判定、修改建议', '⚖️', 90, TRUE, TRUE)
ON CONFLICT (workspace_id, slug) DO UPDATE SET
    name = EXCLUDED.name,
    description = EXCLUDED.description,
    icon = EXCLUDED.icon,
    sort_order = EXCLUDED.sort_order,
    is_active = EXCLUDED.is_active,
    is_standard = EXCLUDED.is_standard,
    updated_at = now();

-- ---------------------------------------------------------------------------
-- 8. 种子数据：每个标准分类的默认字段定义
-- ---------------------------------------------------------------------------

INSERT INTO setting_field_definitions (category_id, field_name, field_key, field_type, is_required, is_searchable, sort_order) VALUES
    ('00000000-0000-0000-0000-000000000001', '题材名称', 'genre_name', 'text', TRUE, TRUE, 1),
    ('00000000-0000-0000-0000-000000000001', '目标读者', 'target_audience', 'multiselect', TRUE, TRUE, 2),
    ('00000000-0000-0000-0000-000000000001', '故事调性', 'tone', 'select', TRUE, TRUE, 3),
    ('00000000-0000-0000-0000-000000000001', '核心卖点', 'selling_points', 'textarea', TRUE, TRUE, 4),
    ('00000000-0000-0000-0000-000000000001', '参考作品', 'reference_works', 'textarea', FALSE, TRUE, 5)
ON CONFLICT (category_id, field_key) DO NOTHING;

INSERT INTO setting_field_definitions (category_id, field_name, field_key, field_type, is_required, is_searchable, sort_order) VALUES
    ('00000000-0000-0000-0000-000000000002', '金手指类型', 'finger_type', 'select', TRUE, TRUE, 1),
    ('00000000-0000-0000-0000-000000000002', '能力描述', 'ability_description', 'textarea', TRUE, TRUE, 2),
    ('00000000-0000-0000-0000-000000000002', '限制条件', 'limitations', 'textarea', TRUE, TRUE, 3),
    ('00000000-0000-0000-0000-000000000002', '成长路径', 'growth_path', 'textarea', FALSE, TRUE, 4),
    ('00000000-0000-0000-0000-000000000002', '反噬代价', 'side_effects', 'textarea', FALSE, TRUE, 5)
ON CONFLICT (category_id, field_key) DO NOTHING;

INSERT INTO setting_field_definitions (category_id, field_name, field_key, field_type, is_required, is_searchable, sort_order) VALUES
    ('00000000-0000-0000-0000-000000000003', '角色定位', 'role', 'select', TRUE, TRUE, 1),
    ('00000000-0000-0000-0000-000000000003', '核心性格', 'core_personality', 'textarea', TRUE, TRUE, 2),
    ('00000000-0000-0000-0000-000000000003', '背景故事', 'backstory', 'textarea', FALSE, TRUE, 3),
    ('00000000-0000-0000-0000-000000000003', '成长曲线', 'growth_arc', 'textarea', FALSE, TRUE, 4),
    ('00000000-0000-0000-0000-000000000003', '语言风格', 'speaking_style', 'textarea', FALSE, TRUE, 5)
ON CONFLICT (category_id, field_key) DO NOTHING;

INSERT INTO setting_field_definitions (category_id, field_name, field_key, field_type, is_required, is_searchable, sort_order) VALUES
    ('00000000-0000-0000-0000-000000000004', '模板类型', 'template_type', 'select', TRUE, TRUE, 1),
    ('00000000-0000-0000-0000-000000000004', '适用场景', 'applicable_scenes', 'textarea', TRUE, TRUE, 2),
    ('00000000-0000-0000-0000-000000000004', '核心结构', 'core_structure', 'textarea', TRUE, TRUE, 3),
    ('00000000-0000-0000-0000-000000000004', '情绪曲线', 'emotion_curve', 'textarea', FALSE, TRUE, 4),
    ('00000000-0000-0000-0000-000000000004', '变体示例', 'variations', 'textarea', FALSE, TRUE, 5)
ON CONFLICT (category_id, field_key) DO NOTHING;

INSERT INTO setting_field_definitions (category_id, field_name, field_key, field_type, is_required, is_searchable, sort_order) VALUES
    ('00000000-0000-0000-0000-000000000005', '命名对象', 'naming_target', 'select', TRUE, TRUE, 1),
    ('00000000-0000-0000-0000-000000000005', '命名规则', 'naming_rule', 'textarea', TRUE, TRUE, 2),
    ('00000000-0000-0000-0000-000000000005', '示例', 'examples', 'textarea', TRUE, TRUE, 3),
    ('00000000-0000-0000-0000-000000000005', '禁忌用字', 'forbidden_chars', 'textarea', FALSE, FALSE, 4)
ON CONFLICT (category_id, field_key) DO NOTHING;

INSERT INTO setting_field_definitions (category_id, field_name, field_key, field_type, is_required, is_searchable, sort_order) VALUES
    ('00000000-0000-0000-0000-000000000006', '场景类型', 'scene_type', 'select', TRUE, TRUE, 1),
    ('00000000-0000-0000-0000-000000000006', '描写重点', 'description_focus', 'textarea', TRUE, TRUE, 2),
    ('00000000-0000-0000-0000-000000000006', '氛围关键词', 'atmosphere_keywords', 'multiselect', FALSE, TRUE, 3),
    ('00000000-0000-0000-0000-000000000006', '字数参考', 'word_count_reference', 'number', FALSE, FALSE, 4)
ON CONFLICT (category_id, field_key) DO NOTHING;

INSERT INTO setting_field_definitions (category_id, field_name, field_key, field_type, is_required, is_searchable, sort_order) VALUES
    ('00000000-0000-0000-0000-000000000007', '技法名称', 'technique_name', 'text', TRUE, TRUE, 1),
    ('00000000-0000-0000-0000-000000000007', '适用环节', 'applicable_phase', 'multiselect', TRUE, TRUE, 2),
    ('00000000-0000-0000-0000-000000000007', '技法说明', 'technique_description', 'textarea', TRUE, TRUE, 3),
    ('00000000-0000-0000-0000-000000000007', '示例片段', 'example_snippet', 'textarea', FALSE, TRUE, 4)
ON CONFLICT (category_id, field_key) DO NOTHING;

INSERT INTO setting_field_definitions (category_id, field_name, field_key, field_type, is_required, is_searchable, sort_order) VALUES
    ('00000000-0000-0000-0000-000000000008', '爽点类型', 'excitement_type', 'select', TRUE, TRUE, 1),
    ('00000000-0000-0000-0000-000000000008', '触发条件', 'trigger_conditions', 'textarea', TRUE, TRUE, 2),
    ('00000000-0000-0000-0000-000000000008', '节奏要点', 'rhythm_points', 'textarea', TRUE, TRUE, 3),
    ('00000000-0000-0000-0000-000000000008', '前置铺垫', 'prerequisites', 'textarea', FALSE, TRUE, 4),
    ('00000000-0000-0000-0000-000000000008', '后续延续', 'follow_up', 'textarea', FALSE, TRUE, 5)
ON CONFLICT (category_id, field_key) DO NOTHING;

INSERT INTO setting_field_definitions (category_id, field_name, field_key, field_type, is_required, is_searchable, sort_order) VALUES
    ('00000000-0000-0000-0000-000000000009', '规则类型', 'rule_type', 'select', TRUE, TRUE, 1),
    ('00000000-0000-0000-0000-000000000009', '问题描述', 'problem_description', 'textarea', TRUE, TRUE, 2),
    ('00000000-0000-0000-0000-000000000009', '判定标准', 'judgment_criteria', 'textarea', TRUE, TRUE, 3),
    ('00000000-0000-0000-0000-000000000009', '修改建议', 'revision_suggestion', 'textarea', TRUE, TRUE, 4),
    ('00000000-0000-0000-0000-000000000009', '严重级别', 'severity', 'select', TRUE, FALSE, 5)
ON CONFLICT (category_id, field_key) DO NOTHING;

-- ---------------------------------------------------------------------------
-- 9. 种子数据：15个 Canonical Genre
-- ---------------------------------------------------------------------------

INSERT INTO genre_canonical (canonical_genre, platform_tags, aliases, description) VALUES
    ('都市', ARRAY['都市', '现代都市', '现代', '都市生活', '都市异能', '都市重生'], 
     ARRAY['modern city', 'urban fantasy', 'city life'], 
     '现代都市背景的网络小说，主角在都市中成长、冒险、提升实力'),
    
    ('玄幻', ARRAY['玄幻', '东方玄幻', '玄幻奇幻'], 
     ARRAY['fantasy', 'xianxia', 'cultivation'], 
     '东方背景的玄幻修炼小说，主角通过修炼提升境界、探索秘境'),
    
    ('仙侠', ARRAY['仙侠', '古典仙侠', '修真'], 
     ARRAY['xianxia', 'immortal', 'cultivation novel'], 
     '仙侠世界的小说，飞升、长生、剑修等元素'),
    
    ('奇幻', ARRAY['奇幻', '西方奇幻', '异世大陆'], 
     ARRAY['fantasy', 'western fantasy', 'isekai'], 
     '西方魔法背景的奇幻小说，魔法、种族、领主等元素'),
    
    ('科幻', ARRAY['科幻', '未来科技', '星际', '末世'], 
     ARRAY['sci-fi', 'science fiction', 'space opera', 'post-apocalyptic'], 
     '科技为主线的小说，星际旅行、人工智能、末世生存等'),
    
    ('历史', ARRAY['历史', '古代历史', '历史穿越'], 
     ARRAY['historical', 'dynasty', 'ancient china'], 
     '以历史时期为背景的小说，穿越、争霸、种田等'),
    
    ('悬疑', ARRAY['悬疑', '推理', '侦探'], 
     ARRAY['mystery', 'detective', 'thriller'], 
     '以推理破案为主线的小说'),
    
    ('游戏', ARRAY['游戏', '游戏异界', '虚拟现实', '电竞'], 
     ARRAY['game', 'vr game', 'esports', 'MMORPG'], 
     '以游戏为核心的小说，全息游戏、电竞、虚拟现实等'),
    
    ('古言', ARRAY['古言', '古代言情', '宅斗', '宫斗'], 
     ARRAY['ancient romance', 'palace drama', 'family intrigue'], 
     '以古代为背景的言情小说，宅斗、宫斗、宫廷等'),
    
    ('现言', ARRAY['现言', '现代言情', '都市言情', '总裁'], 
     ARRAY['modern romance', 'contemporary romance', 'ceo romance'], 
     '以现代为背景的言情小说，总裁、甜宠、虐恋等'),
    
    ('幻言', ARRAY['幻言', '玄幻言情'], 
     ARRAY['fantasy romance', 'xianxia romance'], 
     '玄幻背景的言情小说，修仙恋爱双线'),
    
    ('年代', ARRAY['年代', '年代文', '七八十年代'], 
     ARRAY['era', '70s 80s', 'historical modern'], 
     '以特定年代为背景的小说，怀旧、奋斗、创业等'),
    
    ('种田', ARRAY['种田', '经营', '发家致富'], 
     ARRAY['farming', 'settlement', 'business'], 
     '以种田经营为主线的小说，发家致富、家长里短'),
    
    ('快穿', ARRAY['快穿', '快穿文', '任务流'], 
     ARRAY['quick transmigration', 'task-based', 'multiple worlds'], 
     '穿越多个世界完成任务的小说'),
    
    ('衍生', ARRAY['衍生', '同人', '综漫', '综影视'], 
     ARRAY['fanfic', 'crossover', 'anime', 'drama adaptation'], 
     '基于已有作品衍生的同人小说')
ON CONFLICT (canonical_genre) DO UPDATE SET
    platform_tags = EXCLUDED.platform_tags,
    aliases = EXCLUDED.aliases,
    description = EXCLUDED.description,
    updated_at = now();

-- ---------------------------------------------------------------------------
-- 10. 示例数据：为每个标准分类添加示例设定
-- ---------------------------------------------------------------------------

INSERT INTO setting_items (
    category_id, workspace_id, item_code, 
    keywords, intent_synonyms, core_summary, detailed_expansion,
    ai_instruction, poison_points, level, applicable_skills, applicable_genres, tags, is_global
) VALUES (
    '00000000-0000-0000-0000-000000000001',
    '2fa7fe16-c1f0-414f-9589-7837be6663b6',
    'GS-GENRE-001',
    ARRAY['都市', '现代', '写实', '现实'],
    ARRAY['现代都市小说怎么写', '现实题材', '普通人的故事'],
    '都市题材以现代都市为背景，强调现实感和代入感，主角通常是普通人在都市中奋斗成长。',
    '都市题材需要注重：1. 真实的社会环境描写 2. 合理的人际关系 3. 贴近生活的情感表达 4. 现实可行的升级路径 5. 避免过于离奇的金手指',
    '都市文要贴近现实，不要出现修仙、法术等超自然元素。金手指要符合现实逻辑，如系统也要有商业可行性。',
    ARRAY['主角一上来就是首富', '三天赚到一个亿', '没有任何限制的超能力'],
    'knowledge',
    ARRAY['init', 'write'],
    ARRAY['都市', '现言'],
    ARRAY['题材指导', '都市入门'],
    TRUE
);

INSERT INTO setting_items (
    category_id, workspace_id, item_code, 
    keywords, intent_synonyms, core_summary, detailed_expansion,
    ai_instruction, poison_points, level, applicable_skills, applicable_genres, tags, is_global
) VALUES (
    '00000000-0000-0000-0000-000000000001',
    '2fa7fe16-c1f0-414f-9589-7837be6663b6',
    'GS-GENRE-002',
    ARRAY['玄幻', '东方', '修炼', '境界', '飞升'],
    ARRAY['修仙小说怎么写', '东方玄幻', '修炼体系', '升级流'],
    '玄幻题材以东方修炼体系为核心，主角通过修炼提升境界，追求长生或飞升。',
    '玄幻题材核心要素：1. 完整的境界体系（炼气、筑基、金丹、元婴等）2. 各境界实力差距要合理 3. 资源稀缺性的营造 4. 势力格局的设定 5. 秘境、传承等探索元素',
    '玄幻文要建立清晰的修炼体系，每个境界要有明确的特征和实力差距。境界压制是爽点的核心来源。',
    ARRAY['境界设定混乱', '实力提升太快', '配角比主角还强太多'],
    'knowledge',
    ARRAY['init', 'write', 'plan'],
    ARRAY['玄幻', '仙侠'],
    ARRAY['题材指导', '玄幻入门'],
    TRUE
);

INSERT INTO setting_items (
    category_id, workspace_id, item_code, 
    keywords, intent_synonyms, core_summary, detailed_expansion,
    ai_instruction, poison_points, level, applicable_skills, applicable_genres, tags, is_global
) VALUES (
    '00000000-0000-0000-0000-000000000002',
    '2fa7fe16-c1f0-414f-9589-7837be6663b6',
    'GS-FINGER-001',
    ARRAY['系统流', '任务系统', '面板'],
    ARRAY['系统文怎么写', '金手指系统', '面板流', '系统商店'],
    '系统流是最常见的金手指类型，主角获得一个可以发布任务、提供奖励的系统辅助成长。',
    '系统流写法要点：1. 系统要有明确的功能模块（任务、商城、属性面板等）2. 系统奖励要合理，不能过于逆天 3. 系统的来历可以神秘但不要喧宾夺主 4. 任务设计要有挑战性和趣味性 5. 系统可以有自己的性格但不能抢戏',
    '系统是辅助工具，不是主角。系统文要避免系统奖励太容易获得，要设计合理的限制和挑战。',
    ARRAY['系统奖励太容易', '系统什么都能解决', '没有系统的限制就没有故事'],
    'knowledge',
    ARRAY['init', 'write'],
    ARRAY['都市', '玄幻', '仙侠', '游戏'],
    ARRAY['金手指类型', '系统流'],
    TRUE
);

INSERT INTO setting_items (
    category_id, workspace_id, item_code, 
    keywords, intent_synonyms, core_summary, detailed_expansion,
    ai_instruction, poison_points, level, applicable_skills, applicable_genres, tags, is_global
) VALUES (
    '00000000-0000-0000-0000-000000000003',
    '2fa7fe16-c1f0-414f-9589-7837be6663b6',
    'GS-CHAR-001',
    ARRAY['主角', '男主', '网文男主', '爽文主角'],
    ARRAY['网文主角怎么写', '主角人设', '男主人设'],
    '网文主角通常具备以下特质：目标明确、意志坚定、有仇必报（或有恩必还）、关键时刻果断决策。',
    '网文主角人设要点：1. 要有清晰的目标（复仇、变强、守护等）2. 性格要有棱角，不能太圣母 3. 遇到冲突要主动出击，不能一直被动挨打 4. 要有成长空间，但不能成长太慢 5. 配角不能威胁到主角的核心地位',
    '主角是故事的核心，要让读者有代入感。主角要有清晰的性格特征，决策要果断，遇到机会要抓住。',
    ARRAY['圣母心泛滥', '一直被动挨打', '没有自己的主见', '处处不如人'],
    'knowledge',
    ARRAY['init', 'plan', 'write'],
    ARRAY['玄幻', '仙侠', '都市'],
    ARRAY['人设模板', '主角'],
    TRUE
);

INSERT INTO setting_items (
    category_id, workspace_id, item_code, 
    keywords, intent_synonyms, core_summary, detailed_expansion,
    ai_instruction, poison_points, level, applicable_skills, applicable_genres, tags, is_global
) VALUES (
    '00000000-0000-0000-0000-000000000004',
    '2fa7fe16-c1f0-414f-9589-7837be6663b6',
    'GS-PLOT-001',
    ARRAY['装逼打脸', '打脸', '逆袭', '打脸爽文', '爽点'],
    ARRAY['装逼打脸怎么写', '打脸情节', '逆袭套路'],
    '装逼打脸是网文最核心的爽点模式，核心是：被轻视→展现实力→打脸对方→获得收益/尊重。',
    '装逼打脸结构：1. 前置铺垫：对方轻视、嘲讽主角（制造冲突）2. 压抑：主角隐忍或低调（积蓄情绪）3. 爆发：主角展现实力（释放爽感）4. 结果：对方震惊/求饶/结交（爽点落地）。关键要点：打脸对象要有身份地位，打脸才有效果；打脸过程要有细节描写；最好有第三方见证；打脸后要有后续收益。',
    '装逼打脸是最核心的爽点。要注意铺垫充分，打脸才够爽。打脸后要有后续收益，让爽感延续。',
    ARRAY['铺垫不够就打脸', '打脸过程太简单', '没有后续收益', '对方没有身份地位'],
    'knowledge',
    ARRAY['plan', 'write'],
    ARRAY['都市', '玄幻', '仙侠'],
    ARRAY['爽点设计', '打脸'],
    TRUE
);

INSERT INTO setting_items (
    category_id, workspace_id, item_code, 
    keywords, intent_synonyms, core_summary, detailed_expansion,
    ai_instruction, poison_points, level, applicable_skills, applicable_genres, tags, is_global
) VALUES (
    '00000000-0000-0000-0000-000000000009',
    '2fa7fe16-c1f0-414f-9589-7837be6663b6',
    'GS-REVIEW-001',
    ARRAY['OOC', '人设崩', '性格崩', '人设崩坏', '性格不符'],
    ARRAY['人物OOC', '人物性格不符', '角色崩坏'],
    'OOC（Out of Character）是指人物行为与既定性格不符，是严重的人物塑造问题。',
    'OOC判定标准：1. 行为动机是否与人物背景/性格一致 2. 决策是否符合人物已有的行为模式 3. 语言风格是否与人物设定一致 4. 遇到问题时是否用人物应有的方式处理。常见OOC场景：圣母型主角突然变得冷漠无情、理智型角色做出冲动决定没有铺垫、反派突然洗白没有任何过渡、配角抢了主角的戏份和能力。',
    '写人物时要时刻对照人设，确保行为决策符合角色性格。如需角色做与性格不符的事，必须有充分的铺垫和合理的动机。',
    ARRAY['性格突变没有铺垫', '圣母变冷酷', '理智变冲动'],
    'defect_compensation',
    ARRAY['review'],
    ARRAY['都市', '玄幻', '仙侠', '古言', '现言'],
    ARRAY['质量问题', '人设问题'],
    TRUE
);

-- ---------------------------------------------------------------------------
-- 11. 函数：BM25 检索
-- ---------------------------------------------------------------------------

CREATE OR REPLACE FUNCTION fn_setting_items_bm25_search(
    p_query TEXT,
    p_workspace_id UUID DEFAULT NULL,
    p_category_id UUID DEFAULT NULL,
    p_level TEXT DEFAULT NULL,
    p_skill TEXT DEFAULT NULL,
    p_genre TEXT DEFAULT NULL,
    p_limit INTEGER DEFAULT 20,
    p_offset INTEGER DEFAULT 0
)
RETURNS TABLE (
    id UUID,
    category_id UUID,
    item_code TEXT,
    core_summary TEXT,
    detailed_expansion TEXT,
    ai_instruction TEXT,
    level TEXT,
    applicable_skills TEXT[],
    applicable_genres TEXT[],
    tags TEXT[],
    rank DOUBLE PRECISION,
    highlight TEXT
)
LANGUAGE plpgsql
AS $$
BEGIN
    RETURN QUERY
    WITH search_query AS (
        SELECT 
            plainto_tsquery('simple', p_query) AS query_tsvector
    ),
    weighted_results AS (
        SELECT
            si.id,
            si.category_id,
            si.item_code,
            si.core_summary,
            si.detailed_expansion,
            si.ai_instruction,
            si.level,
            si.applicable_skills,
            si.applicable_genres,
            si.tags,
            COALESCE(
                ts_rank_cd(
                    setweight(to_tsvector('simple', array_to_string(si.intent_synonyms, ' ')), 'A') ||
                    setweight(to_tsvector('simple', array_to_string(si.keywords, ' ')), 'B') ||
                    setweight(to_tsvector('simple', si.core_summary), 'C') ||
                    setweight(to_tsvector('simple', COALESCE(si.detailed_expansion, '')), 'D'),
                    sq.query_tsvector
                ) * 4.0 +
                ts_rank_cd(
                    to_tsvector('simple', array_to_string(si.keywords, ' ')),
                    sq.query_tsvector
                ) * 3.0 +
                ts_rank_cd(
                    to_tsvector('simple', si.core_summary),
                    sq.query_tsvector
                ) * 2.0 +
                ts_rank_cd(
                    to_tsvector('simple', COALESCE(si.detailed_expansion, '')),
                    sq.query_tsvector
                ) * 1.0,
                0.0
            ) AS rank,
            ts_headline('simple', si.core_summary, sq.query_tsvector,
                'StartSel=<mark>, StopSel=</mark>, MaxWords=50, MinWords=20') AS highlight
        FROM setting_items si, search_query sq
        WHERE
            (
                to_tsvector('simple', array_to_string(si.intent_synonyms, ' ')) @@ sq.query_tsvector OR
                to_tsvector('simple', array_to_string(si.keywords, ' ')) @@ sq.query_tsvector OR
                to_tsvector('simple', si.core_summary) @@ sq.query_tsvector OR
                to_tsvector('simple', COALESCE(si.detailed_expansion, '')) @@ sq.query_tsvector
            )
            AND (p_workspace_id IS NULL OR si.workspace_id = p_workspace_id OR si.is_global = TRUE)
            AND (p_category_id IS NULL OR si.category_id = p_category_id)
            AND (p_level IS NULL OR si.level = p_level)
            AND (p_skill IS NULL OR p_skill = ANY(si.applicable_skills))
            AND (p_genre IS NULL OR p_genre = ANY(si.applicable_genres))
    )
    SELECT
        wr.id,
        wr.category_id,
        wr.item_code,
        wr.core_summary,
        wr.detailed_expansion,
        wr.ai_instruction,
        wr.level,
        wr.applicable_skills,
        wr.applicable_genres,
        wr.tags,
        wr.rank,
        wr.highlight
    FROM weighted_results wr
    ORDER BY wr.rank DESC
    LIMIT p_limit
    OFFSET p_offset;
END;
$$;

-- ---------------------------------------------------------------------------
-- 12. 函数：题材规范化
-- ---------------------------------------------------------------------------

CREATE OR REPLACE FUNCTION fn_genre_resolve(
    p_input TEXT
)
RETURNS TABLE (
    canonical_genre TEXT,
    match_type TEXT,
    confidence NUMERIC
)
LANGUAGE plpgsql
AS $$
BEGIN
    RETURN QUERY
    WITH input_lower AS (
        SELECT lower(p_input) AS input_text
    ),
    matched AS (
        SELECT
            gc.canonical_genre,
            CASE
                WHEN gc.canonical_genre = il.input_text THEN 'exact'
                WHEN gc.canonical_genre LIKE '%' || il.input_text || '%' THEN 'partial'
                WHEN il.input_text = ANY(gc.platform_tags) THEN 'platform_tag'
                WHEN il.input_text = ANY(gc.aliases) THEN 'alias'
                ELSE 'fuzzy'
            END AS match_type,
            CASE
                WHEN gc.canonical_genre = il.input_text THEN 1.0
                WHEN il.input_text = ANY(gc.platform_tags) THEN 0.95
                WHEN il.input_text = ANY(gc.aliases) THEN 0.9
                WHEN il.input_text LIKE '%' || gc.canonical_genre || '%' THEN 0.8
                WHEN gc.canonical_genre LIKE '%' || il.input_text || '%' THEN 0.7
                ELSE 0.5
            END AS confidence
        FROM genre_canonical gc, input_lower il
        ORDER BY confidence DESC
        LIMIT 5
    )
    SELECT m.canonical_genre, m.match_type, m.confidence
    FROM matched m;
END;
$$;

-- ---------------------------------------------------------------------------
-- 13. 函数：CSV 导入验证
-- ---------------------------------------------------------------------------

CREATE OR REPLACE FUNCTION fn_setting_items_csv_validate(
    p_csv_content TEXT
)
RETURNS TABLE (
    row_number INTEGER,
    is_valid BOOLEAN,
    error_message TEXT,
    parsed_data JSONB
)
LANGUAGE plpgsql
AS $$
DECLARE
    row TEXT;
    row_num INTEGER := 0;
    headers TEXT[];
    values_arr TEXT[];
BEGIN
    headers := string_to_array(replace(split_part(p_csv_content, E'\n', 1), E'\r', ''), ',');
    
    IF NOT ('core_summary' = ANY(headers)) THEN
        RAISE EXCEPTION 'Missing required column: core_summary';
    END IF;
    
    FOR row IN SELECT unnest(string_to_array(replace(substring(p_csv_content from position(E'\n' in p_csv_content) + 1), E'\r', ''), E'\n'))
    LOOP
        row_num := row_num + 1;
        IF row = '' THEN
            CONTINUE;
        END IF;
        
        values_arr := string_to_array(replace(row, E'\r', ''), ',');
        
        IF array_length(values_arr, 1) >= array_position(headers, 'core_summary') 
           AND trim(values_arr[array_position(headers, 'core_summary')]) = '' THEN
            RETURN QUERY SELECT row_num, FALSE, 'core_summary cannot be empty', NULL::JSONB;
        ELSE
            RETURN QUERY SELECT row_num, TRUE, NULL::TEXT, row_to_json(row)::JSONB;
        END IF;
    END LOOP;
END;
$$;

-- ---------------------------------------------------------------------------
-- 14. 视图：全局设定总览
-- ---------------------------------------------------------------------------

CREATE OR REPLACE VIEW v_setting_items_overview AS
SELECT 
    si.id,
    si.item_code,
    si.core_summary,
    si.level,
    si.is_global,
    sc.name AS category_name,
    sc.slug AS category_slug,
    si.tags,
    si.applicable_skills,
    si.applicable_genres,
    si.created_at,
    si.updated_at
FROM setting_items si
JOIN setting_categories sc ON si.category_id = sc.id
ORDER BY sc.sort_order, si.sort_order;

CREATE OR REPLACE VIEW v_genre_canonical_list AS
SELECT 
    canonical_genre,
    platform_tags,
    aliases,
    description,
    array_length(platform_tags, 1) + array_length(aliases, 1) AS alias_count
FROM genre_canonical
ORDER BY canonical_genre;

-- ============================================================================
-- 全局设定系统初始化完成
-- ============================================================================