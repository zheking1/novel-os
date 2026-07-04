-- =============================================
-- Novel OS 可扩展分类架构迁移脚本
-- Version: 1.0
-- Date: 2026-06-29
-- Description: 创建元数据驱动的可扩展分类架构
-- =============================================

BEGIN;

-- =============================================
-- 1. 分类定义表 categories
-- =============================================
CREATE TABLE IF NOT EXISTS categories (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    slug VARCHAR(50) UNIQUE NOT NULL,          -- URL友好标识
    name VARCHAR(100) NOT NULL,                -- 分类名称
    name_en VARCHAR(100),                     -- 英文名称
    description TEXT,                          -- 分类描述
    icon VARCHAR(50),                         -- 图标
    color VARCHAR(20),                        -- 颜色
    sort_order INTEGER DEFAULT 0,              -- 排序
    parent_id UUID REFERENCES categories(id),  -- 父分类
    level INTEGER DEFAULT 0,                  -- 层级深度
    config JSONB DEFAULT '{}',                 -- 分类配置
    is_system BOOLEAN DEFAULT false,          -- 是否系统分类
    is_active BOOLEAN DEFAULT true,            -- 是否启用
    created_at TIMESTAMPTZ DEFAULT now(),
    updated_at TIMESTAMPTZ DEFAULT now()
);

-- =============================================
-- 2. 标签表 tags
-- =============================================
CREATE TABLE IF NOT EXISTS tags (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    slug VARCHAR(50) UNIQUE NOT NULL,
    name VARCHAR(100) NOT NULL,
    category VARCHAR(50),                     -- 所属大类
    description TEXT,
    color VARCHAR(20),
    usage_count INTEGER DEFAULT 0,             -- 使用次数
    is_recommended BOOLEAN DEFAULT false,     -- 推荐标签
    is_active BOOLEAN DEFAULT true,
    created_at TIMESTAMPTZ DEFAULT now()
);

-- =============================================
-- 3. 知识条目表 knowledge_base
-- =============================================
CREATE TABLE IF NOT EXISTS knowledge_base (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    code VARCHAR(50),                         -- 原编号 NR-001
    title VARCHAR(200) NOT NULL,             -- 标题
    content TEXT NOT NULL,                    -- 内容（用于检索）
    summary TEXT,                             -- 摘要
    detail TEXT,                              -- 详细展开
    examples TEXT,                             -- 正例
    counter_examples TEXT,                    -- 反例

    -- 元数据（JSONB灵活存储）
    metadata JSONB DEFAULT '{}',

    -- 来源信息
    source VARCHAR(50) DEFAULT 'manual',      -- manual/opencode
    source_file VARCHAR(200),                 -- 来源文件

    -- 分类关联
    category_id UUID REFERENCES categories(id),

    -- 适用题材
    applicable_genres TEXT[] DEFAULT '{}',

    -- 适用技能
    applicable_skills TEXT[] DEFAULT '{}',

    -- 层级
    level VARCHAR(20) DEFAULT 'knowledge',

    -- 状态
    status VARCHAR(20) DEFAULT 'active',

    -- 统计
    view_count INTEGER DEFAULT 0,
    use_count INTEGER DEFAULT 0,

    -- 搜索向量
    search_vector TSVECTOR GENERATED ALWAYS AS (
        to_tsvector('simple', coalesce(title, '') || ' ' || coalesce(content, ''))
    ) STORED,

    created_at TIMESTAMPTZ DEFAULT now(),
    updated_at TIMESTAMPTZ DEFAULT now()
);

-- =============================================
-- 4. 知识标签关联表 knowledge_tags
-- =============================================
CREATE TABLE IF NOT EXISTS knowledge_tags (
    knowledge_id UUID REFERENCES knowledge_base(id) ON DELETE CASCADE,
    tag_id UUID REFERENCES tags(id) ON DELETE CASCADE,
    created_at TIMESTAMPTZ DEFAULT now(),
    PRIMARY KEY (knowledge_id, tag_id)
);

-- =============================================
-- 5. 向量索引映射表 knowledge_vectors
-- =============================================
CREATE TABLE IF NOT EXISTS knowledge_vectors (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    knowledge_id UUID NOT NULL REFERENCES knowledge_base(id) ON DELETE CASCADE,
    qdrant_collection VARCHAR(100) NOT NULL,
    qdrant_point_id VARCHAR(100),
    vector_model VARCHAR(50) DEFAULT 'text-embedding-3-small',
    dimension INTEGER DEFAULT 1536,
    created_at TIMESTAMPTZ DEFAULT now(),
    UNIQUE(knowledge_id, qdrant_collection)
);

-- =============================================
-- 6. 索引创建
-- =============================================

-- 全文搜索索引
CREATE INDEX IF NOT EXISTS idx_knowledge_search ON knowledge_base USING GIN(search_vector);

-- 分类索引
CREATE INDEX IF NOT EXISTS idx_knowledge_category ON knowledge_base(category_id);

-- 来源索引
CREATE INDEX IF NOT EXISTS idx_knowledge_source ON knowledge_base(source);

-- 适用题材索引
CREATE INDEX IF NOT EXISTS idx_knowledge_genres ON knowledge_base USING GIN(applicable_genres);

-- 适用技能索引
CREATE INDEX IF NOT EXISTS idx_knowledge_skills ON knowledge_base USING GIN(applicable_skills);

-- 标签统计索引
CREATE INDEX IF NOT EXISTS idx_tags_usage ON tags(usage_count DESC);

-- 分类排序索引
CREATE INDEX IF NOT EXISTS idx_category_sort ON categories(sort_order);

-- 元数据索引
CREATE INDEX IF NOT EXISTS idx_knowledge_metadata ON knowledge_base USING GIN(metadata);

-- 编号索引
CREATE INDEX IF NOT EXISTS idx_knowledge_code ON knowledge_base(code);

-- =============================================
-- 7. 初始化数据：10个系统分类
-- =============================================

INSERT INTO categories (slug, name, name_en, description, icon, color, sort_order, is_system) VALUES
('world', '世界观', 'World', '世界设定、地域、组织等', 'globe', '#4CAF50', 1, true),
('character', '角色人设', 'Character', '角色设定、关系、动机', 'user', '#2196F3', 2, true),
('skill', '术法技能', 'Skill', '功法、招式、能力', 'zap', '#FF9800', 3, true),
('writing_technique', '写作技法', 'Writing Technique', '对话、情感、场景描写等技法', 'pen-tool', '#9C27B0', 4, true),
('plot_archetype', '桥段套路', 'Plot Archetype', '经典桥段、套路、反转', 'layers', '#E91E63', 5, true),
('pacing', '爽点节奏', 'Pacing', '节奏控制、爽点设计、高潮分布', 'activity', '#00BCD4', 6, true),
('scene_template', '场景模板', 'Scene Template', '各类场景的写作模板', 'film', '#795548', 7, true),
('genre_guide', '题材指南', 'Genre Guide', '题材分类、调性指南、裁决规则', 'book-open', '#607D8B', 8, true),
('naming', '命名规范', 'Naming', '角色名、书名、地点名等命名规则', 'tag', '#3F51B5', 9, true),
('knowledge_qa', '知识问答', 'Knowledge QA', '知识问答、资料查询', 'help-circle', '#009688', 10, true)
ON CONFLICT (slug) DO NOTHING;

-- =============================================
-- 8. 初始化标签
-- =============================================

INSERT INTO tags (slug, name, category, description, is_recommended) VALUES
-- 写作技法标签
('dialogue', '对话技法', 'writing_technique', '对话相关写作技巧', true),
('emotion', '情感描写', 'writing_technique', '情感表达技巧', true),
('scene', '场景描写', 'writing_technique', '场景构建技巧', true),
('rhythm', '节奏控制', 'writing_technique', '叙事节奏把控', true),
('battle', '战斗分镜', 'writing_technique', '战斗场景写法', true),
('foreshadow', '伏笔布局', 'writing_technique', '伏笔铺设技巧', true),

-- 桥段套路标签
('face_slapping', '打脸', 'plot_archetype', '打脸类桥段', true),
('romance', '感情线', 'plot_archetype', '感情类桥段', true),
('rebirth', '重生穿越', 'plot_archetype', '重生穿越类桥段', true),
('competition', '竞争类', 'plot_archetype', '竞争比赛类桥段', true),

-- 爽点节奏标签
('suppression', '压抑蓄力', 'pacing', '压抑后爆发节奏', true),
('micro_reverse', '微反转', 'pacing', '小反转补刀节奏', true),
('golden_opening', '黄金三章', 'pacing', '开篇节奏', true),
('chapter_hook', '章末钩子', 'pacing', '章节结尾钩子', true),

-- 题材标签
('xianxia', '仙侠', 'genre_guide', '仙侠题材', true),
('xuanhuan', '玄幻', 'genre_guide', '玄幻题材', true),
('urban', '都市', 'genre_guide', '都市题材', true),
('scifi', '科幻', 'genre_guide', '科幻题材', true),
('mystery', '悬疑', 'genre_guide', '悬疑题材', true)
ON CONFLICT (slug) DO NOTHING;

-- =============================================
-- 9. 更新 updated_at 触发器
-- =============================================

CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = now();
    RETURN NEW;
END;
$$ language 'plpgsql';

CREATE TRIGGER update_categories_updated_at
    BEFORE UPDATE ON categories
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_knowledge_base_updated_at
    BEFORE UPDATE ON knowledge_base
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

COMMIT;

-- =============================================
-- 验证查询
-- =============================================

SELECT '=== 分类统计 ===' as info;
SELECT slug, name, is_system FROM categories ORDER BY sort_order;

SELECT '=== 标签统计 ===' as info;
SELECT category, COUNT(*) as count FROM tags GROUP BY category;

SELECT '=== 知识条目统计 ===' as info;
SELECT COUNT(*) as total FROM knowledge_base;
