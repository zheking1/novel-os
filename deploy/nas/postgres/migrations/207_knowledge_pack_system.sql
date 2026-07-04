-- Migration 207: Knowledge Pack System
-- 类型关联知识包 + 自定义分类 + 精准检索

-- 小说类型知识配置表
CREATE TABLE IF NOT EXISTS genre_knowledge_config (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    genre VARCHAR(50) NOT NULL UNIQUE,         -- 玄幻/末日/科幻/历史/灵异/都市
    included_categories TEXT[] DEFAULT '{}',   -- 包含的分类
    excluded_categories TEXT[] DEFAULT '{}',   -- 排除的分类
    description TEXT,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

-- 项目知识包（用户可自定义）
CREATE TABLE IF NOT EXISTS project_knowledge_pack (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    project_id UUID NOT NULL UNIQUE,
    genre VARCHAR(50),                         -- 基础类型
    active_categories TEXT[] DEFAULT '{}',     -- 实际启用的分类
    custom_categories JSONB DEFAULT '{}',      -- 用户自定义分类 {name: {parent, description}}
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

-- 插入默认类型配置
INSERT INTO genre_knowledge_config (genre, included_categories, excluded_categories, description) VALUES
('玄幻', ARRAY['角色', '物品装备', '生物生态', '世界设定', '力量体系', '历史文化', '情节参考'], ARRAY['经济货币', '专业术语'], '修仙/魔法/武侠类小说'),
('末日', ARRAY['角色', '物品装备', '生物生态', '世界设定', '力量体系', '情节参考'], ARRAY['诗词对联', '传说典故', '修炼等级'], '丧尸/废土/生存类小说'),
('科幻', ARRAY['角色', '物品装备', '生物生态', '世界设定', '力量体系', '历史文化', '情节参考'], ARRAY['阵法机关', '修炼等级'], '星际/赛博/未来类小说'),
('历史', ARRAY['角色', '物品装备', '世界设定', '历史文化', '情节参考', '写作参考'], ARRAY['修炼等级', '异能', '系统', '阵法机关'], '古代/近代/架空历史类小说'),
('灵异', ARRAY['角色', '物品装备', '生物生态', '力量体系', '历史文化', '情节参考'], ARRAY['科技', '经济货币', '修炼等级'], '鬼怪/悬疑/惊悚类小说'),
('都市', ARRAY['角色', '物品装备', '世界设定', '情节参考', '写作参考'], ARRAY['修炼等级', '传说典故', '诗词对联', '阵法机关'], '现代/职场/言情类小说'),
('游戏', ARRAY['角色', '物品装备', '世界设定', '力量体系', '情节参考'], ARRAY['历史文化', '诗词对联'], '网游/电竞/虚拟现实类小说'),
('无限', ARRAY['角色', '物品装备', '生物生态', '世界设定', '力量体系', '情节参考'], ARRAY['经济货币'], '无限流/快穿/系统类小说')
ON CONFLICT (genre) DO NOTHING;

-- 索引
CREATE INDEX IF NOT EXISTS idx_project_pack_project ON project_knowledge_pack(project_id);
CREATE INDEX IF NOT EXISTS idx_genre_config_genre ON genre_knowledge_config(genre);
