-- Migration 205: Knowledge Base System
-- Creates: ref_categories, knowledge_entities, knowledge_relations,
--          universal_knowledge, project_knowledge, world_snapshots,
--          ref_search_jobs, ref_gap_logs

BEGIN;

-- ============================================================
-- 1. ref_categories (知识分类)
-- ============================================================
CREATE TABLE IF NOT EXISTS ref_categories (
  id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
  parent_id UUID REFERENCES ref_categories(id) ON DELETE SET NULL,
  slug VARCHAR(50) NOT NULL UNIQUE,
  name VARCHAR(100) NOT NULL,
  description TEXT,
  genre_tags TEXT[] DEFAULT '{}',
  search_keywords TEXT[] DEFAULT '{}',
  sort_order INT DEFAULT 0,
  is_system BOOLEAN DEFAULT false,
  created_at TIMESTAMPTZ DEFAULT now()
);

CREATE INDEX IF NOT EXISTS idx_rc_parent ON ref_categories(parent_id);
CREATE INDEX IF NOT EXISTS idx_rc_slug ON ref_categories(slug);

-- Seed top-level categories
INSERT INTO ref_categories (slug, name, description, sort_order, is_system) VALUES
  ('history', '历史资料', '历史人物、事件、进程、地理', 1, true),
  ('era', '时代背景', '政治、经济、社会、文化、科技', 2, true),
  ('genre', '题材设定模板', '修仙、玄幻、科幻、灵异、末日、游戏、都市', 3, true),
  ('professional', '专业知识', '军事、医学、建筑、法律、宗教、工艺、自然科学', 4, true),
  ('writing', '写作参考', '对话风格、描写素材、名称素材', 5, true)
ON CONFLICT (slug) DO NOTHING;

-- Sub-categories for history
INSERT INTO ref_categories (parent_id, slug, name, sort_order, is_system)
SELECT id, 'historical_figure', '历史人物', 1, true FROM ref_categories WHERE slug = 'history'
ON CONFLICT (slug) DO NOTHING;
INSERT INTO ref_categories (parent_id, slug, name, sort_order, is_system)
SELECT id, 'historical_event', '历史事件', 2, true FROM ref_categories WHERE slug = 'history'
ON CONFLICT (slug) DO NOTHING;
INSERT INTO ref_categories (parent_id, slug, name, sort_order, is_system)
SELECT id, 'historical_process', '历史进程', 3, true FROM ref_categories WHERE slug = 'history'
ON CONFLICT (slug) DO NOTHING;
INSERT INTO ref_categories (parent_id, slug, name, sort_order, is_system)
SELECT id, 'historical_geo', '历史地理', 4, true FROM ref_categories WHERE slug = 'history'
ON CONFLICT (slug) DO NOTHING;

-- Sub-categories for era
INSERT INTO ref_categories (parent_id, slug, name, sort_order, is_system)
SELECT id, 'politics', '政治体制', 1, true FROM ref_categories WHERE slug = 'era'
ON CONFLICT (slug) DO NOTHING;
INSERT INTO ref_categories (parent_id, slug, name, sort_order, is_system)
SELECT id, 'economy', '经济体系', 2, true FROM ref_categories WHERE slug = 'era'
ON CONFLICT (slug) DO NOTHING;
INSERT INTO ref_categories (parent_id, slug, name, sort_order, is_system)
SELECT id, 'society', '社会结构', 3, true FROM ref_categories WHERE slug = 'era'
ON CONFLICT (slug) DO NOTHING;
INSERT INTO ref_categories (parent_id, slug, name, sort_order, is_system)
SELECT id, 'culture', '文化风俗', 4, true FROM ref_categories WHERE slug = 'era'
ON CONFLICT (slug) DO NOTHING;
INSERT INTO ref_categories (parent_id, slug, name, sort_order, is_system)
SELECT id, 'technology', '科技水平', 5, true FROM ref_categories WHERE slug = 'era'
ON CONFLICT (slug) DO NOTHING;

-- Sub-categories for genre
INSERT INTO ref_categories (parent_id, slug, name, sort_order, is_system)
SELECT id, 'xianxia', '修仙体系', 1, true FROM ref_categories WHERE slug = 'genre'
ON CONFLICT (slug) DO NOTHING;
INSERT INTO ref_categories (parent_id, slug, name, sort_order, is_system)
SELECT id, 'xuanhuan', '玄幻设定', 2, true FROM ref_categories WHERE slug = 'genre'
ON CONFLICT (slug) DO NOTHING;
INSERT INTO ref_categories (parent_id, slug, name, sort_order, is_system)
SELECT id, 'scifi', '科幻设定', 3, true FROM ref_categories WHERE slug = 'genre'
ON CONFLICT (slug) DO NOTHING;
INSERT INTO ref_categories (parent_id, slug, name, sort_order, is_system)
SELECT id, 'horror', '灵异设定', 4, true FROM ref_categories WHERE slug = 'genre'
ON CONFLICT (slug) DO NOTHING;
INSERT INTO ref_categories (parent_id, slug, name, sort_order, is_system)
SELECT id, 'post_apocalyptic', '末日设定', 5, true FROM ref_categories WHERE slug = 'genre'
ON CONFLICT (slug) DO NOTHING;
INSERT INTO ref_categories (parent_id, slug, name, sort_order, is_system)
SELECT id, 'game', '游戏设定', 6, true FROM ref_categories WHERE slug = 'genre'
ON CONFLICT (slug) DO NOTHING;
INSERT INTO ref_categories (parent_id, slug, name, sort_order, is_system)
SELECT id, 'urban', '都市设定', 7, true FROM ref_categories WHERE slug = 'genre'
ON CONFLICT (slug) DO NOTHING;

-- ============================================================
-- 2. knowledge_entities (知识实体)
-- ============================================================
CREATE TABLE IF NOT EXISTS knowledge_entities (
  id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
  entity_type VARCHAR(50) NOT NULL,
  name VARCHAR(200) NOT NULL,
  aliases TEXT[] DEFAULT '{}',
  summary TEXT,
  content TEXT NOT NULL,
  structured_data JSONB DEFAULT '{}',
  source VARCHAR(50) DEFAULT 'manual',
  source_url TEXT,
  reliability FLOAT DEFAULT 0.5,
  genre_tags TEXT[] DEFAULT '{}',
  era VARCHAR(100),
  embedding_id TEXT,
  search_vector TSVECTOR GENERATED ALWAYS AS (
    to_tsvector('simple', COALESCE(name,'') || ' ' || COALESCE(content,''))
  ) STORED,
  status VARCHAR(20) DEFAULT 'active',
  use_count INT DEFAULT 0,
  created_at TIMESTAMPTZ DEFAULT now(),
  updated_at TIMESTAMPTZ DEFAULT now()
);

CREATE INDEX IF NOT EXISTS idx_ke_type ON knowledge_entities(entity_type);
CREATE INDEX IF NOT EXISTS idx_ke_genre ON knowledge_entities USING GIN(genre_tags);
CREATE INDEX IF NOT EXISTS idx_ke_search ON knowledge_entities USING GIN(search_vector);
CREATE INDEX IF NOT EXISTS idx_ke_embedding ON knowledge_entities(embedding_id);
CREATE INDEX IF NOT EXISTS idx_ke_name ON knowledge_entities(name);
CREATE INDEX IF NOT EXISTS idx_ke_status ON knowledge_entities(status);

-- ============================================================
-- 3. knowledge_relations (实体关联)
-- ============================================================
CREATE TABLE IF NOT EXISTS knowledge_relations (
  id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
  from_entity_id UUID REFERENCES knowledge_entities(id) ON DELETE CASCADE,
  to_entity_id UUID REFERENCES knowledge_entities(id) ON DELETE CASCADE,
  relation_type VARCHAR(50) NOT NULL,
  relation_detail VARCHAR(200),
  strength FLOAT DEFAULT 1.0,
  metadata JSONB DEFAULT '{}',
  created_at TIMESTAMPTZ DEFAULT now(),
  UNIQUE(from_entity_id, to_entity_id, relation_type)
);

CREATE INDEX IF NOT EXISTS idx_kr_from ON knowledge_relations(from_entity_id);
CREATE INDEX IF NOT EXISTS idx_kr_to ON knowledge_relations(to_entity_id);
CREATE INDEX IF NOT EXISTS idx_kr_type ON knowledge_relations(relation_type);

-- ============================================================
-- 4. universal_knowledge (通用知识库)
-- ============================================================
CREATE TABLE IF NOT EXISTS universal_knowledge (
  id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
  category_id UUID REFERENCES ref_categories(id) ON DELETE SET NULL,
  topic VARCHAR(200) NOT NULL,
  summary TEXT,
  content TEXT NOT NULL,
  structured_data JSONB DEFAULT '{}',
  era VARCHAR(100),
  year_range INT[],
  genre_tags TEXT[] DEFAULT '{}',
  source VARCHAR(50) DEFAULT 'manual',
  source_url TEXT,
  reliability FLOAT DEFAULT 0.5,
  last_verified_at TIMESTAMPTZ,
  embedding_id TEXT,
  search_vector TSVECTOR GENERATED ALWAYS AS (
    to_tsvector('simple', COALESCE(topic,'') || ' ' || COALESCE(content,''))
  ) STORED,
  tags TEXT[] DEFAULT '{}',
  status VARCHAR(20) DEFAULT 'active',
  use_count INT DEFAULT 0,
  created_at TIMESTAMPTZ DEFAULT now(),
  updated_at TIMESTAMPTZ DEFAULT now()
);

CREATE INDEX IF NOT EXISTS idx_uk_genre ON universal_knowledge USING GIN(genre_tags);
CREATE INDEX IF NOT EXISTS idx_uk_year ON universal_knowledge(year_range);
CREATE INDEX IF NOT EXISTS idx_uk_search ON universal_knowledge USING GIN(search_vector);
CREATE INDEX IF NOT EXISTS idx_uk_embedding ON universal_knowledge(embedding_id);
CREATE INDEX IF NOT EXISTS idx_uk_category ON universal_knowledge(category_id);
CREATE INDEX IF NOT EXISTS idx_uk_status ON universal_knowledge(status);

-- ============================================================
-- 5. project_knowledge (项目知识库)
-- ============================================================
CREATE TABLE IF NOT EXISTS project_knowledge (
  id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
  project_id UUID NOT NULL,
  category VARCHAR(50) NOT NULL,
  key VARCHAR(200) NOT NULL,
  value JSONB NOT NULL,
  description TEXT,
  chapter_no INT,
  related_entry_ids UUID[] DEFAULT '{}',
  tags TEXT[] DEFAULT '{}',
  status VARCHAR(20) DEFAULT 'active',
  created_at TIMESTAMPTZ DEFAULT now(),
  updated_at TIMESTAMPTZ DEFAULT now(),
  UNIQUE(project_id, category, key)
);

CREATE INDEX IF NOT EXISTS idx_pk_project ON project_knowledge(project_id);
CREATE INDEX IF NOT EXISTS idx_pk_category ON project_knowledge(project_id, category);
CREATE INDEX IF NOT EXISTS idx_pk_status ON project_knowledge(status);

-- ============================================================
-- 6. world_snapshots (世界状态快照)
-- ============================================================
CREATE TABLE IF NOT EXISTS world_snapshots (
  id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
  project_id UUID NOT NULL,
  chapter_no INT NOT NULL,
  story_time VARCHAR(100),
  story_year INT,
  story_era VARCHAR(100),
  story_progress FLOAT,
  world_state JSONB NOT NULL,
  character_count INT DEFAULT 0,
  active_threads TEXT[] DEFAULT '{}',
  relevant_knowledge_ids UUID[] DEFAULT '{}',
  created_at TIMESTAMPTZ DEFAULT now()
);

CREATE INDEX IF NOT EXISTS idx_ws_project ON world_snapshots(project_id, chapter_no);

-- ============================================================
-- 7. ref_search_jobs (搜索任务队列)
-- ============================================================
CREATE TABLE IF NOT EXISTS ref_search_jobs (
  id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
  project_id UUID,
  query_text TEXT NOT NULL,
  search_context TEXT,
  category_id UUID REFERENCES ref_categories(id) ON DELETE SET NULL,
  status VARCHAR(20) DEFAULT 'pending',
  results_count INT DEFAULT 0,
  entries_created INT DEFAULT 0,
  error_message TEXT,
  triggered_by VARCHAR(50),
  chapter_no INT,
  created_at TIMESTAMPTZ DEFAULT now(),
  completed_at TIMESTAMPTZ
);

CREATE INDEX IF NOT EXISTS idx_rsj_status ON ref_search_jobs(status);
CREATE INDEX IF NOT EXISTS idx_rsj_project ON ref_search_jobs(project_id);

-- ============================================================
-- 8. ref_gap_logs (知识缺口记录)
-- ============================================================
CREATE TABLE IF NOT EXISTS ref_gap_logs (
  id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
  project_id UUID,
  gap_type VARCHAR(50) NOT NULL,
  description TEXT NOT NULL,
  context TEXT,
  entity_name VARCHAR(200),
  entity_type VARCHAR(50),
  resolved BOOLEAN DEFAULT false,
  resolved_by_entry_id UUID,
  resolved_at TIMESTAMPTZ,
  created_at TIMESTAMPTZ DEFAULT now()
);

CREATE INDEX IF NOT EXISTS idx_rgl_project ON ref_gap_logs(project_id);
CREATE INDEX IF NOT EXISTS idx_rgl_resolved ON ref_gap_logs(resolved);

COMMIT;
